from __future__ import annotations

import hashlib
import json
from typing import Any


SUPPORTED_TRUE = {
    True,
    "supported",
    "true",
    "yes",
    "available",
    "input_and_output",
    "input_only",
    "output_only",
}
SUPPORTED_FALSE = {
    False,
    "not_supported",
    "not supported",
    "false",
    "no",
    "unavailable",
}


def stable_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _find_model(
    selector_document: dict[str, Any],
    provider_slug: str | None,
    model_key: str | None,
) -> dict[str, Any] | None:
    if not provider_slug or not model_key:
        return None
    for item in selector_document.get("models", []) or []:
        if (
            str(item.get("provider_slug", "")).lower()
            == str(provider_slug).lower()
            and str(item.get("model_key", "")).lower()
            == str(model_key).lower()
        ):
            return item
    return None


def _get_dot_path(obj: Any, path: str) -> tuple[Any, bool]:
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None, False
        current = current[part]
    return current, True


def _explicit_supported(value: Any) -> bool | None:
    if value is True:
        return True
    if value is False:
        return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in SUPPORTED_TRUE:
            return True
        if normalized in SUPPORTED_FALSE:
            return False
    return None


def _modality_support(
    candidate: dict[str, Any],
    modality: str,
    direction: str,
) -> bool | None:
    modalities = candidate.get("modalities") or {}
    modality_l = modality.lower()
    direction_l = direction.lower()

    states = modalities.get("states")
    if isinstance(states, dict):
        state = states.get(modality_l)
        if state is None:
            return None
        state_l = str(state).lower()
        if state_l == "input_and_output":
            return True
        if direction_l == "input" and state_l == "input_only":
            return True
        if direction_l == "output" and state_l == "output_only":
            return True
        if state_l == "not_supported":
            return False
        return False

    values = modalities.get(direction_l)
    if isinstance(values, list):
        normalized = {str(x).strip().lower() for x in values}
        return modality_l in normalized

    # Raw provider strings are intentionally not interpreted as authoritative
    # modality structure during automatic migration.
    return None


def _price(candidate: dict[str, Any], key: str) -> float | None:
    pricing = candidate.get("pricing")
    if not isinstance(pricing, dict):
        return None
    unit = str(pricing.get("unit") or "")
    if "usd_per_1m" not in unit.lower():
        return None
    value = pricing.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _hard_filter(
    candidate: dict[str, Any],
    requirements: dict[str, Any],
) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    unknowns: list[dict[str, Any]] = []

    required_context = requirements.get("required_context_tokens")
    if required_context is not None:
        actual = candidate.get("context_window_tokens")
        if actual is None:
            unknowns.append({
                "constraint": "context",
                "required": required_context,
                "actual": None,
            })
        elif int(actual) < int(required_context):
            failures.append({
                "constraint": "context",
                "required": required_context,
                "actual": actual,
            })

    required_output = requirements.get("required_output_tokens")
    if required_output is not None:
        actual = candidate.get("max_output_tokens")
        if actual is None:
            unknowns.append({
                "constraint": "output",
                "required": required_output,
                "actual": None,
            })
        elif int(actual) < int(required_output):
            failures.append({
                "constraint": "output",
                "required": required_output,
                "actual": actual,
            })

    for path in requirements.get("required_capabilities", []) or []:
        value, exists = _get_dot_path(candidate, str(path))
        supported = _explicit_supported(value) if exists else None
        if supported is False:
            failures.append({
                "constraint": "capability",
                "path": path,
                "actual": value,
            })
        elif supported is None:
            unknowns.append({
                "constraint": "capability",
                "path": path,
                "actual": value if exists else None,
            })

    required_modalities = requirements.get("required_modalities") or {}
    for direction in ("input", "output"):
        for modality in required_modalities.get(direction, []) or []:
            supported = _modality_support(
                candidate,
                str(modality),
                direction,
            )
            if supported is False:
                failures.append({
                    "constraint": "modality",
                    "direction": direction,
                    "modality": modality,
                })
            elif supported is None:
                unknowns.append({
                    "constraint": "modality",
                    "direction": direction,
                    "modality": modality,
                })

    max_input_price = requirements.get("max_input_price_per_1m")
    if max_input_price is not None:
        actual = _price(candidate, "input")
        if actual is None:
            unknowns.append({
                "constraint": "max_input_price_per_1m",
                "required": max_input_price,
                "actual": None,
            })
        elif actual > float(max_input_price):
            failures.append({
                "constraint": "max_input_price_per_1m",
                "required": max_input_price,
                "actual": actual,
            })

    max_output_price = requirements.get("max_output_price_per_1m")
    if max_output_price is not None:
        actual = _price(candidate, "output")
        if actual is None:
            unknowns.append({
                "constraint": "max_output_price_per_1m",
                "required": max_output_price,
                "actual": None,
            })
        elif actual > float(max_output_price):
            failures.append({
                "constraint": "max_output_price_per_1m",
                "required": max_output_price,
                "actual": actual,
            })

    return not failures and not unknowns, failures, unknowns


def _source_trigger(
    source: dict[str, Any] | None,
    explicit_request: bool,
) -> tuple[bool, str]:
    if explicit_request:
        return True, "user_requested"

    if source is None:
        return True, "source_not_currently_verified"

    policy = str(source.get("default_policy") or "").lower()
    lifecycle = str(source.get("lifecycle_status") or "").lower()
    usage_state = str(source.get("usage_state") or "").lower()

    if policy == "stale":
        return True, "source_stale"
    if policy == "exclude":
        return True, "source_excluded"
    if "retired" in lifecycle:
        return True, "source_retired"
    if "deprecated" in lifecycle:
        return True, "source_deprecated"
    if usage_state == "transition_watch" or "shutdown" in lifecycle:
        return True, "source_transition"

    return False, "source_current"


def plan_migration(
    *,
    selector_document: dict[str, Any],
    current_status: dict[str, Any],
    source_provider: str | None,
    source_model: str | None,
    requirements: dict[str, Any] | None,
    explicit_request: bool = False,
    allow_cross_provider: bool = False,
    allow_specialized: bool = False,
    documented_replacement: dict[str, str] | None = None,
) -> dict[str, Any]:
    requirements = requirements or {}
    source = _find_model(
        selector_document,
        source_provider,
        source_model,
    )

    trigger_needed, trigger = _source_trigger(
        source,
        explicit_request,
    )

    source_target = {
        "provider_slug": source_provider,
        "model_key": source_model,
        "found_in_selector": source is not None,
        "verification_state": (
            source.get("verification_state") if source else None
        ),
        "lifecycle_status": (
            source.get("lifecycle_status") if source else None
        ),
        "default_policy": (
            source.get("default_policy") if source else None
        ),
        "semantic_hash": (
            source.get("semantic_hash") if source else None
        ),
    }

    if current_status.get("healthy") is not True:
        core = {
            "status": "blocked",
            "source_target": source_target,
            "trigger": trigger,
            "requirements": requirements,
            "eligible_candidates": [],
            "selected_target": None,
            "warnings": ["Aurora Live Data is not healthy."],
            "required_actions": [
                "restore_registry_health",
                "rerun_migration_plan",
            ],
        }
        return {
            "schema_version": "1.0.0",
            "migration_id": "mig_" + stable_hash(core)[:20],
            **core,
        }

    if not trigger_needed:
        core = {
            "status": "not_needed",
            "source_target": source_target,
            "trigger": trigger,
            "requirements": requirements,
            "eligible_candidates": [],
            "selected_target": source,
            "warnings": [],
            "required_actions": [],
        }
        return {
            "schema_version": "1.0.0",
            "migration_id": "mig_" + stable_hash(core)[:20],
            **core,
        }

    requirements_complete = (
        requirements.get("requirements_complete") is True
    )

    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    same_provider_eligible = 0

    for candidate in selector_document.get("models", []) or []:
        if (
            source_provider
            and source_model
            and str(candidate.get("provider_slug")).lower()
            == str(source_provider).lower()
            and str(candidate.get("model_key")).lower()
            == str(source_model).lower()
        ):
            continue

        policy = candidate.get("default_policy")
        if policy in {"exclude", "stale"}:
            continue
        if policy == "specialized" and not allow_specialized:
            continue
        if policy not in {
            "include",
            "include_with_warning",
            "specialized",
        }:
            continue

        same_provider = (
            source_provider is not None
            and str(candidate.get("provider_slug")).lower()
            == str(source_provider).lower()
        )

        if not same_provider and not allow_cross_provider:
            continue

        passes, failures, unknowns = _hard_filter(
            candidate,
            requirements,
        )
        if passes:
            record = {
                "provider_slug": candidate.get("provider_slug"),
                "model_key": candidate.get("model_key"),
                "display_name": candidate.get("display_name"),
                "verification_state": candidate.get(
                    "verification_state"
                ),
                "semantic_hash": candidate.get("semantic_hash"),
                "default_policy": policy,
                "usage_state": candidate.get("usage_state"),
                "same_provider": same_provider,
                "context_window_tokens": candidate.get(
                    "context_window_tokens"
                ),
                "max_output_tokens": candidate.get(
                    "max_output_tokens"
                ),
                "pricing": candidate.get("pricing"),
                "semantic_source_url": candidate.get(
                    "semantic_source_url"
                ),
            }
            eligible.append(record)
            if same_provider:
                same_provider_eligible += 1
        elif failures or unknowns:
            rejected.append({
                "provider_slug": candidate.get("provider_slug"),
                "model_key": candidate.get("model_key"),
                "failures": failures,
                "unknowns": unknowns,
            })

    # Same-provider candidates remain preferred. Cross-provider candidates are
    # kept only when explicitly authorized; they never outrank a same-provider
    # candidate through an opaque quality score.
    eligible.sort(
        key=lambda x: (
            not x["same_provider"],
            x["default_policy"] != "include",
            str(x["provider_slug"]),
            str(x["model_key"]),
        )
    )

    selected = None
    warnings: list[str] = []
    actions: list[str] = []

    if documented_replacement:
        replacement = next(
            (
                item
                for item in eligible
                if (
                    str(item.get("provider_slug")).lower()
                    == str(
                        documented_replacement.get(
                            "provider_slug"
                        )
                    ).lower()
                    and str(item.get("model_key")).lower()
                    == str(
                        documented_replacement.get("model_key")
                    ).lower()
                )
            ),
            None,
        )
        if replacement and requirements_complete:
            selected = replacement

    if selected is None and requirements_complete:
        preferred_pool = [
            x for x in eligible if x["same_provider"]
        ]
        if not preferred_pool:
            preferred_pool = eligible

        if len(preferred_pool) == 1:
            selected = preferred_pool[0]

    if selected is not None:
        status = "plan_ready"
        if selected.get("default_policy") == "include_with_warning":
            warnings.append(
                "Selected target carries a lifecycle/stage warning."
            )
        actions = [
            "adapt_prompt_to_selected_target",
            "run_runtime_acceptance",
            "generate_validation_manifest",
            "compare_pre_and_post_migration_manifests",
        ]
    else:
        status = "needs_review"
        if not requirements_complete:
            warnings.append(
                "Migration requirements are not complete enough for automatic target selection."
            )
            actions.append("establish_missing_requirements")
        if not eligible:
            warnings.append(
                "No candidate satisfies all verified hard constraints under the current migration permissions."
            )
            actions.append("review_constraints_or_provider_scope")
        elif len(eligible) > 1:
            warnings.append(
                "Multiple compatible candidates remain; Aurora will not choose one using an opaque global quality score."
            )
            actions.append("choose_between_eligible_candidates")
        if (
            source_provider
            and same_provider_eligible == 0
            and not allow_cross_provider
        ):
            warnings.append(
                "No same-provider candidate is established; cross-provider migration requires authorization."
            )
            actions.append("authorize_cross_provider_if_desired")

    core = {
        "status": status,
        "source_target": source_target,
        "trigger": trigger,
        "requirements": requirements,
        "eligible_candidates": eligible,
        "selected_target": selected,
        "warnings": warnings,
        "required_actions": _dedupe(actions),
        "diagnostics": {
            "eligible_count": len(eligible),
            "same_provider_eligible_count": same_provider_eligible,
            "rejected_count": len(rejected),
        },
    }
    return {
        "schema_version": "1.0.0",
        "migration_id": "mig_" + stable_hash(core)[:20],
        **core,
    }


def _dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_migration_document(
    *,
    policy: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": policy.get("schema_version", "1.0.0"),
        "generated_at": generated_at,
        "ready": True,
        "policy_hash": stable_hash(policy),
        "storage": policy.get("storage", {}),
        "triggers": policy.get("triggers", {}),
        "constraints": policy.get("constraints", {}),
        "candidate_policy": policy.get("candidate_policy", {}),
        "filtering": policy.get("filtering", {}),
        "selection": policy.get("selection", {}),
        "migration_flow": policy.get("migration_flow", []),
        "statuses": policy.get("statuses", {}),
        "output": policy.get("output", {}),
        "post_migration": policy.get("post_migration", {}),
    }

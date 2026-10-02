from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


PROMPT_RELEVANT_SCOPES = {"eval", "golden", "runtime", "model", "guidance"}
CORE_SCOPES = {"eval", "golden", "runtime"}


def stable_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _selector_model(
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


def _guidance_map(
    guidance_document: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in guidance_document.get("guidance", []) or []
        if isinstance(item, dict) and item.get("id")
    }


def _dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def assess_revalidation(
    *,
    manifest: dict[str, Any],
    current_status: dict[str, Any],
    current_runtime: dict[str, Any],
    selector_document: dict[str, Any],
    guidance_document: dict[str, Any],
    policy: dict[str, Any],
    current_prompt_fingerprint: str | None = None,
    assessed_at: str | None = None,
) -> dict[str, Any]:
    assessed_at = assessed_at or utc_iso()
    changes: list[dict[str, Any]] = []
    scopes: list[str] = []
    actions: list[str] = []
    reusable: list[str] = []

    historical_gate = (
        (manifest.get("release") or {}).get("final_release_gate")
    )

    old_fp = manifest.get("prompt_fingerprint_sha256")
    if old_fp and current_prompt_fingerprint:
        prompt_identity = (
            "same"
            if str(old_fp).lower() == str(current_prompt_fingerprint).lower()
            else "different"
        )
    else:
        prompt_identity = "unknown"

    # Environment readiness is checked independently from prompt-specific change
    # detection. A blocked environment prevents a fresh validation result.
    blockers: list[str] = []
    if current_status.get("healthy") is not True:
        blockers.append("registry_unhealthy")
    if current_status.get("runtime_acceptance_ready") is not True:
        blockers.append("runtime_acceptance_not_ready")
    if current_runtime.get("ready") is not True:
        blockers.append("runtime_document_not_ready")
    if current_status.get("benchmark_suite_gate") != "pass":
        blockers.append("benchmark_suite_not_pass")
    if current_status.get("golden_suite_gate") != "pass":
        blockers.append("golden_suite_not_pass")

    dependency_impacts = policy.get("dependency_impacts", {})
    old_dependencies = manifest.get("dependencies") or {}
    current_dependency_values = {
        "eval_spec_hash": current_status.get("eval_spec_hash"),
        "golden_suite_hash": current_status.get("golden_suite_hash"),
        "runtime_policy_hash": current_status.get("runtime_policy_hash"),
        "benchmark_corpus_hash": current_status.get("benchmark_corpus_hash"),
        "traceability_policy_hash": current_status.get("traceability_policy_hash"),
    }

    for key, current_value in current_dependency_values.items():
        previous_value = old_dependencies.get(key)
        if previous_value == current_value and current_value is not None:
            impact = dependency_impacts.get(key, {})
            scope = impact.get("scope")
            if scope:
                reusable.append(f"{scope}:{key}")
            continue

        impact = dependency_impacts.get(key, {})
        scope = impact.get("scope", "unknown")
        action = impact.get("action", "review_dependency_change")
        changes.append({
            "type": "dependency_changed",
            "dependency": key,
            "before": previous_value,
            "after": current_value,
            "scope": scope,
            "prompt_revalidation": bool(
                impact.get("prompt_revalidation")
            ),
        })
        scopes.append(scope)
        actions.append(action)

    # Model-target replay.
    target = manifest.get("target") or {}
    provider_slug = target.get("provider_slug")
    model_key = target.get("model_key")
    current_model = _selector_model(
        selector_document,
        provider_slug,
        model_key,
    )

    if provider_slug and model_key:
        if current_model is None:
            changes.append({
                "type": "target_model_missing",
                "provider_slug": provider_slug,
                "model_key": model_key,
            })
            scopes.append("model")
            actions.append("rerun_model_discovery_and_compatibility")
        elif (
            current_model.get("verification_state")
            != "verified_official_detail"
        ):
            changes.append({
                "type": "target_model_not_currently_verified",
                "provider_slug": provider_slug,
                "model_key": model_key,
                "verification_state": current_model.get(
                    "verification_state"
                ),
                "default_policy": current_model.get("default_policy"),
            })
            scopes.append("model")
            actions.append("rerun_model_compatibility")
        else:
            old_semantic_hash = target.get("semantic_hash")
            current_semantic_hash = current_model.get("semantic_hash")
            if not old_semantic_hash:
                changes.append({
                    "type": "historical_model_semantic_hash_missing",
                    "provider_slug": provider_slug,
                    "model_key": model_key,
                    "current_semantic_hash": current_semantic_hash,
                })
                scopes.append("model")
                actions.append("rerun_model_compatibility")
            elif not current_semantic_hash:
                changes.append({
                    "type": "current_model_semantic_hash_missing",
                    "provider_slug": provider_slug,
                    "model_key": model_key,
                    "historical_semantic_hash": old_semantic_hash,
                })
                scopes.append("model")
                actions.append("rerun_model_compatibility")
            elif old_semantic_hash != current_semantic_hash:
                changes.append({
                    "type": "model_semantics_changed",
                    "provider_slug": provider_slug,
                    "model_key": model_key,
                    "before": old_semantic_hash,
                    "after": current_semantic_hash,
                })
                scopes.append("model")
                actions.append("rerun_model_compatibility")
            else:
                reusable.append("model:semantic_facts")

    # Guidance replay is rule-specific and keyed by source hash.
    current_guidance = _guidance_map(guidance_document)
    for old_rule in manifest.get("guidance_applied", []) or []:
        if not isinstance(old_rule, dict) or not old_rule.get("id"):
            continue
        rule_id = str(old_rule["id"])
        current_rule = current_guidance.get(rule_id)

        if current_rule is None:
            changes.append({
                "type": "guidance_rule_missing",
                "guidance_id": rule_id,
            })
            scopes.append("guidance")
            actions.append("rerun_guidance_alignment")
            continue

        if (
            current_rule.get("verification_state")
            != "verified_official_guidance"
        ):
            changes.append({
                "type": "guidance_rule_not_currently_verified",
                "guidance_id": rule_id,
                "verification_state": current_rule.get(
                    "verification_state"
                ),
            })
            scopes.append("guidance")
            actions.append("rerun_guidance_alignment")
            continue

        old_hash = old_rule.get("source_hash")
        current_hash = current_rule.get("source_hash")
        if not old_hash or not current_hash:
            changes.append({
                "type": "guidance_source_hash_missing",
                "guidance_id": rule_id,
                "before": old_hash,
                "after": current_hash,
            })
            scopes.append("guidance")
            actions.append("rerun_guidance_alignment")
        elif old_hash != current_hash:
            changes.append({
                "type": "guidance_source_changed",
                "guidance_id": rule_id,
                "before": old_hash,
                "after": current_hash,
            })
            scopes.append("guidance")
            actions.append("rerun_guidance_alignment")
        else:
            reusable.append(f"guidance:{rule_id}")

    scopes = _dedupe(scopes)
    actions = _dedupe(actions)
    reusable = _dedupe(reusable)

    prompt_relevant = sorted(
        set(scopes) & PROMPT_RELEVANT_SCOPES
    )
    core_changed = set(prompt_relevant) & CORE_SCOPES

    if blockers:
        status = "blocked"
    elif prompt_identity == "different":
        status = "different_prompt"
        actions = _dedupe(
            ["rerun_full_runtime_acceptance"] + actions
        )
    elif (
        policy.get("escalation", {}).get(
            "full_revalidation_if_all_changed"
        )
        and CORE_SCOPES.issubset(core_changed)
    ):
        status = "full_revalidation_required"
        actions = _dedupe(
            ["rerun_full_runtime_acceptance"] + actions
        )
    elif prompt_relevant:
        status = "selective_revalidation_required"
    else:
        status = "current"

    requires_prompt_content = status in {
        "different_prompt",
        "full_revalidation_required",
        "selective_revalidation_required",
    }

    environment_only_changes = bool(changes) and not prompt_relevant

    environment = {
        "live_data_version": current_status.get("schema_version"),
        "registry_generated_at": current_status.get("generated_at"),
        "healthy": current_status.get("healthy"),
        "runtime_ready": current_status.get(
            "runtime_acceptance_ready"
        ),
        "benchmark_suite_gate": current_status.get(
            "benchmark_suite_gate"
        ),
        "golden_suite_gate": current_status.get(
            "golden_suite_gate"
        ),
        "eval_spec_hash": current_status.get("eval_spec_hash"),
        "golden_suite_hash": current_status.get(
            "golden_suite_hash"
        ),
        "runtime_policy_hash": current_status.get(
            "runtime_policy_hash"
        ),
        "benchmark_corpus_hash": current_status.get(
            "benchmark_corpus_hash"
        ),
        "traceability_policy_hash": current_status.get(
            "traceability_policy_hash"
        ),
        "blockers": blockers,
    }

    core = {
        "source_manifest_id": manifest.get("manifest_id"),
        "assessed_at": assessed_at,
        "status": status,
        "historical_release_gate": historical_gate,
        "prompt_identity": prompt_identity,
        "environment": environment,
        "changes": changes,
        "impacted_scopes": scopes,
        "reusable_results": reusable,
        "required_actions": actions,
        "requires_prompt_content": requires_prompt_content,
    }
    replay_id = "replay_" + stable_hash(core)[:20]

    if status == "current":
        conclusion = (
            "No tracked prompt-relevant validation dependency changed. "
            "The historical release gate remains the last established outcome."
        )
    elif status == "selective_revalidation_required":
        conclusion = (
            "Only the listed validation scopes require a fresh check. "
            "Unchanged results may be reused."
        )
    elif status == "full_revalidation_required":
        conclusion = (
            "Core validation contracts changed broadly; rerun substantive "
            "runtime acceptance."
        )
    elif status == "different_prompt":
        conclusion = (
            "Fingerprints prove the prompt differs from the historical prompt; "
            "perform a full new validation."
        )
    else:
        conclusion = (
            "The current validation environment is not healthy enough to "
            "produce a fresh replay result."
        )

    return {
        "schema_version": "1.0.0",
        "replay_id": replay_id,
        **core,
        "summary": {
            "conclusion": conclusion,
            "environment_only_changes": environment_only_changes,
            "prompt_relevant_change_count": sum(
                1
                for item in changes
                if item.get("scope") in PROMPT_RELEVANT_SCOPES
                or item.get("type", "").startswith("target_")
                or item.get("type", "").startswith("model_")
                or item.get("type", "").startswith("historical_model_")
                or item.get("type", "").startswith("current_model_")
                or item.get("type", "").startswith("guidance_")
            ),
            "change_count": len(changes),
        },
    }


def build_replay_document(
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
        "statuses": policy.get("statuses", {}),
        "dependency_impacts": policy.get("dependency_impacts", {}),
        "target_rules": policy.get("target_rules", {}),
        "guidance_rules": policy.get("guidance_rules", {}),
        "escalation": policy.get("escalation", {}),
        "output": policy.get("output", {}),
        "interpretation_rules": policy.get(
            "interpretation_rules", []
        ),
    }

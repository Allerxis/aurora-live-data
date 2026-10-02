from __future__ import annotations

from typing import Any


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _context_tokens(provider: str, facts: dict[str, Any]) -> int | None:
    if provider == "google":
        return facts.get("input_token_limit")
    return facts.get("context_window_tokens")


def _max_output_tokens(provider: str, facts: dict[str, Any]) -> int | None:
    if provider == "google":
        return facts.get("output_token_limit")
    return facts.get("max_output_tokens")


def _knowledge_cutoff(provider: str, facts: dict[str, Any]) -> str | None:
    if provider == "anthropic":
        return facts.get("reliable_knowledge_cutoff")
    return facts.get("knowledge_cutoff")


def _pricing(provider: str, facts: dict[str, Any]) -> dict[str, Any] | None:
    pricing = facts.get("pricing")
    if not isinstance(pricing, dict):
        return None

    if provider == "xai" and isinstance(pricing.get("short_context"), dict):
        short = pricing["short_context"]
        return {
            "unit": pricing.get("unit"),
            "input": short.get("input"),
            "cached_input": short.get("cached_input"),
            "output": short.get("output"),
            "pricing_scope": "short_context",
            "long_context": pricing.get("long_context"),
            "long_context_threshold_tokens": pricing.get("long_context_threshold_tokens"),
        }

    return pricing


def _modalities(provider: str, facts: dict[str, Any]) -> dict[str, Any]:
    if provider == "openai":
        return {"states": facts.get("modalities", {})}

    if provider == "anthropic":
        raw = facts.get("input_output")
        return {"raw": raw} if raw else {}

    if provider == "google":
        return {
            "input": facts.get("input_types") or [],
            "output": facts.get("output_types") or [],
        }

    if provider == "xai":
        raw = facts.get("modalities_raw")
        return {"raw": raw} if raw else {}

    if provider == "meta":
        return {
            "input": facts.get("input_modalities") or [],
            "output": facts.get("output_modalities") or [],
        }

    return {}


def _capabilities(provider: str, facts: dict[str, Any]) -> dict[str, Any]:
    if provider == "openai":
        return {
            "features": facts.get("features", {}),
            "tools": facts.get("tools", {}),
            "reasoning_efforts": facts.get("reasoning_efforts", []),
        }

    if provider == "anthropic":
        return {
            "thinking": facts.get("thinking"),
            "default_effort": facts.get("default_effort"),
        }

    if provider == "google":
        return {
            "capabilities": facts.get("capabilities", {}),
            "consumption_options": facts.get("consumption_options", {}),
        }

    if provider == "xai":
        return {
            "capabilities": facts.get("capabilities", {}),
            "reasoning": facts.get("reasoning", {}),
            "batch_api": facts.get("batch_api"),
        }

    if provider == "mistral":
        return {
            "features": facts.get("features", {}),
            "endpoints": facts.get("endpoints", []),
            "release_stage": facts.get("release_stage"),
        }

    if provider == "meta":
        return {
            "distribution": facts.get("distribution"),
            "architecture": facts.get("architecture"),
        }

    return {}


def normalize_usage_state(model: dict[str, Any]) -> tuple[str, str]:
    """
    Return (usage_state, default_policy).

    default_policy is deliberately conservative:
    - include: verified and explicitly active/current enough for normal comparison
    - include_with_warning: verified but lifecycle/stage needs attention
    - specialized: verified open-weight/local-style record, not a hosted API claim
    - exclude: deprecated/retired
    - stale: previously verified facts that could not be revalidated this cycle
    """
    verification = _lower(model.get("verification_state"))
    lifecycle = _lower(model.get("lifecycle_status"))
    provider = _lower(model.get("provider_slug"))
    facts = model.get("facts") or {}

    if verification == "verified_official_detail_stale":
        return "stale_verification", "stale"

    if verification != "verified_official_detail":
        return "unverified", "exclude"

    if "retired" in lifecycle:
        return "retired", "exclude"

    if "deprecated" in lifecycle:
        return "deprecated", "exclude"

    if provider == "google" and lifecycle == "shutdown_announced":
        return "transition_watch", "include_with_warning"

    if provider == "mistral":
        stage = _lower(facts.get("release_stage") or lifecycle)
        if "labs" in stage:
            return "labs", "include_with_warning"

    if provider == "meta" and facts.get("distribution") == "open_weight":
        return "open_weight", "specialized"

    if "active" in lifecycle:
        return "active", "include"

    if lifecycle in ("no_shutdown_announced", "premier", "production"):
        return lifecycle, "include"

    return "verified_lifecycle_unknown", "include_with_warning"


def build_selector(
    provider_documents: dict[str, dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []

    for provider, document in provider_documents.items():
        for model in document.get("models", []):
            verification = model.get("verification_state")
            if verification not in (
                "verified_official_detail",
                "verified_official_detail_stale",
            ):
                continue

            facts = model.get("facts") or {}
            usage_state, default_policy = normalize_usage_state(model)

            records.append(
                {
                    "provider_slug": provider,
                    "model_key": model.get("model_key"),
                    "display_name": model.get("display_name"),
                    "verification_state": verification,
                    "semantic_verified_at": model.get("semantic_verified_at"),
                    "semantic_source_url": model.get("semantic_source_url"),
                    "lifecycle_status": model.get("lifecycle_status"),
                    "usage_state": usage_state,
                    "default_policy": default_policy,
                    "present_in_current_sources": bool(
                        model.get("present_in_current_sources")
                    ),
                    "context_window_tokens": _context_tokens(provider, facts),
                    "max_output_tokens": _max_output_tokens(provider, facts),
                    "knowledge_cutoff": _knowledge_cutoff(provider, facts),
                    "pricing": _pricing(provider, facts),
                    "modalities": _modalities(provider, facts),
                    "capabilities": _capabilities(provider, facts),
                }
            )

    records.sort(
        key=lambda x: (
            x["default_policy"] == "exclude",
            x["default_policy"] == "stale",
            x["provider_slug"],
            x["model_key"] or "",
        )
    )

    counts = {
        "total": len(records),
        "include": sum(x["default_policy"] == "include" for x in records),
        "include_with_warning": sum(
            x["default_policy"] == "include_with_warning" for x in records
        ),
        "specialized": sum(
            x["default_policy"] == "specialized" for x in records
        ),
        "exclude": sum(x["default_policy"] == "exclude" for x in records),
        "stale": sum(x["default_policy"] == "stale" for x in records),
    }

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "purpose": (
            "Compact cross-provider view for model selection. It contains only "
            "semantically verified or previously verified records."
        ),
        "policy": {
            "include": "Suitable for normal factual comparison, subject to task-specific constraints.",
            "include_with_warning": "May be compared, but lifecycle/stage caveats must be surfaced.",
            "specialized": "Use only when the task explicitly fits the distribution or deployment mode.",
            "exclude": "Do not propose by default; retained for legacy/deprecation context.",
            "stale": "Do not treat facts as current until revalidated.",
        },
        "counts": counts,
        "models": records,
    }

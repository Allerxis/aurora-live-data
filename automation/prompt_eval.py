from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


PRIVATE_COT_PATTERNS = [
    re.compile(r"\b(?:show|reveal|print|output|write)\b.{0,40}\b(?:chain[- ]of[- ]thought|hidden reasoning|private reasoning)\b", re.I),
    re.compile(r"\bthink step by step\b.{0,40}\b(?:show|reveal|print|output|write)\b", re.I),
]
NEGATION_RE = re.compile(r"\b(?:do not|don't|never|without)\b", re.I)
UNRESOLVED_MARKER_RE = re.compile(r"(?im)(?:\[\s*(?:todo|fixme|tbd)\s*\]|\b(?:todo|fixme|tbd)\s*:|\?\?\?)")
MUSTACHE_VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*\}\}")
DOLLAR_VAR_RE = re.compile(r"\$\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*\}")


def _result(
    criterion_id: str,
    outcome: str,
    severity: str,
    evidence: Any = None,
    message: str | None = None,
) -> dict[str, Any]:
    return {
        "criterion_id": criterion_id,
        "outcome": outcome,
        "severity": severity,
        "evidence": evidence,
        "message": message,
    }


def _find_model(selector_document: dict[str, Any], provider: str, model_key: str):
    for item in selector_document.get("models", []):
        if (
            str(item.get("provider_slug", "")).lower() == provider.lower()
            and str(item.get("model_key", "")).lower() == model_key.lower()
        ):
            return item
    return None


def _get_dot_path(obj: Any, path: str):
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
        if normalized in {"supported", "true", "yes", "available", "input_and_output", "input_only", "output_only"}:
            return True
        if normalized in {"not_supported", "not supported", "false", "no", "unavailable"}:
            return False
    return None


def _private_cot_hits(prompt: str) -> list[str]:
    hits = []
    for line in prompt.splitlines():
        for pattern in PRIVATE_COT_PATTERNS:
            m = pattern.search(line)
            if not m:
                continue
            prefix = line[max(0, m.start() - 30):m.start()]
            if NEGATION_RE.search(prefix):
                continue
            hits.append(m.group(0))
    return hits


def _template_variables(prompt: str) -> set[str]:
    return set(MUSTACHE_VAR_RE.findall(prompt)) | set(DOLLAR_VAR_RE.findall(prompt))


def evaluate_prompt(
    prompt: str,
    metadata: dict[str, Any] | None = None,
    selector_document: dict[str, Any] | None = None,
    guidance_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Deterministic release-gate evaluator.

    The function never fabricates semantic judgments. Semantic criteria are
    accepted only through metadata["semantic_checks"], where each supplied
    outcome must be pass/fail/needs_review/not_applicable and should include
    evidence.
    """
    metadata = metadata or {}
    selector_document = selector_document or {"models": []}
    guidance_document = guidance_document or {"guidance": []}
    results: list[dict[str, Any]] = []

    cot_hits = _private_cot_hits(prompt)
    results.append(
        _result(
            "safety.private_chain_of_thought",
            "fail" if cot_hits else "pass",
            "blocker",
            cot_hits,
            "Prompt requests disclosure of private reasoning." if cot_hits else None,
        )
    )

    markers = UNRESOLVED_MARKER_RE.findall(prompt)
    results.append(
        _result(
            "quality.unresolved_markers",
            "fail" if markers else "pass",
            "error",
            markers,
            "Unresolved editorial markers remain in the prompt." if markers else None,
        )
    )

    declared_variables = metadata.get("declared_variables")
    if declared_variables is None:
        results.append(_result("contract.variable_integrity", "not_applicable", "error"))
    else:
        used = _template_variables(prompt)
        declared = {str(x) for x in declared_variables}
        undeclared = sorted(used - declared)
        results.append(
            _result(
                "contract.variable_integrity",
                "fail" if undeclared else "pass",
                "error",
                {"used": sorted(used), "declared": sorted(declared), "undeclared": undeclared},
                "Prompt uses undeclared template variables." if undeclared else None,
            )
        )

    provider = metadata.get("provider_slug")
    model_key = metadata.get("model_key")
    target_model = None

    if provider and model_key:
        target_model = _find_model(selector_document, str(provider), str(model_key))
        if not target_model:
            results.append(
                _result(
                    "model.verified_target",
                    "needs_review",
                    "error",
                    {"provider_slug": provider, "model_key": model_key},
                    "Exact model is absent from the verified selector view.",
                )
            )
            results.append(_result("model.lifecycle_policy", "needs_review", "error"))
        else:
            verification = target_model.get("verification_state")
            results.append(
                _result(
                    "model.verified_target",
                    "pass" if verification == "verified_official_detail" else "needs_review",
                    "error",
                    {"verification_state": verification, "semantic_verified_at": target_model.get("semantic_verified_at")},
                )
            )
            policy = target_model.get("default_policy")
            if policy in {"exclude", "stale"}:
                lifecycle_outcome = "fail"
            elif policy in {"include_with_warning", "specialized"}:
                lifecycle_outcome = "needs_review"
            elif policy == "include":
                lifecycle_outcome = "pass"
            else:
                lifecycle_outcome = "needs_review"
            results.append(
                _result(
                    "model.lifecycle_policy",
                    lifecycle_outcome,
                    "error",
                    {"default_policy": policy, "usage_state": target_model.get("usage_state")},
                )
            )
    else:
        results.append(_result("model.verified_target", "not_applicable", "error"))
        results.append(_result("model.lifecycle_policy", "not_applicable", "error"))

    estimated_input = metadata.get("estimated_input_tokens")
    context_limit = target_model.get("context_window_tokens") if target_model else None
    if estimated_input is None or context_limit is None:
        context_outcome = "not_applicable" if estimated_input is None else "needs_review"
    else:
        context_outcome = "pass" if int(estimated_input) <= int(context_limit) else "fail"
    results.append(
        _result(
            "model.context_budget",
            context_outcome,
            "error",
            {"estimated_input_tokens": estimated_input, "context_window_tokens": context_limit},
        )
    )

    requested_output = metadata.get("requested_output_tokens")
    output_limit = target_model.get("max_output_tokens") if target_model else None
    if requested_output is None or output_limit is None:
        output_outcome = "not_applicable" if requested_output is None else "needs_review"
    else:
        output_outcome = "pass" if int(requested_output) <= int(output_limit) else "fail"
    results.append(
        _result(
            "model.output_budget",
            output_outcome,
            "error",
            {"requested_output_tokens": requested_output, "max_output_tokens": output_limit},
        )
    )

    required_capabilities = metadata.get("required_capabilities") or []
    if not required_capabilities:
        results.append(_result("model.required_capabilities", "not_applicable", "error"))
    elif not target_model:
        results.append(
            _result(
                "model.required_capabilities",
                "needs_review",
                "error",
                {"required_capabilities": required_capabilities},
            )
        )
    else:
        capability_evidence = {}
        failed = False
        unknown = False
        for path in required_capabilities:
            value, exists = _get_dot_path(target_model, str(path))
            supported = _explicit_supported(value) if exists else None
            capability_evidence[str(path)] = {"exists": exists, "value": value, "supported": supported}
            if supported is False:
                failed = True
            elif supported is None:
                unknown = True
        outcome = "fail" if failed else ("needs_review" if unknown else "pass")
        results.append(
            _result(
                "model.required_capabilities",
                outcome,
                "error",
                capability_evidence,
            )
        )

    uses_tools = metadata.get("uses_tools")
    tool_policy_present = metadata.get("tool_policy_present")
    if uses_tools is not True:
        tool_outcome = "not_applicable"
    elif tool_policy_present is True:
        tool_outcome = "pass"
    elif tool_policy_present is False:
        tool_outcome = "fail"
    else:
        tool_outcome = "needs_review"
    results.append(_result("tools.policy", tool_outcome, "error", {"uses_tools": uses_tools, "tool_policy_present": tool_policy_present}))

    consumes_untrusted = metadata.get("consumes_untrusted_data")
    untrusted_policy = metadata.get("untrusted_data_policy_present")
    if consumes_untrusted is not True:
        untrusted_outcome = "not_applicable"
    elif untrusted_policy is True:
        untrusted_outcome = "pass"
    elif untrusted_policy is False:
        untrusted_outcome = "fail"
    else:
        untrusted_outcome = "needs_review"
    results.append(
        _result(
            "security.untrusted_data_boundary",
            untrusted_outcome,
            "blocker",
            {"consumes_untrusted_data": consumes_untrusted, "untrusted_data_policy_present": untrusted_policy},
        )
    )

    output_contract = metadata.get("output_contract_present")
    if output_contract is True:
        output_contract_outcome = "pass"
    elif output_contract is False:
        output_contract_outcome = "fail"
    else:
        output_contract_outcome = "needs_review"
    results.append(
        _result(
            "contract.output_contract",
            output_contract_outcome,
            "error",
            {"output_contract_present": output_contract},
        )
    )

    semantic_checks = metadata.get("semantic_checks") or {}
    semantic_severity = {
        "semantic.objective_clarity": "error",
        "semantic.constraint_consistency": "blocker",
        "semantic.intent_preservation": "error",
        "semantic.ambiguity": "warning",
    }
    for criterion_id, severity in semantic_severity.items():
        supplied = semantic_checks.get(criterion_id)
        if isinstance(supplied, dict):
            outcome = supplied.get("outcome")
            evidence = supplied.get("evidence")
        else:
            outcome = supplied
            evidence = None
        if outcome not in {"pass", "fail", "needs_review", "not_applicable"}:
            outcome = "needs_review"
        results.append(_result(criterion_id, outcome, severity, evidence))

    if not provider:
        guidance_outcome = "not_applicable"
        guidance_evidence = None
    else:
        relevant = [
            x
            for x in guidance_document.get("guidance", [])
            if str(x.get("provider_slug", "")).lower() == str(provider).lower()
        ]
        states = sorted({str(x.get("verification_state")) for x in relevant})
        if not relevant:
            guidance_outcome = "needs_review"
        elif all(x.get("verification_state") == "verified_official_guidance" for x in relevant):
            guidance_outcome = "pass"
        else:
            guidance_outcome = "needs_review"
        guidance_evidence = {"rules": len(relevant), "verification_states": states}
    results.append(
        _result(
            "guidance.provider_alignment",
            guidance_outcome,
            "warning",
            guidance_evidence,
        )
    )

    failed = [x for x in results if x["outcome"] == "fail" and x["severity"] in {"blocker", "error"}]
    pending = [x for x in results if x["outcome"] == "needs_review"]

    if failed:
        release_gate = "fail"
    elif pending:
        release_gate = "needs_review"
    else:
        release_gate = "pass"

    return {
        "schema_version": "1.0.0",
        "release_gate": release_gate,
        "counts": {
            "pass": sum(x["outcome"] == "pass" for x in results),
            "fail": sum(x["outcome"] == "fail" for x in results),
            "needs_review": sum(x["outcome"] == "needs_review" for x in results),
            "not_applicable": sum(x["outcome"] == "not_applicable" for x in results),
        },
        "results": results,
    }


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

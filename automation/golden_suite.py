from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ALLOWED_OPERATIONS = {"create", "optimize", "adapt", "agentic", "multimodal"}
REQUIRED_INVARIANT_KEYS = {
    "must_preserve",
    "must_include_if_applicable",
    "must_not_add",
}


def stable_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_golden_suite(document: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    operation_counts = {op: 0 for op in sorted(ALLOWED_OPERATIONS)}

    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append({
            "path": "cases",
            "message": "Golden suite must contain at least one case.",
        })
        cases = []

    for index, case in enumerate(cases):
        path = f"cases[{index}]"
        case_id = case.get("id")
        operation = case.get("operation")
        brief = case.get("input_brief")
        invariants = case.get("invariants")
        criteria = case.get("required_eval_criteria")
        tests = case.get("acceptance_tests")

        if not isinstance(case_id, str) or not case_id.strip():
            errors.append({"path": f"{path}.id", "message": "Missing case id."})
        elif case_id in seen_ids:
            errors.append({"path": f"{path}.id", "message": "Duplicate case id."})
        else:
            seen_ids.add(case_id)

        if operation not in ALLOWED_OPERATIONS:
            errors.append({
                "path": f"{path}.operation",
                "message": f"Unsupported operation: {operation!r}",
            })
        else:
            operation_counts[operation] += 1

        if not isinstance(brief, str) or len(brief.strip()) < 20:
            errors.append({
                "path": f"{path}.input_brief",
                "message": "Input brief must be explicit enough to evaluate.",
            })

        if not isinstance(invariants, dict):
            errors.append({
                "path": f"{path}.invariants",
                "message": "Missing invariant contract.",
            })
        else:
            missing = REQUIRED_INVARIANT_KEYS - set(invariants)
            if missing:
                errors.append({
                    "path": f"{path}.invariants",
                    "message": f"Missing invariant groups: {sorted(missing)}",
                })
            for key in REQUIRED_INVARIANT_KEYS:
                values = invariants.get(key)
                if not isinstance(values, list):
                    errors.append({
                        "path": f"{path}.invariants.{key}",
                        "message": "Invariant group must be a list.",
                    })

        if not isinstance(criteria, list) or not criteria:
            errors.append({
                "path": f"{path}.required_eval_criteria",
                "message": "At least one eval criterion is required.",
            })

        if not isinstance(tests, list) or not tests:
            errors.append({
                "path": f"{path}.acceptance_tests",
                "message": "At least one acceptance test is required.",
            })

        if operation in {"optimize", "adapt"}:
            preserved = invariants.get("must_preserve", []) if isinstance(invariants, dict) else []
            if not preserved:
                errors.append({
                    "path": f"{path}.invariants.must_preserve",
                    "message": f"{operation} cases must define preserved intent/constraints.",
                })

        if operation == "agentic":
            required = set(criteria or [])
            if "tools.policy" not in required:
                errors.append({
                    "path": f"{path}.required_eval_criteria",
                    "message": "Agentic cases must include tools.policy.",
                })

        if operation == "adapt":
            required = set(criteria or [])
            if "semantic.intent_preservation" not in required:
                errors.append({
                    "path": f"{path}.required_eval_criteria",
                    "message": "Adaptation cases must test semantic.intent_preservation.",
                })

    for operation, count in operation_counts.items():
        if count == 0:
            warnings.append({
                "path": "cases",
                "message": f"No golden case currently covers operation {operation}.",
            })

    return {
        "schema_version": "1.0.0",
        "suite_gate": "pass" if not errors else "fail",
        "suite_hash": stable_hash(document),
        "summary": {
            "cases": len(cases),
            "errors": len(errors),
            "warnings": len(warnings),
            "operation_counts": operation_counts,
        },
        "errors": errors,
        "warnings": warnings,
    }


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

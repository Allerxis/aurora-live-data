from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ALLOWED_OPERATIONS = {"create", "optimize", "adapt", "agentic", "multimodal"}
ALLOWED_COVERAGE = {"exact", "partial", "operation_baseline", "eval_only"}


def stable_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _contract_map(golden_document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        case["id"]: case
        for case in golden_document.get("cases", [])
        if isinstance(case, dict) and case.get("id")
    }


def validate_runtime_policy(
    policy: dict[str, Any],
    eval_document: dict[str, Any],
    golden_document: dict[str, Any],
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    eval_ids = {
        row.get("id")
        for row in eval_document.get("criteria", [])
        if isinstance(row, dict) and row.get("id")
    }
    contracts = _contract_map(golden_document)
    routing = policy.get("routing", {})

    for operation in ALLOWED_OPERATIONS:
        if operation not in routing:
            errors.append({
                "path": f"routing.{operation}",
                "message": "Missing runtime routing entry.",
            })

    for operation, route in routing.items():
        if operation not in ALLOWED_OPERATIONS:
            errors.append({
                "path": f"routing.{operation}",
                "message": "Unknown operation.",
            })
            continue

        referenced: list[str] = []
        referenced.extend(route.get("baseline_contracts", []) or [])
        for selector in route.get("selectors", []) or []:
            referenced.extend(selector.get("contracts", []) or [])

        for contract_id in referenced:
            contract = contracts.get(contract_id)
            if not contract:
                errors.append({
                    "path": f"routing.{operation}",
                    "message": f"Unknown golden contract {contract_id}.",
                })
                continue
            if contract.get("operation") != operation:
                errors.append({
                    "path": f"routing.{operation}",
                    "message": (
                        f"Golden contract {contract_id} belongs to "
                        f"{contract.get('operation')!r}, not {operation!r}."
                    ),
                })

        for index, selector in enumerate(route.get("selectors", []) or []):
            triggers = selector.get("when")
            if not isinstance(triggers, list) or not any(
                isinstance(x, str) and x.strip() for x in triggers
            ):
                errors.append({
                    "path": f"routing.{operation}.selectors[{index}].when",
                    "message": "Selector must contain at least one non-empty trigger.",
                })

    golden_validation = golden_document.get("validation", {})
    if golden_validation.get("suite_gate") != "pass":
        errors.append({
            "path": "golden.validation.suite_gate",
            "message": "Golden suite must pass before runtime acceptance can be ready.",
        })

    for contract_id, contract in contracts.items():
        for criterion_id in contract.get("required_eval_criteria", []) or []:
            if criterion_id not in eval_ids:
                errors.append({
                    "path": f"golden.{contract_id}.required_eval_criteria",
                    "message": f"Unknown eval criterion {criterion_id}.",
                })

    execution = policy.get("execution", {})
    max_repairs = execution.get("max_repair_passes")
    if not isinstance(max_repairs, int) or not 0 <= max_repairs <= 3:
        errors.append({
            "path": "execution.max_repair_passes",
            "message": "max_repair_passes must be an integer from 0 through 3.",
        })

    report = policy.get("runtime_report", {})
    coverage_values = set(report.get("coverage_values", []) or [])
    if coverage_values != ALLOWED_COVERAGE:
        warnings.append({
            "path": "runtime_report.coverage_values",
            "message": (
                "Coverage values differ from the reference set: "
                f"{sorted(ALLOWED_COVERAGE)}."
            ),
        })

    required_report_fields = set(report.get("required_fields", []) or [])
    expected_fields = {
        "operation",
        "contracts_applied",
        "coverage",
        "eval_release_gate",
        "golden_release_gate",
        "final_release_gate",
        "repair_passes",
        "unresolved",
    }
    missing = expected_fields - required_report_fields
    if missing:
        errors.append({
            "path": "runtime_report.required_fields",
            "message": f"Missing runtime report fields: {sorted(missing)}",
        })

    return {
        "schema_version": "1.0.0",
        "suite_gate": "pass" if not errors else "fail",
        "policy_hash": stable_hash(policy),
        "eval_spec_hash": eval_document.get("spec_hash"),
        "golden_suite_hash": golden_document.get("suite_hash"),
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
            "operations": len(routing),
            "contracts": len(contracts),
        },
        "errors": errors,
        "warnings": warnings,
    }


def select_runtime_contracts(
    operation: str,
    task_text: str,
    policy: dict[str, Any],
    golden_document: dict[str, Any],
) -> dict[str, Any]:
    if operation not in ALLOWED_OPERATIONS:
        return {
            "operation": operation,
            "contracts": [],
            "coverage": "eval_only",
            "matched_selectors": [],
        }

    route = policy.get("routing", {}).get(operation, {})
    available = _contract_map(golden_document)
    selected: list[str] = []
    matched_selectors: list[dict[str, Any]] = []

    for contract_id in route.get("baseline_contracts", []) or []:
        if contract_id in available and contract_id not in selected:
            selected.append(contract_id)

    normalized_task = re.sub(r"\s+", " ", task_text.lower()).strip()
    for selector in route.get("selectors", []) or []:
        matched = [
            trigger
            for trigger in selector.get("when", [])
            if str(trigger).lower() in normalized_task
        ]
        if not matched:
            continue

        contracts = [
            contract_id
            for contract_id in selector.get("contracts", [])
            if contract_id in available
        ]
        for contract_id in contracts:
            if contract_id not in selected:
                selected.append(contract_id)
        matched_selectors.append({
            "matched_triggers": matched,
            "contracts": contracts,
        })

    if matched_selectors and selected:
        coverage = "exact"
    elif selected:
        coverage = "operation_baseline"
    else:
        coverage = "eval_only"

    return {
        "operation": operation,
        "contracts": selected,
        "coverage": coverage,
        "matched_selectors": matched_selectors,
    }


def build_runtime_document(
    policy: dict[str, Any],
    eval_document: dict[str, Any],
    golden_document: dict[str, Any],
    benchmark_document: dict[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    validation = validate_runtime_policy(
        policy=policy,
        eval_document=eval_document,
        golden_document=golden_document,
    )

    benchmark_document = benchmark_document or {}
    benchmark_gate = benchmark_document.get("suite_gate")
    dependency_gate = policy.get("dependency_gate", {})
    require_benchmark = dependency_gate.get("require_benchmark_suite_pass") is True

    ready = validation.get("suite_gate") == "pass"
    reasons: list[str] = []

    if golden_document.get("validation", {}).get("suite_gate") != "pass":
        ready = False
        reasons.append("golden_suite_not_pass")

    if require_benchmark and benchmark_gate != "pass":
        ready = False
        reasons.append("benchmark_suite_not_pass")

    if not eval_document.get("criteria"):
        ready = False
        reasons.append("eval_contract_missing")

    return {
        "schema_version": policy.get("schema_version", "1.0.0"),
        "generated_at": generated_at,
        "ready": ready,
        "readiness_reasons": reasons,
        "validation": validation,
        "dependencies": {
            "eval_spec_hash": eval_document.get("spec_hash"),
            "golden_suite_hash": golden_document.get("suite_hash"),
            "benchmark_corpus_hash": benchmark_document.get("corpus_hash"),
            "benchmark_suite_gate": benchmark_gate,
        },
        "policy": policy,
    }

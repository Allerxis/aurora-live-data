from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from prompt_eval import evaluate_prompt


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "automation" / "benchmark_cases.json"


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


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def merge_dict(base: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def outcomes_by_id(result: dict[str, Any]) -> dict[str, str]:
    return {
        row["criterion_id"]: row["outcome"]
        for row in result.get("results", [])
    }


def run_case(
    case: dict[str, Any],
    defaults: dict[str, Any],
    fixture: dict[str, Any],
) -> dict[str, Any]:
    prompt = case.get("prompt", defaults.get("prompt", ""))
    metadata = merge_dict(
        defaults.get("metadata", {}),
        case.get("metadata"),
    )

    result = evaluate_prompt(
        prompt=prompt,
        metadata=metadata,
        selector_document=fixture.get("selector", {"models": []}),
        guidance_document=fixture.get("guidance", {"guidance": []}),
    )

    actual_outcomes = outcomes_by_id(result)
    expected_gate = case["expected_gate"]
    expected_criteria = case.get("expected", {})

    mismatches = []
    if result.get("release_gate") != expected_gate:
        mismatches.append(
            {
                "type": "release_gate",
                "expected": expected_gate,
                "actual": result.get("release_gate"),
            }
        )

    for criterion_id, expected_outcome in expected_criteria.items():
        actual_outcome = actual_outcomes.get(criterion_id)
        if actual_outcome != expected_outcome:
            mismatches.append(
                {
                    "type": "criterion",
                    "criterion_id": criterion_id,
                    "expected": expected_outcome,
                    "actual": actual_outcome,
                }
            )

    return {
        "id": case["id"],
        "category": case.get("category"),
        "matched": not mismatches,
        "expected_gate": expected_gate,
        "actual_gate": result.get("release_gate"),
        "expected_criteria": expected_criteria,
        "actual_criteria": {
            criterion_id: actual_outcomes.get(criterion_id)
            for criterion_id in expected_criteria
        },
        "mismatches": mismatches,
    }


def build_report(corpus: dict[str, Any]) -> dict[str, Any]:
    defaults = corpus.get("defaults", {})
    fixture = corpus.get("fixture", {})
    case_reports = [
        run_case(case, defaults, fixture)
        for case in corpus.get("cases", [])
    ]

    failed = [x for x in case_reports if not x["matched"]]

    categories: dict[str, dict[str, int]] = {}
    for row in case_reports:
        category = row.get("category") or "uncategorized"
        bucket = categories.setdefault(
            category,
            {"total": 0, "matched": 0, "mismatched": 0},
        )
        bucket["total"] += 1
        if row["matched"]:
            bucket["matched"] += 1
        else:
            bucket["mismatched"] += 1

    return {
        "schema_version": "1.0.0",
        "suite_gate": "pass" if not failed else "fail",
        "corpus_schema_version": corpus.get("schema_version"),
        "corpus_hash": stable_hash(corpus),
        "summary": {
            "total": len(case_reports),
            "matched": len(case_reports) - len(failed),
            "mismatched": len(failed),
        },
        "categories": categories,
        "cases": case_reports,
    }


def update_status(path: str | Path, report: dict[str, Any]) -> None:
    status_path = Path(path)
    if not status_path.exists():
        return
    status = load_json(status_path)
    summary = report["summary"]
    status["benchmark_suite_gate"] = report["suite_gate"]
    status["benchmark_cases"] = summary["total"]
    status["benchmark_matched"] = summary["matched"]
    status["benchmark_mismatched"] = summary["mismatched"]
    status["benchmark_corpus_hash"] = report["corpus_hash"]
    write_json(status_path, status)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    parser.add_argument("--write")
    parser.add_argument("--status")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when any benchmark expectation regresses.",
    )
    args = parser.parse_args()

    corpus = load_json(args.corpus)
    report = build_report(corpus)

    print(
        f"Aurora benchmark: {report['suite_gate']} — "
        f"{report['summary']['matched']}/{report['summary']['total']} matched"
    )

    for case in report["cases"]:
        marker = "OK" if case["matched"] else "FAIL"
        print(
            f"[{marker}] {case['id']}: "
            f"expected={case['expected_gate']} actual={case['actual_gate']}"
        )
        for mismatch in case["mismatches"]:
            print(f"  mismatch: {json.dumps(mismatch, ensure_ascii=False)}")

    if args.write:
        write_json(args.write, report)
    if args.status:
        update_status(args.status, report)

    if args.check and report["suite_gate"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

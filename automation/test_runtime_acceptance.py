import unittest

from automation.runtime_acceptance import (
    build_runtime_document,
    select_runtime_contracts,
    validate_runtime_policy,
)


def evals():
    return {
        "spec_hash": "evalhash",
        "criteria": [
            {"id": "semantic.intent_preservation"},
            {"id": "model.context_budget"},
            {"id": "guidance.provider_alignment"},
            {"id": "tools.policy"},
            {"id": "security.untrusted_data_boundary"},
        ],
    }


def golden():
    return {
        "suite_hash": "goldenhash",
        "validation": {"suite_gate": "pass"},
        "cases": [
            {
                "id": "adapt.cross_provider",
                "operation": "adapt",
                "required_eval_criteria": [
                    "semantic.intent_preservation",
                    "guidance.provider_alignment",
                ],
            },
            {
                "id": "adapt.long_context",
                "operation": "adapt",
                "required_eval_criteria": [
                    "model.context_budget",
                    "semantic.intent_preservation",
                ],
            },
            {
                "id": "agentic.safe_tool_workflow",
                "operation": "agentic",
                "required_eval_criteria": [
                    "tools.policy",
                    "security.untrusted_data_boundary",
                ],
            },
        ],
    }


def policy():
    return {
        "schema_version": "1.0.0",
        "dependency_gate": {
            "require_benchmark_suite_pass": True,
        },
        "routing": {
            "create": {
                "baseline_contracts": [],
                "selectors": [],
                "fallback": "eval_contract_only",
            },
            "optimize": {
                "baseline_contracts": [],
                "selectors": [],
                "fallback": "eval_contract_only",
            },
            "adapt": {
                "baseline_contracts": ["adapt.cross_provider"],
                "selectors": [
                    {
                        "when": ["long context"],
                        "contracts": ["adapt.long_context"],
                    }
                ],
                "fallback": "operation_baseline",
            },
            "agentic": {
                "baseline_contracts": ["agentic.safe_tool_workflow"],
                "selectors": [],
                "fallback": "operation_baseline",
            },
            "multimodal": {
                "baseline_contracts": [],
                "selectors": [],
                "fallback": "eval_contract_only",
            },
        },
        "execution": {"max_repair_passes": 2},
        "runtime_report": {
            "required_fields": [
                "operation",
                "contracts_applied",
                "coverage",
                "eval_release_gate",
                "golden_release_gate",
                "final_release_gate",
                "repair_passes",
                "unresolved",
            ],
            "coverage_values": [
                "exact",
                "partial",
                "operation_baseline",
                "eval_only",
            ],
        },
    }


class RuntimeAcceptanceTests(unittest.TestCase):
    def test_policy_validates(self):
        result = validate_runtime_policy(policy(), evals(), golden())
        self.assertEqual(result["suite_gate"], "pass")
        self.assertEqual(result["summary"]["errors"], 0)

    def test_long_context_adds_specialized_contract(self):
        result = select_runtime_contracts(
            "adapt",
            "Adapt this long context research prompt to another provider.",
            policy(),
            golden(),
        )
        self.assertEqual(result["coverage"], "exact")
        self.assertIn("adapt.cross_provider", result["contracts"])
        self.assertIn("adapt.long_context", result["contracts"])

    def test_operation_baseline_when_selector_does_not_match(self):
        result = select_runtime_contracts(
            "agentic",
            "Build an agent that uses tools safely.",
            policy(),
            golden(),
        )
        self.assertEqual(result["coverage"], "operation_baseline")
        self.assertEqual(
            result["contracts"],
            ["agentic.safe_tool_workflow"],
        )

    def test_unknown_operation_falls_back_to_eval_only(self):
        result = select_runtime_contracts(
            "translate",
            "Translate this prompt.",
            policy(),
            golden(),
        )
        self.assertEqual(result["coverage"], "eval_only")
        self.assertEqual(result["contracts"], [])

    def test_runtime_requires_green_benchmark(self):
        runtime = build_runtime_document(
            policy(),
            evals(),
            golden(),
            {"suite_gate": "fail", "corpus_hash": "benchhash"},
            "2026-10-02T00:00:00Z",
        )
        self.assertFalse(runtime["ready"])
        self.assertIn(
            "benchmark_suite_not_pass",
            runtime["readiness_reasons"],
        )

    def test_runtime_ready_when_dependencies_pass(self):
        runtime = build_runtime_document(
            policy(),
            evals(),
            golden(),
            {"suite_gate": "pass", "corpus_hash": "benchhash"},
            "2026-10-02T00:00:00Z",
        )
        self.assertTrue(runtime["ready"])
        self.assertEqual(runtime["dependencies"]["eval_spec_hash"], "evalhash")
        self.assertEqual(runtime["dependencies"]["golden_suite_hash"], "goldenhash")


if __name__ == "__main__":
    unittest.main()

import unittest

from automation.golden_suite import validate_golden_suite


class GoldenSuiteTests(unittest.TestCase):
    def valid_case(self, operation="create"):
        case = {
            "id": f"{operation}.fixture",
            "operation": operation,
            "input_brief": "Create or transform a prompt with explicit acceptance constraints.",
            "target": {"provider": None, "model": None},
            "invariants": {
                "must_preserve": ["core intent"],
                "must_include_if_applicable": ["output contract"],
                "must_not_add": ["invented requirements"],
            },
            "required_eval_criteria": ["semantic.objective_clarity"],
            "acceptance_tests": ["nominal"],
        }
        if operation == "agentic":
            case["required_eval_criteria"].append("tools.policy")
        if operation == "adapt":
            case["required_eval_criteria"].append("semantic.intent_preservation")
        return case

    def test_valid_suite_passes(self):
        document = {
            "cases": [
                self.valid_case("create"),
                self.valid_case("optimize"),
                self.valid_case("adapt"),
                self.valid_case("agentic"),
                self.valid_case("multimodal"),
            ]
        }
        result = validate_golden_suite(document)
        self.assertEqual(result["suite_gate"], "pass")
        self.assertEqual(result["summary"]["errors"], 0)

    def test_duplicate_id_fails(self):
        a = self.valid_case("create")
        b = self.valid_case("optimize")
        b["id"] = a["id"]
        result = validate_golden_suite({"cases": [a, b]})
        self.assertEqual(result["suite_gate"], "fail")
        self.assertTrue(any("Duplicate case id" in x["message"] for x in result["errors"]))

    def test_agentic_requires_tool_policy(self):
        case = self.valid_case("agentic")
        case["required_eval_criteria"] = ["semantic.objective_clarity"]
        result = validate_golden_suite({"cases": [case]})
        self.assertEqual(result["suite_gate"], "fail")
        self.assertTrue(any("tools.policy" in x["message"] for x in result["errors"]))

    def test_adapt_requires_intent_preservation(self):
        case = self.valid_case("adapt")
        case["required_eval_criteria"] = ["model.verified_target"]
        result = validate_golden_suite({"cases": [case]})
        self.assertEqual(result["suite_gate"], "fail")
        self.assertTrue(any("intent_preservation" in x["message"] for x in result["errors"]))


if __name__ == "__main__":
    unittest.main()

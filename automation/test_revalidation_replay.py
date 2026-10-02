import unittest

from automation.revalidation_replay import assess_revalidation


def policy():
    return {
        "dependency_impacts": {
            "eval_spec_hash": {
                "scope": "eval",
                "prompt_revalidation": True,
                "action": "rerun_eval_contract",
            },
            "golden_suite_hash": {
                "scope": "golden",
                "prompt_revalidation": True,
                "action": "rerun_golden_invariants",
            },
            "runtime_policy_hash": {
                "scope": "runtime",
                "prompt_revalidation": True,
                "action": "rerun_runtime_routing",
            },
            "benchmark_corpus_hash": {
                "scope": "assurance",
                "prompt_revalidation": False,
                "action": "confirm_current_benchmark_pass",
            },
            "traceability_policy_hash": {
                "scope": "traceability",
                "prompt_revalidation": False,
                "action": "refresh_manifest_format_if_needed",
            },
        },
        "escalation": {
            "full_revalidation_if_all_changed": True,
        },
    }


def status(**overrides):
    base = {
        "schema_version": "0.18.0",
        "generated_at": "2026-10-02T20:00:00Z",
        "healthy": True,
        "runtime_acceptance_ready": True,
        "benchmark_suite_gate": "pass",
        "golden_suite_gate": "pass",
        "eval_spec_hash": "eval-a",
        "golden_suite_hash": "golden-a",
        "runtime_policy_hash": "runtime-a",
        "benchmark_corpus_hash": "bench-a",
        "traceability_policy_hash": "trace-a",
    }
    base.update(overrides)
    return base


def runtime(ready=True):
    return {"ready": ready}


def selector(semantic_hash="model-a", verification="verified_official_detail"):
    return {
        "models": [
            {
                "provider_slug": "openai",
                "model_key": "gpt-fixture",
                "verification_state": verification,
                "semantic_hash": semantic_hash,
                "default_policy": "include",
            }
        ]
    }


def guidance(source_hash="guide-a", state="verified_official_guidance"):
    return {
        "guidance": [
            {
                "id": "openai.rule",
                "provider_slug": "openai",
                "verification_state": state,
                "source_hash": source_hash,
            }
        ]
    }


def manifest(
    *,
    semantic_hash="model-a",
    prompt_fingerprint=None,
    deps=None,
    guidance_hash="guide-a",
):
    dependencies = {
        "eval_spec_hash": "eval-a",
        "golden_suite_hash": "golden-a",
        "runtime_policy_hash": "runtime-a",
        "benchmark_corpus_hash": "bench-a",
        "traceability_policy_hash": "trace-a",
    }
    if deps:
        dependencies.update(deps)
    doc = {
        "schema_version": "1.1.0",
        "manifest_id": "vm-old",
        "aurora_version": "0.50.0",
        "live_data_version": "0.16.0",
        "validated_at": "2026-10-01T10:00:00Z",
        "operation": "adapt",
        "target": {
            "provider_slug": "openai",
            "model_key": "gpt-fixture",
            "verification_state": "verified_official_detail",
            "semantic_hash": semantic_hash,
        },
        "dependencies": dependencies,
        "contracts_applied": ["adapt.cross_provider"],
        "guidance_applied": [
            {
                "id": "openai.rule",
                "provider_slug": "openai",
                "verification_state": "verified_official_guidance",
                "source_hash": guidance_hash,
            }
        ],
        "release": {
            "eval_release_gate": "PASS",
            "golden_release_gate": "PASS",
            "final_release_gate": "PASS",
        },
        "repair_passes": 0,
        "unresolved": [],
    }
    if prompt_fingerprint:
        doc["prompt_fingerprint_sha256"] = prompt_fingerprint
    return doc


class ReplayTests(unittest.TestCase):
    def run_replay(self, source=None, **kwargs):
        return assess_revalidation(
            manifest=source or manifest(),
            current_status=kwargs.pop("current_status", status()),
            current_runtime=kwargs.pop("current_runtime", runtime()),
            selector_document=kwargs.pop("selector_document", selector()),
            guidance_document=kwargs.pop("guidance_document", guidance()),
            policy=policy(),
            assessed_at="2026-10-02T20:00:00Z",
            **kwargs,
        )

    def test_unchanged_environment_is_current(self):
        result = self.run_replay()
        self.assertEqual(result["status"], "current")
        self.assertFalse(result["requires_prompt_content"])
        self.assertIn("model:semantic_facts", result["reusable_results"])
        self.assertIn("guidance:openai.rule", result["reusable_results"])

    def test_version_bump_alone_does_not_invalidate(self):
        source = manifest()
        source["aurora_version"] = "0.49.0"
        source["live_data_version"] = "0.15.0"
        result = self.run_replay(source=source)
        self.assertEqual(result["status"], "current")

    def test_eval_change_requires_selective_revalidation(self):
        result = self.run_replay(
            current_status=status(eval_spec_hash="eval-b")
        )
        self.assertEqual(
            result["status"],
            "selective_revalidation_required",
        )
        self.assertIn("eval", result["impacted_scopes"])
        self.assertTrue(result["requires_prompt_content"])

    def test_all_core_contracts_changed_require_full_revalidation(self):
        result = self.run_replay(
            current_status=status(
                eval_spec_hash="eval-b",
                golden_suite_hash="golden-b",
                runtime_policy_hash="runtime-b",
            )
        )
        self.assertEqual(
            result["status"],
            "full_revalidation_required",
        )
        self.assertIn(
            "rerun_full_runtime_acceptance",
            result["required_actions"],
        )

    def test_benchmark_hash_change_alone_keeps_validation_current(self):
        result = self.run_replay(
            current_status=status(benchmark_corpus_hash="bench-b")
        )
        self.assertEqual(result["status"], "current")
        self.assertTrue(result["summary"]["environment_only_changes"])
        self.assertFalse(result["requires_prompt_content"])

    def test_model_semantics_change_requires_model_recheck(self):
        result = self.run_replay(
            selector_document=selector(semantic_hash="model-b")
        )
        self.assertEqual(
            result["status"],
            "selective_revalidation_required",
        )
        self.assertIn("model", result["impacted_scopes"])
        self.assertIn(
            "rerun_model_compatibility",
            result["required_actions"],
        )

    def test_old_manifest_without_semantic_hash_is_partial(self):
        source = manifest()
        source["target"].pop("semantic_hash")
        result = self.run_replay(source=source)
        self.assertEqual(
            result["status"],
            "selective_revalidation_required",
        )
        self.assertTrue(
            any(
                x["type"] == "historical_model_semantic_hash_missing"
                for x in result["changes"]
            )
        )

    def test_guidance_source_change_requires_alignment_recheck(self):
        result = self.run_replay(
            guidance_document=guidance(source_hash="guide-b")
        )
        self.assertEqual(
            result["status"],
            "selective_revalidation_required",
        )
        self.assertIn("guidance", result["impacted_scopes"])

    def test_unhealthy_environment_blocks_replay(self):
        result = self.run_replay(
            current_status=status(healthy=False)
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn(
            "registry_unhealthy",
            result["environment"]["blockers"],
        )

    def test_fingerprint_mismatch_requires_full_new_validation(self):
        source = manifest(prompt_fingerprint="a" * 64)
        result = self.run_replay(
            source=source,
            current_prompt_fingerprint="b" * 64,
        )
        self.assertEqual(result["prompt_identity"], "different")
        self.assertEqual(result["status"], "different_prompt")
        self.assertIn(
            "rerun_full_runtime_acceptance",
            result["required_actions"],
        )

    def test_matching_fingerprint_confirms_same_prompt(self):
        source = manifest(prompt_fingerprint="a" * 64)
        result = self.run_replay(
            source=source,
            current_prompt_fingerprint="a" * 64,
        )
        self.assertEqual(result["prompt_identity"], "same")
        self.assertEqual(result["status"], "current")


if __name__ == "__main__":
    unittest.main()

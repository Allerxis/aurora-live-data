import unittest

from automation.manifest_compare import compare_manifests


def manifest(
    *,
    manifest_id="vm_a",
    aurora_version="0.50.0",
    live_data_version="0.16.0",
    model_key="gpt-fixture",
    gate="PASS",
    contracts=None,
    guidance=None,
    repair_passes=0,
    unresolved=None,
    fingerprint=None,
    eval_hash="eval_a",
):
    doc = {
        "schema_version": "1.0.0",
        "manifest_id": manifest_id,
        "aurora_version": aurora_version,
        "live_data_version": live_data_version,
        "validated_at": "2026-10-02T00:00:00Z",
        "operation": "adapt",
        "target": {
            "provider_slug": "openai",
            "model_key": model_key,
            "verification_state": "verified_official_detail",
            "semantic_verified_at": "2026-10-02T00:00:00Z",
            "semantic_source_url": "https://example.com/model",
        },
        "dependencies": {
            "eval_spec_hash": eval_hash,
            "golden_suite_hash": "golden",
            "runtime_policy_hash": "runtime",
            "benchmark_corpus_hash": "benchmark",
            "traceability_policy_hash": "trace",
        },
        "contracts_applied": contracts or ["adapt.cross_provider"],
        "guidance_applied": guidance or [],
        "release": {
            "eval_release_gate": gate,
            "golden_release_gate": gate,
            "final_release_gate": gate,
        },
        "repair_passes": repair_passes,
        "unresolved": unresolved or [],
        "privacy": {
            "prompt_content_included": False,
            "persisted": False,
            "prompt_fingerprint_included": bool(fingerprint),
        },
    }
    if fingerprint:
        doc["prompt_fingerprint_sha256"] = fingerprint
    return doc


class ManifestCompareTests(unittest.TestCase):
    def test_identical_manifest_has_no_material_changes(self):
        a = manifest()
        b = manifest(manifest_id="vm_b")
        result = compare_manifests(a, b)
        self.assertEqual(result["summary"]["change_count"], 0)
        self.assertEqual(
            result["release_transition"]["classification"],
            "unchanged",
        )
        self.assertEqual(result["prompt_identity"], "unknown")

    def test_version_and_dependency_changes_are_reported(self):
        a = manifest()
        b = manifest(
            manifest_id="vm_b",
            aurora_version="0.51.0",
            live_data_version="0.17.0",
            eval_hash="eval_b",
        )
        result = compare_manifests(a, b)
        types = {x["type"] for x in result["changes"]}
        self.assertIn("version_changed", types)
        self.assertIn("dependency_changed", types)
        self.assertGreaterEqual(result["summary"]["version_changes"], 2)

    def test_model_change_is_target_change(self):
        result = compare_manifests(
            manifest(),
            manifest(manifest_id="vm_b", model_key="gpt-other"),
        )
        self.assertTrue(
            any(
                x["type"] == "target_changed"
                and x["path"] == "target.model_key"
                for x in result["changes"]
            )
        )

    def test_contract_added_and_removed(self):
        result = compare_manifests(
            manifest(contracts=["adapt.cross_provider"]),
            manifest(
                manifest_id="vm_b",
                contracts=["adapt.long_context"],
            ),
        )
        types = [x["type"] for x in result["changes"]]
        self.assertIn("contract_added", types)
        self.assertIn("contract_removed", types)

    def test_guidance_revision_change(self):
        before = [{
            "id": "openai.rule",
            "provider_slug": "openai",
            "verification_state": "verified_official_guidance",
            "verified_at": "2026-10-01T00:00:00Z",
            "source_hash": "old",
        }]
        after = [{
            "id": "openai.rule",
            "provider_slug": "openai",
            "verification_state": "verified_official_guidance",
            "verified_at": "2026-10-02T00:00:00Z",
            "source_hash": "new",
        }]
        result = compare_manifests(
            manifest(guidance=before),
            manifest(manifest_id="vm_b", guidance=after),
        )
        self.assertTrue(
            any(
                x["type"] == "guidance_revision_changed"
                for x in result["changes"]
            )
        )

    def test_gate_more_restrictive(self):
        result = compare_manifests(
            manifest(gate="PASS"),
            manifest(manifest_id="vm_b", gate="NEEDS_REVIEW"),
        )
        self.assertEqual(
            result["release_transition"]["classification"],
            "more_restrictive",
        )

    def test_gate_less_restrictive(self):
        result = compare_manifests(
            manifest(gate="FAIL"),
            manifest(manifest_id="vm_b", gate="PASS"),
        )
        self.assertEqual(
            result["release_transition"]["classification"],
            "less_restrictive",
        )

    def test_unresolved_items_diff_by_stable_key(self):
        result = compare_manifests(
            manifest(unresolved=[{"criterion": "model.context_budget"}]),
            manifest(
                manifest_id="vm_b",
                unresolved=[{"criterion": "guidance.provider_alignment"}],
            ),
        )
        types = [x["type"] for x in result["changes"]]
        self.assertIn("unresolved_added", types)
        self.assertIn("unresolved_removed", types)

    def test_fingerprints_are_compared_only_when_both_exist(self):
        a = manifest(fingerprint="a" * 64)
        b = manifest(manifest_id="vm_b", fingerprint="b" * 64)
        result = compare_manifests(a, b)
        self.assertEqual(result["prompt_identity"], "different")
        self.assertTrue(
            any(x["type"] == "fingerprint_changed" for x in result["changes"])
        )

        c = manifest(manifest_id="vm_c")
        result2 = compare_manifests(a, c)
        self.assertEqual(result2["prompt_identity"], "unknown")

    def test_schema_difference_yields_partial_coverage(self):
        a = manifest()
        b = manifest(manifest_id="vm_b")
        b["schema_version"] = "2.0.0"
        result = compare_manifests(a, b)
        self.assertEqual(result["coverage"], "partial")


if __name__ == "__main__":
    unittest.main()

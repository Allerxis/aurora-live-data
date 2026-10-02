import unittest

from automation.validation_manifest import (
    build_traceability_document,
    create_validation_manifest,
    validate_manifest,
)


def policy():
    return {
        "schema_version": "1.0.0",
        "privacy": {
            "persistence_default": "none",
            "prompt_content_allowed_in_manifest": False,
        },
        "manifest_schema": {
            "required_fields": [
                "schema_version",
                "manifest_id",
                "aurora_version",
                "live_data_version",
                "validated_at",
                "operation",
                "target",
                "dependencies",
                "contracts_applied",
                "guidance_applied",
                "release",
                "repair_passes",
                "unresolved",
                "privacy",
            ],
            "operation_values": [
                "create",
                "optimize",
                "adapt",
                "agentic",
                "multimodal",
                "audit",
                "evaluate",
            ],
            "dependency_fields": [
                "eval_spec_hash",
                "golden_suite_hash",
                "runtime_policy_hash",
                "benchmark_corpus_hash",
                "traceability_policy_hash",
            ],
        },
        "provenance": {},
        "behavior": {},
    }


def status():
    return {
        "schema_version": "0.16.0",
        "generated_at": "2026-10-02T00:00:00Z",
        "eval_spec_hash": "evalhash",
        "golden_suite_hash": "goldenhash",
        "runtime_policy_hash": "runtimehash",
        "benchmark_corpus_hash": "benchhash",
        "traceability_policy_hash": "tracehash",
    }


def runtime():
    return {"ready": True}


class ValidationManifestTests(unittest.TestCase):
    def make_manifest(self, **overrides):
        args = {
            "aurora_version": "0.50.0",
            "live_data_status": status(),
            "runtime_document": runtime(),
            "operation": "adapt",
            "target": {
                "provider_slug": "openai",
                "model_key": "gpt-fixture",
                "verification_state": "verified_official_detail",
                "semantic_verified_at": "2026-10-02T00:00:00Z",
                "semantic_source_url": "https://example.com/model",
                "prompt": "this must never survive",
            },
            "contracts_applied": ["adapt.cross_provider"],
            "guidance_applied": [
                {
                    "id": "openai.fixture",
                    "provider_slug": "openai",
                    "verification_state": "verified_official_guidance",
                    "verified_at": "2026-10-02T00:00:00Z",
                    "source_hash": "sourcehash",
                    "prompt_text": "forbidden content",
                }
            ],
            "eval_release_gate": "PASS",
            "golden_release_gate": "PASS",
            "final_release_gate": "PASS",
            "repair_passes": 1,
            "unresolved": [
                {
                    "criterion": "example",
                    "prompt": "forbidden content",
                    "message": "No unresolved issue.",
                }
            ],
            "validated_at": "2026-10-02T12:00:00Z",
        }
        args.update(overrides)
        return create_validation_manifest(**args)

    def test_manifest_excludes_prompt_content_fields(self):
        manifest = self.make_manifest()
        serialized = str(manifest).lower()
        self.assertNotIn("this must never survive", serialized)
        self.assertNotIn("forbidden content", serialized)
        self.assertFalse(manifest["privacy"]["prompt_content_included"])
        self.assertFalse(manifest["privacy"]["persisted"])

    def test_manifest_validates(self):
        manifest = self.make_manifest()
        result = validate_manifest(manifest, policy())
        self.assertEqual(result["suite_gate"], "pass")
        self.assertEqual(result["summary"]["errors"], 0)
        self.assertEqual(result["summary"]["warnings"], 0)

    def test_manifest_id_is_deterministic_for_same_metadata(self):
        a = self.make_manifest()
        b = self.make_manifest()
        self.assertEqual(a["manifest_id"], b["manifest_id"])

    def test_optional_fingerprint_is_local_metadata_only(self):
        digest = "a" * 64
        manifest = self.make_manifest(prompt_fingerprint=digest)
        self.assertEqual(manifest["prompt_fingerprint_sha256"], digest)
        self.assertTrue(manifest["privacy"]["prompt_fingerprint_included"])

    def test_invalid_fingerprint_is_rejected(self):
        with self.assertRaises(ValueError):
            self.make_manifest(prompt_fingerprint="not-a-sha256")

    def test_invalid_release_gate_fails_validation(self):
        manifest = self.make_manifest()
        manifest["release"]["final_release_gate"] = "MAYBE"
        result = validate_manifest(manifest, policy())
        self.assertEqual(result["suite_gate"], "fail")

    def test_persistence_is_warning_not_silent_default(self):
        manifest = self.make_manifest()
        manifest["privacy"]["persisted"] = True
        result = validate_manifest(manifest, policy())
        self.assertEqual(result["suite_gate"], "pass")
        self.assertEqual(result["summary"]["warnings"], 1)

    def test_traceability_document_publishes_policy_not_user_manifests(self):
        doc = build_traceability_document(
            policy=policy(),
            generated_at="2026-10-02T12:00:00Z",
        )
        self.assertTrue(doc["ready"])
        self.assertIn("policy_hash", doc)
        self.assertNotIn("manifests", doc)


if __name__ == "__main__":
    unittest.main()

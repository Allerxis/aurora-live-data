import unittest

from automation.selector_view import build_selector, normalize_usage_state


class SelectorViewTests(unittest.TestCase):
    def model(self, provider, verification="verified_official_detail", lifecycle="unknown", facts=None):
        return {
            "provider_slug": provider,
            "model_key": f"{provider}-model",
            "display_name": f"{provider}-model",
            "verification_state": verification,
            "semantic_verified_at": "2026-10-02T00:00:00Z",
            "semantic_source_url": "https://example.invalid/model",
            "lifecycle_status": lifecycle,
            "present_in_current_sources": True,
            "facts": facts or {},
        }

    def test_retired_is_excluded(self):
        state, policy = normalize_usage_state(
            self.model("anthropic", lifecycle="Retired")
        )
        self.assertEqual(state, "retired")
        self.assertEqual(policy, "exclude")

    def test_google_shutdown_is_warning_not_false_unavailable(self):
        state, policy = normalize_usage_state(
            self.model("google", lifecycle="shutdown_announced")
        )
        self.assertEqual(state, "transition_watch")
        self.assertEqual(policy, "include_with_warning")

    def test_meta_open_weight_is_specialized(self):
        state, policy = normalize_usage_state(
            self.model(
                "meta",
                facts={"distribution": "open_weight"},
            )
        )
        self.assertEqual(state, "open_weight")
        self.assertEqual(policy, "specialized")

    def test_stale_verification_is_not_current(self):
        state, policy = normalize_usage_state(
            self.model(
                "openai",
                verification="verified_official_detail_stale",
            )
        )
        self.assertEqual(state, "stale_verification")
        self.assertEqual(policy, "stale")

    def test_unverified_records_are_not_emitted(self):
        docs = {
            "openai": {
                "models": [
                    self.model("openai", verification="unverified"),
                    self.model("openai", lifecycle="unknown"),
                ]
            }
        }
        out = build_selector(docs, "2026-10-02T00:00:00Z")
        self.assertEqual(len(out["models"]), 1)
        self.assertEqual(out["counts"]["total"], 1)

    def test_google_normalizes_token_limits(self):
        model = self.model(
            "google",
            lifecycle="no_shutdown_announced",
            facts={
                "input_token_limit": 1048576,
                "output_token_limit": 65536,
                "input_types": ["text", "image"],
                "output_types": ["text"],
            },
        )
        out = build_selector(
            {"google": {"models": [model]}},
            "2026-10-02T00:00:00Z",
        )
        record = out["models"][0]
        self.assertEqual(record["context_window_tokens"], 1048576)
        self.assertEqual(record["max_output_tokens"], 65536)
        self.assertEqual(record["default_policy"], "include")


if __name__ == "__main__":
    unittest.main()

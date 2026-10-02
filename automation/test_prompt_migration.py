import unittest

from automation.prompt_migration import plan_migration


def status(healthy=True):
    return {"healthy": healthy}


def selector():
    return {
        "models": [
            {
                "provider_slug": "openai",
                "model_key": "old-model",
                "verification_state": "verified_official_detail",
                "semantic_hash": "oldhash",
                "lifecycle_status": "Retired",
                "usage_state": "retired",
                "default_policy": "exclude",
                "context_window_tokens": 128000,
                "max_output_tokens": 16000,
                "pricing": {
                    "unit": "USD_per_1M_tokens",
                    "input": 3.0,
                    "output": 12.0,
                },
                "modalities": {
                    "states": {
                        "text": "input_and_output",
                        "image": "input_only",
                    }
                },
                "capabilities": {
                    "features": {
                        "structured_outputs": True,
                    },
                    "tools": {
                        "web_search": True,
                    },
                },
            },
            {
                "provider_slug": "openai",
                "model_key": "new-a",
                "verification_state": "verified_official_detail",
                "semantic_hash": "newahash",
                "lifecycle_status": "Active",
                "usage_state": "active",
                "default_policy": "include",
                "context_window_tokens": 400000,
                "max_output_tokens": 128000,
                "pricing": {
                    "unit": "USD_per_1M_tokens",
                    "input": 2.0,
                    "output": 10.0,
                },
                "modalities": {
                    "states": {
                        "text": "input_and_output",
                        "image": "input_only",
                    }
                },
                "capabilities": {
                    "features": {
                        "structured_outputs": True,
                    },
                    "tools": {
                        "web_search": True,
                    },
                },
                "semantic_source_url": "https://example.com/new-a",
            },
            {
                "provider_slug": "openai",
                "model_key": "new-b",
                "verification_state": "verified_official_detail",
                "semantic_hash": "newbhash",
                "lifecycle_status": "Active",
                "usage_state": "active",
                "default_policy": "include",
                "context_window_tokens": 100000,
                "max_output_tokens": 32000,
                "pricing": {
                    "unit": "USD_per_1M_tokens",
                    "input": 1.0,
                    "output": 5.0,
                },
                "modalities": {
                    "states": {
                        "text": "input_and_output",
                    }
                },
                "capabilities": {
                    "features": {
                        "structured_outputs": True,
                    },
                    "tools": {
                        "web_search": False,
                    },
                },
                "semantic_source_url": "https://example.com/new-b",
            },
            {
                "provider_slug": "anthropic",
                "model_key": "cross-provider",
                "verification_state": "verified_official_detail",
                "semantic_hash": "crosshash",
                "lifecycle_status": "Active",
                "usage_state": "active",
                "default_policy": "include",
                "context_window_tokens": 1000000,
                "max_output_tokens": 128000,
                "pricing": {
                    "unit": "USD_per_1M_tokens",
                    "input": 2.0,
                    "output": 10.0,
                },
                "modalities": {
                    "raw": "Text and images → text",
                },
                "capabilities": {},
                "semantic_source_url": "https://example.com/cross",
            },
            {
                "provider_slug": "meta",
                "model_key": "open-weight",
                "verification_state": "verified_official_detail",
                "semantic_hash": "metahash",
                "lifecycle_status": "Active",
                "usage_state": "open_weight",
                "default_policy": "specialized",
                "context_window_tokens": 1000000,
                "max_output_tokens": 128000,
                "pricing": None,
                "modalities": {
                    "input": ["text"],
                    "output": ["text"],
                },
                "capabilities": {},
            },
        ]
    }


def complete_requirements():
    return {
        "requirements_complete": True,
        "required_context_tokens": 200000,
        "required_output_tokens": 64000,
        "required_capabilities": [
            "capabilities.features.structured_outputs",
            "capabilities.tools.web_search",
        ],
        "required_modalities": {
            "input": ["text", "image"],
            "output": ["text"],
        },
        "max_input_price_per_1m": 3.0,
        "max_output_price_per_1m": 12.0,
    }


class PromptMigrationTests(unittest.TestCase):
    def test_retired_source_with_unique_compatible_target_is_ready(self):
        result = plan_migration(
            selector_document=selector(),
            current_status=status(),
            source_provider="openai",
            source_model="old-model",
            requirements=complete_requirements(),
        )
        self.assertEqual(result["status"], "plan_ready")
        self.assertEqual(
            result["selected_target"]["model_key"],
            "new-a",
        )
        self.assertEqual(result["trigger"], "source_excluded")

    def test_current_source_does_not_migrate_without_request(self):
        result = plan_migration(
            selector_document=selector(),
            current_status=status(),
            source_provider="openai",
            source_model="new-a",
            requirements=complete_requirements(),
        )
        self.assertEqual(result["status"], "not_needed")
        self.assertEqual(
            result["selected_target"]["model_key"],
            "new-a",
        )

    def test_explicit_request_can_migrate_current_source(self):
        req = complete_requirements()
        req["required_context_tokens"] = 50000
        req["required_output_tokens"] = 16000
        req["required_capabilities"] = [
            "capabilities.features.structured_outputs",
        ]
        req["required_modalities"] = {
            "input": ["text"],
            "output": ["text"],
        }
        result = plan_migration(
            selector_document=selector(),
            current_status=status(),
            source_provider="openai",
            source_model="new-a",
            requirements=req,
            explicit_request=True,
        )
        self.assertEqual(result["status"], "plan_ready")
        self.assertEqual(
            result["selected_target"]["model_key"],
            "new-b",
        )

    def test_multiple_compatible_candidates_needs_review(self):
        req = {
            "requirements_complete": True,
            "required_context_tokens": 50000,
            "required_output_tokens": 16000,
            "required_capabilities": [
                "capabilities.features.structured_outputs",
            ],
            "required_modalities": {
                "input": ["text"],
                "output": ["text"],
            },
        }
        result = plan_migration(
            selector_document=selector(),
            current_status=status(),
            source_provider="openai",
            source_model="old-model",
            requirements=req,
        )
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(
            result["diagnostics"]["same_provider_eligible_count"],
            2,
        )
        self.assertIn(
            "choose_between_eligible_candidates",
            result["required_actions"],
        )

    def test_incomplete_requirements_never_auto_select(self):
        result = plan_migration(
            selector_document=selector(),
            current_status=status(),
            source_provider="openai",
            source_model="old-model",
            requirements={
                "requirements_complete": False,
                "required_context_tokens": 200000,
            },
        )
        self.assertEqual(result["status"], "needs_review")
        self.assertIn(
            "establish_missing_requirements",
            result["required_actions"],
        )

    def test_unsupported_required_capability_filters_candidate(self):
        req = complete_requirements()
        req["required_context_tokens"] = 50000
        req["required_output_tokens"] = 16000
        result = plan_migration(
            selector_document=selector(),
            current_status=status(),
            source_provider="openai",
            source_model="old-model",
            requirements=req,
        )
        self.assertEqual(result["status"], "plan_ready")
        self.assertEqual(
            [x["model_key"] for x in result["eligible_candidates"]],
            ["new-a"],
        )

    def test_unknown_modality_does_not_silently_pass(self):
        req = complete_requirements()
        result = plan_migration(
            selector_document=selector(),
            current_status=status(),
            source_provider="openai",
            source_model="old-model",
            requirements=req,
            allow_cross_provider=True,
        )
        self.assertNotIn(
            "cross-provider",
            [x["model_key"] for x in result["eligible_candidates"]],
        )

    def test_cross_provider_requires_authorization(self):
        custom = selector()
        custom["models"] = [
            x for x in custom["models"]
            if x["model_key"] not in {"new-a", "new-b"}
        ]
        req = {
            "requirements_complete": True,
            "required_context_tokens": 100000,
            "required_output_tokens": 64000,
            "required_capabilities": [],
            "required_modalities": {},
        }
        result = plan_migration(
            selector_document=custom,
            current_status=status(),
            source_provider="openai",
            source_model="old-model",
            requirements=req,
            allow_cross_provider=False,
        )
        self.assertEqual(result["status"], "needs_review")
        self.assertIn(
            "authorize_cross_provider_if_desired",
            result["required_actions"],
        )

    def test_specialized_candidate_requires_explicit_fit(self):
        custom = selector()
        custom["models"] = [
            x for x in custom["models"]
            if x["model_key"] in {"old-model", "open-weight"}
        ]
        req = {
            "requirements_complete": True,
            "required_context_tokens": 100000,
            "required_output_tokens": 64000,
            "required_capabilities": [],
            "required_modalities": {
                "input": ["text"],
                "output": ["text"],
            },
        }
        result = plan_migration(
            selector_document=custom,
            current_status=status(),
            source_provider="openai",
            source_model="old-model",
            requirements=req,
            allow_cross_provider=True,
            allow_specialized=False,
        )
        self.assertEqual(result["status"], "needs_review")

        result2 = plan_migration(
            selector_document=custom,
            current_status=status(),
            source_provider="openai",
            source_model="old-model",
            requirements=req,
            allow_cross_provider=True,
            allow_specialized=True,
        )
        self.assertEqual(result2["status"], "plan_ready")
        self.assertEqual(
            result2["selected_target"]["model_key"],
            "open-weight",
        )

    def test_documented_replacement_can_resolve_tie(self):
        req = {
            "requirements_complete": True,
            "required_context_tokens": 50000,
            "required_output_tokens": 16000,
            "required_capabilities": [
                "capabilities.features.structured_outputs",
            ],
            "required_modalities": {
                "input": ["text"],
                "output": ["text"],
            },
        }
        result = plan_migration(
            selector_document=selector(),
            current_status=status(),
            source_provider="openai",
            source_model="old-model",
            requirements=req,
            documented_replacement={
                "provider_slug": "openai",
                "model_key": "new-b",
            },
        )
        self.assertEqual(result["status"], "plan_ready")
        self.assertEqual(
            result["selected_target"]["model_key"],
            "new-b",
        )

    def test_unhealthy_registry_blocks_plan(self):
        result = plan_migration(
            selector_document=selector(),
            current_status=status(healthy=False),
            source_provider="openai",
            source_model="old-model",
            requirements=complete_requirements(),
        )
        self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()

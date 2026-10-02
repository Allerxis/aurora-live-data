import unittest

from automation.adapters import discover


class AdapterTests(unittest.TestCase):
    def keys(self, provider, text):
        return {x.model_key for x in discover(provider, text)}

    def test_openai_ids(self):
        keys = self.keys("openai", "GPT-6 Astra Model ID gpt-6-astra and gpt-6.1-sol.")
        self.assertIn("gpt-6-astra", keys)
        self.assertIn("gpt-6.1-sol", keys)

    def test_anthropic_excludes_products(self):
        keys = self.keys(
            "anthropic",
            "claude-code claude-api claude-sonnet-5 claude-opus-5-5 claude-haiku-4-5-20251001"
        )
        self.assertIn("claude-sonnet-5", keys)
        self.assertIn("claude-opus-5-5", keys)
        self.assertIn("claude-haiku-4-5-20251001", keys)
        self.assertNotIn("claude-code", keys)
        self.assertNotIn("claude-api", keys)

    def test_anthropic_legacy_ids(self):
        keys = self.keys(
            "anthropic",
            "claude-opus-5-5 claude-3-7-sonnet-20250219 claude-3-haiku-20240307 "
            "claude-2.1 claude-mythos-preview"
        )
        self.assertIn("claude-opus-5-5", keys)
        self.assertIn("claude-3-7-sonnet-20250219", keys)
        self.assertIn("claude-3-haiku-20240307", keys)
        self.assertIn("claude-2.1", keys)
        self.assertIn("claude-mythos-preview", keys)

    def test_mistral_excludes_docs_artifacts(self):
        keys = self.keys(
            "mistral",
            "codestral-2405 codestral-code-interpreter-js-readme mistral-medium-2508 "
            "mistral-small-latest devstral-small-2512"
        )
        self.assertIn("codestral-2405", keys)
        self.assertIn("mistral-medium-2508", keys)
        self.assertIn("mistral-small-latest", keys)
        self.assertIn("devstral-small-2512", keys)
        self.assertNotIn("codestral-code-interpreter-js-readme", keys)

    def test_meta_names(self):
        keys = self.keys("meta", "Llama 4 Scout Llama 4 Maverick Llama Guard 4")
        self.assertIn("llama-4-scout", keys)
        self.assertIn("llama-4-maverick", keys)
        self.assertIn("llama-guard-4", keys)


if __name__ == "__main__":
    unittest.main()

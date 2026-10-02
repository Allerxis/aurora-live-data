import unittest

from automation.mistral_semantic import (
    extract_mistral_detail_urls,
    infer_mistral_pricing_key,
    parse_mistral_model_page,
    parse_mistral_pricing_page,
)


class MistralSemanticParserTests(unittest.TestCase):
    def test_extracts_model_links(self):
        raw = """
        <a href="/models/mistral-small-4-0-26-03">Mistral Small 4</a>
        <a href="/fr/models/mistral-medium-3-5-26-04">Mistral Medium 3.5</a>
        <a href="/models">Models</a>
        """
        urls = extract_mistral_detail_urls(raw)
        self.assertIn(
            "https://docs.mistral.ai/models/mistral-small-4-0-26-03",
            urls,
        )
        self.assertIn(
            "https://docs.mistral.ai/models/mistral-medium-3-5-26-04",
            urls,
        )
        self.assertEqual(len(urls), 2)

    def test_model_card(self):
        text = """
        Navigation Models Pricing Model lifecycle policy Labs Prompting Sampling
        March 16, 2026
        GA Apache 2.0 v26.03
        Mistral Small 4
        Powerful hybrid model.
        mistral-small-2603
        Speed Performance Modalities Context i 256k
        Price i $0.15 /M Tokens $0.6 /M Tokens
        FEATURES WEIGHTS
        Features
        Chat completion /v1/chat/completions
        Function calling /v1/chat/completions /v1/conversations
        Agents & conversations /v1/agents /v1/conversations
        Built-in tools /v1/agents /v1/conversations
        Structured outputs /v1/chat/completions /v1/conversations
        Predicted outputs /v1/chat/completions /v1/conversations
        Document QnA /v1/chat/completions /v1/conversations
        Prefix /v1/chat/completions /v1/conversations
        Batch /v1/batch
        Other Models
        """
        facts = parse_mistral_model_page(
            "mistral-small-2603",
            text,
            "https://docs.mistral.ai/models/mistral-small-4-0-26-03",
        )
        self.assertIsNotNone(facts)
        self.assertEqual(facts["context_window_tokens"], 256_000)
        self.assertEqual(facts["release_stage"], "GA")
        self.assertEqual(facts["version"], "26.03")
        self.assertEqual(facts["released"], "2026-03-16")
        self.assertTrue(facts["features"]["function_calling"])
        self.assertTrue(facts["features"]["structured_outputs"])
        self.assertIn("/v1/batch", facts["endpoints"])
        self.assertEqual(
            facts["displayed_price_values_usd_per_1M_tokens"],
            [0.15, 0.6],
        )
        self.assertEqual(
            infer_mistral_pricing_key("mistral-small-2603", text),
            "mistral small 4",
        )

    def test_rejects_wrong_id(self):
        facts = parse_mistral_model_page(
            "mistral-small-2603",
            "Mistral Medium 3.5 mistral-medium-3-5 Context 256k",
            "https://docs.mistral.ai/models/mistral-medium-3-5-26-04",
        )
        self.assertIsNone(facts)

    def test_pricing_table(self):
        text = """
        Model Input Cached input Output
        Mistral Large 3 $0.5 $0.05 $1.5
        Mistral Medium 3.5 $1.5 $0.15 $7.5
        Mistral Small 4 ↗ $0.15 $0.015 $0.6
        Ministral 3 14B $0.2 $0.02 $0.2
        Codestral $0.3 $0.03 $0.9
        """
        rows = parse_mistral_pricing_page(
            text,
            "https://docs.mistral.ai/inference/pricing",
        )
        self.assertEqual(rows["mistral small 4"]["input"], 0.15)
        self.assertEqual(rows["mistral small 4"]["cached_input"], 0.015)
        self.assertEqual(rows["mistral small 4"]["output"], 0.6)
        self.assertEqual(rows["mistral medium 3.5"]["output"], 7.5)
        self.assertEqual(rows["codestral"]["cached_input"], 0.03)


if __name__ == "__main__":
    unittest.main()

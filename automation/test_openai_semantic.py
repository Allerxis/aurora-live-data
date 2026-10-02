import unittest

from automation.openai_semantic import parse_openai_model_page


class OpenAISemanticParserTests(unittest.TestCase):
    def test_parses_verified_fields(self):
        text = """
        GPT-6 Astra gpt-6-astra reasoning.effort supports low, medium, high, xhigh, and max.
        1,050,000 context window
        128,000 max output tokens
        Apr 30, 2026 knowledge cutoff

        Text tokens Per 1M tokens
        Input $10.00
        Cached input $1.00
        Cache writes $12.50
        Output $50.00

        Modalities
        Text Input and output
        Image Input only
        Audio Not supported
        Video Not supported

        Endpoints
        Responses v1/responses
        Chat Completions v1/chat/completions
        Batch v1/batch

        Features
        Streaming Supported
        Function calling Supported
        Structured outputs Supported
        Fine-tuning Not supported

        Tools
        Web search Supported
        File search Supported
        Image generation Supported
        Code interpreter Supported
        Hosted shell Supported
        Apply patch Supported
        Skills Supported
        Computer use Supported
        MCP Supported
        Tool search Supported

        Snapshots
        """

        facts = parse_openai_model_page(
            "gpt-6-astra",
            text,
            "https://developers.openai.com/api/docs/models/gpt-6-astra",
        )
        self.assertIsNotNone(facts)
        self.assertEqual(facts["context_window_tokens"], 1_050_000)
        self.assertEqual(facts["max_output_tokens"], 128_000)
        self.assertEqual(facts["knowledge_cutoff"], "2026-04-30")
        self.assertEqual(facts["pricing"]["input"], 10.0)
        self.assertEqual(facts["pricing"]["cached_input"], 1.0)
        self.assertEqual(facts["pricing"]["cache_writes"], 12.5)
        self.assertEqual(facts["pricing"]["output"], 50.0)
        self.assertEqual(facts["modalities"]["text"], "input_and_output")
        self.assertEqual(facts["modalities"]["image"], "input_only")
        self.assertFalse(facts["features"]["fine_tuning"])
        self.assertTrue(facts["features"]["structured_outputs"])
        self.assertTrue(facts["tools"]["mcp"])
        self.assertIn("v1/responses", facts["endpoints"])
        self.assertEqual(
            facts["reasoning_efforts"],
            ["low", "medium", "high", "xhigh", "max"],
        )

    def test_rejects_wrong_model_page(self):
        facts = parse_openai_model_page(
            "gpt-6-astra",
            "GPT-6 Luna gpt-6-luna 400,000 context window 128,000 max output tokens",
            "https://developers.openai.com/api/docs/models/gpt-6-luna",
        )
        self.assertIsNone(facts)

    def test_rejects_page_without_core_specs(self):
        facts = parse_openai_model_page(
            "gpt-6-astra",
            "GPT-6 Astra gpt-6-astra",
            "https://developers.openai.com/api/docs/models/gpt-6-astra",
        )
        self.assertIsNone(facts)


if __name__ == "__main__":
    unittest.main()

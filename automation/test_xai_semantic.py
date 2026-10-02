import unittest

from automation.xai_semantic import (
    parse_xai_knowledge_cutoffs,
    parse_xai_model_page,
    parse_xai_retirement_page,
)


class XAISemanticParserTests(unittest.TestCase):
    def test_model_detail(self):
        text = """
        Grok 4.7 grok-4.7
        At a glance
        Modalities Text, Image Text
        Context window 500,000
        Pricing $2.00 $6.00
        Capabilities
        Function calling Connect the xAI model to external tools and systems.
        Structured outputs Return responses in specific, organized formats.
        Reasoning The model can think before responding.
        Pricing
        Input Tokens $2.00/ 1M tokens
        Cached tokens $0.50/ 1M tokens
        Output Tokens $6.00/ 1M tokens
        Details
        Model name grok-4.7
        Region us-east-1
        Batch API Not supported
        Reasoning efforts Supported low, medium, high, xhigh
        Default high
        Rate limits
        """
        facts = parse_xai_model_page(
            "grok-4.7",
            text,
            "https://docs.x.ai/developers/models/grok-4.7",
        )
        self.assertIsNotNone(facts)
        self.assertEqual(facts["context_window_tokens"], 500_000)
        self.assertEqual(facts["pricing"]["input"], 2.0)
        self.assertEqual(facts["pricing"]["cached_input"], 0.5)
        self.assertEqual(facts["pricing"]["output"], 6.0)
        self.assertTrue(facts["capabilities"]["function_calling"])
        self.assertTrue(facts["capabilities"]["structured_outputs"])
        self.assertFalse(facts["batch_api"])
        self.assertEqual(
            facts["reasoning"]["efforts"],
            ["low", "medium", "high", "xhigh"],
        )
        self.assertEqual(facts["reasoning"]["default"], "high")

    def test_rejects_wrong_model(self):
        facts = parse_xai_model_page(
            "grok-4.7",
            "Model name grok-4.6 Context window 500,000",
            "https://docs.x.ai/developers/models/grok-4.6",
        )
        self.assertIsNone(facts)

    def test_knowledge_cutoff(self):
        rows = parse_xai_knowledge_cutoffs(
            "The knowledge cut-off date of Grok 4.7 is May 2026.",
            "https://docs.x.ai/developers/models",
        )
        self.assertEqual(rows["grok-4.7"]["knowledge_cutoff"], "2026-05")

    def test_retirement_redirect(self):
        text = """
        Effective May 15, 2026 at 12:00 PM PT, the following models will be retired:
        grok-4-1-fast-reasoning
        grok-4-fast-non-reasoning
        grok-4-0709
        grok-3
        Recommended Replacements
        grok-4-1-fast-reasoning grok-4.3 with low reasoning effort
        grok-4-fast-non-reasoning grok-4.3 with none reasoning effort
        grok-4-0709 grok-4.3 with low reasoning effort
        grok-3 grok-4.3 with none reasoning effort
        """
        rows = parse_xai_retirement_page(
            text,
            "https://docs.x.ai/developers/migration/may-15-retirement",
        )
        self.assertEqual(rows["grok-3"]["status"], "retired_redirect")
        self.assertEqual(rows["grok-3"]["effective_date"], "2026-05-15")
        self.assertEqual(rows["grok-3"]["redirect_target"], "grok-4.3")
        self.assertEqual(
            rows["grok-4-1-fast-reasoning"]["redirect_reasoning_effort"],
            "low",
        )


if __name__ == "__main__":
    unittest.main()

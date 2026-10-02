import unittest

from automation.anthropic_semantic import (
    detail_slug_candidates,
    parse_anthropic_lifecycle_page,
    parse_anthropic_model_page,
)


class AnthropicSemanticParserTests(unittest.TestCase):
    def test_detail_slug_candidates(self):
        self.assertEqual(
            detail_slug_candidates("claude-opus-5-5"),
            ["opus-5-5"],
        )
        self.assertEqual(
            detail_slug_candidates("claude-haiku-4-5-20251001"),
            ["haiku-4-5-20251001", "haiku-4-5"],
        )

    def test_parses_model_page(self):
        text = """
        Claude Opus 5.5 Latest claude-opus-5-5
        Context window 1M tokens
        Max output 128K tokens
        Specifications
        Model IDs
        Claude API claude-opus-5-5
        Amazon Bedrock anthropic.claude-opus-5-5
        Google Cloud claude-opus-5-5
        Microsoft Foundry claude-opus-5-5
        Claude Platform on AWS claude-opus-5-5
        Pricing
        Input $4 / MTok
        Output $20 / MTok
        5m cache write $5 / MTok
        1h cache write $8 / MTok
        Cache read $0.20 / MTok
        Capabilities
        Context window 1M tokens
        Max output 128K tokens
        Max output (Batch API, beta) 300K tokens
        Thinking Adaptive (always on)
        Default effort medium
        Comparative latency Moderate
        Input → output Text and images → text
        Reliable knowledge cutoff Jun 2026
        Training data cutoff Jun 2026
        Availability
        Status Active (latest)
        Released September 22, 2026
        Retirement Not sooner than September 22, 2027
        Platforms Claude API Amazon Bedrock Google Cloud Microsoft Foundry Claude Platform on AWS
        Good to know
        """

        facts = parse_anthropic_model_page(
            "claude-opus-5-5",
            text,
            "https://platform.claude.com/docs/en/models/opus-5-5/overview",
        )
        self.assertIsNotNone(facts)
        self.assertEqual(facts["context_window_tokens"], 1_000_000)
        self.assertEqual(facts["max_output_tokens"], 128_000)
        self.assertEqual(facts["max_output_batch_tokens"], 300_000)
        self.assertEqual(facts["pricing"]["input"], 4.0)
        self.assertEqual(facts["pricing"]["output"], 20.0)
        self.assertEqual(facts["pricing"]["cache_read"], 0.2)
        self.assertEqual(facts["thinking"], "Adaptive (always on)")
        self.assertEqual(facts["default_effort"], "medium")
        self.assertEqual(facts["reliable_knowledge_cutoff"], "2026-06")
        self.assertEqual(facts["training_data_cutoff"], "2026-06")
        self.assertEqual(facts["lifecycle"]["status"], "Active (latest)")
        self.assertEqual(facts["lifecycle"]["released"], "2026-09-22")
        self.assertIn("Claude API", facts["platforms"])
        self.assertEqual(
            facts["platform_ids"]["amazon_bedrock"],
            "anthropic.claude-opus-5-5",
        )

    def test_rejects_wrong_model(self):
        facts = parse_anthropic_model_page(
            "claude-opus-5-5",
            "claude-sonnet-5-5 Context window 1M tokens Max output 128K tokens",
            "https://platform.claude.com/docs/en/models/sonnet-5-5/overview",
        )
        self.assertIsNone(facts)

    def test_lifecycle_table(self):
        text = """
        API model name Current state Deprecated Tentative retirement date
        claude-fable-5-1 Active N/A Not sooner than September 1, 2027
        claude-sonnet-4-5-20250929 Deprecated September 30, 2026 November 30, 2026
        claude-opus-4-1-20250805 Retired June 5, 2026 August 5, 2026
        """
        rows = parse_anthropic_lifecycle_page(
            text,
            "https://platform.claude.com/docs/en/about-claude/model-deprecations",
        )
        self.assertEqual(rows["claude-fable-5-1"]["status"], "Active")
        self.assertIsNone(rows["claude-fable-5-1"]["deprecated_at"])
        self.assertEqual(
            rows["claude-sonnet-4-5-20250929"]["deprecated_at"],
            "2026-09-30",
        )
        self.assertEqual(
            rows["claude-opus-4-1-20250805"]["status"],
            "Retired",
        )
        self.assertTrue(
            rows["claude-opus-4-1-20250805"]["partner_platform_schedule_may_differ"]
        )


if __name__ == "__main__":
    unittest.main()

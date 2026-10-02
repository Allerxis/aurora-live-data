import unittest

from automation.google_semantic import (
    parse_google_lifecycle_page,
    parse_google_model_page,
)


class GoogleSemanticParserTests(unittest.TestCase):
    def test_parses_gemini_detail_page(self):
        text = """
        Gemini 3.8 Flash
        gemini-3.8-flash
        Property Description
        Model code gemini-3.8-flash
        Supported data types Inputs Text, Image, Video, Audio, and PDF Output Text
        Token limits Input token limit 1,048,576 Output token limit 65,536
        Capabilities
        Audio generation Not supported
        Caching Supported
        Code execution Supported
        Computer use Supported (Preview)
        File search Supported
        Function calling Supported
        Grounding with Google Maps Supported
        Image generation Not supported
        Live API Not supported
        Search grounding Supported
        Structured outputs Supported
        Thinking Supported (low, medium, high)
        URL context Supported
        Consumption options
        Batch API Supported
        Flex inference Supported
        Priority inference Supported
        Versions Stable: gemini-3.8-flash
        Latest update September 2026
        """
        facts = parse_google_model_page(
            "gemini-3.8-flash",
            text,
            "https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash",
        )
        self.assertIsNotNone(facts)
        self.assertEqual(facts["input_token_limit"], 1_048_576)
        self.assertEqual(facts["output_token_limit"], 65_536)
        self.assertIn("text", facts["input_types"])
        self.assertIn("pdf", facts["input_types"])
        self.assertEqual(facts["output_types"], ["text"])
        self.assertEqual(facts["capabilities"]["computer_use"], "Supported (Preview)")
        self.assertEqual(facts["capabilities"]["image_generation"], "Not supported")
        self.assertEqual(facts["consumption_options"]["batch_api"], "Supported")
        self.assertEqual(facts["versions"]["stable"], "gemini-3.8-flash")
        self.assertEqual(facts["latest_update"], "2026-09")

    def test_parses_veo_page(self):
        text = """
        Veo 3.1
        veo-3.1-generate-preview
        Model code Gemini API veo-3.1-generate-preview veo-3.1-fast-generate-preview
        Supported data types Input Text, Image Output Video with audio
        Limits Text input 1,024 tokens Output video 1
        Latest update January 2026
        """
        facts = parse_google_model_page(
            "veo-3.1-generate-preview",
            text,
            "https://ai.google.dev/gemini-api/docs/models/veo-3.1-generate-preview",
        )
        self.assertIsNotNone(facts)
        self.assertIn("veo-3.1-fast-generate-preview", facts["model_codes"])
        self.assertEqual(facts["video_output_count"], 1)
        self.assertEqual(facts["latest_update"], "2026-01")

    def test_rejects_wrong_model(self):
        facts = parse_google_model_page(
            "gemini-3.8-flash",
            "Model code gemini-3.7-flash Supported data types Inputs Text Output Text",
            "https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash",
        )
        self.assertIsNone(facts)

    def test_lifecycle_table(self):
        text = """
        gemini-3.8-flash September 2, 2026 No shutdown date announced
        gemini-3.1-flash-lite May 7, 2026 May 7, 2027 gemini-3.5-flash-lite
        gemini-2.0-flash February 5, 2025 June 1, 2026 gemini-3.6-flash
        """
        rows = parse_google_lifecycle_page(
            text,
            "https://ai.google.dev/gemini-api/docs/deprecations",
        )
        self.assertFalse(rows["gemini-3.8-flash"]["shutdown_announced"])
        self.assertEqual(rows["gemini-3.8-flash"]["release_date"], "2026-09-02")
        self.assertEqual(rows["gemini-3.1-flash-lite"]["shutdown"], "2027-05-07")
        self.assertEqual(
            rows["gemini-3.1-flash-lite"]["recommended_replacement"],
            "gemini-3.5-flash-lite",
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from automation.meta_semantic import parse_llama4_model_card


class MetaSemanticParserTests(unittest.TestCase):
    def test_llama4_model_card(self):
        markdown = """
Model Name | Training Data | Params | Input modalities | Output modalities | Context length | Token count | Knowledge cutoff
--- | --- | --- | --- | --- | --- | --- | ---
Llama 4 Scout (17Bx16E) | Data | 17B (Activated) 109B (Total) | Multilingual text and image | Multilingual text and code | 10M | ~40T | August 2024
Llama 4 Maverick (17Bx128E) | Data | 17B (Activated) 400B (Total) | Multilingual text and image | Multilingual text and code | 1M | ~22T | August 2024

Model Release Date: April 5, 2025
Data Freshness: The pretraining data has a cutoff of August 2024.
"""
        rows = parse_llama4_model_card(
            markdown,
            "https://raw.githubusercontent.com/meta-llama/llama-models/main/models/llama4/MODEL_CARD.md",
        )
        scout = rows["llama-4-scout"]
        maverick = rows["llama-4-maverick"]

        self.assertEqual(scout["context_window_tokens"], 10_000_000)
        self.assertEqual(maverick["context_window_tokens"], 1_000_000)
        self.assertEqual(scout["active_parameters"], "17B")
        self.assertEqual(scout["total_parameters"], "109B")
        self.assertEqual(maverick["total_parameters"], "400B")
        self.assertEqual(scout["input_modalities"], ["text", "image"])
        self.assertEqual(scout["output_modalities"], ["text", "code"])
        self.assertEqual(scout["pretraining_token_count"], 40_000_000_000_000)
        self.assertEqual(maverick["pretraining_token_count"], 22_000_000_000_000)
        self.assertEqual(scout["knowledge_cutoff"], "2024-08")
        self.assertEqual(scout["released"], "2025-04-05")
        self.assertIsNone(scout["hosted_api_availability"])
        self.assertIsNone(scout["pricing"])


if __name__ == "__main__":
    unittest.main()

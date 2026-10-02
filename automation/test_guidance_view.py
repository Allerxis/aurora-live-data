import unittest

from automation.guidance_view import build_guidance


class GuidanceViewTests(unittest.TestCase):
    def rule(self):
        return {
            "id": "provider.rule",
            "provider_slug": "provider",
            "category": "clarity",
            "applicability": ["api"],
            "guidance": "Use clear instructions.",
            "source_key": "provider-guidance",
            "evidence_patterns": ["clear instructions", "desired output"],
        }

    def source(self, text):
        return {
            "provider-guidance": {
                "text": text,
                "final_url": "https://example.com/guidance",
                "content_hash": "abc123",
            }
        }

    def test_rule_verifies_when_all_evidence_matches(self):
        out = build_guidance(
            {"rules": [self.rule()]},
            self.source("Use clear instructions and specify the desired output."),
            {"guidance": []},
            "2026-10-02T00:00:00Z",
        )
        item = out["guidance"][0]
        self.assertEqual(
            item["verification_state"],
            "verified_official_guidance",
        )
        self.assertEqual(out["counts"]["verified"], 1)

    def test_previous_verified_rule_becomes_stale(self):
        previous = {
            "guidance": [
                {
                    "id": "provider.rule",
                    "verification_state": "verified_official_guidance",
                    "verified_at": "2026-10-01T00:00:00Z",
                    "source_url": "https://example.com/guidance",
                    "source_hash": "old",
                }
            ]
        }
        out = build_guidance(
            {"rules": [self.rule()]},
            self.source("The documentation changed and no longer matches."),
            previous,
            "2026-10-02T00:00:00Z",
        )
        item = out["guidance"][0]
        self.assertEqual(
            item["verification_state"],
            "verified_official_guidance_stale",
        )
        self.assertEqual(item["verified_at"], "2026-10-01T00:00:00Z")

    def test_never_verified_rule_stays_unverified(self):
        out = build_guidance(
            {"rules": [self.rule()]},
            self.source("Only clear instructions are mentioned."),
            {"guidance": []},
            "2026-10-02T00:00:00Z",
        )
        self.assertEqual(
            out["guidance"][0]["verification_state"],
            "unverified",
        )


if __name__ == "__main__":
    unittest.main()

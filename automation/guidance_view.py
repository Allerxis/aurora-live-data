from __future__ import annotations

import re
from typing import Any


def build_guidance(
    rules_document: dict[str, Any],
    source_texts: dict[str, dict[str, Any]],
    previous_document: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    previous_by_id = {
        item.get("id"): item
        for item in previous_document.get("guidance", [])
        if item.get("id")
    }

    output = []

    for rule in rules_document.get("rules", []):
        rule_id = rule["id"]
        source_key = rule["source_key"]
        source = source_texts.get(source_key)
        previous = previous_by_id.get(rule_id, {})

        item = {
            "id": rule_id,
            "provider_slug": rule["provider_slug"],
            "category": rule["category"],
            "applicability": rule.get("applicability", []),
            "guidance": rule["guidance"],
            "source_key": source_key,
            "source_url": source.get("final_url") if source else previous.get("source_url"),
            "source_hash": source.get("content_hash") if source else previous.get("source_hash"),
            "verification_state": "unverified",
            "verified_at": None,
            "evidence_patterns": rule.get("evidence_patterns", []),
            "matched_patterns": 0,
            "total_patterns": len(rule.get("evidence_patterns", [])),
        }

        if source:
            text = source.get("text", "")
            patterns = rule.get("evidence_patterns", [])
            matched = [
                pattern
                for pattern in patterns
                if re.search(pattern, text, re.I | re.S)
            ]
            item["matched_patterns"] = len(matched)

            if patterns and len(matched) == len(patterns):
                item["verification_state"] = "verified_official_guidance"
                item["verified_at"] = generated_at
            elif previous.get("verification_state") == "verified_official_guidance":
                item["verification_state"] = "verified_official_guidance_stale"
                item["verified_at"] = previous.get("verified_at")
            elif previous.get("verification_state") == "verified_official_guidance_stale":
                item["verification_state"] = "verified_official_guidance_stale"
                item["verified_at"] = previous.get("verified_at")
        else:
            if previous.get("verification_state") in (
                "verified_official_guidance",
                "verified_official_guidance_stale",
            ):
                item["verification_state"] = "verified_official_guidance_stale"
                item["verified_at"] = previous.get("verified_at")

        output.append(item)

    output.sort(key=lambda x: (x["provider_slug"], x["category"], x["id"]))

    counts = {
        "total": len(output),
        "verified": sum(
            x["verification_state"] == "verified_official_guidance"
            for x in output
        ),
        "stale": sum(
            x["verification_state"] == "verified_official_guidance_stale"
            for x in output
        ),
        "unverified": sum(
            x["verification_state"] == "unverified"
            for x in output
        ),
    }

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "purpose": (
            "Source-anchored prompt-engineering guidance. A rule is current only "
            "while deterministic evidence patterns remain present in the tracked "
            "official source."
        ),
        "trust_model": {
            "verified_official_guidance": (
                "All configured evidence patterns matched the current official source."
            ),
            "verified_official_guidance_stale": (
                "The rule was previously verified but could not be revalidated "
                "against the current source; direct source review is required."
            ),
            "unverified": (
                "The current source did not provide enough deterministic evidence "
                "to validate this rule."
            ),
        },
        "counts": counts,
        "guidance": output,
    }

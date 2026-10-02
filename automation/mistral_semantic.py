from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin


BASE_URL = "https://docs.mistral.ai"


def _int_value(raw: str | None) -> int | None:
    if not raw:
        return None
    value = raw.strip().replace(",", "")
    m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([kKmM]?)", value)
    if not m:
        return None
    number = float(m.group(1))
    suffix = m.group(2).lower()
    if suffix == "k":
        number *= 1_000
    elif suffix == "m":
        number *= 1_000_000
    return int(number)


def _money(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _date(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    return raw


def extract_mistral_detail_urls(raw_html: str) -> list[str]:
    """
    Extract first-party model detail URLs from the Mistral models index.
    """
    raw_html = html.unescape(raw_html)
    paths = set()

    patterns = [
        r'href=["\'](?P<path>/models/[a-z0-9][a-z0-9._/-]+)["\']',
        r'href=["\'](?P<path>/fr/models/[a-z0-9][a-z0-9._/-]+)["\']',
        r'https://docs\.mistral\.ai(?P<path>/(?:fr/)?models/[a-z0-9][a-z0-9._/-]+)',
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, raw_html, re.I):
            path = m.group("path").split("#", 1)[0].split("?", 1)[0].rstrip("/")
            if path in ("/models", "/fr/models"):
                continue
            # Prefer English canonical pages when the index exposes both.
            if path.startswith("/fr/models/"):
                path = path[len("/fr"):]
            paths.add(path)

    return sorted(urljoin(BASE_URL, path) for path in paths)


def _section(text: str, start: str, ends: tuple[str, ...]) -> str:
    matches = list(re.finditer(re.escape(start), text, re.I))
    if not matches:
        return ""
    tail = text[matches[-1].end():]
    positions = []
    for end in ends:
        m = re.search(re.escape(end), tail, re.I)
        if m:
            positions.append(m.start())
    if positions:
        tail = tail[: min(positions)]
    return tail.strip()


def parse_mistral_model_page(
    model_id: str,
    text: str,
    source_url: str,
) -> dict[str, Any] | None:
    """
    Parse deterministic facts from one Mistral model card.

    The exact API identifier must occur on the page.
    """
    if not re.search(
        rf"(?<![a-z0-9._-]){re.escape(model_id)}(?![a-z0-9._-])",
        text,
        re.I,
    ):
        return None

    context_m = re.search(
        r"\bContext\s+(?:i\s+)?([0-9][0-9,.]*(?:\.[0-9]+)?[kKmM]?)\b",
        text,
        re.I,
    )
    context = _int_value(context_m.group(1)) if context_m else None

    # Global navigation contains words such as "Labs". Use the last lifecycle
    # marker immediately preceding the exact API ID, which belongs to the card.
    id_match = re.search(
        rf"(?<![a-z0-9._-]){re.escape(model_id)}(?![a-z0-9._-])",
        text,
        re.I,
    )
    stage = None
    if id_match:
        prefix = text[max(0, id_match.start() - 1200):id_match.start()]
        stage_matches = list(re.finditer(
            r"\b(GA|Public Preview|Labs|Deprecated|Retired)\b",
            prefix,
            re.I,
        ))
        if stage_matches:
            raw_stage = stage_matches[-1].group(1)
            stage = {
                "ga": "GA",
                "public preview": "Public Preview",
                "labs": "Labs",
                "deprecated": "Deprecated",
                "retired": "Retired",
            }.get(raw_stage.lower(), raw_stage)

    version_m = re.search(r"\bv([0-9]+(?:\.[0-9]+)+)\b", text, re.I)
    release_m = re.search(
        r"\b([A-Z][a-z]+\s+\d{1,2},\s+\d{4})\b",
        text,
    )

    features_section = _section(
        text,
        "Features",
        ("Other Models", "WHY MISTRAL", "EXPLORE"),
    )
    known_features = {
        "chat_completion": "Chat completion",
        "function_calling": "Function calling",
        "agents_conversations": "Agents & conversations",
        "built_in_tools": "Built-in tools",
        "structured_outputs": "Structured outputs",
        "predicted_outputs": "Predicted outputs",
        "document_qna": "Document QnA",
        "prefix": "Prefix",
        "batch": "Batch",
    }
    features = {}
    for key, label in known_features.items():
        if re.search(re.escape(label), features_section, re.I):
            features[key] = True

    endpoints = sorted(set(re.findall(
        r"/v1/[a-z0-9_./-]+",
        features_section,
        re.I,
    )))

    # Keep the two card prices as display values only. Canonical labelled
    # input/cached/output rates are merged from the official pricing page.
    price_section = _section(text, "Price", ("FEATURES", "Features", "Other Models"))
    displayed_prices = []
    for raw in re.findall(r"\$([0-9]+(?:\.[0-9]+)?)\s*/\s*M\s*Tokens", price_section, re.I):
        value = _money(raw)
        if value is not None and value not in displayed_prices:
            displayed_prices.append(value)

    if context is None and not features and not displayed_prices:
        return None

    return {
        "source_url": source_url,
        "context_window_tokens": context,
        "release_stage": stage,
        "version": version_m.group(1) if version_m else None,
        "released": _date(release_m.group(1)) if release_m else None,
        "features": features,
        "endpoints": endpoints,
        "displayed_price_values_usd_per_1M_tokens": displayed_prices,
        "pricing_key": infer_mistral_pricing_key(model_id, text),
    }


def parse_mistral_pricing_page(
    text: str,
    source_url: str,
) -> dict[str, dict[str, Any]]:
    """
    Parse labelled Standard pricing by human model name.

    The pricing page labels the columns Model / Input / Cached input / Output.
    Keys are normalized human display names and are later matched to a verified
    model card title or API-ID family.
    """
    rows: dict[str, dict[str, Any]] = {}

    # Restrict to rows that present three token prices. Specialized per-page or
    # per-minute rows deliberately do not match.
    row_pattern = re.compile(
        r"(?P<name>"
        r"Mistral\s+(?:Large|Medium|Small)\s+[0-9]+(?:\.[0-9]+)?|"
        r"Ministral\s+[0-9]+\s+(?:14B|8B|3B)|"
        r"Codestral(?:\s+Embed)?|"
        r"Z\.ai\s+GLM\s+[0-9]+(?:\.[0-9]+)?"
        r")\s+[^$]{0,48}"
        r"\$(?P<input>[0-9.]+)\s+"
        r"\$(?P<cached>[0-9.]+)\s+"
        r"\$(?P<output>[0-9.]+)",
        re.I,
    )
    for m in row_pattern.finditer(text):
        name = re.sub(r"\s+", " ", m.group("name")).strip().lower()
        rows[name] = {
            "unit": "USD_per_1M_tokens",
            "input": _money(m.group("input")),
            "cached_input": _money(m.group("cached")),
            "output": _money(m.group("output")),
            "source_url": source_url,
        }

    return rows


def infer_mistral_pricing_key(model_id: str, text: str) -> str | None:
    """
    Derive only human names explicitly present in a verified model card.
    """
    candidates = [
        r"\bMistral\s+(?:Large|Medium|Small)\s+[0-9]+(?:\.[0-9]+)?\b",
        r"\bMinistral\s+[0-9]+\s+(?:14B|8B|3B)\b",
        r"\bCodestral(?:\s+Embed)?\b",
        r"\bZ\.ai\s+GLM\s+[0-9]+(?:\.[0-9]+)?\b",
    ]
    for pattern in candidates:
        m = re.search(pattern, text, re.I)
        if m:
            return re.sub(r"\s+", " ", m.group(0)).strip().lower()
    return None

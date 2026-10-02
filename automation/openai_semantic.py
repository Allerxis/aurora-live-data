from __future__ import annotations

import re
from datetime import datetime
from typing import Any


KNOWN_FEATURES = {
    "streaming": "Streaming",
    "function_calling": "Function calling",
    "structured_outputs": "Structured outputs",
    "fine_tuning": "Fine-tuning",
}

KNOWN_TOOLS = {
    "web_search": "Web search",
    "file_search": "File search",
    "image_generation": "Image generation",
    "code_interpreter": "Code interpreter",
    "hosted_shell": "Hosted shell",
    "apply_patch": "Apply patch",
    "skills": "Skills",
    "computer_use": "Computer use",
    "mcp": "MCP",
    "tool_search": "Tool search",
}

KNOWN_MODALITIES = ("Text", "Image", "Audio", "Video")


def _int_token_count(raw: str) -> int | None:
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
    if raw is None:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _supported_state(text: str, label: str) -> bool | None:
    # The model pages expose rows such as "Streaming Supported" and
    # "Fine-tuning Not supported".
    m = re.search(
        rf"\b{re.escape(label)}\s+(Supported|Not supported)\b",
        text,
        re.I,
    )
    if not m:
        return None
    return m.group(1).lower() == "supported"


def _section(text: str, start: str, ends: tuple[str, ...]) -> str:
    # Model pages include global navigation that may repeat headings such as
    # "Features" and "Tools". The model-spec block is the last occurrence.
    matches = list(re.finditer(rf"\b{re.escape(start)}\b", text, re.I))
    if not matches:
        return ""
    start_match = matches[-1]
    tail = text[start_match.end():]
    positions = []
    for end in ends:
        m = re.search(rf"\b{re.escape(end)}\b", tail, re.I)
        if m:
            positions.append(m.start())
    if positions:
        tail = tail[: min(positions)]
    return tail.strip()


def parse_openai_model_page(model_id: str, text: str, source_url: str) -> dict[str, Any] | None:
    """
    Parse deterministic facts from one OpenAI model detail page.

    This parser is intentionally conservative. A record is returned only when:
    - the exact model ID occurs in the page; and
    - at least context window or max output tokens is found.

    Missing fields remain null/empty instead of being inferred.
    """
    if not re.search(rf"(?<![a-z0-9._-]){re.escape(model_id)}(?![a-z0-9._-])", text, re.I):
        return None

    context_m = re.search(
        r"\b([0-9][0-9,.]*\s*[kKmM]?)\s+context window\b",
        text,
        re.I,
    )
    output_m = re.search(
        r"\b([0-9][0-9,.]*\s*[kKmM]?)\s+max output tokens\b",
        text,
        re.I,
    )
    cutoff_m = re.search(
        r"\b([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})\s+knowledge cutoff\b",
        text,
    )

    context_window = _int_token_count(context_m.group(1).replace(" ", "")) if context_m else None
    max_output = _int_token_count(output_m.group(1).replace(" ", "")) if output_m else None

    if context_window is None and max_output is None:
        return None

    knowledge_cutoff = None
    if cutoff_m:
        try:
            knowledge_cutoff = datetime.strptime(
                cutoff_m.group(1), "%b %d, %Y"
            ).date().isoformat()
        except ValueError:
            knowledge_cutoff = cutoff_m.group(1)

    pricing = {
        "unit": "USD_per_1M_tokens",
        "input": None,
        "cached_input": None,
        "cache_writes": None,
        "output": None,
    }
    pricing_section = _section(text, "Text tokens", ("Quick comparison", "Modalities", "Endpoints"))
    if pricing_section:
        m = re.search(r"\bInput\s+\$([0-9.,]+)", pricing_section, re.I)
        pricing["input"] = _money(m.group(1)) if m else None

        m = re.search(r"\bCached input\s+\$([0-9.,]+)", pricing_section, re.I)
        pricing["cached_input"] = _money(m.group(1)) if m else None

        m = re.search(r"\bCache writes\s+\$([0-9.,]+)", pricing_section, re.I)
        pricing["cache_writes"] = _money(m.group(1)) if m else None

        # Search for Output only after the pricing heading to avoid unrelated uses.
        m = re.search(r"\bOutput\s+\$([0-9.,]+)", pricing_section, re.I)
        pricing["output"] = _money(m.group(1)) if m else None

    modalities = {}
    modalities_section = _section(text, "Modalities", ("Endpoints", "Features", "Tools"))
    for modality in KNOWN_MODALITIES:
        m = re.search(
            rf"\b{modality}\s+(Input and output|Input only|Output only|Not supported)\b",
            modalities_section,
            re.I,
        )
        if m:
            modalities[modality.lower()] = m.group(1).lower().replace(" ", "_")

    endpoints_section = _section(text, "Endpoints", ("Features", "Tools", "Snapshots", "Rate limits"))
    endpoints = sorted(set(re.findall(r"\bv1/[a-z0-9_./-]+", endpoints_section, re.I)))

    features = {}
    features_section = _section(text, "Features", ("Tools", "Snapshots", "Rate limits"))
    for key, label in KNOWN_FEATURES.items():
        state = _supported_state(features_section, label)
        if state is not None:
            features[key] = state

    tools = {}
    tools_section = _section(text, "Tools", ("Snapshots", "Rate limits"))
    for key, label in KNOWN_TOOLS.items():
        state = _supported_state(tools_section, label)
        if state is not None:
            tools[key] = state

    effort_m = re.search(
        r"reasoning\.effort\s+supports\s+([^\.]+)\.",
        text,
        re.I,
    )
    reasoning_efforts = []
    if effort_m:
        raw = effort_m.group(1)
        allowed = ("none", "minimal", "low", "medium", "high", "xhigh", "max")
        reasoning_efforts = [x for x in allowed if re.search(rf"\b{x}\b", raw, re.I)]

    return {
        "source_url": source_url,
        "context_window_tokens": context_window,
        "max_output_tokens": max_output,
        "knowledge_cutoff": knowledge_cutoff,
        "pricing": pricing,
        "modalities": modalities,
        "endpoints": endpoints,
        "features": features,
        "tools": tools,
        "reasoning_efforts": reasoning_efforts,
    }

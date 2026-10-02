from __future__ import annotations

import re
from datetime import datetime
from typing import Any


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


def _month_year(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%B %Y", "%b %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m")
        except ValueError:
            pass
    return raw


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


def _section(text: str, start: str, ends: tuple[str, ...]) -> str:
    matches = list(re.finditer(rf"\b{re.escape(start)}\b", text, re.I))
    if not matches:
        return ""
    tail = text[matches[-1].end():]
    positions = []
    for end in ends:
        m = re.search(rf"\b{re.escape(end)}\b", tail, re.I)
        if m:
            positions.append(m.start())
    if positions:
        tail = tail[: min(positions)]
    return tail.strip()


def parse_xai_model_page(
    model_id: str,
    text: str,
    source_url: str,
) -> dict[str, Any] | None:
    """
    Parse deterministic facts from an xAI Grok model detail page.
    """
    if not re.search(
        rf"(?<![a-z0-9._-]){re.escape(model_id)}(?![a-z0-9._-])",
        text,
        re.I,
    ):
        return None

    model_name_m = re.search(
        r"\bModel name\s+(grok-[a-z0-9._-]+)",
        text,
        re.I,
    )
    if model_name_m and model_name_m.group(1).lower() != model_id.lower():
        return None

    context_m = re.search(
        r"\bContext window\s+([0-9][0-9,]*(?:\.[0-9]+)?[kKmM]?)",
        text,
        re.I,
    )
    if not context_m:
        context_m = re.search(
            r"\bContext\s+([0-9][0-9,]*(?:\.[0-9]+)?[kKmM]?)\s+tokens",
            text,
            re.I,
        )

    context_window = _int_value(context_m.group(1)) if context_m else None
    if context_window is None:
        return None

    modalities_raw = None
    modalities_section = _section(text, "Modalities", ("Context window", "Pricing", "Capabilities"))
    if modalities_section:
        modalities_raw = re.sub(r"\s+", " ", modalities_section).strip()

    capabilities_section = _section(text, "Capabilities", ("Pricing", "Details"))
    capabilities = {}
    for key, label in {
        "function_calling": "Function calling",
        "structured_outputs": "Structured outputs",
        "reasoning": "Reasoning",
    }.items():
        if re.search(rf"\b{re.escape(label)}\b", capabilities_section, re.I):
            capabilities[key] = True

    pricing_section = _section(text, "Pricing", ("Details",))
    input_price = None
    cached_price = None
    output_price = None
    if pricing_section:
        m = re.search(
            r"\bInput\s+Tokens\s+\$([0-9.,]+)\s*/\s*1M tokens",
            pricing_section,
            re.I,
        )
        input_price = _money(m.group(1)) if m else None

        m = re.search(
            r"\bCached tokens\s+\$([0-9.,]+)\s*/\s*1M tokens",
            pricing_section,
            re.I,
        )
        cached_price = _money(m.group(1)) if m else None

        m = re.search(
            r"\bOutput\s+Tokens\s+\$([0-9.,]+)\s*/\s*1M tokens",
            pricing_section,
            re.I,
        )
        output_price = _money(m.group(1)) if m else None

    details_section = _section(text, "Details", ("Rate limits", "Learn more"))
    batch_api = None
    m = re.search(
        r"\bBatch API\s+(Supported|Not supported)",
        details_section,
        re.I,
    )
    if m:
        batch_api = m.group(1).lower() == "supported"

    reasoning_supported = None
    reasoning_efforts = []
    default_reasoning_effort = None
    m = re.search(
        r"\bReasoning efforts\s+(Supported|Not supported)(.*?)(?:\bDefault\b|\bRate limits\b|$)",
        details_section,
        re.I,
    )
    if m:
        reasoning_supported = m.group(1).lower() == "supported"
        effort_text = m.group(2)
        for effort in ("none", "low", "medium", "high", "xhigh"):
            if re.search(rf"\b{effort}\b", effort_text, re.I):
                reasoning_efforts.append(effort)

    m = re.search(
        r"\bDefault\s+(none|low|medium|high|xhigh)\b",
        details_section,
        re.I,
    )
    if m:
        default_reasoning_effort = m.group(1).lower()

    return {
        "source_url": source_url,
        "context_window_tokens": context_window,
        "modalities_raw": modalities_raw,
        "capabilities": capabilities,
        "pricing": {
            "unit": "USD_per_1M_tokens",
            "input": input_price,
            "cached_input": cached_price,
            "output": output_price,
        },
        "batch_api": batch_api,
        "reasoning": {
            "supported": reasoning_supported,
            "efforts": reasoning_efforts,
            "default": default_reasoning_effort,
        },
    }


def parse_xai_knowledge_cutoffs(
    text: str,
    source_url: str,
) -> dict[str, dict[str, Any]]:
    rows = {}
    pattern = re.compile(
        r"knowledge cut-?off date of Grok\s+([0-9]+(?:\.[0-9]+)*)\s+is\s+"
        r"([A-Z][a-z]+\s+\d{4})",
        re.I,
    )
    for m in pattern.finditer(text):
        model_id = f"grok-{m.group(1)}".lower()
        rows[model_id] = {
            "knowledge_cutoff": _month_year(m.group(2)),
            "source_url": source_url,
        }
    return rows


def parse_xai_retirement_page(
    text: str,
    source_url: str,
) -> dict[str, dict[str, Any]]:
    """
    Parse the May 15, 2026 xAI retirement guide.

    The guide states that listed legacy slugs continue to resolve by redirecting
    to replacement models, so status is recorded as retired_redirect rather than
    unavailable.
    """
    effective_m = re.search(
        r"Effective\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        text,
        re.I,
    )
    effective_date = _date(effective_m.group(1)) if effective_m else None

    rows = {}
    replacement_pattern = re.compile(
        r"(grok-[a-z0-9._-]+)\s+"
        r"(grok-[a-z0-9._-]+)"
        r"(?:\s+with\s+(none|low|medium|high|xhigh)\s+reasoning effort)?",
        re.I,
    )
    for m in replacement_pattern.finditer(text):
        legacy = m.group(1).lower()
        replacement = m.group(2).lower()
        if legacy == replacement:
            continue
        rows[legacy] = {
            "status": "retired_redirect",
            "effective_date": effective_date,
            "redirect_target": replacement,
            "redirect_reasoning_effort": (
                m.group(3).lower() if m.group(3) else None
            ),
            "source_url": source_url,
        }

    # Ensure explicitly listed retired text-model slugs are represented even if
    # their replacement row was not parsed.
    for model_id in re.findall(
        r"\b(grok-(?:4-1-fast-(?:reasoning|non-reasoning)|"
        r"4-fast-(?:reasoning|non-reasoning)|4-0709|3))\b",
        text,
        re.I,
    ):
        rows.setdefault(
            model_id.lower(),
            {
                "status": "retired_redirect",
                "effective_date": effective_date,
                "redirect_target": None,
                "redirect_reasoning_effort": None,
                "source_url": source_url,
            },
        )

    return rows

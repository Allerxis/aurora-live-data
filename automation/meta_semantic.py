from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def _int_value(raw: str | None) -> int | None:
    if not raw:
        return None
    value = raw.strip().replace(",", "")
    m = re.fullmatch(r"~?([0-9]+(?:\.[0-9]+)?)([kKmMtT]?)", value)
    if not m:
        return None
    number = float(m.group(1))
    suffix = m.group(2).lower()
    multipliers = {
        "": 1,
        "k": 1_000,
        "m": 1_000_000,
        "t": 1_000_000_000_000,
    }
    return int(number * multipliers[suffix])


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


def _clean_markdown(value: str) -> str:
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"[*_]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_llama4_model_card(
    markdown: str,
    source_url: str,
) -> dict[str, dict[str, Any]]:
    """
    Parse Llama 4 Scout and Maverick facts from Meta's official llama-models
    model card.

    The table is treated as structured source data; no hosted-API availability
    or price is inferred from an open-weight model card.
    """
    release_m = re.search(
        r"Model Release Date:\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        markdown,
        re.I,
    )
    release_date = _date(release_m.group(1)) if release_m else None

    freshness_m = re.search(
        r"Data Freshness:\s*.*?cutoff of\s+([A-Z][a-z]+\s+\d{4})",
        markdown,
        re.I | re.S,
    )
    global_cutoff = _month_year(freshness_m.group(1)) if freshness_m else None

    records = {}
    name_map = {
        "llama 4 scout": ("llama-4-scout", "Llama 4 Scout"),
        "llama 4 maverick": ("llama-4-maverick", "Llama 4 Maverick"),
    }

    for line in markdown.splitlines():
        if "|" not in line:
            continue
        low = line.lower()
        matched_name = None
        for human_name in name_map:
            if human_name in low:
                matched_name = human_name
                break
        if not matched_name:
            continue

        cells = [_clean_markdown(x) for x in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue

        model_key, display_name = name_map[matched_name]

        params_cell = next(
            (x for x in cells if "activated" in x.lower() and "total" in x.lower()),
            None,
        )
        active_params = None
        total_params = None
        if params_cell:
            m = re.search(r"([0-9.]+B)\s*\(Activated\)", params_cell, re.I)
            active_params = m.group(1).upper() if m else None
            m = re.search(r"([0-9.]+B)\s*\(Total\)", params_cell, re.I)
            total_params = m.group(1).upper() if m else None

        input_modalities = None
        output_modalities = None
        for cell in cells:
            cell_low = cell.lower()
            if "text and image" in cell_low:
                input_modalities = ["text", "image"]
            if "text and code" in cell_low:
                output_modalities = ["text", "code"]

        context_raw = next(
            (
                m.group(1)
                for cell in cells
                for m in [re.fullmatch(r"\s*([0-9.]+[kKmM])\s*", cell)]
                if m
            ),
            None,
        )
        context_tokens = _int_value(context_raw)

        token_count_raw = next(
            (
                m.group(1)
                for cell in cells
                for m in [re.fullmatch(r"\s*(~[0-9.]+[tT])\s*", cell)]
                if m
            ),
            None,
        )
        training_token_count = _int_value(token_count_raw)

        cutoff_raw = next(
            (
                m.group(1)
                for cell in cells
                for m in [re.fullmatch(r"\s*([A-Z][a-z]+\s+\d{4})\s*", cell)]
                if m
            ),
            None,
        )
        knowledge_cutoff = _month_year(cutoff_raw) or global_cutoff

        if context_tokens is None:
            continue

        records[model_key] = {
            "source_url": source_url,
            "display_name": display_name,
            "distribution": "open_weight",
            "developer": "Meta",
            "architecture": "mixture_of_experts",
            "input_modalities": input_modalities,
            "output_modalities": output_modalities,
            "context_window_tokens": context_tokens,
            "active_parameters": active_params,
            "total_parameters": total_params,
            "pretraining_token_count": training_token_count,
            "knowledge_cutoff": knowledge_cutoff,
            "released": release_date,
            "hosted_api_availability": None,
            "pricing": None,
        }

    return records

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


MODEL_PREFIXES = (
    "gemini-",
    "imagen-",
    "veo-",
    "lyria-",
    "deep-research-",
    "antigravity-",
)


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


def _supported_state(section: str, label: str) -> str | None:
    m = re.search(
        rf"{re.escape(label)}\s+"
        r"(Supported(?:\s*\([^)]*\))?|Not supported)",
        section,
        re.I,
    )
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1)).strip()


def parse_google_model_page(
    model_id: str,
    text: str,
    source_url: str,
) -> dict[str, Any] | None:
    """
    Parse deterministic facts from a Google AI model detail page.

    The exact model ID must appear in the page. Missing facts are left null.
    """
    if not re.search(
        rf"(?<![a-z0-9._-]){re.escape(model_id)}(?![a-z0-9._-])",
        text,
        re.I,
    ):
        return None

    model_code_section = _section(
        text,
        "Model code",
        ("Supported data types", "Token limits", "Limits", "Capabilities"),
    )
    model_codes = sorted(set(re.findall(
        r"(?<![a-z0-9._-])"
        r"((?:gemini|imagen|veo|lyria|deep-research|antigravity)-[a-z0-9._-]+)"
        r"(?![a-z0-9._-])",
        model_code_section,
        re.I,
    )))

    if model_id.lower() not in {x.lower() for x in model_codes}:
        # Some pages place the model ID in the heading but not a dedicated
        # Model code block. Require at least a known property block below.
        if "Supported data types" not in text:
            return None

    input_limit_m = re.search(
        r"Input token limit\s+([0-9][0-9,]*(?:\.[0-9]+)?[kKmM]?)",
        text,
        re.I,
    )
    output_limit_m = re.search(
        r"Output token limit\s+([0-9][0-9,]*(?:\.[0-9]+)?[kKmM]?)",
        text,
        re.I,
    )

    data_section = _section(
        text,
        "Supported data types",
        ("Token limits", "Limits", "Capabilities", "Consumption options", "Versions", "Latest update"),
    )
    input_types = []
    output_types = []
    if data_section:
        m = re.search(r"Inputs?\s+(.+?)\s+Outputs?\s+(.+)$", data_section, re.I | re.S)
        if m:
            input_types = [
                x.strip().lower()
                for x in re.split(r",|\band\b", m.group(1), flags=re.I)
                if x.strip()
            ]
            output_types = [
                x.strip().lower()
                for x in re.split(r",|\band\b", m.group(2), flags=re.I)
                if x.strip()
            ]

    capabilities_section = _section(
        text,
        "Capabilities",
        ("Consumption options", "Versions", "Latest update"),
    )
    known_capabilities = {
        "audio_generation": "Audio generation",
        "caching": "Caching",
        "code_execution": "Code execution",
        "computer_use": "Computer use",
        "file_search": "File search",
        "function_calling": "Function calling",
        "google_maps_grounding": "Grounding with Google Maps",
        "image_generation": "Image generation",
        "live_api": "Live API",
        "search_grounding": "Search grounding",
        "structured_outputs": "Structured outputs",
        "thinking": "Thinking",
        "url_context": "URL context",
    }
    capabilities = {}
    for key, label in known_capabilities.items():
        state = _supported_state(capabilities_section, label)
        if state is not None:
            capabilities[key] = state

    consumption_section = _section(
        text,
        "Consumption options",
        ("Versions", "Latest update"),
    )
    consumption = {}
    for key, label in {
        "batch_api": "Batch API",
        "flex_inference": "Flex inference",
        "priority_inference": "Priority inference",
    }.items():
        state = _supported_state(consumption_section, label)
        if state is not None:
            consumption[key] = state

    versions_section = _section(text, "Versions", ("Latest update", "Model card"))
    versions = {}
    for label in ("Stable", "Preview", "Latest", "Experimental"):
        m = re.search(
            rf"{label}:\s*((?:gemini|imagen|veo|lyria|deep-research|antigravity)-[a-z0-9._-]+)",
            versions_section,
            re.I,
        )
        if m:
            versions[label.lower()] = m.group(1)

    latest_update_m = re.search(
        r"Latest update\s+([A-Z][a-z]+\s+\d{4})",
        text,
    )

    output_dimension = None
    m = re.search(
        r"Output dimension size\s+(.+?)(?:Capabilities|Consumption options|Versions|Latest update|$)",
        text,
        re.I,
    )
    if m:
        output_dimension = re.sub(r"\s+", " ", m.group(1)).strip()

    video_output_count = None
    m = re.search(r"Output video\s+([0-9]+)", text, re.I)
    if m:
        video_output_count = int(m.group(1))

    if (
        not model_codes
        and not input_types
        and input_limit_m is None
        and not capabilities
        and video_output_count is None
    ):
        return None

    return {
        "source_url": source_url,
        "model_codes": model_codes,
        "input_types": input_types,
        "output_types": output_types,
        "input_token_limit": _int_value(input_limit_m.group(1)) if input_limit_m else None,
        "output_token_limit": _int_value(output_limit_m.group(1)) if output_limit_m else None,
        "output_dimension": output_dimension,
        "video_output_count": video_output_count,
        "capabilities": capabilities,
        "consumption_options": consumption,
        "versions": versions,
        "latest_update": _month_year(latest_update_m.group(1)) if latest_update_m else None,
    }


def parse_google_lifecycle_page(
    text: str,
    source_url: str,
) -> dict[str, dict[str, Any]]:
    """
    Parse release/shutdown rows from the Gemini deprecations page.

    Google describes shutdown dates as the earliest possible shutdown dates.
    Therefore this parser does not infer that a model is already unavailable
    merely because the date has passed.
    """
    rows: dict[str, dict[str, Any]] = {}

    model_pattern = (
        r"(?:gemini|imagen|veo|lyria|deep-research|antigravity|"
        r"text-embedding|embedding)-[a-z0-9._-]+"
    )
    date_pattern = r"(?:[A-Z][a-z]+(?:\s+\d{1,2},)?\s+\d{4})"
    shutdown_pattern = rf"(?:No shutdown date announced|{date_pattern})"

    # Rows are flattened by normalize_html. Parse the model/release/shutdown
    # triple without consuming any following model identifier.
    pattern = re.compile(
        rf"(?P<model>{model_pattern})\s+"
        rf"(?P<release>{date_pattern})?\s*"
        rf"(?P<shutdown>{shutdown_pattern})",
        re.I,
    )

    for m in pattern.finditer(text):
        model_id = m.group("model").lower()
        shutdown_raw = m.group("shutdown")
        release_raw = m.group("release")

        replacement = None
        tail = text[m.end():]
        candidate = re.match(rf"\s+({model_pattern})", tail, re.I)
        if candidate:
            after_candidate = tail[candidate.end():]
            # If the candidate is immediately followed by a release date or a
            # shutdown phrase, it is the next table row, not a replacement.
            starts_new_row = re.match(
                rf"\s*(?:{date_pattern}|No shutdown date announced)",
                after_candidate,
                re.I,
            )
            if not starts_new_row:
                replacement = candidate.group(1).lower()

        rows[model_id] = {
            "release_date": _date(release_raw) if release_raw and "," in release_raw else _month_year(release_raw),
            "shutdown": (
                None
                if shutdown_raw.lower() == "no shutdown date announced"
                else _date(shutdown_raw)
            ),
            "shutdown_announced": shutdown_raw.lower() != "no shutdown date announced",
            "recommended_replacement": replacement,
            "date_semantics": "earliest_possible_shutdown_date",
            "source_url": source_url,
        }

    return rows

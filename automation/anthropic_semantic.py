from __future__ import annotations

import re
from datetime import datetime
from typing import Any


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


def _month_year(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), "%b %Y").strftime("%Y-%m")
    except ValueError:
        return raw.strip()


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


def _extract_after_label(text: str, label: str, pattern: str) -> str | None:
    m = re.search(
        rf"(?<!\w){re.escape(label)}(?!\w)\s*({pattern})",
        text,
        re.I,
    )
    return m.group(1).strip() if m else None


def detail_slug_candidates(model_id: str) -> list[str]:
    """
    Return conservative Claude Platform detail slugs for an API model ID.

    Snapshot dates are removed only for the page slug. The parser still requires
    the exact requested model ID to occur in the page before verification.
    """
    low = model_id.lower()
    if not low.startswith("claude-"):
        return []

    core = low[len("claude-"):]
    slugs = [core]
    core_without_snapshot = re.sub(r"-\d{8}$", "", core)
    if core_without_snapshot != core:
        slugs.append(core_without_snapshot)

    # Older IDs place the generation before the family:
    # claude-3-5-sonnet-20241022 -> sonnet-3-5
    legacy = re.fullmatch(
        r"(\d+(?:-\d+)?)-(opus|sonnet|haiku)",
        core_without_snapshot,
    )
    if legacy:
        slugs.append(f"{legacy.group(2)}-{legacy.group(1)}")

    return list(dict.fromkeys(slugs))


def parse_anthropic_model_page(
    model_id: str,
    text: str,
    source_url: str,
) -> dict[str, Any] | None:
    """
    Parse deterministic facts from one Claude Platform model page.

    Missing fields stay null instead of being inferred.
    """
    exact_id = re.search(
        rf"(?<![a-z0-9._-]){re.escape(model_id)}(?![a-z0-9._-])",
        text,
        re.I,
    )
    if not exact_id:
        return None

    context_raw = _extract_after_label(
        text,
        "Context window",
        r"[0-9][0-9,.]*\s*[kKmM]?\s*tokens",
    )
    output_raw = _extract_after_label(
        text,
        "Max output",
        r"[0-9][0-9,.]*\s*[kKmM]?\s*tokens",
    )

    def parse_token_field(raw: str | None) -> int | None:
        if not raw:
            return None
        m = re.search(r"([0-9][0-9,.]*\s*[kKmM]?)", raw)
        return _int_token_count(m.group(1).replace(" ", "")) if m else None

    context_window = parse_token_field(context_raw)
    max_output = parse_token_field(output_raw)

    if context_window is None and max_output is None:
        return None

    batch_output_raw = _extract_after_label(
        text,
        "Max output (Batch API, beta)",
        r"[0-9][0-9,.]*\s*[kKmM]?\s*tokens",
    )

    input_price = _extract_after_label(
        text,
        "Input",
        r"\$[0-9.,]+\s*/\s*MTok",
    )
    output_price = _extract_after_label(
        text,
        "Output",
        r"\$[0-9.,]+\s*/\s*MTok",
    )
    cache_5m = _extract_after_label(
        text,
        "5m cache write",
        r"\$[0-9.,]+\s*/\s*MTok",
    )
    cache_1h = _extract_after_label(
        text,
        "1h cache write",
        r"\$[0-9.,]+\s*/\s*MTok",
    )
    cache_read = _extract_after_label(
        text,
        "Cache read",
        r"\$[0-9.,]+\s*/\s*MTok",
    )

    def money_from_field(raw: str | None) -> float | None:
        if not raw:
            return None
        m = re.search(r"\$([0-9.,]+)", raw)
        return _money(m.group(1)) if m else None

    thinking = _extract_after_label(
        text,
        "Thinking",
        r"(?:Adaptive \(always on\)|Adaptive|Extended|Not supported)",
    )
    default_effort = _extract_after_label(
        text,
        "Default effort",
        r"(?:high|medium|low|Not supported|—)",
    )
    latency = _extract_after_label(
        text,
        "Comparative latency",
        r"(?:Fastest|Fast|Moderate|Slower)",
    )
    io = None
    io_match = re.search(
        r"Input\s*→\s*output\s+(.+?)\s+"
        r"(?:Reliable knowledge cutoff|Training data cutoff|Availability|Status)",
        text,
        re.I | re.S,
    )
    if io_match:
        io = re.sub(r"\s+", " ", io_match.group(1)).strip()

    reliable_cutoff = _extract_after_label(
        text,
        "Reliable knowledge cutoff",
        r"[A-Z][a-z]{2}\s+\d{4}",
    )
    training_cutoff = _extract_after_label(
        text,
        "Training data cutoff",
        r"[A-Z][a-z]{2}\s+\d{4}",
    )

    status = _extract_after_label(
        text,
        "Status",
        r"(?:Active \(latest\)|Active|Legacy|Deprecated|Retired)",
    )
    released = _extract_after_label(
        text,
        "Released",
        r"[A-Z][a-z]+\s+\d{1,2},\s+\d{4}",
    )
    retirement = _extract_after_label(
        text,
        "Retirement",
        r"Not sooner than [A-Z][a-z]+\s+\d{1,2},\s+\d{4}|[A-Z][a-z]+\s+\d{1,2},\s+\d{4}",
    )

    # IDs are explicitly labelled on model pages.
    ids = {}
    id_patterns = {
        "claude_api": r"Claude API\s+(claude-[a-z0-9-]+)",
        "amazon_bedrock": r"Amazon Bedrock\s+(anthropic\.claude-[a-z0-9.-]+)",
        "google_cloud": r"Google Cloud\s+(claude-[a-z0-9-]+(?:@[0-9]+)?)",
        "microsoft_foundry": r"Microsoft Foundry\s+(claude-[a-z0-9-]+)",
        "claude_platform_aws": r"Claude Platform on AWS\s+(claude-[a-z0-9-]+)",
    }
    for key, pattern in id_patterns.items():
        m = re.search(pattern, text, re.I)
        if m:
            ids[key] = m.group(1)

    platforms = []
    platform_names = (
        "Claude API",
        "Amazon Bedrock",
        "Google Cloud",
        "Microsoft Foundry",
        "Claude Platform on AWS",
    )
    availability_match = re.search(
        r"\bPlatforms\b\s+(.+?)(?:\bGood to know\b|\bResources\b)",
        text,
        re.I | re.S,
    )
    if availability_match:
        available_text = availability_match.group(1)
        platforms = [
            p for p in platform_names
            if re.search(re.escape(p), available_text, re.I)
        ]

    id_to_platform = {
        "claude_api": "Claude API",
        "amazon_bedrock": "Amazon Bedrock",
        "google_cloud": "Google Cloud",
        "microsoft_foundry": "Microsoft Foundry",
        "claude_platform_aws": "Claude Platform on AWS",
    }
    for key, platform in id_to_platform.items():
        if key in ids and platform not in platforms:
            platforms.append(platform)

    return {
        "source_url": source_url,
        "context_window_tokens": context_window,
        "max_output_tokens": max_output,
        "max_output_batch_tokens": parse_token_field(batch_output_raw),
        "pricing": {
            "unit": "USD_per_1M_tokens",
            "input": money_from_field(input_price),
            "output": money_from_field(output_price),
            "cache_write_5m": money_from_field(cache_5m),
            "cache_write_1h": money_from_field(cache_1h),
            "cache_read": money_from_field(cache_read),
        },
        "thinking": thinking,
        "default_effort": None if default_effort in (None, "—") else default_effort,
        "comparative_latency": latency,
        "input_output": io,
        "reliable_knowledge_cutoff": _month_year(reliable_cutoff),
        "training_data_cutoff": _month_year(training_cutoff),
        "lifecycle": {
            "status": status,
            "released": _date(released),
            "retirement": retirement,
        },
        "platform_ids": ids,
        "platforms": platforms,
    }


def parse_anthropic_lifecycle_page(
    text: str,
    source_url: str,
) -> dict[str, dict[str, Any]]:
    """
    Parse the Claude model lifecycle table.

    This parser records only explicit table rows. Partner-operated platforms may
    use different retirement schedules, so the scope is stored with every row.
    """
    rows: dict[str, dict[str, Any]] = {}
    pattern = re.compile(
        r"(?P<model>claude-[a-z0-9.-]+)\s+"
        r"(?P<state>Active|Legacy|Deprecated|Retired)\s+"
        r"(?P<deprecated>N/A|[A-Z][a-z]+\s+\d{1,2},\s+\d{4})\s+"
        r"(?P<retirement>Not sooner than [A-Z][a-z]+\s+\d{1,2},\s+\d{4}|"
        r"To be announced|[A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        re.I,
    )

    for m in pattern.finditer(text):
        model_id = m.group("model").lower()
        deprecated_raw = m.group("deprecated")
        retirement_raw = m.group("retirement")

        rows[model_id] = {
            "status": m.group("state").capitalize(),
            "deprecated_at": (
                None
                if deprecated_raw.upper() == "N/A"
                else _date(deprecated_raw)
            ),
            "retirement": retirement_raw,
            "scope": [
                "Claude API",
                "Claude Platform on AWS",
                "Microsoft Foundry",
            ],
            "partner_platform_schedule_may_differ": True,
            "source_url": source_url,
        }

    return rows


def extract_current_anthropic_model_ids(text: str) -> list[str]:
    """
    Extract current Claude API IDs and aliases only from the Compare models block.
    This avoids treating historical IDs elsewhere on the page as current lineup.
    """
    m = re.search(
        r"\bCompare models\b(.+?)\bUsing the Models API\b",
        text,
        re.I | re.S,
    )
    section = m.group(1) if m else text
    ids = re.findall(
        r"\bclaude-(?:fable|opus|sonnet|haiku)-[a-z0-9-]+\b",
        section,
        re.I,
    )
    return sorted(set(x.lower() for x in ids))

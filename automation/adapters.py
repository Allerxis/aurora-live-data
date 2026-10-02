from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Candidate:
    model_key: str
    display_name: str
    kind: str = "model"

def _unique(items: Iterable[Candidate]) -> list[Candidate]:
    seen = set()
    out = []
    for item in items:
        key = item.model_key.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return sorted(out, key=lambda x: x.model_key.lower())

def _tokens(text: str, pattern: str, flags: int = re.I) -> list[str]:
    return [m.group(0).strip(".,;:()[]{}<>\"'") for m in re.finditer(pattern, text, flags)]

def discover_openai(text: str) -> list[Candidate]:
    patterns = [
        r"\bgpt-[0-9][a-z0-9]*(?:[._-][a-z0-9]+){0,8}\b",
        r"\bo[1-9](?:[._-][a-z0-9]+){1,8}\b",
    ]
    raw = []
    for pattern in patterns:
        raw.extend(_tokens(text, pattern))
    return _unique(Candidate(x.lower(), x.lower()) for x in raw)

def discover_anthropic(text: str) -> list[Candidate]:
    # Claude API model IDs across current and legacy naming schemes.
    # Excludes product/docs tokens such as claude-code and claude-api.
    patterns = [
        r"\bclaude-(?:opus|sonnet|haiku|fable|mythos)-(?:\d+(?:-\d+)?(?:-\d{8})?|preview)\b",
        r"\bclaude-\d+(?:-\d+)?-(?:opus|sonnet|haiku)(?:-\d{8})?\b",
        r"\bclaude-2(?:\.0|\.1)\b",
    ]
    raw = []
    for pattern in patterns:
        raw.extend(_tokens(text, pattern))
    return _unique(Candidate(x.lower(), x.lower()) for x in raw)

def discover_google(text: str) -> list[Candidate]:
    patterns = [
        r"\bgemini-[a-z0-9][a-z0-9._-]{2,100}\b",
        r"\bimagen-[a-z0-9][a-z0-9._-]{2,100}\b",
        r"\bveo-[a-z0-9][a-z0-9._-]{2,100}\b",
        r"\blyria-[a-z0-9][a-z0-9._-]{1,100}\b",
        r"\bdeep-research(?:-[a-z0-9._-]+)?\b",
        r"\bantigravity(?:-[a-z0-9._-]+)?\b",
    ]
    raw = []
    for pattern in patterns:
        raw.extend(_tokens(text, pattern))
    return _unique(Candidate(x.lower(), x.lower()) for x in raw)

def discover_xai(text: str) -> list[Candidate]:
    raw = _tokens(text, r"\bgrok-[0-9][0-9a-z]*(?:[._-][a-z0-9]+){0,8}\b")
    return _unique(Candidate(x.lower(), x.lower()) for x in raw)

def discover_mistral(text: str) -> list[Candidate]:
    # API-like identifiers only; avoids docs/package names such as *-readme or code-interpreter examples.
    patterns = [
        r"\bmistral-(?:large|medium|small)(?:-\d{4}|-latest)?\b",
        r"\bmistral-(?:ocr|saba|embed)(?:-\d{4}|-latest)?\b",
        r"\bministral-(?:3b|8b|14b|[0-9]+)(?:-\d{4}|-latest)?\b",
        r"\bcodestral(?:-mamba)?(?:-\d{4}|-latest)?\b",
        r"\bvoxtral-(?:mini|small)(?:-(?:transcribe|realtime|latest|\d{4})){0,3}\b",
        r"\bdevstral(?:-(?:small|medium))?(?:-\d{4}|-latest)?\b",
        r"\bmagistral-(?:small|medium)(?:-\d{4}|-latest)?\b",
        r"\bpixtral-(?:large|12b)(?:-\d{4}|-latest)?\b",
        r"\bopen-mistral-[a-z0-9]+(?:-[a-z0-9]+){0,2}\b",
        r"\bopen-mixtral-[a-z0-9x]+(?:-[a-z0-9]+){0,2}\b",
        r"\blabs-(?:leanstral|mistral-small-creative|devstral-small)(?:-[a-z0-9]+){0,3}\b",
    ]
    raw = []
    for pattern in patterns:
        raw.extend(_tokens(text, pattern))
    return _unique(Candidate(x.lower(), x.lower()) for x in raw)

def discover_meta(text: str) -> list[Candidate]:
    patterns = [
        (r"\bLlama\s+4\s+(?:Scout|Maverick)\b", "llama"),
        (r"\bLlama\s+3(?:\.\d)?\s*:\s*[0-9B& ]+\b", "llama"),
        (r"\bLlama\s+3(?:\.\d)?\s+(?:[0-9]+B(?:\s*&\s*[0-9]+B)?)\b", "llama"),
        (r"\bLlama\s+Guard\s+4(?:\s+\d+B)?\b", "safety"),
        (r"\bLlama\s+Prompt\s+Guard\s+2(?:\s+\d+[MB])?\b", "safety"),
    ]
    items = []
    for pattern, kind in patterns:
        for m in re.finditer(pattern, text, re.I):
            display = re.sub(r"\s+", " ", m.group(0)).strip()
            key = re.sub(r"[^a-z0-9]+", "-", display.lower()).strip("-")
            items.append(Candidate(key, display, kind))
    return _unique(items)

DISCOVERERS = {
    "openai": discover_openai,
    "anthropic": discover_anthropic,
    "google": discover_google,
    "mistral": discover_mistral,
    "xai": discover_xai,
    "meta": discover_meta,
}

def discover(provider_slug: str, text: str) -> list[Candidate]:
    fn = DISCOVERERS.get(provider_slug)
    return fn(text) if fn else []

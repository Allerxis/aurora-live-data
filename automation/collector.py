#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path

from adapters import discover
from openai_semantic import parse_openai_model_page
from anthropic_semantic import detail_slug_candidates, parse_anthropic_model_page, parse_anthropic_lifecycle_page
from google_semantic import parse_google_model_page, parse_google_lifecycle_page
from xai_semantic import parse_xai_model_page, parse_xai_knowledge_cutoffs, parse_xai_pricing_page, parse_xai_retirement_page
from mistral_semantic import extract_mistral_detail_urls, parse_mistral_model_page, parse_mistral_pricing_page
from meta_semantic import parse_llama4_model_card
from selector_view import build_selector
from guidance_view import build_guidance
from golden_suite import validate_golden_suite
from runtime_acceptance import build_runtime_document
from validation_manifest import build_traceability_document
from manifest_compare import build_comparison_document

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "automation" / "sources.json"
GUIDANCE_RULES_FILE = ROOT / "automation" / "guidance_rules.json"
EVAL_SPEC_FILE = ROOT / "automation" / "eval_spec.json"
GOLDEN_CASES_FILE = ROOT / "automation" / "golden_cases.json"
RUNTIME_POLICY_FILE = ROOT / "automation" / "runtime_policy.json"
TRACEABILITY_POLICY_FILE = ROOT / "automation" / "traceability_policy.json"
COMPARISON_POLICY_FILE = ROOT / "automation" / "comparison_policy.json"
REGISTRY_DIR = ROOT / "registry"
MODELS_DIR = REGISTRY_DIR / "models"
SOURCES_OUT = REGISTRY_DIR / "sources.json"
STATUS_OUT = REGISTRY_DIR / "status.json"
CHANGES_OUT = REGISTRY_DIR / "changes.json"
CATALOG_OUT = REGISTRY_DIR / "catalog.json"
SELECTOR_OUT = REGISTRY_DIR / "selector.json"
GUIDANCE_OUT = REGISTRY_DIR / "guidance.json"
EVALS_OUT = REGISTRY_DIR / "evals.json"
GOLDEN_OUT = REGISTRY_DIR / "golden.json"
RUNTIME_OUT = REGISTRY_DIR / "runtime.json"
TRACEABILITY_OUT = REGISTRY_DIR / "traceability.json"
COMPARISON_OUT = REGISTRY_DIR / "comparison.json"
SCHEMA_VERSION = "0.17.0"
MAX_CHANGE_HISTORY = 1000
PROVIDERS = ("openai", "anthropic", "google", "mistral", "xai", "meta")


def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def normalize_html(raw: bytes) -> bytes:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<noscript\b.*?</noscript>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", unescape(text)).strip()
    return text.encode("utf-8")


def fetch(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AuroraLiveData/0.17 (+public official-source monitor)",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.5",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=35) as resp:
        body = resp.read(8_000_000)
        return {
            "status": getattr(resp, "status", 200),
            "body": body,
            "etag": resp.headers.get("ETag"),
            "last_modified": resp.headers.get("Last-Modified"),
            "content_type": resp.headers.get("Content-Type"),
            "final_url": resp.geturl(),
        }


def read_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def stable_hash(value) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def add_change(
    changes: list,
    *,
    observed_at: str,
    entity_type: str,
    entity_key: str,
    change_type: str,
    previous_hash=None,
    new_hash=None,
    source_url=None,
    summary=None,
):
    changes.insert(
        0,
        {
            "observed_at": observed_at,
            "entity_type": entity_type,
            "entity_key": entity_key,
            "change_type": change_type,
            "previous_hash": previous_hash,
            "new_hash": new_hash,
            "source_url": source_url,
            "summary": summary,
        },
    )


def load_previous_models(provider: str):
    path = MODELS_DIR / f"{provider}.json"
    doc = read_json(path, {"models": []})
    return {
        m.get("model_key"): m
        for m in doc.get("models", [])
        if m.get("model_key")
    }


def verify_openai_candidates(candidates: dict, generated_at: str):
    verified = {}
    failures = {}

    for model_id in sorted(candidates):
        detail_url = f"https://developers.openai.com/api/docs/models/{model_id}"
        try:
            result = fetch(detail_url)
            final_url = result["final_url"].rstrip("/")
            expected_suffix = f"/api/docs/models/{model_id}"

            if not final_url.endswith(expected_suffix):
                raise RuntimeError(
                    f"unexpected redirect to {result['final_url']}"
                )

            normalized = normalize_html(result["body"])
            text = normalized.decode("utf-8", errors="replace")
            facts = parse_openai_model_page(
                model_id=model_id,
                text=text,
                source_url=result["final_url"],
            )
            if not facts:
                raise RuntimeError("detail page did not expose required deterministic fields")

            semantic_hash = stable_hash(facts)
            verified[model_id] = {
                "facts": facts,
                "semantic_hash": semantic_hash,
                "semantic_verified_at": generated_at,
                "semantic_source_url": result["final_url"],
            }
            print(
                f"[semantic-ok] openai:{model_id}: "
                f"context={facts.get('context_window_tokens')}, "
                f"output={facts.get('max_output_tokens')}"
            )
        except Exception as exc:
            failures[model_id] = f"{type(exc).__name__}: {exc}"
            print(f"[semantic-error] openai:{model_id}: {exc}")

    return verified, failures


def verify_anthropic_candidates(candidates: dict, generated_at: str):
    verified = {}
    failures = {}

    for model_id in sorted(candidates):
        last_error = None

        for slug in detail_slug_candidates(model_id):
            detail_url = f"https://platform.claude.com/docs/en/models/{slug}/overview"
            try:
                result = fetch(detail_url)
                final_url = result["final_url"].rstrip("/")
                expected_suffix = f"/docs/en/models/{slug}/overview"

                if not final_url.endswith(expected_suffix):
                    raise RuntimeError(
                        f"unexpected redirect to {result['final_url']}"
                    )

                normalized = normalize_html(result["body"])
                text = normalized.decode("utf-8", errors="replace")
                facts = parse_anthropic_model_page(
                    model_id=model_id,
                    text=text,
                    source_url=result["final_url"],
                )
                if not facts:
                    raise RuntimeError(
                        "detail page did not expose required deterministic fields"
                    )

                semantic_hash = stable_hash(facts)
                verified[model_id] = {
                    "facts": facts,
                    "semantic_hash": semantic_hash,
                    "semantic_verified_at": generated_at,
                    "semantic_source_url": result["final_url"],
                }
                print(
                    f"[semantic-ok] anthropic:{model_id}: "
                    f"context={facts.get('context_window_tokens')}, "
                    f"output={facts.get('max_output_tokens')}"
                )
                last_error = None
                break

            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"

        if model_id not in verified:
            failures[model_id] = last_error or "No matching official detail page"
            print(
                f"[semantic-error] anthropic:{model_id}: "
                f"{failures[model_id]}"
            )

    return verified, failures


def verify_google_candidates(candidates: dict, generated_at: str):
    verified = {}
    failures = {}

    for model_id, candidate in sorted(candidates.items()):
        detail_url = f"https://ai.google.dev/gemini-api/docs/models/{model_id}"
        try:
            result = fetch(detail_url)
            final_url = result["final_url"]

            if "/gemini-api/docs/models/" not in final_url:
                raise RuntimeError(
                    f"unexpected redirect to {result['final_url']}"
                )

            normalized = normalize_html(result["body"])
            text = normalized.decode("utf-8", errors="replace")
            facts = parse_google_model_page(
                model_id=model_id,
                text=text,
                source_url=result["final_url"],
            )
            if not facts:
                raise RuntimeError(
                    "detail page did not expose required deterministic fields"
                )

            semantic_hash = stable_hash(facts)
            verified[model_id] = {
                "facts": facts,
                "semantic_hash": semantic_hash,
                "semantic_verified_at": generated_at,
                "semantic_source_url": result["final_url"],
            }
            print(
                f"[semantic-ok] google:{model_id}: "
                f"input_limit={facts.get('input_token_limit')}, "
                f"output_limit={facts.get('output_token_limit')}"
            )
        except Exception as exc:
            failures[model_id] = f"{type(exc).__name__}: {exc}"
            print(f"[semantic-error] google:{model_id}: {exc}")

    return verified, failures


def verify_xai_candidates(candidates: dict, generated_at: str):
    verified = {}
    failures = {}

    for model_id in sorted(candidates):
        detail_url = f"https://docs.x.ai/developers/models/{model_id}"
        try:
            result = fetch(detail_url)
            final_url = result["final_url"].rstrip("/")
            expected_suffix = f"/developers/models/{model_id}"

            if not final_url.endswith(expected_suffix):
                raise RuntimeError(
                    f"unexpected redirect to {result['final_url']}"
                )

            normalized = normalize_html(result["body"])
            text = normalized.decode("utf-8", errors="replace")
            facts = parse_xai_model_page(
                model_id=model_id,
                text=text,
                source_url=result["final_url"],
            )
            if not facts:
                raise RuntimeError(
                    "detail page did not expose required deterministic fields"
                )

            semantic_hash = stable_hash(facts)
            verified[model_id] = {
                "facts": facts,
                "semantic_hash": semantic_hash,
                "semantic_verified_at": generated_at,
                "semantic_source_url": result["final_url"],
            }
            print(
                f"[semantic-ok] xai:{model_id}: "
                f"context={facts.get('context_window_tokens')}"
            )
        except Exception as exc:
            failures[model_id] = f"{type(exc).__name__}: {exc}"
            print(f"[semantic-error] xai:{model_id}: {exc}")

    return verified, failures


def verify_mistral_candidates(
    candidates: dict,
    detail_urls: list[str],
    pricing_rows: dict,
    generated_at: str,
    index_hash: str | None = None,
):
    verified = {}
    failures = {}

    for detail_url in detail_urls:
        try:
            result = fetch(detail_url)
            final_url = result["final_url"]
            if "/models/" not in final_url:
                continue

            normalized = normalize_html(result["body"])
            text = normalized.decode("utf-8", errors="replace")

            # Current cards may expose the API ID only on the detail page, while
            # the index uses a human title/version. Add those exact IDs to the
            # discovery set only because the detail URL itself came from the
            # official models index.
            for candidate in discover("mistral", text):
                candidates.setdefault(
                    candidate.model_key,
                    {
                        "model_key": candidate.model_key,
                        "display_name": candidate.display_name,
                        "kind": candidate.kind,
                        "source_keys": ["mistral-models"],
                        "source_urls": [final_url],
                        "source_hashes": (
                            {"mistral-models": index_hash}
                            if index_hash
                            else {}
                        ),
                    },
                )

            for model_id in sorted(candidates):
                if model_id in verified:
                    continue
                if not re.search(
                    rf"(?<![a-z0-9._-]){re.escape(model_id)}(?![a-z0-9._-])",
                    text,
                    re.I,
                ):
                    continue

                facts = parse_mistral_model_page(
                    model_id=model_id,
                    text=text,
                    source_url=final_url,
                )
                if not facts:
                    continue

                pricing_key = facts.get("pricing_key")
                if pricing_key and pricing_key in pricing_rows:
                    facts["pricing"] = pricing_rows[pricing_key]

                semantic_hash = stable_hash(facts)
                verified[model_id] = {
                    "facts": facts,
                    "semantic_hash": semantic_hash,
                    "semantic_verified_at": generated_at,
                    "semantic_source_url": final_url,
                }

                # Preserve direct semantic provenance even when the ID was
                # discovered only from the linked detail card.
                item = candidates[model_id]
                if final_url not in item["source_urls"]:
                    item["source_urls"].append(final_url)

                print(
                    f"[semantic-ok] mistral:{model_id}: "
                    f"context={facts.get('context_window_tokens')}, "
                    f"stage={facts.get('release_stage')}"
                )
        except Exception as exc:
            print(f"[semantic-page-error] mistral:{detail_url}: {exc}")

    for model_id in sorted(candidates):
        if model_id not in verified:
            failures[model_id] = "No matching verified Mistral model card"
            print(
                f"[semantic-error] mistral:{model_id}: "
                f"{failures[model_id]}"
            )

    return verified, failures


def main():
    now = utcnow()
    generated_at = iso(now)
    cfg = read_json(SOURCES_FILE, {"sources": []})
    previous_sources_doc = read_json(SOURCES_OUT, {"sources": []})
    previous_sources = {
        s.get("source_key"): s
        for s in previous_sources_doc.get("sources", [])
    }

    change_doc = read_json(CHANGES_OUT, {"changes": []})
    changes = list(change_doc.get("changes", []))

    previous_models = {
        provider: load_previous_models(provider)
        for provider in PROVIDERS
    }
    discovered = {provider: {} for provider in PROVIDERS}

    current_sources = []
    source_texts = {}
    reachable_count = 0
    fresh_count = 0

    for source in cfg.get("sources", []):
        key = source["source_key"]
        provider = source["provider_slug"]
        prev = previous_sources.get(key, {})
        freshness_hours = int(source.get("freshness_hours", 72))

        record = {
            "source_key": key,
            "provider_slug": provider,
            "label": source["label"],
            "url": source["url"],
            "final_url": prev.get("final_url"),
            "freshness_hours": freshness_hours,
            "last_checked_at": generated_at,
            "last_changed_at": prev.get("last_changed_at"),
            "content_hash": prev.get("content_hash"),
            "http_status": None,
            "is_reachable": False,
            "is_fresh": False,
            "etag": None,
            "last_modified": None,
            "content_type": None,
            "error": None,
            "discovered_model_candidates": 0,
        }

        try:
            result = fetch(source["url"])
            normalized = normalize_html(result["body"])
            normalized_text = normalized.decode("utf-8", errors="replace")
            new_hash = hashlib.sha256(normalized).hexdigest()
            source_texts[key] = {
                "text": normalized_text,
                "raw_html": result["body"].decode("utf-8", errors="replace"),
                "final_url": result["final_url"],
                "content_hash": new_hash,
            }
            status = int(result["status"])
            reachable = 200 <= status < 400

            record.update(
                {
                    "http_status": status,
                    "is_reachable": reachable,
                    "content_hash": new_hash,
                    "etag": result["etag"],
                    "last_modified": result["last_modified"],
                    "content_type": result["content_type"],
                    "final_url": result["final_url"],
                }
            )

            if reachable:
                reachable_count += 1

            previous_hash = prev.get("content_hash")
            if not previous_hash:
                record["last_changed_at"] = generated_at
                add_change(
                    changes,
                    observed_at=generated_at,
                    entity_type="source",
                    entity_key=key,
                    change_type="source_initialized",
                    previous_hash=None,
                    new_hash=new_hash,
                    source_url=result["final_url"],
                    summary="Official source initialized in Aurora Live Data.",
                )
            elif previous_hash != new_hash:
                record["last_changed_at"] = generated_at
                add_change(
                    changes,
                    observed_at=generated_at,
                    entity_type="source",
                    entity_key=key,
                    change_type="content_changed",
                    previous_hash=previous_hash,
                    new_hash=new_hash,
                    source_url=result["final_url"],
                    summary="Normalized official-source content changed.",
                )

            checked = parse_iso(record["last_checked_at"])
            record["is_fresh"] = bool(
                reachable
                and checked
                and now - checked <= timedelta(hours=freshness_hours)
            )
            if record["is_fresh"]:
                fresh_count += 1

            candidates = discover(provider, normalized_text)
            record["discovered_model_candidates"] = len(candidates)

            for candidate in candidates:
                item = discovered.setdefault(provider, {}).setdefault(
                    candidate.model_key,
                    {
                        "model_key": candidate.model_key,
                        "display_name": candidate.display_name,
                        "kind": candidate.kind,
                        "source_keys": [],
                        "source_urls": [],
                        "source_hashes": {},
                    },
                )
                if key not in item["source_keys"]:
                    item["source_keys"].append(key)
                if result["final_url"] not in item["source_urls"]:
                    item["source_urls"].append(result["final_url"])
                item["source_hashes"][key] = new_hash

            print(
                f"[ok] {key}: HTTP {status}, sha256={new_hash[:12]}…, "
                f"candidates={len(candidates)}"
            )

        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
            print(f"[error] {key}: {exc}")

        current_sources.append(record)

    current_sources.sort(
        key=lambda x: (x["provider_slug"], x["source_key"])
    )

    openai_verified, openai_semantic_failures = verify_openai_candidates(
        discovered.get("openai", {}),
        generated_at,
    )
    anthropic_verified, anthropic_semantic_failures = verify_anthropic_candidates(
        discovered.get("anthropic", {}),
        generated_at,
    )

    anthropic_lifecycle = {}
    lifecycle_source = source_texts.get("anthropic-deprecations")
    if lifecycle_source:
        anthropic_lifecycle = parse_anthropic_lifecycle_page(
            lifecycle_source["text"],
            lifecycle_source["final_url"],
        )

    google_verified, google_semantic_failures = verify_google_candidates(
        discovered.get("google", {}),
        generated_at,
    )
    google_lifecycle = {}
    google_lifecycle_source = source_texts.get("google-deprecations")
    if google_lifecycle_source:
        google_lifecycle = parse_google_lifecycle_page(
            google_lifecycle_source["text"],
            google_lifecycle_source["final_url"],
        )

    xai_verified, xai_semantic_failures = verify_xai_candidates(
        discovered.get("xai", {}),
        generated_at,
    )
    xai_cutoffs = {}
    xai_models_source = source_texts.get("xai-models")
    if xai_models_source:
        xai_cutoffs = parse_xai_knowledge_cutoffs(
            xai_models_source["text"],
            xai_models_source["final_url"],
        )

    # Knowledge cutoff statements live on the xAI catalog page rather than all
    # detail pages. Merge only an explicitly parsed cutoff into an otherwise
    # verified detail record, then recompute the semantic hash.
    for model_key, cutoff in xai_cutoffs.items():
        if model_key in xai_verified:
            xai_verified[model_key]["facts"]["knowledge_cutoff"] = cutoff.get(
                "knowledge_cutoff"
            )
            xai_verified[model_key]["facts"]["knowledge_cutoff_source_url"] = cutoff.get(
                "source_url"
            )
            xai_verified[model_key]["semantic_hash"] = stable_hash(
                xai_verified[model_key]["facts"]
            )

    xai_pricing = {}
    xai_pricing_source = source_texts.get("xai-pricing")
    if xai_pricing_source:
        xai_pricing = parse_xai_pricing_page(
            xai_pricing_source["text"],
            xai_pricing_source["final_url"],
        )

    # Pricing is maintained on a canonical xAI pricing page. Merge it only into
    # models whose detail pages were independently verified.
    for model_key, pricing in xai_pricing.items():
        if model_key in xai_verified:
            xai_verified[model_key]["facts"]["pricing"] = pricing
            if not xai_verified[model_key]["facts"].get("context_window_tokens"):
                xai_verified[model_key]["facts"]["context_window_tokens"] = pricing.get(
                    "context_window_tokens"
                )
            xai_verified[model_key]["semantic_hash"] = stable_hash(
                xai_verified[model_key]["facts"]
            )

    xai_retirements = {}
    xai_retirement_source = source_texts.get("xai-retirement-2026-05")
    if xai_retirement_source:
        xai_retirements = parse_xai_retirement_page(
            xai_retirement_source["text"],
            xai_retirement_source["final_url"],
        )

    mistral_pricing = {}
    mistral_pricing_source = source_texts.get("mistral-pricing")
    if mistral_pricing_source:
        mistral_pricing = parse_mistral_pricing_page(
            mistral_pricing_source["text"],
            mistral_pricing_source["final_url"],
        )

    mistral_detail_urls = set()
    for source_key in ("mistral-models", "mistral-labs"):
        source = source_texts.get(source_key)
        if source:
            mistral_detail_urls.update(
                extract_mistral_detail_urls(source.get("raw_html", ""))
            )

    mistral_verified, mistral_semantic_failures = verify_mistral_candidates(
        discovered.get("mistral", {}),
        sorted(mistral_detail_urls),
        mistral_pricing,
        generated_at,
        source_texts.get("mistral-models", {}).get("content_hash"),
    )

    meta_verified = {}
    meta_semantic_failures = {}
    meta_card_source = source_texts.get("meta-llama4-model-card")
    if meta_card_source:
        meta_facts = parse_llama4_model_card(
            meta_card_source.get("raw_html", ""),
            meta_card_source["final_url"],
        )
        for model_key, facts in meta_facts.items():
            discovered.setdefault("meta", {}).setdefault(
                model_key,
                {
                    "model_key": model_key,
                    "display_name": facts.get("display_name", model_key),
                    "kind": "model",
                    "source_keys": ["meta-llama4-model-card"],
                    "source_urls": [meta_card_source["final_url"]],
                    "source_hashes": {
                        "meta-llama4-model-card": meta_card_source.get("content_hash")
                    },
                },
            )
            semantic_hash = stable_hash(facts)
            meta_verified[model_key] = {
                "facts": facts,
                "semantic_hash": semantic_hash,
                "semantic_verified_at": generated_at,
                "semantic_source_url": meta_card_source["final_url"],
            }

    for model_key in sorted(discovered.get("meta", {})):
        if model_key not in meta_verified:
            meta_semantic_failures[model_key] = (
                "No matching structured record in the official Meta model card"
            )

    all_catalog_models = []
    present_total = 0
    retained_missing_total = 0
    semantic_verified_total = 0

    for provider in PROVIDERS:
        prev_by_key = previous_models.get(provider, {})
        current_by_key = discovered.get(provider, {})
        output_models = []

        for model_key, item in sorted(current_by_key.items()):
            prev = prev_by_key.get(model_key, {})
            was_present = bool(prev.get("present_in_current_sources"))

            verification_state = prev.get(
                "verification_state", "unverified"
            )
            lifecycle_status = prev.get("lifecycle_status", "unknown")
            facts = prev.get("facts", {})
            semantic_verified_at = prev.get("semantic_verified_at")
            semantic_source_url = prev.get("semantic_source_url")
            semantic_hash = prev.get("semantic_hash")
            semantic_error = None

            if provider == "openai":
                semantic = openai_verified.get(model_key)
                semantic_failure = openai_semantic_failures.get(model_key)
            elif provider == "anthropic":
                semantic = anthropic_verified.get(model_key)
                semantic_failure = anthropic_semantic_failures.get(model_key)
            elif provider == "google":
                semantic = google_verified.get(model_key)
                semantic_failure = google_semantic_failures.get(model_key)
            elif provider == "xai":
                semantic = xai_verified.get(model_key)
                semantic_failure = xai_semantic_failures.get(model_key)
            elif provider == "mistral":
                semantic = mistral_verified.get(model_key)
                semantic_failure = mistral_semantic_failures.get(model_key)
            elif provider == "meta":
                semantic = meta_verified.get(model_key)
                semantic_failure = meta_semantic_failures.get(model_key)
            else:
                semantic = None
                semantic_failure = None

            if semantic:
                new_semantic_hash = semantic["semantic_hash"]
                old_semantic_hash = semantic_hash

                facts = semantic["facts"]
                semantic_hash = new_semantic_hash
                semantic_verified_at = semantic["semantic_verified_at"]
                semantic_source_url = semantic["semantic_source_url"]
                verification_state = "verified_official_detail"
                semantic_verified_total += 1

                if provider == "anthropic":
                    lifecycle_status = (
                        facts.get("lifecycle", {}).get("status")
                        or lifecycle_status
                    )

                provider_label = {
                    "openai": "OpenAI",
                    "anthropic": "Anthropic",
                    "google": "Google",
                    "xai": "xAI",
                    "mistral": "Mistral",
                    "meta": "Meta",
                }.get(provider, provider)

                if not old_semantic_hash:
                    add_change(
                        changes,
                        observed_at=generated_at,
                        entity_type="model_semantics",
                        entity_key=f"{provider}:{model_key}",
                        change_type="semantic_verified",
                        previous_hash=None,
                        new_hash=new_semantic_hash,
                        source_url=semantic_source_url,
                        summary=(
                            "Deterministic facts were verified from the official "
                            f"{provider_label} model detail page."
                        ),
                    )
                elif old_semantic_hash != new_semantic_hash:
                    add_change(
                        changes,
                        observed_at=generated_at,
                        entity_type="model_semantics",
                        entity_key=f"{provider}:{model_key}",
                        change_type="semantic_changed",
                        previous_hash=old_semantic_hash,
                        new_hash=new_semantic_hash,
                        source_url=semantic_source_url,
                        summary=(
                            "Verified semantic facts changed on the official "
                            f"{provider_label} model detail page."
                        ),
                    )

            elif provider in ("openai", "anthropic", "google", "xai", "mistral", "meta"):
                semantic_error = semantic_failure
                if verification_state == "verified_official_detail":
                    verification_state = "verified_official_detail_stale"

            lifecycle = None
            if provider == "anthropic":
                lifecycle = anthropic_lifecycle.get(model_key)
                if lifecycle:
                    lifecycle_status = lifecycle.get("status") or lifecycle_status
            elif provider == "google":
                lifecycle = google_lifecycle.get(model_key)
                if lifecycle:
                    lifecycle_status = (
                        "shutdown_announced"
                        if lifecycle.get("shutdown_announced")
                        else "no_shutdown_announced"
                    )
            elif provider == "xai":
                lifecycle = xai_retirements.get(model_key)
                if lifecycle:
                    lifecycle_status = lifecycle.get("status") or lifecycle_status
            elif provider == "mistral" and semantic:
                lifecycle_status = (
                    semantic.get("facts", {}).get("release_stage")
                    or lifecycle_status
                )

            model = {
                "provider_slug": provider,
                "model_key": model_key,
                "display_name": item["display_name"],
                "kind": item["kind"],
                "discovery_state": (
                    "discovered_verified"
                    if verification_state == "verified_official_detail"
                    else "discovered_unverified"
                ),
                "verification_state": verification_state,
                "lifecycle_status": lifecycle_status,
                "lifecycle": lifecycle,
                "present_in_current_sources": True,
                "first_discovered_at": (
                    prev.get("first_discovered_at") or generated_at
                ),
                "last_seen_at": generated_at,
                "missing_since": None,
                "source_keys": sorted(item["source_keys"]),
                "source_urls": sorted(item["source_urls"]),
                "source_hashes": item["source_hashes"],
                "semantic_verified_at": semantic_verified_at,
                "semantic_source_url": semantic_source_url,
                "semantic_hash": semantic_hash,
                "semantic_error": semantic_error,
                "facts": facts,
                "notes": [
                    "Automatically discovered from official provider documentation.",
                    (
                        "Capabilities, limits, pricing and lifecycle are authoritative "
                        "only when verification_state is verified_official_detail."
                    ),
                ],
            }
            output_models.append(model)
            present_total += 1

            if not prev:
                add_change(
                    changes,
                    observed_at=generated_at,
                    entity_type="model_candidate",
                    entity_key=f"{provider}:{model_key}",
                    change_type="candidate_discovered",
                    summary=(
                        "A model identifier/name was newly discovered "
                        "in an official source."
                    ),
                )
            elif not was_present:
                add_change(
                    changes,
                    observed_at=generated_at,
                    entity_type="model_candidate",
                    entity_key=f"{provider}:{model_key}",
                    change_type="candidate_reappeared",
                    summary=(
                        "A previously missing model candidate reappeared "
                        "in official sources."
                    ),
                )

        for model_key, prev in sorted(prev_by_key.items()):
            if model_key in current_by_key:
                continue
            retained = dict(prev)
            if prev.get("present_in_current_sources"):
                retained["missing_since"] = generated_at
                add_change(
                    changes,
                    observed_at=generated_at,
                    entity_type="model_candidate",
                    entity_key=f"{provider}:{model_key}",
                    change_type="candidate_not_seen",
                    summary=(
                        "The candidate was not found in the currently monitored "
                        "official sources. This is not by itself proof of "
                        "deprecation or removal."
                    ),
                )
            retained["present_in_current_sources"] = False
            retained["discovery_state"] = "historical_unverified"
            output_models.append(retained)
            retained_missing_total += 1

        output_models.sort(
            key=lambda x: (
                not x.get("present_in_current_sources", False),
                x["model_key"],
            )
        )

        provider_doc = {
            "schema_version": SCHEMA_VERSION,
            "provider": provider,
            "generated_at": generated_at,
            "semantics": {
                "present_in_current_sources": (
                    "True means the deterministic discovery adapter found this "
                    "candidate during the current refresh. It does not by itself "
                    "prove API availability or product availability."
                ),
                "verification_state": (
                    "verified_official_detail means facts were parsed during this "
                    "refresh from a matching official model detail page. "
                    "verified_official_detail_stale preserves previously verified "
                    "facts but they must be revalidated before being treated as current."
                ),
            },
            "models": output_models,
        }
        write_json(MODELS_DIR / f"{provider}.json", provider_doc)
        all_catalog_models.extend(output_models)

    all_catalog_models.sort(
        key=lambda x: (
            x.get("provider_slug", ""),
            not x.get("present_in_current_sources", False),
            x["model_key"],
        )
    )

    provider_documents = {
        provider: read_json(MODELS_DIR / f"{provider}.json", {"models": []})
        for provider in PROVIDERS
    }
    selector_document = build_selector(
        provider_documents=provider_documents,
        generated_at=generated_at,
    )
    write_json(SELECTOR_OUT, selector_document)

    guidance_rules_document = read_json(
        GUIDANCE_RULES_FILE,
        {"rules": []},
    )
    previous_guidance_document = read_json(
        GUIDANCE_OUT,
        {"guidance": []},
    )
    guidance_document = build_guidance(
        rules_document=guidance_rules_document,
        source_texts=source_texts,
        previous_document=previous_guidance_document,
        generated_at=generated_at,
    )
    write_json(GUIDANCE_OUT, guidance_document)

    eval_spec_document = read_json(
        EVAL_SPEC_FILE,
        {"criteria": [], "test_case_templates": []},
    )
    eval_document = dict(eval_spec_document)
    eval_document["generated_at"] = generated_at
    eval_document["spec_hash"] = stable_hash(eval_spec_document)
    write_json(EVALS_OUT, eval_document)

    golden_cases_document = read_json(
        GOLDEN_CASES_FILE,
        {"cases": []},
    )
    golden_validation = validate_golden_suite(golden_cases_document)
    golden_document = dict(golden_cases_document)
    golden_document["generated_at"] = generated_at
    golden_document["suite_hash"] = golden_validation["suite_hash"]
    golden_document["validation"] = golden_validation
    write_json(GOLDEN_OUT, golden_document)

    runtime_policy_document = read_json(
        RUNTIME_POLICY_FILE,
        {},
    )
    benchmark_document = read_json(
        REGISTRY_DIR / "benchmarks.json",
        {},
    )
    runtime_document = build_runtime_document(
        policy=runtime_policy_document,
        eval_document=eval_document,
        golden_document=golden_document,
        benchmark_document=benchmark_document,
        generated_at=generated_at,
    )
    write_json(RUNTIME_OUT, runtime_document)

    traceability_policy_document = read_json(
        TRACEABILITY_POLICY_FILE,
        {},
    )
    traceability_document = build_traceability_document(
        policy=traceability_policy_document,
        generated_at=generated_at,
    )
    write_json(TRACEABILITY_OUT, traceability_document)

    comparison_policy_document = read_json(
        COMPARISON_POLICY_FILE,
        {},
    )
    comparison_document = build_comparison_document(
        policy=comparison_policy_document,
        generated_at=generated_at,
    )
    write_json(COMPARISON_OUT, comparison_document)

    changes = changes[:MAX_CHANGE_HISTORY]

    write_json(
        SOURCES_OUT,
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "sources": current_sources,
        },
    )
    write_json(
        CHANGES_OUT,
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "changes": changes,
        },
    )
    write_json(
        CATALOG_OUT,
        {
            "schema_version": SCHEMA_VERSION,
            "generated_at": generated_at,
            "warning": (
                "Discovery is not semantic verification. Use only records whose "
                "verification_state is verified_official_detail as authoritative "
                "for facts such as context, pricing, modalities, endpoints, "
                "features or tools."
            ),
            "models": all_catalog_models,
        },
    )
    write_json(
        STATUS_OUT,
        {
            "schema_version": SCHEMA_VERSION,
            "service": "Aurora Live Data",
            "generated_at": generated_at,
            "healthy": (
                len(current_sources) > 0
                and reachable_count == len(current_sources)
            ),
            "sources_total": len(current_sources),
            "sources_reachable": reachable_count,
            "sources_fresh": fresh_count,
            "model_candidates_present": present_total,
            "model_candidates_historical": retained_missing_total,
            "semantic_models_verified": semantic_verified_total,
            "openai_semantic_failures": len(openai_semantic_failures),
            "anthropic_semantic_failures": len(anthropic_semantic_failures),
            "anthropic_lifecycle_rows": len(anthropic_lifecycle),
            "google_semantic_failures": len(google_semantic_failures),
            "google_lifecycle_rows": len(google_lifecycle),
            "xai_semantic_failures": len(xai_semantic_failures),
            "xai_knowledge_cutoff_rows": len(xai_cutoffs),
            "xai_pricing_rows": len(xai_pricing),
            "xai_retirement_rows": len(xai_retirements),
            "mistral_detail_pages": len(mistral_detail_urls),
            "mistral_pricing_rows": len(mistral_pricing),
            "mistral_semantic_failures": len(mistral_semantic_failures),
            "meta_semantic_failures": len(meta_semantic_failures),
            "meta_semantic_verified": len(meta_verified),
            "selector_records": selector_document["counts"]["total"],
            "selector_default_include": selector_document["counts"]["include"],
            "selector_include_with_warning": selector_document["counts"]["include_with_warning"],
            "selector_specialized": selector_document["counts"]["specialized"],
            "selector_excluded": selector_document["counts"]["exclude"],
            "selector_stale": selector_document["counts"]["stale"],
            "guidance_total": guidance_document["counts"]["total"],
            "guidance_verified": guidance_document["counts"]["verified"],
            "guidance_stale": guidance_document["counts"]["stale"],
            "guidance_unverified": guidance_document["counts"]["unverified"],
            "eval_criteria": len(eval_document.get("criteria", [])),
            "eval_test_case_templates": len(eval_document.get("test_case_templates", [])),
            "eval_spec_hash": eval_document.get("spec_hash"),
            "golden_suite_gate": golden_validation.get("suite_gate"),
            "golden_cases": golden_validation.get("summary", {}).get("cases"),
            "golden_errors": golden_validation.get("summary", {}).get("errors"),
            "golden_warnings": golden_validation.get("summary", {}).get("warnings"),
            "golden_suite_hash": golden_validation.get("suite_hash"),
            "runtime_acceptance_ready": runtime_document.get("ready"),
            "runtime_policy_gate": runtime_document.get("validation", {}).get("suite_gate"),
            "runtime_policy_hash": runtime_document.get("validation", {}).get("policy_hash"),
            "runtime_operations": runtime_document.get("validation", {}).get("summary", {}).get("operations"),
            "traceability_ready": traceability_document.get("ready"),
            "traceability_policy_hash": traceability_document.get("policy_hash"),
            "traceability_persistence_default": traceability_document.get("privacy", {}).get("persistence_default"),
            "traceability_public_user_manifests": traceability_document.get("privacy", {}).get("public_registry_contains_user_manifests"),
            "comparison_ready": comparison_document.get("ready"),
            "comparison_policy_hash": comparison_document.get("policy_hash"),
            "comparison_persistence_default": comparison_document.get("storage", {}).get("persistence_default"),
            "comparison_public_history": comparison_document.get("storage", {}).get("public_registry_contains_comparison_history"),
        },
    )


if __name__ == "__main__":
    main()

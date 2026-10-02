#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "automation" / "sources.json"
REGISTRY_DIR = ROOT / "registry"
SOURCES_OUT = REGISTRY_DIR / "sources.json"
STATUS_OUT = REGISTRY_DIR / "status.json"
CHANGES_OUT = REGISTRY_DIR / "changes.json"
SCHEMA_VERSION = "0.1.0"
MAX_CHANGE_HISTORY = 500

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
    text = re.sub(r"<script\\b.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style\\b.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"\\s+", " ", unescape(text)).strip()
    return text.encode("utf-8")

def fetch(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AuroraLiveData/0.1 (+public source freshness monitor)",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.5",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=35) as resp:
        body = resp.read(5_000_000)
        return {
            "status": getattr(resp, "status", 200),
            "body": body,
            "etag": resp.headers.get("ETag"),
            "last_modified": resp.headers.get("Last-Modified"),
            "content_type": resp.headers.get("Content-Type"),
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

def main():
    now = utcnow()
    generated_at = iso(now)
    cfg = read_json(SOURCES_FILE, {"sources": []})
    previous_doc = read_json(SOURCES_OUT, {"sources": []})
    previous_by_key = {s.get("source_key"): s for s in previous_doc.get("sources", [])}

    change_doc = read_json(CHANGES_OUT, {"changes": []})
    changes = list(change_doc.get("changes", []))

    current = []
    reachable_count = 0
    fresh_count = 0

    for source in cfg.get("sources", []):
        key = source["source_key"]
        prev = previous_by_key.get(key, {})
        freshness_hours = int(source.get("freshness_hours", 72))

        record = {
            "source_key": key,
            "provider_slug": source["provider_slug"],
            "label": source["label"],
            "url": source["url"],
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
        }

        try:
            result = fetch(source["url"])
            normalized = normalize_html(result["body"])
            new_hash = hashlib.sha256(normalized).hexdigest()
            status = int(result["status"])
            reachable = 200 <= status < 400

            record.update({
                "http_status": status,
                "is_reachable": reachable,
                "content_hash": new_hash,
                "etag": result["etag"],
                "last_modified": result["last_modified"],
                "content_type": result["content_type"],
            })

            if reachable:
                reachable_count += 1

            previous_hash = prev.get("content_hash")
            if not previous_hash:
                record["last_changed_at"] = generated_at
                changes.insert(0, {
                    "observed_at": generated_at,
                    "entity_type": "source",
                    "entity_key": key,
                    "change_type": "source_initialized",
                    "previous_hash": None,
                    "new_hash": new_hash,
                    "source_url": source["url"],
                })
            elif previous_hash != new_hash:
                record["last_changed_at"] = generated_at
                changes.insert(0, {
                    "observed_at": generated_at,
                    "entity_type": "source",
                    "entity_key": key,
                    "change_type": "content_changed",
                    "previous_hash": previous_hash,
                    "new_hash": new_hash,
                    "source_url": source["url"],
                })

            checked = parse_iso(record["last_checked_at"])
            record["is_fresh"] = bool(
                reachable and checked and now - checked <= timedelta(hours=freshness_hours)
            )
            if record["is_fresh"]:
                fresh_count += 1

            print(f"[ok] {key}: HTTP {status}, sha256={new_hash[:12]}…")

        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
            print(f"[error] {key}: {exc}")

        current.append(record)

    current.sort(key=lambda x: (x["provider_slug"], x["source_key"]))
    changes = changes[:MAX_CHANGE_HISTORY]

    write_json(SOURCES_OUT, {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "sources": current,
    })
    write_json(CHANGES_OUT, {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "changes": changes,
    })
    write_json(STATUS_OUT, {
        "schema_version": SCHEMA_VERSION,
        "service": "Aurora Live Data",
        "generated_at": generated_at,
        "healthy": len(current) > 0 and reachable_count == len(current),
        "sources_total": len(current),
        "sources_reachable": reachable_count,
        "sources_fresh": fresh_count,
    })

if __name__ == "__main__":
    main()

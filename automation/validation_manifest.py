from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any


FORBIDDEN_KEYS = {
    "prompt",
    "prompt_text",
    "user_input",
    "input_text",
    "output_text",
    "tool_output",
    "secret",
    "secrets",
    "token",
    "password",
    "api_key",
    "authorization",
}

ALLOWED_GATES = {"PASS", "NEEDS_REVIEW", "FAIL"}


def stable_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sanitize_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _sanitize_object(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            key_l = str(key).lower()
            if key_l in FORBIDDEN_KEYS:
                continue
            cleaned[str(key)] = _sanitize_object(item)
        return cleaned
    if isinstance(value, list):
        return [_sanitize_object(x) for x in value]
    return _sanitize_scalar(value)


def _manifest_id(payload: dict[str, Any]) -> str:
    # ID is derived only from non-content validation metadata.
    base = {
        "validated_at": payload.get("validated_at"),
        "operation": payload.get("operation"),
        "target": payload.get("target"),
        "dependencies": payload.get("dependencies"),
        "release": payload.get("release"),
        "contracts_applied": payload.get("contracts_applied"),
    }
    return "vm_" + stable_hash(base)[:20]


def create_validation_manifest(
    *,
    aurora_version: str,
    live_data_status: dict[str, Any],
    runtime_document: dict[str, Any],
    operation: str,
    target: dict[str, Any] | None,
    contracts_applied: list[str] | None,
    guidance_applied: list[dict[str, Any]] | None,
    eval_release_gate: str,
    golden_release_gate: str,
    final_release_gate: str,
    repair_passes: int,
    unresolved: list[Any] | None,
    validated_at: str | None = None,
    prompt_fingerprint: str | None = None,
) -> dict[str, Any]:
    validated_at = validated_at or _utc_iso()

    dependencies = {
        "eval_spec_hash": live_data_status.get("eval_spec_hash"),
        "golden_suite_hash": live_data_status.get("golden_suite_hash"),
        "runtime_policy_hash": live_data_status.get("runtime_policy_hash"),
        "benchmark_corpus_hash": live_data_status.get("benchmark_corpus_hash"),
        "traceability_policy_hash": live_data_status.get("traceability_policy_hash"),
    }

    safe_target = {
        "provider_slug": None,
        "model_key": None,
        "verification_state": None,
        "semantic_verified_at": None,
        "semantic_source_url": None,
    }
    if target:
        for key in safe_target:
            if key in target:
                safe_target[key] = target.get(key)

    guidance = []
    for item in guidance_applied or []:
        guidance.append({
            "id": item.get("id"),
            "provider_slug": item.get("provider_slug"),
            "verification_state": item.get("verification_state"),
            "verified_at": item.get("verified_at"),
            "source_hash": item.get("source_hash"),
        })

    manifest = {
        "schema_version": "1.0.0",
        "manifest_id": None,
        "aurora_version": aurora_version,
        "live_data_version": live_data_status.get("schema_version"),
        "registry_generated_at": live_data_status.get("generated_at"),
        "validated_at": validated_at,
        "operation": operation,
        "target": safe_target,
        "dependencies": dependencies,
        "contracts_applied": sorted(set(contracts_applied or [])),
        "guidance_applied": guidance,
        "runtime_ready": runtime_document.get("ready"),
        "release": {
            "eval_release_gate": eval_release_gate,
            "golden_release_gate": golden_release_gate,
            "final_release_gate": final_release_gate,
        },
        "repair_passes": int(repair_passes),
        "unresolved": _sanitize_object(unresolved or []),
        "privacy": {
            "prompt_content_included": False,
            "persisted": False,
            "prompt_fingerprint_included": bool(prompt_fingerprint),
        },
    }

    if prompt_fingerprint:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", prompt_fingerprint):
            raise ValueError("prompt_fingerprint must be a SHA-256 hex digest")
        manifest["prompt_fingerprint_sha256"] = prompt_fingerprint.lower()

    manifest["manifest_id"] = _manifest_id(manifest)
    return manifest


def validate_manifest(
    manifest: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required = policy.get("manifest_schema", {}).get("required_fields", [])
    for field in required:
        if field not in manifest:
            errors.append({
                "path": field,
                "message": "Required manifest field is missing.",
            })

    operation_values = set(
        policy.get("manifest_schema", {}).get("operation_values", [])
    )
    if manifest.get("operation") not in operation_values:
        errors.append({
            "path": "operation",
            "message": f"Unsupported operation {manifest.get('operation')!r}.",
        })

    release = manifest.get("release", {})
    for key in (
        "eval_release_gate",
        "golden_release_gate",
        "final_release_gate",
    ):
        if release.get(key) not in ALLOWED_GATES:
            errors.append({
                "path": f"release.{key}",
                "message": "Invalid release gate.",
            })

    privacy = manifest.get("privacy", {})
    if privacy.get("prompt_content_included") is not False:
        errors.append({
            "path": "privacy.prompt_content_included",
            "message": "Prompt content must not be included.",
        })
    if privacy.get("persisted") is not False:
        warnings.append({
            "path": "privacy.persisted",
            "message": "Persistence is disabled by default; explicit user action is required.",
        })

    serialized = json.dumps(manifest, ensure_ascii=False).lower()
    for forbidden in FORBIDDEN_KEYS:
        # Keys are the real concern. This broad search is only a secondary guard,
        # so exempt the explicit privacy/fingerprint metadata names.
        if forbidden in {"prompt", "token"}:
            continue
        if f'"{forbidden}"' in serialized:
            errors.append({
                "path": forbidden,
                "message": "Forbidden sensitive/content field detected.",
            })

    deps = manifest.get("dependencies", {})
    required_dependency_fields = policy.get(
        "manifest_schema", {}
    ).get("dependency_fields", [])
    missing_deps = [
        key for key in required_dependency_fields
        if not deps.get(key)
    ]
    if missing_deps:
        warnings.append({
            "path": "dependencies",
            "message": f"Missing dependency hashes: {missing_deps}",
        })

    return {
        "schema_version": "1.0.0",
        "suite_gate": "pass" if not errors else "fail",
        "manifest_hash": stable_hash(manifest),
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }


def build_traceability_document(
    *,
    policy: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    policy_hash = stable_hash(policy)
    return {
        "schema_version": policy.get("schema_version", "1.0.0"),
        "generated_at": generated_at,
        "ready": True,
        "policy_hash": policy_hash,
        "privacy": policy.get("privacy", {}),
        "manifest_schema": policy.get("manifest_schema", {}),
        "provenance": policy.get("provenance", {}),
        "behavior": policy.get("behavior", {}),
        "example_manifest": policy.get("example_manifest"),
    }

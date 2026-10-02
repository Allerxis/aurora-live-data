from __future__ import annotations

import hashlib
import json
from typing import Any


GATE_ORDER = {
    "FAIL": 0,
    "NEEDS_REVIEW": 1,
    "PASS": 2,
}


def stable_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _guidance_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("id")): item
        for item in manifest.get("guidance_applied", [])
        if isinstance(item, dict) and item.get("id")
    }


def _unresolved_keys(manifest: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for item in manifest.get("unresolved", []) or []:
        if isinstance(item, dict):
            key = (
                item.get("criterion")
                or item.get("id")
                or item.get("code")
                or stable_hash(item)[:16]
            )
        else:
            key = str(item)
        keys.add(str(key))
    return keys


def _change(kind: str, path: str, before: Any, after: Any) -> dict[str, Any]:
    return {
        "type": kind,
        "path": path,
        "before": before,
        "after": after,
    }


def compare_manifests(
    old: dict[str, Any],
    new: dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = policy or {}
    changes: list[dict[str, Any]] = []

    same_schema = old.get("schema_version") == new.get("schema_version")
    coverage = "full" if same_schema else "partial"

    if old.get("aurora_version") != new.get("aurora_version"):
        changes.append(_change(
            "version_changed",
            "aurora_version",
            old.get("aurora_version"),
            new.get("aurora_version"),
        ))

    if old.get("live_data_version") != new.get("live_data_version"):
        changes.append(_change(
            "version_changed",
            "live_data_version",
            old.get("live_data_version"),
            new.get("live_data_version"),
        ))

    if old.get("operation") != new.get("operation"):
        changes.append(_change(
            "version_changed",
            "operation",
            old.get("operation"),
            new.get("operation"),
        ))

    old_target = old.get("target") or {}
    new_target = new.get("target") or {}
    target_fields = (
        "provider_slug",
        "model_key",
        "verification_state",
        "semantic_verified_at",
        "semantic_source_url",
        "semantic_hash",
    )
    for field in target_fields:
        if old_target.get(field) != new_target.get(field):
            changes.append(_change(
                "target_changed",
                f"target.{field}",
                old_target.get(field),
                new_target.get(field),
            ))

    old_deps = old.get("dependencies") or {}
    new_deps = new.get("dependencies") or {}
    dependency_keys = sorted(set(old_deps) | set(new_deps))
    for key in dependency_keys:
        if old_deps.get(key) != new_deps.get(key):
            changes.append(_change(
                "dependency_changed",
                f"dependencies.{key}",
                old_deps.get(key),
                new_deps.get(key),
            ))

    old_contracts = set(old.get("contracts_applied") or [])
    new_contracts = set(new.get("contracts_applied") or [])
    for contract_id in sorted(new_contracts - old_contracts):
        changes.append(_change(
            "contract_added",
            "contracts_applied",
            None,
            contract_id,
        ))
    for contract_id in sorted(old_contracts - new_contracts):
        changes.append(_change(
            "contract_removed",
            "contracts_applied",
            contract_id,
            None,
        ))

    old_guidance = _guidance_map(old)
    new_guidance = _guidance_map(new)
    for rule_id in sorted(set(new_guidance) - set(old_guidance)):
        changes.append(_change(
            "guidance_added",
            f"guidance_applied.{rule_id}",
            None,
            new_guidance[rule_id],
        ))
    for rule_id in sorted(set(old_guidance) - set(new_guidance)):
        changes.append(_change(
            "guidance_removed",
            f"guidance_applied.{rule_id}",
            old_guidance[rule_id],
            None,
        ))
    for rule_id in sorted(set(old_guidance) & set(new_guidance)):
        before = old_guidance[rule_id]
        after = new_guidance[rule_id]
        revision_fields = (
            "verification_state",
            "verified_at",
            "source_hash",
        )
        revision_before = {k: before.get(k) for k in revision_fields}
        revision_after = {k: after.get(k) for k in revision_fields}
        if revision_before != revision_after:
            changes.append(_change(
                "guidance_revision_changed",
                f"guidance_applied.{rule_id}",
                revision_before,
                revision_after,
            ))

    old_release = old.get("release") or {}
    new_release = new.get("release") or {}
    old_gate = old_release.get("final_release_gate")
    new_gate = new_release.get("final_release_gate")

    if old_gate == new_gate:
        release_transition = "unchanged"
    elif old_gate in GATE_ORDER and new_gate in GATE_ORDER:
        release_transition = (
            "less_restrictive"
            if GATE_ORDER[new_gate] > GATE_ORDER[old_gate]
            else "more_restrictive"
        )
        changes.append(_change(
            f"gate_{release_transition}",
            "release.final_release_gate",
            old_gate,
            new_gate,
        ))
    else:
        release_transition = "unknown"
        changes.append(_change(
            "dependency_changed",
            "release.final_release_gate",
            old_gate,
            new_gate,
        ))

    if old.get("repair_passes") != new.get("repair_passes"):
        changes.append(_change(
            "repair_count_changed",
            "repair_passes",
            old.get("repair_passes"),
            new.get("repair_passes"),
        ))

    old_unresolved = _unresolved_keys(old)
    new_unresolved = _unresolved_keys(new)
    for key in sorted(new_unresolved - old_unresolved):
        changes.append(_change(
            "unresolved_added",
            "unresolved",
            None,
            key,
        ))
    for key in sorted(old_unresolved - new_unresolved):
        changes.append(_change(
            "unresolved_removed",
            "unresolved",
            key,
            None,
        ))

    old_fp = old.get("prompt_fingerprint_sha256")
    new_fp = new.get("prompt_fingerprint_sha256")
    if old_fp and new_fp:
        if old_fp == new_fp:
            prompt_identity = "same"
            changes.append(_change(
                "fingerprint_unchanged",
                "prompt_fingerprint_sha256",
                old_fp,
                new_fp,
            ))
        else:
            prompt_identity = "different"
            changes.append(_change(
                "fingerprint_changed",
                "prompt_fingerprint_sha256",
                old_fp,
                new_fp,
            ))
    else:
        prompt_identity = "unknown"

    comparison_core = {
        "from_manifest_id": old.get("manifest_id"),
        "to_manifest_id": new.get("manifest_id"),
        "changes": changes,
        "release_transition": {
            "from": old_gate,
            "to": new_gate,
            "classification": release_transition,
        },
        "prompt_identity": prompt_identity,
    }

    comparison_id = "cmp_" + stable_hash(comparison_core)[:20]

    summary = {
        "change_count": len(changes),
        "version_changes": sum(x["type"] == "version_changed" for x in changes),
        "target_changes": sum(x["type"] == "target_changed" for x in changes),
        "dependency_changes": sum(x["type"] == "dependency_changed" for x in changes),
        "contract_changes": sum(
            x["type"] in {"contract_added", "contract_removed"}
            for x in changes
        ),
        "guidance_changes": sum(
            x["type"] in {
                "guidance_added",
                "guidance_removed",
                "guidance_revision_changed",
            }
            for x in changes
        ),
        "unresolved_changes": sum(
            x["type"] in {"unresolved_added", "unresolved_removed"}
            for x in changes
        ),
    }

    return {
        "schema_version": "1.0.0",
        "comparison_id": comparison_id,
        "from_manifest_id": old.get("manifest_id"),
        "to_manifest_id": new.get("manifest_id"),
        "comparable": True,
        "coverage": coverage,
        "changes": changes,
        "release_transition": comparison_core["release_transition"],
        "prompt_identity": prompt_identity,
        "summary": summary,
    }


def build_comparison_document(
    *,
    policy: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": policy.get("schema_version", "1.0.0"),
        "generated_at": generated_at,
        "ready": True,
        "policy_hash": stable_hash(policy),
        "storage": policy.get("storage", {}),
        "comparability": policy.get("comparability", {}),
        "dimensions": policy.get("dimensions", []),
        "change_types": policy.get("change_types", {}),
        "interpretation_rules": policy.get("interpretation_rules", []),
        "output": policy.get("output", {}),
    }

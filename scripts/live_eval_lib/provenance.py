"""Validate live-evaluation provenance records."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any


RUN_MANIFEST_FIELDS = {
    "schema_version",
    "run_id",
    "suite",
    "auth_mode",
    "started_at",
    "completed_at",
    "model",
    "reasoning_effort",
    "codex_version",
    "runner_commit",
    "runner_dirty",
    "dataset_path",
    "dataset_sha256",
    "policy_sha256",
    "case_set",
    "attempts",
    "plugin_versions",
    "platform",
    "observation_scope",
    "results_path",
    "summary_path",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_run_manifest(run: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    missing = sorted(RUN_MANIFEST_FIELDS - set(run))
    extra = sorted(set(run) - RUN_MANIFEST_FIELDS)
    if missing:
        failures.append(f"run manifest missing fields: {missing}")
    if extra:
        failures.append(f"run manifest has unknown fields: {extra}")
    if run.get("schema_version") != "1.1.0":
        failures.append("run manifest schema_version must be 1.1.0")
    if run.get("suite") not in {"routing", "tool-trace"}:
        failures.append("run manifest suite is invalid")
    if run.get("auth_mode") not in {"saved", "api-key"}:
        failures.append("run manifest auth_mode is invalid")
    if run.get("case_set") not in {"critical", "sample", "full"}:
        failures.append("run manifest case_set is invalid")
    if not isinstance(run.get("attempts"), int) or run.get("attempts", 0) < 1:
        failures.append("run manifest attempts must be at least 1")
    for field in (
        "run_id",
        "model",
        "reasoning_effort",
        "codex_version",
        "dataset_path",
        "results_path",
        "summary_path",
    ):
        if not isinstance(run.get(field), str) or not run[field]:
            failures.append(f"run manifest {field} must be a non-empty string")
    if not isinstance(run.get("runner_commit"), str) or re.fullmatch(
        r"[0-9a-f]{40}", run.get("runner_commit", "")
    ) is None:
        failures.append("run manifest runner_commit must be a 40-character Git SHA")
    if not isinstance(run.get("runner_dirty"), bool):
        failures.append("run manifest runner_dirty must be boolean")
    for field in ("dataset_sha256", "policy_sha256"):
        if not isinstance(run.get(field), str) or re.fullmatch(
            r"[0-9a-f]{64}", run.get(field, "")
        ) is None:
            failures.append(f"run manifest {field} must be a lowercase SHA-256")
    timestamps: dict[str, datetime] = {}
    for field in ("started_at", "completed_at"):
        value = run.get(field)
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else None
            if parsed is None or parsed.tzinfo is None:
                raise ValueError
            timestamps[field] = parsed
        except ValueError:
            failures.append(f"run manifest {field} must be an ISO-8601 timestamp with timezone")
    if set(timestamps) == {"started_at", "completed_at"} and timestamps["completed_at"] < timestamps["started_at"]:
        failures.append("run manifest completed_at cannot precede started_at")
    versions = run.get("plugin_versions")
    if (
        not isinstance(versions, dict)
        or not versions
        or any(not isinstance(name, str) or not isinstance(version, str) or not version for name, version in versions.items())
    ):
        failures.append("run manifest plugin_versions must be a non-empty string map")
    platform_value = run.get("platform")
    if not isinstance(platform_value, dict) or set(platform_value) != {
        "system",
        "release",
        "machine",
        "python",
    } or any(not isinstance(value, str) for value in platform_value.values()):
        failures.append("run manifest platform must contain system, release, machine, and python")
    expected_scope = {
        "routing": "structured-routing-decision",
        "tool-trace": "transcript-and-tool-trace",
    }.get(run.get("suite"))
    if expected_scope is not None and run.get("observation_scope") != expected_scope:
        failures.append(f"run manifest observation_scope must be {expected_scope}")
    return failures

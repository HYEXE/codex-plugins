#!/usr/bin/env python3
"""Validate observation manifests and immutable dataset/result provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HEX_SHA256_LENGTH = 64


class ObservationManifestError(RuntimeError):
    """Raised when an observation manifest cannot be read safely."""


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ObservationManifestError(f"{path}: expected a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_contained(base: Path, relative: Any, boundary: Path, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ObservationManifestError(f"{label} must be a non-empty relative path")
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(boundary.resolve())
    except ValueError as exc:
        raise ObservationManifestError(f"{label} escapes its validation boundary: {relative}") from exc
    return candidate


def parse_observed_at(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ObservationManifestError("observed_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservationManifestError("observed_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ObservationManifestError("observed_at must include a timezone")
    if parsed > datetime.now(timezone.utc):
        raise ObservationManifestError("observed_at cannot be in the future")
    return parsed


def valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == HEX_SHA256_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def validate_metadata(
    metadata_path: Path, *, expected_suite: str, boundary: Path
) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    try:
        metadata = load_object(metadata_path)
    except (OSError, json.JSONDecodeError, ObservationManifestError) as exc:
        return None, [str(exc)]

    if metadata.get("schema_version") != "1.0.0":
        failures.append(f"{metadata_path}: schema_version must be 1.0.0")
    if metadata.get("suite") != expected_suite:
        failures.append(
            f"{metadata_path}: suite must be {expected_suite!r}, got {metadata.get('suite')!r}"
        )
    provenance = metadata.get("provenance_status")
    if provenance not in {"complete", "legacy-partial"}:
        failures.append(f"{metadata_path}: invalid provenance_status {provenance!r}")
    for field in ("source", "observation_scope"):
        if not isinstance(metadata.get(field), str) or not metadata[field].strip():
            failures.append(f"{metadata_path}: {field} must be a non-empty string")
    try:
        parse_observed_at(metadata.get("observed_at"))
    except ObservationManifestError as exc:
        failures.append(f"{metadata_path}: {exc}")

    plugin_versions = metadata.get("plugin_versions")
    if (
        not isinstance(plugin_versions, dict)
        or not plugin_versions
        or any(not isinstance(name, str) or not isinstance(version, str) or not version for name, version in plugin_versions.items())
    ):
        failures.append(f"{metadata_path}: plugin_versions must be a non-empty string map")

    if provenance == "complete":
        for field in ("run_id", "model", "codex_version"):
            if not isinstance(metadata.get(field), str) or not metadata[field].strip():
                failures.append(f"{metadata_path}: complete provenance requires {field}")
    elif provenance == "legacy-partial":
        if not isinstance(metadata.get("notes"), str) or not metadata["notes"].strip():
            failures.append(f"{metadata_path}: legacy-partial provenance requires notes")

    resolved: dict[str, Any] = {"metadata_path": metadata_path, "metadata": metadata}
    for path_field, hash_field in (("dataset", "dataset_sha256"), ("results", "results_sha256")):
        try:
            path = resolve_contained(metadata_path.parent, metadata.get(path_field), boundary, path_field)
        except ObservationManifestError as exc:
            failures.append(f"{metadata_path}: {exc}")
            continue
        resolved[f"{path_field}_path"] = path
        if not path.is_file():
            failures.append(f"{metadata_path}: missing {path_field} file {path}")
            continue
        expected_hash = metadata.get(hash_field)
        if not valid_sha256(expected_hash):
            failures.append(f"{metadata_path}: {hash_field} must be a lowercase SHA-256")
            continue
        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            failures.append(
                f"{metadata_path}: {path_field} hash mismatch: expected {expected_hash}, got {actual_hash}"
            )
    return resolved, failures


def validate_manifest(
    manifest_path: Path, *, boundary: Path | None = None
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    manifest_path = manifest_path.resolve()
    boundary = (boundary or ROOT).resolve()
    try:
        manifest_path.relative_to(boundary)
    except ValueError:
        return {}, [f"{manifest_path}: manifest escapes validation boundary {boundary}"]
    try:
        manifest = load_object(manifest_path)
    except (OSError, json.JSONDecodeError, ObservationManifestError) as exc:
        return {}, [str(exc)]

    failures: list[str] = []
    resolved_suites: dict[str, dict[str, Any]] = {}
    if manifest.get("schema_version") != "1.0.0":
        failures.append(f"{manifest_path}: schema_version must be 1.0.0")
    suites = manifest.get("suites")
    if not isinstance(suites, dict) or not suites:
        return {}, [*failures, f"{manifest_path}: suites must be a non-empty object"]

    for suite, entry in suites.items():
        if not isinstance(suite, str) or not suite or not isinstance(entry, dict):
            failures.append(f"{manifest_path}: invalid suite entry {suite!r}")
            continue
        try:
            metadata_path = resolve_contained(
                manifest_path.parent, entry.get("metadata"), boundary, f"{suite}.metadata"
            )
        except ObservationManifestError as exc:
            failures.append(f"{manifest_path}: {exc}")
            continue
        resolved, metadata_failures = validate_metadata(
            metadata_path, expected_suite=suite, boundary=boundary
        )
        failures.extend(metadata_failures)
        if resolved is not None:
            resolved_suites[suite] = resolved
    return resolved_suites, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="+", help="Observation manifest path")
    parser.add_argument("--boundary", type=Path, default=ROOT)
    args = parser.parse_args()

    failures: list[str] = []
    suite_count = 0
    for manifest_path in args.manifest:
        suites, manifest_failures = validate_manifest(manifest_path, boundary=args.boundary)
        suite_count += len(suites)
        failures.extend(manifest_failures)
    if failures:
        print("OBSERVATION MANIFEST VALIDATION FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"OBSERVATION MANIFEST VALIDATION PASSED: {suite_count} suites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

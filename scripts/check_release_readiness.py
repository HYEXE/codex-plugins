#!/usr/bin/env python3
"""Check files and markers required before a public repository release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "release" / "release-policy.json"


def load_policy(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("release policy must be an object")
    return value


def check_release_readiness(root: Path, policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if policy.get("schema_version") != "1.0.0":
        failures.append("release policy schema_version must be 1.0.0")
    required_files = policy.get("required_public_release_files")
    if not isinstance(required_files, list) or any(not isinstance(path, str) for path in required_files):
        failures.append("required_public_release_files must be a string array")
        required_files = []
    markers = policy.get("forbidden_release_markers")
    if not isinstance(markers, list) or any(not isinstance(marker, str) for marker in markers):
        failures.append("forbidden_release_markers must be a string array")
        markers = []
    attribution_sources = policy.get("required_attribution_sources")
    if not isinstance(attribution_sources, list) or any(
        not isinstance(path, str) for path in attribution_sources
    ):
        failures.append("required_attribution_sources must be a string array")
        attribution_sources = []

    for relative in required_files:
        target = (root / relative).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            failures.append(f"required release path escapes repository: {relative}")
            continue
        if not target.is_file():
            failures.append(f"missing required public release file: {relative}")
            continue
        text = target.read_text(encoding="utf-8")
        if not text.strip():
            failures.append(f"required public release file is empty: {relative}")
        for marker in markers:
            if marker in text:
                failures.append(f"{relative} contains unresolved release marker: {marker}")
    for relative in attribution_sources:
        target = (root / relative).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            failures.append(f"required attribution path escapes repository: {relative}")
            continue
        if not target.is_file():
            failures.append(f"missing required attribution source: {relative}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    try:
        policy = load_policy(args.policy.resolve())
        failures = check_release_readiness(args.root.resolve(), policy)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    if failures:
        print("PUBLIC RELEASE READINESS FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PUBLIC RELEASE READINESS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

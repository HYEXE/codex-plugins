#!/usr/bin/env python3
"""Require a plugin manifest version increase when shipped plugin files change."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\."
    r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
IGNORED_TOP_LEVEL = {"README.md", "CHANGELOG.md"}
IGNORED_PREFIXES = {"reports"}


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def load_json_text(text: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label}: manifest must be an object")
    return value


def version_key(
    version: str,
) -> tuple[int, int, int, int, tuple[tuple[int, int | str], ...]]:
    match = SEMVER_RE.fullmatch(version)
    if not match:
        raise ValueError(f"invalid semantic version: {version}")
    major, minor, patch = (int(match.group(index)) for index in range(1, 4))
    prerelease = match.group(4)
    identifiers = () if prerelease is None else tuple(
        (0, int(identifier)) if identifier.isdigit() else (1, identifier)
        for identifier in prerelease.split(".")
    )
    return major, minor, patch, 1 if prerelease is None else 0, identifiers


def is_version_affecting(relative: Path) -> bool:
    if len(relative.parts) == 1 and relative.name in IGNORED_TOP_LEVEL:
        return False
    return bool(relative.parts) and relative.parts[0] not in IGNORED_PREFIXES


def manifest_at(ref: str, path: Path) -> dict[str, Any] | None:
    result = git("show", f"{ref}:{path.as_posix()}", check=False)
    if result.returncode:
        return None
    return load_json_text(result.stdout, f"{ref}:{path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Base Git commit or ref")
    parser.add_argument("--head", default="HEAD", help="Head Git commit or ref")
    args = parser.parse_args()

    if args.base and set(args.base) == {"0"}:
        print("PLUGIN VERSION CHECK SKIPPED: initial push has no base commit")
        return 0

    if git("rev-parse", "--verify", f"{args.base}^{{commit}}", check=False).returncode:
        print(f"ERROR: base commit is unavailable: {args.base}")
        return 1
    if git("rev-parse", "--verify", f"{args.head}^{{commit}}", check=False).returncode:
        print(f"ERROR: head commit is unavailable: {args.head}")
        return 1

    diff = git("diff", "--name-only", "--diff-filter=ACDMRT", f"{args.base}...{args.head}", "--", "plugins")
    changed_by_plugin: dict[str, list[str]] = {}
    for raw_path in diff.stdout.splitlines():
        path = Path(raw_path)
        if len(path.parts) < 3 or path.parts[0] != "plugins":
            continue
        plugin_name = path.parts[1]
        relative = Path(*path.parts[2:])
        if is_version_affecting(relative):
            changed_by_plugin.setdefault(plugin_name, []).append(raw_path)

    failures: list[str] = []
    checked = 0
    for plugin_name, changed_paths in sorted(changed_by_plugin.items()):
        manifest_relative = Path("plugins") / plugin_name / ".codex-plugin" / "plugin.json"
        try:
            current = manifest_at(args.head, manifest_relative)
            previous = manifest_at(args.base, manifest_relative)
        except ValueError as exc:
            failures.append(f"{plugin_name}: {exc}")
            continue

        if current is None:
            failures.append(f"{plugin_name}: manifest is missing at {args.head}")
            continue
        current_version = str(current.get("version", ""))
        try:
            current_key = version_key(current_version)
        except ValueError as exc:
            failures.append(f"{plugin_name}: {exc}")
            continue

        if previous is None:
            print(f"{plugin_name}: new plugin at {current_version}; version comparison skipped")
            checked += 1
            continue
        previous_version = str(previous.get("version", ""))
        try:
            previous_key = version_key(previous_version)
        except ValueError as exc:
            failures.append(f"{plugin_name}: base manifest has {exc}")
            continue

        if current_key <= previous_key:
            failures.append(
                f"{plugin_name}: {len(changed_paths)} shipped file(s) changed but version "
                f"did not increase ({previous_version} -> {current_version})"
            )
        else:
            print(
                f"{plugin_name}: {previous_version} -> {current_version} "
                f"for {len(changed_paths)} shipped file(s)"
            )
        checked += 1

    if failures:
        print("PLUGIN VERSION CHECK FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"PLUGIN VERSION CHECK PASSED: {checked} changed plugin(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate repository and plugin release tags against current manifests."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "release" / "release-policy.json"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def validate_tag(tag: str, policy: dict[str, Any], root: Path) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    root = root.resolve()
    if policy.get("schema_version") != "1.0.0":
        failures.append("release policy schema_version must be 1.0.0")
    channels = policy.get("channels")
    if not isinstance(channels, dict) or channels.get("nightly") != "main" or not isinstance(
        channels.get("stable"), str
    ):
        failures.append("release policy must define stable and main nightly channels")
    plugin_versions: dict[str, str] = {}
    plugins = policy.get("plugins")
    if not isinstance(plugins, dict) or not plugins:
        return ["release policy plugins must be a non-empty object"], {}

    matched_plugin: str | None = None
    tag_version: str | None = None
    for plugin_name, config in plugins.items():
        if not isinstance(config, dict):
            failures.append(f"{plugin_name}: release policy must be an object")
            continue
        manifest_value = config.get("manifest")
        prefix = config.get("tag_prefix")
        if not isinstance(manifest_value, str) or not isinstance(prefix, str):
            failures.append(f"{plugin_name}: manifest and tag_prefix are required")
            continue
        manifest_path = (root / manifest_value).resolve()
        try:
            manifest_path.relative_to(root)
        except ValueError:
            failures.append(f"{plugin_name}: manifest path escapes repository")
            continue
        manifest = load_object(manifest_path)
        manifest_name = manifest.get("name")
        version = manifest.get("version")
        if manifest_name != plugin_name or not isinstance(version, str) or SEMVER.fullmatch(version) is None:
            failures.append(f"{plugin_name}: invalid plugin manifest identity or version")
            continue
        plugin_versions[plugin_name] = version
        if tag.startswith(prefix):
            matched_plugin = plugin_name
            tag_version = tag[len(prefix):]
            if tag_version != version:
                failures.append(f"{tag}: expected {plugin_name} manifest version {version}")

    repository_prefix = policy.get("repository_tag_prefix")
    release_kind = "plugin"
    if isinstance(repository_prefix, str) and tag.startswith(repository_prefix):
        release_kind = "repository"
        tag_version = tag[len(repository_prefix):]
        if SEMVER.fullmatch(tag_version) is None:
            failures.append(f"{tag}: repository release tag must end in SemVer")
    elif matched_plugin is None:
        failures.append(f"unsupported release tag: {tag}")

    metadata = {
        "schema_version": "1.0.0",
        "tag": tag,
        "release_kind": release_kind,
        "plugin": matched_plugin,
        "tag_version": tag_version,
        "plugin_versions": plugin_versions,
    }
    return failures, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        policy = load_object(args.policy.resolve())
        failures, metadata = validate_tag(args.tag, policy, ROOT)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    if failures:
        if args.json:
            print(json.dumps({"valid": False, "failures": failures}, ensure_ascii=False))
        else:
            print("RELEASE TAG INVALID")
            for failure in failures:
                print(f"- {failure}")
        return 1
    if args.json:
        print(json.dumps({"valid": True, **metadata}, ensure_ascii=False, indent=2))
    else:
        print(f"RELEASE TAG VALID: {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

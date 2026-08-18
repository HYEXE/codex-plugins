"""Discover marketplace plugins and build isolated installation plans."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PluginDiscoveryError(RuntimeError):
    """Raised when marketplace plugin metadata is incomplete or unsafe."""


@dataclass(frozen=True)
class PluginSpec:
    name: str
    version: str
    path: Path
    manifest_path: Path


@dataclass(frozen=True)
class MarketplaceSpec:
    name: str
    plugins: tuple[PluginSpec, ...]


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PluginDiscoveryError(f"{path}: expected a JSON object")
    return value


def resolve_contained(root: Path, relative: str, label: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise PluginDiscoveryError(f"{label} escapes repository: {relative}") from exc
    return candidate


def discover_marketplace(root: Path, marketplace_path: Path) -> MarketplaceSpec:
    payload = load_object(marketplace_path)
    marketplace_name = payload.get("name")
    entries = payload.get("plugins")
    if not isinstance(marketplace_name, str) or not marketplace_name:
        raise PluginDiscoveryError("marketplace name must be a non-empty string")
    if not isinstance(entries, list) or not entries:
        raise PluginDiscoveryError("marketplace plugins must be a non-empty array")

    plugins: list[PluginSpec] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            raise PluginDiscoveryError(f"marketplace plugin {index} must be an object")
        name = entry.get("name")
        source = entry.get("source")
        relative = source.get("path") if isinstance(source, dict) else None
        if not isinstance(name, str) or not name:
            raise PluginDiscoveryError(f"marketplace plugin {index} needs a name")
        if name in seen:
            raise PluginDiscoveryError(f"duplicate marketplace plugin: {name}")
        if not isinstance(relative, str) or not relative:
            raise PluginDiscoveryError(f"{name}: source.path must be a non-empty string")
        plugin_path = resolve_contained(root, relative, f"{name} source.path")
        manifest_path = plugin_path / ".codex-plugin" / "plugin.json"
        try:
            manifest = load_object(manifest_path)
        except OSError as exc:
            raise PluginDiscoveryError(f"{name}: missing plugin manifest {manifest_path}") from exc
        version = manifest.get("version")
        if manifest.get("name") != name or not isinstance(version, str) or not version:
            raise PluginDiscoveryError(f"{name}: manifest identity or version is invalid")
        seen.add(name)
        plugins.append(
            PluginSpec(
                name=name,
                version=version,
                path=plugin_path,
                manifest_path=manifest_path,
            )
        )
    return MarketplaceSpec(name=marketplace_name, plugins=tuple(plugins))


def plugin_versions(spec: MarketplaceSpec) -> dict[str, str]:
    return {plugin.name: plugin.version for plugin in spec.plugins}


def installed_skill_ids(spec: MarketplaceSpec) -> list[str]:
    skill_ids = {
        skill_file.parent.name
        for plugin in spec.plugins
        for skill_file in plugin.path.glob("skills/*/SKILL.md")
    }
    if not skill_ids:
        raise PluginDiscoveryError("marketplace contains no discoverable skills")
    return sorted(skill_ids)


def installation_commands(
    codex_bin: str, root: Path, spec: MarketplaceSpec
) -> list[list[str]]:
    return [
        [codex_bin, "plugin", "marketplace", "add", str(root), "--json"],
        *[
            [codex_bin, "plugin", "add", f"{plugin.name}@{spec.name}", "--json"]
            for plugin in spec.plugins
        ],
    ]

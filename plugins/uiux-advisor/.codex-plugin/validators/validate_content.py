#!/usr/bin/env python3
"""Validate UI/UX Advisor knowledge-base and toolkit content."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]
DEFAULT_CONFIG = PLUGIN_ROOT / ".codex-plugin" / "quality-gates.json"
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

from check_freshness import classify_freshness  # noqa: E402


SEMVER_PATTERN = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\."
    r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
GUIDE_ID_PATTERN = re.compile(r"uiux-playbook-(\d{3})")
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
PACKAGE_NAME_PATTERN = re.compile(
    r"(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def resolve_config_path(
    config_path: Path,
    value: Any,
    label: str,
    failures: list[str],
) -> Path:
    if not isinstance(value, str) or not value:
        failures.append(f"{label}: path must be a non-empty string")
        return config_path.parent
    resolved = (config_path.parent / value).resolve()
    plugin_root = config_path.parent.parent.resolve()
    try:
        resolved.relative_to(plugin_root)
    except ValueError:
        failures.append(f"{label}: path escapes plugin directory: {value}")
        return config_path.parent
    return resolved


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def validate_frontend_toolkits(
    config_path: Path,
    quality_config: dict[str, Any],
    failures: list[str],
    warnings: list[str],
) -> None:
    registry_config = quality_config.get("toolkit_registry")
    if not isinstance(registry_config, dict):
        failures.append("uiux-advisor: missing toolkit_registry quality gate")
        return
    registry_path = resolve_config_path(
        config_path,
        registry_config.get("path"),
        "uiux-advisor toolkit_registry",
        failures,
    )
    check(registry_path.is_file(), "uiux-advisor: missing frontend toolkit registry", failures)
    if not registry_path.is_file():
        return

    try:
        payload = load_json(registry_path)
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"uiux-advisor: invalid frontend toolkit registry: {exc}")
        return
    if not isinstance(payload, dict):
        failures.append("uiux-advisor: frontend toolkit registry must be an object")
        return

    schema_version = payload.get("schema_version")
    expected_schema = registry_config.get("schema_version")
    check(
        isinstance(expected_schema, str) and schema_version == expected_schema,
        f"uiux-advisor: toolkit schema_version must be {expected_schema}",
        failures,
    )
    snapshot_date = payload.get("snapshot_date")
    try:
        parsed_snapshot = date.fromisoformat(snapshot_date) if isinstance(snapshot_date, str) else None
        check(
            parsed_snapshot is not None and parsed_snapshot <= date.today(),
            "uiux-advisor: invalid or future toolkit snapshot_date",
            failures,
        )
    except ValueError:
        parsed_snapshot = None
        failures.append("uiux-advisor: invalid toolkit snapshot_date")

    tools = payload.get("tools")
    check(isinstance(tools, list), "uiux-advisor: toolkit tools must be an array", failures)
    if not isinstance(tools, list):
        return
    minimum_count = registry_config.get("minimum_count")
    check(
        isinstance(minimum_count, int) and minimum_count > 0,
        "uiux-advisor: toolkit minimum_count must be a positive integer",
        failures,
    )
    if isinstance(minimum_count, int):
        check(
            len(tools) >= minimum_count,
            f"uiux-advisor: expected at least {minimum_count} toolkits, got {len(tools)}",
            failures,
        )

    allowed_kinds = {
        "api",
        "build-tool",
        "framework",
        "library",
        "registry",
        "specification",
        "test-runner",
        "workbench",
    }
    configured_roles = registry_config.get("required_roles")
    check(
        isinstance(configured_roles, list)
        and bool(configured_roles)
        and all(isinstance(role, str) and role for role in configured_roles),
        "uiux-advisor: toolkit required_roles must be a non-empty string array",
        failures,
    )
    allowed_roles = set(configured_roles) if isinstance(configured_roles, list) else set()
    allowed_ecosystems = {
        "web",
        "vanilla",
        "react",
        "vue",
        "svelte",
        "angular",
        "solid",
        "astro",
        "multi-platform",
    }
    configured_ecosystems = registry_config.get("required_ecosystems")
    check(
        isinstance(configured_ecosystems, list)
        and bool(configured_ecosystems)
        and all(isinstance(ecosystem, str) and ecosystem for ecosystem in configured_ecosystems),
        "uiux-advisor: toolkit required_ecosystems must be a non-empty string array",
        failures,
    )
    required_ecosystems = (
        set(configured_ecosystems) if isinstance(configured_ecosystems, list) else set()
    )
    check(
        required_ecosystems <= allowed_ecosystems,
        f"uiux-advisor: unknown required ecosystems {sorted(required_ecosystems - allowed_ecosystems)}",
        failures,
    )
    allowed_adoption = {"native", "package", "registry", "source-copy", "specification"}
    allowed_status = {"candidate", "verified", "deprecated"}
    allowed_license_review = {"required-at-adoption", "verified", "not-applicable"}
    configured_ids = registry_config.get("required_ids")
    check(
        isinstance(configured_ids, list)
        and bool(configured_ids)
        and all(isinstance(tool_id, str) and tool_id for tool_id in configured_ids),
        "uiux-advisor: toolkit required_ids must be a non-empty string array",
        failures,
    )
    required_ids = set(configured_ids) if isinstance(configured_ids, list) else set()
    freshness = registry_config.get("freshness")
    warning_after = freshness.get("warning_after_days") if isinstance(freshness, dict) else None
    error_after = freshness.get("error_after_days") if isinstance(freshness, dict) else None
    valid_freshness = (
        isinstance(warning_after, int)
        and isinstance(error_after, int)
        and 0 <= warning_after < error_after
    )
    check(valid_freshness, "uiux-advisor: invalid toolkit freshness budget", failures)

    ids: list[str] = []
    names: list[str] = []
    official_urls: list[str] = []
    covered_roles: set[str] = set()
    covered_ecosystems: set[str] = set()
    for index, tool in enumerate(tools, 1):
        if not isinstance(tool, dict):
            failures.append(f"uiux-advisor: toolkit {index} must be an object")
            continue
        label = tool.get("id") or f"toolkit-{index}"
        tool_id = tool.get("id")
        name = tool.get("name")
        check(
            isinstance(tool_id, str) and SLUG_PATTERN.fullmatch(tool_id) is not None,
            f"uiux-advisor: {label} has invalid id",
            failures,
        )
        check(isinstance(name, str) and bool(name.strip()), f"uiux-advisor: {label} missing name", failures)
        if isinstance(tool_id, str):
            ids.append(tool_id)
        if isinstance(name, str):
            names.append(name)

        check(tool.get("kind") in allowed_kinds, f"uiux-advisor: {label} has invalid kind", failures)
        check(tool.get("adoption") in allowed_adoption, f"uiux-advisor: {label} has invalid adoption", failures)
        check(tool.get("status") in allowed_status, f"uiux-advisor: {label} has invalid status", failures)
        check(
            tool.get("license_review") in allowed_license_review,
            f"uiux-advisor: {label} has invalid license_review",
            failures,
        )
        roles = tool.get("roles")
        valid_roles = (
            isinstance(roles, list)
            and bool(roles)
            and all(isinstance(role, str) and bool(role) for role in roles)
        )
        check(valid_roles, f"uiux-advisor: {label} has invalid roles", failures)
        if valid_roles:
            check(len(roles) == len(set(roles)), f"uiux-advisor: {label} has duplicate roles", failures)
            check(set(roles) <= allowed_roles, f"uiux-advisor: {label} has unknown roles", failures)
            covered_roles.update(roles)
        ecosystems = tool.get("ecosystems")
        valid_ecosystems = (
            isinstance(ecosystems, list)
            and bool(ecosystems)
            and all(isinstance(ecosystem, str) and bool(ecosystem) for ecosystem in ecosystems)
        )
        check(valid_ecosystems, f"uiux-advisor: {label} has invalid ecosystems", failures)
        if valid_ecosystems:
            check(
                len(ecosystems) == len(set(ecosystems)),
                f"uiux-advisor: {label} has duplicate ecosystems",
                failures,
            )
            check(
                set(ecosystems) <= allowed_ecosystems,
                f"uiux-advisor: {label} has unknown ecosystems",
                failures,
            )
            covered_ecosystems.update(ecosystems)
        for field in ("capabilities", "surfaces"):
            values = tool.get(field)
            valid_values = (
                isinstance(values, list)
                and bool(values)
                and all(
                    isinstance(value, str) and SLUG_PATTERN.fullmatch(value) is not None
                    for value in values
                )
            )
            check(valid_values, f"uiux-advisor: {label} has invalid {field}", failures)
            if valid_values:
                check(
                    len(values) == len(set(values)),
                    f"uiux-advisor: {label} has duplicate {field}",
                    failures,
                )
        check(tool.get("risk") in {"low", "medium", "high"}, f"uiux-advisor: {label} has invalid risk", failures)
        check(
            isinstance(tool.get("fallback"), str) and bool(tool["fallback"].strip()),
            f"uiux-advisor: {label} missing fallback",
            failures,
        )
        official_url = tool.get("official_url")
        check(
            isinstance(official_url, str) and official_url.startswith("https://"),
            f"uiux-advisor: {label} has invalid official_url",
            failures,
        )
        if isinstance(official_url, str):
            official_urls.append(official_url)
        checked_on = tool.get("checked_on")
        try:
            parsed_checked = date.fromisoformat(checked_on) if isinstance(checked_on, str) else None
            check(
                parsed_checked is not None
                and parsed_checked <= date.today()
                and (parsed_snapshot is None or parsed_checked <= parsed_snapshot),
                f"uiux-advisor: {label} has invalid checked_on",
                failures,
            )
            if parsed_checked is not None and valid_freshness:
                status, age = classify_freshness(
                    parsed_checked,
                    warning_after_days=warning_after,
                    error_after_days=error_after,
                )
                if status == "error":
                    failures.append(
                        f"uiux-advisor: {label} toolkit freshness exceeded: {age} days"
                    )
                elif status == "warning":
                    warnings.append(
                        f"uiux-advisor: {label} toolkit should be refreshed: {age} days"
                    )
        except ValueError:
            failures.append(f"uiux-advisor: {label} has invalid checked_on")
        check(
            isinstance(tool.get("selection_note"), str) and bool(tool["selection_note"].strip()),
            f"uiux-advisor: {label} missing selection_note",
            failures,
        )
        if tool.get("license_review") == "verified":
            check(bool(tool.get("license_spdx")), f"uiux-advisor: {label} missing license_spdx", failures)
            check(
                isinstance(tool.get("license_url"), str) and tool["license_url"].startswith("https://"),
                f"uiux-advisor: {label} missing license_url",
                failures,
            )

    check(len(ids) == len(set(ids)), "uiux-advisor: duplicate toolkit IDs", failures)
    check(len(names) == len(set(names)), "uiux-advisor: duplicate toolkit names", failures)
    check(
        len(official_urls) == len(set(official_urls)),
        "uiux-advisor: duplicate toolkit official URLs",
        failures,
    )
    check(required_ids <= set(ids), f"uiux-advisor: missing required toolkits {sorted(required_ids - set(ids))}", failures)
    check(allowed_roles <= covered_roles, f"uiux-advisor: uncovered toolkit roles {sorted(allowed_roles - covered_roles)}", failures)
    check(
        required_ecosystems <= covered_ecosystems,
        f"uiux-advisor: uncovered toolkit ecosystems {sorted(required_ecosystems - covered_ecosystems)}",
        failures,
    )


def validate_stack_relations(
    config_path: Path,
    quality_config: dict[str, Any],
    failures: list[str],
) -> None:
    relations_config = quality_config.get("stack_relations")
    registry_config = quality_config.get("toolkit_registry")
    if not isinstance(relations_config, dict):
        failures.append("uiux-advisor: missing stack_relations quality gate")
        return
    if not isinstance(registry_config, dict):
        failures.append("uiux-advisor: cannot validate stack relations without toolkit_registry")
        return

    relations_path = resolve_config_path(
        config_path,
        relations_config.get("path"),
        "uiux-advisor stack_relations",
        failures,
    )
    registry_path = resolve_config_path(
        config_path,
        registry_config.get("path"),
        "uiux-advisor toolkit_registry",
        failures,
    )
    check(relations_path.is_file(), "uiux-advisor: missing frontend stack relations", failures)
    if not relations_path.is_file() or not registry_path.is_file():
        return

    try:
        payload = load_json(relations_path)
        registry = load_json(registry_path)
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"uiux-advisor: invalid frontend stack relations: {exc}")
        return
    if not isinstance(payload, dict) or not isinstance(registry, dict):
        failures.append("uiux-advisor: stack relations and toolkit registry must be objects")
        return

    expected_schema = relations_config.get("schema_version")
    check(
        isinstance(expected_schema, str) and payload.get("schema_version") == expected_schema,
        f"uiux-advisor: stack relation schema_version must be {expected_schema}",
        failures,
    )
    snapshot_date = payload.get("snapshot_date")
    try:
        parsed_snapshot = date.fromisoformat(snapshot_date) if isinstance(snapshot_date, str) else None
        check(
            parsed_snapshot is not None and parsed_snapshot <= date.today(),
            "uiux-advisor: invalid or future stack relation snapshot_date",
            failures,
        )
    except ValueError:
        failures.append("uiux-advisor: invalid stack relation snapshot_date")

    tools = registry.get("tools")
    known_tool_ids = {
        tool.get("id") for tool in tools if isinstance(tool, dict) and isinstance(tool.get("id"), str)
    } if isinstance(tools, list) else set()
    known_roles = set(registry_config.get("required_roles", []))
    relations = payload.get("relations")
    check(isinstance(relations, list) and bool(relations), "uiux-advisor: stack relations must be a non-empty array", failures)
    if not isinstance(relations, list):
        return

    required_ids_value = relations_config.get("required_tool_ids")
    check(
        isinstance(required_ids_value, list)
        and bool(required_ids_value)
        and all(isinstance(tool_id, str) and tool_id for tool_id in required_ids_value),
        "uiux-advisor: stack relation required_tool_ids must be a non-empty string array",
        failures,
    )
    required_ids = set(required_ids_value) if isinstance(required_ids_value, list) else set()
    relation_by_id: dict[str, dict[str, Any]] = {}
    package_owners: dict[str, str] = {}
    for index, relation in enumerate(relations, 1):
        if not isinstance(relation, dict):
            failures.append(f"uiux-advisor: stack relation {index} must be an object")
            continue
        tool_id = relation.get("tool_id")
        label = tool_id if isinstance(tool_id, str) and tool_id else f"relation-{index}"
        check(tool_id in known_tool_ids, f"uiux-advisor: {label} references unknown toolkit", failures)
        if isinstance(tool_id, str):
            check(tool_id not in relation_by_id, f"uiux-advisor: duplicate stack relation {tool_id}", failures)
            relation_by_id[tool_id] = relation

        package_names = relation.get("package_names")
        valid_packages = (
            isinstance(package_names, list)
            and bool(package_names)
            and all(
                isinstance(package_name, str)
                and PACKAGE_NAME_PATTERN.fullmatch(package_name) is not None
                for package_name in package_names
            )
        )
        check(valid_packages, f"uiux-advisor: {label} has invalid package_names", failures)
        if valid_packages:
            check(len(package_names) == len(set(package_names)), f"uiux-advisor: {label} has duplicate package_names", failures)
            for package_name in package_names:
                owner = package_owners.setdefault(package_name, str(tool_id))
                check(owner == tool_id, f"uiux-advisor: package {package_name} maps to multiple toolkits", failures)

        provides_roles = relation.get("provides_roles")
        valid_roles = (
            isinstance(provides_roles, list)
            and bool(provides_roles)
            and all(isinstance(role, str) and role in known_roles for role in provides_roles)
        )
        check(valid_roles, f"uiux-advisor: {label} has invalid provides_roles", failures)
        if valid_roles:
            check(len(provides_roles) == len(set(provides_roles)), f"uiux-advisor: {label} has duplicate provides_roles", failures)

        for field in ("conflicts_with", "overlaps_with"):
            related_ids = relation.get(field)
            valid_related = (
                isinstance(related_ids, list)
                and all(isinstance(related_id, str) and related_id for related_id in related_ids)
            )
            check(valid_related, f"uiux-advisor: {label} has invalid {field}", failures)
            if valid_related:
                check(len(related_ids) == len(set(related_ids)), f"uiux-advisor: {label} has duplicate {field}", failures)
                check(tool_id not in related_ids, f"uiux-advisor: {label} {field} references itself", failures)

        conflicts = set(relation.get("conflicts_with", []))
        overlaps = set(relation.get("overlaps_with", []))
        check(not conflicts.intersection(overlaps), f"uiux-advisor: {label} conflict and overlap relations intersect", failures)

    relation_ids = set(relation_by_id)
    check(required_ids <= relation_ids, f"uiux-advisor: missing required stack relations {sorted(required_ids - relation_ids)}", failures)
    for tool_id, relation in relation_by_id.items():
        for field in ("conflicts_with", "overlaps_with"):
            for related_id in relation.get(field, []):
                check(related_id in relation_ids, f"uiux-advisor: {tool_id} {field} references unknown relation {related_id}", failures)
                reverse = relation_by_id.get(related_id, {}).get(field, [])
                check(tool_id in reverse, f"uiux-advisor: {tool_id} and {related_id} have asymmetric {field}", failures)


def validate_uiux_kb(
    config_path: Path,
    quality_config: dict[str, Any],
    failures: list[str],
    warnings: list[str],
) -> None:
    kb_config = quality_config.get("knowledge_base")
    if not isinstance(kb_config, dict):
        failures.append("uiux-advisor: missing knowledge_base quality gate")
        return
    kb_dir = resolve_config_path(
        config_path,
        kb_config.get("path"),
        "uiux-advisor knowledge_base",
        failures,
    )
    guides_path = kb_dir / "guides.jsonl"
    sources_path = kb_dir / "sources.json"
    check(guides_path.is_file(), "uiux-advisor: missing guides.jsonl", failures)
    check(sources_path.is_file(), "uiux-advisor: missing sources.json", failures)
    if not guides_path.is_file() or not sources_path.is_file():
        return

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(guides_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"uiux-advisor: invalid guides.jsonl line {line_number}: {exc}")
            continue
        if not isinstance(record, dict):
            failures.append(f"uiux-advisor: guides.jsonl line {line_number} must be an object")
            continue
        records.append(record)

    try:
        sources = load_json(sources_path)
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"uiux-advisor: invalid sources.json: {exc}")
        sources = []
    check(isinstance(sources, list), "uiux-advisor: sources.json must be an array", failures)
    if isinstance(sources, list):
        source_records = [source for source in sources if isinstance(source, dict)]
        check(len(source_records) == len(sources), "uiux-advisor: every source must be an object", failures)
    else:
        source_records = []

    source_ids: list[str] = []
    source_required = ("id", "title", "publisher", "url", "source_type", "scope", "stability", "usage")
    for index, source in enumerate(source_records, 1):
        label = source.get("id") or f"source-{index}"
        for field in source_required:
            check(isinstance(source.get(field), str) and bool(source[field].strip()), f"uiux-advisor: {label} missing {field}", failures)
        source_id = source.get("id")
        if isinstance(source_id, str):
            source_ids.append(source_id)
        url = source.get("url")
        check(isinstance(url, str) and url.startswith(("https://", "http://")), f"uiux-advisor: {label} has invalid URL", failures)
    check(len(source_ids) == len(set(source_ids)), "uiux-advisor: duplicate source IDs", failures)
    known_source_ids = set(source_ids)

    ids = [record.get("id") for record in records]
    markdown_paths = [record.get("markdown_path") for record in records]
    string_ids = [guide_id for guide_id in ids if isinstance(guide_id, str)]
    string_markdown_paths = [path for path in markdown_paths if isinstance(path, str)]
    expected_count = kb_config.get("expected_guide_count")
    check(
        isinstance(expected_count, int) and expected_count > 0,
        "uiux-advisor: expected_guide_count must be a positive integer",
        failures,
    )
    if isinstance(expected_count, int):
        check(
            len(records) == expected_count,
            f"uiux-advisor: expected {expected_count} records, got {len(records)}",
            failures,
        )
    check(len(string_ids) == len(set(string_ids)), "uiux-advisor: duplicate guide IDs", failures)
    check(len(string_markdown_paths) == len(set(string_markdown_paths)), "uiux-advisor: duplicate guide Markdown paths", failures)
    known_guide_ids = {guide_id for guide_id in ids if isinstance(guide_id, str)}
    used_source_ids: set[str] = set()
    required_fields = (
        "id",
        "num",
        "slug",
        "title",
        "category",
        "rule",
        "sources",
        "tags",
        "related_ids",
        "time_sensitive",
        "markdown_path",
        "version",
        "snapshot_date",
    )
    freshness = kb_config.get("freshness")
    time_warning = (
        freshness.get("time_sensitive_warning_after_days") if isinstance(freshness, dict) else None
    )
    time_error = (
        freshness.get("time_sensitive_error_after_days") if isinstance(freshness, dict) else None
    )
    stable_warning = (
        freshness.get("stable_warning_after_days") if isinstance(freshness, dict) else None
    )
    stable_error = (
        freshness.get("stable_error_after_days") if isinstance(freshness, dict) else None
    )
    valid_freshness = all(
        isinstance(value, int)
        for value in (time_warning, time_error, stable_warning, stable_error)
    ) and 0 <= time_warning < time_error and 0 <= stable_warning < stable_error
    check(valid_freshness, "uiux-advisor: invalid knowledge-base freshness budget", failures)

    for index, record in enumerate(records, 1):
        guide_id = record.get("id")
        label = guide_id if isinstance(guide_id, str) and guide_id else f"guide-{index}"
        for field in required_fields:
            check(field in record, f"uiux-advisor: {label} missing {field}", failures)

        match = GUIDE_ID_PATTERN.fullmatch(guide_id) if isinstance(guide_id, str) else None
        check(match is not None, f"uiux-advisor: {label} has invalid guide ID", failures)
        if match:
            check(record.get("num") == int(match.group(1)), f"uiux-advisor: {label} num does not match ID", failures)
        slug = record.get("slug")
        check(isinstance(slug, str) and SLUG_PATTERN.fullmatch(slug) is not None, f"uiux-advisor: {label} has invalid slug", failures)
        for field in ("title", "category", "rule"):
            check(isinstance(record.get(field), str) and bool(record[field].strip()), f"uiux-advisor: {label} missing {field}", failures)

        version = record.get("version")
        check(isinstance(version, str) and SEMVER_PATTERN.fullmatch(version) is not None, f"uiux-advisor: {label} has invalid version", failures)
        snapshot_date = record.get("snapshot_date")
        try:
            parsed_snapshot = date.fromisoformat(snapshot_date) if isinstance(snapshot_date, str) else None
            check(parsed_snapshot is not None and parsed_snapshot <= date.today(), f"uiux-advisor: {label} has future snapshot_date", failures)
            if parsed_snapshot is not None and valid_freshness:
                if record.get("time_sensitive") is True:
                    warning_after, error_after = time_warning, time_error
                else:
                    warning_after, error_after = stable_warning, stable_error
                status, age = classify_freshness(
                    parsed_snapshot,
                    warning_after_days=warning_after,
                    error_after_days=error_after,
                )
                if status == "error":
                    failures.append(
                        f"uiux-advisor: {label} guide freshness exceeded: {age} days"
                    )
                elif status == "warning":
                    warnings.append(
                        f"uiux-advisor: {label} guide should be refreshed: {age} days"
                    )
        except ValueError:
            failures.append(f"uiux-advisor: {label} has invalid snapshot_date")
        check(isinstance(record.get("time_sensitive"), bool), f"uiux-advisor: {label} time_sensitive must be boolean", failures)

        for field in ("sources", "tags", "related_ids"):
            values = record.get(field)
            check(
                isinstance(values, list) and bool(values) and all(isinstance(value, str) and value for value in values),
                f"uiux-advisor: {label} {field} must be a non-empty string array", failures)
            if isinstance(values, list):
                check(len(values) == len(set(values)), f"uiux-advisor: {label} has duplicate {field}", failures)

        record_sources = record.get("sources")
        if isinstance(record_sources, list):
            unknown_sources = sorted(set(record_sources) - known_source_ids)
            check(not unknown_sources, f"uiux-advisor: {label} references unknown sources {unknown_sources}", failures)
            used_source_ids.update(source_id for source_id in record_sources if isinstance(source_id, str))
        related_ids = record.get("related_ids")
        if isinstance(related_ids, list):
            unknown_related = sorted(set(related_ids) - known_guide_ids)
            check(not unknown_related, f"uiux-advisor: {label} references unknown guides {unknown_related}", failures)
            check(guide_id not in related_ids, f"uiux-advisor: {label} relates to itself", failures)

        markdown_path = record.get("markdown_path")
        if not isinstance(markdown_path, str):
            failures.append(f"uiux-advisor: {label} missing guide Markdown")
            continue
        resolved = (kb_dir / markdown_path).resolve()
        try:
            resolved.relative_to(kb_dir.resolve())
        except ValueError:
            failures.append(f"uiux-advisor: {label} has unsafe Markdown path {markdown_path}")
            continue
        check(resolved.is_file(), f"uiux-advisor: {label} missing guide Markdown {markdown_path}", failures)
        if resolved.is_file():
            frontmatter = parse_frontmatter(resolved)
            expected_frontmatter = {
                "id": guide_id,
                "title": record.get("title"),
                "slug": slug,
                "category": record.get("category"),
                "version": version,
                "snapshot_date": snapshot_date,
                "time_sensitive": str(record.get("time_sensitive")).lower(),
            }
            for field, expected in expected_frontmatter.items():
                check(frontmatter.get(field) == str(expected), f"uiux-advisor: {label} Markdown {field} mismatch", failures)

    unused_sources = sorted(known_source_ids - used_source_ids)
    check(not unused_sources, f"uiux-advisor: unused source registry entries {unused_sources}", failures)
    if isinstance(expected_count, int):
        check(
            len(list((kb_dir / "guides").rglob("*.md"))) == expected_count,
            "uiux-advisor: guide file count mismatch",
            failures,
        )

    broken: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)#]+\.md)(?:#[^)]+)?\)")
    for markdown in kb_dir.rglob("*.md"):
        for target in link_pattern.findall(markdown.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://")):
                continue
            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(kb_dir.resolve())
            except ValueError:
                broken.append(f"{markdown.relative_to(kb_dir)} -> unsafe {target}")
                continue
            if not resolved.is_file():
                broken.append(f"{markdown.relative_to(kb_dir)} -> {target}")
    check(not broken, f"uiux-advisor: broken links: {broken[:5]}", failures)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    failures: list[str] = []
    warnings: list[str] = []
    try:
        quality_config = load_json(args.config.resolve())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot load quality gate configuration: {exc}")
        return 1
    if not isinstance(quality_config, dict):
        print("ERROR: quality gate configuration must be an object")
        return 1

    validate_uiux_kb(args.config.resolve(), quality_config, failures, warnings)
    validate_frontend_toolkits(
        args.config.resolve(),
        quality_config,
        failures,
        warnings,
    )
    validate_stack_relations(
        args.config.resolve(),
        quality_config,
        failures,
    )

    if warnings:
        print("UIUX CONTENT VALIDATION WARNINGS")
        for warning in warnings:
            print(f"- {warning}")
    if failures:
        print("UIUX CONTENT VALIDATION FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("UIUX CONTENT VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

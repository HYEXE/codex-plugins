#!/usr/bin/env python3
"""Run deterministic frontend toolkit registry search regressions."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = PLUGIN_ROOT / ".codex-plugin" / "evals" / "toolkit-search-cases.jsonl"
SEARCH_SCRIPT = (
    PLUGIN_ROOT
    / "skills"
    / "uiux-advisor"
    / "scripts"
    / "search_toolkits.py"
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: line {line_number}: invalid JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"{path}: line {line_number}: record must be an object")
        records.append(record)
    return records


def load_search_module() -> ModuleType:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("uiux_search_toolkits", SEARCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load search module: {SEARCH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    allowed_filters = {
        "tool_id",
        "role",
        "ecosystem",
        "kind",
        "capability",
        "surface",
        "risk",
        "max_risk",
        "adoption",
        "status",
        "strategy",
        "existing_tool_ids",
        "recommend",
        "top",
    }
    for index, case in enumerate(cases, 1):
        case_id = case.get("id")
        label = case_id if isinstance(case_id, str) and case_id else f"line-{index}"
        if not isinstance(case_id, str) or not case_id:
            failures.append(f"{label}: missing id")
        elif case_id in seen:
            failures.append(f"{label}: duplicate id")
        else:
            seen.add(case_id)

        filters = case.get("filters")
        if not isinstance(filters, dict) or not filters:
            failures.append(f"{label}: filters must be a non-empty object")
            filters = {}
        else:
            unknown = sorted(set(filters) - allowed_filters)
            if unknown:
                failures.append(f"{label}: unknown filters {unknown}")
            for name, value in filters.items():
                if name == "recommend" and not isinstance(value, bool):
                    failures.append(f"{label}: recommend must be boolean")
                elif name == "top" and (not isinstance(value, int) or isinstance(value, bool) or value < 1):
                    failures.append(f"{label}: top must be a positive integer")
                elif name == "existing_tool_ids" and (
                    not isinstance(value, list)
                    or any(not isinstance(tool_id, str) or not tool_id for tool_id in value)
                    or len(value) != len(set(value))
                ):
                    failures.append(f"{label}: existing_tool_ids must be a unique string array")
                elif name == "strategy" and value not in {"conservative", "ecosystem-first"}:
                    failures.append(f"{label}: strategy must be conservative or ecosystem-first")
                elif name not in {"recommend", "top", "existing_tool_ids", "strategy"} and (
                    not isinstance(value, str) or not value
                ):
                    failures.append(f"{label}: {name} must be a non-empty string")

        for field in ("must_include", "forbidden_ids"):
            value = case.get(field, [])
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                failures.append(f"{label}: {field} must be a string array")
            elif len(value) != len(set(value)):
                failures.append(f"{label}: {field} contains duplicates")
        expect_empty = case.get("expect_empty", False)
        if not isinstance(expect_empty, bool):
            failures.append(f"{label}: expect_empty must be boolean")
        if not case.get("must_include") and not expect_empty:
            failures.append(f"{label}: must_include must not be empty unless expect_empty is true")
        ordered_prefix = case.get("ordered_prefix", [])
        if not isinstance(ordered_prefix, list) or any(not isinstance(item, str) for item in ordered_prefix):
            failures.append(f"{label}: ordered_prefix must be a string array")
        if set(case.get("must_include", [])) & set(case.get("forbidden_ids", [])):
            failures.append(f"{label}: required and forbidden IDs overlap")
        for field in ("must_warn", "provided_roles"):
            mapping = case.get(field, {})
            if not isinstance(mapping, dict) or any(
                not isinstance(key, str)
                or not key
                or not isinstance(values, list)
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
                for key, values in mapping.items()
            ):
                failures.append(f"{label}: {field} must map strings to unique string arrays")

    if len(cases) < 8:
        failures.append(f"toolkit search suite needs at least 8 cases, got {len(cases)}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--show-results", action="store_true")
    args = parser.parse_args()

    try:
        cases = load_jsonl(args.cases)
        module = load_search_module()
        payload = module.load_registry(module.REGISTRY_PATH)
        relations_payload = module.load_relations(module.RELATIONS_PATH, payload)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    failures = validate_cases(cases)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    failed_cases: list[str] = []
    filter_names = (
        "tool_id",
        "role",
        "ecosystem",
        "kind",
        "capability",
        "surface",
        "risk",
        "max_risk",
        "adoption",
        "status",
        "strategy",
        "existing_tool_ids",
        "recommend",
        "top",
    )
    for case in cases:
        filters = case["filters"]
        namespace = argparse.Namespace(**{
            name: filters.get(
                name,
                False
                if name == "recommend"
                else "conservative"
                if name == "strategy"
                else []
                if name == "existing_tool_ids"
                else None,
            )
            for name in filter_names
        })
        namespace.existing_packages = []
        result_tools = module.search(payload, namespace)
        result_ids = [tool["id"] for tool in result_tools]
        context = module.build_recommendation_context(
            relations_payload,
            namespace,
            result_tools,
        )
        reasons: list[str] = []
        if case.get("expect_empty") and result_ids:
            reasons.append(f"expected no matches, got {result_ids}")
        ordered_prefix = case.get("ordered_prefix", [])
        if ordered_prefix and result_ids[: len(ordered_prefix)] != ordered_prefix:
            reasons.append(f"ordered prefix {result_ids[:len(ordered_prefix)]} != {ordered_prefix}")
        missing = sorted(set(case.get("must_include", [])) - set(result_ids))
        if missing:
            reasons.append(f"missing required IDs {missing}")
        forbidden = sorted(set(case.get("forbidden_ids", [])) & set(result_ids))
        if forbidden:
            reasons.append(f"returned forbidden IDs {forbidden}")
        for tool_id, warning_codes in case.get("must_warn", {}).items():
            actual_codes = {
                warning["code"]
                for warning in context["warnings_by_tool"].get(tool_id, [])
            }
            missing_codes = sorted(set(warning_codes) - actual_codes)
            if missing_codes:
                reasons.append(f"{tool_id} missing warning codes {missing_codes}")
        for role, provider_ids in case.get("provided_roles", {}).items():
            missing_providers = sorted(
                set(provider_ids) - set(context["provided_roles"].get(role, []))
            )
            if missing_providers:
                reasons.append(f"{role} missing installed providers {missing_providers}")
        if args.show_results or reasons:
            print(f"{case['id']}: {result_ids}")
        if reasons:
            failed_cases.append(f"{case['id']}: {'; '.join(reasons)}")

    if failed_cases:
        print("TOOLKIT SEARCH REGRESSION FAILED")
        for failure in failed_cases:
            print(f"- {failure}")
        return 1
    print(f"TOOLKIT SEARCH REGRESSION PASSED: {len(cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

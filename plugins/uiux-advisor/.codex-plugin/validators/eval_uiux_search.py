#!/usr/bin/env python3
"""Run deterministic UI/UX knowledge-base search regression cases."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = PLUGIN_ROOT / ".codex-plugin" / "evals" / "uiux-search-cases.jsonl"
SEARCH_SCRIPT = (
    PLUGIN_ROOT
    / "skills"
    / "uiux-advisor"
    / "scripts"
    / "search_kb.py"
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
    spec = importlib.util.spec_from_file_location("uiux_search_kb", SEARCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load search module: {SEARCH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    for index, case in enumerate(cases, 1):
        case_id = case.get("id")
        label = case_id if isinstance(case_id, str) and case_id else f"line-{index}"
        if not isinstance(case_id, str) or not case_id:
            failures.append(f"{label}: missing id")
        elif case_id in seen:
            failures.append(f"{label}: duplicate id")
        else:
            seen.add(case_id)
        if not isinstance(case.get("query"), str) or not case["query"].strip():
            failures.append(f"{label}: missing query")
        top = case.get("top", 5)
        if not isinstance(top, int) or top < 1 or top > 20:
            failures.append(f"{label}: top must be between 1 and 20")
        for field in ("top_one_of", "must_include", "forbidden_ids"):
            value = case.get(field, [])
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                failures.append(f"{label}: {field} must be a string array")
            elif len(value) != len(set(value)):
                failures.append(f"{label}: {field} contains duplicates")
        if not case.get("top_one_of"):
            failures.append(f"{label}: top_one_of must not be empty")
        if set(case.get("must_include", [])) & set(case.get("forbidden_ids", [])):
            failures.append(f"{label}: required and forbidden IDs overlap")
    if len(cases) < 15:
        failures.append(f"search suite needs at least 15 cases, got {len(cases)}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--show-results", action="store_true")
    args = parser.parse_args()

    try:
        cases = load_jsonl(args.cases)
        module = load_search_module()
        records = module.load_records()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    failures = validate_cases(cases)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    failed_cases: list[str] = []
    for case in cases:
        results = module.search(
            records,
            case["query"],
            case.get("top", 5),
            case.get("category"),
            case.get("source"),
        )
        result_ids = [result["id"] for result in results]
        reasons: list[str] = []
        if not result_ids or result_ids[0] not in case["top_one_of"]:
            reasons.append(f"top result {result_ids[:1]} not in {case['top_one_of']}")
        missing = sorted(set(case.get("must_include", [])) - set(result_ids))
        if missing:
            reasons.append(f"missing required IDs {missing}")
        forbidden = sorted(set(case.get("forbidden_ids", [])) & set(result_ids))
        if forbidden:
            reasons.append(f"returned forbidden IDs {forbidden}")
        if args.show_results or reasons:
            print(f"{case['id']}: {result_ids}")
        if reasons:
            failed_cases.append(f"{case['id']}: {'; '.join(reasons)}")

    if failed_cases:
        print("UIUX SEARCH REGRESSION FAILED")
        for failure in failed_cases:
            print(f"- {failure}")
        return 1
    print(f"UIUX SEARCH REGRESSION PASSED: {len(cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

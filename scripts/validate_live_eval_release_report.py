#!/usr/bin/env python3
"""Validate release comparison provenance before publishing it as a release asset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_live_eval_release_report import RUN_EXPECTATIONS, RUN_LABELS, parse_run_ids


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("release comparison report must be a JSON object")
    return value


def validate_report(payload: dict[str, Any], tag: str, run_ids_value: str) -> list[str]:
    failures: list[str] = []
    expected_ids = parse_run_ids(run_ids_value)
    if payload.get("schema_version") != "1.1.0":
        failures.append("schema_version must be 1.1.0")
    if payload.get("current_tag") != tag:
        failures.append(f"current_tag must be {tag}")

    raw_runs = payload.get("runs")
    if not isinstance(raw_runs, list):
        return failures + ["runs must be an array"]
    runs = {
        item.get("label"): item
        for item in raw_runs
        if isinstance(item, dict) and isinstance(item.get("label"), str)
    }
    if len(runs) != len(raw_runs):
        failures.append("run labels must be unique non-empty strings")
    if set(runs) != set(RUN_LABELS):
        failures.append(f"runs must contain exactly {list(RUN_LABELS)}")

    observed_ids: list[str] = []
    for label in RUN_LABELS:
        item = runs.get(label)
        if not isinstance(item, dict):
            continue
        run_id = item.get("run_id")
        observed_ids.append(str(run_id))
        if run_id != expected_ids[label]:
            failures.append(f"{label}: run_id does not match release input")
        expected_suite, expected_case_set = RUN_EXPECTATIONS[label]
        if item.get("suite") != expected_suite or item.get("case_set") != expected_case_set:
            failures.append(f"{label}: suite/case_set mismatch")
        if item.get("release_gate") is not True:
            failures.append(f"{label}: release_gate must be true")
    if len(observed_ids) != len(set(observed_ids)):
        failures.append("runs contain duplicate run IDs")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--run-ids", required=True)
    args = parser.parse_args()
    try:
        failures = validate_report(load_object(args.report), args.tag, args.run_ids)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    if failures:
        print("LIVE EVAL RELEASE REPORT INVALID")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"LIVE EVAL RELEASE REPORT VALID: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

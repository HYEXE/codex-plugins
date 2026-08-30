#!/usr/bin/env python3
"""Validate release comparison provenance before publishing it as a release asset."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

from build_live_eval_release_report import (
    COMMON_PROVENANCE_FIELDS,
    RUN_EXPECTATIONS,
    RUN_LABELS,
    SUITE_PROVENANCE_FIELDS,
    parse_run_ids,
    validate_coherent_run_bundle,
)


SHA256 = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
RUN_STRING_FIELDS = (
    "model",
    "reasoning_effort",
    "codex_version",
    "runner_commit",
    "dataset_path",
    "dataset_sha256",
    "policy_sha256",
    "completed_at",
)


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("release comparison report must be a JSON object")
    return value


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def is_absolute_reference(value: str) -> bool:
    return Path(value).is_absolute() or WINDOWS_ABSOLUTE_PATH.match(value) is not None


def validate_gate(label: str, gate_name: str, value: Any) -> list[str]:
    prefix = f"{label}.{gate_name}"
    if not isinstance(value, dict):
        return [f"{prefix} must be an object"]
    failures: list[str] = []
    passed = value.get("passed")
    total = value.get("total")
    rate = value.get("rate")
    required_rate = value.get("required_rate")
    gate_passed = value.get("gate_passed")
    if not isinstance(passed, int) or isinstance(passed, bool) or passed < 0:
        failures.append(f"{prefix}.passed must be a non-negative integer")
    if not isinstance(total, int) or isinstance(total, bool) or total <= 0:
        failures.append(f"{prefix}.total must be a positive integer")
    if (
        isinstance(passed, int)
        and not isinstance(passed, bool)
        and isinstance(total, int)
        and not isinstance(total, bool)
        and total > 0
        and passed > total
    ):
        failures.append(f"{prefix}.passed cannot exceed total")
    for field, metric in (("rate", rate), ("required_rate", required_rate)):
        if not is_number(metric) or not 0.0 <= float(metric) <= 1.0:
            failures.append(f"{prefix}.{field} must be a number between 0 and 1")
    if (
        isinstance(passed, int)
        and not isinstance(passed, bool)
        and isinstance(total, int)
        and not isinstance(total, bool)
        and total > 0
        and is_number(rate)
        and abs(float(rate) - (passed / total)) > 0.0001
    ):
        failures.append(f"{prefix}.rate does not match passed/total")
    if not isinstance(gate_passed, bool):
        failures.append(f"{prefix}.gate_passed must be a boolean")
    return failures


def validate_trend(item: Any, index: int) -> list[str]:
    prefix = f"trends[{index}]"
    if not isinstance(item, dict):
        return [f"{prefix} must be an object"]
    failures: list[str] = []
    if item.get("label") not in RUN_LABELS:
        failures.append(f"{prefix}.label must be a known run label")
    for field in ("current_run_id", "previous_run_id"):
        if not isinstance(item.get(field), str) or not item.get(field):
            failures.append(f"{prefix}.{field} must be a non-empty string")
    for gate_name in ("critical", "general"):
        gate = item.get(gate_name)
        if not isinstance(gate, dict):
            failures.append(f"{prefix}.{gate_name} must be an object")
            continue
        for field in ("current", "previous"):
            value = gate.get(field)
            if not is_number(value) or not 0.0 <= float(value) <= 1.0:
                failures.append(
                    f"{prefix}.{gate_name}.{field} must be a number between 0 and 1"
                )
        delta = gate.get("delta_rate")
        if not is_number(delta) or not -1.0 <= float(delta) <= 1.0:
            failures.append(
                f"{prefix}.{gate_name}.delta_rate must be a number between -1 and 1"
            )
    gate_change = item.get("release_gate")
    if not isinstance(gate_change, dict):
        failures.append(f"{prefix}.release_gate must be an object")
    else:
        for field in ("current", "previous", "changed"):
            if not isinstance(gate_change.get(field), bool):
                failures.append(
                    f"{prefix}.release_gate.{field} must be a boolean"
                )
    return failures


def validate_previous(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        return ["previous must be null or an object"]
    failures: list[str] = []
    for field in ("schema_version", "current_tag"):
        if not isinstance(value.get(field), str) or not value.get(field):
            failures.append(f"previous.{field} must be a non-empty string")
    source = value.get("source")
    if not isinstance(source, str) or not source:
        failures.append("previous.source must be a non-empty string")
    elif (
        is_absolute_reference(source)
        or "/" in source
        or "\\" in source
        or Path(source).name != source
    ):
        failures.append("previous.source must be a filename, not a local path")
    if "note" in value and not isinstance(value.get("note"), str):
        failures.append("previous.note must be a string")
    return failures


def validate_report(payload: dict[str, Any], tag: str, run_ids_value: str) -> list[str]:
    failures: list[str] = []
    expected_ids = parse_run_ids(run_ids_value)
    if payload.get("schema_version") != "1.1.0":
        failures.append("schema_version must be 1.1.0")
    if not is_timestamp(payload.get("generated_at")):
        failures.append("generated_at must be a timezone-aware ISO timestamp")
    if payload.get("current_tag") != tag:
        failures.append(f"current_tag must be {tag}")
    if "current_run_root" in payload:
        failures.append("current_run_root must not expose a local path")

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
    coherent_runs: list[dict[str, Any]] = []
    for label in RUN_LABELS:
        item = runs.get(label)
        if not isinstance(item, dict):
            continue
        coherent_runs.append(item)
        run_id = item.get("run_id")
        observed_ids.append(str(run_id))
        if run_id != expected_ids[label]:
            failures.append(f"{label}: run_id does not match release input")
        expected_suite, expected_case_set = RUN_EXPECTATIONS[label]
        if item.get("suite") != expected_suite or item.get("case_set") != expected_case_set:
            failures.append(f"{label}: suite/case_set mismatch")
        for field in RUN_STRING_FIELDS:
            if not isinstance(item.get(field), str) or not item.get(field):
                failures.append(f"{label}.{field} must be a non-empty string")
        if not isinstance(item.get("attempts"), int) or isinstance(item.get("attempts"), bool) or item.get("attempts", 0) <= 0:
            failures.append(f"{label}.attempts must be a positive integer")
        if not isinstance(item.get("runner_dirty"), bool):
            failures.append(f"{label}.runner_dirty must be a boolean")
        for field in ("dataset_sha256", "policy_sha256"):
            value = item.get(field)
            if not isinstance(value, str) or SHA256.fullmatch(value) is None:
                failures.append(f"{label}.{field} must be a lowercase SHA-256")
        plugin_versions = item.get("plugin_versions")
        if (
            not isinstance(plugin_versions, dict)
            or not plugin_versions
            or not all(
                isinstance(key, str)
                and key
                and isinstance(value, str)
                and value
                for key, value in plugin_versions.items()
            )
        ):
            failures.append(
                f"{label}.plugin_versions must be a non-empty string map"
            )
        if not is_timestamp(item.get("completed_at")):
            failures.append(
                f"{label}.completed_at must be a timezone-aware ISO timestamp"
            )
        failures.extend(validate_gate(label, "critical", item.get("critical")))
        failures.extend(validate_gate(label, "general", item.get("general")))
        if item.get("release_gate") is not True:
            failures.append(f"{label}: release_gate must be true")
    if len(observed_ids) != len(set(observed_ids)):
        failures.append("runs contain duplicate run IDs")

    coherent_fields = set(COMMON_PROVENANCE_FIELDS + SUITE_PROVENANCE_FIELDS)
    if coherent_runs and all(
        coherent_fields.issubset(run.keys()) for run in coherent_runs
    ):
        try:
            validate_coherent_run_bundle(coherent_runs)
        except ValueError as exc:
            failures.append(str(exc))

    trends = payload.get("trends")
    if not isinstance(trends, list):
        failures.append("trends must be an array")
    else:
        for index, trend in enumerate(trends):
            failures.extend(validate_trend(trend, index))

    alerts = payload.get("alerts")
    if not isinstance(alerts, list) or not all(
        isinstance(alert, str) and alert for alert in alerts
    ):
        failures.append("alerts must be an array of non-empty strings")

    if "previous" not in payload:
        failures.append("previous metadata is required")
    else:
        failures.extend(validate_previous(payload.get("previous")))
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

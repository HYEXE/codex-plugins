#!/usr/bin/env python3
"""Validate skill-routing cases and score independently observed selections."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "skill-routing.jsonl"
KNOWN_SKILLS = {
    "build-design-system",
    "build-data-visualization",
    "compose-creative-ui",
    "implement-ui-motion",
    "prompt-coach",
    "prompt-compiler",
    "prompt-evaluator",
    "uiux-advisor",
    "uiux-auditor",
}


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


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    counts: Counter[str | None] = Counter()
    for index, case in enumerate(cases, 1):
        case_id = case.get("id")
        prompt = case.get("prompt")
        expected = case.get("expected_skill")
        forbidden = case.get("forbidden_skills", [])
        boundary = case.get("boundary")
        label = case_id if isinstance(case_id, str) and case_id else f"line-{index}"

        if not isinstance(case_id, str) or not case_id:
            failures.append(f"{label}: missing id")
        elif case_id in seen:
            failures.append(f"{label}: duplicate id")
        else:
            seen.add(case_id)

        if not isinstance(prompt, str) or not prompt.strip():
            failures.append(f"{label}: missing prompt")
        elif any(f"${skill}" in prompt for skill in KNOWN_SKILLS):
            failures.append(f"{label}: prompt leaks an explicit skill selector")

        if "expected_skill" not in case:
            failures.append(f"{label}: missing expected_skill")
        if expected is not None and expected not in KNOWN_SKILLS:
            failures.append(f"{label}: unknown expected_skill {expected}")
        else:
            counts[expected] += 1

        if not isinstance(forbidden, list) or any(skill not in KNOWN_SKILLS for skill in forbidden):
            failures.append(f"{label}: forbidden_skills must contain known skill names")
        elif len(forbidden) != len(set(forbidden)):
            failures.append(f"{label}: duplicate forbidden_skills")
        elif expected in forbidden:
            failures.append(f"{label}: expected_skill cannot also be forbidden")

        if not isinstance(boundary, str) or not boundary:
            failures.append(f"{label}: missing boundary")

    for skill in sorted(KNOWN_SKILLS):
        if counts[skill] < 5:
            failures.append(f"{skill}: needs at least 5 positive cases, got {counts[skill]}")
    if counts[None] < 3:
        failures.append(f"no-skill boundary needs at least 3 cases, got {counts[None]}")
    return failures


def validate_observed(cases: list[dict[str, Any]], observed: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    expected_ids = [case["id"] for case in cases]
    observed_by_id: dict[str, dict[str, Any]] = {}
    for record in observed:
        case_id = record.get("id")
        selected = record.get("selected_skill")
        if not isinstance(case_id, str) or not case_id:
            failures.append("observed record missing id")
            continue
        if case_id in observed_by_id:
            failures.append(f"observed duplicate id: {case_id}")
            continue
        if selected is not None and selected not in KNOWN_SKILLS:
            failures.append(f"{case_id}: unknown selected_skill {selected}")
        if "selected_skill" not in record:
            failures.append(f"{case_id}: missing selected_skill")
        observed_by_id[case_id] = record

    missing = sorted(set(expected_ids) - set(observed_by_id))
    extra = sorted(set(observed_by_id) - set(expected_ids))
    if missing:
        failures.append(f"observed results missing cases: {missing}")
    if extra:
        failures.append(f"observed results contain extra cases: {extra}")
    return failures


def score(cases: list[dict[str, Any]], observed: list[dict[str, Any]]) -> int:
    failures = validate_observed(cases, observed)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    observed_by_id = {record["id"]: record for record in observed}
    mismatches: list[str] = []
    boundary_counts: Counter[str] = Counter()
    boundary_passes: Counter[str] = Counter()
    for case in cases:
        case_id = case["id"]
        expected = case.get("expected_skill")
        selected = observed_by_id[case_id].get("selected_skill")
        boundary = case["boundary"]
        boundary_counts[boundary] += 1
        if selected == expected:
            boundary_passes[boundary] += 1
        else:
            mismatches.append(f"{case_id}: expected {expected!r}, observed {selected!r}")

    passed = len(cases) - len(mismatches)
    print(f"ROUTING SCORE: {passed}/{len(cases)} ({passed / max(len(cases), 1) * 100:.1f}%)")
    for boundary in sorted(boundary_counts):
        print(f"- {boundary}: {boundary_passes[boundary]}/{boundary_counts[boundary]}")
    for mismatch in mismatches:
        print(f"MISMATCH: {mismatch}")
    return 1 if mismatches else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="Validate routing case structure and coverage")
    score_parser = subparsers.add_parser("score", help="Score independently observed routing results")
    score_parser.add_argument("observed", type=Path)
    args = parser.parse_args()

    try:
        cases = load_jsonl(args.cases)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    failures = validate_cases(cases)
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    if args.command == "validate":
        counts = Counter(case.get("expected_skill") for case in cases)
        print(
            "ROUTING CASES VALID: "
            f"{len(cases)} cases, {len(KNOWN_SKILLS)} skills, {counts[None]} no-skill boundaries"
        )
        return 0

    try:
        observed = load_jsonl(args.observed)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return score(cases, observed)


if __name__ == "__main__":
    raise SystemExit(main())

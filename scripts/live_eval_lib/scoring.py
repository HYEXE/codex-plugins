"""Deterministic release-gate scoring for live observations."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any

from .events import action_trace_items


ROUTING_PASS_OUTCOMES = {"canonical", "acceptable"}


def classify_routing_selection(case: dict[str, Any], selected: Any) -> str:
    """Classify a routing decision without collapsing allowed and forbidden alternatives."""
    forbidden = case.get("forbidden_skills", [])
    acceptable = case.get("acceptable_skills", [])
    if isinstance(forbidden, list) and selected in forbidden:
        return "forbidden"
    if selected == case.get("expected_skill"):
        return "canonical"
    if isinstance(acceptable, list) and selected in acceptable:
        return "acceptable"
    return "unexpected"


def score_gates(
    case_results: list[dict[str, Any]], suite_policy: dict[str, Any]
) -> dict[str, Any]:
    grouped: dict[str, list[bool]] = defaultdict(list)
    for result in case_results:
        grouped[result["gate"]].append(bool(result["passed"]))
    critical_values = grouped["critical"]
    general_values = grouped["general"]
    critical_rate = sum(critical_values) / len(critical_values) if critical_values else 1.0
    general_rate = sum(general_values) / len(general_values) if general_values else 1.0
    critical_required = float(suite_policy["critical_min_pass_rate"])
    general_required = float(suite_policy["general_min_pass_rate"])
    return {
        "critical": {
            "passed": sum(critical_values),
            "total": len(critical_values),
            "rate": critical_rate,
            "required_rate": critical_required,
            "gate_passed": critical_rate >= critical_required,
        },
        "general": {
            "passed": sum(general_values),
            "total": len(general_values),
            "rate": general_rate,
            "required_rate": general_required,
            "gate_passed": general_rate >= general_required,
        },
        "release_gate": critical_rate >= critical_required and general_rate >= general_required,
    }


def score_routing(
    cases: list[dict[str, Any]], observations: list[dict[str, Any]], suite_policy: dict[str, Any]
) -> dict[str, Any]:
    by_id = {case["id"]: case for case in cases}
    critical_ids = set(suite_policy["critical_case_ids"])
    case_results: list[dict[str, Any]] = []
    for observation in observations:
        case_id = observation.get("case_id")
        case = by_id.get(case_id)
        if case is None:
            case_results.append(
                {
                    "case_id": case_id,
                    "gate": "general",
                    "passed": False,
                    "outcome": "unexpected",
                    "reason": "unknown case",
                }
            )
            continue
        selected = observation.get("selected_skill")
        expected = case.get("expected_skill")
        outcome = classify_routing_selection(case, selected)
        external_items = observation.get("external_event_items", [])
        passed = (
            outcome in ROUTING_PASS_OUTCOMES
            and not observation.get("error")
            and not external_items
        )
        reasons: list[str] = []
        if outcome == "acceptable":
            reasons.append(f"accepted alternative {selected!r}; canonical {expected!r}")
        elif outcome == "forbidden":
            reasons.append(f"forbidden skill selected: {selected!r}")
        elif outcome == "unexpected":
            reasons.append(f"expected {expected!r}, observed {selected!r}")
        if external_items:
            reasons.append("routing classification invoked a tool")
        if observation.get("error"):
            reasons.append(str(observation["error"]))
        case_results.append(
            {
                "case_id": case_id,
                "attempt": observation.get("attempt"),
                "gate": "critical" if case_id in critical_ids else "general",
                "passed": passed,
                "outcome": outcome,
                "reason": "; ".join(reasons),
            }
        )
    gate_score = score_gates(case_results, suite_policy)
    forbidden_failures = sum(result["outcome"] == "forbidden" for result in case_results)
    gate_score["release_gate"] = gate_score["release_gate"] and forbidden_failures == 0
    outcomes = {
        outcome: sum(result["outcome"] == outcome for result in case_results)
        for outcome in ("canonical", "acceptable", "forbidden", "unexpected")
    }
    return {
        "suite": "routing",
        "case_results": case_results,
        "outcomes": outcomes,
        "forbidden_failures": forbidden_failures,
        **gate_score,
    }


def normalized_calls(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    return [
        {key: call.get(key, "") for key in ("action", "target", "content")}
        for call in value
        if isinstance(call, dict)
    ]


def score_tool_trace(
    cases: list[dict[str, Any]], observations: list[dict[str, Any]], suite_policy: dict[str, Any]
) -> dict[str, Any]:
    by_id = {case["id"]: case for case in cases}
    critical_ids = set(suite_policy["critical_case_ids"])
    case_results: list[dict[str, Any]] = []
    for observation in observations:
        case_id = observation.get("case_id")
        case = by_id.get(case_id)
        reasons: list[str] = []
        passed = case is not None and not observation.get("error")
        if case is None:
            reasons.append("unknown case")
        else:
            turns = observation.get("turns") if isinstance(observation.get("turns"), list) else []
            expected_turns = case.get("expected_turns", [])
            if len(turns) != len(expected_turns):
                passed = False
                reasons.append(f"expected {len(expected_turns)} turns, observed {len(turns)}")
            for index, expected_turn in enumerate(expected_turns):
                observed_calls = normalized_calls(turns[index].get("external_calls", [])) if index < len(turns) else []
                expected_calls = normalized_calls(expected_turn.get("external_calls", []))
                if observed_calls != expected_calls:
                    passed = False
                    reasons.append(
                        f"turn {index + 1} external calls differ: expected {expected_calls}, observed {observed_calls}"
                    )
                raw_observed_items = (
                    turns[index].get("external_event_items", []) if index < len(turns) else []
                )
                observed_items = action_trace_items(raw_observed_items)
                observed_types = [
                    item.get("type") for item in observed_items if isinstance(item, dict)
                ]
                expected_types = expected_turn.get("external_event_types", [])
                if observed_types != expected_types:
                    passed = False
                    reasons.append(
                        f"turn {index + 1} event types differ: expected {expected_types}, observed {observed_types}"
                    )
                serialized_items = json.dumps(observed_items, ensure_ascii=False, sort_keys=True)
                for fragment in expected_turn.get("command_contains", []):
                    if fragment not in serialized_items:
                        passed = False
                        reasons.append(
                            f"turn {index + 1} tool trace is missing command fragment {fragment!r}"
                        )
            joined = "\n".join(
                turn.get("assistant", "") for turn in turns if isinstance(turn, dict)
            )
            for pattern in case.get("required_output_patterns", []):
                if re.search(pattern, joined) is None:
                    passed = False
                    reasons.append(f"required output pattern missing: {pattern!r}")
            for pattern in case.get("forbidden_output_patterns", []):
                if re.search(pattern, joined) is not None:
                    passed = False
                    reasons.append(f"forbidden output pattern matched: {pattern!r}")
        if observation.get("error"):
            reasons.append(str(observation["error"]))
        case_results.append(
            {
                "case_id": case_id,
                "attempt": observation.get("attempt"),
                "gate": "critical" if case_id in critical_ids else "general",
                "passed": passed,
                "reason": "; ".join(reasons),
            }
        )
    return {
        "suite": "tool-trace",
        "case_results": case_results,
        **score_gates(case_results, suite_policy),
    }

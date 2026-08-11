#!/usr/bin/env python3
"""Validate and score independently observed Prompt Coach behavior."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


USAGE = """usage: eval_harness.py [validate | self-test | score RESULTS.jsonl | template | --help]

Commands:
  validate              Validate the bundled behavior case dataset.
  self-test             Verify transcript tampering makes the release checks fail.
  score RESULTS.jsonl   Score independent observations against the dataset.
  template              Emit a blank observation template, not model output.
  -h, --help            Show this help message.
"""

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases.jsonl"
DIMENSIONS = (
    "decision",
    "question_rounds",
    "questions_per_round",
    "final_prompt",
    "execution_claim",
    "automatic_handoff",
    "assumption_disclosure",
    "activation_only",
    "unresolved_marked",
)
BOOLEAN_DIMENSIONS = DIMENSIONS[3:]
NUMBERED_LINE = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
FINAL_PROMPT_HEADING = re.compile(r"(?m)^\s*#{0,2}\s*최종 프롬프트\s*$")
ASSUMPTION_HEADING = re.compile(r"(?m)^\s*(?:가정|가정 또는 확인 필요 사항)\s*:")
UNRESOLVED_PLACEHOLDER = re.compile(r"(?m)^.*:\s*\[확인 필요\]\s*$")
EXECUTION_CLAIM = re.compile(
    r"(?:^실행 결과\s*$|"
    r"실제 대상 작업(?:까지)?\s*(?:을| 를)?\s*(?:실행|수행)(?:했|하였)습니다)",
    re.MULTILINE,
)
HANDOFF_CLAIM = re.compile(
    r"(?:prompt-compiler|\bhandoff\b).{0,30}(?:로\s*)?(?:자동으로\s*)?"
    r"(?:전달|넘겼|연결)(?:했|하였|되었)습니다",
    re.IGNORECASE,
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise SystemExit(f"{path}:{line_number}: record must be an object")
            records.append(record)
    return records


def validate_range(value: Any, label: str, problems: list[str]) -> None:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(not isinstance(item, int) or item < 0 for item in value)
        or value[0] > value[1]
    ):
        problems.append(f"{label}: expected a non-negative [min, max] range")


def validate_case_records(cases: list[dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    seen: set[str] = set()
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            problems.append("case missing id")
            continue
        if case_id in seen:
            problems.append(f"duplicate id {case_id}")
        seen.add(case_id)
        if not isinstance(case.get("category"), str) or not case["category"]:
            problems.append(f"{case_id}: missing category")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            problems.append(f"{case_id}: missing prompt")
        expected = case.get("expected")
        if not isinstance(expected, dict):
            problems.append(f"{case_id}: expected must be an object")
            continue
        if set(expected) != set(DIMENSIONS):
            problems.append(f"{case_id}: expected dimensions must be {list(DIMENSIONS)}")
            continue
        if not isinstance(expected["decision"], str) or not expected["decision"]:
            problems.append(f"{case_id}: invalid decision")
        validate_range(expected["question_rounds"], f"{case_id}: question_rounds", problems)
        validate_range(expected["questions_per_round"], f"{case_id}: questions_per_round", problems)
        for dimension in BOOLEAN_DIMENSIONS:
            if not isinstance(expected[dimension], bool):
                problems.append(f"{case_id}: {dimension} must be boolean")
    return problems


def validate_cases() -> int:
    cases = load_jsonl(CASES)
    problems = validate_case_records(cases)
    if problems:
        print("PROMPT COACH DATASET INVALID")
        for problem in problems:
            print(f"- {problem}")
        return 1
    categories = {case["category"] for case in cases}
    print(f"PROMPT COACH DATASET VALID: {len(cases)} cases, {len(categories)} categories")
    return 0


def in_range(value: int, bounds: list[int]) -> bool:
    return bounds[0] <= value <= bounds[1]


def derive_observation(transcript: list[dict[str, str]]) -> dict[str, Any]:
    assistant_texts = [turn["content"] for turn in transcript if turn["role"] == "assistant"]
    joined_output = "\n".join(assistant_texts)
    question_counts = [
        0 if FINAL_PROMPT_HEADING.search(text) else len(NUMBERED_LINE.findall(text))
        for text in assistant_texts
    ]
    question_rounds = sum(count > 0 for count in question_counts)
    final_prompt = FINAL_PROMPT_HEADING.search(joined_output) is not None
    execution_claim = EXECUTION_CLAIM.search(joined_output) is not None
    automatic_handoff = HANDOFF_CLAIM.search(joined_output) is not None
    assumption_disclosure = ASSUMPTION_HEADING.search(joined_output) is not None
    activation_only = (
        len(assistant_texts) == 1
        and assistant_texts[0].startswith("Prompt Coach 모드를")
        and not final_prompt
        and question_rounds == 0
        and not execution_claim
    )
    unresolved_marked = UNRESOLVED_PLACEHOLDER.search(joined_output) is not None
    first_user = next(
        (turn["content"] for turn in transcript if turn["role"] == "user"), ""
    )
    if activation_only:
        decision = "activate-task-gate"
    elif execution_claim:
        decision = "execute-with-compiler"
    elif question_rounds and final_prompt and unresolved_marked:
        decision = "finalize-with-unresolved"
    elif question_rounds and not final_prompt:
        decision = "clarify-before-compile"
    elif final_prompt and "prompt-coach만" in first_user and "실행" in first_user:
        decision = "final-prompt-only"
    elif final_prompt and assumption_disclosure:
        decision = "refine-directly"
    elif final_prompt:
        decision = "pass-through"
    else:
        decision = "unknown"
    return {
        "decision": decision,
        "question_counts": question_counts,
        "final_prompt": final_prompt,
        "execution_claim": execution_claim,
        "automatic_handoff": automatic_handoff,
        "assumption_disclosure": assumption_disclosure,
        "activation_only": activation_only,
        "unresolved_marked": unresolved_marked,
    }


def compare_observation(
    case: dict[str, Any], transcript: list[dict[str, str]], result: dict[str, Any]
) -> tuple[dict[str, bool], dict[str, Any]]:
    expected = case["expected"]
    derived = derive_observation(transcript)
    observed_value = result.get("observed")
    observed = observed_value if isinstance(observed_value, dict) else {}
    counts = derived["question_counts"]
    positive_counts = [count for count in counts if count > 0]
    comparisons = {
        "decision": derived["decision"] == expected["decision"],
        "question_rounds": in_range(len(positive_counts), expected["question_rounds"]),
        "questions_per_round": (
            all(in_range(count, expected["questions_per_round"]) for count in positive_counts)
            if positive_counts
            else expected["questions_per_round"] == [0, 0]
        ),
        **{
            dimension: derived[dimension] is expected[dimension]
            for dimension in BOOLEAN_DIMENSIONS
        },
    }
    if observed != derived:
        comparisons = {name: False for name in DIMENSIONS}
    return comparisons, derived


def validate_result_record(
    case: dict[str, Any], result: dict[str, Any]
) -> tuple[list[str], dict[str, bool]]:
    case_id = case["id"]
    problems: list[str] = []
    if result.get("source") != "independent-forward-test":
        problems.append("source must be independent-forward-test")
    if not isinstance(result.get("run_id"), str) or not result["run_id"].startswith("/root/"):
        problems.append("run_id must identify the independent forward-test task")
    if result.get("observation_scope") != "user-facing-transcript":
        problems.append("observation_scope must be user-facing-transcript")
    transcript = result.get("transcript")
    if not isinstance(transcript, list) or not transcript:
        problems.append("transcript must be a non-empty array")
        transcript = []
    valid_transcript: list[dict[str, str]] = []
    assistant_texts: list[str] = []
    for index, turn in enumerate(transcript, 1):
        if not isinstance(turn, dict) or turn.get("role") not in {"user", "assistant"}:
            problems.append(f"transcript turn {index} has invalid role")
            continue
        content = turn.get("content")
        if not isinstance(content, str) or not content.strip():
            problems.append(f"transcript turn {index} has empty content")
            continue
        if turn["role"] == "assistant":
            assistant_texts.append(content)
        valid_transcript.append({"role": turn["role"], "content": content})
    first_turn = transcript[0] if transcript and isinstance(transcript[0], dict) else None
    if first_turn and first_turn.get("role") == "user":
        if first_turn.get("content") != case["prompt"]:
            problems.append("first user turn does not match the case prompt")
    else:
        problems.append("transcript must start with the user prompt")
    if not assistant_texts:
        problems.append("transcript has no assistant output")

    comparisons, derived = compare_observation(case, valid_transcript, result)
    observed = result.get("observed")
    if not isinstance(observed, dict):
        problems.append("observed must be an object")
    elif observed != derived:
        problems.append("observed values do not match transcript-derived behavior")
    adjudication = result.get("adjudication")
    if not isinstance(adjudication, list):
        problems.append("adjudication must be an array")
        adjudication = []
    names = [
        item.get("name")
        for item in adjudication
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    ]
    if len(names) != len(set(names)):
        problems.append("adjudication contains duplicate dimensions")
    by_name = {
        item.get("name"): item
        for item in adjudication
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    missing = sorted(set(DIMENSIONS) - set(by_name))
    extra = sorted(set(by_name) - set(DIMENSIONS))
    if missing:
        problems.append(f"missing adjudication dimensions: {missing}")
    if extra:
        problems.append(f"unknown adjudication dimensions: {extra}")
    joined_output = "\n".join(assistant_texts)
    for name in DIMENSIONS:
        item = by_name.get(name)
        if not item:
            continue
        if not isinstance(item.get("passed"), bool):
            problems.append(f"{name}: passed must be boolean")
        if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            problems.append(f"{name}: evidence is required")
        excerpt = item.get("excerpt")
        if not isinstance(excerpt, str) or not excerpt.strip():
            problems.append(f"{name}: excerpt is required")
        elif excerpt not in joined_output:
            problems.append(f"{name}: excerpt is not present in assistant output")
    return problems, {
        name: comparisons[name] and bool(by_name.get(name, {}).get("passed"))
        for name in DIMENSIONS
    }


def score_results(path: Path) -> int:
    cases = load_jsonl(CASES)
    case_problems = validate_case_records(cases)
    if case_problems:
        for problem in case_problems:
            print(f"DATASET ERROR: {problem}")
        return 1
    records = load_jsonl(path)
    by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: list[str] = []
    for record in records:
        case_id = record.get("case_id")
        if case_id in by_id:
            duplicate_ids.append(str(case_id))
        if isinstance(case_id, str):
            by_id[case_id] = record
    expected_ids = {case["id"] for case in cases}
    missing = sorted(expected_ids - set(by_id))
    extra = sorted(set(by_id) - expected_ids)
    if missing:
        print("MISSING OBSERVATIONS:", ", ".join(missing))
    if extra:
        print("UNKNOWN OBSERVATIONS:", ", ".join(extra))
    if duplicate_ids:
        print("DUPLICATE OBSERVATIONS:", ", ".join(sorted(duplicate_ids)))

    passed_cases = 0
    for case in cases:
        result = by_id.get(case["id"])
        if result is None:
            continue
        problems, checks = validate_result_record(case, result)
        failed_checks = [name for name, passed in checks.items() if not passed]
        passed = not problems and not failed_checks
        passed_cases += int(passed)
        status = "PASS" if passed else "FAIL"
        print(f"{case['id']}: {status}")
        for problem in problems:
            print(f"  record: {problem}")
        if failed_checks:
            print(f"  behavior: {', '.join(failed_checks)}")

    release = (
        passed_cases == len(cases)
        and len(records) == len(cases)
        and not missing
        and not extra
        and not duplicate_ids
    )
    print(f"PROMPT COACH CASES PASSED: {passed_cases}/{len(cases)}")
    print("PROMPT COACH RELEASE GATE:", "PASS" if release else "FAIL")
    return 0 if release else 2


def self_test() -> int:
    cases = {case["id"]: case for case in load_jsonl(CASES)}
    observations = {
        result["case_id"]: result
        for result in load_jsonl(ROOT / "evals" / "observed-results-2026-08-11.jsonl")
    }
    case = cases["sufficient-request"]
    tampered = json.loads(json.dumps(observations[case["id"]], ensure_ascii=False))
    assistant_turn = next(
        turn for turn in tampered["transcript"] if turn["role"] == "assistant"
    )
    assistant_turn["content"] += "\n\n실제 대상 작업까지 실행했습니다."
    problems, checks = validate_result_record(case, tampered)
    if problems and not checks["execution_claim"]:
        print("PROMPT COACH HARNESS SELF-TEST: PASS")
        return 0
    print("PROMPT COACH HARNESS SELF-TEST: FAIL")
    return 1


def emit_template() -> None:
    for case in load_jsonl(CASES):
        record = {
            "case_id": case["id"],
            "source": "TEMPLATE ONLY - replace with independent-forward-test",
            "run_id": "",
            "observation_scope": "user-facing-transcript",
            "transcript": [{"role": "user", "content": case["prompt"]}],
            "observed": {
                "decision": "",
                "question_counts": [],
                **{dimension: False for dimension in BOOLEAN_DIMENSIONS},
            },
            "adjudication": [
                {"name": name, "passed": False, "evidence": "", "excerpt": ""}
                for name in DIMENSIONS
            ],
        }
        print(json.dumps(record, ensure_ascii=False))


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if command in {"help", "-h", "--help"}:
        print(USAGE)
        return 0
    if command == "validate":
        return validate_cases()
    if command == "self-test":
        return self_test()
    if command == "score":
        if len(sys.argv) < 3:
            raise SystemExit("score requires RESULTS.jsonl")
        return score_results(Path(sys.argv[2]))
    if command == "template":
        emit_template()
        return 0
    raise SystemExit(f"unknown command: {command}\n\n{USAGE}")


if __name__ == "__main__":
    raise SystemExit(main())

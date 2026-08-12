#!/usr/bin/env python3
"""Validate and score independently observed Prompt Compiler orchestration."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


USAGE = """usage: eval_orchestration.py [validate | self-test | score RESULTS.jsonl | template | --help]

Commands:
  validate              Validate the bundled orchestration case dataset.
  self-test             Verify transcript tampering makes the release checks fail.
  score RESULTS.jsonl   Score independent observations against the dataset.
  template              Emit blank observation records, not model output.
  -h, --help            Show this help message.
"""

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "orchestration-cases.jsonl"
DIMENSIONS = (
    "question_rounds",
    "questions_per_round",
    "final_prompt_visible",
    "plan_visible",
    "result_delivered",
    "handoff_claim",
    "resubmit_request",
    "external_action_claim",
)
BOOLEAN_DIMENSIONS = DIMENSIONS[2:]
OBSERVED_FIELDS = ("question_counts",) + BOOLEAN_DIMENSIONS
QUESTION_LINE = re.compile(r"^\s*(?:\d+[.)]\s+)?[^\n?]*\?.*$", re.MULTILINE)
FINAL_PROMPT_HEADING = re.compile(r"(?mi)^\s*#{0,3}\s*최종 프롬프트\s*$")
PLAN_HEADING = re.compile(r"(?mi)^\s*#{0,3}\s*(?:작업\s*)?계획\s*:?.*$")
HANDOFF_CLAIM = re.compile(
    r"(?:두\s*번째|별도|다른)\s*(?:모델|스킬).{0,40}"
    r"(?:자동(?:으로)?\s*)?(?:호출|전달|넘겼|연결)(?:했|하였|되었)습니다|"
    r"자동\s*handoff.{0,20}(?:했|되었)습니다",
    re.IGNORECASE | re.DOTALL,
)
RESUBMIT_REQUEST = re.compile(
    r"(?:프롬프트|내용).{0,30}(?:복사|붙여넣).{0,30}"
    r"(?:다시|새\s*메시지로).{0,20}(?:보내|입력|제출)(?:세요|\s*주세요|줘)",
    re.IGNORECASE | re.DOTALL,
)
EXTERNAL_ACTION_CLAIM = re.compile(
    r"(?:이메일|메시지)(?:을|를)?\s*(?:전송|발송)했습니다|"
    r"(?:게시|배포|push|merge|병합|삭제)(?:를|을)?\s*완료했습니다",
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
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_number}: record must be an object")
            records.append(record)
    return records


def valid_range(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, int) and item >= 0 for item in value)
        and value[0] <= value[1]
    )


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
        follow_up_prompts = case.get("follow_up_prompts", [])
        if not isinstance(follow_up_prompts, list) or any(
            not isinstance(item, str) or not item.strip() for item in follow_up_prompts
        ):
            problems.append(f"{case_id}: follow_up_prompts must be a non-empty string array")
        for field in ("required_output_patterns", "forbidden_output_patterns"):
            patterns = case.get(field, [])
            if not isinstance(patterns, list) or any(not isinstance(item, str) for item in patterns):
                problems.append(f"{case_id}: {field} must be a string array")
                continue
            for pattern in patterns:
                try:
                    re.compile(pattern)
                except re.error as exc:
                    problems.append(f"{case_id}: invalid {field} pattern {pattern!r}: {exc}")
        expected = case.get("expected")
        if not isinstance(expected, dict) or set(expected) != set(DIMENSIONS):
            problems.append(f"{case_id}: expected dimensions must be {list(DIMENSIONS)}")
            continue
        for name in DIMENSIONS[:2]:
            if not valid_range(expected[name]):
                problems.append(f"{case_id}: {name} must be a non-negative [min, max] range")
        for name in BOOLEAN_DIMENSIONS:
            if not isinstance(expected[name], bool):
                problems.append(f"{case_id}: {name} must be boolean")
    return problems


def validate_cases() -> int:
    cases = load_jsonl(CASES)
    problems = validate_case_records(cases)
    if problems:
        print("PROMPT ORCHESTRATION DATASET INVALID")
        for problem in problems:
            print(f"- {problem}")
        return 1
    categories = {case["category"] for case in cases}
    print(f"PROMPT ORCHESTRATION DATASET VALID: {len(cases)} cases, {len(categories)} categories")
    return 0


def derive_observation(case: dict[str, Any], transcript: list[dict[str, str]]) -> dict[str, Any]:
    assistant_texts = [turn["content"] for turn in transcript if turn["role"] == "assistant"]
    joined = "\n".join(assistant_texts)
    counts = [len(QUESTION_LINE.findall(text)) for text in assistant_texts]
    patterns = case["required_output_patterns"]
    return {
        "question_counts": counts,
        "final_prompt_visible": FINAL_PROMPT_HEADING.search(joined) is not None,
        "plan_visible": PLAN_HEADING.search(joined) is not None,
        "result_delivered": bool(patterns) and all(re.search(pattern, joined) for pattern in patterns),
        "handoff_claim": HANDOFF_CLAIM.search(joined) is not None,
        "resubmit_request": RESUBMIT_REQUEST.search(joined) is not None,
        "external_action_claim": EXTERNAL_ACTION_CLAIM.search(joined) is not None,
    }


def in_range(value: int, bounds: list[int]) -> bool:
    return bounds[0] <= value <= bounds[1]


def compare(case: dict[str, Any], derived: dict[str, Any]) -> dict[str, bool]:
    expected = case["expected"]
    positive_counts = [count for count in derived["question_counts"] if count > 0]
    return {
        "question_rounds": in_range(len(positive_counts), expected["question_rounds"]),
        "questions_per_round": (
            all(in_range(count, expected["questions_per_round"]) for count in positive_counts)
            if positive_counts
            else expected["questions_per_round"] == [0, 0]
        ),
        **{
            name: derived[name] is expected[name]
            for name in BOOLEAN_DIMENSIONS
        },
    }


def validate_result_record(
    case: dict[str, Any], result: dict[str, Any]
) -> tuple[list[str], dict[str, bool]]:
    problems: list[str] = []
    if result.get("source") != "independent-forward-test":
        problems.append("source must be independent-forward-test")
    run_id = result.get("run_id")
    if not isinstance(run_id, str) or not run_id.startswith("/root/"):
        problems.append("run_id must identify the independent forward-test task")
    if result.get("observation_scope") != "user-facing-transcript":
        problems.append("observation_scope must be user-facing-transcript")

    transcript_value = result.get("transcript")
    transcript = transcript_value if isinstance(transcript_value, list) else []
    if not transcript:
        problems.append("transcript must be a non-empty array")
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
        valid_transcript.append({"role": turn["role"], "content": content})
        if turn["role"] == "assistant":
            assistant_texts.append(content)
    if not valid_transcript or valid_transcript[0] != {"role": "user", "content": case["prompt"]}:
        problems.append("transcript must start with the exact case prompt")
    expected_follow_ups = case.get("follow_up_prompts")
    if expected_follow_ups is not None:
        user_turns = [turn["content"] for turn in valid_transcript if turn["role"] == "user"]
        if user_turns != [case["prompt"], *expected_follow_ups]:
            problems.append("transcript user turns do not match prompt and follow_up_prompts")
    if not assistant_texts:
        problems.append("transcript has no assistant output")

    derived = derive_observation(case, valid_transcript)
    observed = result.get("observed")
    if not isinstance(observed, dict) or set(observed) != set(OBSERVED_FIELDS):
        problems.append(f"observed fields must be {list(OBSERVED_FIELDS)}")
    elif observed != derived:
        problems.append("observed values do not match transcript-derived behavior")
    checks = compare(case, derived)

    adjudication = result.get("adjudication")
    items = adjudication if isinstance(adjudication, list) else []
    if not isinstance(adjudication, list):
        problems.append("adjudication must be an array")
    by_name = {
        item.get("name"): item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    names = [item.get("name") for item in items if isinstance(item, dict)]
    if len(names) != len(set(names)):
        problems.append("adjudication contains duplicate dimensions")
    missing = sorted(set(DIMENSIONS) - set(by_name))
    extra = sorted(set(by_name) - set(DIMENSIONS))
    if missing:
        problems.append(f"missing adjudication dimensions: {missing}")
    if extra:
        problems.append(f"unknown adjudication dimensions: {extra}")
    joined = "\n".join(assistant_texts)
    for pattern in case.get("forbidden_output_patterns", []):
        if re.search(pattern, joined):
            problems.append(f"forbidden output pattern matched: {pattern!r}")
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
        elif excerpt not in joined:
            problems.append(f"{name}: excerpt is not present in assistant output")
    return problems, {
        name: checks[name] and bool(by_name.get(name, {}).get("passed"))
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
    duplicates: list[str] = []
    for record in records:
        case_id = record.get("case_id")
        if isinstance(case_id, str):
            if case_id in by_id:
                duplicates.append(case_id)
            by_id[case_id] = record
    expected_ids = {case["id"] for case in cases}
    missing = sorted(expected_ids - set(by_id))
    extra = sorted(set(by_id) - expected_ids)
    passed_cases = 0
    for case in cases:
        result = by_id.get(case["id"])
        if result is None:
            continue
        problems, checks = validate_result_record(case, result)
        failed = [name for name, passed in checks.items() if not passed]
        passed = not problems and not failed
        passed_cases += int(passed)
        print(f"{case['id']}: {'PASS' if passed else 'FAIL'}")
        for problem in problems:
            print(f"  record: {problem}")
        if failed:
            print(f"  behavior: {', '.join(failed)}")
    if missing:
        print("MISSING OBSERVATIONS:", ", ".join(missing))
    if extra:
        print("UNKNOWN OBSERVATIONS:", ", ".join(extra))
    if duplicates:
        print("DUPLICATE OBSERVATIONS:", ", ".join(sorted(duplicates)))
    release = (
        passed_cases == len(cases)
        and len(records) == len(cases)
        and not missing
        and not extra
        and not duplicates
    )
    print(f"PROMPT ORCHESTRATION CASES PASSED: {passed_cases}/{len(cases)}")
    print("PROMPT ORCHESTRATION RELEASE GATE:", "PASS" if release else "FAIL")
    return 0 if release else 2


def self_test() -> int:
    case = load_jsonl(CASES)[0]
    output = "The meeting has been moved to 3 p.m."
    transcript = [
        {"role": "user", "content": case["prompt"]},
        {"role": "assistant", "content": output},
    ]
    observed = derive_observation(case, transcript)
    record = {
        "case_id": case["id"],
        "source": "independent-forward-test",
        "run_id": "/root/harness-self-test",
        "observation_scope": "user-facing-transcript",
        "transcript": transcript,
        "observed": observed,
        "adjudication": [
            {"name": name, "passed": True, "evidence": "synthetic self-test", "excerpt": output}
            for name in DIMENSIONS
        ],
    }
    mutations = (
        ("handoff_claim", "두 번째 모델로 자동 전달했습니다."),
        ("resubmit_request", "이 프롬프트를 복사해 새 메시지로 다시 보내 주세요."),
        ("external_action_claim", "이메일을 전송했습니다."),
    )
    for dimension, sentence in mutations:
        tampered = json.loads(json.dumps(record, ensure_ascii=False))
        tampered["transcript"][1]["content"] += f"\n{sentence}"
        problems, checks = validate_result_record(case, tampered)
        if not problems or checks[dimension]:
            print(f"PROMPT ORCHESTRATION HARNESS SELF-TEST: FAIL ({dimension})")
            return 1
    forbidden_case = json.loads(json.dumps(case, ensure_ascii=False))
    forbidden_case["forbidden_output_patterns"] = [r"백그라운드에서.*완료"]
    tampered = json.loads(json.dumps(record, ensure_ascii=False))
    tampered["transcript"][1]["content"] += "\n백그라운드에서 나중에 완료하겠습니다."
    problems, _ = validate_result_record(forbidden_case, tampered)
    if not any("forbidden output pattern matched" in problem for problem in problems):
        print("PROMPT ORCHESTRATION HARNESS SELF-TEST: FAIL (forbidden_output_patterns)")
        return 1
    if mutations:
        print("PROMPT ORCHESTRATION HARNESS SELF-TEST: PASS")
        return 0
    print("PROMPT ORCHESTRATION HARNESS SELF-TEST: FAIL")
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
                "question_counts": [],
                **{name: False for name in BOOLEAN_DIMENSIONS},
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
    try:
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
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    raise SystemExit(f"unknown command: {command}\n\n{USAGE}")


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate an Interactive Slides production proposal and approval gate."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from pathlib import Path


REQUIRED_FIELDS = {
    "proposal_version",
    "proposal_status",
    "presentation_mode",
    "title",
    "estimated_slides",
    "estimated_duration_minutes",
    "total_effort_points",
    "confidence",
    "blocking_questions",
    "rate_card_supplied",
    "approved_by",
    "approved_at",
}
REQUIRED_SECTIONS = (
    "전체 제작 견적",
    "슬라이드별 제작안",
    "디자인 시스템과 슬라이드 패밀리",
    "에셋과 출처 계획",
    "인터랙션과 기술 범위",
    "위험과 의존성",
    "미결 질문",
    "수정 이력",
    "승인 기록",
    "완료 기준",
)
ALLOWED_STATUSES = {"draft", "review", "approved", "production", "qa", "delivered"}
ALLOWED_MODES = {"demo", "experience", "hybrid"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
ALLOWED_SLIDE_STATUSES = {"review", "approved", "revise", "remove", "defer"}
RESOLVED_SLIDE_STATUSES = {"approved", "remove", "defer"}
SLIDE_ROW = re.compile(r"^\|\s*(S\d{2,})\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)


def parse_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if not text.startswith("---\n"):
        return {}, ["proposal must start with YAML-style front matter"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, ["front matter closing delimiter is missing"]

    metadata: dict[str, str] = {}
    for number, line in enumerate(text[4:end].splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"front matter line {number} must contain ':'")
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = parse_scalar(value)
    return metadata, errors


def positive_int(metadata: dict[str, str], key: str, errors: list[str], allow_zero: bool = False) -> int | None:
    raw = metadata.get(key, "")
    try:
        value = int(raw)
    except ValueError:
        errors.append(f"{key} must be an integer")
        return None
    minimum = 0 if allow_zero else 1
    if value < minimum:
        errors.append(f"{key} must be at least {minimum}")
    return value


def validate(path: Path, require_approved: bool) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    metadata, errors = parse_frontmatter(text)

    missing_fields = sorted(REQUIRED_FIELDS - metadata.keys())
    errors.extend(f"missing front matter field: {field}" for field in missing_fields)

    if not metadata.get("title", "").strip():
        errors.append("title must not be empty")

    status = metadata.get("proposal_status", "")
    mode = metadata.get("presentation_mode", "")
    confidence = metadata.get("confidence", "")
    if status and status not in ALLOWED_STATUSES:
        errors.append(f"unsupported proposal_status: {status}")
    if mode and mode not in ALLOWED_MODES:
        errors.append(f"unsupported presentation_mode: {mode}")
    if confidence and confidence not in ALLOWED_CONFIDENCE:
        errors.append(f"unsupported confidence: {confidence}")

    positive_int(metadata, "proposal_version", errors)
    estimated_slides = positive_int(metadata, "estimated_slides", errors)
    positive_int(metadata, "estimated_duration_minutes", errors)
    positive_int(metadata, "total_effort_points", errors)
    blocking_questions = positive_int(metadata, "blocking_questions", errors, allow_zero=True)

    headings = set(re.findall(r"^##\s+(.+?)\s*$", text, re.MULTILINE))
    errors.extend(
        f"missing required section: {section}"
        for section in REQUIRED_SECTIONS
        if section not in headings
    )

    slide_entries = [(slide_id, slide_status.strip()) for slide_id, slide_status in SLIDE_ROW.findall(text)]
    slide_rows = len(slide_entries)
    slide_id_counts = Counter(slide_id for slide_id, _ in slide_entries)
    duplicate_slide_ids = sorted(
        slide_id for slide_id, count in slide_id_counts.items() if count > 1
    )
    errors.extend(f"duplicate slide ID: {slide_id}" for slide_id in duplicate_slide_ids)
    if estimated_slides is not None and slide_rows != estimated_slides:
        errors.append(
            f"estimated_slides is {estimated_slides}, but {slide_rows} slide rows were found"
        )
    unsupported_slide_statuses = [
        f"{slide_id} ({slide_status})"
        for slide_id, slide_status in slide_entries
        if slide_status not in ALLOWED_SLIDE_STATUSES
    ]
    if unsupported_slide_statuses:
        errors.append(
            "unsupported slide row statuses: " + ", ".join(unsupported_slide_statuses)
        )

    if require_approved:
        if status != "approved":
            errors.append("production gate requires proposal_status: approved")
        if blocking_questions != 0:
            errors.append("production gate requires blocking_questions: 0")
        if not metadata.get("approved_by"):
            errors.append("production gate requires approved_by")
        if not metadata.get("approved_at"):
            errors.append("production gate requires approved_at")
        unresolved_slide_rows = [
            f"{slide_id} ({slide_status})"
            for slide_id, slide_status in slide_entries
            if slide_status not in RESOLVED_SLIDE_STATUSES
        ]
        if unresolved_slide_rows:
            errors.append(
                "production gate requires resolved slide rows: "
                + ", ".join(unresolved_slide_rows)
            )
    else:
        unresolved_slide_rows = []

    return {
        "valid": not errors,
        "path": str(path),
        "proposal_version": metadata.get("proposal_version"),
        "proposal_status": status,
        "presentation_mode": mode,
        "slide_rows": slide_rows,
        "duplicate_slide_ids": duplicate_slide_ids,
        "unresolved_slide_rows": unresolved_slide_rows,
        "require_approved": require_approved,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--require-approved", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if not args.proposal.is_file():
        print(f"proposal not found: {args.proposal}", file=sys.stderr)
        return 2

    result = validate(args.proposal, args.require_approved)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["valid"]:
        print(
            "PRODUCTION PROPOSAL VALID: "
            f"v{result['proposal_version']} · {result['proposal_status']} · "
            f"{result['slide_rows']} slides"
        )
    else:
        print("PRODUCTION PROPOSAL INVALID", file=sys.stderr)
        for error in result["errors"]:
            print(f"- {error}", file=sys.stderr)

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Search the UI/UX Playbook KR knowledge base using a small BM25-style ranker."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
KB_DIR = SCRIPT_DIR.parent / "references" / "kb"
JSONL_PATH = KB_DIR / "guides.jsonl"

CONCEPT_GROUPS = [
    {"button", "buttons", "버튼", "행동", "cta", "action"},
    {"form", "forms", "폼", "입력", "input", "field", "필드"},
    {"error", "errors", "오류", "에러", "실패", "복구", "recovery"},
    {"loading", "로드", "로딩", "progress", "진행", "spinner", "스피너"},
    {"focus", "포커스", "keyboard", "키보드", "tab", "탭"},
    {"accessibility", "a11y", "접근성", "inclusive", "포용", "보조기술"},
    {"modal", "dialog", "모달", "대화상자", "overlay", "오버레이", "drawer", "드로어"},
    {"navigation", "nav", "내비게이션", "탐색", "메뉴", "menu"},
    {"responsive", "반응형", "adaptive", "적응형", "reflow", "재배치"},
    {"touch", "터치", "pointer", "포인터", "target", "목표"},
    {"research", "리서치", "연구", "interview", "인터뷰", "survey", "설문"},
    {"usability", "사용성", "test", "testing", "테스트", "검증"},
    {"design-system", "designsystem", "디자인시스템", "system", "시스템", "governance", "거버넌스"},
    {"token", "tokens", "토큰", "variant", "변형", "state", "상태"},
    {"ai", "인공지능", "생성형", "모델", "model", "uncertainty", "불확실성"},
    {"content", "콘텐츠", "copy", "카피", "label", "레이블", "plain", "평이한"},
    {"performance", "성능", "latency", "지연", "vitals", "반응성"},
    {"privacy", "개인정보", "consent", "동의", "permission", "권한"},
    {"table", "테이블", "data", "데이터", "list", "목록"},
    {"motion", "모션", "animation", "애니메이션", "reduced", "감소"},
    {"color", "색상", "contrast", "대비", "non-color", "비색상"},
    {"typography", "타이포그래피", "readability", "가독성", "text", "텍스트"},
    {"metrics", "metric", "지표", "analytics", "분석", "experiment", "실험"},
    {"handoff", "핸드오프", "acceptance", "인수", "qa", "회귀", "regression"},
    {"onboarding", "온보딩", "first-use", "첫사용", "empty", "빈상태"},
    {"destructive", "파괴적", "high-risk", "고위험", "delete", "삭제", "undo", "실행취소"},
]

FIELD_WEIGHTS = {
    "title": 7.0,
    "tags": 5.0,
    "rule": 4.5,
    "category": 3.5,
    "situation": 2.8,
    "principles": 2.3,
    "must": 2.2,
    "should": 1.8,
    "workflow": 1.5,
    "failures": 1.6,
    "validation": 1.5,
    "agent_notes": 1.2,
    "sources": 0.8,
}

TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣][0-9A-Za-z가-힣._+-]*")


def normalize_token(token: str) -> str:
    return token.casefold().strip("._+-")


def tokenize(text: str) -> list[str]:
    tokens = [normalize_token(t) for t in TOKEN_RE.findall(text)]
    return [t for t in tokens if t]


def expand_terms(tokens: list[str]) -> list[str]:
    expanded = set(tokens)
    for group in CONCEPT_GROUPS:
        normalized = {normalize_token(item) for item in group}
        if expanded & normalized:
            expanded.update(normalized)
    return sorted(expanded)


def flatten(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(flatten(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(flatten(v) for v in value)
    return str(value)


def load_records() -> list[dict[str, Any]]:
    if not JSONL_PATH.exists():
        raise FileNotFoundError(f"Knowledge base not found: {JSONL_PATH}")
    records = []
    with JSONL_PATH.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSONL at line {line_number}: {exc}") from exc
    return records


def make_index(records: list[dict[str, Any]]) -> tuple[list[dict[str, Counter]], dict[str, int], float]:
    indexed: list[dict[str, Counter]] = []
    document_frequency: Counter[str] = Counter()
    total_length = 0
    for record in records:
        field_counts: dict[str, Counter] = {}
        document_terms: set[str] = set()
        doc_length = 0
        for field in FIELD_WEIGHTS:
            counts = Counter(tokenize(flatten(record.get(field, ""))))
            field_counts[field] = counts
            document_terms.update(counts)
            doc_length += sum(counts.values())
        field_counts["__length__"] = Counter({"length": doc_length})
        indexed.append(field_counts)
        document_frequency.update(document_terms)
        total_length += doc_length
    average_length = total_length / max(len(records), 1)
    return indexed, dict(document_frequency), average_length


def score_record(
    record: dict[str, Any],
    field_counts: dict[str, Counter],
    query_tokens: list[str],
    document_frequency: dict[str, int],
    document_count: int,
    average_length: float,
) -> float:
    score = 0.0
    doc_length = field_counts["__length__"]["length"]
    k1 = 1.35
    b = 0.72
    for token in query_tokens:
        df = document_frequency.get(token, 0)
        idf = math.log(1.0 + (document_count - df + 0.5) / (df + 0.5))
        for field, weight in FIELD_WEIGHTS.items():
            tf = field_counts[field].get(token, 0)
            if not tf:
                continue
            denominator = tf + k1 * (1 - b + b * doc_length / max(average_length, 1.0))
            score += weight * idf * (tf * (k1 + 1) / denominator)
    query_phrase = " ".join(query_tokens)
    title_tokens = set(tokenize(record.get("title", "")))
    tag_tokens = set(tokenize(flatten(record.get("tags", []))))
    exact_overlap = set(query_tokens) & (title_tokens | tag_tokens)
    score += 2.0 * len(exact_overlap)
    if query_phrase and query_phrase in flatten(record).casefold():
        score += 4.0
    return score


def search(records: list[dict[str, Any]], query: str, top: int, category: str | None, source: str | None) -> list[dict[str, Any]]:
    filtered = records
    if category:
        filtered = [r for r in filtered if category.casefold() in r.get("category", "").casefold()]
    if source:
        filtered = [r for r in filtered if source in r.get("sources", [])]
    if not query.strip():
        return filtered[:top]
    indexed, df, avg_len = make_index(filtered)
    query_tokens = expand_terms(tokenize(query))
    scored = []
    for record, fields in zip(filtered, indexed):
        score = score_record(record, fields, query_tokens, df, len(filtered), avg_len)
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    results = []
    for score, record in scored[:top]:
        item = dict(record)
        item["score"] = round(score, 4)
        results.append(item)
    return results


def resolve_id(raw_id: str) -> str:
    raw = raw_id.strip().casefold()
    if raw.startswith("uiux-playbook-"):
        return raw
    if raw.isdigit():
        return f"uiux-playbook-{int(raw):03d}"
    return raw


def print_result(result: dict[str, Any], full: bool = False) -> None:
    print(f"[{result['id']}] {result['title']}")
    print(f"category: {result['category']}")
    print(f"score: {result.get('score', '-')}")
    print(f"rule: {result['rule']}")
    print(f"sources: {', '.join(result.get('sources', []))}")
    print(f"time_sensitive: {result.get('time_sensitive', False)}")
    print(f"path: {result['markdown_path']}")
    if result.get("related_ids"):
        print(f"related: {', '.join(result['related_ids'])}")
    if full:
        markdown_path = KB_DIR / result["markdown_path"]
        print("\n" + markdown_path.read_text(encoding="utf-8"))
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Search UI/UX Playbook KR")
    parser.add_argument("--query", default="", help="Korean or English search query")
    parser.add_argument("--top", type=int, default=6, help="Number of results")
    parser.add_argument("--category", help="Filter by category text")
    parser.add_argument("--source", help="Filter by source ID")
    parser.add_argument("--id", help="Read a specific numeric or full guide ID")
    parser.add_argument("--full", action="store_true", help="Print full Markdown for selected results")
    parser.add_argument("--json", action="store_true", help="Return JSON")
    parser.add_argument("--list-categories", action="store_true", help="List categories")
    args = parser.parse_args()

    if args.top < 1 or args.top > 50:
        parser.error("--top must be between 1 and 50")

    records = load_records()

    if args.list_categories:
        categories = sorted({r["category"] for r in records})
        if args.json:
            print(json.dumps(categories, ensure_ascii=False, indent=2))
        else:
            print("\n".join(categories))
        return 0

    if args.id:
        target_id = resolve_id(args.id)
        matches = [r for r in records if r["id"].casefold() == target_id]
        if not matches:
            print(f"Guide not found: {args.id}", file=sys.stderr)
            return 2
        results = matches
    else:
        results = search(records, args.query, args.top, args.category, args.source)

    if args.json:
        output = []
        for result in results:
            item = dict(result)
            if args.full:
                item["markdown"] = (KB_DIR / item["markdown_path"]).read_text(encoding="utf-8")
            output.append(item)
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No matching guides found.")
            return 1
        for result in results:
            print_result(result, full=args.full)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

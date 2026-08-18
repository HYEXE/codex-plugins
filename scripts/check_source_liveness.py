#!/usr/bin/env python3
"""Create a non-blocking liveness and drift report for external UI/UX sources."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KB_SOURCES = ROOT / "plugins" / "uiux-advisor" / "skills" / "uiux-advisor" / "references" / "kb" / "sources.json"
TOOLKIT_REGISTRY = ROOT / "plugins" / "uiux-advisor" / "skills" / "uiux-advisor" / "references" / "frontend-toolkit-registry.json"
USER_AGENT = "codex-plugins-source-liveness/1.0"
MAX_BODY_BYTES = 512 * 1024


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title_parts: list[str] = []
        self.canonical_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "link" and "canonical" in (attributes.get("rel") or "").lower().split():
            href = attributes.get("href")
            if href:
                self.canonical_url = href

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return normalize_text(" ".join(self.title_parts))


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        validate_target(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    source_kind: str
    expected_title: str
    requested_url: str


@dataclass
class SourceResult:
    source_id: str
    source_kind: str
    requested_url: str
    status: str
    http_status: int | None = None
    final_url: str | None = None
    canonical_url: str | None = None
    observed_title: str | None = None
    title_similarity: float | None = None
    content_sha256: str | None = None
    content_bytes: int = 0
    error: str | None = None


def load_object(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


def title_similarity(expected: str, observed: str) -> float:
    expected_normalized = normalize_text(expected).casefold()
    observed_normalized = normalize_text(observed).casefold()
    if not expected_normalized or not observed_normalized:
        return 0.0
    if expected_normalized in observed_normalized or observed_normalized in expected_normalized:
        return 1.0
    return round(SequenceMatcher(None, expected_normalized, observed_normalized).ratio(), 3)


def public_addresses(hostname: str) -> list[str]:
    addresses = sorted({item[4][0] for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)})
    if not addresses:
        raise ValueError("hostname did not resolve")
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        if not parsed.is_global:
            raise ValueError(f"hostname resolves to a non-public address: {address}")
    return addresses


def validate_target(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("source URL must be credential-free HTTPS")
    public_addresses(parsed.hostname)


def inspect_html(record: SourceRecord, body: bytes, final_url: str, status: int) -> SourceResult:
    text = body.decode("utf-8", errors="replace")
    parser = MetadataParser()
    parser.feed(text)
    canonical = urllib.parse.urljoin(final_url, parser.canonical_url) if parser.canonical_url else None
    similarity = title_similarity(record.expected_title, parser.title) if parser.title else 0.0
    return SourceResult(
        source_id=record.source_id,
        source_kind=record.source_kind,
        requested_url=record.requested_url,
        status="ok" if 200 <= status < 400 else "http-error",
        http_status=status,
        final_url=final_url,
        canonical_url=canonical,
        observed_title=parser.title or None,
        title_similarity=similarity,
        content_sha256=hashlib.sha256(body).hexdigest(),
        content_bytes=len(body),
    )


def check_source(record: SourceRecord, timeout: int) -> SourceResult:
    try:
        validate_target(record.requested_url)
        request = urllib.request.Request(
            record.requested_url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        )
        opener = urllib.request.build_opener(SafeRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            final_url = response.geturl()
            validate_target(final_url)
            body = response.read(MAX_BODY_BYTES + 1)
            if len(body) > MAX_BODY_BYTES:
                body = body[:MAX_BODY_BYTES]
            return inspect_html(record, body, final_url, response.status)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        return SourceResult(
            source_id=record.source_id,
            source_kind=record.source_kind,
            requested_url=record.requested_url,
            status="unreachable",
            error=str(exc),
        )


def load_sources() -> list[SourceRecord]:
    kb_sources = load_object(KB_SOURCES)
    toolkit_payload = load_object(TOOLKIT_REGISTRY)
    tools = toolkit_payload.get("tools") if isinstance(toolkit_payload, dict) else None
    if not isinstance(kb_sources, list) or not isinstance(tools, list):
        raise ValueError("source registries have invalid structures")
    records = [
        SourceRecord(
            source_id=str(item["id"]),
            source_kind="knowledge-base",
            expected_title=str(item["title"]),
            requested_url=str(item["url"]),
        )
        for item in kb_sources
        if isinstance(item, dict)
    ]
    records.extend(
        SourceRecord(
            source_id=str(item["id"]),
            source_kind="toolkit",
            expected_title=str(item["name"]),
            requested_url=str(item["official_url"]),
        )
        for item in tools
        if isinstance(item, dict)
    )
    if len({(record.source_kind, record.source_id) for record in records}) != len(records):
        raise ValueError("source registries contain duplicate identities")
    return records


def load_baseline(path: Path | None) -> dict[tuple[str, str], dict[str, Any]]:
    if path is None or not path.is_file():
        return {}
    payload = load_object(path)
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        raise ValueError("baseline results must be an array")
    return {
        (str(item.get("source_kind")), str(item.get("source_id"))): item
        for item in results
        if isinstance(item, dict)
    }


def build_report(results: list[SourceResult], baseline: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    serialized: list[dict[str, Any]] = []
    for result in sorted(results, key=lambda item: (item.source_kind, item.source_id)):
        item = asdict(result)
        previous = baseline.get((result.source_kind, result.source_id), {})
        previous_hash = previous.get("content_sha256")
        item["canonical_changed"] = bool(
            result.canonical_url
            and normalize_url(result.canonical_url) != normalize_url(result.requested_url)
        )
        item["title_changed"] = result.title_similarity is not None and result.title_similarity < 0.45
        item["hash_changed"] = bool(
            isinstance(previous_hash, str)
            and result.content_sha256
            and previous_hash != result.content_sha256
        )
        serialized.append(item)
    return {
        "schema_version": "1.0.0",
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "non_blocking": True,
        "summary": {
            "total": len(serialized),
            "reachable": sum(item["status"] == "ok" for item in serialized),
            "unreachable": sum(item["status"] != "ok" for item in serialized),
            "canonical_changed": sum(bool(item["canonical_changed"]) for item in serialized),
            "title_changed": sum(bool(item["title_changed"]) for item in serialized),
            "hash_changed": sum(bool(item["hash_changed"]) for item in serialized),
        },
        "results": serialized,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Source liveness report",
        "",
        f"- checked: {report['checked_at']}",
        f"- reachable: {summary['reachable']}/{summary['total']}",
        f"- unreachable: {summary['unreachable']}",
        f"- canonical drift: {summary['canonical_changed']}",
        f"- title drift: {summary['title_changed']}",
        f"- hash drift versus baseline: {summary['hash_changed']}",
        "",
        "This report is advisory and does not block pull requests or releases.",
    ]
    notable = [
        item
        for item in report["results"]
        if item["status"] != "ok" or item["canonical_changed"] or item["title_changed"] or item["hash_changed"]
    ]
    if notable:
        lines.extend(["", "## Notable results", ""])
        for item in notable:
            flags = [
                name
                for name in ("status", "canonical_changed", "title_changed", "hash_changed")
                if item.get(name) not in {False, "ok"}
            ]
            lines.append(f"- `{item['source_kind']}:{item['source_id']}`: {', '.join(flags)}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.timeout_seconds < 1 or args.workers < 1 or args.workers > 16:
        print("ERROR: invalid timeout or worker count")
        return 2
    try:
        records = load_sources()
        baseline = load_baseline(args.baseline)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2

    results: list[SourceResult] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(check_source, record, args.timeout_seconds): record for record in records}
        for future in as_completed(futures):
            results.append(future.result())
    report = build_report(results, baseline)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(markdown_report(report), encoding="utf-8")
    summary = report["summary"]
    print(
        "SOURCE LIVENESS REPORT: "
        f"reachable={summary['reachable']}/{summary['total']} "
        f"unreachable={summary['unreachable']} title_drift={summary['title_changed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create a release-to-release live-eval comparison report."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT_DEFAULT = ROOT / "artifacts" / "live-eval"
RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{12}$")
RUN_LABELS = (
    "routing_critical",
    "routing_full",
    "tool_trace_critical",
    "tool_trace_full",
)
RUN_EXPECTATIONS = {
    "routing_critical": ("routing", "critical"),
    "routing_full": ("routing", "full"),
    "tool_trace_critical": ("tool-trace", "critical"),
    "tool_trace_full": ("tool-trace", "full"),
}
REQUIRED_MANIFEST_FIELDS = {
    "run_id",
    "suite",
    "case_set",
    "attempts",
    "model",
    "codex_version",
    "runner_commit",
    "runner_dirty",
    "dataset_path",
    "completed_at",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def parse_run_ids(value: str) -> dict[str, str]:
    tokens = [item.strip() for item in value.split(",")]
    tokens = [item for item in tokens if item]
    if not tokens:
        raise ValueError("run IDs are required")

    labeled: dict[str, str] = {}
    if any("=" in item for item in tokens):
        for item in tokens:
            if "=" not in item:
                raise ValueError(f"mixed run-id input format is not allowed: {item}")
            label, run_id = [part.strip() for part in item.split("=", 1)]
            if not label or not run_id:
                raise ValueError(f"invalid run-id mapping: {item}")
            if label not in RUN_LABELS:
                raise ValueError(f"unknown run label: {label}")
            if label in labeled:
                raise ValueError(f"duplicate run label: {label}")
            if RUN_ID_PATTERN.fullmatch(run_id) is None:
                raise ValueError(f"invalid run ID format: {run_id}")
            labeled[label] = run_id
    else:
        if len(tokens) != len(RUN_LABELS):
            raise ValueError(
                f"expected {len(RUN_LABELS)} run IDs in order {RUN_LABELS}, got {len(tokens)}"
            )
        labeled = dict(zip(RUN_LABELS, tokens, strict=True))
        for run_id in tokens:
            if RUN_ID_PATTERN.fullmatch(run_id) is None:
                raise ValueError(f"invalid run ID format: {run_id}")

    missing = [label for label in RUN_LABELS if label not in labeled]
    if missing:
        raise ValueError(f"missing run labels: {missing}")
    if len(set(labeled.values())) != len(labeled):
        raise ValueError("duplicate run IDs are not allowed")
    return labeled


def normalize_rate(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def pick_gate(payload: dict[str, Any], gate: str) -> dict[str, Any]:
    value = payload.get(gate)
    if not isinstance(value, dict):
        raise ValueError(f"missing {gate} gate metrics")
    for key in ("passed", "total", "rate", "required_rate", "gate_passed"):
        if key not in value:
            raise ValueError(f"{gate}.{key} metric is missing")
    return value


def load_run_bundle(run_root: Path, run_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    run_dir = run_root / run_id
    if not run_dir.is_dir():
        raise ValueError(f"run directory not found: {run_dir}")
    manifest_path = run_dir / "run.json"
    summary_path = run_dir / "summary.json"
    if not manifest_path.is_file():
        raise ValueError(f"missing run manifest: {manifest_path}")
    if not summary_path.is_file():
        raise ValueError(f"missing run summary: {summary_path}")
    manifest = load_json(manifest_path)
    summary = load_json(summary_path)
    suite = manifest.get("suite")
    if suite not in {"routing", "tool-trace"}:
        raise ValueError(f"unsupported run suite: {suite}")
    if summary.get("suite") != suite:
        raise ValueError(f"summary suite mismatch: {summary.get('suite')} != {suite}")
    return manifest, summary


def build_run_record(label: str, run_id: str, run_root: Path) -> dict[str, Any]:
    manifest, summary = load_run_bundle(run_root, run_id)
    missing = sorted(REQUIRED_MANIFEST_FIELDS - manifest.keys())
    if missing:
        raise ValueError(f"{run_id}: run manifest missing fields: {missing}")
    if manifest.get("run_id") != run_id:
        raise ValueError(f"{run_id}: run manifest identity mismatch")
    critical = pick_gate(summary, "critical")
    general = pick_gate(summary, "general")
    return {
        "label": label,
        "run_id": run_id,
        "suite": str(manifest["suite"]),
        "case_set": str(manifest["case_set"]),
        "attempts": int(manifest["attempts"]),
        "model": str(manifest["model"]),
        "codex_version": str(manifest["codex_version"]),
        "runner_commit": str(manifest["runner_commit"]),
        "runner_dirty": bool(manifest["runner_dirty"]),
        "dataset_path": str(manifest["dataset_path"]),
        "completed_at": str(manifest["completed_at"]),
        "critical": {
            "passed": int(critical["passed"]),
            "total": int(critical["total"]),
            "rate": normalize_rate(critical["rate"]),
            "required_rate": normalize_rate(critical["required_rate"]),
            "gate_passed": bool(critical["gate_passed"]),
        },
        "general": {
            "passed": int(general["passed"]),
            "total": int(general["total"]),
            "rate": normalize_rate(general["rate"]),
            "required_rate": normalize_rate(general["required_rate"]),
            "gate_passed": bool(general["gate_passed"]),
        },
        "release_gate": bool(summary.get("release_gate")),
    }


def build_runs(run_ids: dict[str, str], run_root: Path) -> list[dict[str, Any]]:
    runs = [build_run_record(label, run_id, run_root) for label, run_id in run_ids.items()]
    for run in runs:
        expected_suite, expected_case_set = RUN_EXPECTATIONS[run["label"]]
        if run["suite"] != expected_suite or run["case_set"] != expected_case_set:
            raise ValueError(
                f"{run['label']}: expected {expected_suite}/{expected_case_set}, "
                f"got {run['suite']}/{run['case_set']}"
            )
    return runs


def find_previous_runs(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = report.get("runs")
    if not isinstance(items, list):
        return {}
    return {
        str(item.get("label")): item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("label"), str)
    }


def format_delta(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return round(current - previous, 4)


def percent_text(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1%}"


def delta_percent_text(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.1%}"


def build_markdown(report: dict[str, Any]) -> str:
    previous = report.get("previous")
    lines = [
        "# Live eval release comparison report",
        "",
        f"- generated: {report['generated_at']}",
        f"- current tag: {report.get('current_tag') or '(not set)'}",
        f"- previous reference: {previous.get('source') if isinstance(previous, dict) else '(not set)'}",
        "",
        "## Current run summary",
        "",
        "| label | suite | case_set | critical | general | release gate | run_id |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["runs"]:
        critical = item["critical"]["rate"]
        general = item["general"]["rate"]
        lines.append(
            "| "
            f"{item['label']} | "
            f"{item['suite']} | "
            f"{item['case_set']} | "
            f"{percent_text(critical)} ({item['critical']['passed']}/{item['critical']['total']}) | "
            f"{percent_text(general)} ({item['general']['passed']}/{item['general']['total']}) | "
            f"{'PASS' if item['release_gate'] else 'FAIL'} | "
            f"{item['run_id']} |"
        )
    if report["trends"]:
        lines.extend(["", "## Trend", "", "| label | critical delta | general delta | gate change |"])
        lines.append("| --- | --- | --- | --- |")
        for item in report["trends"]:
            gate_change = "same"
            if item["release_gate"]["changed"]:
                gate_change = "PASS→FAIL" if item["release_gate"]["current"] is False else "FAIL→PASS"
            lines.append(
                f"| {item['label']} | {delta_percent_text(item['critical']['delta_rate'])} | "
                f"{delta_percent_text(item['general']['delta_rate'])} | {gate_change} |"
            )
    if report["alerts"]:
        lines.extend(
            [
                "",
                "## Alerts",
                "",
                "- " + "\n- ".join(report["alerts"]),
            ]
        )
    else:
        lines.extend(["", "## Alerts", "", "- none"])
    return "\n".join(lines) + "\n"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_ids = parse_run_ids(args.run_ids)
    runs = build_runs(run_ids, args.run_root.resolve())
    report: dict[str, Any] = {
        "schema_version": "1.1.0",
        "generated_at": utc_now(),
        "current_tag": args.current_tag,
        "current_run_root": str((args.run_root.resolve()).as_posix()),
        "runs": runs,
        "trends": [],
        "alerts": [],
        "previous": None,
    }

    if args.previous_report is None:
        return report

    previous_payload = load_json(args.previous_report)
    report["previous"] = {
        "schema_version": previous_payload.get("schema_version"),
        "source": args.previous_report.as_posix(),
        "current_tag": previous_payload.get("current_tag"),
    }
    previous_runs = find_previous_runs(previous_payload)
    threshold = args.regression_threshold
    for run in runs:
        label = run["label"]
        previous = previous_runs.get(label, {})
        previous_run_id = str(previous.get("run_id")) if isinstance(previous.get("run_id"), str) else None
        if not previous_run_id or previous.get("suite") != run["suite"] or previous.get("case_set") != run["case_set"]:
            continue
        critical_delta = format_delta(run["critical"]["rate"], previous.get("critical", {}).get("rate"))
        general_delta = format_delta(run["general"]["rate"], previous.get("general", {}).get("rate"))
        previous_gate = bool(previous.get("release_gate", False))
        trend = {
            "label": label,
            "current_run_id": run["run_id"],
            "previous_run_id": previous_run_id,
            "critical": {
                "current": run["critical"]["rate"],
                "previous": previous.get("critical", {}).get("rate"),
                "delta_rate": critical_delta,
            },
            "general": {
                "current": run["general"]["rate"],
                "previous": previous.get("general", {}).get("rate"),
                "delta_rate": general_delta,
            },
            "release_gate": {
                "current": run["release_gate"],
                "previous": previous_gate,
                "changed": previous_gate != run["release_gate"],
            },
        }
        run["previous"] = {"run_id": previous_run_id}
        report["trends"].append(trend)

        if critical_delta is not None and critical_delta < -threshold:
            report["alerts"].append(
                f"{label} critical rate dropped by {-critical_delta:.1%}: {previous_run_id} -> {run['run_id']}"
            )
        if general_delta is not None and general_delta < -threshold:
            report["alerts"].append(
                f"{label} general rate dropped by {-general_delta:.1%}: {previous_run_id} -> {run['run_id']}"
            )

    if not report["trends"]:
        report["previous"]["note"] = "no comparable labels found"
    return report


def write_report(args: argparse.Namespace, report: dict[str, Any]) -> None:
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(build_markdown(report), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-ids", required=True, help="Four run IDs or label=run-id pairs")
    parser.add_argument(
        "--run-root", type=Path, default=RUN_ROOT_DEFAULT, help="Live-eval run root (default: artifacts/live-eval)"
    )
    parser.add_argument("--current-tag", default=None, help="Current release tag")
    parser.add_argument("--previous-report", type=Path, help="Optional previous report JSON for trend comparison")
    parser.add_argument(
        "--regression-threshold",
        type=float,
        default=0.05,
        help="Alert when rate drops more than threshold (default: 0.05)",
    )
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not (0.0 <= args.regression_threshold <= 1.0):
        print("ERROR: regression threshold must be between 0 and 1")
        return 2
    if args.previous_report is not None and not args.previous_report.exists():
        print(f"ERROR: previous report not found: {args.previous_report}")
        return 2
    try:
        report = build_report(args)
        write_report(args, report)
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"LIVE EVAL RELEASE REPORT: {args.output_json}")
    for item in report["runs"]:
        critical = item["critical"]["rate"]
        general = item["general"]["rate"]
        print(
            f"- {item['label']}: {percent_text(critical)} critical, "
            f"{percent_text(general)} general, release_gate={item['release_gate']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run a non-blocking local live-eval canary matrix for multiple models and builds."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LIVE_EVAL_SCRIPT = ROOT / "scripts" / "live_eval.py"
RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{12}$")
RUN_ROOT_DEFAULT = ROOT / "artifacts" / "live-eval-canary"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_text(path: Path, value: str | dict[str, Any], *, as_json: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if as_json:
        content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    else:
        content = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    path.write_text(content, encoding="utf-8")


def parse_models(values: list[str]) -> list[str]:
    models: list[str] = []
    for raw in values:
        for token in raw.split(","):
            model = token.strip()
            if model:
                if model in models:
                    continue
                models.append(model)
    if not models:
        raise ValueError("--model must include at least one model")
    return models


def parse_codex_builds(values: list[str]) -> list[tuple[str, str]]:
    builds: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in values:
        if "=" in raw:
            label, binary = [part.strip() for part in raw.split("=", 1)]
            if not label or not binary:
                raise ValueError(f"invalid --codex-build spec: {raw}")
        else:
            binary = raw.strip()
            if not binary:
                raise ValueError("--codex-build cannot be empty")
            label = Path(binary).name or binary
        if label in seen:
            raise ValueError(f"duplicate canary build label: {label}")
        seen.add(label)
        builds.append((label, binary))
    if not builds:
        raise ValueError("at least one --codex-build is required")
    return builds


def safe_path_component(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z._-]+", "-", value).strip("._-") or "cell"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
    return f"{normalized[:48]}-{digest}"


def find_last_run_dir(root: Path) -> Path:
    candidates = [path for path in root.iterdir() if path.is_dir() and RUN_ID_PATTERN.fullmatch(path.name)]
    if not candidates:
        raise ValueError(f"run directory not found under {root}")
    candidates.sort(key=lambda path: path.name)
    return candidates[-1]


def run_live_eval_case(
    *,
    codex_bin: str,
    model: str,
    suite: str,
    case_set: str,
    attempts: int,
    reasoning_effort: str,
    auth_mode: str,
    timeout_seconds: int,
    output_dir: Path,
) -> int:
    command = [
        sys.executable,
        str(LIVE_EVAL_SCRIPT),
        "run",
        "--suite",
        suite,
        "--case-set",
        case_set,
        "--attempts",
        str(attempts),
        "--model",
        model,
        "--reasoning-effort",
        reasoning_effort,
        "--auth-mode",
        auth_mode,
        "--codex-bin",
        codex_bin,
        "--timeout-seconds",
        str(timeout_seconds),
        "--output-dir",
        str(output_dir),
    ]
    process = subprocess.run(
        command,
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode == 0 or process.returncode in (1, 3):
        # 1=summary validation issue / 3=release gate fail. Both indicate completed run artifacts.
        return process.returncode
    print(process.stderr.strip() or process.stdout.strip())
    return process.returncode


def normalize_rate(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def build_run_record(suite_root: Path) -> dict[str, Any]:
    run_dir = find_last_run_dir(suite_root)
    manifest = load_json(run_dir / "run.json")
    summary = load_json(run_dir / "summary.json")
    if not isinstance(summary.get("critical"), dict):
        raise ValueError("summary missing critical block")
    if not isinstance(summary.get("general"), dict):
        raise ValueError("summary missing general block")
    critical = summary["critical"]
    general = summary["general"]
    for field in ("passed", "total", "rate", "required_rate", "gate_passed"):
        if field not in critical or field not in general:
            raise ValueError(f"summary missing {field}")
    return {
        "run_id": str(manifest.get("run_id")),
        "run_path": str(run_dir.as_posix()),
        "suite": str(manifest.get("suite")),
        "case_set": str(manifest.get("case_set")),
        "attempts": int(manifest.get("attempts", 0)),
        "model": str(manifest.get("model")),
        "codex_version": str(manifest.get("codex_version")),
        "critical": {
            "passed": int(critical["passed"]),
            "total": int(critical["total"]),
            "rate": normalize_rate(critical["rate"]),
        },
        "general": {
            "passed": int(general["passed"]),
            "total": int(general["total"]),
            "rate": normalize_rate(general["rate"]),
        },
        "release_gate": bool(summary.get("release_gate", False)),
        "required_critical_rate": normalize_rate(critical.get("required_rate")),
        "required_general_rate": normalize_rate(general.get("required_rate")),
        "started_at": str(manifest.get("started_at")),
        "completed_at": str(manifest.get("completed_at")),
    }


def percent_text(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1%}"


def format_delta(current: float | None, previous: float | None) -> str:
    if current is None or previous is None:
        return "n/a"
    return f"{(current - previous):+.1%}"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Live eval canary matrix report",
        "",
        f"- generated: {report['generated_at']}",
        f"- case set: {report['case_set']}",
        f"- attempts: {report['attempts']}",
        f"- reasoning effort: {report['reasoning_effort']}",
        f"- auth mode: {report['auth_mode']}",
        "",
        "## Matrix",
        "",
        "| build | model | suite | critical | general | release gate | run_id |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in report["matrix"]:
        for run in cell["runs"]:
            if run.get("critical") is None or run.get("general") is None:
                lines.append(
                    "| "
                    f"{cell['build_label']} | "
                    f"{cell['model']} | "
                    f"{run['suite']} | "
                    "n/a | n/a | n/a | "
                    "no run |"
                )
                continue
            lines.append(
                "| "
                f"{cell['build_label']} | "
                f"{cell['model']} | "
                f"{run['suite']} | "
                f"{percent_text(run['critical']['rate'])} ({run['critical']['passed']}/{run['critical']['total']}) | "
                f"{percent_text(run['general']['rate'])} ({run['general']['passed']}/{run['general']['total']}) | "
                f"{'PASS' if run['release_gate'] else 'FAIL'} | "
                f"{run['run_id']} |"
            )
    lines.extend(["", "## Baseline trend", ""])
    if report["baseline"] is None:
        lines.append("- no baseline is configured.")
    elif report["trends"]:
        lines.append("| build | model | suite | critical Δ | general Δ | gate change |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for trend in report["trends"]:
            lines.append(
                "| "
                f"{trend['build_label']}/{trend['model']} | "
                f"{trend['suite']} | "
                f"{format_delta(trend['critical']['current'], trend['critical']['baseline'])} | "
                f"{format_delta(trend['general']['current'], trend['general']['baseline'])} | "
                f"{'PASS→FAIL' if trend['gate_changed'] and not trend['current_gate'] else ('FAIL→PASS' if trend['gate_changed'] else 'same')} |"
            )
    else:
        lines.append("- no comparable baseline runs found.")

    lines.extend(["", "## Alerts", ""])
    if report["alerts"]:
        lines.extend(f"- {alert}" for alert in report["alerts"])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_root = args.output_root / args.invocation_id
    run_root.mkdir(parents=True, exist_ok=True)

    matrix: list[dict[str, Any]] = []
    trends: list[dict[str, Any]] = []
    alerts: list[str] = []
    failures: list[str] = []
    cell_runs: dict[str, dict[str, dict[str, Any]]] = {}

    for build_label, codex_bin in args.codex_builds:
        for model in args.models:
            cell_id = f"{build_label}:{model}"
            cell_path = f"{safe_path_component(build_label)}__{safe_path_component(model)}"
            entries: list[dict[str, Any]] = []
            cell_runs[cell_id] = {}

            for suite in args.suites:
                suite_dir = run_root / cell_path / suite

                if args.dry_run:
                    entries.append(
                        {
                            "suite": suite,
                            "run_id": None,
                            "run_path": str(suite_dir),
                            "critical": None,
                            "general": None,
                            "release_gate": None,
                            "error": "dry-run",
                            "attempts": args.attempts,
                            "model": model,
                            "codex_version": None,
                            "codex_bin": codex_bin,
                        }
                    )
                    continue

                suite_dir.mkdir(parents=True, exist_ok=True)

                code = run_live_eval_case(
                    codex_bin=codex_bin,
                    model=model,
                    suite=suite,
                    case_set=args.case_set,
                    attempts=args.attempts,
                    reasoning_effort=args.reasoning_effort,
                    auth_mode=args.auth_mode,
                    timeout_seconds=args.timeout_seconds,
                    output_dir=suite_dir,
                )
                if code not in (0, 1, 3):
                    failures.append(f"{cell_id}:{suite}: command failed with code {code}")

                try:
                    record = build_run_record(suite_dir)
                    record["codex_bin"] = codex_bin
                    record["return_code"] = code
                    record["command"] = (
                        f"{sys.executable} {LIVE_EVAL_SCRIPT} run "
                        f"--suite {suite} --case-set {args.case_set} "
                        f"--model {model} --codex-bin {codex_bin} "
                        f"--attempts {args.attempts} --reasoning-effort {args.reasoning_effort}"
                    )
                except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    entries.append(
                        {
                            "suite": suite,
                            "run_id": None,
                            "run_path": str(suite_dir),
                            "critical": None,
                            "general": None,
                            "release_gate": None,
                            "error": str(exc),
                            "attempts": args.attempts,
                            "model": model,
                            "codex_version": None,
                            "codex_bin": codex_bin,
                            "return_code": code,
                        }
                    )
                    continue
                entries.append(record)
                cell_runs[cell_id][suite] = record

            matrix.append(
                {
                    "build_label": build_label,
                    "model": model,
                    "cell_id": cell_id,
                    "artifact_path": cell_path,
                    "codex_bin": codex_bin,
                    "runs": entries,
                }
            )

    baseline_key = args.baseline
    if baseline_key is None:
        baseline_key = next(iter(cell_runs), None)
    elif baseline_key not in cell_runs:
        failures.append(f"baseline cell '{baseline_key}' not found; fallback to first cell")
        baseline_key = next(iter(cell_runs), None)

    if baseline_key is not None:
        baseline = cell_runs.get(baseline_key, {})
        for cell in matrix:
            for run in cell["runs"]:
                suite = run["suite"]
                baseline_run = baseline.get(suite)
                if not baseline_run or run.get("critical") is None or baseline_run.get("critical") is None:
                    continue
                trend = {
                    "build_label": cell["build_label"],
                    "model": cell["model"],
                    "suite": suite,
                    "critical": {
                        "current": run["critical"]["rate"],
                        "baseline": baseline_run["critical"]["rate"],
                    },
                    "general": {
                        "current": run["general"]["rate"],
                        "baseline": baseline_run["general"]["rate"],
                    },
                    "current_gate": bool(run["release_gate"]),
                    "baseline_gate": bool(baseline_run["release_gate"]),
                }
                trend["gate_changed"] = trend["current_gate"] != trend["baseline_gate"]
                trends.append(trend)

                if run["critical"]["rate"] is not None and baseline_run["critical"]["rate"] is not None:
                    delta = run["critical"]["rate"] - baseline_run["critical"]["rate"]
                    if delta < -args.regression_threshold:
                        alerts.append(
                            f"{cell['build_label']}:{cell['model']} critical dropped by {-delta:.1%} on {suite}"
                        )
                if run["general"]["rate"] is not None and baseline_run["general"]["rate"] is not None:
                    delta = run["general"]["rate"] - baseline_run["general"]["rate"]
                    if delta < -args.regression_threshold:
                        alerts.append(
                            f"{cell['build_label']}:{cell['model']} general dropped by {-delta:.1%} on {suite}"
                        )

    report = {
        "schema_version": "1.1.0",
        "generated_at": utc_now(),
        "case_set": args.case_set,
        "attempts": args.attempts,
        "reasoning_effort": args.reasoning_effort,
        "auth_mode": args.auth_mode,
        "timeout_seconds": args.timeout_seconds,
        "matrix": matrix,
        "baseline": baseline_key,
        "trends": trends,
        "alerts": alerts,
        "failures": failures,
        "invocation_root": str(run_root.as_posix()),
        "suite_selection": args.suites,
    }

    output_json = args.output_json or (run_root / "live-eval-canary-matrix.json")
    output_markdown = args.output_markdown or (run_root / "live-eval-canary-matrix.md")
    write_text(output_json, report, as_json=True)
    write_text(output_markdown, build_markdown(report))
    report["output_json"] = str(output_json.as_posix())
    report["output_markdown"] = str(output_markdown.as_posix())
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument(
        "--suite",
        action="append",
        choices=("routing", "tool-trace"),
    )
    parser.add_argument("--case-set", choices=("critical", "sample", "full"), default="critical")
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--reasoning-effort", default="medium")
    parser.add_argument(
        "--auth-mode",
        choices=("saved", "api-key"),
        default="saved",
    )
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument(
        "--codex-build",
        action="append",
        required=True,
        help="Canary build spec: <label>=<codex-bin>; label is optional if omitted",
    )
    parser.add_argument(
        "--baseline",
        help="Optional baseline cell in form <build-label>:<model>. Defaults to the first cell.",
    )
    parser.add_argument(
        "--regression-threshold",
        type=float,
        default=0.05,
        help="Alert when critical/general drop exceeds threshold (0~1).",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=RUN_ROOT_DEFAULT,
        help="Base directory for canary artifacts",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-markdown", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def normalize_arguments(args: argparse.Namespace) -> argparse.Namespace:
    if not args.suite:
        args.suites = ["routing", "tool-trace"]
    else:
        normalized: list[str] = []
        seen_suite: set[str] = set()
        for suite in args.suite:
            if suite and suite.strip() and suite not in seen_suite:
                normalized.append(suite)
                seen_suite.add(suite)
        args.suites = normalized
    if not args.suites:
        raise ValueError("--suite must include at least one suite")
    for suite in args.suites:
        if suite not in {"routing", "tool-trace"}:
            raise ValueError(f"unsupported suite: {suite}")

    args.models = parse_models(args.model)
    args.codex_builds = parse_codex_builds(args.codex_build)

    if not (0 <= args.regression_threshold <= 1):
        raise ValueError("--regression-threshold must be between 0 and 1")

    args.invocation_id = utc_now().replace(":", "").replace("-", "")
    args.output_root = args.run_root
    return args


def main() -> int:
    try:
        args = normalize_arguments(parse_args())
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.auth_mode == "api-key" and not (os.environ.get("CODEX_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        print("ERROR: CODEX_API_KEY or OPENAI_API_KEY is required for api-key auth mode")
        return 2

    if args.dry_run:
        print("Dry-run mode: executing command plan only.")

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
    if args.output_markdown is not None:
        args.output_markdown.parent.mkdir(parents=True, exist_ok=True)

    try:
        report = build_report(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"CANARY MATRIX REPORT: {report['output_json']}")
    for item in report["matrix"]:
        print(f"- {item['build_label']}:{item['model']}")
        for run in item["runs"]:
            if run.get("critical") is None:
                print(f"  - {run['suite']}: no run artifacts")
                continue
            print(
                f"  - {run['suite']}: {percent_text(run['critical']['rate'])} critical, "
                f"{percent_text(run['general']['rate'])} general, release_gate={run['release_gate']}"
            )
    if report["alerts"]:
        print("Alerts:")
        for alert in report["alerts"]:
            print(f"- {alert}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

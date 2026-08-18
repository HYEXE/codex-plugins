#!/usr/bin/env python3
"""Create a release attestation for operator-confirmed local live eval runs."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{12}$")
RUN_LABELS = (
    "routing_critical",
    "routing_full",
    "tool_trace_critical",
    "tool_trace_full",
)


def parse_run_ids(value: str) -> dict[str, str]:
    run_ids = [item.strip() for item in value.split(",")]
    if len(run_ids) != len(RUN_LABELS):
        raise ValueError(f"local live eval requires {len(RUN_LABELS)} ordered run IDs")
    if len(set(run_ids)) != len(run_ids):
        raise ValueError("local live eval run IDs must be unique")
    for run_id in run_ids:
        if RUN_ID_PATTERN.fullmatch(run_id) is None:
            raise ValueError(f"invalid local live eval run ID: {run_id}")
    return dict(zip(RUN_LABELS, run_ids, strict=True))


def build_attestation(
    *,
    tag: str,
    commit: str,
    model: str,
    codex_version: str,
    run_ids: str,
    actor: str,
    repository: str,
    workflow_run_id: str,
    workflow_run_attempt: str,
) -> dict[str, Any]:
    if not tag:
        raise ValueError("release tag must be non-empty")
    if COMMIT_PATTERN.fullmatch(commit) is None:
        raise ValueError("release commit must be a 40-character lowercase Git SHA")
    for label, value in (
        ("model", model),
        ("Codex version", codex_version),
        ("actor", actor),
        ("repository", repository),
        ("workflow run ID", workflow_run_id),
        ("workflow run attempt", workflow_run_attempt),
    ):
        if not value.strip():
            raise ValueError(f"{label} must be non-empty")
    return {
        "schema_version": "1.0.0",
        "attestation_type": "operator-confirmed-local-live-eval",
        "release_tag": tag,
        "release_commit": commit,
        "auth_mode": "saved-chatgpt",
        "model": model,
        "codex_version": codex_version,
        "runs": parse_run_ids(run_ids),
        "operator_assertion": {
            "confirmed": True,
            "actor": actor,
            "statement": (
                "All listed local live eval runs completed against the release commit "
                "and passed their configured release gates."
            ),
        },
        "github": {
            "repository": repository,
            "workflow_run_id": workflow_run_id,
            "workflow_run_attempt": workflow_run_attempt,
        },
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--codex-version", required=True)
    parser.add_argument("--run-ids", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--workflow-run-attempt", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        attestation = build_attestation(
            tag=args.tag,
            commit=args.commit,
            model=args.model,
            codex_version=args.codex_version,
            run_ids=args.run_ids,
            actor=args.actor,
            repository=args.repository,
            workflow_run_id=args.workflow_run_id,
            workflow_run_attempt=args.workflow_run_attempt,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(attestation, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"LOCAL LIVE EVAL ATTESTATION CREATED: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

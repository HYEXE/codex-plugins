#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, sys

root = Path(__file__).resolve().parents[1]
required = [
    "README.md",
    "LANGUAGE_POLICY.md",
    "SKILL.md",
    "agents/openai.yaml",
    "references/intent-frame.md",
    "references/task-graph.md",
    "references/execution-contracts.md",
    "references/routing.md",
    "references/permissions.md",
    "references/verification.md",
    "references/recovery.md",
    "references/evaluation.md",
    "evals/cases.jsonl",
    "evals/compiler-trace.schema.json",
    "evals/eval_adapter.md",
    "evals/end_to_end.md",
    "machine-interface.sha256.json",
    "scripts/eval_harness.py",
    "scripts/validate_localization.py",
]
errors = [f"Missing: {rel}" for rel in required if not (root / rel).exists()]

skill = (root / "SKILL.md").read_text(encoding="utf-8")
for marker in [
    "name: prompt-compiler",
    "single-node-first bias",
    "Compilation never creates authorization.",
    "Freshness Gate",
    "Artifact Gate",
    "Anti-over-orchestration Gate",
]:
    if marker not in skill:
        errors.append(f"Missing SKILL marker: {marker}")

try:
    json.loads((root / "evals/compiler-trace.schema.json").read_text(encoding="utf-8"))
    json.loads((root / "machine-interface.sha256.json").read_text(encoding="utf-8"))
except Exception as exc:
    errors.append(f"Invalid JSON: {exc}")

checks = [
    [sys.executable, str(root / "scripts/eval_harness.py"), "validate"],
    [sys.executable, str(root / "scripts/validate_localization.py")],
]
outputs = []
for cmd in checks:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    outputs.append(proc.stdout.strip())
    if proc.returncode:
        errors.append(proc.stdout + proc.stderr)

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print("-", error)
    raise SystemExit(1)

print("VALIDATION PASSED")
for output in outputs:
    print(output)

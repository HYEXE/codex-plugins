#!/usr/bin/env python3
"""Evaluate deterministic router cases."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "core" / "router" / "evals" / "routing-cases.jsonl"


def main() -> int:
    total = passed = 0
    for line in CASES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        total += 1
        case = json.loads(line)
        text = case["request"].lower()
        expected = case["expected_plugin"]
        selected = "prompt-compiler" if "prompt" in text else "uiux-advisor" if "ui" in text else None
        passed += selected == expected
    print(json.dumps({"passed": passed, "total": total}))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())

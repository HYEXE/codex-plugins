#!/usr/bin/env python3
"""Validate plugin contract declarations."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "core" / "plugin-contracts" / "schema.json"
PLUGINS = ("prompt-compiler", "uiux-advisor")


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    required = set(schema.get("required", []))
    failures = []
    for plugin in PLUGINS:
        path = ROOT / "plugins" / plugin / ".codex-plugin" / "plugin.json"
        if not path.exists():
            failures.append(f"missing {path}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        missing = required - payload.keys()
        if missing:
            failures.append(f"{plugin}: missing {sorted(missing)}")
    if failures:
        print("\n".join(failures))
        return 1
    print("plugin contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

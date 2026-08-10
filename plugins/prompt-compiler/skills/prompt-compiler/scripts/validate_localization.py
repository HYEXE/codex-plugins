#!/usr/bin/env python3
"""Validate canonical machine-interface hashes for Prompt Compiler v3.2-ko."""
from pathlib import Path
import hashlib, json, sys

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "machine-interface.sha256.json").read_text(encoding="utf-8"))
errors = []

for rel, expected in manifest["files"].items():
    path = root / rel
    if not path.exists():
        errors.append(f"Missing machine-critical file: {rel}")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        errors.append(f"Machine interface changed: {rel}")

if errors:
    print("LOCALIZATION VALIDATION FAILED")
    for error in errors:
        print("-", error)
    raise SystemExit(1)

print(f"LOCALIZATION VALIDATION PASSED: {len(manifest['files'])} machine-critical files match recorded checksums")

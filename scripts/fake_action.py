#!/usr/bin/env python3
"""Record a hermetic external action for controlled live evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_ACTIONS = {"send_email"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True, choices=sorted(ALLOWED_ACTIONS))
    parser.add_argument("--target", required=True)
    parser.add_argument("--content", required=True)
    args = parser.parse_args()

    log_value = os.environ.get("CODEX_FAKE_ACTION_LOG")
    if not log_value:
        parser.error("CODEX_FAKE_ACTION_LOG is required")
    log_path = Path(log_value).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "action": args.action,
        "target": args.target,
        "content": args.content,
        "content_sha256": hashlib.sha256(args.content.encode("utf-8")).hexdigest(),
        "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"status": "recorded", **record}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

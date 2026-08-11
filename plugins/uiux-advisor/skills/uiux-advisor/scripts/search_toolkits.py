#!/usr/bin/env python3
"""Search the UI/UX Advisor frontend toolkit registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "references" / "frontend-toolkit-registry.json"
WEB_FRAMEWORKS = {"vanilla", "react", "vue", "svelte", "angular", "solid"}


def load_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("tools"), list):
        raise ValueError(f"{path}: expected an object with a tools array")
    return payload


def matches(tool: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.tool_id and tool.get("id") != args.tool_id:
        return False
    if args.role and args.role not in tool.get("roles", []):
        return False
    if args.ecosystem:
        ecosystems = tool.get("ecosystems", [])
        exact_match = args.ecosystem in ecosystems
        web_fallback = args.ecosystem in WEB_FRAMEWORKS and "web" in ecosystems
        if not exact_match and not web_fallback:
            return False
    if args.kind and tool.get("kind") != args.kind:
        return False
    return True


def render_text(tool: dict[str, Any]) -> str:
    return "\n".join(
        (
            f"{tool['id']} | {tool['name']}",
            f"  kind: {tool['kind']}",
            f"  roles: {', '.join(tool['roles'])}",
            f"  ecosystems: {', '.join(tool['ecosystems'])}",
            f"  adoption: {tool['adoption']}",
            f"  status: {tool['status']}",
            f"  license_review: {tool['license_review']}",
            f"  official_url: {tool['official_url']}",
            f"  selection_note: {tool['selection_note']}",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--id", dest="tool_id")
    parser.add_argument("--role")
    parser.add_argument("--ecosystem")
    parser.add_argument("--kind")
    parser.add_argument("--json", action="store_true", help="Emit matching records as JSON")
    args = parser.parse_args()

    try:
        payload = load_registry(args.registry)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    tools = [tool for tool in payload["tools"] if isinstance(tool, dict) and matches(tool, args)]
    if args.json:
        print(json.dumps(tools, ensure_ascii=False, indent=2))
    elif tools:
        print("\n\n".join(render_text(tool) for tool in tools))
    else:
        print("No matching toolkit entries.")
    return 0 if tools else 1


if __name__ == "__main__":
    raise SystemExit(main())

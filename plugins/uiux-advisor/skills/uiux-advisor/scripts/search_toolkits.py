#!/usr/bin/env python3
"""Search the UI/UX Advisor frontend toolkit registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "references" / "frontend-toolkit-registry.json"
WEB_FRAMEWORKS = {"vanilla", "react", "vue", "svelte", "angular", "solid", "astro"}
RISK_RANK = {"low": 0, "medium": 1, "high": 2}
ADOPTION_RANK = {"native": 0, "specification": 1, "package": 2, "registry": 3, "source-copy": 4}


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
    if args.capability and args.capability not in tool.get("capabilities", []):
        return False
    if args.surface and args.surface not in tool.get("surfaces", []):
        return False
    if args.risk and tool.get("risk") != args.risk:
        return False
    max_risk = getattr(args, "max_risk", None)
    if max_risk and RISK_RANK.get(str(tool.get("risk")), 99) > RISK_RANK[max_risk]:
        return False
    adoption = getattr(args, "adoption", None)
    if adoption and tool.get("adoption") != adoption:
        return False
    if args.status and tool.get("status") != args.status:
        return False
    return True


def search(payload: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    tools = [tool for tool in payload["tools"] if isinstance(tool, dict) and matches(tool, args)]
    if getattr(args, "recommend", False):
        tools = sorted(tools, key=lambda tool: recommendation_key(tool, args))
    top = getattr(args, "top", None)
    return tools[:top] if top is not None else tools


def recommendation_key(tool: dict[str, Any], args: argparse.Namespace) -> tuple[int, int, int, str]:
    ecosystems = tool.get("ecosystems", [])
    ecosystem_penalty = 0
    if args.ecosystem and args.ecosystem not in ecosystems and "web" in ecosystems:
        ecosystem_penalty = 1
    return (
        RISK_RANK.get(str(tool.get("risk")), 99),
        ecosystem_penalty,
        ADOPTION_RANK.get(str(tool.get("adoption")), 99),
        str(tool.get("id", "")),
    )


def recommendation_reasons(tool: dict[str, Any], args: argparse.Namespace) -> list[str]:
    reasons = [f"risk={tool['risk']}", f"adoption={tool['adoption']}"]
    if args.ecosystem:
        match = "exact" if args.ecosystem in tool.get("ecosystems", []) else "web-fallback"
        reasons.append(f"ecosystem={match}")
    for name, field in (("role", "roles"), ("capability", "capabilities"), ("surface", "surfaces")):
        value = getattr(args, name)
        if value and value in tool.get(field, []):
            reasons.append(f"{name}={value}")
    return reasons


def list_values(payload: dict[str, Any], field: str) -> list[str]:
    if field == "risk":
        return sorted({str(tool.get("risk")) for tool in payload["tools"] if tool.get("risk")})
    if field == "status":
        return sorted({str(tool.get("status")) for tool in payload["tools"] if tool.get("status")})
    if field in {"kind", "adoption"}:
        return sorted({str(tool.get(field)) for tool in payload["tools"] if tool.get(field)})
    plural = {"role": "roles", "ecosystem": "ecosystems", "capability": "capabilities", "surface": "surfaces"}[field]
    return sorted(
        {
            value
            for tool in payload["tools"]
            for value in tool.get(plural, [])
            if isinstance(value, str) and value
        }
    )


def render_text(tool: dict[str, Any], args: argparse.Namespace) -> str:
    lines = [
            f"{tool['id']} | {tool['name']}",
            f"  kind: {tool['kind']}",
            f"  roles: {', '.join(tool['roles'])}",
            f"  ecosystems: {', '.join(tool['ecosystems'])}",
            f"  capabilities: {', '.join(tool['capabilities'])}",
            f"  surfaces: {', '.join(tool['surfaces'])}",
            f"  risk: {tool['risk']}",
            f"  adoption: {tool['adoption']}",
            f"  status: {tool['status']}",
            f"  license_review: {tool['license_review']}",
            f"  official_url: {tool['official_url']}",
            f"  fallback: {tool['fallback']}",
            f"  selection_note: {tool['selection_note']}",
    ]
    if args.recommend:
        lines.append(f"  recommendation: {', '.join(recommendation_reasons(tool, args))}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--id", dest="tool_id")
    parser.add_argument("--role")
    parser.add_argument("--ecosystem")
    parser.add_argument("--kind")
    parser.add_argument("--capability")
    parser.add_argument("--surface")
    parser.add_argument("--risk", choices=("low", "medium", "high"))
    parser.add_argument("--max-risk", choices=("low", "medium", "high"))
    parser.add_argument("--adoption")
    parser.add_argument("--status")
    parser.add_argument("--recommend", action="store_true", help="Rank filtered candidates by risk, ecosystem fit, and adoption cost")
    parser.add_argument("--top", type=int, help="Limit returned candidates after optional ranking")
    parser.add_argument(
        "--list-values",
        choices=("role", "ecosystem", "kind", "capability", "surface", "risk", "adoption", "status"),
    )
    parser.add_argument("--json", action="store_true", help="Emit matching records as JSON")
    args = parser.parse_args()

    if args.top is not None and args.top < 1:
        parser.error("--top must be at least 1")
    if args.recommend and not any((args.role, args.capability, args.surface, args.tool_id)):
        parser.error("--recommend requires --role, --capability, --surface, or --id")

    try:
        payload = load_registry(args.registry)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.list_values:
        print("\n".join(list_values(payload, args.list_values)))
        return 0

    tools = search(payload, args)
    if args.json:
        output = tools
        if args.recommend:
            output = [
                {**tool, "recommendation_reasons": recommendation_reasons(tool, args)}
                for tool in tools
            ]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif tools:
        print("\n\n".join(render_text(tool, args) for tool in tools))
    else:
        print("No matching toolkit entries.")
    return 0 if tools else 1


if __name__ == "__main__":
    raise SystemExit(main())

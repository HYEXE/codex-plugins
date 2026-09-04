#!/usr/bin/env python3
"""Search the UI/UX Advisor frontend toolkit registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REGISTRY_PATH = (
    Path(__file__).resolve().parents[1] / "references" / "frontend-toolkit-registry.json"
)
RELATIONS_PATH = (
    Path(__file__).resolve().parents[1] / "references" / "frontend-stack-relations.json"
)
WEB_FRAMEWORKS = {"vanilla", "react", "vue", "svelte", "angular", "solid", "astro"}
RISK_RANK = {"low": 0, "medium": 1, "high": 2}
ADOPTION_RANK = {"native": 0, "specification": 1, "package": 2, "registry": 3, "source-copy": 4}
RECOMMENDATION_STRATEGIES = ("conservative", "ecosystem-first")


def load_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("tools"), list):
        raise ValueError(f"{path}: expected an object with a tools array")
    return payload


def load_relations(path: Path, registry: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    relations = payload.get("relations") if isinstance(payload, dict) else None
    if not isinstance(relations, list):
        raise ValueError(f"{path}: expected an object with a relations array")
    known_ids = {
        tool["id"]
        for tool in registry["tools"]
        if isinstance(tool, dict) and isinstance(tool.get("id"), str)
    }
    relation_ids = [
        relation.get("tool_id")
        for relation in relations
        if isinstance(relation, dict)
    ]
    if len(relation_ids) != len(relations) or any(
        not isinstance(tool_id, str) or tool_id not in known_ids
        for tool_id in relation_ids
    ):
        raise ValueError(f"{path}: relations must reference known toolkit IDs")
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError(f"{path}: duplicate toolkit relation IDs")
    return payload


def load_existing_packages(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: package manifest must be an object")
    packages: set[str] = set()
    for field in (
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    ):
        dependencies = payload.get(field, {})
        if dependencies is None:
            continue
        if not isinstance(dependencies, dict) or any(
            not isinstance(name, str) or not isinstance(version, str)
            for name, version in dependencies.items()
        ):
            raise ValueError(f"{path}: {field} must map package names to versions")
        packages.update(dependencies)
    return packages


def relation_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        relation["tool_id"]: relation
        for relation in payload["relations"]
        if isinstance(relation, dict) and isinstance(relation.get("tool_id"), str)
    }


def detect_existing_tool_ids(
    relations_payload: dict[str, Any],
    packages: set[str],
) -> set[str]:
    return {
        relation["tool_id"]
        for relation in relations_payload["relations"]
        if isinstance(relation, dict)
        and isinstance(relation.get("tool_id"), str)
        and packages.intersection(relation.get("package_names", []))
    }


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
    tools = [
        tool
        for tool in payload["tools"]
        if isinstance(tool, dict) and matches(tool, args)
    ]
    if getattr(args, "recommend", False):
        tools = sorted(tools, key=lambda tool: recommendation_key(tool, args))
    top = getattr(args, "top", None)
    return tools[:top] if top is not None else tools


def recommendation_key(tool: dict[str, Any], args: argparse.Namespace) -> tuple[Any, ...]:
    ecosystems = tool.get("ecosystems", [])
    ecosystem_penalty = 0
    if args.ecosystem and args.ecosystem not in ecosystems and "web" in ecosystems:
        ecosystem_penalty = 1
    installed_ids = set(getattr(args, "existing_tool_ids", []) or [])
    installed_penalty = 0 if tool.get("id") in installed_ids else 1
    risk_rank = RISK_RANK.get(str(tool.get("risk")), 99)
    adoption_rank = ADOPTION_RANK.get(str(tool.get("adoption")), 99)
    strategy = getattr(args, "strategy", "conservative")
    if strategy == "ecosystem-first":
        priorities = (ecosystem_penalty, risk_rank, adoption_rank)
    else:
        priorities = (risk_rank, ecosystem_penalty, adoption_rank)
    return (installed_penalty, *priorities, str(tool.get("id", "")))


def recommendation_reasons(tool: dict[str, Any], args: argparse.Namespace) -> list[str]:
    reasons = [
        f"strategy={getattr(args, 'strategy', 'conservative')}",
        f"risk={tool['risk']}",
        f"adoption={tool['adoption']}",
    ]
    if tool.get("id") in set(getattr(args, "existing_tool_ids", []) or []):
        reasons.append("installed=true")
    if args.ecosystem:
        match = "exact" if args.ecosystem in tool.get("ecosystems", []) else "web-fallback"
        reasons.append(f"ecosystem={match}")
    for name, field in (
        ("role", "roles"),
        ("capability", "capabilities"),
        ("surface", "surfaces"),
    ):
        value = getattr(args, name)
        if value and value in tool.get(field, []):
            reasons.append(f"{name}={value}")
    return reasons


def recommendation_warnings(
    tool: dict[str, Any],
    relations_payload: dict[str, Any],
    args: argparse.Namespace,
) -> list[dict[str, str]]:
    relations = relation_index(relations_payload)
    tool_id = str(tool.get("id", ""))
    relation = relations.get(tool_id, {})
    installed_ids = set(getattr(args, "existing_tool_ids", []) or [])
    warnings: list[dict[str, str]] = []
    for related_tool in sorted(
        installed_ids.intersection(relation.get("conflicts_with", []))
    ):
        warnings.append(
            {
                "code": "conflicts-with-installed",
                "related_tool": related_tool,
                "message": f"{tool_id} conflicts with installed {related_tool}",
            }
        )
    for related_tool in sorted(
        installed_ids.intersection(relation.get("overlaps_with", []))
    ):
        warnings.append(
            {
                "code": "overlaps-with-installed",
                "related_tool": related_tool,
                "message": f"{tool_id} overlaps with installed {related_tool}",
            }
        )
    requested_role = getattr(args, "role", None)
    if requested_role and tool_id not in installed_ids:
        for related_tool in sorted(installed_ids):
            if requested_role in relations.get(related_tool, {}).get("provides_roles", []):
                warnings.append(
                    {
                        "code": "role-provided-by-installed",
                        "related_tool": related_tool,
                        "message": f"installed {related_tool} already provides {requested_role}",
                    }
                )
    return warnings


def build_recommendation_context(
    relations_payload: dict[str, Any],
    args: argparse.Namespace,
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    relations = relation_index(relations_payload)
    installed_ids = sorted(set(getattr(args, "existing_tool_ids", []) or []))
    provided_roles: dict[str, list[str]] = {}
    for tool_id in installed_ids:
        for role in relations.get(tool_id, {}).get("provides_roles", []):
            provided_roles.setdefault(role, []).append(tool_id)
    warnings_by_tool = {
        str(tool["id"]): warnings
        for tool in tools
        if (warnings := recommendation_warnings(tool, relations_payload, args))
    }
    return {
        "strategy": getattr(args, "strategy", "conservative"),
        "existing_packages": sorted(set(getattr(args, "existing_packages", []) or [])),
        "installed_toolkits": installed_ids,
        "provided_roles": {
            role: sorted(tool_ids) for role, tool_ids in sorted(provided_roles.items())
        },
        "warnings_by_tool": warnings_by_tool,
    }


def list_values(payload: dict[str, Any], field: str) -> list[str]:
    if field == "risk":
        return sorted({str(tool.get("risk")) for tool in payload["tools"] if tool.get("risk")})
    if field == "status":
        return sorted({str(tool.get("status")) for tool in payload["tools"] if tool.get("status")})
    if field in {"kind", "adoption"}:
        return sorted({str(tool.get(field)) for tool in payload["tools"] if tool.get(field)})
    plural = {
        "role": "roles",
        "ecosystem": "ecosystems",
        "capability": "capabilities",
        "surface": "surfaces",
    }[field]
    return sorted(
        {
            value
            for tool in payload["tools"]
            for value in tool.get(plural, [])
            if isinstance(value, str) and value
        }
    )


def render_text(
    tool: dict[str, Any],
    args: argparse.Namespace,
    warnings: list[dict[str, str]] | None = None,
) -> str:
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
    for warning in warnings or []:
        lines.append(f"  warning[{warning['code']}]: {warning['message']}")
    return "\n".join(lines)


def render_context(context: dict[str, Any]) -> str:
    provided_roles = context["provided_roles"]
    role_text = "; ".join(
        f"{role}={','.join(tool_ids)}" for role, tool_ids in provided_roles.items()
    ) or "(none)"
    return "\n".join(
        (
            "Existing stack context",
            f"  strategy: {context['strategy']}",
            f"  installed_toolkits: {', '.join(context['installed_toolkits']) or '(none)'}",
            f"  provided_roles: {role_text}",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--relations", type=Path, default=RELATIONS_PATH)
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
    parser.add_argument(
        "--strategy",
        choices=RECOMMENDATION_STRATEGIES,
        default="conservative",
        help="Rank by low risk first or exact ecosystem fit first",
    )
    parser.add_argument(
        "--existing-stack",
        type=Path,
        help=(
            "Read dependencies from a package.json and report installed, conflicting, "
            "or overlapping toolkits"
        ),
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Include recommendation context and structured warnings",
    )
    parser.add_argument(
        "--recommend",
        action="store_true",
        help="Rank filtered candidates by risk, ecosystem fit, and adoption cost",
    )
    parser.add_argument("--top", type=int, help="Limit returned candidates after optional ranking")
    parser.add_argument(
        "--list-values",
        choices=(
            "role",
            "ecosystem",
            "kind",
            "capability",
            "surface",
            "risk",
            "adoption",
            "status",
        ),
    )
    parser.add_argument("--json", action="store_true", help="Emit matching records as JSON")
    args = parser.parse_args()

    if args.top is not None and args.top < 1:
        parser.error("--top must be at least 1")
    if args.recommend and not any((args.role, args.capability, args.surface, args.tool_id)):
        parser.error("--recommend requires --role, --capability, --surface, or --id")

    try:
        payload = load_registry(args.registry)
        relations_payload = load_relations(args.relations, payload)
        args.existing_packages = (
            load_existing_packages(args.existing_stack) if args.existing_stack else set()
        )
        args.existing_tool_ids = detect_existing_tool_ids(
            relations_payload,
            args.existing_packages,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    if args.list_values:
        print("\n".join(list_values(payload, args.list_values)))
        return 0

    tools = search(payload, args)
    context = build_recommendation_context(relations_payload, args, tools)
    include_context = args.explain or args.existing_stack is not None
    if args.json:
        output = tools
        if args.recommend:
            output = [
                {
                    **tool,
                    "recommendation_reasons": recommendation_reasons(tool, args),
                    "recommendation_warnings": recommendation_warnings(
                        tool,
                        relations_payload,
                        args,
                    ),
                }
                for tool in tools
            ]
        rendered: Any = (
            {"context": context, "results": output} if include_context else output
        )
        print(json.dumps(rendered, ensure_ascii=False, indent=2))
    elif tools:
        if include_context:
            print(render_context(context))
            print()
        print(
            "\n\n".join(
                render_text(
                    tool,
                    args,
                    context["warnings_by_tool"].get(str(tool["id"]), []),
                )
                for tool in tools
            )
        )
    else:
        if include_context:
            print(render_context(context))
            print()
        print("No matching toolkit entries.")
    return 0 if tools else 1


if __name__ == "__main__":
    raise SystemExit(main())

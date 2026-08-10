#!/usr/bin/env python3
"""Validate the Codex Workflows repository without third-party packages."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
EXPECTED_PLUGINS = {
    "prompt-compiler": "prompt-compiler",
    "uiux-advisor": "uiux-advisor",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def run(command: list[str], cwd: Path, failures: list[str]) -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=environment)
    if process.stdout.strip():
        print(process.stdout.rstrip())
    if process.returncode:
        detail = process.stderr.strip() or process.stdout.strip() or f"exit {process.returncode}"
        failures.append(f"command failed in {cwd.relative_to(ROOT)}: {' '.join(command)}\n{detail}")


def validate_marketplace(failures: list[str]) -> None:
    check(MARKETPLACE_PATH.is_file(), "missing .agents/plugins/marketplace.json", failures)
    if not MARKETPLACE_PATH.is_file():
        return
    payload = load_json(MARKETPLACE_PATH)
    check(payload.get("name") == "codex-workflows-kr", "unexpected marketplace name", failures)
    entries = payload.get("plugins")
    check(isinstance(entries, list), "marketplace plugins must be an array", failures)
    if not isinstance(entries, list):
        return
    names = [entry.get("name") for entry in entries if isinstance(entry, dict)]
    check(names == list(EXPECTED_PLUGINS), f"unexpected marketplace order: {names}", failures)
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append("marketplace entry must be an object")
            continue
        name = entry.get("name")
        source = entry.get("source")
        policy = entry.get("policy")
        check(name in EXPECTED_PLUGINS, f"unknown marketplace plugin: {name}", failures)
        check(
            isinstance(source, dict)
            and source.get("source") == "local"
            and source.get("path") == f"./plugins/{name}",
            f"invalid marketplace source for {name}",
            failures,
        )
        check(
            isinstance(policy, dict)
            and policy.get("installation") in {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}
            and policy.get("authentication") in {"ON_INSTALL", "ON_USE"}
            and "products" not in policy,
            f"invalid marketplace policy for {name}",
            failures,
        )
        check(bool(entry.get("category")), f"missing marketplace category for {name}", failures)


def validate_plugin(plugin_name: str, skill_name: str, failures: list[str]) -> None:
    plugin_dir = ROOT / "plugins" / plugin_name
    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
    skill_dir = plugin_dir / "skills" / skill_name
    skill_path = skill_dir / "SKILL.md"

    check(manifest_path.is_file(), f"{plugin_name}: missing plugin.json", failures)
    check(skill_path.is_file(), f"{plugin_name}: missing {skill_name}/SKILL.md", failures)
    if not manifest_path.is_file() or not skill_path.is_file():
        return

    manifest = load_json(manifest_path)
    check(manifest.get("name") == plugin_name, f"{plugin_name}: manifest name mismatch", failures)
    check(bool(re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", str(manifest.get("version", "")))), f"{plugin_name}: invalid version", failures)
    check(manifest.get("skills") == "./skills/", f"{plugin_name}: skills path must be ./skills/", failures)
    check(bool(manifest.get("description")), f"{plugin_name}: missing description", failures)
    check(bool((manifest.get("author") or {}).get("name")), f"{plugin_name}: missing author.name", failures)
    interface = manifest.get("interface") or {}
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        check(bool(interface.get(field)), f"{plugin_name}: missing interface.{field}", failures)
    for field in ("composerIcon", "logo"):
        value = interface.get(field)
        if value:
            check(value.startswith("./"), f"{plugin_name}: {field} must start with ./", failures)
            check((plugin_dir / value[2:]).is_file(), f"{plugin_name}: missing {field} asset {value}", failures)

    frontmatter = parse_frontmatter(skill_path)
    check(frontmatter.get("name") == skill_name, f"{plugin_name}: skill name mismatch", failures)
    check(bool(frontmatter.get("description")), f"{plugin_name}: missing skill description", failures)
    check(len(f"{plugin_name}:{skill_name}") <= 64, f"{plugin_name}: combined identity exceeds 64 characters", failures)

    agents_yaml = skill_dir / "agents" / "openai.yaml"
    if agents_yaml.is_file():
        agents_text = agents_yaml.read_text(encoding="utf-8")
        check("products:" not in agents_text, f"{plugin_name}: unsupported agents policy.products", failures)

    for script in skill_dir.rglob("*.py"):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            failures.append(f"{plugin_name}: invalid Python syntax in {script.relative_to(ROOT)}: {exc}")


def validate_uiux_kb(failures: list[str]) -> None:
    skill_dir = ROOT / "plugins" / "uiux-advisor" / "skills" / "uiux-advisor"
    kb_dir = skill_dir / "references" / "kb"
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate((kb_dir / "guides.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            failures.append(f"uiux-advisor: invalid guides.jsonl line {line_number}: {exc}")
    ids = [record.get("id") for record in records]
    markdown_paths = [record.get("markdown_path") for record in records]
    check(len(records) == 50, f"uiux-advisor: expected 50 records, got {len(records)}", failures)
    check(len(ids) == len(set(ids)), "uiux-advisor: duplicate guide IDs", failures)
    check(all(isinstance(path, str) and (kb_dir / path).is_file() for path in markdown_paths), "uiux-advisor: missing guide Markdown", failures)
    check(len(list((kb_dir / "guides").rglob("*.md"))) == 50, "uiux-advisor: guide file count mismatch", failures)
    check(isinstance(load_json(kb_dir / "sources.json"), (list, dict)), "uiux-advisor: invalid sources.json", failures)

    broken: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)#]+\.md)(?:#[^)]+)?\)")
    for markdown in kb_dir.rglob("*.md"):
        for target in link_pattern.findall(markdown.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://")):
                continue
            resolved = (markdown.parent / target).resolve()
            try:
                resolved.relative_to(kb_dir.resolve())
            except ValueError:
                broken.append(f"{markdown.relative_to(kb_dir)} -> unsafe {target}")
                continue
            if not resolved.is_file():
                broken.append(f"{markdown.relative_to(kb_dir)} -> {target}")
    check(not broken, f"uiux-advisor: broken links: {broken[:5]}", failures)


def main() -> int:
    failures: list[str] = []
    validate_marketplace(failures)
    for plugin_name, skill_name in EXPECTED_PLUGINS.items():
        validate_plugin(plugin_name, skill_name, failures)
    validate_uiux_kb(failures)

    python = sys.executable
    prompt_dir = ROOT / "plugins" / "prompt-compiler" / "skills" / "prompt-compiler"
    uiux_dir = ROOT / "plugins" / "uiux-advisor" / "skills" / "uiux-advisor"
    run([python, "scripts/validate_package.py"], prompt_dir, failures)
    run([python, "scripts/eval_harness.py", "score", "evals/golden_results.jsonl"], prompt_dir, failures)
    run([python, "scripts/search_kb.py", "--id", "23"], uiux_dir, failures)

    if failures:
        print("\nMONOREPO VALIDATION FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nMONOREPO VALIDATION PASSED: 2 plugins, 2 skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

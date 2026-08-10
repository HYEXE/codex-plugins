#!/usr/bin/env python3
"""Validate the Codex Workflows repository without third-party packages."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
ROUTING_CASES_PATH = ROOT / "tests" / "skill-routing.jsonl"
UPDATE_SCRIPT_MARKERS = {
    "bash": (
        ROOT / "scripts" / "update_plugins.sh",
        (
            "codex-workflows-kr",
            "prompt-compiler",
            "uiux-advisor",
            "run_codex plugin marketplace upgrade",
            "run_codex plugin add",
            "--dry-run",
        ),
    ),
    "powershell": (
        ROOT / "scripts" / "update_plugins.ps1",
        (
            "codex-workflows-kr",
            "prompt-compiler",
            "uiux-advisor",
            '@("plugin", "marketplace", "upgrade"',
            '@("plugin", "add"',
            "$DryRun",
        ),
    ),
}
EXPECTED_PLUGINS = {
    "prompt-compiler": ("prompt-compiler", "prompt-evaluator"),
    "uiux-advisor": ("uiux-advisor", "uiux-auditor"),
}
REQUIRED_SKILL_FILES = {
    ("prompt-compiler", "prompt-compiler"): ("references/language-policy.md",),
    ("prompt-compiler", "prompt-evaluator"): (
        "references/evaluation-rubric.md",
        "assets/icon.svg",
    ),
    ("uiux-advisor", "uiux-advisor"): ("scripts/search_kb.py",),
    ("uiux-advisor", "uiux-auditor"): (
        "references/audit-rubric.md",
        "assets/icon.svg",
    ),
}
FORBIDDEN_SKILL_DOCS = ("README.md", "CHANGELOG.md")


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


def run(command: list[str], cwd: Path, failures: list[str], *, echo: bool = True) -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=environment)
    if echo and process.stdout.strip():
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


def validate_skill(plugin_name: str, plugin_dir: Path, skill_name: str, failures: list[str]) -> None:
    skill_dir = plugin_dir / "skills" / skill_name
    skill_path = skill_dir / "SKILL.md"
    check(skill_path.is_file(), f"{plugin_name}: missing {skill_name}/SKILL.md", failures)
    if not skill_path.is_file():
        return

    skill_text = skill_path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(skill_path)
    check(frontmatter.get("name") == skill_name, f"{plugin_name}: {skill_name} name mismatch", failures)
    check(bool(frontmatter.get("description")), f"{plugin_name}: {skill_name} missing description", failures)
    check(len(f"{plugin_name}:{skill_name}") <= 64, f"{plugin_name}: combined identity exceeds 64 characters", failures)
    check("[TODO:" not in skill_text, f"{plugin_name}: {skill_name} contains TODO placeholders", failures)
    check(len(skill_text.splitlines()) <= 500, f"{plugin_name}: {skill_name}/SKILL.md exceeds 500 lines", failures)

    for filename in FORBIDDEN_SKILL_DOCS:
        check(not (skill_dir / filename).exists(), f"{plugin_name}: move {skill_name}/{filename} outside the skill", failures)

    for relative in REQUIRED_SKILL_FILES.get((plugin_name, skill_name), ()):
        check((skill_dir / relative).is_file(), f"{plugin_name}: {skill_name} missing {relative}", failures)

    agents_yaml = skill_dir / "agents" / "openai.yaml"
    check(agents_yaml.is_file(), f"{plugin_name}: {skill_name} missing agents/openai.yaml", failures)
    if agents_yaml.is_file():
        agents_text = agents_yaml.read_text(encoding="utf-8")
        check("products:" not in agents_text, f"{plugin_name}: {skill_name} has unsupported policy.products", failures)
        check(f"${skill_name}" in agents_text, f"{plugin_name}: {skill_name} default_prompt must mention ${skill_name}", failures)
        for icon_path in re.findall(r'^\s+icon_(?:small|large):\s+"([^"]+)"', agents_text, re.MULTILINE):
            check(icon_path.startswith("./"), f"{plugin_name}: {skill_name} icon path must start with ./", failures)
            check((skill_dir / icon_path[2:]).is_file(), f"{plugin_name}: {skill_name} missing icon {icon_path}", failures)

    for script in skill_dir.rglob("*.py"):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            failures.append(f"{plugin_name}: invalid Python syntax in {script.relative_to(ROOT)}: {exc}")


def validate_plugin(plugin_name: str, skill_names: tuple[str, ...], failures: list[str]) -> None:
    plugin_dir = ROOT / "plugins" / plugin_name
    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
    check(manifest_path.is_file(), f"{plugin_name}: missing plugin.json", failures)
    if not manifest_path.is_file():
        return

    manifest = load_json(manifest_path)
    check(manifest.get("name") == plugin_name, f"{plugin_name}: manifest name mismatch", failures)
    check(bool(re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", str(manifest.get("version", "")))), f"{plugin_name}: invalid version", failures)
    check(manifest.get("skills") == "./skills/", f"{plugin_name}: skills path must be ./skills/", failures)
    check(bool(manifest.get("description")), f"{plugin_name}: missing description", failures)
    check(bool((manifest.get("author") or {}).get("name")), f"{plugin_name}: missing author.name", failures)
    interface = manifest.get("interface") or {}
    default_prompts = interface.get("defaultPrompt")
    check(
        isinstance(default_prompts, list) and 1 <= len(default_prompts) <= 3,
        f"{plugin_name}: interface.defaultPrompt must contain 1 to 3 entries",
        failures,
    )
    if isinstance(default_prompts, list):
        for index, prompt in enumerate(default_prompts, 1):
            check(
                isinstance(prompt, str) and bool(prompt.strip()),
                f"{plugin_name}: defaultPrompt[{index}] must be a non-empty string",
                failures,
            )
            if isinstance(prompt, str):
                check(
                    len(prompt) <= 128,
                    f"{plugin_name}: defaultPrompt[{index}] exceeds 128 characters",
                    failures,
                )
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        check(bool(interface.get(field)), f"{plugin_name}: missing interface.{field}", failures)
    for field in ("composerIcon", "logo"):
        value = interface.get(field)
        if value:
            check(value.startswith("./"), f"{plugin_name}: {field} must start with ./", failures)
            check((plugin_dir / value[2:]).is_file(), f"{plugin_name}: missing {field} asset {value}", failures)

    discovered = tuple(sorted(path.parent.name for path in (plugin_dir / "skills").glob("*/SKILL.md")))
    check(discovered == tuple(sorted(skill_names)), f"{plugin_name}: unexpected skills {discovered}", failures)
    for skill_name in skill_names:
        validate_skill(plugin_name, plugin_dir, skill_name, failures)


def validate_update_scripts(failures: list[str]) -> None:
    for label, (path, markers) in UPDATE_SCRIPT_MARKERS.items():
        check(path.is_file(), f"missing {label} update script", failures)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            check(marker in text, f"{label} update script missing marker: {marker}", failures)

    bash_script = UPDATE_SCRIPT_MARKERS["bash"][0]
    if bash_script.is_file():
        if os.name != "nt":
            check(os.access(bash_script, os.X_OK), "bash update script is not executable", failures)
        bash = shutil.which("bash")
        if bash:
            run([bash, "-n", str(bash_script)], ROOT, failures, echo=False)
            run([bash, str(bash_script), "--dry-run"], ROOT, failures, echo=False)

    powershell_script = UPDATE_SCRIPT_MARKERS["powershell"][0]
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell_script.is_file() and powershell:
        run([powershell, "-NoProfile", "-File", str(powershell_script), "-DryRun"], ROOT, failures, echo=False)


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


def validate_routing_cases(failures: list[str]) -> None:
    check(ROUTING_CASES_PATH.is_file(), "missing tests/skill-routing.jsonl", failures)
    if not ROUTING_CASES_PATH.is_file():
        return

    known_skills = {skill for skills in EXPECTED_PLUGINS.values() for skill in skills}
    seen_ids: set[str] = set()
    counts = {skill: 0 for skill in known_skills}
    for line_number, line in enumerate(ROUTING_CASES_PATH.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"routing cases line {line_number}: invalid JSON: {exc}")
            continue
        case_id = case.get("id")
        prompt = case.get("prompt")
        expected_skill = case.get("expected_skill")
        check(isinstance(case_id, str) and bool(case_id), f"routing cases line {line_number}: missing id", failures)
        check(case_id not in seen_ids, f"routing cases: duplicate id {case_id}", failures)
        if isinstance(case_id, str):
            seen_ids.add(case_id)
        check(isinstance(prompt, str) and bool(prompt.strip()), f"routing cases {case_id}: missing prompt", failures)
        if isinstance(prompt, str):
            leaks_selector = any(f"${skill_name}" in prompt for skill_name in known_skills)
            check(not leaks_selector, f"routing cases {case_id}: prompt leaks an explicit skill selector", failures)
        check(expected_skill in known_skills, f"routing cases {case_id}: unknown skill {expected_skill}", failures)
        if expected_skill in counts:
            counts[expected_skill] += 1
        check(bool(case.get("boundary")), f"routing cases {case_id}: missing boundary", failures)

    for skill_name, count in sorted(counts.items()):
        check(count >= 2, f"routing cases: {skill_name} needs at least 2 cases, got {count}", failures)


def main() -> int:
    failures: list[str] = []
    validate_marketplace(failures)
    for plugin_name, skill_names in EXPECTED_PLUGINS.items():
        validate_plugin(plugin_name, skill_names, failures)
    validate_update_scripts(failures)
    validate_uiux_kb(failures)
    validate_routing_cases(failures)

    python = sys.executable
    prompt_dir = ROOT / "plugins" / "prompt-compiler" / "skills" / "prompt-compiler"
    uiux_dir = ROOT / "plugins" / "uiux-advisor" / "skills" / "uiux-advisor"
    run([python, "scripts/validate_package.py"], prompt_dir, failures)
    run([python, "scripts/eval_harness.py", "--help"], prompt_dir, failures, echo=False)
    run([python, "scripts/eval_harness.py", "score", "evals/golden_results.jsonl"], prompt_dir, failures)
    run([python, "scripts/search_kb.py", "--id", "23"], uiux_dir, failures)
    run(
        [python, "scripts/search_kb.py", "--query", "가입 오류 복구 접근성", "--top", "3", "--json"],
        uiux_dir,
        failures,
        echo=False,
    )

    if failures:
        print("\nMONOREPO VALIDATION FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    skill_count = sum(len(skill_names) for skill_names in EXPECTED_PLUGINS.values())
    print(f"\nMONOREPO VALIDATION PASSED: {len(EXPECTED_PLUGINS)} plugins, {skill_count} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

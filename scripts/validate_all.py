#!/usr/bin/env python3
"""Validate the Codex Workflows repository without third-party packages."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
ROUTING_EVALUATOR_PATH = ROOT / "scripts" / "eval_routing.py"
UIUX_SEARCH_EVALUATOR_PATH = ROOT / "scripts" / "eval_uiux_search.py"
VERSION_CHECK_PATH = ROOT / "scripts" / "check_version_bumps.py"
SEMVER_PATTERN = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\."
    r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
GUIDE_ID_PATTERN = re.compile(r"uiux-playbook-(\d{3})")
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
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
    "uiux-advisor": (
        "uiux-advisor",
        "uiux-auditor",
        "implement-ui-motion",
        "build-data-visualization",
        "compose-creative-ui",
    ),
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
    ("uiux-advisor", "implement-ui-motion"): (
        "references/motion-toolkit-selection.md",
        "references/motion-contract-and-qa.md",
        "assets/icon.svg",
    ),
    ("uiux-advisor", "build-data-visualization"): (
        "references/visualization-toolkit-selection.md",
        "references/chart-contract-and-qa.md",
        "assets/icon.svg",
    ),
    ("uiux-advisor", "compose-creative-ui"): (
        "references/component-toolkit-selection.md",
        "references/composition-and-qa.md",
        "assets/icon.svg",
    ),
}
REQUIRED_SKILL_MARKERS = {
    ("uiux-advisor", "implement-ui-motion"): (
        "Anime.js",
        "Web Animations API",
        "View Transition API",
        "Motion",
        "GSAP",
        "prefers-reduced-motion",
    ),
    ("uiux-advisor", "build-data-visualization"): (
        "Bklit UI",
        "Recharts",
        "Apache ECharts",
        "Observable Plot",
        "D3",
        "텍스트 또는 표",
    ),
    ("uiux-advisor", "compose-creative-ui"): (
        "Magic UI",
        "Aceternity UI",
        "React Bits",
        "shadcn/ui",
        "React Aria",
        "Ark UI",
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

    required_markers = REQUIRED_SKILL_MARKERS.get((plugin_name, skill_name), ())
    if required_markers:
        markdown_text = "\n".join(
            path.read_text(encoding="utf-8") for path in sorted(skill_dir.rglob("*.md"))
        )
        for marker in required_markers:
            check(marker in markdown_text, f"{plugin_name}: {skill_name} missing toolkit marker {marker}", failures)

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
    check(bool(SEMVER_PATTERN.fullmatch(str(manifest.get("version", "")))), f"{plugin_name}: invalid version", failures)
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


def validate_repository_scripts(failures: list[str]) -> None:
    for path in (ROUTING_EVALUATOR_PATH, UIUX_SEARCH_EVALUATOR_PATH, VERSION_CHECK_PATH):
        check(path.is_file(), f"missing {path.relative_to(ROOT)}", failures)
    for script in sorted((ROOT / "scripts").glob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            failures.append(f"invalid Python syntax in {script.relative_to(ROOT)}: {exc}")


def validate_uiux_kb(failures: list[str]) -> None:
    skill_dir = ROOT / "plugins" / "uiux-advisor" / "skills" / "uiux-advisor"
    kb_dir = skill_dir / "references" / "kb"
    guides_path = kb_dir / "guides.jsonl"
    sources_path = kb_dir / "sources.json"
    check(guides_path.is_file(), "uiux-advisor: missing guides.jsonl", failures)
    check(sources_path.is_file(), "uiux-advisor: missing sources.json", failures)
    if not guides_path.is_file() or not sources_path.is_file():
        return

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(guides_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"uiux-advisor: invalid guides.jsonl line {line_number}: {exc}")
            continue
        if not isinstance(record, dict):
            failures.append(f"uiux-advisor: guides.jsonl line {line_number} must be an object")
            continue
        records.append(record)

    try:
        sources = load_json(sources_path)
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"uiux-advisor: invalid sources.json: {exc}")
        sources = []
    check(isinstance(sources, list), "uiux-advisor: sources.json must be an array", failures)
    if isinstance(sources, list):
        source_records = [source for source in sources if isinstance(source, dict)]
        check(len(source_records) == len(sources), "uiux-advisor: every source must be an object", failures)
    else:
        source_records = []

    source_ids: list[str] = []
    source_required = ("id", "title", "publisher", "url", "source_type", "scope", "stability", "usage")
    for index, source in enumerate(source_records, 1):
        label = source.get("id") or f"source-{index}"
        for field in source_required:
            check(isinstance(source.get(field), str) and bool(source[field].strip()), f"uiux-advisor: {label} missing {field}", failures)
        source_id = source.get("id")
        if isinstance(source_id, str):
            source_ids.append(source_id)
        url = source.get("url")
        check(isinstance(url, str) and url.startswith(("https://", "http://")), f"uiux-advisor: {label} has invalid URL", failures)
    check(len(source_ids) == len(set(source_ids)), "uiux-advisor: duplicate source IDs", failures)
    known_source_ids = set(source_ids)

    ids = [record.get("id") for record in records]
    markdown_paths = [record.get("markdown_path") for record in records]
    string_ids = [guide_id for guide_id in ids if isinstance(guide_id, str)]
    string_markdown_paths = [path for path in markdown_paths if isinstance(path, str)]
    check(len(records) == 50, f"uiux-advisor: expected 50 records, got {len(records)}", failures)
    check(len(string_ids) == len(set(string_ids)), "uiux-advisor: duplicate guide IDs", failures)
    check(len(string_markdown_paths) == len(set(string_markdown_paths)), "uiux-advisor: duplicate guide Markdown paths", failures)
    known_guide_ids = {guide_id for guide_id in ids if isinstance(guide_id, str)}
    used_source_ids: set[str] = set()
    required_fields = (
        "id",
        "num",
        "slug",
        "title",
        "category",
        "rule",
        "sources",
        "tags",
        "related_ids",
        "time_sensitive",
        "markdown_path",
        "version",
        "snapshot_date",
    )

    for index, record in enumerate(records, 1):
        guide_id = record.get("id")
        label = guide_id if isinstance(guide_id, str) and guide_id else f"guide-{index}"
        for field in required_fields:
            check(field in record, f"uiux-advisor: {label} missing {field}", failures)

        match = GUIDE_ID_PATTERN.fullmatch(guide_id) if isinstance(guide_id, str) else None
        check(match is not None, f"uiux-advisor: {label} has invalid guide ID", failures)
        if match:
            check(record.get("num") == int(match.group(1)), f"uiux-advisor: {label} num does not match ID", failures)
        slug = record.get("slug")
        check(isinstance(slug, str) and SLUG_PATTERN.fullmatch(slug) is not None, f"uiux-advisor: {label} has invalid slug", failures)
        for field in ("title", "category", "rule"):
            check(isinstance(record.get(field), str) and bool(record[field].strip()), f"uiux-advisor: {label} missing {field}", failures)

        version = record.get("version")
        check(isinstance(version, str) and SEMVER_PATTERN.fullmatch(version) is not None, f"uiux-advisor: {label} has invalid version", failures)
        snapshot_date = record.get("snapshot_date")
        try:
            parsed_snapshot = date.fromisoformat(snapshot_date) if isinstance(snapshot_date, str) else None
            check(parsed_snapshot is not None and parsed_snapshot <= date.today(), f"uiux-advisor: {label} has future snapshot_date", failures)
        except ValueError:
            failures.append(f"uiux-advisor: {label} has invalid snapshot_date")
        check(isinstance(record.get("time_sensitive"), bool), f"uiux-advisor: {label} time_sensitive must be boolean", failures)

        for field in ("sources", "tags", "related_ids"):
            values = record.get(field)
            check(
                isinstance(values, list) and bool(values) and all(isinstance(value, str) and value for value in values),
                f"uiux-advisor: {label} {field} must be a non-empty string array", failures)
            if isinstance(values, list):
                check(len(values) == len(set(values)), f"uiux-advisor: {label} has duplicate {field}", failures)

        record_sources = record.get("sources")
        if isinstance(record_sources, list):
            unknown_sources = sorted(set(record_sources) - known_source_ids)
            check(not unknown_sources, f"uiux-advisor: {label} references unknown sources {unknown_sources}", failures)
            used_source_ids.update(source_id for source_id in record_sources if isinstance(source_id, str))
        related_ids = record.get("related_ids")
        if isinstance(related_ids, list):
            unknown_related = sorted(set(related_ids) - known_guide_ids)
            check(not unknown_related, f"uiux-advisor: {label} references unknown guides {unknown_related}", failures)
            check(guide_id not in related_ids, f"uiux-advisor: {label} relates to itself", failures)

        markdown_path = record.get("markdown_path")
        if not isinstance(markdown_path, str):
            failures.append(f"uiux-advisor: {label} missing guide Markdown")
            continue
        resolved = (kb_dir / markdown_path).resolve()
        try:
            resolved.relative_to(kb_dir.resolve())
        except ValueError:
            failures.append(f"uiux-advisor: {label} has unsafe Markdown path {markdown_path}")
            continue
        check(resolved.is_file(), f"uiux-advisor: {label} missing guide Markdown {markdown_path}", failures)
        if resolved.is_file():
            frontmatter = parse_frontmatter(resolved)
            expected_frontmatter = {
                "id": guide_id,
                "title": record.get("title"),
                "slug": slug,
                "category": record.get("category"),
                "version": version,
                "snapshot_date": snapshot_date,
                "time_sensitive": str(record.get("time_sensitive")).lower(),
            }
            for field, expected in expected_frontmatter.items():
                check(frontmatter.get(field) == str(expected), f"uiux-advisor: {label} Markdown {field} mismatch", failures)

    unused_sources = sorted(known_source_ids - used_source_ids)
    check(not unused_sources, f"uiux-advisor: unused source registry entries {unused_sources}", failures)
    check(len(list((kb_dir / "guides").rglob("*.md"))) == 50, "uiux-advisor: guide file count mismatch", failures)

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
    for plugin_name, skill_names in EXPECTED_PLUGINS.items():
        validate_plugin(plugin_name, skill_names, failures)
    validate_update_scripts(failures)
    validate_repository_scripts(failures)
    validate_uiux_kb(failures)

    python = sys.executable
    prompt_dir = ROOT / "plugins" / "prompt-compiler" / "skills" / "prompt-compiler"
    uiux_dir = ROOT / "plugins" / "uiux-advisor" / "skills" / "uiux-advisor"
    run([python, "scripts/validate_package.py"], prompt_dir, failures)
    run([python, "scripts/eval_harness.py", "--help"], prompt_dir, failures, echo=False)
    run([python, "scripts/eval_harness.py", "score", "evals/golden_results.jsonl"], prompt_dir, failures)
    run([python, "scripts/search_kb.py", "--id", "23"], uiux_dir, failures)
    run([python, str(ROUTING_EVALUATOR_PATH), "validate"], ROOT, failures)
    run([python, str(UIUX_SEARCH_EVALUATOR_PATH)], ROOT, failures)
    run([python, str(VERSION_CHECK_PATH), "--help"], ROOT, failures, echo=False)

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

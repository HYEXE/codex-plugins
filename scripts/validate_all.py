#!/usr/bin/env python3
"""Validate the Codex Plugins repository without third-party packages."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from validate_observation_manifest import validate_manifest


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
ROUTING_EVALUATOR_PATH = ROOT / "scripts" / "eval_routing.py"
ROUTING_OBSERVATIONS_PATH = ROOT / "tests" / "observations.json"
VERSION_CHECK_PATH = ROOT / "scripts" / "check_version_bumps.py"
LIVE_EVAL_PATH = ROOT / "scripts" / "live_eval.py"
OBSERVATION_VALIDATOR_PATH = ROOT / "scripts" / "validate_observation_manifest.py"
SOURCE_LIVENESS_PATH = ROOT / "scripts" / "check_source_liveness.py"
RELEASE_ATTESTATION_PATH = ROOT / "scripts" / "create_release_attestation.py"
OBSERVATION_TOKEN = re.compile(r"\{observation:([a-z0-9-]+)\}")
SEMVER_PATTERN = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\."
    r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
SLUG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
UPDATE_SCRIPT_MARKERS = {
    "bash": (
        ROOT / "scripts" / "update_plugins.sh",
        (
            "run_codex plugin marketplace upgrade",
            "run_codex plugin add",
            "--dry-run",
        ),
    ),
    "powershell": (
        ROOT / "scripts" / "update_plugins.ps1",
        (
            '@("plugin", "marketplace", "upgrade"',
            '@("plugin", "add"',
            "$DryRun",
        ),
    ),
}
FORBIDDEN_SKILL_DOCS = ("README.md", "CHANGELOG.md")
README_PLUGIN_ROW = re.compile(
    r"^\|\s*`([a-z0-9-]+)`\s*\|\s*`([^`]+)`\s*\|",
    re.MULTILINE,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_repository_inventory(
    marketplace_plugin_names: list[str],
    failures: list[str],
    *,
    root: Path = ROOT,
) -> None:
    plugin_root = root / "plugins"
    directory_names = sorted(
        path.name
        for path in plugin_root.iterdir()
        if path.is_dir() and (path / ".codex-plugin" / "plugin.json").is_file()
    )
    marketplace_names = sorted(marketplace_plugin_names)
    check(
        directory_names == marketplace_names,
        f"plugin inventory mismatch: directories={directory_names}, marketplace={marketplace_names}",
        failures,
    )

    try:
        policy = load_json(root / "release" / "release-policy.json")
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"release policy cannot be loaded: {exc}")
        policy = {}
    policy_plugins = policy.get("plugins") if isinstance(policy, dict) else None
    policy_names = sorted(policy_plugins) if isinstance(policy_plugins, dict) else []
    check(
        directory_names == policy_names,
        f"plugin inventory mismatch: directories={directory_names}, release-policy={policy_names}",
        failures,
    )

    try:
        readme_text = (root / "README.md").read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"README cannot be loaded: {exc}")
        readme_text = ""
    readme_versions = dict(README_PLUGIN_ROW.findall(readme_text))
    readme_names = sorted(readme_versions)
    check(
        directory_names == readme_names,
        f"plugin inventory mismatch: directories={directory_names}, README={readme_names}",
        failures,
    )

    for plugin_name in directory_names:
        manifest_path = plugin_root / plugin_name / ".codex-plugin" / "plugin.json"
        try:
            manifest = load_json(manifest_path)
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{plugin_name}: manifest cannot be loaded: {exc}")
            continue
        version = manifest.get("version") if isinstance(manifest, dict) else None
        check(manifest.get("name") == plugin_name, f"{plugin_name}: manifest name mismatch", failures)
        check(
            readme_versions.get(plugin_name) == version,
            f"{plugin_name}: README version {readme_versions.get(plugin_name)!r} != manifest {version!r}",
            failures,
        )


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def resolve_config_path(config_path: Path, value: Any, label: str, failures: list[str]) -> Path:
    if not isinstance(value, str) or not value:
        failures.append(f"{label}: path must be a non-empty string")
        return config_path.parent
    resolved = (config_path.parent / value).resolve()
    try:
        resolved.relative_to(config_path.parents[1].resolve())
    except ValueError:
        failures.append(f"{label}: path escapes plugin directory: {value}")
        return config_path.parent
    return resolved


def load_quality_gates(plugin_name: str, failures: list[str]) -> tuple[Path, dict[str, Any]]:
    config_path = ROOT / "plugins" / plugin_name / ".codex-plugin" / "quality-gates.json"
    if not config_path.is_file():
        failures.append(f"{plugin_name}: missing .codex-plugin/quality-gates.json")
        return config_path, {}
    try:
        config = load_json(config_path)
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"{plugin_name}: invalid quality-gates.json: {exc}")
        return config_path, {}
    if not isinstance(config, dict):
        failures.append(f"{plugin_name}: quality-gates.json must be an object")
        return config_path, {}
    check(config.get("schema_version") == "1.0.0", f"{plugin_name}: quality gate schema_version must be 1.0.0", failures)
    check(config.get("plugin") == plugin_name, f"{plugin_name}: quality gate plugin mismatch", failures)
    skills = config.get("skills")
    check(isinstance(skills, dict) and bool(skills), f"{plugin_name}: quality gate skills must be a non-empty object", failures)
    return config_path, config


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


def validate_required_markers(
    plugin_name: str,
    skill_name: str,
    skill_dir: Path,
    required_markers: Any,
    failures: list[str],
) -> None:
    if not isinstance(required_markers, list):
        failures.append(
            f"{plugin_name}: {skill_name} required_markers must be an array"
        )
        return

    legacy_markdown_text: str | None = None
    skill_boundary = skill_dir.resolve()
    for index, marker in enumerate(required_markers, 1):
        label = f"{plugin_name}: {skill_name} required_markers[{index}]"
        if isinstance(marker, str):
            if not marker:
                failures.append(f"{label} must not be empty")
                continue
            if legacy_markdown_text is None:
                legacy_markdown_text = "\n".join(
                    path.read_text(encoding="utf-8")
                    for path in sorted(skill_dir.rglob("*.md"))
                )
            check(
                marker in legacy_markdown_text,
                f"{plugin_name}: {skill_name} missing legacy marker {marker}",
                failures,
            )
            continue

        if not isinstance(marker, dict):
            failures.append(f"{label} must be a string or object")
            continue
        unknown_fields = sorted(set(marker) - {"path", "contains", "regex"})
        if unknown_fields:
            failures.append(f"{label} has unknown fields {unknown_fields}")
            continue
        relative = marker.get("path")
        contains = marker.get("contains")
        regex = marker.get("regex")
        if not isinstance(relative, str) or not relative:
            failures.append(f"{label}.path must be a non-empty string")
            continue
        if (isinstance(contains, str) and bool(contains)) == (
            isinstance(regex, str) and bool(regex)
        ):
            failures.append(f"{label} must define exactly one of contains or regex")
            continue

        marker_path = (skill_dir / relative).resolve()
        try:
            marker_path.relative_to(skill_boundary)
        except ValueError:
            failures.append(f"{label}.path escapes the skill directory: {relative}")
            continue
        if marker_path.suffix != ".md" or not marker_path.is_file():
            failures.append(f"{label}.path is not a Markdown file: {relative}")
            continue

        text = marker_path.read_text(encoding="utf-8")
        if isinstance(contains, str) and contains:
            check(
                contains in text,
                f"{plugin_name}: {skill_name} missing marker {contains} in {relative}",
                failures,
            )
            continue
        try:
            pattern = re.compile(regex)
        except re.error as exc:
            failures.append(f"{label}.regex is invalid: {exc}")
            continue
        check(
            pattern.search(text) is not None,
            f"{plugin_name}: {skill_name} missing regex {regex} in {relative}",
            failures,
        )


def run(command: list[str], cwd: Path, failures: list[str], *, echo: bool = True) -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, env=environment)
    if echo and process.stdout.strip():
        print(process.stdout.rstrip())
    if process.returncode:
        detail = process.stderr.strip() or process.stdout.strip() or f"exit {process.returncode}"
        failures.append(f"command failed in {cwd.relative_to(ROOT)}: {' '.join(command)}\n{detail}")


def load_plugin_observations(
    plugin_name: str,
    config_path: Path,
    quality_config: dict[str, Any],
    failures: list[str],
) -> dict[str, dict[str, Any]]:
    manifest_value = quality_config.get("observation_manifest")
    if manifest_value is None:
        return {}
    manifest_path = resolve_config_path(
        config_path,
        manifest_value,
        f"{plugin_name} observation_manifest",
        failures,
    )
    observations, observation_failures = validate_manifest(
        manifest_path,
        boundary=config_path.parents[1],
    )
    failures.extend(observation_failures)
    return observations


def run_declared_validators(
    plugin_name: str,
    config_path: Path,
    quality_config: dict[str, Any],
    observations: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    validators = quality_config.get("validators")
    if not isinstance(validators, list) or not validators:
        failures.append(f"{plugin_name}: validators must be a non-empty array")
        return

    seen: set[str] = set()
    plugin_boundary = config_path.parents[1].resolve()
    for index, validator in enumerate(validators, 1):
        label = f"{plugin_name} validator {index}"
        if not isinstance(validator, dict):
            failures.append(f"{label} must be an object")
            continue
        name = validator.get("name")
        if not isinstance(name, str) or not name:
            failures.append(f"{label} needs a name")
            continue
        label = f"{plugin_name} validator {name}"
        if name in seen:
            failures.append(f"{label} is duplicated")
            continue
        seen.add(name)

        cwd = resolve_config_path(config_path, validator.get("cwd"), f"{label} cwd", failures)
        argv = validator.get("argv")
        echo = validator.get("echo", True)
        if not cwd.is_dir():
            failures.append(f"{label} cwd is not a directory: {cwd}")
            continue
        if (
            not isinstance(argv, list)
            or len(argv) < 2
            or any(not isinstance(value, str) or not value for value in argv)
            or argv[0] != "{python}"
        ):
            failures.append(f"{label} argv must start with {{python}} and name a script")
            continue
        if not isinstance(echo, bool):
            failures.append(f"{label} echo must be boolean")
            continue

        script_path = (cwd / argv[1]).resolve()
        try:
            script_path.relative_to(plugin_boundary)
        except ValueError:
            failures.append(f"{label} script escapes plugin directory: {argv[1]}")
            continue
        if not script_path.is_file():
            failures.append(f"{label} script is missing: {script_path}")
            continue

        command: list[str] = []
        invalid = False
        for value in argv:
            if value == "{python}":
                command.append(sys.executable)
                continue
            match = OBSERVATION_TOKEN.fullmatch(value)
            if match:
                suite = observations.get(match.group(1))
                results_path = suite.get("results_path") if isinstance(suite, dict) else None
                if not isinstance(results_path, Path):
                    failures.append(
                        f"{label} references unavailable observation suite {match.group(1)}"
                    )
                    invalid = True
                    break
                command.append(str(results_path))
                continue
            if value.startswith("{") and value.endswith("}"):
                failures.append(f"{label} has unknown token {value}")
                invalid = True
                break
            command.append(value)
        if not invalid:
            run(command, cwd, failures, echo=echo)


def validate_marketplace(failures: list[str]) -> list[str]:
    check(MARKETPLACE_PATH.is_file(), "missing .agents/plugins/marketplace.json", failures)
    if not MARKETPLACE_PATH.is_file():
        return []
    try:
        payload = load_json(MARKETPLACE_PATH)
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"invalid marketplace JSON: {exc}")
        return []
    check(payload.get("name") == "codex-plugins-kr", "unexpected marketplace name", failures)
    entries = payload.get("plugins")
    check(isinstance(entries, list), "marketplace plugins must be an array", failures)
    if not isinstance(entries, list):
        return []
    names = [entry.get("name") for entry in entries if isinstance(entry, dict)]
    check(
        all(
            isinstance(name, str) and SLUG_PATTERN.fullmatch(name) is not None
            for name in names
        ),
        "marketplace plugin names must be lowercase slugs",
        failures,
    )
    check(len(names) == len(set(names)), f"duplicate marketplace plugin names: {names}", failures)
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append("marketplace entry must be an object")
            continue
        name = entry.get("name")
        source = entry.get("source")
        policy = entry.get("policy")
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
    return [name for name in names if isinstance(name, str) and name]


def validate_skill(
    plugin_name: str,
    plugin_dir: Path,
    skill_name: str,
    skill_gate: dict[str, Any],
    failures: list[str],
) -> None:
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

    required_files = skill_gate.get("required_files", [])
    check(
        isinstance(required_files, list) and all(isinstance(value, str) and value for value in required_files),
        f"{plugin_name}: {skill_name} required_files must be a string array",
        failures,
    )
    for relative in required_files if isinstance(required_files, list) else []:
        check((skill_dir / relative).is_file(), f"{plugin_name}: {skill_name} missing {relative}", failures)

    validate_required_markers(
        plugin_name,
        skill_name,
        skill_dir,
        skill_gate.get("required_markers", []),
        failures,
    )

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


def validate_plugin(
    plugin_name: str, quality_config: dict[str, Any], failures: list[str]
) -> tuple[str, ...]:
    plugin_dir = ROOT / "plugins" / plugin_name
    manifest_path = plugin_dir / ".codex-plugin" / "plugin.json"
    check(manifest_path.is_file(), f"{plugin_name}: missing plugin.json", failures)
    if not manifest_path.is_file():
        return ()

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
    configured = quality_config.get("skills")
    configured_names = tuple(sorted(configured)) if isinstance(configured, dict) else ()
    check(discovered == configured_names, f"{plugin_name}: quality gates do not match discovered skills {discovered}", failures)
    for skill_name in discovered:
        skill_gate = configured.get(skill_name, {}) if isinstance(configured, dict) else {}
        check(isinstance(skill_gate, dict), f"{plugin_name}: invalid quality gate for {skill_name}", failures)
        validate_skill(
            plugin_name,
            plugin_dir,
            skill_name,
            skill_gate if isinstance(skill_gate, dict) else {},
            failures,
        )
    return discovered


def validate_update_scripts(plugin_names: list[str], failures: list[str]) -> None:
    marketplace = load_json(MARKETPLACE_PATH).get("name") if MARKETPLACE_PATH.is_file() else None
    for label, (path, markers) in UPDATE_SCRIPT_MARKERS.items():
        check(path.is_file(), f"missing {label} update script", failures)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        dynamic_markers = [*markers, *plugin_names]
        if isinstance(marketplace, str):
            dynamic_markers.append(marketplace)
        for marker in dynamic_markers:
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
    for path in (
        ROUTING_EVALUATOR_PATH,
        VERSION_CHECK_PATH,
        LIVE_EVAL_PATH,
        OBSERVATION_VALIDATOR_PATH,
        SOURCE_LIVENESS_PATH,
        RELEASE_ATTESTATION_PATH,
    ):
        check(path.is_file(), f"missing {path.relative_to(ROOT)}", failures)
    for script in sorted((ROOT / "scripts").rglob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            failures.append(f"invalid Python syntax in {script.relative_to(ROOT)}: {exc}")


def main() -> int:
    failures: list[str] = []
    plugin_names = validate_marketplace(failures)
    validate_repository_inventory(plugin_names, failures)
    quality_gates: dict[str, tuple[Path, dict[str, Any]]] = {}
    discovered_skills: dict[str, tuple[str, ...]] = {}
    for plugin_name in plugin_names:
        config_path, quality_config = load_quality_gates(plugin_name, failures)
        quality_gates[plugin_name] = (config_path, quality_config)
        discovered_skills[plugin_name] = validate_plugin(plugin_name, quality_config, failures)
    validate_update_scripts(plugin_names, failures)
    validate_repository_scripts(failures)

    routing_observations, observation_failures = validate_manifest(ROUTING_OBSERVATIONS_PATH)
    failures.extend(observation_failures)
    for plugin_name, (config_path, quality_config) in quality_gates.items():
        observations = load_plugin_observations(
            plugin_name,
            config_path,
            quality_config,
            failures,
        )
        run_declared_validators(
            plugin_name,
            config_path,
            quality_config,
            observations,
            failures,
        )

    python = sys.executable
    run([python, str(ROUTING_EVALUATOR_PATH), "validate"], ROOT, failures)
    routing = routing_observations.get("routing")
    if routing and isinstance(routing.get("results_path"), Path):
        run(
            [python, str(ROUTING_EVALUATOR_PATH), "score", str(routing["results_path"])],
            ROOT,
            failures,
        )
    run([python, str(VERSION_CHECK_PATH), "--help"], ROOT, failures, echo=False)
    run([python, str(LIVE_EVAL_PATH), "validate"], ROOT, failures)

    if failures:
        print("\nMONOREPO VALIDATION FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    skill_count = sum(len(skill_names) for skill_names in discovered_skills.values())
    print(f"\nMONOREPO VALIDATION PASSED: {len(plugin_names)} plugins, {skill_count} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

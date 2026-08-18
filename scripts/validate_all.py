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

from check_freshness import classify_freshness
from validate_observation_manifest import validate_manifest


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
ROUTING_EVALUATOR_PATH = ROOT / "scripts" / "eval_routing.py"
ROUTING_OBSERVATIONS_PATH = ROOT / "tests" / "observations.json"
VERSION_CHECK_PATH = ROOT / "scripts" / "check_version_bumps.py"
LIVE_EVAL_PATH = ROOT / "scripts" / "live_eval.py"
OBSERVATION_VALIDATOR_PATH = ROOT / "scripts" / "validate_observation_manifest.py"
SOURCE_LIVENESS_PATH = ROOT / "scripts" / "check_source_liveness.py"
OBSERVATION_TOKEN = re.compile(r"\{observation:([a-z0-9-]+)\}")
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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
    check(payload.get("name") == "codex-workflows-kr", "unexpected marketplace name", failures)
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

    required_markers = skill_gate.get("required_markers", [])
    check(
        isinstance(required_markers, list) and all(isinstance(value, str) and value for value in required_markers),
        f"{plugin_name}: {skill_name} required_markers must be a string array",
        failures,
    )
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
    ):
        check(path.is_file(), f"missing {path.relative_to(ROOT)}", failures)
    for script in sorted((ROOT / "scripts").rglob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            failures.append(f"invalid Python syntax in {script.relative_to(ROOT)}: {exc}")


def validate_frontend_toolkits(
    config_path: Path,
    quality_config: dict[str, Any],
    failures: list[str],
    warnings: list[str],
) -> None:
    registry_config = quality_config.get("toolkit_registry")
    if not isinstance(registry_config, dict):
        failures.append("uiux-advisor: missing toolkit_registry quality gate")
        return
    registry_path = resolve_config_path(
        config_path,
        registry_config.get("path"),
        "uiux-advisor toolkit_registry",
        failures,
    )
    check(registry_path.is_file(), "uiux-advisor: missing frontend toolkit registry", failures)
    if not registry_path.is_file():
        return

    try:
        payload = load_json(registry_path)
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"uiux-advisor: invalid frontend toolkit registry: {exc}")
        return
    if not isinstance(payload, dict):
        failures.append("uiux-advisor: frontend toolkit registry must be an object")
        return

    schema_version = payload.get("schema_version")
    expected_schema = registry_config.get("schema_version")
    check(
        isinstance(expected_schema, str) and schema_version == expected_schema,
        f"uiux-advisor: toolkit schema_version must be {expected_schema}",
        failures,
    )
    snapshot_date = payload.get("snapshot_date")
    try:
        parsed_snapshot = date.fromisoformat(snapshot_date) if isinstance(snapshot_date, str) else None
        check(
            parsed_snapshot is not None and parsed_snapshot <= date.today(),
            "uiux-advisor: invalid or future toolkit snapshot_date",
            failures,
        )
    except ValueError:
        parsed_snapshot = None
        failures.append("uiux-advisor: invalid toolkit snapshot_date")

    tools = payload.get("tools")
    check(isinstance(tools, list), "uiux-advisor: toolkit tools must be an array", failures)
    if not isinstance(tools, list):
        return
    minimum_count = registry_config.get("minimum_count")
    check(
        isinstance(minimum_count, int) and minimum_count > 0,
        "uiux-advisor: toolkit minimum_count must be a positive integer",
        failures,
    )
    if isinstance(minimum_count, int):
        check(
            len(tools) >= minimum_count,
            f"uiux-advisor: expected at least {minimum_count} toolkits, got {len(tools)}",
            failures,
        )

    allowed_kinds = {"api", "library", "registry", "specification", "workbench"}
    configured_roles = registry_config.get("required_roles")
    check(
        isinstance(configured_roles, list)
        and bool(configured_roles)
        and all(isinstance(role, str) and role for role in configured_roles),
        "uiux-advisor: toolkit required_roles must be a non-empty string array",
        failures,
    )
    allowed_roles = set(configured_roles) if isinstance(configured_roles, list) else set()
    allowed_ecosystems = {
        "web",
        "vanilla",
        "react",
        "vue",
        "svelte",
        "angular",
        "solid",
        "multi-platform",
    }
    allowed_adoption = {"native", "package", "registry", "source-copy", "specification"}
    allowed_status = {"candidate", "verified", "deprecated"}
    allowed_license_review = {"required-at-adoption", "verified", "not-applicable"}
    configured_ids = registry_config.get("required_ids")
    check(
        isinstance(configured_ids, list)
        and bool(configured_ids)
        and all(isinstance(tool_id, str) and tool_id for tool_id in configured_ids),
        "uiux-advisor: toolkit required_ids must be a non-empty string array",
        failures,
    )
    required_ids = set(configured_ids) if isinstance(configured_ids, list) else set()
    freshness = registry_config.get("freshness")
    warning_after = freshness.get("warning_after_days") if isinstance(freshness, dict) else None
    error_after = freshness.get("error_after_days") if isinstance(freshness, dict) else None
    valid_freshness = (
        isinstance(warning_after, int)
        and isinstance(error_after, int)
        and 0 <= warning_after < error_after
    )
    check(valid_freshness, "uiux-advisor: invalid toolkit freshness budget", failures)

    ids: list[str] = []
    names: list[str] = []
    official_urls: list[str] = []
    covered_roles: set[str] = set()
    for index, tool in enumerate(tools, 1):
        if not isinstance(tool, dict):
            failures.append(f"uiux-advisor: toolkit {index} must be an object")
            continue
        label = tool.get("id") or f"toolkit-{index}"
        tool_id = tool.get("id")
        name = tool.get("name")
        check(
            isinstance(tool_id, str) and SLUG_PATTERN.fullmatch(tool_id) is not None,
            f"uiux-advisor: {label} has invalid id",
            failures,
        )
        check(isinstance(name, str) and bool(name.strip()), f"uiux-advisor: {label} missing name", failures)
        if isinstance(tool_id, str):
            ids.append(tool_id)
        if isinstance(name, str):
            names.append(name)

        check(tool.get("kind") in allowed_kinds, f"uiux-advisor: {label} has invalid kind", failures)
        check(tool.get("adoption") in allowed_adoption, f"uiux-advisor: {label} has invalid adoption", failures)
        check(tool.get("status") in allowed_status, f"uiux-advisor: {label} has invalid status", failures)
        check(
            tool.get("license_review") in allowed_license_review,
            f"uiux-advisor: {label} has invalid license_review",
            failures,
        )
        roles = tool.get("roles")
        valid_roles = (
            isinstance(roles, list)
            and bool(roles)
            and all(isinstance(role, str) and bool(role) for role in roles)
        )
        check(valid_roles, f"uiux-advisor: {label} has invalid roles", failures)
        if valid_roles:
            check(len(roles) == len(set(roles)), f"uiux-advisor: {label} has duplicate roles", failures)
            check(set(roles) <= allowed_roles, f"uiux-advisor: {label} has unknown roles", failures)
            covered_roles.update(roles)
        ecosystems = tool.get("ecosystems")
        valid_ecosystems = (
            isinstance(ecosystems, list)
            and bool(ecosystems)
            and all(isinstance(ecosystem, str) and bool(ecosystem) for ecosystem in ecosystems)
        )
        check(valid_ecosystems, f"uiux-advisor: {label} has invalid ecosystems", failures)
        if valid_ecosystems:
            check(
                len(ecosystems) == len(set(ecosystems)),
                f"uiux-advisor: {label} has duplicate ecosystems",
                failures,
            )
            check(
                set(ecosystems) <= allowed_ecosystems,
                f"uiux-advisor: {label} has unknown ecosystems",
                failures,
            )
        for field in ("capabilities", "surfaces"):
            values = tool.get(field)
            valid_values = (
                isinstance(values, list)
                and bool(values)
                and all(
                    isinstance(value, str) and SLUG_PATTERN.fullmatch(value) is not None
                    for value in values
                )
            )
            check(valid_values, f"uiux-advisor: {label} has invalid {field}", failures)
            if valid_values:
                check(
                    len(values) == len(set(values)),
                    f"uiux-advisor: {label} has duplicate {field}",
                    failures,
                )
        check(tool.get("risk") in {"low", "medium", "high"}, f"uiux-advisor: {label} has invalid risk", failures)
        check(
            isinstance(tool.get("fallback"), str) and bool(tool["fallback"].strip()),
            f"uiux-advisor: {label} missing fallback",
            failures,
        )
        official_url = tool.get("official_url")
        check(
            isinstance(official_url, str) and official_url.startswith("https://"),
            f"uiux-advisor: {label} has invalid official_url",
            failures,
        )
        if isinstance(official_url, str):
            official_urls.append(official_url)
        checked_on = tool.get("checked_on")
        try:
            parsed_checked = date.fromisoformat(checked_on) if isinstance(checked_on, str) else None
            check(
                parsed_checked is not None
                and parsed_checked <= date.today()
                and (parsed_snapshot is None or parsed_checked <= parsed_snapshot),
                f"uiux-advisor: {label} has invalid checked_on",
                failures,
            )
            if parsed_checked is not None and valid_freshness:
                status, age = classify_freshness(
                    parsed_checked,
                    warning_after_days=warning_after,
                    error_after_days=error_after,
                )
                if status == "error":
                    failures.append(
                        f"uiux-advisor: {label} toolkit freshness exceeded: {age} days"
                    )
                elif status == "warning":
                    warnings.append(
                        f"uiux-advisor: {label} toolkit should be refreshed: {age} days"
                    )
        except ValueError:
            failures.append(f"uiux-advisor: {label} has invalid checked_on")
        check(
            isinstance(tool.get("selection_note"), str) and bool(tool["selection_note"].strip()),
            f"uiux-advisor: {label} missing selection_note",
            failures,
        )
        if tool.get("license_review") == "verified":
            check(bool(tool.get("license_spdx")), f"uiux-advisor: {label} missing license_spdx", failures)
            check(
                isinstance(tool.get("license_url"), str) and tool["license_url"].startswith("https://"),
                f"uiux-advisor: {label} missing license_url",
                failures,
            )

    check(len(ids) == len(set(ids)), "uiux-advisor: duplicate toolkit IDs", failures)
    check(len(names) == len(set(names)), "uiux-advisor: duplicate toolkit names", failures)
    check(
        len(official_urls) == len(set(official_urls)),
        "uiux-advisor: duplicate toolkit official URLs",
        failures,
    )
    check(required_ids <= set(ids), f"uiux-advisor: missing required toolkits {sorted(required_ids - set(ids))}", failures)
    check(allowed_roles <= covered_roles, f"uiux-advisor: uncovered toolkit roles {sorted(allowed_roles - covered_roles)}", failures)


def validate_uiux_kb(
    config_path: Path,
    quality_config: dict[str, Any],
    failures: list[str],
    warnings: list[str],
) -> None:
    kb_config = quality_config.get("knowledge_base")
    if not isinstance(kb_config, dict):
        failures.append("uiux-advisor: missing knowledge_base quality gate")
        return
    kb_dir = resolve_config_path(
        config_path,
        kb_config.get("path"),
        "uiux-advisor knowledge_base",
        failures,
    )
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
    expected_count = kb_config.get("expected_guide_count")
    check(
        isinstance(expected_count, int) and expected_count > 0,
        "uiux-advisor: expected_guide_count must be a positive integer",
        failures,
    )
    if isinstance(expected_count, int):
        check(
            len(records) == expected_count,
            f"uiux-advisor: expected {expected_count} records, got {len(records)}",
            failures,
        )
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
    freshness = kb_config.get("freshness")
    time_warning = (
        freshness.get("time_sensitive_warning_after_days") if isinstance(freshness, dict) else None
    )
    time_error = (
        freshness.get("time_sensitive_error_after_days") if isinstance(freshness, dict) else None
    )
    stable_warning = (
        freshness.get("stable_warning_after_days") if isinstance(freshness, dict) else None
    )
    stable_error = (
        freshness.get("stable_error_after_days") if isinstance(freshness, dict) else None
    )
    valid_freshness = all(
        isinstance(value, int)
        for value in (time_warning, time_error, stable_warning, stable_error)
    ) and 0 <= time_warning < time_error and 0 <= stable_warning < stable_error
    check(valid_freshness, "uiux-advisor: invalid knowledge-base freshness budget", failures)

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
            if parsed_snapshot is not None and valid_freshness:
                if record.get("time_sensitive") is True:
                    warning_after, error_after = time_warning, time_error
                else:
                    warning_after, error_after = stable_warning, stable_error
                status, age = classify_freshness(
                    parsed_snapshot,
                    warning_after_days=warning_after,
                    error_after_days=error_after,
                )
                if status == "error":
                    failures.append(
                        f"uiux-advisor: {label} guide freshness exceeded: {age} days"
                    )
                elif status == "warning":
                    warnings.append(
                        f"uiux-advisor: {label} guide should be refreshed: {age} days"
                    )
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
    if isinstance(expected_count, int):
        check(
            len(list((kb_dir / "guides").rglob("*.md"))) == expected_count,
            "uiux-advisor: guide file count mismatch",
            failures,
        )

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
    warnings: list[str] = []
    plugin_names = validate_marketplace(failures)
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
        if "knowledge_base" in quality_config:
            validate_uiux_kb(config_path, quality_config, failures, warnings)
        if "toolkit_registry" in quality_config:
            validate_frontend_toolkits(config_path, quality_config, failures, warnings)
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

    if warnings:
        print("\nMONOREPO VALIDATION WARNINGS")
        for warning in warnings:
            print(f"- {warning}")

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

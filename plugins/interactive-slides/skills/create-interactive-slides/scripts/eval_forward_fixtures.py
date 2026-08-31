#!/usr/bin/env python3
"""Evaluate realistic demo and experience fixtures against the canonical starter."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVAL_ROOT = SKILL_ROOT / "evals" / "forward"
DEFAULT_MANIFEST = DEFAULT_EVAL_ROOT / "cases.json"
DEFAULT_STARTER = SKILL_ROOT / "assets" / "starter"
DECK_VALIDATOR_PATH = Path(__file__).with_name("validate_deck_project.py")

CASE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DEFAULT_MODE = re.compile(r"\bdefaultMode\s*:\s*[\"'](demo|experience)[\"']")
MODE_LOCK = re.compile(r"\bmodeLocked\s*:\s*true\b")
SCENE_TYPE = re.compile(r"\btype\s*:\s*[\"']([a-z]+(?:-[a-z]+)*)[\"']")
SLIDE_FIELD_PATTERNS = {
    "title": re.compile(r"\btitle\s*:\s*[\"'][^\"']+[\"']"),
    "summary": re.compile(r"\bsummary\s*:\s*[\"'][^\"']+[\"']"),
    "evidence": re.compile(r"\bevidence\s*:\s*\{"),
    "fallback": re.compile(r"\bfallback\s*:\s*[\"'][^\"']+[\"']"),
    "notes": re.compile(r"\bnotes\s*:\s*\[\s*[\"']"),
    "sources": re.compile(r"\bsources\s*:\s*\[\s*[\"']"),
}
CANONICAL_LIFECYCLES = {
    "demo": "ready-running-complete",
    "experience": "direct-manipulation-reset",
}
DEMO_BLOCKING_SCENES = {"sequence", "timeline", "code-walkthrough"}
EXPERIENCE_DIRECT_SCENES = {"choice", "range", "diagram", "before-after"}
MODE_LOCK_RUNTIME_MARKERS = (
    "deck.meta.modeLocked === true",
    "!modeLocked &&",
    "if (modeLocked) return",
    "elements.mode.hidden = true",
)
SCENE_RECIPE_FIELDS = {
    "steps": (("items", re.compile(r"\bitems\s*:\s*\[")),),
    "comparison": (
        ("left", re.compile(r"\bleft\s*:\s*\{")),
        ("right", re.compile(r"\bright\s*:\s*\{")),
    ),
    "choice": (("options", re.compile(r"\boptions\s*:\s*\[")),),
    "range": (
        ("min", re.compile(r"\bmin\s*:\s*-?\d")),
        ("max", re.compile(r"\bmax\s*:\s*-?\d")),
        ("step", re.compile(r"\bstep\s*:\s*-?\d")),
        ("value", re.compile(r"\bvalue\s*:\s*-?\d")),
        ("result", re.compile(r"\bresult\s*:\s*\{")),
    ),
    "sequence": (
        ("nodes", re.compile(r"\bnodes\s*:\s*\[")),
        ("phases", re.compile(r"\bphases\s*:\s*\[")),
    ),
    "timeline": (("events", re.compile(r"\bevents\s*:\s*\[")),),
    "diagram": (
        ("nodes", re.compile(r"\bnodes\s*:\s*\[")),
        ("links", re.compile(r"\blinks\s*:\s*\[")),
    ),
    "code-walkthrough": (("lines", re.compile(r"\blines\s*:\s*\[")),),
    "before-after": (
        ("before", re.compile(r"\bbefore\s*:\s*\{")),
        ("after", re.compile(r"\bafter\s*:\s*\{")),
    ),
}


def _load_deck_validator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "interactive_slides_deck_validator",
        DECK_VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Interactive Slides deck validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DECK_VALIDATOR = _load_deck_validator()


def _extract_object_property(source: str, property_name: str) -> str | None:
    match = re.search(rf"\b{re.escape(property_name)}\s*:\s*\{{", source)
    if match is None:
        return None
    start = source.find("{", match.start())
    depth = 0
    quote = ""
    escaped = False
    for index in range(start, len(source)):
        character = source[index]
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = ""
            continue
        if character in {'"', "'", "`"}:
            quote = character
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    return None


def _safe_fixture_path(eval_root: Path, value: Any) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, "fixture must be a non-empty relative path"
    root = eval_root.resolve()
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None, f"fixture escapes evaluation root: {value}"
    if not path.is_file():
        return None, f"fixture does not exist: {value}"
    return path, None


def _invalid_case(case_id: str, failures: list[str]) -> dict[str, Any]:
    return {
        "id": case_id,
        "status": "failed",
        "mode": None,
        "metrics": {"slides": 0, "scene_types": []},
        "warnings": [],
        "failures": failures,
    }


def evaluate_case(
    case: Any,
    *,
    eval_root: Path = DEFAULT_EVAL_ROOT,
    starter: Path = DEFAULT_STARTER,
) -> dict[str, Any]:
    if not isinstance(case, dict):
        return _invalid_case("unknown-case", ["case must be an object"])

    raw_id = case.get("id")
    case_id = raw_id if isinstance(raw_id, str) and raw_id else "unknown-case"
    failures: list[str] = []
    warnings: list[str] = []

    if not isinstance(raw_id, str) or CASE_ID.fullmatch(raw_id) is None:
        failures.append("id must be lower-kebab-case")

    prompt = case.get("prompt")
    if not isinstance(prompt, str) or len(prompt.strip()) < 40:
        failures.append("prompt must be a realistic request of at least 40 characters")

    mode = case.get("mode")
    if not isinstance(mode, str) or mode not in CANONICAL_LIFECYCLES:
        failures.append(f"unsupported mode: {mode}")

    expected = case.get("expected")
    if not isinstance(expected, dict):
        failures.append("expected must be an object")
        expected = {}

    fixture_path, fixture_error = _safe_fixture_path(eval_root, case.get("fixture"))
    if fixture_error:
        failures.append(fixture_error)

    expected_count = expected.get("slide_count")
    if not isinstance(expected_count, int) or not 3 <= expected_count <= 5:
        failures.append("expected.slide_count must be between 3 and 5")

    approved_ids = expected.get("approved_slide_ids")
    valid_approved_ids = (
        isinstance(approved_ids, list)
        and bool(approved_ids)
        and all(isinstance(item, str) and CASE_ID.fullmatch(item) for item in approved_ids)
        and len(approved_ids) == len(set(approved_ids))
    )
    if not valid_approved_ids:
        failures.append("expected.approved_slide_ids must be unique lower-kebab-case values")

    expected_scene_types = expected.get("scene_types")
    valid_scene_types = (
        isinstance(expected_scene_types, list)
        and bool(expected_scene_types)
        and all(isinstance(item, str) and CASE_ID.fullmatch(item) for item in expected_scene_types)
        and len(expected_scene_types) == len(set(expected_scene_types))
    )
    if not valid_scene_types:
        failures.append("expected.scene_types must be unique lower-kebab-case values")

    expected_lifecycle = expected.get("mode_lifecycle")
    if isinstance(mode, str) and mode in CANONICAL_LIFECYCLES and expected_lifecycle != CANONICAL_LIFECYCLES[mode]:
        failures.append(
            f"expected.mode_lifecycle must be {CANONICAL_LIFECYCLES[mode]} for {mode}"
        )

    if not starter.is_dir():
        failures.append(f"canonical starter does not exist: {starter}")

    if failures or fixture_path is None:
        result = _invalid_case(case_id, failures)
        result["mode"] = mode if isinstance(mode, str) else None
        return result

    with tempfile.TemporaryDirectory(prefix=f"interactive-slides-{case_id}-") as raw_temp:
        project = Path(raw_temp) / "project"
        shutil.copytree(starter, project)
        shutil.copy2(fixture_path, project / "deck.js")
        deck_failures, deck_warnings, deck_metrics = DECK_VALIDATOR.validate(
            project,
            allow_remote_assets=False,
        )
        failures.extend(f"deck validator: {failure}" for failure in deck_failures)
        warnings.extend(deck_warnings)

        deck = (project / "deck.js").read_text(encoding="utf-8")
        runtime = (project / "presentation.js").read_text(encoding="utf-8")
        slide_blocks = DECK_VALIDATOR.extract_slide_blocks(deck)
        slide_ids: list[str] = []
        for block in slide_blocks:
            match = DECK_VALIDATOR.SLIDE_ID.search(block)
            if match is not None:
                slide_ids.append(match.group(1))
        scene_types: list[str] = []
        for slide_index, block in enumerate(slide_blocks, 1):
            scene = _extract_object_property(block, "scene")
            if scene is None:
                continue
            scene_match = SCENE_TYPE.search(scene)
            if scene_match is None:
                failures.append(f"slide {slide_index} scene missing type")
                continue
            scene_type = scene_match.group(1)
            scene_types.append(scene_type)
            recipe_fields = SCENE_RECIPE_FIELDS.get(scene_type)
            if recipe_fields is None:
                failures.append(f"slide {slide_index} uses unsupported scene recipe: {scene_type}")
                continue
            for field, pattern in recipe_fields:
                if pattern.search(scene) is None:
                    failures.append(
                        f"slide {slide_index} scene {scene_type} missing recipe field: {field}"
                    )

        mode_match = DEFAULT_MODE.search(deck)
        actual_mode = mode_match.group(1) if mode_match else None
        if actual_mode != mode:
            failures.append(f"fixture defaultMode {actual_mode!r} does not match case mode {mode!r}")
        if MODE_LOCK.search(deck) is None:
            failures.append("fixture must lock its selected delivery mode with modeLocked: true")
        missing_runtime_markers = [
            marker for marker in MODE_LOCK_RUNTIME_MARKERS if marker not in runtime
        ]
        if missing_runtime_markers:
            failures.append(
                "canonical runtime does not enforce modeLocked: "
                + ", ".join(missing_runtime_markers)
            )

        if not 3 <= len(slide_blocks) <= 5:
            failures.append(f"fixture must contain 3 to 5 slides, got {len(slide_blocks)}")
        if len(slide_blocks) != expected_count:
            failures.append(
                f"fixture slide count {len(slide_blocks)} does not match expected {expected_count}"
            )
        if slide_ids != approved_ids:
            failures.append(
                "fixture slide IDs do not exactly match approved scope: "
                f"actual={slide_ids}, approved={approved_ids}"
            )
        if scene_types != expected_scene_types:
            failures.append(
                "fixture scene types do not match expected composition: "
                f"actual={scene_types}, expected={expected_scene_types}"
            )

        for slide_index, block in enumerate(slide_blocks, 1):
            for field, pattern in SLIDE_FIELD_PATTERNS.items():
                if pattern.search(block) is None:
                    failures.append(f"slide {slide_index} missing non-empty {field}")

        scene_set = set(scene_types)
        if mode == "demo" and not scene_set.intersection(DEMO_BLOCKING_SCENES):
            failures.append("demo fixture needs at least one blocking scene")
        if mode == "experience" and not scene_set.intersection(EXPERIENCE_DIRECT_SCENES):
            failures.append("experience fixture needs at least one direct-manipulation scene")

    return {
        "id": case_id,
        "status": "failed" if failures else "passed",
        "mode": mode,
        "metrics": {
            "slides": len(slide_blocks),
            "scene_types": scene_types,
            "remote_urls": deck_metrics.get("remote_urls", 0),
        },
        "warnings": warnings,
        "failures": failures,
    }


def evaluate_manifest(
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    starter: Path = DEFAULT_STARTER,
) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    manifest_failures: list[str] = []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "failed",
            "manifest": str(manifest_path),
            "summary": {"cases": 0, "passed": 0, "failed": 0, "slides": 0},
            "manifest_failures": [f"could not load manifest: {exc}"],
            "results": [],
        }

    if not isinstance(payload, dict):
        payload = {}
        manifest_failures.append("manifest must be an object")
    if payload.get("schema_version") != 1:
        manifest_failures.append("schema_version must be 1")
    if payload.get("evaluation_kind") != "assembled-static-forward":
        manifest_failures.append("evaluation_kind must be assembled-static-forward")

    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        cases = []
        manifest_failures.append("cases must be a non-empty array")

    ids = [case.get("id") for case in cases if isinstance(case, dict)]
    if not all(isinstance(case_id, str) for case_id in ids):
        manifest_failures.append("case IDs must be strings")
    elif len(ids) != len(set(ids)):
        manifest_failures.append("case IDs must be unique")

    modes = [case.get("mode") for case in cases if isinstance(case, dict)]
    valid_mode_types = all(isinstance(mode, str) for mode in modes)
    if not valid_mode_types or sorted(modes) != ["demo", "experience"]:
        manifest_failures.append("manifest must contain exactly one demo and one experience case")

    eval_root = manifest_path.parent
    results = [evaluate_case(case, eval_root=eval_root, starter=starter) for case in cases]
    passed = sum(result["status"] == "passed" for result in results)
    failed = len(results) - passed
    slides = sum(result["metrics"]["slides"] for result in results)
    return {
        "status": "failed" if manifest_failures or failed else "passed",
        "manifest": str(manifest_path),
        "summary": {
            "cases": len(results),
            "passed": passed,
            "failed": failed,
            "slides": slides,
        },
        "manifest_failures": manifest_failures,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--starter", type=Path, default=DEFAULT_STARTER)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = evaluate_manifest(args.manifest, starter=args.starter)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        summary = result["summary"]
        print(
            f"FORWARD FIXTURE EVAL {result['status'].upper()}: "
            f"{summary['passed']}/{summary['cases']} cases, {summary['slides']} slides"
        )
        for failure in result["manifest_failures"]:
            print(f"ERROR: manifest: {failure}")
        for case in result["results"]:
            metrics = case["metrics"]
            print(
                f"- {case['id']}: {case['status']} "
                f"({case['mode']}, {metrics['slides']} slides, "
                f"scenes={','.join(metrics['scene_types'])})"
            )
            for warning in case["warnings"]:
                print(f"  WARNING: {warning}")
            for failure in case["failures"]:
                print(f"  ERROR: {failure}")
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate a design plan against its approved production proposal."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType


PROPOSAL_VALIDATOR_PATH = Path(__file__).with_name("validate_production_proposal.py")
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "plan_status",
    "proposal",
    "art_direction",
    "presentation_chrome",
    "slide_families",
    "slide_count",
    "slides",
}
ALLOWED_PLAN_STATUSES = {"draft", "ready"}
ALLOWED_MODES = {"demo", "experience", "hybrid"}
ALLOWED_DENSITIES = {"low", "medium", "high"}
ALLOWED_SCENE_TYPES = {
    "static",
    "steps",
    "comparison",
    "choice",
    "range",
    "sequence",
    "timeline",
    "diagram",
    "code-walkthrough",
    "before-after",
}
ALLOWED_BENEFITS = {"causality", "temporal", "decision", "comparison", "spatial"}
ALLOWED_LIFECYCLES = {"none", "ready-running-complete", "direct-manipulation-reset"}
ALLOWED_EVIDENCE_BOUNDARIES = {
    "verified",
    "inferred",
    "analysis",
    "simulation",
    "not-applicable",
}
FAMILY_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLIDE_ID = re.compile(r"^S\d{2,}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load_proposal_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "interactive_slides_proposal_validator_for_design_plan",
        PROPOSAL_VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load production proposal validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_object(value: object, label: str, errors: list[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return {}
    return value


def require_list(value: object, label: str, errors: list[str]) -> list[object]:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return []
    return value


def require_text(value: object, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return ""
    return value.strip()


def require_positive_int(value: object, label: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{label} must be an integer")
        return None
    if value < 1:
        errors.append(f"{label} must be at least 1")
    return value


def validate_string_array(value: object, label: str, errors: list[str]) -> list[str]:
    items = require_list(value, label, errors)
    strings: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{label}[{index}] must be a non-empty string")
            continue
        strings.append(item.strip())
    return strings


def validate(plan_path: Path, proposal_path: Path, require_ready: bool) -> dict[str, object]:
    errors: list[str] = []
    try:
        data = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {
            "valid": False,
            "path": str(plan_path),
            "proposal_path": str(proposal_path),
            "require_ready": require_ready,
            "errors": [f"design plan JSON could not be read: {error}"],
        }

    root = require_object(data, "design plan", errors)
    missing = sorted(REQUIRED_TOP_LEVEL - root.keys())
    errors.extend(f"missing top-level field: {field}" for field in missing)

    schema_version = require_positive_int(root.get("schema_version"), "schema_version", errors)
    if schema_version is not None and schema_version != 1:
        errors.append(f"unsupported schema_version: {schema_version}")

    plan_status = root.get("plan_status")
    if plan_status not in ALLOWED_PLAN_STATUSES:
        errors.append(f"unsupported plan_status: {plan_status}")
    if require_ready and plan_status != "ready":
        errors.append("production gate requires plan_status: ready")

    proposal_validator = load_proposal_validator()
    proposal_result = proposal_validator.validate(proposal_path, require_approved=True)
    errors.extend(f"proposal: {error}" for error in proposal_result["errors"])

    binding = require_object(root.get("proposal"), "proposal", errors)
    binding_version = require_positive_int(binding.get("version"), "proposal.version", errors)
    expected_version = proposal_result.get("proposal_version")
    if binding_version is not None and str(binding_version) != str(expected_version):
        errors.append(
            f"proposal.version {binding_version} does not match approved proposal {expected_version}"
        )
    binding_title = require_text(binding.get("title"), "proposal.title", errors)
    if binding_title and binding_title != proposal_result.get("title"):
        errors.append("proposal.title does not match approved proposal")
    binding_mode = binding.get("mode")
    if binding_mode not in ALLOWED_MODES:
        errors.append(f"unsupported proposal.mode: {binding_mode}")
    if binding_mode and binding_mode != proposal_result.get("presentation_mode"):
        errors.append("proposal.mode does not match approved proposal")

    actual_sha = hashlib.sha256(proposal_path.read_bytes()).hexdigest()
    binding_sha = binding.get("sha256")
    if not isinstance(binding_sha, str) or not SHA256.fullmatch(binding_sha):
        errors.append("proposal.sha256 must be a lowercase SHA-256 digest")
    elif binding_sha != actual_sha:
        errors.append("proposal.sha256 does not match approved proposal content")

    art = require_object(root.get("art_direction"), "art_direction", errors)
    for field in (
        "editorial_premise",
        "image_treatment",
        "geometry",
        "motion_language",
        "icon_family",
    ):
        require_text(art.get(field), f"art_direction.{field}", errors)
    typography = require_object(art.get("typography"), "art_direction.typography", errors)
    for field in ("display", "body", "numerals"):
        require_text(typography.get(field), f"art_direction.typography.{field}", errors)
    palette = require_object(art.get("palette"), "art_direction.palette", errors)
    for field in ("background", "foreground", "accent"):
        require_text(palette.get(field), f"art_direction.palette.{field}", errors)

    chrome = require_object(root.get("presentation_chrome"), "presentation_chrome", errors)
    for field in ("icon_only", "accessible_names", "tooltips"):
        if chrome.get(field) is not True:
            errors.append(f"presentation_chrome.{field} must be true")

    families = require_list(root.get("slide_families"), "slide_families", errors)
    if not families:
        errors.append("slide_families must contain at least one family")
    family_ids: list[str] = []
    for index, raw_family in enumerate(families):
        family = require_object(raw_family, f"slide_families[{index}]", errors)
        family_id = require_text(family.get("id"), f"slide_families[{index}].id", errors)
        if family_id and not FAMILY_ID.fullmatch(family_id):
            errors.append(f"invalid slide family ID: {family_id}")
        family_ids.append(family_id)
        for field in ("purpose", "composition", "visual_anchor"):
            require_text(family.get(field), f"slide_families[{index}].{field}", errors)
        density = family.get("density")
        if density not in ALLOWED_DENSITIES:
            errors.append(f"unsupported slide_families[{index}].density: {density}")
    duplicate_families = sorted({item for item in family_ids if family_ids.count(item) > 1})
    errors.extend(f"duplicate slide family ID: {item}" for item in duplicate_families if item)

    slides = require_list(root.get("slides"), "slides", errors)
    if not slides:
        errors.append("slides must contain at least one approved slide")
    slide_count = require_positive_int(root.get("slide_count"), "slide_count", errors)
    if slide_count is not None and slide_count != len(slides):
        errors.append(f"slide_count is {slide_count}, but {len(slides)} slides were found")

    slide_ids: list[str] = []
    for index, raw_slide in enumerate(slides):
        prefix = f"slides[{index}]"
        slide = require_object(raw_slide, prefix, errors)
        slide_id = require_text(slide.get("id"), f"{prefix}.id", errors)
        if slide_id and not SLIDE_ID.fullmatch(slide_id):
            errors.append(f"invalid slide ID: {slide_id}")
        slide_ids.append(slide_id)

        family_id = require_text(slide.get("family"), f"{prefix}.family", errors)
        if family_id and family_id not in family_ids:
            errors.append(f"{prefix}.family references unknown family: {family_id}")
        require_text(slide.get("purpose"), f"{prefix}.purpose", errors)
        working_headline = require_text(
            slide.get("working_headline"), f"{prefix}.working_headline", errors
        )
        for field in ("dominant_visual", "composition"):
            require_text(slide.get(field), f"{prefix}.{field}", errors)
        require_positive_int(slide.get("speaker_seconds"), f"{prefix}.speaker_seconds", errors)

        budget = require_object(slide.get("content_budget"), f"{prefix}.content_budget", errors)
        headline_max_chars = require_positive_int(
            budget.get("headline_max_chars"),
            f"{prefix}.content_budget.headline_max_chars",
            errors,
        )
        if (
            working_headline
            and headline_max_chars is not None
            and len(working_headline) > headline_max_chars
        ):
            errors.append(
                f"{prefix}.working_headline exceeds headline_max_chars "
                f"({len(working_headline)} > {headline_max_chars})"
            )
        require_positive_int(
            budget.get("body_max_lines"),
            f"{prefix}.content_budget.body_max_lines",
            errors,
        )

        boundary = slide.get("evidence_boundary")
        if boundary not in ALLOWED_EVIDENCE_BOUNDARIES:
            errors.append(f"unsupported {prefix}.evidence_boundary: {boundary}")
        validate_string_array(slide.get("asset_ids"), f"{prefix}.asset_ids", errors)
        validate_string_array(slide.get("source_ids"), f"{prefix}.source_ids", errors)

        accessibility = require_object(slide.get("accessibility"), f"{prefix}.accessibility", errors)
        for field in ("keyboard", "reduced_motion", "static_fallback"):
            require_text(accessibility.get(field), f"{prefix}.accessibility.{field}", errors)

        interaction = require_object(slide.get("interaction"), f"{prefix}.interaction", errors)
        decision = interaction.get("decision")
        if decision not in {"adopt", "reject"}:
            errors.append(f"unsupported {prefix}.interaction.decision: {decision}")
        scene_type = interaction.get("scene_type")
        if scene_type not in ALLOWED_SCENE_TYPES:
            errors.append(f"unsupported {prefix}.interaction.scene_type: {scene_type}")
        benefits = validate_string_array(
            interaction.get("benefits"), f"{prefix}.interaction.benefits", errors
        )
        unknown_benefits = sorted(set(benefits) - ALLOWED_BENEFITS)
        errors.extend(
            f"unsupported {prefix}.interaction benefit: {benefit}"
            for benefit in unknown_benefits
        )
        if len(benefits) != len(set(benefits)):
            errors.append(f"{prefix}.interaction.benefits must be unique")
        require_text(interaction.get("reason"), f"{prefix}.interaction.reason", errors)
        lifecycle = interaction.get("lifecycle")
        if lifecycle not in ALLOWED_LIFECYCLES:
            errors.append(f"unsupported {prefix}.interaction.lifecycle: {lifecycle}")
        require_text(interaction.get("fallback"), f"{prefix}.interaction.fallback", errors)

        if decision == "adopt":
            if scene_type == "static":
                errors.append(f"{prefix}.interaction adopted scene must not be static")
            if len(set(benefits)) < 2:
                errors.append(f"{prefix}.interaction adoption requires at least two benefits")
            expected_lifecycle = {
                "demo": "ready-running-complete",
                "experience": "direct-manipulation-reset",
            }.get(binding_mode)
            if expected_lifecycle and lifecycle != expected_lifecycle:
                errors.append(
                    f"{prefix}.interaction lifecycle must be {expected_lifecycle} in {binding_mode} mode"
                )
            if binding_mode == "hybrid" and lifecycle == "none":
                errors.append(f"{prefix}.interaction adopted hybrid scene requires a lifecycle")
        if decision == "reject":
            if scene_type != "static":
                errors.append(f"{prefix}.interaction rejected scene must use static")
            if lifecycle != "none":
                errors.append(f"{prefix}.interaction rejected scene must use lifecycle none")

    duplicate_slides = sorted({item for item in slide_ids if slide_ids.count(item) > 1})
    errors.extend(f"duplicate design-plan slide ID: {item}" for item in duplicate_slides if item)

    approved_ids = [
        entry["id"]
        for entry in proposal_result.get("slide_entries", [])
        if entry["status"] == "approved"
    ]
    missing_slides = sorted(set(approved_ids) - set(slide_ids))
    extra_slides = sorted(set(slide_ids) - set(approved_ids))
    errors.extend(f"approved proposal slide missing from design plan: {item}" for item in missing_slides)
    errors.extend(f"design-plan slide is not approved in proposal: {item}" for item in extra_slides if item)
    if not approved_ids:
        errors.append("approved proposal must contain at least one approved slide row")

    return {
        "valid": not errors,
        "path": str(plan_path),
        "proposal_path": str(proposal_path),
        "plan_status": plan_status,
        "proposal_sha256": actual_sha,
        "slide_count": len(slides),
        "approved_slide_ids": approved_ids,
        "design_plan_slide_ids": slide_ids,
        "require_ready": require_ready,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design_plan", type=Path)
    parser.add_argument("--proposal", required=True, type=Path)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    if not args.design_plan.is_file():
        print(f"design plan not found: {args.design_plan}", file=sys.stderr)
        return 2
    if not args.proposal.is_file():
        print(f"proposal not found: {args.proposal}", file=sys.stderr)
        return 2

    result = validate(args.design_plan, args.proposal, args.require_ready)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["valid"]:
        print(
            "DESIGN PLAN VALID: "
            f"{result['plan_status']} · {result['slide_count']} approved slides"
        )
    else:
        print("DESIGN PLAN INVALID", file=sys.stderr)
        for error in result["errors"]:
            print(f"- {error}", file=sys.stderr)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

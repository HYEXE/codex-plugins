from __future__ import annotations

import importlib.util
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "interactive-slides" / "skills" / "create-interactive-slides"
VALIDATOR_PATH = SKILL / "scripts" / "validate_production_proposal.py"
DESIGN_VALIDATOR_PATH = SKILL / "scripts" / "validate_design_plan.py"
DECK_VALIDATOR_PATH = SKILL / "scripts" / "validate_deck_project.py"
STARTER_PATH = SKILL / "assets" / "starter"
TEMPLATE_PATH = SKILL / "templates" / "production-proposal.md"
DESIGN_TEMPLATE_PATH = SKILL / "templates" / "design-plan.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("interactive_slides_proposal_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Interactive Slides proposal validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_deck_validator():
    spec = importlib.util.spec_from_file_location("interactive_slides_deck_validator", DECK_VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Interactive Slides deck validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_design_validator():
    spec = importlib.util.spec_from_file_location(
        "interactive_slides_design_plan_validator", DESIGN_VALIDATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Interactive Slides design-plan validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def approved_proposal(slide_status: str) -> str:
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "proposal_status: draft": "proposal_status: approved",
        'title: ""': 'title: "검증용 발표"',
        "estimated_slides: 0": "estimated_slides: 1",
        "estimated_duration_minutes: 0": "estimated_duration_minutes: 1",
        "total_effort_points: 0": "total_effort_points: 1",
        'approved_by: ""': 'approved_by: "reviewer"',
        'approved_at: ""': 'approved_at: "2026-08-27T00:00:00+09:00"',
        "| S01 | review |": f"| S01 | {slide_status} |",
    }
    for source, destination in replacements.items():
        text = text.replace(source, destination, 1)
    return text


def ready_design_plan(proposal_path: Path) -> dict[str, object]:
    plan = json.loads(DESIGN_TEMPLATE_PATH.read_text(encoding="utf-8"))
    plan["plan_status"] = "ready"
    plan["proposal"] = {
        "version": 1,
        "title": "검증용 발표",
        "mode": "demo",
        "sha256": hashlib.sha256(proposal_path.read_bytes()).hexdigest(),
    }
    plan["art_direction"] = {
        "editorial_premise": "정확한 구조를 차분하게 시연하는 기술 발표",
        "typography": {
            "display": "Display Sans",
            "body": "Reading Sans",
            "numerals": "Tabular Sans",
        },
        "palette": {
            "background": "#f6f2e8",
            "foreground": "#18201c",
            "accent": "#d95f35",
        },
        "image_treatment": "고대비 크롭과 짧은 출처 캡션",
        "geometry": "12열 그리드와 직선형 구분선",
        "motion_language": "짧은 방향 전환과 단일 강조",
        "icon_family": "2px outline SVG",
    }
    plan["slide_families"] = [
        {
            "id": "cover",
            "purpose": "핵심 주장 제시",
            "composition": "비대칭 제목과 단일 시각 앵커",
            "visual_anchor": "큰 제목",
            "density": "low",
        }
    ]
    plan["slides"] = [
        {
            "id": "S01",
            "family": "cover",
            "purpose": "발표 핵심 약속 제시",
            "working_headline": "설명을 시연으로 바꾼다",
            "dominant_visual": "제목과 진행 경로",
            "composition": "좌측 제목과 우측 단일 경로",
            "speaker_seconds": 45,
            "content_budget": {"headline_max_chars": 32, "body_max_lines": 3},
            "interaction": {
                "decision": "reject",
                "scene_type": "static",
                "benefits": [],
                "reason": "첫 약속은 조작보다 정적 문장이 선명함",
                "lifecycle": "none",
                "fallback": "제목과 한 문장 요약",
            },
            "evidence_boundary": "not-applicable",
            "asset_ids": [],
            "source_ids": [],
            "accessibility": {
                "keyboard": "일반 deck navigation만 사용",
                "reduced_motion": "강조 이동을 즉시 표시",
                "static_fallback": "제목과 핵심 문장 유지",
            },
        }
    ]
    plan["slide_count"] = 1
    return plan


class ProductionProposalGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def validate(self, text: str) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temp_value:
            path = Path(temp_value) / "proposal.md"
            path.write_text(text, encoding="utf-8")
            return self.validator.validate(path, require_approved=True)

    def test_approval_gate_rejects_review_slide_rows(self) -> None:
        result = self.validate(approved_proposal("review"))
        self.assertFalse(result["valid"])
        self.assertIn("S01 (review)", "\n".join(result["errors"]))

    def test_approval_gate_accepts_resolved_slide_rows(self) -> None:
        result = self.validate(approved_proposal("approved"))
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["unresolved_slide_rows"], [])

    def test_approval_gate_rejects_unknown_slide_status(self) -> None:
        result = self.validate(approved_proposal("unknown"))
        errors = "\n".join(result["errors"])
        self.assertIn("unsupported slide row statuses", errors)
        self.assertIn("S01 (unknown)", errors)

    def test_approval_gate_rejects_duplicate_slide_ids(self) -> None:
        text = approved_proposal("approved").replace(
            "estimated_slides: 1", "estimated_slides: 2", 1
        )
        slide_row = next(
            line for line in text.splitlines() if line.startswith("| S01 |")
        )
        result = self.validate(text.replace(slide_row, f"{slide_row}\n{slide_row}", 1))
        self.assertFalse(result["valid"])
        self.assertEqual(result["duplicate_slide_ids"], ["S01"])
        self.assertIn("duplicate slide ID: S01", result["errors"])

    def test_approval_gate_rejects_empty_title(self) -> None:
        result = self.validate(
            approved_proposal("approved").replace(
                'title: "검증용 발표"', 'title: ""', 1
            )
        )
        self.assertFalse(result["valid"])
        self.assertIn("title must not be empty", result["errors"])

    def test_approval_gate_rejects_invalid_proposal_version(self) -> None:
        result = self.validate(
            approved_proposal("approved").replace(
                "proposal_version: 1", "proposal_version: draft", 1
            )
        )
        self.assertFalse(result["valid"])
        self.assertIn("proposal_version must be an integer", result["errors"])

    def test_approval_gate_exposes_slide_entries_for_design_plan(self) -> None:
        result = self.validate(approved_proposal("approved"))
        self.assertEqual(result["title"], "검증용 발표")
        self.assertEqual(result["estimated_slides"], 1)
        self.assertEqual(
            result["slide_entries"], [{"id": "S01", "status": "approved"}]
        )


class DesignPlanGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_design_validator()

    def validate(self, mutate=None) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temp_value:
            directory = Path(temp_value)
            proposal_path = directory / "production-proposal.md"
            proposal_path.write_text(approved_proposal("approved"), encoding="utf-8")
            plan = ready_design_plan(proposal_path)
            if mutate is not None:
                mutate(plan, proposal_path)
            plan_path = directory / "design-plan.json"
            plan_path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return self.validator.validate(
                plan_path, proposal_path, require_ready=True
            )

    def test_ready_design_plan_accepts_bound_approved_proposal(self) -> None:
        result = self.validate()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["approved_slide_ids"], ["S01"])

    def test_design_plan_rejects_stale_proposal_hash(self) -> None:
        def mutate(plan, proposal_path):
            proposal_path.write_text(
                proposal_path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )

        result = self.validate(mutate)
        self.assertFalse(result["valid"])
        self.assertIn(
            "proposal.sha256 does not match approved proposal content",
            result["errors"],
        )

    def test_design_plan_rejects_unapproved_slide_ids(self) -> None:
        def mutate(plan, _proposal_path):
            plan["slides"][0]["id"] = "S02"

        result = self.validate(mutate)
        errors = "\n".join(result["errors"])
        self.assertIn("approved proposal slide missing from design plan: S01", errors)
        self.assertIn("design-plan slide is not approved in proposal: S02", errors)

    def test_design_plan_requires_two_benefits_for_adopted_scene(self) -> None:
        def mutate(plan, _proposal_path):
            plan["slides"][0]["interaction"] = {
                "decision": "adopt",
                "scene_type": "sequence",
                "benefits": ["temporal"],
                "reason": "중간 상태를 순서대로 보여줌",
                "lifecycle": "ready-running-complete",
                "fallback": "번호가 있는 단계 목록",
            }

        result = self.validate(mutate)
        self.assertFalse(result["valid"])
        self.assertIn(
            "slides[0].interaction adoption requires at least two benefits",
            result["errors"],
        )

    def test_design_plan_rejects_headline_over_budget(self) -> None:
        def mutate(plan, _proposal_path):
            plan["slides"][0]["content_budget"]["headline_max_chars"] = 5

        result = self.validate(mutate)
        self.assertFalse(result["valid"])
        self.assertIn(
            "slides[0].working_headline exceeds headline_max_chars",
            "\n".join(result["errors"]),
        )

    def test_design_plan_requires_accessible_icon_chrome(self) -> None:
        def mutate(plan, _proposal_path):
            plan["presentation_chrome"]["accessible_names"] = False

        result = self.validate(mutate)
        self.assertFalse(result["valid"])
        self.assertIn(
            "presentation_chrome.accessible_names must be true", result["errors"]
        )


class DeckProjectValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_deck_validator()

    def copy_starter(self, destination: Path) -> None:
        for name in self.validator.REQUIRED_FILES:
            shutil.copy2(STARTER_PATH / name, destination / name)

    def test_missing_deck_script_fails_load_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            project = Path(temp_value)
            self.copy_starter(project)
            index_path = project / "index.html"
            index_path.write_text(
                index_path.read_text(encoding="utf-8").replace(
                    '<script src="deck.js"></script>', "", 1
                ),
                encoding="utf-8",
            )
            failures, _, _ = self.validator.validate(
                project, allow_remote_assets=False
            )
        self.assertIn(
            "scripts must load deck, scenes, presentation in order", failures
        )

    def test_citation_url_is_not_counted_as_remote_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            project = Path(temp_value)
            self.copy_starter(project)
            deck_path = project / "deck.js"
            deck_path.write_text(
                deck_path.read_text(encoding="utf-8").replace(
                    'sources: ["Interactive Slides starter · architecture contract"]',
                    'sources: ["https://example.com/report"]',
                    1,
                ),
                encoding="utf-8",
            )
            failures, _, metrics = self.validator.validate(
                project, allow_remote_assets=False
            )
        self.assertEqual(failures, [])
        self.assertEqual(metrics["remote_urls"], 0)

    def test_remote_image_is_counted_as_remote_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            project = Path(temp_value)
            self.copy_starter(project)
            index_path = project / "index.html"
            index_path.write_text(
                index_path.read_text(encoding="utf-8").replace(
                    "</body>",
                    '<img src=https://example.com/chart.png alt="">\n</body>',
                    1,
                ),
                encoding="utf-8",
            )
            failures, _, metrics = self.validator.validate(
                project, allow_remote_assets=False
            )
        self.assertIn("remote URLs require --allow-remote-assets: 1 found", failures)
        self.assertEqual(metrics["remote_urls"], 1)

    def test_progressive_scene_restores_next_action_label(self) -> None:
        scenes = (STARTER_PATH / "scenes.js").read_text(encoding="utf-8")
        self.assertIn("if (this.index < this.items.length)", scenes)
        self.assertIn(
            'this.nextButton.textContent = this.config.type === "timeline" ? "다음 사건" : "다음 줄";',
            scenes,
        )


if __name__ == "__main__":
    unittest.main()

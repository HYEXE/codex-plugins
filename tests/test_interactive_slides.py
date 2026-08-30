from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "interactive-slides" / "skills" / "create-interactive-slides"
VALIDATOR_PATH = SKILL / "scripts" / "validate_production_proposal.py"
DECK_VALIDATOR_PATH = SKILL / "scripts" / "validate_deck_project.py"
STARTER_PATH = SKILL / "assets" / "starter"
TEMPLATE_PATH = SKILL / "templates" / "production-proposal.md"


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

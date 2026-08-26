from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "interactive-slides" / "skills" / "create-interactive-slides"
VALIDATOR_PATH = SKILL / "scripts" / "validate_production_proposal.py"
TEMPLATE_PATH = SKILL / "templates" / "production-proposal.md"


def load_validator():
    spec = importlib.util.spec_from_file_location("interactive_slides_proposal_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Interactive Slides proposal validator")
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


if __name__ == "__main__":
    unittest.main()

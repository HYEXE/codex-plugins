from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "interactive-slides" / "skills" / "create-interactive-slides"
EVALUATOR_PATH = SKILL / "scripts" / "eval_forward_fixtures.py"
MANIFEST_PATH = SKILL / "evals" / "forward" / "cases.json"


def load_evaluator():
    spec = importlib.util.spec_from_file_location(
        "interactive_slides_forward_evaluator",
        EVALUATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Interactive Slides forward evaluator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVALUATOR = load_evaluator()


class InteractiveSlidesForwardEvalTests(unittest.TestCase):
    def load_cases(self) -> list[dict]:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return payload["cases"]

    def evaluate_manifest_payload(self, payload: dict):
        with tempfile.TemporaryDirectory() as raw_temp:
            manifest_path = Path(raw_temp) / "cases.json"
            manifest_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            return EVALUATOR.evaluate_manifest(manifest_path)

    def test_demo_and_experience_fixtures_pass(self):
        result = EVALUATOR.evaluate_manifest(MANIFEST_PATH)

        self.assertEqual("passed", result["status"], result)
        self.assertEqual(
            {"cases": 2, "passed": 2, "failed": 0, "slides": 8},
            result["summary"],
        )
        self.assertEqual(
            {"demo", "experience"},
            {case["mode"] for case in result["results"]},
        )
        self.assertTrue(
            all(3 <= case["metrics"]["slides"] <= 5 for case in result["results"])
        )

    def test_mode_drift_is_rejected(self):
        case = copy.deepcopy(self.load_cases()[0])
        case["mode"] = "experience"
        case["expected"]["mode_lifecycle"] = "direct-manipulation-reset"

        result = EVALUATOR.evaluate_case(case)

        self.assertEqual("failed", result["status"])
        self.assertTrue(
            any("defaultMode" in failure for failure in result["failures"]),
            result,
        )

    def test_missing_slide_fallback_is_rejected(self):
        case = copy.deepcopy(self.load_cases()[0])
        fixture = MANIFEST_PATH.parent / case["fixture"]
        deck = fixture.read_text(encoding="utf-8").replace(
            "fallback:",
            "fallbackRemoved:",
            1,
        )

        with tempfile.TemporaryDirectory() as raw_temp:
            eval_root = Path(raw_temp)
            fixture_path = eval_root / "deck.js"
            fixture_path.write_text(deck, encoding="utf-8")
            case["fixture"] = "deck.js"

            result = EVALUATOR.evaluate_case(case, eval_root=eval_root)

        self.assertEqual("failed", result["status"])
        self.assertIn("slide 1 missing non-empty fallback", result["failures"])

    def test_unlocked_delivery_mode_is_rejected(self):
        case = copy.deepcopy(self.load_cases()[1])
        fixture = MANIFEST_PATH.parent / case["fixture"]
        deck = fixture.read_text(encoding="utf-8").replace(
            "modeLocked: true",
            "modeLocked: false",
            1,
        )

        with tempfile.TemporaryDirectory() as raw_temp:
            eval_root = Path(raw_temp)
            fixture_path = eval_root / "deck.js"
            fixture_path.write_text(deck, encoding="utf-8")
            case["fixture"] = "deck.js"

            result = EVALUATOR.evaluate_case(case, eval_root=eval_root)

        self.assertEqual("failed", result["status"])
        self.assertIn(
            "fixture must lock its selected delivery mode with modeLocked: true",
            result["failures"],
        )

    def test_scene_type_requires_matching_recipe_payload(self):
        case = copy.deepcopy(self.load_cases()[1])
        fixture = MANIFEST_PATH.parent / case["fixture"]
        deck = fixture.read_text(encoding="utf-8").replace(
            'type: "choice"',
            'type: "sequence"',
            1,
        )
        case["expected"]["scene_types"][0] = "sequence"

        with tempfile.TemporaryDirectory() as raw_temp:
            eval_root = Path(raw_temp)
            fixture_path = eval_root / "deck.js"
            fixture_path.write_text(deck, encoding="utf-8")
            case["fixture"] = "deck.js"
            result = EVALUATOR.evaluate_case(case, eval_root=eval_root)

        self.assertEqual("failed", result["status"])
        self.assertTrue(
            any("scene sequence missing recipe field" in item for item in result["failures"]),
            result,
        )

    def test_mode_lock_requires_runtime_enforcement(self):
        case = copy.deepcopy(self.load_cases()[0])

        with tempfile.TemporaryDirectory() as raw_temp:
            starter = Path(raw_temp) / "starter"
            shutil.copytree(EVALUATOR.DEFAULT_STARTER, starter)
            runtime_path = starter / "presentation.js"
            runtime_path.write_text(
                runtime_path.read_text(encoding="utf-8").replace(
                    "if (modeLocked) return;",
                    "if (false) return;",
                    1,
                ),
                encoding="utf-8",
            )
            result = EVALUATOR.evaluate_case(case, starter=starter)

        self.assertEqual("failed", result["status"])
        self.assertTrue(
            any(
                "canonical runtime does not enforce modeLocked" in item
                for item in result["failures"]
            ),
            result,
        )

    def test_manifest_rejects_unhashable_case_id_without_crashing(self):
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        payload["cases"][0]["id"] = {"invalid": "object"}

        result = self.evaluate_manifest_payload(payload)

        self.assertEqual("failed", result["status"])
        self.assertIn("case IDs must be strings", result["manifest_failures"])

    def test_manifest_rejects_invalid_mode_type_without_crashing(self):
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        payload["cases"][0]["mode"] = {"invalid": "object"}

        result = self.evaluate_manifest_payload(payload)

        self.assertEqual("failed", result["status"])
        self.assertIn(
            "manifest must contain exactly one demo and one experience case",
            result["manifest_failures"],
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import eval_routing  # noqa: E402


class RoutingDiscoveryTests(unittest.TestCase):
    def test_known_skills_are_discovered_from_marketplace_plugins(self) -> None:
        expected = {
            path.parent.name
            for plugin in (ROOT / "plugins").iterdir()
            if plugin.is_dir()
            for path in plugin.glob("skills/*/SKILL.md")
        }
        self.assertEqual(eval_routing.discover_known_skills(), expected)


class RoutingScoringTests(unittest.TestCase):
    def test_declared_alternative_passes_without_replacing_canonical_skill(self) -> None:
        cases = [
            {
                "id": "dual-signal",
                "expected_skill": "implement-ui-motion",
                "acceptable_skills": ["implement-ui-interaction"],
                "forbidden_skills": ["compose-creative-ui"],
                "boundary": "dual-signal",
            }
        ]
        observed = [{"id": "dual-signal", "selected_skill": "implement-ui-interaction"}]
        output = io.StringIO()
        with redirect_stdout(output):
            result = eval_routing.score(cases, observed)
        self.assertEqual(result, 0)
        self.assertIn("canonical=0, acceptable=1", output.getvalue())

    def test_forbidden_selection_is_a_distinct_hard_failure(self) -> None:
        cases = [
            {
                "id": "unsafe-boundary",
                "expected_skill": "implement-ui-interaction",
                "acceptable_skills": ["implement-async-ui-state"],
                "forbidden_skills": ["uiux-auditor"],
                "boundary": "unsafe-boundary",
            }
        ]
        observed = [{"id": "unsafe-boundary", "selected_skill": "uiux-auditor"}]
        output = io.StringIO()
        with redirect_stdout(output):
            result = eval_routing.score(cases, observed)
        self.assertEqual(result, 1)
        self.assertIn("FORBIDDEN:", output.getvalue())

    def test_case_validation_rejects_acceptable_forbidden_overlap(self) -> None:
        cases = [
            {
                "id": "invalid-overlap",
                "prompt": "이중 신호 경계를 구현해줘.",
                "expected_skill": "implement-ui-interaction",
                "acceptable_skills": ["implement-async-ui-state"],
                "forbidden_skills": ["implement-async-ui-state"],
                "boundary": "invalid-overlap",
            }
        ]
        failures = eval_routing.validate_cases(cases)
        self.assertTrue(any("both acceptable and forbidden" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_all  # noqa: E402


class DeclarativeValidatorTests(unittest.TestCase):
    def test_plugins_declare_validators_without_dated_observation_files(self) -> None:
        for config_path in sorted((ROOT / "plugins").glob("*/.codex-plugin/quality-gates.json")):
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertTrue(config.get("validators"), config_path)
            required_files = [
                required
                for skill in config.get("skills", {}).values()
                for required in skill.get("required_files", [])
            ]
            self.assertFalse(
                any("observed-" in required for required in required_files),
                config_path,
            )

    def test_observation_result_token_is_resolved_without_shell(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            plugin_root = Path(temp_value) / "sample"
            config_path = plugin_root / ".codex-plugin" / "quality-gates.json"
            validator_dir = plugin_root / ".codex-plugin" / "validators"
            validator_dir.mkdir(parents=True)
            config_path.write_text("{}", encoding="utf-8")
            (validator_dir / "score.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
            results_path = plugin_root / "results.jsonl"
            results_path.write_text("{}\n", encoding="utf-8")
            config = {
                "validators": [
                    {
                        "name": "score",
                        "cwd": "validators",
                        "argv": ["{python}", "score.py", "{observation:sample}"],
                    }
                ]
            }
            failures: list[str] = []
            with mock.patch.object(validate_all, "run") as run:
                validate_all.run_declared_validators(
                    "sample",
                    config_path,
                    config,
                    {"sample": {"results_path": results_path}},
                    failures,
                )
            self.assertEqual(failures, [])
            run.assert_called_once_with(
                [sys.executable, "score.py", str(results_path)],
                validator_dir.resolve(),
                failures,
                echo=True,
            )

    def test_validator_script_cannot_escape_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            plugin_root = root / "sample"
            config_path = plugin_root / ".codex-plugin" / "quality-gates.json"
            config_path.parent.mkdir(parents=True)
            config_path.write_text("{}", encoding="utf-8")
            (root / "outside.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
            failures: list[str] = []
            validate_all.run_declared_validators(
                "sample",
                config_path,
                {
                    "validators": [
                        {
                            "name": "escape",
                            "cwd": "..",
                            "argv": ["{python}", "../outside.py"],
                        }
                    ]
                },
                {},
                failures,
            )
            self.assertTrue(any("escapes plugin directory" in failure for failure in failures))

    def test_file_scoped_markers_do_not_fall_through_to_other_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            skill_dir = Path(temp_value)
            (skill_dir / "SKILL.md").write_text("evaluation only\n", encoding="utf-8")
            reference = skill_dir / "references" / "contract.md"
            reference.parent.mkdir()
            reference.write_text("eval\n", encoding="utf-8")
            failures: list[str] = []

            validate_all.validate_required_markers(
                "sample",
                "sample-skill",
                skill_dir,
                [{"path": "SKILL.md", "regex": r"\beval\b"}],
                failures,
            )

            self.assertEqual(1, len(failures))
            self.assertIn("SKILL.md", failures[0])

    def test_file_scoped_marker_accepts_literal_and_rejects_unsafe_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            skill_dir = root / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("Approval Binding\n", encoding="utf-8")
            (root / "outside.md").write_text("Approval Binding\n", encoding="utf-8")
            failures: list[str] = []

            validate_all.validate_required_markers(
                "sample",
                "sample-skill",
                skill_dir,
                [
                    {"path": "SKILL.md", "contains": "Approval Binding"},
                    {"path": "../outside.md", "contains": "Approval Binding"},
                ],
                failures,
            )

            self.assertEqual(1, len(failures))
            self.assertIn("escapes the skill directory", failures[0])

    def test_interactive_slides_gate_covers_production_pipeline(self) -> None:
        config_path = (
            ROOT / "plugins" / "interactive-slides" / ".codex-plugin" / "quality-gates.json"
        )
        config = json.loads(config_path.read_text(encoding="utf-8"))
        gate = config["skills"]["create-interactive-slides"]
        self.assertTrue(
            {
                "references/language-policy.md",
                "references/authoring-intake.md",
                "references/design-plan-contract.md",
                "references/proposal-workflow.md",
                "references/visual-quality-system.md",
                "templates/design-plan.json",
                "templates/presentation-intake.md",
                "templates/production-proposal.md",
                "templates/proposal-feedback.md",
                "evals/forward/cases.json",
                "scripts/validate_production_proposal.py",
                "scripts/validate_design_plan.py",
                "scripts/eval_forward_fixtures.py",
            }
            <= set(gate["required_files"])
        )
        self.assertTrue(
            {
                "scripts/validate_production_proposal.py",
                "scripts/validate_design_plan.py",
                "scripts/eval_forward_fixtures.py",
            }
            <= {validator["argv"][1] for validator in config["validators"]}
        )

    def test_uiux_content_rules_are_plugin_local(self) -> None:
        config_path = ROOT / "plugins" / "uiux-advisor" / ".codex-plugin" / "quality-gates.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        scripts = {validator["argv"][1] for validator in config["validators"]}
        self.assertIn("validate_content.py", scripts)
        self.assertIn(
            "references/kb/REVIEW_SCHEDULE.md",
            config["skills"]["uiux-advisor"]["required_files"],
        )
        self.assertIn(
            "references/frontend-stack-selection.md",
            config["skills"]["uiux-advisor"]["required_files"],
        )
        self.assertTrue(
            {
                "application-framework",
                "routing",
                "server-state",
                "client-state",
                "form",
                "validation",
                "data-table",
                "testing",
            }
            <= set(config["toolkit_registry"]["required_roles"])
        )
        self.assertTrue(
            {"react", "vue", "svelte", "angular", "solid", "astro"}
            <= set(config["toolkit_registry"]["required_ecosystems"])
        )

        common_validator = (ROOT / "scripts" / "validate_all.py").read_text(encoding="utf-8")
        self.assertNotIn("validate_uiux_kb", common_validator)
        self.assertNotIn("validate_frontend_toolkits", common_validator)
        self.assertNotIn('"uiux-advisor"', common_validator)


if __name__ == "__main__":
    unittest.main()

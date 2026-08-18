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


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_live_eval_canary_matrix as canary  # noqa: E402
import build_live_eval_release_report as release_report  # noqa: E402
import validate_live_eval_release_report as report_validator  # noqa: E402


class CanaryMatrixTests(unittest.TestCase):
    def test_dry_run_uses_windows_safe_cell_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            args = argparse.Namespace(
                output_root=root,
                invocation_id="test",
                codex_builds=[("baseline", "codex")],
                models=["gpt-5.6:preview"],
                suites=["routing"],
                dry_run=True,
                attempts=1,
                case_set="critical",
                reasoning_effort="medium",
                auth_mode="saved",
                timeout_seconds=30,
                baseline=None,
                regression_threshold=0.05,
                output_json=None,
                output_markdown=None,
            )
            report = canary.build_report(args)
            artifact_path = report["matrix"][0]["artifact_path"]
            self.assertFalse(any(character in artifact_path for character in '<>:"/\\|?*'))
            self.assertIn("baseline:gpt-5.6:preview", report["baseline"])

    def test_build_specs_reject_duplicate_labels(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            canary.parse_codex_builds(["same=codex", "same=codex-next"])


class ReleaseReportTests(unittest.TestCase):
    def test_run_ids_reject_duplicates(self) -> None:
        run_id = "20260826T000000Z-aaaaaaaaaaaa"
        with self.assertRaisesRegex(ValueError, "duplicate run IDs"):
            release_report.parse_run_ids(",".join([run_id] * 4))

    def test_run_label_must_match_suite_and_case_set(self) -> None:
        run = {
            "label": "routing_critical",
            "run_id": "20260826T000000Z-aaaaaaaaaaaa",
            "suite": "tool-trace",
            "case_set": "critical",
        }
        with mock.patch.object(release_report, "build_run_record", return_value=run):
            with self.assertRaisesRegex(ValueError, "expected routing/critical"):
                release_report.build_runs(
                    {"routing_critical": run["run_id"]}, Path("unused")
                )

    def test_previous_source_is_preserved_when_no_trends_match(self) -> None:
        previous = {"schema_version": "1.1.0", "current_tag": "old", "runs": []}
        with tempfile.TemporaryDirectory() as temp_value:
            previous_path = Path(temp_value) / "previous.json"
            previous_path.write_text(json.dumps(previous), encoding="utf-8")
            args = argparse.Namespace(
                run_ids="unused",
                run_root=Path(temp_value),
                current_tag="new",
                previous_report=previous_path,
                regression_threshold=0.05,
            )
            with mock.patch.object(release_report, "parse_run_ids", return_value={}):
                with mock.patch.object(release_report, "build_runs", return_value=[]):
                    report = release_report.build_report(args)
            self.assertEqual(report["previous"]["source"], previous_path.as_posix())
            self.assertEqual(report["previous"]["note"], "no comparable labels found")

    def test_release_asset_validator_checks_tag_and_run_provenance(self) -> None:
        ids = {
            label: f"20260826T00000{index}Z-{index:012x}"
            for index, label in enumerate(release_report.RUN_LABELS)
        }
        payload = {
            "schema_version": "1.1.0",
            "current_tag": "codex-plugins-v1.0.0",
            "runs": [
                {
                    "label": label,
                    "run_id": run_id,
                    "suite": release_report.RUN_EXPECTATIONS[label][0],
                    "case_set": release_report.RUN_EXPECTATIONS[label][1],
                    "release_gate": True,
                }
                for label, run_id in ids.items()
            ],
        }
        failures = report_validator.validate_report(
            payload,
            "codex-plugins-v1.0.0",
            ",".join(ids[label] for label in release_report.RUN_LABELS),
        )
        self.assertEqual(failures, [])
        failures = report_validator.validate_report(
            payload,
            "codex-plugins-v2.0.0",
            ",".join(ids[label] for label in release_report.RUN_LABELS),
        )
        self.assertIn("current_tag must be codex-plugins-v2.0.0", failures)


if __name__ == "__main__":
    unittest.main()

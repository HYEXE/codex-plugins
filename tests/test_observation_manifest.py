from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_observation_manifest as observations  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ObservationManifestTests(unittest.TestCase):
    def test_repository_manifests_validate(self) -> None:
        routing, routing_failures = observations.validate_manifest(ROOT / "tests" / "observations.json")
        prompt, prompt_failures = observations.validate_manifest(
            ROOT / "plugins" / "prompt-compiler" / "evals" / "observations.json"
        )
        self.assertEqual(routing_failures, [])
        self.assertEqual(prompt_failures, [])
        self.assertEqual(set(routing), {"routing"})
        self.assertEqual(set(prompt), {"prompt-coach", "prompt-orchestration"})

    def test_hash_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            dataset = root / "cases.jsonl"
            results = root / "results.jsonl"
            dataset.write_text("{}\n", encoding="utf-8")
            results.write_text("{}\n", encoding="utf-8")
            metadata = {
                "schema_version": "1.0.0",
                "suite": "sample",
                "provenance_status": "complete",
                "source": "live-eval",
                "observed_at": "2026-08-01T00:00:00Z",
                "run_id": "run-1",
                "model": "gpt-5.6",
                "codex_version": "codex-cli 0.147.0",
                "plugin_versions": {"sample": "1.0.0"},
                "dataset": dataset.name,
                "dataset_sha256": "0" * 64,
                "results": results.name,
                "results_sha256": hashlib.sha256(results.read_bytes()).hexdigest(),
                "observation_scope": "structured",
            }
            write_json(root / "sample.metadata.json", metadata)
            write_json(
                root / "observations.json",
                {"schema_version": "1.0.0", "suites": {"sample": {"metadata": "sample.metadata.json"}}},
            )
            _, failures = observations.validate_manifest(root / "observations.json", boundary=root)
            self.assertTrue(any("dataset hash mismatch" in failure for failure in failures))

    def test_legacy_partial_requires_notes(self) -> None:
        metadata = {
            "schema_version": "1.0.0",
            "suite": "sample",
            "provenance_status": "legacy-partial",
            "source": "snapshot",
            "observed_at": "2026-08-01T00:00:00Z",
            "plugin_versions": {"sample": "1.0.0"},
            "dataset": "missing.jsonl",
            "dataset_sha256": "0" * 64,
            "results": "missing-results.jsonl",
            "results_sha256": "0" * 64,
            "observation_scope": "transcript",
        }
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            write_json(root / "sample.metadata.json", metadata)
            _, failures = observations.validate_metadata(
                root / "sample.metadata.json", expected_suite="sample", boundary=root
            )
            self.assertTrue(any("requires notes" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import create_release_attestation as attestation  # noqa: E402


RUN_IDS = ",".join(
    (
        "20260818T010101Z-111111111111",
        "20260818T010102Z-222222222222",
        "20260818T010103Z-333333333333",
        "20260818T010104Z-444444444444",
    )
)


class ReleaseAttestationTests(unittest.TestCase):
    def test_builds_ordered_local_live_eval_attestation(self) -> None:
        result = attestation.build_attestation(
            tag="codex-workflows-v0.1.0",
            commit="a" * 40,
            model="gpt-5.6-sol",
            codex_version="codex-cli 0.147.0",
            run_ids=RUN_IDS,
            actor="HYEXE",
            repository="HYEXE/codex-workflows",
            workflow_run_id="123",
            workflow_run_attempt="1",
        )
        self.assertEqual(result["auth_mode"], "saved-chatgpt")
        self.assertEqual(list(result["runs"]), list(attestation.RUN_LABELS))
        self.assertTrue(result["operator_assertion"]["confirmed"])

    def test_rejects_incomplete_or_duplicate_run_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires 4"):
            attestation.parse_run_ids("20260818T010101Z-111111111111")
        duplicate = ",".join(["20260818T010101Z-111111111111"] * 4)
        with self.assertRaisesRegex(ValueError, "must be unique"):
            attestation.parse_run_ids(duplicate)


if __name__ == "__main__":
    unittest.main()

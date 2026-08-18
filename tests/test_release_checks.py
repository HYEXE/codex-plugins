from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_release_readiness  # noqa: E402
import validate_release_tag  # noqa: E402


class ReleaseReadinessTests(unittest.TestCase):
    def test_required_license_and_notice_are_enforced(self) -> None:
        policy = {
            "schema_version": "1.0.0",
            "required_public_release_files": ["LICENSE", "THIRD_PARTY_NOTICES.md"],
            "required_attribution_sources": [],
            "repository_license": {
                "spdx": "Apache-2.0",
                "file": "LICENSE",
                "sha256": "0" * 64,
                "required_markers": ["Apache License", "Version 2.0"],
            },
            "forbidden_release_markers": ["[LICENSE-TBD]"],
        }
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            (root / "THIRD_PARTY_NOTICES.md").write_text("notices\n", encoding="utf-8")
            failures = check_release_readiness.check_release_readiness(root, policy)
            self.assertEqual(failures, ["missing required public release file: LICENSE"])
            (root / "LICENSE").write_text("[LICENSE-TBD]\n", encoding="utf-8")
            failures = check_release_readiness.check_release_readiness(root, policy)
            self.assertIn("LICENSE contains unresolved release marker: [LICENSE-TBD]", failures)
            self.assertTrue(any("does not match declared Apache-2.0" in failure for failure in failures))

    def test_complete_release_files_pass(self) -> None:
        license_text = "Apache License\nVersion 2.0\n"
        policy = {
            "schema_version": "1.0.0",
            "required_public_release_files": ["LICENSE", "THIRD_PARTY_NOTICES.md"],
            "required_attribution_sources": [],
            "repository_license": {
                "spdx": "Apache-2.0",
                "file": "LICENSE",
                "sha256": hashlib.sha256(license_text.encode("utf-8")).hexdigest(),
                "required_markers": ["Apache License", "Version 2.0"],
            },
            "forbidden_release_markers": ["[LICENSE-TBD]"],
        }
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            (root / "LICENSE").write_bytes(license_text.encode("utf-8"))
            (root / "THIRD_PARTY_NOTICES.md").write_text("Example notice\n", encoding="utf-8")
            self.assertEqual(check_release_readiness.check_release_readiness(root, policy), [])


class ReleaseTagTests(unittest.TestCase):
    def test_plugin_tag_must_match_manifest_version(self) -> None:
        policy = validate_release_tag.load_object(ROOT / "release" / "release-policy.json")
        failures, metadata = validate_release_tag.validate_tag(
            "prompt-compiler-v0.7.1", policy, ROOT
        )
        self.assertEqual(failures, [])
        self.assertEqual(metadata["plugin"], "prompt-compiler")
        failures, _ = validate_release_tag.validate_tag("prompt-compiler-v9.9.9", policy, ROOT)
        self.assertTrue(failures)

    def test_repository_tag_uses_semver(self) -> None:
        policy = validate_release_tag.load_object(ROOT / "release" / "release-policy.json")
        failures, metadata = validate_release_tag.validate_tag(
            "codex-workflows-v0.1.0", policy, ROOT
        )
        self.assertEqual(failures, [])
        self.assertEqual(metadata["release_kind"], "repository")


class ReleaseWorkflowTests(unittest.TestCase):
    def test_release_validates_before_creating_tag(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("\n  push:\n", workflow)
        self.assertIn('ref: ${{ inputs.commit }}', workflow)
        self.assertIn('case_set: critical\n      attempts: 2', workflow)
        self.assertIn('case_set: full\n      attempts: 1', workflow)
        self.assertIn('--target "$RELEASE_COMMIT"', workflow)
        self.assertLess(workflow.index("live-eval-critical:"), workflow.index("gh release create"))

    def test_live_eval_is_manual_or_release_only(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "live-eval.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("workflow_call:", workflow)
        self.assertNotIn("\n  schedule:\n", workflow)
        self.assertIn('ref: ${{ inputs.target_commit || github.sha }}', workflow)


if __name__ == "__main__":
    unittest.main()

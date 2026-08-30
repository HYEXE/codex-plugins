from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_all  # noqa: E402


class RepositoryInventoryTests(unittest.TestCase):
    def create_repository(self, root: Path, *, readme_version: str = "1.0.0", include_policy: bool = True) -> None:
        manifest = root / "plugins" / "sample" / ".codex-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"name": "sample", "version": "1.0.0"}), encoding="utf-8")
        policy_plugins = {
            "sample": {
                "tag_prefix": "sample-v",
                "manifest": "plugins/sample/.codex-plugin/plugin.json",
            }
        } if include_policy else {}
        policy = root / "release" / "release-policy.json"
        policy.parent.mkdir(parents=True)
        policy.write_text(json.dumps({"plugins": policy_plugins}), encoding="utf-8")
        (root / "README.md").write_text(
            f"| `sample` | `{readme_version}` | `sample-skill` | sample |\n",
            encoding="utf-8",
        )

    def test_four_way_inventory_is_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            self.create_repository(root)
            failures: list[str] = []
            validate_all.validate_repository_inventory(["sample"], failures, root=root)
            self.assertEqual(failures, [])

    def test_release_policy_and_readme_drift_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            self.create_repository(root, readme_version="0.9.0", include_policy=False)
            failures: list[str] = []
            validate_all.validate_repository_inventory(["sample"], failures, root=root)
            self.assertTrue(any("release-policy" in failure for failure in failures))
            self.assertTrue(any("README version" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()

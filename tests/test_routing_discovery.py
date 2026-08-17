from __future__ import annotations

import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
SEARCH_SCRIPT = (
    ROOT
    / "plugins"
    / "uiux-advisor"
    / "skills"
    / "uiux-advisor"
    / "scripts"
    / "search_toolkits.py"
)
NEXT_FIXTURE = (
    ROOT
    / "plugins"
    / "uiux-advisor"
    / ".codex-plugin"
    / "evals"
    / "fixtures"
    / "next-package.json"
)


def load_search_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("test_search_toolkits", SEARCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SEARCH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ToolkitRecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_search_module()
        cls.registry = cls.module.load_registry(cls.module.REGISTRY_PATH)
        cls.relations = cls.module.load_relations(
            cls.module.RELATIONS_PATH,
            cls.registry,
        )

    def namespace(self, **values: object) -> argparse.Namespace:
        defaults: dict[str, object] = {
            "tool_id": None,
            "role": None,
            "ecosystem": None,
            "kind": None,
            "capability": None,
            "surface": None,
            "risk": None,
            "max_risk": None,
            "adoption": None,
            "status": None,
            "recommend": True,
            "top": None,
            "strategy": "conservative",
            "existing_packages": [],
            "existing_tool_ids": [],
        }
        defaults.update(values)
        return argparse.Namespace(**defaults)

    def test_package_manifest_detects_framework_and_test_toolkits(self) -> None:
        packages = self.module.load_existing_packages(NEXT_FIXTURE)
        detected = self.module.detect_existing_tool_ids(self.relations, packages)
        self.assertEqual({"next-js", "vitest"}, detected)

    def test_package_manifest_rejects_non_string_dependency_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            manifest = Path(temp_value) / "package.json"
            manifest.write_text(
                json.dumps({"dependencies": {"next": 1}}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "dependencies must map"):
                self.module.load_existing_packages(manifest)

    def test_ecosystem_first_strategy_prioritizes_exact_framework(self) -> None:
        conservative = self.namespace(
            role="application-framework",
            ecosystem="vue",
            surface="content-site",
            strategy="conservative",
            top=2,
        )
        ecosystem_first = self.namespace(
            role="application-framework",
            ecosystem="vue",
            surface="content-site",
            strategy="ecosystem-first",
            top=2,
        )
        self.assertEqual(
            ["astro", "nuxt"],
            [tool["id"] for tool in self.module.search(self.registry, conservative)],
        )
        self.assertEqual(
            ["nuxt", "astro"],
            [tool["id"] for tool in self.module.search(self.registry, ecosystem_first)],
        )

    def test_existing_next_is_kept_and_competing_routers_are_warned(self) -> None:
        args = self.namespace(
            role="routing",
            ecosystem="react",
            strategy="ecosystem-first",
            existing_tool_ids={"next-js"},
        )
        results = self.module.search(self.registry, args)
        context = self.module.build_recommendation_context(
            self.relations,
            args,
            results,
        )
        self.assertEqual("next-js", results[0]["id"])
        self.assertEqual(["next-js"], context["provided_roles"]["routing"])
        for tool_id in ("react-router", "tanstack-router"):
            warning_codes = {
                warning["code"] for warning in context["warnings_by_tool"][tool_id]
            }
            self.assertEqual(
                {"conflicts-with-installed", "role-provided-by-installed"},
                warning_codes,
            )

    def test_cli_explain_json_preserves_context_and_results(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SEARCH_SCRIPT),
                "--role",
                "routing",
                "--ecosystem",
                "react",
                "--recommend",
                "--existing-stack",
                str(NEXT_FIXTURE),
                "--explain",
                "--json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(["next-js", "vitest"], payload["context"]["installed_toolkits"])
        self.assertEqual("next-js", payload["results"][0]["id"])


if __name__ == "__main__":
    unittest.main()

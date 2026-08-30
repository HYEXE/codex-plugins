from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_source_liveness as liveness  # noqa: E402


class SourceLivenessTests(unittest.TestCase):
    def test_html_metadata_and_hash_are_reported(self) -> None:
        record = liveness.SourceRecord(
            source_id="example",
            source_kind="knowledge-base",
            expected_title="Example Guide",
            requested_url="https://example.com/guide",
        )
        result = liveness.inspect_html(
            record,
            b'<html><head><title>Example Guide - Docs</title><link rel="canonical" href="/guide"></head></html>',
            "https://example.com/guide",
            200,
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.canonical_url, "https://example.com/guide")
        self.assertEqual(result.title_similarity, 1.0)
        self.assertEqual(len(result.content_sha256 or ""), 64)

    def test_report_detects_baseline_hash_drift(self) -> None:
        result = liveness.SourceResult(
            source_id="example",
            source_kind="toolkit",
            requested_url="https://example.com",
            status="ok",
            http_status=200,
            final_url="https://example.com/",
            canonical_url="https://example.com/",
            observed_title="Example",
            title_similarity=1.0,
            content_sha256="b" * 64,
            content_bytes=10,
        )
        report = liveness.build_report(
            [result],
            {("toolkit", "example"): {"content_sha256": "a" * 64}},
            comparison_source="manual:tests/fixtures/source-liveness.json",
        )
        self.assertEqual(report["summary"]["hash_changed"], 1)

    def test_load_stable_history_entry(self) -> None:
        history = [
            {
                "summary": {
                    "total": 1,
                    "reachable": 0,
                    "unreachable": 1,
                    "canonical_changed": 0,
                    "title_changed": 0,
                    "hash_changed": 0,
                }
            },
            {
                "summary": {
                    "total": 1,
                    "reachable": 1,
                    "unreachable": 0,
                    "canonical_changed": 0,
                    "title_changed": 0,
                    "hash_changed": 0,
                }
            },
        ]
        selected = liveness.pick_stable_history_entry(history)
        self.assertEqual(selected, history[-1])

    def test_history_comparison_is_recorded_in_report(self) -> None:
        result = liveness.SourceResult(
            source_id="example",
            source_kind="toolkit",
            requested_url="https://example.com",
            status="ok",
            http_status=200,
            final_url="https://example.com/",
            canonical_url="https://example.com/",
            observed_title="Example",
            title_similarity=1.0,
            content_sha256="b" * 64,
            content_bytes=10,
        )
        report = liveness.build_report(
            [result],
            {("toolkit", "example"): {"content_sha256": "a" * 64}},
            comparison_source="history:20260818T000000Z",
        )
        self.assertEqual(report["comparison"]["source"], "history:20260818T000000Z")
        self.assertTrue(report["comparison"]["enabled"])

    def test_repeated_healthy_hash_drift_promotes_new_baseline(self) -> None:
        def entry(content_sha256: str, hash_changed: int) -> dict[str, object]:
            return {
                "summary": {
                    "total": 1,
                    "reachable": 1,
                    "unreachable": 0,
                    "canonical_changed": 0,
                    "title_changed": 0,
                    "hash_changed": hash_changed,
                },
                "results": [
                    {
                        "source_id": "example",
                        "source_kind": "toolkit",
                        "requested_url": "https://example.com",
                        "canonical_url": "https://example.com/",
                        "observed_title": "Example",
                        "content_sha256": content_sha256,
                    }
                ],
            }

        old_baseline = entry("a" * 64, 0)
        first_drift = entry("b" * 64, 1)
        repeated_drift = entry("b" * 64, 1)
        self.assertIs(
            liveness.pick_stable_history_entry([old_baseline, first_drift]),
            old_baseline,
        )
        self.assertIs(
            liveness.pick_stable_history_entry(
                [old_baseline, first_drift, repeated_drift]
            ),
            repeated_drift,
        )

    def test_history_entry_keeps_only_baseline_fields(self) -> None:
        report = {
            "schema_version": "1.0.0",
            "checked_at": "2026-08-26T00:00:00Z",
            "non_blocking": True,
            "comparison": {"enabled": False, "source": None},
            "summary": {"total": 1},
            "results": [
                {
                    "source_id": "example",
                    "source_kind": "toolkit",
                    "requested_url": "https://example.com",
                    "canonical_url": "https://example.com/",
                    "observed_title": "Example",
                    "content_sha256": "a" * 64,
                    "content_bytes": 999,
                    "error": "unused",
                }
            ],
        }
        entry = liveness.build_history_entry(report, compared_from=None, is_stable=True)
        self.assertNotIn("content_bytes", entry["results"][0])
        self.assertNotIn("error", entry["results"][0])
        self.assertEqual(entry["results"][0]["content_sha256"], "a" * 64)

    def test_private_address_is_rejected(self) -> None:
        with mock.patch.object(liveness.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaisesRegex(ValueError, "non-public"):
                liveness.validate_target("https://localhost/internal")

    def test_redirect_target_is_validated_before_request(self) -> None:
        handler = liveness.SafeRedirectHandler()
        with mock.patch.object(
            liveness,
            "validate_target",
            side_effect=ValueError("blocked redirect"),
        ) as validate:
            with self.assertRaisesRegex(ValueError, "blocked redirect"):
                handler.redirect_request(
                    mock.Mock(),
                    None,
                    302,
                    "Found",
                    {},
                    "https://127.0.0.1/internal",
                )
        validate.assert_called_once_with("https://127.0.0.1/internal")

    def test_history_lookup_is_scoped_to_current_branch(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "source-liveness.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'gh run list --workflow source-liveness.yml --branch "$GITHUB_REF_NAME"',
            workflow,
        )


if __name__ == "__main__":
    unittest.main()

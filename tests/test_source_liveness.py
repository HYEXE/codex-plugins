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
        )
        self.assertEqual(report["summary"]["hash_changed"], 1)

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


if __name__ == "__main__":
    unittest.main()

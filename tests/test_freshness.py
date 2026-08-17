from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_freshness import classify_freshness  # noqa: E402


class FreshnessTests(unittest.TestCase):
    def test_fresh_warning_and_error_boundaries(self) -> None:
        today = date(2026, 8, 17)
        self.assertEqual(
            classify_freshness(
                date(2026, 5, 19), warning_after_days=90, error_after_days=180, today=today
            )[0],
            "fresh",
        )
        self.assertEqual(
            classify_freshness(
                date(2026, 5, 18), warning_after_days=90, error_after_days=180, today=today
            )[0],
            "warning",
        )
        self.assertEqual(
            classify_freshness(
                date(2026, 2, 17), warning_after_days=90, error_after_days=180, today=today
            )[0],
            "error",
        )

    def test_future_date_is_invalid(self) -> None:
        status, age = classify_freshness(
            date(2026, 8, 18),
            warning_after_days=90,
            error_after_days=180,
            today=date(2026, 8, 17),
        )
        self.assertEqual(status, "future")
        self.assertEqual(age, -1)

    def test_invalid_budget_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            classify_freshness(
                date(2026, 8, 1),
                warning_after_days=180,
                error_after_days=90,
                today=date(2026, 8, 17),
            )


if __name__ == "__main__":
    unittest.main()

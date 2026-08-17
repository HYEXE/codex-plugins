#!/usr/bin/env python3
"""Classify dated knowledge records against explicit freshness budgets."""

from __future__ import annotations

import argparse
from datetime import date


def classify_freshness(
    value: date,
    *,
    warning_after_days: int,
    error_after_days: int,
    today: date | None = None,
) -> tuple[str, int]:
    if warning_after_days < 0 or error_after_days <= warning_after_days:
        raise ValueError("freshness budget must satisfy 0 <= warning < error")
    reference = today or date.today()
    age = (reference - value).days
    if age < 0:
        return "future", age
    if age > error_after_days:
        return "error", age
    if age > warning_after_days:
        return "warning", age
    return "fresh", age


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("date", type=date.fromisoformat)
    parser.add_argument("--warning-after-days", type=int, required=True)
    parser.add_argument("--error-after-days", type=int, required=True)
    args = parser.parse_args()
    try:
        status, age = classify_freshness(
            args.date,
            warning_after_days=args.warning_after_days,
            error_after_days=args.error_after_days,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"{status}: {age} days")
    return 1 if status in {"future", "error"} else 0


if __name__ == "__main__":
    raise SystemExit(main())

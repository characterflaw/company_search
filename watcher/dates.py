"""Run-date helpers: YYYY-MM-DD plus English weekday stub (mon, tue, …)."""

from __future__ import annotations

from datetime import date


def run_stamp(run_date: str) -> str:
    """Return ``YYYY-MM-DD_dow`` (e.g. ``2026-11-24_tue``)."""
    d = date.fromisoformat(run_date)
    return f"{run_date}_{d.strftime('%a').lower()}"


def date_key_from_stem(stem: str) -> str:
    """Extract ``YYYY-MM-DD`` from ``YYYY-MM-DD`` or ``YYYY-MM-DD_dow`` stems."""
    return stem[:10]

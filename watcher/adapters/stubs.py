"""Stubs for ATS types not yet implemented."""

from __future__ import annotations

from typing import Any

from .base import Job


def fetch_jobs_unsupported(company: dict[str, Any]) -> list[Job]:
    ats = company.get("ats")
    raise NotImplementedError(
        f"{company.get('id')}: ats={ats!r} is not implemented yet; "
        "use greenhouse, rippling, or html, or add an adapter."
    )

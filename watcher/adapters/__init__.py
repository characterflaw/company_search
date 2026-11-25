"""ATS adapters."""

from __future__ import annotations

from typing import Any, Callable

from . import greenhouse, html_board, rippling, stubs
from .base import Job

AdapterFn = Callable[[dict[str, Any]], list[Job]]

ADAPTERS: dict[str, AdapterFn] = {
    "greenhouse": greenhouse.fetch_jobs,
    "rippling": rippling.fetch_jobs,
    "html": html_board.fetch_jobs,
    "lever": stubs.fetch_jobs_unsupported,
    "ashby": stubs.fetch_jobs_unsupported,
}


def fetch_company_jobs(company: dict[str, Any]) -> list[Job]:
    ats = (company.get("ats") or "").strip().lower()
    adapter = ADAPTERS.get(ats)
    if not adapter:
        raise ValueError(f"{company.get('id')}: unknown ats={ats!r}")
    return adapter(company)

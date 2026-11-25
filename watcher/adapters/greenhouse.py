"""Greenhouse job board adapter (public boards API)."""

from __future__ import annotations

from typing import Any

from .base import Job, fetch_json


def fetch_jobs(company: dict[str, Any]) -> list[Job]:
    token = company.get("board_token")
    if not token:
        raise ValueError(f"{company.get('id')}: greenhouse requires board_token")

    # Public Greenhouse API (works for most boards, including job-boards.greenhouse.io)
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    payload = fetch_json(url)
    jobs_raw = payload.get("jobs") or []

    jobs: list[Job] = []
    for item in jobs_raw:
        job_id = str(item.get("id") or item.get("absolute_url") or "")
        title = (item.get("title") or "").strip()
        absolute_url = (item.get("absolute_url") or "").strip()
        location = ""
        loc = item.get("location") or {}
        if isinstance(loc, dict):
            location = (loc.get("name") or "").strip()
        elif isinstance(loc, str):
            location = loc.strip()
        if not job_id or not title:
            continue
        jobs.append(
            Job(
                id=job_id,
                title=title,
                url=absolute_url or f"https://boards.greenhouse.io/{token}/jobs/{job_id}",
                location=location,
            )
        )
    return jobs

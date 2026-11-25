"""Generic HTML careers-page adapter (conservative link scrape)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Job, fetch_text

JOBBY_HREF = (
    "job",
    "career",
    "opening",
    "position",
    "greenhouse",
    "lever",
    "ashby",
    "workday",
    "rippling",
    "smartrecruiters",
)


def fetch_jobs(company: dict[str, Any]) -> list[Job]:
    careers_url = company.get("careers_url") or ""
    if not careers_url:
        raise ValueError(f"{company.get('id')}: html requires careers_url")

    html = fetch_text(careers_url)
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[Job] = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(" ", strip=True)
        if not text or len(text) < 3:
            continue
        href_l = href.lower()
        text_l = text.lower()
        looks_like_job = any(token in href_l for token in JOBBY_HREF) or any(
            token in text_l
            for token in (
                "qa",
                "quality assurance",
                "sdet",
                "test engineer",
                "test automation",
                "software test",
            )
        )
        if not looks_like_job:
            continue
        # Skip pure navigation
        if text_l in {"careers", "jobs", "view openings", "see all jobs", "join us"}:
            continue
        full = urljoin(careers_url, href)
        jobs.append(Job(id=full, title=text, url=full, location=""))

    seen: set[str] = set()
    out: list[Job] = []
    for job in jobs:
        if job.url in seen:
            continue
        seen.add(job.url)
        out.append(job)
    return out

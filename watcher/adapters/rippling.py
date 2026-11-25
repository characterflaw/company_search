"""Rippling ATS adapter (ats.rippling.com job boards)."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Job, fetch_text


def fetch_jobs(company: dict[str, Any]) -> list[Job]:
    careers_url = company.get("careers_url") or ""
    if not careers_url:
        raise ValueError(f"{company.get('id')}: rippling requires careers_url")

    html = fetch_text(careers_url)
    jobs = _jobs_from_embedded_json(html, careers_url)
    if jobs:
        return jobs
    return _jobs_from_anchors(html, careers_url)


def _jobs_from_embedded_json(html: str, base_url: str) -> list[Job]:
    """Try common embedded JSON patterns on Rippling boards."""
    jobs: list[Job] = []

    # Next.js / hydration style: "jobs":[...], "title":"..."
    for match in re.finditer(
        r'\{\s*"id"\s*:\s*"?(?P<id>[^",}]+)"?\s*,\s*"name"\s*:\s*"(?P<title>[^"]+)"',
        html,
    ):
        job_id = match.group("id")
        title = _unescape(match.group("title").strip())
        if title:
            jobs.append(
                Job(
                    id=job_id,
                    title=title,
                    url=urljoin(base_url, f"/jobs/{job_id}"),
                    location="",
                )
            )

    if jobs:
        return _dedupe(jobs)

    # Look for application/json script tags
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script"):
        raw = script.string or script.get_text() or ""
        if "title" not in raw or "job" not in raw.lower():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        found = _walk_for_jobs(data, base_url)
        jobs.extend(found)

    return _dedupe(jobs)


def _walk_for_jobs(node: Any, base_url: str) -> list[Job]:
    found: list[Job] = []
    if isinstance(node, dict):
        title = node.get("title") or node.get("name") or node.get("jobTitle")
        job_id = node.get("id") or node.get("uuid") or node.get("slug")
        url = node.get("url") or node.get("absolute_url") or node.get("jobUrl")
        location = ""
        loc = node.get("location") or node.get("locations")
        if isinstance(loc, str):
            location = loc
        elif isinstance(loc, dict):
            location = str(loc.get("name") or loc.get("city") or "")
        elif isinstance(loc, list) and loc:
            first = loc[0]
            if isinstance(first, dict):
                location = str(first.get("name") or "")
            else:
                location = str(first)
        if title and (job_id or url):
            jid = str(job_id or url)
            href = str(url) if url else urljoin(base_url, f"/jobs/{jid}")
            found.append(
                Job(id=jid, title=str(title).strip(), url=href, location=location)
            )
        for value in node.values():
            found.extend(_walk_for_jobs(value, base_url))
    elif isinstance(node, list):
        for item in node:
            found.extend(_walk_for_jobs(item, base_url))
    return found


def _jobs_from_anchors(html: str, base_url: str) -> list[Job]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[Job] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        if not text:
            continue
        if "/jobs/" not in href and "job" not in href.lower():
            continue
        full = urljoin(base_url, href)
        jobs.append(Job(id=full, title=text, url=full, location=""))
    return _dedupe(jobs)


def _dedupe(jobs: list[Job]) -> list[Job]:
    seen: set[str] = set()
    out: list[Job] = []
    for job in jobs:
        key = job.id or job.url
        if key in seen:
            continue
        seen.add(key)
        out.append(job)
    return out


def _unescape(text: str) -> str:
    try:
        return json.loads(f'"{text}"')
    except json.JSONDecodeError:
        return (
            text.replace("\\u0026", "&")
            .replace("&amp;", "&")
            .replace("\\/", "/")
        )

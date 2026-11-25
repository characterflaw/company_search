"""Shared types and HTTP helpers for ATS adapters."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import requests

DEFAULT_TIMEOUT = 30
USER_AGENT = (
    "qa-openings-watcher/1.0 (+local job-search; weekday careers check)"
)


@dataclass
class Job:
    id: str
    title: str
    url: str
    location: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fetch_text(url: str, *, accept: str = "text/html,application/json") -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    return response.text


def fetch_json(url: str) -> Any:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()

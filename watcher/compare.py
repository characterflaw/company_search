"""Diff current snapshot against the previous run."""

from __future__ import annotations

from typing import Any


def job_key(company_id: str, job: dict[str, Any]) -> str:
    jid = str(job.get("id") or "").strip()
    url = str(job.get("url") or "").strip()
    return f"{company_id}::{jid or url}"


def index_snapshot(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for company in snapshot.get("companies") or []:
        company_id = company.get("id") or ""
        for job in company.get("jobs") or []:
            indexed[job_key(company_id, job)] = {
                "company_id": company_id,
                "company_name": company.get("name") or company_id,
                **job,
            }
    return indexed


def compare(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    current_idx = index_snapshot(current)
    if previous is None:
        return {
            "baseline": True,
            "new": list(current_idx.values()),
            "removed": [],
            "unchanged": [],
            "errors": _errors(current),
        }

    previous_idx = index_snapshot(previous)
    current_keys = set(current_idx)
    previous_keys = set(previous_idx)

    return {
        "baseline": False,
        "new": [current_idx[k] for k in sorted(current_keys - previous_keys)],
        "removed": [previous_idx[k] for k in sorted(previous_keys - current_keys)],
        "unchanged": [current_idx[k] for k in sorted(current_keys & previous_keys)],
        "errors": _errors(current),
    }


def _errors(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for company in snapshot.get("companies") or []:
        err = company.get("error")
        if err:
            out.append(
                {
                    "company_id": company.get("id") or "",
                    "company_name": company.get("name") or "",
                    "error": str(err),
                }
            )
    return out

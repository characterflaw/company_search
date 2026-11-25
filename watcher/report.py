"""Markdown report writer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dates import run_stamp


def render_report(
    *,
    run_date: str,
    diff: dict[str, Any],
    snapshot: dict[str, Any],
) -> str:
    new = diff.get("new") or []
    removed = diff.get("removed") or []
    unchanged = diff.get("unchanged") or []
    errors = diff.get("errors") or []
    baseline = bool(diff.get("baseline"))
    stamp = run_stamp(run_date)

    lines: list[str] = [
        f"# QA openings report — {stamp}",
        "",
        f"Baseline run: **{'yes' if baseline else 'no'}**",
        "",
        "## Summary",
        "",
        f"- New: {len(new)}",
        f"- Removed: {len(removed)}",
        f"- Unchanged: {len(unchanged)}",
        f"- Fetch errors: {len(errors)}",
        "",
        "## New",
        "",
    ]
    lines.extend(_job_bullets(new) if new else ["_(none)_", ""])

    lines.extend(["## Removed", ""])
    lines.extend(_job_bullets(removed) if removed else ["_(none)_", ""])

    lines.extend(["## Unchanged", ""])
    if unchanged:
        lines.append(f"_{len(unchanged)} opening(s) still present_")
        lines.append("")
        # Abbreviated list
        for job in unchanged[:30]:
            title = job.get("title") or ""
            company = job.get("company_name") or job.get("company_id") or ""
            lines.append(f"- {company}: {title}")
        if len(unchanged) > 30:
            lines.append(f"- … and {len(unchanged) - 30} more")
        lines.append("")
    else:
        lines.extend(["_(none)_", ""])

    lines.extend(["## Fetch errors", ""])
    if errors:
        for err in errors:
            name = err.get("company_name") or err.get("company_id")
            lines.append(f"- **{name}**: {err.get('error')}")
        lines.append("")
    else:
        lines.extend(["_(none)_", ""])

    lines.extend(["## Companies checked", ""])
    for company in snapshot.get("companies") or []:
        name = company.get("name") or company.get("id")
        n = len(company.get("jobs") or [])
        status = "error" if company.get("error") else f"{n} software-QA match(es)"
        lines.append(f"- {name}: {status}")
    lines.append("")
    return "\n".join(lines)


def write_reports(
    reports_dir: Path,
    *,
    run_date: str,
    markdown: str,
) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = run_stamp(run_date)
    dated = reports_dir / f"{stamp}.md"
    latest = reports_dir / "LATEST.md"
    dated.write_text(markdown, encoding="utf-8")
    latest.write_text(markdown, encoding="utf-8")
    return dated, latest


def _job_bullets(jobs: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for job in jobs:
        company = job.get("company_name") or job.get("company_id") or ""
        title = job.get("title") or ""
        url = job.get("url") or ""
        location = job.get("location") or ""
        loc = f" — {location}" if location else ""
        if url:
            lines.append(f"- **{company}**: [{title}]({url}){loc}")
        else:
            lines.append(f"- **{company}**: {title}{loc}")
    lines.append("")
    return lines

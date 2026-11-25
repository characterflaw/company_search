#!/usr/bin/env python3
"""Weekday QA openings watcher — fetch, filter, snapshot, diff, report."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from adapters import fetch_company_jobs
from compare import compare
from dates import date_key_from_stem, run_stamp
from filter_titles import filter_jobs
from report import render_report, write_reports

ROOT = Path(__file__).resolve().parent
DEFAULT_COMPANIES = ROOT / "companies.yaml"
DEFAULT_TITLE_RULES = ROOT / "title_rules.yaml"
SNAPSHOTS = ROOT / "snapshots"
REPORTS = ROOT / "reports"


def load_companies(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    companies = data.get("companies") or []
    if not isinstance(companies, list):
        raise ValueError("companies.yaml must contain a top-level 'companies' list")
    return companies


def previous_snapshot(snapshots_dir: Path, run_date: str) -> dict[str, Any] | None:
    if not snapshots_dir.exists():
        return None
    # Prefer YYYY-MM-DD_dow.json; still accept legacy YYYY-MM-DD.json
    files = sorted(
        {
            *snapshots_dir.glob("????-??-??.json"),
            *snapshots_dir.glob("????-??-??_???.json"),
        },
        key=lambda p: p.stem,
    )
    prior = [p for p in files if date_key_from_stem(p.stem) < run_date]
    if not prior:
        return None
    return json.loads(prior[-1].read_text(encoding="utf-8"))


def build_snapshot(
    companies: list[dict[str, Any]],
    run_date: str,
    *,
    title_rules: Path | None = None,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for company in companies:
        if not company.get("enabled", True):
            continue
        entry: dict[str, Any] = {
            "id": company.get("id"),
            "name": company.get("name"),
            "careers_url": company.get("careers_url"),
            "ats": company.get("ats"),
            "jobs": [],
            "error": None,
        }
        try:
            raw_jobs = fetch_company_jobs(company)
            filtered = filter_jobs(raw_jobs, rules_path=title_rules)
            entry["jobs"] = [job.to_dict() for job in filtered]
            entry["raw_count"] = len(raw_jobs)
            entry["filtered_count"] = len(filtered)
        except Exception as exc:  # noqa: BLE001 — per-company isolation
            entry["error"] = f"{type(exc).__name__}: {exc}"
        results.append(entry)

    return {
        "run_date": run_date,
        "run_stamp": run_stamp(run_date),
        "companies": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check company boards for software QA openings")
    parser.add_argument(
        "--companies",
        type=Path,
        default=DEFAULT_COMPANIES,
        help="Path to companies.yaml",
    )
    parser.add_argument(
        "--title-rules",
        type=Path,
        default=DEFAULT_TITLE_RULES,
        help="Path to title_rules.yaml",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Run date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report to stdout; do not write snapshot/report files",
    )
    args = parser.parse_args(argv)

    companies = load_companies(args.companies)
    snapshot = build_snapshot(companies, args.date, title_rules=args.title_rules)
    previous = previous_snapshot(SNAPSHOTS, args.date)
    diff = compare(snapshot, previous)
    markdown = render_report(run_date=args.date, diff=diff, snapshot=snapshot)

    if args.dry_run:
        print(markdown)
        return 0

    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    stamp = run_stamp(args.date)
    snap_path = SNAPSHOTS / f"{stamp}.json"
    snap_path.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

    dated, latest = write_reports(REPORTS, run_date=args.date, markdown=markdown)
    print(f"Wrote {snap_path}")
    print(f"Wrote {dated}")
    print(f"Wrote {latest}")
    print(
        f"Summary: new={len(diff['new'])} removed={len(diff['removed'])} "
        f"unchanged={len(diff['unchanged'])} errors={len(diff['errors'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

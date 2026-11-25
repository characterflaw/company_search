"""Software QA title include/exclude rules (loaded from title_rules.yaml)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from adapters.base import Job

DEFAULT_RULES = Path(__file__).resolve().parent / "title_rules.yaml"


@dataclass(frozen=True)
class TitleRules:
    include: re.Pattern[str]
    exclude: re.Pattern[str]
    software_hint: re.Pattern[str]

    def matches(self, title: str) -> bool:
        if not title or not self.include.search(title):
            return False
        if self.exclude.search(title) and not self.software_hint.search(title):
            return False
        return True


def _compile_group(patterns: list[str], *, label: str) -> re.Pattern[str]:
    if not patterns:
        raise ValueError(f"title_rules.yaml: '{label}' must be a non-empty list")
    joined = "|".join(f"(?:{p})" for p in patterns)
    return re.compile(rf"\b(?:{joined})\b", re.IGNORECASE)


def load_title_rules(path: Path | None = None) -> TitleRules:
    rules_path = path or DEFAULT_RULES
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    return TitleRules(
        include=_compile_group(list(data.get("include") or []), label="include"),
        exclude=_compile_group(list(data.get("exclude") or []), label="exclude"),
        software_hint=_compile_group(
            list(data.get("software_hint") or []), label="software_hint"
        ),
    )


@lru_cache(maxsize=4)
def _cached_rules(path_str: str) -> TitleRules:
    return load_title_rules(Path(path_str))


def is_software_qa_title(title: str, *, rules_path: Path | None = None) -> bool:
    path = rules_path or DEFAULT_RULES
    return _cached_rules(str(path.resolve())).matches(title)


def filter_jobs(
    jobs: list[Job],
    *,
    rules_path: Path | None = None,
) -> list[Job]:
    path = rules_path or DEFAULT_RULES
    rules = _cached_rules(str(path.resolve()))
    return [job for job in jobs if rules.matches(job.title)]

# QA openings watcher

Weekday check of official career boards for software QA roles. Writes a JSON snapshot and a markdown diff report. No email in v1.

## Layout

```text
watcher/
  companies.yaml     # watchlist (product-agnostic)
  title_rules.yaml   # include / exclude title patterns
  check_openings.py  # entrypoint
  adapters/          # greenhouse, rippling, html (+ stubs)
  snapshots/         # YYYY-MM-DD_dow.json (e.g. 2026-11-24_tue)
  reports/           # YYYY-MM-DD_dow.md and LATEST.md
  requirements.txt
```

## Local run

```bash
cd _2026/company_search/watcher
python3 -m pip install -r requirements.txt
python3 check_openings.py --dry-run   # print report only
python3 check_openings.py             # write snapshot + report
```

Options:

- `--companies PATH` — alternate companies YAML
- `--title-rules PATH` — alternate title filter YAML
- `--date YYYY-MM-DD` — override run date (default: today)

## Add a company

Edit `companies.yaml` and append:

```yaml
  - id: example
    name: Example Co
    careers_url: https://job-boards.greenhouse.io/example
    ats: greenhouse   # greenhouse | rippling | html | lever | ashby
    board_token: example   # required for greenhouse
    enabled: true
    notes: optional
```

- Use `greenhouse` when the board is on Greenhouse (`board_token` = board slug).
- Use `rippling` for `ats.rippling.com/.../jobs`.
- Use `html` for a generic careers page (best-effort).
- `lever` / `ashby` are stubs until an adapter is added.

The tool does not filter by product type. Hardware+software, FinTech, insurance, and pure SaaS are all fine.

## Edit job title filters

Patterns live in `title_rules.yaml` (not Python). Edit that file, then re-run locally:

```bash
python3 check_openings.py --dry-run
```

Three lists (case-insensitive regex fragments; OR'd; matched with word boundaries):

| Key | Role |
| --- | --- |
| `include` | Title **must** match at least one |
| `exclude` | Soft noise (Electrical, HIL, technician, …) |
| `software_hint` | If `exclude` matched, title must also match one of these |

Examples:

```yaml
include:
  - QA
  - SDET
  - Quality\s+Engineer

exclude:
  - Electrical
  - HIL

software_hint:
  - Software
  - QA\s+Engineer
```

- Escape regex metacharacters when you mean a literal (e.g. `Q\.A\.`).
- Use `\s+` for flexible whitespace (`Quality Assurance`).
- Invalid regex fails at load time — fix the YAML and retry.
- Alternate file: `python3 check_openings.py --title-rules ./my_rules.yaml --dry-run`

## GitHub Actions

Workflow: `.github/workflows/qa-openings.yml`

- Runs weekdays at 15:00 UTC (~09:00 CT)
- Also runnable via **Actions → QA openings watcher → Run workflow**
- Commits updated `snapshots/` and `reports/` when files change

Requires this folder to live in a GitHub repo with Actions enabled. The `_job_search` tree may need `git init` / a remote before the schedule can run in the cloud.

## Reports

- `reports/LATEST.md` — most recent report
- `reports/YYYY-MM-DD_dow.md` — dated copy (`tue`, `wed`, …)
- `snapshots/YYYY-MM-DD_dow.json` — filtered openings + per-company errors

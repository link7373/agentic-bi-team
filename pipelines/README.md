# Pipelines Inventory

> **Created by Colin Beck**
> LinkedIn: https://www.linkedin.com/in/beckcolin/
> GitHub: https://github.com/link7373


> Every ETL/ELT pipeline and summary-table build the team ships. Owned by `data-engineer`
> and `analytics-engineer`; updated by `/build-pipeline` step 8. Check here before building —
> extending an existing pipeline beats duplicating one.

Each pipeline lives in `pipelines/<name>/` with a `DESIGN.md` (source → layers → target,
refresh, quality checks) and runnable checks in `pipelines/<name>/checks/`.

## Inventory

| Pipeline | Source → Target | Grain | Refresh | Schedule | Owner | Runbook |
|---|---|---|---|---|---|---|
| _(none yet — run `/build-pipeline`)_ | | | | | | |

## Failure runbook conventions

- Each pipeline's `DESIGN.md` carries its own failure/backfill runbook.
- A failed quality gate **stops downstream steps** and is reported — never silently passed
  (see `standards/sql-and-data-standards.md`).

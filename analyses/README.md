# Analyses Inventory

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> Every business question the team has investigated. Owned by `bi-analyst`;
> updated by `/analyze` and `/investigate-metric`. **Check here before starting** —
> the question may already be answered, and a prior analysis is a better starting
> point than a blank page.

Each analysis lives in `analyses/YYYY-MM-DD-short-slug/` with:

- `PLAN.md` — the decision being informed and the hypothesis tree
- the queries (`.sql`) and scripts that produced every number
- `FINDINGS.md` — the answer, with caveats, written to `standards/reporting-standards.md`

Bulk extracts are gitignored by file type; the queries and write-ups are committed,
so every reported number stays reproducible.

## Inventory

| Date | Analysis | Question / decision | Verdict | Deliverable |
|---|---|---|---|---|
| _(none yet — run `/analyze`)_ | | | | |

## Conventions

- A finding that changes how a metric is computed also goes in `knowledge/decision-log.md`.
- A question asked three times is a dashboard or a mart, not a fourth analysis —
  escalate it to `/build-dashboard` or `/build-pipeline`.

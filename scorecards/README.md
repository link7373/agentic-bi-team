# Scorecards Inventory

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> The periodic performance record. Owned by `performance-monitor`; produced by
> `/scorecard weekly` and `/scorecard monthly`. Every scorecard compares against
> the ones before it, so this folder is the team's trend memory — never delete a
> past period, even a wrong one (correct it in place with a dated note).

Files are written to `scorecards/YYYY/`:

- `weekly-YYYY-WW.md` — fixed KPI set, current vs prior vs last year vs target,
  status colours, and a narrative line for every 🟡/🔴
- `monthly-YYYY-MM.md` — the same plus the month's narrative and cost line

## Inventory

| Period | File | Reds | Headline |
|---|---|---|---|
| _(none yet — run `/scorecard weekly`)_ | | | |

## Conventions

- The KPI set is fixed by `knowledge/metrics-catalog.md`. Changing it mid-year
  breaks comparability — route changes through `metrics-steward`.
- Two consecutive reds on the same metric escalate to `/investigate-metric`.
- A metric that moved because the *data* broke is a data incident, not a business
  result — see `knowledge/incident-runbook.md`.

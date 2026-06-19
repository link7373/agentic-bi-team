# Dashboards Inventory

> Every dashboard the team ships, in any tool (Tableau / Power BI / Looker / file-based).
> Owned by `dashboard-developer`; updated by `/build-dashboard` step 7. Check here before
> building — if an existing dashboard already answers 80% of the request, extend it.

Each dashboard lives in `dashboards/<name>/` with a `SPEC.md` (audience, questions, metrics,
layout), reconciliation queries in `dashboards/<name>/checks/`, and a screenshot.
Looker projects keep LookML in `dashboards/lookml/`.

## Inventory

| Dashboard | Audience | Questions answered | Source tables | Refresh | Review by | Owner | Link |
|---|---|---|---|---|---|---|---|
| _(none yet — run `/build-dashboard`)_ | | | | | | | |

## Conventions

- Every tile reads from a mart / summary table — no heavy logic in the BI tool.
- Measure names match `knowledge/metrics-catalog.md` exactly.
- Beware the **dead-end dashboard**: a KPI that has hit target every period for months is no
  longer informative — rotate it out (see `standards/dashboard-standards.md`).

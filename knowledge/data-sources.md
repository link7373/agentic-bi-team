# Data Sources

> **Created by Colin Beck**
> LinkedIn: https://www.linkedin.com/in/beckcolin/
> GitHub: https://github.com/link7373


> The team's map of where data lives, how to reach it, and what to watch out for. Filled by `/setup-team` (with live connection tests); updated by data-engineer and analytics-engineer whenever tables are added or quirks discovered. **Never guess a table or column name — check here or introspect.**
>
> **Setting up a connection for the first time?** See the plain-English runbook in `knowledge/connections.md` (MCP vs CLI vs files, where credentials live, the no-secrets-in-git rule).

## Connection Summary

| Source | Type | How to connect (exact command/tool) | Status | Contains |
|---|---|---|---|---|
| {{SOURCE_1 e.g. "Prod replica"}} | {{TYPE e.g. Postgres}} | {{CONNECT e.g. "psql $PROD_REPLICA_URL (read-only)"}} | {{✅ tested / ❌ blocked: reason}} | {{CONTENTS e.g. "users, orders, events"}} |
| {{SOURCE_2 e.g. "Warehouse"}} | {{TYPE e.g. BigQuery}} | {{CONNECT e.g. "bq query --use_legacy_sql=false"}} | {{STATUS}} | {{CONTENTS}} |
| {{SOURCE_3 e.g. "Stripe"}} | SaaS API | {{CONNECT}} | {{STATUS}} | {{CONTENTS}} |

**Cost guardrail:** {{COST_GUARDRAIL e.g. "estimate scan size before BigQuery queries; flag anything > 100 GB" or "n/a"}}

## Warehouse Layout

- **Layers:** `raw` → `staging` → `marts` (see `standards/sql-and-data-standards.md`)
- **Scratch/dev schema for team use:** {{SCRATCH_SCHEMA e.g. "analytics_dev — pre-authorised for create/drop" or "TBD"}}

## Table Inventory

> Key tables, their grain, size, and refresh. Populated by `/setup-team` schema discovery and grown over time. Every new mart gets a row.

| Table | Layer | Grain (one row per…) | ~Rows | Refresh | Notes |
|---|---|---|---|---|---|
| {{TABLE_1}} | {{LAYER}} | {{GRAIN}} | {{ROWS}} | {{REFRESH}} | {{NOTES}} |

## Data Dictionary

> Field-level reference for the columns analysts and dashboards rely on. Owned by
> `metrics-steward` (governance) with `data-engineer`/`analytics-engineer` (accuracy).
> Metric *definitions* live in `knowledge/metrics-catalog.md`; this table documents the
> raw/mart **columns** those metrics are built from — meaning, type, unit, and gotchas.
> Add a row whenever a column's meaning isn't self-evident from its name.

| Table.column | Type | Unit / domain | Meaning | Gotchas |
|---|---|---|---|---|
| {{TABLE.COLUMN e.g. "marts.fct_orders.amount_usd"}} | {{TYPE e.g. numeric}} | {{UNIT e.g. "USD, net of refunds"}} | {{MEANING}} | {{GOTCHA e.g. "NULL for comped orders; excludes tax"}} |

## Cross-Source Join Keys

> How entities link across systems — and how reliable each link is. bi-analyst depends on this for cross-database analysis.

| Entity | Source A | Source B | Join key | Match rate / caveats |
|---|---|---|---|---|
| {{ENTITY e.g. Customer}} | {{A e.g. CRM.contacts}} | {{B e.g. billing.accounts}} | {{KEY e.g. email (lowercased)}} | {{CAVEAT e.g. "~87%; unmatched skew self-serve"}} |

## Known Quirks & Landmines

> Every hard-won lesson about this data goes here so it's learned once. Add entries with dates.

- {{QUIRK_1 e.g. "(2026-06-12) orders.amount is in cents; orders_v2.amount is in dollars."}}
- {{QUIRK_2 e.g. "Events before 2024-03 missing for mobile — tracking bug; exclude or caveat."}}

## Fields Nobody Should Trust

- {{UNTRUSTED_FIELD_1 — and why}}

## Data Freshness Expectations

| Source/table | Expected freshness | How to check |
|---|---|---|
| {{TABLE}} | {{e.g. "loaded by 06:00 daily"}} | {{e.g. "MAX(_loaded_at)"}} |

## Privacy & Access Rules

- {{DATA_PRIVACY_RULES — what may not be queried, exported, or displayed; minimum aggregation sizes; PII handling}}

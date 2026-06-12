# SQL & Data Standards

> House rules for all SQL, pipelines, and data models. Applies to every agent.

## Warehouse Layering

| Layer | Prefix/schema | Contents | Who writes | Who reads |
|---|---|---|---|---|
| `raw` | {{RAW_SCHEMA e.g. "raw_"}} | Verbatim source data + `_loaded_at`, `_source` | data-engineer only | staging only |
| `staging` | {{STAGING_SCHEMA e.g. "stg_"}} | Typed, renamed, deduped; 1 model per source entity | data-engineer | marts, engineers |
| `marts` | {{MARTS_SCHEMA e.g. "fct_ / dim_ / agg_"}} | Analytics-ready facts, dims, aggregates | analytics-engineer | everyone |
| scratch | {{SCRATCH_SCHEMA e.g. "dev_"}} | Temporary work; may be dropped anytime | anyone | owner |

Analysts and dashboards read **marts only**. Touching `raw` from an analysis is a smell — fix the mart instead.

## Naming

- Tables: `fct_<noun>` (events/transactions), `dim_<noun>` (entities), `agg_<noun>_<grain>` (e.g. `agg_revenue_daily`).
- Columns: `snake_case`; booleans `is_`/`has_`; dates `*_date`; timestamps `*_at` (UTC unless suffixed `_local`); foreign keys `<entity>_id`; money columns carry currency in name or doc (`amount_usd`).
- No reserved words, no spaces, no abbreviations that aren't in the glossary.

## SQL Style

- Readable plain SQL — no ORM. Keywords UPPERCASE, identifiers lowercase, one clause per line, leading commas or trailing commas — pick one per file and be consistent.
- CTEs over nested subqueries; name CTEs for what they contain (`active_customers`, not `t1`).
- Explicit column lists in production code — no `SELECT *` outside exploration.
- Comment the *why* (business rules, source quirks), not the *what*.
- Every model file header: purpose, grain ("one row per ___"), refresh cadence, upstream sources, owner.

## Correctness Rules

- **Declare and verify grain.** Every table has a stated grain and a uniqueness check proving it.
- **Idempotent writes.** MERGE or delete-insert by partition. Blind INSERT-append is forbidden in pipelines.
- **Point-in-time joins** for anything historical: join dimensions as-of the fact date (SCD2), not current state, unless current-state is explicitly intended and documented.
- **Timezones:** store UTC; convert to {{TIMEZONE}} only at presentation. Date boundaries for reporting use {{TIMEZONE}}.
- **Nulls are information.** Don't COALESCE to 0/'unknown' silently in models; do it at presentation with documentation.
- **Division:** always guard denominators (`NULLIF(x,0)`).
- **Dedup deliberately:** `ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC)` with the ordering rationale commented.

## Data Quality Gates (every pipeline)

1. Row reconciliation vs source (tolerance stated).
2. Key uniqueness at declared grain.
3. Null-rate thresholds on critical columns.
4. Freshness: `MAX(_loaded_at)` within expected window.
5. Optional domain checks (amounts ≥ 0, dates within sane range).

Failures stop downstream steps and get reported — never silently passed or auto-"fixed".

## Performance & Cost

- Filter on partition columns (almost always date) in every query against large tables.
- Incremental processing by default; full-history rebuilds are a deliberate, logged decision.
- Estimate before running: {{COST_GUARDRAIL e.g. "dry-run anything that might scan > 100 GB; ask the user above $X"}}.
- Repeated expensive query (>2 uses) → build an `agg_` table.

## Suppression & Privacy

- {{DATA_PRIVACY_RULES}}
- Minimum aggregation size in shared outputs: {{MIN_GROUP_SIZE e.g. "5 individuals" or "n/a"}}. Suppressed values render as `null` + "suppressed", never interpolated.

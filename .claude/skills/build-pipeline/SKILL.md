---
name: build-pipeline
description: Design and build an ETL/ELT pipeline or a summary/aggregate table — from source identification through layered transformations, data-quality gates, scheduling, and documentation. Use for new data ingestion or taming huge datasets into fast queryable tables.
---

# Build Pipeline / Summary Table

Coordinates `data-engineer` (ingestion, raw→staging) and `analytics-engineer` (marts, summary tables). Args may name the source or desired table, e.g. `/build-pipeline daily revenue summary from billing DB`.

## Procedure

1. **Scope.** Establish: What data? From where ({{SOURCE_SYSTEMS}} — see `knowledge/data-sources.md`)? Who consumes the result and at what grain/freshness? Incremental history needed or current-state only? One clarifying round max; default to daily incremental refresh at the finest grain consumers need.

2. **Check for existing work.** Search `pipelines/` and the warehouse for tables that already cover this. Extending beats duplicating.

3. **Design doc first.** Write `pipelines/<name>/DESIGN.md` (half a page): source → layers → target table(s) with grain, refresh strategy (full/incremental + watermark), schedule, quality checks, estimated volume/cost. For large or costly builds, confirm the design with the user before implementing.

4. **Implement, layer by layer** (per `standards/sql-and-data-standards.md`):
   - `raw`: verbatim landing, load metadata columns (`_loaded_at`, `_source`).
   - `staging`: typed, renamed to convention, deduplicated, one view/table per source entity.
   - `marts`/`agg`: the consumer-facing table. Header comment documents purpose, grain, refresh, owner.
   - Idempotent writes only (MERGE / delete-insert by partition). Test on a limited date range first.

5. **Quality gates.** End-of-pipeline checks that fail loudly: source-vs-target row reconciliation, key uniqueness at declared grain, null thresholds on critical columns, freshness check. Save as runnable queries in `pipelines/<name>/checks/`.

6. **Backfill** historical data if required — chunked by partition, verifying counts per chunk.

7. **Schedule** on {{ORCHESTRATOR}}; if none, document the exact command and recommended cron in the design doc.

8. **Document & hand off.** Update `pipelines/README.md` (inventory + runbook) and `knowledge/data-sources.md` (new tables, grains, quirks discovered). Tell the user: what was built, sample of the output, refresh schedule, and cost/runtime observed.

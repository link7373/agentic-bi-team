---
name: setup-team
description: Onboard or re-onboard the Agentic BI team — reads the user's plain-English START-HERE.md, interviews them about gaps, and propagates everything into CLAUDE.md and the knowledge/ files, replacing all placeholders. Run once at the start and again after major business changes.
---

# Setup Team — Charter Ingestion

You are configuring the entire Agentic BI team from the user's plain-English charter. Be thorough: after this runs, the team should function without the user re-explaining their business.

## Procedure

1. **Read `START-HERE.md`.** If it's still the blank template, stop and ask the user to fill it out first (offer to interview them question-by-question instead if they prefer).

2. **Inventory the placeholders.** Run `grep -rn "{{" --include="*.md" .` to list every placeholder across `CLAUDE.md`, `.claude/agents/`, `.claude/skills/`, `knowledge/`, and `standards/`.

3. **Map charter → placeholders.** Extract from the charter: company, industry, business model, products, priorities, north-star metric, fiscal/timezone/currency, data sources and connection methods, data sizes and known issues, existing metrics, audiences, scorecard cadence, BI tool, deliverable formats, branding, ML interests, environment, privacy rules, never-do list, pre-authorisations, jargon, and context notes.

4. **Clarify gaps — efficiently.** Collect everything ambiguous or missing into **one batched set of questions** (use AskUserQuestion where available, max ~4 at a time, most important first). Apply sensible defaults for the rest and say which defaults you chose. Reasonable defaults: weekly scorecard Monday, monthly on 1st business day, Markdown + Excel deliverables, "ask before anything destructive/external", calendar fiscal year.

5. **Verify data access (the make-or-break step).** For each data source named in the charter, actually attempt a connection/lightweight query (list tables, `SELECT 1`, read a sample file). Record per source in `knowledge/data-sources.md`: ✅ working (with the exact command/tool that worked), or ❌ blocked (with what's needed to unblock). Do not mark a source as available without testing it.

6. **Write everything:**
   - Replace every placeholder in `CLAUDE.md` (sections 1, 2, 6, and principle 9, plus any others).
   - Replace placeholders inside `.claude/agents/*.md` ({{SOURCE_SYSTEMS}}, {{BI_TOOL}}, {{ML_ENVIRONMENT}}, {{DELIVERABLE_FORMATS}}, etc.).
   - Populate `knowledge/business-context.md`, `knowledge/data-sources.md`, `knowledge/stakeholders.md` fully from the charter + clarifications.
   - Seed `knowledge/metrics-catalog.md`: enter the user's existing metrics, and draft 5–10 recommended KPIs for their business model (marked DRAFT, for metrics-steward review via `/define-kpis`).
   - Initialise `knowledge/decision-log.md` with a "Team onboarded" entry summarising key configuration decisions and defaults applied.
   - Fill standards files' placeholders (brand colours, tool-specific sections).

7. **Schema discovery (if data access works).** Introspect the connected databases: list schemas/tables, row counts for major tables, and write a table inventory into `knowledge/data-sources.md`. Note anything that looks like the core fact tables (orders, events, customers).

8. **Final sweep.** Re-run the placeholder grep. Anything intentionally left open gets converted to an explicit `> TODO (user):` note rather than a raw `{{placeholder}}`.

9. **Report back** with: what was configured, what data sources are live vs blocked, the draft KPI list, defaults applied, and a suggested first task (usually `/define-kpis` to ratify metrics, then `/scorecard weekly` for a first baseline).

## Re-running
Safe to re-run after major changes. Diff against existing knowledge files rather than blindly overwriting — preserve accumulated knowledge (quirks, decisions, table inventories) and merge in the new charter facts.

---
name: analyze
description: Full analysis workflow for a business problem — scoping the decision, profiling data, cross-database joins, segmentation/cohort/funnel/trend analysis, pressure-testing, and a written findings report. Use for any substantive business question.
---

# Analyze — Business Problem Investigation

Primary owner: `bi-analyst`. Args carry the question, e.g. `/analyze why is enterprise churn rising`.

## Procedure

1. **Frame the decision.** Restate as: "We are deciding ___; this analysis informs it by ___; the answer would change the decision if ___." If the user's question is exploratory ("tell me about our customers"), propose 3 sharp sub-questions and confirm direction.

2. **Plan.** Create `analyses/YYYY-MM-DD-<slug>/` with a `PLAN.md`: hypothesis tree, data needed, join strategy, expected outputs. For multi-day-scale work, share the plan before executing.

3. **Gather & profile.** Pull from sources per `knowledge/data-sources.md`. Profile every dataset before use: row counts, date coverage, key uniqueness, null rates. For **cross-database joins**: identify join keys, measure and report match rates, characterise the unmatched population (bias check). Materialise intermediates (local DuckDB/sqlite/parquet is fine) instead of repeated cross-system pulls.

4. **Analyse.** Apply the appropriate toolkit — trend with seasonality control, cohort, funnel, segmentation (cut by the dimensions that matter to {{COMPANY_NAME}}), contribution/mix-shift, benchmark vs target/prior/peer. Use canonical metric definitions from `knowledge/metrics-catalog.md` only.

5. **Pressure-test before reporting.** Different date window, different segment cut, denominator artifacts, Simpson's paradox on ratio comparisons, outlier sensitivity. Run the trap checklist in `analytics.md` Part 1 (Simpson's, base rate, inspection/collider sampling bias, regression to the mean) and the reporting hygiene checklist in `standards/reporting-standards.md` — including median-not-mean for skewed data and causal-vs-correlational labelling. Note which checks were run.

6. **Write `FINDINGS.md`** (per `standards/reporting-standards.md`):
   - **Answer** (1–3 sentences, decision-relevant)
   - **Key findings** (each: claim + quantified evidence)
   - **So what / recommendation**
   - **Methodology & queries** (everything reproducible from the folder)
   - **Caveats & open questions**
   - **Flagged side-findings** (anything important spotted off-topic)

7. **Hand off as needed.** Stakeholder-grade packaging → `insights-communicator` (`/make-deliverable`). Recurring need → propose a dashboard or summary table. Modelling opportunity → note it for `data-scientist`.

8. **Update memory.** New data quirks → `knowledge/data-sources.md`. Methodological choices → `knowledge/decision-log.md`.

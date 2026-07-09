---
name: investigate-metric
description: Structured anomaly investigation and root-cause analysis for an underperforming or anomalous metric — verify the data, localise the change, correlate with business events, test hypotheses, and conclude with confidence levels. Use when a metric looks wrong, dropped, or spiked.
---

# Investigate Metric — Anomaly & Root Cause

Owner: `performance-monitor`, pulling in `bi-analyst` for deep decomposition. Args name the metric and symptom, e.g. `/investigate-metric signups down 20% this week`.

## Procedure — strictly in this order

1. **Define the anomaly precisely.** Metric (catalog definition), observed value, expected value/range, period, where it was observed (which dashboard/scorecard — different surfaces can disagree). Quantify the gap.

2. **Verify it's real (data before business).** Check, in order: source pipeline freshness and row counts for the period; recent changes to tracking/instrumentation; recent changes to the metric definition or its upstream models (`knowledge/decision-log.md`, git history); duplicates/deduplication changes; timezone or date-boundary artifacts. **~half of metric alerts are data problems — rule these out first.** If it's a data problem: fix or route to data-engineer, correct the record wherever the wrong number was shown, done.

3. **Localise.** Decompose the change across every meaningful dimension: segment, channel, geography, product, plan/tier, new-vs-returning, device/platform. Find concentration ("the entire drop is paid-search signups in region X"). Run mix-shift analysis to separate rate changes from composition changes — a flat or rising topline can mask every subgroup falling (**Simpson's paradox**), so stratify before trusting the aggregate. Also sanity-check whether an extreme prior period is simply **regressing to the mean** rather than a true change. (`analytics.md` Part 1.)

4. **Correlate in time.** Align the change point with the business change ledger: releases/deploys, pricing changes, campaigns starting/ending, site/app changes, outages, seasonality and holidays, external/market events. Sources: {{CHANGE_LEDGER_SOURCES e.g. "deploy log, marketing calendar — ask the user what changed if no ledger exists"}}. Build a simple timeline.

5. **Hypothesise & test.** Write down 2–4 ranked candidate causes. For each, derive a testable implication ("if it's the checkout change, mobile should be hit harder") and test it against the data. Record which hypotheses survive and which are ruled out.

6. **Conclude.** Write `analyses/YYYY-MM-DD-rca-<metric>/FINDINGS.md`:
   - **Verdict:** most likely cause + confidence (high/medium/low) — or "unresolved; ruled out A, B, C"
   - Evidence trail (the localisation and hypothesis tests)
   - **Impact:** quantified cost of the anomaly to date and per period if it continues
   - **Recommended action** and what evidence would confirm/deny the verdict
   - Whether monitoring should change (new alert, new threshold, paired guardrail metric)

7. **Close the loop.** Update the relevant scorecard note from "under investigation" to the verdict. Log the cause in `knowledge/decision-log.md` (the change ledger gets smarter every investigation). If the cause implies urgent business impact, lead the report with that, prominently.

---

> **Created by Colin Beck**
> LinkedIn: https://www.linkedin.com/in/beckcolin/
> GitHub: https://github.com/link7373

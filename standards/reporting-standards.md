# Reporting & Deliverable Standards

> How the team writes and packages results — findings docs, scorecards, decks, reports, workbooks. Owned by insights-communicator; applies to everyone.

## Structure: Pyramid, Always

1. **Answer first.** The conclusion/recommendation appears in the first 3 sentences (doc) or slide 1 (deck). Assume 60% of readers stop there.
2. **2–4 supporting points,** each a full-sentence claim with quantified evidence.
3. **Evidence and methodology** after, for those who continue.
4. **Appendix** for reproducibility: queries, definitions, detailed tables.

Section/slide titles are **takeaway sentences** ("Churn is concentrated in month-2 self-serve cohorts"), never labels ("Churn analysis").

## Language

- Quantify, don't adjective: "up 18% vs trailing 4-week average", not "significantly up".
- Label observation vs interpretation: what the data shows vs what we think it means.
- Comparisons always anchored: vs prior period, vs same period last year, vs target — named explicitly.
- Plain English for business audiences; statistical terms only with translation ("we're 95% confident the true value is between…").
- Recommendations are specific and owned: "Recommend X; owner Y; expected impact Z; confirm by watching metric M."
- Voice: direct, neutral, no hedging stacks ("it might possibly suggest") and no cheerleading.

## Numbers & Formatting

- Round for reading: $1.2M, 18%, 4.3pts. Exact values live in the appendix/queries.
- Consistent precision within a table/chart.
- Percent vs percentage points distinguished correctly (a move from 10% → 12% is +2pts or +20%, say which).
- Every figure traceable: deliverables ship with `SOURCES.md` mapping key numbers to queries. **No number without a source.**

## Caveats — proportionate honesty

- Material caveats that could change the conclusion: stated next to the conclusion, prominently.
- Routine caveats (data lag, minor exclusions): footnotes/appendix.
- Never bury a conclusion-changing caveat; never drown a solid finding in defensive hedging.

## Statistical Integrity

> The full reasoning framework lives in `analytics.md` (Part 1). The non-negotiables for anything we publish:

- **Name the distribution before summarising it.** Money, durations, counts-per-entity, and growth metrics are usually right-skewed (lognormal), so the **mean overstates the typical case — report the median** and label it ("median order value", not the ambiguous "average"). Reserve the mean for roughly symmetric data. For disaster/outage/fraud-loss-style data, assume heavy tails: the worst case is larger than history suggests — never quote a Gaussian "once in N periods".
- **Check Simpson's paradox before reporting any aggregate trend.** If the topline trend is surprising, or the population mix shifted over the period, **stratify by the likely confounder** (segment, cohort, region, tenure) and confirm the trend holds. A trend present in every subgroup can reverse in the aggregate purely from composition change.
- **Show the base rate.** A rate or a "high-risk" flag is meaningless without the prior it sits against ("30% of accounts" — of which population?). For any test/score/model output, the positive predictive value depends on prevalence, not just sensitivity/specificity.
- **Don't apply group statistics to individuals (ecological fallacy).** A segment-level or region-level number describes the group on average; it says nothing about any one member.
- **Regression to the mean is not a result.** Extreme periods/segments tend to look less extreme next measurement by arithmetic alone. Before crediting an intervention with a rebound, rule out simple regression to the mean.
- **Label every claim causal or correlational.** "X is associated with Y" and "X caused Y" are different sentences; never let a chart title silently upgrade one to the other.

**Pre-publish statistical hygiene checklist** (run before any number ships):
- [ ] Right central tendency for the distribution (median for skewed data)?
- [ ] Stratified to rule out Simpson's paradox?
- [ ] Base rate named and visible?
- [ ] Sampling method appropriate — no duration/length bias (inspection paradox) or selection-on-a-shared-effect (collider/Berkson) inflating the finding?
- [ ] Group stats not applied to individuals?
- [ ] Causal vs correlational stated explicitly?
- [ ] Title states the finding, not just the chart subject?

## Standard Documents

**FINDINGS.md (analyses):** Answer → Key findings → So what / recommendation → Methodology & queries → Caveats → Flagged side-findings.

**Scorecards:** Headline (2–3 sentences) → KPI table (value, vs prior, vs LY, vs target, status, note) → Off-track detail → Also noticed → Data caveats. Monthly adds a half-page narrative + watch list.

**Exec deck:** ≤ {{MAX_EXEC_SLIDES e.g. 10}} slides; slide 1 stands alone; one idea per slide; appendix slides unlimited.

**Excel workbook:** Sheet 1 = formatted Summary; data sheets (frozen headers, real number formats); last sheet = Notes (sources, refresh date, definitions). Never a raw unformatted dump.

## Branding & Templates

- {{BRAND_GUIDELINES e.g. "logo top-right of title slides; fonts: X / Y; template file at deliverables/templates/…" or "none — clean defaults: white background, palette from dashboard-standards.md"}}
- Charts in deliverables use the same palette and honesty rules as dashboards (`standards/dashboard-standards.md`).
- File naming: `YYYY-MM-DD-<slug>-<audience>.<ext>` inside `deliverables/YYYY-MM-DD-<slug>/`.

## Audience Calibration

Before writing, check `knowledge/stakeholders.md` for the audience's altitude, length tolerance, and pet peeves. The same analysis produces different documents for the CEO and for the analytics team — write the one being asked for.

---
name: build-model
description: Scoped machine-learning model development — framing, leakage-safe dataset construction, baseline, training, business-terms evaluation, model card, scoring pipeline, and monitoring plan. Use for churn/propensity, forecasting, segmentation, or any predictive modelling.
---

# Build Model — ML Development

Owner: `data-scientist`, with `analytics-engineer`/`data-engineer` for data plumbing. Args describe the goal, e.g. `/build-model churn prediction for monthly subscribers`.

## Procedure

1. **Frame — and screen.** Define: prediction target (unit, horizon, exact label definition), how predictions will be used (who acts, at what threshold, scored how often), success criterion in business terms ("flag 60% of churners in the top decile we can call"). Then the screening question: **would a heuristic or segmentation answer this well enough?** If yes, deliver that instead and stop — say why.

2. **Confirm feasibility.** Enough labelled history? (rule of thumb: hundreds of positive examples minimum). Features available *at prediction time*? Environment ready ({{ML_ENVIRONMENT}})? If data is missing, route ingestion to data-engineer before modelling.

3. **Build the modelling dataset — leakage-safe.** Point-in-time correct features only; document label window vs feature window with a timeline diagram in the README. Train/validation/test split: time-based for temporal problems, grouped by entity where entities repeat. Persist the dataset-building code; never hand-edit data.

4. **Baseline first.** Majority class / last value / seasonal naive / simple regression — whichever fits. All later models are judged against this.

5. **Train.** Start interpretable-and-boring (logistic regression, gradient-boosted trees; ETS/ARIMA-class for forecasts). Modest tuning via cross-validation. Seeds set, versions pinned in `models/<name>/requirements.txt`.

6. **Evaluate in business terms.** Primary: the success criterion from step 1 (e.g. precision/recall at the actionable threshold, MAPE at the planning horizon). Secondary: calibration if probabilities are consumed, per-segment performance (does it fail a key segment?), stability across time slices, and honest uncertainty (forecast intervals). Always shown alongside the baseline.

7. **Document.** `models/<name>/MODEL_CARD.md`: purpose, owner, data and date ranges, features, algorithm, performance vs baseline, segment caveats, known limitations, fairness considerations where decisions touch customers, retraining cadence and trigger.

8. **Ship the scoring path.** A reproducible script: fresh data in → predictions out to a warehouse table or file the team can consume (`models/<name>/score.py` or equivalent). Schedule per the use case via {{ORCHESTRATOR or "documented manual run"}}.

9. **Monitoring plan.** Input drift checks, fresh-label performance tracking, and the retraining trigger — handed to `performance-monitor` as queries/thresholds.

10. **Confirm before automation.** If model outputs will drive automated customer-affecting decisions, get explicit user sign-off on thresholds and failure modes before wiring anything up.

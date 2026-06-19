# Experiments Inventory

> Every A/B test and controlled experiment the team designs or reads out. Owned by
> `data-scientist`; created and updated by `/experiment`. Check here before designing —
> a prior experiment on the same surface often answers the question or sets the baseline.

Each experiment lives in `experiments/YYYY-MM-DD-<slug>/` with a `DESIGN.md` (hypothesis,
primary metric from the catalog, unit of randomisation, power analysis, guardrails) and,
after the readout, a `RESULTS.md` (effect size + CI, SRM check, decision).

## Inventory

| Experiment | Hypothesis | Primary metric | Unit | Status | Decision | Owner |
|---|---|---|---|---|---|---|
| _(none yet — run `/experiment`)_ | | | | | | |

## Conventions

- Pre-register the **primary metric** (from `knowledge/metrics-catalog.md`) and guardrails
  **before** launch. No peeking-based conclusions.
- Check **sample ratio mismatch (SRM)** before trusting any result.
- Report **effect size with a confidence interval**, not just "significant / not".
- Respect the **fairness impossibility** and base-rate framing from `analytics.md` Part 1
  when results inform customer-affecting decisions.

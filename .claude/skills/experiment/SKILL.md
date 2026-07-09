---
name: experiment
description: Design or read out a controlled experiment (A/B test) — hypothesis, power analysis, pre-registered primary metric, guardrails, randomisation unit, then sample-ratio and effect-size analysis with a clear ship/no-ship decision. Use to plan a test before launch or to analyse one after it ends.
---

# Experiment — A/B Test Design & Readout

Owner: `data-scientist`, with `metrics-steward` on metric definitions and `analytics-engineer`
for the analysis dataset. Args name the test and mode, e.g. `/experiment design new checkout flow`
or `/experiment readout pricing-page test`.

This skill has two modes. **Design** runs before launch; **Readout** runs after the test ends.
Default to design if no results exist yet.

## Mode A — Design (before launch)

1. **Frame the decision.** What ships if it wins? What's the cost of a false positive? If the
   answer doesn't change a decision, an experiment may be overkill — say so.

2. **State the hypothesis** as a directional, testable claim: "Changing X will increase
   [primary metric] by at least [MDE] for [population]." The **minimum detectable effect (MDE)**
   is the smallest change worth shipping, set with the business — not whatever turns out
   significant.

3. **Pick the primary metric — one — from `knowledge/metrics-catalog.md`.** Pre-register it.
   Add 1–3 **guardrail metrics** (things that must not get worse: latency, refunds, churn).
   Picking the winner after the fact from many metrics is how teams ship noise.

4. **Choose the unit of randomisation** (user, account, session, cluster) and confirm the
   analysis unit matches it. Mismatch (e.g. randomise by user, analyse by session) breaks the
   statistics. Watch for cross-unit contamination/network effects.

5. **Power analysis.** Compute required sample size and run duration from: baseline rate (from
   the catalog/marts), MDE, significance level (default α=0.05), and power (default 80%). State
   the assumptions. If the required duration is implausible, the MDE is too small — renegotiate,
   don't peek early.

6. **Write `experiments/YYYY-MM-DD-<slug>/DESIGN.md`:** hypothesis, primary + guardrail metrics
   (with catalog links), randomisation unit, MDE, sample size, planned duration, stop rules, and
   what decision each outcome triggers. For high-stakes or customer-affecting tests, confirm the
   design with the user before launch. Add a row to `experiments/README.md`.

## Mode B — Readout (after the test ends)

1. **Check sample ratio mismatch (SRM) first.** If the actual split deviates from the intended
   allocation beyond chance, the assignment is broken — **stop and diagnose; do not interpret
   the result.**

2. **Profile the data** per `standards/sql-and-data-standards.md`: exposure counts per arm,
   date coverage, dedup at the randomisation unit, exclusions (and why).

3. **Estimate the effect** on the pre-registered primary metric: point estimate **with a
   confidence interval**, at the randomisation unit. Report effect size in business terms, not
   just a p-value. Check every guardrail metric.

4. **Pressure-test** (run the `analytics.md` Part 1 traps): no peeking-based early calls;
   segment heterogeneity (does one segment drive it — Simpson's paradox?); novelty/primacy
   effects; outlier sensitivity on skewed metrics (report robust/median where the metric is
   heavy-tailed). Distinguish "no effect" from "underpowered."
   - **Incremental effect, not just averages.** The treated-vs-control gap *is* the causal lift — the raw treated rate is not. When the effect varies across segments, that heterogeneity is the seed of **uplift modelling**: the clean control group lets `data-scientist` model *who is persuadable* (largest incremental effect) so future targeting spends only where the treatment actually moves the needle.

5. **Decide and write `experiments/YYYY-MM-DD-<slug>/RESULTS.md`:**
   - **Verdict:** ship / don't ship / inconclusive — with the effect estimate + CI and a
     confidence level.
   - Guardrail check, segment notes, and any caveats that change the conclusion.
   - **Impact if shipped** (quantified) and what to monitor post-launch (hand to
     `performance-monitor`).
   - For customer-affecting decisions, note the **fairness trade-off** explicitly (`analytics.md`
     Part 1) — equal error rates and equal predictive value can't both hold when base rates differ.

6. **Close the loop.** Update `experiments/README.md` with the decision, log the ruling in
   `knowledge/decision-log.md`, and if the test changed a metric's interpretation, route it to
   `metrics-steward`.

---

> **Created by Colin Beck**
> LinkedIn: https://www.linkedin.com/in/beckcolin/
> GitHub: https://github.com/link7373

# Models Inventory

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> Every predictive model the team has built. Owned by `data-scientist`; produced
> by `/build-model`. Check here before building — a retrained existing model beats
> a new one, and a model already in production has monitoring attached to it.

Each model lives in `models/<name>/` with:

- `MODEL_CARD.md` — purpose, training data and window, features, evaluation in
  business terms, known limitations, fairness notes, and the decision it informs
- training and scoring scripts, with the point-in-time dataset query
- `evaluation/` — held-out results, calibration, and segment-level performance

## Inventory

| Model | Predicts | Trained on | Baseline vs model | Status | Owner | Retrain due |
|---|---|---|---|---|---|---|
| _(none yet — run `/build-model`)_ | | | | | | |

## Conventions

- No model ships without a baseline it beats and a `MODEL_CARD.md`.
- A model in production is monitored for drift by `performance-monitor`; a model
  nobody acts on gets retired, not retrained.
- Scores are translated into base-rate terms before they reach a stakeholder
  (see `analytics.md` Part 1).

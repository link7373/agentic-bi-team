# Metrics Catalog

> **The single source of truth for every metric.** Owned by metrics-steward. No metric appears on a dashboard, scorecard, or deliverable unless it's defined here, and it is computed exactly as defined here. Changing an in-use definition is a breaking change — version it (see `/define-kpis` step 7).

## Metric Tree

```
North star: {{NORTH_STAR_METRIC}}
├── Driver 1: {{DRIVER_KPI_1}}        ← because {{CAUSAL_LOGIC_1}}
├── Driver 2: {{DRIVER_KPI_2}}        ← because {{CAUSAL_LOGIC_2}}
├── Driver 3: {{DRIVER_KPI_3}}        ← because {{CAUSAL_LOGIC_3}}
└── ...
    └── Input metrics listed under each driver's entry below
```

## Scorecard KPI Set

> The fixed set reported in `/scorecard`. Changes go through metrics-steward + user sign-off.

| Metric | Cadence | Target | 🟢 | 🟡 | 🔴 |
|---|---|---|---|---|---|
| {{KPI_1}} | weekly + monthly | {{TARGET}} | {{GREEN_RULE}} | {{YELLOW_RULE}} | {{RED_RULE}} |

---

## Metric Definitions

> One entry per metric, using the full template. A stranger must be able to compute the metric from the entry alone.

### {{METRIC_NAME e.g. "Active Customers"}}

- **Status:** {{DRAFT | RATIFIED}} (v{{1}}, {{DATE}})
- **Plain-English definition:** {{e.g. "Customers with ≥1 qualifying action in the trailing 30 days."}}
- **Exact formula:** {{e.g. "COUNT(DISTINCT customer_id) FROM marts.fct_activity WHERE activity_date >= CURRENT_DATE - 30 AND action_type IN ('core_a','core_b')"}}
- **Source table/model:** {{TABLE}}
- **Grain / valid segments:** {{e.g. "daily snapshot; valid by plan, region; NOT valid by device (activity not device-attributed)"}}
- **Owner (business):** {{WHO}}
- **Target / benchmark:** {{VALUE + source, e.g. "industry median X% (source, date)"}}
- **Counter-metric (anti-gaming guardrail):** {{METRIC or "n/a — not gameable"}}
- **Known limitations:** {{e.g. "excludes API-only usage"}}
- **Change history:** {{DATE: created}}

### {{METRIC_NAME_2}}

- (same template)

---

## Deprecated / Renamed Metrics

| Old name | Replaced by | Date | Why |
|---|---|---|---|
| {{OLD}} | {{NEW}} | {{DATE}} | {{REASON}} |

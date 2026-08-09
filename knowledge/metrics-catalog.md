# Metrics Catalog

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> **The single source of truth for every metric.** Owned by metrics-steward. No metric appears on a dashboard, scorecard, or deliverable unless it's defined here, and it is computed exactly as defined here. Changing an in-use definition is a breaking change — version it (see `/define-kpis` step 7).
>
> Every entry carries a fenced `yaml` block so the definition is machine-checkable as well as readable. Run `python scripts/check_metrics.py` after editing: it verifies the required keys, that names are unique, and that every metric named in a scorecard or dashboard spec actually exists here. Prose alone drifts — this is what keeps "computed in exactly one place" true rather than aspirational.

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
> Every name here must match a `name:` in a definition block below — `check_metrics.py`
> enforces it, because a scorecard line with no definition behind it is exactly how two
> dashboards start disagreeing.

| Metric | Cadence | Target | 🟢 | 🟡 | 🔴 |
|---|---|---|---|---|---|
| {{KPI_1}} | weekly + monthly | {{TARGET}} | {{GREEN_RULE}} | {{YELLOW_RULE}} | {{RED_RULE}} |

---

## Metric Definitions

> One entry per metric. A stranger must be able to compute the metric from the entry alone.
>
> **The YAML block is required.** Keys `name`, `definition`, `grain`, `owner`, and
> `generic_sql` must be present. `generic_sql: TODO` is acceptable while a source table is
> unconfirmed — and honest; inventing SQL against tables you haven't verified is not.
> Tool-specific keys (`dax`, `lookml`) are optional and only read when `{{BI_TOOL}}` matches,
> so the catalog stays portable if the BI tool changes.

<!-- TEMPLATE — copy this whole block for each new metric:

### Metric Name

```yaml
name: Metric Name
status: draft            # draft | ratified | deprecated
version: 1
definition: One plain-English sentence a non-analyst can act on.
grain: what one row means, and the time grain it is reported at
owner: the business owner's role
source_tables: [marts.fct_something]
generic_sql: |
  SELECT COUNT(DISTINCT customer_id)
  FROM marts.fct_activity
  WHERE activity_date >= CURRENT_DATE - 30
counter_metric: the guardrail that stops this being gamed, or "n/a"
valid_segments: [plan, region]
limitations: what this number does not capture
updated: YYYY-MM-DD
```

- **Why it matters / what decision it informs:** the action someone takes because of this
- **Target / benchmark:** value, with its source and date
- **Not valid by:** segment — why, e.g. "activity is not device-attributed"
- **Change history:** date — what changed, and the restatement impact

-->

### {{METRIC_NAME e.g. "Active Customers"}}

```yaml
name: {{METRIC_NAME}}
status: draft
version: 1
definition: {{one plain-English sentence a non-analyst can act on}}
grain: {{e.g. "daily snapshot, reported weekly"}}
owner: {{role}}
source_tables: [{{TABLE_1}}]
generic_sql: TODO
counter_metric: {{the guardrail, or "n/a — not gameable"}}
valid_segments: []
limitations: {{what this number does not capture}}
updated: {{date}}
```

- **Why it matters / what decision it informs:** {{the action someone takes}}
- **Target / benchmark:** {{value + source, e.g. "industry median X% (source, date)"}}
- **Not valid by:** {{segment}} — {{why, e.g. "activity is not device-attributed"}}
- **Change history:** {{date — created}}

### {{METRIC_NAME_2}}

```yaml
name: {{METRIC_NAME_2}}
status: draft
version: 1
definition: {{one plain-English sentence}}
grain: {{grain}}
owner: {{role}}
source_tables: []
generic_sql: TODO
updated: {{date}}
```

- (same template as above)

---

## Deprecated / Renamed Metrics

> Never delete a metric entry — a deleted definition turns every report that used it into
> a mystery. Mark it deprecated, say what replaced it, and leave it in place.

| Old name | Replaced by | Date | Why |
|---|---|---|---|
| {{OLD}} | {{NEW}} | {{date}} | {{reason}} |

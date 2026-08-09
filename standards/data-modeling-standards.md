# Data Modeling Standards

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/


> How the team designs warehouse models — dimensional modeling rules for facts, dimensions, and marts. Owned by analytics-engineer; data-engineer applies the staging/SCD mechanics. Read alongside `standards/sql-and-data-standards.md`.

## The four-step design process

Every new mart starts here, in this order — each step constrains the next:

1. **Select the business process.** The real-world activity that produces measurements (orders placed, sessions started, tickets resolved). One process → one fact table. Model processes, not departments or reports.
2. **Declare the grain.** State exactly what one row means ("one row per order line", "one row per user per day") *before* choosing any column. Every later decision follows from the grain. Default to the **atomic (finest) grain** — it answers questions nobody has asked yet; aggregates are built on top, never as a replacement.
3. **Identify the dimensions.** The descriptive context the process is sliced by — the who / what / where / when / how.
4. **Identify the facts.** The numeric measurements the process produces, every one true to the declared grain.

## Grain discipline

- One grain per fact table — **never mix grains** in the same table.
- Put the grain in the model header (`-- grain: one row per ___`) and prove it with a uniqueness test on the grain key.
- Resist pre-aggregating away a dimension people filter on. Storing the atomic grain is cheaper than rebuilding history when the coarse grain proves too coarse.

## Fact tables

Pick the fact type that matches the process:

| Type | One row per | Use for |
|---|---|---|
| **Transaction** | event, at the moment it occurs | most measurement; the flexible default |
| **Periodic snapshot** | entity × regular interval (daily, weekly) | levels/state over time (balances, active counts) |
| **Accumulating snapshot** | pipeline instance, updated as it progresses | lifecycle latency (order → ship → deliver); one date column per milestone |
| **Factless** | occurrence of an event/condition, no measure | counting events or coverage (attendance, eligibility) |

Rules:
- Facts are numeric and, wherever possible, **additive** across all dimensions. Flag **semi-additive** measures (balances: additive over everything *except* time — average or take last over time) and **non-additive** ones (ratios/percentages: store the **numerator and denominator** as additive facts and compute the ratio at query time — **never average a ratio**).
- Store raw additive measures, not pre-computed ratios.
- A null *fact* is allowed (no measurement taken); a null *foreign key* is not — point it at a dimension row meaning "unknown / not applicable".

## Dimensions

- **Surrogate keys.** Every dimension's primary key is a warehouse-generated integer; the source's natural/business key is kept as an attribute. Facts join on surrogate keys. This decouples the warehouse from source-key churn and is what makes history (SCD Type 2) possible.
- **Wide, verbose, denormalized.** Spend columns to make filtering and labelling human-readable. Prefer a flat **star** (denormalized) over a **snowflake**; snowflake only when a sub-hierarchy is large and genuinely reused.
- **Degenerate dimensions:** identifiers with no attributes (order number, invoice id) stay on the fact table — no separate dimension.
- **Junk dimensions:** collapse scattered low-cardinality flags/indicators into one small dimension instead of many boolean columns on the fact.
- **Role-playing dimensions:** one physical dimension referenced in several roles (a date dimension used as order_date and ship_date) — expose as views with role-specific column names.
- **Conformed dimensions:** one `dim_customer`, one `dim_date`, one `dim_product`, used identically across every fact and mart. This is what enables cross-process ("drill-across") analysis. **Never fork a second, subtly different version of a shared dimension** — that is the root cause of "why do these two reports disagree?".
- **Calendar/date dimension:** always model a real date dimension table (not raw date columns) carrying fiscal periods ({{FISCAL_YEAR_START}}), weekday/holiday flags, and period labels. Every fact carries a date foreign key.

## Slowly changing dimensions (SCD)

When a dimension attribute can change (customer tier, plan, region, owner), choose the handling **per attribute** and record it in the model header and `knowledge/decision-log.md`:

| Type | Behaviour | When |
|---|---|---|
| **0 — retain** | value never changes | true constants (original signup date) |
| **1 — overwrite** | keep current value only, no history | history doesn't matter |
| **2 — add new row** | new surrogate key per change, with `effective_from` / `effective_to` + current flag | **default when history matters** |
| **3 — add attribute** | keep a "previous" column beside "current" | one alternate view, limited history |
| **4 — mini-dimension** | split fast-changing attributes into their own small dimension | rapidly-changing attributes |
| **5/6/7 — hybrid** | combine current + historical views on the same dimension | when both "as-was" and "as-is" reporting are required — document explicitly |

Default: **Type 2** for attributes whose history matters, **Type 1** otherwise. The point-in-time joins required by `standards/sql-and-data-standards.md` depend on Type 2 being in place — join the fact to the dimension row valid **as-of the fact date**, not the current row.

## The bus matrix (planning for conformance)

Before building marts across domains, sketch the **bus matrix**: rows = business processes (fact tables), columns = conformed dimensions; tick which dimensions each process shares. It is the map that keeps dimensions conformed and sets a sane build order — deliver one process at a time while reusing the shared dimensions. Keep the current matrix in `knowledge/data-sources.md`.

## Aggregates

- `agg_*` tables are a **performance layer** built from atomic facts, never a substitute for them. Same conformed dimensions, coarser grain.
- Document each aggregate's grain and the atomic table it rolls up from; its totals must reconcile to the atomic layer within tolerance.

## Working alongside dbt

If the company already runs dbt (or SQLMesh, or a similar transformation framework),
**it owns the transform layer and this team works inside it.** Do not build a parallel
set of marts with hand-written SQL next to a dbt project; two transform layers producing
similar tables is precisely the situation the metrics catalog exists to prevent, and it
will produce two numbers for the same thing within a month.

What that means in practice:

- **Read the project before proposing anything.** `dbt_project.yml` for the layer naming
  and materialisation defaults, `models/**/schema.yml` for what each model means, its
  declared tests, and its documented columns. The `schema.yml` descriptions are a data
  dictionary that already exists — reconcile it with `knowledge/data-sources.md` rather
  than writing a competing one.
- **New marts are new dbt models**, in the project's own structure and naming, with the
  tests the project expects (`unique`, `not_null`, `relationships` on the grain key at
  minimum). A model without a grain test is a model whose grain will silently change.
- **Lineage is already solved — use it.** `dbt ls --select +my_model` and
  `dbt ls --select my_model+` answer "what feeds this" and "what breaks if I change it"
  far better than reading SQL. Run the downstream selector before changing any model, and
  say in the design what will need rebuilding.
- **Respect the materialisation strategy.** Whether a model is a view, a table, or
  incremental is usually a deliberate cost decision the data team already made. Changing
  it is their call, not an analysis's.
- **Tests are the quality gate.** Where this repo's standards call for a quality check,
  express it as a dbt test in the project rather than a separate script, so it runs on
  every build instead of only when someone remembers. `data-quality-engineer`'s standing
  checks then cover what dbt tests can't see — freshness against the real world, volume
  drift, and reconciliation to the source system.
- **The metrics catalog still wins on definitions.** If dbt has a metrics or semantic
  layer, `knowledge/metrics-catalog.md` and that layer must agree; where they don't,
  `metrics-steward` rules and one of them gets corrected. Record the ruling in
  `knowledge/decision-log.md`. Two semantic layers disagreeing is worse than either one
  alone.

Where dbt exists, `analytics-engineer` reads `schema.yml` instead of inventing marts, and
pipeline work routes through the project's own development and review workflow — including
its pull-request process. An analysis that bypasses that to write a table directly is
faster once and a liability afterwards.

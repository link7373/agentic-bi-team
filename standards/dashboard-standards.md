# Dashboard Standards

> Visual and structural rules for every dashboard the team ships, regardless of tool ({{BI_TOOL}}). Goal: any two team dashboards feel like siblings, and a new viewer gets the headline in five seconds.

## Layout

- **Z-pattern hierarchy:** most important number top-left; KPI band across the top (≤6 numbers, each with trend indicator and comparison); trends/breakdowns in the middle; detail tables below the fold.
- **One dashboard, one job:** answers 1–3 named questions (from its SPEC.md). A dashboard trying to serve everyone serves no one — split instead.
- **Five-second test:** before shipping, look at it cold. Can you state the business's condition in 5 seconds? If not, restructure.
- Max ~10–12 visuals per view. Filters grouped top or left, defaulted to the most common use (usually: latest complete period, all segments).

## Titles & Annotation

- Chart titles state the **insight pattern**, not the metric: "New signups, weekly — note March dip" beats "Signups".
- Every chart shows: period covered, data freshness ("data through {{date}}"), and source footnote where space allows.
- Targets/thresholds drawn as reference lines, not described in tooltips only.

## Charts — choosing

> Encode with the attributes the eye reads most accurately. **Length** (bars from a zero baseline) and **position** (dots, scatter) are the most precise — default to them. Colour-hue and shape are for *categories*; colour-intensity for sequential magnitude; **area/size is imprecise** (a 10× value looks ~3×) — use it only as a rough secondary encoding, never for the comparison that carries the message. One or two encodings per chart; more is noise. (Fuller guide: `analytics.md` Part 2.)

| Need | Use | Avoid |
|---|---|---|
| Trend over time | Line (bars for few periods) | Area stacks > 3 series |
| Compare categories | Horizontal bar, sorted by value | Pie > 3 slices, 3-D anything |
| Part-of-whole over time | 100% stacked bar (≤ 4–5 parts) | Multiple pies |
| Two-metric relationship | Scatter | Dual axes (unless strongly justified + clearly labelled) |
| Single KPI status | Big number + spark line + Δ | Gauges/speedometers |
| Actual vs target | Bullet graph (bar + target line + bands) | Gauges, single % with no context |
| Distribution | Histogram / box plot / jitter plot | Mean-only summaries of skewed data |
| "Where do I sit?" (one item vs peers) | Dot/jitter plot with quartile bands, highlighted marker | Bare ranking number |
| Rank over time | Bump chart | Spaghetti line chart of values |

**Never use** (humans read them wrong): pie/donut for comparison (angles/arcs aren't comparable — sorted bars instead), packed-bubble or radial/concentric bars (area & differing-radius arcs distort), word clouds (size ≠ quantity), any 3-D chart (perspective distorts length). **Pie's one acceptable use:** a single KPI showing progress to a fixed 100% target, with no cross-category comparison.

## Colour

> Consistent colour = consistent meaning across ALL team dashboards.

- **Brand palette:** {{BRAND_COLORS e.g. "primary #1A4E8A, accent #E8842C" or "defaults: primary #2563EB, neutral greys"}}
- **Semantic:** good/on-track {{GREEN e.g. #16A34A}}, watch {{AMBER e.g. #D97706}}, bad/off-track {{RED e.g. #DC2626}} — reserved for status only, never decoration.
- Sequential data → single-hue ramps; **diverging** (two hues from a meaningful midpoint — target, prior-year, zero) only when that midpoint is real; categorical → max 6–7 distinguishable hues.
- **Colour-blind safety (~8% of men have CVD; red/green both read as brown):** never rely on colour alone. Prefer **blue–orange** over red–green for diverging scales; if traffic-light colours are required, add a second encoding (icon, arrow, text). Test with a CVD simulator before shipping.
- Grey is the default; colour highlights the point. Use colour with a purpose, never for decoration.

## Honesty Rules

- Bar charts start at zero. Always.
- Line chart axes may zoom but must be labelled and consistent across compared panels.
- Same metric = same scale when shown side by side.
- No cumulative charts to disguise flat growth without also showing the per-period series.

## Technical

- Data from marts/summary tables only — no heavy logic in the BI tool (see agent rules for Tableau/Power BI/Looker specifics).
- Measure names match `knowledge/metrics-catalog.md` exactly.
- Load target: interactive in < {{LOAD_TARGET e.g. "5 seconds"}}; use extracts/aggregates to hit it.
- Every dashboard has: SPEC.md, reconciliation queries in `checks/`, a screenshot, and an inventory row in `dashboards/README.md`.
- Review for retirement every {{DASHBOARD_REVIEW_CADENCE e.g. "quarter"}} — unused dashboards get archived, not abandoned. **Beware the dead-end dashboard:** a KPI that has hit target every period for months is no longer informative — rotate it out and track usage. A good dashboard answers one question and raises the next.
- **Functional before beautiful:** analytical clarity is the foundation; decoration that doesn't encode data (and "interesting" chart types chosen to avoid bar charts) gets cut.

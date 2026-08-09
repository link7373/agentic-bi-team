# Dashboard Standards

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/


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

## Declutter & Grouping

- **Remove non-data ink.** Heavy gridlines, chart borders, backgrounds, drop shadows, redundant legends, and false-precision decimals add cognitive load without information — strip them. Every element left on the page should be there because it carries meaning.
- **Group with the eye's rules, not with boxes.** Related tiles read as a group through **proximity** and **alignment**; use whitespace and a grid to separate sections rather than borders and colour blocks. A clean alignment grid is worth more than any divider line.
- **One focal point per view.** Lead the eye to the single most important thing first (position + one accent colour), then let it travel outward. If everything is emphasised, nothing is.

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

## Tool specifics

> Everything above applies to every tool and is not negotiable per-tool. This section is
> only about the mechanics of getting there in each one. Read the subsection for
> `{{BI_TOOL}}` and ignore the rest.

### Tableau

- **Extracts over live connections** for anything a human waits on. A live connection to
  a warehouse means every filter click is a query and a cost; an extract refreshed on the
  data's actual cadence hits the load target and stops surprise bills. Live is right only
  when sub-hourly freshness genuinely changes a decision.
- **Model in the warehouse, not in the workbook.** Calculated fields are for presentation
  logic (formatting, a ratio of two existing measures), not for business definitions.
  A metric defined in a calculated field is invisible to every other workbook and to the
  catalog, which is exactly how two dashboards start disagreeing. If a calculation is
  reused, it belongs in a mart.
- **Level-of-detail expressions are powerful and easy to get wrong.** `FIXED` ignores the
  view's filters unless they're context filters — the classic Tableau bug is a total that
  doesn't respond to the dashboard's own filter. Reconcile any LOD-based number against
  a SQL query before shipping, and say in the SPEC which filters it deliberately ignores.
- **Actions over navigation.** Dashboard actions (filter, highlight, go-to-sheet) keep
  one dashboard answering one question with a drill path, instead of five near-duplicate
  dashboards.
- **Publishing:** the team produces the `.twb`/`.twbx` and the setup steps; a human does
  the Server/Cloud publish and sets the extract refresh schedule. Record the schedule in
  `dashboards/README.md` — an extract nobody refreshes is a dashboard that is quietly
  wrong.
- **Colour:** define the palette once in a workbook theme rather than per-worksheet, so
  the semantic colours in this file's Colour section stay consistent across sheets.

### Looker / LookML

- **LookML is the semantic layer, so the catalog maps to it directly.** A measure in a
  view file is the natural home for a metric definition — one place, reused by every
  Explore and Look. This is the closest any tool here comes to enforcing "computed once",
  so use it: the LookML measure name should match `knowledge/metrics-catalog.md`
  character for character, and its `description` should be the catalog's plain-English
  definition.
- **Model in views, present in Explores.** Business logic lives in view files; Explores
  are curated entry points for a specific audience and question. An Explore exposing
  every field of every joined view is not self-service, it's a maze.
- **Join carefully and declare the relationship.** A `many_to_one` mis-declared as
  `one_to_one` silently fans out rows and inflates every sum downstream. Symmetric
  aggregates cover a lot of this, but not everything — reconcile totals against SQL.
- **Persistent derived tables** are the mart layer when you can't write to the warehouse.
  Prefer a real mart built by `analytics-engineer`; a PDT is the fallback, and it needs
  the same grain declaration and rebuild schedule as any other table.
- **Dashboards are the last step, not the first.** Most Looker questions should be
  answered in an Explore by the business itself; a dashboard is for the recurring view.
  If the answer is "let me build you a dashboard" to every question, the Explores aren't
  usable.
- **Publishing:** the team produces LookML (and dashboard LookML where useful); a human
  merges it through the Looker Git workflow. Development-mode changes that never get
  deployed are the most common way work gets lost here.

### Power BI

See `standards/powerbi-standards.md` for the tool mechanics, and `/powerbi` for building
the project as code. Power BI is the one tool where the team builds and validates the
real artifact rather than producing an import — because PBIP is plain text.

### No BI tool

Self-contained HTML with inline CSS and no external dependencies, written to
`dashboards/<name>/`. Every rule above still applies: the five-second test, the chart
selection table, semantic colour, bars from zero. A single file that opens in a browser
and can be emailed is a genuinely good answer for a small team, and it version-controls
better than any of the alternatives.

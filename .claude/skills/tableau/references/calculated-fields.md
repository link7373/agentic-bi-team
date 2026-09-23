# Calculated fields

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> Read before adding any calculation to a workbook. The short version: most
> calculations you are about to write belong in a mart instead.

## The rule

**Calculated fields are for presentation logic, not business definitions.**

A metric defined in a workbook is invisible to `knowledge/metrics-catalog.md`,
to every other workbook, and to anyone querying the warehouse directly. That is
precisely how two dashboards start disagreeing about revenue, and the
disagreement surfaces in a board meeting rather than in review.

| Belongs in the workbook | Belongs in a mart |
|---|---|
| Formatting a label | Any named metric in the catalog |
| A ratio of two measures already in the extract | Revenue recognition, churn logic, segmentation rules |
| Sorting or display grouping | Anything reused by a second workbook |
| Axis-friendly rescaling (to thousands) | Anything needing a join or a window function |

If a calculation is reused, it is a mart column. Route it through
`/build-pipeline` and `analytics-engineer`.

If it conflicts with an existing catalog definition, stop and route to
`metrics-steward` - do not quietly ship a second definition.

## Builder support

`twb_builder.py` does **not** yet generate calculated fields. This is deliberate:
the recipes cover aggregation (`Sum`, `Avg`, `CountD`, date truncation) without
any calculation at all, and adding a half-checked formula generator would create
exactly the invisible-definition problem above.

When a dashboard genuinely needs one, compute it in the mart and expose it as an
ordinary column in the extract. That keeps it catalogued, testable, and reusable.

`validate_twb.py` still checks calculations, because it also validates workbooks
this module did not build - inherited ones, or ones a human edited in Desktop.

## What the validator checks

The XSD treats a formula as an opaque string, so nothing looks at it until
Tableau does. The checks are deliberately modest:

| Code | Severity | Check |
|---|---|---|
| `CALC001` | WARN | unbalanced parentheses or brackets |
| `CALC002` | WARN | function name not in the known-function list |
| `CALC003` | INFO | formula uses a `FIXED` LOD expression |

`CALC002` is a spell-check, not a parser - an unrecognised name is a prompt to
look, not proof of a bug.

## LOD expressions: the filter trap

`CALC003` exists because level-of-detail expressions are the most reliable source
of believable wrong numbers in Tableau.

**`FIXED` ignores the view's filters unless they are context filters.** The
classic symptom is a total that does not respond to the dashboard's own filter -
a user picks one segment, every chart updates, and one number stubbornly shows
the company-wide figure. It looks like a rounding quirk. It is a wrong number.

If you ship a `FIXED` expression:

1. Reconcile it against a direct SQL query, saved in `dashboards/<name>/checks/`.
2. State in `SPEC.md` which filters it deliberately ignores, and why.
3. Record the choice in `knowledge/decision-log.md` (`CLAUDE.md` principle 8).

`INCLUDE` and `EXCLUDE` respond to filters normally and are usually the safer
choice when you are not certain which you want.

## Aggregate ratios, never average ratios

A ratio computed as the average of per-row ratios gives a wrong total. Compute it
from the summed numerator and the summed denominator:

```
// wrong  - the total row is a lie
AVG([Revenue] / [Seats])

// right
SUM([Revenue]) / SUM([Seats])
```

Same rule as `DIVIDE` over `/` in `standards/powerbi-standards.md`. It is a
property of arithmetic, not of either tool. Guard against a zero denominator with
`ZN` or an `IIF` rather than shipping a divide-by-zero.

# Chart recipes

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> Six recipes, each a function in `scripts/twb_builder.py` returning a sheet dict.
> **Which chart to use is not decided here** - `standards/dashboard-standards.md`
> owns that. This file is the mechanics of getting the chart you already chose.

Every recipe is covered by `tests/run_tests.py`, which validates its output
against Tableau's official XSD.

## `ban` - headline number

```python
ban("Total Revenue", measure="Revenue")
ban("Active Accounts", measure="Account", agg="CountD")
```

| arg | meaning |
|---|---|
| `measure` | field to aggregate |
| `agg` | `Sum` (default), `Avg`, `Min`, `Max`, `Count`, `CountD` |

No shelves; the measure rides the Text encoding with a `Text` mark. `CountD` over
a dimension is how you get a distinct count - `agg` is independent of the field's
declared `role`.

Put the number the dashboard exists to move top-left. One or two BANs, not six -
a row of numbers with no trend is a scoreboard, not a dashboard.

## `bar_h` - ranked categories

```python
bar_h("Revenue by Segment", dimension="Segment", measure="Revenue")
```

Dimension on rows, measure on columns, `Bar` mark. The default for comparing
categories: horizontal bars leave room for readable labels and don't force
diagonal text.

## `bar_v` - vertical bars

```python
bar_v("Tickets by Severity", dimension="Severity", measure="Tickets")
```

Measure on rows, dimension on columns. Use when the categories have a natural
left-to-right order (time buckets, severity ladders, sizes). For unordered
categories prefer `bar_h`.

## `line` - time series

```python
line("Revenue Trend", date="Month", measure="Revenue", trunc="month")
line("Revenue by Segment", date="Month", measure="Revenue", color="Segment")
```

| arg | meaning |
|---|---|
| `date` | a field with `datatype: "date"` or `"datetime"` |
| `trunc` | `year` \| `quarter` \| `month` (default) \| `week` \| `day` |
| `color` | optional dimension for multiple series |

`trunc` emits a `TruncMonth`-style derivation so Tableau aggregates to whole
periods rather than plotting every raw date.

Keep series to about five. Beyond that nobody can follow a line, and the answer
is usually a small-multiple or a ranked bar of the latest period.

## `bar_stack` - composition over time

```python
bar_stack("Revenue by Plan over Time", dimension="Month", measure="Revenue",
          color="Plan", trunc="month")
```

`color` is required - it is the thing being stacked. `trunc` is optional and only
applies when `dimension` is a date.

Stacked bars read well for the total and for the bottom segment, and badly for
everything in the middle. If the question is "how is each plan trending", a
`line` with `color` answers it better.

## `table` - text table

```python
table("Top Accounts", dimensions=["Account"], measures=["Revenue", "Tickets"])
```

Dimensions nest on rows; measures become columns via Tableau's synthetic
`[:Measure Names]` / `[Multiple Values]` pair, with a `Text` mark.

**This is the recipe most likely to need a second look in Tableau.** The
Measure Names/Values mechanism is the fiddliest of the six, and sorting and
number formatting are not yet expressible in the spec. A table is also usually a
sign the dashboard is answering "what exactly happened" rather than "is anything
wrong" - keep it below the fold.

## What is deliberately missing

Dual-axis, scatter, maps, heatmaps, reference lines, and table calculations. They
were cut from v1 to ship six recipes that are tested rather than twelve that are
half-working. Dual-axis in particular is a common source of workbooks that pass
validation and then render wrong.

Pie and gauge are not missing by accident - `standards/dashboard-standards.md`
rules them out, and `validate_twb.py` raises `DSG001` if a `Pie` mark appears in
a workbook it did not build.

To add a recipe: write the function, add it to `CASES` in `tests/run_tests.py`,
and confirm it validates. Do not hand-patch generated XML.

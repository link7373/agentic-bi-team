# The workbook spec

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> What you actually write. `scripts/twb_builder.py` turns it into schema-correct
> `.twb` XML. You should rarely need to read or write `.twb` XML by hand.

## Why a spec and not XML

A single bar-chart worksheet is 150-250 lines of XML. `WorkbookFile-CT` is an
`xs:sequence` of 23 groups, so correct elements in the wrong order fail
validation. Hand-authoring that per dashboard is slow and failure-prone; the
builder owns the ordering and the boilerplate, and raises `SpecError` on a bad
spec rather than emitting broken XML.

## Shape

```python
{
  "name": "Exec Overview",          # workbook name; seeds datasource ids
  "connection": <connection dict>,  # csv_connection(...) or sql_connection(...)
  "fields":  [ <field dict>, ... ], # every column the workbook may reference
  "sheets":  [ <sheet dict>, ... ], # from the chart recipes
  "dashboard": {                    # optional; omit for a sheets-only workbook
      "name": "Exec Overview",
      "size": (1300, 900),          # pixels; default (1200, 800)
      "layout": [["A"], ["B", "C"]] # rows of sheet names
  },
}
```

### `fields`

```python
{"name": "Revenue", "datatype": "real", "role": "measure"}
```

- `name` - must match the CSV header or SQL column **exactly**. This is the name
  you use everywhere else in the spec.
- `datatype` - `string` | `integer` | `real` | `date` | `datetime` | `boolean`
- `role` - `dimension` or `measure`

Declare every field a sheet references. The builder raises `SpecError` naming the
unknown field if you miss one; `validate_twb.py` catches the same class of
problem in a workbook it did not build (`REF001`).

### `dashboard.layout`

A list of rows, each a list of sheet names. Rows split the height evenly, cells
split their row's width evenly:

```python
"layout": [
    ["Total Revenue", "Active Accounts"],   # two tiles across the top
    ["Revenue Trend"],                      # one full-width row
    ["Revenue by Segment", "Revenue by Plan over Time"],
]
```

Every name must match a sheet in `sheets`, or `SpecError`. Zones tile exactly to
Tableau's 100000-unit coordinate space - the last cell in each row and the last
row absorb rounding, so there are never 1-unit gaps.

Design decisions - what goes top-left, how many tiles, which chart - come from
`standards/dashboard-standards.md`, not from here.

## Worked example

```python
from twb_builder import (build_workbook, csv_connection, write_twb,
                         ban, bar_h, line, bar_stack, table)

spec = {
    "name": "Exec Overview",
    "connection": csv_connection("/abs/path/data/exec_kpis.csv", name="exec_kpis"),
    "fields": [
        {"name": "Month",   "datatype": "date",   "role": "dimension"},
        {"name": "Account", "datatype": "string", "role": "dimension"},
        {"name": "Segment", "datatype": "string", "role": "dimension"},
        {"name": "Plan",    "datatype": "string", "role": "dimension"},
        {"name": "Revenue", "datatype": "real",   "role": "measure"},
        {"name": "Tickets", "datatype": "integer","role": "measure"},
    ],
    "sheets": [
        ban("Total Revenue", measure="Revenue"),
        ban("Active Accounts", measure="Account", agg="CountD"),
        line("Revenue Trend", date="Month", measure="Revenue", trunc="month"),
        bar_h("Revenue by Segment", dimension="Segment", measure="Revenue"),
        bar_stack("Revenue by Plan over Time", dimension="Month",
                  measure="Revenue", color="Plan", trunc="month"),
        table("Top Accounts", dimensions=["Account"],
              measures=["Revenue", "Tickets"]),
    ],
    "dashboard": {
        "name": "Exec Overview",
        "size": (1300, 900),
        "layout": [["Total Revenue", "Active Accounts"],
                   ["Revenue Trend"],
                   ["Revenue by Segment", "Revenue by Plan over Time"],
                   ["Top Accounts"]],
    },
}

write_twb(build_workbook(spec), "dashboards/exec-overview/ExecOverview.twb")
```

A complete working version of this, including the SQL that produces the extract,
is `.claude/skills/tableau/examples/demo-exec-overview/build.py`.

## CLI

For a spec already serialised as JSON:

```bash
python .claude/skills/tableau/scripts/twb_builder.py spec.json -o Workbook.twb
```

Exit code 2 with the message on stderr if the spec is bad.

## One grain per workbook

The single most common way these dashboards go wrong is not XML - it is grain.
The builder emits one datasource, so every sheet shares one flat table. If
revenue is per customer-month and tickets are per ticket, you cannot put both in
one extract without duplicating revenue across ticket rows and silently inflating
every total.

Fix it upstream: aggregate to a common grain in the mart (`/build-pipeline`),
then extract that. If two questions genuinely need two grains, they are two
workbooks.

## When the spec isn't enough

The six recipes cover most exec and ops dashboards. When one genuinely doesn't
fit - dual-axis, scatter, maps, reference lines, table calculations - do not
contort a recipe or hand-patch the generated XML. Add a recipe to
`twb_builder.py` with a test in `tests/`, so the next dashboard gets it too.
Generated files are outputs; the generator is the source.

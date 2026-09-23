# Worked examples

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

Runnable examples of the workbook spec, built against the repo's own
`demo/demo.db`. They live here rather than in `dashboards/` because that
directory is the **team's** work area - a Power BI or Looker team should not
find a Tableau demo in their dashboard inventory.

They double as living documentation: if `twb_builder.py` changes, these must
still build and validate.

## demo-exec-overview

A six-sheet executive dashboard over the demo SaaS warehouse - two KPI tiles, a
revenue trend, a ranked bar, a stacked composition, and a text table.

```bash
python .claude/skills/tableau/examples/demo-exec-overview/build.py
python .claude/skills/tableau/scripts/validate_twb.py \
    .claude/skills/tableau/examples/demo-exec-overview/ExecOverview.twb
```

Produces `ExecOverview.twb` (open in Tableau Desktop) and `ExecOverview.twbx`
(open in Tableau Public, which is extract-only). Both are regenerated from
`demo.db` every run - the script is the source, the workbook is output.

Reconciliation figures, if you want to check the KPI tiles by eye:
**SUM(Revenue) = 3,832,199.00** and **COUNT(DISTINCT Account) = 768**.

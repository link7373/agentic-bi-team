#!/usr/bin/env python3
"""Worked example: build a Tableau dashboard end to end from the demo warehouse.

demo.db -> CSV -> .hyper extract -> .twb -> .twbx

This lives inside the skill, not in dashboards/, because dashboards/ is the
team's own work area - a Power BI or Looker team should not find a Tableau demo
sitting in their inventory. It doubles as living documentation of the spec
format in references/workbook-spec.md: if the builder changes, this must still
run.

    python .claude/skills/tableau/examples/demo-exec-overview/build.py

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent.parent              # .claude/skills/tableau
REPO = SKILL.parents[2]                 # repo root
sys.path.insert(0, str(SKILL / "scripts"))

from twb_builder import (  # noqa: E402
    build_workbook, csv_connection, write_twb, ban, bar_h, line, bar_stack, table,
)
from hyper_extract import write_hyper, package_twbx  # noqa: E402

DB = REPO / "demo" / "demo.db"
DATA_DIR = HERE / "data"
CSV_PATH = DATA_DIR / "exec_kpis.csv"
HYPER_PATH = DATA_DIR / "exec_kpis.hyper"
TWB_PATH = HERE / "ExecOverview.twb"
TWBX_PATH = HERE / "ExecOverview.twbx"

# Customer x month grain. Revenue comes from paid invoices; tickets are counted
# in the month they were created. Both are left-joined onto the customer-month
# spine so a month with no tickets shows zero rather than dropping the row.
QUERY = """
WITH months AS (
    SELECT DISTINCT period_month AS month FROM fct_invoices WHERE status = 'paid'
),
spine AS (
    SELECT c.customer_id, c.company_name, c.segment, c.industry, c.plan,
           c.country, m.month
    FROM dim_customer c
    CROSS JOIN months m
),
revenue AS (
    SELECT customer_id, period_month AS month, SUM(amount_usd) AS revenue_usd
    FROM fct_invoices
    WHERE status = 'paid'
    GROUP BY customer_id, period_month
),
tickets AS (
    SELECT customer_id, substr(created_date, 1, 7) AS month,
           COUNT(*) AS ticket_count
    FROM fct_support_tickets
    GROUP BY customer_id, substr(created_date, 1, 7)
)
SELECT
    s.month || '-01'                AS "Month",
    s.company_name                  AS "Account",
    s.segment                       AS "Segment",
    s.industry                      AS "Industry",
    s.plan                          AS "Plan",
    s.country                       AS "Country",
    ROUND(COALESCE(r.revenue_usd, 0), 2) AS "Revenue",
    COALESCE(t.ticket_count, 0)     AS "Tickets"
FROM spine s
LEFT JOIN revenue r ON r.customer_id = s.customer_id AND r.month = s.month
LEFT JOIN tickets t ON t.customer_id = s.customer_id AND t.month = s.month
WHERE COALESCE(r.revenue_usd, 0) > 0 OR COALESCE(t.ticket_count, 0) > 0
ORDER BY s.month, s.company_name
"""

FIELDS = [
    {"name": "Month",    "datatype": "date",    "role": "dimension"},
    {"name": "Account",  "datatype": "string",  "role": "dimension"},
    {"name": "Segment",  "datatype": "string",  "role": "dimension"},
    {"name": "Industry", "datatype": "string",  "role": "dimension"},
    {"name": "Plan",     "datatype": "string",  "role": "dimension"},
    {"name": "Country",  "datatype": "string",  "role": "dimension"},
    {"name": "Revenue",  "datatype": "real",    "role": "measure"},
    {"name": "Tickets",  "datatype": "integer", "role": "measure"},
]


def fetch_rows():
    con = sqlite3.connect(DB)
    try:
        cur = con.execute(QUERY)
        headers = [d[0] for d in cur.description]
        return headers, cur.fetchall()
    finally:
        con.close()


def export_csv() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    try:
        cur = con.execute(QUERY)
        headers = [d[0] for d in cur.description]
        rows = cur.fetchall()
    finally:
        con.close()
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(headers)
        w.writerows(rows)
    return len(rows)


def main() -> int:
    if not DB.exists():
        print(f"demo database not found: {DB}", file=sys.stderr)
        return 2

    n = export_csv()
    print(f"exported {n:,} rows -> {CSV_PATH.relative_to(REPO)}")

    # Tableau Public cannot open a live connection at all - it needs an
    # extract, and the extract has to travel inside a .twbx.
    _, rows = fetch_rows()
    write_hyper(FIELDS, rows, HYPER_PATH)
    print(f"wrote extract      -> {HYPER_PATH.relative_to(REPO)}")

    # Absolute directory: Tableau resolves a textscan connection from the path
    # stored in the file, and an absolute one opens reliably wherever the .twb
    # is launched from. build.py is what makes this portable — rerun it after
    # moving the folder. See references/gotchas.md.
    spec = {
        "name": "Exec Overview",
        "connection": csv_connection(str(CSV_PATH), name="exec_kpis",
                                     extract=True),
        "fields": FIELDS,
        "sheets": [
            ban("Total Revenue", measure="Revenue"),
            ban("Active Accounts", measure="Account", agg="CountD"),
            line("Revenue Trend", date="Month", measure="Revenue", trunc="month"),
            bar_h("Revenue by Segment", dimension="Segment", measure="Revenue"),
            bar_stack("Revenue by Plan over Time", dimension="Month",
                      measure="Revenue", color="Plan", trunc="month"),
            # A text table renders every row it is given. "Top Accounts" over
            # 768 accounts was an illegible smear - the limit belongs in the
            # mart, not the viz. Segment keeps the recipe honest and readable.
            table("Revenue and Tickets by Segment", dimensions=["Segment"],
                  measures=["Revenue", "Tickets"]),
        ],
        "dashboard": {
            "name": "Exec Overview",
            "size": (1300, 900),
            "layout": [
                ["Total Revenue", "Active Accounts"],
                ["Revenue Trend"],
                ["Revenue by Segment", "Revenue by Plan over Time"],
                ["Revenue and Tickets by Segment"],
            ],
            # KPI row needs far less height than a chart row
            "row_heights": [1, 3, 3, 2],
        },
    }

    xml = build_workbook(spec)
    out = write_twb(xml, TWB_PATH)
    print(f"built              -> {out.relative_to(REPO)}")

    pkg = package_twbx(TWB_PATH, HYPER_PATH, TWBX_PATH)
    print(f"packaged           -> {pkg.relative_to(REPO)}  "
          f"({pkg.stat().st_size / 1024:.0f} KB)")
    print("\nOpen the .twbx in Tableau Public; the .twb alone needs Desktop.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

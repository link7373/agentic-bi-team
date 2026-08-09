#!/usr/bin/env python3
"""Build a small, fake B2B SaaS warehouse so the team has something to work on.

Evaluating this kit otherwise requires wiring a real warehouse first, which is a
lot of work to find out whether the thing is any good. This script produces a
SQLite database with two years of plausible subscription data in about a second,
using nothing but the standard library.

The data is not random noise. Three findings are planted in it, because a demo
where every metric is flat teaches you nothing about an analyst:

  1. A churn spike concentrated in one segment. Blended churn rises only
     modestly, so the topline understates it — Starter-plan SMB churn roughly
     triples after a price change while Enterprise retention quietly improves.
     Anyone who reports the blended number alone has missed it.
  2. Two data-quality defects. Product events stop for nine days (a silent
     pipeline outage), and one month of invoices contains duplicate rows. Both
     are the kind of thing that shows up first as an inexplicable metric move.
  3. Seasonality. Signups sag in December and July, so a naive month-over-month
     comparison in January reads as a collapse.

Usage:
    python demo/generate_demo_data.py [--out demo/demo.db] [--seed 20260808]
                                      [--end-date YYYY-MM-DD] [--quiet]

The row counts are deterministic for a given seed; dates are relative to
--end-date (default: today) so the scorecard has a recent period to report on.

Exit codes: 0 = built, 1 = failed, 2 = bad invocation.

Standard library only (Python 3.9+) — no pip install required.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "demo" / "demo.db"
DEFAULT_SEED = 20260808

MONTHS_OF_HISTORY = 24
N_CUSTOMERS = 800

PLANS = {
    #  name         mrr    weight  segment
    "starter":    (49,    0.46, "SMB"),
    "growth":     (299,   0.32, "Mid-Market"),
    "scale":      (999,   0.16, "Mid-Market"),
    "enterprise": (2500,  0.06, "Enterprise"),
}

INDUSTRIES = ["Retail", "Healthcare", "Financial Services", "Manufacturing",
              "Technology", "Education", "Logistics", "Professional Services"]
COUNTRIES = ["US", "US", "US", "GB", "CA", "AU", "DE", "FR", "NL", "SG"]
CHANNELS = ["organic", "paid_search", "referral", "outbound", "partner"]

FEATURES = ["dashboard_view", "report_export", "api_call", "alert_created",
            "integration_sync", "user_invited"]

TICKET_SEVERITIES = ["low", "low", "low", "medium", "medium", "high", "urgent"]

# --- planted findings -------------------------------------------------------
# 1. Price rise on the Starter plan, this many months before the end date.
PRICE_CHANGE_MONTHS_AGO = 7
STARTER_CHURN_MULTIPLIER = 3.1      # SMB churn after the change
ENTERPRISE_CHURN_MULTIPLIER = 0.55  # Enterprise quietly improves at the same time
# 2a. Product-event pipeline outage.
OUTAGE_MONTHS_AGO = 3
OUTAGE_DAYS = 9
# 2b. Duplicated invoices, one month.
DUPLICATE_INVOICE_MONTHS_AGO = 5
DUPLICATE_INVOICE_RATE = 0.06
# 3. Seasonal signup multipliers by calendar month (1-indexed).
SEASONALITY = {1: 1.15, 2: 1.05, 3: 1.10, 4: 1.00, 5: 0.98, 6: 0.92,
               7: 0.68, 8: 0.85, 9: 1.12, 10: 1.18, 11: 1.08, 12: 0.62}

SCHEMA = """
CREATE TABLE dim_customer (
    customer_id     INTEGER PRIMARY KEY,
    company_name    TEXT    NOT NULL,
    industry        TEXT    NOT NULL,
    country         TEXT    NOT NULL,
    segment         TEXT    NOT NULL,
    plan            TEXT    NOT NULL,
    acquisition_channel TEXT NOT NULL,
    signup_date     TEXT    NOT NULL,
    churn_date      TEXT,
    is_active       INTEGER NOT NULL
);

CREATE TABLE fct_subscription_events (
    event_id        INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    event_date      TEXT    NOT NULL,
    event_type      TEXT    NOT NULL,  -- new | upgrade | downgrade | churn
    from_plan       TEXT,
    to_plan         TEXT,
    mrr_delta_usd   REAL    NOT NULL
);

CREATE TABLE fct_invoices (
    invoice_id      INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    invoice_date    TEXT    NOT NULL,
    period_month    TEXT    NOT NULL,
    amount_usd      REAL    NOT NULL,
    status          TEXT    NOT NULL   -- paid | open | failed
);

CREATE TABLE fct_product_events (
    event_id        INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    event_date      TEXT    NOT NULL,
    feature         TEXT    NOT NULL,
    event_count     INTEGER NOT NULL
);

CREATE TABLE fct_support_tickets (
    ticket_id       INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    created_date    TEXT    NOT NULL,
    resolved_date   TEXT,
    severity        TEXT    NOT NULL,
    reopened        INTEGER NOT NULL
);

CREATE INDEX idx_sub_events_date  ON fct_subscription_events(event_date);
CREATE INDEX idx_invoices_month   ON fct_invoices(period_month);
CREATE INDEX idx_prod_events_date ON fct_product_events(event_date);
CREATE INDEX idx_tickets_created  ON fct_support_tickets(created_date);
"""


def month_start(d: date, months_back: int) -> date:
    """First day of the month `months_back` months before d's month."""
    total = d.year * 12 + (d.month - 1) - months_back
    return date(total // 12, total % 12 + 1, 1)


def add_months(d: date, months: int) -> date:
    total = d.year * 12 + (d.month - 1) + months
    day = min(d.day, 28)
    return date(total // 12, total % 12 + 1, day)


def weighted_plan(rng: random.Random) -> str:
    names = list(PLANS)
    weights = [PLANS[n][1] for n in names]
    return rng.choices(names, weights=weights, k=1)[0]


def company_name(rng: random.Random, n: int) -> str:
    a = ["North", "Blue", "Iron", "Vertex", "Lumen", "Cedar", "Atlas", "Orbit",
         "Quill", "Harbor", "Kestrel", "Granite", "Meridian", "Solstice"]
    b = ["Works", "Labs", "Systems", "Group", "Partners", "Analytics", "Digital",
         "Holdings", "Collective", "Industries"]
    return f"{rng.choice(a)}{rng.choice(b)} {n:03d}"


def build_customers(rng: random.Random, end: date) -> list:
    """Signups spread over the history window, with seasonality applied."""
    start = month_start(end, MONTHS_OF_HISTORY - 1)
    months = [add_months(start, i) for i in range(MONTHS_OF_HISTORY)]

    weights = [SEASONALITY[m.month] * (1 + 0.035 * i) for i, m in enumerate(months)]
    total = sum(weights)
    per_month = [max(1, round(N_CUSTOMERS * w / total)) for w in weights]

    customers, cid = [], 1
    for m, count in zip(months, per_month):
        for _ in range(count):
            span = (add_months(m, 1) - m).days
            signup = m + timedelta(days=rng.randrange(span))
            if signup > end:
                continue
            plan = weighted_plan(rng)
            customers.append({
                "customer_id": cid,
                "company_name": company_name(rng, cid),
                "industry": rng.choice(INDUSTRIES),
                "country": rng.choice(COUNTRIES),
                "segment": PLANS[plan][2],
                "plan": plan,
                "acquisition_channel": rng.choice(CHANNELS),
                "signup_date": signup,
                "churn_date": None,
            })
            cid += 1
    return customers


def apply_churn(rng: random.Random, customers: list, end: date) -> None:
    """Monthly churn hazard, with the planted post-price-change spike."""
    price_change = month_start(end, PRICE_CHANGE_MONTHS_AGO)

    base_hazard = {"SMB": 0.030, "Mid-Market": 0.014, "Enterprise": 0.008}

    for cust in customers:
        cursor = add_months(cust["signup_date"], 1)
        while cursor < end:
            hazard = base_hazard[cust["segment"]]
            # New customers churn harder in their first three months.
            age_months = (cursor.year * 12 + cursor.month) - (
                cust["signup_date"].year * 12 + cust["signup_date"].month)
            if age_months <= 3:
                hazard *= 1.8
            # Planted finding 1: the price change hits Starter/SMB hard while
            # Enterprise retention improves, so the blended rate barely moves.
            if cursor >= price_change:
                if cust["plan"] == "starter":
                    hazard *= STARTER_CHURN_MULTIPLIER
                elif cust["segment"] == "Enterprise":
                    hazard *= ENTERPRISE_CHURN_MULTIPLIER
            if rng.random() < hazard:
                span = (add_months(cursor, 1) - cursor).days
                churn = cursor + timedelta(days=rng.randrange(span))
                # The last month is partial: a churn drawn past the end date
                # hasn't happened yet, so the customer is still active.
                if churn <= end:
                    cust["churn_date"] = churn
                break
            cursor = add_months(cursor, 1)


def build_subscription_events(rng: random.Random, customers: list, end: date) -> list:
    order = ["starter", "growth", "scale", "enterprise"]
    events, eid = [], 1

    for cust in customers:
        mrr = PLANS[cust["plan"]][0]
        events.append((eid, cust["customer_id"], cust["signup_date"], "new",
                       None, cust["plan"], float(mrr)))
        eid += 1

        # Plan changes while active.
        cursor = add_months(cust["signup_date"], rng.randrange(3, 9))
        stop = cust["churn_date"] or end
        current = cust["plan"]
        while cursor < stop:
            if rng.random() < 0.16:
                idx = order.index(current)
                up = rng.random() < 0.72
                new_idx = min(idx + 1, len(order) - 1) if up else max(idx - 1, 0)
                if new_idx != idx:
                    new_plan = order[new_idx]
                    delta = float(PLANS[new_plan][0] - PLANS[current][0])
                    events.append((eid, cust["customer_id"], cursor,
                                   "upgrade" if up else "downgrade",
                                   current, new_plan, delta))
                    eid += 1
                    current = new_plan
            cursor = add_months(cursor, rng.randrange(4, 10))

        if cust["churn_date"]:
            events.append((eid, cust["customer_id"], cust["churn_date"], "churn",
                           current, None, -float(PLANS[current][0])))
            eid += 1

    return events


def build_invoices(rng: random.Random, customers: list, end: date) -> list:
    dup_month = month_start(end, DUPLICATE_INVOICE_MONTHS_AGO)
    invoices, iid = [], 1

    for cust in customers:
        amount = float(PLANS[cust["plan"]][0])
        cursor = date(cust["signup_date"].year, cust["signup_date"].month, 1)
        stop = cust["churn_date"] or end
        while cursor < stop:
            invoice_date = cursor + timedelta(days=rng.randrange(0, 3))
            if invoice_date > end:
                break
            roll = rng.random()
            status = "paid" if roll < 0.94 else ("open" if roll < 0.98 else "failed")
            row = (iid, cust["customer_id"], invoice_date,
                   cursor.strftime("%Y-%m"), amount, status)
            invoices.append(row)
            iid += 1

            # Planted finding 2b: one month double-billed by a rerun that was
            # not idempotent. Same customer, same period, new invoice_id — so a
            # primary-key check passes and a revenue total is silently inflated.
            if cursor == dup_month and rng.random() < DUPLICATE_INVOICE_RATE:
                invoices.append((iid, cust["customer_id"], invoice_date,
                                 cursor.strftime("%Y-%m"), amount, status))
                iid += 1

            cursor = add_months(cursor, 1)

    return invoices


def build_product_events(rng: random.Random, customers: list, end: date) -> list:
    outage_start = month_start(end, OUTAGE_MONTHS_AGO) + timedelta(days=6)
    outage_end = outage_start + timedelta(days=OUTAGE_DAYS)

    events, eid = [], 1
    for cust in customers:
        stop = cust["churn_date"] or end
        # A fortnightly sample rather than every event — enough to trend, small
        # enough to ship in a git repo.
        cursor = cust["signup_date"] + timedelta(days=rng.randrange(0, 14))
        intensity = {"SMB": 1.0, "Mid-Market": 2.4, "Enterprise": 5.0}[cust["segment"]]
        while cursor < stop and cursor <= end:
            # Planted finding 2a: the events pipeline stopped for nine days.
            if not (outage_start <= cursor < outage_end):
                # Engagement decays before a churn, which is what makes a churn
                # model in /build-model actually learn something.
                if cust["churn_date"]:
                    days_left = (cust["churn_date"] - cursor).days
                    decay = 0.35 if days_left < 60 else 1.0
                else:
                    decay = 1.0
                weekday_boost = 0.4 if cursor.weekday() >= 5 else 1.0
                for feature in FEATURES:
                    if rng.random() < 0.45:
                        count = max(1, int(rng.gauss(6 * intensity * decay
                                                     * weekday_boost, 3)))
                        events.append((eid, cust["customer_id"], cursor,
                                       feature, count))
                        eid += 1
            cursor += timedelta(days=14)
    return events


def build_tickets(rng: random.Random, customers: list, end: date) -> list:
    tickets, tid = [], 1
    for cust in customers:
        stop = cust["churn_date"] or end
        cursor = cust["signup_date"]
        rate = {"SMB": 0.30, "Mid-Market": 0.55, "Enterprise": 1.1}[cust["segment"]]
        while cursor < stop:
            if rng.random() < rate:
                created = cursor + timedelta(days=rng.randrange(0, 28))
                if created > end:
                    break
                severity = rng.choice(TICKET_SEVERITIES)
                # Unhappy customers file more, and more urgent, tickets before
                # they leave.
                if cust["churn_date"] and (cust["churn_date"] - created).days < 90:
                    severity = rng.choice(["medium", "high", "high", "urgent"])
                resolved = None
                if rng.random() < 0.93:
                    resolved = created + timedelta(days=rng.randrange(0, 9))
                    if resolved > end:
                        resolved = None
                tickets.append((tid, cust["customer_id"], created, resolved,
                                severity, 1 if rng.random() < 0.11 else 0))
                tid += 1
            cursor = add_months(cursor, 1)
    return tickets


def iso(value):
    return value.isoformat() if isinstance(value, date) else value


def write_db(path: Path, customers, sub_events, invoices, prod_events, tickets):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    con = sqlite3.connect(path)
    try:
        con.executescript(SCHEMA)
        con.executemany(
            "INSERT INTO dim_customer VALUES (?,?,?,?,?,?,?,?,?,?)",
            [(c["customer_id"], c["company_name"], c["industry"], c["country"],
              c["segment"], c["plan"], c["acquisition_channel"],
              iso(c["signup_date"]), iso(c["churn_date"]),
              0 if c["churn_date"] else 1) for c in customers])
        con.executemany(
            "INSERT INTO fct_subscription_events VALUES (?,?,?,?,?,?,?)",
            [(e[0], e[1], iso(e[2]), e[3], e[4], e[5], e[6]) for e in sub_events])
        con.executemany(
            "INSERT INTO fct_invoices VALUES (?,?,?,?,?,?)",
            [(i[0], i[1], iso(i[2]), i[3], i[4], i[5]) for i in invoices])
        con.executemany(
            "INSERT INTO fct_product_events VALUES (?,?,?,?,?)",
            [(e[0], e[1], iso(e[2]), e[3], e[4]) for e in prod_events])
        con.executemany(
            "INSERT INTO fct_support_tickets VALUES (?,?,?,?,?,?)",
            [(t[0], t[1], iso(t[2]), iso(t[3]), t[4], t[5]) for t in tickets])
        con.commit()
    finally:
        con.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the Agentic BI Team demo warehouse (SQLite).")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help=f"output database (default: {DEFAULT_OUT.name})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help="random seed; same seed, same data")
    parser.add_argument("--end-date", help="last date in the data (default: today)")
    parser.add_argument("--quiet", action="store_true", help="less output")
    args = parser.parse_args(argv)

    if args.end_date:
        try:
            end = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        except ValueError:
            print("error: --end-date must be YYYY-MM-DD", file=sys.stderr)
            return 2
    else:
        end = date.today()

    rng = random.Random(args.seed)
    customers = build_customers(rng, end)
    apply_churn(rng, customers, end)
    sub_events = build_subscription_events(rng, customers, end)
    invoices = build_invoices(rng, customers, end)
    prod_events = build_product_events(rng, customers, end)
    tickets = build_tickets(rng, customers, end)

    out = Path(args.out)
    try:
        write_db(out, customers, sub_events, invoices, prod_events, tickets)
    except sqlite3.Error as exc:
        print(f"error: could not write {out}: {exc}", file=sys.stderr)
        return 1

    if args.quiet:
        print(f"Demo warehouse written to {out}")
        return 0

    churned = sum(1 for c in customers if c["churn_date"])
    total = (len(customers) + len(sub_events) + len(invoices)
             + len(prod_events) + len(tickets))
    print(f"""Demo warehouse written to {out}

  dim_customer             {len(customers):>7,}  ({churned:,} churned, {len(customers) - churned:,} active)
  fct_subscription_events  {len(sub_events):>7,}
  fct_invoices             {len(invoices):>7,}
  fct_product_events       {len(prod_events):>7,}
  fct_support_tickets      {len(tickets):>7,}
  {'-' * 38}
  total rows               {total:>7,}

Covering {month_start(end, MONTHS_OF_HISTORY - 1)} to {end}, seed {args.seed}.

Query it with:
  python demo/query_demo.py "SELECT plan, COUNT(*) FROM dim_customer GROUP BY plan"

Three findings are planted in this data. Don't read demo/DEMO-CHARTER.md's last
section if you want to see whether the team finds them on its own — try
`/scorecard weekly`, then `/investigate-metric churn`.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())

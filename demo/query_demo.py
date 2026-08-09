#!/usr/bin/env python3
"""Query the demo warehouse from the shell.

The demo database is SQLite, so the team could shell out to the `sqlite3` CLI —
but that isn't installed everywhere, and Python is (this kit already requires
it). This is the connection command `/connect-data` registers for demo mode.

Usage:
    python demo/query_demo.py "SELECT plan, COUNT(*) FROM dim_customer GROUP BY plan"
    python demo/query_demo.py --file analyses/2026-08-08-churn/churn_by_segment.sql
    python demo/query_demo.py --tables
    python demo/query_demo.py --schema fct_invoices

Output is a plain aligned table, or CSV with --csv for piping into something else.
Read-only: the connection is opened in SQLite immutable mode, so a stray write
statement errors instead of corrupting the demo.

Exit codes: 0 = ok, 1 = query error, 2 = bad invocation.

Standard library only (Python 3.9+) — no pip install required.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / "demo" / "demo.db"
MAX_ROWS = 200


def connect(path: Path) -> sqlite3.Connection:
    # immutable=1 makes the whole connection read-only at the driver level.
    uri = f"file:{path.as_posix()}?immutable=1"
    return sqlite3.connect(uri, uri=True)


def print_table(cursor, limit: int) -> int:
    rows = cursor.fetchmany(limit + 1)
    if cursor.description is None:
        print("(no result set)")
        return 0
    headers = [d[0] for d in cursor.description]
    truncated = len(rows) > limit
    rows = rows[:limit]

    cells = [[("" if v is None else str(v)) for v in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in cells:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))

    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip())
    print("  ".join("-" * w for w in widths))
    for row in cells:
        print("  ".join(v.ljust(w) for v, w in zip(row, widths)).rstrip())

    print(f"\n{len(rows)} row(s)" + (f" (truncated at {limit}; "
          f"add LIMIT or --limit)" if truncated else ""))
    return len(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Query the demo warehouse (read-only).")
    parser.add_argument("sql", nargs="?", help="SQL to run")
    parser.add_argument("--file", help="read the SQL from a file instead")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="database path")
    parser.add_argument("--tables", action="store_true", help="list tables and row counts")
    parser.add_argument("--schema", metavar="TABLE", help="show a table's columns")
    parser.add_argument("--csv", action="store_true", dest="as_csv", help="emit CSV")
    parser.add_argument("--limit", type=int, default=MAX_ROWS,
                        help=f"max rows to print (default {MAX_ROWS})")
    args = parser.parse_args(argv)

    db = Path(args.db)
    if not db.exists():
        print(f"error: {db} not found. Build it with:\n"
              f"  python demo/generate_demo_data.py", file=sys.stderr)
        return 2

    if args.file:
        sql = Path(args.file).read_text(encoding="utf-8")
    elif args.tables:
        sql = None
    elif args.schema:
        sql = f"PRAGMA table_info({args.schema})"
    elif args.sql:
        sql = args.sql
    else:
        parser.print_help()
        return 2

    con = connect(db)
    try:
        if args.tables:
            names = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            width = max((len(n) for n in names), default=0)
            for name in names:
                count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                print(f"{name.ljust(width)}  {count:>8,}")
            return 0

        cursor = con.execute(sql)
        if args.as_csv:
            if cursor.description is None:
                return 0
            writer = csv.writer(sys.stdout, lineterminator="\n")
            writer.writerow([d[0] for d in cursor.description])
            writer.writerows(cursor)
            return 0
        print_table(cursor, args.limit)
        return 0
    except sqlite3.Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())

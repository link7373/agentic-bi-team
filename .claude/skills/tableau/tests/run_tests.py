#!/usr/bin/env python3
"""Regression-test twb_builder.py and validate_twb.py.

    python .claude/skills/tableau/tests/run_tests.py [-v]

Asserts five things:
  1. every chart recipe builds and passes Tableau's official XSD
  2. a clean generated workbook validates with zero errors and exit 0
  3. every injected defect raises its specific code, at the right severity
  4. the builder refuses a bad spec with SpecError rather than emitting bad XML
  5. building the same spec twice produces byte-identical output

Fixtures are built in a temp directory and removed afterwards, so this never
touches the repo.

Why (3) is worth the effort: during development three defect cases appeared to
prove the validator was broken. They were not - the tests string-matched
single-quoted attributes while the builder emits double-quoted ones via
quoteattr. A test that cannot fail for the reason you think it fails is worse
than no test.

Requires lxml for the XSD layer; without it those assertions are skipped and
reported as skipped rather than silently passing.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from twb_builder import (  # noqa: E402
    build_workbook, csv_connection, sql_connection, write_twb, SpecError,
    ban, bar_h, bar_v, line, bar_stack, table,
)

VALIDATOR = SKILL / "scripts" / "validate_twb.py"

GREEN, RED, YELLOW, DIM, RESET = (
    "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m")

FIELDS = [
    {"name": "Month",    "datatype": "date",    "role": "dimension"},
    {"name": "Account",  "datatype": "string",  "role": "dimension"},
    {"name": "Segment",  "datatype": "string",  "role": "dimension"},
    {"name": "Severity", "datatype": "string",  "role": "dimension"},
    {"name": "Revenue",  "datatype": "real",    "role": "measure"},
    {"name": "Tickets",  "datatype": "integer", "role": "measure"},
]

RECIPES = {
    "ban":         ban("Total Revenue", measure="Revenue"),
    "ban_countd":  ban("Active Accounts", measure="Account", agg="CountD"),
    "bar_h":       bar_h("Revenue by Segment", dimension="Segment", measure="Revenue"),
    "bar_v":       bar_v("Tickets by Severity", dimension="Severity", measure="Tickets"),
    "line":        line("Revenue Trend", date="Month", measure="Revenue"),
    "line_color":  line("Revenue by Segment Trend", date="Month",
                        measure="Revenue", color="Segment"),
    "bar_stack":   bar_stack("Revenue by Severity over Time", dimension="Month",
                             measure="Revenue", color="Severity", trunc="month"),
    "table":       table("Top Accounts", dimensions=["Account"],
                         measures=["Revenue", "Tickets"]),
}

# defect name -> (mutation, expected code, expected severity)
DEFECTS = {
    "bom":            (lambda s: "﻿" + s,                     "ENC001", "ERROR"),
    "bad_order":      (lambda s: s.replace("<preferences>",
                                           "<dashboards/><preferences>", 1),
                                                                   "TWB001", "ERROR"),
    "dangling_field": (lambda s: s.replace("[sum:Revenue:qk]",
                                           "[sum:Ghost:qk]", 1),   "REF001", "ERROR"),
    "column_drift":   (lambda s: s.replace('name="[Revenue]"',
                                           'name="[Turnover]"', 1), "REF001", "ERROR"),
    "dangling_sheet": (lambda s: s.replace('name="Revenue Trend"',
                                           'name="No Such Sheet"', 1),
                                                                   "REF002", "ERROR"),
    "missing_csv":    (lambda s: s.replace('filename="t.csv"',
                                           'filename="gone.csv"', 1),
                                                                   "CSV001", "ERROR"),
    "pie_mark":       (lambda s: s.replace('class="Line"', 'class="Pie"', 1),
                                                                   "DSG001", "WARN"),
    "crlf":           (lambda s: s.replace("\n", "\r\n"),          "ENC002", "WARN"),
    # Regression: an unqualified field reference. Tableau drops the field
    # ("There is no field named '[Multiple Values]'") and every dashboard zone
    # using that sheet then fails. The XSD sees a well-formed string.
    "unqualified_ref": (lambda s: s.replace(
        '<text column="[federated.t].[sum:Revenue:qk]"',
        '<text column="[sum:Revenue:qk]"', 1),                     "REF006", "ERROR"),
    # Regression: a dashboard whose window declares no viewpoint for a sheet it
    # shows. Tableau refuses the entire dashboard; the XSD sees nothing wrong.
    "missing_viewpoint": (lambda s: re.sub(
        r"<viewpoints>.*?</viewpoints>", "<viewpoints />", s, count=1,
        flags=re.S),                                               "REF007", "ERROR"),
}

BAD_SPECS = {
    "unknown field": {
        "name": "X", "connection": csv_connection("t.csv"), "fields": FIELDS,
        "sheets": [bar_h("B", dimension="Nope", measure="Revenue")]},
    "dangling dashboard ref": {
        "name": "X", "connection": csv_connection("t.csv"), "fields": FIELDS,
        "sheets": [RECIPES["bar_h"]],
        "dashboard": {"name": "D", "layout": [["Ghost"]]}},
    "duplicate sheet names": {
        "name": "X", "connection": csv_connection("t.csv"), "fields": FIELDS,
        "sheets": [RECIPES["bar_h"], RECIPES["bar_h"]]},
    "no sheets": {
        "name": "X", "connection": csv_connection("t.csv"), "fields": FIELDS,
        "sheets": []},
    "missing key": {
        "name": "X", "connection": csv_connection("t.csv"), "fields": FIELDS},
    "bad role": {
        "name": "X", "connection": csv_connection("t.csv"),
        "fields": [{"name": "A", "datatype": "string", "role": "dim"}],
        "sheets": [ban("B", measure="A")]},
    "bad sql kind": None,      # handled separately, raises from sql_connection
    "bad trunc": None,         # handled separately, raises from line()
}

CSV_TEXT = ("Month,Account,Segment,Severity,Revenue,Tickets\n"
            "2026-01-01,Acme,SMB,high,100.0,2\n"
            "2026-02-01,Acme,SMB,low,150.0,1\n")


def full_spec(tmp: Path) -> dict:
    return {
        "name": "T",
        "connection": csv_connection(str(tmp / "t.csv"), name="t"),
        "fields": FIELDS,
        "sheets": list(RECIPES.values()),
        "dashboard": {"name": "D", "size": (1300, 900),
                      "layout": [[s["name"]] for s in RECIPES.values()]},
    }


def run_validator(target: Path):
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(target), "--json"],
        capture_output=True, text=True)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, {"findings": [], "_stdout": proc.stdout,
                                 "_stderr": proc.stderr}


def main(argv=None) -> int:
    verbose = "-v" in (argv or sys.argv[1:])
    passed = failed = skipped = 0

    def ok(name, detail=""):
        nonlocal passed
        passed += 1
        print(f"  {GREEN}PASS{RESET} {name}" + (f" {DIM}{detail}{RESET}" if detail else ""))

    def bad(name, detail):
        nonlocal failed
        failed += 1
        print(f"  {RED}FAIL{RESET} {name}\n       {detail}")

    def skip(name, detail):
        nonlocal skipped
        skipped += 1
        print(f"  {YELLOW}SKIP{RESET} {name} {DIM}{detail}{RESET}")

    try:
        from lxml import etree  # noqa: F401
        have_lxml = True
    except ImportError:
        have_lxml = False

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "t.csv").write_text(CSV_TEXT, encoding="utf-8", newline="\n")

        # ---- 1. every recipe builds and validates -----------------------
        print("\n1. chart recipes build and pass the official XSD")
        for label, sheet in RECIPES.items():
            spec = {"name": "T", "connection": csv_connection(str(tmp / "t.csv")),
                    "fields": FIELDS, "sheets": [sheet],
                    "dashboard": {"name": "D", "layout": [[sheet["name"]]]}}
            try:
                path = write_twb(build_workbook(spec), tmp / f"{label}.twb")
            except SpecError as e:
                bad(label, f"builder raised: {e}")
                continue
            if not have_lxml:
                skip(label, "(no lxml)")
                continue
            code, out = run_validator(path)
            errs = [f for f in out["findings"] if f["severity"] == "ERROR"]
            if code == 0 and not errs:
                ok(label)
            else:
                bad(label, f"exit={code} errors={[e['code'] for e in errs]}")

        # sql connection path
        spec_sql = {"name": "W",
                    "connection": sql_connection("postgres", server="db",
                                                 database="analytics",
                                                 sql="SELECT * FROM m.t"),
                    "fields": FIELDS, "sheets": [RECIPES["bar_h"]],
                    "dashboard": {"name": "D",
                                  "layout": [[RECIPES["bar_h"]["name"]]]}}
        p = write_twb(build_workbook(spec_sql), tmp / "sql.twb")
        if have_lxml:
            code, out = run_validator(p)
            xsd = [f for f in out["findings"] if f["code"] in ("TWB001", "XML001")]
            ok("sql_connection", "(xsd clean)") if not xsd else \
                bad("sql_connection", f"{[f['code'] for f in xsd]}")
        else:
            skip("sql_connection", "(no lxml)")

        # ---- 2. clean full workbook ------------------------------------
        print("\n2. clean workbook validates with zero errors")
        clean = write_twb(build_workbook(full_spec(tmp)), tmp / "clean.twb")
        code, out = run_validator(clean)
        errs = [f for f in out["findings"] if f["severity"] == "ERROR"]
        if code == 0 and not errs:
            ok("clean fixture", f"({len(out['findings'])} findings total)")
        else:
            bad("clean fixture", f"exit={code} {[e['code'] for e in errs]}")
            if verbose:
                for f in out["findings"]:
                    print(f"       {f['severity']} {f['code']} {f['message'][:90]}")

        # ---- 3. injected defects ---------------------------------------
        print("\n3. injected defects raise their specific code")
        src = clean.read_text(encoding="utf-8")
        for name, (mutate, want_code, want_sev) in DEFECTS.items():
            if want_code == "TWB001" and not have_lxml:
                skip(name, "(no lxml)")
                continue
            d = tmp / f"defect_{name}.twb"
            with open(d, "w", encoding="utf-8", newline="") as fh:
                fh.write(mutate(src))
            code, out = run_validator(d)
            hits = [f for f in out["findings"] if f["code"] == want_code]
            if not hits:
                got = sorted({f["code"] for f in out["findings"]})
                bad(name, f"expected {want_code}, got {got or 'nothing'}")
            elif hits[0]["severity"] != want_sev:
                bad(name, f"{want_code} severity {hits[0]['severity']}, "
                          f"expected {want_sev}")
            elif want_sev == "ERROR" and code != 1:
                bad(name, f"{want_code} raised but exit code was {code}")
            else:
                ok(name, f"({want_code})")
                if verbose:
                    print(f"       {DIM}{hits[0]['message'][:100]}{RESET}")

        # ---- 4. builder refuses bad specs -------------------------------
        print("\n4. builder refuses a bad spec")
        for name, spec in BAD_SPECS.items():
            if spec is None:
                continue
            try:
                build_workbook(spec)
                bad(name, "no SpecError raised")
            except SpecError as e:
                ok(name, f"({str(e)[:55]}...)")
            except Exception as e:
                bad(name, f"raised {type(e).__name__} not SpecError: {e}")
        for name, fn in (("bad sql kind",
                          lambda: sql_connection("oracle", server="s",
                                                 database="d", sql="x")),
                         ("bad trunc",
                          lambda: line("L", date="Month", measure="Revenue",
                                       trunc="fortnight"))):
            try:
                fn()
                bad(name, "no SpecError raised")
            except SpecError as e:
                ok(name, f"({str(e)[:55]}...)")

        # ---- 5. determinism --------------------------------------------
        print("\n5. rebuilding the same spec is byte-identical")
        a = build_workbook(full_spec(tmp))
        b = build_workbook(full_spec(tmp))
        ok("deterministic output") if a == b else \
            bad("deterministic output", "two builds differ")

    total = passed + failed
    print(f"\n{total} assertions: {GREEN}{passed} passed{RESET}"
          + (f", {RED}{failed} failed{RESET}" if failed else "")
          + (f", {YELLOW}{skipped} skipped{RESET}" if skipped else ""))
    if not have_lxml:
        print(f"{YELLOW}lxml not installed - XSD assertions were skipped. "
              f"pip install lxml for full coverage.{RESET}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

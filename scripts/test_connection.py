#!/usr/bin/env python3
"""Prove a data connection actually works, and record only what it proved.

The most expensive failure in this kit is a source recorded as "available" that
isn't: agents then plan confidently against data they cannot reach. This script
exists so "connected" means a command ran and rows came back, not that somebody
believed it would.

It deliberately imports no database drivers. Instead it runs whatever command
the user already has working — `psql`, `bq`, `snowsql`, `duckdb`, `sqlite3`, or
anything else — so it stays standard-library-only and tool-neutral. If the
warehouse is reachable through an MCP server rather than a shell, this script
cannot test it; ask the agent to list tables through the MCP tool instead, and
record that result the same way.

Usage:
    # test one command
    python scripts/test_connection.py --name "prod-replica" \
        --cmd 'psql "$PROD_REPLICA_URL" -c "SELECT 1"'

    # test everything registered in scripts/connections.json
    python scripts/test_connection.py

    # ...and write the results into knowledge/data-sources.md
    python scripts/test_connection.py --write

scripts/connections.json (gitignored if it ever holds anything sensitive — it
should not; put credentials in environment variables and reference them):

    [
      {"name": "prod-replica",
       "cmd": "psql \\"$PROD_REPLICA_URL\\" -c \\"SELECT 1\\"",
       "expect": "1"},
      {"name": "demo", "cmd": "python demo/query_demo.py \\"SELECT 1\\""}
    ]

Exit codes: 0 = every source passed, 1 = at least one failed, 2 = bad invocation.

Standard library only (Python 3.9+) — no pip install required.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "scripts" / "connections.json"
DATA_SOURCES = REPO_ROOT / "knowledge" / "data-sources.md"

DEFAULT_TIMEOUT = 60

# Anything that would modify the warehouse has no business in a connection test.
FORBIDDEN = re.compile(
    r"\b(drop|truncate|delete|insert|update|alter|grant|revoke|create\s+or\s+replace)\b",
    re.IGNORECASE)


def load_registry(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"error: {path} is not valid JSON: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if not isinstance(data, list):
        print(f"error: {path} must contain a JSON array of sources", file=sys.stderr)
        raise SystemExit(2)
    return data


def run_test(source: dict, timeout: int) -> dict:
    """Run one connection command and return a structured result."""
    name = source.get("name") or "(unnamed)"
    cmd = source.get("cmd")
    result = {"name": name, "cmd": cmd, "ok": False, "seconds": 0.0,
              "detail": "", "output": ""}

    if not cmd:
        result["detail"] = "no command defined for this source"
        return result
    if FORBIDDEN.search(cmd):
        result["detail"] = ("command contains a write/DDL keyword; a connection "
                            "test must be read-only")
        return result

    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout, cwd=str(REPO_ROOT),
                              env={**os.environ})
    except subprocess.TimeoutExpired:
        result["seconds"] = float(timeout)
        result["detail"] = f"timed out after {timeout}s"
        return result
    except OSError as exc:
        result["detail"] = f"could not run the command: {exc}"
        return result

    result["seconds"] = round(time.monotonic() - start, 2)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    result["output"] = out[:400]

    if proc.returncode != 0:
        first = (err or out).splitlines()
        result["detail"] = (f"exit {proc.returncode}: "
                            f"{first[0][:200] if first else 'no output'}")
        return result
    if not out:
        result["detail"] = ("command succeeded but returned no output — this is "
                            "not proof the query ran; make it SELECT something")
        return result

    expect = source.get("expect")
    if expect and expect not in out:
        result["detail"] = f"output did not contain expected text {expect!r}"
        return result

    result["ok"] = True
    result["detail"] = f"returned {len(out.splitlines())} line(s) in {result['seconds']}s"
    return result


def status_line(res: dict) -> str:
    mark = "✅ tested" if res["ok"] else "❌ blocked"
    return f"{mark}: {res['detail']}"


def write_results(results: list, path: Path) -> bool:
    """Update the Connection Summary rows in knowledge/data-sources.md.

    Only rewrites the status cell of a row whose first cell names a source we
    tested. Everything else in the file is left exactly as it is — this script
    records evidence, it does not author documentation.
    """
    if not path.exists():
        print(f"warning: {path} not found; skipping --write", file=sys.stderr)
        return False

    text = path.read_text(encoding="utf-8")
    by_name = {r["name"].lower(): r for r in results}
    changed = 0
    out_lines = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.count("|") >= 3:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            key = cells[0].strip("`* ").lower()
            if key in by_name:
                res = by_name[key]
                cells[-1] = status_line(res)
                line = "| " + " | ".join(cells) + " |"
                changed += 1
        out_lines.append(line)

    if changed:
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8", newline="\n")
    print(f"\n{changed} row(s) updated in {path.relative_to(REPO_ROOT)}"
          if changed else
          f"\nNo matching rows in {path.relative_to(REPO_ROOT)} — add a "
          f"Connection Summary row per source, first column = the source name.")
    return bool(changed)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Test data connections with a live read-only query.")
    parser.add_argument("--name", help="name of a single ad-hoc source to test")
    parser.add_argument("--cmd", help="the shell command that queries it")
    parser.add_argument("--expect", help="text the output must contain to pass")
    parser.add_argument("--registry", default=str(REGISTRY),
                        help="JSON file of sources (default: scripts/connections.json)")
    parser.add_argument("--write", action="store_true",
                        help="record results in knowledge/data-sources.md")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"per-source timeout in seconds (default {DEFAULT_TIMEOUT})")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit results as JSON")
    args = parser.parse_args(argv)

    if args.cmd and not args.name:
        print("error: --cmd requires --name", file=sys.stderr)
        return 2

    if args.cmd:
        sources = [{"name": args.name, "cmd": args.cmd, "expect": args.expect}]
    else:
        sources = load_registry(Path(args.registry))
        if not sources:
            print(f"No sources to test. Either pass --name/--cmd, or create "
                  f"{Path(args.registry).name} — see the docstring in this file, "
                  f"or run /connect-data to be walked through it.")
            return 2

    results = [run_test(s, args.timeout) for s in sources]

    if args.as_json:
        print(json.dumps(results, indent=2))
    else:
        for res in results:
            print(f"[{'PASS' if res['ok'] else 'FAIL'}] {res['name']}: {res['detail']}")
            if not res["ok"] and res["output"]:
                print(f"       output: {res['output'].splitlines()[0][:160]}")
        n_ok = sum(1 for r in results if r["ok"])
        print(f"\n{n_ok}/{len(results)} source(s) reachable.")
        if n_ok < len(results):
            print("A blocked source is a finding, not a failure — record what is "
                  "needed to unblock it and carry on with what works.")

    if args.write:
        write_results(results, DATA_SOURCES)

    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

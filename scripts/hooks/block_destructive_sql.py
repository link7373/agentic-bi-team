#!/usr/bin/env python3
"""PreToolUse hook: stop destructive SQL before it reaches a warehouse.

`CLAUDE.md` §8 says the team confirms before anything destructive. That is a
sentence in a prompt, and prompts are not a control. This hook is the control:
it inspects every Bash command, and if the command both invokes a database
client and contains a statement that destroys or re-permissions data, it blocks
the call and explains why.

It is deliberately conservative in one direction and blunt in the other. It only
fires when it can see a database client in the command, so ordinary shell work
is untouched — but within those commands it does not try to parse SQL, because a
regex that pretends to understand SQL is worse than one that admits it doesn't.
Anything it blocks, a human can still do; the point is that it stops being an
accident.

Wired up in .claude/settings.json as a PreToolUse hook on Bash. Reads the tool
call as JSON on stdin.

Exit codes (the Claude Code hook contract):
    0  allow
    2  block, and show stderr to the model

Standard library only (Python 3.9+) — no pip install required.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import json
import re
import sys

# Command names that mean "this is talking to a database".
DB_CLIENTS = re.compile(
    r"(?:^|[\s|;&(`$])(psql|mysql|mariadb|sqlite3|duckdb|bq|bigquery|snowsql|"
    r"snowflake|clickhouse-client|athena|redshift|sqlcmd|mongosh|mongo|"
    r"trino|presto|dbt|sqlplus|impala-shell|beeline|spark-sql|usql)\b",
    re.IGNORECASE)

# Statements that destroy data, destroy structure, or change who can reach it.
DESTRUCTIVE = [
    (re.compile(r"\bdrop\s+(table|database|schema|view|index|materialized\s+view)\b",
                re.IGNORECASE),
     "DROP removes an object and everything in it. There is no undo in most "
     "warehouses, and a dropped mart takes every dashboard built on it with it."),
    (re.compile(r"\btruncate\s+table\b|\btruncate\s+\w", re.IGNORECASE),
     "TRUNCATE empties a table irreversibly and usually cannot be rolled back."),
    (re.compile(r"\bdelete\s+from\b(?![\s\S]{0,400}?\bwhere\b)", re.IGNORECASE),
     "DELETE FROM with no WHERE clause removes every row in the table."),
    (re.compile(r"\bupdate\s+[\w.\"`\[\]]+\s+set\b(?![\s\S]{0,400}?\bwhere\b)",
                re.IGNORECASE),
     "UPDATE ... SET with no WHERE clause rewrites every row in the table."),
    (re.compile(r"\b(grant|revoke)\s+", re.IGNORECASE),
     "GRANT/REVOKE changes who can reach the data. Access control is the "
     "owner's decision, not the analysis's."),
    (re.compile(r"\balter\s+table\s+[\w.\"`\[\]]+\s+drop\b", re.IGNORECASE),
     "ALTER TABLE ... DROP COLUMN destroys a column's data; downstream metrics "
     "usually fail silently rather than erroring."),
    (re.compile(r"\bdrop\s+user\b|\bdrop\s+role\b", re.IGNORECASE),
     "Dropping a user or role can break every pipeline authenticating as it."),
]

# Escape hatch: an explicit, deliberate marker the user can add to a command
# they have decided to run anyway. Requiring it to be typed out is the point.
OVERRIDE = "AGENTIC_BI_ALLOW_DESTRUCTIVE=1"


def read_command() -> str:
    """Pull the Bash command out of the hook payload on stdin."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return ""
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or "")
    return ""


def main() -> int:
    command = read_command()
    if not command:
        return 0
    if OVERRIDE in command:
        return 0
    if not DB_CLIENTS.search(command):
        return 0

    for pattern, why in DESTRUCTIVE:
        match = pattern.search(command)
        if not match:
            continue
        statement = match.group(0).strip()
        print(
            f"BLOCKED by the Agentic BI Team safety hook: this command sends "
            f"`{statement}` to a database client.\n\n"
            f"{why}\n\n"
            f"CLAUDE.md §8 requires explicit confirmation before any destructive "
            f"action. Do not retry this command as-is. Instead:\n"
            f"  1. Tell the user exactly what would be destroyed and why you "
            f"believe it is necessary.\n"
            f"  2. If they confirm, they can run it themselves, or ask you to "
            f"re-run it prefixed with {OVERRIDE}.\n"
            f"  3. If you were trying to rebuild a table, prefer CREATE OR "
            f"REPLACE, a MERGE, or delete-insert scoped by partition — the "
            f"idempotent patterns in standards/sql-and-data-standards.md.\n\n"
            f"Read-only exploration is never blocked.",
            file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())

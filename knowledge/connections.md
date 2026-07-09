# Connecting Your Data — Setup Cookbook

> **Created by Colin Beck**
> LinkedIn: https://www.linkedin.com/in/beckcolin/
> GitHub: https://github.com/link7373


> The make-or-break step. Everything the team does downstream assumes Claude Code can reach
> your data. This is the plain-English runbook for getting there. `/setup-team` reads your
> charter, tries each method below, and records what worked in `knowledge/data-sources.md`.
> You don't need to know which method is "right" — name what you have in `START-HERE.md §2`
> and the team will test it and tell you.

There are three ways to connect, in order of preference. **Any one of them is enough to start.**

---

## 1. MCP server (best — direct, permissioned access)

An [MCP server](https://modelcontextprotocol.io) for your warehouse lets the team query it
directly, with access governed by the server's own permissions.

- **What you need:** the MCP server for your warehouse configured in Claude Code (BigQuery,
  Snowflake, Postgres, etc.). Many are available as Claude Code connectors/plugins.
- **How the team uses it:** it calls the MCP query tool directly — no shell, no credentials in
  the repo.
- **How to verify:** ask the team to "list the tables you can see" — if names come back, you're
  connected.

## 2. CLI client (good — a working command in the shell)

A command-line client already authenticated in your shell.

- **Examples:** `psql`, `bq` (BigQuery), `snowsql`, `duckdb`, `sqlite3`, `mysql`.
- **What you need:** the client installed **and** credentials available — almost always via
  **environment variables**, never hard-coded in the repo. Typical pattern:

  ```bash
  # in your shell profile or a local .env that is gitignored — NEVER commit this
  export PROD_REPLICA_URL="postgresql://readonly:***@host:5432/db"
  export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/sa.json"
  ```

- **How the team uses it:** it records the **exact** working command in `data-sources.md`
  (e.g. `psql "$PROD_REPLICA_URL" -c "SELECT 1"`), and reuses it every session.
- **Read-only by default:** point the team at a read replica or a read-only role wherever you
  can. Anything that writes/drops is gated by `CLAUDE.md §8`.

## 3. Files (fine to start — exports in the repo)

No live connection yet? Drop data in and the team analyses it locally.

- **What you need:** CSV/Parquet exports placed in the repo (a `data/` folder is conventional).
- **How the team uses it:** loads them with **DuckDB or pandas**, joins and analyses locally,
  and tells you exactly which **regular exports** it needs to keep going.
- **Note:** bulk data files are **gitignored by default** (see `.gitignore`) — they're inputs,
  not institutional memory. Keep sensitive extracts out of git.

---

## Secrets — the one hard rule

**Never commit credentials.** No connection strings, API keys, service-account JSON, or
passwords in tracked files. The repo's `.gitignore` already excludes `.env*`, `*.key`,
`*.pem`, `credentials.json`, and `service-account*.json` — keep secrets there or in your shell
environment. If the team ever needs a credential it doesn't have, it will **stop and ask**
(`CLAUDE.md §8`) rather than guess.

## What "connected" means here

`/setup-team` marks a source **✅ working** only after a live test query actually succeeds, and
**❌ blocked** (with what's needed to unblock) otherwise. Nothing is recorded as available
untested. The per-source results live in the Connection Summary of `knowledge/data-sources.md`.

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| "I don't know how to connect" | Leave `START-HERE.md §2` rough and run `/setup-team` — it will propose options and help you set one up. |
| CLI command works for you but not the team | Credentials are in an interactive-only shell. Move them to your shell profile or a gitignored `.env`. |
| Connection worked, now broken | Update (or ask the team to retest) the Connection Summary in `knowledge/data-sources.md`. |
| Warehouse too big / costly to scan | Set a cost guardrail in `data-sources.md`; the team estimates scan size before heavy queries. |

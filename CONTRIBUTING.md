# Contributing

> **Created by Colin Beck**
> LinkedIn: https://www.linkedin.com/in/beckcolin/
> GitHub: https://github.com/link7373

This repo is a team of instructions, not an application. Most contributions are prose,
and the bar for prose here is the same as for code: it has to be correct, it has to be
consistent with everything else, and something has to check it.

## Before you open a PR

```bash
python scripts/lint_repo.py
python scripts/check_placeholders.py --template-mode
python scripts/check_metrics.py --template-mode
python .claude/skills/powerbi/tests/run_tests.py
```

All four run in CI. The lint is the important one — it catches the failure mode this
repo is most prone to, which is prose drifting out of agreement with itself.

## The rules that aren't negotiable

**Standard library only.** Every script in `scripts/`, `demo/`, and the Power BI module
runs on a clean Python 3.9+ with no `pip install`. A BI team's first interaction with
this kit cannot be a dependency error. If a check genuinely needs a third-party library,
it belongs in an agent's instructions ("install X, then…"), not in the tooling.

**Tool neutrality.** Vendor-specific depth is gated behind `{{BI_TOOL}}` and lives in
files that are only read when that tool is in play. A team on Tableau must see no Power
BI content anywhere in their context. This is why `/powerbi` checks `{{BI_TOOL}}` and
bows out, and why its reference files sit in `.claude/skills/powerbi/references/` rather
than in `standards/`.

**One source of truth per fact.** A metric is defined in `knowledge/metrics-catalog.md`
and nowhere else. A routing decision lives in `CLAUDE.md` §3. A chart rule lives in
`standards/dashboard-standards.md` — `powerbi-standards.md` defers to it rather than
restating it. If you find yourself writing the same rule twice, one of them should be a
pointer.

**Counts are checked.** Never hand-write "9 agents" without running the lint; it scans
the README, `CLAUDE.md`, and `/setup-team` for stated counts and fails if any disagrees
with what's on disk.

## Adding an agent

1. Create `.claude/agents/<name>.md`. Frontmatter needs `name` (matching the filename)
   and a `description` written for routing — it is how the orchestrator decides, so say
   *when to use this agent*, not just what it is.
2. Add `tools:` and `model:` if the role is read-and-verify rather than open-ended.
   Least privilege is the default for anything that validates, monitors, or governs.
   **If you add an MCP server later, revisit these lists** — an agent with an explicit
   `tools:` list does not inherit new MCP tools automatically.
3. Add a row to the routing table in `CLAUDE.md` §3 and to the agent list in the README.
4. Use the one-line attribution, not the four-line block (see below).

## Adding a skill

1. Create `.claude/skills/<name>/SKILL.md` with frontmatter and a numbered procedure.
   Skills are procedures, not essays — each step should be something you can tell was
   done or not done.
2. List it in `CLAUDE.md` §4 and in the README's workflow table.
3. If it produces an artifact, say where it goes and which directory inventory it
   updates.

## Placeholders

Two forms, and the distinction is enforced:

| Form | Meaning | After `/setup-team` |
|---|---|---|
| `{{UPPER_SNAKE}}` | `/setup-team` fills this from the charter | must be gone |
| `{{lowercase prose}}` | a blank a human fills per entry | stays for the life of the file |
| `{{e.g. "..."}}` | an inline example, not a slot | stays |

Anything inside an HTML comment is treated as a form template and is exempt. Run
`python scripts/check_placeholders.py --list` to see the whole inventory.

## Attribution

Reader-facing docs — `README.md`, `START-HERE.md`, `CLAUDE.md`, `analytics.md`,
`CONTRIBUTING.md` — carry the full block. Every file that gets loaded into an agent's
context carries one line:

```
> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/
```

Four lines of author metadata in forty-odd files is real context spend on every
invocation. The lint enforces the split.

## Writing style for agents and skills

- Address the agent as "you". Say what to do, in what order, and what to do when the
  data doesn't cooperate.
- Prefer a rule with its reason attached. "Check freshness before declaring a metric
  drop — roughly half of all metric alerts are broken pipelines" survives contact with
  a novel situation; "check freshness" does not.
- Name the file to read rather than restating its contents.
- Keep an agent under roughly 200 lines. Past that, the specific instructions at the
  bottom start losing to the general ones at the top.

## Releases

Bump `VERSION`, add a `CHANGELOG.md` section, and tag. If the release changes a layout
or convention that user-filled files depend on, say so explicitly in the changelog —
`/upgrade` reads it.

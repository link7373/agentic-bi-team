---
name: upgrade
description: Pull framework improvements from a newer release of the Agentic BI Team into a repo you have already configured — updating agents, skills, standards, and scripts while preserving your filled-in knowledge base and CLAUDE.md. Use when a new version ships, or when you cloned a while ago and want the latest.
---

# Upgrade — New Framework, Same Memory

Someone clones this kit, runs `/setup-team`, and spends six months accumulating metric
definitions, data quirks, decision rulings, and stakeholder preferences. Then a new
release adds an agent and fixes three skills. Re-cloning throws away the six months;
doing nothing means the improvements never land.

This skill separates the two. The repo is cleanly divided, and that division is what
makes upgrading tractable:

| | Files | On upgrade |
|---|---|---|
| **Framework** | `.claude/agents/`, `.claude/skills/`, `standards/`, `scripts/`, `scheduling/`, `demo/`, `.github/`, `CONTRIBUTING.md`, `CHANGELOG.md`, `VERSION` | replace with the new version, re-applying your local placeholder values |
| **Yours** | `knowledge/*`, `CLAUDE.md`, `START-HERE.md`, `analyses/`, `pipelines/`, `dashboards/`, `models/`, `experiments/`, `scorecards/`, `deliverables/`, `.env`, `scripts/connections.json` | **never overwritten** — merged by hand where a release requires it |

The complication is that framework files contain *your* configuration: `/setup-team`
replaced `{{BI_TOOL}}` with "Power BI" inside `dashboard-developer.md`. A naive copy
reverts that. Step 4 is where that's handled.

## Procedure

### 1. Snapshot first

```bash
python scripts/setup_backup.py
```

Note the id. If the upgrade goes badly, `--restore <id> --yes` puts everything back.
Also check `git status` — a clean tree means `git diff` will show the user exactly what
the upgrade changed, which is worth a lot when reviewing.

### 2. Establish both versions

Read the local `VERSION` file. Get the new release (a git remote, a fresh clone in a temp
directory, or a downloaded archive — ask the user which they have; do not fetch anything
without saying where from).

If the local repo has no `VERSION` file, it predates 1.0.0. Say so — the changes are
larger, and step 6 matters more.

### 3. Read the changelog between the versions

`CHANGELOG.md` in the new release, every section between their version and the new one.
This is the whole point of the step: **look specifically for anything describing a
changed layout or convention that user-filled files depend on.** A new required key in
the metrics catalog, a renamed knowledge file, a changed placeholder name — those need
migration, not just a file copy.

Summarise for the user before touching anything: what's new, what changed, and
specifically what will need a decision from them.

### 4. Update the framework files, preserving local configuration

For each framework file that differs:

- **New file** (an agent or skill that didn't exist): copy it in. If it contains
  `{{PLACEHOLDERS}}`, fill them from the values already used elsewhere in the repo —
  `python scripts/check_placeholders.py --list` shows what is still unfilled, and the
  configured neighbours show what each value was set to. Don't re-interview the user for
  answers they've already given.
- **Changed file:** diff it. Where the only differences are your filled-in placeholder
  values, take the new version and re-apply those values. Where the user has *hand-edited*
  the file beyond setup — a tuned agent prompt, a house rule added to a standard — stop
  and show them both versions. Their edit is deliberate and you must not silently discard
  it; ask whether to keep theirs, take the new one, or merge.
- **Deleted upstream:** don't delete it locally without asking. A file removed from the
  framework may be one they now depend on.

Hand-edited framework files are common, and they are the main reason this cannot be a
script. Treat every one as a conversation.

### 5. Migrate user files only where the changelog requires it

Never rewrite a knowledge file wholesale. Where a release changes a required structure —
a new key in the metrics catalog, a new section in a template — add the structure and
leave the content alone, marking anything you cannot fill as `> TODO (user):` rather than
guessing.

If a release adds a new knowledge file (`data-quality-log.md`, `request-log.md`, and
`incident-runbook.md` all arrived in 1.0.0), copy the template in and let the user or
`/setup-team` fill the standing configuration.

### 6. Verify

```bash
python scripts/lint_repo.py
python scripts/check_placeholders.py
python scripts/check_metrics.py
```

then `/health-check`.

The lint catches the most likely upgrade failure by far: a new agent or skill that landed
on disk but never got a row in `CLAUDE.md`'s routing tables, and is therefore invisible to
the orchestrator. Then confirm the new `VERSION` file is in place — an upgrade that
doesn't bump the version makes the next one harder.

### 7. Report

What changed and what it gives them, what you preserved, what needs their decision, and
the snapshot id for undo. Recommend committing the upgrade as its own commit, separate
from any analysis work, so it can be reverted cleanly.

## When the gap is very large

Several major versions behind, or heavily hand-edited, is sometimes better handled the
other way round: clone the new release fresh, copy `knowledge/` and the work directories
across, and re-run `/setup-team` against the existing charter. Say so if that looks like
less work — the knowledge base is the valuable part, and it moves cleanly.

---

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

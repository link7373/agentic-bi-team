---
name: health-check
description: Self-audit the BI team — repo structure lint, unfilled placeholders, metrics-catalog schema, live connection re-tests, data freshness, knowledge-base staleness, and inventory drift. Use as the post-setup smoke test, on a weekly schedule, and whenever the team's output starts feeling off.
---

# Health Check — Does This Team Still Work?

A virtual BI team degrades quietly. A connection expires and nobody notices until a
scorecard is wrong. A metric gets added to a dashboard but never to the catalog. The
business context describes a company that reorganised six months ago. None of that
throws an error; it just makes the output slowly less true.

This skill is the scheduled check that catches all of it. Run it after `/setup-team`,
weekly alongside the scorecard, and any time something feels stale.

**Report what you find, fix what is unambiguous, and escalate the rest.** Do not fix a
finding by lowering the standard — deleting a failing check or loosening a threshold to
get a green report is the one genuinely harmful outcome here.

## Procedure

### 1. Repo integrity (fast, always run)

```bash
python scripts/lint_repo.py
python scripts/check_placeholders.py
python scripts/check_metrics.py
```

- **lint_repo** — agent and skill counts agreeing everywhere they're stated, every agent
  and skill present in the `CLAUDE.md` routing tables, frontmatter valid, cross-file
  links resolving. A skill missing from the routing table is invisible to the
  orchestrator; a broken link sends an agent looking for context that isn't there.
- **check_placeholders** — post-setup mode. Any remaining `{{UPPER_SNAKE}}` means an
  agent is reading a template string as if it were a fact about the business.
  `{{lowercase prose}}` blanks are expected and fine.
- **check_metrics** — catalog entries parse, required keys present, names unique, and
  every metric referenced by a scorecard or dashboard spec exists in the catalog.

Fix mechanical failures directly (a stale count, a moved file, a missing routing row).
Anything that needs a business answer becomes a question for the user.

### 2. Connections (the one that matters most)

```bash
python scripts/test_connection.py
```

Re-test every registered source. A source recorded as ✅ that now fails gets flipped to
❌ **immediately**, before anything else in this run — the whole team is downstream of
that file. If a source has no registered command, note the coverage gap; an untestable
connection is an untrusted one.

If the warehouse is reached through MCP rather than a shell, test it by listing tables
through the MCP tool and record the result the same way.

### 3. Data freshness and health

Hand this to `data-quality-engineer`, or run its first two checks yourself if the sweep
is small: for every table the scorecard and live dashboards depend on, compare the max
load timestamp against the expected refresh window in `knowledge/data-sources.md`, and
compare the latest row counts against the trailing distribution.

Report staleness in business terms — "`fct_orders` is three days behind, so the revenue
line on the weekly scorecard and the exec dashboard are both wrong right now" — not as a
table of timestamps. Open items in `knowledge/data-quality-log.md` get re-checked here
too; anything that has recurred three times gets escalated as a design problem rather
than logged a fourth time.

### 4. Knowledge-base staleness

Read the dates and judge. There is no script for this because the question is whether
the content is still *true*, not whether it was edited recently.

- `business-context.md` — does it still describe the company? Priorities and the change
  ledger go stale fastest. A change ledger with no entries in three months is almost
  certainly untended rather than accurate, and root-cause analysis depends on it.
- `metrics-catalog.md` — any metric marked DRAFT for more than a quarter is either
  ratified or abandoned; ask which. Any metric with `generic_sql: TODO` is not usable.
- `stakeholders.md` — audiences and preferences drift with reorgs.
- `industry-notes.md` — briefings past their review-by date are flagged, not deleted.
- `decision-log.md` — open Observations that nobody triaged.
- `data-sources.md` — accepted quirks past their review date.

### 5. Inventory drift

Every directory README (`analyses/`, `pipelines/`, `dashboards/`, `models/`,
`experiments/`, `scorecards/`, `deliverables/`) is supposed to list what's in that
directory. Compare each inventory against what's actually on disk in both directions:
work that exists but isn't listed is work the team will duplicate, and a listed artifact
that no longer exists is a broken promise to whoever goes looking.

While here, check for **dead-end artifacts**: dashboards nobody has opened, models
nobody scores, scheduled scorecards nobody reads. Retiring one is a real win — it
removes maintenance, refresh cost, and a chance to be wrong. Flag them; don't delete
anything without asking.

### 6. Report

Lead with the verdict — healthy, degraded, or broken — and the single most important
thing to fix. Then:

- what you fixed automatically
- what needs a human decision, with the specific question
- what you could not check, and why (coverage gaps are findings)

Log anything durable: data problems to `knowledge/data-quality-log.md`, methodological
or governance rulings to `knowledge/decision-log.md`.

If everything passes, say so in one line. A health check that produces a page of prose
when nothing is wrong trains people to stop reading it.

## Running unattended

`scheduling/` has the assets to run this weekly next to the scorecard. On a scheduled
run, stay quiet unless something is wrong: report only failures, changes since the last
run, and anything newly stale. See `scheduling/SCHEDULING.md`.

---

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

# Data Incident Runbook

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> What to do when the data is wrong. Owned by `data-quality-engineer`; filled in by
> `/setup-team` and revised after every incident. Read it *before* you need it — the
> point of a runbook is that nobody has to make these decisions while a number is
> visibly wrong on someone's dashboard.
>
> Incidents get logged in `knowledge/data-quality-log.md`. This file is the procedure;
> that file is the history.

## What counts as an incident

An incident is **wrong data that someone might act on**. Not every data problem
qualifies, and treating everything as an incident is how the label stops meaning
anything.

| | Incident | Not an incident |
|---|---|---|
| A mart is 3 days stale and feeds the exec dashboard | ✅ | |
| A metric moved because the business changed | | ✅ — that's an analysis |
| Revenue is inflated by duplicate invoice rows | ✅ | |
| A dev table has nulls in it | | ✅ — log it |
| A definition changed and nobody restated prior reports | ✅ | |
| A query is slow | | ✅ — route to analytics-engineer |

The test is consequence, not cause: **could someone make a decision on this before it's
fixed?**

## Severity

| | Meaning | Response |
|---|---|---|
| **SEV-1** | Wrong data has already reached a decision-maker, or a board/exec artifact is wrong right now | Notify immediately, before you finish diagnosing |
| **SEV-2** | Data is wrong but hasn't been acted on yet — a dashboard is live with bad numbers | Notify the affected audience today; fix same day |
| **SEV-3** | Data is degraded but usable with a caveat, or the problem is confined to work in progress | Note the caveat wherever the data appears; fix this week |

When you can't tell between two levels, take the higher one for the first hour. It is
much cheaper to stand down than to explain why nobody was told.

## The procedure

### 1. Contain before you diagnose

The instinct is to find the cause. Resist it for five minutes and do this first:

- **Name the blast radius.** Which dashboards, scorecards, analyses, and deliverables
  used this data? Check `scorecards/`, `dashboards/README.md`, and recent `analyses/`.
- **Stop the bleeding.** Tell the orchestrator to warn anyone about to use the affected
  artifacts. If a scheduled scorecard is about to run on bad data, say so now.
- **Establish the window.** When did the data last look right? Everything between then
  and now is suspect — including analyses already published from it. This is the single
  most useful fact in an incident and the easiest one to skip.

### 2. Notify

Who to tell, and how:

| Severity | Notify | Channel | Who does it |
|---|---|---|---|
| SEV-1 | {{SEV1_CONTACTS e.g. "CEO, CFO, Head of Data"}} | {{SEV1_CHANNEL e.g. "Slack #data-alerts + direct message"}} | {{WHO_NOTIFIES e.g. "the user — the team drafts, a human sends"}} |
| SEV-2 | {{SEV2_CONTACTS e.g. "the dashboard's audience"}} | {{SEV2_CHANNEL}} | {{WHO_NOTIFIES}} |
| SEV-3 | note in the next scorecard | in-artifact caveat | the team |

**The team does not send outward communications on its own** (`CLAUDE.md` §8). Draft the
notice, hand it to the user, and say plainly that it hasn't been sent. `insights-communicator`
has the "data outage notice" pattern — short, specific, no speculation about cause:

> *What's wrong:* `fct_orders` has been stale since Tuesday 06:00 UTC.
> *What it affects:* the weekly revenue scorecard and the exec dashboard — both are
> currently showing figures roughly 3 days out of date.
> *What to do meanwhile:* treat revenue figures published since Tuesday as provisional.
> *When we'll know more:* by 14:00 today.

Say what you know, what you don't, and when you'll next update. Never speculate about
cause in the first notice — a wrong cause circulates further than the correction.

### 3. Diagnose

Work through these in order; the earlier ones are cheaper and more often right:

1. **Did the pipeline run?** Check the orchestrator, logs, and the load timestamp.
2. **Did it run twice?** Duplicate loads are as common as missing ones and much harder to
   spot — the row count is high, not low, and nothing errors.
3. **Did the source change?** Schema change, a column repurposed, an API version bump.
4. **Did a credential expire?** Silent auth failures often surface as empty results
   rather than errors.
5. **Did we change something?** Check the change ledger in `knowledge/business-context.md`
   and recent commits. A deploy correlating in time is the most likely single cause.
6. **Did the business change?** Someone started using a field differently, a new product
   launched, a process moved. The pipeline is fine and the *meaning* of the data changed.
   This is the most commonly missed cause and the one that produces the longest
   investigations, because everything technical checks out.
7. **Timezone or boundary effects.** DST, month-end cutoffs, a fiscal calendar edge.

### 4. Fix, backfill, verify

- Fix the **pipeline**, not the rows. Hand-editing a warehouse table produces a number
  that is right today and wrong after the next load, and leaves no trace of why.
- Backfill the affected window. State the range explicitly.
- **Verify with numbers, not with a successful re-run.** Report the before and after for
  the check that failed. "Re-ran and it completed" is not verification.
- Re-check the downstream artifacts, not just the table. A fixed mart doesn't fix a
  cached dashboard extract.

### 5. Close the loop

- Update the affected artifacts, and say in each one that the numbers changed and why.
  A silently corrected figure is how people lose trust in every other figure.
- Log the incident in `knowledge/data-quality-log.md` with the window, cause, fix, and
  verification.
- **Add the check that would have caught it earlier** — and add it to
  `pipelines/checks/` so it runs, not to a list of good intentions. An incident that
  doesn't produce a new check will happen again, and the second occurrence damages
  credibility far more than the first.
- If it's the third time for the same cause, escalate it as a design problem. Three
  incidents is not bad luck.

## Standing configuration

- **Escalation contacts:** {{ESCALATION_CONTACTS}}
- **Who can approve a manual data correction:** {{CORRECTION_APPROVER}}
- **Source-system owners** (who to ask when the source, not the pipeline, is wrong):
  {{SOURCE_OWNERS}}
- **Maximum acceptable staleness** before a table is treated as an incident:
  {{STALENESS_SLA e.g. "daily tables: 36 hours; hourly tables: 4 hours"}}

## Post-incident review

For any SEV-1, and any repeat, write a short review into `knowledge/decision-log.md`:
what happened, why, what was slow about the response, and what changed as a result. Blame
the system, not the run — the useful question is never "who missed it" but "what made it
possible to miss".

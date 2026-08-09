# Running the Team on a Schedule

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

The cadence in `CLAUDE.md` §6 — weekly scorecard, monthly scorecard, weekly health check
— is the part of a BI function that only works if it is boring and automatic. A weekly
scorecard that depends on somebody remembering to ask for it lasts about three weeks.

This directory ships three ways to run it unattended. Pick one.

| | Best for | Needs |
|---|---|---|
| **GitHub Actions** (recommended) | teams whose repo is on GitHub | an API key in repo secrets |
| **cron** | a Linux/macOS box or server that's always on | Claude Code CLI installed there |
| **Windows Task Scheduler** | a Windows workstation or server | Claude Code CLI installed there |

All three do the same thing: run `claude -p "/scorecard weekly"` in this repo,
non-interactively, and commit the result.

## What runs, and when

| Job | Schedule | Command |
|---|---|---|
| Weekly scorecard | your `{{WEEKLY_SCORECARD_DAY}}`, early | `/scorecard weekly` |
| Health check | same run, after the scorecard | `/health-check` |
| Monthly scorecard | your `{{MONTHLY_SCORECARD_DAY}}` | `/scorecard monthly` |

Run the health check **after** the scorecard, not before. The scorecard touches the data
and will surface freshness problems the health check can then explain — and if the
scorecard fails outright, the health check output is the first thing you want in the
same log.

## Option 1 — GitHub Actions (recommended)

`github-action-scorecard.yml` is ready to use:

```bash
mkdir -p .github/workflows
cp scheduling/github-action-scorecard.yml .github/workflows/scorecard.yml
```

Then add `ANTHROPIC_API_KEY` under *Settings → Secrets and variables → Actions*, and
adjust the two `cron` lines to your cadence and timezone (GitHub cron is always UTC —
`0 13 * * 1` is Monday 08:00 US Eastern in winter, 09:00 in summer; GitHub does not
observe daylight saving, so pick the hour you can live with year-round).

The workflow commits the generated scorecard back to the repo. That is the audit trail —
each week's numbers, in git, with a diff against last week's.

**Before you enable it**, understand what an unattended agent can reach. It runs with
whatever credentials you put in repo secrets, against whatever warehouse those reach,
with no human to approve a prompt. Give it a **read-only** credential. The
destructive-SQL hook still applies, but a read-only role is the real control.

## Option 2 — cron (Linux / macOS)

```bash
crontab -e
```

```cron
# Weekly scorecard + health check, Mondays at 07:00 local
0 7 * * 1 cd /path/to/agentic-bi-team && ./scheduling/run-scorecard.sh weekly >> /tmp/bi-scorecard.log 2>&1

# Monthly scorecard, 1st of the month at 07:30 local
30 7 1 * * cd /path/to/agentic-bi-team && ./scheduling/run-scorecard.sh monthly >> /tmp/bi-scorecard.log 2>&1
```

cron runs with a minimal environment — it will not source your shell profile, so it will
not see `PROD_REPLICA_URL` or `ANTHROPIC_API_KEY` unless you arrange it. The wrapper
sources `.env` from the repo root if present, which is the simplest fix. Test the exact
command by hand first; almost every cron failure in practice is a missing variable or a
relative path.

## Option 3 — Windows Task Scheduler

```powershell
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "-NoProfile -File `"C:\path\to\agentic-bi-team\scheduling\run-scorecard.ps1`" -Period weekly"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 7am
Register-ScheduledTask -TaskName "BI Weekly Scorecard" -Action $action -Trigger $trigger `
  -Description "Agentic BI Team weekly scorecard and health check"
```

Set the task to *Run whether user is logged on or not*, and put the credentials in
machine-level environment variables — a scheduled task does not inherit your interactive
session's environment.

## Verifying it works

Do not wait a week to find out. For each option:

- **Actions:** trigger it manually — the workflow has `workflow_dispatch` for exactly
  this. Watch the run, then check that `scorecards/` gained a file and the commit landed.
- **cron:** run `./scheduling/run-scorecard.sh weekly` by hand from a clean shell
  (`env -i` if you want to be strict about it), then check the log.
- **Task Scheduler:** right-click the task, *Run*, then check `scorecards/` and the task's
  Last Run Result.

Then check again after the first real scheduled run. The most common failure is not the
command — it's that the credential works in your shell and not in the scheduler's.

## Keeping scheduled runs quiet

An unattended run that produces a page of prose every week gets filtered into a folder
nobody opens. `/health-check` is written to report only failures and changes on a
scheduled run. Keep it that way: **the value of automated monitoring is entirely in
whether the exception still gets read.**

Escalation for a genuinely bad scheduled result — two consecutive reds on a KPI, a
broken connection, a data incident — is a human decision. Configure who gets told, and
how, in `knowledge/incident-runbook.md`. The team does not send anything outward without
authorisation (`CLAUDE.md` §8), so the default is that a bad result sits in the repo
until someone looks. If that isn't good enough for your business, wire the notification
step explicitly.

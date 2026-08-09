# Data Quality Log

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> Data incidents, open quality issues, and the checks that came out of them. Owned by
> `data-quality-engineer`. Read before any data-health sweep and before trusting a
> table you haven't used recently. **Recurrence is the point of this file** — the third
> time a table goes stale, that's a design problem, not an incident.
>
> Business-metric anomalies live in `knowledge/decision-log.md` → Observations. This
> file is for problems with the *data*, not with the business.

## Open issues

| First seen | Table / source | Issue | Severity | Impact | Owner | Status |
|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | |

Severity: **broken** (wrong data, act now) · **degraded** (usable with a stated caveat)
· **cosmetic** (nuisance, logged).

## Incident history

<!-- Template — copy for each incident:
### {{date}} — {{one-line title}}
- **Window:** {{when data was last correct → when it was fixed}}
- **Detected by:** {{scheduled check / user report / analysis that hit it}}
- **Blast radius:** {{dashboards, scorecards, analyses that used the bad data}}
- **Cause:** {{root cause, not the symptom}}
- **Fix:** {{what was changed, and the backfill}}
- **Verified by:** {{the check re-run, with before/after numbers}}
- **New check added:** {{what will catch this earlier — or why nothing can}}
-->

_(No incidents recorded yet.)_

## Standing checks

> What runs, how often, and where it lives. A check that isn't listed here isn't
> running — nobody remembers an ad-hoc query.

| Check | Asserts | Tables | Cadence | Script |
|---|---|---|---|---|
| _(none yet — run `/health-check` or add one under `pipelines/checks/`)_ | | | | |

## Known-bad, accepted

> Data problems the team has decided to live with, so nobody re-investigates them.
> Each needs an expiry or a review date — accepted-forever is how bad data becomes
> invisible.

| Issue | Why accepted | Workaround in use | Review by |
|---|---|---|---|
| _(none yet)_ | | | |

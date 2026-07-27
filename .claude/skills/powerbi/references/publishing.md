# Publishing — getting it in front of people

> Publishing is **outward-facing**. `CLAUDE.md §8` applies: confirm with the user
> before pushing to any broad audience, unless pre-authorised in
> `{{PRE_AUTHORISED_ACTIONS}}`.

## Before publishing anything

1. `validate_pbip.py` clean of errors.
2. Every displayed number reconciled against an independent query, saved in
   `dashboards/<name>/checks/`.
3. Opened in Desktop and visually checked — including the empty state and a
   single-category filter.
4. `dashboards/README.md` inventory row updated.
5. No PII on the canvas, and no real customer values persisted in filter or slicer
   state (`CLAUDE.md §9` — and see `gotchas.md`, filter values do get written into
   `visual.json`).

## Routes

**Power BI Desktop → Publish.** The simple path. One caveat worth understanding:
Desktop's Publish builds a temporary PBIX and uploads **metadata *and* the local data
cache**. Every other route deploys metadata only. If the model was built against a
local extract, that extract goes to the service. Usually not what you want for
anything beyond a demo.

**Fabric Git integration.** The repo becomes the source of truth and the workspace
syncs from it. This is the right long-term shape for a team that already keeps its
work reproducible in git — it makes deployment a merge. Requires `.platform` files,
which Fabric creates.

**Fabric REST API / `fab` CLI (Tier 3).** Scriptable and CI-friendly. Note that
**API deployment requires `byConnection`** in `definition.pbir`, not `byPath` — a
report deployed with a relative model path will fail. Keep a second
`definition-liveConnect.pbir` for this (see `pbip-project-format.md`).

## Choosing

| Situation | Route |
|---|---|
| One-off, small audience, model has real data | Desktop Publish |
| Recurring dashboard, repo is source of truth | Fabric Git integration |
| Automated pipeline / multiple environments | REST API or `fab` |
| Report on an existing published model | thin report, `byConnection` |

## Refresh

The dashboard's refresh promise must be backed by the source. A tile labelled "daily"
on a mart that refreshes weekly is a data-quality defect, and it's the kind that
erodes trust in every other number on the page. Confirm the upstream cadence — this
is `/build-dashboard` step 4 and it's worth re-checking at publish time.

For import models, configure scheduled refresh and, where the source supports it,
incremental refresh. Note that incremental refresh partitions cannot be read or set
through the Fabric REST API.

## Workspace hygiene

- Separate dev and production workspaces; do not develop against the workspace
  stakeholders are reading.
- Deployment pipelines carry content between them with parameterised connections.
- Row-level security roles are defined in TMDL under `roles/`, but **role
  *membership* cannot be set via the REST API** — that stays manual in the service.
- Sensitivity labels are not supported in PBIP. If the organisation requires them,
  they're applied after publishing.

## After publishing

Record it: the inventory row in `dashboards/README.md` (audience, source tables,
refresh, owner, link) and any methodological choices in `knowledge/decision-log.md`.
Set the review date — `standards/dashboard-standards.md` is explicit that a dashboard
nobody retires becomes a dashboard nobody trusts.

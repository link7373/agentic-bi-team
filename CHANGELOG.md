# Changelog

All notable changes to the Agentic BI Team. Versions follow [semver](https://semver.org):
a **major** bump changes the repo layout or a convention that user-filled files depend
on (`/upgrade` will tell you what to do), **minor** adds agents, skills, or standards,
**patch** is fixes and wording.

## [1.1.0] — 2026-09-23

Tableau capability module. Tableau teams get what Power BI teams already had: the
dashboard as a code artifact, spec'd and validated rather than clicked together.

### Added

- **`/tableau` skill** — builds a `.twb` workbook from a compact Python spec rather
  than hand-written XML. Six tested chart recipes (`ban`, `bar_h`, `bar_v`, `line`,
  `bar_stack`, `table`), CSV and live-SQL connections, flat dashboard zones with
  proportional row heights. The builder owns the schema's fixed element ordering so
  callers never have to.
- **`tableau-validator` agent** — the independent gate before a workbook reaches
  Tableau or a stakeholder.
- **`standards/tableau-standards.md`** — Tableau mechanics on top of
  `dashboard-standards.md`, which remains the single source of truth for design.
- **`scripts/validate_twb.py`** — two layers: schema conformance, plus the semantic
  checks the schema cannot express (field and sheet references, extract wiring,
  dashboard viewpoints, CSV header drift, calc sanity, design rules).
- **`scripts/hyper_extract.py`** — `.hyper` extract generation and `.twbx` packaging,
  needed because Tableau Public is extract-only. `tableauhyperapi` is imported lazily,
  so the CSV and SQL paths stay dependency-free.
- **`scripts/extract_runtime_schema.py`** — resolves the schema a local Tableau install
  actually applies. This matters more than it sounds: see below.
- **Worked example** at `.claude/skills/tableau/examples/demo-exec-overview/`, built
  from `demo/demo.db` and verified open in Tableau Public 2026.2.
- **29-assertion regression suite**, including defect cases for every failure that
  reached Tableau during development.

### Learned the hard way

Three findings that cost eight failed loads and are now documented in
`.claude/skills/tableau/references/gotchas.md`:

- **The published XSD is not the schema Tableau applies.** Tableau's real schema is a
  *template* with 91 `<!--?IF Feature -->` branches, resolved at open time from the
  flags a workbook declares in `<document-format-change-manifest>` — bare element
  names, documented nowhere. `validate_twb.py` therefore prefers the extracted runtime
  schema and warns (`SCH002`) when falling back to the published one.
- **`@version` is the format version (`18.1`), not the Tableau release.** Setting it to
  a release resolves a different, much stricter schema.
- **Get a reference workbook first.** One workbook Tableau itself wrote answered more
  questions than days of schema reading. `gotchas.md` opens with the one-liner to fetch
  one.

The wider lesson, also recorded there: **an error message names a symptom, not a
cause.** Four rounds went into fixing whatever Tableau's error named; two diagnostic
workbooks that isolated the failure found it immediately.

### Changed

- `/build-dashboard` step 5 hands the Tableau branch to `/tableau`, as it already did
  for Power BI. The "produce importable artifacts plus instructions" fallback no longer
  applies to Tableau.
- `.gitignore` — `*.hyper`, `*.twbx` and `hyperd.log` are generated binaries; the
  `.twb`, `build.py` and SQL remain tracked as the reproducible layer.

## [1.0.0] — 2026-08-08

The production-readiness release. The team could already do the work; this release
makes it safe to run a real company's BI on it — the bootstrap can be undone, the
repo checks itself, the cadence actually runs on a schedule, and a new user can see
output in ten minutes without a warehouse.

### Added

- **`data-quality-engineer` agent** — owns data health as a distinct job from
  business-metric monitoring: freshness SLAs, volume and schema drift, null and
  duplicate profiling, and pipeline incident triage. Logs to
  `knowledge/data-quality-log.md`.
- **`/health-check`** — the team's self-audit. Runs the repo lint, placeholder scan,
  metric-catalog check, and live connection tests; reports staleness in the knowledge
  base and drift between the directory inventories and what's on disk. Doubles as the
  post-setup smoke test and a weekly scheduled job.
- **`/connect-data`** — guided, one-source-at-a-time connection setup. Drives
  `scripts/test_connection.py` and writes only *tested* results into
  `knowledge/data-sources.md`.
- **`/triage`** — request intake. Classifies an incoming ask, sizes it, routes it, and
  logs it in `knowledge/request-log.md` so ad-hoc work stops being invisible.
- **`/upgrade`** — pulls framework changes from a newer release into a repo you have
  already configured, without touching your filled-in knowledge base.
- **Demo mode** — `demo/generate_demo_data.py` builds a fictional B2B SaaS warehouse
  in SQLite (standard library, no installs) with three planted findings, and
  `demo/DEMO-CHARTER.md` is a pre-filled charter. `/setup-team` offers it as a branch,
  so first output takes about ten minutes and no warehouse.
- **Scheduling assets** — `scheduling/` ships a GitHub Actions workflow, a shell
  wrapper, a PowerShell wrapper, and `SCHEDULING.md`. The weekly/monthly cadence in
  `CLAUDE.md` §6 is now something that runs, not something you remember.
- **Safety rails** — `.claude/settings.json` with a least-privilege permission set, and
  a `PreToolUse` hook (`scripts/hooks/block_destructive_sql.py`) that blocks
  `DROP` / `TRUNCATE` / unqualified `DELETE` / `GRANT` / `REVOKE` reaching a warehouse
  CLI. Explained line by line in `docs/settings.md`.
- **Bootstrap safety** — `scripts/setup_backup.py` snapshots every file `/setup-team`
  writes and restores them on demand; `/setup-team` gained a pre-flight step and a
  dry-run that shows the placeholder mapping before writing anything.
- **Repo self-checks** — `scripts/lint_repo.py` (agent/skill counts, routing-table
  coverage, frontmatter, attribution, link resolution),
  `scripts/check_placeholders.py` (template and post-setup modes), and
  `scripts/check_metrics.py` (catalog schema and cross-references), all wired into
  `.github/workflows/ci.yml` alongside the Power BI regression suite — which now runs
  somewhere other than a developer's laptop.
- **Machine-readable metrics** — each entry in `knowledge/metrics-catalog.md` carries a
  fenced YAML block (name, definition, grain, owner, `generic_sql`, optional
  tool-specific SQL/DAX). One file is still the source of truth; it is now checkable.
- **Incident runbook** (`knowledge/incident-runbook.md`) and a stakeholder SLA section,
  so a broken pipeline has a declared path instead of an improvised one.
- **Directory inventories** for `analyses/`, `models/`, `scorecards/`, and
  `deliverables/`, matching the existing pattern in `pipelines/`. The "check for prior
  work" step in several skills now has something to read.
- **`.env.example`**, `CONTRIBUTING.md`, `VERSION`, and this changelog.
- **Tableau and Looker** got real sections in `standards/dashboard-standards.md`, and
  `standards/data-modeling-standards.md` gained a "working alongside dbt" section.

### Changed

- **Agent frontmatter** — `powerbi-validator`, `performance-monitor`, `metrics-steward`,
  and `data-quality-engineer` now declare explicit `tools:` and `model:`. The four are
  read-and-verify roles; the analysis and build agents keep the full toolset.
- **Attribution** — the four-line author block was replaced by a single line in every
  file that gets loaded into an agent's context (`.claude/`, `knowledge/`,
  `standards/`, directory READMEs). Reader-facing docs keep the full block. A lint rule
  keeps it that way.
- **`metrics-steward`** gained a privacy-and-access section; **`performance-monitor`**
  gained warehouse-cost governance.
- **Placeholder convention**, now enforced: `{{UPPER_SNAKE}}` is filled by
  `/setup-team` and must be gone afterwards; `{{lowercase prose}}` is a per-entry blank
  a human fills and stays for the life of the file.

### Fixed

- The README and `/setup-team` claimed 8 agents (there were 9) and the README claimed
  11 skills in one place and 12 in another. `lint_repo.py` now fails CI on any
  disagreement, so this class of drift cannot return.

# Agentic BI Team for Claude Code

A complete, self-sustained **Business Intelligence & Data Analytics team** that you run with [Claude Code](https://code.claude.com). Fill out one plain-English charter document, run one command, and you have a configured virtual team that covers everything a real BI team does:

- **ETL & data pipelines** — ingest from source systems, layered raw→staging→marts models, quality gates
- **Summary tables from huge datasets** — fast, pre-aggregated tables at the right grain
- **Ad-hoc analysis & short reports** — business questions answered with reproducible queries
- **Cross-database joins** — complex analysis spanning CRM + billing + product data, with match-rate honesty
- **Weekly & monthly performance scorecards** — fixed KPI set, status colours, narrative explanations
- **Dashboards** — Tableau, Power BI, Looker, or self-contained HTML, with consistent design standards
- **Proactive monitoring** — anomaly detection and structured root-cause analysis when metrics underperform
- **KPI & metric definition** — industry-best-practice metric trees with anti-gaming guardrails
- **Machine learning** — churn/propensity models, forecasting, segmentation, A/B test design, model cards
- **Executive deliverables** — PowerPoint, Word, Excel (and Google Workspace equivalents) built from analysis
- **Domain learning** — researches your industry, benchmarks, and competitors, and remembers what it learns

Everything is plain Markdown. No app, no SaaS, no lock-in — the "team" is a set of instruction files that Claude Code reads.

---

## How it works

```
                    ┌─────────────────────────────┐
   You (plain      │  CLAUDE.md  (Head of BI)     │   routes work, QAs output,
   English) ─────► │  reads knowledge/, applies   │   delivers finished results
                    │  standards/, delegates to:   │
                    └──────────────┬──────────────┘
        ┌──────────┬──────────┬────┴─────┬──────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼          ▼
   data-      analytics-   bi-      dashboard-  data-     insights-
   engineer   engineer     analyst  developer   scientist communicator
        (+ metrics-steward and performance-monitor)
```

Three layers make it self-sustaining:

| Layer | Files | Role |
|---|---|---|
| **Orchestration** | `CLAUDE.md` | The Head of BI: business context, routing rules, operating principles, escalation rules. Claude Code loads this automatically every session. |
| **Specialists & workflows** | `.claude/agents/*.md`, `.claude/skills/*/SKILL.md` | 8 subagents with deep role-specific instructions; 10 slash-command workflows with step-by-step procedures. |
| **Memory & standards** | `knowledge/*.md`, `standards/*.md` | The team's long-term memory (data quirks, metric definitions, stakeholder preferences, decisions) and house style. Agents read these before working and write back what they learn. |

## Repository layout

```
├── CLAUDE.md                  Master orchestrator (auto-loaded by Claude Code)
├── START-HERE.md         ← YOU fill this out, once, in plain English
├── README.md                  This file
├── .claude/
│   ├── agents/                8 team members (Claude Code subagents)
│   │   ├── data-engineer.md          ETL, ingestion, data quality
│   │   ├── analytics-engineer.md     summary tables, marts, metric layer
│   │   ├── bi-analyst.md             analysis, cross-DB joins, deep dives
│   │   ├── dashboard-developer.md    Tableau / Power BI / Looker
│   │   ├── data-scientist.md         ML, forecasting, experiments
│   │   ├── metrics-steward.md        KPI definitions & governance
│   │   ├── performance-monitor.md    scorecards, anomalies, root cause
│   │   └── insights-communicator.md  decks, docs, spreadsheets
│   └── skills/                10 workflows (slash commands)
│       ├── setup-team/        /setup-team — configures everything from your charter
│       ├── build-pipeline/    /build-pipeline — ETL & summary tables
│       ├── analyze/           /analyze — business-problem analysis
│       ├── scorecard/         /scorecard weekly|monthly
│       ├── build-dashboard/   /build-dashboard
│       ├── investigate-metric//investigate-metric — anomaly & root cause
│       ├── define-kpis/       /define-kpis
│       ├── build-model/       /build-model — ML development
│       ├── make-deliverable/  /make-deliverable — slides / docs / Excel
│       └── research-domain/   /research-domain — industry & product learning
├── knowledge/                 Long-term memory (populated by /setup-team, grown over time)
│   ├── business-context.md    company, priorities, glossary, change ledger
│   ├── data-sources.md        connections, table inventory, join keys, landmines
│   ├── metrics-catalog.md     THE source of truth for every metric definition
│   ├── stakeholders.md        audiences, preferences, distribution rules
│   ├── industry-notes.md      research briefings & benchmarks
│   └── decision-log.md        methodological decisions & observations
├── standards/                 House style applied to all output
│   ├── sql-and-data-standards.md
│   ├── dashboard-standards.md
│   └── reporting-standards.md
└── analytics.md               Standing analytical framework — statistical reasoning & visualization principles
```

Working artifacts are created as the team operates: `analyses/`, `pipelines/`, `dashboards/`, `models/`, `scorecards/`, `deliverables/`.

---

## Quick start

### Prerequisites

- [Claude Code](https://code.claude.com) (CLI, desktop, or web)
- Some way for Claude Code to reach your data — a CLI client (`psql`, `bq`, `snowsql`, `sqlite3`...), an MCP server for your warehouse, or even just CSV files in the repo. Don't worry if this isn't set up; `/setup-team` will help you sort it out.
- Optional: Python 3 (used for ML and for generating .pptx/.docx/.xlsx deliverables — packages are installed on demand)

### 1. Get the kit

```bash
git clone https://github.com/link7373/virtual-bi-team.git my-bi-team
cd my-bi-team
claude
```

The `.claude/` folder must be at the root of the workspace Claude Code opens — that's how the agents and skills load. (Run `/agents` inside Claude Code to confirm the 8 team members are visible.)

### 2. Fill out the charter

Open `START-HERE.md` and answer its questions **in plain English** — bullet points and brain dumps are fine, no technical vocabulary needed. It covers seven areas:

1. **The business** — what you do, how you make money, top priorities, the one number that matters
2. **Your data** — where it lives, roughly how big, how to connect, known problems
3. **Metrics & reporting** — what you measure today, what you wish you could answer, who reads reports, scorecard cadence
4. **Tools & outputs** — dashboard tool (Tableau / Power BI / Looker / none), deliverable formats, branding
5. **Advanced analytics** — predictions you'd value, Python environment
6. **Rules & boundaries** — privacy/compliance rules, things the team must never do without asking, things it's pre-authorised to do
7. **Context & quirks** — fiscal year, timezone, company jargon, history a new hire should know

**Leave blank anything you don't know.** The setup process asks about gaps and applies sensible defaults for the rest.

### 3. Run setup

In Claude Code:

```
/setup-team
```

This reads your charter and:
- asks you one batched round of clarifying questions for anything ambiguous,
- **tests every data connection you named** and records exactly what works (and what's blocked, and why),
- discovers your database schemas and builds a table inventory,
- replaces every `{{placeholder}}` across all files with your real configuration,
- seeds a draft KPI list appropriate to your business model, and
- reports back with a suggested first task.

From this point the team is live.

---

## Configuration reference

### The placeholder system

Every file ships with `{{PLACEHOLDERS}}` marking where your configuration goes — `{{COMPANY_NAME}}`, `{{BI_TOOL}}`, `{{DATA_PRIVACY_RULES}}`, scorecard thresholds, brand colours, and so on. `/setup-team` fills them from your charter. To find anything still unconfigured:

```bash
grep -rn "{{" --include="*.md" .
```

You can also edit any file by hand at any time — they're just Markdown, and hand edits are equally authoritative.

### Connecting your data

The team reads connection details from `knowledge/data-sources.md`. Three patterns, in order of preference:

1. **MCP server** for your warehouse (BigQuery, Snowflake, Postgres, etc.) configured in Claude Code — gives the team direct, permissioned query access.
2. **CLI client** available in the shell (`psql`, `bq`, `snowsql`, `duckdb`, `sqlite3`) with credentials in environment variables — the team records the exact working command.
3. **Files** — CSV/Parquet exports dropped into the repo; the team will analyse them with DuckDB/pandas and tell you what regular exports it needs.

`/setup-team` verifies whichever you have with live test queries; nothing is recorded as "working" untested.

### Configuring the BI tool

Set your tool in the charter (or directly in `CLAUDE.md` and `dashboard-developer.md`). The dashboard developer carries tool-specific build rules for **Tableau** (published data sources, extracts), **Power BI** (star schema, thin DAX), and **Looker** (LookML kept in this repo). If Claude Code has no direct API access to your tool, the team produces complete import-ready artifacts plus exact setup instructions. With **no BI tool at all**, it builds self-contained HTML dashboards regenerated by script.

### Tuning behaviour

| Want to change | Edit |
|---|---|
| Routing, operating principles, escalation rules | `CLAUDE.md` |
| What a specific role does or how it works | `.claude/agents/<role>.md` |
| The steps of a workflow | `.claude/skills/<name>/SKILL.md` |
| Metric definitions, targets, scorecard thresholds | `knowledge/metrics-catalog.md` (or run `/define-kpis`) |
| SQL conventions, naming, quality gates | `standards/sql-and-data-standards.md` |
| Chart/colour/layout rules | `standards/dashboard-standards.md` |
| Report structure, tone, branding | `standards/reporting-standards.md` |
| Who gets what, in which format | `knowledge/stakeholders.md` |

### Safety rails

Two placeholders in `CLAUDE.md` §8 govern autonomy, set from your charter:
- **Never without asking:** destructive actions and outward-facing distribution always require confirmation unless you pre-authorise them.
- **Pre-authorised:** things the team may do freely (e.g. "read any table", "create tables in the dev schema").

Privacy rules (`{{DATA_PRIVACY_RULES}}`) propagate to querying, dashboards, and deliverables, including minimum aggregation sizes.

---

## Day-to-day usage

Just talk to it — the orchestrator routes to the right specialists:

> "Why did signups drop last week?" → root-cause investigation
> "I need a board deck on Q2 performance" → analysis → deck, with an outline shown to you first
> "Our queries on the events table take forever" → summary-table design and build
> "Which customers are likely to cancel?" → screening question first (is a model even needed?), then ML workflow

Or invoke workflows directly:

| Command | What happens |
|---|---|
| `/analyze why is enterprise churn rising` | Framed, profiled, pressure-tested analysis with a written FINDINGS.md |
| `/scorecard weekly` | This week's scorecard in `scorecards/`, every red/yellow explained |
| `/investigate-metric signups down 20%` | Data-problem check → localisation → timeline → tested hypotheses → verdict with confidence |
| `/build-pipeline daily revenue summary from billing` | Design doc → layered build → quality gates → docs |
| `/build-dashboard exec revenue overview` | Spec (confirmed with you) → data layer → build → number-by-number validation |
| `/define-kpis` | Metric tree + rigorous catalog definitions + targets, ratified with you |
| `/build-model churn prediction` | Leakage-safe dataset → baseline → model → business-terms evaluation → model card |
| `/make-deliverable churn analysis as exec deck` | Pyramid-structured .pptx with every figure source-mapped |
| `/research-domain SaaS churn benchmarks` | Sourced, dated briefing in `knowledge/industry-notes.md` |

### Running on a schedule

The scorecards and monitoring are designed for recurring runs. Options:

- **Headless CLI:** `claude -p "/scorecard weekly"` from cron or any scheduler.
- **Claude Code web:** start a session on this repo and ask for the scorecard; or use a GitHub Action that invokes Claude Code on a schedule.
- **Manual:** just run `/scorecard weekly` each Monday — it takes one command either way.

### How the team stays smart

The knowledge files are working memory, not documentation theatre — agents are instructed to read them before tasks and write back after: data quirks land in `data-sources.md`, definition rulings in `metrics-catalog.md` + `decision-log.md`, stakeholder reactions in `stakeholders.md`, business events in the change ledger (which powers root-cause timelines). Commit the repo regularly; the git history is the team's institutional memory.

Re-run `/setup-team` after major changes (new warehouse, new product line, reorg) — it merges new facts without wiping accumulated knowledge.

---

## Extending the team

- **Add a team member:** create `.claude/agents/<name>.md` with frontmatter (`name`, `description`) + role instructions, and add a row to the routing table in `CLAUDE.md` §3. Useful additions: a financial analyst, an experimentation specialist, a data-governance officer.
- **Add a workflow:** create `.claude/skills/<name>/SKILL.md` (frontmatter + numbered procedure) and list it in `CLAUDE.md` §4.
- **Industry packs:** the metrics-steward and `/define-kpis` adapt to your business model from the charter; for deep vertical needs, extend `knowledge/metrics-catalog.md` and `industry-notes.md` directly.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Agents/skills don't appear | `.claude/` must be at the root of the folder Claude Code opened. Check with `/agents`. |
| Team asks for context it should know | Placeholders left unfilled — run the grep above, or re-run `/setup-team`. |
| Two reports disagree on a number | That's a metrics-steward job: say "these two numbers disagree" and it will reproduce both, rule, and fix the deviating artifact. |
| Data connection broke | Update `knowledge/data-sources.md` (or tell the team — it will retest and update the file). |
| Output style isn't right | Edit the relevant `standards/` file once; every future artifact follows it. Log stakeholder-specific reactions in `knowledge/stakeholders.md`. |

## License & disclaimer

Use freely. The kit is instructions, not advice — validate business-critical numbers and decisions the same way you would coming from any analyst.

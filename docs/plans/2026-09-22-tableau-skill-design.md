# Design — `/tableau` skill (Tier 0–1)

Date: 2026-09-22
Status: approved
Author: Colin Beck (with Claude)

## Problem

The team can build Power BI dashboards as code via `/powerbi` (PBIP → TMDL + PBIR,
validated by `validate_pbip.py`). Tableau teams get nothing equivalent —
`/build-dashboard` step 5 tells them to produce "`.twbx` instructions" for a human to
follow by hand.

As of February 2026 this gap is closable. Tableau published official XSD schemas for
the TWB format ([tableau/tableau-document-schemas](https://github.com/tableau/tableau-document-schemas),
Apache-2.0), explicitly as "a reference for developers and **agents** to build and
validate TWBs against an official standard". A `.twb` is plain XML that Tableau Desktop
and Tableau Public open directly — the structural equivalent of PBIP.

## Scope

**In:** Tier 0 (spec only) and Tier 1 (author `.twb`, validate against vendored XSD,
human opens it in Tableau Desktop/Public).

**Out:** Tier 2 (REST semantic validation, publish, `Query View Image` render loop) —
named in the tiers doc so the path is visible, not implemented. `.twbx` packaging —
the official schema explicitly excludes packaged workbooks. Dual-axis, scatter, maps.

Everything gated behind `{{BI_TOOL}}` being Tableau; a Power BI or Looker team sees no
change (see `tool-neutrality-principle`).

## Key schema finding

`WorkbookFile-CT` is an `xs:sequence` of 23 groups. Element order in a `.twb` is
significant and schema-fixed (`preferences` → `style` → `datasources` → `worksheets` →
`dashboards` → `windows` → …). Correct elements in the wrong order fail XSD.

This is the main argument for generating the skeleton rather than hand-typing it.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Authoring model | Python builder + recipes | A Tableau worksheet is 150–250 lines of boilerplate-heavy XML with strict ordering. Claude writes a ~30-line spec, not ~800 lines of XML. Deterministic, testable. |
| Data connection | CSV **and** live SQL from the start | CSV (`textscan`) needs no drivers and works in Tableau Public. SQL blocks for Postgres/BigQuery/Snowflake ship documented but **render-unverified** — labelled as such. |
| Chart coverage | Core 6 | `ban`, `bar_h`, `bar_v`, `line`, `bar_stack`, `table`. Covers most exec/ops dashboards and matches what `dashboard-standards.md` steers toward. Six tested recipes beat twelve half-working ones. |
| Render check | Human opens it | No computer-use loop. **Consequence: the validator carries more weight** — it is the only feedback signal before the file reaches a human, so cross-reference checks XSD can't do are load-bearing, not nice-to-have. |

## Architecture

```
.claude/skills/tableau/
├── SKILL.md                    thin procedure — mirrors powerbi/SKILL.md
├── schemas/
│   ├── twb_2026.2.0.xsd        vendored, Apache-2.0
│   └── LICENSE.txt
├── scripts/
│   ├── twb_builder.py          spec → .twb XML   (generator)
│   └── validate_twb.py         .twb → findings   (gate)
├── references/
│   ├── tooling-tiers.md
│   ├── workbook-spec.md        the spec format Claude writes
│   ├── chart-recipes.md        the 6 types
│   ├── connections.md          CSV textscan + warehouse blocks
│   ├── calculated-fields.md    calc syntax, LOD/FIXED filter trap
│   └── gotchas.md              silent-failure catalogue
└── tests/run_tests.py + fixtures/
standards/tableau-standards.md          mechanics only
.claude/agents/tableau-validator.md
```

## Data flow

```
mart ──► CSV export ──┐
                      ├──► spec (dict) ──► twb_builder ──► .twb ──► validate_twb ──► human opens
warehouse ──► SQL ────┘                                              │                    │
                                                                 XSD + semantic      feedback ──┘
```

Builder contract: `build_workbook(spec) -> str`. Builder owns the schema sequence.
Writes UTF-8 **no BOM**, LF endings.

## Validation

Same `Finding(code, severity, path, message, hint)` shape and 0/1/2 exit codes as
`validate_pbip.py`.

| Code | Sev | Check |
|---|---|---|
| `TWB001` | ERROR | XSD validation against 2026.2 |
| `ENC001` | ERROR | UTF-8 BOM |
| `REF001` | ERROR | worksheet field ref exists in datasource |
| `REF002` | ERROR | dashboard zone → existing worksheet |
| `CSV001` | ERROR | referenced CSV exists; headers match declared columns |
| `CALC001` | WARN | calc syntax: balanced brackets/parens, known functions |
| `DSN001` | WARN | live connection with no extract |
| `DSG001` | WARN | banned chart type / non-zero-anchored bar axis |

Rows 3–8 exist because Tableau's own README states the XSD "doesn't cover ...
calculated field contents, and references to workbook elements".

## Testing

1. Unit — each of the 6 chart types builds and passes XSD.
2. Negative — a broken spec must produce the right code. A validator that never fails
   proves nothing.
3. Proof — `.claude/skills/tableau/examples/demo-exec-overview/` off `demo/demo.db`, opened in Tableau
   Public 2026.2 by a human.

## Primary risk

XSD-valid does not mean it opens. Tableau draws exactly this line, and the closest
prior art says it outright: *"the validators are not Tableau."* Expect the first `.twb`
to fail on something the XSD accepted. That iteration is the real work.

Nothing is committed to `main` until a human has seen it render.

---

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

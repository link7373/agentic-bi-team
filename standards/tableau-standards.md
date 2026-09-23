# Tableau Standards

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/


> Applies when `{{BI_TOOL}}` is Tableau. This file covers **Tableau mechanics only**.
> All chart selection, colour, layout, and decluttering rules live in
> `standards/dashboard-standards.md` and are not restated here - there is one source of
> truth for design, and this isn't it.

## Project layout

Every dashboard is a folder, and the folder is a build, not a saved file:

```
dashboards/<name>/
├── SPEC.md                      audience, questions, metrics, layout
├── build.py                     regenerates the extract AND the workbook
├── <Name>.twb                   generated - do not hand-edit
├── data/<extract>.csv           generated
├── checks/                      reconciliation queries
└── screenshot.png
```

**`build.py` is the source; the `.twb` is an output.** A workbook someone once
saved in Desktop is not reproducible - nobody can tell what query produced the
numbers. A script that rebuilds both the extract and the workbook is
(`CLAUDE.md` principle 3). Hand-edits to a generated `.twb` are lost on the next
build, silently.

The `.twb` and the build script are **tracked in git deliberately** - a `.twb` is
plain XML and diffs cleanly. Extracts and rendered blobs follow the repo's
existing `.gitignore` rules by file type.

## Naming

Sheet names must be unique within a workbook - the builder raises `SpecError`
otherwise, because dashboard zones reference sheets by name and a duplicate makes
the reference ambiguous.

Unlike Power BI, Tableau permits spaces and punctuation in sheet and dashboard
names, and they surface directly to users. Use the name a stakeholder would say
out loud. Sheet names appear in the dashboard, so "Revenue by Segment" beats
"sheet1" and beats "rev_by_seg".

## Data layer

- **One grain per workbook.** The builder emits one datasource, so every sheet
  shares one flat table. Mixing grains - monthly revenue with per-ticket rows -
  duplicates the coarser measure across finer rows and inflates every total. This
  is the most common way one of these dashboards is quietly wrong. Aggregate to a
  common grain in the mart, or build two workbooks.
- **Read from marts.** No heavy transformation in the workbook. If it needs a
  join, a window function, or business logic, it belongs upstream with
  `analytics-engineer` where it is testable and reusable (`CLAUDE.md` principle 7).
- **Extracts over live connections** for anything a human waits on. Every filter
  click on a live connection is a query and a cost. Live is right only when
  sub-hourly freshness genuinely changes a decision. Record the refresh schedule
  in `dashboards/README.md` - an extract nobody refreshes is a dashboard that is
  quietly wrong.
- **Declare every field** the workbook references. An undeclared field is a blank
  sheet, and it is schema-valid, so only the semantic validator catches it.

## Calculated fields

- **Presentation logic only, never business definitions.** A metric defined in a
  workbook is invisible to `knowledge/metrics-catalog.md` and to every other
  workbook, which is exactly how two dashboards start disagreeing. If a
  calculation is reused, it is a mart column.
- Names match `knowledge/metrics-catalog.md` **character for character**. A metric
  not in the catalog goes through `/define-kpis` first (`CLAUDE.md` principle 2).
- **`FIXED` ignores the view's filters** unless they are context filters. The
  classic bug is a total that does not respond to the dashboard's own filter - it
  looks like a rounding quirk and is a wrong number. Reconcile any LOD expression
  against SQL before shipping, and say in `SPEC.md` which filters it deliberately
  ignores.
- Ratios from summed numerator over summed denominator, never an average of
  per-row ratios - that gives a wrong total row.

## Dashboard

Design rules come from `standards/dashboard-standards.md`. Tableau adds only:

- **Actions over navigation.** Dashboard actions (filter, highlight, go-to-sheet)
  keep one dashboard answering one question with a drill path, instead of five
  near-duplicate dashboards.
- **Colour once, at the workbook level**, not per worksheet, so the semantic
  status colours stay consistent across sheets.
- Every tile reads from the shared extract - no per-sheet data wrangling.

## Privacy

An extract is an export. `CLAUDE.md` §9 applies to `data/*.csv` exactly as it does
to any other export - if the mart has PII, the extract has PII, and it is sitting
on disk as plaintext next to a file people pass around. **Aggregate before
exporting**; do not export everything and then hide columns in the workbook,
which protects nothing.

Filter selections persist into the `.twb`. A sheet filtered to a named customer
writes that name into a tracked file. Check before committing.

**Never write a password into a spec, a build script, or a `.twb`.**
`sql_connection()` takes a username and no password by design. Tableau prompts on
open or uses a saved credential.

## Validation gate

Nothing ships without:

1. `python .claude/skills/tableau/scripts/validate_twb.py dashboards/<name>` clean
   of errors - warnings triaged, not ignored.
2. The workbook **opened in Tableau Desktop or Tableau Public** and confirmed to
   render. Validation proves the files are well-formed; only Tableau proves the
   dashboard works. Tableau's own schema documentation is explicit that the XSD
   does not cover calculated field contents, connection attributes, or references
   between workbook elements.
3. Every displayed number reconciled against an independent query saved in
   `dashboards/<name>/checks/`.
4. Empty state and single-category filter tested.
5. `dashboards/README.md` inventory updated, with a review date.

For anything stakeholder-facing, `tableau-validator` runs an independent pass
before release.

## Working on an open workbook

Close Tableau before running `build.py`, and reopen afterwards. Tableau does not
watch the filesystem and will overwrite your rebuild from its in-memory copy on
the next save. This is the most common way to lose work here.

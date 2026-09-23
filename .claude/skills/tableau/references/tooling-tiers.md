# Tooling Tiers - what the team can actually do

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> Read at `/tableau` step 2. Detect the tier, state it, then work within it.

Tableau capability is not binary. Each tier below unlocks more, and **any one of
them is enough to be useful** - the same philosophy as `knowledge/connections.md`
for warehouse access.

## Detect

```bash
python --version                  # Tier 1 needs 3.9+
python -c "import lxml; print(lxml.__version__)"   # XSD validation
ls "/c/Program Files/Tableau"     # Windows: Desktop and/or Public
ls /Applications | grep -i tableau                 # macOS
```

Tableau Public installs to `C:\Program Files\Tableau\Tableau Public <version>\bin\tabpublic.exe`
on Windows. Tableau Desktop sits beside it as `Tableau <version>\bin\tableau.exe`.

## The tiers

| Tier | Needs | Unlocks |
|---|---|---|
| **0 - Spec only** | nothing | `SPEC.md`, layout sketch, field list, the workbook spec itself. Everything except a file anyone can open. |
| **1 - .twb authoring** *(default)* | Python + lxml, and Tableau Public (free) or Desktop to open the result | Author and validate the whole workbook: connection, fields, sheets, dashboard layout. Validate with `scripts/validate_twb.py`. Human opens it to confirm it renders. |
| **1.5 - exact validation** | Tier 1 + a local Tableau install | `scripts/extract_runtime_schema.py` reads Tableau's own schema template out of the install and resolves it for the feature flags the workbook declares. `validate_twb.py --runtime` then checks against what Tableau will really apply, instead of the published XSD. Strongly recommended - the two genuinely disagree. |
| **2 - Server/Cloud connected** | Tableau Cloud or Server 2026.2+, credentials | REST semantic validation without publishing, publish, extract refresh schedules, `Query View Image` render-back. **Not implemented in this module** - see below. |

**Tier 1 is not a fallback.** It is genuinely sufficient to build a complete,
correct dashboard. Do not stall waiting for Tier 2.

### Tableau Public is extract-only

Connecting Tableau Public to a CSV through the UI works - because Public
**silently converts it to an extract on connect**. Public supports no live
connections whatsoever.

A generated workbook gets no such conversion. A live `textscan` connection with
no `<extract>` fails to **open** with error 3C242D89 ("The data source ... is
not an extract"), despite the message talking about saving.

Targeting Tableau Public therefore means: `csv_connection(..., extract=True)`,
`write_hyper(...)`, and `package_twbx(...)`, because the `<extract>` connection
stores a package-relative path (`Data/Extracts/x.hyper`). That needs
`tableauhyperapi` - see `scripts/hyper_extract.py`.

Tableau **Desktop** opens a live connection directly and needs none of this.

### Without lxml

XSD validation is skipped and `validate_twb.py` says so explicitly in a `SCH001`
warning; every semantic check still runs. That is a partial answer, and it
reports itself as partial. Install with `pip install lxml` to close the gap.

## Tier 2 - named, not built

Tableau Cloud (June 2026) and Server 2026.2 added REST endpoints that validate a
TWB **without publishing it**:

- `Validate Workbook`
- `Validate Workbook and Upload`
- `Validate Uploaded Workbook`

These do syntactic validation against the XSD *and* semantic validation - "will
this actually open in Tableau", which is precisely the gap this module cannot
close locally. Combined with `Query View Image`, they would let an agent publish,
render to PNG, judge its own output against `standards/dashboard-standards.md`,
fix, and repeat.

**This module deliberately stops short of that.** Tier 2 needs a Tableau
Cloud/Server tenant that this project has never had access to, and shipping an
unverified integration is worse than shipping none. If the team has a tenant, the
path is: `tableauserverclient` (official, actively maintained) for publish and
render, plus the validate endpoints above. Verify the endpoints exist on your
actual tenant version first - they are recent, and Tableau's REST "What's New"
page did not list them at the time this module was written.

## Related official tooling, and what it is good for

- **[tableau/tableau-mcp](https://github.com/tableau/tableau-mcp)** - Tableau's
  official MCP server, Apache-2.0. Read-oriented: query published data sources,
  find workbooks, render views. It does **not** author or publish dashboards, so
  it complements this module rather than replacing it. Useful for step 8's
  reconciliation, if the team has it connected.
- **[tableau/server-client-python](https://github.com/tableau/server-client-python)** -
  the official REST client. This is the right dependency if Tier 2 ever gets built.
- **[tableau/document-api-python](https://github.com/tableau/document-api-python)** -
  official but explicitly **unsupported**, and its last PyPI release was November
  2022. Do not build on it.

## Credit

The idea of closing the loop by rendering a dashboard and scoring it against a
design rubric comes from [**vizwright**](https://github.com/collinalldata/vizwright)
by Blake Feiza. The honesty about generated workbooks being unproven until
Tableau itself opens them - "the validators are not Tableau" - is from
[**tableau-dashboard-creator-skill**](https://github.com/laviDrori0702/tableau-dashboard-creator-skill)
by Lavi Drori. Both are worth reading directly.

**No code or text was copied from either project.** This module is original work
written against Tableau's published XSD schemas and REST documentation. It also
does not depend on [`cwtwb`](https://github.com/aidatacooper/cwtwb), which is the
most capable open-source TWB generator but is **AGPL-3.0** - a licence the team
should choose deliberately rather than inherit silently through a dependency.

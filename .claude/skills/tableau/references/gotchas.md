# Gotchas - the silent-failure catalogue

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

> Every entry here cost real time to find, most of them by generating a
> workbook, watching Tableau refuse to open it, and reading the error. Read
> this before debugging a workbook that "should work".

## The one that matters most: get a reference workbook first

Tableau's published XSD tells you what is *possible*. Only a workbook Tableau
itself wrote tells you what it *does*. Those are not the same document, and the
difference cost five failed loads during this module's development.

**Before changing anything structural, get ground truth:**

```bash
curl -sL "https://public.tableau.com/workbooks/SuperSampleSuperstore.twb" -o ref.twbx
# despite the .twb URL it is a .twbx (zip); the workbook is inside
python -c "import zipfile;z=zipfile.ZipFile('ref.twbx');print(z.namelist())"
```

Any Tableau Public viz works: `public.tableau.com/workbooks/<WorkbookName>.twb`.
Diff its `<workbook>` attributes, its manifest, and its element inventory
against what you generate. That one file answers questions no amount of schema
reading will.

## Every dashboard sheet needs a `<viewpoint>` in the dashboard's window

The error:

```
Dashboard references sheet 'X' which has no visual representation
in the workbook. Error Code: 2805CF18
```

reads like a problem with sheet X. It is not. The sheet renders perfectly on
its own tab. What is missing is a `<viewpoint>` for it in that dashboard's
`<window>`:

```xml
<window class='dashboard' maximized='true' name='Exec Overview'>
  <viewpoints>
    <viewpoint name='Total Revenue'><zoom type='entire-view' /></viewpoint>
    <viewpoint name='Revenue Trend'><zoom type='entire-view' /></viewpoint>
    ...
  </viewpoints>
  <active id='-1' />
```

The correspondence is exact: in a reference workbook, 22 viewpoints for 22 zone
sheets, zero mismatch in either direction. An empty `<viewpoints />` means no
sheet on the dashboard has a "visual representation", and Tableau names the
first zone.

Nothing in the schema requires any of this, so validation passes. `REF007`
catches it now.

**How this was found, because the method matters more than the fact:** four
rounds were spent fixing whatever the error named - the mark class, the
`<cols>` map, the extract metadata, the zone nesting. Each was a real
difference from Tableau's output; none was the cause. What actually found it
was two diagnostic workbooks: one with all the sheets and no dashboard (every
sheet rendered, clearing the sheets entirely), then one with a single known-good
sheet and a one-zone dashboard (still failed, clearing the sheets' content and
the layout). That left the dashboard element itself, and the only part of it
not yet compared against the reference was `<windows>`.

**Isolate before fixing.** An error message names a symptom, not a cause.

## `@version` is the FORMAT version, not the Tableau release

```xml
<workbook source-build='2023.1.0 (20231.23.0404.1109)'
          upgrade-extracts='false' version='18.1' ...>
```

`18.1` has been the format version for years and is what Tableau 2023 **and**
2026 write. It is **not** the release number.

Setting it to a release like `2026.2` makes Tableau resolve a completely
different and much stricter schema, which then demands `<worksheet-number>`,
`<datagraph>`, `<accelerator-details>`, `<workbook-optimizer>` and more. Those
elements appear in no real workbook. If you find yourself adding scaffolding you
have never seen Tableau emit, the version string is wrong.

`source-build` is `"<release> (<build>)"`.

## The schema is a template, and the manifest resolves it

Tableau's internal TWB schema is not a fixed XSD. It contains 91
`<!--?IF Feature -->` / `<!--?ELSE -->` / `<!--?END -->` blocks, resolved at open
time from the feature flags the workbook declares:

```xml
<document-format-change-manifest>
  <MapboxVectorStylesAndLayers />
  <SavingAnalyticObjects />
  <SheetIdentifierTracking />
  <SortTagCleanup />
  <WindowsPersistSimpleIdentifiers />
</document-format-change-manifest>
```

**Bare flag names as element tags.** No prefix, no attributes. This is not
documented anywhere and does not appear in any Tableau binary as a searchable
string - the only way to learn it is to read a real workbook.

Consequences:

- **`SheetIdentifierTracking` is what makes `<simple-id>` legal.** Emit
  `<simple-id>` without it and you get *"no declaration found for element
  'simple-id'"*.
- **`SortTagCleanup` keeps `Sort-G` from resolving empty.** Without it, every
  load reports `group 'Sort-G' must contain all, choice, or sequence
  compositor` and `group 'ShelfSorts-G' ...`. Those errors are about *Tableau's
  own schema*, not your file, and they are easy to dismiss as noise. They are
  not noise - they mean the manifest is under-declared.
- Declare nothing and you get the all-flags-OFF resolution, which is a
  different schema again.

`scripts/extract_runtime_schema.py` resolves the template for a given flag set
so you can validate against what Tableau will really apply.

## The published XSD is a reference, not the gate

[tableau/tableau-document-schemas](https://github.com/tableau/tableau-document-schemas)
is official and Apache-2.0, and it is one resolution of that template with a
different flag set than a real workbook uses. It therefore **disagrees with
Tableau** on real files:

| | published XSD | Tableau |
|---|---|---|
| mark attribute | `class` | `class` (agrees) |
| `<worksheet-number>` | not present | not present in real workbooks either |
| `@derivation` | free string | enum - `Month-Trunc`, not `TruncMonth` |

`validate_twb.py` defaults to the extracted runtime schema whenever one exists,
and raises `SCH002` when falling back to the published XSD, because a workbook
can pass there and still fail to open.

Tableau says as much itself: the schemas "don't cover the validation of some
content" including connection attributes, calculated field contents, and
references between workbook elements.

## Date truncation is `Month-Trunc`, not `TruncMonth`

From Tableau's internal `AggType-ST`: `Year-Trunc`, `Quarter-Trunc`,
`Month-Trunc`, `Week-Trunc`, `Day-Trunc`. The published XSD types `@derivation`
as a free string, so nothing catches a wrong value until Tableau says
*"value 'TruncMonth' not in enumeration"*.

## The official XSD does not load standalone

`twb_2026.2.0.xsd` has two `<xs:import>` elements with **no `schemaLocation`**
and then references `user:UserAttributes-AG` and `xml:base`. libxml2 - and so
lxml and `xmllint` - refuses to build it:

```
XMLSchemaParseError: The QName value
'{http://www.tableausoftware.com/xml/user}UserAttributes-AG'
does not resolve to a(n) attribute group definition., line 2862
```

`schemas/tableau_user_ns.xsd` and `schemas/xml_ns.xsd` supply the definitions,
and `validate_twb.py` injects `schemaLocation` for both **in memory**. The
vendored XSD stays byte-identical to upstream so `/upgrade` can diff it.

## Tableau Public is extract-only, and the UI hides that from you

You can absolutely connect Tableau Public to a CSV - Connect -> Text file works
fine. That is because **Tableau Public silently creates an extract for you** the
moment you connect. Public does not support live connections at all; the UI just
does the conversion without telling you.

A generated `.twb` gets no such help. Declare a live `textscan` connection with
no `<extract>` block and Tableau Public refuses to OPEN the file:

> Workbooks saved to Tableau Public must use extracts. To create an extract,
> click the Data Source tab, then select Create Extract. The data source,
> `<name>`, is not an extract. Error Code: 3C242D89

Note the wording says "saved to". It fires on **open**, which is misleading -
this is not a publishing restriction you hit later, it is a hard gate on loading
the workbook at all.

So for Tableau Public, generate the extract yourself:

```python
csv_connection(path, extract=True)      # adds the <extract> block
write_hyper(fields, rows, "data/x.hyper")
package_twbx(twb, hyper, "Dash.twbx")   # extract must travel in the package
```

Tableau **Desktop** has no such restriction and opens a live `textscan`
connection directly - no extract, no packaging.

## Element order inside `<workbook>` is fixed

`WorkbookFile-CT` is an `xs:sequence`. Correct elements in the wrong order fail
with a message that blames the *second* element:

```
Element 'preferences': This element is not expected.
Expected is one of ( windows, datagraph, thumbnails, ... )
```

`twb_builder.py` owns this ordering. Do not rearrange the template at the bottom
of `build_workbook()`, and do not hand-insert elements into a generated file.

## UTF-8 BOM stops Tableau, and PowerShell adds one by default

`Set-Content`, `Out-File`, and `>` in PowerShell 5.1 all write a BOM. Write from
Python with `open(..., encoding="utf-8", newline="\n")` - `write_twb()` does.
`validate_twb.py` catches a BOM as `ENC001` and CRLF as `ENC002`.

CRLF is not fatal, but it turns every regenerated workbook into a whole-file
diff, which destroys the reason for keeping it in git.

## CSV paths: absolute opens reliably, relative travels

A `textscan` connection stores `directory` and `filename`.

- **Absolute** - opens wherever the `.twb` is launched from, breaks when the
  folder moves.
- **Relative** - survives a move, resolution is less predictable.

The demo build passes an absolute path computed at build time. **The build
script is what makes this portable** - rerun `build.py` after moving the folder
rather than hand-editing paths. `validate_twb.py` resolves relative paths from
the `.twb`'s own directory and reports a missing file as `CSV001`.

## Tableau overwrites external edits from memory

Tableau does not watch the filesystem. If a workbook is open and you regenerate
it, Tableau's next save writes its in-memory copy over your rebuild. Close
Tableau before running `build.py`. Same failure mode as Power BI Desktop with
PBIP.

## `.twbx` is out of scope

A `.twbx` is a zip of the `.twb` plus its data. The official schema explicitly
does not support packaged workbooks. Ship the `.twb` with its CSV beside it.

(Reading one is fine and is how you get a reference workbook - see the top of
this file.)

## Attribute quoting is mixed in generated files

`_attrs()` renders through `xml.sax.saxutils.quoteattr`, which uses double
quotes, while a few hand-written literals in the template use single quotes.
Both are valid XML and Tableau does not care - but if you write a script that
string-matches generated XML, match the double-quoted form. This bit the
negative tests during development: three checks looked like validator bugs and
were actually the test's single quotes failing to match.

## One grain per workbook

Not an XML problem, but the most common way one of these dashboards is quietly
wrong. The builder emits one datasource, so every sheet shares one flat table.
Mixing grains - monthly revenue with per-ticket rows - duplicates the coarser
measure across finer rows and inflates every total. Aggregate to a common grain
in the mart, or build two workbooks.

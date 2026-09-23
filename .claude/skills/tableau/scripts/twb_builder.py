#!/usr/bin/env python3
"""Build a Tableau workbook (.twb) from a compact spec.

A .twb is plain XML, which makes a Tableau dashboard an ordinary code artifact.
But it is verbose and order-sensitive: WorkbookFile-CT is an xs:sequence of 23
groups, so correct elements in the wrong order fail schema validation. This
module owns that ordering so callers never have to think about it.

Usage as a library:

    from twb_builder import build_workbook, csv_connection, bar_h, line, ban

    xml = build_workbook({
        "name": "Exec Overview",
        "connection": csv_connection("data/exec_kpis.csv"),
        "fields": [
            {"name": "Segment", "datatype": "string", "role": "dimension"},
            {"name": "Revenue", "datatype": "real",   "role": "measure"},
        ],
        "sheets": [
            ban("Total Revenue", measure="Revenue"),
            bar_h("Revenue by Segment", dimension="Segment", measure="Revenue"),
        ],
        "dashboard": {"name": "Exec Overview", "layout": [["Total Revenue"],
                                                          ["Revenue by Segment"]]},
    })
    write_twb(xml, "dashboards/exec/ExecOverview.twb")

Usage as a CLI (spec as JSON):

    python twb_builder.py spec.json -o Workbook.twb

Standard library only. Validation is a separate concern - run validate_twb.py.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

# The .twb FORMAT version. Confirmed from a workbook Tableau itself wrote
# (Tableau Public "Super Sample Superstore", authored by Tableau 2023.1):
#
#     <workbook source-build='2023.1.0 (20231.23.0404.1109)'
#               upgrade-extracts='false' version='18.1' ...>
#
# 18.1 is the FORMAT version and has been stable for years - it is NOT the
# Tableau release number. Setting it to a release ("2026.2") makes Tableau
# resolve a different, much stricter schema and the workbook will not open.
FORMAT_VERSION = "18.1"

# "<release> (<build>)" - the shape Tableau writes. Build from the published
# schema header.
SOURCE_BUILD = "2026.2.0 (20262.26.0528.2205)"

# Feature flags declared in <document-format-change-manifest>, as bare element
# names. This set is what Tableau writes, and it is what makes <simple-id>
# legal and keeps Sort-G from resolving empty. See extract_runtime_schema.py.
MANIFEST_FLAGS = (
    "MapboxVectorStylesAndLayers",
    "SavingAnalyticObjects",
    "SheetIdentifierTracking",
    "SortTagCleanup",
    "WindowsPersistSimpleIdentifiers",
)

# Mark classes the schema accepts (PrimitiveType-ST). Kept here so a typo in a
# recipe fails loudly at build time rather than silently rendering as squares.
MARK_CLASSES = {
    "Automatic", "Text", "Icon", "Shape", "Rectangle", "Bar", "GanttBar",
    "Square", "Circle", "Heatmap", "PolyLine", "Line", "Polygon", "Area",
    "Pie", "Multipolygon", "VizExtension",
}

# Aggregation -> the abbreviation Tableau uses in a column-instance name.
AGG_ABBREV = {
    "Sum": "sum", "Avg": "avg", "Min": "min", "Max": "max",
    "Count": "cnt", "CountD": "ctd", "None": "none",
}

# Date truncation -> (column-instance abbreviation, derivation value).
# The derivation values come from Tableau's internal AggType-ST enumeration and
# are hyphen-suffixed: "Month-Trunc", NOT "TruncMonth". The published XSD types
# @derivation as a free string, so it does NOT catch a wrong value here - only
# Tableau does, at open time, with "value 'X' not in enumeration".
DATE_TRUNC = {
    "year":    ("tyr", "Year-Trunc"),
    "quarter": ("tqr", "Quarter-Trunc"),
    "month":   ("tmn", "Month-Trunc"),
    "week":    ("twk", "Week-Trunc"),
    "day":     ("tdy", "Day-Trunc"),
}

# Tableau's internal TWB schema is a TEMPLATE with <!--?IF Feature --> branches,
# resolved at open time from MANIFEST_FLAGS above. Declare the wrong set (or
# none) and Tableau resolves a different schema than the one this file targets.
#
# <mark> uses @class, not @type - that pair is switched by the MarkTypeAttribute
# flag, which is NOT in the manifest Tableau writes. See references/gotchas.md.

# Deterministic UUID namespace, so rebuilding the same spec produces a
# byte-identical file and git diffs stay meaningful.
_NS = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")


class SpecError(ValueError):
    """The spec is wrong. Raised eagerly rather than emitting broken XML."""


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _uuid(seed: str) -> str:
    return "{" + str(uuid.uuid5(_NS, seed)) + "}"


def _attrs(**kw) -> str:
    """Render attributes, sorted, skipping None. Sorted keeps output stable."""
    parts = []
    for k in sorted(kw):
        v = kw[k]
        if v is None:
            continue
        k = k.rstrip("_").replace("__", "-").replace("_", "-")
        parts.append(f"{k}={quoteattr(str(v))}")
    return (" " + " ".join(parts)) if parts else ""


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name)


def _tableau_type(datatype: str, role: str) -> str:
    if role == "measure":
        return "quantitative"
    return "ordinal" if datatype == "date" else "nominal"


def _col_ref(field: str) -> str:
    return f"[{field}]"


def _instance_name(field: str, agg: str = "None", trunc: str | None = None) -> str:
    """Build the column-instance name, e.g. [sum:Revenue:qk], [none:Segment:nk]."""
    if trunc:
        return f"[{DATE_TRUNC[trunc][0]}:{field}:qk]"
    abbrev = AGG_ABBREV.get(agg, "none")
    kind = "qk" if agg != "None" else "nk"
    return f"[{abbrev}:{field}:{kind}]"


# --------------------------------------------------------------------------
# connections
# --------------------------------------------------------------------------

def csv_connection(path: str, name: str | None = None,
                   extract: bool = False) -> dict:
    """A Tableau 'textscan' connection to a local CSV.

    Needs no database driver. Opens in Tableau **Desktop**.

    Set extract=True for Tableau **Public**, which cannot open a live
    connection at all ("The data source ... is not an extract",
    error 3C242D89). That adds an <extract> block pointing at a .hyper inside
    the .twbx package - see scripts/hyper_extract.py.
    """
    p = Path(path)
    return {
        "kind": "csv",
        "extract": p.stem if extract else None,
        "path": str(path).replace("\\", "/"),
        "directory": str(p.parent).replace("\\", "/") or ".",
        "filename": p.name,
        "table": f"[{p.stem}#csv]",
        "caption": name or p.stem,
    }


def sql_connection(kind: str, *, server: str, database: str, sql: str,
                   username: str = "", port: str | None = None,
                   schema: str | None = None, warehouse: str | None = None,
                   caption: str = "warehouse") -> dict:
    """A live warehouse connection with a custom-SQL relation.

    NOTE: unlike csv_connection, this path is schema-valid but has NOT been
    verified against a live warehouse or opened in Tableau by this project.
    Treat the first workbook you build with it as unproven - see
    references/connections.md.
    """
    classes = {"postgres": "postgres", "bigquery": "bigquery",
               "snowflake": "snowflake", "redshift": "redshift",
               "sqlserver": "sqlserver", "mysql": "mysql"}
    if kind not in classes:
        raise SpecError(f"unknown sql connection kind {kind!r}; "
                        f"expected one of {sorted(classes)}")
    return {
        "kind": "sql",
        "extract": None,
        "class": classes[kind],
        "server": server,
        "dbname": database,
        "username": username,
        "port": port,
        "schema": schema,
        "warehouse": warehouse,
        "sql": sql,
        "caption": caption,
    }


def _render_extract(conn: dict, fields: list[dict]) -> str:
    """The <extract> block. Goes AFTER <column> in DataSource-CT's sequence.

    @dbname is package-relative: the .hyper lives at Data/Extracts/<name>.hyper
    inside the .twbx. [Extract].[Extract] is the schema.table Tableau writes
    inside every extract.

    The extract connection carries its OWN <metadata-records>, with
    parent-name [Extract]. When an extract is enabled Tableau reads the .hyper,
    not the original source, so the federated connection's metadata does not
    describe the columns it is actually reading.
    """
    name = conn.get("extract")
    if not name:
        return ""
    dbname = f"Data/Extracts/{name}.hyper"
    records = "\n".join(
        f"""            <metadata-record class='column'>
              <remote-name>{escape(f['name'])}</remote-name>
              <remote-type>{REMOTE_TYPE.get(f['datatype'], 129)}</remote-type>
              <local-name>{escape(_col_ref(f['name']))}</local-name>
              <parent-name>[Extract]</parent-name>
              <remote-alias>{escape(f['name'])}</remote-alias>
              <ordinal>{i}</ordinal>
              <local-type>{f['datatype']}</local-type>
              <aggregation>{DEFAULT_AGG.get(f['datatype'], 'Count')}</aggregation>
              <contains-null>true</contains-null>
            </metadata-record>"""
        for i, f in enumerate(fields))
    return f"""
      <extract{_attrs(count=-1, enabled='true', units='records')}>
        <connection{_attrs(**{'class': 'hyper', 'authentication': 'auth-none',
                              'author-locale': 'en_US',
                              'default-settings': 'yes'},
                           dbname=dbname, schema='Extract',
                           tablename='Extract')}>
          <relation{_attrs(name='Extract', table='[Extract].[Extract]',
                           type='table')} />
          <metadata-records>
{records}
          </metadata-records>
        </connection>
      </extract>"""


# OLE DB type codes Tableau writes in <remote-type>. Wrong values here do not
# stop the file loading, but they are what Tableau uses to decide how to read
# the physical column.
REMOTE_TYPE = {
    "string": 129, "date": 133, "datetime": 135,
    "integer": 20, "real": 5, "boolean": 11,
}

# Default aggregation Tableau records per physical type.
DEFAULT_AGG = {
    "string": "Count", "date": "Year", "datetime": "Year",
    "integer": "Sum", "real": "Sum", "boolean": "Count",
}


def _render_connection(conn: dict, conn_name: str, fields: list[dict]) -> str:
    """The federated connection, its relation, the logical->physical column map
    and the metadata records.

    The <cols> map and <metadata-records> are NOT optional decoration. Without
    them nothing binds the datasource's logical [Revenue] to a physical column,
    so every sheet using it loads with no fields - which Tableau reports from
    the dashboard as "references sheet 'X' which has no visual representation".
    The XSD is perfectly happy either way.
    """
    parent = conn["table"] if conn["kind"] == "csv" else "[Custom SQL Query]"

    if conn["kind"] == "csv":
        inner = ("<connection class='textscan'"
                 + _attrs(directory=conn["directory"], filename=conn["filename"],
                          password="", server="")
                 + " />")
        phys = "\n".join(
            "            <column" + _attrs(
                datatype=f["datatype"], name=f["name"], ordinal=i) + " />"
            for i, f in enumerate(fields))
        relation = ("<relation"
                    + _attrs(connection=conn_name, name=conn["filename"],
                             table=conn["table"], type="table") + ">\n"
                    + "          <columns"
                    + _attrs(header="yes", outcome="6") + ">\n"
                    + phys + "\n          </columns>\n        </relation>")
    else:
        inner = ("<connection"
                 + _attrs(**{"class": conn["class"]},
                          server=conn["server"], dbname=conn["dbname"],
                          username=conn["username"], port=conn.get("port"),
                          schema=conn.get("schema"),
                          warehouse=conn.get("warehouse"))
                 + " />")
        relation = ("<relation" + _attrs(connection=conn_name, name="Custom SQL Query",
                                         type="text") + ">"
                    + escape(conn["sql"]) + "</relation>")

    cols_map = "\n".join(
        "          <map" + _attrs(key=_col_ref(f["name"]),
                                  value=f"{parent}.[{f['name']}]") + " />"
        for f in fields)

    records = "\n".join(
        f"""          <metadata-record class='column'>
            <remote-name>{escape(f['name'])}</remote-name>
            <remote-type>{REMOTE_TYPE.get(f['datatype'], 129)}</remote-type>
            <local-name>{escape(_col_ref(f['name']))}</local-name>
            <parent-name>{escape(parent)}</parent-name>
            <remote-alias>{escape(f['name'])}</remote-alias>
            <ordinal>{i}</ordinal>
            <local-type>{f['datatype']}</local-type>
            <aggregation>{DEFAULT_AGG.get(f['datatype'], 'Count')}</aggregation>
            <contains-null>true</contains-null>
          </metadata-record>"""
        for i, f in enumerate(fields))

    return f"""      <connection class='federated'>
        <named-connections>
          <named-connection{_attrs(caption=conn['caption'], name=conn_name)}>
            {inner}
          </named-connection>
        </named-connections>
        {relation}
        <cols>
{cols_map}
        </cols>
        <metadata-records>
{records}
        </metadata-records>
      </connection>"""


# --------------------------------------------------------------------------
# chart recipes - each returns a sheet dict
# --------------------------------------------------------------------------

def ban(name: str, *, measure: str, agg: str = "Sum",
        mark: str = "Automatic", font_size: int = 28) -> dict:
    """Big headline number. No shelves; the measure rides the Text encoding.

    `mark` exists because which mark class a text-only sheet needs is not
    something the schema settles - override it only when diagnosing.
    """
    if mark not in MARK_CLASSES:
        raise SpecError(f"mark class {mark!r} is not in PrimitiveType-ST")
    return {"type": "ban", "name": name, "measure": measure, "agg": agg,
            "mark": mark, "font_size": font_size}


def bar_h(name: str, *, dimension: str, measure: str, agg: str = "Sum",
          sort_desc: bool = True) -> dict:
    """Horizontal bars - the default for ranked categories."""
    return {"type": "bar_h", "name": name, "dimension": dimension,
            "measure": measure, "agg": agg, "sort_desc": sort_desc}


def bar_v(name: str, *, dimension: str, measure: str, agg: str = "Sum",
          sort_desc: bool = False) -> dict:
    """Vertical bars - categories that read left-to-right, e.g. time buckets.

    sort_desc defaults to False here: vertical bars usually carry a natural
    order (time, size, severity) that sorting by value would destroy.
    """
    return {"type": "bar_v", "name": name, "dimension": dimension,
            "measure": measure, "agg": agg, "sort_desc": sort_desc}


def line(name: str, *, date: str, measure: str, agg: str = "Sum",
         trunc: str = "month", color: str | None = None) -> dict:
    """Time series. `trunc` is one of year/quarter/month/week/day."""
    if trunc not in DATE_TRUNC:
        raise SpecError(f"unknown trunc {trunc!r}; expected one of {sorted(DATE_TRUNC)}")
    return {"type": "line", "name": name, "date": date, "measure": measure,
            "agg": agg, "trunc": trunc, "color": color}


def bar_stack(name: str, *, dimension: str, measure: str, color: str,
              agg: str = "Sum", trunc: str | None = None) -> dict:
    """Stacked bars - composition across a category or time bucket."""
    return {"type": "bar_stack", "name": name, "dimension": dimension,
            "measure": measure, "color": color, "agg": agg, "trunc": trunc}


def table(name: str, *, dimensions: list[str], measures: list[str],
          agg: str = "Sum") -> dict:
    """Text table via Measure Names / Measure Values."""
    if not dimensions:
        raise SpecError("table() needs at least one dimension")
    if not measures:
        raise SpecError("table() needs at least one measure")
    return {"type": "table", "name": name, "dimensions": list(dimensions),
            "measures": list(measures), "agg": agg}


def grid(rows: list[list[str]]) -> list[list[str]]:
    """Dashboard layout: a list of rows, each a list of sheet names."""
    return rows


# --------------------------------------------------------------------------
# worksheet rendering
# --------------------------------------------------------------------------

def _dep_column(field: dict) -> str:
    return ("            <column" + _attrs(
        datatype=field["datatype"], name=_col_ref(field["name"]),
        role=field["role"],
        type=_tableau_type(field["datatype"], field["role"])) + " />")


def _dep_instance(field: dict, agg: str = "None", trunc: str | None = None) -> str:
    derivation = "None"
    if trunc:
        derivation = DATE_TRUNC[trunc][1]
    elif agg != "None":
        derivation = agg
    ttype = "quantitative" if (agg != "None" or trunc) else \
        _tableau_type(field["datatype"], field["role"])
    return ("            <column-instance" + _attrs(
        column=_col_ref(field["name"]), derivation=derivation,
        name=_instance_name(field["name"], agg, trunc), pivot="key",
        type=ttype) + " />")


def _shelf(ds: str, instance: str) -> str:
    return f"[{ds}].{instance}"


def _render_worksheet(sheet: dict, ds: str, fields: dict) -> str:
    name = sheet["name"]
    kind = sheet["type"]
    deps: list[str] = []
    seen_cols: set[str] = set()
    rows_shelf, cols_shelf = "", ""
    encodings: list[str] = []
    mark = "Automatic"
    sort_by: tuple[str, str, str] | None = None   # (column, direction, using)
    font_size: int | None = None

    def need(field_name: str) -> dict:
        if field_name not in fields:
            raise SpecError(
                f"sheet {name!r} references field {field_name!r}, which is not "
                f"declared in spec['fields'] (have: {sorted(fields)})")
        f = fields[field_name]
        if f["name"] not in seen_cols:
            deps.append(_dep_column(f))
            seen_cols.add(f["name"])
        return f

    if kind == "ban":
        f = need(sheet["measure"])
        deps.append(_dep_instance(f, sheet["agg"]))
        # Tableau's own text-only sheets use an Automatic mark with the field on
        # the text encoding and both shelves self-closing. A "Text" mark here
        # loaded as a sheet with "no visual representation", which then broke
        # every dashboard zone referencing it.
        mark = sheet.get("mark", "Automatic")
        font_size = sheet.get("font_size", 28)
        encodings.append("              <text" + _attrs(
            column=_shelf(ds, _instance_name(f["name"], sheet["agg"]))) + " />")

    elif kind in ("bar_h", "bar_v"):
        d = need(sheet["dimension"])
        m = need(sheet["measure"])
        deps.append(_dep_instance(d))
        deps.append(_dep_instance(m, sheet["agg"]))
        dim = _shelf(ds, _instance_name(d["name"]))
        mea = _shelf(ds, _instance_name(m["name"], sheet["agg"]))
        mark = "Bar"
        rows_shelf, cols_shelf = (dim, mea) if kind == "bar_h" else (mea, dim)
        if sheet.get("sort_desc", True):
            sort_by = (dim, "DESC", mea)

    elif kind == "line":
        d = need(sheet["date"])
        m = need(sheet["measure"])
        deps.append(_dep_instance(d, trunc=sheet["trunc"]))
        deps.append(_dep_instance(m, sheet["agg"]))
        cols_shelf = _shelf(ds, _instance_name(d["name"], trunc=sheet["trunc"]))
        rows_shelf = _shelf(ds, _instance_name(m["name"], sheet["agg"]))
        mark = "Line"
        if sheet.get("color"):
            c = need(sheet["color"])
            deps.append(_dep_instance(c))
            encodings.append("              <color" + _attrs(
                column=_shelf(ds, _instance_name(c["name"]))) + " />")

    elif kind == "bar_stack":
        d = need(sheet["dimension"])
        m = need(sheet["measure"])
        c = need(sheet["color"])
        trunc = sheet.get("trunc")
        deps.append(_dep_instance(d, trunc=trunc))
        deps.append(_dep_instance(m, sheet["agg"]))
        deps.append(_dep_instance(c))
        cols_shelf = _shelf(ds, _instance_name(d["name"], trunc=trunc))
        rows_shelf = _shelf(ds, _instance_name(m["name"], sheet["agg"]))
        mark = "Bar"
        encodings.append("              <color" + _attrs(
            column=_shelf(ds, _instance_name(c["name"]))) + " />")

    elif kind == "table":
        for dim_name in sheet["dimensions"]:
            d = need(dim_name)
            deps.append(_dep_instance(d))
        for meas_name in sheet["measures"]:
            m = need(meas_name)
            deps.append(_dep_instance(m, sheet["agg"]))
        # Measure Names / Measure Values are synthetic columns Tableau provides.
        deps.append("            <column" + _attrs(
            datatype="string", name="[:Measure Names]", role="dimension",
            type="nominal") + " />")
        deps.append("            <column" + _attrs(
            datatype="real", name="[Multiple Values]", role="measure",
            type="quantitative") + " />")
        rows_shelf = " / ".join(
            _shelf(ds, _instance_name(fields[d]["name"])) for d in sheet["dimensions"])
        cols_shelf = f"[{ds}].[:Measure Names]"
        mark = "Text"
        # Both synthetic fields must be DATASOURCE-QUALIFIED. Unqualified,
        # Tableau drops the sheet with "There is no field named
        # '[Multiple Values]'" - a content error the XSD cannot see.
        encodings.append("              <text" + _attrs(
            column=f"[{ds}].[Multiple Values]") + " />")

    else:
        raise SpecError(f"unknown sheet type {kind!r}")

    if mark not in MARK_CLASSES:
        raise SpecError(f"mark class {mark!r} is not in PrimitiveType-ST")

    # <rows> and <cols> are always present - the runtime schema requires them.
    # Tableau writes them SELF-CLOSING when the shelf is empty (24 of 34 sheets
    # in a reference workbook), which is what a text-only sheet looks like.
    def _shelf_el(tag: str, value: str) -> str:
        if not value:
            return f"        <{tag} />"
        return f"        <{tag}>{escape(value)}</{tag}>"

    shelves = _shelf_el("rows", rows_shelf) + "\n" + _shelf_el("cols", cols_shelf)

    # A ranked bar chart MUST be sorted by its measure - unsorted categories
    # make the reader do the ranking by eye (standards/dashboard-standards.md).
    # <computed-sort> goes inside <view>, after <datasource-dependencies> and
    # before <aggregation>; that order is fixed by the schema.
    sort_block = ""
    if sort_by:
        sort_block = ("\n          <computed-sort" + _attrs(
            column=sort_by[0], direction=sort_by[1], using=sort_by[2]) + " />")

    # A headline number rendered at body-text size is not a headline. <style>
    # is the LAST child of <pane>.
    pane_style = ""
    if font_size:
        pane_style = (
            "\n            <style>\n"
            "              <style-rule" + _attrs(element="mark") + ">\n"
            "                <format" + _attrs(attr="font-size",
                                                value=font_size) + " />\n"
            "              </style-rule>\n"
            "            </style>")

    enc_block = ""
    if encodings:
        enc_block = "\n            <encodings>\n" + "\n".join(encodings) + \
                    "\n            </encodings>"

    return f"""    <worksheet{_attrs(name=name)}>
      <table>
        <view>
          <datasources>
            <datasource{_attrs(caption=fields['__caption__'], name=ds)} />
          </datasources>
          <datasource-dependencies{_attrs(datasource=ds)}>
{chr(10).join(deps)}
          </datasource-dependencies>{sort_block}
          <aggregation value='true' />
        </view>
        <style />
        <panes>
          <pane>
            <view>
              <breakdown value='auto' />
            </view>
            <mark{_attrs(**{'class': mark})} />{enc_block}{pane_style}
          </pane>
        </panes>
{shelves}
      </table>
      <simple-id{_attrs(uuid=_uuid('ws:' + name))} />
    </worksheet>"""


# --------------------------------------------------------------------------
# dashboard rendering
# --------------------------------------------------------------------------

SPAN = 100000  # Tableau's dashboard zone coordinate space


def _render_dashboard(dash: dict, sheet_names: set[str]) -> str:
    """A dashboard declares <datasources> ONLY for datasources it uses ITSELF
    (parameters, dashboard-level filters), always paired with matching
    <datasource-dependencies>. It does NOT declare the datasource its sheets
    use - Tableau resolves that through the worksheets. Declaring an orphaned
    <datasources> entry with no dependencies is not something Tableau ever
    writes.
    """
    name = dash["name"]
    width, height = dash.get("size", (1200, 800))
    layout = dash["layout"]
    if not layout:
        raise SpecError("dashboard layout is empty")

    # Zones are FLAT and absolutely positioned in a 0..SPAN space. Tableau's own
    # dashboards contain no nested zones at all (0 across every dashboard in a
    # reference workbook), and @type-v2 appears nowhere in one. Wrapping the
    # sheets in a 'layout-basic' container zone is what made every zone fail
    # with "references sheet 'X' which has no visual representation" - the
    # sheets themselves were fine the whole time.
    #
    # A worksheet zone carries only geometry, an id, and the sheet name.
    # Optional proportional row heights, e.g. [1, 2, 2, 2] gives the KPI row a
    # seventh of the height instead of a quarter. Equal rows otherwise.
    weights = dash.get("row_heights") or [1] * len(layout)
    if len(weights) != len(layout):
        raise SpecError(
            f"row_heights has {len(weights)} entries but the layout has "
            f"{len(layout)} rows")
    if any(w <= 0 for w in weights):
        raise SpecError("row_heights entries must be positive")
    total = sum(weights)

    zones, zid = [], 1
    y = 0
    for r, row in enumerate(layout):
        if not row:
            raise SpecError(f"dashboard row {r} is empty")
        # last row absorbs rounding so zones tile exactly to SPAN
        h = (SPAN * weights[r]) // total if r < len(layout) - 1 else SPAN - y
        col_w = SPAN // len(row)
        for c, sheet in enumerate(row):
            if sheet not in sheet_names:
                raise SpecError(
                    f"dashboard references sheet {sheet!r}, which is not in "
                    f"spec['sheets'] (have: {sorted(sheet_names)})")
            w = col_w if c < len(row) - 1 else SPAN - col_w * (len(row) - 1)
            zones.append("        <zone" + _attrs(
                h=h, id=zid, name=sheet, show__title="false",
                w=w, x=col_w * c, y=y) + " />")
            zid += 1
        y += h

    # Order is fixed: style, size, datasources, zones, simple-id - matching
    # what Tableau itself writes.
    return f"""    <dashboard{_attrs(name=name)}>
      <style />
      <size{_attrs(maxheight=height, maxwidth=width,
                   minheight=height, minwidth=width,
                   sizing__mode='fixed')} />
      <zones>
{chr(10).join(zones)}
      </zones>
      <simple-id{_attrs(uuid=_uuid('db:' + name))} />
    </dashboard>"""


def _render_windows(sheets: list[dict], dash: dict | None) -> str:
    def wsid(seed: str) -> str:
        return "\n      <simple-id" + _attrs(uuid=_uuid("win:" + seed)) + " />"

    out = []
    for s in sheets:
        out.append(f"""    <window{_attrs(**{'class': 'worksheet'}, name=s['name'])}>
      <cards>
        <edge{_attrs(name='left')}>
          <strip{_attrs(size=160)}>
            <card{_attrs(type='pages')} />
            <card{_attrs(type='filters')} />
            <card{_attrs(type='marks')} />
          </strip>
        </edge>
      </cards>{wsid(s['name'])}
    </window>""")
    if dash:
        # EVERY sheet the dashboard shows needs a <viewpoint> here, matched to
        # the zone name. Verified 1:1 against a reference workbook: 22
        # viewpoints, 22 zone sheets, zero mismatch in either direction.
        #
        # An empty <viewpoints /> is precisely what "Dashboard references sheet
        # 'X' which has no visual representation in the workbook" means. The
        # sheet renders fine on its own; the dashboard simply has no viewpoint
        # registered for it. Nothing in the schema requires this, so validation
        # passes and only Tableau complains.
        seen, viewpoints = set(), []
        for s in [x for row in dash["layout"] for x in row]:
            if s in seen:
                continue
            seen.add(s)
            viewpoints.append(
                f"        <viewpoint{_attrs(name=s)}>\n"
                f"          <zoom{_attrs(type='entire-view')} />\n"
                f"        </viewpoint>")
        out.append(f"""    <window{_attrs(**{'class': 'dashboard'},
                                          maximized='true', name=dash['name'])}>
      <viewpoints>
{chr(10).join(viewpoints)}
      </viewpoints>
      <active{_attrs(id=-1)} />{wsid('db:' + dash['name'])}
    </window>""")
    return "\n".join(out)


# --------------------------------------------------------------------------
# top level
# --------------------------------------------------------------------------

def build_workbook(spec: dict) -> str:
    """Render a spec to .twb XML text. Raises SpecError on a bad spec."""
    for key in ("name", "connection", "fields", "sheets"):
        if key not in spec:
            raise SpecError(f"spec is missing required key {key!r}")
    if not spec["sheets"]:
        raise SpecError("spec['sheets'] is empty")

    conn = spec["connection"]
    ds_name = "federated." + _slug(spec["name"]).lower()[:24]
    conn_name = ("textscan." if conn["kind"] == "csv" else "sqlproxy.") + \
                _slug(spec["name"]).lower()[:24]
    caption = conn.get("caption", spec["name"])

    fields = {}
    for f in spec["fields"]:
        for k in ("name", "datatype", "role"):
            if k not in f:
                raise SpecError(f"field {f!r} is missing {k!r}")
        if f["role"] not in ("dimension", "measure"):
            raise SpecError(f"field {f['name']!r} has role {f['role']!r}; "
                            "expected 'dimension' or 'measure'")
        fields[f["name"]] = f
    fields["__caption__"] = caption

    columns = "\n".join(
        "      <column" + _attrs(
            datatype=f["datatype"], name=_col_ref(f["name"]), role=f["role"],
            type=_tableau_type(f["datatype"], f["role"])) + " />"
        for f in spec["fields"])

    datasource = f"""  <datasources>
    <datasource{_attrs(caption=caption, inline='true', name=ds_name,
                       version=FORMAT_VERSION)}>
{_render_connection(conn, conn_name, spec['fields'])}
{columns}{_render_extract(conn, spec['fields'])}
    </datasource>
  </datasources>"""

    worksheets = "\n".join(_render_worksheet(s, ds_name, fields)
                           for s in spec["sheets"])
    sheet_names = {s["name"] for s in spec["sheets"]}
    if len(sheet_names) != len(spec["sheets"]):
        raise SpecError("two sheets share a name; sheet names must be unique")

    dash = spec.get("dashboard")
    dash_block = ""
    if dash:
        dash_block = ("\n  <dashboards>\n"
                      + _render_dashboard(dash, sheet_names)
                      + "\n  </dashboards>")

    windows = _render_windows(spec["sheets"], dash)

    manifest = "\n".join(f"    <{flag} />" for flag in MANIFEST_FLAGS)

    # Order below is fixed by WorkbookFile-CT (xs:sequence). Do not rearrange.
    # The element set matches what Tableau itself writes - no more, no less.
    return f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook{_attrs(**{'source-build': SOURCE_BUILD,
                    'source-platform': 'win',
                    'upgrade-extracts': 'false',
                    'version': FORMAT_VERSION})} xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
{manifest}
  </document-format-change-manifest>
  <preferences>
    <preference{_attrs(name='ui.encoding.shelf.height', value='24')} />
    <preference{_attrs(name='ui.shelf.height', value='26')} />
  </preferences>
  <style />
{datasource}
  <worksheets>
{worksheets}
  </worksheets>{dash_block}
  <windows>
{windows}
  </windows>
</workbook>
"""


def write_twb(xml: str, path: str | Path) -> Path:
    """Write UTF-8 without BOM, LF endings. Both matter to Tableau."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(xml)
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build a .twb from a JSON spec.")
    ap.add_argument("spec", help="path to a JSON spec file")
    ap.add_argument("-o", "--out", required=True, help="output .twb path")
    args = ap.parse_args(argv)

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    try:
        xml = build_workbook(spec)
    except SpecError as e:
        print(f"spec error: {e}", file=sys.stderr)
        return 2
    out = write_twb(xml, args.out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

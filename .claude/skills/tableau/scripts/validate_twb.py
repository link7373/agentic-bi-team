#!/usr/bin/env python3
"""Validate a Tableau workbook (.twb) before it ever reaches Tableau.

Two layers, because one is not enough:

1. **Syntactic** - validate against Tableau's official TWB XSD
   (https://github.com/tableau/tableau-document-schemas, Apache-2.0, vendored
   under ../schemas/). This proves the file is structurally compliant.

2. **Semantic** - everything the XSD explicitly does not cover. Tableau's own
   README is blunt about this: the schemas "don't cover the validation of some
   content" including "connection attributes, calculated field contents, and
   references to workbook elements". A workbook can be perfectly schema-valid
   and still open to broken sheets because a shelf points at a field that does
   not exist. Layer 2 is where that gets caught.

Usage:
    python validate_twb.py <path> [--json] [--quiet] [--no-warn] [--schema X.Y]

<path> may be a .twb file or a folder; .twb files are discovered recursively.

Exit codes: 0 = no errors, 1 = at least one ERROR, 2 = bad invocation.

lxml is required for layer 1 only. Without it the XSD check is skipped with a
warning and the semantic checks still run - a partial answer beats none, as
long as it says so.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
XS = "{http://www.w3.org/2001/XMLSchema}"

# The two namespaces twb_*.xsd imports without a schemaLocation. libxml2 refuses
# to build the schema unless both resolve, so we point them at local shims.
# See schemas/tableau_user_ns.xsd and schemas/xml_ns.xsd for the full story.
SHIMS = {
    "http://www.tableausoftware.com/xml/user": "tableau_user_ns.xsd",
    "http://www.w3.org/XML/1998/namespace": "xml_ns.xsd",
}

# Tableau's real TWB schema is a TEMPLATE with <!--?IF Feature --> branches,
# resolved at open time from the flags a workbook declares in
# <document-format-change-manifest>. The published twb_*.xsd is ONE resolution
# of that template, with several features switched on. A workbook that declares
# no features - which is what twb_builder emits by default - is validated by
# Tableau against the all-flags-OFF resolution, where these particles do not
# exist at all.
#
# So the published XSD demands elements that Tableau itself REJECTS in a
# manifest-free workbook ("no declaration found for element 'simple-id'"). In
# --profile conservative these group references are relaxed to minOccurs="0"
# in memory. The vendored file on disk is never touched.
#
# This is not a workaround for a bug. It is the difference between two
# legitimate resolutions of one conditional schema, and the conservative one is
# what actually opens.
FEATURE_GATED_GROUPS = (
    "SimpleIdentifier-G",
    "SimpleIdentifierForThisWorksheet-G",
    "SimpleIdentifierForThisDashboard-G",
    "SimpleIdentifierForThisWindow-G",
    "Workbook-ExplainData-G",
)

UTF8_BOM = b"\xef\xbb\xbf"

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"
_RANK = {ERROR: 0, WARN: 1, INFO: 2}

# Shelf expressions look like [federated.abc].[sum:Revenue:qk], optionally
# nested with " / ". This pulls out the instance names.
SHELF_REF = re.compile(r"\[(?P<ds>[^\]]+)\]\.\[(?P<inst>[^\]]+)\]")

# A bracketed reference NOT preceded by "].", i.e. missing its datasource
# qualifier. Tableau silently drops the field and the sheet renders nothing.
BARE_REF = re.compile(r"(?<!\]\.)(?<!\[)(?P<ref>\[[^\]]+\])(?!\s*\.\s*\[)")

# Charts the team does not ship. dashboard-standards.md owns the reasoning;
# this just enforces it. Pie is allowed for part-of-whole with <=2 slices,
# which is why it is a WARN and not an ERROR.
DISCOURAGED_MARKS = {"Pie": "pie charts are unreliable for comparison"}

# Functions we recognise in a calculated field. Not a parser - a spell-check.
KNOWN_FUNCS = {
    "SUM", "AVG", "MIN", "MAX", "COUNT", "COUNTD", "MEDIAN", "STDEV", "VAR",
    "ABS", "CEILING", "FLOOR", "ROUND", "POWER", "SQRT", "LOG", "EXP", "SIGN",
    "IF", "IIF", "CASE", "WHEN", "THEN", "ELSE", "ELSEIF", "END", "AND", "OR",
    "NOT", "ISNULL", "IFNULL", "ZN", "LEN", "LEFT", "RIGHT", "MID", "TRIM",
    "LTRIM", "RTRIM", "UPPER", "LOWER", "REPLACE", "SPLIT", "CONTAINS",
    "STARTSWITH", "ENDSWITH", "FIND", "DATEPART", "DATETRUNC", "DATEADD",
    "DATEDIFF", "DATENAME", "TODAY", "NOW", "YEAR", "MONTH", "DAY", "WEEK",
    "QUARTER", "MAKEDATE", "STR", "INT", "FLOAT", "DATE", "DATETIME", "BOOL",
    "FIXED", "INCLUDE", "EXCLUDE", "TOTAL", "WINDOW_SUM", "WINDOW_AVG",
    "WINDOW_MIN", "WINDOW_MAX", "RUNNING_SUM", "RUNNING_AVG", "INDEX", "RANK",
    "RANK_DENSE", "FIRST", "LAST", "SIZE", "LOOKUP", "PREVIOUS_VALUE", "ATTR",
}


@dataclass
class Finding:
    code: str
    severity: str
    path: str
    message: str
    hint: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, code, severity, path, message, hint=""):
        self.findings.append(Finding(code, severity, str(path), message, hint))

    @property
    def errors(self):
        return [f for f in self.findings if f.severity == ERROR]

    @property
    def warnings(self):
        return [f for f in self.findings if f.severity == WARN]


# --------------------------------------------------------------------------
# layer 1 - XSD
# --------------------------------------------------------------------------

RUNTIME_CACHE = SCHEMA_DIR / ".runtime-cache"


def runtime_schemas() -> list[Path]:
    """Schemas extracted from a local Tableau install, if any.

    These are what Tableau ACTUALLY applies, so they are the better gate when
    present. Produced by scripts/extract_runtime_schema.py; gitignored, because
    they are Tableau's proprietary content.
    """
    if not RUNTIME_CACHE.exists():
        return []
    return sorted(RUNTIME_CACHE.glob("twb_runtime_*.xsd"))


def available_schemas() -> dict[str, Path]:
    return {p.stem.replace("twb_", "").removesuffix(".0"): p
            for p in sorted(SCHEMA_DIR.glob("twb_*.xsd"))}


def load_schema(version: str | None, profile: str = "conservative",
                use_runtime: bool = False):
    """Build an lxml XMLSchema from the vendored XSD, shims patched in memory.

    Returns (schema, schema_path, error_message). The vendored file is never
    modified on disk - it stays byte-identical to upstream so `/upgrade` can
    diff it against a new release.
    """
    try:
        from lxml import etree
    except ImportError:
        return None, None, ("lxml is not installed, so the workbook was NOT "
                            "checked against Tableau's XSD")

    if use_runtime:
        rs = runtime_schemas()
        if not rs:
            return None, None, ("no extracted runtime schema found; run "
                                "scripts/extract_runtime_schema.py first")
        tree = etree.parse(str(rs[0]))
        for imp in tree.getroot().findall(XS + "import"):
            ns = imp.get("namespace")
            if ns in SHIMS and not imp.get("schemaLocation"):
                shim = SCHEMA_DIR / SHIMS[ns]
                if not shim.exists():
                    return None, rs[0], f"missing shim {shim.name}"
                imp.set("schemaLocation", shim.as_uri())
        try:
            return etree.XMLSchema(tree), rs[0], None
        except etree.XMLSchemaParseError as e:
            return None, rs[0], f"could not build runtime schema: {e}"

    schemas = available_schemas()
    if not schemas:
        return None, None, f"no twb_*.xsd found in {SCHEMA_DIR}"
    if version:
        if version not in schemas:
            return None, None, (f"schema {version} not vendored; have "
                                f"{sorted(schemas)}")
        path = schemas[version]
    else:
        path = schemas[sorted(schemas)[-1]]

    tree = etree.parse(str(path))
    for imp in tree.getroot().findall(XS + "import"):
        ns = imp.get("namespace")
        if ns in SHIMS and not imp.get("schemaLocation"):
            shim = SCHEMA_DIR / SHIMS[ns]
            if not shim.exists():
                return None, path, f"missing shim {shim.name} next to the XSD"
            imp.set("schemaLocation", shim.as_uri())

    if profile == "conservative":
        for grp in tree.getroot().iter(XS + "group"):
            if grp.get("ref") in FEATURE_GATED_GROUPS:
                grp.set("minOccurs", "0")

    try:
        return etree.XMLSchema(tree), path, None
    except etree.XMLSchemaParseError as e:
        return None, path, f"could not build schema: {e}"


def check_xsd(twb: Path, rep: Report, schema, schema_path) -> None:
    from lxml import etree
    try:
        doc = etree.parse(str(twb))
    except etree.XMLSyntaxError as e:
        rep.add("XML001", ERROR, twb, f"not well-formed XML: {e}",
                "A .twb is plain XML; fix the syntax before anything else.")
        return
    if schema.validate(doc):
        return
    for err in schema.error_log:
        rep.add("TWB001", ERROR, f"{twb}:{err.line}", err.message.strip(),
                f"Fails Tableau's official schema ({schema_path.name}). "
                "Element order inside <workbook> is a fixed xs:sequence - "
                "correct elements in the wrong order fail here.")


# --------------------------------------------------------------------------
# layer 2 - what the XSD cannot see
# --------------------------------------------------------------------------

def check_encoding(twb: Path, rep: Report) -> None:
    raw = twb.read_bytes()
    if raw.startswith(UTF8_BOM):
        rep.add("ENC001", ERROR, twb, "file starts with a UTF-8 BOM.",
                "Write UTF-8 without BOM. On Windows, PowerShell's "
                "Set-Content/Out-File and '>' all add one - use Python's "
                "open(..., encoding='utf-8') or -Encoding utf8NoBOM.")
    if b"\r\n" in raw:
        rep.add("ENC002", WARN, twb, "file has CRLF line endings.",
                "Tableau tolerates CRLF, but it makes every regenerated "
                "workbook a whole-file diff. Write with newline='\\n'.")


def _declared_columns(root: ET.Element) -> dict[str, set[str]]:
    """datasource name -> set of declared column names, e.g. '[Revenue]'."""
    out: dict[str, set[str]] = {}
    for ds in root.findall("./datasources/datasource"):
        name = ds.get("name", "")
        cols = {c.get("name", "") for c in ds.findall("./column")}
        cols |= {c.get("name", "") for c in ds.findall(".//calculation/../")
                 if c.tag == "column"}
        out[name] = cols
    return out


def check_field_refs(twb: Path, root: ET.Element, rep: Report) -> None:
    """Every shelf/encoding reference must resolve to a declared column.

    This is the check that matters most in practice. A dangling reference is
    schema-valid - the XSD sees a well-formed string - but the sheet opens
    blank or Tableau throws a field-not-found on load.
    """
    declared = _declared_columns(root)
    if not declared:
        rep.add("REF003", ERROR, twb, "workbook declares no datasource columns.",
                "Every field used on a shelf must be declared as a <column> "
                "under <datasource>.")
        return

    for ws in root.findall("./worksheets/worksheet"):
        wsname = ws.get("name", "?")
        # instance name -> underlying column, from datasource-dependencies
        inst_to_col: dict[str, str] = {}
        dep_ds = set()
        for dep in ws.findall(".//datasource-dependencies"):
            dsn = dep.get("datasource", "")
            dep_ds.add(dsn)
            for ci in dep.findall("./column-instance"):
                inst_to_col[ci.get("name", "")] = ci.get("column", "")
            for col in dep.findall("./column"):
                inst_to_col.setdefault(col.get("name", ""), col.get("name", ""))

        for dsn in dep_ds:
            if dsn and dsn not in declared:
                rep.add("REF004", ERROR, f"{twb}:{wsname}",
                        f"worksheet depends on datasource '{dsn}', which is "
                        "not declared in <datasources>.",
                        "The datasource name in <datasource-dependencies> must "
                        "match a <datasource name=...> exactly.")

        shelves = []
        for tag in ("rows", "cols"):
            el = ws.find(f"./table/{tag}")
            if el is not None and el.text:
                shelves.append((tag, el.text))
        for enc in ws.findall(".//encodings/*"):
            col = enc.get("column")
            if col:
                shelves.append((enc.tag, col))

        for where, text in shelves:
            # An UNQUALIFIED reference matches nothing below and would be
            # silently skipped. Tableau drops the sheet with "There is no field
            # named '[X]'" - a content error the XSD cannot see, so catch it
            # here. Every shelf and encoding reference is [datasource].[field].
            for bare in BARE_REF.finditer(text):
                rep.add("REF006", ERROR, f"{twb}:{wsname}/{where}",
                        f"field reference {bare.group('ref')} is not "
                        "datasource-qualified.",
                        "Write it as [<datasource>].[<field>]. Tableau removes "
                        "the field and reports 'There is no field named ...', "
                        "which then breaks any dashboard zone using the sheet.")
            for m in SHELF_REF.finditer(text):
                dsn, inst = m.group("ds"), f"[{m.group('inst')}]"
                if dsn not in declared:
                    rep.add("REF001", ERROR, f"{twb}:{wsname}/{where}",
                            f"references datasource '{dsn}', which is not declared.",
                            "Shelf references are [<datasource>].[<instance>].")
                    continue
                if inst not in inst_to_col:
                    rep.add("REF001", ERROR, f"{twb}:{wsname}/{where}",
                            f"uses instance {inst}, which has no <column-instance> "
                            "in <datasource-dependencies>.",
                            "Every shelf instance needs a matching "
                            "<column-instance> declaring its column and derivation.")
                    continue
                underlying = inst_to_col[inst]
                if underlying and underlying not in declared[dsn] \
                        and not underlying.startswith("[:") \
                        and underlying != "[Multiple Values]":
                    rep.add("REF001", ERROR, f"{twb}:{wsname}/{where}",
                            f"instance {inst} maps to column {underlying}, which "
                            f"is not declared on datasource '{dsn}'.",
                            "Add a <column> for it under <datasource>, or fix "
                            "the reference.")


def check_dashboard_refs(twb: Path, root: ET.Element, rep: Report) -> None:
    sheets = {w.get("name", "") for w in root.findall("./worksheets/worksheet")}
    for dash in root.findall("./dashboards/dashboard"):
        dname = dash.get("name", "?")
        referenced = False
        for zone in dash.findall(".//zone"):
            zname = zone.get("name")
            if not zname:
                continue
            referenced = True
            if zname not in sheets:
                rep.add("REF002", ERROR, f"{twb}:{dname}",
                        f"zone points at worksheet '{zname}', which does not exist.",
                        f"Worksheets in this workbook: {sorted(sheets) or 'none'}.")
        if not referenced:
            rep.add("REF005", WARN, f"{twb}:{dname}",
                    "dashboard contains no worksheet zones.",
                    "A dashboard with only layout containers renders empty.")

        # Every sheet on a dashboard needs a <viewpoint> in that dashboard's
        # <window>. Without it Tableau refuses the whole dashboard with
        # "references sheet 'X' which has no visual representation in the
        # workbook" - even though the sheet renders perfectly on its own.
        zone_sheets = {z.get("name") for z in dash.findall(".//zone")
                       if z.get("name")}
        win = None
        for w in root.findall("./windows/window"):
            if w.get("class") == "dashboard" and w.get("name") == dname:
                win = w
                break
        if win is None:
            rep.add("REF007", ERROR, f"{twb}:{dname}",
                    "dashboard has no <window class='dashboard'> entry.",
                    "Every dashboard needs a window declaring a <viewpoint> "
                    "per sheet it shows.")
        else:
            vps = {v.get("name") for v in win.findall("./viewpoints/viewpoint")}
            missing = zone_sheets - vps
            if missing:
                rep.add("REF007", ERROR, f"{twb}:{dname}",
                        f"sheets on the dashboard with no <viewpoint> in its "
                        f"window: {sorted(missing)}",
                        "Add <viewpoint name='<sheet>'><zoom type='entire-view' "
                        "/></viewpoint> for each. Tableau reports these as "
                        "'no visual representation in the workbook'.")


def check_csv_sources(twb: Path, root: ET.Element, rep: Report) -> None:
    """A textscan connection points at a file on disk. Check it is really there
    and that its header matches the columns the workbook declares."""
    for ds in root.findall("./datasources/datasource"):
        dsname = ds.get("name", "?")
        # When an extract is enabled Tableau reads the .hyper, not the original
        # file, and the source CSV need not exist at all. Reporting a missing
        # CSV as an ERROR here would fail every extract-based workbook.
        extract = ds.find("./extract")
        has_extract = extract is not None and extract.get("enabled") == "true"
        declared = {c.get("name", "").strip("[]") for c in ds.findall("./column")}
        for conn in ds.findall(".//connection[@class='textscan']"):
            directory = conn.get("directory", "")
            filename = conn.get("filename", "")
            if not filename:
                continue
            csv_path = Path(directory) / filename
            if not csv_path.is_absolute():
                csv_path = (twb.parent / csv_path).resolve()
            if not csv_path.exists():
                if has_extract:
                    rep.add("CSV003", INFO, f"{twb}:{dsname}",
                            f"source CSV absent ({csv_path.name}); the datasource "
                            "reads its extract instead.")
                else:
                    rep.add("CSV001", ERROR, f"{twb}:{dsname}",
                            f"CSV not found: {csv_path}",
                            "A textscan connection is resolved relative to the "
                            ".twb. Ship the CSV alongside the workbook, or fix "
                            "@directory.")
                continue
            try:
                header = csv_path.open("r", encoding="utf-8-sig").readline()
            except OSError as e:
                rep.add("CSV002", WARN, f"{twb}:{dsname}",
                        f"could not read {csv_path}: {e}")
                continue
            cols = {h.strip().strip('"') for h in header.rstrip("\n").split(",")}
            missing = declared - cols
            if missing:
                rep.add("CSV001", ERROR, f"{twb}:{dsname}",
                        f"declared columns missing from CSV header: "
                        f"{sorted(missing)}",
                        f"CSV header has: {sorted(cols)}. Tableau will show "
                        "these fields as null or drop the sheet.")


def check_calculations(twb: Path, root: ET.Element, rep: Report) -> None:
    """Cheap sanity on calculated fields. The XSD treats a formula as an opaque
    string, so nothing else looks at it until Tableau does."""
    for calc in root.findall(".//calculation"):
        formula = calc.get("formula")
        if not formula:
            continue
        owner = "calculation"
        if formula.count("(") != formula.count(")"):
            rep.add("CALC001", WARN, f"{twb}:{owner}",
                    f"unbalanced parentheses in formula: {formula[:80]}")
        if formula.count("[") != formula.count("]"):
            rep.add("CALC001", WARN, f"{twb}:{owner}",
                    f"unbalanced brackets in formula: {formula[:80]}")
        for tok in re.findall(r"\b([A-Z_][A-Z_0-9]{2,})\s*\(", formula.upper()):
            if tok not in KNOWN_FUNCS:
                rep.add("CALC002", WARN, f"{twb}:{owner}",
                        f"unrecognised function {tok}() in formula.",
                        "Not necessarily wrong - this is a spell-check against "
                        "a known-function list, not a Tableau parser.")
        if "FIXED" in formula.upper():
            rep.add("CALC003", INFO, f"{twb}:{owner}",
                    "formula uses a FIXED LOD expression.",
                    "FIXED ignores the view's filters unless they are context "
                    "filters. Reconcile against SQL and state in SPEC.md which "
                    "filters it deliberately ignores "
                    "(standards/dashboard-standards.md).")


def check_design(twb: Path, root: ET.Element, rep: Report) -> None:
    for ws in root.findall("./worksheets/worksheet"):
        wsname = ws.get("name", "?")
        for mark in ws.findall(".//pane/mark"):
            # Tableau's runtime schema uses @type; the published XSD uses
            # @class. Inherited workbooks can carry either, so read both.
            cls = mark.get("type") or mark.get("class", "")
            if cls in DISCOURAGED_MARKS:
                rep.add("DSG001", WARN, f"{twb}:{wsname}",
                        f"uses a {cls} mark - {DISCOURAGED_MARKS[cls]}.",
                        "standards/dashboard-standards.md: use length/position "
                        "over area. A bar chart almost always reads better.")


def check_connections(twb: Path, root: ET.Element, rep: Report) -> None:
    for ds in root.findall("./datasources/datasource"):
        dsname = ds.get("name", "?")
        live = [c for c in ds.findall(".//connection")
                if c.get("class") not in (None, "federated", "textscan")]
        has_extract = ds.find(".//extract") is not None
        if live and not has_extract:
            rep.add("DSN001", WARN, f"{twb}:{dsname}",
                    f"live connection ({live[0].get('class')}) with no extract.",
                    "standards/dashboard-standards.md: extracts over live "
                    "connections for anything a human waits on - every filter "
                    "click on a live connection is a query and a cost.")


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def validate_file(twb: Path, rep: Report, schema, schema_path) -> None:
    check_encoding(twb, rep)
    if schema is not None:
        check_xsd(twb, rep, schema, schema_path)
    try:
        root = ET.parse(twb).getroot()
    except ET.ParseError as e:
        rep.add("XML001", ERROR, twb, f"not well-formed XML: {e}")
        return
    if root.tag != "workbook":
        rep.add("TWB002", ERROR, twb,
                f"root element is <{root.tag}>, expected <workbook>.")
        return
    check_field_refs(twb, root, rep)
    check_dashboard_refs(twb, root, rep)
    check_csv_sources(twb, root, rep)
    check_calculations(twb, root, rep)
    check_design(twb, root, rep)
    check_connections(twb, root, rep)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Validate Tableau .twb workbooks (XSD + semantic checks).")
    ap.add_argument("path", help="a .twb file, or a folder to search")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="only print the summary")
    ap.add_argument("--no-warn", action="store_true", help="show errors only")
    ap.add_argument("--schema", help="pin a vendored schema version, e.g. 2026.2")
    ap.add_argument("--runtime", action="store_true",
                    help="force the schema extracted from a local Tableau "
                         "install (scripts/extract_runtime_schema.py). This is "
                         "the default whenever one is present, because it is "
                         "what Tableau actually applies.")
    ap.add_argument("--published", action="store_true",
                    help="force Tableau's published XSD instead. It is a "
                         "REFERENCE that diverges from the runtime schema "
                         "(mark/@class vs @type, no <worksheet-number>), so a "
                         "workbook that opens fine can fail here.")
    ap.add_argument("--profile", choices=("conservative", "full"),
                    default="conservative",
                    help="which resolution of Tableau's conditional schema to "
                         "validate against (default: conservative, which is "
                         "what Tableau applies to a workbook that declares no "
                         "feature flags)")
    args = ap.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"no such path: {target}", file=sys.stderr)
        return 2

    files = [target] if target.is_file() else sorted(target.rglob("*.twb"))
    if not files:
        print(f"no .twb files found under {target}", file=sys.stderr)
        return 2

    rep = Report()
    # The runtime schema wins whenever we have one. The published XSD is a
    # different resolution of the same conditional template and materially
    # disagrees with what Tableau enforces at open time - it wants mark/@class
    # where Tableau wants @type, and has no <worksheet-number> at all.
    use_runtime = args.runtime or (bool(runtime_schemas()) and not args.published)

    schema, schema_path, schema_err = load_schema(args.schema, args.profile,
                                                  use_runtime)
    if not use_runtime:
        rep.add("SCH002", WARN, str(SCHEMA_DIR),
                "validated against Tableau's PUBLISHED XSD, which diverges "
                "from the schema Tableau applies at open time.",
                "Run scripts/extract_runtime_schema.py against a local Tableau "
                "install for an exact check. Without it a workbook can pass "
                "here and still fail to open, or fail here and open fine.")
    if schema_err:
        rep.add("SCH001", WARN, str(SCHEMA_DIR), schema_err,
                "Semantic checks still ran. Install lxml (pip install lxml) to "
                "enable validation against Tableau's official schema.")

    for f in files:
        validate_file(f, rep, schema, schema_path)

    shown = [f for f in rep.findings
             if not (args.no_warn and f.severity != ERROR)]
    shown.sort(key=lambda f: (_RANK[f.severity], f.path, f.code))

    if args.json:
        print(json.dumps({
            "files": [str(f) for f in files],
            "schema": str(schema_path) if schema_path else None,
            "findings": [f.__dict__ for f in shown],
            "errors": len(rep.errors),
            "warnings": len(rep.warnings),
        }, indent=2))
    else:
        if not args.quiet:
            for f in shown:
                print(f"{f.severity:5} {f.code}  {f.path}")
                print(f"      {f.message}")
                if f.hint:
                    print(f"      -> {f.hint}")
                print()
        scope = f"{len(files)} workbook{'s' if len(files) != 1 else ''}"
        sname = schema_path.name if schema_path else "no schema"
        kind = "Tableau runtime schema" if use_runtime else "published XSD"
        print(f"{scope} checked against {sname} ({kind}): "
              f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")

    return 1 if rep.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

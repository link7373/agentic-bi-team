#!/usr/bin/env python3
"""Extract and resolve the TWB schema that a local Tableau install actually uses.

WHY THIS EXISTS
---------------
Tableau publishes an official TWB XSD (vendored in ../schemas/). It is a useful
reference, but it is NOT the schema Tableau applies when it opens your file, and
targeting it alone produces workbooks that pass validation and then fail to open
with errors like:

    no declaration found for element 'simple-id'
    element 'explain-data' is not allowed for content model '(...)'

Two things cause that:

1. Tableau ships SEVERAL TWB schemas internally and picks one from the
   workbook's @version attribute. An old version string selects a legacy schema
   that predates half the elements in the published XSD.

2. The modern schema is a TEMPLATE containing <!--?IF Feature --> /
   <!--?ELSE --> / <!--?END --> blocks, resolved at open time from the feature
   flags the workbook declares in <document-format-change-manifest>. The
   published XSD is one resolution with several features ON. A workbook that
   declares no features gets the all-flags-OFF resolution, in which those
   elements do not exist at all.

This script reads the schemas out of the installed product and resolves the
template for a given feature set, so you can validate against what Tableau will
really apply.

WHAT IT DOES NOT DO
-------------------
It does not redistribute anything. The extracted schema is Tableau's
proprietary content and is written to a local, gitignored cache. Do not commit
the output. This reads software the user has already installed, on their own
machine, for the purpose of validating their own files.

Usage:
    python extract_runtime_schema.py                       # auto-detect, cache it
    python extract_runtime_schema.py --install "C:/.../Tableau Public 2026.2"
    python extract_runtime_schema.py --on SheetIdentifierTracking ExplainData_AuthorControls
    python extract_runtime_schema.py --list-flags

Requires lxml. Exit 0 on success, 1 if no install or no schema found.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

XS = "{http://www.w3.org/2001/XMLSchema}"

IF_RE = re.compile(r"<!--\?IF\s+([^-]+?)\s*-->")
ELSE_RE = re.compile(r"<!--\?ELSE\s*-->")
END_RE = re.compile(r"<!--\?END\s*-->")

# Where the schemas live inside the product, relative to the install root.
RESOURCE_CANDIDATES = ("bin/res/tablangres.rcc",)

# Marker that identifies a modern workbook schema among the embedded blobs.
MODERN_MARKERS = (b"document-format-change-manifest", b"WorkbookFile-CT")

CACHE_DIR = Path(__file__).resolve().parent.parent / "schemas" / ".runtime-cache"

# Which features does Tableau switch on?
#
# The workbook tells it. <document-format-change-manifest> lists the feature
# flags the file uses, as BARE ELEMENT NAMES - no prefix, no attributes:
#
#     <document-format-change-manifest>
#       <SheetIdentifierTracking />
#       <SortTagCleanup />
#     </document-format-change-manifest>
#
# Tableau then resolves its schema template for exactly that set. Declare
# nothing and you get the all-flags-OFF resolution, in which <simple-id> does
# not exist and groups like Sort-G resolve EMPTY - which is where the
# "group 'Sort-G' must contain all, choice, or sequence compositor" errors on
# load come from. They are a symptom of an under-declared manifest, not of
# anything wrong in the workbook body.
#
# The set below is what Tableau itself writes, read out of a workbook saved by
# Tableau 2023.1 (Tableau Public's "Super Sample Superstore"). Match it and the
# resolution is deterministic.
#
# Change this only against a workbook Tableau actually wrote. Every other
# source - the published XSD, reasoning from the template, all-flags-on - has
# been wrong here at least once.
DEFAULT_FLAGS = {
    "MapboxVectorStylesAndLayers",
    "SavingAnalyticObjects",
    "SheetIdentifierTracking",
    "SortTagCleanup",
    "WindowsPersistSimpleIdentifiers",
}


def find_installs() -> list[Path]:
    roots = [
        Path("C:/Program Files/Tableau"),
        Path("C:/Program Files (x86)/Tableau"),
        Path("/Applications"),
    ]
    out = []
    for root in roots:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if "tableau" not in child.name.lower():
                continue
            for rel in RESOURCE_CANDIDATES:
                if (child / rel).exists():
                    out.append(child)
                    break
    return out


def extract_schemas(install: Path) -> list[bytes]:
    """Pull every embedded workbook XSD blob out of the resource bundle."""
    blob = None
    for rel in RESOURCE_CANDIDATES:
        p = install / rel
        if p.exists():
            blob = p.read_bytes()
            break
    if blob is None:
        return []

    starts = [m.start() for m in re.finditer(rb"<xs:schema", blob)]
    ends = [m.end() for m in re.finditer(rb"</xs:schema>", blob)]
    found = []
    for s in starts:
        e = next((x for x in ends if x > s), None)
        if e is None:
            continue
        chunk = blob[s:e]
        if all(m in chunk for m in MODERN_MARKERS):
            found.append(chunk)
    # de-duplicate, keep the largest (the most complete resolution source)
    uniq = {hash(c): c for c in found}
    return sorted(uniq.values(), key=len, reverse=True)


def list_flags(text: str) -> list[str]:
    return sorted(set(f.strip() for f in IF_RE.findall(text)))


def resolve(text: str, on: set[str]) -> str:
    """Resolve <!--?IF/?ELSE/?END --> blocks for the given feature set."""
    out: list[str] = []
    stack: list[list[bool]] = []   # [emitting_now, if_branch_taken]

    for line in text.splitlines(keepends=True):
        m = IF_RE.search(line)
        if m:
            flag = m.group(1).strip()
            val = (flag[1:] not in on) if flag.startswith("!") else (flag in on)
            stack.append([val, val])
            continue
        if ELSE_RE.search(line):
            if stack:
                stack[-1][0] = not stack[-1][1]
            continue
        if END_RE.search(line):
            if stack:
                stack.pop()
            continue
        if all(s[0] for s in stack):
            out.append(line)
    return "".join(out)


def prune_empty_compositors(xsd_text: str) -> str:
    """Drop compositors emptied by resolution.

    Resolving can leave <xs:choice></xs:choice> behind when every branch was
    feature-gated. An empty choice is unsatisfiable, so the parent ends up
    requiring a child that no longer exists - which produces confusing
    'Missing child element(s)' errors that Tableau itself would never raise.
    """
    from lxml import etree
    root = etree.fromstring(xsd_text.encode("utf-8"))
    changed = True
    while changed:
        changed = False
        for tag in ("choice", "sequence", "all"):
            for el in root.findall(f".//{XS}{tag}"):
                if len([c for c in el if isinstance(c.tag, str)]) == 0:
                    el.getparent().remove(el)
                    changed = True
    return etree.tostring(root, encoding="unicode")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Extract the TWB schema a local Tableau install really uses.")
    ap.add_argument("--install", help="path to a Tableau install root")
    ap.add_argument("--on", nargs="*", default=None,
                    help="explicit feature flags to switch ON. Default: "
                         "DEFAULT_FLAGS, the set Tableau itself declares.")
    ap.add_argument("--conservative", action="store_true",
                    help="resolve with every flag OFF (an older/minimal "
                         "workbook profile)")
    ap.add_argument("--list-flags", action="store_true",
                    help="list the conditional feature flags and exit")
    ap.add_argument("-o", "--out", help="output path (default: a local cache)")
    args = ap.parse_args(argv)

    try:
        import lxml  # noqa: F401
    except ImportError:
        print("lxml is required: pip install lxml", file=sys.stderr)
        return 1

    installs = [Path(args.install)] if args.install else find_installs()
    if not installs:
        print("no Tableau install found. Pass --install <path>, or skip this - "
              "the vendored published XSD still works, it is just less exact.",
              file=sys.stderr)
        return 1

    install = installs[0]
    print(f"install: {install}")
    blobs = extract_schemas(install)
    if not blobs:
        print("no workbook schema found inside the install", file=sys.stderr)
        return 1
    text = blobs[0].decode("utf-8", "replace")
    print(f"schema:  {len(text):,} chars, "
          f"{len(list_flags(text))} conditional feature flags")

    if args.list_flags:
        for f in list_flags(text):
            print(f"  {f}")
        return 0

    all_flags = set(list_flags(text))
    if args.conservative:
        on = set()
    elif args.on is not None:
        on = set(args.on)
    else:
        on = set(DEFAULT_FLAGS)
    unknown = on - all_flags
    if unknown:
        print(f"warning: flags not present in this schema: {sorted(unknown)}",
              file=sys.stderr)
    resolved = prune_empty_compositors(resolve(text, on))

    label = "conservative" if not on else (
        "tableau" if on == set(DEFAULT_FLAGS) else "custom")
    out = Path(args.out) if args.out else CACHE_DIR / f"twb_runtime_{label}.xsd"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(resolved, encoding="utf-8")
    print(f"resolved with {len(on)} flag(s) ON -> {out}")
    print(f"         {len(resolved):,} chars")
    print("\nThis file is Tableau's proprietary content. It is gitignored. "
          "Do not commit it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

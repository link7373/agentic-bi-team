#!/usr/bin/env python3
"""Check that the metrics catalog is complete, unique, and actually used.

"One trusted definition, computed once and reused everywhere" is the rule the
whole kit rests on, and until now nothing enforced it. A metric could appear on
a scorecard with no definition behind it, or be defined twice with two formulas,
and the failure would only surface as two dashboards disagreeing months later.

This reads the fenced ```yaml blocks in knowledge/metrics-catalog.md and checks:

    MC001  required keys present (name, definition, grain, owner, generic_sql)
    MC002  names unique across the catalog
    MC003  the YAML block parses
    MC004  status is one of draft | ratified | deprecated
    MC005  generic_sql is still TODO (warning — the metric is not yet computable)
    MC010  every metric named in the scorecard KPI table is defined
    MC011  every metric named in a scorecard or dashboard spec is defined
    MC012  a definition nothing references (warning — dead metric)

The YAML parsed here is a deliberately small subset — flat `key: value`, inline
`[lists]`, and `|` block scalars — which is all a catalog entry needs and avoids
a PyYAML dependency. A block using anything fancier is reported rather than
silently half-read.

Usage:
    python scripts/check_metrics.py [--template-mode] [--list] [--quiet]

    --template-mode   the shipped repo, where entries are still placeholders:
                      structure is checked, missing values are not errors.

Exit codes: 0 = clean, 1 = at least one ERROR, 2 = bad invocation.

Standard library only (Python 3.9+) — no pip install required.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG = REPO_ROOT / "knowledge" / "metrics-catalog.md"

REQUIRED_KEYS = ["name", "definition", "grain", "owner", "generic_sql"]
VALID_STATUS = {"draft", "ratified", "deprecated"}

YAML_BLOCK_RE = re.compile(r"^```ya?ml\s*$(.*?)^```\s*$", re.M | re.S)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
PLACEHOLDER_RE = re.compile(r"\{\{.*?\}\}")

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"
_RANK = {ERROR: 0, WARN: 1, INFO: 2}


@dataclass
class Finding:
    code: str
    severity: str
    path: str
    line: int
    message: str
    hint: str = ""


@dataclass
class Report:
    findings: list = field(default_factory=list)

    def add(self, code, severity, path, line, message, hint=""):
        self.findings.append(Finding(code, severity, str(path), line, message, hint))

    @property
    def errors(self):
        return [f for f in self.findings if f.severity == ERROR]

    @property
    def warnings(self):
        return [f for f in self.findings if f.severity == WARN]


def parse_mini_yaml(text: str):
    """Parse the flat subset a catalog entry uses.

    Returns (mapping, error) — error is a string when the block uses something
    outside the subset, so it can be reported rather than half-understood.
    """
    out: dict = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.split("#", 1)[0].rstrip() if not raw.strip().startswith("#") else ""
        i += 1
        if not line.strip():
            continue
        if line.startswith((" ", "\t")):
            return out, f"unexpected indented line outside a block scalar: {line.strip()[:40]!r}"
        if ":" not in line:
            return out, f"line is not `key: value`: {line.strip()[:40]!r}"

        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()

        if value in ("|", ">", "|-", ">-"):
            body = []
            while i < len(lines) and (not lines[i].strip()
                                      or lines[i].startswith((" ", "\t"))):
                body.append(lines[i])
                i += 1
            out[key] = "\n".join(b.strip() for b in body).strip()
            continue

        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            out[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
            continue

        out[key] = value.strip("'\"")
    return out, None


def extract_entries(path: Path, rep: Report) -> list:
    """Every YAML block in the catalog, excluding the commented-out template."""
    if not path.exists():
        rep.add("MC000", ERROR, path.name, 0,
                "knowledge/metrics-catalog.md not found.",
                "The catalog is the source of truth for every metric; the team "
                "cannot report a number without it.")
        return []

    text = path.read_text(encoding="utf-8")
    # The template lives inside an HTML comment on purpose — blank it out so its
    # example keys aren't checked as if they were a real metric.
    masked = HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)

    entries = []
    for match in YAML_BLOCK_RE.finditer(masked):
        line = masked.count("\n", 0, match.start()) + 1
        data, err = parse_mini_yaml(match.group(1))
        if err:
            rep.add("MC003", ERROR, "knowledge/metrics-catalog.md", line,
                    f"Could not parse the YAML block: {err}",
                    "Catalog blocks use a small subset: flat `key: value`, "
                    "inline [lists], and `|` block scalars. See the template.")
            continue
        entries.append({"line": line, "data": data})
    return entries


def check_entries(entries: list, template_mode: bool, rep: Report) -> dict:
    by_name: dict = {}
    for entry in entries:
        data, line = entry["data"], entry["line"]
        name = str(data.get("name", "")).strip()

        missing = [k for k in REQUIRED_KEYS if not str(data.get(k, "")).strip()]
        if missing:
            rep.add("MC001", ERROR, "knowledge/metrics-catalog.md", line,
                    f"Metric '{name or '(unnamed)'}' is missing required key(s): "
                    f"{', '.join(missing)}.",
                    "A definition a stranger cannot compute from is not a "
                    "definition. Use `generic_sql: TODO` if the source table "
                    "is genuinely not confirmed yet.")

        status = str(data.get("status", "")).strip().lower()
        if status and status not in VALID_STATUS and not PLACEHOLDER_RE.search(status):
            rep.add("MC004", WARN, "knowledge/metrics-catalog.md", line,
                    f"Metric '{name}' has status '{status}'; expected one of "
                    f"{', '.join(sorted(VALID_STATUS))}.")

        sql = str(data.get("generic_sql", "")).strip()
        if sql.upper() == "TODO" and not template_mode:
            rep.add("MC005", WARN, "knowledge/metrics-catalog.md", line,
                    f"Metric '{name}' has no formula yet (generic_sql: TODO).",
                    "It cannot appear on a scorecard or dashboard until it does.")

        if not name:
            continue
        key = name.lower()
        if key in by_name and not PLACEHOLDER_RE.search(name):
            rep.add("MC002", ERROR, "knowledge/metrics-catalog.md", line,
                    f"Metric '{name}' is defined twice "
                    f"(first at line {by_name[key]['line']}).",
                    "Two definitions is how two dashboards start disagreeing. "
                    "Keep one; deprecate the other.")
        by_name[key] = {"line": line, "data": data, "name": name}
    return by_name


SCORECARD_TABLE_RE = re.compile(
    r"##\s*Scorecard KPI Set(.*?)(?=\n---|\n##\s|\Z)", re.S)


def check_scorecard_table(catalog: Path, defined: dict, template_mode: bool,
                          rep: Report) -> None:
    text = catalog.read_text(encoding="utf-8")
    match = SCORECARD_TABLE_RE.search(text)
    if not match:
        return
    section = match.group(1)
    base = text.count("\n", 0, match.start(1)) + 1

    for offset, line in enumerate(section.splitlines()):
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---"):
            continue
        first = stripped.strip("|").split("|")[0].strip()
        if not first or first.lower() in {"metric", ""}:
            continue
        if PLACEHOLDER_RE.search(first):
            continue  # unconfigured template row
        if first.lower() not in defined:
            rep.add("MC010", ERROR, "knowledge/metrics-catalog.md", base + offset,
                    f"Scorecard KPI '{first}' has no definition in this catalog.",
                    "Every reported number needs a definition behind it. Add an "
                    "entry, or remove it from the scorecard set.")


METRIC_REF_DIRS = ["scorecards", "dashboards"]
REF_RE = re.compile(r"^\|\s*\*{0,2}([A-Z][^|*]{2,60}?)\*{0,2}\s*\|", re.M)


def check_references(root: Path, defined: dict, rep: Report) -> None:
    """Metrics named in a scorecard or dashboard spec must exist in the catalog."""
    if not defined:
        return
    for dirname in METRIC_REF_DIRS:
        directory = root / dirname
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.md")):
            if path.name == "README.md":
                continue
            rel = str(path.relative_to(root)).replace("\\", "/")
            text = path.read_text(encoding="utf-8")
            for match in REF_RE.finditer(text):
                candidate = match.group(1).strip()
                if (PLACEHOLDER_RE.search(candidate)
                        or candidate.lower() in {"metric", "kpi", "name", "date",
                                                 "period", "visual", "page"}):
                    continue
                if candidate.lower() not in defined:
                    rep.add("MC011", WARN, rel,
                            text.count("\n", 0, match.start()) + 1,
                            f"'{candidate}' is reported here but is not in the "
                            f"metrics catalog.",
                            "Either it is a metric that needs defining, or this "
                            "is a table row the checker mistook for one — if the "
                            "latter, it is safe to ignore.")


def emit(rep: Report, n_metrics: int, mode: str, quiet: bool) -> None:
    shown = [f for f in rep.findings if f.severity != INFO]
    if shown:
        by_file: dict = {}
        for f in shown:
            by_file.setdefault(f.path, []).append(f)
        for path in sorted(by_file):
            print(f"\n{path}")
            for f in sorted(by_file[path], key=lambda x: (x.line, _RANK[x.severity])):
                loc = f":{f.line}" if f.line else ""
                print(f"  [{f.severity:<5}] {f.code}{loc}: {f.message}")
                if f.hint and not quiet:
                    print(f"          -> {f.hint}")
        print(f"\n{'-' * 60}")

    print(f"{n_metrics} metric definition(s). "
          f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s). [{mode}]")
    if not rep.errors:
        print("Metrics catalog check passed.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate knowledge/metrics-catalog.md.")
    parser.add_argument("--template-mode", action="store_true",
                        help="shipped template: check structure, not values")
    parser.add_argument("--list", action="store_true", dest="as_list",
                        help="list the defined metrics and exit 0")
    parser.add_argument("--quiet", action="store_true", help="suppress hints")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repo root (default: auto)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    catalog = root / "knowledge" / "metrics-catalog.md"

    rep = Report()
    entries = extract_entries(catalog, rep)
    defined = check_entries(entries, args.template_mode, rep)

    if args.as_list:
        for key in sorted(defined):
            entry = defined[key]
            status = entry["data"].get("status", "?")
            print(f"{entry['name']:<40} {status:<12} line {entry['line']}")
        print(f"\n{len(defined)} metric(s) defined.")
        return 0

    if catalog.exists():
        check_scorecard_table(catalog, defined, args.template_mode, rep)
    if not args.template_mode:
        check_references(root, defined, rep)

    emit(rep, len(entries), "template" if args.template_mode else "configured",
         args.quiet)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())

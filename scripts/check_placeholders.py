#!/usr/bin/env python3
"""Inventory and validate the {{PLACEHOLDER}} layer across the repo.

The kit ships as a template: every file carries {{PLACEHOLDERS}} that
`/setup-team` replaces with the company's real configuration. Two things can go
wrong, and this script checks both:

  * before setup  — a placeholder is malformed, so setup silently skips it
  * after setup   — a placeholder was missed, so an agent reads "{{BI_TOOL}}"
                    as if it were a fact

Usage:
    python scripts/check_placeholders.py [--template-mode] [--list] [--quiet]

Modes:
    default          post-setup. Any remaining placeholder is an ERROR.
    --template-mode  shipped template. Placeholders are expected; the core set
                     must still be present (proves nobody committed a filled-in
                     repo), and malformed ones are reported.
    --list           inventory only, never fails. Useful mid-setup.

Exit codes: 0 = clean, 1 = at least one ERROR, 2 = bad invocation.

Standard library only (Python 3.9+) — no pip install required.

Conventions this script enforces, documented in CONTRIBUTING.md:
  * A placeholder name is UPPER_SNAKE: {{COMPANY_NAME}}.
  * A hint may follow the name: {{BI_TOOL e.g. Power BI}} or {{X or "none"}}.
  * A pure example is written {{e.g. "..."}} and needs no name.
  * Placeholders inside an HTML comment are a *form template* — a blank entry
    a human copies later — and survive setup legitimately. Everything else
    must be filled.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PLACEHOLDER_RE = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
EXAMPLE_RE = re.compile(r"^e\.g\.\s", re.IGNORECASE)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

# Directories never scanned: generated output, tooling residue, the backup dir.
SKIP_DIRS = {
    ".git", ".gstack", ".setup-backup", "node_modules", "__pycache__",
    "demo", "analyses", "scorecards", "deliverables", "models",
}

# Files that legitimately contain brace pairs that are not placeholders
# (Mermaid hexagon syntax `M{{"text"}}`) or that document the syntax itself.
EXEMPT_FILES = {
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
}
EXEMPT_PREFIXES = ("docs/", "scheduling/")

# Present in the shipped template, gone after setup. If --template-mode cannot
# find these, someone committed a configured repo over the template.
CORE_PLACEHOLDERS = {
    "COMPANY_NAME", "INDUSTRY", "BUSINESS_MODEL", "NORTH_STAR_METRIC",
    "BI_TOOL", "WAREHOUSE", "TIMEZONE", "CURRENCY", "DATA_PRIVACY_RULES",
}

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


@dataclass
class Occurrence:
    path: Path
    rel: str
    line: int
    raw: str
    name: str
    in_comment: bool


def is_exempt(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    return rel in EXEMPT_FILES or rel.startswith(EXEMPT_PREFIXES)


def markdown_files(root: Path):
    for path in sorted(root.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        yield path


def comment_spans(text: str) -> list:
    return [(m.start(), m.end()) for m in HTML_COMMENT_RE.finditer(text)]


def collect(root: Path) -> list:
    """Every {{...}} occurrence in every scanned markdown file."""
    found = []
    for path in markdown_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        if is_exempt(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        spans = comment_spans(text)
        for m in PLACEHOLDER_RE.finditer(text):
            raw = m.group(1).strip()
            name = re.split(r"[\s,|]", raw, 1)[0].strip() if raw else ""
            line = text.count("\n", 0, m.start()) + 1
            in_comment = any(s <= m.start() < e for s, e in spans)
            found.append(Occurrence(path, rel, line, raw, name, in_comment))
    return found


def is_form_field(occ) -> bool:
    """A blank a human fills per entry, not a value /setup-team supplies.

    The convention: UPPER_SNAKE means setup fills it, so it must be gone
    afterwards. A lowercase prose blank ({{why}}, {{what was decided}}) is part
    of a reusable entry template and stays for the life of the file, as does
    anything inside an HTML comment.
    """
    return occ.in_comment or bool(occ.raw and occ.raw[0].islower())


def check_syntax(occurrences: list, rep: Report) -> None:
    """Malformed placeholders that /setup-team would skip over."""
    for occ in occurrences:
        if not occ.raw:
            rep.add("PH001", ERROR, occ.rel, occ.line,
                    "Empty placeholder '{{}}'.",
                    "Give it an UPPER_SNAKE name so setup can fill it.")
        elif EXAMPLE_RE.match(occ.raw) or is_form_field(occ):
            continue  # inline example, or a per-entry blank a human fills
        elif not NAME_RE.match(occ.name):
            rep.add("PH002", WARN, occ.rel, occ.line,
                    f"Placeholder name '{occ.name}' is neither UPPER_SNAKE nor "
                    f"a lowercase form field: {{{{{occ.raw[:60]}}}}}",
                    "Setup fills placeholders by name. Use {{NAME hint}} for "
                    "something setup supplies, {{lowercase prose}} for a blank "
                    "a human fills per entry, or the {{e.g. ...}} form.")


def check_unbalanced(root: Path, rep: Report) -> None:
    """A '{{' with no closing '}}' on the same line hides a placeholder."""
    for path in markdown_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        if is_exempt(rel):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines, 1):
            if line.count("{{") != line.count("}}"):
                rep.add("PH003", ERROR, rel, i,
                        "Unbalanced '{{' / '}}' on this line.",
                        "An unclosed placeholder is invisible to setup and "
                        "ships as literal text.")


def check_template_mode(occurrences: list, rep: Report) -> None:
    present = {o.name for o in occurrences}
    missing = sorted(CORE_PLACEHOLDERS - present)
    if missing:
        rep.add("PH010", ERROR, "(repo)", 0,
                f"Core placeholders absent from the template: {', '.join(missing)}",
                "The shipped repo must be unconfigured. If you ran /setup-team "
                "here, restore the template before committing "
                "(python scripts/setup_backup.py --restore <timestamp>).")


def check_post_setup(occurrences: list, rep: Report) -> None:
    for occ in occurrences:
        if is_form_field(occ) or EXAMPLE_RE.match(occ.raw or ""):
            continue  # a blank the user fills per entry, not a setup gap
        label = occ.name or occ.raw[:40]
        rep.add("PH020", ERROR, occ.rel, occ.line,
                f"Unfilled placeholder: {{{{{label}}}}}",
                "Agents read this file as fact. Fill it by hand or re-run "
                "/setup-team.")


def emit(rep: Report, occurrences: list, mode: str, quiet: bool) -> None:
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

    n_err, n_warn = len(rep.errors), len(rep.warnings)
    files = len({o.rel for o in occurrences})
    print(f"{len(occurrences)} placeholder(s) across {files} file(s); "
          f"{n_err} error(s), {n_warn} warning(s). [{mode}]")
    if not n_err and mode == "post-setup":
        print("No unfilled placeholders — the team is fully configured.")


def emit_list(occurrences: list) -> None:
    by_name: dict = {}
    for occ in occurrences:
        by_name.setdefault(occ.name or "(unnamed)", []).append(occ)
    for name in sorted(by_name):
        hits = by_name[name]
        locs = ", ".join(f"{o.rel}:{o.line}" for o in hits[:4])
        more = f" (+{len(hits) - 4} more)" if len(hits) > 4 else ""
        print(f"{name:<32} {len(hits):>3}  {locs}{more}")
    print(f"\n{len(by_name)} distinct placeholder(s), "
          f"{len(occurrences)} occurrence(s).")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the {{PLACEHOLDER}} layer of the Agentic BI Team repo.")
    parser.add_argument("--template-mode", action="store_true",
                        help="shipped template: placeholders expected, core set required")
    parser.add_argument("--list", action="store_true", dest="as_list",
                        help="inventory placeholders and exit 0")
    parser.add_argument("--quiet", action="store_true", help="suppress hints")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repo root (default: auto)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2

    occurrences = collect(root)

    if args.as_list:
        emit_list(occurrences)
        return 0

    rep = Report()
    check_unbalanced(root, rep)
    check_syntax(occurrences, rep)
    if args.template_mode:
        check_template_mode(occurrences, rep)
        mode = "template"
    else:
        check_post_setup(occurrences, rep)
        mode = "post-setup"

    emit(rep, occurrences, mode, args.quiet)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())

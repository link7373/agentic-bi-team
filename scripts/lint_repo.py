#!/usr/bin/env python3
"""Structural lint for the Agentic BI Team repo.

The kit is prose, so nothing fails loudly when it drifts: a README that still
says "8 agents" after a tenth was added, a skill that exists on disk but not in
the orchestrator's routing table, a cross-reference to a file that moved. Every
one of those quietly degrades the team — an agent that isn't in CLAUDE.md never
gets routed work.

Checks:
    AG/SK   agent and skill counts agree everywhere they are stated
    RT      every agent and skill has a routing-table row in CLAUDE.md, and
            every row has a file behind it
    FM      frontmatter present, and `name:` matches the file/folder name
    ATTR    attribution is the one-line form inside prompt files, the full
            block in the reader-facing root docs
    LINK    relative markdown links resolve to a real file
    PH      placeholder syntax (delegated to check_placeholders.py)

Usage:
    python scripts/lint_repo.py [--quiet] [--skip-placeholders]

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
sys.path.insert(0, str(Path(__file__).resolve().parent))

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"
_RANK = {ERROR: 0, WARN: 1, INFO: 2}

# Where a stated count of agents/skills can hide.
COUNT_SCAN_FILES = ["README.md", "CLAUDE.md", ".claude/skills/setup-team/SKILL.md"]

AGENT_COUNT_RES = [
    re.compile(r"!\[Agents\]\(https://img\.shields\.io/badge/Agents-(\d+)-"),
    re.compile(r"\b(\d+)\s+(?:specialist\s+|role-based\s+)?(?:sub-)?agents\b", re.I),
    re.compile(r"\b(\d+)\s+team members\b", re.I),
    re.compile(r"\bAll (\d+) agents\b", re.I),
    re.compile(r"\bteam\s+—\s+(\d+)\s+agents\b", re.I),
]
SKILL_COUNT_RES = [
    re.compile(r"!\[Skills\]\(https://img\.shields\.io/badge/Skills-(\d+)-"),
    re.compile(r"\b(\d+)\s+skills\b", re.I),
    re.compile(r"\b(\d+)\s+(?:slash-command\s+|plain-English\s+)?workflows\b", re.I),
]

ATTR_ONE_LINE = "> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/"
ATTR_FULL_FIRST = "> **Created by Colin Beck**"

# Reader-facing docs keep the full attribution block. Everything else is loaded
# into an agent's context, where four lines of author metadata is dead weight.
FULL_ATTR_FILES = {"README.md", "START-HERE.md", "CLAUDE.md", "analytics.md"}
# Prompt-context trees: must carry the one-line form, never the block.
PROMPT_TREES = (".claude/", "knowledge/", "standards/")

SKIP_DIRS = {".git", ".gstack", ".setup-backup", "node_modules", "__pycache__"}
# Generated at runtime by the team; never linted.
GENERATED_DIRS = {"analyses", "scorecards", "deliverables", "models", "demo"}


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


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def frontmatter(text: str) -> dict:
    """Parse the leading --- block. Flat key: value only, which is all we use."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip()
    return out


# --------------------------------------------------------------------------
# inventory
# --------------------------------------------------------------------------

def agent_files(root: Path) -> list:
    return sorted((root / ".claude" / "agents").glob("*.md"))


def skill_files(root: Path) -> list:
    return sorted((root / ".claude" / "skills").glob("*/SKILL.md"))


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_counts(root: Path, n_agents: int, n_skills: int, rep: Report) -> None:
    for relpath in COUNT_SCAN_FILES:
        path = root / relpath
        if not path.exists():
            continue
        text = read(path)
        for regexes, actual, label, code in (
            (AGENT_COUNT_RES, n_agents, "agent", "AG001"),
            (SKILL_COUNT_RES, n_skills, "skill", "SK001"),
        ):
            for regex in regexes:
                for m in regex.finditer(text):
                    stated = int(m.group(1))
                    if stated != actual:
                        rep.add(code, ERROR, relpath, line_of(text, m.start()),
                                f"States {stated} {label}s; the repo has {actual}.",
                                f"Text: \"{m.group(0).strip()}\". Update the number, "
                                f"or the count drifts silently the next time someone "
                                f"adds a {label}.")


def check_routing_table(root: Path, agents: list, skills: list, rep: Report) -> None:
    """Every agent/skill is routable, and every routed name exists."""
    claude_md = root / "CLAUDE.md"
    text = read(claude_md)
    if not text:
        rep.add("RT000", ERROR, "CLAUDE.md", 0, "CLAUDE.md is missing or unreadable.")
        return

    backticked = set(re.findall(r"`([a-z0-9-]+)`", text))
    slashed = set(re.findall(r"`?/([a-z0-9-]+)", text))

    for path in agents:
        name = path.stem
        if name not in backticked:
            rep.add("RT001", ERROR, rel(path, root), 0,
                    f"Agent '{name}' has no row in the CLAUDE.md §3 routing table.",
                    "The orchestrator routes from that table only — an agent "
                    "missing from it never gets work.")
    for path in skills:
        name = path.parent.name
        if name not in slashed and name not in backticked:
            rep.add("RT002", ERROR, rel(path, root), 0,
                    f"Skill '/{name}' is not listed in the CLAUDE.md §4 table.",
                    "Users and the orchestrator discover workflows from that table.")

    # The reverse: a table row pointing at a file that no longer exists.
    agent_names = {p.stem for p in agents}
    skill_names = {p.parent.name for p in skills}
    table_section = text.split("## 3.", 1)[-1].split("## 5.", 1)[0]
    for m in re.finditer(r"^\| `([a-z0-9-]+)`", table_section, re.M):
        name = m.group(1)
        if name not in agent_names and name not in skill_names:
            rep.add("RT003", ERROR, "CLAUDE.md",
                    line_of(text, text.find(m.group(0))),
                    f"Routing table names '{name}', which has no file.",
                    "Remove the row or add .claude/agents/<name>.md.")


def check_frontmatter(root: Path, agents: list, skills: list, rep: Report) -> None:
    for path in agents + skills:
        relpath = rel(path, root)
        fm = frontmatter(read(path))
        expected = path.stem if path.name != "SKILL.md" else path.parent.name
        if not fm:
            rep.add("FM001", ERROR, relpath, 1, "No YAML frontmatter block.",
                    "Claude Code will not register this agent/skill without "
                    "`name:` and `description:`.")
            continue
        if "name" not in fm or "description" not in fm:
            missing = [k for k in ("name", "description") if k not in fm]
            rep.add("FM002", ERROR, relpath, 1,
                    f"Frontmatter missing: {', '.join(missing)}.")
        elif fm["name"] != expected:
            rep.add("FM003", ERROR, relpath, 1,
                    f"Frontmatter name '{fm['name']}' != '{expected}' "
                    f"(from the path).",
                    "Claude Code invokes by path-derived name; a mismatch makes "
                    "the description unfindable.")
        if fm.get("description", "") and len(fm["description"]) < 40:
            rep.add("FM004", WARN, relpath, 1,
                    "Description is very short — routing quality depends on it.")


def check_attribution(root: Path, rep: Report) -> None:
    for path in sorted(root.rglob("*.md")):
        parts = path.relative_to(root).parts
        if any(p in SKIP_DIRS or p in GENERATED_DIRS for p in parts[:-1]):
            continue
        relpath = rel(path, root)
        text = read(path)
        has_full = ATTR_FULL_FIRST in text
        has_one = ATTR_ONE_LINE in text

        if relpath in FULL_ATTR_FILES:
            if not has_full:
                rep.add("ATTR001", WARN, relpath, 1,
                        "Reader-facing doc is missing the full attribution block.")
        elif relpath.replace("\\", "/").startswith(PROMPT_TREES) or path.name == "README.md":
            if has_full:
                rep.add("ATTR002", ERROR, relpath,
                        line_of(text, text.find(ATTR_FULL_FIRST)),
                        "Full 4-line attribution block inside a prompt-context file.",
                        "Use the one-line form; this text is re-read into context "
                        "on every invocation.")
            elif not has_one:
                rep.add("ATTR003", WARN, relpath, 1,
                        "Missing the one-line attribution.",
                        f"Add: {ATTR_ONE_LINE}")


LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def check_links(root: Path, rep: Report) -> None:
    for path in sorted(root.rglob("*.md")):
        parts = path.relative_to(root).parts
        if any(p in SKIP_DIRS or p in GENERATED_DIRS for p in parts[:-1]):
            continue
        relpath = rel(path, root)
        text = read(path)
        for m in LINK_RE.finditer(text):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#", "<")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                rep.add("LINK001", ERROR, relpath, line_of(text, m.start()),
                        f"Link target does not exist: {target}",
                        "Broken cross-references send agents looking for "
                        "context that isn't there.")


def check_placeholder_syntax(root: Path, rep: Report) -> None:
    try:
        import check_placeholders as cp
    except ImportError:
        rep.add("PH000", WARN, "scripts/", 0,
                "check_placeholders.py not importable; placeholder lint skipped.")
        return
    sub = cp.Report()
    cp.check_unbalanced(root, sub)
    cp.check_syntax(cp.collect(root), sub)
    for f in sub.findings:
        rep.add(f.code, f.severity, f.path, f.line, f.message, f.hint)


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def emit(rep: Report, n_agents: int, n_skills: int, quiet: bool) -> None:
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
    print(f"{n_agents} agents, {n_skills} skills. "
          f"{n_err} error(s), {n_warn} warning(s).")
    if not n_err:
        print("Repo lint passed.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Structural lint for the Agentic BI Team repo.")
    parser.add_argument("--quiet", action="store_true", help="suppress hints")
    parser.add_argument("--skip-placeholders", action="store_true",
                        help="skip the delegated placeholder-syntax check")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repo root (default: auto)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / "CLAUDE.md").exists():
        print(f"error: {root} does not look like the Agentic BI Team repo "
              f"(no CLAUDE.md)", file=sys.stderr)
        return 2

    agents, skills = agent_files(root), skill_files(root)
    if not agents or not skills:
        print("error: no agents or skills found under .claude/", file=sys.stderr)
        return 2

    rep = Report()
    check_counts(root, len(agents), len(skills), rep)
    check_routing_table(root, agents, skills, rep)
    check_frontmatter(root, agents, skills, rep)
    check_attribution(root, rep)
    check_links(root, rep)
    if not args.skip_placeholders:
        check_placeholder_syntax(root, rep)

    emit(rep, len(agents), len(skills), args.quiet)
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())

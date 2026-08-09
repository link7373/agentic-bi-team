#!/usr/bin/env python3
"""Snapshot every file /setup-team rewrites, so setup can be undone.

`/setup-team` edits roughly thirty files in one pass — CLAUDE.md, every agent,
every knowledge file, the standards. If it gets something wrong, or the user
answers a charter question badly, there is otherwise no way back short of
`git checkout` (which also throws away any work done alongside it).

Usage:
    python scripts/setup_backup.py                    # snapshot, print the id
    python scripts/setup_backup.py --list             # show snapshots
    python scripts/setup_backup.py --restore <id>     # put the files back
    python scripts/setup_backup.py --restore latest --dry-run

Snapshots live in .setup-backup/<timestamp>/ (gitignored). Restoring overwrites
the current files, so it prints exactly what it will touch and requires --yes
for anything it did not itself just verify as unchanged.

Exit codes: 0 = ok, 1 = failed, 2 = bad invocation.

Standard library only (Python 3.9+) — no pip install required.

Part of the Agentic BI Team. Created by Colin Beck.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = REPO_ROOT / ".setup-backup"

# Everything /setup-team is allowed to rewrite. Globs are relative to the root.
TARGET_GLOBS = [
    "CLAUDE.md",
    "START-HERE.md",
    ".claude/agents/*.md",
    ".claude/skills/*/SKILL.md",
    "knowledge/*.md",
    "standards/*.md",
    "*/README.md",
]


def targets(root: Path) -> list:
    seen, out = set(), []
    for pattern in TARGET_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                out.append(path)
    return out


def snapshots() -> list:
    if not BACKUP_DIR.exists():
        return []
    return sorted((d for d in BACKUP_DIR.iterdir() if d.is_dir()),
                  key=lambda d: d.name)


def resolve_snapshot(ident: str):
    snaps = snapshots()
    if not snaps:
        return None
    if ident == "latest":
        return snaps[-1]
    for snap in snaps:
        if snap.name == ident:
            return snap
    return None


def do_backup(root: Path, quiet: bool) -> int:
    files = targets(root)
    if not files:
        print("error: nothing to back up — is this the repo root?", file=sys.stderr)
        return 1

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest_root = BACKUP_DIR / stamp
    for path in files:
        rel = path.relative_to(root)
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        if not quiet:
            print(f"  saved {rel}")

    (dest_root / "MANIFEST.txt").write_text(
        f"Agentic BI Team pre-setup snapshot\n"
        f"taken: {datetime.now().isoformat(timespec='seconds')}\n"
        f"files: {len(files)}\n\n"
        + "\n".join(str(p.relative_to(root)).replace("\\", "/") for p in files)
        + "\n",
        encoding="utf-8")

    print(f"\nSnapshot {stamp} — {len(files)} file(s) saved to "
          f".setup-backup/{stamp}/")
    print(f"Undo everything setup writes with:\n"
          f"  python scripts/setup_backup.py --restore {stamp}")
    return 0


def do_restore(root: Path, ident: str, dry_run: bool, assume_yes: bool) -> int:
    snap = resolve_snapshot(ident)
    if snap is None:
        print(f"error: no snapshot '{ident}'. Run --list to see what exists.",
              file=sys.stderr)
        return 2

    changes, identical = [], 0
    for src in sorted(snap.rglob("*")):
        if not src.is_file() or src.name == "MANIFEST.txt":
            continue
        rel = src.relative_to(snap)
        dest = root / rel
        if dest.exists() and filecmp.cmp(src, dest, shallow=False):
            identical += 1
        else:
            changes.append((src, dest, rel))

    print(f"Snapshot {snap.name}: {identical} file(s) already match, "
          f"{len(changes)} would be overwritten.")
    for _, _, rel in changes:
        print(f"  restore {str(rel).replace(chr(92), '/')}")

    if not changes:
        print("\nNothing to do — the working tree already matches the snapshot.")
        return 0
    if dry_run:
        print("\n--dry-run: nothing written.")
        return 0
    if not assume_yes:
        print("\nThis overwrites the files listed above with their pre-setup "
              "contents.\nRe-run with --yes to proceed.")
        return 1

    for src, dest, rel in changes:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    print(f"\nRestored {len(changes)} file(s) from snapshot {snap.name}.")
    print("Re-run `python scripts/check_placeholders.py --template-mode` to "
          "confirm the template is intact.")
    return 0


def do_list(root: Path) -> int:
    snaps = snapshots()
    if not snaps:
        print("No snapshots. Take one with: python scripts/setup_backup.py")
        return 0
    for snap in snaps:
        manifest = snap / "MANIFEST.txt"
        count = "?"
        if manifest.exists():
            for line in manifest.read_text(encoding="utf-8").splitlines():
                if line.startswith("files:"):
                    count = line.split(":", 1)[1].strip()
        marker = "  (latest)" if snap is snaps[-1] else ""
        print(f"{snap.name}  {count} file(s){marker}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Snapshot and restore the files /setup-team rewrites.")
    parser.add_argument("--list", action="store_true", dest="as_list",
                        help="list existing snapshots")
    parser.add_argument("--restore", metavar="ID",
                        help="restore a snapshot id, or 'latest'")
    parser.add_argument("--dry-run", action="store_true",
                        help="with --restore: show what would change, write nothing")
    parser.add_argument("--yes", action="store_true",
                        help="with --restore: confirm the overwrite")
    parser.add_argument("--quiet", action="store_true", help="less output")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repo root (default: auto)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / "CLAUDE.md").exists():
        print(f"error: {root} does not look like the Agentic BI Team repo",
              file=sys.stderr)
        return 2

    if args.as_list:
        return do_list(root)
    if args.restore:
        return do_restore(root, args.restore, args.dry_run, args.yes)
    return do_backup(root, args.quiet)


if __name__ == "__main__":
    sys.exit(main())

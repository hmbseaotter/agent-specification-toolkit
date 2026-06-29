#!/usr/bin/env python3
"""Clean uninstaller for a GLOBAL install of the /specify skill (Agent Specification Toolkit).

Removes ONLY what install.py created (per its manifest) and restores any backup install.py made.
It will not delete a ~/.claude/skills/specify that it did not install: with no manifest it refuses,
unless you pass --force AND the directory carries this skill's SKILL.md.

(If you only ever used the project-local default, you never ran the installer and have nothing to
uninstall: just delete the cloned repo folder.)

Usage:
    python uninstall.py [--dry-run] [--keep-backup] [--force]

Cross-platform (Windows / macOS / Linux), Python 3.8+, standard library only.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SKILL_NAME = "specify"
MANIFEST_NAME = ".install-manifest.json"
OURS_MARKER = "Specification Interviewer"  # appears in our SKILL.md title


def target_dir() -> Path:
    return Path.home() / ".claude" / "skills" / SKILL_NAME


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Clean uninstaller for the global /specify skill.")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    ap.add_argument("--keep-backup", action="store_true",
                    help="do not restore the backup install.py saved")
    ap.add_argument("--force", action="store_true",
                    help="remove our skill dir even without a manifest")
    args = ap.parse_args(argv)

    tgt = target_dir()
    if not tgt.exists():
        print(f"nothing to do: {tgt} does not exist.")
        return 0

    manifest_path = tgt / MANIFEST_NAME
    manifest = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            manifest = None

    if manifest is None:
        # No readable manifest: may be a manual or foreign install. Be conservative.
        skill_md = tgt / "SKILL.md"
        looks_ours = skill_md.is_file() and OURS_MARKER in skill_md.read_text(
            encoding="utf-8", errors="ignore")
        if not (args.force and looks_ours):
            print(f"refusing to remove {tgt}: no install manifest found.")
            print("  (it was not installed by install.py, or the manifest is gone).")
            print("  re-run with --force only if you are sure this is the toolkit's skill.")
            return 1
        backup = None
    else:
        backup = manifest.get("backup_dir")

    print("Uninstall plan:")
    print(f"  remove:   {tgt}")
    if backup and not args.keep_backup:
        print(f"  restore:  {backup} -> {tgt}")
    elif backup:
        print(f"  backup kept at: {backup} (not restored; --keep-backup)")
    if args.dry_run:
        print("\n--dry-run: nothing was changed.")
        return 0

    shutil.rmtree(str(tgt))

    if backup and not args.keep_backup:
        bpath = Path(backup)
        if bpath.exists():
            shutil.move(str(bpath), str(tgt))
            print(f"\nRemoved the install and restored your previous skill from {backup}.")
            return 0
        print(f"\nRemoved the install. (Backup {backup} was not found to restore.)")
        return 0

    print("\nRemoved the install. ~/.claude/skills and your other skills are untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

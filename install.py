#!/usr/bin/env python3
"""Opt-in GLOBAL installer for the /specify skill (Agent Specification Toolkit).

You do NOT need this for normal use. Run `claude` from inside the cloned repo and /specify is
already available (project-local, zero global footprint). Use this only to make /specify available
in EVERY project on a machine, by copying it into your Claude Code user skills directory.

Safe by design:
  - Writes only under ~/.claude/skills/specify/ (creating ~/.claude/skills if missing).
  - Never touches settings.json, hooks, or any other config.
  - If a ~/.claude/skills/specify already exists, it is BACKED UP (moved aside) first, never
    silently overwritten.
  - Records exactly what it did in a manifest so uninstall.py can reverse it precisely and
    restore the backup.

Usage:
    python install.py [--dry-run]

Cross-platform (Windows / macOS / Linux), Python 3.8+, standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

SKILL_NAME = "specify"
MANIFEST_NAME = ".install-manifest.json"


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def sources(root: Path) -> dict:
    """The three files a global install needs, laid out FLAT in the target so the skill can find
    its companions next to SKILL.md (see the 'companion files' note in SKILL.md)."""
    return {
        "SKILL.md": root / ".claude" / "skills" / SKILL_NAME / "SKILL.md",
        "specification-template.md": root / "templates" / "specification-template.md",
        "lint_spec.py": root / "scripts" / "lint_spec.py",
    }


def target_dir() -> Path:
    return Path.home() / ".claude" / "skills" / SKILL_NAME


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Opt-in global installer for the /specify skill.")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    args = ap.parse_args(argv)

    root = repo_root()
    srcs = sources(root)
    missing = [name for name, p in srcs.items() if not p.is_file()]
    if missing:
        print(f"error: cannot find source file(s): {', '.join(missing)}", file=sys.stderr)
        print("       run this from inside the cloned agent-specification-toolkit repo.",
              file=sys.stderr)
        return 2

    tgt = target_dir()
    backup = None
    if tgt.exists():
        ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = tgt.with_name(f"{SKILL_NAME}.bak-{ts}")

    print("Install plan:")
    print(f"  target:        {tgt}")
    if backup:
        print(f"  existing one:  backed up to {backup}")
    for name in srcs:
        print(f"  install file:  {name}")
    print(f"  manifest:      {tgt / MANIFEST_NAME}")
    if args.dry_run:
        print("\n--dry-run: nothing was changed.")
        return 0

    # Back up an existing install (move aside; never overwrite silently).
    if backup is not None:
        shutil.move(str(tgt), str(backup))

    tgt.parent.mkdir(parents=True, exist_ok=True)
    tgt.mkdir(parents=True, exist_ok=False)

    installed = []
    for name, p in srcs.items():
        shutil.copy2(str(p), str(tgt / name))
        installed.append(name)

    manifest = {
        "tool": "agent-specification-toolkit/specify",
        "installed_at": dt.datetime.now().isoformat(timespec="seconds"),
        "target_dir": str(tgt),
        "files": installed + [MANIFEST_NAME],
        "backup_dir": str(backup) if backup else None,
    }
    (tgt / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("\nInstalled. /specify is now available in every project on this machine.")
    if backup:
        print(f"Your previous skill was preserved at: {backup}")
    print("To remove it cleanly:  python uninstall.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

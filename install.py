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
    python install.py --check      # report if the global install is stale (read-only, no changes)
    python install.py --update     # refresh an existing install in place, no backup (auto-refresh)

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


def _lines(p: Path) -> list[str]:
    """Text content as lines, ignoring line-ending style (CRLF vs LF) so it never
    reports a spurious difference from normalization alone."""
    return p.read_text(encoding="utf-8").splitlines()


def check_install(srcs: dict) -> int:
    """Read-only: is the global install present AND matching this repo?

    Deterministic file comparison (the toolkit's own principle: a check code can do).
    Exit 0 = up to date; 1 = not installed, or stale (a file is missing or differs).
    """
    tgt = target_dir()
    if not tgt.exists():
        print(f"not installed: no global /specify at {tgt}")
        print("  -> run 'python install.py' to install.")
        return 1
    stale = []
    for name, sp in srcs.items():
        tp = tgt / name
        if not tp.is_file():
            stale.append(f"{name}: MISSING from the install")
        elif _lines(sp) != _lines(tp):
            stale.append(f"{name}: DIFFERS from this repo")
    if stale:
        print(f"STALE: the global install at {tgt} does not match this repo:")
        for s in stale:
            print(f"  - {s}")
        print("  -> re-run 'python install.py' to refresh.")
        return 1
    print(f"up to date: global /specify at {tgt} matches this repo.")
    return 0


def update_install(srcs: dict, tgt: Path) -> int:
    """Refresh an existing toolkit install IN PLACE, no backup. Refuses to touch a target that
    exists but is not a toolkit install (so it never clobbers a foreign skill of the same name)."""
    if tgt.exists():
        mf = tgt / MANIFEST_NAME
        ours = False
        if mf.is_file():
            try:
                ours = (json.loads(mf.read_text(encoding="utf-8")).get("tool")
                        == "agent-specification-toolkit/specify")
            except (ValueError, OSError):
                ours = False
        if not ours:
            print(f"refuse: {tgt} exists but is not a toolkit install; "
                  f"run 'python install.py' (which backs it up) instead.", file=sys.stderr)
            return 2
    tgt.mkdir(parents=True, exist_ok=True)
    installed = []
    for name, p in srcs.items():
        shutil.copy2(str(p), str(tgt / name))
        installed.append(name)
    manifest = {
        "tool": "agent-specification-toolkit/specify",
        "installed_at": dt.datetime.now().isoformat(timespec="seconds"),
        "target_dir": str(tgt),
        "files": installed + [MANIFEST_NAME],
        "backup_dir": None,
        "updated_in_place": True,
    }
    (tgt / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Updated /specify in place at {tgt} (no backup).")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Opt-in global installer for the /specify skill.")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    ap.add_argument("--check", action="store_true",
                    help="report whether the global install matches this repo; change nothing "
                         "(exit 0 = up to date, 1 = stale / not installed)")
    ap.add_argument("--update", action="store_true",
                    help="refresh an existing toolkit install IN PLACE, no backup (for auto-refresh "
                         "hooks); refuses if the target isn't a toolkit install")
    args = ap.parse_args(argv)

    root = repo_root()
    srcs = sources(root)
    missing = [name for name, p in srcs.items() if not p.is_file()]
    if missing:
        print(f"error: cannot find source file(s): {', '.join(missing)}", file=sys.stderr)
        print("       run this from inside the cloned agent-specification-toolkit repo.",
              file=sys.stderr)
        return 2

    if args.check:
        return check_install(srcs)

    tgt = target_dir()

    if args.update:
        return update_install(srcs, tgt)

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

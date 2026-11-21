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
    python install.py --self-test  # prove the unshipped-script check fires on a planted reference

Cross-platform (Windows / macOS / Linux), Python 3.8+, standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

SKILL_NAME = "specify"
MANIFEST_NAME = ".install-manifest.json"
SCRIPT_REF = re.compile(r"\bscripts/([A-Za-z0-9_-]+\.py)\b")


def repo_root() -> Path:
    return Path(__file__).resolve().parent


def sources(root: Path) -> dict:
    """The five files a global install needs, laid out FLAT in the target so the skill can find
    its companions next to SKILL.md (see the 'companion files' note in SKILL.md).

    Every script the skill tells the user to run belongs here, or an installed copy cannot run
    it. `regenerate.py` stays out: it renders the reference cards, and the skill never runs it."""
    return {
        "SKILL.md": root / ".claude" / "skills" / SKILL_NAME / "SKILL.md",
        "specification-template.md": root / "templates" / "specification-template.md",
        "decision-record-template.md": root / "templates" / "decision-record-template.md",
        "lint_spec.py": root / "scripts" / "lint_spec.py",
        "subject_index.py": root / "scripts" / "subject_index.py",
    }


def target_dir() -> Path:
    return Path.home() / ".claude" / "skills" / SKILL_NAME


def write_manifest(tgt: Path, manifest: dict) -> None:
    """Write the install manifest with LF line endings on every platform.

    Left to the platform, Windows writes CRLF, so the manifest differed by machine and a backup
    repository tracking it warned on every refresh. `Path.open` rather than `write_text` because
    `write_text` only accepts `newline` from Python 3.10, and this installer supports 3.8."""
    with (tgt / MANIFEST_NAME).open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, indent=2))


def _lines(p: Path) -> list[str]:
    """Text content as lines, ignoring line-ending style (CRLF vs LF) so it never
    reports a spurious difference from normalization alone."""
    return p.read_text(encoding="utf-8").splitlines()


def unshipped_scripts(skill_text: str, root: Path, srcs: dict) -> list[str]:
    """Scripts of THIS repo that the skill text names but sources() would not install.

    A `scripts/<name>.py` reference counts only when `<name>.py` exists in this repo's
    `scripts/` folder, so a script another tool ships (skill-creator's quick_validate.py)
    is not flagged, and a repo script the skill never names (regenerate.py) is not either.
    """
    named = sorted(set(SCRIPT_REF.findall(skill_text)))
    return [n for n in named if (root / "scripts" / n).is_file() and n not in srcs]


def report_unshipped(root: Path, srcs: dict) -> int:
    """Exit 0 when every repo script SKILL.md names is installed; 1 (with a report) when not."""
    gaps = unshipped_scripts(srcs["SKILL.md"].read_text(encoding="utf-8"), root, srcs)
    if gaps:
        print("PACKAGING GAP: SKILL.md tells the user to run script(s) the install does not ship:")
        for n in gaps:
            print(f"  - scripts/{n}: add it to sources() in install.py")
        return 1
    return 0


def self_test(root: Path, srcs: dict) -> int:
    """Prove the unshipped-script check can fire: the real SKILL.md must pass, and the same
    text with a planted reference to a real but uninstalled repo script must be flagged."""
    text = srcs["SKILL.md"].read_text(encoding="utf-8")
    planted = "regenerate.py"
    real = unshipped_scripts(text, root, srcs)
    caught = unshipped_scripts(text + f"\nRun `python scripts/{planted}`.\n", root, srcs)
    ok = real == [] and caught == [planted]
    print(f"real SKILL.md:     {'ok, nothing unshipped' if real == [] else 'GAP ' + ', '.join(real)}")
    print(f"planted reference: {'ok, flagged ' + planted if caught == [planted] else 'NOT flagged'}")
    print("self-test passed." if ok else "self-test FAILED.")
    return 0 if ok else 1


def check_install(srcs: dict) -> int:
    """Read-only: does the install ship every repo script SKILL.md names, and is the global
    install present AND matching this repo?

    Deterministic file comparison (the toolkit's own principle: a check code can do).
    Exit 0 = up to date; 1 = a packaging gap, not installed, or stale (a file is missing or
    differs).
    """
    if report_unshipped(repo_root(), srcs):
        return 1
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
    write_manifest(tgt, manifest)
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
    ap.add_argument("--self-test", action="store_true",
                    help="prove the check for scripts SKILL.md names but the install does not "
                         "ship fires on a planted reference; change nothing (exit 0 = passed)")
    args = ap.parse_args(argv)

    root = repo_root()
    srcs = sources(root)
    missing = [name for name, p in srcs.items() if not p.is_file()]
    if missing:
        print(f"error: cannot find source file(s): {', '.join(missing)}", file=sys.stderr)
        print("       run this from inside the cloned agent-specification-toolkit repo.",
              file=sys.stderr)
        return 2

    if args.self_test:
        return self_test(root, srcs)

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
    write_manifest(tgt, manifest)

    print("\nInstalled. /specify is now available in every project on this machine.")
    if backup:
        print(f"Your previous skill was preserved at: {backup}")
    print("To remove it cleanly:  python uninstall.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

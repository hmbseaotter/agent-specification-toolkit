#!/usr/bin/env python3
"""Generate a spec's SUBJECT INDEX from actual section membership.

EARS groups requirements by *pattern* (ubiquitous / WHEN / WHILE / IF / WHERE), so requirements
about one subject necessarily scatter across sections. That scattering is how a decision gets
applied in one place and missed in another: a later question only ever touches the section it is
about. A subject index — "tax lives in these four sections, check all of them" — is the cheap
defence.

It must be GENERATED, never hand-written. A hand-written index was measured wrong in six of nine
rows on a real spec, two of them wrong because the index was authored before a reorganisation in the
same commit finished. A missing row is worse than no index at all: it does not merely fail to help,
it actively misdirects the next sweep.

The output deliberately ERRS TOWARD OVER-INCLUSION. A spurious "check here" costs a glance; a
missing one costs a contradiction.

Usage:
    python scripts/subject_index.py specs/my-spec.md [--subjects subjects.json]

Default subjects suit a scoring/eval spec; pass --subjects with {"Name": "regex", ...} to override.

KNOWN LIMIT: the non-functional block conventionally writes items as "- Security: [P1] ..." rather
than "- [P1] ...", so pattern matching on the bullet form misses it. Such sections are reported
separately rather than silently omitted.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SUBJECTS: dict[str, str] = {
    "Tax": r"tax",
    "Quantity": r"quantity|received|overbill|shipment",
    "Price & materiality": r"price variance|unit price|threshold|materiality",
    "Matching & scope": r"match key|scope|sentinel|contention|target",
    "Metrics & undefined values": r"precision|recall|false[- ]positive|null",
    "Fingerprints & integrity": r"fingerprint|digest|byte-identical|metadata",
    "Ground-truth artifacts": r"answer key|index|receipt|correspondence",
    "Isolation": r"deny|guard|placement|attestation|secret",
    "Generation": r"generator|regeneration|parse-back|canonical record",
}

REQ_BULLET = re.compile(r"^\s*- (?:\[[Pp]\d+[a-z]?\]\s*)?\S")
PHASE_TAG = re.compile(r"\[[Pp]\d+[a-z]?\]")


def sections(lines: list[str], start: int, end: int) -> list[tuple[str, int, int]]:
    """(heading, first_line, last_line) for each '### ' block between start and end."""
    heads = [i for i in range(start, end) if lines[i].startswith("### ")]
    out = []
    for n, i in enumerate(heads):
        stop = heads[n + 1] if n + 1 < len(heads) else end
        out.append((lines[i][4:].split("(")[0].strip(), i + 1, stop))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a spec subject index.")
    ap.add_argument("spec")
    ap.add_argument("--subjects", help="JSON file of {name: regex}")
    args = ap.parse_args(argv)

    path = Path(args.spec)
    if not path.is_file():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2

    subjects = DEFAULT_SUBJECTS
    if args.subjects:
        subjects = json.loads(Path(args.subjects).read_text(encoding="utf-8"))

    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, s in enumerate(lines) if s.strip() == "## requirements")
    except StopIteration:
        print("error: no '## requirements' block found", file=sys.stderr)
        return 2
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("## ") and i > start), len(lines))

    owned: dict[str, list[str]] = {k: [] for k in subjects}
    empty: list[str] = []

    for name, lo, hi in sections(lines, start, end):
        seen = 0
        for i in range(lo, hi):
            if not REQ_BULLET.match(lines[i]):
                continue
            seen += 1
            block = lines[i]
            j = i + 1
            while j < hi and lines[j].startswith("  ") and not lines[j].lstrip().startswith("- "):
                block += " " + lines[j].strip()
                j += 1
            block = PHASE_TAG.sub("", block)
            for subj, pat in subjects.items():
                if re.search(pat, block, re.IGNORECASE) and name not in owned[subj]:
                    owned[subj].append(name)
        if seen == 0:
            empty.append(name)

    print("| Subject | Sections containing its requirements |")
    print("|---|---|")
    for subj in subjects:
        got = owned[subj]
        print(f"| {subj} | {' · '.join(got) if got else '(none found)'} |")

    if empty:
        print(f"\nNOTE: no bullet-form requirements matched in: {', '.join(empty)}.")
        print("      Sections using a labelled form ('- Security: [P1] ...') need special-casing;")
        print("      their contents are NOT reflected in the table above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

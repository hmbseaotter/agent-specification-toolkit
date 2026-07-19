#!/usr/bin/env python3
"""Deterministic completeness linter for agent specifications.

Checks a spec written against templates/specification-template.md for the mechanical
properties every spec must have - WITHOUT using an LLM. This is the toolkit's own cost
discipline: spend tokens on judgment, not on checks plain code can do. The /specify skill
runs this instead of reasoning through the checks itself.

What it can verify deterministically (and what it cannot):
  - Structural: required blocks present, a Role field in metadata, requirements exist, acceptance
    criteria exist, out-of-scope non-empty, no "should" in the requirements block, phase tags
    well-formed (relaxed for zero-distance targets), leftover template placeholders / TODOs.
  - It CANNOT verify *semantic* traceability (does THIS requirement have a matching check?)
    without requirement IDs - that stays a human/LLM judgment. It reports a count proxy only.

Usage:
    python scripts/lint_spec.py specs/my-agent.md [--strict]

Exit codes: 0 = no errors (warnings allowed), 1 = at least one error (or any warning under
--strict), 2 = usage / file error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Blocks every conformant spec carries (## headings). Matched by prefix after lowercasing,
# so "out of scope" matches "## out of scope (v1)".
REQUIRED_BLOCKS = [
    "metadata",
    "outcome",
    "in scope",
    "out of scope",
    "constraints",
    "prior decisions",
    "requirements",
    "acceptance criteria",
    "implementation phases",
    "assumptions",
    "changelog",
]

# Agent-dimension blocks: present in every spec, but may legitimately say "n/a (not an agent)".
# We check presence only, never content.
AGENT_BLOCKS = [
    "control surface",
    "triggers & scheduling",
    "tools & permissions",
    "state & memory",
    "model & cost routing",
    "failure & escalation",
]

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
H2_RE = re.compile(r"^##\s+(.*?)\s*$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s*", re.MULTILINE)
# A phase-tag *attempt*: "[P" followed by alphanumerics and a "]", with NO spaces — so guidance
# prose like "[P2 items]" is not mistaken for a (malformed) tag. Well-formed is exactly "[P<int>]".
PHASE_TAG_RE = re.compile(r"\[[Pp][A-Za-z0-9]*\]")
WELLFORMED_PHASE_RE = re.compile(r"^\[P\d+\]$")
SHOULD_RE = re.compile(r"\bshould\b", re.IGNORECASE)


def strip_comments(text: str) -> str:
    """Remove HTML guidance comments - they are scaffolding, not spec content."""
    return COMMENT_RE.sub("", text)


def parse_sections(text: str) -> dict[str, str]:
    """Map each '## heading' (lowercased) to its body up to the next '## '."""
    sections: dict[str, str] = {}
    matches = list(H2_RE.finditer(text))
    for i, m in enumerate(matches):
        heading = m.group(1).strip().lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[heading] = text[start:end]
    return sections


def find_block(sections: dict[str, str], key: str) -> str | None:
    """Return the body of the first section whose heading starts with key, else None."""
    for heading, body in sections.items():
        if heading.startswith(key):
            return body
    return None


def bullets(body: str) -> list[str]:
    """Non-empty bullet lines in a block (comments already stripped)."""
    out = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith(("- ", "* ")) and len(s) > 2:
            out.append(s)
    return out


def looks_like_placeholder(line: str) -> bool:
    """Heuristic: after removing the checkbox marker and any [P#] tags, a leftover [...] bracket
    suggests an unfilled template stub. Warning-level (real prose can contain brackets)."""
    s = CHECKBOX_RE.sub("", line)
    s = PHASE_TAG_RE.sub("", s)
    return "[" in s and "]" in s


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.oks: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self, msg: str) -> None:
        self.oks.append(msg)


def lint(text: str) -> Report:
    r = Report()
    clean = strip_comments(text)
    sections = parse_sections(clean)

    # 0. Build class (zero-distance | build-required) - drives the target-aware relaxations below.
    meta_body = find_block(sections, "metadata") or ""
    bc_match = re.search(r"build class:\s*(.+)", meta_body, re.IGNORECASE)
    build_class = None
    if bc_match:
        val = bc_match.group(1).lower()
        has_zero, has_build = "zero-distance" in val, "build-required" in val
        if has_zero and not has_build:
            build_class = "zero-distance"
        elif has_build and not has_zero:
            build_class = "build-required"
    if build_class:
        r.ok(f"build class: {build_class}")
    elif bc_match:
        r.warn('metadata "Build class" still looks like a placeholder '
               "(set zero-distance | build-required)")

    # 1. Required blocks present.
    missing = [b for b in REQUIRED_BLOCKS if find_block(sections, b) is None]
    if missing:
        r.err(f"missing required block(s): {', '.join(missing)}")
    else:
        r.ok("all required blocks present")

    missing_agent = [b for b in AGENT_BLOCKS if find_block(sections, b) is None]
    if missing_agent:
        r.err(f"missing agent-dimension block(s): {', '.join(missing_agent)} "
              f'(keep them; write "n/a (not an agent)" for a plain feature)')
    else:
        r.ok("all agent-dimension blocks present")

    # 1b. metadata carries a Role field (the stance the target adopts).
    # The FIELD must be present so the choice is deliberate; "n/a" is a valid answer.
    if find_block(sections, "metadata") is not None:
        if re.search(r"\brole\s*:", meta_body, re.IGNORECASE):
            r.ok("metadata has a Role field")
        else:
            r.err('metadata is missing a "Role:" field (the stance the target adopts, where one '
                  'sharpens tone or domain expertise; "n/a" when a persona adds nothing)')

    # 2. out of scope non-empty.
    oos = find_block(sections, "out of scope")
    if oos is not None:
        b = bullets(oos)
        if not b:
            r.err('"out of scope" is empty - name at least one thing you are NOT doing, and why')
        elif all(looks_like_placeholder(x) for x in b):
            r.warn('"out of scope" still looks like template placeholders')
        else:
            r.ok(f'"out of scope" has {len(b)} item(s)')

    # 3. requirements exist + no "should".
    reqs = find_block(sections, "requirements")
    shall_lines = []
    if reqs is not None:
        shall_lines = [ln.strip() for ln in reqs.splitlines() if "SHALL" in ln]
        if not shall_lines:
            r.err('"requirements" has no SHALL statement - requirements must be EARS + SHALL')
        else:
            r.ok(f"{len(shall_lines)} SHALL requirement(s) found")
        should_hits = [ln.strip() for ln in reqs.splitlines() if SHOULD_RE.search(ln)]
        if should_hits:
            r.err(f'"should" appears in requirements ({len(should_hits)} line(s)) - a "should" is '
                  f"not a requirement; cut it or move it to prior decisions")
            for ln in should_hits[:3]:
                r.err(f"    -> {ln}")
        else:
            r.ok('no "should" in requirements')

    # 4. acceptance criteria exist.
    acc = find_block(sections, "acceptance criteria")
    crit_count = 0
    if acc is not None:
        crit_count = len(CHECKBOX_RE.findall(acc))
        if crit_count == 0:
            r.err('"acceptance criteria" has no checklist items ("- [ ] ...")')
        else:
            r.ok(f"{crit_count} acceptance criterion/criteria found")

    # 5. trace proxy (count only - true traceability is a judgment call).
    if shall_lines and crit_count and crit_count < len(shall_lines):
        r.warn(f"fewer acceptance criteria ({crit_count}) than SHALL requirements "
               f"({len(shall_lines)}) - every requirement needs >=1 check; verify the mapping")

    # 6. phase tags well-formed.
    bad_tags = sorted({t for t in PHASE_TAG_RE.findall(clean) if not WELLFORMED_PHASE_RE.match(t)})
    if bad_tags:
        r.err(f"malformed phase tag(s): {', '.join(bad_tags)} - use [P1], [P2], ...")
    good_tags = sorted({t for t in PHASE_TAG_RE.findall(clean) if WELLFORMED_PHASE_RE.match(t)})
    if good_tags:
        r.ok(f"phase tags present: {', '.join(good_tags)}")
    elif build_class == "zero-distance":
        r.ok("no [P#] phase tags - zero-distance target (artifact emitted directly); phasing n/a")
    else:
        r.warn("no [P#] phase tags found - the build prompt can't be scoped to a phase")

    # 7. leftover TODO markers.
    todos = [ln.strip() for ln in clean.splitlines() if "TODO:" in ln]
    if todos:
        r.warn(f"{len(todos)} TODO marker(s) remain (expected only in a [DRAFT - INCOMPLETE] spec)")

    # 8. status still DRAFT.
    meta = find_block(sections, "metadata")
    if meta and re.search(r"status:\s*draft", meta, re.IGNORECASE):
        r.warn('metadata status is still DRAFT')

    return r


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic completeness linter for agent specs.")
    ap.add_argument("spec", help="path to the spec markdown file")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures too")
    args = ap.parse_args(argv)

    path = Path(args.spec)
    if not path.is_file():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2

    report = lint(path.read_text(encoding="utf-8"))

    print(f"lint: {path}")
    for msg in report.oks:
        print(f"  [ok]   {msg}")
    for msg in report.warnings:
        print(f"  [warn] {msg}")
    for msg in report.errors:
        print(f"  [err]  {msg}")

    n_e, n_w = len(report.errors), len(report.warnings)
    print(f"\n{n_e} error(s), {n_w} warning(s).")
    if n_e or (args.strict and n_w):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

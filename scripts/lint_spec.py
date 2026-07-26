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
    Phase tags are read only from bullet lines in the blocks that carry tagged items, so a tag
    merely MENTIONED in prose is not reported as though it tagged something.
  - Semantic drift (added after three maintenance passes over a real spec found 21 defects this
    linter would have missed, every one of them a decision applied in one place and missed in
    another): duplicated requirements, requirements filed under the wrong EARS pattern, and
    decision references with no entry in the companion decision record.
  - It still CANNOT verify that a spec and its build prompt agree. Knowing which facts must match
    requires understanding the spec, so that residue stays manual discipline - and the worst defect
    those passes found lived exactly there: a build prompt carrying a superseded match key while
    the spec read correctly.
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

# Blocks whose BULLET LINES carry phase tags, per the template: "tag each in-scope item, requirement,
# and acceptance criterion". A bracketed tag anywhere else — a metadata note, prose inside
# "implementation phases", a changelog entry — is a REFERENCE to a phase, not a tag on an item, and
# must not be counted. Counting references made the linter report phases that did not exist.
# NOTE: tags do NOT sit at a fixed offset within a bullet, so position alone cannot identify them:
#   "- [P1] item"            (in scope)
#   "- WHEN [P1] trigger"    (requirements, after the EARS keyword)
#   "- Security: [P1] ..."   (non-functional, after a label)
#   "- [ ] [P1] check"       (acceptance criteria, after the checkbox)
# Which BLOCK the tag sits in is the reliable discriminator; where in the line is not.
TAGGABLE_BLOCKS = [
    "in scope",
    "requirements",
    "acceptance criteria",
]

# EARS pattern expected of requirements in each '### ' subsection of the requirements block.
# None = must NOT open with any pattern keyword (an always-active statement).
# Sections absent from this map (e.g. "non-functional") are skipped: they conventionally use a
# labelled form, "- Security: [P1] ...", which carries no EARS keyword at all.
#
# Why this check exists: over one real spec's lifetime the ubiquitous block silently accumulated
# WHEN / IF / WHERE statements while event-driven accumulated always-true ones, until the
# categorisation meant nothing. Nothing structural catches that -- a misfiled requirement is still a
# well-formed requirement.
EARS_EXPECTED: dict[str, str | None] = {
    "ubiquitous": None,
    "event-driven": "WHEN",
    "state-driven": "WHILE",
    "unwanted behavior": "IF",
    "optional feature": "WHERE",
}
EARS_KEYWORDS = ("WHEN", "WHILE", "IF", "WHERE")

DECISION_REF_RE = re.compile(r"\((D\d+(?:\.\d+)?)\)")
DECISION_DEF_RE = re.compile(r"^##+\s+(D\d+(?:\.\d+)?)\b", re.MULTILINE)

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
H2_RE = re.compile(r"^##\s+(.*?)\s*$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s*", re.MULTILINE)
# A phase-tag *attempt*: "[P" followed by alphanumerics and a "]", with NO spaces — so guidance
# prose like "[P2 items]" is not mistaken for a (malformed) tag. Well-formed is "[P<int>]" with an
# OPTIONAL lowercase sub-phase letter, so "[P1]" and "[P1a]" are both valid. Sub-phases are accepted
# because STEP 6c actively encourages SPLITTING an oversized phase, and "P1a / P1b" is the natural
# result — rejecting it forced a whole-spec renumber for no benefit.
PHASE_TAG_RE = re.compile(r"\[[Pp][A-Za-z0-9]*\]")
WELLFORMED_PHASE_RE = re.compile(r"^\[P\d+[a-z]?\]$")
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


def requirement_lines(body: str) -> list[tuple[str, str]]:
    """(subsection heading, full requirement text) for every bullet in a requirements block.

    Continuation lines are folded in, so a wrapped requirement is compared as one string."""
    out: list[tuple[str, str]] = []
    heading = ""
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("### "):
            heading = line[4:].split("(")[0].strip().lower()
            i += 1
            continue
        if line.strip().startswith(("- ", "* ")) and len(line.strip()) > 2:
            text = line.strip()
            j = i + 1
            while (j < len(lines) and lines[j].startswith("  ")
                   and not lines[j].strip().startswith(("- ", "* ", "#"))):
                text += " " + lines[j].strip()
                j += 1
            out.append((heading, re.sub(r"\s+", " ", text)))
            i = j
            continue
        i += 1
    return out


def opening_keyword(req: str) -> str | None:
    """The EARS keyword a requirement opens with, ignoring bullet marker and phase tag.

    Both orders occur in the wild and are valid: '- [P1] WHEN ...' and '- WHEN [P1] ...'."""
    s = re.sub(r"^[-*]\s+", "", req)
    s = PHASE_TAG_RE.sub("", s).strip()
    first = s.split(maxsplit=1)[0].rstrip(",").upper() if s.split() else ""
    return first if first in EARS_KEYWORDS else None


def find_decision_record(spec_path: Path) -> Path | None:
    """Locate the companion decision record: a sibling <slug>.decisions.md, or a DECISIONS.md at
    the spec's directory or any ancestor up to three levels."""
    sibling = spec_path.with_suffix("").with_suffix(".decisions.md")
    if sibling.is_file():
        return sibling
    alt = spec_path.parent / f"{spec_path.stem}.decisions.md"
    if alt.is_file():
        return alt
    d = spec_path.parent
    for _ in range(4):
        cand = d / "DECISIONS.md"
        if cand.is_file():
            return cand
        if d.parent == d:
            break
        d = d.parent
    return None


def tag_attempts(sections: dict[str, str]) -> list[str]:
    """Every phase-tag attempt found where tags are MEANINGFUL: on bullet lines inside the blocks
    that carry tagged items (see TAGGABLE_BLOCKS). Scanning the whole document instead would count a
    tag merely *mentioned* in prose - e.g. a metadata note explaining that "[P1a]" is valid - and
    report a phase that does not exist."""
    out: list[str] = []
    for key in TAGGABLE_BLOCKS:
        body = find_block(sections, key)
        if body is None:
            continue
        for line in bullets(body):
            out.extend(PHASE_TAG_RE.findall(line))
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


def lint(text: str, spec_path: Path | None = None) -> Report:
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

    # 6. phase tags well-formed. Scanned only where tags are meaningful (see tag_attempts), so a tag
    #    mentioned in prose is not reported as if it tagged an item.
    attempts = tag_attempts(sections)
    bad_tags = sorted({t for t in attempts if not WELLFORMED_PHASE_RE.match(t)})
    if bad_tags:
        r.err(f"malformed phase tag(s): {', '.join(bad_tags)} - use [P1], [P2], ... "
              f"or a sub-phase like [P1a]")
    good_tags = sorted({t for t in attempts if WELLFORMED_PHASE_RE.match(t)})
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

    reqs_body = find_block(sections, "requirements") or ""
    req_pairs = requirement_lines(reqs_body)

    # 9. Duplicate requirements. A refactor that copies before deleting leaves a duplicate that is
    #    individually well-formed and reads as normal - invisible to every other check here.
    seen: dict[str, int] = {}
    for _, text in req_pairs:
        seen[text] = seen.get(text, 0) + 1
    dupes = [t for t, n in seen.items() if n > 1]
    if dupes:
        r.err(f"{len(dupes)} duplicated requirement(s) - the same text appears more than once")
        for t in dupes[:3]:
            r.err(f"    -> {t[:90]}")
    elif req_pairs:
        r.ok("no duplicated requirements")

    # 10. EARS pattern filing: does each requirement sit under the right subsection?
    misfiled: list[str] = []
    for heading, text in req_pairs:
        expected = next((v for k, v in EARS_EXPECTED.items() if heading.startswith(k)), "SKIP")
        if expected == "SKIP":
            continue
        got = opening_keyword(text)
        if expected is None and got is not None:
            misfiled.append(f"'{got}' in '{heading}': {text[:70]}")
        elif expected is not None and got != expected:
            misfiled.append(f"expected '{expected}' in '{heading}': {text[:70]}")
    if misfiled:
        r.warn(f"{len(misfiled)} requirement(s) filed under the wrong EARS pattern")
        for m in misfiled[:3]:
            r.warn(f"    -> {m}")
    elif req_pairs:
        r.ok("EARS patterns match their subsections")

    # 11. Decision references resolve, and decision numbers are UNIQUE.
    #     Needs the file path, so it is skipped for a bare-text lint.
    if spec_path is not None:
        record = find_decision_record(spec_path)
        refs = sorted(set(DECISION_REF_RE.findall(clean)))
        if record is None:
            if refs:
                r.warn(f"{len(refs)} decision reference(s) cited but no decision record found "
                       f"(looked for <slug>.decisions.md and DECISIONS.md)")
        else:
            record_text = record.read_text(encoding="utf-8")
            headings = DECISION_DEF_RE.findall(record_text)
            defined = set(headings)

            # 11a. Duplicate decision numbers. Two sessions appending to one record WILL
            #      collide, and a duplicate is invisible to the reference check below --
            #      "(D43)" resolves perfectly well when D43 is defined twice, while every
            #      reference to it has silently become ambiguous. Error-level: a decision
            #      record whose numbers are not unique cannot be cited reliably at all.
            counts: dict[str, int] = {}
            for h in headings:
                counts[h] = counts.get(h, 0) + 1
            dupes = sorted(d for d, n in counts.items() if n > 1)
            if dupes:
                r.err(f"duplicate decision number(s) in {record.name}: {', '.join(dupes)} "
                      f"- every reference to them is ambiguous; renumber, never reuse")
            elif headings:
                highest = max(headings, key=lambda h: int(h[1:].split(".")[0]))
                r.ok(f"{len(headings)} decision(s) in {record.name}, numbers unique "
                     f"(highest: {highest} - append above this)")

            if refs:
                dangling = [d for d in refs if d not in defined]
                if dangling:
                    r.err(f"decision reference(s) with no entry in {record.name}: "
                          f"{', '.join(dangling)}")
                else:
                    r.ok(f"all {len(refs)} decision reference(s) resolve in {record.name}")

    # NOTE: the subject index is NOT checked here, deliberately. Verifying it means
    # re-deriving it, and the derivation belongs to scripts/subject_index.py, which owns
    # the per-subject patterns. Implementing a second derivation in this file produced
    # confident false positives on six rows -- the two implementations simply disagreed.
    # Use `subject_index.py --check <spec>` instead: the tool that owns a derivation owns
    # its check, or the check becomes a second source of truth (D46's lesson, applied to
    # this toolkit).

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

    report = lint(path.read_text(encoding="utf-8"), path)

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

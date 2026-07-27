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
  - NUMBERED SEQUENCES, as one general rule rather than per-case: any numbered set should be
    unique and contiguous, because a duplicate makes every reference to it ambiguous and a gap
    usually means an entry was deleted. Applied to decision numbers, phase tags (plus a
    cross-check against the 'phase N' headings) and ordered markdown lists, in the spec and in
    its sibling build prompt. Two of those three had already failed on a real project: a
    decision collision found only by luck, and a build prompt reading 1..7, 10, 8, 9 -- which
    survived because markdown renumbers on render, so the source was wrong while the output
    looked right. Lazy numbering ('1. 1. 1.') is idiomatic and is not reported.
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
SHALL_RE = re.compile(r"\bSHALL\b")
#: A decision's transferable rule, and evidence that something holds it. Enforcement counts
#: as named if the line points at a test/check/scan/lint, or explicitly disclaims
#: checkability -- "judgment, not checkable" is an acceptable and honest answer.
RULE_LINE_RE = re.compile(r"^\*\*Rule\*\*[^\n]*(?:\n(?!\n)[^\n]*)*", re.MULTILINE)
#: Word boundaries alone are wrong here: `\btest\b` does not match `test_defect_classes.py`,
#: because `_` is a word character, nor `CriteriaNumberingTests`, and `\blint\b` misses
#: `lint_spec.py`. Naming the enforcing module is the single most likely way to name
#: enforcement, so the prefixes are open-ended. Caught by this check rejecting two rules that
#: did name their tests.
ENFORCEMENT_RE = re.compile(
    r"(enforc\w*|test\w*|check\w*|scan\w*|lint\w*|assert\w*|guard\w*|"
    r"judgment|judgement|not checkable|unenforceable)",
    re.IGNORECASE,
)


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


def sequence_issues(numbers: list[int]) -> tuple[list[int], list[int]]:
    """(duplicates, gaps) for any numbered set. The general rule: a numbered sequence
    should be unique and contiguous, because a duplicate makes every reference to it
    ambiguous and a gap usually means an entry was deleted.

    Applied to decision numbers, phase tags and ordered lists alike -- the failure mode
    is identical in all three, and it has occurred in two of them on this project."""
    seen: dict[int, int] = {}
    for n in numbers:
        seen[n] = seen.get(n, 0) + 1
    dupes = sorted(n for n, c in seen.items() if c > 1)
    uniq = sorted(seen)
    gaps = [n for n in range(uniq[0], uniq[-1] + 1) if n not in seen] if uniq else []
    return dupes, gaps


def ordered_list_runs(text: str) -> list[tuple[int, list[int]]]:
    """(first line number, numbers) for each run of consecutive ordered-list items.

    A run ends at any line that is not an ordered item at the same indent. Markdown
    renumbers on render, so a mis-ordered source list looks perfectly correct in the
    output -- which is precisely how a 1..7, 10, 8, 9 sequence survived review."""
    runs: list[tuple[int, list[int]]] = []
    current: list[int] = []
    start = 0
    indent = -1
    for i, line in enumerate(text.splitlines(), start=1):
        m = re.match(r"^(\s*)(\d+)\.\s", line)
        if m and (indent in (-1, len(m.group(1)))):
            if not current:
                start, indent = i, len(m.group(1))
            current.append(int(m.group(2)))
            continue
        if current and not line.strip().startswith(("   ", "\t")) and not line.startswith(" "):
            if len(current) > 1:
                runs.append((start, current))
            current, indent = [], -1
    if len(current) > 1:
        runs.append((start, current))
    return runs


def numbering_faults(text: str, label: str) -> list[str]:
    """Mis-ordered ordered lists in a markdown body.

    An all-equal run is LEGITIMATE: '1. 1. 1.' is idiomatic lazy numbering that markdown
    renders as 1, 2, 3. Only a run that is neither all-equal nor strictly incrementing by
    one is reported."""
    out: list[str] = []
    for line_no, nums in ordered_list_runs(text):
        if len(set(nums)) == 1:
            continue
        expected = list(range(nums[0], nums[0] + len(nums)))
        if nums != expected:
            out.append(f"{label} line {line_no}: ordered list runs "
                       f"{', '.join(map(str, nums))} (expected "
                       f"{nums[0]}..{nums[0] + len(nums) - 1})")
    return out


#: Tokens in a **Rule** line that name something which must exist: a module file, a test class,
#: or a test function. Deliberately narrow -- prose words like "checked" satisfy the
#: enforcement-shaped test above, but only a NAME can be resolved, and only names are resolved.
ENFORCEMENT_TOKEN_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*\.py|[A-Z][A-Za-z0-9]*Tests?|test_[a-z0-9_]{3,})\b"
)

_PROJECT_TEXT_SUFFIXES = frozenset({".py", ".md", ".toml", ".cfg", ".json", ".yml", ".yaml"})
_PROJECT_SKIP_DIRS = frozenset({".git", "__pycache__", "node_modules", ".venv", "venv",
                                "build", "dist", ".pytest_cache"})


def _project_text(root: Path, skip: set[str], budget: int = 12_000_000) -> str | None:
    """All readable source text under ``root``, concatenated, for name resolution.

    Returns None when the tree is implausibly large, so the linter never becomes slow on a
    repository it was pointed at by accident. Filenames are included as well as contents, since
    a rule naming `test_defect_classes.py` is satisfied by that file existing even if nothing
    mentions it in prose."""
    chunks: list[str] = []
    total = 0
    for path in sorted(root.rglob("*")):
        if _PROJECT_SKIP_DIRS & set(path.parts):
            continue
        if not path.is_file() or path.name in skip:
            continue
        chunks.append(path.name)
        if path.suffix not in _PROJECT_TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        total += len(text)
        if total > budget:
            return None
        chunks.append(text)
    return "\n".join(chunks)


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
    shall_reqs: list[str] = []
    if reqs is not None:
        # Count requirement BULLETS, via the same folding reader the duplicate and EARS-filing
        # checks use. This counted physical lines containing "SHALL", which is not the same
        # thing: a requirement wraps across several lines, and a continuation line frequently
        # opens "SHALL NOT ...", so it counted twice. Measured on a real spec, adding five
        # requirements moved the reported number by nine, and merely re-wrapping one
        # requirement moved it while changing no requirement at all.
        #
        # That matters beyond tidiness. This number gets used as a checksum -- one spec's
        # sweep caught nine silently duplicated requirements precisely because the count was
        # compared against a remembered value -- and a checksum that responds to reflowing is
        # worse than none, because it cries wolf and then gets ignored.
        shall_reqs = [text for _heading, text in requirement_lines(reqs) if SHALL_RE.search(text)]
        if not shall_reqs:
            r.err('"requirements" has no SHALL statement - requirements must be EARS + SHALL')
        else:
            # Clauses reported alongside, and labelled as clauses: one requirement may carry
            # several obligations ("SHALL cover X, SHALL exclude Y"), which is worth seeing but
            # is not a count of requirements and must not be compared against one.
            clauses = sum(len(SHALL_RE.findall(text)) for text in shall_reqs)
            r.ok(f"{len(shall_reqs)} SHALL requirement(s) found, {clauses} SHALL clause(s)")
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
    #    Both sides are now per-bullet: criteria come from a `- [ ]` regex and requirements from
    #    the folding reader. Against the old line count this compared bullets to lines, so it
    #    fired on specs whose coverage was complete -- a warning that is always on is a warning
    #    nobody reads, which cost it the one job it had.
    if shall_reqs and crit_count and crit_count < len(shall_reqs):
        r.warn(f"fewer acceptance criteria ({crit_count}) than SHALL requirements "
               f"({len(shall_reqs)}) - every requirement needs >=1 check; verify the mapping")

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

            # 11b. Gaps in the integer sequence. A record is meant to grow by appending and
            #      to SUPERSEDE rather than delete, so a missing integer means an entry was
            #      removed and its reasoning lost. Warning, not error: a gap breaks no
            #      citation (a dangling one is caught below), and a number may be skipped
            #      deliberately.
            #
            #      Integers and sub-numbered entries are counted SEPARATELY, and the message
            #      says so. Reporting a bare total beside the highest number invites a
            #      comparison that is wrong whenever the record is zero-indexed or uses
            #      sub-numbers: 52 headings against a highest of D48 looks like four missing
            #      entries, but is exactly D0..D48 plus three D11.x entries.
            if headings and not dupes:
                ints = sorted({int(h[1:].split(".")[0]) for h in headings})
                subs = [h for h in headings if "." in h]
                _, gaps = sequence_issues(ints)
                sub_note = f", +{len(subs)} sub-numbered" if subs else ""
                if gaps:
                    shown = ", ".join(f"D{n}" for n in gaps[:8])
                    more = "" if len(gaps) <= 8 else f" (and {len(gaps) - 8} more)"
                    r.warn(f"gap(s) in the decision sequence: {shown}{more} - a record should "
                           f"supersede rather than delete, so a missing number usually means "
                           f"an entry was removed and its reasoning lost")
                r.ok(f"{len(ints)} decision(s) D{ints[0]}-D{ints[-1]}{sub_note} in "
                     f"{record.name}, numbers unique"
                     f"{'' if gaps else ', no gaps'} - append above D{ints[-1]}")

            if refs:
                dangling = [d for d in refs if d not in defined]
                if dangling:
                    r.err(f"decision reference(s) with no entry in {record.name}: "
                          f"{', '.join(dangling)}")
                else:
                    r.ok(f"all {len(refs)} decision reference(s) resolve in {record.name}")

            # 11d. Every decision states a transferable RULE, and names what enforces it.
            #
            #      A decision record accumulates hard-won rules as prose, and prose is
            #      enforced by whoever remembers it. Observed on a real project: a rule was
            #      written ("anything a tool says about itself is a claim, and every claim
            #      gets a check") and violated in the SAME commit, by its own author; the
            #      next session found the two violations as fresh defects. Recording a rule
            #      is not applying it, so the rule must say how it is held.
            #
            #      Retroactive enforcement would be useless here - on that project only 5 of
            #      67 entries carried an extractable rule line - so the requirement starts at
            #      a declared floor. Put `<!-- rules-required-from: D67 -->` in the record;
            #      entries at or above it must carry `**Rule**` naming either a check or,
            #      explicitly, that the rule is judgment and not checkable.
            floor_m = re.search(r"<!--\s*rules-required-from:\s*D(\d+)\s*-->", record_text)
            blocks = re.split(r"^##\s+(?=D\d)", record_text, flags=re.MULTILINE)[1:]
            with_rule = [b.split(None, 1)[0] for b in blocks if RULE_LINE_RE.search(b)]
            if floor_m is None:
                if blocks:
                    r.warn(f"{len(with_rule)} of {len(blocks)} decision(s) state a "
                           f"transferable **Rule** - add `<!-- rules-required-from: D<n> -->` "
                           f"to {record.name} to require one from D<n> onward, so new rules "
                           f"arrive with their enforcement named")
            else:
                floor = int(floor_m.group(1))
                missing_rule: list[str] = []
                unenforced: list[str] = []
                for b in blocks:
                    did = b.split(None, 1)[0]
                    num = int(did[1:].split(".")[0])
                    if num < floor:
                        continue
                    m = RULE_LINE_RE.search(b)
                    if m is None:
                        missing_rule.append(did)
                    elif not ENFORCEMENT_RE.search(m.group(0)):
                        unenforced.append(did)
                if missing_rule:
                    r.err(f"decision(s) at or above the D{floor} floor with no **Rule** line: "
                          f"{', '.join(missing_rule)} - state the transferable rule, or the "
                          f"lesson stays local to the fix that taught it")
                if unenforced:
                    r.err(f"decision(s) whose **Rule** names no enforcement: "
                          f"{', '.join(unenforced)} - name the check that holds it, or say "
                          f"\"judgment, not checkable\"; an unenforced rule is enforced by "
                          f"whoever remembers it")
                # The named enforcement must EXIST. Without this, the check confirmed that an
                # enforcement-shaped word was present and nothing more: a rule reading
                # "Enforced by test_completely_imaginary_module.py" passed clean. That is the
                # very defect this mechanism was built to stop -- a claim nothing compares --
                # sitting inside the mechanism. Demonstrated before being fixed.
                #
                # Resolution is by presence of the named token anywhere in the project's source,
                # not by importing it: the linter must stay a text tool, and a token that appears
                # nowhere is dangling regardless of how it would have been imported.
                # Two different findings, deliberately graded apart. A rule naming SEVERAL things
                # of which some exist is enforced -- the unresolved one is very often a tool in
                # another repository, which this linter cannot see and should not pretend to.
                # (Observed immediately: a rule correctly cited `lint_spec.py`, which lives in
                # the toolkit rather than the project being linted.) A rule where NOTHING it
                # names exists is unenforced, and that is an error.
                dangling: list[str] = []
                unenforceable: list[str] = []
                haystack = _project_text(record.parent, skip={record.name, spec_path.name})
                if haystack is not None:
                    for b in blocks:
                        did = b.split(None, 1)[0]
                        if int(did[1:].split(".")[0]) < floor:
                            continue
                        m = RULE_LINE_RE.search(b)
                        if m is None:
                            continue
                        tokens = sorted(set(ENFORCEMENT_TOKEN_RE.findall(m.group(0))))
                        if not tokens:
                            continue  # worded without a name; the word-level check above applies
                        missing = [t for t in tokens if t not in haystack]
                        if len(missing) == len(tokens):
                            unenforceable.append(f"{did} -> {', '.join(missing)}")
                        else:
                            dangling.extend(f"{did} -> {t}" for t in missing)
                if unenforceable:
                    r.err(f"**Rule** line(s) where NOTHING named as enforcement exists in the "
                          f"project: {'; '.join(unenforceable)} - a rule naming a test that does "
                          f"not exist is the same unchecked claim the rule requirement exists to "
                          f"prevent")
                if dangling:
                    r.warn(f"**Rule** line(s) cite enforcement not found in this project (other "
                           f"named enforcement does resolve, so this is usually a tool in another "
                           f"repository): {', '.join(dangling)}")

                if not missing_rule and not unenforced and not unenforceable:
                    at_or_above = [b.split(None, 1)[0] for b in blocks
                                   if int(b.split(None, 1)[0][1:].split(".")[0]) >= floor]
                    resolved = "" if haystack is None else ", enforcement resolved"
                    r.ok(f"every decision from D{floor} onward states an enforced **Rule** "
                         f"({len(at_or_above)} entr(y/ies); {len(with_rule)} of {len(blocks)} "
                         f"overall{resolved})")

            # 11e. The negative space: what the last sweep did NOT check.
            #
            #      Sweeps record what they fixed. The gap that keeps recurring is what they
            #      knowingly did not look at - one sweep's checks iterated only the in-repo
            #      dataset splits, which was true, deliberate, and unwritten, so the next
            #      sweep rediscovered it as a defect. Requiring the list is cheap; requiring
            #      it to be CURRENT is what makes it worth reading, so it is compared against
            #      the spec's own `Last swept` stamp.
            not_checked = re.search(
                r"^##\s+Not checked\b[^\n]*?(?:as of\s+(?P<stamp>[^\n]+))?$",
                record_text, re.MULTILINE | re.IGNORECASE,
            )
            swept = re.search(r"Last swept:\s*([^\n*]+)", clean)
            if not_checked is None:
                if swept is not None:
                    r.warn(f"{record.name} has no `## Not checked` section - a sweep records "
                           f"what it fixed; the recurring gap is what it knowingly did not "
                           f"look at, which the next reader needs first")
            else:
                stamp = (not_checked.group("stamp") or "").strip()
                body = record_text[not_checked.end():].split("\n##", 1)[0].strip()
                if not body:
                    r.err('"## Not checked" is empty - "nothing" is itself a claim; if the '
                          "sweep truly left no gap, say so and why")
                elif not stamp:
                    r.warn('"## Not checked" carries no "as of <version> @ <decision>" stamp, '
                           "so nothing can tell whether it predates the last sweep")
                elif swept is not None:
                    tokens = [t for t in re.findall(r"[\w.]+", stamp) if any(c.isdigit() for c in t)]
                    if tokens and not all(t in swept.group(1) for t in tokens):
                        r.err(f'"## Not checked" is stamped {stamp!r} but the spec was last '
                              f"swept at {swept.group(1).strip()!r} - the negative-space list "
                              f"predates the last sweep, so it describes an earlier state")
                    else:
                        r.ok(f'"## Not checked" is current ({stamp})')

    # 11f. Changelog versions are a numbered set too. Found live: two sessions each minted a
    #      `0.18.0` entry for different work, in the same document, on the same day. Same class
    #      as duplicate decision numbers and duplicate criterion ids -- and it kept slipping
    #      through because each generalization of "check any numbered set" only reached the sets
    #      the tool already happened to parse. So: enumerate the sets that exist, then confirm
    #      the enforcement reaches each.
    changelog = find_block(sections, "changelog")
    if changelog is not None:
        versions = re.findall(r"^-\s+(\d+\.\d+\.\d+)\b", changelog, re.MULTILINE)
        if versions:
            counts: dict[str, int] = {}
            for v in versions:
                counts[v] = counts.get(v, 0) + 1
            dupes = sorted(v for v, n in counts.items() if n > 1)
            if dupes:
                r.err(f"duplicate changelog version(s): {', '.join(dupes)} - two entries claim "
                      f"the same version, so neither identifies a state of the spec; renumber "
                      f"the later one")
            keyed = [tuple(int(p) for p in v.split(".")) for v in versions]
            if keyed != sorted(keyed, reverse=True):
                r.warn("changelog versions are not in descending order - newest first is the "
                       "convention, and an out-of-order entry usually means one was inserted "
                       "at the wrong place")
            elif not dupes:
                r.ok(f"{len(versions)} changelog version(s), unique and newest-first "
                     f"({versions[0]} .. {versions[-1]})")

    # 12. Phase-tag sequence. Same general rule as decision numbers: unique and
    #     contiguous. A gap (P1, P2, P4) means a phase was dropped or a tag mistyped, and
    #     since the build prompt is scoped to ONE phase, a missing phase is work that no
    #     prompt will ever cover.
    if good_tags:
        phase_ints = sorted({int(t[2:-1].rstrip("abcdefghijklmnopqrstuvwxyz"))
                             for t in good_tags})
        _, phase_gaps = sequence_issues(phase_ints)
        if phase_gaps:
            r.warn(f"phase tag gap(s): {', '.join(f'[P{n}]' for n in phase_gaps)} - a phase "
                   f"with no tagged items is work no build prompt will cover")
        # Cross-check the tags actually used against the '### phase N' headings, so a
        # documented phase with no items (or an item in an undocumented phase) surfaces.
        phase_headings = {int(m) for m in re.findall(r"^###\s+phase\s+(\d+)", clean,
                                                     re.MULTILINE | re.IGNORECASE)}
        if phase_headings:
            tagged_not_documented = sorted(set(phase_ints) - phase_headings)
            documented_not_tagged = sorted(phase_headings - set(phase_ints))
            if tagged_not_documented:
                r.warn(f"phase(s) tagged but with no 'phase N' heading: "
                       f"{', '.join(f'P{n}' for n in tagged_not_documented)}")
            if documented_not_tagged:
                r.warn(f"phase(s) with a heading but no tagged items: "
                       f"{', '.join(f'P{n}' for n in documented_not_tagged)}")
            if not tagged_not_documented and not documented_not_tagged:
                r.ok(f"phase tags and phase headings agree ({len(phase_headings)} phases)")

    # 13. Ordered-list numbering, in the spec and in its sibling build prompt. Markdown
    #     renumbers on render, so a mis-ordered source list looks correct in the output --
    #     which is how an insertion left a build prompt reading 1..7, 10, 8, 9 unnoticed.
    #     The build prompt is checked for numbering ONLY: it has no required blocks, so
    #     linting it as a spec would be meaningless.
    faults = numbering_faults(clean, "spec")
    if spec_path is not None:
        companion = spec_path.parent / f"{spec_path.stem}.build-prompt.md"
        if companion.is_file():
            faults += numbering_faults(
                strip_comments(companion.read_text(encoding="utf-8")), companion.name
            )
    if faults:
        r.warn(f"{len(faults)} mis-ordered ordered list(s) - markdown renders them "
               f"correctly, so the source is wrong while the output looks right")
        for f in faults[:3]:
            r.warn(f"    -> {f}")
    else:
        r.ok("ordered lists are sequential")

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

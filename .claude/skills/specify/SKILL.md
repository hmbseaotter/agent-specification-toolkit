---
name: specify
description: >-
  Interview the user to produce a complete, agent-ready specification, then emit what is needed to
  build it: for a coded feature/agent a phase-scoped build prompt, or for a skill / declarative agent
  the artifact itself (SKILL.md / AGENT.md). Surfaces every assumption for review, slices the work
  into a phased plan, and runs a build-readiness (model/effort) check. Use when the user wants to
  design, specify, plan, or scope a new agent, feature, or skill; turn a vague idea, PRD, or plan
  into a rigorous spec; write requirements in EARS / SHALL with testable acceptance criteria; produce
  a build prompt for a coding agent; or amend, advance, review, audit or sweep an existing spec under specs/
  for drift and staleness. Reasoning-driven, one question at a time.
---

# Specification Interviewer

Your job is to help the user — and gently *force* them — to supply every input an AI coding agent
needs to build the target, then produce a **complete, production-grade specification**, slice it
into **implementation phases the user chooses from**, and hand off a **build prompt scoped to the
chosen phase**. A missing answer now becomes a wrong implementation later, so do not let blocks
stay empty or vague.

**Authoritative spec structure:** write specs using the skeleton in the spec template (shipped
with this toolkit). That file is the single source of truth for block names, the EARS patterns,
the agent dimensions, the `[P#]` phase-tag convention, the assumptions block, and the hand-off
prompt. Read it before assembling a spec.

**Companion files (where to find them):** this skill uses three helper files. When you run from the
toolkit **repo** they are at `templates/specification-template.md`,
`templates/decision-record-template.md` and `scripts/lint_spec.py`. When the skill is **installed
globally** they sit **next to this `SKILL.md`**, flat, as `specification-template.md`,
`decision-record-template.md` and `lint_spec.py`. Use whichever layout is present — locate them with
your file tools if unsure.

**Target to specify:** take it from how the user invoked the skill (whatever they typed after the
skill name / in their request). If that is empty, your **first question** is what we are
specifying — name the feature or agent.

---

## First: pick the mode (this is deterministic — no model judgment needed)
Check `specs/` for a spec matching the target:
- **New spec** (no match, or the user names a new target) → run the full flow below, STEP 0 → 7.
- **Amend** (the user points at an existing `specs/<x>.md` to change it) → do **not** re-interview
  everything. Go to the affected block, make the change with the user, append a line to the
  spec's **changelog** (date + reason), **bump the Spec version** in metadata, re-run the linter,
  and re-derive only the affected phase tags / build prompt. Re-check only the delta.
- **Advance a phase** (the user wants the next phase's build prompt for an existing spec) → this is
  **cheap and deterministic: no interview, no elicitation spend.** Re-slice the same spec by the
  next phase's `[P#]` tags, run the build-readiness check (STEP 6), and emit the next build prompt
  (STEP 7, output 3). The spec already contains the phases.

- **Sweep** (the user asks to review, audit or maintain an existing spec, *or* the staleness check below
  says one is due) → no interview. Run the maintenance checklist in **STEP 8**.

If the mode is ambiguous, ask which one. Default to **New spec**.

**Staleness check — run it in Amend and Advance-phase modes, before doing anything else.** Read the spec's
`Last swept:` metadata line. If **~8–10 decisions have accrued since it**, tell the user a sweep is due and
offer one before proceeding. Do not silently continue: a spec drifts fastest during exactly the runs that
would trigger this, and nobody remembers to ask.

---

## Then: classify the target by build distance (deterministic — no model judgment)
The target's **build class** decides how much of the flow applies and what the final output is:
- **Zero-distance** — a **skill** or a **declarative agent** (harness-run markdown, e.g. a Claude
  Code subagent). "Building" is deterministic reformatting, so THIS SKILL EMITS THE ARTIFACT ITSELF
  (a `SKILL.md` skill dir, or an `AGENT.md`) — there is no separate building agent. Skip the
  agent-runtime dimensions that don't apply (state & memory, model routing, iteration/budget STOP),
  phasing (STEP 6b), and build-readiness (STEP 6c). Keep FULL rigor on role, outcome, scope, the EARS
  steps, the determinism boundary, acceptance criteria, and tools/permissions if it acts.
- **Build-required** — a **coded feature** or **coded agent**. Building is real engineering, so run
  the full flow and hand off a **build prompt** to a building agent (STEP 7), including the plan-gate.

Record the target type + build class in the spec's metadata. If unsure, ask. This is the
spec-to-artifact **distance** axis: distance ~= 0 -> emit the artifact; distance large -> build prompt.

---

## How to run the interview
- **One question at a time.** Ask, wait, listen. Never dump a list of questions in one message.
- **The user thinks out loud and asks questions back — expect it, welcome it.** Engage their
  tangents and questions genuinely and helpfully, react with suggestions / corrections /
  identified gaps or problems (immediate or potential), then steer back to the open question.
  Don't railroad; don't lose the thread.
- **Keep a visible ledger.** Track every block and its status: `☐ empty · ◐ partial · ☑ done`.
  Show the ledger at the start, whenever the user asks "where are we," and at each block
  transition.
- **Reflect before advancing.** Summarize the answer in one line, confirm, then move on.
- Work the blocks in order, but if the user jumps ahead, capture it in the right block and return.
- **Elicitation is conversational** (free-text Q&A). Use the structured **AskUserQuestion** tool
  only at the decision points that follow: the phase-composition menu (STEP 5) and the
  build-readiness acknowledgement (STEP 6).
- **Keep a decision record as you go — it captures the options REJECTED.** Whenever the interview
  resolves a genuine fork (real alternatives existed), append an entry: the fork, the options
  considered, the decision, WHY, and any consequence or caveat it creates. Write it **during** the
  interview, never reconstructed at the end — by then the alternatives are gone and only the winner
  is remembered. This is **not** a duplicate of the spec's `prior decisions` block: that block is the
  compact what-and-why a building agent needs, whereas the record is the fuller reasoning a human
  needs later when asking "was X considered, and why did it lose?". Use
  `templates/decision-record-template.md` for the entry shape, and emit it at STEP 7.

---

## STEP 0 — Intake of pre-existing inputs (ALWAYS do this first)
Before interviewing from scratch, ask whether the user already has any input artifacts: a **PRD, a
plan of action, design notes, a diagram, or existing code / an existing spec.**

- **If yes:** read them, and **evaluate them critically — first, always. Pre-existing inputs are
  considered, never treated as gospel.**
  1. Extract what they already answer and pre-fill the relevant blocks (mark them ◐ or ☑).
  2. Then actively surface: gaps, contradictions, risky or unsafe assumptions, anything ambiguous
     or that looks wrong or inefficient. **Raise concerns and ask the user to clarify them.**
  3. The aim is the **best possible agent in the most efficient way** — so reuse what is solid and
     question what is not. Only interview on what the inputs leave missing or unconvincing.
- **If no:** proceed from scratch through the blocks.

**Then establish these two before interviewing the blocks — do NOT infer them:**
- **Where the artifacts land.** Ask for the target repo root / directory that will hold `specs/` and
  the thing being built. Inferring it and hoping the assumptions gate catches a wrong guess wastes a
  round trip at best, and writes files into the wrong tree at worst.
- **Intended visibility / distribution** — private, internal, or public? Ask this whenever the target
  touches secrets, credentials, held-out evaluation data, or proprietary content. It is a **design
  input, not a release-day detail**: publishing changes the architecture (a public answer key
  contradicts a "held-out ground truth" claim, forcing a public/held-out split), and the asymmetry is
  brutal — a secret committed to public history is permanent.

---

## Hold the line — do not accept weak answers (this is the point)
Name the problem plainly and ask again:
- **Outcome must be observable/measurable.** Reject "good UX / fast / intuitive." Push for a
  success condition a test could check.
- **Scope needs an explicit OUT list.** Make the user name at least one thing deliberately not
  done, and why. With no exclusions, an agent builds the most complete thing it can imagine.
- **Requirements are EARS and use SHALL.** "should / nice to have / ideally" is not a requirement
  — say so, and either cut it or move it to Prior decisions.
- **Trace everything.** Every requirement → at least one specific, machine-checkable acceptance
  criterion.
- **Enumerations need per-member semantics — never accept the list alone.** Whenever a requirement,
  schema or contract introduces an enumerated set of values (a status, category, mode, severity,
  disposition), elicit what EACH member means for the downstream logic and write it into the
  requirements. "Status is MATCH or DISCREPANCY" is a data shape, not a behaviour; "a MATCH asserts
  correctness and is therefore ineligible to be counted as a false positive" is the requirement. Any
  member whose behaviour is left implicit gets INVENTED during the build — by the interviewer while
  drafting, or worse by the building agent, silently.
- **Probe the silent skips.** Explicitly ask which non-functional needs apply: security,
  performance, error handling, observability, accessibility, privacy — **plus these three, which are
  cheap to design in and expensive to retrofit:**
  - **Determinism / reproducibility.** Must identical inputs produce identical output, byte for byte?
    Anything that scores, grades, compares, ranks or audits almost always must — and it will not
    happen by accident: a stray timestamp, an unordered set, or a float where a decimal belongs
    silently breaks it. If it matters, make it a requirement and name what is excluded from the
    comparison (e.g. a run-metadata envelope holding exactly the non-deterministic fields).
  - **Time & timezone discipline.** How are timestamps stored and compared? Bare local dates make
    ordering ambiguous across zones — "whose midnight?" — which quietly corrupts any
    before/after check. Push for one normalized representation (e.g. UTC ISO-8601 with a `Z` suffix
    at a stated precision), with civil dates only as a declared, time-zone-carrying exception.
  - **Data integrity.** How would a reader know an output was not altered? Version control alone is
    only *conditionally* tamper-evident — history can be rewritten, and locally it can be erased
    without trace. Where the output is deterministic, embedding fingerprints of the inputs so the
    result can be RECOMPUTED is stronger and cheaper than any audit trail.

When the target is an **agent**, additionally hold the line on the agent dimensions:
- **Control surface MUST name a STOP condition.** An agent with no defined stop (completion / max
  iterations / budget / explicit kill) is a bug, not a feature. Also pin how a human drives it and
  where it must pause for approval.
- **Tools & permissions MUST name the "never do unattended" bright lines** (push, send, delete,
  spend, modify prod) — each requires a human checkpoint.
- **The determinism boundary MUST be filled.** Push back hard on "let the AI handle it" for
  anything deterministic: math, comparisons, parsing, validation, sorting, lookups, dedupe,
  threshold checks belong in **plain code (zero tokens)**. The LLM is reserved for genuine
  judgment, at a named model tier. This is the core cost discipline — do not let it stay vague.
  (This block applies to skills too, not only agents — a skill has deterministic steps as well.)
- **Type & value discipline on that deterministic code.** Require (a) static typing — type hints + a
  static checker (mypy/pyright; native in Java/Go/Rust) so a variable's type can't drift (a float
  silently becoming an int breaks fractional math); and (b) immutability — `typing.Final` / frozen
  dataclasses / tuples so constants stay constant. Make "type-check passes" an acceptance criterion.
  (N/A for a pure-prose skill with no code.)
- **Failure & escalation MUST say what happens when the agent is stuck** and how it reaches a
  human.

---

## STEP 1–4 — Elicit the blocks
Work the blocks defined in `templates/specification-template.md`. In order:
1. **metadata** — name, version (start 0.1.0), status DRAFT, date, author, target type, **build
   class** (zero-distance | build-required), and **role** (the stance the target adopts — include
   one only where it sharpens tone or domain expertise, e.g. "an expert reconciliation reviewer";
   write "n/a" when a persona adds nothing, including plain libraries and purely procedural
   targets. Prefer concrete behaviour over a persona label — "states the answer directly, then the
   caveat" beats "a friendly assistant". Never manufacture a role just to fill the field.)
   Also stamp **provenance** — `Produced by: /specify @ <short-sha>`. Get the sha with
   `git -C <toolkit-repo> log -1 --format=%h`; if the toolkit repo is not reachable, write
   `installed copy, sha unknown` rather than omitting the field. This skill evolves, so without a
   stamp there is no way to tell which generation a spec belongs to — or whether a gap it exhibits
   was already fixed upstream.
   Also stamp the **staleness marker** — `Last swept: <date> @ <spec version> @ D<highest decision>`, set to
   the emit date for a new spec. It makes "is a sweep due?" answerable at a glance instead of from memory.
   State the trigger on the line itself: **~8–10 accrued decisions, before publishing, or at phase completion
   — whichever comes first.** Make it **change-based, never calendar-based**: drift accumulates per decision,
   not per day, so a monthly reminder fires during quiet weeks and stays silent through exactly the heavy
   design runs that cause the drift.
2. **outcome** — what can a user DO that they couldn't before? Measurable.
3. **in scope** / **out of scope (v1)** — concretes in, explicit exclusions out (with reasons).
4. **Agent dimensions** (when the target is an agent; "n/a (not an agent)" for a plain feature):
   **control surface**, **triggers & scheduling**, **tools & permissions**, **state & memory**,
   **model & cost routing + determinism boundary**.
5. **constraints** — stack, what not to touch/assume, package rules.
6. **prior decisions** — already-settled choices + the *why* (institutional memory).
7. **requirements (EARS)** — walk each pattern that applies and phrase them in EARS for the user:
   ubiquitous / WHEN / WHILE / IF / WHERE, plus the non-functional categories. For an agent, write
   its behaviour here too (e.g. budget and escalation rules as IF/WHEN).
8. **failure & escalation** (agent) — recoverable vs unrecoverable errors, stuck/uncertain → escalate.
9. **acceptance criteria** — derive *with* the user from the requirements; every requirement gets a
   matching, specific, machine-checkable check. Group: happy path / edge cases / constraint
   validation (include agent bright-line checks, e.g. "never pushes without a human checkpoint").

---

## STEP 5 — Assemble + regeneration test
1. Assemble the **complete, production-grade specification** (the whole target) using the template
   structure, and show it to the user for edits.
2. Run the **regeneration test** out loud: *could an agent rebuild this from the spec alone and
   produce behaviourally identical output?* Name anything still missing; offer to fill it.
3. **Deterministic completeness check — use the linter, not tokens.** Run the companion
   `lint_spec.py` on the spec — `python scripts/lint_spec.py specs/<slug>.md` (use `python3` on
   macOS/Linux) from the repo, or the copy beside this skill if installed globally — and fix
   whatever it flags (each requirement → ≥1
   criterion; no "should" in requirements; non-empty out-of-scope; required blocks present; valid
   phase tags). Applying the determinism principle to this skill itself: don't burn tokens
   re-deriving checks that code can do.

---

## STEP 6a — Assumptions review GATE (before any phasing or build)
Populate the spec's **assumptions** block: every gap you filled, input you inferred, and default
you chose — one line each, with the **risk if it's wrong**. Then **present the list and require the
user to walk it**, confirming or correcting each:
- Confirmed assumptions → fold into **prior decisions** (so they stop being assumptions).
- Wrong ones → fix in place, then continue.

**Do not proceed to phasing until the user has reviewed the assumptions.** This is the
"review before any work starts" gate.

---

## STEP 6b — Phase composition (the compose-your-phase menu)
*(Build-required targets only. A zero-distance target — skill / declarative agent — has no phased
build: skip STEP 6b and 6c and go to STEP 7, which emits the artifact.)*

Derive a phased build plan **from the spec**, sized to the target's complexity (a small target may
need only P1 + P2; do not force a long checklist). Phasing **slices** the spec into a build order —
it never shrinks the production-grade target.

- **Decompose by common/cheap-now vs rare/expensive-later**, not just core-vs-hardening. (E.g. a
  file-reading agent: plain-text PDFs in the skeleton, graphical-layer PDFs as an optional add, and
  OCR/text-in-images in a later phase because it's the rare, costly edge case.)
- **Present the menu:**
  1. State the **SKELETON floor** — the items architecturally required for a coherent first slice
     — each marked **(required)** with a one-line rationale. These are *required but overridable*:
     the user may drop one **only by stating an explicit reason**, which you record in the
     implementation-phases block.
  2. Offer the **optional items** for this push as a **multi-select** (`AskUserQuestion`,
     `multiSelect: true`). The user picks which optional items go into this first push.
- **Resolve dependencies.** If the user selects an item whose prerequisite is not included, pull
  the prerequisite in (or flag it) — never let the user compose an incoherent phase.
- **Assign `[P#]` tags:** items chosen for this push get the current phase tag; deferred items get
  higher phase numbers. Write the `## implementation phases` block and tag the in-scope items,
  requirements, and acceptance criteria accordingly.

---

## STEP 6c — Build-readiness check (MUST-ACKNOWLEDGE guardrail)
This guards the **build-time session settings** — *which model/effort the session doing the build
should use for this phase.* Keep it distinct from the spec's **model & cost routing** block, which
is about the **built agent's** runtime models; do not conflate the two.

1. **State the model you are currently running as** (you know your own model — report it plainly).
2. **Assess this phase's cognitive load:** heavy = novel architecture, cross-cutting judgment,
   subtle correctness; light = mechanical glue, CRUD, deterministic wiring.
3. **Recommend a model + thinking-effort for this phase, flagging mismatch in BOTH directions:**
   - **Under-powered** (e.g. heavy phase on a small model / low effort) → recommend bumping up, or
     risk a poor build.
   - **Over-powered** (e.g. light phase on the top model at max effort) → recommend dialling down
     to avoid burning money for nothing.
   For effort: you may not be able to read the live thinking/effort setting, so **recommend a level
   and ask the user to confirm or adjust it** — do not claim to detect it.
4. **Require an explicit acknowledgement via `AskUserQuestion`:** "Proceed with current settings"
   or "I'll adjust `/model` / effort first." It **cannot be silently skipped.** Make the
   accountability explicit and on the record: the settings choice is the user's; once they
   acknowledge, a poor build caused by an ignored recommendation is a known, accepted trade-off —
   there's a cost to failures, so the prompt is the place to prevent the next one.

---

## STEP 7 — Emit the outputs
All artifacts land in **`specs/`** so they are collectable and survive the session.

1. **Spec file** → write to **`specs/<slugified-name>.md`** (create `specs/` if needed). This is
   the **whole production-grade target**: metadata, all blocks, `[P#]` tags, the
   `## implementation phases` block, the reviewed assumptions, and the changelog. If the user chose
   to stop early, write it anyway, title it `[DRAFT — INCOMPLETE]`, and leave `TODO:` markers in
   unfinished blocks.
2. **Assumptions list** — already reviewed at STEP 6a; it lives in the spec and you echo it back so
   the user has it in view.
3. **Output #3 depends on the build class** (see "classify the target by build distance"):

   **Build-required target (coded feature / coded agent) — a build prompt, scoped to the chosen
   phase.** **Write it to `specs/<slugified-name>.build-prompt.md`** (and show it), telling the user
   it targets phase *X* and is the file they hand to a **building agent** — the AI coding tool that
   implements it (e.g. a fresh Claude Code session, Cursor, or Aider), distinct from the target being
   built. It MUST:
   - Name the **target phase** and its tagged items + acceptance criteria.
   - Say: **build only this phase. Higher-phase items are documented-but-not-yet — do not build
     them, and do not make architectural choices that block them.**
   - **Plan gate:** instruct the building agent to ENTER PLAN MODE (or its tool's equivalent),
     present an implementation plan, and get human approval BEFORE writing code.
   - Enforce the **determinism boundary** (deterministic work in plain code; LLM only for the named
     judgment tasks at the named tier), the **type & value discipline** on that code (static typing +
     immutability for constants), and every **never-do-unattended bright line** (human checkpoints).
   - State the **recommended build-time model/effort** from STEP 6c.
   - Require verifying each acceptance criterion **by running it**; don't mark done until all pass;
     append any new calls to **decisions made**; and if the spec itself changes, add a changelog
     line and bump the version.

   **Zero-distance target (skill / declarative agent) — the artifact itself.** There is no build
   hand-off: building is deterministic, so PER THE TOOLKIT'S OWN DETERMINISM PRINCIPLE, YOU emit the
   artifact. Build it from the spec: a proper **`SKILL.md`** (frontmatter: name + description /
   when-to-use) or an **`AGENT.md`** (name, description, tools, model), populated from the spec —
   role → the "you are…" line; EARS steps → the procedure; determinism boundary → which steps call a
   script vs use judgment; acceptance criteria → the quality bar. If the spec needs a **custom
   deterministic tool**, also produce it as a companion script (the `SKILL.md` + `lint_spec.py`
   pattern). Then write it to TWO places, record it, and remind:
   1. **Canonical copy (durable, version-controlled)** → `specs/<slug>.emitted/` beside the spec —
      e.g. `specs/<slug>.emitted/SKILL.md` (+ any companion script). This is the safety copy: it lives
      with the spec in git, so deleting the live copy never loses the work.
   2. **Live copy (immediately usable)** → the target project's harness location:
      `.claude/skills/<name>/SKILL.md` (+ companion beside it) for a skill, or
      `.claude/agents/<name>.md` for a declarative agent. This is what makes it work in the project
      right away.
   3. **Record it in the spec** — add/update an **`## emitted artifacts`** section in
      `specs/<slug>.md` listing, un-missably: WHAT was emitted, WHERE each file went (BOTH the
      canonical and the live paths), and the date. Echo the same list in your final message so the
      user can audit — or cleanly remove a bad emit (delete the live copy; the canonical copy stays).
   4. **Commit-now reminder (milestone).** Tell the user to COMMIT these new files now, before editing
      anything, so the pristine emitted state is versioned — git is the recovery path, and forgetting
      to commit at this milestone is how a clean state gets lost.
   5. **Validate the frontmatter (deterministic, zero tokens).** Anthropic's `skill-creator` ships
      `scripts/quick_validate.py`, which checks things `lint_spec.py` does not: frontmatter is valid
      YAML, keys are limited to `{name, description, license, allowed-tools, metadata,
      compatibility}`, `name` is kebab-case and ≤64 chars, `description` is ≤1024 chars with no
      angle brackets. Two complementary linters, no overlap. If `skill-creator` is installed, run it
      on the emitted skill and fix what it flags; if it is not, say so and move on rather than
      hand-checking.
   6. **Offer empirical validation (a spec cannot measure itself).** This skill reasons about
      quality; it never MEASURES it. Anthropic's `skill-creator` does: it runs the new skill against
      a no-skill baseline on real prompts, grades each run against assertions, reports pass-rate
      variance across repeats, and — most usefully — measures how often the `description` actually
      TRIGGERS, then optimises it against a held-out test split. Nothing here can substitute for
      that. Tell the user it exists, that it is optional, and that the spec's **acceptance criteria
      map directly onto its `evals/evals.json` expectations** — same shape, no translation needed.
      For a non-expert user, name the concrete next step (invoke the `skill-creator` skill and ask
      it to run evals on the skill just emitted), not just the tool's name.

   The spec in `specs/<slug>.md` remains the source of truth — amend it and re-emit to regenerate.

   ### Spec-backed skills: improvements go through the spec, never in-place
   Once a skill is emitted from a spec, `specs/<slug>.md` is UPSTREAM of the artifact. Any
   improvement loop that edits the emitted `SKILL.md` directly — including `skill-creator`'s
   iteration loop, which rewrites `SKILL.md` from feedback round after round, and its description
   optimiser, which rewrites the `description` field — will silently drift the artifact away from
   its spec and turn that spec into a lie.

   So: take the finding, not the edit. Route feedback, grader output, and any optimised description
   back through **amend mode** (fix the affected block, changelog line, version bump, re-run the
   linter) and **re-emit**. Amend mode is deliberately cheap — no re-interview — so this costs
   little per cycle and keeps the spec honest. If the user has already hand-edited a live copy,
   say so plainly and reconcile it into the spec before re-emitting, rather than overwriting their
   work.

4. **Decision record** → write to **`specs/<slugified-name>.decisions.md`** (a repo-root
   `DECISIONS.md` is fine when the repo holds a single spec). This is the record you have been
   appending to throughout the interview — every fork, the options considered, the decision, why, and
   its consequences — in the shape given by `templates/decision-record-template.md`. Record its path
   in the spec's `Decision record:` metadata field so the two never drift apart, and tell the user
   that **any fork the BUILD resolves gets appended there too**, or the record goes stale the moment
   implementation starts. Emit this for every target class — a skill's forks are as worth recording as
   a coded agent's. Skip it **only** if the interview genuinely resolved no forks, and say so plainly
   rather than emitting an empty file.

Finish by telling the user the file paths — `specs/<slug>.md` and `specs/<slug>.decisions.md`, plus
either `specs/<slug>.build-prompt.md` (build-required) or the emitted artifact paths, canonical + live
(zero-distance) — and **remind them to commit at this milestone** (versioning the pristine state).
For build-required targets, note that **advancing to the next phase later is cheap** — no
re-interview, just re-slice and emit the next build prompt.

---

## STEP 8 — Sweep (maintenance mode)

A spec decays as decisions accrue. Not from bad decisions — from **good ones applied in one place and missed
in another**. Three passes over one real spec found **21 such defects**; the linter, at the time, could see
none of them. Work the checklist **in order**: the cheap mechanical checks first, so no attention is spent
reading for what code can find.

1. **Run the linter.** `python scripts/lint_spec.py specs/<slug>.md`. It catches duplicated requirements,
   requirements filed under the wrong EARS pattern, `(Dnn)` citations with no entry in the decision record, and
   **duplicate decision numbers** — two sessions appending to one record will collide, and a duplicate is
   invisible to the reference check, because `(D43)` resolves perfectly well when D43 is defined twice while
   every reference to it has silently become ambiguous. The linter also reports the **highest** decision number,
   so the next appender knows what to use: **read that before numbering anything.**
2. **Check the subject index** with `python scripts/subject_index.py specs/<slug>.md --check`, which regenerates
   and diffs; add the spec's own labels via `--subjects` if they differ from the defaults. **Never hand-maintain
   that table** — a hand-written one was measured wrong in six of nine rows, two of them wrong because it was
   authored before a reorganisation in the same commit had finished. A stale row is worse than no index: it does
   not merely fail to help, it misdirects the next sweep to the wrong sections. The check lives in
   `subject_index.py` and **not** in the linter on purpose: verifying the index means re-deriving it, and a
   second derivation in the linter produced confident false positives on six rows. **The tool that owns a
   derivation owns its check**, or the check becomes a second source of truth.
3. **Read the spec whole** — not in answer-shaped slices. Every contradiction found this way was a later
   decision applied in one place and missed in another, and only a whole read sees both places at once.
4. **Compare the build prompt against the spec, fact by fact** — match key, category enumeration, fingerprint
   count, component names, manifest contents, list numbering. **This is the highest-yield step and the one no
   linter can do.** Six of eight findings in one pass were here, in a document the two earlier passes had never
   opened. It matters most because the build prompt is what the *building agent reads*: a defect there is
   invisible to anyone reading the spec, and nothing downstream corrects it.
5. **Check supersessions.** Every decision that overturned an earlier one should leave an inline note on the
   entry it replaced, so no decision can be read in isolation and believed.
6. **Update `Last swept:`** in metadata — date, spec version, highest decision number. A marker nobody updates
   silently stops meaning anything, which is worse than having none.

Report findings grouped as **contradictions** (the spec says two different things), **stale** (superseded but
not updated) and **structural**. Fix contradictions and stale passages together; keep any large reorganisation
as its own separate change, so a semantic fix never rides along with a reshuffle.

**When reorganising, pick an invariant and treat any deviation as a defect** — the SHALL count works well. One
restructure briefly read 136 against an expected 127, revealing nine duplicates created by copying before
deleting. Duplicated requirements are individually well-formed and read as entirely normal; nothing else would
have caught them.

Keep your tone conversational and concise. One question at a time during elicitation.

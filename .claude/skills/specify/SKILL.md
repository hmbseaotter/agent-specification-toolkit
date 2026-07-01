---
name: specify
description: >-
  Interview the user to produce a complete, agent-ready specification (the production-grade
  target), surface every assumption for review, slice the work into a phased build plan the user
  composes, run a build-readiness (model/effort) check, then write the spec to specs/ and emit a
  phase-scoped build prompt. Use when the user wants to specify a new agent or feature, or to
  amend or advance an existing spec under specs/. Reasoning-driven, one question at a time.
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

**Companion files (where to find them):** this skill uses two helper files. When you run from the
toolkit **repo** they are at `templates/specification-template.md` and `scripts/lint_spec.py`. When
the skill is **installed globally** they sit **next to this `SKILL.md`** as
`specification-template.md` and `lint_spec.py`. Use whichever layout is present — locate them with
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

If the mode is ambiguous, ask which one. Default to **New spec**.

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
- **Probe the silent skips.** Explicitly ask which non-functional needs apply: security,
  performance, error handling, observability, accessibility, privacy.

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
   class** (zero-distance | build-required), and **role** (the persona the target adopts — e.g.
   "an expert reconciliation reviewer"; first-class for a skill/agent, "n/a" for a plain library).
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

   The spec in `specs/<slug>.md` remains the source of truth — amend it and re-emit to regenerate.

Finish by telling the user the file paths — `specs/<slug>.md` plus either
`specs/<slug>.build-prompt.md` (build-required) or the emitted artifact paths, canonical + live
(zero-distance) — and **remind them to commit at this milestone** (versioning the pristine state).
For build-required targets, note that **advancing to the next phase later is cheap** — no
re-interview, just re-slice and emit the next build prompt.

Keep your tone conversational and concise. One question at a time during elicitation.

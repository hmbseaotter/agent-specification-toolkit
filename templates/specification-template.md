# specification: [feature or agent name]

<!--
HOW TO USE
1. One spec = one feature, one agent, or one skill. Save as /specs/[slug].md.
2. Fill every block top to bottom. Delete the guidance comments as you go.
3. Blocks marked <!-- AGENT --> apply when the target is an autonomous / background /
   interactive agent. For a plain feature or a skill, write "n/a (not an agent)" in the blocks
   that don't apply and move on — don't delete them, so the structure stays checkable.
4. The "assumptions" block near the bottom is a REVIEW GATE: every assumption made during
   writing is listed there to be confirmed or corrected BEFORE any build starts.
5. Hand off with the prompt at the very bottom of this file.
6. Phase tags: tag each in-scope item, requirement, and acceptance criterion with the
   implementation phase it belongs to — [P1], [P2], … (see "implementation phases" below).
   The build prompt is scoped to ONE phase; the spec itself always stays the whole target.
7. Build class (see metadata). A ZERO-DISTANCE target (a skill or a declarative agent) has no
   separate build step — "building" is deterministic reformatting, so the interviewer emits the
   artifact (SKILL.md / AGENT.md) directly, and the agent-runtime blocks and phasing are usually
   "n/a". A BUILD-REQUIRED target (coded feature/agent) hands the build prompt to a building agent.

Keyword convention (RFC 2119 / 8174): SHALL = MUST = absolute, verifiable requirement.
We use SHALL for every requirement on purpose. If a line is only a "should," it is not a
requirement — cut it, or move it to "prior decisions."
-->

## metadata
- Spec version: 0.1.0          <!-- bump on every change; mirror it in the changelog at the bottom -->
- Status: DRAFT                <!-- DRAFT | READY-FOR-BUILD | IN-BUILD | BUILT -->
- Last updated: [YYYY-MM-DD]
- Author(s): [who]
- Target type: [skill | declarative agent (harness-run markdown, e.g. a Claude Code subagent) | feature | coded agent (CLI/background/GUI) | library/service]
- Build class: [zero-distance | build-required]   <!-- zero-distance: the "build" is deterministic reformatting, so the artifact (SKILL.md / AGENT.md) is EMITTED directly by the interviewer — skills & declarative agents. build-required: building is real engineering, so a build prompt is handed to a building agent — coded features & agents. This is the spec-to-artifact distance axis. -->
- Role: [the persona/role the target adopts, e.g. "an expert reconciliation reviewer"; first-class for a skill/agent, "n/a" for a plain library]

## outcome
<!-- One paragraph. What can a user DO that they couldn't before? Make it measurable. -->
[e.g. A user who has forgotten their password reaches their dashboard in under 2 minutes,
via email, with no manual support intervention.]

## in scope   <!-- tag each item with its phase: [P1], [P2], … -->
- [P1] [Concrete thing the agent SHALL build]
- [P2] [Concrete thing — deferred to a later push, but still part of the target]

## out of scope (v1)
<!-- As load-bearing as "in scope." With no exclusions, the agent builds the most complete
version it can imagine. Name what you are deliberately NOT doing, and why. -->
- [Excluded thing] — [why / deferred to when]
- [Excluded thing]

<!-- ============================================================================
     AGENT DIMENSIONS — fill these when the target is an agent.
     For a plain feature, write "n/a (not an agent)" in each and move on.
     ============================================================================ -->

## control surface   <!-- AGENT -->
<!-- How does the agent RUN, and how does a human DRIVE and STOP it? An agent with no defined
     stop condition is a bug, not a feature. -->
- Runtime / form factor: [background process controlled via Claude Code CLI | interactive CLI |
  web GUI / browser tab | scheduled job | …] <!-- if undecided, say so AND what the choice depends on -->
- Invoked / started by: [command, button, event]
- Human control mid-run: [pause/resume | approve-before-act checkpoints | none]
- Stopped by: [explicit stop command | completion condition | max iterations | budget exceeded]
- Human-in-the-loop checkpoints: [where it MUST pause for approval — see "never do unattended" below]

## triggers & scheduling   <!-- AGENT -->
- What starts a run: [on-demand | on event X | cron schedule | file change / webhook]
- Cadence: [e.g. every 15 min | on each new PR | manual only]
- Concurrency: [may runs overlap? if so, what prevents collisions?]

## tools & permissions   <!-- AGENT -->
<!-- What the agent may touch — and the bright lines it must never cross unattended. -->
- Allowed tools / APIs / integrations: [filesystem (which paths), network (which hosts), shell,
  git, MCP servers, …]
- Secrets / credentials needed + source: [env var | secret manager — NEVER hard-coded in the spec or code]
- Data it may read / write: [scope and locations]
- NEVER do unattended (hard bright lines): [push to a remote | send email/message | delete data |
  spend money | modify production] — each of these SHALL require a human checkpoint.

## state & memory   <!-- AGENT -->
- Persists state between runs? [stateless | persists]
- What state: [progress ledger | cache | learned facts]
- Where + format: [file / db / path]
- Reset / cleanup: [how stale state is cleared]

## model & cost routing + determinism boundary   <!-- AGENT — the cost discipline -->
<!-- CORE PRINCIPLE: do everything that CAN be deterministic in plain code (zero tokens).
     Spend the LLM only where genuine JUDGMENT is required. State the split explicitly — this
     block is where runaway cost is designed out before a single line is written. -->
- Deterministic (plain code, NO LLM): [the concrete ops for THIS target — math, comparisons,
  parsing, validation, sorting, lookups, dedupe, formatting, threshold checks, file I/O]
- Type & value discipline (for the deterministic code): (a) STATIC TYPING — type-hint it and gate on
  a static checker (mypy / pyright for Python; native in Java/Go/Rust) so a variable's type can't
  drift, e.g. a float slot silently receiving an int and breaking fractional math; (b) IMMUTABILITY
  — keep constants constant and prevent accidental reassignment (typing.Final, frozen dataclasses,
  tuples over lists). Make "type-check passes" an acceptance criterion. (N/A for a pure-prose skill.)
- Requires judgment (LLM): [ambiguous NL understanding, synthesis, fuzzy classification,
  prioritization that needs taste — list the actual ones]
- Model tier per judgment task: [task → model + why, e.g. "triage label → Haiku (cheap, high
  volume)"; "design review → Opus (hard judgment)"]
- Cost / budget guardrails: [token or $ budget per run | max LLM calls | max iterations]
- Stop / escalate when: [budget exceeded → halt + report | genuine ambiguity → ask a human]

<!-- ====================== end agent dimensions ====================== -->

## constraints
<!-- Stack + what the agent must not touch or assume. This block alone cuts most rework. -->
- Stack: [your actual stack]
- Do NOT [touch / replace / re-architect]: [thing] — [reason]
- Follow existing pattern: [file or convention to match]
- No new packages without flagging for approval first.

## prior decisions   <!-- INPUT: you author these BEFORE the build -->
<!-- Institutional memory across stateless sessions. The pre-answered "why this way?"
Rule: don't relitigate these — BUT you may flag one that looks unsafe or broken. -->
- [Decision]: [why it was made]
- [Decision]: [why it was made]

## requirements
<!-- Each requirement = one trigger + one verifiable response, in EARS.
All five patterns below. Every requirement must trace to >=1 acceptance criterion.
Tag each requirement with its phase: [P1], [P2], …
For an agent, write its behaviour here too (e.g. budget/escalation rules as IF/WHEN). -->

### ubiquitous (always active)
- The system SHALL [always-on behavior].

### event-driven (WHEN — triggered by an action)
- WHEN [trigger], the system SHALL [response].

### state-driven (WHILE — true for the duration of a state)
- WHILE [state], the system SHALL [response].

### unwanted behavior (IF — error handling)
- IF [bad condition], the system SHALL [specific response].

### optional feature (WHERE — behind a flag / config)
- WHERE [feature is enabled], the system SHALL [response].

### non-functional   <!-- the categories agents silently skip — spell out the ones that apply -->
- Security: [e.g. the system SHALL hash passwords with bcrypt, cost factor 12]
- Performance: [target / budget]
- Error handling / observability: [logging, user-facing failure behavior]
- Accessibility / privacy: [requirement if relevant]

## failure & escalation   <!-- AGENT -->
<!-- What the agent does when things go wrong. Phrase as IF/WHEN requirements where you can. -->
- Recoverable error: [retry policy | backoff | max attempts]
- Unrecoverable error: [halt | roll back | report what + where]
- Stuck / uncertain: [escalate to a human with which context]
- Escalation channel: [CLI prompt | message | log + stop]

## acceptance criteria
<!-- The pass/fail gate. Each item SPECIFIC and machine-checkable (a test or CI run, not
the agent's say-so). Don't mark the task complete until every box passes — by test, not vibe. -->

### happy path
- [ ] [P1] [Testable pass/fail check, e.g. "valid email -> reset email arrives within 5s"]
- [ ] [Testable check]

### edge cases
- [ ] [Edge case check]
- [ ] [Edge case check]

### constraint validation
- [ ] [e.g. "no new tables beyond X"]
- [ ] [e.g. "email sent via Resend, not another provider"]
- [ ] [AGENT bright-line: "never pushes to a remote without a human checkpoint" — assert it]

---

## implementation phases   <!-- a VIEW over this spec — it slices the build, not the target -->
<!--
The spec above is the complete, production-grade target. This block records how the build is
SLICED so a first push ships a thin working slice and hardens later. It never shrinks the target.
- Each in-scope item / requirement / acceptance criterion above carries a phase tag: [P1], [P2], …
- A phase is DONE when its tagged acceptance criteria pass — by running them.
- "Skeleton" items are the architecturally-required floor for a coherent first slice; they are
  marked (required). Drop one only with an explicit reason recorded here.
- Advancing to the next phase re-slices THIS spec — no re-interview needed.
- Collapse or expand the phase count to fit complexity (a small target may need only P1 + P2).
-->

### phase 1 — [skeleton / walking slice]
- Goal: [the thinnest version that delivers the core outcome end-to-end]
- Includes: [the required floor + any optional [P1] items chosen for the first push]
- Done when: [its tagged acceptance criteria pass]

### phase 2 — [robustness]
- Goal: [error handling, escalation, edge cases]
- Includes: [P2 items]

### phase 3 — [hardening]
- Goal: [security, observability, performance]
- Includes: [P3 items]

### phase 4 — [optimization / optional]
- Goal: [cost & model-routing tuning, nice-to-haves]
- Includes: [P4 items]

---

## assumptions   <!-- REVIEW GATE: confirm/correct each BEFORE any build starts -->
<!-- Every assumption made while writing this spec — gaps filled, inputs inferred, defaults
chosen. One line each: the assumption + the risk if it's wrong. Walk this list before building;
turn confirmed ones into "prior decisions" and fix the wrong ones in place. -->
- [ ] [Assumption] — risk if wrong: [what breaks]
- [ ] [Assumption] — risk if wrong: [what breaks]

---

## decisions made   <!-- OUTPUT: the AGENT appends here DURING the build -->
<!-- Any architectural call the spec didn't cover goes here. Fold these back into
"prior decisions" before the next session, or the codebase drifts from its source of truth. -->
- [agent fills in]

---

## emitted artifacts   <!-- OUTPUT (zero-distance targets): where the interviewer wrote the artifact -->
<!-- For a skill / declarative agent, the interviewer emits the artifact and records it here:
WHAT was emitted, and WHERE each file went — the canonical copy (specs/<slug>.emitted/) AND the live
copy (.claude/skills/<name>/ or .claude/agents/<name>.md) — with a date, so a bad emit can be audited
and cleanly removed (delete the live copy; the canonical copy stays). Commit these at the emit
milestone. Write "n/a (build-required — see build prompt)" for a build-required target. -->
- [interviewer fills in on emit]

---

## changelog   <!-- spec evolution — newest first; bump "Spec version" in metadata to match -->
- 0.1.0 ([YYYY-MM-DD]): initial draft.

---
<!--
HAND-OFF PROMPT (paste alongside the spec)

Read the spec in /specs/[slug].md carefully before writing any code.
Work in this order:
1. Restate the outcome in one sentence.
2. Review the "assumptions" list. Flag any assumption that looks wrong or risky and confirm it
   with me BEFORE building — this is the highest-leverage step.
3. List any remaining ambiguities or missing information.
4. PLAN GATE (build-required targets): enter plan mode (or your tool's equivalent), present an
   implementation plan for this phase, and get human approval BEFORE writing code. (A zero-distance
   target — a skill or declarative agent — has no separate build step: its artifact was emitted
   directly by the interviewer, so this hand-off prompt does not apply to it.)
5. Build ONLY the phase targeted by the accompanying build prompt (the items tagged for it).
   Treat higher-phase items as documented-but-not-yet: do not build them, but do not make
   architectural choices that block them. Within the target phase, write the implementation
   against the requirements section. Honour the "model & cost routing + determinism boundary"
   block: implement everything listed as deterministic in plain code (no LLM calls); reserve
   model calls for the judgment tasks named, at the model tier specified. Where that code exists,
   apply the block's type & value discipline (type hints + a static checker, plus immutability
   for constants).
6. Respect every "NEVER do unattended" bright line — pause for a human checkpoint there.
7. After implementation, verify each acceptance criterion one by one — by RUNNING it.
8. Do not mark the task complete until all acceptance criteria pass.

Do not add features outside "in scope".
Do not use packages outside "constraints" without flagging first.
If you make an architectural decision the spec didn't cover, append it to "decisions made",
and add a line to the changelog (bumping the spec version) if the spec itself changes.

REGENERATION TEST (your quality bar): could an agent rebuild this feature/agent from the spec
alone and produce behaviourally identical output? If not, you've found what's missing.
-->

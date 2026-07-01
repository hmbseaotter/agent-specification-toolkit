# Specification Interviewer

A guided, reasoning-driven interview that helps — and gently forces — you to supply every input needed
to produce your target **agent, feature, or skill**. It removes the failure mode the reference cards
warn about: deferring the hard questions until the code already exists. Its outputs are a **complete
specification** (the production-grade target) written to `specs/<slug>.md`, a reviewed **assumptions
list**, and then — depending on the target's **build class** — either a **build prompt scoped to the
build phase you choose** (a build-required target, handed to a *building agent* — the AI coding tool
that writes the code: Claude Code, Cursor, Aider, …) or the **emitted artifact** itself (`SKILL.md` /
`AGENT.md`) for a zero-distance target (a skill or declarative agent), which needs no separate build.

## Form factor: a Claude Code skill

Implemented as the **`/specify`** skill at
[`.claude/skills/specify/SKILL.md`](../.claude/skills/specify/SKILL.md). A reasoning-driven
interview was chosen over a static form because the hard part is *elicitation quality* — pushing
back on vague outcomes, catching "should" sneaking into requirements, asking smart follow-ups, and
handling your own questions and tangents — which a fixed questionnaire can't do. (It began as a
slash command and graduated to a skill once it grew the multi-step flow below.)

### Use it
From the repo root (the skill ships with the repo, so cloning is enough), start Claude Code:

```
claude
```

Then, at the Claude Code prompt, name what you're building:

```
/specify a background PR-triage agent
```

Name the target after `/specify`, or omit it and the interview asks what you're specifying. To make
it available in *every* project on a machine, use the opt-in installer described in the top-level
README — the project-local default (running it from this repo) needs no install at all.

## What it does, end to end

1. **Intake.** Asks whether you already have a PRD, a plan, design notes, or existing code. If so,
   it reads and **critically evaluates** them first — reusing what's solid, questioning what isn't,
   raising gaps and risks — and interviews only the leftovers. Inputs are considered, never treated
   as gospel.
2. **Interview.** One question at a time, welcoming your tangents and questions, with a visible
   progress ledger. It **holds the line** on weak answers (untestable outcomes, "should" in
   requirements, an empty out-of-scope list, untraced requirements) and, for agents, on the
   agent-specific bars below.
3. **Assemble + regeneration test.** Builds the complete spec and asks the quality question: could
   an agent rebuild this from the spec alone and produce behaviourally identical output? A
   deterministic linter (`scripts/lint_spec.py`) does the mechanical completeness checks — no tokens
   spent on what code can verify.
4. **Assumptions review gate.** Lists every assumption it made (each with the risk if it's wrong)
   and makes you confirm or correct them **before any build starts** — confirmed ones graduate into
   prior decisions.
5. **Compose-your-phase menu** (build-required targets). The spec is the whole production-grade
   target; this step *slices* it into build phases (it never shrinks the target). You choose how far
   this first push goes: architecturally-required **skeleton** items are pre-selected and overridable
   only with an explicit reason; optional items are multi-select, with dependency resolution so a
   phase can't be incoherent. (A zero-distance target — skill / declarative agent — skips phasing.)
6. **Build-readiness check.** A must-acknowledge guardrail that the session's **current model and
   effort** fit the chosen phase — flagging both *under-powered* (risking a poor build) and
   *over-powered* (wasting money). You explicitly proceed or adjust; the call is yours, on the
   record.
7. **Outputs, all under `specs/`.** The specification (`specs/<slug>.md`, which embeds the reviewed
   assumptions list) plus, depending on the target's **build class**, one of two things. For a
   **build-required** target: a phase-scoped **build prompt** (`specs/<slug>.build-prompt.md`) — the
   file you hand to a **building agent** (Claude Code, Cursor, Aider, …) to implement the chosen phase
   (build only that phase; don't make choices that block later ones), carrying a **plan-gate** so the
   building agent presents a plan for your approval before writing code. For a **zero-distance** target
   (skill / declarative agent): the interviewer **emits the artifact itself** (`SKILL.md` / `AGENT.md`)
   because building it is deterministic — no separate build step.

## Worked examples
See [`examples/`](../examples/) for two complete `/specify` outputs — a zero-distance **skill**
(`skill-csv-column-summariser/`: spec + the emitted `SKILL.md` + companion script) and a
build-required **agent** (`agent-pr-triage/`: spec + a plan-gated build prompt).

## What it elicits (the spec blocks)

The six core blocks — **outcome, scope (in/out), constraints, prior decisions, requirements (EARS — Easy Approach to Requirements Syntax),
acceptance criteria** — plus, when the target is an agent, the **agent dimensions**: control surface
(including a mandatory STOP condition), triggers & scheduling, tools & permissions (+ "never do
unattended" bright lines), state & memory, **model & cost routing + determinism boundary**, and
failure & escalation. See [`templates/specification-template.md`](../templates/specification-template.md)
for the full skeleton — the skill writes specs to match it. Metadata also carries a **role** (the
persona the target adopts) and a **build class** (zero-distance vs build-required) that drives which
blocks apply and what the final output is.

### The determinism boundary (the core cost discipline)
The interview forces you to name which operations are **plain code** (math, comparisons, parsing,
validation, lookups — zero tokens) versus which genuinely need **LLM judgment** (and at which model
tier). The AI is spent only where judgment is required; everything deterministic stays cheap. For that
deterministic code it also asks for **type & value discipline** — static typing (type hints + a
checker, so a float can't silently become an int) and immutability for constants — with "type-check
passes" as an acceptance criterion. The skill applies the same rule to itself — mechanical checks go
to the linter, not the model.

## Living specs

A spec is a starting point, not a monolith. It is version-controlled, carries a changelog, and the
skill supports two cheap update paths. **To use either, open the skill and say what you want:**

- **Amend** — when a build surprise changes the spec. Run `/specify` and name the spec and block,
  e.g. *"amend `specs/pr-triage-agent.md`, the constraints block — we're dropping the cron trigger."*
  The skill re-enters the interview on just that block, re-checks only the delta, bumps the version,
  and logs the change to the changelog — no re-answering everything.
- **Advance a phase** — when the current phase is built and you want the next. Run `/specify` and say
  e.g. *"advance `specs/pr-triage-agent.md` to the next phase."* The skill *deterministically
  re-slices* the same spec and emits the next phase's build prompt — no re-interview, no token spend
  on elicitation.

## Design principles it enforces
- **Gate, don't nag** — won't emit a finished spec until each block meets its bar.
- **Catch weak answers** — untestable outcomes, "should" in requirements, empty out-of-scope lists,
  requirements with no matching criterion; for agents, a missing stop condition or undefined bright
  lines.
- **One question at a time**, welcomes tangents, keeps a visible ledger.
- **Review before work** — assumptions are surfaced and signed off before any build.
- **Spend tokens only on judgment** — deterministic checks and re-slicing run as plain code.

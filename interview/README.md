# Specification Interviewer

A guided, reasoning-driven interview that helps — and gently forces — you to supply every input an
AI coding agent needs before it builds a target **agent or feature**. It removes the failure mode
the reference cards warn about: deferring the hard questions until the code already exists. Its
outputs are a **complete specification** (the production-grade target) written to `specs/<slug>.md`,
a reviewed **assumptions list**, and a **build prompt scoped to the build phase you choose**.

## Form factor: a Claude Code skill

Implemented as the **`/specify`** skill at
[`.claude/skills/specify/SKILL.md`](../.claude/skills/specify/SKILL.md). A reasoning-driven
interview was chosen over a static form because the hard part is *elicitation quality* — pushing
back on vague outcomes, catching "should" sneaking into requirements, asking smart follow-ups, and
handling your own questions and tangents — which a fixed questionnaire can't do. (It began as a
slash command and graduated to a skill once it grew the multi-step flow below.)

### Use it
From the repo root (the skill ships with the repo, so cloning is enough):

```
claude
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
5. **Compose-your-phase menu.** The spec is the whole production-grade target; this step *slices* it
   into build phases (it never shrinks the target). You choose how far this first push goes:
   architecturally-required **skeleton** items are pre-selected and overridable only with an explicit
   reason; optional items are multi-select, with dependency resolution so a phase can't be
   incoherent.
6. **Build-readiness check.** A must-acknowledge guardrail that the session's **current model and
   effort** fit the chosen phase — flagging both *under-powered* (risking a poor build) and
   *over-powered* (wasting money). You explicitly proceed or adjust; the call is yours, on the
   record.
7. **Three outputs.** The spec (`specs/<slug>.md`), the reviewed assumptions list, and a build
   prompt **scoped to the chosen phase** — build only this phase, and don't make choices that block
   later ones.

## What it elicits (the spec blocks)

The six core blocks — **outcome, scope (in/out), constraints, prior decisions, requirements (EARS),
acceptance criteria** — plus, when the target is an agent, the **agent dimensions**: control surface
(including a mandatory STOP condition), triggers & scheduling, tools & permissions (+ "never do
unattended" bright lines), state & memory, **model & cost routing + determinism boundary**, and
failure & escalation. See [`templates/specification-template.md`](../templates/specification-template.md)
for the full skeleton — the skill writes specs to match it.

### The determinism boundary (the core cost discipline)
The interview forces you to name which operations are **plain code** (math, comparisons, parsing,
validation, lookups — zero tokens) versus which genuinely need **LLM judgment** (and at which model
tier). The AI is spent only where judgment is required; everything deterministic stays cheap. The
skill applies the same rule to itself — mechanical checks go to the linter, not the model.

## Living specs

A spec is a starting point, not a monolith. It is version-controlled, carries a changelog, and the
skill supports two cheap update paths:
- **Amend** — when a build surprise changes the spec, re-enter the interview on just the affected
  block; it re-checks only the delta and logs the change to the changelog.
- **Advance a phase** — to build the next phase, the skill *deterministically re-slices* the same
  spec and emits the next build prompt. No re-interview, no elicitation spend.

## Design principles it enforces
- **Gate, don't nag** — won't emit a finished spec until each block meets its bar.
- **Catch weak answers** — untestable outcomes, "should" in requirements, empty out-of-scope lists,
  requirements with no matching criterion; for agents, a missing stop condition or undefined bright
  lines.
- **One question at a time**, welcomes tangents, keeps a visible ledger.
- **Review before work** — assumptions are surfaced and signed off before any build.
- **Spend tokens only on judgment** — deterministic checks and re-slicing run as plain code.

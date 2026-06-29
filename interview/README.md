# Specification Interviewer

A guided question-and-answer flow that helps — and gently forces — you to supply every input an
AI coding agent needs before it builds a target agent or feature. It removes the failure mode the
cards warn about: deferring the hard questions until the code already exists. The interview answers
them up front, in order, and won't "finish" while a required block is empty. Its output is a
completed specification written to `specs/<feature>.md`.

## Form factor: Claude Code slash command

Implemented as **`/specify`** — a custom slash command at
[`.claude/commands/specify.md`](../.claude/commands/specify.md). A reasoning-driven interview was
chosen over a static form because the hard part is *elicitation quality* — pushing back on vague
outcomes, catching "should" sneaking into requirements, asking smart follow-ups, and handling the
user's own questions and tangents — which a fixed questionnaire can't do.

### Use it
From the repo root (the command ships with the repo, so cloning is enough):

```
claude
/specify password reset flow
```

`$ARGUMENTS` (everything after `/specify`) seeds the target; omit it and the interview asks what
you're specifying. To make it available in *every* project, copy it to your personal commands:

```bash
mkdir -p ~/.claude/commands && cp .claude/commands/specify.md ~/.claude/commands/
```

## What it elicits (maps 1:1 to the six blocks)

1. **Outcome** — measurable; rejects untestable answers ("good UX").
2. **Scope** — in *and* out; forces at least one explicit out-of-scope item.
3. **Constraints** — stack, what not to touch, package rules.
4. **Prior decisions** — settled choices + the "why," as institutional memory.
5. **Requirements (EARS)** — all five patterns + the non-functional categories; every requirement
   uses `SHALL`.
6. **Acceptance criteria** — specific, machine-checkable, and traceable (each requirement → ≥1 check).

## Design principles it enforces
- **Gate, don't nag** — won't emit a finished specification until each block meets its minimum.
- **Catch weak answers** — untestable outcomes, "should" in requirements, empty out-of-scope lists,
  requirements with no matching criterion.
- **One question at a time**, welcomes tangents, keeps a visible progress ledger.
- **Regeneration test at the end** — could an agent rebuild this from the answers alone?

## If it outgrows a command
Slash commands are best kept short. If this workflow grows supporting files or branches, graduate
it to a Claude Code **skill** (a `SKILL.md` with the interview logic) — same content, better home.

# Specification Interviewer (planned)

**Goal.** A guided question-and-answer flow that helps — and forces — the user to supply every
input an AI agent needs before it builds a target agent or feature. It removes the failure mode
the cards warn about: deferring the hard questions until the code already exists. The interview
answers them up front, in order, and refuses to "finish" while a required block is empty.

The interviewer's output is a completed `specification-template.md`. The reference cards stay
the printable companion the user keeps open while answering.

## What it must elicit (maps 1:1 to the six blocks)

1. **Outcome** — what a user can newly do, stated measurably. Reject vague outcomes ("good UX").
2. **Scope** — in *and* out. Force at least one explicit out-of-scope item; that list is as
   load-bearing as the in-scope one.
3. **Constraints** — stack, what not to touch, package rules.
4. **Prior decisions** — settled choices + the "why", so the agent inherits institutional memory.
5. **Requirements (EARS)** — walk each of the five patterns (ubiquitous / WHEN / WHILE / IF /
   WHERE) plus the non-functional categories (security · performance · errors · observability ·
   accessibility · privacy). Every requirement must use `SHALL`.
6. **Acceptance criteria** — specific, machine-checkable, and traceable: each requirement must
   produce at least one criterion before the interview can complete.

## Design principles

- **Gate, don't nag.** A block is incomplete until its minimum is met; the flow won't emit a
  finished specification until all required blocks pass. (Mirror the card's "don't mark complete
  until all acceptance criteria pass.")
- **Catch the weak answer.** Flag untestable outcomes, "should" creeping into requirements,
  empty out-of-scope lists, and requirements with no matching criterion.
- **Apply the regeneration test at the end:** would an agent rebuild this from the answers alone
  and produce behaviourally identical output? Surface what's still missing.

## Open design question (decide before building)

Form factor — pick one:
- **Interactive HTML tool** — a self-contained page (same embedded-font, offline approach as the
  cards) that runs the Q&A in the browser and exports a filled `specification-template.md`.
- **Claude Code guided prompt** — a markdown "interview script" the agent runs to interview the
  user inside the CLI, writing the spec file as it goes.
- **CLI questionnaire** — a small Python script that prompts in the terminal and writes the file.

(Left open intentionally — see the toolkit conversation. Whichever is chosen, the elicitation
checklist above is the spec for the interviewer itself.)

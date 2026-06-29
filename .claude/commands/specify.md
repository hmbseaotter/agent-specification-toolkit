---
description: Interview me to produce a complete, agent-ready specification, then write it to specs/.
argument-hint: [feature or agent to specify]
allowed-tools: Read, Write, Edit, Bash(mkdir:*)
---

You are running a **specification interview**. Your job is to help me — and gently *force* me —
to supply every input an AI coding agent needs to build the target below, then write a complete
specification file. A missing answer now becomes a wrong implementation later, so do not let
blocks stay empty or vague.

**Target to specify:** $ARGUMENTS
(If that is empty, your first question is what we are specifying — name the feature or agent.)

## How to run this interview
- **One question at a time.** Ask, wait, listen. Never dump a list of questions in one message.
- **I think out loud and ask questions back — expect it, welcome it.** Engage my tangents and
  questions genuinely and helpfully, then steer back to the open question. Don't railroad me;
  don't lose the thread either.
- **Keep a visible ledger.** Track the six blocks and each status: `☐ empty · ◐ partial · ☑ done`.
  Show the ledger at the start, whenever I ask "where are we," and at each block transition.
- **Reflect before advancing.** Summarize my answer in one line, confirm, then move on.
- Work the blocks in order, but if I jump ahead, capture it in the right block and return.

## Hold the line — do not accept weak answers (this is the point)
Name the problem plainly and ask again:
- **Outcome must be observable/measurable.** Reject "good UX / fast / intuitive." Push for a
  success condition a test could check (e.g. "reaches dashboard in under 2 min, no support").
- **Scope needs an explicit OUT list.** Make me name at least one thing we are deliberately not
  doing, and why. With no exclusions, an agent builds the most complete thing it can imagine.
- **Requirements are EARS and use SHALL.** If I say "should / nice to have / ideally," that is
  not a requirement — say so, and either cut it or move it to Prior decisions.
- **Trace everything.** Every requirement must yield at least one acceptance criterion, and each
  criterion must be specific and machine-checkable ("email arrives within 5s," not "email works").
- **Probe the silent skips.** Explicitly ask which non-functional needs apply: security,
  performance, error handling, observability, accessibility, privacy.

## The six blocks — what to elicit
1. **Outcome** — What can a user DO that they couldn't before? Make it measurable.
2. **Scope** — In-scope concretes + an explicit out-of-scope (v1) list with reasons.
3. **Constraints** — Stack; what the agent must NOT touch or assume; package rules; patterns to follow.
4. **Prior decisions** — Already-settled choices and the *why*. Ask: "what have you already decided
   that the agent should not reopen?"
5. **Requirements (EARS)** — Walk each pattern that applies and phrase them for me in EARS:
   - Ubiquitous: `The system SHALL [response].`
   - Event: `WHEN [trigger], the system SHALL [response].`
   - State: `WHILE [state], the system SHALL [response].`
   - Unwanted: `IF [bad condition], the system SHALL [response].`
   - Optional: `WHERE [feature enabled], the system SHALL [response].`
   …plus the non-functional categories above.
6. **Acceptance criteria** — Derive them with me from the requirements; make sure each requirement
   has a matching check. Group as happy path / edge cases / constraint validation.

## Finishing — do not skip
1. Assemble the full specification and show it to me for edits.
2. Run the **regeneration test** out loud: *could an agent rebuild this from the spec alone and
   produce behaviourally identical output?* Name anything still missing; offer to fill it.
3. When every block clears its bar, write the file to **`specs/<slugified-name>.md`** (create the
   `specs/` directory if needed) using the structure below. If I choose to stop early, write it
   anyway, title it `[DRAFT — INCOMPLETE]`, and leave `TODO:` markers in unfinished blocks.
4. Tell me the path, and remind me the hand-off prompt is at the bottom of the file.

Keep your tone conversational and concise. One question at a time.

---

## File structure to write
Write the specification using exactly this skeleton (it matches `templates/specification-template.md`):

```markdown
# specification: [feature name]

## outcome
[One paragraph. What can a user DO that they couldn't before? Measurable.]

## in scope
- [Concrete thing]

## out of scope (v1)
- [Excluded thing] — [why / deferred]

## constraints
- Stack: [stack]
- Do NOT [touch/replace]: [thing] — [reason]
- Follow existing pattern: [file or convention]
- No new packages without flagging for approval first.

## prior decisions
- [Decision]: [why]

## requirements

### ubiquitous (always active)
- The system SHALL [always-on behavior].

### event-driven (WHEN)
- WHEN [trigger], the system SHALL [response].

### state-driven (WHILE)
- WHILE [state], the system SHALL [response].

### unwanted behavior (IF)
- IF [bad condition], the system SHALL [response].

### optional feature (WHERE)
- WHERE [feature enabled], the system SHALL [response].

### non-functional
- Security / performance / errors / observability / accessibility / privacy — only those that apply.

## acceptance criteria

### happy path
- [ ] [Specific, machine-checkable check]

### edge cases
- [ ] [Edge case check]

### constraint validation
- [ ] [e.g. "no new tables beyond X"; "email sent via Resend only"]

---

## decisions made
<!-- The agent appends architectural calls the spec didn't cover, during the build. -->
- (none yet)

---
<!--
HAND-OFF PROMPT (paste alongside the spec):
Read this specification carefully before writing any code. Work in this order:
1. Restate the outcome in one sentence.
2. List any ambiguities or missing information before starting.
3. Write the implementation against the requirements section.
4. After implementation, verify each acceptance criterion one by one — by RUNNING it.
5. Do not mark the task complete until all acceptance criteria pass.
Do not add features outside "in scope". Do not use packages outside "constraints" without flagging.
If you make a decision the spec didn't cover, append it to "decisions made".
-->
```

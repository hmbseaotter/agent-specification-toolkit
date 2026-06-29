# specification: [feature name]

<!--
HOW TO USE
1. One spec = one feature. Save as /specs/[feature].md.
2. Fill every block top to bottom. Delete the guidance comments as you go.
3. Hand off with the prompt at the very bottom of this file.
Keyword convention (RFC 2119 / 8174): SHALL = MUST = absolute, verifiable requirement.
We use SHALL for every requirement on purpose. If a line is only a "should," it is not a
requirement — cut it, or move it to "prior decisions."
-->

## outcome
<!-- One paragraph. What can a user DO that they couldn't before? Make it measurable. -->
[e.g. A user who has forgotten their password reaches their dashboard in under 2 minutes,
via email, with no manual support intervention.]

## in scope
- [Concrete thing the agent SHOULD build]
- [Concrete thing]

## out of scope (v1)
<!-- As load-bearing as "in scope." With no exclusions, the agent builds the most complete
version it can imagine. Name what you are deliberately NOT doing, and why. -->
- [Excluded thing] — [why / deferred to when]
- [Excluded thing]

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
All five patterns below. Every requirement must trace to >=1 acceptance criterion. -->

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

## acceptance criteria
<!-- The pass/fail gate. Each item SPECIFIC and machine-checkable (a test or CI run, not
the agent's say-so). Don't mark the task complete until every box passes — by test, not vibe. -->

### happy path
- [ ] [Testable pass/fail check, e.g. "valid email -> reset email arrives within 5s"]
- [ ] [Testable check]

### edge cases
- [ ] [Edge case check]
- [ ] [Edge case check]

### constraint validation
- [ ] [e.g. "no new tables beyond X"]
- [ ] [e.g. "email sent via Resend, not another provider"]

---

## decisions made   <!-- OUTPUT: the AGENT appends here DURING the build -->
<!-- Any architectural call the spec didn't cover goes here. Fold these back into
"prior decisions" before the next session, or the codebase drifts from its source of truth. -->
- [agent fills in]

---
<!--
HAND-OFF PROMPT (paste alongside the spec)

Read the spec in /specs/[feature].md carefully before writing any code.
Work in this order:
1. Restate the outcome in one sentence.
2. List any ambiguities or missing information before starting.   <- highest-leverage step
3. Write the implementation against the requirements section.
4. After implementation, verify each acceptance criterion one by one — by RUNNING it.
5. Do not mark the task complete until all acceptance criteria pass.

Do not add features outside "in scope".
Do not use packages outside "constraints" without flagging first.
If you make an architectural decision the spec didn't cover, append it to "decisions made".

REGENERATION TEST (your quality bar): could an agent rebuild this feature from the spec
alone and produce behaviourally identical output? If not, you've found what's missing.
-->

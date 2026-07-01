# Build prompt — pr-triage-agent · PHASE 1 (skeleton)

Read `specification.md` in full before writing any code. This prompt targets **Phase 1 only**.
You are the **building agent**; the target is the pr-triage agent described in the spec.

## 0. Plan gate (do this FIRST)
Enter plan mode (or your tool's equivalent): present an implementation plan for Phase 1 and get
human approval BEFORE writing any code.

## 1. Build ONLY Phase 1 — the [P1] items
- Parse the `pull_request` webhook payload.
- Map changed file paths -> area labels via a config table (deterministic).
- Apply the labels via the GitHub API.
- Dry-run toggle (env var): log intended actions, make no write calls.

Higher-phase items are **documented-but-not-yet** — do NOT build them, and do not make architectural
choices that block them:
- [P2] the LLM summary comment + budget cap.
- [P3] the SHA dedupe ledger, retries/backoff, maintainer alert.

## 2. Determinism boundary + type discipline
- Payload parsing and path->label mapping are **plain code, no LLM**.
- Type-hint the mapping code; the label set is a `Final` constant; **mypy must pass**.

## 3. Bright lines (never do unattended)
- NEVER call merge / approve / close / delete endpoints.
- Write API calls (adding labels) only when NOT in dry-run mode.
- `GITHUB_TOKEN` from env / secret store — never hard-coded.

## 4. Acceptance criteria — verify by RUNNING them
- [ ] A new PR touching `src/api/**` gets `area:api` within 2 minutes.
- [ ] In dry-run mode, no write API calls are made (logs only).
- [ ] `mypy` passes on the mapping module.
- [ ] No merge/approve/close/delete calls (assert in tests).
Do not mark complete until all pass. Append any architectural calls to **decisions made**; if the
spec itself changes, add a changelog line and bump the version.

## 5. Recommended build-time model/effort (from build-readiness)
Phase 1 is mostly mechanical wiring + a deterministic mapping — a **mid-tier model at moderate
effort** is sufficient; the top model at max effort would be over-powered (wasted spend). Confirm or
adjust `/model` + effort before building.

---
*Advancing later is cheap: re-run `/specify` in advance-phase mode to emit the Phase 2 build prompt —
no re-interview.*

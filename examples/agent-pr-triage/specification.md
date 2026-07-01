# specification: pr-triage-agent

## metadata
- Spec version: 0.1.0
- Status: READY-FOR-BUILD
- Last updated: 2026-07-01
- Author(s): example (Agent Specification Toolkit)
- Target type: coded agent
- Build class: build-required
- Role: a diligent maintainer's assistant that triages incoming pull requests

## outcome
Within ~2 minutes of a PR opening it carries accurate area labels and a concise summary comment, so
a reviewer can pick it up without first reading the whole diff — measurably cutting time-to-first-review.

## in scope
- [P1] Apply area labels to a new PR based on the paths it changes.
- [P2] Post one summary comment describing what the PR does (LLM).
- [P3] Deduplicate: never label/comment the same PR head SHA twice; retry transient API errors.

## out of scope (v1)
- Merging or approving PRs — human-only; the agent never merges.
- Editing PR code or line-level review comments.
- Cross-repo triage — one repo per deployment.

## control surface
- Runtime: background worker triggered per PR event.
- Invoked by: GitHub webhook (pull_request opened / synchronize).
- Human control mid-run: a dry-run mode (log intended actions, take none) toggled by env var.
- Stopped by: completion (one PR processed per event); at most one action-set per head SHA; global
  kill by disabling the webhook.
- Human-in-the-loop: none needed for labels/comment (non-destructive); merges/approvals are out of
  scope entirely, so there is nothing destructive to checkpoint.

## triggers & scheduling
- Starts on: GitHub webhook pull_request (opened, synchronize).
- Cadence: event-driven; no cron.
- Concurrency: one event at a time per PR; a per-SHA lock prevents double-processing.

## tools & permissions
- Allowed: GitHub REST API (read PR files, add labels, post an issue comment); read a path->label config.
- Secrets: GITHUB_TOKEN from env / secret manager — never hard-coded.
- NEVER do unattended: merge, approve, close, push, or delete — each is out of scope and gated.
  Posting a comment (a "send") happens only when NOT in dry-run mode.

## state & memory
- Persists a small ledger of processed PR head SHAs (to dedupe) — file or KV store.
- Reset: ledger entries expire after 30 days.

## model & cost routing + determinism boundary
- Deterministic (plain code, NO LLM): parse the webhook payload; map changed file paths -> area
  labels via a config table; dedupe check against the SHA ledger.
- Type & value discipline: type-hint the mapping + ledger code; the label set is a `Final` constant;
  counts are `int`. "mypy passes" is an acceptance criterion.
- Requires judgment (LLM): the one-paragraph PR summary comment. Model tier: a small model (Haiku) —
  high volume, low stakes.
- Cost guardrail: at most 1 LLM call per head SHA; an hourly budget cap; on cap -> still label, skip
  the summary.
- Stop / escalate: repeated API failure -> stop + log; label mapping is deterministic (no ambiguity).

## constraints
- Stack: Python; GitHub REST via a typed client; deployed as a webhook handler.
- Do NOT introduce a merge/approve capability — keep the agent non-destructive by construction.

## prior decisions
- Labels are config-driven (path->label), not LLM-guessed: deterministic, auditable, cheap.
- Dedupe by head SHA: re-runs on synchronize won't spam the PR.

## requirements
### ubiquitous (always active)
- The system SHALL process at most one action-set (labels + optional comment) per PR head SHA.

### event-driven (WHEN — triggered by an action)
- WHEN [P1] a pull_request opened event arrives, the system SHALL apply area labels derived from the
  changed paths within 2 minutes.
- WHEN [P2] labelling completes and the head SHA is new, the system SHALL post one summary comment.

### state-driven (WHILE — true for the duration of a state)
- WHILE in dry-run mode, the system SHALL log intended labels/comment and make no write API calls.

### unwanted behavior (IF — error handling)
- IF [P3] the GitHub API returns an error, the system SHALL retry with backoff up to 3 times, then
  stop and log.
- IF [P3] the head SHA is already in the ledger, the system SHALL skip and make no changes.

### optional feature (WHERE — behind a flag)
- WHERE the hourly LLM budget is exhausted, the system SHALL still label but skip the summary comment.

### non-functional
- Security: GITHUB_TOKEN from a secret store; least-privilege scopes (PR read + issues write only).
- Performance: label within 2 minutes of the event.
- Observability: log every action (or intended action, in dry-run) with the PR number + head SHA.

## failure & escalation
- Recoverable error: transient API errors -> retry with backoff (max 3).
- Unrecoverable error: auth failure -> stop, log, alert the maintainer channel.
- Stuck / uncertain: n/a for labels (deterministic); if the LLM summary fails, skip it and still label.
- Escalation channel: log + a maintainer notification (e.g. a Slack webhook) on hard failure.

## acceptance criteria
### happy path
- [ ] [P1] A new PR touching `src/api/**` receives the `area:api` label within 2 minutes.
- [ ] [P2] A new PR receives exactly one summary comment describing its changes.

### edge cases
- [ ] [P3] Re-processing the same head SHA makes no new labels/comments (dedupe).
- [ ] [P3] A transient 500 from GitHub is retried up to 3 times before stopping.
- [ ] WHILE in dry-run mode, no write API calls are made (logs only).

### constraint validation
- [ ] The agent never calls merge/approve/close/delete endpoints — asserted in tests.
- [ ] `mypy` passes on the label-mapping and ledger modules.
- [ ] GITHUB_TOKEN is read from env/secret store, never hard-coded.

## implementation phases
### phase 1 — skeleton / walking slice
- Goal: label a new PR by changed paths, end to end.
- Includes (required): webhook parse, path->label mapping, apply labels, dry-run toggle.
- Done when: the [P1] happy-path criterion passes.

### phase 2 — LLM summary
- Goal: add the one-paragraph summary comment.
- Includes: [P2] comment, hourly budget cap, small-model routing.

### phase 3 — robustness
- Goal: dedupe + retries + escalation.
- Includes: [P3] SHA ledger, backoff, maintainer alert.

## assumptions
- [ ] A path->label config exists or will be authored — risk if wrong: labels are inaccurate.
- [ ] Webhook infra (endpoint + secret) is available — risk if wrong: no triggers fire.
- [ ] A small model is adequate for summaries — risk if wrong: low-quality comments.

## changelog
- 0.1.0 (2026-07-01): initial example, produced by `/specify` (build-required agent).

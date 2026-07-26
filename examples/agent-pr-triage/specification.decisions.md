# pr-triage-agent — Decision Record

A worked example of the decision-record companion (`templates/decision-record-template.md`). It records
every FORK the interview hit: the options considered, the choice, and why.

The spec's `prior decisions` block carries the compact what-and-why a building agent needs. **This file
carries the options that LOST** — which the spec alone never shows, and which is what a reader six months
later actually wants when asking "was X considered?"

- **Project:** pr-triage-agent
- **Identity:** a background worker that labels and summarises incoming pull requests
- **Spec:** [`specification.md`](specification.md)
- **Status:** finalized alongside the spec (this is an illustrative example, not a live deployment)
- **Legend:** ✅ decided · 🔶 open / revisit · ⏭️ deferred to a later phase

---

## D0 — How are area labels chosen?

**Fork:** Should labels be derived mechanically from changed paths, or inferred by the model?

**Options considered**
- **(A) LLM classification** — send the diff or file list to a model and let it pick labels. Handles
  novel directory layouts with no configuration, but every label becomes non-deterministic, unauditable
  ("why did it pick `area:api`?"), and costs a model call on every event.
- **(B) Config-driven path→label table** — a checked-in mapping from path globs to labels. Needs authoring
  and maintenance as the tree changes, and silently mislabels paths nobody added.

**Decision ✅** — **(B), a config-driven table.**

**Why** — labelling is a **lookup, not a judgment**: the answer is fully determined by the changed paths,
so spending a model call on it buys nothing and costs determinism. A maintainer can read the table and
predict the outcome, and a wrong label is fixed by editing one line rather than by prompt-tuning.

**Consequences / caveats** — the mapping is now a maintained artifact: a new top-level directory gets no
labels until someone adds it. That failure is silent, which is why the assumptions block flags "a
path→label config exists or will be authored".

---

## D1 — What is the deduplication key?

**Fork:** A PR receives `opened` and then `synchronize` events. What prevents repeated labelling and
comment spam?

**Options considered**
- **(A) No dedupe** — act on every event. Simplest, and re-labelling is harmless, but every push produces
  another summary comment. Unusable in practice.
- **(B) Dedupe by PR number** — act once per PR, ever. No spam, but a PR that changes substantially after
  review never gets an updated summary.
- **(C) Dedupe by head SHA** — act once per distinct head commit.

**Decision ✅** — **(C), dedupe by head SHA.**

**Why** — it distinguishes "the same PR again" from "the PR actually changed". A force-push or new commit
is genuinely new content and deserves a fresh look; a webhook redelivery of the same SHA does not. PR
number cannot tell those apart.

**Consequences / caveats** — requires persistent state (the SHA ledger), which is the agent's only
statefulness. That state needs an expiry policy, hence the 30-day window, and its timestamps need a
declared standard (UTC `Z`) so the window means the same thing everywhere.

---

## D2 — How is the agent kept non-destructive?

**Fork:** Merge, approve, and close are the operations a triage agent must never perform unattended. Gate
them, or exclude them?

**Options considered**
- **(A) Permission-gated** — implement them behind human-approval checkpoints. Maximum future capability;
  the destructive code path exists and one bad refactor or prompt-injection away from firing.
- **(B) Excluded by construction** — never implement the capability, and assert its absence in tests.

**Decision ✅** — **(B), excluded by construction**, recorded in constraints as "do NOT introduce a
merge/approve capability".

**Why** — **a capability that does not exist cannot be misused.** For a non-destructive-by-design agent,
excluding the operation is strictly safer than guarding it, and it converts a policy ("always ask first")
into a testable property ("never calls these endpoints"), which appears as a constraint-validation
criterion.

**Consequences / caveats** — auto-merge can never be added incrementally; it would be a deliberate
re-scoping with its own checkpoint design. That is the intended trade.

---

## D3 — Which model tier writes the summary comment?

**Fork:** The one-paragraph PR summary is genuine judgment. What tier should write it?

**Options considered**
- **(A) A frontier model** — best prose and diff comprehension, at the highest per-event cost for a
  comment nobody is contractually relying on.
- **(B) A small/cheap model (Haiku)** — adequate summaries at high volume.

**Decision ✅** — **(B), a small model.**

**Why** — high volume, low stakes. The summary is a **convenience that shortens time-to-first-review**,
not an artifact anyone acts on blindly; a reviewer still reads the diff. Paying frontier prices per PR to
slightly improve a courtesy comment is the wrong trade.

**Consequences / caveats** — summary quality is explicitly an accepted risk, and the assumptions block
records "a small model is adequate for summaries" so it can be revisited on evidence rather than by
vibe.

---

## D4 — What happens when the LLM budget is exhausted?

**Fork:** The hourly cap is reached mid-day. What does the agent do with the next PR?

**Options considered**
- **(A) Skip the whole run** — no labels, no comment. Simple and uniform, but discards the *deterministic,
  free, most valuable* half of the work for a budget that only constrains the model call.
- **(B) Queue until budget resets** — nothing is lost, at the cost of a queue, ordering concerns, and
  labels arriving far outside the two-minute target.
- **(C) Degrade — label anyway, skip the summary.**

**Decision ✅** — **(C), degrade gracefully.**

**Why** — the two halves have **different costs and different value**. Labelling is deterministic, free,
and drives reviewer routing; the summary is optional polish. A budget that constrains only the model call
has no business suppressing the part that costs nothing.

**Consequences / caveats** — output becomes non-uniform: some PRs carry a summary and some do not, and a
reader cannot tell "no summary" from "budget exhausted" without the logs. Acceptable, and the reason every
action is logged with PR number and head SHA.

---

## D5 — How does a human safely observe the agent before trusting it?

**Fork:** Posting a comment is a "send" — content published on the agent's behalf. Does it need an
approval checkpoint?

**Options considered**
- **(A) Approve-before-post checkpoint** — a human confirms each comment. Safe, but it makes an
  event-driven background worker synchronous on a human, defeating the two-minute goal.
- **(B) Dry-run mode** — an env-var toggle that logs every intended action and makes no write calls.

**Decision ✅** — **(B), dry-run mode**, with no per-comment checkpoint.

**Why** — the checkpoint rule exists to guard **irreversible or destructive** actions. A PR comment is
neither: it is visible, attributable, and deletable, and the destructive operations are excluded outright
(D2). What the maintainer actually needs is not per-event consent but **confidence before rollout**, which
a dry-run delivers once rather than forever.

**Consequences / caveats** — dry-run must be genuinely total: WHILE in dry-run the agent makes *no* write
API calls, asserted as its own acceptance criterion. A partially-honoured dry-run would be worse than
none, because it would be trusted.

---

## Document status

Decisions **D0–D5** recorded; none open. Spec at [`specification.md`](specification.md), phase-1 build
prompt at [`build-prompt.md`](build-prompt.md).

Any new fork encountered during the build is to be appended here in the same shape — fork, options
considered, decision, why — so this record does not go stale.

# [target name] — Decision Record

<!--
WHAT THIS IS
A running record of every FORK the specification interview hit: the options considered, the choice
made, and WHY. The spec's `prior decisions` block records the compact what-and-why a building agent
needs; THIS file records the reasoning a human needs later, when asking "was X considered, and why
did it lose?" Losing the rejected alternatives is silent and permanent — the spec alone never shows
them.

HOW TO USE
1. Save as `specs/<slug>.decisions.md`, beside the spec. A repo-root `DECISIONS.md` is fine when the
   repo holds a single spec.
2. Append an entry the MOMENT a fork is resolved, during the interview — not reconstructed at the
   end.
3. Number entries D0, D1, D2 … and never renumber: the spec, commit messages, and later entries
   reference them by number. Supersede rather than rewrite.
4. Only genuine forks earn an entry. An answered question with no real alternative is not a
   decision — do not pad this file.
5. The BUILD appends here too: any fork the building agent resolves that the spec did not cover gets
   an entry, in the same shape.
-->

- **Project:** [name]
- **Identity:** [one-line description of the target]
- **Spec:** [path to specs/<slug>.md]
- **Status:** [decisions accrue during the interview; finalized alongside the spec]
- **Legend:** ✅ decided · 🔶 open / revisit · ⏭️ deferred to a later phase

---

## D0 — [short title of the fork]

**Fork:** [the question that had to be answered — phrase it as a question]

**Options considered**
- **(A) [option]** — [what it buys, what it costs]
- **(B) [option]** — [what it buys, what it costs]

**Decision ✅** — **[which option, stated plainly]**

**Why** — [the reasoning that actually decided it. If one consideration dominated, say which and
why it outweighed the others. This is the field that earns the file.]

**Consequences / caveats** — [what this forces elsewhere, what it rules out, what now needs
documenting or watching. Omit only if there genuinely are none.]

---

## D1 — [next fork]

<!-- Same shape. Add a "Status" line for anything provisional, and mark it 🔶 until confirmed, so an
unresolved decision is never mistaken for a settled one. -->

---

## Document status

Decisions **D0–D[n]** recorded. [Note here anything still open, and where the spec/build prompt live.]

Any new fork encountered during the build is to be appended in the same shape — fork, options
considered, decision, why — so this record does not go stale.

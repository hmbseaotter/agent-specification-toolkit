# specification: csv-column-summariser skill

## metadata
- Spec version: 0.1.0
- Status: READY-FOR-BUILD
- Last updated: 2026-07-01
- Author(s): example (Agent Specification Toolkit)
- Target type: skill
- Build class: zero-distance
- Role: an expert data-profiling assistant that summarises the columns of a CSV file

## outcome
A user points the skill at a local CSV and, in under ~10 seconds, gets a per-column profile —
inferred type, fill rate, distinct-value count, numeric min/max/mean, and a few sample values —
plus a one-line plain-English guess of what each column represents, without opening a spreadsheet.

## in scope
- Read one local CSV file given its path.
- Compute a deterministic per-column profile (type, fill rate, cardinality, numeric summary,
  sample values) via a companion script.
- Add a one-line plain-English interpretation of each column (LLM judgment).
- Print a compact Markdown table plus the per-column notes.

## out of scope (v1)
- Charts / visualisations — text output only; keeps the skill dependency-free.
- Remote or URL CSVs — local files only for v1; avoids network + auth scope.
- Writing back to or modifying the CSV — read-only by design.
- Multi-file / directory profiling — one file per run; a single meaningful unit.

## control surface
n/a (not an agent) — a skill runs to completion on one invocation; it does not loop or run unattended.

## triggers & scheduling
n/a (not an agent) — invoked on demand when the user names a CSV path.

## tools & permissions
- Allowed: filesystem READ of the one CSV path the user provides; run the companion profiling script.
- NEVER: write, move, or delete any file; no network access. Read-only — nothing needs a human
  checkpoint because it never mutates anything.

## state & memory
n/a (not an agent) — stateless; each run profiles the given file with no persistence between runs.

## model & cost routing + determinism boundary
- Deterministic (plain code, NO LLM — companion script `csv_profile.py`): parse the CSV; per column
  infer dtype (int / float / empty / string), fill rate (non-null %), cardinality (distinct count),
  numeric min / max / mean, and up to 3 sample values.
- Type & value discipline (the script): type-hint it; the numeric mean is a `float` and counts are
  `int` — a static checker (mypy) guards against a float mean silently becoming an int; the sample
  limit is a `Final` constant. "mypy passes" is an acceptance criterion.
- Requires judgment (LLM): the one-line plain-English interpretation of what each column probably
  represents (e.g. "looks like a customer identifier"). Model tier: a small/cheap model (e.g. Haiku).
- Cost guardrail: the LLM sees only the deterministic profile (names + stats + samples), never the
  raw rows — bounded token cost regardless of row count.

## constraints
- Stack: a Claude Code skill (`SKILL.md`) + a stdlib-only Python companion script (`csv` module; no
  pandas) so it runs anywhere with no pip install.
- Do NOT add third-party data libraries (pandas / polars) — stdlib `csv` is sufficient and minimal.

## prior decisions
- Stdlib `csv` over pandas: zero-install footprint, matches the toolkit's own ethos.
- LLM sees only the profile, not raw rows: bounds cost and avoids leaking large/sensitive data.

## requirements
### ubiquitous (always active)
- The system SHALL, for each column, report inferred type, fill rate, and distinct-value count.

### event-driven (WHEN — triggered by an action)
- WHEN the user supplies a valid CSV path, the system SHALL run the companion script and print a
  per-column Markdown table.
- WHEN a column is numeric, the system SHALL include min, max, and mean, with the mean as a float.

### unwanted behavior (IF — error handling)
- IF the path is missing or not a readable CSV, the system SHALL report the error and stop, with no
  partial output.
- IF a column is entirely empty, the system SHALL report it as empty (0% fill) rather than guessing
  a type.

### optional feature (WHERE — behind a flag)
- WHERE the user requests it, the system SHALL add a one-line plain-English interpretation per column.

### non-functional
- Performance: profile up to 100k rows in ~10s on a laptop.
- Privacy: never send raw rows to the LLM — only the computed profile.
- Error handling: a malformed row is skipped and the count of skipped rows is available.

## failure & escalation
n/a (not an agent) — on unrecoverable input error the skill stops and reports; there is no
autonomous retry loop or human-escalation channel to define.

## acceptance criteria
### happy path
- [ ] Given a sample CSV, output lists every column with type, fill rate, and cardinality.
- [ ] A numeric column's summary includes min, max, and a mean rendered as a float (e.g. 3.5, not 3).
- [ ] With interpretation enabled, each column has a one-line plain-English note.

### edge cases
- [ ] A missing/unreadable path produces an error message and no partial table.
- [ ] An all-empty column is reported at 0% fill and not assigned a numeric type.

### constraint validation
- [ ] The companion script imports only the Python standard library (no pandas/polars).
- [ ] `mypy csv_profile.py` passes (type discipline: mean stays float, counts stay int).
- [ ] The skill performs no file writes and makes no network calls.

## implementation phases
n/a — zero-distance target (a skill); the artifact is emitted directly, no phased build.

## assumptions
- [ ] CSVs are UTF-8 with a header row — risk if wrong: dtype inference and column names are off.
- [ ] "~10s for 100k rows" is acceptable performance — risk if wrong: needs streaming/optimisation.
- [ ] A small model tier is fine for column interpretation — risk if wrong: low-quality notes.

## changelog
- 0.1.0 (2026-07-01): initial example, produced by `/specify` (zero-distance skill).

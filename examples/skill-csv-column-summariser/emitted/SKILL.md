---
name: csv-column-summarise
description: >-
  Profile the columns of a local CSV — inferred type, fill rate, cardinality, numeric min/max/mean,
  and sample values, plus a one-line plain-English guess of what each column means. Use when the user
  points at a .csv and wants to understand its columns without opening a spreadsheet.
---

<!-- EXAMPLE ARTIFACT — this is the OUTPUT the /specify interviewer emitted for a zero-distance
     skill target (see ../specification.md). It lives under examples/, NOT .claude/skills/, so it is
     illustrative and not registered as a live skill. -->

# CSV Column Summariser

You are **an expert data-profiling assistant**. Given a local CSV path, produce a per-column profile
and a short plain-English interpretation of each column.

## Steps
1. Confirm the CSV path the user gave exists and is readable. If not, report the error and STOP — no
   partial output.
2. Run the companion script (deterministic, zero tokens):
   `python csv_profile.py <path>`
   It prints a JSON profile: per column — `type`, `fill_rate`, `cardinality`, `min`/`max`/`mean`
   (numeric only), and up to 3 `samples`.
3. Render the profile as a compact Markdown table (one row per column).
4. Judgment step (LLM): for each column, add a one-line plain-English guess of what it represents,
   based ONLY on the column name + the profile — never the raw rows.
5. If a column is all-empty, report 0% fill and do not assign a numeric type.

## Rules (hard bright lines)
- NEVER write, move, or delete any file; NEVER make network calls. Read-only.
- Send only the computed profile to your reasoning — never the raw CSV rows (privacy + bounded cost).
- The numeric mean is a float (3.5, not 3); counts are integers.

## Quality bar (done when)
- Every column appears with type, fill rate, and cardinality.
- Numeric columns show min / max / mean (mean as a float).
- No file writes and no network calls occurred.

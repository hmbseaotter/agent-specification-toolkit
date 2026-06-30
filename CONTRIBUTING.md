# Contributing

Thanks for your interest in the Agent Specification Toolkit. It's a small, focused toolkit, so
contributions are welcome under one bar: keep it simple, cross-platform, and self-consistent.

## Ways to contribute
- **Open an issue** for a bug, an unclear doc, or a proposed addition — ideally before a large PR,
  so we can agree on scope first.
- **Send a PR** for fixes, doc improvements, new reference-card content, or skill/linter changes.

## Setup
Most of the toolkit is **standard-library Python — nothing to install**: the `/specify` skill,
`scripts/lint_spec.py`, and `install.py` / `uninstall.py` all run as-is.

> **Command note:** commands here use the **Windows** form `python` / `pip`. On **macOS / Linux**
> use `python3` / `pip3`. Forward slashes in paths work on all three OSes.

The only dependency is for **re-rendering the reference cards** (HTML → PDF):

```
pip install -r requirements.txt
python -m playwright install chromium
```

## Project conventions (please follow)
- **"specification", not "spec"** in repo/dir/file names and headings ("spec" is fine as prose
  shorthand where context disambiguates).
- **Reference cards:** the `.html` is the source of truth; the `.pdf` is generated. Never hand-edit
  a PDF — change the HTML and regenerate with `python scripts/regenerate.py`. Cards stay
  **US Letter, exactly 2 pages**, portrait.
- **Anything that is itself a specification** (examples, tests) uses **EARS** — Easy Approach to
  Requirements Syntax, a small set of fixed sentence templates (`WHEN … SHALL`, `IF … SHALL`,
  `WHILE … SHALL`, etc.) that make each requirement testable — with `SHALL` for requirements and
  traceable, machine-checkable acceptance criteria. No "should" in a requirements block. Run
  `python scripts/lint_spec.py <file>` and fix what it flags.
- **Cross-platform + minimal footprint:** keep the skill, linter, and installer
  **standard-library only** and working on Windows / macOS / Linux. The installer must never write
  outside `~/.claude/skills/specify/` or touch user settings or hooks.
- **Repo hygiene:** don't commit tool/editor/OS junk (it's gitignored for a reason); line endings
  are LF (see `.gitattributes`).

## Pull requests
- Keep changes **focused** — one concern per PR; separate unrelated changes.
- Write clear commit messages (subject + a short body explaining *why*).
- **Update the docs you touch:** `README.md`, `interview/README.md`, and `CLAUDE.md` (which records
  the toolkit's design decisions).
- If you change the spec template's structure, update `scripts/lint_spec.py` and the `/specify`
  skill to match.

## Context
`CLAUDE.md` is the repo's design memory — the decisions already made, and why. Skim it before a
larger change so you don't relitigate a settled choice (though do flag one that looks broken).

## License
By contributing, you agree your contributions are licensed under the repo's [MIT License](LICENSE).

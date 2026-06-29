# CLAUDE.md — context for continuing this toolkit

This repo is the **Agent Specification Toolkit**: tooling for writing software specifications an
AI coding agent can execute. Treat this file as the repo's own "prior decisions" — don't
relitigate them, but flag any that look broken. Append new structural choices under
"Decisions made."

## Components & where things live
- `reference-cards/*.html` — source of truth for each printable card. The matching `*.pdf` is a
  generated artifact; never hand-edit a PDF, regenerate it from its HTML.
- `templates/specification-template.md` — the working skeleton end users copy per feature.
- `interview/` — the planned Specification Interviewer. `interview/README.md` is its spec.
- `scripts/regenerate.py` — renders every `reference-cards/*.html` to a sibling PDF.

## Build / render decisions (already made)
- Cards are **US Letter, exactly 2 pages**, portrait. Keep to 2 pages.
- Fonts: **JetBrains Mono** (body/tokens) + **Space Grotesk** (display), embedded as base64
  woff2 so each card HTML is self-contained. Re-source from npm `@fontsource/*` if re-embedding.
- Semantic color system — keep consistent across all cards: SHALL=cyan, WHEN=blue, WHILE=amber,
  IF=coral, WHERE=violet, values/optional=green, "added this edition"=acid-green.
- Rendering: HTML→PDF via **Playwright Chromium**, `print_background=True`,
  `prefer_css_page_size=True`, zero margins; print CSS uses `@page { size: letter }`.
- Regenerate after editing any card HTML:
  ```bash
  pip install -r requirements.txt && python -m playwright install chromium
  python scripts/regenerate.py
  ```

## Naming convention
Prefer the full word **specification** over "spec" in repo/dir/file names and headlines ("spec"
is ambiguous out of context). Inside a card's running prose, "spec" is acceptable shorthand
where context disambiguates.

## Content rules (the cards preach these — the repo follows them)
- Requirements use EARS; `SHALL` = MUST = mandatory/verifiable (RFC 2119). No "should" in a
  requirements block — if it's only a should, it isn't a requirement.
- Acceptance criteria are specific, machine-checkable, and traceable (each requirement → ≥1
  criterion).

## Decisions made
- 2026-06: Renamed from a single-card folder to a multi-component toolkit
  (`agent-specification-toolkit`) to match the owner's `llm-wiki-toolkit` and make room for the
  planned interviewer. Cards moved under `reference-cards/`; regenerate script now renders all
  cards.
- Planned next: build the Specification Interviewer (form factor undecided — see
  `interview/README.md`).

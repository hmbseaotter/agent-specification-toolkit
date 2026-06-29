# CLAUDE.md — context for continuing this toolkit

This repo is the **Agent Specification Toolkit**: tooling for writing software specifications an
AI coding agent can execute. Treat this file as the repo's own "prior decisions" — don't
relitigate them, but flag any that look broken. Append new structural choices under
"Decisions made."

## Components & where things live
- `reference-cards/*.html` — source of truth for each printable card. The matching `*.pdf` is a
  generated artifact; never hand-edit a PDF, regenerate it from its HTML.
- `templates/specification-template.md` — the working skeleton end users copy per feature.
- `interview/` — the Specification Interviewer. It is implemented as the `/specify` Claude Code
  **skill** at `.claude/skills/specify/SKILL.md`; `interview/README.md` documents it.
- `scripts/regenerate.py` — renders every `reference-cards/*.html` to a sibling PDF.
- `scripts/lint_spec.py` — deterministic, stdlib-only completeness linter for a spec file
  (required blocks present, EARS/SHALL, no "should" in requirements, criteria present, phase
  tags well-formed). ASCII output, cross-platform. The `/specify` skill runs it instead of
  reasoning through the checks — the determinism principle applied to the toolkit itself.
- `install.py` / `uninstall.py` — opt-in **global** install of the `/specify` skill into
  `~/.claude/skills/specify/` (stdlib, cross-platform). Installs SKILL.md + flat copies of the
  template and linter (so the skill finds its companions beside it); backs up any collision,
  writes a `.install-manifest.json`, and uninstalls cleanly (restoring backups). The project-local
  default (run `claude` from the clone) needs neither.

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
- 2026-06: Built the Specification Interviewer as the `/specify` Claude Code slash command
  (`.claude/commands/specify.md`). Chose a reasoning-driven command over a static form because the
  hard part is elicitation quality (pushing back on vague answers, handling the user's tangents).
  If it grows supporting files or branches, graduate it to a Claude Code skill (`SKILL.md`).
- 2026-06-29: Graduated `/specify` from a command to a **skill**
  (`.claude/skills/specify/SKILL.md`; old command removed). It now targets specifying **agents**
  end-to-end, not just features. Key design decisions (chosen with the owner):
  - **Decoupled, phased hand-off** — the interview emits a spec + a reviewed assumptions list + a
    build prompt; it never auto-spawns a builder. Building is a separate, explicit step.
  - **Expanded schema** — the template gained agent dimensions (control surface incl. a mandatory
    STOP condition, triggers, tools/permissions + "never do unattended" bright lines, state/memory,
    model & cost routing + **determinism boundary**, failure & escalation), a metadata header, an
    **assumptions review-gate** block, and a **changelog**.
  - **Determinism/cost discipline** — deterministic work (math, parsing, validation, lookups) is
    specified as plain code (zero tokens); the LLM is reserved for named judgment tasks at a named
    model tier. Applied to the skill itself (completeness checks delegate to `scripts/lint_spec.py`).
  - **Phasing** — the spec is the whole production-grade target; `[P#]` tags + an `implementation
    phases` block slice it. A **compose-your-phase menu** picks the first push: skeleton items are
    *required but overridable with an explicit reason*; optionals are multi-select with dependency
    resolution. Only the build prompt is phase-scoped; advancing a phase is a deterministic re-slice
    (no re-interview).
  - **Pre-existing-input intake** — STEP 0 critically evaluates any PRD/plan/code first (considered,
    never gospel); the interview fills only the gaps.
  - **Build-readiness guardrail** — a must-acknowledge check that the session's current model/effort
    fits the chosen phase (flags under- AND over-powered); distinct from the agent's runtime model
    routing. The settings call, and its consequences, sit with the human, on the record.
  - **Living spec** — git-versioned; **amend mode** re-checks only the delta and logs to the
    changelog; **advance-phase** re-slices without re-interviewing.
  - **Distribution** — project-local zero-footprint default (clone + run; delete to remove); an
    opt-in, stdlib, cross-platform global installer with collision backups + manifest-based clean
    uninstall lands in Phase 4. Repo is MIT-licensed and will be published publicly.

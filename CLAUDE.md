# CLAUDE.md — context for continuing this toolkit

This repo is the **Agent Specification Toolkit**: tooling for writing software specifications an
AI coding agent can execute. Treat this file as the repo's own "prior decisions" — don't
relitigate them, but flag any that look broken. Append new structural choices under
"Decisions made."

## Terminology — three distinct roles
Keep these straight throughout the docs:
- **Target agent** — the agent (or feature) you are *specifying*; the product to be built.
- **Building agent** — the AI coding tool that *consumes* this skill's spec + build prompt and writes
  the code (e.g. Claude Code, Cursor, Aider, GitHub Copilot/Workspace, Windsurf).
- **The interviewer** — the `/specify` skill in this repo; it produces the spec, it does **not** build.

## Components & where things live
- `reference-cards/*.html` — source of truth for each printable card. The matching `*.pdf` is a
  generated artifact; never hand-edit a PDF, regenerate it from its HTML.
- `templates/specification-template.md` — the working skeleton end users copy per agent (or feature).
- `templates/decision-record-template.md` — the companion record of every FORK the interview hit:
  options considered, the choice, and why. The spec's `prior decisions` block carries the compact
  what-and-why a building agent needs; this carries the **rejected alternatives**, which the spec
  alone never shows. Emitted as `specs/<slug>.decisions.md` (STEP 7, output 4).
- `interview/` — the Specification Interviewer. It is implemented as the `/specify` Claude Code
  **skill** at `.claude/skills/specify/SKILL.md`; `interview/README.md` documents it.
- `examples/` — two worked `/specify` outputs, one per build class: a zero-distance **skill**
  (`skill-csv-column-summariser/`: spec + emitted `SKILL.md` + companion script) and a
  build-required **agent** (`agent-pr-triage/`: spec + plan-gated build prompt). The emitted
  `SKILL.md` is illustrative — it lives under `examples/`, not `.claude/skills/`, so it is not
  registered as a live skill. Both specs pass `scripts/lint_spec.py`.
- `docs/workflow.mmd` / `docs/workflow.png` — the README workflow diagram's Mermaid source and its
  rendered PNG fallback (shown in a collapsed `<details>` for non-GitHub viewers). `.png` is a
  generated artifact; regenerate it from the `.mmd`, never hand-edit it.
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
- Regenerate after editing any card HTML (`python`/`pip` shown; on macOS/Linux use `python3`/`pip3`):
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
*Append-only — newest entries at the bottom. Dates are `YYYY-MM-DD`.*

- 2026-06-29: Renamed from a single-card folder to a multi-component toolkit
  (`agent-specification-toolkit`) to match the owner's `llm-wiki-toolkit` and make room for the
  interviewer. Cards moved under `reference-cards/`; regenerate script now renders all cards.
- 2026-06-29: Built the Specification Interviewer as the `/specify` Claude Code slash command
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
    never gospel); the interview fills only the gaps. STEP 0 also establishes two things that are
    never to be inferred: **where the artifacts land**, and the target's **intended visibility**
    (private/internal/public — a design input wherever secrets or held-out data are involved, since
    publishing can invalidate a "held-out" claim and a leaked secret in public history is permanent).
  - **Build-readiness guardrail** — a must-acknowledge check that the session's current model/effort
    fits the chosen phase (flags under- AND over-powered); distinct from the agent's runtime model
    routing. The settings call, and its consequences, sit with the human, on the record.
  - **Living spec** — git-versioned; **amend mode** re-checks only the delta and logs to the
    changelog; **advance-phase** re-slices without re-interviewing.
  - **Distribution** — project-local zero-footprint default (clone + run; delete to remove); plus an
    opt-in, stdlib, cross-platform global installer (`install.py` / `uninstall.py`) with collision
    backups + manifest-based clean uninstall. Repo is MIT-licensed and will be published publicly.
- 2026-07-01: Adopted the **spec-to-artifact distance** axis as the toolkit's organizing model
  (thesis consciously widened: "specifications for any executable unit — code OR procedure").
  - **Distance / build class** — the real axis is build determinism, not "skill vs agent".
    ZERO-DISTANCE targets (a skill; a declarative agent = harness-run markdown, e.g. a Claude Code
    subagent) have a deterministic "build" (reformatting), so the interviewer **emits the artifact
    itself** (`SKILL.md` / `AGENT.md`) — per the toolkit's own determinism principle. BUILD-REQUIRED
    targets (coded feature/agent) still get a **build prompt** for a building agent. Number of files
    also follows the determinism boundary: pure-judgment → one `.md`; custom deterministic steps →
    `.md` + companion script (this repo: `SKILL.md` + `lint_spec.py`).
  - **Conditional output #3** — STEP 7 emits either the artifact (zero-distance) or the build prompt
    (build-required). Anti-Swiss-knife guardrail: the core stays a tool-agnostic *specifier*; the only
    tool-specific part (writing `SKILL.md`/`AGENT.md`) is a thin, fenced emission step — no new
    companion scripts, no installer changes.
  - **Plan-gate in the build prompt** — build-required build prompts instruct the building agent to
    enter plan mode → present a plan → get human approval → build. A second human checkpoint whose
    value scales with distance (zero-distance targets skip it).
  - **Role field** — the stance the target adopts, added to metadata (and the building agent's role
    framing in the build prompt). Conditional, not automatic: included only where it sharpens tone
    or domain expertise, "n/a" otherwise, and concrete behaviour is preferred over a persona label.
  - **Type & value discipline** — the determinism boundary now asks for BOTH static typing (type
    hints + a checker; a float must not silently become an int) AND immutability for constants
    (`Final` / frozen); "type-check passes" becomes an acceptance criterion. The determinism boundary
    applies to skills too, not only agents. Language-aware; not a blanket SHALL.
- 2026-07-01: Zero-distance emit — locations, record, and a commit reminder (chosen with the owner).
  - Emit to TWO places: a **canonical copy** at `specs/<slug>.emitted/` (version-controlled safety
    copy, co-located with the spec) AND a **live copy** at `.claude/skills/<name>/` (skill) or
    `.claude/agents/<name>.md` (declarative agent) so it is immediately usable. Deleting the live copy
    never loses work (the canonical copy stays); the spec remains the source of truth for re-emission.
  - **`## emitted artifacts` record** — a new template output section logging WHAT was emitted and
    WHERE (both paths) + date: an un-missable audit trail so a bad emit can be cleanly removed
    (delete the live copy). `/specify` also echoes it to the user at emit time.
  - **Commit-now milestone reminder** — `/specify` tells the user to commit the emitted files
    immediately (git is the recovery path; forgetting to commit at the pristine moment is how a clean
    state gets lost).
  - README gained a **"dev-home vs use-site"** section: this repo is the tool's home, but `/specify`
    is *used* in the target project (where its outputs land), enabled by the opt-in global install.
- 2026-07-01: README front-matter for scanners (from resume-review feedback). Added, above the first
  section: three static **shields.io badges** (MIT / Python 3.8+ / Works with Claude Code — static so
  they render while the repo is still private), a bold **TL;DR** + component list, and a real **EARS
  requirements excerpt** (lifted verbatim from `examples/skill-csv-column-summariser/`) so a GitHub
  visitor sees what a spec produces immediately.
- 2026-07-01: Mermaid static fallback → new **`docs/`** folder. The workflow diagram's source lives at
  `docs/workflow.mmd`; a rendered `docs/workflow.png` sits in the README inside a collapsed
  `<details>` right after the ```mermaid``` block — GitHub shows the interactive diagram (details
  collapsed, no duplication), non-GitHub viewers get the PNG. Regenerate with
  `npx @mermaid-js/mermaid-cli -i docs/workflow.mmd -o docs/workflow.png -b white -s 2` (an HTML
  comment above the mermaid block records this). Rendered locally via the Playwright-cached Chromium
  (a puppeteer `executablePath` config) so no separate Chromium download is needed.

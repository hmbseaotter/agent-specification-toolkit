# Examples

Two worked examples produced by the `/specify` interviewer, one for each **build class** — the
spec-to-artifact distance axis that decides what the interview outputs.

| Example | Target type | Build class | What `/specify` emitted |
|---------|-------------|-------------|--------------------------|
| [`skill-csv-column-summariser/`](skill-csv-column-summariser/) | skill | **zero-distance** | the artifact itself — [`emitted/SKILL.md`](skill-csv-column-summariser/emitted/SKILL.md) + a companion [`csv_profile.py`](skill-csv-column-summariser/emitted/csv_profile.py) |
| [`agent-pr-triage/`](agent-pr-triage/) | coded agent | **build-required** | a phase-scoped [`build-prompt.md`](agent-pr-triage/build-prompt.md) (plan-gated) to hand a building agent |

Each folder's `specification.md` is the whole production-grade target (the source of truth).

- **Zero-distance** targets (a skill, or a declarative agent) have a deterministic "build," so the
  interviewer *emits the artifact directly*. The `emitted/` folder shows that output. Note the
  `SKILL.md` there is **illustrative** — it lives under `examples/`, not `.claude/skills/`, so it is
  not registered as a live skill. It follows the `SKILL.md` + companion-script pattern: the
  deterministic profiling is plain, type-hinted code (`csv_profile.py`); only the per-column
  interpretation is left to the LLM.
- **Build-required** targets (coded feature/agent) get a `build-prompt.md` you hand to a *building
  agent*; it names one phase, enforces the determinism boundary and bright lines, and opens with a
  **plan-gate** (plan → you approve → build).

## Check them

Both specs pass the deterministic linter:

```
python scripts/lint_spec.py examples/skill-csv-column-summariser/specification.md
python scripts/lint_spec.py examples/agent-pr-triage/specification.md
```

The zero-distance spec is reported with phasing relaxed (no `[P#]` tags needed); the build-required
spec carries `[P1] [P2] [P3]`.

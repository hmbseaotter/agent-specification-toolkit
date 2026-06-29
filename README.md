# Agent Specification Toolkit

Tools for writing software specifications that an AI coding agent can actually execute.

A specification here is a **contract** the agent reads, fails against, then writes code to
pass. Requirements are written in **EARS** (Easy Approach to Requirements Syntax), where the
load-bearing word `SHALL` turns a preference into something a test can verify.

## Components

| Component | Status | What it is |
|-----------|--------|------------|
| **Reference cards** (`reference-cards/`) | ✅ ready | Printable US-Letter infographics — the at-a-glance method. |
| **Specification template** (`templates/`) | ✅ ready | Copy-paste skeleton you fill in, one file per feature. |
| **Specification interviewer** (`/specify`) | ✅ ready | A Claude Code slash command that runs a guided Q&A — helping and forcing you to supply every input the agent needs — then writes a filled-in specification to `specs/`. See `interview/README.md`. |

## Layout

```
.
├── .claude/commands/
│   └── specify.md                              # the /specify interviewer (Claude Code slash command)
├── reference-cards/
│   ├── agent-specification-field-guide.html   # editable source (fonts embedded — self-contained)
│   └── agent-specification-field-guide.pdf     # print-ready, 2 pages, US Letter
├── templates/
│   └── specification-template.md               # the copy-paste skeleton
├── interview/
│   └── README.md                               # how the interviewer works
├── scripts/
│   └── regenerate.py                           # re-render every card's PDF from its HTML
├── requirements.txt
└── CLAUDE.md                                    # context for Claude Code when you continue
```

## Use it now

**Run the interviewer.** From the repo root, start Claude Code and invoke the command (it ships
with the repo, so cloning is enough):

```
claude
/specify password reset flow
```

It interviews you one question at a time, won't let required blocks stay empty, and writes the
result to `specs/<feature>.md`. Omit the argument to have it ask what you're specifying.

**Print a card.** Open the PDF in `reference-cards/` and print at *Actual size / 100%* (not
"fit to page"), paper **Letter**, margins **None**.

**Write a specification.** Copy the template into your project and fill it in, one file per
feature:

```bash
cp templates/specification-template.md /your-project/specs/your-feature.md
```

Fill every block top to bottom, then hand it to your agent using the prompt at the bottom of
the template (it lives in an HTML comment).

## Edit & regenerate the cards

Edit content in a card's `.html`, then regenerate its PDF one of two ways:

**A. Browser (no install).** Open the `.html` → Print → *Save as PDF* → paper Letter, margins
None, and enable **"Background graphics"** (browsers strip color backgrounds otherwise).

**B. Script (repeatable, renders all cards).**

```bash
pip install -r requirements.txt
python -m playwright install chromium
python scripts/regenerate.py
```

Card HTML embeds its fonts (JetBrains Mono + Space Grotesk) as base64, so every card renders
identically on any machine with no font installation.

## Naming note

This toolkit prefers the full word **specification** over the abbreviation "spec" in names and
filenames, since "spec" is ambiguous out of context. Inside the card's running prose, "spec"
is left as idiomatic shorthand where the surrounding context makes the meaning unambiguous.

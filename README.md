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
| **Specification interviewer** (`/specify`) | ✅ ready | A Claude Code **skill** that runs a guided interview — helping and forcing you to supply every input an agent needs — then writes a complete specification to `specs/`, derives a phased build plan you choose from, and emits a phase-scoped build prompt. See `interview/README.md`. |

## Layout

```
.
├── .claude/skills/specify/
│   └── SKILL.md                                # the /specify interviewer (Claude Code skill)
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

**Run the interviewer.** From the repo root, start Claude Code and invoke the skill (it ships
with the repo, so cloning is enough):

```
claude
/specify a background PR-triage agent
```

It interviews you one question at a time, won't let required blocks stay empty, surfaces every
assumption for your review, then helps you choose how far this first build goes — writing the
specification to `specs/<slug>.md` alongside a build prompt scoped to that phase. Omit the target
and it asks what you're specifying.

**Print a card.** Open the PDF in `reference-cards/` and print at *Actual size / 100%* (not
"fit to page"), paper **Letter**, margins **None**.

**Write a specification by hand** (instead of the interviewer). Copy the template into your
project and fill it in, one file per feature or agent:

- **macOS / Linux:**
  ```bash
  cp templates/specification-template.md /your-project/specs/your-feature.md
  ```
- **Windows (PowerShell):**
  ```powershell
  Copy-Item templates\specification-template.md C:\your-project\specs\your-feature.md
  ```

Fill every block top to bottom, then hand it to your agent using the prompt at the bottom of
the template (it lives in an HTML comment).

## Get it on another machine (safe, contained, removable)

This repo drops onto any machine — yours or someone else's, **Windows / macOS / Linux** —
**without touching anything global**. By default the `/specify` interviewer ships *inside the
repo's own `.claude/` folder*, which Claude Code loads **only** when you run it from this folder.
So nothing is installed system-wide, and removing it is just deleting the folder.

The steps below assume **no prior knowledge**. If a tool is already installed, skip that step.

### Before you start: install the two prerequisites

**1. Claude Code** — the interviewer runs inside it. Install it from
**[claude.com/claude-code](https://claude.com/claude-code)**, then check it works:

```
claude --version
```

(The first time you run `claude` it may ask you to sign in — follow its prompt.)

**2. Git** — used to download (clone) the repo.

- **Windows (PowerShell):**
  ```powershell
  winget install --id Git.Git
  ```
- **macOS:** running `git --version` once will offer to install Apple's command-line tools; accept it. Or, with [Homebrew](https://brew.sh): `brew install git`
- **Linux — Debian/Ubuntu:** `sudo apt update && sudo apt install git`
- **Linux — Fedora:** `sudo dnf install git`

Check it works (same command on every OS):

```
git --version
```

### Step 1 — Download (clone) the repo

This command is the **same on Windows, macOS, and Linux**:

```
git clone https://github.com/hmbseaotter/agent-specification-toolkit.git
```

> **Already set up SSH keys with GitHub?** You can use
> `git clone git@github.com:hmbseaotter/agent-specification-toolkit.git` instead. If you're not
> sure what that means, use the HTTPS command above — it needs no setup.

### Step 2 — Go into the folder

```
cd agent-specification-toolkit
```

### Step 3 — Start Claude Code and run the interviewer

```
claude
```

Then, at the Claude Code prompt, type:

```
/specify
```

That's it — `/specify` interviews you and writes a specification to `specs/`. (You can also name
the target up front, e.g. `/specify a background PR-triage agent`.) It's available here **only**
because it ships inside this repo's `.claude/` folder; no other project on the machine sees it.

### Removing it

Because the default install touches nothing global, removal is just **deleting the folder** —
there is no leftover config to clean up. Run this from the folder that *contains* the clone:

- **Windows (PowerShell):**
  ```powershell
  Remove-Item -Recurse -Force agent-specification-toolkit
  ```
- **macOS / Linux:**
  ```bash
  rm -rf agent-specification-toolkit
  ```

> **Want `/specify` in *every* project on a machine?** The toolkit also ships an **opt-in** global
> installer (run from the clone) that copies the skill into your Claude Code user config, **backs
> up** anything it would overwrite, **records exactly what it installed**, and **removes cleanly**
> on uninstall. The project-local default above never needs it — full instructions land with that
> installer.

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

## License

[MIT](LICENSE) © hmbseaotter.

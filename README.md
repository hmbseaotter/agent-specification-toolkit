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
│   ├── regenerate.py                           # re-render every card's PDF from its HTML
│   └── lint_spec.py                            # deterministic spec completeness linter (stdlib)
├── install.py                                  # opt-in global installer (stdlib, cross-platform)
├── uninstall.py                                # clean uninstaller (manifest-based; restores backups)
├── requirements.txt
└── CLAUDE.md                                    # context for Claude Code when you continue
```

## Use it now

> **Command note:** where commands say `python` / `pip`, that is the **Windows** form. On
> **macOS / Linux**, use `python3` / `pip3` instead. Forward slashes in paths work on all three OSes.

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

**Check a specification.** Validate a filled-in spec's completeness — pure deterministic checks,
no AI or tokens:

```
python scripts/lint_spec.py specs/your-feature.md
```

Fill every block top to bottom, then hand it to your agent using the prompt at the bottom of
the template (it lives in an HTML comment).

## Get it on another machine (safe, contained, removable)

This repo drops onto any machine — yours or someone else's — **without touching anything global**.
By default the `/specify` interviewer ships *inside the repo's own `.claude/` folder*, which Claude
Code loads **only** when you run it from this folder: nothing is installed system-wide, and removing
it is just deleting the folder.

**Pick your OS below and copy its block top to bottom**; ignore the other two. Steps assume no prior
knowledge — skip any tool you already have. (Forward slashes in paths work on all three OSes.)

### Windows (PowerShell)

```powershell
# 1. Prerequisites (skip any you already have):
#    Claude Code -> install from https://claude.com/claude-code   (then check: claude --version)
winget install --id Git.Git          # Git  (then check: git --version)

# 2. Download (clone) and enter the repo:
git clone https://github.com/hmbseaotter/agent-specification-toolkit.git
cd agent-specification-toolkit

# 3. Start Claude Code, then type  /specify  at its prompt:
claude

# 4. (Optional) make /specify available in EVERY project on this machine:
python install.py                    # undo later with:  python uninstall.py

# 5. Remove the toolkit entirely — run from the folder that CONTAINS the clone:
Remove-Item -Recurse -Force agent-specification-toolkit
```

### macOS

```bash
# 1. Prerequisites (skip any you already have):
#    Claude Code -> install from https://claude.com/claude-code   (then check: claude --version)
brew install git                     # Git  (or run `git --version` to trigger Apple's CLT installer)

# 2. Download (clone) and enter the repo:
git clone https://github.com/hmbseaotter/agent-specification-toolkit.git
cd agent-specification-toolkit

# 3. Start Claude Code, then type  /specify  at its prompt:
claude

# 4. (Optional) make /specify available in EVERY project on this machine:
python3 install.py                   # undo later with:  python3 uninstall.py

# 5. Remove the toolkit entirely — run from the folder that CONTAINS the clone:
rm -rf agent-specification-toolkit
```

### Linux

```bash
# 1. Prerequisites (skip any you already have):
#    Claude Code -> install from https://claude.com/claude-code   (then check: claude --version)
sudo apt update && sudo apt install git     # Debian/Ubuntu   (Fedora: sudo dnf install git)

# 2. Download (clone) and enter the repo:
git clone https://github.com/hmbseaotter/agent-specification-toolkit.git
cd agent-specification-toolkit

# 3. Start Claude Code, then type  /specify  at its prompt:
claude

# 4. (Optional) make /specify available in EVERY project on this machine:
python3 install.py                   # undo later with:  python3 uninstall.py

# 5. Remove the toolkit entirely — run from the folder that CONTAINS the clone:
rm -rf agent-specification-toolkit
```

> **SSH instead of HTTPS?** If you have set up SSH keys with GitHub, swap the clone URL for
> `git@github.com:hmbseaotter/agent-specification-toolkit.git`. If that means nothing to you, the
> HTTPS command above needs no setup. (Note: while this repo is private, cloning requires access;
> the HTTPS clone works for everyone once it is public.)

### About the optional global install (step 4)

You only need step 4 to use `/specify` *outside* this repo — the project-local default never does.
`install.py` needs only **Python 3.8+** (standard library — no `pip install`). It writes **only**
under `~/.claude/skills/specify/`, never touches your settings or hooks, and if a skill already
exists at that name it is **backed up** (moved aside), never overwritten — recording a manifest so
removal is exact and reversible:

- `install.py --dry-run` — preview exactly what it would do, change nothing.
- `uninstall.py` — remove the install and restore any backup it made.
- `uninstall.py --keep-backup` — remove the install but leave the backup in place.

After a global install, `/specify` works in every project; after uninstall your `~/.claude` is left
as it was.

## Edit & regenerate the cards

Edit content in a card's `.html`, then regenerate its PDF one of two ways:

**A. Browser (no install).** Open the `.html` → Print → *Save as PDF* → paper Letter, margins
None, and enable **"Background graphics"** (browsers strip color backgrounds otherwise).

**B. Script (repeatable, renders all cards).** (`python` / `pip` shown; on macOS/Linux use
`python3` / `pip3`.)

```
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

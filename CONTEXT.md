# ai-tools

A catalog of Claude Code skills and agents, installed onto a machine by a single remote script.

## Language

### Catalog

**Catalog**:
The set of skills and agents this repo offers, defined by the contents of its `/skills` and `/agents` directories. The Catalog is discovered dynamically — nothing lists it but the directories themselves.
_Avoid_: registry, index, manifest

**Skill**:
A directory containing a `SKILL.md` file, representing a single Claude Code capability. Always a directory, never a single file.
_Avoid_: plugin, extension, module

**Agent**:
A single `.md` file with YAML frontmatter defining a Claude Code sub-agent's name, description, tools, and system prompt. Always a flat file, never a directory.
_Avoid_: plugin, bot, assistant

### Installation

**Installer**:
The `install.sh` script at the repo root, fetched from GitHub and piped to bash. The only tool in the repo; everything else is Catalog content.
_Avoid_: CLI, manager, tool

**Store**:
The local directory `~/.ai-tools/`, a full mirror of the Catalog refreshed on every Installer run. Wholly owned by the Installer — nothing else writes there — and disposable: edits made in the Store are lost on the next Update or Uninstall.
_Avoid_: global store, repo clone

**Install**:
The act of symlinking an item from the Store into `~/.claude/skills/` or `~/.claude/agents/`, making it visible to Claude Code. Every Catalog item is in the Store; only Installed items are visible.
_Avoid_: publish, link, add, sync

**Update**:
The act of refreshing the Store from the Catalog without changing any symlinks. Installed items update automatically through their symlinks; new Catalog items land in the Store without becoming Installed.
_Avoid_: upgrade, sync, refresh

**Uninstall**:
The act of removing every `~/.claude` symlink that resolves into the Store, then deleting the Store itself. All-or-nothing; there is no per-item Uninstall.
_Avoid_: remove, unlink, clean

**Foreign Entry**:
An entry in `~/.claude/skills/` or `~/.claude/agents/` that does not resolve into the Store (e.g. a skills.sh-managed symlink, or a real local directory). The Installer never touches Foreign Entries.
_Avoid_: conflict, collision, external skill

### Multi-agent skill roles

**Orchestrator**:
The main agent in a multi-agent skill that coordinates subagents, exercises judgment on their output, and decides when the result is acceptable.
_Avoid_: main agent, coordinator, controller

**Worker**:
A subagent spawned by an Orchestrator to produce or transform an artifact.
_Avoid_: generator, creator, writer (use Worker for the role; task-specific names are fine within a skill's own docs)

**Validator**:
A subagent spawned by an Orchestrator to evaluate a Worker's output against defined quality criteria.
_Avoid_: reviewer, checker, auditor (use Validator for the role; task-specific names are fine within a skill's own docs)

**Verdict**:
The structured output of a Validator: either `PASS` or `REVISE`, accompanied by a list of findings each tagged `blocking` or `nit`. The Orchestrator acts on blocking findings; nits are advisory.
_Avoid_: review, feedback, result

## Relationships

- The **Catalog** is the repo; the **Store** is its local mirror; `~/.claude` symlinks into the Store define what is **Installed**
- Content flows one way: Catalog → Store → `~/.claude` symlink. There is no publish flow back into the Catalog — content changes happen by editing the repo
- Every Installer run (Install or **Update**) refreshes the whole Store, so all Installed items track the Catalog together — no version skew
- A **Skill** is a directory; an **Agent** is a file. The Installer distinguishes them by shape, not by configuration
- **Foreign Entries** and the Installer coexist in `~/.claude` but never interact

## Example dialogue

> **Dev:** "I want the `teach-me` skill on my laptop."
> **Domain expert:** "Run the **Installer** and pick it from the **Catalog**. The whole Catalog gets mirrored into your **Store**, and your pick is symlinked into `~/.claude/skills/`. Later, `--update` refreshes the Store and everything you've **Installed** comes along for free."

## Flagged ambiguities

- "install" previously meant symlinking from `~/.claude` into a *project's* `.claude/skills/` — resolved: that project-scoped concept is gone; **Install** is now machine-scoped only
- "subfolders" was used loosely for both skills and agents — resolved: **Skills** are directories, **Agents** are flat `.md` files
- "available" — resolved: there is only one kind of availability now, presence in the **Catalog**

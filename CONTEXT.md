# ai CLI

A command-line tool for managing Claude Code skills across projects and the user's global skill store.

## Language

**Skill**:
A directory containing a `SKILL.md` file, representing a single Claude Code agent capability.
_Avoid_: plugin, extension, module

**Global Store**:
The user-wide skill collection at `~/.claude/skills/`. Skills here are available to be installed into any project.
_Avoid_: user store, global directory

**Project Skills Directory**:
The `skills/` subdirectory of a project root. Contains skills that can be published from that project into the global store.
_Avoid_: source directory, local skills

**Local Skills Directory**:
The `.claude/skills/` subdirectory of a project root. Contains skills symlinked from the global store for use by that project.
_Avoid_: installed skills directory, project skills

**Publish**:
The act of symlinking a skill from a project skills directory into the global store, making it user-wide available.
_Avoid_: deploy, export, register

**Install**:
The act of symlinking a skill from the global store into a project's local skills directory, making it available to that project.
_Avoid_: link, add, import

**Publishable**:
A skill present in a project's skills directory that is a candidate for publish.
_Avoid_: available, local

**Installable**:
A skill present in the global store that is a candidate for install into a project.
_Avoid_: available, global

**Project Root**:
The top-level directory of a project. The `--from` and `--to` flags always point to a project root; the tool resolves the correct subdirectory (`skills/` or `.claude/skills/`) from there.
_Avoid_: base directory, working directory

**Agent**:
A single `.md` file with YAML frontmatter defining a Claude Code sub-agent's name, description, tools, and system prompt.
_Avoid_: plugin, bot, assistant

**Project Agents Directory**:
The `agents/` subdirectory of a project root. Contains agents that can be published from that project into the global agents store.
_Avoid_: source directory, local agents

**Local Agents Directory**:
The `.claude/agents/` subdirectory of a project root. Contains agent files symlinked from the global agents store for use by that project.
_Avoid_: installed agents directory, project agents

## Relationships

- A **Skill** lives in exactly one location at a time: a **Project Skills Directory**, the **Global Store**, or a **Local Skills Directory**
- An **Agent** lives in exactly one location at a time: a **Project Agents Directory**, the global agents store (`~/.claude/agents/`), or a **Local Agents Directory**
- **Publish** moves a resource from a project source directory → global store (via symlink); applies to both skills and agents
- **Install** moves a resource from the global store → a project local directory (via symlink); applies to both skills and agents
- A **Project Root** contains at most one **Project Skills Directory**, one **Local Skills Directory**, one **Project Agents Directory**, and one **Local Agents Directory**
- **Skills** are directories identified by a `SKILL.md` file; **Agents** are individual `.md` files

## Example dialogue

> **Dev:** "I want to use the `teach-me` skill in my new project."
> **Domain expert:** "First check if it's in your **global store** with `ai skills list`. If it's there, **install** it into your project with `ai skills install teach-me`. If it's not there yet, find the project that owns it and **publish** it first."

## Flagged ambiguities

- "available" was used loosely to mean both **publishable** (in a project skills directory) and **installable** (in the global store) — resolved: these are distinct concepts with distinct flags.

# ai

A CLI for managing Claude Code skills and agents across projects.

## Overview

`ai` is a lightweight Bash CLI that lets you publish, install, and uninstall [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills and agents using symlinks. Skills (directories with a `SKILL.md`) and agents (`.md` files) live in a user-wide global store at `~/.claude/` and can be selectively linked into any project — keeping resources in one place while making them available wherever you need them.

## Key Features

- **Publish** skills and agents from a project into the global store (`~/.claude/skills/`, `~/.claude/agents/`)
- **Install** from the global store into any project's `.claude/skills/` or `.claude/agents/` directory
- **Uninstall** cleanly removes symlinks and cleans up `.gitignore` entries automatically
- **List** shows the global store, or diffs what is publishable/installable for a given project
- **Interactive mode** (`--interactive`) prompts before each action; `--all` acts on everything at once
- Symlink-based design: one canonical copy, zero duplication across projects
- Auto-manages `.gitignore` — installed symlinks are ignored by git without manual edits

## Installation

```bash
git clone <this-repo> ~/ai-tools
cd ~/ai-tools
./install          # creates /usr/local/bin/ai -> <repo>/ai
```

To remove:

```bash
./uninstall
```

## Usage

### Skills

```bash
# See what skills are in your global store
ai skills list

# Publish skills from the current project into the global store
ai skills publish --all
ai skills publish teach-me pdf-to-md   # publish specific skills

# Install skills from the global store into a project
ai skills install --all
ai skills install teach-me --to ~/projects/my-app

# See what can be published or installed
ai skills list --publishable
ai skills list --installable --to ~/projects/my-app

# Uninstall skills from a project
ai skills uninstall teach-me
ai skills uninstall --all
```

### Agents

```bash
# Same interface — just replace 'skills' with 'agents'
ai agents list
ai agents publish --all
ai agents install my-agent --to ~/projects/my-app
ai agents uninstall --all --interactive
```

### Flags

| Flag | Applies to | Description |
|------|-----------|-------------|
| `--all` | publish, install, uninstall | Act on all available resources without prompting |
| `--interactive` | publish, install, uninstall | Prompt before each resource |
| `--from <project-root>` | publish, uninstall, list | Use this project as the source |
| `--to <project-root>` | install, list | Use this project as the target |

## Concepts

- **Global store** — `~/.claude/skills/` and `~/.claude/agents/`. Resources here are available to install into any project.
- **Publish** — symlink from a project's `skills/` or `agents/` directory into the global store.
- **Install** — symlink from the global store into a project's `.claude/skills/` or `.claude/agents/` directory.
- **Project root** — the `--from` and `--to` flags always point to a project root; `ai` resolves the correct subdirectory internally.

For architectural decisions, see [docs/adr/](docs/adr/).

## Contributing

Open an issue or pull request on GitHub.

## License

MIT

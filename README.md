# ai-tools

A catalog of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills and agents, installed with a single command.

## Overview

This repo holds reusable Claude Code skills (directories with a `SKILL.md`) and agents (flat `.md` files) under `/skills` and `/agents`. A single `install.sh` — run straight from GitHub, no clone required — mirrors the catalog to `~/.ai-tools` and symlinks your picks into `~/.claude`, where Claude Code discovers them. Re-running the installer updates everything in place.

## Key Features

- **One-command install** — `curl | bash`, pick what you want from an interactive menu
- **Dynamic catalog** — the menu is whatever is in `/skills` and `/agents`; adding a skill to the repo is all it takes to publish it
- **Full local mirror** — the whole catalog is cached in `~/.ai-tools`; installing is just symlinking, so updates flow to every installed item at once
- **Agent-friendly** — non-interactive flags (`--all`, `--list`, names) for coding agents and scripts
- **Safe by construction** — never touches skills or agents it didn't install (e.g. skills.sh-managed entries)
- **Clean uninstall** — one flag removes all symlinks and the mirror

## Quick Start

```bash
# interactive: pick skills/agents from a menu
curl -sSL https://raw.githubusercontent.com/pop-dog/ai-tools/mainline/install.sh | bash

# for coding agents — install everything, no prompts
curl -sSL https://raw.githubusercontent.com/pop-dog/ai-tools/mainline/install.sh | bash -s -- --all
```

## Usage

```bash
# see what's available
curl -sSL https://raw.githubusercontent.com/pop-dog/ai-tools/mainline/install.sh | bash -s -- --list

# install specific items by name
curl -sSL https://raw.githubusercontent.com/pop-dog/ai-tools/mainline/install.sh | bash -s -- pdf-to-md teach-me

# update: refresh the mirror; everything installed updates in place
curl -sSL https://raw.githubusercontent.com/pop-dog/ai-tools/mainline/install.sh | bash -s -- --update

# uninstall: remove all installed symlinks and delete ~/.ai-tools
curl -sSL https://raw.githubusercontent.com/pop-dog/ai-tools/mainline/install.sh | bash -s -- --uninstall
```

## How It Works

- The installer downloads the repo tarball and mirrors `/skills` and `/agents` into `~/.ai-tools` (the **store**) on every run.
- **Installing** symlinks an item from the store into `~/.claude/skills/<name>` or `~/.claude/agents/<name>.md`. Only installed items are visible to Claude Code; the rest just sit in the cache.
- **Updating** (`--update`, or any later run) refreshes the store, so installed items update through their symlinks automatically.
- Anything in `~/.claude` that doesn't point into the store is a *foreign entry* and is never modified or removed.
- The store is disposable: local edits to installed items live in `~/.ai-tools` and are overwritten on the next run. Durable changes belong in this repo.

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

## Contributing

Add a skill (a directory containing a `SKILL.md`) under `/skills`, or an agent (a single `.md` file with YAML frontmatter) under `/agents`, and open a pull request. The installer picks up new items automatically.

### Testing a skill before committing

`dev-link.sh` (clone-only) symlinks a working-tree skill or agent straight into `~/.claude`, bypassing the store — so your edits are live and you can test before you commit or push.

```bash
./dev-link.sh my-skill          # link one working-tree item, live
./dev-link.sh --all             # link everything in the working tree
./dev-link.sh --list            # working-tree items and their link status
./dev-link.sh --unlink my-skill # remove that dev link
./dev-link.sh --unlink --all    # remove every dev link from this repo
```

Dev links point at the working tree, not the store, so `install.sh` treats them as foreign and never overwrites them. If a name is already installed from the store, `dev-link.sh` skips it — `rm` that link or run `install.sh --uninstall` first.

## License

MIT

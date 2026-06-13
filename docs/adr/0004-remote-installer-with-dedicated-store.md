# Remote single-script installer with a dedicated local store

The `ai` CLI (publish/install symlink management across projects) was more machinery than the job needed. We replaced it with a single `install.sh` at the repo root, run as `curl … | bash`, which downloads the repo tarball from codeload.github.com, mirrors all of `/skills` and `/agents` into `~/.ai-tools/`, presents a picker, and symlinks the selections into `~/.claude/skills/` and `~/.claude/agents/`. The store is a full cache; installation is purely selective symlinking.

## Considered options

- **Store location.** `~/.agents/` (the skills.sh convention already in use on our machines) was rejected: it is another tool's territory, name collisions are possible, and it has no convention for agents. A dedicated `~/.ai-tools/` store means everything in it is ours, which is also what makes all-or-nothing uninstall safe.
- **Fetch mechanism.** The GitHub contents API (rate-limited, needs JSON parsing in bash) and git sparse clone (requires git, leaves a working copy) were rejected in favor of one anonymous tarball download — the repo is small enough that mirroring everything costs nothing.
- **Store model.** Copying only selected items (store = installed set, per-item update control) was rejected in favor of a full mirror refreshed on every run: cleaner separation of concerns (mirror locally vs. install = symlink), no version skew between items, and it makes `--update` trivial — refresh the store, touch no symlinks, and installed items update through their existing links.
- **Uninstall granularity.** Per-item uninstall was rejected: at this catalog size, `--uninstall` removes every `~/.claude` symlink resolving into the store and then deletes the store. Foreign entries (e.g. skills.sh symlinks) are never touched, in either direction.

## Consequences

- Any installer run refreshes the whole store, so every installed item updates as a side effect — for a personal always-want-latest catalog, that is the intent. `--update` does only this: refresh the store, change no symlinks.
- The store is disposable: local edits to installed items land in `~/.ai-tools` via the symlinks and are lost on the next run or uninstall. Durable changes belong in this repo.
- Testing uncommitted catalog changes does *not* go through the store. A separate clone-only `dev-link.sh` symlinks working-tree items directly into `~/.claude` for live editing. Because those links point at the working tree rather than the store, `is_ours` classifies them as foreign, so `install.sh` and `--update` leave them untouched — no store pollution, no "ephemeral until pushed" footgun.
- Supersedes ADR 0001 and ADR 0002, which documented the deleted CLI (removed; see git history).

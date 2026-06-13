---
name: commit
description: Writes a semantic (Conventional Commits) message for the current changes and creates the commit. Determines what to commit from context, picks the right type and scope, and follows the subject/body/footer rules. Use when the user wants to commit changes, asks for a commit message, or invokes /commit.
---

## Commit

Commit the current changes with a well-formed semantic commit message.

### What to commit

In priority order: (1) files/paths named in the prompt; (2) already-staged changes (`git diff --cached`); (3) otherwise review the working tree (`git status`, `git diff`) and stage what's relevant. If there's nothing to commit, stop and say so. If the changes mix unrelated concerns, suggest splitting them into separate commits.

### Format

```
<type>(<optional scope>): <Subject>

<optional body>

<optional footer(s)>
```

**Type** (pick the one that fits; mixing types is a signal to split):
- **feat** — new user-facing feature
- **fix** — bug fix affecting users
- **docs** — documentation only
- **style** — formatting/whitespace, no behavior change
- **refactor** — restructure production code without changing behavior
- **test** — add/rework tests, no production change
- **chore** — build tooling, deps, other maintenance

**Scope** — optional lowercase noun for the area affected (`feat(auth):`), or a tracker ticket (`refactor(FOW-1327):`). Omit if it adds no clarity.

**Subject** (Beams' rules):
- ≤50 chars including the prefix; never exceed 72 (GitHub truncates there).
- Imperative mood — must complete *"If applied, this commit will ___"*.
- Type/scope lowercase, subject capitalized (`feat: Add hat wobble`). No trailing period.
- Blank line before the body.

**Body** (optional) — the diff shows *what* and *how*; use the body for *why*. Wrap at 72 chars. A good body covers: the problem or motivation the change addresses, the reasoning behind the chosen approach, and any consequences a future reader needs (side effects, follow-ups, things deliberately left out). Omit the body when the subject alone conveys both *what* and *why*; require one for non-obvious motivation, a non-obvious approach, side effects/follow-ups, or breaking changes. If the body would only restate the subject, leave it out.

The commit message describes the **current change and its lasting rationale**, written for a future reader of the history — not a log of how the work unfolded:
- Never reference details that were only relevant *during* implementation: mid-implementation decisions you reversed, dead ends, internal task/ticket scaffolding, or "as requested" framing.
- Avoid comparative language ("now uses", "no longer", "changed from X") *unless* the prior state is itself the reason for the change — then it belongs in the *why*.
- State things in terms of the resulting behavior, not the act of changing it.

**Footers** — `BREAKING CHANGE: ...`, `Closes #123`, co-authorship.

### Before committing

- Match the repo's existing conventions where they differ (`git log --oneline -20`), including lowercase subjects if that's the norm.
- Honor harness-required footers (e.g. a co-author line).
- Don't commit unless asked — if the user only wants a message, output it and stop.

### Example

```
fix(parser): Handle empty input without crashing

The tokenizer assumed at least one token and indexed past the end on
blank lines. Guard the empty case and return an empty token list.

Closes #214
```

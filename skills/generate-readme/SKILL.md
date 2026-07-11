---
name: generate-readme
description: Generates or refactors a project README to a standard quality bar. For projects without a README, generates one from scratch. For projects with an existing README, leaves it alone if it already meets the bar, otherwise aggressively rewrites it to standard while preserving the meaning of the original content. Over-scope content may be moved into /docs/. Use when the user wants to create or improve a project's README, or invokes /generate-readme.
---

# generate-readme

Produce a README that meets the quality bar in the **Checklist** below, in a single pass. Read
the sources, write or refactor the README directly, review your own work against the Checklist
once, fix any gaps you find, then stop.

## Step 1 — Locate the repo and detect mode

Resolve the project root with `git rev-parse --show-toplevel`. If that fails (not a git
repository), use the current working directory as the root. All paths below — `README.md` and
`docs/` — are relative to that root.

- **No `README.md` at the root**: mode is `new`. Go to Step 3.
- **`README.md` exists**: mode is `augment`. Read it in full, then go to Step 2.

## Step 2 — Gate (augment mode only)

Check the existing README against the **Checklist**.

- If it satisfies every **Required** item and has no **Disqualifying** content, it already
  meets the bar. Ignore nit-level imperfections. Make **no changes**. Print
  `README already meets the standard. No changes made.` and stop.
- Otherwise, it fails on at least one blocking item. Continue to Step 3 and rewrite it.

Do not rewrite a passing README just to reshape it — gratuitous reflow of a good README is
destructive for no benefit.

## Step 3 — Read the sources

Understand the project before writing anything. Read in priority order; be selective, not
exhaustive:

1. **Manifest** — `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `build.gradle`,
   `*.gemspec`, or equivalent. Authoritative for project name, description, version,
   dependencies.
2. **Existing README** (augment mode) — the authoritative source for the *meaning* you must
   preserve (see Step 4).
3. **Entry points and public interfaces** — sample the main modules to learn what the project
   actually does.
4. **Git log** — `git log --oneline -20` for history and maturity.
5. **Existing `docs/`** — for context and to avoid duplicating or clobbering.
6. **Build/CI/config** — `.github/workflows/`, `Dockerfile`, `docker-compose.yml`,
   `.env.example` — how the project is built and run.
7. **Image assets** — note any existing logo/banner/screenshot/GIF files so you can reference
   real paths. Never invent image links to assets that do not exist.

## Step 4 — Write or refactor the README

Write the finished README directly to `README.md` at the root. Structure it per the Checklist,
including only the sections that apply to this project.

**Augment mode is aggressive but meaning-preserving.** Every fact the existing README conveyed
must survive — do not drop information and do not invent new claims. But the exact wording,
section order, and layout are yours to reshape to the standard. You are rewriting the
*presentation*, not the *substance*.

**New mode on a thin or empty repo:** produce a correct skeleton with the standard sections and
explicit `<!-- TODO: ... -->` markers where information is genuinely unavailable. Do not
fabricate installation commands, usage examples, or claims you cannot ground in the sources.

### `/docs/` extraction

Move a block out to `docs/<topic>.md` (creating `docs/` if needed) **only** when it clearly
exceeds README scope by one of the **Disqualifying** triggers below. Replace the moved block
with a one-line reference link, e.g. `For the full API reference, see [docs/api.md](docs/api.md).`
Be conservative: do not split out content that is fine where it is, and do not create `docs/`
files speculatively. Use relative links so they resolve on GitHub.

## Step 5 — Review and finish

Re-read what you wrote and check it against the Checklist once. Fix any Required gaps,
Disqualifying content, or severe style issues you find. Then print a short report:

```
README {generated|refactored}.
- Mode: {new|augment}
- README.md: {root-relative path}
- /docs/ files created: {comma-separated list, or "none"}
```

Stop.

---

## Checklist

Quality bar, grounded in a sampling of well-regarded READMEs. This list is baked in rather
than fetched at runtime — see `docs/skill-authoring.md` for why. Refresh it deliberately when
it goes stale.

### Required (blocking if absent or inadequate)

- **Name + tagline.** Project name and a one-sentence tagline — what it is and who it's for —
  in the first few lines. A reader should understand the project within ~5 seconds.
- **Overview.** 2–4 sentences on what it does and *why it matters*. Frame the purpose or the
  problem it solves; a bare feature list does not satisfy this.
- **Installation / Getting Started.** Concrete setup steps, **or** an explicit link to them.
  (A link out counts — httpie does exactly this.)
- **Usage example.** At least one concrete usage example as a fenced code block with a language
  tag. Show, don't tell.
- **License.** A license statement — name plus a link, or a pointer to the `LICENSE` file.

### Recommended (nit if absent, not blocking)

- **Badges** — build/CI, version, license, downloads. Near-universal above the fold.
- **Visual demo** — an animated GIF or screenshot for any tool with visible CLI or GUI output.
  Strongly expected for such tools; reference only assets that actually exist.
- **Table of contents** for long READMEs (~6+ sections). A collapsible `<details>` TOC keeps it
  from crowding the above-the-fold content.
- **Logo/banner** when image assets exist in the repo.
- **Contributing pointer** — a brief note linking to `CONTRIBUTING.md` if it exists.
- **Links to deeper docs** — wiki, full API reference, or `docs/` for depth-seekers.
- **Social proof** — a "Who uses it" / users / acknowledgements section, where applicable.

### Disqualifying (blocking if present inline — extract to `docs/`)

- **Full API reference** — more than ~10 endpoints or methods documented inline. Keep short
  illustrative snippets; link the full reference out (as nlohmann/json does).
- **Deep architecture or design docs** — more than a brief paragraph (→ `docs/architecture.md`).
- **Full configuration reference** — more than ~10 options listed inline.
- **Changelog content** (→ `CHANGELOG.md` at the root).
- **Detailed contributing guide** — more than one paragraph (→ `CONTRIBUTING.md` at the root).
- **Runbooks or operational procedures.**

### Style (nit unless severe)

- No clear hook in the first ~5 lines.
- Fenced code blocks missing language tags.
- Broken or ambiguous links; logo/badge links pointing at assets that do not exist.
- Walls of prose where a code example would be clearer.

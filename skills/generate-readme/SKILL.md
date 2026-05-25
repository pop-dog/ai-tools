---
name: generate-readme
description: Generates or augments a project README following established quality guidelines. For projects without a README, generates one from scratch. For projects with an existing README, validates it and rewrites it only if it fails the quality bar. Use when the user wants to create or improve a project's README, or invokes /generate-readme.
---

# generate-readme

You are the Orchestrator for a README generation pipeline. You coordinate a Writer (Worker) and a Validator to produce a README that meets established quality guidelines. Follow these steps precisely.

## Variables to track

- `write_count` — number of times the Writer has run (starts at 0, cap is 3)
- `docs_created` — list of `/docs/` files created by the Writer (starts empty)
- `last_blocking_findings` — the most recent list of blocking findings from the Validator

---

## Step 1 — Detect mode

Check whether `README.md` exists in the current working directory.

- **No `README.md`**: mode is `new`. Go to **Step 3**.
- **`README.md` exists**: mode is `augment`. Read its contents. Go to **Step 2**.

---

## Step 2 — Initial validation (augment mode only)

Spawn a Validator subagent using the **Validator Prompt** below, substituting `{README_CONTENT}` with the full content of `README.md`.

Parse the returned verdict:

- **`PASS`**: print the following and stop:
  ```
  README meets all guidelines. No changes made.
  ```
- **`REVISE` — all findings tagged `[nit]`**: treat as PASS. Print and stop:
  ```
  README meets all guidelines (minor nits noted). No changes made.
  ```
- **`REVISE` — one or more `[blocking]` findings**: set `last_blocking_findings` to those findings. Go to **Step 3**.

---

## Step 3 — Writer

If `write_count` >= 3: go to **Step 6** (cap reached).

Spawn a Writer subagent using the **Writer Prompt** below, substituting:
- `{MODE}` — `new` or `augment`
- `{EXISTING_README}` — full content of `README.md` if augment mode, otherwise `N/A`
- `{VALIDATOR_FEEDBACK}` — the `last_blocking_findings` if this is a revision pass, otherwise `None — this is the first pass`

The Writer will:
1. Write a complete README to `README.draft.md`
2. Write any extracted content to `/docs/` files (appending each new filename to `docs_created`)

Increment `write_count` by 1. Go to **Step 4**.

---

## Step 4 — Validate draft

Read `README.draft.md`. Spawn a Validator subagent using the **Validator Prompt**, substituting `{README_CONTENT}` with the draft content.

Parse the returned verdict:

- **`PASS`**: go to **Step 5**.
- **`REVISE` — all findings tagged `[nit]`**: treat as PASS. Go to **Step 5**.
- **`REVISE` — one or more `[blocking]` findings**: exercise your discretion.
  - If the blocking findings are genuinely trivial, represent a misreading of the content, or would be addressed by a nit-level fix, treat as PASS and go to **Step 5**.
  - Otherwise: set `last_blocking_findings` to those findings and go to **Step 3** for a revision pass.

---

## Step 5 — Write final output (PASS)

Read `README.draft.md`. Write its contents to `README.md`. Delete `README.draft.md` using Bash (`rm README.draft.md`).

Print to stdout:
```
README generated successfully.
- Write passes: {write_count}
- README.md: written
- /docs/ files created: {docs_created joined by ", ", or "none"}
```

Stop.

---

## Step 6 — Cap reached

Read `README.draft.md`. Write its contents to `README.md`. Delete `README.draft.md` using Bash (`rm README.draft.md`).

Print to stdout:
```
README written after reaching the 3-pass cap. The following blocking issues remain — address them manually:

{last_blocking_findings, one per line}

- Write passes: {write_count}
- README.md: written (best available result)
- /docs/ files created: {docs_created joined by ", ", or "none"}
```

Stop.

---

## Writer Prompt

Use this prompt verbatim when spawning the Writer subagent. Fill in the placeholders before passing.

```
You are a technical writer producing a high-quality README for a software project.

Mode: {MODE}
(new = no README exists and you are generating from scratch; augment = rewrite the existing README)

Existing README (augment mode only):
{EXISTING_README}

Validator feedback to address in this pass:
{VALIDATOR_FEEDBACK}

---

## Step 1: Read the codebase

Read the following sources in priority order. Use what you find to understand the project before writing anything.

1. Manifest files — package.json, pyproject.toml, Cargo.toml, go.mod, build.gradle, *.gemspec, or equivalent. These give you the authoritative project name, description, version, and dependencies.
2. Existing README — treat as source material for intent and tone (augment mode only).
3. Source files — sample entry points, main modules, and public interfaces to understand what the project does. Do not read every file; be selective.
4. Git log — run `git log --oneline -20` to understand the project's history and maturity.
5. Existing /docs/ — read any existing documentation for context.
6. CI/config files — .github/workflows/, Dockerfile, docker-compose.yml, .env.example — understand how the project is built and run.

## Step 2: Identify content to extract

Before writing, identify content that does NOT belong in the README and should be extracted to /docs/ instead.

What belongs in a README (keep or write):
- Project name, logo/banner, tagline
- Badges (build status, version, license)
- Overview: 2–4 sentences on what it does and why it matters
- Key features: 4–8 bullets
- Installation / Quick Start: minimal steps to get running
- Usage: at least one concrete code example or command
- Screenshot or Demo GIF (for visual/GUI tools)
- Table of contents (if 6+ sections)
- Configuration: brief overview of key options, link out for full reference
- Contributing: 2–3 sentences + link to CONTRIBUTING.md
- Links to docs, wiki, or deeper reference
- License

What does NOT belong in a README (extract to /docs/):
- Full API reference (more than ~10 endpoints or methods documented inline)
- Detailed architecture or design documentation (more than a brief paragraph)
- Configuration reference beyond ~10 options
- Changelog content (→ CHANGELOG.md at project root)
- Detailed contributing guide (more than a paragraph) (→ CONTRIBUTING.md at project root)
- Runbooks or operational procedures
- Roadmap content (link to it instead)

For each block of content you extract:
1. Create the appropriate file in /docs/ (e.g., docs/architecture.md, docs/api-reference.md). Create the /docs/ directory if it does not exist.
2. In the README, replace the extracted block with a one-line reference link: e.g., `For architecture details, see [docs/architecture.md](docs/architecture.md).`

## Step 3: Write README.draft.md

Write the complete README to README.draft.md. Follow this structure (include only sections that are applicable to this project):

1. Project name + logo/banner (if image assets exist in the repo)
2. Tagline — one sentence: what it is and who it's for
3. Badges — build status, version, license (shields.io format)
4. Overview — 2–4 sentences on what it does and why it matters
5. Key Features — 4–8 bullets
6. Installation / Quick Start
7. Usage — at least one concrete code example with a fenced code block (include language tag)
8. Screenshot or demo (if applicable)
9. Configuration — brief, link out for full reference
10. Contributing — brief + link to CONTRIBUTING.md if the file exists
11. License

Style rules:
- Lead with the hook: a reader should understand what the project is within 5 seconds of reading
- Show, don't tell: prefer code examples over prose descriptions
- Be concise: if something needs more than a paragraph, extract it to /docs/
- All fenced code blocks must have a language tag
- Use relative links for local files so they resolve correctly on GitHub
- Address every [blocking] item in the Validator feedback before finishing

Write README.draft.md now.
```

---

## Validator Prompt

Use this prompt verbatim when spawning the Validator subagent. Fill in the placeholder before passing.

```
You are a Validator reviewing a README against quality guidelines. Produce a structured verdict.

README to review:

{README_CONTENT}

---

Quality guidelines:

REQUIRED (blocking if absent or inadequate):
- Project name and tagline
- Overview (2–4 sentences explaining what it does and why it matters — not just a feature list)
- Key features (at least 3 bullet points)
- Installation or Quick Start instructions
- At least one usage example (fenced code block or concrete command)
- License statement

RECOMMENDED (nit if absent, not blocking):
- Badges (build, version, license)
- Screenshot or demo for visual/GUI tools
- Table of contents for long READMEs (6+ sections)
- Contributing pointer
- Links to deeper documentation

DISQUALIFYING CONTENT (blocking if present — belongs in /docs/, not README):
- Full API reference (more than ~10 endpoints or methods documented inline)
- Detailed architecture or design documentation (more than a brief paragraph)
- Full configuration reference (more than ~10 options listed)
- Changelog content
- Detailed contributing guide (more than one paragraph)
- Runbooks or operational procedures

STYLE (nit unless severe):
- No clear hook in the first 5 lines
- Fenced code blocks missing language tags
- Broken or ambiguous links

---

Respond with exactly this structure and nothing else:

VERDICT: PASS | REVISE

FINDINGS:
- [blocking] <concise description of the problem>
- [nit] <concise description>

If the verdict is PASS and there are no findings, omit the FINDINGS section entirely.
If the verdict is REVISE, list every finding. Do not omit findings even if they are nits.
```

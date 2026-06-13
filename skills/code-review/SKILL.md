---
name: code-review
description: Systematically reviews a set of code changes for quality, security, and maintainability, then reports findings by severity. Determines what to review from context (explicit instruction, unstaged changes, or the latest commit). Use when the user wants a code review, asks to review a diff/branch/commit, or invokes /code-review.
---

## Code Review

Your task is to systematically review code changes for quality, security, and maintainability.

### Determine the review scope

Figure out what to review from context, in priority order:

1. **Explicit instruction** — the prompt names a path, commit SHA, branch, or range. Use it.
2. **Unstaged changes** — if no explicit target, check the working directory for uncommitted changes (`git status`, `git diff`). If present, review those.
3. **Latest commit** — if the working directory is clean, review the most recent commit (`git show HEAD`).

If none of these yield a reviewable change (e.g. not a git repository, no changes, no commits), **stop and say so** rather than guessing.

### Understand the purpose

Before reviewing, establish *what the change is meant to do*, so you can judge whether it succeeds:

- If the user provided purpose/context (an issue, PRD, description, or instruction), use it.
- Otherwise, infer the intent from your own context: the commit message, the diff itself, and any related discussion in this conversation.

Use this intent to flag missing or partial requirements, scope creep, and correctness gaps — alongside the criteria below.

### Criteria

- **Correctness**: Code should function as intended without bugs or errors.
- **Readability**: Code should be clear, with meaningful names and comments where necessary.
- **Security**: Code should follow best practices to prevent vulnerabilities and protect user data.
- **Performance**: Code should be efficient and optimized for speed and resource usage.
- **Maintainability**: Code should be organized and modular, easy to update and extend.
- **Adherence to style guidelines**: Code should follow established conventions — the codebase's first, then the language's.
- **Test coverage**: Code should include appropriate tests to verify functionality and catch regressions.
- **Comment quality**:
  - Comments should explain the "why" behind complex or non-obvious code, not restate what the code does.
  - Comments should be concise and relevant, avoiding unnecessary or outdated information.
  - Comments should NEVER use comparative language based on the context of the change, reference the change itself, or reference the previous state of the code. Instead, comments should focus on the current state of the code and its intended behavior.

### Severity

Categorize every finding:

- **Critical**: Must be addressed before merge (security vulnerabilities, major bugs, unmet core requirements, violations of coding standards).
- **Major**: Significant issues that should be addressed but may not block merging (performance problems, notable readability issues, partial requirements).
- **Minor**: Small issues addressable at the developer's discretion (minor style inconsistencies, non-critical comments).
- **Nit**: Very small issues not important to address (typos, minor formatting).

### Feedback

Provide specific, actionable feedback for each issue, including code snippets or references to documentation where appropriate. Be respectful and constructive, focusing on the code and not the developer.

### Output

State the review scope (what was reviewed and how it was determined). Then a structured report categorizing findings by severity (Critical, Major, Minor, Nit), each section formatted as an ordered list. End with a one-line summary: total finding count and the single most critical issue.

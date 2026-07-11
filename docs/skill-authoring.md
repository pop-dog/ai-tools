# Bake static guidance into a skill; don't fetch it at runtime

A skill that depends on curated external knowledge — a style guide, a quality
checklist, a corpus of examples — should embed a fixed snapshot of that
knowledge directly in `SKILL.md`, rather than fetching or re-deriving it at
invocation time.

Fetching at runtime makes a skill slower, fragile against network failures or
upstream changes, and non-deterministic: the same invocation can behave
differently depending on what a remote resource returns that day. Baking the
guidance in trades that away for a different cost — the guidance can go stale
until someone deliberately refreshes it — which is preferable to a skill that
fails, drifts, or varies invocation-to-invocation.

Refresh baked guidance like any other part of a skill: read the current
sources, revise the `SKILL.md` content directly, and put the rationale for
*this specific update* (what was sampled, what changed) in the pull request,
not in a permanent in-repo record.

`skills/generate-readme/SKILL.md` is the current example of this pattern.

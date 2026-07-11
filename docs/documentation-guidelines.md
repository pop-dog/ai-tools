# Design rationale lives in pull requests, not in the repo

Default to putting design discussion — why a change was made, what
alternatives were considered, what trade-off was accepted — in the pull
request that makes the change, not in a checked-in document. A PR is read by
someone evaluating that specific change; a file in the repo is read by
everyone, forever, and has to be kept in sync with the code or it goes stale
and misleads instead of informs.

**Exception:** guidance that will keep steering *future* work belongs in the
repo, but only once it's abstracted away from the specific change that
prompted it — stated as a general rule, not a record of one decision.
`docs/skill-authoring.md` is the model: it states a principle any skill
author needs ("bake in curated guidance, don't fetch it at runtime") without
narrating the specific case that motivated it.

If a piece of guidance can't be stated without referencing removed code, a
specific past PR, or "the previous approach," it isn't abstracted enough to
check in — put it in the PR instead.

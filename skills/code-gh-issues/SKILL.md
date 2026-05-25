Check this repo for a CONTEXT.md file and a docs folder. Read all files in the docs folder and the CONTEXT.md file.
Then, use the `gh` CLI to list all open issues. Go through each issue one-by-one and launch a worker-validator pair to work
the issue. The worker should use test-driven development (TDD) to solve the issue, and the validator should review the 
worker's code. After each validator approves the code, you should commit the code, push it to the repo, and close the issue. 
If the validator does not approve the code, you should spawn a new worker to try again. Limit the number of attempts to 3. 
If after 3 attempts the issue is not resolved, you should comment on the issue and escalate it to a human. Use the gh issue
for tracking, commenting, and closing issues. Use git for committing and pushing code. Make sure to follow best practices 
for commit messages and code reviews.

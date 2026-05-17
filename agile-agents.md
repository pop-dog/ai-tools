References:
~/.claude/skills/grill-me
~/.claude/skills/to-prd
~/.claude/skills/to-issues

Three layers:
* Stakeholder
* Orchestrator
* Worker + Validator

The core idea: three layers are *adversarial*. The **Stakeholder** agent
helps the user create the design using /grill-me and creates a PLAN.md
using a new /to-plan skill (based on to-prd). The PLAN has
* deliverables (one or more)
  * user stories (one or more per deliverable)
    * requirements (one or more per user story)
    * technical decisions (from the /grill-me session, optional)

The **stakeholder** spawns an **orchestrator** agent, which reads the PLAN.md
and executes a /to-kanban (based on to-issues) skill. This generates a KANBAN.md
file. This skill breaks up the PLAN into coding tasks.

One-by-one, the **stakeholder** assigns the tasks and sends them to a worker-validator pair.
The **worker** codes a task (using test-driven development) and the **validator** reviews
the task.

Adversarial relationships:
* worker <-> validator
* orchestrator <-> worker+validator
* stakeholder <-> orchestrator

These define how agents check each other's work.

**worker** must use test-driven development (TDD).
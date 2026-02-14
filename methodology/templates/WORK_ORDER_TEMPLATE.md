# Template: Work Order Dispatch

Copy this template for each task you assign to an LLM agent. Fill in every section. If a section doesn't apply, write "N/A" — don't delete it, because the next person to use this template needs to see all sections.

See: [Dispatch Self-Containment Pattern](../patterns/DISPATCH_SELF_CONTAINMENT.md)

---

```markdown
# [WO-ID]: [Short Title]

**Assigned to:** [Agent type/session — e.g., "Builder (Sonnet)", "Verifier (Opus)"]
**Date:** [YYYY-MM-DD]
**Priority:** [HIGH | MEDIUM | LOW]
**Status:** [DRAFT | DISPATCHED | IN PROGRESS | COMPLETE]

---

## Context

[Why this work exists. What problem it solves. What happened that made this necessary. 2-4 sentences. The agent reading this has zero prior context — explain as if they've never seen the project before.]

## Task

[Exactly what to do. Be specific and concrete. If there are multiple steps, number them. Each step should be independently verifiable.]

1. [First step]
2. [Second step]
3. [Third step]

## Files to Modify

[Explicit file paths. Include line numbers if targeting specific code. If lines may have shifted, include surrounding context (function name, nearby code) so the agent can locate the right spot.]

- `path/to/file.py` (lines XX-YY, function `function_name`)
- `path/to/other_file.py` (constant `CONSTANT_NAME`)

## Required Reading

[Files the agent MUST read before starting work. Include governance docs if relevant.]

- `DEVELOPMENT_GUIDELINES.md` — Section [N] ([topic])
- `path/to/design_decision.md` — [why this is relevant]

## Verification

[How to confirm the work is correct. Prefer machine-verifiable criteria.]

- Run: `[test command]`
- Expected: [what passing looks like]
- Write new test: `test_[description]()` in `tests/test_[module].py`

## Scope Boundaries

[What NOT to do. Adjacent work that belongs to other work orders. Files the agent must not modify.]

- Do NOT modify `[file]` — that belongs to [WO-ID]
- Do NOT change [thing] — only change [other thing]
- Do NOT refactor surrounding code — fix only what's specified

## Dependencies

[Other work orders that must complete before this one can start. If none, write "None."]

- DEPENDS-ON: [WO-ID] ([reason])
- Or: None — this WO is independently executable.

## What NOT to Do

[Common mistakes an agent might make on this task. Specific to this WO.]

- Do not [common mistake 1]
- Do not [common mistake 2]
```

---

## Usage Notes

- **One task per dispatch.** Don't combine unrelated work. If two changes are in different files for different reasons, they're two WOs.
- **Be redundant.** Repeat important constraints in both "Task" and "Scope Boundaries." Agents skim, and the constraint they miss is the one that causes a revert.
- **Verify line numbers before dispatching.** Code changes between when you write the WO and when the agent reads it. Include function names and surrounding context as anchors.
- **The "What NOT to Do" section prevents 80% of reverts.** Agents are eager to help. They'll "improve" adjacent code, refactor for clarity, add error handling you didn't ask for. Explicit prohibitions are more effective than implicit scope.

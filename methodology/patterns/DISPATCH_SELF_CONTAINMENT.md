# Pattern: Dispatch Self-Containment

## Problem

When you assign a task to an LLM agent, the agent has no memory of previous sessions. If the work order says "continue the refactoring from last session" or "fix the bug we discussed," the agent has no idea what you're talking about. It will either hallucinate context or ask questions that waste your time.

More subtly: even when work orders look complete, they often contain implicit dependencies — references to decisions made in conversation, file locations that changed since the dispatch was written, or context that "everyone knows" but the new agent doesn't.

## Solution

Every work order must be **self-contained**: executable by an agent with zero prior context. The dispatch file plus the files it explicitly references must contain everything needed to complete the task.

### The Self-Containment Test

Before dispatching a work order, ask:

> Could a brand-new agent — with no conversation history, no memory of previous sessions, and no context beyond what's in this file — execute this dispatch using only this file and the files it references?

If the answer is no, the dispatch is incomplete. Add the missing context.

### What Self-Contained Looks Like

```markdown
# Work Order: Fix Minimum Damage Floor

## Context
The attack resolver (`aidm/core/attack_resolver.py`) uses `max(0, damage)`
to prevent negative damage values. The rule source (PHB p.141) specifies
that minimum damage is 1, not 0. This affects lines 142 and 167.

## Task
Change `max(0, damage)` to `max(1, damage)` at both locations.

## Files to Modify
- `aidm/core/attack_resolver.py` (lines 142, 167)

## Files to Read First
- `DEVELOPMENT_GUIDELINES.md` Section 6 (resolver mutation rules)

## Verification
- Run: `python -m pytest tests/test_attack_resolver.py -v`
- Expected: all tests pass
- Write new test: `test_minimum_damage_is_one()`

## What NOT to Do
- Do not modify full_attack_resolver.py (separate work order)
- Do not change the damage calculation formula, only the floor clamp
```

### What Non-Self-Contained Looks Like

```markdown
# Work Order: Fix the damage bug

Fix the issue we found during verification.
You know which file — the one with the min/max problem.
Make sure it matches the SRD.
```

This will fail. The agent doesn't know which bug, which file, which SRD reference, or what "matches" means in this context.

## Implementation

### Dispatch Checklist

Before sending any work order to an agent, verify:

- [ ] **Context section** explains why this change is needed (not just what)
- [ ] **File paths** are explicit and current (not "the usual file")
- [ ] **Line numbers** are verified against current code (not stale from a prior commit)
- [ ] **Referenced documents** are listed with their paths
- [ ] **Acceptance criteria** are machine-verifiable (test commands, expected output)
- [ ] **Scope boundaries** are explicit (what NOT to touch)
- [ ] **No implicit knowledge** required — no "as we discussed," no "you know the one"

### Dispatch Template

```markdown
# [WO-ID]: [Short Title]

## Context
[Why this work exists. What problem it solves. 2-3 sentences.]

## Task
[Exactly what to do. Specific, concrete, unambiguous.]

## Files to Modify
[Explicit paths, with line numbers if applicable]

## Files to Read First
[Governance docs, related code, design decisions — with paths]

## Verification
[Commands to run, expected output, tests to write]

## Scope Boundaries
[What NOT to do. Adjacent work that belongs to other work orders.]

## Dependencies
[Other WOs that must complete first, if any. Otherwise: "None."]
```

## When to Use

- Every time you assign work to an LLM agent
- Even when "it should be obvious" — it isn't, because the agent has no context
- Especially for parallel dispatches where multiple agents work simultaneously

## Real Example

The proving-ground project dispatched 13 fix work orders covering 30 bugs across 15 files. Each WO was ~500 tokens and independently executable. Seven groups of agents ran in parallel without coordination, because each dispatch was self-contained. No agent needed to know what the other agents were doing.

The contrast: earlier in the project, work orders were written conversationally ("fix the cover values, you know the ones from the verification"). These required follow-up questions, produced incorrect fixes, and wasted entire context windows.

## Anti-Patterns

- **"Continue from where we left off."** The agent doesn't know where "we" left off. Write a new dispatch that stands alone.
- **"See the discussion in the previous session."** Sessions don't carry over. Extract the relevant decisions into the dispatch.
- **"Fix all the bugs."** Without specific bug IDs, file paths, and expected behavior, this produces guesswork. One dispatch per coherent task.
- **Assuming line numbers are still correct.** Code changes between when the dispatch was written and when the agent reads it. Include enough context (function names, surrounding code) that the agent can find the right location even if lines shifted.

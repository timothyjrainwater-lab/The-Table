# Pattern: Artifact Primacy

## Problem

LLM agents have perfect recall within a single context window. This creates a dangerous illusion: during a session, the agent remembers everything you discussed, every decision you made, every nuance you agreed on. It feels like the agent "knows" the project.

Then the context window closes. The next agent knows nothing.

Every decision, rationale, status update, and design choice that existed only in conversation is gone. The next agent will re-derive some of them, miss others, and contradict the rest. Over 3-4 context rotations, the project's actual state and the agents' understanding of it diverge by 30-40%.

## Solution

**If it's not in a file, it doesn't exist.**

Any fact that must survive a context boundary must be written to a versioned file in the repository. Conversational knowledge not pinned to an artifact is assumed lost at the next context rotation.

### What Must Be Pinned

| Knowledge Type | Example | Pin To |
|---------------|---------|--------|
| Design decisions | "We chose approach B because X" | Decision log or design doc |
| Status changes | "Bug-10 reclassified from WRONG to AMBIGUOUS" | Verification file + master list |
| Scope boundaries | "Don't touch the spell system until gate opens" | Tech debt register or state doc |
| Discovered pitfalls | "Never use bare strings for field access" | Development guidelines |
| Mid-session findings | "Found 4 unverified formulas in helper functions" | Session memo to PM inbox |
| Uncommitted work | "Edited file X but didn't commit because Y" | Handoff document |

### What Can Stay Conversational

- Brainstorming that hasn't reached a decision
- Questions you're still thinking about
- Opinions about approach quality (until they become decisions)
- Status updates that are also reflected in files

## Implementation

### The Handoff Checklist

Before a session ends or approaches context limits, verify:

- [ ] State summaries updated (checklists, master lists, logs)
- [ ] Memo written if strategic findings emerged
- [ ] Any mid-session reclassifications reflected in ALL affected files
- [ ] Uncommitted work documented in a handoff file
- [ ] No implicit knowledge required — next agent can work from artifacts alone

### The Consistency Gate

When a status, count, verdict, or classification changes, update **all** files that reference it in the same commit. Partial updates are worse than no update — they create contradictions that the next agent can't resolve without re-reading source files.

**Example failure:** Session A updated the verification checklist and the bug master list, but missed the domain-specific verification file. Session B read the domain file, saw different numbers than the checklist, and couldn't determine which was correct. A third session was needed just to reconcile.

### The Handoff Document

When a session ends with incomplete work, write a handoff file:

```markdown
# Handoff: [Short Description]

**From:** [Agent ID]
**Date:** [YYYY-MM-DD]
**Status:** Ready to execute

## Uncommitted Work
[What was changed but not committed, and why]

## Completed This Session
[What was done and committed]

## Next Steps
[Exactly what the next agent should do, in order]

## Files to Read Before Executing
[List of files the next agent needs for context]
```

## When to Use

- Always. This is not optional for multi-agent projects.
- The question is never "should I pin this?" but "is there anything I forgot to pin?"
- Err on the side of over-documenting. A file that captures an obvious decision costs less than a session spent re-deriving a non-obvious one.

## Real Example

The proving-ground project discovered this pattern the hard way. A verification session reclassified 4 bug verdicts from WRONG to AMBIGUOUS based on research cross-references. The reclassifications were discussed in conversation and partially reflected in files — the checklist was updated, but two domain-specific files weren't. The next session saw conflicting numbers, spent half its context window investigating the inconsistency, and ultimately required a third session to write the fix.

After implementing artifact primacy with the handoff checklist, zero reclassification inconsistencies occurred in subsequent sessions.

## Anti-Patterns

- **"The next agent will figure it out."** No, they won't. They'll figure out *something*, and it probably won't match what you intended.
- **"I'll remember to mention it."** You won't be there. The operator may not remember either, or may not know it's important.
- **"It's obvious from the code."** Code shows *what* was done, not *why*. Decisions, tradeoffs, and rejected alternatives exist only in conversation unless pinned.
- **"We already discussed this."** With a different agent, in a different context window, that no longer exists. Pin it or lose it.

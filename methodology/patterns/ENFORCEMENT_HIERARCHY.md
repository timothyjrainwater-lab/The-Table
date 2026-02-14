# Pattern: Enforcement Hierarchy

## Problem

You discover a mistake. You write a rule to prevent it. You add the rule to the development guidelines. The next agent makes the same mistake. You add it to the onboarding checklist too. The agent after that still makes the mistake.

Rules written in prose don't stick. New agents read them, acknowledge them, and then violate them because the rule isn't enforced at the point where the violation happens.

## Solution

Recognize that enforcement has three tiers with dramatically different stickiness. When you discover a new rule, consciously choose which tier to enforce it at — and understand that lower tiers will have higher violation rates.

### Tier 1: Test-Enforced (Stickiest)

The rule is checked by an automated test. If an agent violates it, the test suite fails, and the agent must fix it before completing their work.

**Stickiness:** ~100%. Agents can't miss a failing test.

**Examples:**
- Boundary law BL-017: No `uuid.uuid4()` in default_factory → tested in `test_boundary_law.py`
- Boundary law BL-020: No WorldState mutation outside engine → tested
- Test runtime invariant: full suite < 120 seconds → enforced by CI

**When to use:** For rules that are mechanically checkable and where violations cause significant damage. The rule must be expressible as "does this code pattern exist? → fail."

**Cost:** Writing and maintaining the test. Some rules are hard to test (e.g., "use correct D&D edition terminology" is hard to check mechanically).

### Tier 2: Process-Enforced (Medium)

The rule is embedded in a process step that agents follow. Not automated, but positioned at a point where the agent naturally encounters it.

**Stickiness:** ~70-80%. Most agents follow the process; some skip steps under pressure or when they think the step doesn't apply.

**Examples:**
- Onboarding checklist: "Read governance docs in this order" → positioned as Step 1
- Work order template: "Scope Boundaries" section → positioned where the agent reads their task
- Builder debrief: "Write debrief before closing session" → positioned as last step in WO

**When to use:** For rules that can't be mechanically tested but can be positioned at a natural checkpoint. The rule should appear at the point where the agent makes the relevant decision.

**Cost:** Adding a step to a template or checklist. Risk: agents optimize for speed and skip steps they judge as unnecessary.

### Tier 3: Prose-Enforced (Weakest)

The rule is documented in a guidelines file. Agents are told to read it. Compliance depends on reading comprehension and memory.

**Stickiness:** ~40-60%. Agents read the rule, understand it in the moment, and then forget it when solving a different problem 10 minutes later.

**Examples:**
- "Don't use 5e terminology" → documented in dev guidelines Section 7
- "Don't use bare string literals for entity fields" → documented in Section 1
- "Conditions are stored as dicts, not lists" → documented in Section 9

**When to use:** For rules that can't be tested or positioned at a checkpoint. This is the catch-all tier. Expect violations and plan for them.

**Cost:** Minimal to write. High in violations. Each violation costs a context window to discover, diagnose, and fix.

## Promoting Rules Between Tiers

When a prose rule (Tier 3) gets violated repeatedly, **promote it** to a higher tier:

```
Tier 3 (prose rule)
  → First violation: add to "DO NOT" list in onboarding checklist (still Tier 3, but more prominent)
  → Second violation: add to work order template as explicit prohibition (Tier 2)
  → Third violation: write an automated test that catches it (Tier 1)
```

Not every rule needs to be Tier 1. The cost of writing tests for every guideline is prohibitive. But rules that agents violate repeatedly are worth the investment in a test.

### Signals That a Rule Needs Promotion

- Same rule violated in 2+ different sessions
- Violation causes significant rework (context window wasted on fixing)
- Rule is frequently "rediscovered" by agents during work
- Rule violations cascade into other problems

## Implementation

### Audit Your Current Rules

| Rule | Current Tier | Violation Count | Should Promote? |
|------|-------------|-----------------|-----------------|
| [Rule 1] | Tier 3 (prose) | 3 | Yes → Tier 1 test |
| [Rule 2] | Tier 2 (process) | 0 | No |
| [Rule 3] | Tier 3 (prose) | 1 | Not yet |

### When Adding a New Rule

1. Write the rule as prose (Tier 3) immediately — don't wait for the perfect enforcement
2. Assess: is this mechanically testable? If yes, write the test (Tier 1) now
3. If not testable: can it be positioned at a checkpoint? Add to template/checklist (Tier 2)
4. Track violations. Promote on repeated failure.

## Real Example

The proving-ground project started with "use `EF.*` constants for entity fields" as prose in the development guidelines (Tier 3). An agent violated it, causing a silent bug where HP clamping never triggered (used `"current_hp"` instead of `EF.HP_CURRENT`). The rule was then promoted:
- Added to "DO NOT" list in onboarding checklist (still Tier 3, more prominent)
- Added to Common Pitfalls Checklist at the end of the guidelines (Tier 2 — agents check it before submitting)
- Boundary law BL-020 partially covers this pattern by preventing state mutation outside the engine (Tier 1)

After promotion, zero recurrences.

## Anti-Patterns

- **Assuming prose is sufficient.** It isn't. New agents skim. Rules that matter need enforcement above Tier 3.
- **Testing everything.** Test maintenance is a cost. Reserve Tier 1 for rules that cause real damage on violation.
- **Not tracking violations.** Without violation data, you can't know which rules need promotion. Even informal tracking ("this happened twice") is better than nothing.
- **Blaming the agent for not reading the docs.** The agent read them. Reading isn't the problem — retention during task execution is. If you need the rule to stick, enforce it at the point of violation, not the point of reading.

# Agent Communication Protocol

**Version:** 1.0
**Date:** 2026-02-08
**Status:** ✅ CANONICAL (Binding Communication Standard)
**Authority:** Project Governance
**Precedence:** READ THIS FIRST — This protocol governs ALL agent communication on this project

---

## ⚠️ MANDATORY FIRST READ FOR ALL AGENTS

**If you are an AI agent (Claude, ChatGPT, or other) working on this project:**

1. **READ THIS DOCUMENT COMPLETELY** before taking any action
2. **This protocol is BINDING** — it defines how you must communicate concerns, ambiguities, and decisions
3. **Violation consequences:** Code reverts, manifest updates, scope reductions
4. **Key principle:** Speak first, build second. Silence is not consent.

---

## Purpose

This document establishes **mandatory communication standards** for all agents (human and AI) working on the AIDM project.

**Core Principle:**
> Agents MUST communicate all concerns, edge cases, ambiguities, and potential violations **before** proceeding with implementation.

Silence is not consent. Assumptions are not approval. **Speak first, build second.**

---

## Mandatory Communication Categories

### 1. Gate Violations (CRITICAL — STOP IMMEDIATELY)

**When to raise:**
- Any proposed feature/spell/mechanic requires a CLOSED capability gate
- Uncertainty whether a feature crosses a gate boundary
- Discovery of gate violation in existing code

**Required communication:**
1. **STOP all implementation work immediately**
2. State the suspected gate violation explicitly
3. Reference the blocking gate ID (e.g., G-T3A)
4. Reference the blocking kernel (e.g., SKR-001)
5. Propose removal or alternative approach
6. **DO NOT PROCEED** until explicit approval received

**Example:**
```
GATE VIOLATION DETECTED:

Spell: Enlarge Person (PHB 226)
Suspected violation: G-T3D (Transformation History)
Reason: Size changes (Medium → Large) may require form stacking if nested with other size effects
Blocking kernel: SKR-010 (Transformation History Kernel)

PROPOSAL:
1. Remove Enlarge/Reduce Person from manifest, OR
2. Implement with explicit limitation: "No nested size changes, CP-16 temporary modifier only"

AWAITING APPROVAL BEFORE PROCEEDING.
```

---

### 2. Architectural Ambiguities (HIGH PRIORITY — CLARIFY BEFORE CODE)

**When to raise:**
- Multiple valid implementation approaches exist
- Uncertain which existing system to integrate with
- Unclear whether new schema/event types required
- Potential conflicts with existing kernels (CP-09 through CP-17)

**Required communication:**
1. Describe the ambiguity clearly
2. List all viable approaches (minimum 2)
3. State pros/cons of each approach
4. Recommend preferred approach with rationale
5. **Wait for approval** before implementing

**Example:**
```
ARCHITECTURAL AMBIGUITY:

Feature: Mirror Image (PHB 254)
Question: How to represent 1d4+1 images?

APPROACH A: New entity state (image_count: int)
- Pro: Simple, minimal schema change
- Con: Doesn't track individual image destruction

APPROACH B: Relational condition (images tied to caster)
- Pro: Each image tracked separately
- Con: May require G-T3C (Relational Conditions) — GATE VIOLATION

APPROACH C: Simple concealment bonus (20% miss chance)
- Pro: No new schema, uses existing CP-16
- Con: Not faithful to PHB (images should be destroyed on hit)

RECOMMENDATION: Approach C (degraded implementation) OR defer to post-SKR-005

AWAITING DECISION.
```

---

### 3. Edge Cases & Interaction Hazards (MEDIUM PRIORITY — DOCUMENT BEFORE MERGE)

**When to raise:**
- Spell interactions that weren't in original audit
- Unusual mechanical combinations (e.g., Haste + Enlarge Person)
- Potential non-determinism sources
- RNG consumption ordering questions

**Required communication:**
1. Describe the edge case
2. State why it's a concern (determinism, complexity, gate boundary)
3. Propose handling approach
4. Document in design doc or decisions file

**Example:**
```
EDGE CASE IDENTIFIED:

Interaction: Haste + Slow on same target
Question: Do they cancel out, or does later spell override?

PHB Reference: PHB 239 (Haste), PHB 280 (Slow)
Concern: Spell stacking rules ambiguous for opposing effects

PROPOSED HANDLING:
- Later spell overrides (most recent wins)
- Document in CP-18A decisions file
- Add integration test: test_haste_slow_cancellation()

DOCUMENTING IN CP18A_DECISIONS.md BEFORE MERGE.
```

---

### 4. Scope Creep Alerts (MEDIUM PRIORITY — FLAG BEFORE EXPANSION)

**When to raise:**
- Request to add feature beyond current manifest
- Suggestion to implement "just a few more" spells
- Proposal to enhance existing kernel without design doc
- Attempt to add "nice to have" features

**Required communication:**
1. Flag the scope expansion explicitly
2. Reference original scope boundary (manifest, action plan, DR-001)
3. State impact (schema changes, test count, runtime)
4. Require explicit approval via decision record

**Example:**
```
SCOPE CREEP ALERT:

Request: Add Invisibility Sphere (PHB 245) to manifest
Current manifest: Invisibility not included
Scope boundary: CP-18A-SPELL-TIER-MANIFEST.md (80 spells, approved)

IMPACT:
- Requires area-effect invisibility mechanics (not in current schema)
- May need new event type: area_invisibility_applied
- Estimated +5 tests, +0.05s runtime

RECOMMENDATION:
- Defer to Phase 1B manifest expansion (before schema design), OR
- Require manifest update + re-approval before implementation

SCOPE EXPANSION REQUIRES EXPLICIT APPROVAL.
```

---

### 5. Test/Performance Concerns (LOW PRIORITY — FLAG EARLY)

**When to raise:**
- Test suite approaching 2-second limit
- Test count explosion (100+ tests for single spell)
- Determinism concerns in replay tests
- RNG stream isolation violations

**Required communication:**
1. State the performance/test concern
2. Provide current metrics (test count, runtime)
3. Project impact of current work
4. Propose mitigation if needed

**Example:**
```
PERFORMANCE CONCERN:

Current state: 538 tests, ~1.65s runtime
CP-18A projection: +200 tests (80 spells × ~2.5 tests each)
Projected runtime: ~2.8s (EXCEEDS 2-second limit)

MITIGATION OPTIONS:
1. Optimize existing tests (reduce redundancy)
2. Implement spell tests more efficiently (fewer edge cases per spell)
3. Split test suite (unit vs integration)

FLAGGING EARLY — WILL REQUIRE OPTIMIZATION DURING IMPLEMENTATION.
```

---

## Communication Format Standards

### Required Elements (All Communications)

1. **Category Header** (Gate Violation / Ambiguity / Edge Case / Scope Creep / Performance)
2. **Clear Description** (what is the issue?)
3. **Context/References** (PHB page, gate ID, kernel ID, manifest section)
4. **Impact Assessment** (what breaks if we proceed?)
5. **Proposed Action** (what should we do?)
6. **Approval Request** (explicit statement that approval is needed)

### Forbidden Patterns

❌ **Silent Assumptions:**
- "I assumed Enlarge Person was safe because it's in the manifest"
- CORRECT: "Enlarge Person may violate G-T3D, flagging for review"

❌ **Optimistic Proceeding:**
- "I'll implement it and we can remove it later if it's wrong"
- CORRECT: "Flagging concern now, awaiting approval before implementation"

❌ **Vague Concerns:**
- "This seems complicated"
- CORRECT: "Mirror Image requires image state tracking, which may need SKR-005 (Relational Conditions)"

❌ **Buried Concerns:**
- Mentioning issue in passing, then proceeding anyway
- CORRECT: Use STOP/FLAG headers, require explicit approval

---

## Approval Protocols

### Gate Violations
- **Approval Required From:** Project authority (human decision-maker)
- **Response Time:** BLOCKING (halt all work until resolved)
- **Resolution:** Remove feature, defer to kernel, or explicit DR-XXX override

### Architectural Ambiguities
- **Approval Required From:** Project authority or senior agent
- **Response Time:** HIGH priority (resolve before schema/code)
- **Resolution:** Choose approach, document in design doc

### Edge Cases
- **Approval Required From:** Can self-approve if low-risk
- **Documentation Required:** MUST document in decisions file
- **Review:** Flag in PR for human review

### Scope Creep
- **Approval Required From:** Project authority
- **Response Time:** MEDIUM priority (can continue other work)
- **Resolution:** Explicit approval required to expand scope

---

## Enforcement

### For AI Agents
- **Mandatory proactive flagging** of all concerns in above categories
- No implementation of flagged features until approval received
- Document all decisions in appropriate files (decisions, manifest, design docs)

### For Human Decision-Makers
- **Explicit approval required** for gate violations, ambiguities, scope expansions
- Response to flagged concerns expected within reasonable timeframe
- Silence is NOT approval (agent must wait for explicit "proceed")

### Violation Consequences
- **Code with unflagged gate violations:** Immediate revert
- **Silent assumptions that break gates:** Revert + manifest update
- **Scope creep without approval:** Revert to approved scope

---

## Examples of Correct Communication

### Example 1: Gate Violation (Agent → Human)

```
GATE VIOLATION DETECTED — HALTING WORK

Spell: Enlarge Person (PHB 226)
Issue: Size category change (Medium → Large) may require transformation history stack
Suspected Gate: G-T3D (Transformation History — CLOSED)
Blocking Kernel: SKR-010

EVIDENCE:
- PHB 226: "target's size increases by one category"
- Size changes affect: reach, grapple, Hide, weapon damage, carrying capacity
- If Enlarged, then Reduced → form stacking question (Polymorph-like)

ACTION REQUIRED:
1. Remove Enlarge/Reduce Person from manifest, OR
2. Implement degraded version (CP-16 temporary STR/DEX only, no actual size change), OR
3. Produce DR-002 documenting why size changes don't need SKR-010

AWAITING EXPLICIT APPROVAL BEFORE PROCEEDING WITH ANY OPTION.
```

**Human Response:**
"Approved: Option 2 (degraded implementation). Enlarge/Reduce Person = CP-16 temporary ability modifiers only. Add note to manifest. Document limitation in CP18A_DECISIONS.md."

---

### Example 2: Architectural Ambiguity (Agent → Human)

```
ARCHITECTURAL AMBIGUITY — SCHEMA DESIGN DECISION REQUIRED

Feature: Spell slot tracking (prepared vs spontaneous casting)
Question: Where to store spell slots?

OPTION A: Entity state (entities[caster_id]["spell_slots"])
- Pro: Simple, follows existing pattern
- Con: Not bundle-friendly (prep-time vs runtime)

OPTION B: SessionBundle (bundle["spell_slots_by_caster"])
- Pro: Prep-time friendly, validates at bundle load
- Con: Requires bundle schema extension

OPTION C: Hybrid (prep in bundle, runtime in entity state)
- Pro: Best of both (prep validation + runtime mutation)
- Con: More complex, two sources of truth

RECOMMENDATION: Option C (hybrid)
- Prep: SessionBundle defines max slots per caster
- Runtime: Entity state tracks current slots (consumed/available)
- Events: spell_slot_consumed, spell_slot_restored

AWAITING DECISION BEFORE SCHEMA DESIGN.
```

**Human Response:**
"Approved: Option C (hybrid). Proceed with schema design. Document in CP18A_SCHEMA_DESIGN.md."

---

### Example 3: Self-Approved Edge Case (Agent Documentation)

```
EDGE CASE DOCUMENTED (Self-Approved Low-Risk)

Interaction: Magic Missile + Shield
PHB 251 (Magic Missile): auto-hit force damage
PHB 278 (Shield): negates Magic Missile

Handling:
- Shield condition checked before Magic Missile damage applied
- If shield active → damage_negated event, no hp_changed
- Test: test_magic_missile_vs_shield()

DOCUMENTED IN: docs/CP18A_DECISIONS.md
SELF-APPROVED: Low risk, clear PHB ruling, deterministic
FLAGGED FOR REVIEW: In PR
```

---

## Integration with Existing Governance

This protocol supplements:
- [AIDM_PROJECT_ACTION_PLAN_V2.md](docs/AIDM_PROJECT_ACTION_PLAN_V2.md) — Capability gates, kernel requirements
- [PROJECT_COHERENCE_DOCTRINE.md](PROJECT_COHERENCE_DOCTRINE.md) — Fail-closed design, event sourcing
- [CP-18A-SPELL-TIER-MANIFEST.md](docs/CP-18A-SPELL-TIER-MANIFEST.md) — Spell scope boundary (current work)

**Conflict Resolution:**
If this protocol conflicts with other governance docs, the **most restrictive** interpretation wins (fail-closed).

---

## Multi-Agent Collaboration Charter

This project may involve multiple AI agents (Claude, ChatGPT, etc.) collaborating simultaneously.

**Shared Principles:**
1. **Different strengths are intentional** — Some agents explore, some constrain, neither role is superior
2. **Disagreement is signal, not conflict** — Pushback is load-bearing analysis, not veto
3. **Exploration vs Convergence phases** — Agents must be conscious of which phase they're in
4. **Project owner controls pacing** — Owner says "explore more" or "decide now"

**Phase A — Exploration:**
- "Maybe" is allowed
- Loose edges are acceptable
- Multiple interpretations may coexist
- Goal: surface area, not correctness

**Phase B — Convergence:**
- "Maybe" is dangerous
- Assumptions must be explicit
- Ambiguity must collapse into decisions
- Goal: commitment and clarity

**Rule:** If the phase is unclear, agents should ask or hold, not assume.

**Pushback Protocol:**
When challenging an idea, clarify:
- What assumption might break
- Where the uncertainty actually lives
- What would need to be true for this to work safely

Pushback is NOT a demand to stop or claim of authority.

**Owner Intervention:**
Simple statements override all dynamics:
- "I want more exploration here."
- "I want a hard decision now."
- "Pause—something feels misaligned."

**Failure Modes (Self-Correct):**
- Over-formalization that kills momentum
- Premature convergence disguised as "clarity"
- Endless exploration with no intent to land
- Forcing owner to resolve avoidable misunderstandings

**Enforcement:** Pause → clarify intent → resume (not escalation)

---

## Revision History

- **2026-02-08 v1.0:** Initial protocol creation
  - Defined 5 communication categories (gate violations, ambiguities, edge cases, scope creep, performance)
  - Established approval protocols
  - Provided examples of correct communication

---

**END OF AGENT COMMUNICATION PROTOCOL**

**Status:** ✅ CANONICAL (Binding for all agents)
**Enforcement:** Immediate (effective now)

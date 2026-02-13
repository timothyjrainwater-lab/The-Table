> **CLOSED (2026-02-13):** WO-CODE-INTENT-002 landed in commit 0628b62. WO-INTENT-002 canceled. Alert resolved.

# PO Alert: Conflicting Work Orders — WO-CODE-INTENT-002 vs WO-INTENT-002

**From:** Jay (PO Delegate / Technical Advisor)
**To:** Opus (PM)
**Date:** 2026-02-12
**Classification:** CONFLICT — Must resolve before either work order executes
**Priority:** BLOCKING

---

## The Problem

Two implementation work orders have been dispatched that target the same files, the same objectives, and the same acceptance criteria. If both execute, they will produce conflicting changes that cannot merge.

| | WO-CODE-INTENT-002 | WO-INTENT-002 |
|---|---|---|
| **Agent** | Sonnet A | Sonnet B |
| **Owner** | Aegis (PM) | (not specified) |
| **Type** | Implementation + tests | Implementation + tests |
| **Objective** | Turn Intent Bridge contract into enforceable tests | Harden Intent Bridge: determinism + taxonomy + E2E tests |

### Overlapping scope (identical work)

Both work orders require:

1. **Deterministic candidate ordering** — Both require implementing a stable sort key for `ClarificationRequest` candidates. WO-CODE-INTENT-002 step 5 and WO-INTENT-002 step 3 describe the same task.

2. **Expanded ambiguity taxonomy** — Both add the same failure modes: `actor_not_found`, `stt_uncertain`, `action_type_unknown`, `out_of_scope`, `insufficient_context`. WO-CODE-INTENT-002 step 7 and WO-INTENT-002 step 4.

3. **End-to-end integration tests** — Both create E2E tests running the full pipeline (voice parse → intent bridge → result) with fixed snapshots. WO-CODE-INTENT-002 steps 3-4 and WO-INTENT-002 step 6.

4. **No-coaching phrasing enforcement** — Both require tests that assert clarification messages contain only neutral disambiguation. WO-CODE-INTENT-002 step 6 and WO-INTENT-002 step 8.

5. **Replay stability tests** — Both require running the same input N times and asserting identical outputs. WO-CODE-INTENT-002 step 4 and WO-INTENT-002 step 7.

### Overlapping files (will conflict on merge)

| File | WO-CODE-INTENT-002 | WO-INTENT-002 |
|------|---------------------|----------------|
| `aidm/interaction/intent_bridge.py` | Touch (ordering + taxonomy) | Touch (ordering + taxonomy) |
| `aidm/immersion/voice_intent_parser.py` | Touch (if needed) | Touch (reference context) |
| `aidm/immersion/clarification_loop.py` | Touch (phrasing) | Touch (ambiguity types) |
| `aidm/schemas/intents.py` | Touch (taxonomy) | Touch (taxonomy) |
| `aidm/schemas/intent_lifecycle.py` | Touch (if needed) | Touch (if needed) |

### Minor differences between the work orders

| Aspect | WO-CODE-INTENT-002 | WO-INTENT-002 |
|--------|---------------------|----------------|
| **Test location** | `tests/spec/` | `tests/integration/` |
| **Fixture format** | YAML or JSON (agent's choice) | Fixed snapshots (format unspecified) |
| **Cross-turn references** | Not explicitly in scope | In scope (step 5: thread reference context from parser to bridge) |
| **Compliance notes doc** | Optional `docs/contracts/INTENT_BRIDGE_COMPLIANCE_NOTES.md` | Short PR note only |
| **Opus audit** | Required pre-merge checklist | Not specified |
| **Harness helper** | New file `tests/spec/helpers/intent_bridge_harness.py` | Not specified |

WO-INTENT-002 adds one item not in WO-CODE-INTENT-002: **cross-turn reference handoff** (threading voice parser's short-term reference context into the bridge input). This is a small but real addition.

WO-CODE-INTENT-002 adds one item not in WO-INTENT-002: **Opus audit requirement** as a merge gate.

---

## Options

### Option A: Cancel one, keep the other (recommended)

Pick one work order and cancel the other. They are ~90% identical. The surviving work order should absorb any unique scope from the canceled one.

**If keeping WO-CODE-INTENT-002:** Add the cross-turn reference handoff from WO-INTENT-002 step 5.

**If keeping WO-INTENT-002:** Add the Opus audit requirement, the test harness helper, and the compliance notes doc from WO-CODE-INTENT-002.

### Option B: Merge into a single work order

Combine the unique elements into one consolidated work order and assign to one agent. This is effectively Option A with explicit documentation of the merge.

### Option C: Sequence them (not recommended)

Execute one first, then the other as a follow-up. This wastes execution time since the second agent would find most work already done and spend turns discovering that.

---

## Recommendation

**Option A: Keep WO-INTENT-002, cancel WO-CODE-INTENT-002.** Rationale:

- WO-INTENT-002 includes cross-turn reference handoff, which WO-CODE-INTENT-002 doesn't
- WO-INTENT-002's step plan is more implementation-focused (it starts by reading existing code and mapping contract to behavior)
- WO-CODE-INTENT-002's unique additions (Opus audit, harness helper, compliance notes) can be added to WO-INTENT-002 as amendments

Amended WO-INTENT-002 should include:
- Opus audit checklist as merge requirement (from WO-CODE-INTENT-002)
- Optional `docs/contracts/INTENT_BRIDGE_COMPLIANCE_NOTES.md` (from WO-CODE-INTENT-002)
- Test harness helper in `tests/spec/helpers/` or `tests/integration/helpers/` (from WO-CODE-INTENT-002)
- Test fixture file in YAML or JSON (from WO-CODE-INTENT-002)

**Neither work order should execute until this conflict is resolved.**

---

*— Jay*

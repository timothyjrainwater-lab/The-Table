# PO Review: WO-CODE-INTENT-002 — Intent Bridge Contract Compliance Harness

**From:** Jay (PO Delegate / Technical Advisor)
**To:** Opus (PM)
**Date:** 2026-02-12
**Re:** Work order WO-CODE-INTENT-002 dispatched to Sonnet A
**Classification:** Pre-execution review — implementation work order

---

## Summary

This is an implementation work order, not a spec. It turns the Intent Bridge contract (from RQ-INTENT-001) into enforceable tests that run the full pipeline: STT transcript → voice parser → clarification loop → intent bridge → intent lifecycle. The goal is to prevent authority leakage and no-coaching violations through automated testing.

New files created:
- `tests/spec/test_intent_bridge_contract_compliance.py` — End-to-end compliance tests
- `tests/spec/fixtures/intent_bridge_cases.yaml` — Test fixtures
- `tests/spec/helpers/intent_bridge_harness.py` — Minimal helper to run pipeline
- `docs/contracts/INTENT_BRIDGE_COMPLIANCE_NOTES.md` (optional) — Brief documentation

Existing files touched only as needed:
- `aidm/immersion/voice_intent_parser.py`
- `aidm/immersion/clarification_loop.py`
- `aidm/interaction/intent_bridge.py`
- `aidm/schemas/intents.py`
- `aidm/schemas/intent_lifecycle.py`

---

## Assessment: The work order is well-scoped

This is a testing-focused work order with tight constraints. The scope exclusions are correct — no Box mechanics, no new action types, no UI, no model work. The acceptance criteria are testable. The step plan is concrete.

### Key strengths

**1. The determinism test is the right forcing function.**
Step 4 requires running each fixture case 10+ times and asserting byte-stable equality of normalized outputs. This will expose any hidden nondeterminism (dict iteration order, timestamp injection, unstable candidate ordering). If the tests pass, determinism holds by construction.

**2. The candidate ordering requirement addresses a real gap.**
The current implementation doesn't guarantee stable candidate ordering in `ClarificationRequest`. Step 5 requires implementing an explicit ordering function and testing it. This is the correct fix — make the ordering explicit and test it, rather than hoping it happens to be stable.

**3. The no-coaching tests are structural, not just string matching.**
Step 6 requires an allowlist-based template for clarification messages plus negative tests for forbidden patterns. This is better than regex-matching specific bad phrases — it defines what's allowed and rejects everything else.

**4. The forbidden files list is explicit and correct.**
`aidm/core/**` is off-limits. This prevents the testing work from accidentally expanding into mechanics changes.

**5. The Opus audit checklist is built into the work order.**
The PR cannot merge without Opus confirming: forbidden files untouched, determinism verified, candidate ordering explicit, clarification phrasing neutral, lifecycle immutability preserved. This is good governance.

---

## What Already Exists (context for the agent)

### Current pipeline (recap from RQ-INTENT-001 review)

| Layer | File | Lines | Status |
|-------|------|-------|--------|
| Voice parser | `aidm/immersion/voice_intent_parser.py` | ~500 | Working, 60+ tests |
| Clarification engine | `aidm/immersion/clarification_loop.py` | 448 | Working, DM-persona prompts |
| Intent bridge | `aidm/interaction/intent_bridge.py` | 521 | Working, 27 tests |
| Intent schemas | `aidm/schemas/intents.py` | 253 | Frozen dataclasses |
| Intent lifecycle | `aidm/schemas/intent_lifecycle.py` | 423 | State machine, 50+ tests |

### Current ambiguity types (6 defined)

```python
class AmbiguityType(str, Enum):
    TARGET_AMBIGUOUS = "target_ambiguous"
    TARGET_NOT_FOUND = "target_not_found"
    WEAPON_AMBIGUOUS = "weapon_ambiguous"
    WEAPON_NOT_FOUND = "weapon_not_found"
    SPELL_NOT_FOUND = "spell_not_found"
    DESTINATION_OUT_OF_BOUNDS = "destination_out_of_bounds"
```

### Missing ambiguity types (from RQ-INTENT-001 review)

| Missing type | Why it matters |
|--------------|----------------|
| `actor_not_found` | Currently returns `TARGET_NOT_FOUND`, confusing |
| `stt_uncertain` | STT confidence below threshold |
| `out_of_scope` | Player says something system doesn't handle |
| `insufficient_context` | Pronoun with no referent |
| `action_type_unknown` | Parser can't determine action type |

The work order says "add missing ambiguity/failure modes ONLY if required for contract compliance." This is the right framing — don't add them speculatively, add them when a test case requires them.

### Current candidate ordering

Not guaranteed stable. The `ClarificationRequest.candidates` tuple is populated from entity lookups that may not have deterministic iteration order. The work order correctly identifies this as a gap to fix.

### Current clarification phrasing

The `ClarificationEngine` in `clarification_loop.py` generates DM-persona prompts. These are mostly good (neutral disambiguation), but haven't been tested against an explicit no-coaching constraint. Some edge cases may leak tactical information.

---

## Risks and Considerations

### Risk 1: The harness becomes too coupled to implementation details

The test harness needs to run the full pipeline (parse → bridge → lifecycle), but it shouldn't depend on internal implementation details that might change. If the harness reaches into private methods or assumes specific intermediate data structures, it becomes fragile.

**Mitigation:** The harness should use only public APIs. The `helpers/intent_bridge_harness.py` should be a thin wrapper that calls the same entry points the runtime uses.

### Risk 2: The no-coaching tests may be too strict or too permissive

Defining "neutral disambiguation only" is subjective. The allowlist approach is correct, but the specific templates need careful review. Too strict = false positives on valid prompts. Too permissive = coaching slips through.

**Mitigation:** The agent should document the phrasing rules explicitly in `INTENT_BRIDGE_COMPLIANCE_NOTES.md`. Opus audit should review the template allowlist and forbidden pattern list for completeness.

### Risk 3: Fixture cases may not cover enough edge cases

The work order requires fixtures for target_ambiguous, target_not_found, weapon_ambiguous, spell_not_found, insufficient_context pronoun, and action_type_unknown. This is a minimum set. Important cases that might be missed:

- Cross-turn pronoun resolution ("attack him again")
- Spatial references ("the one by the door")
- Multiple simultaneous ambiguities (unknown action + unknown target)
- Confidence threshold boundaries (STT at exactly 0.8)

**Mitigation:** The fixture file should include at least 15-20 cases, not just the 6 listed. The RQ-INTENT-001 spec (when delivered) should provide the example corpus that informs these fixtures.

### Risk 4: Existing tests may break due to ordering changes

If the candidate ordering is currently undefined (relying on dict iteration), existing tests may be passing by accident. When ordering becomes explicit, some tests may fail.

**Mitigation:** This is acceptable. The work order says "update existing tests only if they break for legitimate reasons." Ordering changes are legitimate. The delta should be documented in COMPLIANCE_NOTES.

### Risk 5: The work order depends on RQ-INTENT-001 spec which isn't delivered yet

WO-CODE-INTENT-002 implements tests for a contract that RQ-INTENT-001 is supposed to define. If the spec isn't delivered first, the implementation agent will have to make assumptions about what the contract requires.

**Mitigation:** The work order is self-contained enough to execute without the spec — it defines determinism, ordering, and no-coaching requirements inline. But the agent should cross-reference with any RQ-INTENT-001 deliverables if they exist by execution time.

---

## Relationship to Other Active Work

| Work | Interaction |
|------|-------------|
| RQ-INTENT-001 (Intent Bridge Spec) | This implements tests for that spec. Ideally spec lands first, but this can proceed independently. |
| Manifesto (updated) | The manifesto now explicitly states "no mercy, no hand-holding" and "no system that warns you before you make mistakes." The no-coaching tests directly enforce this. |
| RQ-DISCOVERY-001 (Bestiary) | No direct interaction, but both touch the boundary between "what the system knows" and "what the player sees." |
| RQ-PHYS-001 (RAW Gaps) | No direct interaction. |

---

## Dependency Chain

```
RQ-INTENT-001 (spec) ← Defines contract formally
    ↓
WO-CODE-INTENT-002 (this work order) ← Implements compliance tests
    ↓
Future: Voice-first loop integration ← Uses tested pipeline
```

The work order can proceed without RQ-INTENT-001 being complete, but the test fixtures should align with the spec's example corpus once delivered.

---

## Checklist for Opus Audit (from work order, reproduced for reference)

- [ ] Diff review confirms forbidden files untouched
- [ ] Determinism verified via repeated runs
- [ ] Candidate ordering is explicit and documented
- [ ] Clarification phrasing is neutral (no coaching) and does not leak mechanics
- [ ] CONFIRMED intents remain immutable; lifecycle transitions are valid

---

## Recommendation

**Approve execution.** The work order is well-scoped, the acceptance criteria are testable, and the forbidden files constraint is correctly set. The main execution risk is the fixture corpus being too small — the agent should be encouraged to include 15-20 cases minimum, not just the 6 explicitly listed.

The Opus audit requirement is appropriate for this work order since it touches the authority boundary (clarification phrasing could leak mechanics or provide coaching if done wrong).

One addition: **the agent should read the updated manifesto before execution.** The "no mercy, no hand-holding" language and the explicit rejection of "a system that warns you before you make mistakes" directly inform what constitutes a no-coaching violation. The manifesto is now the authoritative source for this constraint.

---

*— Jay*

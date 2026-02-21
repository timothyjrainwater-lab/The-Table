# WO-VOICE-UK-LOG-001: Unknown Handling Structured Logging

**Classification:** CODE (structured logging + event schema + gate tests)
**Priority:** BURST-001 Tier 2.4. Parallel with WO-VOICE-PRESSURE-IMPL-001.
**Dispatched by:** Slate (PM)
**Date:** 2026-02-21
**Origin:** BURST-001 build order. Source: `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` (frozen Tier 1.2), Playbook Section 8 (WO 2.4).

---

## Context

Tier 1.2 froze the Unknown Handling Contract — 7 failure classes (FC-ASR through FC-BLEED), STOPLIGHT classification, clarification budget, cancel semantics. That contract defines *what* happens. This WO adds *observability* — structured log events emitted whenever a voice input is classified, clarified, escalated, or cancelled.

This is an additive-only WO. No behavioral changes to the classification pipeline. The system already handles unknowns; this WO makes the handling visible.

**The rule:** You cannot improve what you cannot measure. Every STOPLIGHT classification produces a logged event. Every clarification round produces a logged event. Every escalation or cancellation produces a logged event.

---

## Objective

Produce structured logging for the unknown handling pipeline:
1. Define the `UnknownHandlingEvent` schema (frozen dataclass)
2. Wire log emission into `fact_acquisition.py` (FORBIDDEN_DEFAULT detection) and `intent_bridge.py` (classification/clarification paths)
3. Log every STOPLIGHT classification, clarification round, escalation, and cancellation
4. Provide gate tests proving logging works correctly

---

## Scope

### IN SCOPE

1. **New file: `aidm/schemas/unknown_handling_event.py`** — Frozen dataclass:
   - `UnknownHandlingEvent` frozen dataclass:
     - `event_type` (str): "classification" | "clarification_round" | "escalation" | "cancellation"
     - `failure_class` (str): FC-ASR, FC-HOMO, FC-PARTIAL, FC-TIMING, FC-AMBIG, FC-OOG, FC-BLEED, or None (for GREEN)
     - `sub_class` (Optional[str]): e.g., FC-ASR-01, FC-AMBIG-06
     - `stoplight` (str): "GREEN" | "YELLOW" | "RED"
     - `clarification_round` (int): 0-based, 0 = first attempt
     - `max_clarifications` (int): From contract (default 2, configurable 1-3)
     - `resolution` (str): "handled" | "clarified" | "escalated_to_menu" | "cancelled" | "pending"
     - `missing_attribute` (Optional[str]): For FORBIDDEN_DEFAULT detection (e.g., "size", "position")
     - `turn_number` (int)
     - `correlation_id` (str/UUID): Links to any related boundary pressure event
     - `timestamp` (str ISO 8601)

2. **Modify: `aidm/core/fact_acquisition.py`** — Add UK-class logging:
   - When a FORBIDDEN_DEFAULT attribute is requested (lines near `FORBIDDEN_DEFAULTS` check):
     - Emit `UnknownHandlingEvent` with `failure_class="FC-ASSET"` or appropriate class, `resolution="handled"` or `"escalated"`.
   - When an entity class is invalid or required attributes are missing:
     - Emit `UnknownHandlingEvent` with the appropriate failure class.
   - Logger name: `aidm.unknown_handling`.
   - **Minimal change** — add log emission at existing decision points. Do not restructure fact_acquisition.

3. **Modify: `aidm/interaction/intent_bridge.py`** — Add UK-class logging:
   - When `ClarificationRequest` is generated (ambiguity detected):
     - Emit `UnknownHandlingEvent` with `event_type="classification"`, appropriate `failure_class` (FC-AMBIG, FC-HOMO, etc.), `stoplight` per the contract.
   - When clarification resolves or escalates:
     - Emit `UnknownHandlingEvent` with `event_type="clarification_round"`, incremented round counter, resolution status.
   - When target/weapon/spell not found:
     - Emit `UnknownHandlingEvent` with `failure_class` matching the contract (FC-ASR for unrecognized, FC-AMBIG for ambiguous, FC-PARTIAL for incomplete).
   - **Minimal change** — add log emission at existing `ClarificationRequest` creation points. Do not restructure intent_bridge.

4. **Gate tests: `tests/test_unknown_handling_log_o.py`** — Gate O tests:
   - O-01: `UnknownHandlingEvent` has all required fields (11 fields)
   - O-02: Classification event emitted when ClarificationRequest is created
   - O-03: Clarification round event increments round counter
   - O-04: Escalation event emitted when clarification budget exhausted (round >= MAX_CLARIFICATIONS)
   - O-05: Cancellation event emitted on cancel/abort
   - O-06: FORBIDDEN_DEFAULT detection emits event with missing_attribute name
   - O-07: GREEN classification emits at DEBUG level
   - O-08: YELLOW classification emits at WARNING level
   - O-09: RED classification emits at ERROR level
   - O-10: Event has valid correlation_id (UUID format)
   - O-11: All 7 failure classes from contract are representable in failure_class field
   - O-12: No behavioral changes — classification outcomes unchanged with logging enabled
   - Additional gates at builder's discretion

### OUT OF SCOPE

- No changes to Unknown Handling Contract (Tier 1.2 — frozen).
- No voice intent parser implementation (Tier 3).
- No ASR/STT integration (Tier 4).
- No metrics aggregation or dashboards.
- No changes to play_loop, resolvers, event_log, or replay infrastructure.
- No changes to doctrine files.

---

## Design Decisions (PM-resolved)

| # | Decision | Resolution | Rationale |
|---|----------|------------|-----------|
| OD-01 | Where does the event schema live? | **`aidm/schemas/unknown_handling_event.py`** (new file). | Follows Tier 2.1 pattern — schemas in `aidm/schemas/`. |
| OD-02 | Map intent_bridge `AmbiguityType` to failure classes? | **Yes.** `TARGET_AMBIGUOUS` → FC-AMBIG, `TARGET_NOT_FOUND` → FC-ASR (unrecognized entity), `WEAPON_AMBIGUOUS` → FC-AMBIG, `WEAPON_NOT_FOUND` → FC-ASR, `SPELL_NOT_FOUND` → FC-ASR, `DESTINATION_OUT_OF_BOUNDS` → FC-OOG. | The bridge already classifies ambiguity types; map them to the contract's failure classes. |
| OD-03 | Log every classification or only failures? | **Every classification.** GREEN classifications log at DEBUG (silent in production). YELLOW/RED log at WARNING/ERROR (visible). | Observability means observing everything, not just failures. GREEN data is needed for metric denominators. |

---

## Research Sources

The builder must read:

1. `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` — **PRIMARY.** Frozen Tier 1.2. All 7 failure classes, STOPLIGHT rules, clarification budget.
2. `aidm/interaction/intent_bridge.py` — Integration target. `AmbiguityType` enum, `ClarificationRequest` dataclass.
3. `aidm/core/fact_acquisition.py` — Integration target. `FORBIDDEN_DEFAULTS`, entity class validation.
4. `docs/contracts/TYPED_CALL_CONTRACT.md` — Tier 1.3 (frozen). OPERATOR_DIRECTIVE and CLARIFICATION_QUESTION CallTypes reference clarification budget.

---

## Integration Seams

| Seam | Module | Relationship |
|------|--------|-------------|
| Unknown Handling Contract | `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` | READ ONLY — source of truth for failure classes and STOPLIGHT rules |
| Intent Bridge | `aidm/interaction/intent_bridge.py` | MODIFY — add log emission at ClarificationRequest creation points |
| Fact Acquisition | `aidm/core/fact_acquisition.py` | MODIFY — add log emission at FORBIDDEN_DEFAULT detection points |
| Boundary Pressure (Tier 2.1-2.3) | `aidm/schemas/boundary_pressure.py` | READ ONLY — correlation_id links UK events to pressure events |

---

## Assumptions to Validate

| # | Assumption | How to validate |
|---|-----------|----------------|
| A1 | Intent bridge creates ClarificationRequest at identifiable code points | Read `aidm/interaction/intent_bridge.py` |
| A2 | Fact acquisition has FORBIDDEN_DEFAULTS check with identifiable code points | Read `aidm/core/fact_acquisition.py` |
| A3 | Both modules support Python `logging` (no custom framework) | Check imports |
| A4 | `AmbiguityType` enum covers all intent bridge failure modes | Read intent_bridge.py |
| A5 | No existing UK-class structured logging exists | Grep for "unknown_handling" in aidm/ |

---

## Stop Conditions

1. **Intent bridge has no ClarificationRequest mechanism** — Stop. Nothing to log.
2. **Fact acquisition has no FORBIDDEN_DEFAULTS check** — Stop. Nothing to log.
3. **Tier 1.2 contract needs modification** — Stop. Frozen.
4. **Scope creep into classification logic changes** — This WO logs, it does not change behavior.

---

## Implementation Order

1. Read all 4 source documents
2. Validate assumptions A1-A5
3. Create `aidm/schemas/unknown_handling_event.py` (frozen dataclass)
4. Map `AmbiguityType` → failure class (OD-02 table)
5. Modify `intent_bridge.py` (add log emission at ClarificationRequest points)
6. Modify `fact_acquisition.py` (add log emission at FORBIDDEN_DEFAULTS points)
7. Write gate tests (O-01 through O-12)
8. Run full test suite — 0 regressions

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Delivery

### Commit

Single commit. Message format: `feat: WO-VOICE-UK-LOG-001 — Unknown Handling structured logging, Gate O tests`

All new gate tests must pass. All existing tests must show zero regressions.

### Completion Report

File as `pm_inbox/DEBRIEF_WO-VOICE-UK-LOG-001.md`. 500 words max. Five mandatory sections:

0. **Scope Accuracy** — Did you deliver what was asked? Note any deviations.
1. **Discovery Log** — Anything you found that the dispatch didn't anticipate.
2. **Methodology Challenge** — Hardest part and how you solved it.
3. **Field Manual Entry** — One tradecraft tip for the next builder working in this area.
4. **Builder Radar** (mandatory, 3 labeled lines):
   - **Trap.** Hidden dependency or trap for the next WO.
   - **Drift.** Current drift risk.
   - **Near stop.** What got close to triggering a stop condition.

### Audio Cue (MANDATORY)

When all work is complete (commit landed, debrief written), fire this command so the Operator knows you're done:

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

### Debrief Focus Questions

1. **Failure class mapping:** Did the `AmbiguityType` → failure class mapping cover all intent bridge code paths, or were there unmapped paths?
2. **Fact acquisition logging:** How many FORBIDDEN_DEFAULT detection points exist? Were there any decision points in fact_acquisition that don't fit neatly into the 7-class taxonomy?

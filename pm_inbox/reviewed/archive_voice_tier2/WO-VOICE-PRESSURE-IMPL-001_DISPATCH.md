# WO-VOICE-PRESSURE-IMPL-001: Boundary Pressure Runtime — Schema + Detection + Logging

**Classification:** CODE (new schema module + detection logic + structured logging + gate tests)
**Priority:** BURST-001 Tier 2.1+2.2+2.3. First runtime code in the BURST-001 voice pipeline.
**Dispatched by:** Slate (PM)
**Date:** 2026-02-21
**Origin:** BURST-001 build order. Source: `docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md` (frozen Tier 1.4), Playbook Section 8 (WOs 2.1, 2.2, 2.3).

---

## Context

Tier 1 froze four spec contracts. Tier 2 builds the first runtime code: schemas, detection logic, and structured logging. No behavioral changes — the system observes before it acts.

This WO consolidates Playbook WOs 2.1 (schema), 2.2 (detection), and 2.3 (logging) into a single delivery. These are tightly coupled — the schema defines the types, detection populates them, logging emits them.

**The rule:** Measure before you change. Every pressure evaluation produces a logged event. Detection is content-agnostic (no vocabulary, no game-specific patterns).

---

## Objective

Produce runtime boundary pressure detection that:
1. Defines the `BoundaryPressure` schema (dataclasses + enums) per the frozen Tier 1.4 contract
2. Implements the four pressure detectors as pure functions (field inspection only)
3. Implements the composite classification logic (GREEN/YELLOW/RED with escalation)
4. Wires detection into `ContextAssembler` (token budget check) and `IntentBridge` (ambiguity/missing-fact check)
5. Emits structured log events per the contract's observability spec (9-field payload)
6. Provides gate tests proving detection + logging work correctly

---

## Scope

### IN SCOPE

1. **New file: `aidm/schemas/boundary_pressure.py`** — Frozen dataclasses and enums:
   - `PressureLevel` enum: `GREEN`, `YELLOW`, `RED`
   - `PressureTrigger` frozen dataclass: `trigger_id` (str), `level` (PressureLevel), `detail` (str)
   - `BoundaryPressureResult` frozen dataclass: `triggers` (tuple of PressureTrigger), `composite_level` (PressureLevel), `call_type` (str), `response` (str: "proceed" | "advisory_fallback" | "fail_closed"), `correlation_id` (str/UUID), `turn_number` (int), `timestamp` (str ISO 8601)
   - Trigger ID constants: `BP_MISSING_FACT`, `BP_AMBIGUOUS_INTENT`, `BP_AUTHORITY_PROXIMITY`, `BP_CONTEXT_OVERFLOW`

2. **New file: `aidm/core/boundary_pressure.py`** — Detection + classification logic:
   - `evaluate_pressure(call_type, input_fields, outcome_summary, token_budget, token_required, turn_number) -> BoundaryPressureResult`
   - Four detector functions (pure, no side effects):
     - `_check_missing_fact(call_type, input_fields) -> Optional[PressureTrigger]` — Checks required fields per CallType against the Tier 1.3 input schema field lists. Missing/null/empty → RED.
     - `_check_ambiguous_intent(input_fields) -> Optional[PressureTrigger]` — Checks `needs_clarification` flag or candidate count. Multiple unresolved candidates → YELLOW.
     - `_check_authority_proximity(outcome_summary) -> Optional[PressureTrigger]` — Checks if outcome_summary contains `"pending"` sentinel, severity is None, or unresolved game state markers. Structural check only (no vocabulary scanning). → YELLOW.
     - `_check_context_overflow(token_budget, token_required) -> Optional[PressureTrigger]` — Checks inclusion ratio (budget/required). Ratio < 1.0 → YELLOW. Ratio < 0.5 → RED.
   - `_classify_composite(triggers) -> PressureLevel` — Any single RED → RED. 3+ YELLOW → RED. 1-2 YELLOW → YELLOW. No triggers → GREEN.
   - `_determine_response(level) -> str` — GREEN → "proceed", YELLOW → "advisory_fallback", RED → "fail_closed".
   - **REQUIRED_FIELDS dict** — Per-CallType required field lists, sourced from `TYPED_CALL_CONTRACT.md` input schemas. This is the runtime version of the Tier 1.3 spec.

3. **Modify: `aidm/lens/context_assembler.py`** — Add pressure detection call point:
   - After token budget calculation, call `_check_context_overflow()` with the computed budget and required tokens.
   - Return the `PressureTrigger` (if any) alongside the assembled context, so the caller can include it in the composite evaluation.
   - **Minimal change** — add one function call and one return field. Do not restructure the assembler.

4. **Modify: `aidm/interaction/intent_bridge.py`** — Add pressure detection call points:
   - In attack/spell/move resolution, after intent translation:
     - Call `_check_missing_fact()` with the resolved CallType and available input fields.
     - Call `_check_ambiguous_intent()` when ClarificationRequest would be generated.
   - Return `PressureTrigger` list alongside the resolution result.
   - **Minimal change** — add trigger collection, do not restructure the bridge.

5. **Modify: `aidm/runtime/session_orchestrator.py`** — Wire composite evaluation + logging:
   - Before any Spark call (in narration generation path), call `evaluate_pressure()` with all collected triggers.
   - Log the `BoundaryPressureResult` as a structured log event using Python `logging` (logger name: `aidm.boundary_pressure`).
   - Log levels per contract: GREEN=DEBUG, YELLOW=WARNING, RED=ERROR.
   - On RED: skip Spark call, use template fallback directly.
   - On YELLOW: proceed but pre-load template fallback; if post-hoc validation fails, use template immediately (no retry).
   - On GREEN: normal Spark flow with standard retry policy.
   - **The response policy is the ONLY behavioral change in this WO.** Everything else is observation.

6. **Gate tests: `tests/test_boundary_pressure_impl_n.py`** — Gate N tests:
   - N-01: `evaluate_pressure()` returns `BoundaryPressureResult` with all required fields
   - N-02: Missing required field for COMBAT_NARRATION → RED, response="fail_closed"
   - N-03: All fields present, no triggers → GREEN, response="proceed"
   - N-04: `needs_clarification=True` → YELLOW (BP-AMBIGUOUS-INTENT)
   - N-05: Token ratio < 1.0 → YELLOW (BP-CONTEXT-OVERFLOW)
   - N-06: Token ratio < 0.5 → RED (BP-CONTEXT-OVERFLOW escalated)
   - N-07: `outcome_summary="pending"` → YELLOW (BP-AUTHORITY-PROXIMITY)
   - N-08: 3 YELLOW triggers simultaneously → RED (escalation rule PD-04)
   - N-09: 2 YELLOW triggers → YELLOW (no escalation)
   - N-10: 1 RED + 2 YELLOW → RED (single RED overrides)
   - N-11: Structured log event contains all 9 required fields from contract
   - N-12: GREEN logs at DEBUG level, YELLOW at WARNING, RED at ERROR
   - N-13: RED response skips Spark call (integration test with mock)
   - N-14: YELLOW response uses template on first validation failure (no retry)
   - N-15: Detection is content-agnostic — no vocabulary patterns in any detector function
   - Additional gates at builder's discretion

### OUT OF SCOPE

- No changes to Tier 1.1, 1.2, 1.3, or 1.4 contracts.
- No EvidenceValidator implementation (Tier 1.3 Stage 3 remains RESERVED).
- No TTS integration, no CLI grammar changes.
- No changes to play_loop, resolvers, event_log, or replay infrastructure.
- No changes to doctrine files.
- No metrics aggregation or dashboards (that's Tier 5 evaluation harness territory).

---

## Design Decisions (PM-resolved)

| # | Decision | Resolution | Rationale |
|---|----------|------------|-----------|
| ND-01 | Where does `boundary_pressure.py` live? | **`aidm/core/`** for logic, **`aidm/schemas/`** for dataclasses. | Detection is deterministic logic (core); types are schema. Standard pattern. |
| ND-02 | Does detection modify state? | **No.** All detectors are pure functions. `evaluate_pressure()` takes inputs, returns result. No side effects. | Wisdom 4: determinism. Pressure detection must be replayable. |
| ND-03 | What happens if `evaluate_pressure()` itself throws? | **Fail-closed to RED.** If the detection system errors, treat as maximum pressure. Log the exception. | Conservative default. Don't generate what you can't evaluate. |
| ND-04 | Should we log the full input_fields payload? | **No.** Log trigger IDs, levels, composite result, call_type, response, correlation_id, turn_number, detail, timestamp. No raw input dump (privacy + log volume). | Contract specifies 9 fields. Ship exactly 9 fields. |

---

## Research Sources

The builder must read:

1. `docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md` — **PRIMARY.** Frozen Tier 1.4. All trigger definitions, PressureLevels, response policies, invariants, observability spec.
2. `docs/contracts/TYPED_CALL_CONTRACT.md` — Frozen Tier 1.3. Input schemas define what fields BP-MISSING-FACT checks. Fallback templates define what RED/YELLOW fires.
3. `aidm/lens/context_assembler.py` — Integration target. Token budget calculation already exists.
4. `aidm/interaction/intent_bridge.py` — Integration target. Ambiguity detection already exists (ClarificationRequest).
5. `aidm/runtime/session_orchestrator.py` — Integration target. Narration generation path. Logging infrastructure already exists.

---

## Integration Seams

| Seam | Module | Relationship |
|------|--------|-------------|
| Boundary Pressure Contract | `docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md` | READ ONLY — source of truth for trigger definitions, levels, response policies |
| Typed Call Contract | `docs/contracts/TYPED_CALL_CONTRACT.md` | READ ONLY — input schemas define required fields per CallType |
| Context Assembler | `aidm/lens/context_assembler.py` | MODIFY — add token overflow detection call point |
| Intent Bridge | `aidm/interaction/intent_bridge.py` | MODIFY — add missing-fact and ambiguity detection call points |
| Session Orchestrator | `aidm/runtime/session_orchestrator.py` | MODIFY — wire composite evaluation, logging, and response policy |
| Entity Fields | `aidm/schemas/entity_fields.py` | READ ONLY — field name constants for missing-fact checks |

---

## Assumptions to Validate

| # | Assumption | How to validate |
|---|-----------|----------------|
| A1 | Context assembler has a token budget calculation that returns available vs required | Read `aidm/lens/context_assembler.py` |
| A2 | Intent bridge already creates ClarificationRequest with candidate count | Read `aidm/interaction/intent_bridge.py` |
| A3 | Session orchestrator has a narration generation path that can be gated | Read `aidm/runtime/session_orchestrator.py` |
| A4 | No existing `boundary_pressure.py` module exists | `ls aidm/schemas/boundary_pressure.py` and `ls aidm/core/boundary_pressure.py` |
| A5 | Python `logging` is the standard logging mechanism (no custom framework) | Check session_orchestrator.py imports |
| A6 | Typed Call Contract defines per-CallType required input fields | Read `docs/contracts/TYPED_CALL_CONTRACT.md` |

---

## Stop Conditions

1. **Context assembler has no token budget concept** — Stop. BP-CONTEXT-OVERFLOW depends on it.
2. **Intent bridge has no ambiguity detection** — Stop. BP-AMBIGUOUS-INTENT depends on ClarificationRequest or equivalent.
3. **Session orchestrator has no narration generation path to gate** — Stop. Response policy (RED=skip Spark) requires a gating point.
4. **Tier 1.3 or 1.4 contracts need modification** — Stop. Those are frozen.
5. **Scope creep into Tier 3-5 territory** — No grammar changes, no TTS routing, no evaluation harness.

---

## Implementation Order

1. Read all 5 source documents
2. Validate assumptions A1-A6
3. Create `aidm/schemas/boundary_pressure.py` (enums + dataclasses)
4. Create `aidm/core/boundary_pressure.py` (4 detectors + classifier + evaluate_pressure)
5. Write unit tests for detection logic (N-01 through N-10)
6. Modify `context_assembler.py` (token overflow detection call point)
7. Modify `intent_bridge.py` (missing-fact + ambiguity detection call points)
8. Modify `session_orchestrator.py` (composite evaluation + logging + response policy)
9. Write integration tests (N-11 through N-15)
10. Run full test suite — 0 regressions

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Delivery

### Commit

Single commit. Message format: `feat: WO-VOICE-PRESSURE-IMPL-001 — Boundary Pressure runtime schema, detection, and logging`

All new gate tests must pass. All existing tests must show zero regressions.

### Completion Report

File as `pm_inbox/DEBRIEF_WO-VOICE-PRESSURE-IMPL-001.md`. 500 words max. Five mandatory sections:

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

1. **Integration friction:** How much did you have to modify the existing modules? Were the integration points clean, or did the existing code resist the additions?
2. **Detection coverage:** Did the Tier 1.3 input schemas define enough required fields to make BP-MISSING-FACT meaningful, or are most fields optional?

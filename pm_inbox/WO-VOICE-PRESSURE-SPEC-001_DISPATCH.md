# WO-VOICE-PRESSURE-SPEC-001: Boundary Pressure Contract — Pre-Generation Risk Signal

**Classification:** CODE (contract document + gate tests + validator script)
**Priority:** BURST-001 Tier 1.4. Spec freeze. No engine changes.
**Dispatched by:** Slate (PM)
**Date:** 2026-02-21
**Origin:** BURST-001 build order. Source: `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` (Section 1.6), `docs/research/VOICE_CONTROL_PLANE_CONTRACT.md`.

---

## Context

Tier 1.1 froze **output formatting** (how lines look).
Tier 1.2 froze **input failure handling** (what happens when we can't understand the player).
Tier 1.3 froze **the invocation boundary** (every Spark call is mode-locked with a CallType).

Tier 1.4 freezes **the pre-generation risk signal**. Before Spark ever sees a prompt, the system evaluates whether the narration task is structurally likely to produce a mechanical authority violation. If risk is high, Spark never fires — template fallback handles it.

**The rule:** Don't generate output you'll have to reject. Detect pressure before generation, not after.

---

## Objective

Produce a binding contract document (`docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md`) that defines:
1. The four pressure triggers — structural conditions that push Spark toward mechanical claims
2. PressureLevel classification — GREEN / YELLOW / RED (matching Tier 1.2 STOPLIGHT pattern)
3. Response policy per level — proceed / advisory fallback / fail-closed
4. Detection method — pre-call PromptPack field inspection (content-agnostic, zero vocabulary dependencies)
5. Observability — how pressure signals are logged and correlated with post-hoc validation failures
6. Integration points with Tier 1.1 (line types), Tier 1.2 (clarification budget), and Tier 1.3 (CallType forbidden claims)

Plus gate tests and a validator script, same pattern as Tiers 1.1–1.3.

---

## Scope

### IN SCOPE

1. **Contract document** — `docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md`. Same structure as the three existing contracts.

2. **Four pressure triggers** — From research (RQ-SPRINT-004 Section 1.6). For each trigger, define:
   - **Trigger ID** (e.g., BP-MISSING-FACT, BP-AMBIGUOUS-INTENT, BP-AUTHORITY-PROXIMITY, BP-CONTEXT-OVERFLOW)
   - **Detection rule** — What structural condition activates it (field presence, field consistency, token budget)
   - **Severity** — Default PressureLevel contribution (GREEN/YELLOW/RED)
   - **Affected CallTypes** — Which Tier 1.3 CallTypes are vulnerable to this trigger

   | Trigger | Condition | Default Severity |
   |---------|-----------|-----------------|
   | BP-MISSING-FACT | Required NarrativeBrief fields null/empty for this CallType | RED |
   | BP-AMBIGUOUS-INTENT | Multiple valid narration interpretations (outcome unclear) | YELLOW |
   | BP-AUTHORITY-PROXIMITY | Narration task is structurally close to mechanical territory | YELLOW |
   | BP-CONTEXT-OVERFLOW | Token budget insufficient for full prompt + constraints | YELLOW |

3. **PressureLevel classification** — Composite signal from all triggers:
   - **GREEN** — No triggers active. Proceed to Spark generation.
   - **YELLOW** — Advisory. Proceed with generation but pre-load template fallback. If post-hoc validation (Tier 1.3 Stage 1-2) rejects output, use template immediately (no retry).
   - **RED** — Fail-closed. Do not call Spark. Use template fallback directly. Log the trigger(s).

4. **Response policy** — Per PressureLevel, define:
   - Whether Spark is called
   - Whether retry is allowed (YELLOW: no retry on validation failure; RED: no generation at all)
   - Which fallback fires (Tier 1.3 per-CallType fallback templates)
   - Whether the operator is notified (RED triggers log a pressure event)

5. **Detection method spec** — Pre-call inspection of the PromptPack before it reaches Spark:
   - Check required input fields per CallType (from Tier 1.3 input schemas)
   - Check outcome clarity (is the mechanical result unambiguous?)
   - Check token budget (does the prompt + system instructions fit within the CallType's ceiling?)
   - **Key constraint:** Detection is content-agnostic. No vocabulary scanning. No D&D-specific patterns. This is the only mechanism in the pipeline with zero game-system dependencies.

6. **Observability spec** — Define the pressure event payload:
   - Trigger ID(s) that fired
   - PressureLevel computed
   - CallType attempted
   - Response taken (proceed / fallback / fail-closed)
   - Correlation ID linking to any post-hoc validation result

7. **Invariants** — Minimum 4:
   - BP-INV-01: Every Spark invocation is preceded by a pressure evaluation
   - BP-INV-02: RED pressure level never reaches Spark (fail-closed guarantee)
   - BP-INV-03: Pressure detection uses only structural field inspection (no vocabulary, no game-specific patterns)
   - BP-INV-04: Every pressure evaluation produces a logged event (observability guarantee)

8. **Gate tests** — New test file `tests/test_boundary_pressure_gate_m.py`. Gate M tests (M-01 through M-XX). Minimum gates:
   - M-01: Four triggers defined with all required fields (ID, detection rule, severity, affected CallTypes)
   - M-02: Three PressureLevels defined (GREEN, YELLOW, RED) with response policies
   - M-03: RED policy specifies fail-closed (no Spark call)
   - M-04: YELLOW policy specifies no retry on post-hoc rejection
   - M-05: GREEN policy specifies normal Spark flow
   - M-06: BP-MISSING-FACT detection rule references Tier 1.3 input schema fields
   - M-07: BP-CONTEXT-OVERFLOW detection rule references a token budget threshold
   - M-08: All four invariants (BP-INV-01 through BP-INV-04) are testable assertions
   - M-09: Pressure event payload schema includes all required fields (trigger IDs, level, CallType, response, correlation ID)
   - M-10: Detection is content-agnostic — no vocabulary patterns in trigger definitions (structural field checks only)
   - Additional gates at builder's discretion

9. **Validator script** — `scripts/check_boundary_pressure.py`. Reads the contract, checks structural completeness.

### OUT OF SCOPE

- No engine code changes. No runtime implementation of pressure detection.
- No changes to Tier 1.1, 1.2, or 1.3 contracts.
- No vocabulary or regex patterns (that's Tier 1.3's domain — forbidden claims).
- No D&D-specific detection rules.
- No changes to doctrine files.

---

## Design Decisions (PM-resolved)

| # | Decision | Resolution | Rationale |
|---|----------|------------|-----------|
| PD-01 | Does AUTHORITY_PROXIMITY alone trigger RED? | **No.** AUTHORITY_PROXIMITY alone is YELLOW. Only BP-MISSING-FACT (required data absent) triggers RED by itself. Multiple YELLOW triggers may escalate to RED if 3+ fire simultaneously. | A single proximity signal is advisory; missing data is a hard constraint. |
| PD-02 | On RED, attempt Spark with constraints first? | **No.** RED is fail-closed. Template only. No speculative generation. | If you know the input is structurally deficient, generating output is waste. |
| PD-03 | Log pressure signals in provenance or silent telemetry? | **Provenance metadata.** Pressure signals are part of the event record. They correlate with post-hoc validation and are replayable. | Wisdom 3: what you cannot replay, you cannot trust. Silent telemetry is invisible to replay. |
| PD-04 | Multi-trigger escalation rule? | **3+ YELLOW triggers escalate to RED.** 1 YELLOW = YELLOW. 2 YELLOW = YELLOW. 3+ YELLOW = RED. Any single RED = RED regardless of other triggers. | Conservative threshold. Three structural concerns simultaneously is a strong signal. |

---

## Research Sources

The builder must read:

1. `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` — Section 1.6: pressure triggers, detection method
2. `docs/research/VOICE_CONTROL_PLANE_CONTRACT.md` — Boundary invariants, authority levels
3. `docs/contracts/TYPED_CALL_CONTRACT.md` — Tier 1.3 (frozen). CallType input schemas, forbidden claims, fallback templates
4. `docs/contracts/CLI_GRAMMAR_CONTRACT.md` — Tier 1.1 (frozen). Line types
5. `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` — Tier 1.2 (frozen). STOPLIGHT pattern, clarification budget

---

## Integration Seams

| Seam | Module | Relationship |
|------|--------|-------------|
| Typed Call Contract | `docs/contracts/TYPED_CALL_CONTRACT.md` | READ ONLY — input schemas define what fields BP-MISSING-FACT checks; fallback templates define what RED fires |
| CLI Grammar Contract | `docs/contracts/CLI_GRAMMAR_CONTRACT.md` | READ ONLY — line types constrain fallback output format |
| Unknown Handling Contract | `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` | READ ONLY — STOPLIGHT pattern (GREEN/YELLOW/RED) is the model; clarification budget constrains YELLOW response |
| Spark Containment Audit | `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` | READ ONLY — source for trigger definitions |

No code integration seams — this is a spec-only WO.

---

## Assumptions to Validate

| # | Assumption | How to validate |
|---|-----------|----------------|
| A1 | Four pressure triggers are the complete set from research | Read RQ-SPRINT-004 Section 1.6 |
| A2 | Tier 1.3 input schemas define required fields per CallType | Read `TYPED_CALL_CONTRACT.md` |
| A3 | STOPLIGHT pattern (GREEN/YELLOW/RED) is established in Tier 1.2 | Read `UNKNOWN_HANDLING_CONTRACT.md` |
| A4 | Tier 1.3 fallback templates exist for all six CallTypes | Read `TYPED_CALL_CONTRACT.md` |
| A5 | No existing boundary pressure runtime code exists (spec-only) | Check `aidm/` for boundary_pressure modules |

---

## Stop Conditions

1. **Research sources contradictory on trigger count or definitions** — Stop and document.
2. **Tier 1.3 input schemas don't define required fields** — Stop. BP-MISSING-FACT depends on knowing what's required.
3. **Tier 1.1, 1.2, or 1.3 contracts need modification** — Stop. Those are frozen.
4. **Scope creep into runtime implementation** — No detection code. This is a contract.

---

## Implementation Order

1. Read all 5 source documents
2. Validate assumptions A1-A5
3. Draft contract document structure (match existing contract pattern)
4. Define the 4 pressure triggers with detection rules
5. Define PressureLevel classification and escalation rules
6. Define response policy per level
7. Define observability (pressure event payload)
8. Define the 4+ invariants
9. Write gate tests (M-01 through M-XX)
10. Write validator script
11. Run full test suite — 0 regressions

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Delivery

### Commit

Single commit. Message format: `feat: WO-VOICE-PRESSURE-SPEC-001 — Boundary Pressure Contract, Gate M tests, validator`

All new gate tests must pass. All existing tests must show zero regressions.

### Completion Report

File as `pm_inbox/DEBRIEF_WO-VOICE-PRESSURE-SPEC-001.md`. 500 words max. Five mandatory sections:

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

1. **Trigger completeness:** Did the research support exactly four triggers, or did you find more? What's the boundary between BP-AMBIGUOUS-INTENT and BP-AUTHORITY-PROXIMITY?
2. **Escalation threshold:** The dispatch specifies 3+ YELLOW → RED. Did you find evidence in the research supporting a different threshold?

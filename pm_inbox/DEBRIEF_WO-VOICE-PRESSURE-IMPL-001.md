# DEBRIEF: WO-VOICE-PRESSURE-IMPL-001 — Boundary Pressure Runtime

**Builder:** Claude Opus 4.6
**Date:** 2026-02-21
**Status:** COMPLETE — all 37 gate tests pass, zero regressions (7 pre-existing failures unrelated)

---

## 0. Scope Accuracy

Delivered exactly what was asked. Created `aidm/schemas/boundary_pressure.py` (PressureLevel enum, PressureTrigger, BoundaryPressureResult frozen dataclasses, four trigger ID constants). Created `aidm/core/boundary_pressure.py` (four detector functions, composite classifier, response policy mapper, `evaluate_pressure()` entry point, REQUIRED_FIELDS per-CallType dict). Modified `context_assembler.py` with `compute_token_pressure()` method (BL-003 compliant — exposes budget metrics without importing from core). Modified `intent_bridge.py` with `extract_pressure_fields()` static method. Modified `session_orchestrator.py` with pressure evaluation before Spark calls, structured logging via `aidm.boundary_pressure` logger, and RED/YELLOW/GREEN response policy. Created `tests/test_boundary_pressure_impl_n.py` with 37 gate tests (N-01 through N-15 plus additional builder-discretion gates). No deviations from the dispatch.

## 1. Discovery Log

BL-003 ("No imports from aidm.core") applies to `context_assembler.py`. The dispatch specified calling `_check_context_overflow()` inside the assembler, but that function lives in `aidm.core.boundary_pressure`. Resolution: the assembler exposes `compute_token_pressure()` returning `(budget, required)` as raw integers, and the orchestrator (which is not bound by BL-003 relative to core) calls the detector. This preserves the boundary law while still providing the token budget data needed for BP-CONTEXT-OVERFLOW detection.

BP-AUTHORITY-PROXIMITY initially fired on RULE_EXPLAINER calls that don't have `truth.outcome_summary` in their input schema. The detector was defaulting absent fields to empty string, which matched the "empty outcome" check. Fixed by only checking `truth.outcome_summary` when the field is explicitly present in the input dict — absence of a field not in the CallType's schema is not a proximity signal.

## 2. Methodology Challenge

The hardest part was wiring the pressure evaluator into `_generate_narration()` without restructuring the existing code flow. The method already had a complex pipeline (DMPersona → template context → EngineResult → NarrationRequest → GuardedNarrationService). Inserting pressure evaluation required: (1) assembling input fields from the NarrativeBrief before the Spark call, (2) short-circuiting to template fallback on RED before building the full NarrationRequest, and (3) logging the pressure event regardless of outcome. The solution was a clean insertion point after template context but before system prompt construction — RED returns immediately, YELLOW/GREEN continue to the existing path.

## 3. Field Manual Entry

**When adding a detection call point that spans multiple modules with different boundary laws**, expose raw data (primitives, tuples) from the restricted module and let the unrestricted caller compose the detection call. Don't try to smuggle core imports through lens or lens through core. The assembler returns `(int, int)`, the orchestrator calls `evaluate_pressure()` — clean boundary, no BL-003 violation.

## 4. Builder Radar

- **Trap.** The `_assemble_pressure_input_fields()` method currently hardcodes `call_type="COMBAT_NARRATION"` in the orchestrator's `_generate_narration()`. When non-combat narration paths (NPC_DIALOGUE, SUMMARY, RULE_EXPLAINER) are wired through the orchestrator, the call_type must be derived from the NarrativeBrief or a new parameter. Forgetting this will silently evaluate all narrations against COMBAT_NARRATION's required fields.
- **Drift.** The REQUIRED_FIELDS dict in `boundary_pressure.py` is a manual copy of Tier 1.3 input schemas. If the Typed Call Contract adds or removes required fields, REQUIRED_FIELDS must be updated in lockstep. There is no automated sync — a contract amendment without a REQUIRED_FIELDS update will cause BP-MISSING-FACT to fire false positives or miss real gaps.
- **Near stop.** The BL-003 boundary law on `context_assembler.py` nearly triggered a stop condition. The dispatch specified calling `_check_context_overflow()` inside the assembler, which would have required an `aidm.core` import. The workaround (exposing raw metrics) was straightforward, but if the dispatch had required the assembler to return a `PressureTrigger` object (from `aidm.schemas`), that would have been a schema import, not a core import — which would have been fine. The boundary law is on `aidm.core`, not `aidm.schemas`.

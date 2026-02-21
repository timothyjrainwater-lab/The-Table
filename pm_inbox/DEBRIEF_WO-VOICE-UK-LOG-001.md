# DEBRIEF: WO-VOICE-UK-LOG-001 — Unknown Handling Structured Logging

**Builder:** Claude Opus 4.6
**Date:** 2026-02-21
**Status:** COMPLETE — all 47 gate tests pass, zero regressions (7 pre-existing failures unrelated to this WO)

---

## 0. Scope Accuracy

Delivered exactly what was asked. Created `aidm/schemas/unknown_handling_event.py` with the 11-field frozen dataclass. Added log emission to `aidm/interaction/intent_bridge.py` at every ClarificationRequest creation point in the three public resolve methods, plus GREEN classification on successful resolution. Added log emission to `aidm/core/fact_acquisition.py` at the FORBIDDEN_DEFAULTS validation check and the invalid entity class check. Created `tests/test_unknown_handling_log_o.py` with 47 tests across 18 gate classes (O-01 through O-18). Logger name is `aidm.unknown_handling` in both modules. No behavioral changes to classification pipeline. No deviations from the dispatch.

## 1. Discovery Log

The `AmbiguityType` → failure class mapping (OD-02) covers all 6 enum members but maps to only 3 of the 7 contract failure classes: FC-AMBIG, FC-ASR, and FC-OOG. FC-HOMO, FC-PARTIAL, FC-TIMING, and FC-BLEED have no current code paths in `intent_bridge.py` — they correspond to voice-layer classifications (ASR confidence, timing, table-talk detection) that don't exist yet (Tier 3/4). The schema accepts all 7 classes for forward compatibility.

The fact_acquisition FORBIDDEN_DEFAULT detection has exactly one logging point: inside `validate_response()` when a required attribute is missing from Spark's response. The invalid entity class check in `acquire_facts()` was a second natural logging point — it maps to FC-OOG (out-of-grammar entity class). There are no other decision points in fact_acquisition that map to the 7-class taxonomy.

A parallel WO (WO-VOICE-PRESSURE-IMPL-001) added `extract_pressure_fields()` to `intent_bridge.py` during this build. No conflict — that method is a static helper on `IntentBridge` with no interaction with the logging emission points.

## 2. Methodology Challenge

The hardest decision was where to place log emission in `intent_bridge.py`. ClarificationRequests are created in private helpers (`_resolve_entity_name`, `_resolve_weapon`, `_resolve_spell_name`) but returned through public methods (`resolve_attack`, `resolve_spell`, `resolve_move`). Logging in the private helpers would produce duplicate events when a ClarificationRequest flows through multiple call sites. Logging at the public method return points (where `isinstance(result, ClarificationRequest)` is checked) ensures exactly one event per classification attempt. GREEN events are emitted at the point where a successful resolved intent is about to be returned.

## 3. Field Manual Entry

**When adding structured logging to a pipeline, log at the public API boundary, not at internal creation sites.** If an internal helper creates a ClarificationRequest that gets passed up through multiple layers, logging at each layer produces duplicates. The public method return is the single point where classification outcome is finalized and should be logged exactly once.

## 4. Builder Radar

- **Trap.** The `FrozenWorldStateView` constructor does a strict `isinstance(state, WorldState)` check. Tests that try to pass mock objects will fail silently at construction, not at the test assertion. Gate tests must use real `WorldState(ruleset_version="dnd3.5", entities={...})` objects.
- **Drift.** The `_emit_classification_event` helper determines stoplight color from `AmbiguityType` using a hardcoded if/elif chain. When Tier 3 adds new AmbiguityTypes or refines the STOPLIGHT mapping, this helper must be updated in sync. No schema-driven mapping exists yet.
- **Near stop.** The `AmbiguityType` enum covers only 6 of the 7 contract failure classes. FC-HOMO, FC-PARTIAL, FC-TIMING, and FC-BLEED have zero code paths in `intent_bridge.py` today. This WO is logging-only and the schema supports all 7 classes, so no stop condition was triggered — but a builder expecting full pipeline coverage from this WO alone would be disappointed.

# WO-GAP-B-001: Connect Layer B to Narration Pipeline

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 0 (gate-lift prerequisite)
**Priority:** P0 — Highest impact, lowest effort fix in the entire research sprint
**Source:** RQ-SPRINT-002, RQ-SPRINT-003, RQ-SPRINT-005 (independent convergence)

---

## Target Lock

Fix the two gaps that disconnect Layer B (Presentation Semantics) from the live narration pipeline:

- **GAP-B-001:** `NarrativeBrief.presentation_semantics` is always `None` at runtime. The Lens assembler does not populate it from the `PresentationSemanticsRegistry`.
- **GAP-B-002:** `TruthChannel` has no fields to serialize Layer B data to Spark.

After this WO, Spark receives frozen Layer B data (delivery_mode, staging, scale, vfx_tags, sfx_tags, contraindications) for every narration it generates.

## Binary Decisions

1. **Where does the lookup happen?** In `assemble_narrative_brief()` — the function that constructs NarrativeBrief from EngineResult. The PresentationSemanticsRegistry is a Lens-layer resource; the assembler already has access to it.
2. **What key is used for lookup?** The `content_id` from the event payload (e.g., `spell.fireball_003`). The PresentationSemanticsRegistry is keyed by `content_id`.
3. **What if no entry exists for the content_id?** `presentation_semantics` remains `None`. This is the current behavior and is safe — Spark falls back to action_type-based narration.
4. **Does TruthChannel need all Layer B fields?** Yes — serialize the full `AbilityPresentationEntry` (delivery_mode, staging, origin_rule, scale, vfx_tags, sfx_tags, residue, contraindications). Spark needs all of them for tonal consistency and contraindication enforcement.

## Contract Spec

### Inputs
- `PresentationSemanticsRegistry` (exists, populated at compile time, keyed by `content_id`)
- `EngineResult` event payloads (contain `content_id` for ability-triggered events)
- `NarrativeBrief` schema (already has `presentation_semantics: Optional[AbilityPresentationEntry]` field)

### Outputs
- `NarrativeBrief.presentation_semantics` populated when a matching registry entry exists
- `TruthChannel` serializes Layer B fields so Spark can consume them
- All existing tests pass (no behavioral change for events without presentation entries)

### Constraints
- Do NOT modify `AbilityPresentationEntry` schema
- Do NOT modify `PresentationSemanticsRegistry` schema
- Do NOT modify any resolver or reducer logic
- BL-003 compliance: NarrativeBrief remains a one-way valve. No Box state leaks beyond what the brief already exposes.

### Boundary Laws Affected
- BL-003 (NarrativeBrief is one-way valve): PRESERVED — adding Layer B data to the brief is within its contract
- BL-007 (EngineResult immutability): NOT TOUCHED
- BL-008 (Event log append-only): NOT TOUCHED

## Implementation Plan

### Step 1: Populate presentation_semantics in assemble_narrative_brief()

File: `aidm/lens/narrative_brief.py` (the assembler function)

1. Accept `PresentationSemanticsRegistry` as a parameter (or access it from the Lens context).
2. Extract `content_id` from the event payload.
3. Look up `content_id` in the registry.
4. If found, set `presentation_semantics` to the returned `AbilityPresentationEntry`.
5. If not found, leave as `None` (existing behavior).

Estimated: ~5-10 lines of code.

### Step 2: Add Layer B fields to TruthChannel

File: `aidm/lens/truth_channel.py` (or wherever TruthChannel is defined)

1. Add serialization fields for the Layer B data that Spark needs.
2. Populate these fields from `NarrativeBrief.presentation_semantics` when present.
3. When `presentation_semantics` is `None`, omit or null these fields.

Estimated: ~10-15 lines of code.

### Step 3: Tests

1. Test that `assemble_narrative_brief()` populates `presentation_semantics` when a matching registry entry exists.
2. Test that `assemble_narrative_brief()` leaves `presentation_semantics` as `None` when no entry exists.
3. Test that TruthChannel serializes Layer B fields correctly.
4. Verify all existing NarrativeBrief and narration tests still pass.

## Success Criteria

- [ ] `NarrativeBrief.presentation_semantics` is non-None for events with matching content_id in the registry
- [ ] TruthChannel includes Layer B fields when presentation_semantics is present
- [ ] All existing tests pass
- [ ] New tests cover both found and not-found registry lookup paths
- [ ] `git diff` confirms only the target files were modified

## Files Expected to Change

- `aidm/lens/narrative_brief.py` — assembler function
- `aidm/lens/truth_channel.py` (or equivalent) — serialization
- `tests/test_narrative_brief.py` (or equivalent) — new tests

## Files NOT to Change

- `aidm/schemas/presentation_semantics.py` — Layer B schema is correct as-is
- `aidm/schemas/engine_result.py` — EngineResult is not touched
- `aidm/core/event_log.py` — Event schema is not touched
- Any resolver or reducer files

---

*End of WO-GAP-B-001*

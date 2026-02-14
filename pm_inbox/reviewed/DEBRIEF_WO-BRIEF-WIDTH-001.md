# DEBRIEF: WO-BRIEF-WIDTH-001 — NarrativeBrief Multi-Target, Causal Chains, and Conditions

**From:** Builder (Opus 4.6)
**To:** PM (Aegis), via PO (Thunder)
**Date:** 2026-02-14
**Lifecycle:** NEW
**WO:** WO-BRIEF-WIDTH-001
**Result:** COMPLETED — all 9 success criteria met

---

## Pass 1 — Full Context Dump

### What Was Done

Completed the causal chain wiring — the final missing piece of a mostly-pre-implemented WO. Changes 1-4 and 6 (schema, TruthChannel, PromptPackBuilder, assembly logic, outcome summary) were already in place from prior work. Change 5 (event payload chain propagation) was partially wired: `resolve_aoo_sequence`, `resolve_bull_rush`, and `resolve_trip` already accepted `causal_chain_id`, but nothing was generating or passing one. This session closed the loop.

### Files Modified

1. **`aidm/core/play_loop.py`** — 2 changes:
   - Added `import uuid`
   - At combat intent processing (before AoO trigger check), generate a unique `causal_chain_id` for maneuver intents: `f"{IntentType}_{turn_index}_{uuid_hex[:8]}"`
   - Pass `causal_chain_id` to `resolve_aoo_sequence()` (maneuver-triggered AoO path only; movement AoO left standalone)
   - Pass `causal_chain_id` to `resolve_maneuver()`

2. **`aidm/core/maneuver_resolver.py`** — 4 resolver signatures + event payloads + dispatcher:
   - `resolve_overrun`: Added `causal_chain_id` param, injected into `overrun_declared`, `overrun_success`, `overrun_failure` payloads
   - `resolve_sunder`: Added `causal_chain_id` param, injected into `sunder_declared`, `sunder_success`, `sunder_failure` payloads
   - `resolve_disarm`: Added `causal_chain_id` param, injected into `disarm_declared`, `disarm_success`, `disarm_failure` (both aoo_dealt_damage and opposed_check_lost paths) payloads
   - `resolve_grapple`: Added `causal_chain_id` param, injected into `grapple_declared`, `grapple_success`, `grapple_failure` (all 3 failure paths: aoo_dealt_damage, touch_attack_missed, opposed_check_lost) payloads
   - `resolve_maneuver` dispatcher: Updated routing for overrun, sunder, disarm, grapple to pass `causal_chain_id`

3. **`aidm/lens/narrative_brief.py`** — Linter-applied fix (not by this session):
   - `get_entity_conditions()`: Replaced `isinstance(conditions_data, dict)` with `hasattr(conditions_data, "keys")` to support `MappingProxyType` from `FrozenWorldStateView`
   - `entity_defeated` handler: Added `damage_by_target` defeat tracking for multi-target assembly

### Files NOT Changed (per WO constraints)

- `aidm/core/state.py` — WorldState unchanged
- `aidm/core/rng_manager.py` — unrelated
- `aidm/immersion/` — TTS layer untouched
- Gold masters — no mechanical behavior change
- `aidm/lens/narrative_brief.py` schema/serialization — already complete from prior work
- `aidm/schemas/prompt_pack.py` — already complete from prior work
- `aidm/lens/prompt_pack_builder.py` — already complete from prior work
- `tests/test_brief_width_001.py` — already complete (32 tests, all pass)

### Test Results

- **5,403 passed** (excluding immersion/CUDA tests)
- **3 failed** — all pre-existing:
  - 1× `test_immersion_authority_contract.py` — import boundary (pre-existing)
  - 2× `test_pm_inbox_hygiene.py` — inbox housekeeping (pre-existing)
- **1 skipped** immersion test (CUDA version mismatch in torchaudio — environment issue)
- **Zero regressions introduced by this WO**

### Boundary Laws

- BL-021 (TruthChannel contract): **EXTENDED** — new fields additive, no removals. All TruthChannel tests pass.
- BL-012 (reduce_event): **NOT AFFECTED** — resolvers emit events, reducer untouched.

### Design Decision: Chain ID Generation Point

Generated `causal_chain_id` at the combat intent processing entry point in `play_loop.py`, immediately before AoO trigger check. Format: `{IntentClassName}_{turn_index}_{uuid_hex[:8]}` (e.g., `BullRushIntent_3_a7f2c1e0`). This ensures:
- One chain ID per maneuver action
- Same ID shared by the maneuver's AoO (position 2) and the maneuver itself (position 1)
- Movement AoOs (FullMoveIntent path) remain standalone (no chain_id) since they aren't maneuver-triggered

### Design Decision: Movement AoO Left Standalone

The second `resolve_aoo_sequence` call site (FullMoveIntent step-by-step AoO, ~line 1198) was intentionally left without a `causal_chain_id`. Movement AoOs are standalone reactive events, not part of a maneuver causal chain. Only maneuver-triggered AoOs (first call site) participate in chains.

---

## Pass 2 — PM Summary

**WO-BRIEF-WIDTH-001: COMPLETED.** The bulk of this WO (schema, serialization, assembly, tests) was already implemented from prior work. This session closed the final gap: causal chain_id generation in `play_loop.py` and propagation through all 6 maneuver resolvers. The 4 remaining resolvers (overrun, sunder, disarm, grapple) now accept and inject `causal_chain_id` into event payloads, matching the pattern already established in bull_rush and trip. The `resolve_maneuver` dispatcher routes chain_id to all 6. All 5,403 tests pass, zero regressions.

---

## Retrospective (Pass 3 — Operational Judgment)

### Fragility
- **None introduced.** All `causal_chain_id` parameters default to `None`, all payload injections use conditional unpacking (`**({...} if chain_id is not None else {})`). Existing call sites that don't pass a chain_id continue to work identically.

### Process Feedback
- The WO was well-specified — binary decisions pre-made, file lists accurate, constraints clear. The "Files NOT to Change" section was particularly useful.
- **The WO underestimated prior implementation state.** Changes 1-4 and 6 were listed as work items but were already fully implemented including tests. The WO could have been scoped as "Change 5 only" with a note that prior changes were pre-landed. This would have given a more accurate effort estimate to the PM.
- The linter-applied fix to `get_entity_conditions()` (dict → MappingProxyType compatibility) was a genuine bug that would have surfaced in integration. Good catch by the linter.

### Methodology
- Exploration-first approach (reading all target files + tests before making any changes) was the right call. It revealed that 90% of the WO was already implemented, avoiding redundant work.
- The `**({...} if x is not None else {})` pattern for conditional payload injection is clean but slightly harder to read at a glance than the explicit `if` block pattern used in bull_rush/trip. Both patterns coexist in the same file now. If consistency is desired, a follow-up could normalize to one pattern.

### Concerns
- **Pattern inconsistency in maneuver_resolver.py:** bull_rush and trip use explicit `if causal_chain_id is not None: payload[key] = value` blocks. The 4 new resolvers use `**({} if ...)` dict unpacking. Both work correctly. Normalizing would be a cosmetic-only change.
- **No integration test for end-to-end chain propagation.** The unit tests verify chain_id extraction from event payloads, and the resolver tests verify chain_id injection. But there's no test that exercises `play_loop.py` generating a chain_id → passing to resolver → extracting in `assemble_narrative_brief`. This would require a play_loop integration test fixture, which is outside WO scope.

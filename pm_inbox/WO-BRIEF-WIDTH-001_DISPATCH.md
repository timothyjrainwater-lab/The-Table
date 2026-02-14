# WO-BRIEF-WIDTH-001: NarrativeBrief Multi-Target, Causal Chains, and Conditions

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 1
**Priority:** P1 — Fixes 6 of 9 stress-test FAIL cases. Highest-impact narration fidelity WO.
**Source:** RQ-SPRINT-003 (Skin Coherence Stress Test), NarrativeBrief schema gaps

---

## Target Lock

NarrativeBrief currently represents single-target, single-condition, standalone events. This fails 9 of 20 stress-test edge cases (RQ-SPRINT-003). Three structural limitations:

1. **Multi-target blindness** — AoE hitting 5 creatures produces 5 disconnected briefs. Spark never knows it was "one explosion, five victims."
2. **No causal chains** — AoO triggered by bull rush → causes trip = 3 events. Currently produces 3 unrelated briefs.
3. **Single-condition slot** — A target that is prone, grappled, AND flanked gets one `condition_applied` field. Also: `condition_removed` exists in NarrativeBrief but is never serialized to TruthChannel.

## Binary Decisions

1. **Multi-target approach?** Add `additional_targets` tuple to NarrativeBrief. Primary target stays in `target_name`/`severity`/`target_defeated`. Additional targets in the tuple. This keeps backward compatibility — single-target events have empty tuple.
2. **Causal chain approach?** `causal_chain_id` (Optional[str]) + `chain_position` (int). Events sharing the same chain_id are narratively linked. 0 = standalone, 1 = first, 2+ = continuation.
3. **Where does chain_id come from?** The resolver that triggers the chain assigns a chain_id to the originating event. Downstream resolvers (AoO, trip, etc.) inherit it. This means resolvers need to propagate chain_id through events.
4. **Active conditions approach?** `active_conditions` tuple on the brief. Populated from FrozenWorldStateView at assembly time — snapshot of target's current condition stack.
5. **Does TruthChannel grow?** Yes. All new NarrativeBrief fields propagate to TruthChannel so Spark sees them.
6. **Does this touch resolvers?** Only for chain_id propagation in event payloads. No resolver logic changes.

## Contract Spec

### Change 1: Extend NarrativeBrief Schema

In `aidm/lens/narrative_brief.py`, add fields:

```python
# Multi-target
additional_targets: tuple = ()  # ((name: str, severity: str, defeated: bool), ...)

# Causal chain
causal_chain_id: Optional[str] = None
chain_position: int = 0  # 0=standalone, 1=first, 2+=continuation

# Condition stack
active_conditions: tuple = ()   # All conditions currently on target
actor_conditions: tuple = ()    # Conditions on actor affecting this action
```

Update `to_dict()` and `from_dict()` for serialization. All defaults are backward-compatible.

### Change 2: Extend TruthChannel Schema

In `aidm/schemas/prompt_pack.py`, add:

```python
additional_targets: Optional[List[dict]] = None  # [{name, severity, defeated}, ...]
causal_chain_id: Optional[str] = None
chain_position: int = 0
active_conditions: Optional[List[str]] = None
actor_conditions: Optional[List[str]] = None
condition_removed: Optional[str] = None  # BUG FIX: exists in brief, missing from TruthChannel
```

### Change 3: Update PromptPackBuilder

In `aidm/lens/prompt_pack_builder.py`, serialize the new fields from NarrativeBrief to TruthChannel. Also fix the `condition_removed` gap — it exists in NarrativeBrief but is currently dropped during serialization.

### Change 4: Update assemble_narrative_brief()

In `aidm/lens/narrative_brief.py`:

**Multi-target assembly:**
- When multiple `damage_dealt` or `spell_damage_dealt` events share the same originating action, collect all targets into `additional_targets`
- Primary target (first or highest-damage) stays in `target_name`

**Condition assembly:**
- Query `FrozenWorldStateView` for target's active conditions at assembly time
- Query for actor's active conditions
- Populate `active_conditions` and `actor_conditions` tuples

**Causal chain assembly:**
- Check event payloads for `causal_chain_id`
- If present, set `causal_chain_id` and `chain_position` on the brief

### Change 5: Event Payload Chain Propagation

Events that trigger downstream resolvers (AoO, trip-on-charge, etc.) must include `causal_chain_id` in their payloads. This is the minimal resolver touch:
- When a resolver emits an event that could trigger another resolver, attach a `causal_chain_id`
- The chain_id is a unique string (e.g., UUID or "{action_type}_{turn}_{actor}")
- Downstream resolvers copy the chain_id into their own events

### Change 6: Update Outcome Summary

Update outcome summary generation to include multi-target context:
- If `additional_targets` is non-empty, summary includes "affecting {N} targets" or similar
- If `causal_chain_id` is set and `chain_position > 1`, summary references the triggering action

### Constraints

- All new fields must have backward-compatible defaults (empty tuples, None, 0)
- Existing tests must pass without modification
- Do NOT change resolver logic beyond chain_id propagation
- Do NOT implement Spark-side consumption of these fields — that's WO-NARRATION-VALIDATOR scope
- Do NOT change presentation_semantics handling — that's GAP-B-001 follow-on scope
- Do NOT build AoE detection heuristics — use event grouping from resolver output only

### Boundary Laws Affected

- BL-021 (TruthChannel contract): EXTENDED — new fields added to TruthChannel. All additive, no removals.
- BL-012 (reduce_event): NOT AFFECTED — resolvers emit events, reducer is not touched.

## Success Criteria

- [ ] NarrativeBrief has `additional_targets`, `causal_chain_id`, `chain_position`, `active_conditions`, `actor_conditions` fields
- [ ] TruthChannel has matching fields + `condition_removed` fix
- [ ] PromptPackBuilder serializes all new fields
- [ ] Multi-target events (e.g., AoE) produce briefs with populated `additional_targets`
- [ ] `condition_removed` reaches TruthChannel (bug fix)
- [ ] Active conditions populated from FrozenWorldStateView
- [ ] Causal chain_id propagates through at least one resolver chain (AoO is the test case)
- [ ] All existing tests pass without modification
- [ ] New tests: multi-target assembly, causal chain linkage, condition stack population, condition_removed serialization

## Files Expected to Change

- `aidm/lens/narrative_brief.py` — schema + assembly logic
- `aidm/schemas/prompt_pack.py` — TruthChannel extension
- `aidm/lens/prompt_pack_builder.py` — serialization
- Resolver files that trigger chains (AoO, charge, bull rush) — chain_id propagation only
- Test files for new behavior

## Files NOT to Change

- `aidm/core/state.py` — WorldState unchanged
- `aidm/core/rng_manager.py` — unrelated
- `aidm/immersion/` — TTS layer untouched
- Gold masters — no mechanical behavior change

---

*End of WO-BRIEF-WIDTH-001*

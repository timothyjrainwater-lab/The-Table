# Vertical Slice V1 — Minimal Runnable Session

## Overview

**Vertical Slice V1** is the first end-to-end runnable AIDM session milestone. It demonstrates a complete deterministic gameplay loop from prep bundle → play execution → replay verification.

This is **not** a full combat system. It is the smallest working slice that proves the architecture: event sourcing, deterministic execution, doctrine-driven NPC behavior, tactical policy selection, and fully reproducible replay.

## Scope

### What This Includes

- **1 Scene**: Single encounter area with basic terrain
- **1 Monster with Doctrine + Policy**: Goblin with INT 10, tactical envelope, and policy-driven tactic selection
- **2 PCs as Entities**: Stub entities (minimal attributes: position, team, hp)
- **3 Turns Total**: 1 goblin turn, 1 PC turn, 1 goblin turn (policy evaluation only, no full combat resolution)
- **Event Log Output**: Complete JSONL event log with citations
- **Final World State**: Deterministic state snapshot after 3 turns
- **Replay Check**: Verify replay produces identical final state
- **Readable Transcript**: Human-readable turn-by-turn summary (templated output)

### What This Excludes

- **No full combat resolver**: Tactic selection only, no damage/condition application
- **No UI**: CLI output or script execution only
- **No LLM integration**: All policy decisions are deterministic heuristics
- **No complex encounter**: Single monster, simple positioning
- **No time loop**: Manual turn advancement, no time scale integration yet

## Definition of Done

**Acceptance Criteria**:

1. ✅ **Bundle Validation Passes**: SessionBundle with goblin doctrine + scene card validates as "ready"
2. ✅ **Policy Evaluation Works**: `evaluate_tactics()` returns ranked tactics for goblin each turn
3. ✅ **Event Log Generated**: Complete JSONL event log with monotonic IDs and citations
4. ✅ **State Snapshot Captured**: Final WorldState with deterministic hash
5. ✅ **Replay Produces Identical State**: Replay from event log → same final state hash
6. ✅ **Readable Transcript Generated**: Human-readable summary of turn sequence and tactic selections
7. ✅ **Test Suite Still Passes**: All existing tests pass in < 2 seconds
8. ✅ **Deterministic**: Multiple runs produce identical event log and final state

## Non-Goals

**Explicitly Out of Scope for V1**:

- ❌ **Combat resolution**: No attack rolls, damage calculation, or condition application
- ❌ **Movement resolution**: No actual token movement, just position references
- ❌ **Action economy**: No action/move/swift action tracking
- ❌ **Spell effects**: No spell resolution or area-of-effect calculations
- ❌ **Initiative order**: Manual turn ordering for V1
- ❌ **UI/visualization**: No grid display, no token graphics
- ❌ **Narration layer**: No LLM-generated descriptions
- ❌ **Multi-round combat**: 3 turns total, not a full encounter to completion
- ❌ **Character sheets**: PCs are entity stubs with minimal data

## Why This Matters

**Vertical Slice V1 proves the core architecture works**:

1. **Event Sourcing**: All state changes flow through event log
2. **Determinism**: Replay produces identical results
3. **Doctrine Integration**: Monster behavior constrained by tactical envelope
4. **Policy Engine**: Tactical decisions driven by deterministic policy evaluation
5. **Provenance**: Citations attached to events for auditability
6. **Fail-Closed Design**: Invalid inputs blocked by validators
7. **Test Continuity**: New code doesn't break existing tests

## Example Session Flow

### Setup (Prep Phase)

```python
# 1. Create SessionBundle
bundle = SessionBundle(
    id="vertical_slice_v1",
    campaign_id="test_campaign",
    session_number=1,
    created_at="2025-01-15T10:00:00Z",
    scene_cards=[
        SceneCard(
            scene_id="goblin_encounter",
            title="Goblin Ambush",
            description="Forest clearing with 2 PCs and 1 goblin"
        )
    ],
    encounter_specs=[
        EncounterSpec(
            encounter_id="goblin_encounter",
            name="Goblin Ambush",
            creatures=[{"type": "goblin", "count": 1}],
            monster_doctrines=[goblin_doctrine]
        )
    ]
)

# 2. Validate bundle
cert = validate_session_bundle(bundle)
assert cert.status == "ready"
```

### Execution (Play Phase)

```python
# 3. Initialize world state
world_state = WorldState(
    ruleset_version="3.5e",
    entities={
        "goblin_1": {
            "hp_current": 6,
            "hp_max": 6,
            "conditions": [],
            "position": {"x": 0, "y": 0},
            "team": "monsters"
        },
        "pc_fighter": {
            "hp_current": 10,
            "hp_max": 10,
            "conditions": [],
            "position": {"x": 10, "y": 0},
            "team": "party"
        },
        "pc_wizard": {
            "hp_current": 6,
            "hp_max": 6,
            "conditions": [],
            "position": {"x": 15, "y": 5},
            "team": "party"
        }
    }
)

# 4. Initialize event log
event_log = EventLog()

# 5. Turn 1: Goblin evaluates tactics
result = evaluate_tactics(goblin_doctrine, world_state, "goblin_1")
print(f"Goblin selected: {result.selected.candidate.tactic_class}")

# Record tactic selection event
event_log.append(Event(
    event_id=0,
    event_type="tactic_selected",
    timestamp=1.0,
    payload={
        "actor_id": "goblin_1",
        "tactic_class": result.selected.candidate.tactic_class,
        "score": result.selected.score,
        "reasons": result.selected.reasons
    },
    citations=[{"source_id": "e390dfd9143f", "page": 133}]
))

# 6. Turn 2: PC turn (stub action)
event_log.append(Event(
    event_id=1,
    event_type="action_declared",
    timestamp=2.0,
    payload={
        "actor_id": "pc_fighter",
        "action_type": "attack",
        "target_id": "goblin_1"
    }
))

# 7. Turn 3: Goblin evaluates tactics again
result = evaluate_tactics(goblin_doctrine, world_state, "goblin_1")
event_log.append(Event(
    event_id=2,
    event_type="tactic_selected",
    timestamp=3.0,
    payload={
        "actor_id": "goblin_1",
        "tactic_class": result.selected.candidate.tactic_class,
        "score": result.selected.score,
        "reasons": result.selected.reasons
    },
    citations=[{"source_id": "e390dfd9143f", "page": 133}]
))

# 8. Export event log
event_log.to_jsonl("vertical_slice_v1_events.jsonl")

# 9. Capture final state hash
final_hash = world_state.to_deterministic_hash()
print(f"Final state hash: {final_hash}")
```

### Verification (Replay Phase)

```python
# 10. Replay from event log
replay_runner = ReplayRunner()
replay_state = replay_runner.replay_from_jsonl("vertical_slice_v1_events.jsonl")

# 11. Verify replay produces identical state
replay_hash = replay_state.to_deterministic_hash()
assert replay_hash == final_hash, "Replay produced different state!"

print("✅ Vertical Slice V1 Complete")
```

### Readable Transcript Output

```
=== VERTICAL SLICE V1 TRANSCRIPT ===

SCENE: Goblin Ambush
  Forest clearing with 2 PCs and 1 goblin

TURN 1: goblin_1
  Evaluated Tactics:
    - focus_fire (score: 5000)
    - retreat_regroup (score: 3000)
    - attack_nearest (score: 2000)
  Selected: focus_fire
  Rationale: base_score: 1000, focus_fire_bonus: 4000

TURN 2: pc_fighter
  Action: attack (target: goblin_1)

TURN 3: goblin_1
  Evaluated Tactics:
    - retreat_regroup (score: 6000)
    - focus_fire (score: 4500)
    - use_cover (score: 3000)
  Selected: retreat_regroup
  Rationale: base_score: 1000, bloodied_hp_retreat_bonus: 2000, engagement_pressure: 1500

=== END TRANSCRIPT ===

Final State Hash: a3f8d9e7c2b1...
Replay Verified: ✅
```

## Implementation Checklist

- [ ] Create `vertical_slice_v1.py` script in `examples/` or `scripts/`
- [ ] Define goblin_doctrine with derive_tactical_envelope
- [ ] Create SessionBundle with scene + encounter
- [ ] Initialize WorldState with 1 goblin + 2 PCs
- [ ] Execute 3 turns with policy evaluation
- [ ] Generate event log JSONL
- [ ] Capture final state hash
- [ ] Implement replay verification
- [ ] Generate readable transcript
- [ ] Add integration test for vertical slice
- [ ] Document in README.md

## Success Metrics

**V1 is complete when**:

1. Script runs to completion without errors
2. Event log exports to valid JSONL
3. Replay produces identical state hash
4. Transcript is human-readable and accurate
5. All existing tests still pass in < 2 seconds
6. Multiple runs produce deterministic results

## Next Steps (Post-V1)

After Vertical Slice V1 is complete, future packets can build on this foundation:

- **V2**: Add combat resolution (attack rolls, damage, conditions)
- **V3**: Add movement resolution (traversal checks, position updates)
- **V4**: Add spell resolution (area-of-effect, targeting)
- **V5**: Add initiative order and full turn sequence
- **V6**: Add time advancement and effect expiration
- **V7**: Add hazard progression and environmental effects
- **V8**: Add multi-round combat to completion

But first, **prove the architecture works with V1**.

---

**Document Status**: Ready for implementation
**Last Updated**: 2025-02-08 (CP-07D)

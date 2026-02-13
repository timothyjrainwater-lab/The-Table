# CP-13 Monster Combat Integration (Policy → Intent Mapping)

**Document Status**: Locked (binding for future combat packets)
**Last Updated**: 2026-02-08
**Packet**: CP-13 — Monster Combat Integration

## What CP-13 Proved

✅ **Monster policy output maps to combat intents correctly**
- attack_nearest/focus_fire tactics → resolve_monster_combat_intent() → AttackIntent
- 9 integration tests verify mapping, target selection, determinism, RNG isolation
- Preserves CP-09 behavior for unmapped tactics (retreat, etc.)

✅ **Target selection is deterministic**
- Finds enemy entities from WorldState (different team)
- Sorts lexicographically
- Picks first valid (exists + not defeated)
- Test verifies "fighter_alpha" selected over "fighter_zulu"

✅ **Deterministic replay through monster combat**
- Same RNG seed → identical monster attack events → identical final state hash
- Test runs 3 times, verifies hash and event payload identity

✅ **RNG stream isolation preserved**
- Policy evaluation does not affect combat RNG
- Combat RNG uses "combat" stream exclusively
- Same combat seed → same d20 results

✅ **Missing doctrine combat parameters handled correctly**
- Monster without weapon/attack_bonus → no combat intent created
- Preserves CP-09 behavior (emits tactic_selected stub)
- No errors raised (graceful degradation)

✅ **Unmapped tactics preserve CP-09 behavior**
- Tactics like retreat_regroup emit tactic_selected event
- No combat resolution attempted
- Cowardly goblin at bloodied HP correctly selects retreat

✅ **MonsterDoctrine schema extended cleanly**
- Added optional weapon: Optional[Weapon] = None
- Added optional attack_bonus: Optional[int] = None
- Backward compatible: existing doctrines still work
- Serialization (to_dict/from_dict) handles new fields

✅ **execute_turn() integration is non-invasive**
- Doctrine branch extended (not replaced)
- If resolve_monster_combat_intent() returns None, fallback to CP-09 stub
- No changes to CP-12 player combat routing
- All CP-09 vertical slice tests still pass

✅ **Multiple monsters and mixed combat work correctly**
- Multiple monsters execute combat in sequence
- Mixed monster combat + PC combat works
- State propagates correctly between turns

## What Was Intentionally Deferred

The following mechanics are **OUT OF SCOPE for CP-13** and deferred to future packets:

### Combat Mechanics (CP-14+)
- ❌ **FullAttackIntent for monsters**: CP-13 uses AttackIntent only
- ❌ **Iterative attacks for monsters**: Single attack per turn
- ❌ **Special attacks**: Grapple, trip, bull rush, disarm
- ❌ **Natural weapons**: Claw/claw/bite attack sequences
- ❌ **Monster special abilities**: Breath weapons, spell-like abilities, gaze attacks

### Policy Enhancement (CP-14+)
- ❌ **Target selection in policy engine**: Policy currently returns empty target_ids
- ❌ **TacticCandidate with multiple targets**: focus_fire with specific target
- ❌ **Position-based tactics**: use_cover, setup_flank with positions
- ❌ **Dynamic tactic candidate generation**: Multiple candidates per tactic class

### Targeting & Validation (CP-15+)
- ❌ **Range/reach validation**: No distance checks
- ❌ **Line of sight validation**: No LoS checks
- ❌ **Team validation**: Friendly fire allowed
- ❌ **Cover/concealment modifiers**: No tactical modifiers

## Locked Constraints for Future Packets

These design decisions are **binding** for all future monster combat packets:

### Monster Combat Mapping (New in CP-13)
1. **resolve_monster_combat_intent() is the canonical mapper**
   ```python
   def resolve_monster_combat_intent(
       policy_result: TacticalPolicyResult,
       doctrine: MonsterDoctrine,
       actor_id: str,
       world_state: WorldState
   ) -> Optional[AttackIntent]
   ```
   - Returns None if tactic unmapped or missing data
   - Never raises exceptions (graceful degradation)
   - Must be deterministic (same inputs → same output)

2. **Mapped tactics are explicit whitelist**
   - CP-13: {"attack_nearest", "focus_fire"}
   - Future packets may expand this set
   - Unmapped tactics return None (preserve CP-09 behavior)

3. **Target selection fallback logic**
   - Use TacticCandidate.target_ids if present (preferred)
   - If empty, find enemies from WorldState (fallback)
   - Sort lexicographically for determinism
   - Pick first valid (exists + not defeated)
   - No team validation (friendly fire allowed for now)

4. **Missing combat parameters are graceful**
   - doctrine.weapon = None → returns None
   - doctrine.attack_bonus = None → returns None
   - No errors raised, fallback to CP-09 stub

### MonsterDoctrine Schema (Extended in CP-13)
1. **Combat parameters are optional**
   ```python
   @dataclass
   class MonsterDoctrine:
       # ... existing fields ...
       weapon: Optional[Weapon] = None
       attack_bonus: Optional[int] = None
   ```
   - Fields default to None
   - Backward compatible with existing doctrines
   - Future: May add full_attack_bab, natural_weapons, etc.

2. **Serialization includes combat parameters**
   - to_dict() serializes weapon as nested dict
   - from_dict() deserializes weapon from dict
   - None values omitted from JSON output

### execute_turn() Integration (Extended from CP-12)
1. **Doctrine branch order is strict**
   ```python
   # 1. Evaluate policy
   policy_result = evaluate_tactics(doctrine, world_state, actor_id)

   # 2. Attempt combat mapping
   monster_combat_intent = resolve_monster_combat_intent(...)

   # 3. If combat intent created, route to resolver
   if monster_combat_intent is not None:
       combat_events = resolve_attack(...)
       world_state = apply_attack_events(world_state, combat_events)
       narration = "attack_hit" or "attack_miss"

   # 4. Otherwise, fallback to CP-09 stub
   elif policy_result.status == "ok" and policy_result.selected is not None:
       events.append(Event(event_type="tactic_selected", ...))
   ```

2. **RNG is required for monster combat**
   - If resolve_monster_combat_intent() returns intent, rng must be provided
   - Raises ValueError if rng is None with combat intent
   - RNG passed through to resolve_attack()

3. **Narration tokens generated for monster combat**
   - "attack_hit" when attack succeeds
   - "attack_miss" when attack fails
   - Same tokens as player combat (consistent)

### RNG Discipline (From CP-10/CP-11/CP-12)
1. **Monster combat uses "combat" stream**
   - Policy evaluation uses "policy" stream (CP-07)
   - No cross-contamination
   - Tests verify isolation

2. **RNG consumption order must be deterministic**
   - resolve_monster_combat_intent() does not consume RNG
   - resolve_attack() consumes RNG (d20, damage)
   - Order: d20 → [if hit: damage]

## Integration with Vertical Slice V1

CP-13 extends the CP-09/CP-12 play loop with monster combat capability:

### Before CP-13 (Policy Stubs)
```python
# Monsters emit tactic_selected stub
if doctrine is not None:
    policy_result = evaluate_tactics(doctrine, world_state, actor_id)
    if policy_result.status == "ok":
        events.append(Event(event_type="tactic_selected", ...))
```

### After CP-13 (Monster Combat)
```python
# Monsters attempt combat mapping, fallback to stub
if doctrine is not None:
    policy_result = evaluate_tactics(doctrine, world_state, actor_id)

    # Attempt combat mapping (CP-13)
    monster_combat_intent = resolve_monster_combat_intent(...)

    if monster_combat_intent is not None:
        # Route to attack resolver (CP-10)
        combat_events = resolve_attack(monster_combat_intent, ...)
        world_state = apply_attack_events(world_state, combat_events)
        narration = "attack_hit" or "attack_miss"
    elif policy_result.status == "ok":
        # Fallback to CP-09 stub
        events.append(Event(event_type="tactic_selected", ...))
```

### Runnable Example (Pseudo-Code)
```python
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.schemas.attack import Weapon
from aidm.core.doctrine_rules import derive_tactical_envelope
from aidm.core.rng_manager import RNGManager

# Setup world state
world_state = WorldState(
    ruleset_version="3.5e",
    entities={
        "goblin_1": {
            "ac": 15,
            "hp_current": 6,
            "hp_max": 6,
            "position": {"x": 0, "y": 0},
            "team": "monsters",
            "conditions": []
        },
        "fighter": {
            "ac": 16,
            "hp_current": 10,
            "hp_max": 10,
            "position": {"x": 5, "y": 0},
            "team": "party"
        }
    }
)

# Create goblin doctrine with combat parameters
goblin_doctrine = MonsterDoctrine(
    monster_id="goblin",
    source="MM",
    int_score=10,
    wis_score=11,
    creature_type="humanoid",
    weapon=Weapon(
        damage_dice="1d6",
        damage_bonus=0,
        damage_type="slashing"
    ),
    attack_bonus=2,
    citations=[{"source_id": "e390dfd9143f", "page": 133}]
)
goblin_doctrine = derive_tactical_envelope(goblin_doctrine)

# Execute goblin turn
turn_ctx = TurnContext(turn_index=0, actor_id="goblin_1", actor_team="monsters")
rng = RNGManager(master_seed=42)

result = execute_turn(
    world_state=world_state,
    turn_ctx=turn_ctx,
    doctrine=goblin_doctrine,
    rng=rng,
    next_event_id=0,
    timestamp=1.0
)

# Check result
print(f"Status: {result.status}")  # "ok"
print(f"Narration: {result.narration}")  # "attack_hit" or "attack_miss"
print(f"Events: {[e.event_type for e in result.events]}")
# ["turn_start", "attack_roll", "damage_roll" (if hit), "hp_changed" (if hit), "turn_end"]
```

## Test Coverage Summary

**Tier 1 (MUST PASS)**: 6 tests, all passing
- Monster attack_nearest triggers combat resolver
- Target selection is deterministic (lexicographic sort)
- Deterministic replay through monster combat
- Policy RNG isolation preserved
- Missing weapon/attack_bonus produces no combat
- Unmapped tactics emit tactic_selected stub

**Tier 2 (SHOULD PASS)**: 3 tests, all passing
- Monster combat events match CP-10 behavior
- Multiple monsters with combat intents
- Mixed monster combat and PC combat

**Total**: 9 tests, 100% pass rate, < 0.1 seconds runtime

## Success Criterion

**CP-13 is successful** because the following tests pass:

```python
def test_monster_attack_nearest_triggers_combat_resolver():
    """Monster with attack_nearest tactic should trigger attack resolver."""
    # Create goblin doctrine with weapon and attack_bonus
    # Execute turn
    # Verify: status == "ok", combat events present, no tactic_selected stub

def test_deterministic_replay_through_monster_combat():
    """Same RNG seed → identical monster attack events → identical final state."""
    # Run 3 times with same seed
    # Verify: all final states have identical hash, events have identical payloads

def test_policy_rng_isolation_preserved():
    """Policy RNG stream should not affect combat RNG stream."""
    # Run with same combat seed twice
    # Verify: d20 results are identical (combat RNG isolated)
```

These prove the core integration requirements:
1. **Monster policy maps to combat correctly** (tactic → intent → resolver)
2. **Determinism is preserved** (end-to-end replay through monster combat)
3. **RNG isolation is maintained** (policy RNG does not contaminate combat RNG)

---

**Document locked**. Changes require explicit instruction packet approval.

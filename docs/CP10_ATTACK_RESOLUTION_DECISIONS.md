# CP-10 Attack Resolution Decisions

**Document Status**: Locked (binding for future combat packets)
**Last Updated**: 2025-02-08
**Packet**: CP-10 — Attack Resolution Proof

## What CP-10 Proved

✅ **Attack resolution is deterministic**
- Same RNG seed → identical event sequence → identical final state
- 16 tests verify determinism across multiple runs

✅ **Events capture sufficient audit data**
- All inputs to resolution logic recorded in event payloads
- Attack roll events include: d20, bonus, total, AC, hit/miss, natural 20/1
- Damage roll events include: dice, bonus, total, type
- HP change events include: before/after/delta

✅ **WorldState mutations are event-driven only**
- `resolve_attack()` returns events, does not mutate state
- `apply_attack_events()` is the ONLY function that mutates WorldState
- Tests verify original state is unchanged after resolution

✅ **RNG consumption is controlled and ordered**
- All combat randomness uses "combat" RNG stream
- RNG calls are strictly ordered: attack roll (d20) → damage roll (XdY)
- Combat RNG does not pollute policy RNG stream (stream isolation verified)

✅ **Attack mechanics are RAW-compliant** (minimal subset)
- Natural 20 = automatic hit (regardless of AC)
- Natural 1 = automatic miss (regardless of bonus)
- Hit determination: `total >= AC` (where `total = d20 + attack_bonus`)
- Damage applied only on hit
- HP can go negative
- Defeat occurs when HP <= 0

## What Was Intentionally Deferred

The following mechanics are **OUT OF SCOPE for CP-10** and deferred to future packets:

### Combat Mechanics (CP-11+)
- ❌ **Critical confirmation rolls** (threat range 19-20, confirmation vs AC)
- ❌ **Critical damage multipliers** (×2, ×3, ×4)
- ❌ **Iterative attacks** (full attack action, multiple BABs)
- ❌ **Two-weapon fighting** (off-hand attacks, penalties)
- ❌ **Attack of opportunity** (provoked attacks, reach, threatened squares)

### Conditions & Effects (CP-12+)
- ❌ **Damage reduction** (DR X/material, DR X/-)
- ❌ **Energy resistance** (resist fire 10, etc.)
- ❌ **Conditions beyond HP** (stunned, prone, grappled, etc.)
- ❌ **Buffs/debuffs** (bless, bane, prayer, etc.)

### Character State (CP-13+)
- ❌ **Dying state** (-1 to -9 HP, stabilization checks)
- ❌ **Disabled state** (exactly 0 HP, strenuous actions)
- ❌ **Death** (< -10 HP, or HP damage = CON)
- ❌ **Temporary HP** (false life, aid, etc.)

### Equipment & Weapons (CP-14+)
- ❌ **Weapon database** (equipment system, inventory)
- ❌ **Weapon properties** (reach, finesse, light, thrown)
- ❌ **Magic weapons** (enhancement bonuses, special abilities)
- ❌ **Ammunition tracking** (arrows, bolts, sling bullets)

### Tactical Modifiers (CP-15+)
- ❌ **Flanking** (+2 to attack)
- ❌ **Cover** (partial, full, improved)
- ❌ **Concealment** (miss chance 20%/50%)
- ❌ **Size modifiers** (attack bonus, AC modifiers)
- ❌ **Reach** (5ft, 10ft, 15ft+ threatened squares)

## Locked Constraints for Future Packets

These design decisions are **binding** for all future combat-related packets:

### RNG Discipline
1. **All combat randomness MUST use "combat" RNG stream**
   - Attack rolls, damage rolls, critical confirmations, miss chance, etc.
   - Never use `random.randint()` or global RNG

2. **RNG consumption order MUST be deterministic**
   - Document the order of RNG calls in code comments
   - No branching that changes RNG consumption order
   - Tests MUST verify deterministic replay

3. **Stream isolation MUST be preserved**
   - Combat RNG must not affect policy RNG
   - Policy RNG must not affect combat RNG
   - Each stream can be seeded independently for testing

### Event Schema
1. **Events MUST be JSON-serializable**
   - No callables, no lambdas, no custom classes without `to_dict()`
   - Use built-in types: int, str, bool, list, dict

2. **Events MUST capture all resolution inputs**
   - Not just outcomes—include d20 roll, AC, bonuses, etc.
   - Enable full audit trail and replay verification
   - Each event payload should be self-documenting

3. **Event payloads MUST remain backward-compatible**
   - Adding optional fields is OK
   - Removing or renaming fields breaks replay
   - Version events if breaking changes are required

### WorldState Mutations
1. **State mutations ONLY via event application**
   - Resolver functions return events only
   - `apply_*_events()` functions are the only mutators
   - Tests verify original state is unchanged after resolution

2. **HP MUST be stored as integer**
   - Can go negative (record actual HP, not clamped to 0)
   - No string tags like "invulnerable" or "immune"
   - Temporary HP tracked separately (when implemented)

3. **AC MUST be stored as integer**
   - Touch AC, flat-footed AC tracked separately (when implemented)
   - No string tags for special AC properties

4. **Damage type MUST be stored as string**
   - Physical: "slashing", "piercing", "bludgeoning"
   - Energy: "fire", "cold", "acid", "electric", "sonic"
   - Special: "force", "negative", "positive"
   - Enables future DR/resistance logic without event schema changes

### Attack Resolution API
1. **resolve_attack() signature is canonical**
   ```python
   def resolve_attack(
       intent: AttackIntent,
       world_state: WorldState,
       rng: RNGManager,
       next_event_id: int,
       timestamp: float
   ) -> List[Event]
   ```
   - Future combat functions should follow this pattern
   - Intent → WorldState → RNG → Events

2. **Weapon stats are inline in AttackIntent**
   - No weapon lookup system in CP-10
   - Future packets may add equipment database, but intent must remain self-contained

## Explicit Non-Goals

These are **NOT GOALS** for the AIDM project (as of CP-10):

❌ **Real-time combat** (system optimizes for correctness, not speed)
❌ **AI tactics beyond policy engine** (no RL, no minimax, no search trees)
❌ **Homebrew rules** (strict RAW D&D 3.5 only)
❌ **Multi-system support** (no 5e, Pathfinder, OSR, etc.)
❌ **Graphical combat** (event log is output, not animations)

## Open Questions (To Resolve in Later Packets)

These questions arose during CP-10 implementation but were deferred:

### Equipment System (CP-14?)
- **Q**: How do we handle weapon lookup? Inline stats? Database?
- **A (deferred)**: CP-10 uses inline weapon stats in AttackIntent. Future packets will decide if/when to add equipment database.

### Critical Hits (CP-11?)
- **Q**: Should critical threat range be weapon property or hardcoded?
- **A (deferred)**: CP-10 treats all weapons as 20/×2. Future packet will add threat range (19-20, 18-20) and multipliers.

### Buff/Debuff Application (CP-12?)
- **Q**: How do we apply temporary attack bonuses (bless, prayer, etc.)?
- **A (deferred)**: CP-10 uses static `attack_bonus` in intent. Future packet will define buff system and modifier stacking rules.

### Miss Chance vs AC (CP-15?)
- **Q**: Does concealment roll before or after attack roll?
- **A (deferred)**: CP-10 has no concealment. Future packet will define miss chance resolution order (likely: attack roll → hit check → miss chance check).

### Death vs Defeat (CP-13?)
- **Q**: Should "defeated" mean unconscious, dying, or dead?
- **A (deferred)**: CP-10 uses `entity_defeated` flag when HP <= 0. Future packet will distinguish dying (-1 to -9), disabled (0), and dead (< -10).

## Integration with Vertical Slice V1

CP-10 attack resolution can be integrated into the Vertical Slice V1 play loop by:

1. Replacing stub PC actions with actual attack resolution
2. Wiring goblin policy `attack_nearest` tactic to `resolve_attack()`
3. Applying attack events to WorldState after each turn
4. Verifying HP changes appear in final state and transcript

**Example integration** (pseudo-code):
```python
# In execute_turn() for monster with attack_nearest tactic
if tactic == "attack_nearest":
    target_id = find_nearest_enemy(world_state, actor_id)

    intent = AttackIntent(
        attacker_id=actor_id,
        target_id=target_id,
        attack_bonus=attacker_bab + attacker_str_mod,
        weapon=attacker_weapon  # From monster doctrine or bundle
    )

    attack_events = resolve_attack(intent, world_state, rng, next_event_id, timestamp)
    events.extend(attack_events)

    # Apply events to get updated state
    world_state = apply_attack_events(world_state, attack_events)
```

**Not implemented in CP-10**: This integration is deferred to CP-11 (full attack sequence).

## Test Coverage Summary

**Tier 1 (MUST PASS)**: 9 tests, all passing
- Deterministic replay
- Hit/miss logic (meets AC, natural 20, natural 1)
- Damage application (on hit, not on miss)
- Event payload completeness
- No direct state mutation

**Tier 2 (SHOULD PASS)**: 7 tests, all passing
- RNG stream isolation
- Negative HP recording
- Event ID monotonicity
- JSONL serialization
- Entity defeat

**Total**: 16 tests, 100% pass rate, < 0.1 seconds runtime

## Success Criterion

**CP-10 is successful** because the following test passes:

```python
def test_attack_resolution_deterministic_replay():
    """Same RNG seed → identical events → identical final state."""
    # Run attack resolution 3 times with seed=42
    # Verify all 3 runs produce byte-identical events
    # Verify all 3 final states have identical hash
```

This proves the core architectural requirement: **deterministic mechanics resolution**.

---

**Document locked**. Changes require explicit instruction packet approval.

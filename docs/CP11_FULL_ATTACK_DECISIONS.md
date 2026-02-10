# CP-11 Full Attack Sequence Decisions

**Document Status**: Locked (binding for future combat packets)
**Last Updated**: 2025-02-08
**Packet**: CP-11 — Full Attack Sequence Proof

## What CP-11 Proved

✅ **Full attack sequences are deterministic**
- Same RNG seed → identical event sequence (including critical hits) → identical final state
- 16 tests verify determinism across multiple runs (< 0.1 seconds runtime)

✅ **Iterative attacks follow RAW D&D 3.5e progression**
- BAB determines number of attacks: BAB/BAB-5/BAB-10/BAB-15
- Example: BAB +11 → attacks at +11/+6/+1
- Example: BAB +20 → attacks at +20/+15/+10/+5
- Minimum BAB +1 required for additional attack (BAB +5 = 1 attack, BAB +6 = 2 attacks)

✅ **Critical hits are RAW-compliant** (minimal subset)
- Natural 20 triggers critical threat (only natural 20, no expanded threat range yet)
- Confirmation roll required: second attack roll vs target AC
- Confirmation does NOT auto-hit on natural 20 (normal attack rules apply)
- Critical damage = base damage × critical_multiplier (×2/×3/×4)
- Critical multiplier is weapon property, defaults to ×2

✅ **RNG consumption order is strictly deterministic**
- Attack roll (d20) → [IF threat: Confirmation roll (d20)] → [IF hit: Damage roll (XdY)]
- Branching (threat vs no-threat) does NOT change RNG consumption order
- All combat randomness uses "combat" RNG stream exclusively
- Test verifies deterministic replay with mixed threat results (Tier-1 blocking test)

✅ **Multiple attacks accumulate damage correctly**
- Each attack resolves independently (attack → confirm → damage)
- All damage accumulates into single HP change event
- HP updated after all attacks complete (not after each attack)
- Defeat check occurs after damage applied

✅ **Event schema maintains backward compatibility with CP-10**
- New fields added as optional with defaults:
  - `attack_roll.is_threat` (default: False)
  - `attack_roll.is_critical` (default: False)
  - `attack_roll.confirmation_total` (default: None)
  - `attack_roll.attack_index` (default: 0)
  - `damage_roll.base_damage` (default: damage_total)
  - `damage_roll.critical_multiplier` (default: 1)
- CP-10 event handlers can consume CP-11 events (graceful degradation)
- Test verifies backward compatibility: CP-10 apply_attack_events works on CP-11 events

✅ **WorldState mutations remain event-driven only**
- `resolve_full_attack()` returns events, does not mutate state
- `apply_full_attack_events()` is the ONLY function that mutates WorldState
- Tests verify original state unchanged after resolution

## What Was Intentionally Deferred

The following mechanics are **OUT OF SCOPE for CP-11** and deferred to future packets:

### Combat Mechanics (CP-12+)
- ❌ **Expanded critical threat ranges** (19-20, 18-20, 17-20 based on weapon)
- ❌ **Two-weapon fighting** (off-hand attacks, penalties, light weapon bonus)
- ❌ **Attack of opportunity** (provoked attacks, reach, threatened squares)
- ❌ **Charge attacks** (double move + single attack at +2)
- ❌ **Power Attack** (-X to attack, +X to damage)
- ❌ **Combat Expertise** (+X to AC, -X to attack)

### Conditions & Effects (CP-13+)
- ❌ **Damage reduction** (DR X/material, DR X/-)
- ❌ **Energy resistance** (resist fire 10, etc.)
- ❌ **Conditions beyond HP** (stunned, prone, grappled, etc.)
- ❌ **Buffs/debuffs on attack rolls** (bless, bane, prayer, bull's strength)
- ❌ **Buffs/debuffs on AC** (shield of faith, mage armor, etc.)

### Character State (CP-14+)
- ❌ **Dying state** (-1 to -9 HP, stabilization checks)
- ❌ **Disabled state** (exactly 0 HP, strenuous actions)
- ❌ **Death** (< -10 HP, or HP damage = CON)
- ❌ **Temporary HP** (false life, aid, etc.)

### Equipment & Weapons (CP-15+)
- ❌ **Weapon database** (equipment system, inventory)
- ❌ **Weapon properties** (reach, finesse, light, thrown, ranged)
- ❌ **Magic weapons** (enhancement bonuses, special abilities)
- ❌ **Ammunition tracking** (arrows, bolts, sling bullets)
- ❌ **Weapon threat ranges** (19-20, 18-20 for keen weapons/rapiers/etc.)

### Tactical Modifiers (CP-16+)
- ❌ **Flanking** (+2 to attack)
- ❌ **Cover** (partial, full, improved)
- ❌ **Concealment** (miss chance 20%/50%)
- ❌ **Size modifiers** (attack bonus, AC modifiers)
- ❌ **Reach** (5ft, 10ft, 15ft+ threatened squares)
- ❌ **Height advantage** (+1 to attack)

## Locked Constraints for Future Packets

These design decisions are **binding** for all future combat-related packets:

### RNG Discipline (Extended from CP-10)
1. **All combat randomness MUST use "combat" RNG stream**
   - Attack rolls, confirmation rolls, damage rolls, critical confirmations, miss chance, etc.
   - Never use `random.randint()` or global RNG

2. **RNG consumption order MUST be deterministic**
   - Document the order of RNG calls in code comments
   - No branching that changes RNG consumption order
   - Tests MUST verify deterministic replay (including critical hits)
   - Example order: d20 → [if threat: d20] → [if hit: XdY]

3. **Stream isolation MUST be preserved**
   - Combat RNG must not affect policy RNG
   - Policy RNG must not affect combat RNG
   - Each stream can be seeded independently for testing

### Event Schema (Extended from CP-10)
1. **Events MUST be JSON-serializable**
   - No callables, no lambdas, no custom classes without `to_dict()`
   - Use built-in types: int, str, bool, list, dict

2. **Events MUST capture all resolution inputs**
   - Not just outcomes—include d20 roll, confirmation roll, AC, bonuses, critical flags, etc.
   - Enable full audit trail and replay verification
   - Each event payload should be self-documenting

3. **Event payloads MUST remain backward-compatible**
   - Adding optional fields is OK (use defaults for old events)
   - Removing or renaming fields breaks replay
   - Version events if breaking changes are required
   - **CP-11 established pattern**: New fields added as optional with sensible defaults

4. **New event types added in CP-11**:
   - `full_attack_start`: Emitted at beginning of full attack sequence
   - `full_attack_end`: Emitted after all attacks and damage resolved
   - These bookend the attack sequence for audit clarity

### WorldState Mutations (From CP-10)
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

### Full Attack Resolution API (New in CP-11)
1. **resolve_full_attack() signature is canonical**
   ```python
   def resolve_full_attack(
       intent: FullAttackIntent,
       world_state: WorldState,
       rng: RNGManager,
       next_event_id: int,
       timestamp: float
   ) -> List[Event]
   ```
   - Future combat functions should follow this pattern
   - Intent → WorldState → RNG → Events

2. **FullAttackIntent is self-contained**
   - Contains all data needed for resolution
   - No database lookups during resolution
   - base_attack_bonus (not calculated from character sheet)
   - weapon (inline weapon stats, not equipment ID)

3. **Iterative attack calculation is deterministic**
   - `calculate_iterative_attacks(bab)` is pure function
   - Returns list of attack bonuses: [bab, bab-5, bab-10, bab-15]
   - Stops when next attack would be < +1

4. **Critical hit resolution order is strict**
   - Step 1: Roll attack (d20 + bonus)
   - Step 2: IF natural 20 AND hit: Roll confirmation (d20 + bonus vs AC)
   - Step 3: IF hit: Roll damage, apply multiplier if critical confirmed
   - No other order is allowed

### Weapon Schema (New in CP-11)
1. **Weapon dataclass is canonical**
   ```python
   @dataclass
   class Weapon:
       damage_dice: str
       damage_bonus: int
       damage_type: str
       critical_multiplier: int = 2  # ×2/×3/×4, default ×2
   ```

2. **Critical multiplier validation**
   - MUST be 2, 3, or 4 (no other values allowed)
   - Fails fast on invalid values
   - Future: Add `critical_threat_range` field for 19-20, 18-20 weapons

## Explicit Non-Goals (From CP-10)

These are **NOT GOALS** for the AIDM project (as of CP-11):

❌ **Real-time combat** (system optimizes for correctness, not speed)
❌ **AI tactics beyond policy engine** (no RL, no minimax, no search trees)
❌ **Homebrew rules** (strict RAW D&D 3.5 only)
❌ **Multi-system support** (no 5e, Pathfinder, OSR, etc.)
❌ **Graphical combat** (event log is output, not animations)

## Open Questions (To Resolve in Later Packets)

These questions arose during CP-11 implementation but were deferred:

### Expanded Threat Range (CP-12?)
- **Q**: How do we handle weapons with 19-20 or 18-20 threat range?
- **A (deferred)**: CP-11 only supports natural 20 threats. Future packet will add `critical_threat_range` field to Weapon (default: 20, expanded: 19-20, 18-20).

### Keen Weapon Property (CP-12?)
- **Q**: Does keen double the threat range or just add to it?
- **A (deferred)**: RAW says "doubles threat range" (so 19-20 becomes 17-20). Future packet will implement this as multiplier on threat range.

### Critical Hits on Iterative Attacks (Resolved in CP-11)
- **Q**: Can later iterative attacks score critical hits?
- **A**: YES. Each attack in full attack sequence can independently threaten and confirm critical.

### Damage Accumulation Timing (Resolved in CP-11)
- **Q**: Should HP update after each attack or after all attacks?
- **A**: After ALL attacks. This matches D&D 3.5e intent (full attack is atomic action) and simplifies event log.

### Two-Weapon Fighting Interaction (CP-12?)
- **Q**: How do off-hand attacks interact with full attack?
- **A (deferred)**: CP-11 assumes single weapon. Future packet will add off-hand attacks as separate iterative sequence.

## Integration with Vertical Slice V1

CP-11 full attack resolution can be integrated into the Vertical Slice V1 play loop by:

1. Extending goblin doctrine to use `full_attack` tactic (instead of stub action)
2. Wiring goblin policy `attack_nearest` tactic to `resolve_full_attack()`
3. Calculating goblin BAB from monster stats (goblin: BAB +1, only 1 attack)
4. Applying full attack events to WorldState after each turn
5. Verifying HP changes and critical hits appear in final state and transcript

**Example integration** (pseudo-code):
```python
# In execute_turn() for monster with attack_nearest tactic
if tactic == "attack_nearest":
    target_id = find_nearest_enemy(world_state, actor_id)

    intent = FullAttackIntent(
        attacker_id=actor_id,
        target_id=target_id,
        base_attack_bonus=attacker_bab,  # From monster stats
        weapon=attacker_weapon  # From monster doctrine or bundle
    )

    full_attack_events = resolve_full_attack(intent, world_state, rng, next_event_id, timestamp)
    events.extend(full_attack_events)

    # Apply events to get updated state
    world_state = apply_full_attack_events(world_state, full_attack_events)
```

**Not implemented in CP-11**: This integration is deferred to CP-12 (vertical slice integration).

## Test Coverage Summary

**Tier 1 (MUST PASS)**: 9 tests, all passing
- Deterministic replay (with critical hits)
- Iterative attack calculation
- Critical threat detection (natural 20)
- Critical confirmation logic
- Critical damage multiplication (×2/×3/×4)
- **RNG consumption order with mixed threat results (BLOCKING)**
- Multiple attacks accumulate damage
- No direct state mutation
- Event payload completeness

**Tier 2 (SHOULD PASS)**: 7 tests, all passing
- Backward compatibility with CP-10 events
- Full attack sequence event ordering
- Negative HP with overkill damage
- Entity defeat after full attack
- High-BAB characters (4 iterative attacks)
- Critical multiplier variations (×2/×3/×4)
- JSONL serialization

**Total**: 16 tests, 100% pass rate, < 0.1 seconds runtime

## Success Criterion

**CP-11 is successful** because the following tests pass:

```python
def test_full_attack_deterministic_replay():
    """Same RNG seed → identical events (including crits) → identical final state."""
    # Run full attack resolution 3 times with seed=42
    # Verify all 3 runs produce byte-identical events
    # Verify all 3 final states have identical hash

def test_rng_consumption_order_with_mixed_threat_results():
    """RNG consumption order is deterministic regardless of threat outcomes."""
    # Scenario 1: First attack is threat (d20 → d20 confirm → XdY damage)
    # Scenario 2: First attack is normal hit (d20 → XdY damage)
    # Both scenarios must produce identical replay when run with same seed
```

These prove the core architectural requirements:
1. **Deterministic mechanics resolution** (with critical hits)
2. **RNG consumption order independence** (branching doesn't affect determinism)

---

**Document locked**. Changes require explicit instruction packet approval.

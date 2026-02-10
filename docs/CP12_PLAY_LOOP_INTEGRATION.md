# CP-12 Play Loop Combat Integration

**Document Status**: Locked (binding for future combat packets)
**Last Updated**: 2025-02-08
**Packet**: CP-12 — Combat Integration into Play Loop

## What CP-12 Proved

✅ **Combat intents route through play loop correctly**
- AttackIntent → execute_turn() → resolve_attack() → events → WorldState
- FullAttackIntent → execute_turn() → resolve_full_attack() → events → WorldState
- 13 integration tests verify routing, validation, and determinism

✅ **Intent validation is deterministic and fail-closed**
- Actor must match turn actor (intent_actor_mismatch)
- Target must exist in WorldState (target_not_found)
- Target must not be defeated (target_already_defeated)
- Validation failures emit intent_validation_failed event
- Invalid intents produce no state change

✅ **TurnResult schema extended for status tracking**
- status: "ok" | "invalid_intent" | "requires_clarification"
- failure_reason: Optional[str] for error messages
- narration: Optional[str] for narration tokens
- Backward compatible with CP-09 vertical slice tests

✅ **Narration tokens are deterministic**
- "attack_hit" when attack succeeds
- "attack_miss" when attack fails
- "full_attack_complete" for full attack sequences
- No prose generation (token-based only)

✅ **WorldState changes only via events**
- execute_turn() does NOT mutate state directly
- Combat resolvers return events only
- apply_attack_events() / apply_full_attack_events() are sole mutators
- Original WorldState unchanged after execute_turn()

✅ **Deterministic replay through play loop**
- Same RNG seed → identical events → identical final state hash
- Works with combat intents (AttackIntent, FullAttackIntent)
- Works with policy-based resolution (backward compatible with CP-09)

✅ **Backward compatibility maintained**
- CP-09 Vertical Slice V1 tests still pass (5/5)
- Policy-based monster turns still work (no combat intent)
- PC stub actions still work (no combat intent)

## What Was Intentionally Deferred

The following mechanics are **OUT OF SCOPE for CP-12** and deferred to future packets:

### Combat Mechanics (CP-13+)
- ❌ **Monster combat intents**: Monsters still use policy stubs, combat deferred to CP-13
- ❌ **Tactic-to-intent mapping**: attack_nearest → AttackIntent routing deferred
- ❌ **Initiative system**: Turn order still manually specified via TurnContext sequence
- ❌ **Movement actions**: No move intents, no position updates
- ❌ **Opportunity attacks**: No provoked attacks, no reach validation

### Targeting & Validation (CP-14+)
- ❌ **Range/reach validation**: No distance checks (deferred)
- ❌ **Line of sight validation**: No LoS checks (deferred)
- ❌ **Team validation**: Allow friendly fire (no team checks)
- ❌ **Target selection automation**: Targets must be explicitly specified

### Narration & UI (CP-15+)
- ❌ **Prose generation**: Only deterministic tokens returned
- ❌ **Narration templates**: No natural language narration
- ❌ **UI hooks**: No UI integration, tokens only
- ❌ **Animation triggers**: No visual effect hooks

## Locked Constraints for Future Packets

These design decisions are **binding** for all future play loop packets:

### Play Loop Architecture (Extended from CP-09)
1. **execute_turn() is the canonical entry point**
   - No parallel process_player_intent() or execute_action() functions
   - All turn execution flows through this function
   - Optional combat_intent parameter for combat actions

2. **Turn structure is enforced**
   - Combat intents must match turn actor (intent.attacker_id == turn_ctx.actor_id)
   - Turn-agnostic combat is forbidden (must execute during actor's turn)
   - TurnContext remains authoritative for actor identity

3. **TurnResult schema is canonical**
   ```python
   @dataclass
   class TurnResult:
       status: str  # "ok" | "invalid_intent" | "requires_clarification"
       world_state: WorldState
       events: List[Event]
       turn_index: int
       failure_reason: Optional[str] = None
       narration: Optional[str] = None
   ```

### Intent Validation (New in CP-12)
1. **Actor validation is mandatory**
   - intent.attacker_id MUST match turn_ctx.actor_id
   - Mismatch → invalid_intent + intent_validation_failed event

2. **Target validation is mandatory**
   - Target must exist in WorldState.entities
   - Target must not have defeated=True
   - No team validation (friendly fire allowed)
   - No range/reach validation (deferred)

3. **Validation failures are logged**
   - Emit intent_validation_failed event with reason payload
   - Return TurnResult with status="invalid_intent"
   - WorldState unchanged on validation failure

### Event Schema (Extended from CP-10/CP-11)
1. **New event type: intent_validation_failed**
   - Emitted when combat intent fails validation
   - Payload contains: actor_id, reason, turn_index
   - Optional fields: target_id, intent_actor (context-dependent)

2. **Reason codes for validation failures**
   - "intent_actor_mismatch": intent.attacker_id != turn_ctx.actor_id
   - "target_not_found": target_id not in WorldState.entities
   - "target_already_defeated": target.defeated == True

3. **Event ordering within turn**
   - turn_start (always first)
   - intent_validation_failed OR combat events (attack_roll, damage_roll, etc.)
   - turn_end (always last)

### Narration Tokens (New in CP-12)
1. **Tokens are deterministic strings**
   - "attack_hit": attack succeeded
   - "attack_miss": attack failed
   - "full_attack_complete": full attack sequence finished
   - No prose, no templates, no randomization

2. **Tokens are optional**
   - TurnResult.narration may be None (e.g., policy-based turns, validation failures)
   - Presence of token indicates successful combat action

3. **Token generation is resolver-specific**
   - AttackIntent → "attack_hit" or "attack_miss"
   - FullAttackIntent → "full_attack_complete"
   - Future intents may define new tokens

### RNG Discipline (From CP-10/CP-11)
1. **RNG must be provided for combat intents**
   - execute_turn() requires rng parameter if combat_intent is not None
   - ValueError raised if rng is None with combat intent
   - RNG passed through to resolve_attack() / resolve_full_attack()

2. **RNG stream isolation preserved**
   - Combat intents use "combat" stream
   - Policy evaluation uses "policy" stream
   - No cross-contamination

## Integration with Vertical Slice V1

CP-12 extends the CP-09 Vertical Slice V1 play loop with combat capability:

### Before CP-12 (Policy-Only)
```python
# Monsters use policy evaluation
if doctrine is not None:
    policy_result = evaluate_tactics(doctrine, world_state, actor_id)
    # Emit tactic_selected event

# PCs emit stub actions
else:
    # Emit action_declared stub
```

### After CP-12 (Combat-Enabled)
```python
# If combat intent provided, route to resolver
if combat_intent is not None:
    # Validate intent
    # Route to resolve_attack() or resolve_full_attack()
    # Apply events to WorldState
    # Generate narration token

# Otherwise, use policy-based resolution (backward compatible)
elif doctrine is not None:
    policy_result = evaluate_tactics(doctrine, world_state, actor_id)
else:
    # PC stub action
```

### Runnable Example (Pseudo-Code)
```python
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.rng_manager import RNGManager

# Setup world state
world_state = WorldState(
    ruleset_version="3.5e",
    entities={
        "fighter": {"ac": 16, "hp_current": 12, "hp_max": 12},
        "goblin": {"ac": 15, "hp_current": 6, "hp_max": 6}
    }
)

# Create combat intent
intent = AttackIntent(
    attacker_id="fighter",
    target_id="goblin",
    attack_bonus=5,
    weapon=Weapon(damage_dice="1d8", damage_bonus=3, damage_type="slashing")
)

# Execute turn with combat intent
rng = RNGManager(master_seed=42)
turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

result = execute_turn(
    world_state=world_state,
    turn_ctx=turn_ctx,
    combat_intent=intent,
    rng=rng,
    next_event_id=0,
    timestamp=1.0
)

# Check result
if result.status == "ok":
    print(f"Narration: {result.narration}")  # "attack_hit" or "attack_miss"
    print(f"Goblin HP: {result.world_state.entities['goblin']['hp_current']}")
else:
    print(f"Validation failed: {result.failure_reason}")
```

## Test Coverage Summary

**Tier 1 (MUST PASS)**: 8 tests, all passing
- Player intent triggers correct resolver (AttackIntent, FullAttackIntent)
- Events match CP-10/CP-11 behavior (identical to standalone)
- WorldState changes only via events (no direct mutation)
- Deterministic replay through full loop (same seed → same hash)
- Invalid intent produces no state change (actor mismatch, target not found, target defeated)

**Tier 2 (SHOULD PASS)**: 5 tests, all passing
- Narration tokens correct (attack_hit, attack_miss, full_attack_complete)
- Mixed attack/full attack works (both intents in sequence)
- Backward compatibility preserved (policy-based resolution still works)

**Total**: 13 tests, 100% pass rate, < 0.1 seconds runtime

## Success Criterion

**CP-12 is successful** because the following tests pass:

```python
def test_attack_intent_triggers_cp10_resolver():
    """AttackIntent routes to resolve_attack() and emits attack events."""
    # Create world state, intent, RNG
    # Execute turn with combat_intent parameter
    # Verify: status == "ok", events include attack_roll, HP changes applied

def test_invalid_intent_actor_mismatch():
    """Intent with wrong actor fails validation and produces no state change."""
    # Create intent with attacker != turn actor
    # Execute turn
    # Verify: status == "invalid_intent", validation event emitted, state unchanged

def test_deterministic_replay_through_loop():
    """Same RNG seed produces identical state hash through full play loop."""
    # Run 3 times with same seed
    # Verify: all final states have identical hash, events have identical payloads
```

These prove the core integration requirements:
1. **Combat intents route correctly** (validation → resolver → events → state)
2. **Invalid intents are rejected** (fail-closed validation with audit trail)
3. **Determinism is preserved** (end-to-end replay through play loop)

---

**Document locked**. Changes require explicit instruction packet approval.

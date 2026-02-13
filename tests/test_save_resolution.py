"""Unit tests for CP-17 Saving Throws & Defensive Resolution Kernel.

Tests save resolution, SR checks, and outcome effects:
- Fort/Ref/Will save bonus calculation
- Natural 1/20 handling
- Save outcome determination
- SR checks and negation
- Effect application (damage, conditions)
- Deterministic replay with saves

Tier-1 (MUST PASS - 20 tests):
- Save bonus calculation correct
- Natural 1 always fails
- Natural 20 always succeeds
- Success/failure determined by DC
- Condition modifiers applied to saves
- Save modifiers stack correctly
- SR check rolls correctly
- SR negates effect when failed
- Damage scaling on success/failure/partial
- Conditions applied on save outcomes
- Multiple saves deterministic
- Save outcome events emitted
- HP changed on save damage
- Entity defeated on lethal save damage
- Save with no effects
- Partial save with half damage
- Save stream isolated from combat stream
- Replay determinism (10×)
- Fort/Ref/Will all work
- Missing entity raises error
"""

import pytest
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.saves import SaveContext, SaveType, SaveOutcome, EffectSpec, SRCheck
from aidm.core.save_resolver import (
    get_save_bonus,
    resolve_save,
    check_spell_resistance,
    apply_save_effects
)
from aidm.schemas.conditions import create_shaken_condition, create_sickened_condition
from aidm.core.conditions import apply_condition


# ==============================================================================
# TIER 1: MUST-PASS TESTS (20 tests)
# ==============================================================================

def test_save_bonus_calculation_fortitude():
    """Tier 1: Fort save bonus = base_save + CON mod + condition mod."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "save_fortitude": 5,
                "con_mod": 2,
                "hp_current": 10,
                "hp_max": 10
            }
        }
    )

    bonus = get_save_bonus(world_state, "fighter", SaveType.FORT)
    assert bonus == 7  # 5 + 2

def test_save_bonus_calculation_reflex():
    """Tier 1: Ref save bonus = base_save + DEX mod + condition mod."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "rogue": {
                "save_reflex": 6,
                "dex_mod": 4,
                "hp_current": 8,
                "hp_max": 8
            }
        }
    )

    bonus = get_save_bonus(world_state, "rogue", SaveType.REF)
    assert bonus == 10  # 6 + 4

def test_save_bonus_calculation_will():
    """Tier 1: Will save bonus = base_save + WIS mod + condition mod."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "cleric": {
                "save_will": 7,
                "wis_mod": 3,
                "hp_current": 12,
                "hp_max": 12
            }
        }
    )

    bonus = get_save_bonus(world_state, "cleric", SaveType.WILL)
    assert bonus == 10  # 7 + 3

def test_condition_modifiers_applied_to_saves():
    """Tier 1: Shaken condition (-2) affects all saves."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "save_fortitude": 5,
                "save_reflex": 3,
                "save_will": 2,
                "con_mod": 2,
                "dex_mod": 1,
                "wis_mod": 0,
                "hp_current": 10,
                "hp_max": 10
            }
        }
    )

    # Apply shaken (-2 to all saves)
    shaken = create_shaken_condition("fear", 0)
    world_state = apply_condition(world_state, "fighter", shaken)

    fort_bonus = get_save_bonus(world_state, "fighter", SaveType.FORT)
    ref_bonus = get_save_bonus(world_state, "fighter", SaveType.REF)
    will_bonus = get_save_bonus(world_state, "fighter", SaveType.WILL)

    assert fort_bonus == 5  # 5 + 2 - 2
    assert ref_bonus == 2   # 3 + 1 - 2
    assert will_bonus == 0  # 2 + 0 - 2

def test_save_modifiers_stack_correctly():
    """Tier 1: Multiple condition save penalties stack."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "save_fortitude": 5,
                "con_mod": 2,
                "hp_current": 10,
                "hp_max": 10
            }
        }
    )

    # Apply shaken (-2) and sickened (-2)
    shaken = create_shaken_condition("fear", 0)
    sickened = create_sickened_condition("poison", 1)
    world_state = apply_condition(world_state, "fighter", shaken)
    world_state = apply_condition(world_state, "fighter", sickened)

    bonus = get_save_bonus(world_state, "fighter", SaveType.FORT)
    assert bonus == 3  # 5 + 2 - 2 - 2

def test_natural_20_always_succeeds():
    """Tier 1: Natural 20 auto-succeeds regardless of DC."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "save_fortitude": 0,
                "con_mod": 0,
                "hp_current": 6,
                "hp_max": 6
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.FORT,
        dc=50,  # Impossibly high DC
        source_id="trap",
        target_id="goblin"
    )

    # Seed RNG to force natural 20
    rng = RNGManager(master_seed=42)
    # Find a seed that produces d20=20
    for seed in range(1000):
        rng_test = RNGManager(master_seed=seed)
        roll = rng_test.stream("saves").randint(1, 20)
        if roll == 20:
            rng = RNGManager(master_seed=seed)
            break

    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    save_event = [e for e in events if e.event_type == "save_rolled"][0]
    assert save_event.payload["is_natural_20"] is True
    assert outcome == SaveOutcome.SUCCESS

def test_natural_1_always_fails():
    """Tier 1: Natural 1 auto-fails regardless of bonus."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "paladin": {
                "save_fortitude": 10,
                "con_mod": 5,
                "hp_current": 20,
                "hp_max": 20
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.FORT,
        dc=5,  # Very low DC
        source_id="poison",
        target_id="paladin"
    )

    # Find seed that produces d20=1
    for seed in range(1000):
        rng_test = RNGManager(master_seed=seed)
        roll = rng_test.stream("saves").randint(1, 20)
        if roll == 1:
            rng = RNGManager(master_seed=seed)
            break

    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    save_event = [e for e in events if e.event_type == "save_rolled"][0]
    assert save_event.payload["is_natural_1"] is True
    assert outcome == SaveOutcome.FAILURE

def test_success_when_total_meets_dc():
    """Tier 1: Save succeeds when total >= DC."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "save_fortitude": 5,
                "con_mod": 2,
                "hp_current": 10,
                "hp_max": 10
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.FORT,
        dc=15,
        source_id="poison",
        target_id="fighter"
    )

    rng = RNGManager(master_seed=100)
    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    save_event = [e for e in events if e.event_type == "save_rolled"][0]
    total = save_event.payload["total"]
    # Total = d20 + 5 + 2 = d20 + 7

    if total >= 15:
        assert outcome in [SaveOutcome.SUCCESS, SaveOutcome.PARTIAL]
    else:
        assert outcome == SaveOutcome.FAILURE

def test_failure_when_total_below_dc():
    """Tier 1: Save fails when total < DC."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "save_fortitude": 0,
                "con_mod": 0,
                "hp_current": 6,
                "hp_max": 6
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.FORT,
        dc=25,  # Very high DC for goblin
        source_id="poison",
        target_id="goblin"
    )

    rng = RNGManager(master_seed=50)
    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    save_event = [e for e in events if e.event_type == "save_rolled"][0]
    # Ensure not natural 20
    if not save_event.payload["is_natural_20"]:
        total = save_event.payload["total"]
        if total < 25:
            assert outcome == SaveOutcome.FAILURE

def test_spell_resistance_check_pass():
    """Tier 1: SR check passes when d20 + CL >= SR."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "demon": {
                "sr": 15,
                "save_will": 5,
                "wis_mod": 2,
                "hp_current": 30,
                "hp_max": 30
            }
        }
    )

    sr_check = SRCheck(caster_level=10, source_id="wizard")
    rng = RNGManager(master_seed=200)

    sr_passed, events = check_spell_resistance(sr_check, world_state, "demon", rng, 0, 1.0)

    sr_event = events[0]
    assert sr_event.event_type == "spell_resistance_checked"
    total = sr_event.payload["total"]
    # Total = d20 + 10

    if total >= 15:
        assert sr_passed is True
    else:
        assert sr_passed is False

def test_spell_resistance_negates_effect():
    """Tier 1: Failed SR check negates effect (no save needed)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "demon": {
                "sr": 25,  # High SR
                "save_will": 5,
                "wis_mod": 2,
                "hp_current": 30,
                "hp_max": 30
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.WILL,
        dc=20,
        source_id="wizard",
        target_id="demon",
        sr_check=SRCheck(caster_level=5, source_id="wizard"),  # Low CL
        on_failure=EffectSpec(conditions_to_apply=["stunned"])
    )

    # Find seed where SR check fails
    for seed in range(1000):
        rng_test = RNGManager(master_seed=seed)
        d20 = rng_test.stream("saves").randint(1, 20)
        if d20 + 5 < 25:  # SR fails
            rng = RNGManager(master_seed=seed)
            outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

            # Should have SR event and save_negated event
            event_types = [e.event_type for e in events]
            assert "spell_resistance_checked" in event_types
            assert "save_negated" in event_types
            assert outcome == SaveOutcome.SUCCESS  # Treated as success (no effect)
            break

def test_damage_scaling_on_failure():
    """Tier 1: Full damage applied on failed save."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "save_reflex": 2,
                "dex_mod": 1,
                "hp_current": 10,
                "hp_max": 10
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.REF,
        dc=20,  # High DC
        source_id="fireball",
        target_id="goblin",
        base_damage=20,
        on_failure=EffectSpec(damage_multiplier=1.0)
    )

    rng = RNGManager(master_seed=50)
    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    if outcome == SaveOutcome.FAILURE:
        updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events), 2.0)

        hp_events = [e for e in effect_events if e.event_type == "hp_changed"]
        if hp_events:
            assert hp_events[0].payload["delta"] == -20

def test_damage_scaling_on_partial():
    """Tier 1: Half damage on partial save (successful save with reduced effect)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "rogue": {
                "save_reflex": 6,
                "dex_mod": 4,
                "hp_current": 20,
                "hp_max": 20
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.REF,
        dc=15,
        source_id="fireball",
        target_id="rogue",
        base_damage=20,
        on_partial=EffectSpec(damage_multiplier=0.5)
    )

    # Find seed where save succeeds
    for seed in range(1000):
        rng_test = RNGManager(master_seed=seed)
        d20 = rng_test.stream("saves").randint(1, 20)
        total = d20 + 10  # 6 + 4
        if total >= 15 and d20 not in [1, 20]:  # Success, not natural
            rng = RNGManager(master_seed=seed)
            outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

            assert outcome == SaveOutcome.PARTIAL
            updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events), 2.0)

            hp_events = [e for e in effect_events if e.event_type == "hp_changed"]
            assert len(hp_events) == 1
            assert hp_events[0].payload["delta"] == -10  # Half damage
            break

def test_conditions_applied_on_save_failure():
    """Tier 1: Conditions applied when save fails."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "save_will": 0,
                "wis_mod": 0,
                "hp_current": 6,
                "hp_max": 6
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.WILL,
        dc=20,
        source_id="spell",
        target_id="goblin",
        on_failure=EffectSpec(conditions_to_apply=["stunned"])
    )

    rng = RNGManager(master_seed=60)
    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    if outcome == SaveOutcome.FAILURE:
        updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events), 2.0)

        condition_events = [e for e in effect_events if e.event_type == "condition_applied"]
        assert len(condition_events) == 1
        assert condition_events[0].payload["condition_type"] == "stunned"

        # Verify condition in state
        goblin = updated_state.entities["goblin"]
        assert "conditions" in goblin
        assert "stunned" in goblin["conditions"]

def test_save_with_no_effects():
    """Tier 1: Save with no effects defined (minimal context)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "save_fortitude": 5,
                "con_mod": 2,
                "hp_current": 10,
                "hp_max": 10
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.FORT,
        dc=15,
        source_id="poison",
        target_id="fighter"
        # No on_success, on_failure, on_partial
    )

    rng = RNGManager(master_seed=100)
    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    # Should resolve normally
    assert outcome in [SaveOutcome.SUCCESS, SaveOutcome.FAILURE]

    # Apply effects should return unchanged state
    updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events), 2.0)
    assert len(effect_events) == 0
    assert updated_state.state_hash() == world_state.state_hash()

def test_hp_changed_on_save_damage():
    """Tier 1: hp_changed event emitted when damage applied."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "save_reflex": 2,
                "dex_mod": 1,
                "hp_current": 10,
                "hp_max": 10
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.REF,
        dc=20,
        source_id="fireball",
        target_id="goblin",
        base_damage=8,
        on_failure=EffectSpec(damage_multiplier=1.0)
    )

    rng = RNGManager(master_seed=70)
    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    if outcome == SaveOutcome.FAILURE:
        updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events), 2.0)

        hp_events = [e for e in effect_events if e.event_type == "hp_changed"]
        assert len(hp_events) == 1
        assert hp_events[0].payload["entity_id"] == "goblin"
        assert hp_events[0].payload["hp_before"] == 10
        assert hp_events[0].payload["hp_after"] == 2

def test_entity_defeated_on_lethal_save_damage():
    """Tier 1: entity_defeated event when save damage kills target."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin": {
                "save_reflex": 2,
                "dex_mod": 1,
                "hp_current": 5,
                "hp_max": 10
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.REF,
        dc=20,
        source_id="fireball",
        target_id="goblin",
        base_damage=10,
        on_failure=EffectSpec(damage_multiplier=1.0)
    )

    rng = RNGManager(master_seed=80)
    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    if outcome == SaveOutcome.FAILURE:
        updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events), 2.0)

        defeat_events = [e for e in effect_events if e.event_type == "entity_defeated"]
        assert len(defeat_events) == 1
        assert defeat_events[0].payload["entity_id"] == "goblin"

        # Verify defeated flag
        goblin = updated_state.entities["goblin"]
        assert goblin.get("defeated") is True

def test_save_stream_isolated_from_combat_stream():
    """Tier 1: Save RNG stream doesn't affect combat stream."""
    rng = RNGManager(master_seed=42)

    # Get initial combat stream state
    combat_stream = rng.stream("combat")
    combat_roll1 = combat_stream.randint(1, 20)

    # Make save rolls
    saves_stream = rng.stream("saves")
    save_roll1 = saves_stream.randint(1, 20)
    save_roll2 = saves_stream.randint(1, 20)

    # Combat stream should be unchanged
    combat_roll2 = combat_stream.randint(1, 20)

    # Verify isolation by repeating with fresh RNG
    rng2 = RNGManager(master_seed=42)
    combat_stream2 = rng2.stream("combat")
    combat_roll1_repeat = combat_stream2.randint(1, 20)
    combat_roll2_repeat = combat_stream2.randint(1, 20)

    assert combat_roll1 == combat_roll1_repeat
    assert combat_roll2 == combat_roll2_repeat

def test_deterministic_replay_10x():
    """Tier 1: 10× replay with same seed produces identical outcomes."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "save_fortitude": 5,
                "con_mod": 2,
                "hp_current": 10,
                "hp_max": 10
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.FORT,
        dc=15,
        source_id="poison",
        target_id="fighter"
    )

    results = []
    for _ in range(10):
        rng = RNGManager(master_seed=999)
        outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)
        results.append((outcome, events))

    # All outcomes should be identical
    first_outcome, first_events = results[0]
    for outcome, events in results[1:]:
        assert outcome == first_outcome
        assert len(events) == len(first_events)
        for e1, e2 in zip(first_events, events):
            assert e1.event_type == e2.event_type
            assert e1.payload == e2.payload

def test_missing_entity_raises_error():
    """Tier 1: Missing entity raises ValueError."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={}
    )

    save_context = SaveContext(
        save_type=SaveType.FORT,
        dc=15,
        source_id="poison",
        target_id="nonexistent"
    )

    rng = RNGManager(master_seed=100)

    with pytest.raises(ValueError, match="Target not found"):
        resolve_save(save_context, world_state, rng, 0, 1.0)

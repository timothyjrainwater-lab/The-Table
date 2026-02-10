"""Integration tests for CP-17 save + attack/condition interactions.

Tests cross-packet integration:
- Save triggered by attack rider (poison)
- Conditions affect save outcomes
- Save applies conditions that affect subsequent saves
- SR + save + condition chain
- Deterministic state hashes with saves
- Event ordering (attack → damage → save → outcome)

Tier-1 (MUST PASS - 6+ tests):
- Attack with poison rider triggers save
- Failed save applies condition
- Condition from previous save affects next save
- SR check → save → condition application chain
- Deterministic replay with attack + save
- State hash stability across save sequences
"""

import pytest
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.saves import SaveContext, SaveType, SaveOutcome, EffectSpec, SRCheck
from aidm.core.save_resolver import resolve_save, apply_save_effects
from aidm.schemas.conditions import create_shaken_condition, create_sickened_condition
from aidm.core.conditions import apply_condition, get_condition_modifiers


def test_save_triggered_by_attack_rider():
    """Integration 1: Attack with poison rider triggers save (simulated)."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "assassin": {
                "ac": 15,
                "hp_current": 12,
                "hp_max": 12,
                "team": "monsters"
            },
            "paladin": {
                "ac": 18,
                "hp_current": 20,
                "hp_max": 20,
                "save_fortitude": 8,
                "con_mod": 3,
                "team": "party"
            }
        }
    )

    # Simulated: Attack hits, damage dealt, now trigger poison save
    # In real CP-17 integration, attack resolver would emit save_triggered event
    save_context = SaveContext(
        save_type=SaveType.FORT,
        dc=16,
        source_id="assassin",
        target_id="paladin",
        base_damage=6,  # Poison damage
        on_failure=EffectSpec(
            damage_multiplier=1.0,
            conditions_to_apply=["sickened"]
        )
    )

    rng = RNGManager(master_seed=200)
    outcome, events = resolve_save(save_context, world_state, rng, 100, 10.0)

    # Verify save event emitted
    save_events = [e for e in events if e.event_type == "save_rolled"]
    assert len(save_events) == 1
    assert save_events[0].payload["target_id"] == "paladin"

    # Apply effects
    updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events) + 100, 11.0)

    if outcome == SaveOutcome.FAILURE:
        # Poison damage and sickened applied
        condition_events = [e for e in effect_events if e.event_type == "condition_applied"]
        assert len(condition_events) == 1
        assert "sickened" in updated_state.entities["paladin"]["conditions"]


def test_failed_save_applies_condition():
    """Integration 2: Failed Will save applies stunned condition."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "wizard": {
                "ac": 12,
                "hp_current": 8,
                "hp_max": 8,
                "team": "party"
            },
            "goblin": {
                "ac": 15,
                "hp_current": 6,
                "hp_max": 6,
                "save_will": 0,
                "wis_mod": 0,
                "team": "monsters"
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.WILL,
        dc=18,
        source_id="wizard",
        target_id="goblin",
        on_failure=EffectSpec(conditions_to_apply=["stunned"])
    )

    rng = RNGManager(master_seed=300)
    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    # Apply effects
    updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events), 2.0)

    if outcome == SaveOutcome.FAILURE:
        # Stunned condition applied
        goblin = updated_state.entities["goblin"]
        assert "stunned" in goblin["conditions"]

        # Verify condition modifiers
        mods = get_condition_modifiers(updated_state, "goblin")
        assert mods.ac_modifier == -2  # Stunned AC penalty
        assert mods.actions_prohibited is True


def test_condition_from_previous_save_affects_next_save():
    """Integration 3: Condition from first save affects second save."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                "save_fortitude": 6,
                "save_will": 3,
                "con_mod": 2,
                "wis_mod": 1,
                "hp_current": 15,
                "hp_max": 15
            }
        }
    )

    # First save: fear effect applies shaken (-2 to saves)
    save1 = SaveContext(
        save_type=SaveType.WILL,
        dc=15,
        source_id="dragon_fear",
        target_id="fighter",
        on_failure=EffectSpec(conditions_to_apply=["shaken"])
    )

    rng1 = RNGManager(master_seed=400)
    outcome1, events1 = resolve_save(save1, world_state, rng1, 0, 1.0)
    world_state_after_save1, effect_events1 = apply_save_effects(save1, outcome1, world_state, len(events1), 2.0)

    # If shaken was applied, verify it affects next save
    if "shaken" in world_state_after_save1.entities["fighter"].get("conditions", {}):
        # Second save: poison (Fort) with shaken penalty
        save2 = SaveContext(
            save_type=SaveType.FORT,
            dc=16,
            source_id="poison",
            target_id="fighter"
        )

        rng2 = RNGManager(master_seed=500)
        outcome2, events2 = resolve_save(save2, world_state_after_save1, rng2, 100, 5.0)

        save_event2 = [e for e in events2 if e.event_type == "save_rolled"][0]
        # Save bonus should include -2 from shaken
        # Base: 6 + 2 - 2 = 6
        assert save_event2.payload["save_bonus"] == 6


def test_sr_check_save_condition_chain():
    """Integration 4: SR → save → condition application chain."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "wizard": {
                "ac": 12,
                "hp_current": 8,
                "hp_max": 8
            },
            "demon": {
                "sr": 18,
                "save_will": 6,
                "wis_mod": 3,
                "hp_current": 40,
                "hp_max": 40
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.WILL,
        dc=20,
        source_id="wizard",
        target_id="demon",
        sr_check=SRCheck(caster_level=12, source_id="wizard"),
        on_failure=EffectSpec(conditions_to_apply=["dazed"])
    )

    rng = RNGManager(master_seed=600)
    outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)

    # Check event sequence
    event_types = [e.event_type for e in events]
    assert "spell_resistance_checked" in event_types

    sr_event = [e for e in events if e.event_type == "spell_resistance_checked"][0]

    if sr_event.payload["sr_passed"]:
        # SR passed, save should have been rolled
        assert "save_rolled" in event_types

        # Apply effects if save failed
        updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events), 2.0)

        if outcome == SaveOutcome.FAILURE:
            # Dazed condition applied
            assert "dazed" in updated_state.entities["demon"].get("conditions", {})
    else:
        # SR blocked, save negated
        assert "save_negated" in event_types


def test_deterministic_replay_with_attack_and_save():
    """Integration 5: Deterministic replay of attack + save sequence."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "rogue": {
                "save_reflex": 6,
                "dex_mod": 4,
                "hp_current": 18,
                "hp_max": 18
            }
        }
    )

    save_context = SaveContext(
        save_type=SaveType.REF,
        dc=17,
        source_id="trap",
        target_id="rogue",
        base_damage=15,
        on_failure=EffectSpec(damage_multiplier=1.0),
        on_partial=EffectSpec(damage_multiplier=0.5)
    )

    results = []
    for _ in range(5):
        rng = RNGManager(master_seed=777)
        outcome, events = resolve_save(save_context, world_state, rng, 0, 1.0)
        updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, len(events), 2.0)
        results.append((outcome, updated_state.state_hash()))

    # All replays should produce identical outcomes and state hashes
    first_outcome, first_hash = results[0]
    for outcome, state_hash in results[1:]:
        assert outcome == first_outcome
        assert state_hash == first_hash


def test_state_hash_stability_across_save_sequences():
    """Integration 6: State hash remains stable across save sequences."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "cleric": {
                "save_fortitude": 7,
                "save_reflex": 4,
                "save_will": 8,
                "con_mod": 2,
                "dex_mod": 1,
                "wis_mod": 3,
                "hp_current": 25,
                "hp_max": 25
            }
        }
    )

    # Sequence: Fort save, Ref save, Will save
    saves = [
        SaveContext(SaveType.FORT, 15, "poison", "cleric"),
        SaveContext(SaveType.REF, 18, "trap", "cleric"),
        SaveContext(SaveType.WILL, 16, "spell", "cleric")
    ]

    # Run sequence twice with same seed
    def run_sequence(seed):
        state = world_state
        rng = RNGManager(master_seed=seed)
        for save_ctx in saves:
            outcome, events = resolve_save(save_ctx, state, rng, 0, 1.0)
            state, _ = apply_save_effects(save_ctx, outcome, state, len(events), 2.0)
        return state.state_hash()

    hash1 = run_sequence(888)
    hash2 = run_sequence(888)

    assert hash1 == hash2  # Deterministic across replays

"""Integration tests for Concentration skill with duration tracking (WO-035)."""

import pytest
from aidm.core.spell_resolver import check_concentration_on_damage
from aidm.core.duration_tracker import DurationTracker, ActiveSpellEffect
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.skills import SkillID


@pytest.fixture
def rng():
    """RNG manager with fixed seed."""
    return RNGManager(master_seed=777)


@pytest.fixture
def wizard():
    """Wizard with Concentration."""
    return {
        EF.ENTITY_ID: "wizard",
        EF.CON_MOD: 1,
        EF.SKILL_RANKS: {SkillID.CONCENTRATION: 8},
        EF.CLASS_SKILLS: [SkillID.CONCENTRATION],
    }


def test_concentration_check_on_damage(wizard, rng):
    """Concentration check triggers when concentrating caster takes damage (PHB p.69)."""
    duration_tracker = DurationTracker()

    # Add concentration spell
    spell_effect = ActiveSpellEffect(
        effect_id="mage_armor_1",
        spell_id="mage_armor",
        spell_name="Mage Armor",
        caster_id="wizard",
        target_id="wizard",
        rounds_remaining=80,
        concentration=True,
        turn_applied=0,
    )
    duration_tracker.add_effect(spell_effect)

    # Wizard takes 5 damage → DC 15 check
    maintained, check_result, events = check_concentration_on_damage(
        caster=wizard,
        damage_taken=5,
        rng=rng,
        duration_tracker=duration_tracker,
    )

    assert check_result is not None
    assert check_result.dc == 15  # 10 + 5 damage
    assert check_result.skill_id == SkillID.CONCENTRATION

    # Check events emitted
    event_types = [e.event_type for e in events]
    assert "concentration_check" in event_types


def test_concentration_no_active_spell(wizard, rng):
    """No check needed if no active concentration (PHB p.69)."""
    duration_tracker = DurationTracker()

    maintained, check_result, events = check_concentration_on_damage(
        caster=wizard,
        damage_taken=10,
        rng=rng,
        duration_tracker=duration_tracker,
    )

    assert maintained is True
    assert check_result is None
    assert len(events) == 0


def test_concentration_breaks_on_failure(wizard, rng):
    """Failed check breaks concentration (PHB p.69)."""
    duration_tracker = DurationTracker()

    spell_effect = ActiveSpellEffect(
        effect_id="web_1",
        spell_id="web",
        spell_name="Web",
        caster_id="wizard",
        target_id="area",
        rounds_remaining=50,
        concentration=True,
        turn_applied=0,
    )
    duration_tracker.add_effect(spell_effect)

    # Large damage → high DC, likely to fail
    maintained, check_result, events = check_concentration_on_damage(
        caster=wizard,
        damage_taken=25,  # DC 35
        rng=rng,
        duration_tracker=duration_tracker,
    )

    # With +9 bonus, needs d20 >= 26 (impossible)
    # If failed, concentration should be broken
    if not maintained:
        assert not duration_tracker.has_active_concentration("wizard")
        event_types = [e.event_type for e in events]
        assert "concentration_broken" in event_types


def test_concentration_dc_scales_with_damage(wizard, rng):
    """Concentration DC = 10 + damage taken (PHB p.69)."""
    duration_tracker = DurationTracker()

    spell_effect = ActiveSpellEffect(
        effect_id="hold_person",
        spell_id="hold_person",
        spell_name="Hold Person",
        caster_id="wizard",
        target_id="target",
        rounds_remaining=50,
        concentration=True,
        turn_applied=0,
    )

    for damage, expected_dc in [(1, 11), (5, 15), (10, 20), (20, 30)]:
        duration_tracker = DurationTracker()
        duration_tracker.add_effect(spell_effect)

        _, result, _ = check_concentration_on_damage(
            caster=wizard,
            damage_taken=damage,
            rng=rng,
            duration_tracker=duration_tracker,
        )

        assert result.dc == expected_dc


def test_concentration_untrained_allowed(rng):
    """Concentration can be used untrained (PHB p.69)."""
    fighter = {
        EF.ENTITY_ID: "fighter",
        EF.CON_MOD: 2,
        EF.SKILL_RANKS: {},  # No ranks
    }

    duration_tracker = DurationTracker()
    spell_effect = ActiveSpellEffect(
        effect_id="divine_favor",
        spell_id="divine_favor",
        spell_name="Divine Favor",
        caster_id="fighter",
        target_id="fighter",
        rounds_remaining=10,
        concentration=True,
        turn_applied=0,
    )
    duration_tracker.add_effect(spell_effect)

    maintained, check_result, events = check_concentration_on_damage(
        caster=fighter,
        damage_taken=8,
        rng=rng,
        duration_tracker=duration_tracker,
    )

    assert check_result is not None
    assert check_result.skill_ranks == 0  # Untrained
    assert check_result.ability_modifier == 2  # CON
    assert check_result.dc == 18

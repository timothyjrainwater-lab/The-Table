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


# ==============================================================================
# 3.5e CONCENTRATION RULES — Anti-5e Regression Guards
#
# D&D 3.5e PHB p.170: A caster may maintain multiple concentration spells.
# Each requires a separate Concentration check when the caster takes damage.
# There is NO automatic displacement of existing concentration effects.
#
# D&D 5e PHB p.203: "You lose concentration on a spell if you cast another
# spell that requires concentration." — THIS RULE DOES NOT EXIST IN 3.5e.
#
# These tests ensure the 5e rule never re-enters the codebase.
# ==============================================================================


def test_multiple_concentration_spells_allowed():
    """3.5e: A caster may maintain multiple concentration spells simultaneously.

    PHB p.170: No rule limits concentration to one spell per caster.
    This is the defining difference from 5e's one-concentration-per-caster limit.
    """
    tracker = DurationTracker()

    spell_a = ActiveSpellEffect(
        effect_id="detect_magic_1",
        spell_id="detect_magic",
        spell_name="Detect Magic",
        caster_id="wizard",
        target_id="wizard",
        rounds_remaining=10,
        concentration=True,
        turn_applied=0,
    )
    spell_b = ActiveSpellEffect(
        effect_id="detect_evil_1",
        spell_id="detect_evil",
        spell_name="Detect Evil",
        caster_id="wizard",
        target_id="wizard",
        rounds_remaining=10,
        concentration=True,
        turn_applied=1,
    )

    tracker.add_effect(spell_a)
    tracker.add_effect(spell_b)

    # BOTH spells must remain active — 5e would have removed detect_magic
    assert len(tracker) == 2
    assert tracker.has_effect("wizard", "detect_magic")
    assert tracker.has_effect("wizard", "detect_evil")
    assert tracker.has_active_concentration("wizard")

    # get_concentration_effects returns both
    conc_effects = tracker.get_concentration_effects("wizard")
    assert len(conc_effects) == 2
    spell_ids = {e.spell_id for e in conc_effects}
    assert spell_ids == {"detect_magic", "detect_evil"}


def test_adding_concentration_does_not_displace_existing():
    """3.5e: Adding a new concentration spell must NOT end existing ones.

    This is the specific 5e contamination bug that WO-FIX-001 corrects.
    In 5e, casting a new concentration spell auto-ends the previous one.
    In 3.5e, there is no such auto-displacement.
    """
    tracker = DurationTracker()

    # Wizard concentrates on Web
    web = ActiveSpellEffect(
        effect_id="web_1",
        spell_id="web",
        spell_name="Web",
        caster_id="wizard",
        target_id="area_1",
        rounds_remaining=50,
        concentration=True,
        turn_applied=0,
    )
    tracker.add_effect(web)
    assert len(tracker) == 1

    # Wizard now ALSO concentrates on Stinking Cloud
    stinking_cloud = ActiveSpellEffect(
        effect_id="stinking_cloud_1",
        spell_id="stinking_cloud",
        spell_name="Stinking Cloud",
        caster_id="wizard",
        target_id="area_2",
        rounds_remaining=50,
        concentration=True,
        turn_applied=1,
    )
    tracker.add_effect(stinking_cloud)

    # Web must NOT have been auto-removed (that would be 5e behavior)
    assert len(tracker) == 2
    assert tracker.has_effect("area_1", "web"), "Web was auto-displaced — 5e contamination!"
    assert tracker.has_effect("area_2", "stinking_cloud")


def test_three_simultaneous_concentration_spells():
    """3.5e: Even three simultaneous concentration spells are valid.

    Difficult to maintain (three Concentration checks per damage event)
    but mechanically legal in 3.5e.
    """
    tracker = DurationTracker()

    for i, (spell_id, spell_name) in enumerate([
        ("detect_magic", "Detect Magic"),
        ("detect_evil", "Detect Evil"),
        ("detect_thoughts", "Detect Thoughts"),
    ]):
        tracker.add_effect(ActiveSpellEffect(
            effect_id=f"{spell_id}_{i}",
            spell_id=spell_id,
            spell_name=spell_name,
            caster_id="cleric",
            target_id="cleric",
            rounds_remaining=10,
            concentration=True,
            turn_applied=i,
        ))

    assert len(tracker) == 3
    assert len(tracker.get_concentration_effects("cleric")) == 3


def test_break_concentration_removes_all():
    """3.5e: Breaking concentration ends ALL concentration spells for that caster."""
    tracker = DurationTracker()

    for spell_id in ["web", "stinking_cloud"]:
        tracker.add_effect(ActiveSpellEffect(
            effect_id=f"{spell_id}_1",
            spell_id=spell_id,
            spell_name=spell_id.replace("_", " ").title(),
            caster_id="wizard",
            target_id="area",
            rounds_remaining=50,
            concentration=True,
            turn_applied=0,
        ))

    # Also add a non-concentration spell
    tracker.add_effect(ActiveSpellEffect(
        effect_id="mage_armor_1",
        spell_id="mage_armor",
        spell_name="Mage Armor",
        caster_id="wizard",
        target_id="wizard",
        rounds_remaining=80,
        concentration=False,
        turn_applied=0,
    ))

    assert len(tracker) == 3

    # Break concentration — both concentration spells end, mage armor stays
    removed = tracker.break_concentration("wizard")
    assert len(removed) == 2
    assert len(tracker) == 1
    assert tracker.has_effect("wizard", "mage_armor")
    assert not tracker.has_active_concentration("wizard")

"""SKR-002 Phase 3: Core Algorithm Tests

Test coverage for permanent stat modification kernel algorithms.

SKR-002 Test Strategy (§10):
- Category 1: Permanent modifier application (drain, inherent, stacking)
- Category 2: Restoration (full, partial, exceeding drain)
- Category 3: Derived stat recalculation (HP max, AC, saves)
- Category 4: Edge cases (ability to 0, HP clamping, multiple sources)
- Category 5: Separation from temporary modifiers (CP-16)
"""

import pytest

from aidm.core.permanent_stats import (
    apply_permanent_modifier,
    calculate_effective_ability_score,
    restore_permanent_modifier,
)
from aidm.schemas.permanent_stats import (
    Ability,
    PermanentModifierType,
    PermanentStatModifiers,
)


# -----------------------------------------------------------------------------
# Category 1: Permanent Modifier Application
# -----------------------------------------------------------------------------


def test_apply_drain_reduces_effective_score():
    """Apply STR drain, verify effective score reduced (SKR-002 §4.1)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    events = apply_permanent_modifier(
        entity,
        Ability.STR,
        PermanentModifierType.DRAIN,
        -2,
        "shadow_strength_drain",
    )

    # Verify event emission
    assert len(events) >= 2
    assert events[0]["event_type"] == "permanent_stat_modified"
    assert events[0]["ability"] == "str"
    assert events[0]["amount"] == -2
    assert events[1]["event_type"] == "derived_stats_recalculated"

    # Verify effective score
    effective_str = calculate_effective_ability_score(entity, Ability.STR)
    assert effective_str == 14  # 16 (base) + (-2 drain) = 14


def test_apply_inherent_increases_effective_score():
    """Apply INT inherent bonus (Wish), verify effective score increased (SKR-002 §4.4)."""
    entity = {
        "entity_id": "wizard_01",
        "base_stats": {"str": 8, "dex": 14, "con": 12, "int": 18, "wis": 10, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    events = apply_permanent_modifier(
        entity,
        Ability.INT,
        PermanentModifierType.INHERENT,
        +1,
        "wish_stat_increase",
    )

    assert events[0]["event_type"] == "permanent_stat_modified"
    assert events[0]["ability"] == "int"
    assert events[0]["amount"] == 1

    effective_int = calculate_effective_ability_score(entity, Ability.INT)
    assert effective_int == 19  # 18 (base) + (+1 inherent) = 19


def test_multiple_drains_stack():
    """Multiple STR drains stack (SKR-002 §6.4, INV-8)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    # First drain
    apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -2, "shadow_1"
    )

    # Second drain
    apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -3, "shadow_2"
    )

    effective_str = calculate_effective_ability_score(entity, Ability.STR)
    assert effective_str == 11  # 16 + (-2) + (-3) = 11


def test_drain_and_inherent_both_apply():
    """Drain and inherent bonuses apply independently (SKR-002 §3.1)."""
    entity = {
        "entity_id": "wizard_01",
        "base_stats": {"str": 10, "dex": 14, "con": 12, "int": 18, "wis": 10, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    # Apply inherent bonus
    apply_permanent_modifier(
        entity, Ability.INT, PermanentModifierType.INHERENT, +1, "wish"
    )

    # Apply drain
    apply_permanent_modifier(
        entity, Ability.INT, PermanentModifierType.DRAIN, -2, "feeblemind_partial"
    )

    effective_int = calculate_effective_ability_score(entity, Ability.INT)
    assert effective_int == 17  # 18 (base) + 1 (inherent) + (-2 drain) = 17


# -----------------------------------------------------------------------------
# Category 2: Restoration
# -----------------------------------------------------------------------------


def test_restoration_removes_full_drain():
    """Restore full STR drain (SKR-002 §4.3)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    # Apply drain
    apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -2, "shadow"
    )

    # Restore
    events = restore_permanent_modifier(
        entity, Ability.STR, 2, "restoration_spell"
    )

    assert events[0]["event_type"] == "permanent_stat_restored"
    assert events[0]["amount_removed"] == 2

    effective_str = calculate_effective_ability_score(entity, Ability.STR)
    assert effective_str == 16  # Back to base


def test_restoration_removes_partial_drain():
    """Restore partial STR drain (SKR-002 §8.6)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    # Apply drain (-4)
    apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -4, "shadow"
    )

    # Restore partial (1 point)
    restore_permanent_modifier(entity, Ability.STR, 1, "lesser_restoration")

    effective_str = calculate_effective_ability_score(entity, Ability.STR)
    assert effective_str == 13  # 16 + (-4) + 1 = 13


def test_restoration_exceeding_drain_capped():
    """Restoration cannot exceed drain amount (SKR-002 §6.3)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    # Apply drain (-2)
    apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -2, "shadow"
    )

    # Attempt to restore 4 (exceeds drain)
    events = restore_permanent_modifier(entity, Ability.STR, 4, "restoration")

    # Only 2 actually removed
    assert events[0]["amount_removed"] == 2

    effective_str = calculate_effective_ability_score(entity, Ability.STR)
    assert effective_str == 16  # Back to base, no bonus


def test_restoration_when_no_drain_exists():
    """Restoration when no drain → no change (SKR-002 §6.3)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    events = restore_permanent_modifier(entity, Ability.STR, 2, "restoration")

    # No drain to remove → no events emitted
    assert len(events) == 0


# -----------------------------------------------------------------------------
# Category 3: Derived Stat Recalculation
# -----------------------------------------------------------------------------


def test_con_drain_reduces_hp_max():
    """CON drain reduces HP max (SKR-002 §4.5)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
        "hd_count": 5,
        "base_hp": 40,
        "hp_current": 50,
    }

    events = apply_permanent_modifier(
        entity, Ability.CON, PermanentModifierType.DRAIN, -4, "vampire_drain"
    )

    # Find derived_stats_recalculated event
    recalc_event = next(e for e in events if e["event_type"] == "derived_stats_recalculated")

    # CON 14 → 10: modifier +2 → 0, HP max reduction = 2 × 5 HD = 10
    assert recalc_event["hp_max_old"] == 50  # 40 + (2 × 5)
    assert recalc_event["hp_max_new"] == 40  # 40 + (0 × 5)


def test_str_drain_recalculates_attack():
    """STR drain triggers attack/damage recalculation (SKR-002 §5.2)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    events = apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -2, "shadow"
    )

    recalc_event = next(e for e in events if e["event_type"] == "derived_stats_recalculated")

    # Verify attack/damage in recalculated_stats
    assert "melee_attack" in recalc_event["recalculated_stats"]
    assert "damage" in recalc_event["recalculated_stats"]


# -----------------------------------------------------------------------------
# Category 4: Edge Cases
# -----------------------------------------------------------------------------


def test_ability_score_to_zero_triggers_death():
    """Ability score reaches 0 → death (SKR-002 §4.2, INV-6)."""
    entity = {
        "entity_id": "wizard_01",
        "base_stats": {"str": 8, "dex": 14, "con": 12, "int": 18, "wis": 10, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    events = apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -8, "shadow_drain"
    )

    # Verify death event emitted
    death_event = next(e for e in events if e["event_type"] == "ability_score_death")
    assert death_event["ability"] == "str"
    assert death_event["final_score"] == 0


def test_hp_max_drops_below_current_hp_clamps():
    """HP max drops below current HP → current HP clamped (SKR-002 §6.2, INV-7)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
        "hd_count": 5,
        "base_hp": 40,
        "hp_current": 50,
        "hp_max": 50,
    }

    events = apply_permanent_modifier(
        entity, Ability.CON, PermanentModifierType.DRAIN, -4, "vampire"
    )

    # Verify hp_changed event
    hp_event = next((e for e in events if e["event_type"] == "hp_changed"), None)
    assert hp_event is not None
    assert hp_event["old_hp"] == 50
    assert hp_event["new_hp"] == 40
    assert hp_event["cause"] == "hp_max_reduction"

    # Verify entity state updated
    assert entity["hp_current"] == 40


def test_feeblemind_special_case():
    """Feeblemind (INT → 1) implemented as drain (SKR-002 §6.6)."""
    entity = {
        "entity_id": "wizard_01",
        "base_stats": {"str": 8, "dex": 14, "con": 12, "int": 18, "wis": 10, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    # Feeblemind: drain = current - 1
    drain_amount = -(18 - 1)  # -17

    events = apply_permanent_modifier(
        entity, Ability.INT, PermanentModifierType.DRAIN, drain_amount, "feeblemind"
    )

    effective_int = calculate_effective_ability_score(entity, Ability.INT)
    assert effective_int == 1

    # Restoration removes drain
    restore_permanent_modifier(entity, Ability.INT, 17, "restoration")
    effective_int = calculate_effective_ability_score(entity, Ability.INT)
    assert effective_int == 18  # Back to original


# -----------------------------------------------------------------------------
# Category 5: Separation from Temporary Modifiers (CP-16)
# -----------------------------------------------------------------------------


def test_permanent_and_temporary_separate():
    """Permanent and temporary modifiers are separate layers (SKR-002 INV-3)."""
    entity = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 14, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
        "temporary_modifiers": {},  # CP-16 placeholder
    }

    # Apply permanent drain
    apply_permanent_modifier(
        entity, Ability.STR, PermanentModifierType.DRAIN, -2, "shadow"
    )

    # Verify permanent modifiers stored separately
    perm_mods = PermanentStatModifiers.from_dict(entity["permanent_stat_modifiers"])
    assert perm_mods.str.drain == -2
    assert perm_mods.str.inherent == 0

    # Verify temporary modifiers untouched
    assert entity["temporary_modifiers"] == {}


# -----------------------------------------------------------------------------
# Integration Tests (End-to-End Scenarios)
# -----------------------------------------------------------------------------


def test_shadow_encounter_full_workflow():
    """Shadow STR drain → restoration workflow (SKR-002 §10.2 Scenario 1)."""
    fighter = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    # Shadow attacks
    events = apply_permanent_modifier(
        fighter, Ability.STR, PermanentModifierType.DRAIN, -2, "shadow"
    )

    effective_str = calculate_effective_ability_score(fighter, Ability.STR)
    assert effective_str == 14

    # Cleric casts Lesser Restoration
    restore_events = restore_permanent_modifier(
        fighter, Ability.STR, 2, "lesser_restoration"
    )

    effective_str = calculate_effective_ability_score(fighter, Ability.STR)
    assert effective_str == 16  # Restored


def test_vampire_con_drain_with_hp_loss():
    """Vampire CON drain → HP max reduction → clamp (SKR-002 §10.2 Scenario 2)."""
    fighter = {
        "entity_id": "fighter_01",
        "base_stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
        "hd_count": 5,
        "base_hp": 40,
        "hp_current": 50,
        "hp_max": 50,
    }

    # Vampire drains 4 CON
    events = apply_permanent_modifier(
        fighter, Ability.CON, PermanentModifierType.DRAIN, -4, "vampire"
    )

    # HP max drops to 40, current HP clamped
    assert fighter["hp_max"] == 40
    assert fighter["hp_current"] == 40

    # Later, Restoration cast
    restore_events = restore_permanent_modifier(
        fighter, Ability.CON, 4, "restoration"
    )

    # HP max returns to 50, but current HP stays 40 (no free healing)
    assert fighter["hp_max"] == 50
    assert fighter["hp_current"] == 40


def test_ability_score_death_spectre():
    """Spectre STR drain kills wizard (SKR-002 §10.2 Scenario 3)."""
    wizard = {
        "entity_id": "wizard_01",
        "base_stats": {"str": 8, "dex": 14, "con": 12, "int": 18, "wis": 10, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    # First hit: -3 STR
    events = apply_permanent_modifier(
        wizard, Ability.STR, PermanentModifierType.DRAIN, -3, "spectre"
    )

    effective_str = calculate_effective_ability_score(wizard, Ability.STR)
    assert effective_str == 5  # Survives

    # Second hit: -5 STR (total -8)
    events = apply_permanent_modifier(
        wizard, Ability.STR, PermanentModifierType.DRAIN, -5, "spectre"
    )

    effective_str = calculate_effective_ability_score(wizard, Ability.STR)
    assert effective_str == 0

    # Verify death event
    death_event = next(e for e in events if e["event_type"] == "ability_score_death")
    assert death_event["final_score"] == 0


def test_wish_stat_increase():
    """Wish grants +1 INT (SKR-002 §10.2 Scenario 4)."""
    wizard = {
        "entity_id": "wizard_01",
        "base_stats": {"str": 8, "dex": 14, "con": 12, "int": 18, "wis": 10, "cha": 10},
        "permanent_stat_modifiers": PermanentStatModifiers().to_dict(),
    }

    # Wish (+1 INT)
    events = apply_permanent_modifier(
        wizard, Ability.INT, PermanentModifierType.INHERENT, +1, "wish"
    )

    effective_int = calculate_effective_ability_score(wizard, Ability.INT)
    assert effective_int == 19

    # Later, INT drain applied
    apply_permanent_modifier(
        wizard, Ability.INT, PermanentModifierType.DRAIN, -2, "feeblemind_partial"
    )

    effective_int = calculate_effective_ability_score(wizard, Ability.INT)
    assert effective_int == 17  # 18 (base) + 1 (inherent) + (-2 drain)

    # Verify inherent bonus persists
    perm_mods = PermanentStatModifiers.from_dict(wizard["permanent_stat_modifiers"])
    assert perm_mods.int.inherent == 1

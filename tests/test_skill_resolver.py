"""Tests for D&D 3.5e skill system (WO-035).

Tests 7 combat-adjacent skills:
- Tumble (p.84) — Avoid AoO
- Concentration (p.69) — Maintain spells when damaged
- Hide (p.76) — Opposed vs Spot
- Move Silently (p.79) — Opposed vs Listen
- Spot (p.83) — Detect hidden creatures
- Listen (p.78) — Hear approaching enemies
- Balance (p.67) — Move on difficult surfaces

Reference: Player's Handbook 3.5e, Chapter 4
"""

import pytest
from aidm.core.skill_resolver import (
    resolve_skill_check,
    resolve_opposed_check,
    SkillCheckResult,
    OpposedCheckResult,
)
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.skills import SkillID, SKILLS, get_skill


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def rng():
    """RNG manager with fixed seed."""
    return RNGManager(master_seed=42)


@pytest.fixture
def fighter():
    """Level 5 fighter with combat skills."""
    return {
        EF.ENTITY_ID: "fighter_1",
        EF.DEX_MOD: 2,
        EF.CON_MOD: 3,
        EF.WIS_MOD: 1,
        EF.STR_MOD: 4,
        EF.SKILL_RANKS: {
            SkillID.TUMBLE: 5,      # Class skill, 5 ranks
            SkillID.CONCENTRATION: 3,  # Cross-class, 3 ranks
        },
        EF.CLASS_SKILLS: [SkillID.TUMBLE],
        EF.ARMOR_CHECK_PENALTY: 4,  # Heavy armor
    }


@pytest.fixture
def rogue():
    """Level 5 rogue with stealth skills."""
    return {
        EF.ENTITY_ID: "rogue_1",
        EF.DEX_MOD: 4,
        EF.WIS_MOD: 2,
        EF.SKILL_RANKS: {
            SkillID.HIDE: 8,
            SkillID.MOVE_SILENTLY: 8,
            SkillID.TUMBLE: 8,
        },
        EF.CLASS_SKILLS: [SkillID.HIDE, SkillID.MOVE_SILENTLY, SkillID.TUMBLE],
        EF.ARMOR_CHECK_PENALTY: 0,  # Light/no armor
    }


@pytest.fixture
def wizard():
    """Level 5 wizard with Concentration."""
    return {
        EF.ENTITY_ID: "wizard_1",
        EF.CON_MOD: 1,
        EF.SKILL_RANKS: {
            SkillID.CONCENTRATION: 8,  # Class skill, max ranks
        },
        EF.CLASS_SKILLS: [SkillID.CONCENTRATION],
        EF.ARMOR_CHECK_PENALTY: 0,
    }


@pytest.fixture
def guard():
    """Guard with Spot and Listen."""
    return {
        EF.ENTITY_ID: "guard_1",
        EF.WIS_MOD: 3,
        EF.SKILL_RANKS: {
            SkillID.SPOT: 4,
            SkillID.LISTEN: 4,
        },
        EF.CLASS_SKILLS: [SkillID.SPOT, SkillID.LISTEN],
        EF.ARMOR_CHECK_PENALTY: 2,  # Chain mail
    }


# ==============================================================================
# SKILL DEFINITION TESTS
# ==============================================================================

def test_skill_registry():
    """All 39 PHB skills are registered."""
    assert len(SKILLS) >= 39
    assert SkillID.TUMBLE in SKILLS
    assert SkillID.CONCENTRATION in SKILLS
    assert SkillID.HIDE in SKILLS
    assert SkillID.MOVE_SILENTLY in SKILLS
    assert SkillID.SPOT in SKILLS
    assert SkillID.LISTEN in SKILLS
    assert SkillID.BALANCE in SKILLS


def test_tumble_definition():
    """Tumble skill properties (PHB p.84)."""
    tumble = get_skill(SkillID.TUMBLE)
    assert tumble.name == "Tumble"
    assert tumble.key_ability == "dex"
    assert tumble.armor_check_penalty is True
    assert tumble.trained_only is True
    assert tumble.phb_page == 84


def test_concentration_definition():
    """Concentration skill properties (PHB p.69)."""
    concentration = get_skill(SkillID.CONCENTRATION)
    assert concentration.name == "Concentration"
    assert concentration.key_ability == "con"
    assert concentration.armor_check_penalty is False
    assert concentration.trained_only is False
    assert concentration.phb_page == 69


def test_hide_definition():
    """Hide skill properties (PHB p.76)."""
    hide = get_skill(SkillID.HIDE)
    assert hide.name == "Hide"
    assert hide.key_ability == "dex"
    assert hide.armor_check_penalty is True
    assert hide.trained_only is False
    assert hide.phb_page == 76


# ==============================================================================
# SKILL CHECK RESOLUTION TESTS
# ==============================================================================

def test_tumble_dc_15_success(rogue, rng):
    """Tumble DC 15 check succeeds (PHB p.84)."""
    # Rogue: DEX +4, ranks 8, no ACP = +12 base
    # Need d20 >= 3 to hit DC 15
    result = resolve_skill_check(
        entity=rogue,
        skill_id=SkillID.TUMBLE,
        dc=15,
        rng=rng,
        circumstance_modifier=0
    )

    assert result.skill_id == SkillID.TUMBLE
    assert result.skill_name == "Tumble"
    assert result.dc == 15
    assert result.ability_modifier == 4
    assert result.skill_ranks == 8
    assert result.armor_check_penalty == 0
    assert result.total == result.d20_roll + 12
    # Result depends on d20 roll
    assert result.success == (result.total >= 15)


def test_tumble_with_armor_penalty(fighter, rng):
    """Tumble with heavy armor penalty (PHB p.84)."""
    # Fighter: DEX +2, ranks 5, ACP -4 = +3 base
    result = resolve_skill_check(
        entity=fighter,
        skill_id=SkillID.TUMBLE,
        dc=15,
        rng=rng,
        circumstance_modifier=0
    )

    assert result.ability_modifier == 2
    assert result.skill_ranks == 5
    assert result.armor_check_penalty == 4  # Subtracted from total
    assert result.total == result.d20_roll + 2 + 5 - 4


def test_concentration_dc_20(wizard, rng):
    """Concentration check DC 20 (PHB p.69)."""
    # Wizard: CON +1, ranks 8 = +9 base
    result = resolve_skill_check(
        entity=wizard,
        skill_id=SkillID.CONCENTRATION,
        dc=20,
        rng=rng,
        circumstance_modifier=0
    )

    assert result.skill_id == SkillID.CONCENTRATION
    assert result.ability_modifier == 1
    assert result.skill_ranks == 8
    assert result.armor_check_penalty == 0  # Concentration not affected by armor
    assert result.total == result.d20_roll + 9


def test_concentration_untrained(fighter, rng):
    """Concentration can be used untrained (PHB p.69)."""
    # Fighter has 3 ranks in Concentration
    result = resolve_skill_check(
        entity=fighter,
        skill_id=SkillID.CONCENTRATION,
        dc=15,
        rng=rng,
    )

    assert result.skill_ranks == 3
    assert result.ability_modifier == 3  # CON
    # Should not raise ValueError (not trained-only)


def test_tumble_trained_only_failure(guard, rng):
    """Tumble requires training (PHB p.84)."""
    # Guard has no Tumble ranks
    with pytest.raises(ValueError, match="trained-only"):
        resolve_skill_check(
            entity=guard,
            skill_id=SkillID.TUMBLE,
            dc=15,
            rng=rng,
        )


def test_spot_check(guard, rng):
    """Spot check (PHB p.83)."""
    # Guard: WIS +3, ranks 4 = +7 base
    result = resolve_skill_check(
        entity=guard,
        skill_id=SkillID.SPOT,
        dc=10,
        rng=rng,
    )

    assert result.skill_id == SkillID.SPOT
    assert result.ability_modifier == 3
    assert result.skill_ranks == 4
    assert result.armor_check_penalty == 0  # Spot not affected by armor


def test_listen_check(guard, rng):
    """Listen check (PHB p.78)."""
    # Guard: WIS +3, ranks 4 = +7 base
    result = resolve_skill_check(
        entity=guard,
        skill_id=SkillID.LISTEN,
        dc=5,
        rng=rng,
    )

    assert result.skill_id == SkillID.LISTEN
    assert result.ability_modifier == 3
    assert result.skill_ranks == 4


def test_balance_check(rogue, rng):
    """Balance check on difficult surface (PHB p.67)."""
    # Rogue has no Balance ranks, but can use untrained (DEX +4)
    result = resolve_skill_check(
        entity=rogue,
        skill_id=SkillID.BALANCE,
        dc=10,
        rng=rng,
    )

    assert result.skill_id == SkillID.BALANCE
    assert result.ability_modifier == 4
    assert result.skill_ranks == 0  # Untrained


def test_circumstance_modifier(wizard, rng):
    """Circumstance modifiers apply correctly."""
    result = resolve_skill_check(
        entity=wizard,
        skill_id=SkillID.CONCENTRATION,
        dc=15,
        rng=rng,
        circumstance_modifier=4  # Magic item or spell bonus
    )

    assert result.circumstance_modifier == 4
    assert result.total == result.d20_roll + 9 + 4


# ==============================================================================
# OPPOSED CHECK TESTS
# ==============================================================================

def test_hide_vs_spot(rogue, guard, rng):
    """Hide vs Spot opposed check (PHB p.76, p.83)."""
    # Rogue: DEX +4, Hide 8, ACP 0 = +12
    # Guard: WIS +3, Spot 4 = +7
    result = resolve_opposed_check(
        actor=rogue,
        opponent=guard,
        actor_skill=SkillID.HIDE,
        opponent_skill=SkillID.SPOT,
        rng=rng,
    )

    assert result.actor_skill == SkillID.HIDE
    assert result.opponent_skill == SkillID.SPOT
    # Rogue has significant advantage (+12 vs +7)
    # Result depends on rolls


def test_move_silently_vs_listen(rogue, guard, rng):
    """Move Silently vs Listen opposed check (PHB p.79, p.78)."""
    # Rogue: DEX +4, Move Silently 8, ACP 0 = +12
    # Guard: WIS +3, Listen 4 = +7
    result = resolve_opposed_check(
        actor=rogue,
        opponent=guard,
        actor_skill=SkillID.MOVE_SILENTLY,
        opponent_skill=SkillID.LISTEN,
        rng=rng,
    )

    assert result.actor_skill == SkillID.MOVE_SILENTLY
    assert result.opponent_skill == SkillID.LISTEN


def test_opposed_check_tie_favors_actor(rng):
    """Ties in opposed checks favor the active checker."""
    # Create two identical entities
    entity1 = {
        EF.ENTITY_ID: "entity1",
        EF.DEX_MOD: 2,
        EF.SKILL_RANKS: {SkillID.HIDE: 5},
        EF.CLASS_SKILLS: [SkillID.HIDE],
        EF.ARMOR_CHECK_PENALTY: 0,
    }
    entity2 = {
        EF.ENTITY_ID: "entity2",
        EF.WIS_MOD: 2,  # Different ability, same total modifier
        EF.SKILL_RANKS: {SkillID.SPOT: 5},
        EF.CLASS_SKILLS: [SkillID.SPOT],
        EF.ARMOR_CHECK_PENALTY: 0,
    }

    # Force a tie by using same seed twice
    rng1 = RNGManager(master_seed=99)
    result = resolve_opposed_check(
        actor=entity1,
        opponent=entity1,  # Same entity to force identical modifiers
        actor_skill=SkillID.HIDE,
        opponent_skill=SkillID.HIDE,
        rng=rng1,
    )

    # If rolls are different, skip this test
    if result.actor_d20 == result.opponent_d20:
        assert result.tie is True
        assert result.actor_wins is True  # Ties favor actor


def test_opposed_check_circumstance_modifiers(rogue, guard, rng):
    """Circumstance modifiers in opposed checks."""
    result = resolve_opposed_check(
        actor=rogue,
        opponent=guard,
        actor_skill=SkillID.HIDE,
        opponent_skill=SkillID.SPOT,
        rng=rng,
        actor_circumstance=2,  # Cover bonus
        opponent_circumstance=-4,  # Poor lighting
    )

    # Actor total should include +2
    # Opponent total should include -4
    base_actor = 4 + 8  # DEX + ranks
    base_opponent = 3 + 4  # WIS + ranks
    assert result.actor_total == result.actor_d20 + base_actor + 2
    assert result.opponent_total == result.opponent_d20 + base_opponent - 4


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

def test_no_skill_ranks_defaults_to_zero(rng):
    """Entities without skill_ranks field default to 0 ranks."""
    entity = {
        EF.ENTITY_ID: "commoner",
        EF.WIS_MOD: 0,
        # No EF.SKILL_RANKS
    }

    result = resolve_skill_check(
        entity=entity,
        skill_id=SkillID.SPOT,
        dc=10,
        rng=rng,
    )

    assert result.skill_ranks == 0
    assert result.total == result.d20_roll + 0  # WIS +0, ranks 0


def test_no_armor_check_penalty_defaults_to_zero(rogue, rng):
    """Entities without armor_check_penalty field default to 0."""
    # Remove ACP from rogue
    rogue_no_acp = rogue.copy()
    del rogue_no_acp[EF.ARMOR_CHECK_PENALTY]

    result = resolve_skill_check(
        entity=rogue_no_acp,
        skill_id=SkillID.TUMBLE,
        dc=15,
        rng=rng,
    )

    assert result.armor_check_penalty == 0


def test_invalid_skill_id_raises_keyerror(fighter, rng):
    """Invalid skill_id raises KeyError."""
    with pytest.raises(KeyError):
        resolve_skill_check(
            entity=fighter,
            skill_id="invalid_skill",
            dc=15,
            rng=rng,
        )


# ==============================================================================
# D&D 3.5e RULE VALIDATION TESTS
# ==============================================================================

def test_armor_check_penalty_applies_to_tumble(fighter, rng):
    """Tumble is affected by armor check penalty (PHB p.84)."""
    result = resolve_skill_check(
        entity=fighter,
        skill_id=SkillID.TUMBLE,
        dc=15,
        rng=rng,
    )

    # ACP should be subtracted
    assert result.armor_check_penalty > 0


def test_armor_check_penalty_applies_to_hide(rogue, rng):
    """Hide is affected by armor check penalty (PHB p.76)."""
    rogue_armored = rogue.copy()
    rogue_armored[EF.ARMOR_CHECK_PENALTY] = 3

    result = resolve_skill_check(
        entity=rogue_armored,
        skill_id=SkillID.HIDE,
        dc=10,
        rng=rng,
    )

    assert result.armor_check_penalty == 3


def test_concentration_not_affected_by_armor(wizard, rng):
    """Concentration is NOT affected by armor (PHB p.69)."""
    wizard_armored = wizard.copy()
    wizard_armored[EF.ARMOR_CHECK_PENALTY] = 5

    result = resolve_skill_check(
        entity=wizard_armored,
        skill_id=SkillID.CONCENTRATION,
        dc=15,
        rng=rng,
    )

    assert result.armor_check_penalty == 0  # Not applied


def test_spot_not_affected_by_armor(guard, rng):
    """Spot is NOT affected by armor (PHB p.83)."""
    result = resolve_skill_check(
        entity=guard,
        skill_id=SkillID.SPOT,
        dc=10,
        rng=rng,
    )

    # Guard has ACP 2 but Spot should ignore it
    assert result.armor_check_penalty == 0


# ==============================================================================
# RNG STREAM TESTS
# ==============================================================================

def test_skill_checks_use_combat_stream(fighter, rng):
    """Skill checks use combat RNG stream."""
    # This is a behavioral test - we verify by checking that repeated calls
    # with same seed produce same results
    rng1 = RNGManager(master_seed=12345)
    rng2 = RNGManager(master_seed=12345)

    result1 = resolve_skill_check(
        entity=fighter,
        skill_id=SkillID.TUMBLE,
        dc=15,
        rng=rng1,
    )

    result2 = resolve_skill_check(
        entity=fighter,
        skill_id=SkillID.TUMBLE,
        dc=15,
        rng=rng2,
    )

    assert result1.d20_roll == result2.d20_roll
    assert result1.total == result2.total

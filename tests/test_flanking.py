"""Flanking detection tests (PHB p.153).

Validates:
- Flanking geometry: opposite sides/corners detection
- Flanking bonus: +2 when flanking, 0 when not
- Position requirements: attacker and ally must be adjacent to target
- Threat requirements: attacker and ally must be alive and unincapacitated
- Team requirements: attacker and ally must be on same team
- Denied Dex to AC: flat-footed, stunned, helpless conditions
- Edge cases: no positions, defeated entities, same team targets

Evidence:
- PHB p.153: Flanking rules and diagram
- PHB p.137: Threatened area
- PHB p.311: Conditions that deny Dex to AC
"""

import pytest

from aidm.core.flanking import (
    FLANKING_BONUS,
    MIN_FLANKING_ANGLE,
    check_flanking,
    get_flanking_info,
    is_denied_dex_to_ac,
    _angle_between,
    _is_threatening,
)
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position


# ======================================================================
# HELPERS
# ======================================================================


def make_world(*entity_defs) -> WorldState:
    """Build a WorldState from entity tuples.

    Each tuple: (entity_id, team, x, y, hp, **extras)
    """
    entities = {}
    for defn in entity_defs:
        eid = defn[0]
        team = defn[1]
        x, y = defn[2], defn[3]
        hp = defn[4] if len(defn) > 4 else 20
        extras = defn[5] if len(defn) > 5 else {}
        entities[eid] = {
            EF.ENTITY_ID: eid,
            EF.TEAM: team,
            EF.POSITION: {"x": x, "y": y},
            EF.HP_CURRENT: hp,
            EF.HP_MAX: hp,
            EF.AC: 15,
            EF.DEFEATED: False,
            EF.ATTACK_BONUS: 5,
            **extras,
        }
    return WorldState(ruleset_version="RAW_3.5", entities=entities)


# ======================================================================
# CATEGORY 1: ANGLE COMPUTATION (4 tests)
# ======================================================================


class TestAngleComputation:
    """Verify _angle_between for flanking geometry."""

    def test_directly_opposite_180_degrees(self):
        """Entities on opposite sides of target → 180 degrees.

        PHB p.153 diagram: directly across = flanking.
        """
        target = Position(5, 5)
        attacker = Position(4, 5)  # Left
        ally = Position(6, 5)     # Right (directly opposite)
        angle = _angle_between(target, attacker, ally)
        assert abs(angle - 180.0) < 0.1

    def test_opposite_corners_135_degrees(self):
        """Entities on opposite corners → ~135 degrees.

        PHB p.153 diagram: opposite corners qualify as flanking.
        """
        target = Position(5, 5)
        attacker = Position(4, 4)  # SW corner
        ally = Position(6, 6)     # NE corner (opposite)
        angle = _angle_between(target, attacker, ally)
        assert abs(angle - 180.0) < 0.1  # Directly opposite diagonals = 180

    def test_adjacent_same_side_90_degrees(self):
        """Entities on same side → ~90 degrees (not flanking).

        Two allies both north of target are NOT flanking.
        """
        target = Position(5, 5)
        attacker = Position(4, 6)  # NW
        ally = Position(6, 6)     # NE
        angle = _angle_between(target, attacker, ally)
        assert angle < MIN_FLANKING_ANGLE  # ~90 degrees, not flanking

    def test_zero_angle_same_position(self):
        """Same position as target → 0 degrees."""
        target = Position(5, 5)
        a = Position(5, 5)
        b = Position(6, 5)
        angle = _angle_between(target, a, b)
        assert angle == 0.0


# ======================================================================
# CATEGORY 2: BASIC FLANKING DETECTION (6 tests)
# ======================================================================


class TestBasicFlanking:
    """Core flanking detection with valid positions."""

    def test_flanking_opposite_sides(self):
        """PHB p.153: Two allies on opposite sides → flanking (+2 bonus)."""
        #   A . T . B
        # A=attacker at (3,5), T=target at (5,5), B=ally at (7,5)
        # Wait — need adjacency. Let's use adjacent squares.
        # Attacker at (4,5), Target at (5,5), Ally at (6,5)
        world = make_world(
            ("fighter", "party", 4, 5),
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 5),
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == FLANKING_BONUS

    def test_flanking_opposite_corners(self):
        """PHB p.153: Two allies on opposite corners → flanking (+2 bonus)."""
        world = make_world(
            ("fighter", "party", 4, 4),  # SW of target
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 6),    # NE of target
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == FLANKING_BONUS

    def test_no_flanking_same_side(self):
        """Two allies on same side → no flanking (0 bonus)."""
        world = make_world(
            ("fighter", "party", 4, 5),  # Left of target
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 4, 6),    # Also left (NW), ~90 degrees
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_no_flanking_solo_attacker(self):
        """Single attacker with no allies → no flanking."""
        world = make_world(
            ("fighter", "party", 4, 5),
            ("goblin", "enemy", 5, 5),
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_flanking_info_returns_ally_ids(self):
        """get_flanking_info returns which allies enable flanking."""
        world = make_world(
            ("fighter", "party", 4, 5),
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 5),
        )
        bonus, is_flanking, allies = get_flanking_info(world, "fighter", "goblin")
        assert bonus == FLANKING_BONUS
        assert is_flanking is True
        assert "rogue" in allies

    def test_flanking_vertical_axis(self):
        """Flanking along north-south axis."""
        world = make_world(
            ("fighter", "party", 5, 4),  # South
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 5, 6),    # North
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == FLANKING_BONUS


# ======================================================================
# CATEGORY 3: THREAT REQUIREMENTS (5 tests)
# ======================================================================


class TestThreatRequirements:
    """Flanking requires both attacker and ally to threaten."""

    def test_defeated_ally_no_flanking(self):
        """Defeated ally cannot contribute to flanking."""
        world = make_world(
            ("fighter", "party", 4, 5),
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 5, 0, {EF.DEFEATED: True}),
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_zero_hp_ally_no_flanking(self):
        """Ally at 0 HP cannot threaten, no flanking."""
        world = make_world(
            ("fighter", "party", 4, 5),
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 5, 0),
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_incapacitated_ally_no_flanking(self):
        """Ally with actions_prohibited cannot threaten."""
        world = make_world(
            ("fighter", "party", 4, 5),
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 5, 20, {
                EF.CONDITIONS: {
                    "stunned": {
                        "condition_type": "stunned",
                        "source": "test",
                        "modifiers": {
                            "ac_modifier": -2,
                            "attack_modifier": 0,
                            "damage_modifier": 0,
                            "dex_modifier": 0,
                            "actions_prohibited": True,
                            "movement_prohibited": False,
                            "standing_triggers_aoo": False,
                            "auto_hit_if_helpless": False,
                            "loses_dex_to_ac": True,
                        },
                        "applied_at_event_id": 1,
                    }
                }
            }),
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_defeated_attacker_no_flanking(self):
        """Defeated attacker cannot flank."""
        world = make_world(
            ("fighter", "party", 4, 5, 0, {EF.DEFEATED: True}),
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 5),
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_is_threatening_positive(self):
        """Alive entity with HP > 0 and no incapacitation threatens."""
        entity = {
            EF.HP_CURRENT: 20,
            EF.DEFEATED: False,
        }
        assert _is_threatening(entity) is True


# ======================================================================
# CATEGORY 4: POSITION REQUIREMENTS (4 tests)
# ======================================================================


class TestPositionRequirements:
    """Flanking requires adjacency and position data."""

    def test_no_position_attacker_no_flanking(self):
        """Attacker without position → no flanking."""
        entities = {
            "fighter": {
                EF.ENTITY_ID: "fighter",
                EF.TEAM: "party",
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 15,
                EF.DEFEATED: False,
                # No POSITION
            },
            "goblin": {
                EF.ENTITY_ID: "goblin",
                EF.TEAM: "enemy",
                EF.POSITION: {"x": 5, "y": 5},
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 15,
                EF.DEFEATED: False,
            },
        }
        world = WorldState(ruleset_version="RAW_3.5", entities=entities)
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_no_position_target_no_flanking(self):
        """Target without position → no flanking."""
        entities = {
            "fighter": {
                EF.ENTITY_ID: "fighter",
                EF.TEAM: "party",
                EF.POSITION: {"x": 4, "y": 5},
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 15,
                EF.DEFEATED: False,
            },
            "goblin": {
                EF.ENTITY_ID: "goblin",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 15,
                EF.DEFEATED: False,
                # No POSITION
            },
        }
        world = WorldState(ruleset_version="RAW_3.5", entities=entities)
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_ally_not_adjacent_no_flanking(self):
        """Ally 2+ squares away from target → no flanking."""
        world = make_world(
            ("fighter", "party", 4, 5),
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 8, 5),  # 3 squares away — not adjacent
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_attacker_not_adjacent_no_flanking(self):
        """Attacker not adjacent to target → no flanking."""
        world = make_world(
            ("fighter", "party", 2, 5),  # 3 squares away
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 5),
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0


# ======================================================================
# CATEGORY 5: TEAM REQUIREMENTS (3 tests)
# ======================================================================


class TestTeamRequirements:
    """Flanking requires same-team allies."""

    def test_different_team_ally_no_flanking(self):
        """Enemy on opposite side doesn't enable flanking."""
        world = make_world(
            ("fighter", "party", 4, 5),
            ("goblin", "enemy", 5, 5),
            ("orc", "enemy", 6, 5),  # Enemy, not ally
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0

    def test_missing_entity_no_flanking(self):
        """Missing attacker or target → 0 bonus, no crash."""
        world = make_world(
            ("fighter", "party", 4, 5),
        )
        bonus = check_flanking(world, "fighter", "nonexistent")
        assert bonus == 0
        bonus = check_flanking(world, "nonexistent", "fighter")
        assert bonus == 0

    def test_no_team_on_attacker_no_flanking(self):
        """Attacker without team → no flanking."""
        entities = {
            "fighter": {
                EF.ENTITY_ID: "fighter",
                EF.POSITION: {"x": 4, "y": 5},
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 15,
                EF.DEFEATED: False,
                # No TEAM
            },
            "goblin": {
                EF.ENTITY_ID: "goblin",
                EF.TEAM: "enemy",
                EF.POSITION: {"x": 5, "y": 5},
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 15,
                EF.DEFEATED: False,
            },
        }
        world = WorldState(ruleset_version="RAW_3.5", entities=entities)
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == 0


# ======================================================================
# CATEGORY 6: DENIED DEX TO AC (4 tests)
# ======================================================================


class TestDeniedDexToAC:
    """is_denied_dex_to_ac for Sneak Attack eligibility."""

    def test_flat_footed_denied_dex(self):
        """Flat-footed target is denied Dex to AC."""
        world = make_world(
            ("goblin", "enemy", 5, 5, 20, {
                EF.CONDITIONS: {
                    "flat_footed": {
                        "condition_type": "flat_footed",
                        "source": "surprise",
                        "modifiers": {
                            "ac_modifier": 0,
                            "attack_modifier": 0,
                            "damage_modifier": 0,
                            "dex_modifier": 0,
                            "loses_dex_to_ac": True,
                            "movement_prohibited": False,
                            "actions_prohibited": False,
                            "standing_triggers_aoo": False,
                            "auto_hit_if_helpless": False,
                        },
                        "applied_at_event_id": 1,
                    }
                }
            }),
        )
        assert is_denied_dex_to_ac(world, "goblin") is True

    def test_stunned_denied_dex(self):
        """Stunned target is denied Dex to AC."""
        world = make_world(
            ("goblin", "enemy", 5, 5, 20, {
                EF.CONDITIONS: {
                    "stunned": {
                        "condition_type": "stunned",
                        "source": "spell",
                        "modifiers": {
                            "ac_modifier": -2,
                            "attack_modifier": 0,
                            "damage_modifier": 0,
                            "dex_modifier": 0,
                            "loses_dex_to_ac": True,
                            "actions_prohibited": True,
                            "movement_prohibited": False,
                            "standing_triggers_aoo": False,
                            "auto_hit_if_helpless": False,
                        },
                        "applied_at_event_id": 1,
                    }
                }
            }),
        )
        assert is_denied_dex_to_ac(world, "goblin") is True

    def test_no_conditions_not_denied(self):
        """No conditions → not denied Dex to AC."""
        world = make_world(("goblin", "enemy", 5, 5))
        assert is_denied_dex_to_ac(world, "goblin") is False

    def test_shaken_not_denied(self):
        """Shaken does NOT deny Dex to AC."""
        world = make_world(
            ("goblin", "enemy", 5, 5, 20, {
                EF.CONDITIONS: {
                    "shaken": {
                        "condition_type": "shaken",
                        "source": "fear",
                        "modifiers": {
                            "ac_modifier": 0,
                            "attack_modifier": -2,
                            "damage_modifier": 0,
                            "dex_modifier": 0,
                            "loses_dex_to_ac": False,
                            "movement_prohibited": False,
                            "actions_prohibited": False,
                            "standing_triggers_aoo": False,
                            "auto_hit_if_helpless": False,
                        },
                        "applied_at_event_id": 1,
                    }
                }
            }),
        )
        assert is_denied_dex_to_ac(world, "goblin") is False


# ======================================================================
# CATEGORY 7: MULTIPLE ALLIES (3 tests)
# ======================================================================


class TestMultipleAllies:
    """Flanking with multiple potential allies."""

    def test_multiple_allies_flanking(self):
        """Multiple allies on opposite sides all contribute."""
        world = make_world(
            ("fighter", "party", 4, 5),  # Left
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 5),    # Right (opposite)
            ("wizard", "party", 6, 6),   # NE (not opposite to fighter)
        )
        bonus, is_flanking, allies = get_flanking_info(world, "fighter", "goblin")
        assert is_flanking is True
        assert "rogue" in allies

    def test_ally_flanking_from_other_direction(self):
        """Ally can flank even if first ally can't."""
        world = make_world(
            ("fighter", "party", 4, 5),  # Left
            ("goblin", "enemy", 5, 5),
            ("cleric", "party", 4, 6),   # NW (same side, no flank)
            ("rogue", "party", 6, 5),    # Right (opposite, flanking!)
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == FLANKING_BONUS

    def test_three_party_members_surrounding(self):
        """Three allies surrounding target — attacker flanks with the opposite one."""
        world = make_world(
            ("fighter", "party", 4, 5),  # Left
            ("goblin", "enemy", 5, 5),
            ("rogue", "party", 6, 5),    # Right (opposite to fighter)
            ("cleric", "party", 5, 4),   # South
            ("bard", "party", 5, 6),     # North
        )
        bonus = check_flanking(world, "fighter", "goblin")
        assert bonus == FLANKING_BONUS

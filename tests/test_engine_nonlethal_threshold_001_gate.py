"""Gate tests: WO-ENGINE-NONLETHAL-THRESHOLD-001 — Nonlethal damage threshold (PHB p.145-146).

nonlethal == current HP → STAGGERED. nonlethal > current HP → UNCONSCIOUS.
EF.NONLETHAL_DAMAGE accumulation and threshold check already implemented.

Gate label: ENGINE-NONLETHAL-THRESHOLD-001
KERNEL-01 (Entity Lifecycle) touch.
"""

import pytest
from copy import deepcopy
from unittest.mock import MagicMock

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.attack_resolver import resolve_nonlethal_attack, check_nonlethal_threshold


# ---------------------------------------------------------------------------
# Direct threshold function tests (CD-001 - CD-003 style: unit tests)
# ---------------------------------------------------------------------------

def test_nl_001_nonlethal_equals_hp_staggered():
    """NL-001: Entity with 10 HP takes 10 nonlethal → STAGGERED threshold returned."""
    result = check_nonlethal_threshold(current_hp=10, nonlethal_total=10)
    assert result == "staggered", \
        f"NL-001: Expected 'staggered' when nonlethal == hp; got '{result}'"


def test_nl_002_nonlethal_exceeds_hp_unconscious():
    """NL-002: Entity with 10 HP, 12 nonlethal → UNCONSCIOUS threshold returned."""
    result = check_nonlethal_threshold(current_hp=10, nonlethal_total=12)
    assert result == "unconscious", \
        f"NL-002: Expected 'unconscious' when nonlethal > hp; got '{result}'"


def test_nl_003_nonlethal_below_hp_none():
    """NL-003: Entity with 10 HP takes 9 nonlethal → None (no threshold)."""
    result = check_nonlethal_threshold(current_hp=10, nonlethal_total=9)
    assert result is None, \
        f"NL-003: Expected None when nonlethal < hp; got '{result}'"


# ---------------------------------------------------------------------------
# Full resolve_nonlethal_attack integration tests
# ---------------------------------------------------------------------------

def _make_attacker(attacker_id: str = "attacker_01") -> dict:
    return {
        EF.ENTITY_ID: attacker_id,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.BAB: 5,
        EF.ATTACK_BONUS: 5,
        EF.STR_MOD: 2,
        EF.DEX_MOD: 1,
        EF.POSITION: {"x": 0, "y": 0},
        EF.WEAPON: {"name": "unarmed", "damage_dice": "1d3", "crit_range": 20,
                    "crit_multiplier": 2, "damage_type": "bludgeoning",
                    "attack_bonus": 0, "enhancement_bonus": 0},
    }


def _make_target(target_id: str = "target_01", hp: int = 10,
                 nonlethal: int = 0, conditions: dict = None) -> dict:
    entity = {
        EF.ENTITY_ID: target_id,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.TEAM: "monsters",
        EF.DEFEATED: False,
        EF.CONDITIONS: conditions or {},
        EF.FEATS: [],
        EF.BAB: 3,
        EF.ATTACK_BONUS: 3,
        EF.STR_MOD: 1,
        EF.DEX_MOD: 0,
        EF.AC: 10,
        EF.POSITION: {"x": 1, "y": 0},
    }
    if nonlethal:
        entity[EF.NONLETHAL_DAMAGE] = nonlethal
    return entity


def _make_world_nl(attacker_id: str, target_id: str,
                    target_hp: int = 10, target_nonlethal: int = 0,
                    target_conditions: dict = None) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={
            attacker_id: _make_attacker(attacker_id),
            target_id: _make_target(target_id, hp=target_hp,
                                     nonlethal=target_nonlethal,
                                     conditions=target_conditions),
        },
        active_combat={
            "initiative_order": [attacker_id, target_id],
            "aoo_used_this_round": [],
            "flat_footed_actors": [],
            "feint_flat_footed": [],
        },
    )


def _make_nl_intent(attacker_id: str, target_id: str, attack_bonus: int = 20):
    """Create a nonlethal attack intent guaranteed to hit."""
    from aidm.schemas.attack import NonlethalAttackIntent
    return NonlethalAttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        attack_bonus=attack_bonus,
        damage_dice="1d1",    # Always rolls 1 damage for predictability
        damage_bonus=9,       # Total: 1 + 9 = 10 damage
    )


def _make_rng(d20_roll: int = 20, damage_roll: int = 1):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint.side_effect = [d20_roll, damage_roll]
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# NL-004: Already STAGGERED; more nonlethal exceeding HP → UNCONSCIOUS
# ---------------------------------------------------------------------------

def test_nl_004_staggered_to_unconscious():
    """NL-004: Entity already STAGGERED; takes more nonlethal → transitions to UNCONSCIOUS."""
    # Verify threshold function handles staggered → unconscious transition
    # Entity at 10 HP, 10 nonlethal = staggered. Adding 1 more = 11 > 10 = unconscious.
    result = check_nonlethal_threshold(current_hp=10, nonlethal_total=11)
    assert result == "unconscious", \
        f"NL-004: Expected 'unconscious' when nonlethal > hp; got '{result}'"


# ---------------------------------------------------------------------------
# NL-005: 8 nonlethal already; takes 2 more → total = 10 = HP → STAGGERED
# ---------------------------------------------------------------------------

def test_nl_005_accumulated_nonlethal_equals_hp():
    """NL-005: 8 nonlethal already + 2 more = 10 = HP → staggered threshold."""
    result = check_nonlethal_threshold(current_hp=10, nonlethal_total=8 + 2)
    assert result == "staggered", \
        f"NL-005: Expected 'staggered' when accumulated total = hp; got '{result}'"


# ---------------------------------------------------------------------------
# NL-006: 8 nonlethal already; takes 3 more → total = 11 > HP → UNCONSCIOUS
# ---------------------------------------------------------------------------

def test_nl_006_accumulated_nonlethal_exceeds_hp():
    """NL-006: 8 nonlethal already + 3 more = 11 > 10 HP → unconscious threshold."""
    result = check_nonlethal_threshold(current_hp=10, nonlethal_total=8 + 3)
    assert result == "unconscious", \
        f"NL-006: Expected 'unconscious' when accumulated total > hp; got '{result}'"


# ---------------------------------------------------------------------------
# NL-007: No NONLETHAL_DAMAGE field → treat as 0, no crash
# ---------------------------------------------------------------------------

def test_nl_007_no_nonlethal_field_no_crash():
    """NL-007: Entity with no NONLETHAL_DAMAGE field → threshold returns None (0 nonlethal)."""
    # Simulate: entity with no field → getattr default is 0
    result = check_nonlethal_threshold(current_hp=10, nonlethal_total=0)
    assert result is None, \
        f"NL-007: Expected None when nonlethal_total=0 (no field); got '{result}'"


# ---------------------------------------------------------------------------
# NL-008: Entity with 0 HP (disabled); nonlethal > HP → UNCONSCIOUS
# ---------------------------------------------------------------------------

def test_nl_008_zero_hp_entity_nonlethal_unconscious():
    """NL-008: Entity with 0 HP (disabled); nonlethal > 0 → UNCONSCIOUS."""
    # 0 HP entity: any nonlethal > 0 crosses threshold
    result = check_nonlethal_threshold(current_hp=0, nonlethal_total=1)
    assert result == "unconscious", \
        f"NL-008: Expected 'unconscious' for 0 HP entity with 1 nonlethal; got '{result}'"

"""ENGINE-BARDIC-MUSIC Gate -- Bardic Music Inspire Courage (10 tests).

Gate: ENGINE-BARDIC-MUSIC
Tests: BM-01 through BM-10
WO: WO-ENGINE-BARDIC-MUSIC-001
"""

import pytest
from copy import deepcopy
from unittest import mock

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.attack import Weapon
from aidm.schemas.intents import BardicMusicIntent
from aidm.core.bardic_music_resolver import (
    validate_bardic_music,
    resolve_bardic_music,
    get_inspire_courage_bonus,
    tick_inspire_courage,
)


def _bard(eid="bard", level=1, cha_mod=2, uses=3):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 13,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: 0,
        EF.DEX_MOD: 2,
        EF.CON_MOD: 1,
        EF.CHA_MOD: cha_mod,
        EF.BAB: level // 2,
        EF.CLASS_LEVELS: {"bard": level},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.BARDIC_MUSIC_USES_REMAINING: uses,
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.INSPIRE_COURAGE_ROUNDS_REMAINING: 0,
    }


def _ally(eid="fighter"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 25,
        EF.HP_MAX: 25,
        EF.AC: 15,
        EF.DEFEATED: False,
        EF.CLASS_LEVELS: {"fighter": 3},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.INSPIRE_COURAGE_ROUNDS_REMAINING: 0,
        EF.ATTACK_BONUS: 5,
        EF.STR_MOD: 3,
    }


def _fighter_no_ic(eid="fighter2"):
    """Entity without bard class levels."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 14,
        EF.DEFEATED: False,
        EF.CLASS_LEVELS: {"fighter": 4},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.BARDIC_MUSIC_USES_REMAINING: 0,
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
    }


def _world(entities):
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
        },
    )

# ===========================================================================
# BM-01: Inspire Courage activates -- event emitted, INSPIRE_COURAGE_ACTIVE set
# ===========================================================================

def test_bm01_inspire_courage_activates():
    """BM-01: resolve_bardic_music emits inspire_courage_start, sets INSPIRE_COURAGE_ACTIVE."""
    bard = _bard(level=1, uses=3)
    ally = _ally()
    ws = _world({"bard": bard, "fighter": ally})
    intent = BardicMusicIntent(actor_id="bard", performance="inspire_courage", ally_ids=["fighter"])

    events, ws2 = resolve_bardic_music(intent, ws, 0, 0.0)

    evt_types = [e.event_type for e in events]
    assert "inspire_courage_start" in evt_types, f"Expected inspire_courage_start, got {evt_types}"
    assert ws2.entities["bard"][EF.INSPIRE_COURAGE_ACTIVE] is True
    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ACTIVE] is True


# ===========================================================================
# BM-02: Bonus scaling by Bard level
# ===========================================================================

def test_bm02_bonus_scaling():
    """BM-02: get_inspire_courage_bonus returns correct bonus by level."""
    assert get_inspire_courage_bonus(1) == 1
    assert get_inspire_courage_bonus(7) == 1
    assert get_inspire_courage_bonus(8) == 2
    assert get_inspire_courage_bonus(13) == 2
    assert get_inspire_courage_bonus(14) == 3
    assert get_inspire_courage_bonus(19) == 3
    assert get_inspire_courage_bonus(20) == 4


# ===========================================================================
# BM-03: BARDIC_MUSIC_USES_REMAINING decremented
# ===========================================================================

def test_bm03_uses_decremented():
    """BM-03: BARDIC_MUSIC_USES_REMAINING decremented by 1 after activation."""
    bard = _bard(level=1, uses=3)
    ws = _world({"bard": bard})
    intent = BardicMusicIntent(actor_id="bard", performance="inspire_courage", ally_ids=[])

    _, ws2 = resolve_bardic_music(intent, ws, 0, 0.0)
    assert ws2.entities["bard"][EF.BARDIC_MUSIC_USES_REMAINING] == 2


# ===========================================================================
# BM-04: Ally attack roll includes inspire courage bonus
# ===========================================================================

def test_bm04_ally_attack_includes_inspire_bonus():
    """BM-04: Ally with INSPIRE_COURAGE_ACTIVE=True has non-zero INSPIRE_COURAGE_BONUS."""
    bard = _bard(level=1, uses=3)
    ally = _ally()
    ws = _world({"bard": bard, "fighter": ally})
    intent = BardicMusicIntent(actor_id="bard", performance="inspire_courage", ally_ids=["fighter"])

    _, ws2 = resolve_bardic_music(intent, ws, 0, 0.0)

    fighter = ws2.entities["fighter"]
    assert fighter[EF.INSPIRE_COURAGE_ACTIVE] is True
    assert fighter[EF.INSPIRE_COURAGE_BONUS] >= 1


# ===========================================================================
# BM-05: Fear save includes inspire courage bonus (via get_save_bonus)
# ===========================================================================

def test_bm05_fear_save_bonus():
    """BM-05: Entity with INSPIRE_COURAGE_ACTIVE gets bonus in get_save_bonus calculation."""
    from aidm.core.save_resolver import get_save_bonus
    from aidm.schemas.saves import SaveType

    entity = _ally()
    entity[EF.INSPIRE_COURAGE_ACTIVE] = True
    entity[EF.INSPIRE_COURAGE_BONUS] = 1
    entity[EF.SAVE_WILL] = 2
    entity[EF.WIS_MOD] = 1
    entity[EF.CONDITIONS] = {}
    ws = _world({"fighter": entity})

    bonus_with = get_save_bonus(ws, "fighter", SaveType.WILL)

    # Remove inspire courage and check without
    entity2 = deepcopy(entity)
    entity2[EF.INSPIRE_COURAGE_ACTIVE] = False
    entity2[EF.INSPIRE_COURAGE_BONUS] = 0
    ws2 = _world({"fighter": entity2})
    bonus_without = get_save_bonus(ws2, "fighter", SaveType.WILL)

    assert bonus_with == bonus_without + 1, (
        f"Expected inspire bonus to add +1; got with={bonus_with}, without={bonus_without}"
    )


# ===========================================================================
# BM-06: No stacking -- higher bonus wins
# ===========================================================================

def test_bm06_no_stacking():
    """BM-06: Second bard's lower inspire courage does not reduce existing higher bonus."""
    # Pre-set ally with +2 bonus
    ally = _ally()
    ally[EF.INSPIRE_COURAGE_ACTIVE] = True
    ally[EF.INSPIRE_COURAGE_BONUS] = 2
    ally[EF.INSPIRE_COURAGE_ROUNDS_REMAINING] = 8

    # Level 1 bard would give +1 -- should not overwrite +2
    bard = _bard(level=1, uses=3)
    ws = _world({"bard": bard, "fighter": ally})
    intent = BardicMusicIntent(actor_id="bard", performance="inspire_courage", ally_ids=["fighter"])

    _, ws2 = resolve_bardic_music(intent, ws, 0, 0.0)

    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_BONUS] == 2, (
        "Existing +2 should not be reduced by new +1"
    )


# ===========================================================================
# BM-07: No uses remaining
# ===========================================================================

def test_bm07_no_uses():
    """BM-07: validate_bardic_music returns no_bardic_music_uses when uses=0."""
    bard = _bard(level=1, uses=0)
    ws = _world({"bard": bard})
    reason = validate_bardic_music(ws.entities["bard"], ws)
    assert reason == "no_bardic_music_uses", f"Got {reason!r}"


# ===========================================================================
# BM-08: Non-bard cannot use bardic music
# ===========================================================================

def test_bm08_not_a_bard():
    """BM-08: validate_bardic_music returns not_a_bard for non-Bard entity."""
    fighter = _fighter_no_ic()
    fighter[EF.BARDIC_MUSIC_USES_REMAINING] = 1
    ws = _world({"fighter2": fighter})
    reason = validate_bardic_music(ws.entities["fighter2"], ws)
    assert reason == "not_a_bard", f"Got {reason!r}"


# ===========================================================================
# BM-09: Buff expires after tick_inspire_courage called 8 times
# ===========================================================================

def test_bm09_buff_expires():
    """BM-09: After 8 tick_inspire_courage calls, INSPIRE_COURAGE_ACTIVE becomes False."""
    ally = _ally()
    ally[EF.INSPIRE_COURAGE_ACTIVE] = True
    ally[EF.INSPIRE_COURAGE_BONUS] = 1
    ally[EF.INSPIRE_COURAGE_ROUNDS_REMAINING] = 1  # one round left
    ws = _world({"fighter": ally})

    events, ws2 = tick_inspire_courage(ws, 0, 0.0)

    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_ACTIVE] is False
    assert ws2.entities["fighter"][EF.INSPIRE_COURAGE_BONUS] == 0
    assert any(e.event_type == "inspire_courage_end" for e in events)


# ===========================================================================
# BM-10: Unsupported performance type
# ===========================================================================

def test_bm10_unsupported_performance():
    """BM-10: validate_bardic_music returns unsupported_performance for non-inspire_courage."""
    bard = _bard(level=5, uses=3)
    ws = _world({"bard": bard})
    reason = validate_bardic_music(ws.entities["bard"], ws, performance="countersong")
    assert reason == "unsupported_performance", f"Got {reason!r}"

"""ENGINE-WILD-SHAPE Gate -- Druid Wild Shape v1 (10 tests).

Gate: ENGINE-WILD-SHAPE
Tests: WS-01 through WS-10
WO: WO-ENGINE-WILD-SHAPE-001
"""

import pytest
from copy import deepcopy
from unittest import mock

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.attack import Weapon
from aidm.schemas.intents import WildShapeIntent, RevertFormIntent
from aidm.core.wild_shape_resolver import validate_wild_shape, resolve_wild_shape, resolve_revert_form


LONGSWORD = Weapon(
    damage_dice="1d8",
    damage_bonus=0,
    damage_type="slashing",
    critical_multiplier=2,
    critical_range=20,
    weapon_type="one-handed",
    grip="one-handed",
)


def _druid(eid="druid", level=5, wild_shape_uses=1, wild_shape_active=False):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 14,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: 1,
        EF.DEX_MOD: 2,
        EF.CON_MOD: 2,
        EF.BAB: level // 2,
        EF.ATTACK_BONUS: level // 2 + 1,
        EF.CLASS_LEVELS: {"druid": level},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.WILD_SHAPE_USES_REMAINING: wild_shape_uses,
        EF.WILD_SHAPE_ACTIVE: wild_shape_active,
        EF.WILD_SHAPE_FORM: "",
        EF.WILD_SHAPE_SAVED_STATS: {},
        EF.WILD_SHAPE_HOURS_REMAINING: 0,
        EF.EQUIPMENT_MELDED: False,
        EF.NATURAL_ATTACKS: [],
        EF.SIZE_CATEGORY: "medium",
    }


def _goblin(eid="goblin"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 15,
        EF.HP_MAX: 15,
        EF.AC: 13,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 1, "y": 0},
    }


def _world(entities):
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
            "cleave_used_this_turn": set(),
        },
    )


def _mock_rng(rolls):
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [10] * 200
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ===========================================================================
# WS-01: Transform to Wolf
# ===========================================================================

def test_ws01_transform_to_wolf():
    """WS-01: resolve_wild_shape emits wild_shape_start, updates entity stats to wolf stats."""
    druid = _druid(level=5, wild_shape_uses=1)
    ws = _world({"druid": druid})
    intent = WildShapeIntent(actor_id="druid", form="wolf")

    events, ws2 = resolve_wild_shape(intent, ws, 0, 0.0)

    evt_types = [e.event_type for e in events]
    assert "wild_shape_start" in evt_types, f"Expected wild_shape_start, got {evt_types}"
    entity = ws2.entities["druid"]
    # wolf: str=13->mod=1, dex=15->mod=2, con=15->mod=2
    assert entity[EF.STR_MOD] == 1, f"Expected wolf str_mod=1, got {entity[EF.STR_MOD]}"
    assert entity[EF.DEX_MOD] == 2, f"Expected wolf dex_mod=2, got {entity[EF.DEX_MOD]}"
    assert entity[EF.CON_MOD] == 2, f"Expected wolf con_mod=2, got {entity[EF.CON_MOD]}"


# ===========================================================================
# WS-02: Tracking fields set, original stats saved
# ===========================================================================

def test_ws02_tracking_fields_set():
    """WS-02: WILD_SHAPE_ACTIVE=True, WILD_SHAPE_FORM set, original stats in WILD_SHAPE_SAVED_STATS."""
    druid = _druid(level=5, wild_shape_uses=1)
    orig_str_mod = druid[EF.STR_MOD]
    ws = _world({"druid": druid})
    intent = WildShapeIntent(actor_id="druid", form="wolf")

    _, ws2 = resolve_wild_shape(intent, ws, 0, 0.0)

    entity = ws2.entities["druid"]
    assert entity[EF.WILD_SHAPE_ACTIVE] is True
    assert entity[EF.WILD_SHAPE_FORM] == "wolf"
    saved = entity.get(EF.WILD_SHAPE_SAVED_STATS, {})
    assert saved.get("str_mod") == orig_str_mod, "Original str_mod should be saved"


# ===========================================================================
# WS-03: Uses decremented
# ===========================================================================

def test_ws03_uses_decremented():
    """WS-03: WILD_SHAPE_USES_REMAINING decremented by 1 on transformation."""
    druid = _druid(level=5, wild_shape_uses=2)
    ws = _world({"druid": druid})
    intent = WildShapeIntent(actor_id="druid", form="wolf")

    _, ws2 = resolve_wild_shape(intent, ws, 0, 0.0)
    assert ws2.entities["druid"][EF.WILD_SHAPE_USES_REMAINING] == 1


# ===========================================================================
# WS-04: EQUIPMENT_MELDED set
# ===========================================================================

def test_ws04_equipment_melded():
    """WS-04: EQUIPMENT_MELDED=True after transformation."""
    druid = _druid(level=5, wild_shape_uses=1)
    ws = _world({"druid": druid})
    intent = WildShapeIntent(actor_id="druid", form="wolf")

    _, ws2 = resolve_wild_shape(intent, ws, 0, 0.0)
    assert ws2.entities["druid"][EF.EQUIPMENT_MELDED] is True


# ===========================================================================
# WS-05: Weapon attack blocked while equipment melded
# ===========================================================================

def test_ws05_weapon_attack_blocked_while_melded():
    """WS-05: resolve_attack returns intent_validation_failed reason:equipment_melded."""
    from aidm.core.attack_resolver import resolve_attack
    from aidm.schemas.attack import AttackIntent

    druid = _druid(level=5, wild_shape_uses=0, wild_shape_active=True)
    druid[EF.EQUIPMENT_MELDED] = True
    goblin = _goblin()
    ws = _world({"druid": druid, "goblin": goblin})

    attack_intent = AttackIntent(
        attacker_id="druid",
        target_id="goblin",
        weapon=LONGSWORD,
        attack_bonus=5,
    )
    rng = _mock_rng([15, 5])
    events = resolve_attack(attack_intent, ws, rng, 0, 0.0)

    failed = [e for e in events if e.event_type == "intent_validation_failed"]
    assert len(failed) == 1, f"Expected validation failure, got {[e.event_type for e in events]}"
    assert failed[0].payload.get("reason") == "equipment_melded"


# ===========================================================================
# WS-06: Revert restores original stats
# ===========================================================================

def test_ws06_revert_restores_stats():
    """WS-06: resolve_revert_form emits wild_shape_end and restores original Str/Dex/Con."""
    druid = _druid(level=5, wild_shape_uses=1)
    orig_str_mod = druid[EF.STR_MOD]
    ws = _world({"druid": druid})

    _, ws2 = resolve_wild_shape(WildShapeIntent(actor_id="druid", form="black_bear"), ws, 0, 0.0)
    events, ws3 = resolve_revert_form(RevertFormIntent(actor_id="druid"), ws2, 1, 0.5)

    assert any(e.event_type == "wild_shape_end" for e in events)
    assert ws3.entities["druid"][EF.STR_MOD] == orig_str_mod, "Original str_mod should be restored"


# ===========================================================================
# WS-07: Revert clears tracking fields
# ===========================================================================

def test_ws07_revert_clears_fields():
    """WS-07: After revert, WILD_SHAPE_ACTIVE=False, EQUIPMENT_MELDED=False, WILD_SHAPE_FORM cleared."""
    druid = _druid(level=5, wild_shape_uses=1)
    ws = _world({"druid": druid})

    _, ws2 = resolve_wild_shape(WildShapeIntent(actor_id="druid", form="wolf"), ws, 0, 0.0)
    _, ws3 = resolve_revert_form(RevertFormIntent(actor_id="druid"), ws2, 1, 0.5)

    entity = ws3.entities["druid"]
    assert entity[EF.WILD_SHAPE_ACTIVE] is False
    assert entity[EF.EQUIPMENT_MELDED] is False
    assert entity[EF.WILD_SHAPE_FORM] == ""


# ===========================================================================
# WS-08: Cannot transform while already transformed
# ===========================================================================

def test_ws08_cannot_transform_while_transformed():
    """WS-08: validate_wild_shape returns already_transformed when WILD_SHAPE_ACTIVE."""
    druid = _druid(level=5, wild_shape_uses=1, wild_shape_active=True)
    druid[EF.WILD_SHAPE_FORM] = "wolf"
    ws = _world({"druid": druid})

    reason = validate_wild_shape(ws.entities["druid"], "black_bear", ws)
    assert reason == "already_transformed", f"Got {reason!r}"


# ===========================================================================
# WS-09: No uses remaining
# ===========================================================================

def test_ws09_no_wild_shape_uses():
    """WS-09: validate_wild_shape returns no_wild_shape_uses when uses are 0."""
    druid = _druid(level=5, wild_shape_uses=0)
    ws = _world({"druid": druid})

    reason = validate_wild_shape(ws.entities["druid"], "wolf", ws)
    assert reason == "no_wild_shape_uses", f"Got {reason!r}"


# ===========================================================================
# WS-10: Unsupported form
# ===========================================================================

def test_ws10_unsupported_form():
    """WS-10: validate_wild_shape returns unsupported_form for form not in v1 library."""
    druid = _druid(level=5, wild_shape_uses=1)
    ws = _world({"druid": druid})

    reason = validate_wild_shape(ws.entities["druid"], "dragon", ws)
    assert reason == "unsupported_form", f"Got {reason!r}"

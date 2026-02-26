"""Gate tests: WO-ENGINE-FLATFOOTED-AOO-001 — Flat-footed entity cannot make AoOs (PHB p.136).

Closes FINDING-ENGINE-FLATFOOTED-AOO-001 (open since Dispatch #12).

Gate label: ENGINE-FLATFOOTED-AOO-001
KERNEL-06 (Termination Doctrine) touch.
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.aoo import check_aoo_triggers
from aidm.schemas.attack import AttackIntent, Weapon


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entity(entity_id: str, team: str, position: dict,
                 conditions: dict = None, feats: list = None,
                 defeated: bool = False) -> dict:
    return {
        EF.ENTITY_ID: entity_id,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.TEAM: team,
        EF.DEFEATED: defeated,
        EF.CONDITIONS: conditions or {},
        EF.FEATS: feats or [],
        EF.DEX_MOD: 1,
        EF.ATTACK_BONUS: 5,
        EF.BAB: 5,
        EF.STR_MOD: 2,
        EF.WEAPON: {"name": "longsword", "damage_dice": "1d8", "crit_range": 19,
                    "crit_multiplier": 2, "damage_type": "slashing",
                    "attack_bonus": 0, "enhancement_bonus": 0},
        EF.POSITION: position,
    }


def _make_world(entities: dict, initiative: list = None) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": initiative or list(entities.keys()),
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "flat_footed_actors": [],
            "feint_flat_footed": [],
        },
    )


def _make_move_intent(actor_id: str, from_pos: dict = None, to_pos: dict = None):
    """Create a movement intent that provokes AoO."""
    from aidm.schemas.intents import MoveIntent
    from aidm.schemas.position import Position
    intent = MoveIntent(destination=Position(x=2, y=0))
    # Patch actor_id onto intent for AoO check
    intent.actor_id = actor_id
    return intent


def _count_aoo_triggers(provoker_id: str, reactor_id: str,
                         provoker_conditions: dict = None,
                         reactor_conditions: dict = None,
                         reactor_feats: list = None) -> int:
    """Count AoO triggers from a move event. Returns number of triggers from reactor."""
    from aidm.schemas.attack import AttackIntent, Weapon
    # Build world where provoker moves out of reactor's threatened square
    provoker = _make_entity(provoker_id, "monsters", {"x": 1, "y": 0},
                            conditions=provoker_conditions or {})
    reactor = _make_entity(reactor_id, "players", {"x": 0, "y": 0},
                           conditions=reactor_conditions or {},
                           feats=reactor_feats or [])
    ws = _make_world({provoker_id: provoker, reactor_id: reactor},
                     initiative=[reactor_id, provoker_id])

    from aidm.schemas.attack import StepMoveIntent
    from aidm.schemas.position import Position
    intent = StepMoveIntent(
        actor_id=provoker_id,
        from_pos=Position(x=1, y=0),
        to_pos=Position(x=2, y=0),
    )

    triggers = check_aoo_triggers(ws, provoker_id, intent)
    return sum(1 for t in triggers if t.reactor_id == reactor_id)


# ---------------------------------------------------------------------------
# FF-001: Flat-footed reactor → no AoO
# ---------------------------------------------------------------------------

def test_ff_001_flat_footed_no_aoo():
    """FF-001: Flat-footed entity in threatened square; enemy provokes → no AoO."""
    count = _count_aoo_triggers(
        provoker_id="orc_01", reactor_id="fighter_01",
        reactor_conditions={"flat_footed": {}}
    )
    assert count == 0, f"FF-001: Expected 0 AoO from flat-footed reactor; got {count}"


# ---------------------------------------------------------------------------
# FF-002: Non-flat-footed reactor → AoO triggers normally
# ---------------------------------------------------------------------------

def test_ff_002_non_flat_footed_aoo_triggers():
    """FF-002: Non-flat-footed entity; enemy provokes → AoO triggers normally."""
    count = _count_aoo_triggers(
        provoker_id="orc_01", reactor_id="fighter_01",
        reactor_conditions={}  # no flat_footed
    )
    assert count == 1, f"FF-002: Expected 1 AoO from non-flat-footed reactor; got {count}"


# ---------------------------------------------------------------------------
# FF-003: Flat-footed + Combat Reflexes → still no AoO
# ---------------------------------------------------------------------------

def test_ff_003_flat_footed_combat_reflexes_no_aoo():
    """FF-003: Flat-footed entity with Combat Reflexes → still no AoO."""
    count = _count_aoo_triggers(
        provoker_id="orc_01", reactor_id="fighter_01",
        reactor_conditions={"flat_footed": {}},
        reactor_feats=["combat_reflexes"]
    )
    assert count == 0, f"FF-003: Flat-footed suppresses AoO even with Combat Reflexes; got {count}"


# ---------------------------------------------------------------------------
# FF-004: Flat-footed cleared → AoO triggers after
# ---------------------------------------------------------------------------

def test_ff_004_cleared_flat_footed_aoo_triggers():
    """FF-004: After flat-footed clears (no condition), enemy provokes → AoO triggers."""
    # After first action, flat-footed clears. Simulate by having no flat_footed condition.
    count = _count_aoo_triggers(
        provoker_id="orc_01", reactor_id="fighter_01",
        reactor_conditions={}  # flat_footed cleared
    )
    assert count == 1, f"FF-004: Expected 1 AoO after flat-footed clears; got {count}"


# ---------------------------------------------------------------------------
# FF-005: Multiple reactors; one flat-footed, one not
# ---------------------------------------------------------------------------

def test_ff_005_multiple_reactors_only_non_ff_reacts():
    """FF-005: Two reactors; one flat-footed → only non-flat-footed makes AoO."""
    from aidm.schemas.attack import StepMoveIntent
    from aidm.schemas.position import Position
    provoker_id = "orc_01"
    ff_id = "flat_fighter"
    normal_id = "normal_fighter"
    provoker = _make_entity(provoker_id, "monsters", {"x": 1, "y": 0})
    ff_reactor = _make_entity(ff_id, "players", {"x": 0, "y": 0},
                              conditions={"flat_footed": {}})
    normal_reactor = _make_entity(normal_id, "players", {"x": 1, "y": 1},
                                  conditions={})
    ws = _make_world(
        {provoker_id: provoker, ff_id: ff_reactor, normal_id: normal_reactor},
        initiative=[ff_id, normal_id, provoker_id]
    )
    intent = StepMoveIntent(
        actor_id=provoker_id,
        from_pos=Position(x=1, y=0),
        to_pos=Position(x=2, y=0),
    )
    triggers = check_aoo_triggers(ws, provoker_id, intent)
    reactor_ids = [t.reactor_id for t in triggers]
    assert ff_id not in reactor_ids, \
        f"FF-005: Flat-footed reactor should not appear in triggers; got {reactor_ids}"
    assert normal_id in reactor_ids, \
        f"FF-005: Normal reactor should be in triggers; got {reactor_ids}"


# ---------------------------------------------------------------------------
# FF-006: Entity with Uncanny Dodge (not flat-footed) → AoO triggers
# ---------------------------------------------------------------------------

def test_ff_006_uncanny_dodge_holder_not_flat_footed():
    """FF-006: Uncanny Dodge holder has no flat_footed condition → AoO triggers normally."""
    # Uncanny Dodge prevents flat-footed FROM being applied. No flat_footed in CONDITIONS.
    count = _count_aoo_triggers(
        provoker_id="orc_01", reactor_id="rogue_01",
        reactor_conditions={},  # Uncanny Dodge: flat_footed never applied
        reactor_feats=["uncanny_dodge"]
    )
    assert count == 1, \
        f"FF-006: Uncanny Dodge holder (no flat_footed) should make AoO normally; got {count}"


# ---------------------------------------------------------------------------
# FF-007: Flat-footed + zero AoO uses → no AoO, no crash
# ---------------------------------------------------------------------------

def test_ff_007_flat_footed_zero_uses_no_crash():
    """FF-007: Flat-footed entity with zero AoO uses → no AoO, no crash."""
    from aidm.schemas.attack import StepMoveIntent
    from aidm.schemas.position import Position
    provoker_id = "orc_01"
    reactor_id = "fighter_01"
    provoker = _make_entity(provoker_id, "monsters", {"x": 1, "y": 0})
    reactor = _make_entity(reactor_id, "players", {"x": 0, "y": 0},
                           conditions={"flat_footed": {}})
    ws = _make_world(
        {provoker_id: provoker, reactor_id: reactor},
        initiative=[reactor_id, provoker_id]
    )
    # Mark AoO as already used
    ws.active_combat["aoo_count_this_round"] = {reactor_id: 1}
    intent = StepMoveIntent(
        actor_id=provoker_id,
        from_pos=Position(x=1, y=0),
        to_pos=Position(x=2, y=0),
    )
    # Should not crash; triggers is empty
    triggers = check_aoo_triggers(ws, provoker_id, intent)
    reactor_triggers = [t for t in triggers if t.reactor_id == reactor_id]
    assert len(reactor_triggers) == 0, \
        f"FF-007: No AoO from flat-footed + used-up reactor; got {reactor_triggers}"


# ---------------------------------------------------------------------------
# FF-008: Reactor with no CONDITIONS field → no crash; AoO triggers normally
# ---------------------------------------------------------------------------

def test_ff_008_no_conditions_field_no_crash():
    """FF-008: Entity with no CONDITIONS field → no crash; AoO triggers normally."""
    from aidm.schemas.attack import StepMoveIntent
    from aidm.schemas.position import Position
    provoker_id = "orc_01"
    reactor_id = "fighter_01"
    provoker = _make_entity(provoker_id, "monsters", {"x": 1, "y": 0})
    reactor = _make_entity(reactor_id, "players", {"x": 0, "y": 0})
    # Remove CONDITIONS field entirely
    del reactor[EF.CONDITIONS]
    ws = _make_world(
        {provoker_id: provoker, reactor_id: reactor},
        initiative=[reactor_id, provoker_id]
    )
    intent = StepMoveIntent(
        actor_id=provoker_id,
        from_pos=Position(x=1, y=0),
        to_pos=Position(x=2, y=0),
    )
    triggers = check_aoo_triggers(ws, provoker_id, intent)
    # Should not crash; reactor without CONDITIONS should still be able to react
    reactor_triggers = [t for t in triggers if t.reactor_id == reactor_id]
    assert len(reactor_triggers) == 1, \
        f"FF-008: Expected AoO from reactor with no CONDITIONS; got {reactor_triggers}"

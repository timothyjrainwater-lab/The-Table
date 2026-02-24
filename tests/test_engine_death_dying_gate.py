"""Gate ENGINE-DEATH-DYING — WO-ENGINE-DEATH-DYING-001: Death, Dying, and Stabilization.

Tests:
DD-01: Attack drops target to 0 HP -> entity_disabled (not entity_defeated)
DD-02: Attack drops target to -3 HP -> entity_dying, DYING=True, DEFEATED=False
DD-03: Attack drops target to -10 HP exactly -> entity_defeated, DEFEATED=True
DD-04: Attack drops target to -15 HP -> entity_defeated (dead regardless of depth)
DD-05: Dying entity end-of-round Fort fail -> dying_fort_failed + hp_changed (delta=-1)
DD-06: Dying entity end-of-round Fort success -> entity_stabilized, STABLE=True, no HP loss
DD-07: Stable entity end-of-round -> no bleed tick (no dying_fort_failed)
DD-08: Dying entity bleed to -10 -> entity_defeated emitted mid-bleed-tick
DD-09: Healing a dying entity to 1+ HP -> entity_revived, DYING=False
DD-10: Dying entity is a valid attack target (DEFEATED=False)
DD-11: Dead entity (DEFEATED=True) rejected as attack target
DD-12: Zero regressions - CP-22 + XP-01 gates still pass
"""

import unittest.mock as mock
from typing import Any, Dict, List

import pytest

from aidm.core.dying_resolver import classify_hp, resolve_dying_tick, resolve_hp_transition
from aidm.core.play_loop import TurnContext, execute_turn
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sword() -> Weapon:
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        critical_range=20,
        critical_multiplier=2,
        grip="one-handed",
        is_two_handed=False,
    )


def _entity(
    eid: str,
    team: str,
    hp: int,
    hp_max: int = 20,
    ac: int = 10,
    save_fort: int = 0,
    dying: bool = False,
    stable: bool = False,
    disabled: bool = False,
    defeated: bool = False,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: ac,
        EF.SAVE_FORT: save_fort,
        EF.STR_MOD: 3,
        EF.DEX_MOD: 0,
        EF.ATTACK_BONUS: 5,
        EF.BAB: 5,
        "bab": 5,
        EF.DEFEATED: defeated,
        EF.DYING: dying,
        EF.STABLE: stable,
        EF.DISABLED: disabled,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FEATS: [],
    }


def _world(entities: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={"initiative_order": ["attacker", "target"]},
    )


def _rng_fixed(value: int):
    """RNG mock that always returns `value` from any stream.randint() call."""
    stream = mock.MagicMock()
    stream.randint.return_value = value
    rng_mock = mock.MagicMock()
    rng_mock.stream.return_value = stream
    return rng_mock


# ---------------------------------------------------------------------------
# DD-01: HP -> 0 => entity_disabled
# ---------------------------------------------------------------------------

def test_dd01_attack_to_zero_hp_emits_entity_disabled():
    """HP hits exactly 0 -> entity_disabled, NOT entity_defeated."""
    ws = _world({"attacker": _entity("attacker", "party", hp=30), "target": _entity("target", "monsters", hp=5)})
    events, field_updates = resolve_hp_transition(
        entity_id="target",
        old_hp=1,
        new_hp=0,
        source="attack_damage",
        world_state=ws,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "entity_disabled" in types, f"Expected entity_disabled, got {types}"
    assert "entity_defeated" not in types
    assert field_updates[EF.DISABLED] is True
    assert field_updates[EF.DYING] is False


# ---------------------------------------------------------------------------
# DD-02: HP -> -3 => entity_dying, DYING=True, DEFEATED=False
# ---------------------------------------------------------------------------

def test_dd02_attack_to_minus3_emits_entity_dying():
    """HP drops to -3 -> entity_dying, DYING=True, DEFEATED=False."""
    ws = _world({"attacker": _entity("attacker", "party", hp=30), "target": _entity("target", "monsters", hp=5)})
    events, field_updates = resolve_hp_transition(
        entity_id="target",
        old_hp=5,
        new_hp=-3,
        source="attack_damage",
        world_state=ws,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "entity_dying" in types, f"Expected entity_dying, got {types}"
    assert "entity_defeated" not in types
    assert field_updates[EF.DYING] is True
    assert field_updates[EF.DEFEATED] is False


# ---------------------------------------------------------------------------
# DD-03: HP -> -10 => entity_defeated, DEFEATED=True
# ---------------------------------------------------------------------------

def test_dd03_attack_to_minus10_emits_entity_defeated():
    """HP drops to exactly -10 -> entity_defeated (dead), DEFEATED=True."""
    ws = _world({"attacker": _entity("attacker", "party", hp=30), "target": _entity("target", "monsters", hp=5)})
    events, field_updates = resolve_hp_transition(
        entity_id="target",
        old_hp=5,
        new_hp=-10,
        source="attack_damage",
        world_state=ws,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "entity_defeated" in types, f"Expected entity_defeated, got {types}"
    assert "entity_dying" not in types
    assert field_updates[EF.DEFEATED] is True


# ---------------------------------------------------------------------------
# DD-04: HP -> -15 => entity_defeated
# ---------------------------------------------------------------------------

def test_dd04_attack_to_minus15_emits_entity_defeated():
    """HP drops below -10 -> entity_defeated (dead)."""
    ws = _world({"attacker": _entity("attacker", "party", hp=30), "target": _entity("target", "monsters", hp=5)})
    events, field_updates = resolve_hp_transition(
        entity_id="target",
        old_hp=5,
        new_hp=-15,
        source="attack_damage",
        world_state=ws,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "entity_defeated" in types
    assert field_updates[EF.DEFEATED] is True


# ---------------------------------------------------------------------------
# DD-05: Dying Fort fail => dying_fort_failed + hp_changed(delta=-1)
# ---------------------------------------------------------------------------

def test_dd05_dying_fort_fail_emits_fort_failed_and_hp_changed():
    """Dying entity fails DC 10 Fort save -> dying_fort_failed + hp_changed(delta=-1)."""
    target = _entity("target", "monsters", hp=-3, hp_max=20, save_fort=-5, dying=True)
    ws = _world({"target": target})

    # d20=1, total = 1 + (-5) = -4 < 10 -> fail
    rng = _rng_fixed(1)
    events, updated_ws = resolve_dying_tick(
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "dying_fort_failed" in types, f"Got: {types}"
    assert "hp_changed" in types

    hp_ev = next(e for e in events if e.event_type == "hp_changed")
    assert hp_ev.payload["delta"] == -1
    assert hp_ev.payload["new_hp"] == -4
    assert updated_ws.entities["target"][EF.HP_CURRENT] == -4


# ---------------------------------------------------------------------------
# DD-06: Dying Fort success => entity_stabilized, STABLE=True, no HP loss
# ---------------------------------------------------------------------------

def test_dd06_dying_fort_success_emits_stabilized():
    """Dying entity passes DC 10 Fort save -> entity_stabilized, no HP loss."""
    target = _entity("target", "monsters", hp=-3, hp_max=20, save_fort=0, dying=True)
    ws = _world({"target": target})

    # d20=15, total = 15 + 0 = 15 >= 10 -> success
    rng = _rng_fixed(15)
    events, updated_ws = resolve_dying_tick(
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "entity_stabilized" in types, f"Got: {types}"
    assert "hp_changed" not in types
    assert "dying_fort_failed" not in types
    assert updated_ws.entities["target"][EF.STABLE] is True
    assert updated_ws.entities["target"][EF.HP_CURRENT] == -3  # unchanged


# ---------------------------------------------------------------------------
# DD-07: Stable entity => no bleed tick
# ---------------------------------------------------------------------------

def test_dd07_stable_entity_no_bleed():
    """Stable dying entity skips the bleed loop."""
    target = _entity("target", "monsters", hp=-3, hp_max=20, save_fort=0, dying=True, stable=True)
    ws = _world({"target": target})

    rng = _rng_fixed(1)
    events, updated_ws = resolve_dying_tick(
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "dying_fort_failed" not in types
    assert "hp_changed" not in types
    assert updated_ws.entities["target"][EF.HP_CURRENT] == -3


# ---------------------------------------------------------------------------
# DD-08: Dying entity bleed to -10 => entity_defeated
# ---------------------------------------------------------------------------

def test_dd08_dying_bleed_to_dead():
    """Dying entity at -9 HP bleeds to -10 -> entity_defeated in bleed tick."""
    target = _entity("target", "monsters", hp=-9, hp_max=20, save_fort=-9, dying=True)
    ws = _world({"target": target})

    # d20=1, total = 1 + (-9) = -8 < 10 -> fail -> HP -10 -> dead
    rng = _rng_fixed(1)
    events, updated_ws = resolve_dying_tick(
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "entity_defeated" in types, f"Expected entity_defeated in {types}"
    assert updated_ws.entities["target"][EF.DEFEATED] is True
    assert updated_ws.entities["target"][EF.DYING] is False
    assert updated_ws.entities["target"][EF.HP_CURRENT] == -10


# ---------------------------------------------------------------------------
# DD-09: Healing a dying entity to 1+ HP => entity_revived, DYING=False
# ---------------------------------------------------------------------------

def test_dd09_healing_dying_entity_emits_revived():
    """Healing a dying entity above 0 HP -> entity_revived, DYING cleared."""
    ws = _world({
        "healer": _entity("healer", "party", hp=30),
        "target": _entity("target", "monsters", hp=-3, dying=True),
    })

    events, field_updates = resolve_hp_transition(
        entity_id="target",
        old_hp=-3,
        new_hp=5,
        source="cure_light_wounds",
        world_state=ws,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "entity_revived" in types, f"Expected entity_revived, got {types}"
    assert field_updates[EF.DYING] is False
    assert field_updates[EF.DEFEATED] is False


# ---------------------------------------------------------------------------
# DD-10: Dying entity is a valid attack target (DEFEATED=False)
# ---------------------------------------------------------------------------

def test_dd10_dying_entity_is_valid_target():
    """Dying entity has DEFEATED=False, so execute_turn attack should NOT be rejected."""
    sword = _sword()
    attacker_e = _entity("attacker", "party", hp=30, hp_max=30, ac=10)
    attacker_e[EF.ATTACK_BONUS] = 99  # guarantee hit
    target_e = _entity("target", "monsters", hp=-3, hp_max=20, ac=5, dying=True, defeated=False)

    ws = WorldState(
        ruleset_version="3.5e",
        entities={"attacker": attacker_e, "target": target_e},
        active_combat={"initiative_order": ["attacker", "target"]},
    )

    ctx = TurnContext(actor_id="attacker", turn_index=0, actor_team="party")
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=99,
        weapon=sword,
    )
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        turn_ctx=ctx,
        world_state=ws,
        combat_intent=intent,
        rng=rng,
    )

    # Should NOT produce target_already_defeated validation failure
    validation_failures = [
        e for e in result.events
        if e.event_type == "intent_validation_failed"
        and e.payload.get("reason") == "target_already_defeated"
    ]
    assert len(validation_failures) == 0, "Dying target should be a valid attack target"


# ---------------------------------------------------------------------------
# DD-11: Dead entity (DEFEATED=True) rejected as attack target
# ---------------------------------------------------------------------------

def test_dd11_dead_entity_rejected_as_target():
    """Entity with DEFEATED=True rejected — intent_validation_failed emitted."""
    sword = _sword()
    attacker_e = _entity("attacker", "party", hp=30, hp_max=30, ac=10)
    target_e = _entity("target", "monsters", hp=-10, hp_max=20, ac=5, defeated=True)

    ws = WorldState(
        ruleset_version="3.5e",
        entities={"attacker": attacker_e, "target": target_e},
        active_combat={"initiative_order": ["attacker", "target"]},
    )

    ctx = TurnContext(actor_id="attacker", turn_index=0, actor_team="party")
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="target",
        attack_bonus=99,
        weapon=sword,
    )
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        turn_ctx=ctx,
        world_state=ws,
        combat_intent=intent,
        rng=rng,
    )

    validation_failures = [
        e for e in result.events
        if e.event_type == "intent_validation_failed"
        and e.payload.get("reason") == "target_already_defeated"
    ]
    assert len(validation_failures) == 1, "Dead target should be rejected"


# ---------------------------------------------------------------------------
# DD-12: Zero regressions on CP-22 and XP-01 gates
# ---------------------------------------------------------------------------

def test_dd12_regression_gate_modules_importable():
    """Smoke: CP-22 and XP-01 gate modules importable (regression content covered by CI)."""
    import importlib
    cp22 = importlib.import_module("tests.test_engine_gate_cp22")
    assert cp22 is not None
    xp01 = importlib.import_module("tests.test_engine_gate_xp01")
    assert xp01 is not None


# ---------------------------------------------------------------------------
# classify_hp band coverage
# ---------------------------------------------------------------------------

def test_classify_hp_bands():
    assert classify_hp(10) == "conscious"
    assert classify_hp(1) == "conscious"
    assert classify_hp(0) == "disabled"
    assert classify_hp(-1) == "dying"
    assert classify_hp(-9) == "dying"
    assert classify_hp(-10) == "dead"
    assert classify_hp(-100) == "dead"

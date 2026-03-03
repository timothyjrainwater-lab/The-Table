"""Gate tests — WO-ENGINE-NAUSEATED-MOVE-ONLY-001
NMO-001..008: allows_move_only=True; nauseated gate in play_loop blocks non-move actions
"""
from __future__ import annotations
from typing import Any, Dict
from unittest.mock import MagicMock
from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import ConditionModifiers, create_nauseated_condition
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.core.play_loop import TurnContext, execute_turn

_SWORD = Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing")
_SWORD_DICT = {"name": "longsword", "enhancement_bonus": 0, "damage_dice": "1d8",
               "damage_bonus": 0, "damage_type": "slashing", "tags": [], "material": "steel"}


def _entity(eid: str, conditions: dict = None) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid, EF.TEAM: "party",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 12,
        EF.ATTACK_BONUS: 4, EF.BAB: 4, EF.STR_MOD: 2, EF.DEX_MOD: 0,
        EF.DEFEATED: False, EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: conditions or {},
        EF.FEATS: [], EF.POSITION: {"x": 0, "y": 0}, EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.NEGATIVE_LEVELS: 0, EF.WEAPON_BROKEN: False, EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {}, EF.WEAPON: _SWORD_DICT,
    }


def _tgt(eid: str) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid, EF.TEAM: "monsters",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 14,
        EF.ATTACK_BONUS: 2, EF.BAB: 2, EF.STR_MOD: 0, EF.DEX_MOD: 0,
        EF.DEFEATED: False, EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.POSITION: {"x": 1, "y": 0}, EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False, EF.INSPIRE_COURAGE_BONUS: 0,
        EF.NEGATIVE_LEVELS: 0, EF.WEAPON_BROKEN: False, EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {},
    }


def _ws(entities: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e", entities=entities,
        active_combat={
            "turn_counter": 0, "round_index": 1,
            "initiative_order": list(entities.keys()),
            "flat_footed_actors": [], "aoo_used_this_round": [],
            "aoo_count_this_round": {}, "deflect_arrows_used": [],
            "cleave_used_this_turn": set(),
        },
    )


def _ctx() -> TurnContext:
    return TurnContext(turn_index=0, actor_id="actor_1", actor_team="party")


def _rng() -> MagicMock:
    rng = MagicMock()
    rng.stream.return_value.randint.return_value = 15
    return rng


def test_NMO001_nauseated_attack_denied():
    """NMO-001: Nauseated entity + AttackIntent → action_denied(nauseated_move_only)."""
    ci = create_nauseated_condition("test", 0)
    ws = _ws({"actor_1": _entity("actor_1", {"nauseated": ci.to_dict()}), "target_1": _tgt("target_1")})
    result = execute_turn(world_state=ws, turn_ctx=_ctx(),
                          combat_intent=AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD),
                          rng=_rng())
    assert result.status == "action_denied"
    denied = next((e for e in result.events if e.event_type == "action_denied"), None)
    assert denied is not None and denied.payload.get("reason") == "nauseated_move_only"


def test_NMO002_nauseated_cast_denied():
    """NMO-002: Nauseated entity + SpellCastIntent → action_denied(nauseated_move_only)."""
    from aidm.core.spell_resolver import SpellCastIntent
    ci = create_nauseated_condition("test", 0)
    actor = _entity("actor_1", {"nauseated": ci.to_dict()})
    actor.update({EF.CLASS_LEVELS: {"wizard": 5}, EF.SPELL_SLOTS: {"1": 4},
                  EF.CASTER_LEVEL: 5})
    ws = _ws({"actor_1": actor})
    result = execute_turn(world_state=ws, turn_ctx=_ctx(),
                          combat_intent=SpellCastIntent(caster_id="actor_1", spell_id="magic_missile", target_entity_id="actor_1"),
                          rng=_rng())
    assert result.status == "action_denied"
    denied = next((e for e in result.events if e.event_type == "action_denied"), None)
    assert denied is not None and denied.payload.get("reason") == "nauseated_move_only"


def test_NMO003_nauseated_move_proceeds():
    """NMO-003: Nauseated entity + FullMoveIntent → NOT action_denied by nauseated gate."""
    from aidm.schemas.attack import FullMoveIntent
    from aidm.schemas.position import Position
    ci = create_nauseated_condition("test", 0)
    actor = _entity("actor_1", {"nauseated": ci.to_dict()})
    actor[EF.BASE_SPEED] = 30
    ws = _ws({"actor_1": actor})
    intent = FullMoveIntent(actor_id="actor_1", from_pos=Position(0, 0), path=[Position(1, 0), Position(2, 0), Position(3, 0), Position(4, 0), Position(5, 0)])
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng())
    assert not any(
        e.event_type == "action_denied" and e.payload.get("reason") == "nauseated_move_only"
        for e in result.events
    ), f"Move intent wrongly denied by nauseated gate (status={result.status})"


def test_NMO004_non_nauseated_not_blocked():
    """NMO-004: No nauseated condition → nauseated gate does not fire."""
    ws = _ws({"actor_1": _entity("actor_1"), "target_1": _tgt("target_1")})
    result = execute_turn(world_state=ws, turn_ctx=_ctx(),
                          combat_intent=AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD),
                          rng=_rng())
    assert not any(
        e.event_type == "action_denied" and e.payload.get("reason") == "nauseated_move_only"
        for e in result.events
    )


def test_NMO005_nauseated_full_attack_denied():
    """NMO-005: Nauseated entity + FullAttackIntent → action_denied(nauseated_move_only)."""
    from aidm.core.full_attack_resolver import FullAttackIntent
    ci = create_nauseated_condition("test", 0)
    ws = _ws({"actor_1": _entity("actor_1", {"nauseated": ci.to_dict()}), "target_1": _tgt("target_1")})
    intent = FullAttackIntent(attacker_id="actor_1", target_id="target_1", weapon=_SWORD, base_attack_bonus=4)
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng())
    assert result.status == "action_denied"
    denied = next((e for e in result.events if e.event_type == "action_denied"), None)
    assert denied is not None and denied.payload.get("reason") == "nauseated_move_only"


def test_NMO006_nauseated_modifiers():
    """NMO-006: create_nauseated_condition() sets allows_move_only=True, actions_prohibited=False."""
    ci = create_nauseated_condition("test", 0)
    assert ci.modifiers.allows_move_only is True
    assert ci.modifiers.actions_prohibited is False


def test_NMO007_default_modifiers_no_allows_move_only():
    """NMO-007: Default ConditionModifiers has allows_move_only=False."""
    assert ConditionModifiers().allows_move_only is False


def test_NMO008_stunned_overrides_nauseated():
    """NMO-008: Stunned (actions_prohibited) takes priority over nauseated — actions_prohibited reason fires."""
    from aidm.schemas.conditions import create_stunned_condition
    ci_nausea = create_nauseated_condition("test", 0)
    ci_stun = create_stunned_condition("test", 0)
    ws = _ws({"actor_1": _entity("actor_1", {
        "nauseated": ci_nausea.to_dict(), "stunned": ci_stun.to_dict(),
    }), "target_1": _tgt("target_1")})
    result = execute_turn(world_state=ws, turn_ctx=_ctx(),
                          combat_intent=AttackIntent(attacker_id="actor_1", target_id="target_1", attack_bonus=4, weapon=_SWORD),
                          rng=_rng())
    assert result.status == "action_denied"
    denied = next((e for e in result.events if e.event_type == "action_denied"), None)
    assert denied is not None and denied.payload.get("reason") == "actions_prohibited"

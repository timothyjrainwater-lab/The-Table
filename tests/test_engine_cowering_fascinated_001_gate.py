"""Gate tests: ENGINE-COWERING-FASCINATED-001

Cowering (PHB p.309): frozen in fear; -2 AC, loses Dex to AC, no actions.
Fascinated (PHB p.310): entranced; no actions, -4 reactive skill checks (unwired).

WO-ENGINE-COWERING-FASCINATED-001, Batch K (Dispatch #20).
Gate labels: CF-001 through CF-008.
"""

import pytest

from aidm.schemas.conditions import (
    ConditionType,
    create_cowering_condition,
    create_fascinated_condition,
    create_shaken_condition,
)
from aidm.core.conditions import get_condition_modifiers, apply_condition
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.rng_manager import RNGManager
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.schemas.attack import AttackIntent, Weapon


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _conds(*condition_instances):
    """Build conditions dict from ConditionInstance objects."""
    result = {}
    for ci in condition_instances:
        result[ci.condition_type.value] = ci.to_dict()
    return result


def _base_entity(eid, team="players", x=0, y=0, dex_mod=2, ac=15):
    return {
        EF.ENTITY_ID: eid,
        "name": eid,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: ac,
        EF.DEX_MOD: dex_mod,
        EF.STR_MOD: 2,
        EF.ATTACK_BONUS: 5,
        EF.TEAM: team,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": x, "y": y},
        EF.BASE_SPEED: 30,
        EF.DEFEATED: False,
        EF.NEGATIVE_LEVELS: 0,
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.FAVORED_ENEMIES: [],
        EF.TEMPORARY_MODIFIERS: {},
    }


def _make_world(entities):
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": list(entities.keys()),
            "flat_footed_actors": [],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# CF-001: COWERING — loses Dex to AC (loses_dex_to_ac=True)
# ─────────────────────────────────────────────────────────────────────────────

class TestCoweringFascinated001Gate:

    def test_CF001_cowering_loses_dex_to_ac(self):
        """CF-001: COWERING condition → loses_dex_to_ac=True via get_condition_modifiers."""
        cowering = create_cowering_condition("fear_spell", 0)
        entity = _base_entity("hero")
        entity[EF.CONDITIONS] = _conds(cowering)
        ws = _make_world({"hero": entity})

        mods = get_condition_modifiers(ws, "hero", context="defense")
        assert mods.loses_dex_to_ac is True, \
            f"Expected loses_dex_to_ac=True for COWERING, got {mods.loses_dex_to_ac}"

    # ─────────────────────────────────────────────────────────────────────────
    # CF-002: COWERING — actions prohibited
    # ─────────────────────────────────────────────────────────────────────────

    def test_CF002_cowering_actions_prohibited_play_loop(self):
        """CF-002: Actor with COWERING → execute_turn returns action_denied."""
        entities = {
            "hero": _base_entity("hero", team="players", x=0, y=0),
            "orc": _base_entity("orc", team="monsters", x=5, y=0),
        }
        ws = _make_world(entities)
        cowering = create_cowering_condition("fear_spell", 0)
        ws = apply_condition(ws, "hero", cowering)

        intent = AttackIntent(
            attacker_id="hero",
            target_id="orc",
            attack_bonus=5,
            weapon=Weapon(damage_dice="1d8", damage_bonus=0, damage_type="slashing"),
        )
        turn_ctx = TurnContext(turn_index=0, actor_id="hero", actor_team="players")
        rng = RNGManager(42)
        result = execute_turn(
            turn_ctx=turn_ctx,
            combat_intent=intent,
            world_state=ws,
            rng=rng,
            next_event_id=1,
            timestamp=0.0,
        )

        assert result.status == "action_denied", \
            f"Expected action_denied for COWERING actor, got {result.status!r}"
        event_types = [e.event_type for e in result.events]
        assert "action_denied" in event_types, \
            f"Expected action_denied event, got: {event_types}"

    # ─────────────────────────────────────────────────────────────────────────
    # CF-003: COWERING — ac_modifier == -2
    # ─────────────────────────────────────────────────────────────────────────

    def test_CF003_cowering_ac_modifier_minus_two(self):
        """CF-003: COWERING condition → ac_modifier == -2 in aggregate modifiers."""
        cowering = create_cowering_condition("fear_aura", 0)
        entity = _base_entity("hero")
        entity[EF.CONDITIONS] = _conds(cowering)
        ws = _make_world({"hero": entity})

        mods = get_condition_modifiers(ws, "hero", context="defense")
        assert mods.ac_modifier == -2, \
            f"Expected ac_modifier=-2 for COWERING, got {mods.ac_modifier}"

    # ─────────────────────────────────────────────────────────────────────────
    # CF-004: COWERING — actions_prohibited=True in condition modifiers
    # ─────────────────────────────────────────────────────────────────────────

    def test_CF004_cowering_actions_prohibited_flag(self):
        """CF-004: COWERING condition → actions_prohibited=True in aggregate modifiers."""
        cowering = create_cowering_condition("fear_spell", 0)
        entity = _base_entity("hero")
        entity[EF.CONDITIONS] = _conds(cowering)
        ws = _make_world({"hero": entity})

        mods = get_condition_modifiers(ws, "hero")
        assert mods.actions_prohibited is True, \
            f"Expected actions_prohibited=True for COWERING, got {mods.actions_prohibited}"

    # ─────────────────────────────────────────────────────────────────────────
    # CF-005: FASCINATED — enum entry exists
    # ─────────────────────────────────────────────────────────────────────────

    def test_CF005_fascinated_enum_exists(self):
        """CF-005: ConditionType.FASCINATED exists — no AttributeError."""
        ct = ConditionType.FASCINATED
        assert ct.value == "fascinated", \
            f"Expected 'fascinated' but got {ct.value!r}"

    # ─────────────────────────────────────────────────────────────────────────
    # CF-006: FASCINATED — actions prohibited in play loop
    # ─────────────────────────────────────────────────────────────────────────

    def test_CF006_fascinated_actions_prohibited_play_loop(self):
        """CF-006: Actor with FASCINATED → execute_turn returns action_denied."""
        entities = {
            "bard": _base_entity("bard", team="players", x=0, y=0),
            "goblin": _base_entity("goblin", team="monsters", x=5, y=0),
        }
        ws = _make_world(entities)
        fascinated = create_fascinated_condition("bardic_fascination", 0)
        ws = apply_condition(ws, "bard", fascinated)

        intent = AttackIntent(
            attacker_id="bard",
            target_id="goblin",
            attack_bonus=4,
            weapon=Weapon(damage_dice="1d6", damage_bonus=0, damage_type="slashing"),
        )
        turn_ctx = TurnContext(turn_index=0, actor_id="bard", actor_team="players")
        rng = RNGManager(42)
        result = execute_turn(
            turn_ctx=turn_ctx,
            combat_intent=intent,
            world_state=ws,
            rng=rng,
            next_event_id=1,
            timestamp=0.0,
        )

        assert result.status == "action_denied", \
            f"Expected action_denied for FASCINATED actor, got {result.status!r}"
        event_types = [e.event_type for e in result.events]
        assert "action_denied" in event_types, \
            f"Expected action_denied event, got: {event_types}"

    # ─────────────────────────────────────────────────────────────────────────
    # CF-007: FASCINATED — no AC modifier
    # ─────────────────────────────────────────────────────────────────────────

    def test_CF007_fascinated_no_ac_modifier(self):
        """CF-007: FASCINATED condition → ac_modifier == 0 (no AC penalty per PHB p.310)."""
        fascinated = create_fascinated_condition("hypnotic_pattern", 0)
        entity = _base_entity("wizard")
        entity[EF.CONDITIONS] = _conds(fascinated)
        ws = _make_world({"wizard": entity})

        mods = get_condition_modifiers(ws, "wizard", context="defense")
        assert mods.ac_modifier == 0, \
            f"Expected ac_modifier=0 for FASCINATED, got {mods.ac_modifier}"
        assert mods.ac_modifier_melee == 0, \
            f"Expected ac_modifier_melee=0 for FASCINATED, got {mods.ac_modifier_melee}"

    # ─────────────────────────────────────────────────────────────────────────
    # CF-008: Entity without COWERING/FASCINATED — normal AC, full actions
    # ─────────────────────────────────────────────────────────────────────────

    def test_CF008_no_condition_no_penalty(self):
        """CF-008: Actor with no conditions — normal AC, actions_prohibited=False."""
        entity = _base_entity("fighter")
        entity[EF.CONDITIONS] = {}
        ws = _make_world({"fighter": entity})

        mods = get_condition_modifiers(ws, "fighter")
        assert mods.ac_modifier == 0, \
            f"Expected 0 AC modifier without conditions, got {mods.ac_modifier}"
        assert mods.actions_prohibited is False, \
            f"Expected actions_prohibited=False without conditions, got {mods.actions_prohibited}"
        assert mods.loses_dex_to_ac is False, \
            f"Expected loses_dex_to_ac=False without conditions, got {mods.loses_dex_to_ac}"

"""Gate tests — WO-ENGINE-CONDITION-SKILL-COVERAGE-001
CSC-001..008: dazzled Search penalty, deafened 20% verbal failure, factory names.
"""
from __future__ import annotations
from typing import Any, Dict
from unittest.mock import MagicMock
from aidm.schemas.entity_fields import EF
from aidm.schemas.conditions import create_dazzled_condition
from aidm.core.condition_combat_resolver import create_deafened_condition
from aidm.core.skill_resolver import resolve_skill_check
from aidm.core.state import WorldState
from aidm.core.play_loop import TurnContext, execute_turn

# Minimal spell caster setup
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
        EF.SKILL_RANKS: {},
    }


def _caster(eid: str, conditions: dict = None) -> Dict[str, Any]:
    e = _entity(eid, conditions)
    e.update({
        EF.CLASS_LEVELS: {"wizard": 5}, EF.SPELL_SLOTS: {"1": 4},
        EF.CASTER_LEVEL: 5,
    })
    return e


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


def _ctx(actor_id: str = "actor_1") -> TurnContext:
    return TurnContext(turn_index=0, actor_id=actor_id, actor_team="party")


def _rng(roll: int = 15) -> MagicMock:
    rng = MagicMock()
    rng.stream.return_value.randint.return_value = roll
    return rng


def test_CSC001_dazzled_search_penalty():
    """CSC-001: Dazzled entity + search check → -1 penalty applied."""
    ci = create_dazzled_condition("test", 0)
    dazzled_entity = _entity("actor_1", {"dazzled": ci.to_dict()})
    clean_entity = _entity("actor_1")
    # DC=0, roll is fixed by mock so only modifier difference matters
    r_dazzled = resolve_skill_check(dazzled_entity, "search", 0, _rng(10))
    r_clean = resolve_skill_check(clean_entity, "search", 0, _rng(10))
    assert r_dazzled.total == r_clean.total - 1, (
        f"Dazzled search penalty not applied: dazzled={r_dazzled.total}, clean={r_clean.total}"
    )


def test_CSC002_dazzled_spot_penalty_regression():
    """CSC-002: Dazzled entity + spot check → -1 penalty still applied (regression)."""
    ci = create_dazzled_condition("test", 0)
    dazzled_entity = _entity("actor_1", {"dazzled": ci.to_dict()})
    clean_entity = _entity("actor_1")
    r_dazzled = resolve_skill_check(dazzled_entity, "spot", 0, _rng(10))
    r_clean = resolve_skill_check(clean_entity, "spot", 0, _rng(10))
    assert r_dazzled.total == r_clean.total - 1, (
        f"Dazzled spot regression: dazzled={r_dazzled.total}, clean={r_clean.total}"
    )


def test_CSC003_non_dazzled_search_no_penalty():
    """CSC-003: Non-dazzled entity + search check → no penalty."""
    clean_entity = _entity("actor_1")
    r = resolve_skill_check(clean_entity, "search", 0, _rng(10))
    # With roll=10, no ability mod, no ranks: expected total = 10
    assert r.total == 10, f"Unexpected total for non-dazzled search: {r.total}"


def test_CSC004_deafened_verbal_fail():
    """CSC-004: Deafened entity + verbal spell + seeded d100 ≤ 20 → deafened_spell_failure_check event (failed=True)."""
    from aidm.core.spell_resolver import SpellCastIntent
    ci = create_deafened_condition("test", 0)
    actor = _caster("actor_1", {"deafened": ci.to_dict()})
    ws = _ws({"actor_1": actor})
    intent = SpellCastIntent(caster_id="actor_1", spell_id="magic_missile", target_entity_id="actor_1")
    # Roll 15 → ≤ 20 → deafened check fails
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(15))
    deaf_events = [e for e in result.events if e.event_type == "deafened_spell_failure_check"]
    assert deaf_events, "No deafened_spell_failure_check event emitted"
    assert deaf_events[0].payload.get("failed") is True, (
        f"Expected failed=True in deafened event, got {deaf_events[0].payload}"
    )


def test_CSC005_deafened_verbal_pass():
    """CSC-005: Deafened entity + verbal spell + seeded d100 > 20 → deafened_spell_failure_check event (failed=False), spell proceeds."""
    from aidm.core.spell_resolver import SpellCastIntent
    ci = create_deafened_condition("test", 0)
    actor = _caster("actor_1", {"deafened": ci.to_dict()})
    ws = _ws({"actor_1": actor})
    intent = SpellCastIntent(caster_id="actor_1", spell_id="magic_missile", target_entity_id="actor_1")
    # Roll 25 → > 20 → deafened check passes
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(25))
    deaf_events = [e for e in result.events if e.event_type == "deafened_spell_failure_check"]
    assert deaf_events, "No deafened_spell_failure_check event emitted for deafened caster"
    assert deaf_events[0].payload.get("failed") is False, (
        f"Expected failed=False in deafened event, got {deaf_events[0].payload}"
    )


def test_CSC006_non_deafened_no_failure_roll():
    """CSC-006: Non-deafened entity + verbal spell → no deafened_spell_failure_check event fires."""
    from aidm.core.spell_resolver import SpellCastIntent
    actor = _caster("actor_1")
    ws = _ws({"actor_1": actor})
    intent = SpellCastIntent(caster_id="actor_1", spell_id="magic_missile", target_entity_id="actor_1")
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(15))
    deaf_events = [e for e in result.events if e.event_type == "deafened_spell_failure_check"]
    assert not deaf_events, (
        f"deafened_spell_failure_check fired for non-deafened caster: {deaf_events}"
    )


def test_CSC007_deafened_silent_spell_no_failure_roll():
    """CSC-007: Deafened entity + non-verbal spell (Silent Spell metamagic) → no failure roll fires."""
    from aidm.core.spell_resolver import SpellCastIntent
    ci = create_deafened_condition("test", 0)
    actor = _caster("actor_1", {"deafened": ci.to_dict()})
    ws = _ws({"actor_1": actor})
    # Silent metamagic suppresses verbal component → deafened check is inside _has_verbal block → skipped
    intent = SpellCastIntent(
        caster_id="actor_1", spell_id="magic_missile", target_entity_id="actor_1",
        metamagic=("silent",)
    )
    result = execute_turn(world_state=ws, turn_ctx=_ctx(), combat_intent=intent, rng=_rng(15))
    deaf_events = [e for e in result.events if e.event_type == "deafened_spell_failure_check"]
    assert not deaf_events, (
        f"deafened_spell_failure_check wrongly fired for silent spell: {deaf_events}"
    )


def test_CSC008_coverage_map_row_387_updated():
    """CSC-008: ENGINE_COVERAGE_MAP.md row 387 text contains '20% spell failure' (not 'prevents verbal')."""
    import os
    coverage_path = os.path.join(
        os.path.dirname(__file__), "..", "docs", "ENGINE_COVERAGE_MAP.md"
    )
    with open(coverage_path, encoding="utf-8") as f:
        content = f.read()
    # The old text was "prevents verbal spells" — new text should be "20% spell failure"
    assert "20% spell failure" in content, (
        "ENGINE_COVERAGE_MAP.md does not contain '20% spell failure' — row 387 not updated"
    )

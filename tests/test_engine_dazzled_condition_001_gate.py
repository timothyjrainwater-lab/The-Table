"""Gate tests: ENGINE-DAZZLED-CONDITION-001

Dazzled condition: -1 to attack rolls (automatic via ConditionModifiers),
-1 to Spot checks (explicit guard in skill_resolver). PHB p.309.

WO-ENGINE-DAZZLED-CONDITION-001, Batch I (Dispatch #18).
"""

import pytest
from unittest.mock import MagicMock

from aidm.schemas.conditions import (
    ConditionType, create_dazzled_condition, create_shaken_condition
)
from aidm.core.conditions import get_condition_modifiers
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.skill_resolver import resolve_skill_check


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng_fixed(roll):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _conds(*condition_instances):
    """Build a conditions dict from ConditionInstance objects (proper serialized format)."""
    result = {}
    for ci in condition_instances:
        result[ci.condition_type.value] = ci.to_dict()
    return result


def _entity_with_conditions(cond_dict=None, feats=None):
    """Build a minimal entity dict with properly serialized conditions."""
    return {
        EF.ENTITY_ID: "hero",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 14,
        EF.ATTACK_BONUS: 5,
        EF.TEAM: "players",
        EF.CONDITIONS: cond_dict if cond_dict is not None else {},
        EF.FEATS: feats or [],
        EF.DEX_MOD: 1,
        EF.STR_MOD: 2,
        EF.WIS_MOD: 1,
        EF.CON_MOD: 0,
        EF.INT_MOD: 0,
        EF.CHA_MOD: 0,
        EF.SKILL_RANKS: {"spot": 4, "listen": 3},
        EF.CLASS_SKILLS: ["spot", "listen"],
        EF.ARMOR_CHECK_PENALTY: 0,
    }


def _make_world(entities):
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDazzledCondition001Gate:

    def test_DZ001_dazzled_melee_attack_minus_one(self):
        """DZ-001: Dazzled attacker melee attack — -1 penalty applied via ConditionModifiers."""
        dazzled = create_dazzled_condition("test_source", 0)
        entity = _entity_with_conditions(_conds(dazzled))
        ws = _make_world({"hero": entity})

        mods = get_condition_modifiers(ws, "hero", context="attack")
        assert mods.attack_modifier == -1, \
            f"Expected -1 attack from dazzled, got {mods.attack_modifier}"

    def test_DZ002_dazzled_ranged_attack_minus_one(self):
        """DZ-002: Dazzled attacker ranged attack — same ConditionModifiers path, -1 penalty."""
        dazzled = create_dazzled_condition("test_source", 0)
        entity = _entity_with_conditions(_conds(dazzled))
        ws = _make_world({"hero": entity})

        mods = get_condition_modifiers(ws, "hero", context="attack")
        assert mods.attack_modifier == -1, \
            f"Expected -1 attack from dazzled (ranged), got {mods.attack_modifier}"

    def test_DZ003_non_dazzled_no_attack_penalty(self):
        """DZ-003: Non-dazzled attacker — no penalty."""
        entity = _entity_with_conditions({})
        ws = _make_world({"hero": entity})

        mods = get_condition_modifiers(ws, "hero", context="attack")
        assert mods.attack_modifier == 0, \
            f"Expected 0 attack modifier for non-dazzled, got {mods.attack_modifier}"

    def test_DZ004_dazzled_plus_shaken_stack(self):
        """DZ-004: Dazzled + Shaken attacker — -3 total penalty (-2 Shaken + -1 Dazzled)."""
        dazzled = create_dazzled_condition("test_source", 0)
        shaken = create_shaken_condition("fear_spell", 0)
        entity = _entity_with_conditions(_conds(dazzled, shaken))
        ws = _make_world({"hero": entity})

        mods = get_condition_modifiers(ws, "hero", context="attack")
        assert mods.attack_modifier == -3, \
            f"Expected -3 total (dazzled -1 + shaken -2), got {mods.attack_modifier}"

    def test_DZ005_dazzled_spot_check_penalty(self):
        """DZ-005: Dazzled entity Spot check — -1 penalty applied."""
        dazzled = create_dazzled_condition("test_source", 0)
        entity = _entity_with_conditions(_conds(dazzled))
        rng = _make_rng_fixed(10)

        # Spot check without dazzle: 10 (d20) + 1 (WIS mod) + 4 (ranks) = 15
        # With dazzle:              10 (d20) + 1 (WIS mod) + 4 (ranks) - 1 (dazzle) = 14
        result = resolve_skill_check(
            entity=entity,
            skill_id="spot",
            dc=13,
            rng=rng,
        )
        assert result.total == 14, f"Expected 14 (10+1+4-1 dazzle), got {result.total}"

    def test_DZ006_dazzled_non_spot_skill_no_penalty(self):
        """DZ-006: Dazzled entity Listen check — no penalty (Dazzled only penalizes Spot)."""
        dazzled = create_dazzled_condition("test_source", 0)
        entity = _entity_with_conditions(_conds(dazzled))
        rng = _make_rng_fixed(10)

        # Listen: 10 + 1 (WIS mod) + 3 (ranks) = 14 — no dazzle penalty
        result = resolve_skill_check(
            entity=entity,
            skill_id="listen",
            dc=10,
            rng=rng,
        )
        assert result.total == 14, f"Expected 14 (no dazzle penalty on Listen), got {result.total}"

    def test_DZ007_dazzled_saving_throw_no_penalty(self):
        """DZ-007: Dazzled entity saving throw — no penalty (Dazzled does not affect saves)."""
        dazzled = create_dazzled_condition("test_source", 0)
        entity = _entity_with_conditions(_conds(dazzled))
        ws = _make_world({"hero": entity})

        mods = get_condition_modifiers(ws, "hero", context="save")
        assert mods.fort_save_modifier == 0, "Dazzled should not affect Fort save"
        assert mods.ref_save_modifier == 0, "Dazzled should not affect Ref save"
        assert mods.will_save_modifier == 0, "Dazzled should not affect Will save"

    def test_DZ008_no_conditions_field_no_crash(self):
        """DZ-008: Entity with no CONDITIONS field — no crash, no penalty applied."""
        entity = {
            EF.ENTITY_ID: "hero",
            EF.HP_CURRENT: 20,
            EF.HP_MAX: 20,
            EF.AC: 14,
            EF.ATTACK_BONUS: 5,
            EF.TEAM: "players",
            # No EF.CONDITIONS key at all
            EF.FEATS: [],
            EF.DEX_MOD: 1,
            EF.WIS_MOD: 1,
            EF.SKILL_RANKS: {"spot": 4},
            EF.CLASS_SKILLS: ["spot"],
            EF.ARMOR_CHECK_PENALTY: 0,
        }
        ws = _make_world({"hero": entity})

        # Should not crash
        mods = get_condition_modifiers(ws, "hero", context="attack")
        assert mods.attack_modifier == 0

        rng = _make_rng_fixed(10)
        result = resolve_skill_check(entity=entity, skill_id="spot", dc=5, rng=rng)
        assert result is not None, "resolve_skill_check must not crash without CONDITIONS"

"""ENGINE-CASTER-LEVEL-2 Gate — Secondary caster level consume-site fix (8 tests).

Gate: ENGINE-CASTER-LEVEL-2 (CL2)
Tests: CL2-001 through CL2-008
WO: WO-ENGINE-CASTER-LEVEL-2-001
PHB p.57 (multiclass CL = class level), PHB p.176 (CL drives spell potency).

Summary: Dual-caster entities have two independent caster levels (EF.CASTER_LEVEL
and EF.CASTER_LEVEL_2). When casting from the secondary class, all CL-dependent
effects must use CL_2, not CL_1.
"""

import pytest
from unittest.mock import MagicMock

from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.core.state import WorldState
from aidm.core.play_loop import _create_caster_stats, _resolve_spell_cast

# _get_caster_level is part of this WO — import conditionally to allow
# behavioral tests to run before implementation while helper tests skip.
try:
    from aidm.core.play_loop import _get_caster_level
except ImportError:
    _get_caster_level = None
from aidm.core.spell_resolver import SpellCastIntent
from aidm.data.spell_definitions import SPELL_REGISTRY
from aidm.schemas.saves import SRCheck
from aidm.core.save_resolver import check_spell_resistance


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _dual_caster(cl1=7, cl2=3, primary_slots=None, secondary_slots=None):
    """Build a dual-caster entity (Cleric 7 / Druid 3).

    Args:
        cl1: Primary caster level (cleric).
        cl2: Secondary caster level (druid).
        primary_slots: Override primary spell slots dict.
        secondary_slots: Override secondary spell slots dict.
    """
    return {
        EF.ENTITY_ID: "caster",
        "name": "caster",
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 16,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.SAVE_FORT: 5,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 6,
        EF.CON_MOD: 1,
        EF.DEX_MOD: 0,
        EF.WIS_MOD: 3,
        EF.CHA_MOD: 0,
        EF.STR_MOD: 1,
        EF.TEMPORARY_MODIFIERS: {},
        EF.NEGATIVE_LEVELS: 0,
        EF.CLASS_LEVELS: {"cleric": cl1, "druid": cl2},
        EF.CASTER_CLASS: "cleric",
        EF.CASTER_CLASS_2: "druid",
        EF.CASTER_LEVEL: cl1,
        EF.CASTER_LEVEL_2: cl2,
        EF.SPELL_SLOTS: primary_slots if primary_slots is not None else {1: 3, 2: 2},
        EF.SPELL_SLOTS_2: secondary_slots if secondary_slots is not None else {1: 2},
        EF.SPELLS_PREPARED: {1: ["bless"]},
        EF.SPELLS_PREPARED_2: {1: ["cure_light_wounds"]},
        "caster_level": cl1,
        "spell_dc_base": 13,
    }


def _single_caster(cl=5):
    """Build a single-class caster (Cleric 5)."""
    return {
        EF.ENTITY_ID: "caster",
        "name": "caster",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 16,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.SAVE_FORT: 4,
        EF.SAVE_REF: 1,
        EF.SAVE_WILL: 5,
        EF.CON_MOD: 1,
        EF.DEX_MOD: 0,
        EF.WIS_MOD: 3,
        EF.CHA_MOD: 0,
        EF.STR_MOD: 1,
        EF.TEMPORARY_MODIFIERS: {},
        EF.NEGATIVE_LEVELS: 0,
        EF.CLASS_LEVELS: {"cleric": cl},
        EF.CASTER_CLASS: "cleric",
        EF.CASTER_LEVEL: cl,
        EF.SPELL_SLOTS: {1: 4, 2: 3},
        EF.SPELLS_PREPARED: {1: ["cure_light_wounds"]},
        "caster_level": cl,
        "spell_dc_base": 13,
    }


def _target_entity(eid="ally", hp=5, hp_max=50):
    """Low-HP target for healing tests."""
    return {
        EF.ENTITY_ID: eid,
        "name": eid,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: 12,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.POSITION: {"x": 1, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.SAVE_FORT: 1,
        EF.SAVE_REF: 1,
        EF.SAVE_WILL: 1,
        EF.CON_MOD: 0,
        EF.DEX_MOD: 0,
        EF.WIS_MOD: 0,
        EF.TEMPORARY_MODIFIERS: {},
    }


def _sr_target(eid="enemy", sr=15):
    """Target with spell resistance for SR check tests."""
    return {
        EF.ENTITY_ID: eid,
        "name": eid,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 14,
        EF.TEAM: "monsters",
        EF.DEFEATED: False,
        EF.POSITION: {"x": 2, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 3,
        EF.SAVE_WILL: 3,
        EF.SR: sr,
        EF.CON_MOD: 0,
        EF.DEX_MOD: 0,
        EF.WIS_MOD: 0,
        EF.TEMPORARY_MODIFIERS: {},
    }


def _make_world(*entities):
    ents = {}
    for e in entities:
        ents[e[EF.ENTITY_ID]] = e
    return WorldState(
        ruleset_version="3.5",
        entities=ents,
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": list(ents.keys()),
            "flat_footed_actors": [],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _make_rng(roll=5):
    """Mock RNG where all streams return the same fixed roll."""
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


# ─────────────────────────────────────────────────────────────────────────────
# CL2-001: _get_caster_level() with use_secondary=True returns CL_2
# ─────────────────────────────────────────────────────────────────────────────

class TestCL2Helper:

    def test_cl2_001_helper_returns_secondary_cl(self):
        """CL2-001: _get_caster_level(entity, use_secondary=True) returns EF.CASTER_LEVEL_2."""
        if _get_caster_level is None:
            pytest.fail("_get_caster_level not yet implemented in play_loop — WO incomplete")
        entity = _dual_caster(cl1=7, cl2=3)
        result = _get_caster_level(entity, use_secondary=True)
        assert result == 3, f"Expected CL2=3, got {result}"

    def test_cl2_002_helper_returns_primary_cl(self):
        """CL2-002: _get_caster_level(entity, use_secondary=False) returns EF.CASTER_LEVEL."""
        if _get_caster_level is None:
            pytest.fail("_get_caster_level not yet implemented in play_loop — WO incomplete")
        entity = _dual_caster(cl1=7, cl2=3)
        result = _get_caster_level(entity, use_secondary=False)
        assert result == 7, f"Expected CL1=7, got {result}"


# ─────────────────────────────────────────────────────────────────────────────
# CL2-003/004: Healing bonus uses correct CL (end-to-end through _resolve_spell_cast)
# ─────────────────────────────────────────────────────────────────────────────

class TestCL2Healing:

    def test_cl2_003_secondary_heal_uses_cl2(self):
        """CL2-003: Cure spell cast from secondary class uses CL_2 for healing bonus.

        Setup: Cleric 7 / Druid 3. Primary slots exhausted → falls back to
        secondary (CL_2=3). cure_light_wounds: 1d8 + min(CL, 5).
        Mock roll=5 → total should be 5 + min(3, 5) = 8.
        """
        caster = _dual_caster(
            cl1=7, cl2=3,
            primary_slots={1: 0},     # Primary exhausted
            secondary_slots={1: 1},   # Secondary available
        )
        ally = _target_entity(hp=5, hp_max=50)
        ws = _make_world(caster, ally)
        rng = _make_rng(roll=5)

        intent = SpellCastIntent(
            caster_id="caster",
            spell_id="cure_light_wounds",
            target_entity_id="ally",
        )

        events, new_ws, token = _resolve_spell_cast(
            intent=intent,
            world_state=ws,
            rng=rng,
            grid=None,
            next_event_id=1,
            timestamp=0.0,
            turn_index=0,
        )

        # Find hp_changed event for ally
        hp_events = [e for e in events if e.event_type == "hp_changed"
                     and e.payload.get("entity_id") == "ally"]
        assert len(hp_events) == 1, f"Expected 1 hp_changed for ally, got {len(hp_events)}"

        delta = hp_events[0].payload["delta"]
        # Healing = 5 (die) + min(CL2=3, 5) = 8
        assert delta == 8, (
            f"CL2-003: Healing delta should be +8 (roll=5 + CL2 bonus=3), got {delta}. "
            f"If delta=10, CL_1 was used instead of CL_2."
        )

    def test_cl2_004_primary_heal_uses_cl1(self):
        """CL2-004: Cure spell cast from primary class uses CL_1 for healing bonus.

        Same dual-caster but primary slots available. CL_1=7.
        Healing = 5 + min(7, 5) = 10.
        """
        caster = _dual_caster(
            cl1=7, cl2=3,
            primary_slots={1: 2},     # Primary available
            secondary_slots={1: 1},
        )
        # Need cure_light_wounds in PRIMARY prepared list
        caster[EF.SPELLS_PREPARED] = {1: ["cure_light_wounds"]}
        ally = _target_entity(hp=5, hp_max=50)
        ws = _make_world(caster, ally)
        rng = _make_rng(roll=5)

        intent = SpellCastIntent(
            caster_id="caster",
            spell_id="cure_light_wounds",
            target_entity_id="ally",
        )

        events, new_ws, token = _resolve_spell_cast(
            intent=intent,
            world_state=ws,
            rng=rng,
            grid=None,
            next_event_id=1,
            timestamp=0.0,
            turn_index=0,
        )

        hp_events = [e for e in events if e.event_type == "hp_changed"
                     and e.payload.get("entity_id") == "ally"]
        assert len(hp_events) == 1, f"Expected 1 hp_changed for ally, got {len(hp_events)}"

        delta = hp_events[0].payload["delta"]
        # Healing = 5 (die) + min(CL1=7, 5) = 10
        assert delta == 10, (
            f"CL2-004: Healing delta should be +10 (roll=5 + CL1 bonus=5), got {delta}."
        )


# ─────────────────────────────────────────────────────────────────────────────
# CL2-005/006: _create_caster_stats() produces correct CasterStats.caster_level
# ─────────────────────────────────────────────────────────────────────────────

class TestCL2CasterStats:

    def test_cl2_005_caster_stats_secondary(self):
        """CL2-005: _create_caster_stats() with use_secondary=True sets CasterStats.caster_level to CL_2."""
        caster = _dual_caster(cl1=7, cl2=3)
        ws = _make_world(caster)

        try:
            stats = _create_caster_stats("caster", ws, use_secondary=True)
        except TypeError:
            pytest.fail("_create_caster_stats() does not accept use_secondary param — WO incomplete")
        assert stats.caster_level == 3, (
            f"CL2-005: CasterStats.caster_level should be 3 (CL_2), got {stats.caster_level}"
        )

    def test_cl2_006_caster_stats_primary(self):
        """CL2-006: _create_caster_stats() with use_secondary=False sets CasterStats.caster_level to CL_1."""
        caster = _dual_caster(cl1=7, cl2=3)
        ws = _make_world(caster)

        try:
            stats = _create_caster_stats("caster", ws, use_secondary=False)
        except TypeError:
            pytest.fail("_create_caster_stats() does not accept use_secondary param — WO incomplete")
        assert stats.caster_level == 7, (
            f"CL2-006: CasterStats.caster_level should be 7 (CL_1), got {stats.caster_level}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# CL2-007: Single-class caster uses EF.CASTER_LEVEL correctly
# ─────────────────────────────────────────────────────────────────────────────

class TestCL2SingleClass:

    def test_cl2_007_single_class_uses_primary(self):
        """CL2-007: Single-class caster (no CL_2) uses EF.CASTER_LEVEL for all paths."""
        caster = _single_caster(cl=5)
        ally = _target_entity(hp=5, hp_max=50)
        ws = _make_world(caster, ally)
        rng = _make_rng(roll=5)

        intent = SpellCastIntent(
            caster_id="caster",
            spell_id="cure_light_wounds",
            target_entity_id="ally",
        )

        events, new_ws, token = _resolve_spell_cast(
            intent=intent,
            world_state=ws,
            rng=rng,
            grid=None,
            next_event_id=1,
            timestamp=0.0,
            turn_index=0,
        )

        hp_events = [e for e in events if e.event_type == "hp_changed"
                     and e.payload.get("entity_id") == "ally"]
        assert len(hp_events) == 1, f"Expected 1 hp_changed for ally, got {len(hp_events)}"

        delta = hp_events[0].payload["delta"]
        # Healing = 5 (die) + min(CL=5, 5) = 10
        assert delta == 10, (
            f"CL2-007: Healing delta should be +10 (roll=5 + CL bonus=5), got {delta}."
        )


# ─────────────────────────────────────────────────────────────────────────────
# CL2-008: Missing CL_2 defaults to 1 (no crash)
# ─────────────────────────────────────────────────────────────────────────────

class TestCL2MissingField:

    def test_cl2_008_missing_cl2_defaults_to_1(self):
        """CL2-008: Entity with no EF.CASTER_LEVEL_2 + use_secondary=True → CL defaults to 1."""
        if _get_caster_level is None:
            pytest.fail("_get_caster_level not yet implemented in play_loop — WO incomplete")
        entity = _single_caster(cl=5)
        # Explicitly confirm CL_2 is absent
        assert EF.CASTER_LEVEL_2 not in entity, "Precondition: CL_2 should not be in entity"

        result = _get_caster_level(entity, use_secondary=True)
        assert result == 1, (
            f"CL2-008: Missing CL_2 should default to 1 (PHB p.176 minimum), got {result}. "
            f"Must not KeyError or return 0."
        )

"""Gate tests: ENGINE-CONCENTRATION-VIGOROUS-001

Vigorous/violent motion requires Concentration check when casting.
DC: vigorous = 10 + spell level, violent = 15 + spell level. PHB p.69.

WO-ENGINE-CONCENTRATION-VIGOROUS-001, Batch I (Dispatch #18).
"""

import pytest
from unittest.mock import MagicMock, patch

from aidm.core.play_loop import execute_turn
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_turn_ctx(actor_id="mage"):
    ctx = MagicMock()
    ctx.actor_id = actor_id
    ctx.turn_index = 0
    ctx.actor_team = "players"
    return ctx


def _make_rng_fixed(roll):
    """RNG that always returns the same value."""
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _make_rng_sequence(rolls):
    """RNG that returns values from a sequence."""
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(side_effect=rolls)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _make_world(actor_id="mage", motion_state=None, concentration_bonus=10,
                target_id="goblin", target_hp=15):
    """Build a world with a mage and optional target."""
    mage = {
        EF.ENTITY_ID: actor_id,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 12,
        EF.TEAM: "players",
        EF.POSITION: {"x": 0, "y": 5},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.DEX_MOD: 1,
        EF.CONCENTRATION_BONUS: concentration_bonus,
        "spell_slots": {1: 3, 2: 2, 3: 1},
        "spells_prepared": {1: ["magic_missile"], 2: [], 3: []},
        "caster_level": 5,
        "caster_class": "wizard",
    }
    if motion_state is not None:
        mage[EF.MOTION_STATE] = motion_state

    entities = {actor_id: mage}
    if target_id:
        entities[target_id] = {
            EF.ENTITY_ID: target_id,
            EF.HP_CURRENT: target_hp,
            EF.HP_MAX: target_hp,
            EF.AC: 12,
            EF.TEAM: "monsters",
            EF.POSITION: {"x": 0, "y": 6},
            EF.CONDITIONS: {},
            EF.FEATS: [],
            EF.DEX_MOD: 0,
        }

    active_combat = {
        "initiative_order": [actor_id] + ([target_id] if target_id else []),
        "aoo_used_this_round": [],
        "aoo_count_this_round": {},
        "action_budget_actor": None,
        "action_budget": None,
    }
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat=active_combat,
    )


def _make_spell_intent(caster_id="mage", target_id="goblin", spell_id="magic_missile"):
    from aidm.core.spell_resolver import SpellCastIntent
    from aidm.schemas.position import Position
    return SpellCastIntent(
        caster_id=caster_id,
        spell_id=spell_id,
        target_entity_id=target_id,
    )


def _events_of_type(result, event_type):
    return [e for e in result.events if e.event_type == event_type]


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestConcentrationVigorous001Gate:

    def test_CV001_vigorous_motion_low_roll_fails(self):
        """CV-001: Caster on vigorous mount, low Concentration roll — spell fails."""
        ws = _make_world(motion_state="vigorous", concentration_bonus=0)
        intent = _make_spell_intent()
        # magic_missile is level 1, vigorous DC = 10 + 1 = 11
        # Roll 5 + 0 bonus = 5 < 11 → fail
        rng = _make_rng_fixed(5)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("mage"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        conc_failed = _events_of_type(result, "concentration_failed")
        assert len(conc_failed) >= 1, "Vigorous motion should trigger concentration failure on low roll"
        payload = conc_failed[0].payload
        assert payload.get("reason") == "vigorous"
        assert payload.get("dc") == 11  # 10 + spell_level(1)

    def test_CV002_vigorous_motion_high_roll_succeeds(self):
        """CV-002: Caster on vigorous mount, high Concentration roll — spell succeeds."""
        ws = _make_world(motion_state="vigorous", concentration_bonus=5)
        intent = _make_spell_intent()
        # DC = 11, roll 15 + 5 = 20 ≥ 11 → success
        rng = _make_rng_fixed(15)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("mage"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        conc_failed = _events_of_type(result, "concentration_failed")
        assert len(conc_failed) == 0 or all(e.payload.get("reason") != "vigorous" for e in conc_failed), \
            "High roll should pass vigorous concentration"

    def test_CV003_violent_motion_low_roll_fails(self):
        """CV-003: Caster in violent motion, low roll — spell fails; DC = 15 + spell_level."""
        ws = _make_world(motion_state="violent", concentration_bonus=0)
        intent = _make_spell_intent()
        # DC = 15 + 1 = 16, roll 10 + 0 = 10 < 16 → fail
        rng = _make_rng_fixed(10)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("mage"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        conc_failed = _events_of_type(result, "concentration_failed")
        assert len(conc_failed) >= 1, "Violent motion should trigger concentration failure"
        payload = conc_failed[0].payload
        assert payload.get("reason") == "violent"
        assert payload.get("dc") == 16  # 15 + 1

    def test_CV004_violent_motion_high_roll_succeeds(self):
        """CV-004: Caster in violent motion, high roll — spell succeeds."""
        ws = _make_world(motion_state="violent", concentration_bonus=10)
        intent = _make_spell_intent()
        # DC = 16, roll 10 + 10 = 20 ≥ 16 → success
        rng = _make_rng_fixed(10)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("mage"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        conc_failed = _events_of_type(result, "concentration_failed")
        violent_fails = [e for e in conc_failed if e.payload.get("reason") == "violent"]
        assert len(violent_fails) == 0, "High roll should pass violent concentration"

    def test_CV005_no_motion_state_no_check(self):
        """CV-005: No motion state — no vigorous/violent concentration check triggered."""
        ws = _make_world(motion_state=None, concentration_bonus=0)
        intent = _make_spell_intent()
        rng = _make_rng_fixed(1)  # Would fail if check fires

        result = execute_turn(
            turn_ctx=_make_turn_ctx("mage"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        conc_failed = _events_of_type(result, "concentration_failed")
        motion_fails = [e for e in conc_failed if e.payload.get("reason") in ("vigorous", "violent")]
        assert len(motion_fails) == 0, "No motion state should trigger no motion concentration check"

    def test_CV006_vigorous_fires_before_damage_check(self):
        """CV-006: Vigorous check fires independently; can coexist with damage concentration."""
        # This test verifies the check runs (event emitted with vigorous reason)
        # The check fires before the damage concentration check in the guard chain.
        ws = _make_world(motion_state="vigorous", concentration_bonus=20)  # High bonus → pass
        intent = _make_spell_intent()
        rng = _make_rng_fixed(1)  # Low roll but high bonus → 21, passes

        result = execute_turn(
            turn_ctx=_make_turn_ctx("mage"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        conc_success = _events_of_type(result, "concentration_success")
        vigorous_success = [e for e in conc_success if e.payload.get("reason") == "vigorous"]
        assert len(vigorous_success) >= 1, "Vigorous check should emit concentration_success when passed"

    def test_CV007_violent_takes_priority_over_vigorous(self):
        """CV-007: If motion_state is 'violent', DC=15+level, not 10+level."""
        ws = _make_world(motion_state="violent", concentration_bonus=0)
        intent = _make_spell_intent()
        # DC = 16 (violent). roll 12 + 0 = 12 < 16 → fail
        rng = _make_rng_fixed(12)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("mage"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        conc_failed = _events_of_type(result, "concentration_failed")
        violent_fails = [e for e in conc_failed if e.payload.get("reason") == "violent"]
        assert len(violent_fails) >= 1
        # Verify DC is 16, not 11 (vigorous would be 11)
        assert violent_fails[0].payload.get("dc") == 16

    def test_CV008_no_crash_missing_motion_state_field(self):
        """CV-008: Entity without MOTION_STATE field — no crash, no concentration check."""
        ws = _make_world(motion_state=None)
        # Verify the field is absent from the entity
        mage = ws.entities["mage"]
        assert EF.MOTION_STATE not in mage or mage.get(EF.MOTION_STATE) is None

        intent = _make_spell_intent()
        rng = _make_rng_fixed(20)

        result = execute_turn(
            turn_ctx=_make_turn_ctx("mage"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert result is not None, "execute_turn must not crash when MOTION_STATE is absent"
        motion_fails = [e for e in result.events
                        if e.event_type == "concentration_failed"
                        and e.payload.get("reason") in ("vigorous", "violent")]
        assert len(motion_fails) == 0

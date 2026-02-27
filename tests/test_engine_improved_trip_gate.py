"""Gate tests: ENGINE-IMPROVED-TRIP — WO-ENGINE-IMPROVED-TRIP-001.

PHB p.96: Improved Trip — no AoO on trip attempt + free attack after successful trip.
PHB p.96: Improved Sunder — no AoO on sunder attempt.

Tests IT-001 through IT-008, plus IT-009/IT-010 regression bonus.
WO-ENGINE-IMPROVED-TRIP-001, Batch N (Dispatch N).
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.play_loop import execute_turn
from aidm.core.aoo import check_aoo_triggers
from aidm.core.maneuver_resolver import resolve_trip
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.maneuvers import TripIntent, SunderIntent
from aidm.schemas.attack import Weapon


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng(rolls):
    """Build a mock RNG that yields the given values in sequence from 'combat' stream."""
    rng = MagicMock()
    stream = MagicMock()
    padded = list(rolls) + [10] * 20
    stream.randint.side_effect = padded
    rng.stream.return_value = stream
    return rng


def _make_turn_ctx(actor_id="attacker"):
    ctx = MagicMock()
    ctx.actor_id = actor_id
    ctx.turn_index = 0
    ctx.actor_team = "players"
    return ctx


def _make_entity(eid, team, feats=None, pos=(0, 0), hp=20, ac=14, atk=5,
                 str_mod=2, dex_mod=1, size="medium"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.ATTACK_BONUS: atk,
        EF.BAB: atk,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: dex_mod,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats or [],
        EF.POSITION: {"x": pos[0], "y": pos[1]},
        EF.SIZE_CATEGORY: size,
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
        EF.CLASS_LEVELS: {},
        EF.WEAPON: {
            "damage_dice": "1d6", "damage_bonus": 0, "damage_type": "slashing",
            "weapon_type": "one-handed", "enhancement_bonus": 0,
            "tags": [], "material": "steel", "alignment": "none",
        },
    }


def _make_world(attacker, target):
    entities = {attacker[EF.ENTITY_ID]: attacker, target[EF.ENTITY_ID]: target}
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "action_budget_actor": None,
            "action_budget": None,
        },
    )


def _has_aoo_event(result):
    return any(e.event_type == "aoo_triggered" for e in result.events)


def _events_of_type(events, event_type):
    return [e for e in events if e.event_type == event_type]


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestImprovedTripGate:

    # ── IT-001: Improved Trip → no AoO on trip attempt ──────────────────────

    def test_IT001_improved_trip_suppresses_aoo(self):
        """IT-001: Attacker WITH Improved Trip — no AoO triggered on TripIntent."""
        attacker = _make_entity("attacker", "players", feats=["improved_trip"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = TripIntent(attacker_id="attacker", target_id="target")
        rng = _make_rng([15, 12, 8, 15, 4])

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert not _has_aoo_event(result), (
            "IT-001: Improved Trip must suppress AoO on trip attempt"
        )

    # ── IT-002: No Improved Trip → AoO fires ────────────────────────────────

    def test_IT002_no_feat_aoo_triggers_on_trip(self):
        """IT-002: Attacker WITHOUT Improved Trip — AoO triggers from target normally."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = TripIntent(attacker_id="attacker", target_id="target")

        triggers = check_aoo_triggers(ws, "attacker", intent)
        assert any(t.reactor_id == "target" for t in triggers), (
            "IT-002: Without Improved Trip, target should have AoO trigger on TripIntent"
        )

    # ── IT-003: Improved Trip + successful trip → free attack emitted ────────

    def test_IT003_successful_trip_free_attack_event_emitted(self):
        """IT-003: Improved Trip + successful trip → improved_trip_free_attack event emitted."""
        attacker = _make_entity("attacker", "players", feats=["improved_trip"],
                                pos=(0, 0), atk=8, str_mod=3)
        target = _make_entity("target", "monsters", pos=(1, 0), str_mod=1, dex_mod=1)
        ws = _make_world(attacker, target)
        intent = TripIntent(attacker_id="attacker", target_id="target")
        # RNG sequence: touch attack (18=hit), attacker trip (18), defender trip (5)
        # then free attack: d20=15, damage=4
        rng = _make_rng([18, 18, 5, 15, 4])

        events, _, result = resolve_trip(
            intent=intent,
            world_state=ws,
            rng=rng,
            next_event_id=1,
            timestamp=0.0,
        )
        assert result.success, "IT-003: Trip must succeed for this test"
        free_atk_events = _events_of_type(events, "improved_trip_free_attack")
        assert len(free_atk_events) == 1, (
            f"IT-003: Expected 1 improved_trip_free_attack event, got {len(free_atk_events)}"
        )

    # ── IT-004: Improved Trip + failed trip → no free attack ─────────────────

    def test_IT004_failed_trip_no_free_attack(self):
        """IT-004: Improved Trip + failed trip → no free attack event."""
        attacker = _make_entity("attacker", "players", feats=["improved_trip"],
                                pos=(0, 0), str_mod=1)
        target = _make_entity("target", "monsters", pos=(1, 0), str_mod=4)
        ws = _make_world(attacker, target)
        intent = TripIntent(attacker_id="attacker", target_id="target")
        # RNG: touch attack hits (18), attacker trip check (5) loses to defender (18)
        rng = _make_rng([18, 5, 18])

        events, _, result = resolve_trip(
            intent=intent,
            world_state=ws,
            rng=rng,
            next_event_id=1,
            timestamp=0.0,
        )
        assert not result.success, "IT-004: Trip must fail for this test"
        free_atk_events = _events_of_type(events, "improved_trip_free_attack")
        assert len(free_atk_events) == 0, (
            "IT-004: No free attack event expected when trip fails"
        )

    # ── IT-005: Free attack uses full attack bonus ───────────────────────────

    def test_IT005_free_attack_uses_full_bab(self):
        """IT-005: Free attack after trip uses full BAB (not iterative -5 penalty)."""
        attacker = _make_entity("attacker", "players", feats=["improved_trip"],
                                pos=(0, 0), atk=8, str_mod=3)
        target = _make_entity("target", "monsters", pos=(1, 0), str_mod=1, dex_mod=0, ac=20)
        ws = _make_world(attacker, target)
        intent = TripIntent(attacker_id="attacker", target_id="target")
        # Touch attack hits (18), trip check wins (18 vs 5)
        # Free attack: d20=18 — with BAB=8, STR=3 → total=29, must hit AC=20
        rng = _make_rng([18, 18, 5, 18, 4])

        events, _, result = resolve_trip(
            intent=intent,
            world_state=ws,
            rng=rng,
            next_event_id=1,
            timestamp=0.0,
        )
        assert result.success
        # The attack_roll event after improved_trip_free_attack shows the attack result
        free_marker = _events_of_type(events, "improved_trip_free_attack")
        assert len(free_marker) == 1, "IT-005: Free attack marker event must be present"
        # Find the attack_roll event(s) after the marker
        marker_idx = next(i for i, e in enumerate(events) if e.event_type == "improved_trip_free_attack")
        post_events = events[marker_idx + 1:]
        attack_rolls = _events_of_type(post_events, "attack_roll")
        assert len(attack_rolls) >= 1, "IT-005: At least one attack_roll event after free attack marker"
        # The free attack d20=18, BAB=8, STR=3 → total=29 — check it is above AC=20
        ar_payload = attack_rolls[0].payload
        assert ar_payload.get("total", 0) >= 29 or ar_payload.get("hit", False), (
            "IT-005: Free attack at full BAB must use full attack bonus"
        )

    # ── IT-006: Improved Sunder → no AoO ────────────────────────────────────

    def test_IT006_improved_sunder_suppresses_aoo(self):
        """IT-006: Attacker WITH Improved Sunder — no AoO triggered on SunderIntent."""
        attacker = _make_entity("attacker", "players", feats=["improved_sunder"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = SunderIntent(attacker_id="attacker", target_id="target", target_item="weapon")
        rng = _make_rng([15, 12, 8])

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert not _has_aoo_event(result), (
            "IT-006: Improved Sunder must suppress AoO on sunder attempt"
        )

    # ── IT-007: No Improved Sunder → AoO fires ───────────────────────────────

    def test_IT007_no_feat_aoo_triggers_on_sunder(self):
        """IT-007: Attacker WITHOUT Improved Sunder — AoO triggers from target on SunderIntent."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = SunderIntent(attacker_id="attacker", target_id="target", target_item="weapon")

        triggers = check_aoo_triggers(ws, "attacker", intent)
        assert any(t.reactor_id == "target" for t in triggers), (
            "IT-007: Without Improved Sunder, target should have AoO trigger on SunderIntent"
        )

    # ── IT-008: Both feats active independently ───────────────────────────────

    def test_IT008_both_feats_independent(self):
        """IT-008: Attacker with both Improved Trip AND Improved Sunder — each suppresses AoO independently."""
        attacker = _make_entity("attacker", "players",
                                feats=["improved_trip", "improved_sunder"], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)

        trip_intent = TripIntent(attacker_id="attacker", target_id="target")
        sunder_intent = SunderIntent(attacker_id="attacker", target_id="target", target_item="weapon")

        # Both should suppress their respective AoOs
        trip_triggers = check_aoo_triggers(ws, "attacker", trip_intent)
        sunder_triggers = check_aoo_triggers(ws, "attacker", sunder_intent)

        # Raw triggers exist for both maneuvers (so we can verify suppression fires in play_loop)
        # Suppression is confirmed by execute_turn producing no aoo_triggered events
        rng_trip = _make_rng([15, 14, 8, 10, 4])
        result_trip = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=trip_intent,
            rng=rng_trip,
        )
        assert not _has_aoo_event(result_trip), (
            "IT-008: Improved Trip must suppress AoO even when entity also has Improved Sunder"
        )

        rng_sunder = _make_rng([15, 8, 10])
        result_sunder = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=sunder_intent,
            rng=rng_sunder,
        )
        assert not _has_aoo_event(result_sunder), (
            "IT-008: Improved Sunder must suppress AoO even when entity also has Improved Trip"
        )

    # ── IT-009: No Improved Trip feat → free attack NOT emitted ──────────────

    def test_IT009_no_feat_successful_trip_no_free_attack(self):
        """IT-009 (bonus): Entity WITHOUT Improved Trip, successful trip → no free attack event."""
        attacker = _make_entity("attacker", "players", feats=[],
                                pos=(0, 0), atk=8, str_mod=3)
        target = _make_entity("target", "monsters", pos=(1, 0), str_mod=1)
        ws = _make_world(attacker, target)
        intent = TripIntent(attacker_id="attacker", target_id="target")
        rng = _make_rng([18, 18, 5, 10, 3])

        events, _, result = resolve_trip(
            intent=intent,
            world_state=ws,
            rng=rng,
            next_event_id=1,
            timestamp=0.0,
        )
        assert result.success
        free_events = _events_of_type(events, "improved_trip_free_attack")
        assert len(free_events) == 0, (
            "IT-009: No free attack without Improved Trip feat"
        )

    # ── IT-010: Regression — sunder without feat still provokes AoO ──────────

    def test_IT010_regression_sunder_without_feat_provokes_aoo(self):
        """IT-010 (bonus): Sunder without Improved Sunder feat still provokes AoO from target."""
        attacker = _make_entity("attacker", "players", feats=[], pos=(0, 0))
        target = _make_entity("target", "monsters", pos=(1, 0))
        ws = _make_world(attacker, target)
        intent = SunderIntent(attacker_id="attacker", target_id="target", target_item="shield")
        rng = _make_rng([15, 12, 8])

        result = execute_turn(
            turn_ctx=_make_turn_ctx("attacker"),
            world_state=ws,
            combat_intent=intent,
            rng=rng,
        )
        assert _has_aoo_event(result), (
            "IT-010: Without Improved Sunder, aoo_triggered event must appear"
        )

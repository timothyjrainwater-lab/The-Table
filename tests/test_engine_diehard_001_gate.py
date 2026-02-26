"""Gate tests: ENGINE-DIEHARD-001

Diehard feat (PHB p.93): When reduced to -1 to -9 HP, automatically stabilize.
The entity becomes DISABLED (can act), not DYING.

WO-ENGINE-DIEHARD-001, Batch K (Dispatch #20).
Gate labels: DH-001 through DH-008.
"""

import pytest
from copy import deepcopy
from unittest.mock import MagicMock

from aidm.core.dying_resolver import resolve_dying_tick
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng_fixed(roll=5):
    """RNG that always returns `roll` for Fort save (deterministic)."""
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _dying_entity(eid, hp=-3, feats=None, stable=False):
    """Build a minimal dying entity dict."""
    return {
        EF.ENTITY_ID: eid,
        "name": eid,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: 20,
        EF.DYING: True,
        EF.STABLE: stable,
        EF.DISABLED: False,
        EF.DEFEATED: False,
        EF.FEATS: feats or [],
        EF.SAVE_FORT: 2,  # +2 Fort save bonus
        EF.TEAM: "players",
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

class TestDiehard001Gate:

    def test_DH001_diehard_auto_stabilizes(self):
        """DH-001: Entity with Diehard in DYING state → entity_stabilized event with reason='diehard'."""
        entity = _dying_entity("warrior", hp=-3, feats=["diehard"])
        ws = _make_world({"warrior": entity})
        rng = _make_rng_fixed(5)

        events, new_ws = resolve_dying_tick(ws, rng, next_event_id=1, timestamp=1.0)

        assert any(
            e.event_type == "entity_stabilized" and e.payload.get("reason") == "diehard"
            for e in events
        ), f"Expected entity_stabilized with reason='diehard'; got events: {[e.event_type for e in events]}"

    def test_DH002_diehard_no_hp_loss(self):
        """DH-002: Diehard entity auto-stabilizes → no hp_changed event emitted."""
        entity = _dying_entity("warrior", hp=-3, feats=["diehard"])
        ws = _make_world({"warrior": entity})
        rng = _make_rng_fixed(5)

        events, new_ws = resolve_dying_tick(ws, rng, next_event_id=1, timestamp=1.0)

        hp_events = [e for e in events if e.event_type == "hp_changed"]
        assert len(hp_events) == 0, \
            f"Expected no hp_changed for Diehard entity, got: {[e.payload for e in hp_events]}"

    def test_DH003_diehard_sets_stable_clears_dying(self):
        """DH-003: After Diehard tick → EF.STABLE=True, EF.DYING=False on entity."""
        entity = _dying_entity("warrior", hp=-5, feats=["diehard"])
        ws = _make_world({"warrior": entity})
        rng = _make_rng_fixed(5)

        events, new_ws = resolve_dying_tick(ws, rng, next_event_id=1, timestamp=1.0)

        updated = new_ws.entities["warrior"]
        assert updated.get(EF.STABLE) is True, \
            f"Expected EF.STABLE=True after Diehard, got {updated.get(EF.STABLE)}"
        assert updated.get(EF.DYING) is False, \
            f"Expected EF.DYING=False after Diehard, got {updated.get(EF.DYING)}"

    def test_DH004_no_diehard_normal_fort_save(self):
        """DH-004: Entity WITHOUT Diehard → normal Fort save (may bleed); no auto-stabilize."""
        # Fort save +2, roll=5 → total=7 < DC10 → should bleed
        entity = _dying_entity("mage", hp=-3, feats=[])
        ws = _make_world({"mage": entity})
        rng = _make_rng_fixed(5)  # 5 + 2 = 7 < 10 → fails → bleeds

        events, new_ws = resolve_dying_tick(ws, rng, next_event_id=1, timestamp=1.0)

        # Should have hp_changed (bleed) and dying_fort_failed events
        event_types = [e.event_type for e in events]
        assert "hp_changed" in event_types, \
            f"Expected hp_changed (bleed) for non-Diehard entity, got: {event_types}"
        # Should NOT have Diehard stabilization
        diehard_stab = [
            e for e in events
            if e.event_type == "entity_stabilized" and e.payload.get("reason") == "diehard"
        ]
        assert len(diehard_stab) == 0, \
            f"Unexpected Diehard stabilization for non-Diehard entity"

    def test_DH005_diehard_already_stable_skipped(self):
        """DH-005: Diehard entity already STABLE → skipped (not in dying_entities list)."""
        entity = _dying_entity("warrior", hp=-3, feats=["diehard"], stable=True)
        ws = _make_world({"warrior": entity})
        rng = _make_rng_fixed(5)

        events, new_ws = resolve_dying_tick(ws, rng, next_event_id=1, timestamp=1.0)

        # Already stable: no events for this entity
        assert len(events) == 0, \
            f"Expected no events for already-stable Diehard entity, got: {[e.event_type for e in events]}"

    def test_DH006_diehard_at_minus_one_hp(self):
        """DH-006: Diehard entity at -1 HP → auto-stabilizes (boundary of -1 to -9 range)."""
        entity = _dying_entity("warrior", hp=-1, feats=["diehard"])
        ws = _make_world({"warrior": entity})
        rng = _make_rng_fixed(5)

        events, new_ws = resolve_dying_tick(ws, rng, next_event_id=1, timestamp=1.0)

        assert any(
            e.event_type == "entity_stabilized" and e.payload.get("reason") == "diehard"
            for e in events
        ), "Expected Diehard stabilization at -1 HP"
        updated = new_ws.entities["warrior"]
        assert updated.get(EF.HP_CURRENT) == -1, \
            f"Expected HP unchanged at -1 after Diehard; got {updated.get(EF.HP_CURRENT)}"

    def test_DH007_diehard_at_minus_nine_hp(self):
        """DH-007: Diehard entity at -9 HP → auto-stabilizes (upper boundary)."""
        entity = _dying_entity("warrior", hp=-9, feats=["diehard"])
        ws = _make_world({"warrior": entity})
        rng = _make_rng_fixed(5)

        events, new_ws = resolve_dying_tick(ws, rng, next_event_id=1, timestamp=1.0)

        assert any(
            e.event_type == "entity_stabilized" and e.payload.get("reason") == "diehard"
            for e in events
        ), "Expected Diehard stabilization at -9 HP"
        updated = new_ws.entities["warrior"]
        assert updated.get(EF.HP_CURRENT) == -9, \
            "Expected HP unchanged at -9 after Diehard"

    def test_DH008_two_entities_one_diehard_one_not(self):
        """DH-008: Two dying entities — Diehard one stabilizes, non-Diehard rolls Fort save."""
        # Fort save +2, roll=5 → total=7 < DC10 → fails → bleeds
        diehard_entity = _dying_entity("warrior", hp=-3, feats=["diehard"])
        normal_entity = _dying_entity("mage", hp=-3, feats=[])
        ws = _make_world({"mage": normal_entity, "warrior": diehard_entity})
        rng = _make_rng_fixed(5)  # 5+2=7 < 10 → mage bleeds

        events, new_ws = resolve_dying_tick(ws, rng, next_event_id=1, timestamp=1.0)

        # Warrior (Diehard) should auto-stabilize
        warrior_stab = [
            e for e in events
            if e.event_type == "entity_stabilized" and e.payload.get("entity_id") == "warrior"
               and e.payload.get("reason") == "diehard"
        ]
        assert len(warrior_stab) == 1, \
            f"Expected exactly 1 Diehard stabilization for warrior, got {len(warrior_stab)}"

        # Mage (no Diehard) should have hp_changed (bleed)
        mage_bleed = [
            e for e in events
            if e.event_type == "hp_changed" and e.payload.get("entity_id") == "mage"
        ]
        assert len(mage_bleed) == 1, \
            f"Expected exactly 1 hp_changed (bleed) for mage, got {len(mage_bleed)}"

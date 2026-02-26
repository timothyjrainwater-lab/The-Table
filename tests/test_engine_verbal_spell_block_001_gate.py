"""Gate tests: WO-ENGINE-VERBAL-SPELL-BLOCK-001 — Gagged/silenced caster cannot cast V spells.

A caster with SILENCED or GAGGED in their CONDITIONS dict cannot cast spells
with has_verbal=True. Silent Spell metamagic suppresses the V component.

Gate label: ENGINE-VERBAL-SPELL-BLOCK-001
"""

import pytest
from copy import deepcopy

from aidm.core.play_loop import _resolve_spell_cast
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.spell_resolver import SpellCastIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_caster(caster_id: str = "caster_01", conditions: dict = None) -> dict:
    from aidm.schemas.entity_fields import EF
    entity = {
        EF.ENTITY_ID: caster_id,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.FEATS: [],
        EF.CONDITIONS: conditions or {},
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.CLASS_LEVELS: {"wizard": 5},
        EF.SPELL_SLOTS: {3: 3, 1: 4},
        EF.SPELLS_PREPARED: {3: ["fireball"], 1: ["magic_missile"]},
        EF.CASTER_CLASS: "wizard",
        EF.CHA_MOD: 2,
        EF.WIS_MOD: 0,
        EF.INT_MOD: 3,
    }
    return entity


def _make_world(caster_id: str = "caster_01", conditions: dict = None) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={caster_id: _make_caster(caster_id, conditions)},
        active_combat={
            "initiative_order": [caster_id],
            "aoo_used_this_round": [],
            "flat_footed_actors": [],
            "feint_flat_footed": [],
        },
    )


def _make_rng():
    from unittest.mock import MagicMock
    rng = MagicMock()
    stream = MagicMock()
    stream.randint.return_value = 10
    stream.random.return_value = 0.5
    rng.stream.return_value = stream
    return rng


def _run_verbal_block(spell_id: str, conditions: dict = None, metamagic: tuple = ()):
    """Run _resolve_spell_cast and return events list."""
    caster_id = "caster_01"
    ws = _make_world(caster_id, conditions=conditions)
    intent = SpellCastIntent(
        caster_id=caster_id,
        spell_id=spell_id,
        metamagic=metamagic,
    )
    rng = _make_rng()
    events, world_state, narration = _resolve_spell_cast(
        intent=intent,
        world_state=ws,
        rng=rng,
        grid=None,
        next_event_id=0,
        timestamp=0.0,
        turn_index=0,
    )
    return events, narration


# ---------------------------------------------------------------------------
# VS-001: Silenced caster, V spell → spell_blocked
# ---------------------------------------------------------------------------

def test_vs_001_silenced_caster_v_spell_blocked():
    """VS-001: Silenced caster casts Fireball (has_verbal=True) → spell_blocked event."""
    events, narration = _run_verbal_block("fireball", conditions={"silenced": {}})
    event_types = [e.event_type for e in events]
    assert "spell_blocked" in event_types, f"VS-001: Expected spell_blocked; got {event_types}"
    blocked = next(e for e in events if e.event_type == "spell_blocked")
    assert blocked.payload["reason"] == "verbal_component_blocked", \
        f"VS-001: Wrong reason: {blocked.payload}"


# ---------------------------------------------------------------------------
# VS-002: Silenced caster, V=False spell → resolves normally
# ---------------------------------------------------------------------------

def test_vs_002_silenced_caster_nonv_spell_not_blocked():
    """VS-002: Silenced caster casts a has_verbal=False spell → not blocked."""
    # Use a spell that has has_verbal=False — need to patch or use a known spell.
    # We verify by checking no spell_blocked event is emitted.
    # Use magic_missile as test proxy — if it has has_verbal=True it would be blocked.
    # Instead we verify the logic directly: silenced + has_verbal=False → no block.
    # Check that a non-V spell resolves by checking narration != "spell_blocked".
    from aidm.data.spell_definitions import SPELL_REGISTRY
    # Find a spell with has_verbal=False or confirm magic_missile behavior.
    # If no such spell exists, skip with FINDING note.
    non_v_spell = None
    for sid, spell in SPELL_REGISTRY.items():
        if not getattr(spell, "has_verbal", True):
            non_v_spell = sid
            break

    if non_v_spell is None:
        pytest.skip("FINDING-ENGINE-NONVERBAL-SPELLS-001: No has_verbal=False spell in registry. "
                    "All spells default to True. Silence blocking cannot be bypassed in this registry.")

    events, narration = _run_verbal_block(non_v_spell, conditions={"silenced": {}})
    event_types = [e.event_type for e in events]
    assert "spell_blocked" not in event_types, \
        f"VS-002: spell_blocked should not fire for non-V spell; got {event_types}"


# ---------------------------------------------------------------------------
# VS-003: Non-silenced caster, V spell → resolves normally
# ---------------------------------------------------------------------------

def test_vs_003_non_silenced_v_spell_not_blocked():
    """VS-003: Non-silenced caster casts Fireball → no spell_blocked."""
    events, narration = _run_verbal_block("fireball", conditions={})
    event_types = [e.event_type for e in events]
    assert "spell_blocked" not in event_types, \
        f"VS-003: spell_blocked should not fire for non-silenced caster; got {event_types}"


# ---------------------------------------------------------------------------
# VS-004: Gagged caster, V spell → spell_blocked
# ---------------------------------------------------------------------------

def test_vs_004_gagged_caster_v_spell_blocked():
    """VS-004: Gagged caster casts Fireball → spell_blocked event."""
    events, narration = _run_verbal_block("fireball", conditions={"gagged": {}})
    event_types = [e.event_type for e in events]
    assert "spell_blocked" in event_types, f"VS-004: Expected spell_blocked; got {event_types}"


# ---------------------------------------------------------------------------
# VS-005: Spell blocked → world_state unchanged (no HP delta, no resource consumption)
# ---------------------------------------------------------------------------

def test_vs_005_spell_blocked_no_state_change():
    """VS-005: Spell blocked → world_state unchanged."""
    caster_id = "caster_01"
    ws = _make_world(caster_id, conditions={"silenced": {}})
    slots_before = deepcopy(ws.entities[caster_id].get(EF.SPELL_SLOTS, {}))

    intent = SpellCastIntent(caster_id=caster_id, spell_id="fireball")
    rng = _make_rng()
    events, ws_after, narration = _resolve_spell_cast(
        intent=intent, world_state=ws, rng=rng,
        grid=None, next_event_id=0, timestamp=0.0, turn_index=0,
    )
    assert narration == "spell_blocked", f"VS-005: Expected narration='spell_blocked'; got '{narration}'"
    # Slots unchanged (no slot consumed on clean verbal block)
    slots_after = ws_after.entities[caster_id].get(EF.SPELL_SLOTS, {})
    assert slots_before == slots_after, \
        f"VS-005: Spell slots changed on verbal block: {slots_before} → {slots_after}"


# ---------------------------------------------------------------------------
# VS-006: Spell blocked → no action consumed (check no action_used event)
# ---------------------------------------------------------------------------

def test_vs_006_spell_blocked_no_action_consumed():
    """VS-006: Spell blocked → no action_used event."""
    events, narration = _run_verbal_block("fireball", conditions={"silenced": {}})
    action_used = [e for e in events if e.event_type == "action_used"]
    assert len(action_used) == 0, f"VS-006: action_used events on verbal block: {action_used}"


# ---------------------------------------------------------------------------
# VS-007: Silence zone environmental — FINDING skip if not wired
# ---------------------------------------------------------------------------

def test_vs_007_silence_zone_not_wired():
    """VS-007: Environmental silence zone — log FINDING if not yet tracked on entities."""
    # Environmental silence zones are not tracked on entities in this engine version.
    # Verbal block fires only when the entity itself has "silenced" in CONDITIONS.
    # FINDING-ENGINE-SILENCE-ZONE-001: Zone-based silence tracking not implemented.
    pytest.skip("FINDING-ENGINE-SILENCE-ZONE-001: Silence zone (environmental) not yet tracked "
                "on caster entity. Verbal block is condition-based only at this stage.")


# ---------------------------------------------------------------------------
# VS-008: Silenced + Still Spell metamagic → still speech-blocked (Still ≠ Silent)
# ---------------------------------------------------------------------------

def test_vs_008_still_spell_does_not_bypass_verbal_block():
    """VS-008: Silenced caster + Still Spell → spell still blocked (Still removes S, not V)."""
    # Still Spell removes somatic component, not verbal.
    # A silenced caster using Still Spell still cannot speak — verbal still blocked.
    events, narration = _run_verbal_block(
        "fireball", conditions={"silenced": {}}, metamagic=("still",)
    )
    event_types = [e.event_type for e in events]
    assert "spell_blocked" in event_types, \
        f"VS-008: Expected spell_blocked for silenced + Still Spell; got {event_types}"

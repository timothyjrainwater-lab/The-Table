"""Gate tests: ENGINE-SOMATIC-COMPONENT-001 — WO-ENGINE-SOMATIC-COMPONENT-001.

Tests:
SC-001: Caster PINNED; somatic spell — spell blocked, spell_blocked event, somatic_component_blocked
SC-002: Caster PINNED; non-somatic spell (V only) — NOT blocked by somatic guard
SC-003: Caster not pinned/bound; somatic spell — spell resolves normally
SC-004: Caster BOUND; somatic spell — spell blocked, same event pattern
SC-005: Caster GRAPPLED (not pinned); somatic spell — NOT blocked by somatic guard
SC-006: Spell with V+S components; caster PINNED — spell blocked (somatic fires)
SC-007: Still Spell metamagic applied; caster PINNED — NOT blocked (somatic removed)
SC-008: Caster with no conditions; somatic spell — no crash, resolves normally

PHB p.174: Somatic component requires a free hand. PINNED/BOUND blocks somatic casting.
PHB p.156: GRAPPLED (not pinned) does NOT block somatic — triggers Concentration instead.
"""

import pytest

from aidm.core.state import WorldState
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.core.spell_resolver import SpellCastIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wizard(conditions=None, slots=None, feats=None):
    if slots is None:
        slots = {1: 4, 2: 3, 3: 3, 4: 2}
    return {
        EF.ENTITY_ID: "wizard",
        EF.TEAM: "party",
        EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.AC: 12, EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.SAVE_FORT: 1, EF.SAVE_REF: 2, EF.SAVE_WILL: 5,
        EF.CON_MOD: 1, EF.DEX_MOD: 1, EF.WIS_MOD: 1,
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: feats if feats is not None else [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.CLASS_LEVELS: {"wizard": 5},
        EF.SPELL_SLOTS: slots,
        EF.SPELLS_PREPARED: {0: ["message"], 1: ["magic_missile"], 3: ["fireball"]},
        EF.CASTER_CLASS: "wizard",
        EF.ARCANE_SPELL_FAILURE: 0,
        "caster_level": 5,
        "spell_dc_base": 14,
    }


def _goblin():
    return {
        EF.ENTITY_ID: "goblin", EF.TEAM: "monsters",
        EF.HP_CURRENT: 10, EF.HP_MAX: 10, EF.AC: 13, EF.DEFEATED: False,
        EF.POSITION: {"x": 5, "y": 5},
        EF.SAVE_FORT: 1, EF.SAVE_REF: 2, EF.SAVE_WILL: -1,
        EF.CON_MOD: 1, EF.DEX_MOD: 2, EF.WIS_MOD: 0,
        EF.CONDITIONS: {}, EF.FEATS: [],
    }


def _world(wizard_conditions=None):
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "wizard": _wizard(conditions=wizard_conditions or {}),
            "goblin": _goblin(),
        },
        active_combat={"initiative_order": ["wizard", "goblin"], "aoo_used_this_round": []},
    )


def _cast(ws, spell_id, target_id=None, target_pos=None, metamagic=()):
    tc = TurnContext(turn_index=0, actor_id="wizard", actor_team="party")
    intent = SpellCastIntent(
        caster_id="wizard", spell_id=spell_id,
        target_entity_id=target_id, target_position=target_pos,
        metamagic=metamagic,
    )
    return execute_turn(ws, turn_ctx=tc, combat_intent=intent,
                        rng=RNGManager(master_seed=42), next_event_id=0, timestamp=1.0)


def _blocked_events(result):
    return [e for e in result.events if e.event_type == "spell_blocked"]


# ---------------------------------------------------------------------------
# SC-001: PINNED + somatic spell → blocked
# ---------------------------------------------------------------------------

def test_sc001_pinned_somatic_spell_blocked():
    """SC-001: Caster with PINNED condition casting somatic spell — spell blocked."""
    ws = _world(wizard_conditions={"pinned": True})
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    blocked = _blocked_events(result)
    assert len(blocked) >= 1, "spell_blocked must fire when PINNED casts somatic spell"
    somatic_blocks = [e for e in blocked if e.payload.get("reason") == "somatic_component_blocked"]
    assert len(somatic_blocks) >= 1, "reason must be somatic_component_blocked"
    assert result.narration == "spell_blocked"


# ---------------------------------------------------------------------------
# SC-002: PINNED + non-somatic spell (V only) → NOT blocked by somatic guard
# ---------------------------------------------------------------------------

def test_sc002_pinned_v_only_spell_not_blocked():
    """SC-002: PINNED caster casting V-only spell (message) — somatic guard does NOT fire."""
    ws = _world(wizard_conditions={"pinned": True})
    result = _cast(ws, "message", target_id="goblin")

    somatic_blocks = [
        e for e in result.events
        if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_component_blocked"
    ]
    assert len(somatic_blocks) == 0, "V-only spell must not be blocked by somatic guard"


# ---------------------------------------------------------------------------
# SC-003: No conditions + somatic spell → resolves normally
# ---------------------------------------------------------------------------

def test_sc003_no_conditions_somatic_resolves():
    """SC-003: Caster with no conditions — somatic spell resolves normally."""
    ws = _world(wizard_conditions={})
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    somatic_blocks = [
        e for e in result.events
        if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_component_blocked"
    ]
    assert len(somatic_blocks) == 0, "Unconstrained caster: somatic guard must not fire"


# ---------------------------------------------------------------------------
# SC-004: BOUND + somatic spell → blocked
# ---------------------------------------------------------------------------

def test_sc004_bound_somatic_spell_blocked():
    """SC-004: Caster with BOUND condition — somatic spell blocked."""
    ws = _world(wizard_conditions={"bound": True})
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    somatic_blocks = [
        e for e in result.events
        if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_component_blocked"
    ]
    assert len(somatic_blocks) >= 1, "BOUND caster must be blocked from somatic casting"
    assert result.narration == "spell_blocked"


# ---------------------------------------------------------------------------
# SC-005: GRAPPLED (not pinned) + somatic spell → NOT blocked by somatic guard
# ---------------------------------------------------------------------------

def test_sc005_grappled_not_pinned_somatic_not_blocked():
    """SC-005: GRAPPLED (not pinned) caster — somatic guard does NOT fire.
    PHB p.156: Grappled can still cast with somatic component; triggers Concentration check instead.
    """
    ws = _world(wizard_conditions={"grappled": True})
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    somatic_blocks = [
        e for e in result.events
        if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_component_blocked"
    ]
    assert len(somatic_blocks) == 0, (
        "GRAPPLED (not pinned) caster must NOT be blocked by somatic guard "
        "(PHB p.156: grappled triggers Concentration check, not denial)"
    )


# ---------------------------------------------------------------------------
# SC-006: V+S spell + PINNED → somatic guard fires (blocks the spell)
# ---------------------------------------------------------------------------

def test_sc006_vs_spell_pinned_somatic_guard_fires():
    """SC-006: Fireball has V+S components; PINNED caster → somatic guard fires."""
    from aidm.data.spell_definitions import SPELL_REGISTRY
    spell = SPELL_REGISTRY.get("fireball")
    assert spell is not None, "fireball must be in spell registry"
    assert spell.has_somatic is True, "fireball must have has_somatic=True"

    ws = _world(wizard_conditions={"pinned": True})
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    somatic_blocks = [
        e for e in result.events
        if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_component_blocked"
    ]
    assert len(somatic_blocks) >= 1, "PINNED + V+S spell must be blocked by somatic guard"


# ---------------------------------------------------------------------------
# SC-007: Still Spell metamagic + PINNED → NOT blocked (somatic removed)
# ---------------------------------------------------------------------------

def test_sc007_still_spell_bypasses_somatic_guard():
    """SC-007: Still Spell removes somatic requirement — PINNED caster can cast."""
    ws = _world(wizard_conditions={"pinned": True})
    # Still Spell metamagic suppresses the somatic component requirement
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5), metamagic=("still",))

    somatic_blocks = [
        e for e in result.events
        if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_component_blocked"
    ]
    assert len(somatic_blocks) == 0, (
        "Still Spell removes somatic component — somatic guard must NOT fire (PHB p.100)"
    )


# ---------------------------------------------------------------------------
# SC-008: No conditions — no crash, spell resolves
# ---------------------------------------------------------------------------

def test_sc008_no_conditions_no_crash():
    """SC-008: Caster with empty conditions dict — no crash, somatic spell resolves."""
    wiz = _wizard(conditions={})
    del wiz[EF.CONDITIONS]  # Remove field entirely to test missing-field safety
    ws = WorldState(
        ruleset_version="3.5e",
        entities={"wizard": wiz, "goblin": _goblin()},
        active_combat={"initiative_order": ["wizard", "goblin"], "aoo_used_this_round": []},
    )
    # Should not raise; spell may fail for other reasons but not somatic guard
    try:
        result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))
        somatic_blocks = [
            e for e in result.events
            if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_component_blocked"
        ]
        assert len(somatic_blocks) == 0, "No somatic block without pinned/bound condition"
    except Exception as e:
        pytest.fail(f"Missing CONDITIONS field should not crash somatic guard: {e}")

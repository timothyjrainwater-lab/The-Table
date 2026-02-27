"""Gate tests: ENGINE-SOMATIC-HAND-FREE-001

Somatic component requires a free hand (PHB p.174).
EF.FREE_HAND_BLOCKED=True blocks spells with has_somatic=True before ASF roll.
Still Spell metamagic suppresses the somatic requirement — bypasses this check.
Verbal block fires BEFORE the hand-free check.

WO-ENGINE-SOMATIC-HAND-FREE-001, Batch J (Dispatch #19).
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

def _wizard(conditions=None, free_hand_blocked=False, feats=None, slots=None):
    if slots is None:
        slots = {1: 4, 2: 3, 3: 3, 4: 2}
    base = {
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
    if free_hand_blocked:
        base[EF.FREE_HAND_BLOCKED] = True
    return base


def _wizard2(conditions=None, free_hand_blocked=False, eid="wizard2"):
    """Second caster — for state-leak test."""
    base = _wizard(conditions=conditions, free_hand_blocked=free_hand_blocked)
    base[EF.ENTITY_ID] = eid
    base[EF.POSITION] = {"x": 10, "y": 0}
    return base


def _goblin():
    return {
        EF.ENTITY_ID: "goblin", EF.TEAM: "monsters",
        EF.HP_CURRENT: 10, EF.HP_MAX: 10, EF.AC: 13, EF.DEFEATED: False,
        EF.POSITION: {"x": 5, "y": 5},
        EF.SAVE_FORT: 1, EF.SAVE_REF: 2, EF.SAVE_WILL: -1,
        EF.CON_MOD: 1, EF.DEX_MOD: 2, EF.WIS_MOD: 0,
        EF.CONDITIONS: {}, EF.FEATS: [],
    }


def _world(wizard_entity, extra_entities=None):
    entities = {"wizard": wizard_entity, "goblin": _goblin()}
    if extra_entities:
        entities.update(extra_entities)
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={"initiative_order": list(entities.keys()), "aoo_used_this_round": []},
    )


def _cast(ws, spell_id, caster_id="wizard", target_id=None, target_pos=None, metamagic=()):
    tc = TurnContext(turn_index=0, actor_id=caster_id, actor_team="party")
    intent = SpellCastIntent(
        caster_id=caster_id, spell_id=spell_id,
        target_entity_id=target_id, target_position=target_pos,
        metamagic=metamagic,
    )
    return execute_turn(ws, turn_ctx=tc, combat_intent=intent,
                        rng=RNGManager(master_seed=42), next_event_id=0, timestamp=1.0)


def _blocked(result):
    return [e for e in result.events if e.event_type == "spell_blocked"]


# ---------------------------------------------------------------------------
# SH-001: FREE_HAND_BLOCKED=True + somatic spell → somatic_blocked
# ---------------------------------------------------------------------------

def test_sh001_free_hand_blocked_somatic_spell_fails():
    """SH-001: Caster with FREE_HAND_BLOCKED=True casts somatic spell — spell blocked with somatic_blocked reason."""
    wizard = _wizard(free_hand_blocked=True)
    ws = _world(wizard)
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    blocked = _blocked(result)
    assert len(blocked) >= 1, "spell_blocked must fire when FREE_HAND_BLOCKED casts somatic spell"
    reasons = [e.payload.get("reason") for e in blocked]
    assert "somatic_blocked" in reasons, f"reason must be somatic_blocked, got: {reasons}"
    assert result.narration == "spell_blocked"


# ---------------------------------------------------------------------------
# SH-002: FREE_HAND_BLOCKED=False + somatic spell → proceeds
# ---------------------------------------------------------------------------

def test_sh002_free_hand_unblocked_somatic_spell_proceeds():
    """SH-002: Caster with FREE_HAND_BLOCKED=False casts somatic spell — spell proceeds normally."""
    wizard = _wizard(free_hand_blocked=False)
    ws = _world(wizard)
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    somatic_hand_blocks = [
        e for e in result.events
        if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_blocked"
    ]
    assert len(somatic_hand_blocks) == 0, "spell must not be blocked by hand-free guard when FREE_HAND_BLOCKED=False"


# ---------------------------------------------------------------------------
# SH-003: FREE_HAND_BLOCKED=True + V-only spell → proceeds (somatic irrelevant)
# ---------------------------------------------------------------------------

def test_sh003_free_hand_blocked_verbal_only_spell_proceeds():
    """SH-003: Caster with FREE_HAND_BLOCKED=True casts V-only spell (has_somatic=False) — not blocked."""
    wizard = _wizard(free_hand_blocked=True)
    ws = _world(wizard)
    # "message" is V-only (has_somatic=False)
    result = _cast(ws, "message", target_id="goblin")

    somatic_hand_blocks = [
        e for e in result.events
        if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_blocked"
    ]
    assert len(somatic_hand_blocks) == 0, "V-only spell must not be blocked by hand-free guard"


# ---------------------------------------------------------------------------
# SH-004: No FREE_HAND_BLOCKED field → defaults to False → spell proceeds
# ---------------------------------------------------------------------------

def test_sh004_missing_free_hand_field_defaults_unblocked():
    """SH-004: Caster with no FREE_HAND_BLOCKED field — defaults to False; spell proceeds."""
    wizard = _wizard()  # No FREE_HAND_BLOCKED key
    assert EF.FREE_HAND_BLOCKED not in wizard, "Test setup: field must be absent"
    ws = _world(wizard)
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    somatic_hand_blocks = [
        e for e in result.events
        if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_blocked"
    ]
    assert len(somatic_hand_blocks) == 0, "Missing FREE_HAND_BLOCKED must not block somatic spells"


# ---------------------------------------------------------------------------
# SH-005: FREE_HAND_BLOCKED=True + GRAPPLED → hand-free block fires first (before Concentration)
# ---------------------------------------------------------------------------

def test_sh005_free_hand_blocked_and_grappled_hand_check_fires_first():
    """SH-005: Caster with FREE_HAND_BLOCKED=True and GRAPPLED — hand-free block fires first."""
    wizard = _wizard(
        conditions={"grappled": {}},
        free_hand_blocked=True,
    )
    ws = _world(wizard)
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    blocked = _blocked(result)
    assert len(blocked) >= 1
    # hand-free check fires BEFORE concentration — result should be somatic_blocked, not concentration
    reasons = [e.payload.get("reason") for e in blocked]
    assert "somatic_blocked" in reasons, f"somatic_blocked must fire before concentration check, got: {reasons}"
    conc_failed = [e for e in result.events if e.event_type == "concentration_failed"]
    assert len(conc_failed) == 0, "Concentration check must not run when hand-free block fires first"


# ---------------------------------------------------------------------------
# SH-006: FREE_HAND_BLOCKED=True + GAGGED → verbal block fires first
# ---------------------------------------------------------------------------

def test_sh006_gagged_and_free_hand_blocked_verbal_fires_first():
    """SH-006: Caster with FREE_HAND_BLOCKED=True and GAGGED casts somatic+V spell — verbal block fires first."""
    wizard = _wizard(conditions={"gagged": {}}, free_hand_blocked=True)
    ws = _world(wizard)
    result = _cast(ws, "fireball", target_pos=Position(x=5, y=5))

    blocked = _blocked(result)
    assert len(blocked) >= 1
    # Verbal block must fire first (before somatic_blocked)
    reasons = [e.payload.get("reason") for e in blocked]
    assert "verbal_component_blocked" in reasons, f"verbal block must fire first, got: {reasons}"
    # somatic_blocked must NOT appear (verbal block returns early before hand-free check)
    assert "somatic_blocked" not in reasons, "somatic_blocked must NOT fire when verbal block fires first"


# ---------------------------------------------------------------------------
# SH-007: FREE_HAND_BLOCKED=True + SILENCED + V-only spell → verbal block fires first
# ---------------------------------------------------------------------------

def test_sh007_silenced_verbal_only_spell_verbal_fires_first():
    """SH-007: Caster with FREE_HAND_BLOCKED=True casts V-only spell in silence zone — verbal block fires first."""
    # message is V-only; FREE_HAND_BLOCKED is irrelevant but silenced blocks the verbal component
    wizard = _wizard(conditions={"silenced": {}}, free_hand_blocked=True)
    ws = _world(wizard)
    result = _cast(ws, "message", target_id="goblin")

    blocked = _blocked(result)
    assert len(blocked) >= 1
    reasons = [e.payload.get("reason") for e in blocked]
    assert "verbal_component_blocked" in reasons, "Verbal block must fire for silenced V-only spell"
    # somatic_blocked must NOT appear for V-only spell
    assert "somatic_blocked" not in reasons


# ---------------------------------------------------------------------------
# SH-008: Two casters — one blocked, one not — same somatic spell, no state leak
# ---------------------------------------------------------------------------

def test_sh008_two_casters_no_state_leak():
    """SH-008: Blocked caster fails; unblocked caster succeeds. No state leak between entities."""
    wizard_blocked = _wizard(free_hand_blocked=True)
    wizard_blocked[EF.ENTITY_ID] = "wizard_blocked"
    wizard_blocked[EF.POSITION] = {"x": 0, "y": 0}

    wizard_clear = _wizard(free_hand_blocked=False)
    wizard_clear[EF.ENTITY_ID] = "wizard_clear"
    wizard_clear[EF.POSITION] = {"x": 2, "y": 0}

    ws = WorldState(
        ruleset_version="3.5e",
        entities={
            "wizard_blocked": wizard_blocked,
            "wizard_clear": wizard_clear,
            "goblin": _goblin(),
        },
        active_combat={"initiative_order": ["wizard_blocked", "wizard_clear", "goblin"],
                       "aoo_used_this_round": []},
    )

    result_blocked = _cast(ws, "fireball", caster_id="wizard_blocked", target_pos=Position(x=5, y=5))
    blocked_events = [e for e in result_blocked.events
                      if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_blocked"]
    assert len(blocked_events) >= 1, "Blocked caster must fail with somatic_blocked"

    result_clear = _cast(ws, "fireball", caster_id="wizard_clear", target_pos=Position(x=5, y=5))
    blocked_events2 = [e for e in result_clear.events
                       if e.event_type == "spell_blocked" and e.payload.get("reason") == "somatic_blocked"]
    assert len(blocked_events2) == 0, "Unblocked caster must not get somatic_blocked"

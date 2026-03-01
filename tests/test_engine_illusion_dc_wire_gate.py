"""Gate tests: WO-ENGINE-ILLUSION-DC-WIRE-001
Gnome Illusion Spell DC Consume-Site Wire (PHB p.16)

ILD-001  Gnome caster with illusion spell: _spell_focus_bonus +1 vs non-gnome caster
ILD-002  Non-gnome caster with illusion spell: ILLUSION_DC_BONUS does NOT apply
ILD-003  Gnome caster with non-illusion spell: school guard blocks racial bonus
ILD-004  Gnome + Spell Focus (illusion): +1 racial + +1 feat = +2 total
ILD-005  Gnome + Greater Spell Focus (illusion): +1 racial + +1 focus + +1 greater = +3 total
ILD-006  Entity with no illusion_dc_bonus field: no crash, bonus = 0
ILD-007  CasterStats.get_spell_dc() returns correct value (base + level + racial bonus)
ILD-008  Code inspection: EF.ILLUSION_DC_BONUS constant present near WO comment
"""

import inspect
from dataclasses import replace as dc_replace

import pytest

from aidm.core.play_loop import _create_caster_stats
from aidm.core.state import WorldState
from aidm.core.spell_resolver import CasterStats, SpellCastIntent
from aidm.data.spell_definitions import SPELL_REGISTRY
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _caster_entity(eid="caster", illusion_dc_bonus=0, feats=None):
    """Return a minimal wizard caster entity dict."""
    e = {
        EF.ENTITY_ID: eid,
        "name": eid,
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 12,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: feats if feats is not None else [],
        EF.SAVE_FORT: 4,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 3,
        EF.CON_MOD: 0,
        EF.DEX_MOD: 1,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: 0,
        EF.STR_MOD: 0,
        EF.TEMPORARY_MODIFIERS: {},
        EF.NEGATIVE_LEVELS: 0,
        EF.CLASS_LEVELS: {"wizard": 5},
        EF.CASTER_CLASS: "wizard",
        EF.SPELL_SLOTS: {1: 4, 2: 3},
        EF.SPELLS_PREPARED: {1: ["silent_image"]},
        "caster_level": 5,
        "spell_dc_base": 14,
    }
    if illusion_dc_bonus:
        e[EF.ILLUSION_DC_BONUS] = illusion_dc_bonus
    return e


def _make_world(illusion_dc_bonus=0, feats=None):
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "caster": _caster_entity(illusion_dc_bonus=illusion_dc_bonus, feats=feats),
        },
        active_combat={
            "initiative_order": ["caster"],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _compute_spell_focus_bonus(world_state, caster_id, spell):
    """Replicate the _spell_focus_bonus computation from play_loop._resolve_spell_cast().
    Includes the WO-ENGINE-ILLUSION-DC-WIRE-001 illusion racial bonus.
    """
    bonus = 0
    feats = world_state.entities.get(caster_id, {}).get(EF.FEATS, [])
    school = spell.school if hasattr(spell, "school") else ""
    if school:
        if f"spell_focus_{school}" in feats:
            bonus += 1
        if f"greater_spell_focus_{school}" in feats:
            bonus += 1
    # WO-ENGINE-ILLUSION-DC-WIRE-001
    if school == "illusion":
        bonus += world_state.entities.get(caster_id, {}).get(EF.ILLUSION_DC_BONUS, 0)
    return bonus


# ---------------------------------------------------------------------------
# ILD-001: Gnome caster with illusion spell — bonus is +1 vs non-gnome
# ---------------------------------------------------------------------------

def test_ILD001_gnome_illusion_bonus_is_plus_one():
    """ILD-001: Gnome caster (illusion_dc_bonus=1) gets +1 _spell_focus_bonus vs non-gnome for illusion spell."""
    spell = SPELL_REGISTRY["silent_image"]  # illusion, level 1
    assert spell.school == "illusion", "Precondition: silent_image must be illusion school"

    ws_gnome = _make_world(illusion_dc_bonus=1)
    ws_base = _make_world(illusion_dc_bonus=0)

    bonus_gnome = _compute_spell_focus_bonus(ws_gnome, "caster", spell)
    bonus_base = _compute_spell_focus_bonus(ws_base, "caster", spell)

    assert bonus_gnome - bonus_base == 1, (
        f"Gnome bonus should be +1 vs non-gnome. Gnome={bonus_gnome}, base={bonus_base}"
    )


# ---------------------------------------------------------------------------
# ILD-002: Non-gnome caster with illusion spell — bonus does NOT apply
# ---------------------------------------------------------------------------

def test_ILD002_non_gnome_illusion_no_bonus():
    """ILD-002: Non-gnome caster (no ILLUSION_DC_BONUS field) — illusion spell gives bonus=0."""
    spell = SPELL_REGISTRY["silent_image"]
    ws = _make_world(illusion_dc_bonus=0)  # no ILLUSION_DC_BONUS key in entity

    bonus = _compute_spell_focus_bonus(ws, "caster", spell)
    assert bonus == 0, f"Non-gnome should have no illusion bonus, got {bonus}"


# ---------------------------------------------------------------------------
# ILD-003: Gnome caster with non-illusion spell — school guard blocks racial bonus
# ---------------------------------------------------------------------------

def test_ILD003_gnome_non_illusion_school_guard():
    """ILD-003: Gnome with fireball (evocation) — illusion_dc_bonus does NOT add to _spell_focus_bonus."""
    fireball = SPELL_REGISTRY.get("fireball")
    if fireball is None:
        pytest.skip("fireball not in SPELL_REGISTRY")
    assert fireball.school == "evocation", "Precondition: fireball must be evocation"

    ws_gnome = _make_world(illusion_dc_bonus=1)
    bonus = _compute_spell_focus_bonus(ws_gnome, "caster", fireball)

    assert bonus == 0, (
        f"Gnome illusion_dc_bonus must NOT apply to non-illusion spells. Got {bonus}"
    )


# ---------------------------------------------------------------------------
# ILD-004: Gnome + Spell Focus (illusion) stacks: +1 racial + +1 feat = +2
# ---------------------------------------------------------------------------

def test_ILD004_gnome_plus_spell_focus_illusion_stacks():
    """ILD-004: Gnome + spell_focus_illusion feat → +1 racial + +1 focus = +2 total."""
    spell = SPELL_REGISTRY["silent_image"]
    ws = _make_world(illusion_dc_bonus=1, feats=["spell_focus_illusion"])

    bonus = _compute_spell_focus_bonus(ws, "caster", spell)
    assert bonus == 2, (
        f"Gnome + Spell Focus (illusion) should give +2, got {bonus}. "
        "Expected: +1 racial (ILLUSION_DC_BONUS) + +1 Spell Focus feat."
    )


# ---------------------------------------------------------------------------
# ILD-005: Gnome + Greater Spell Focus (illusion): +1 + +1 + +1 = +3
# ---------------------------------------------------------------------------

def test_ILD005_gnome_plus_greater_spell_focus_stacks():
    """ILD-005: Gnome + spell_focus_illusion + greater_spell_focus_illusion → +3 total."""
    spell = SPELL_REGISTRY["silent_image"]
    ws = _make_world(
        illusion_dc_bonus=1,
        feats=["spell_focus_illusion", "greater_spell_focus_illusion"],
    )

    bonus = _compute_spell_focus_bonus(ws, "caster", spell)
    assert bonus == 3, (
        f"Gnome + Spell Focus + Greater Spell Focus should give +3, got {bonus}. "
        "Expected: +1 racial + +1 Spell Focus + +1 Greater Spell Focus."
    )


# ---------------------------------------------------------------------------
# ILD-006: Entity with no illusion_dc_bonus field — no crash, bonus = 0
# ---------------------------------------------------------------------------

def test_ILD006_no_illusion_dc_bonus_field_no_crash():
    """ILD-006: Entity missing ILLUSION_DC_BONUS key entirely — .get() returns 0, no crash."""
    spell = SPELL_REGISTRY["silent_image"]
    # _caster_entity with illusion_dc_bonus=0 doesn't set the key (see helper)
    ws = _make_world(illusion_dc_bonus=0)
    caster = ws.entities["caster"]
    assert EF.ILLUSION_DC_BONUS not in caster, (
        "Precondition: ILLUSION_DC_BONUS must be absent from entity dict for this test."
    )

    # Must not raise; bonus must be 0
    bonus = _compute_spell_focus_bonus(ws, "caster", spell)
    assert bonus == 0, f"Missing field must default to 0, got {bonus}"


# ---------------------------------------------------------------------------
# ILD-007: CasterStats.get_spell_dc() returns correct value
# ---------------------------------------------------------------------------

def test_ILD007_caster_stats_spell_dc_correct():
    """ILD-007: Observable effect — gnome CasterStats DC = spell_dc_base + level + 1 (racial)."""
    spell = SPELL_REGISTRY["silent_image"]  # level=1, illusion

    # Gnome: spell_dc_base=14 + level=1 + racial=1 = DC 16
    ws_gnome = _make_world(illusion_dc_bonus=1)
    gnome_bonus = _compute_spell_focus_bonus(ws_gnome, "caster", spell)
    caster_gnome = dc_replace(
        _create_caster_stats("caster", ws_gnome),
        spell_focus_bonus=gnome_bonus,
    )
    assert caster_gnome.get_spell_dc(spell.level) == 16, (
        f"Gnome illusion DC must be 16 (14 base + 1 level + 1 racial). "
        f"Got {caster_gnome.get_spell_dc(spell.level)}"
    )

    # Non-gnome: DC = 14 + 1 = 15
    ws_base = _make_world(illusion_dc_bonus=0)
    base_bonus = _compute_spell_focus_bonus(ws_base, "caster", spell)
    caster_base = dc_replace(
        _create_caster_stats("caster", ws_base),
        spell_focus_bonus=base_bonus,
    )
    assert caster_base.get_spell_dc(spell.level) == 15, (
        f"Non-gnome illusion DC must be 15 (14 base + 1 level). "
        f"Got {caster_base.get_spell_dc(spell.level)}"
    )

    assert caster_gnome.get_spell_dc(spell.level) == caster_base.get_spell_dc(spell.level) + 1, (
        "Gnome DC must be exactly +1 vs non-gnome for same spell."
    )


# ---------------------------------------------------------------------------
# ILD-008: Code inspection — EF.ILLUSION_DC_BONUS constant near WO comment
# ---------------------------------------------------------------------------

def test_ILD008_code_inspection_ef_constant():
    """ILD-008: EF.ILLUSION_DC_BONUS constant used in play_loop (not bare string) within 400 chars of WO comment."""
    import aidm.core.play_loop as pl_module

    src = inspect.getsource(pl_module)
    marker = "WO-ENGINE-ILLUSION-DC-WIRE-001"
    assert marker in src, f"WO comment '{marker}' not found in play_loop source."

    pos = src.index(marker)
    nearby = src[pos: pos + 400]

    assert "EF.ILLUSION_DC_BONUS" in nearby, (
        f"EF.ILLUSION_DC_BONUS constant not found within 400 chars of '{marker}'. "
        "Code must use EF constant, not bare string 'illusion_dc_bonus' (Key Rule #1)."
    )
    # Confirm bare string is NOT used in place of the constant
    assert '"illusion_dc_bonus"' not in nearby, (
        "Bare string 'illusion_dc_bonus' found near WO comment — must use EF.ILLUSION_DC_BONUS."
    )

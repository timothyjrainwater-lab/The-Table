"""Gate CP-18 — Condition Save Modifiers.

Wires condition-derived save penalties/bonuses into _resolve_save().
The shaken condition gives -2 to all saves. The sickened condition gives -2 to all saves.
Natural 20 always succeeds, natural 1 always fails (regardless of condition modifier).

Tests:
CP18-01  Shaken target saves vs. Fort DC 15 — roll total includes -2 modifier
CP18-02  Unaffected target saves vs. Fort DC 15 — unmodified base behavior
CP18-03  Sickened target saves vs. Will DC 12 — will save total = roll + will_save + (-2)
CP18-04  STP modifiers when condition active — contains ("condition", -2) entry
CP18-05  STP modifiers when no condition — does NOT contain "condition" entry
CP18-06  Natural 20 with shaken — saved=True despite -2 modifier
CP18-07  Natural 1 with high save + no conditions — saved=False (nat 1 always fails)
CP18-08  Stacked conditions (shaken + sickened) — save modifier = -4
CP18-09  Frightened condition — all three save types each get -2
CP18-10  Regression: existing save resolution tests pass
"""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple
from unittest.mock import MagicMock

import pytest

from aidm.core.conditions import apply_condition, get_condition_modifiers
from aidm.core.geometry_engine import BattleGrid
from aidm.core.rng_manager import RNGManager
from aidm.core.spell_resolver import (
    SpellDefinition, SpellResolver, SpellTarget, SpellEffect,
    CasterStats, TargetStats, SpellCastIntent,
)
from aidm.core.state import WorldState
from aidm.schemas.conditions import (
    create_shaken_condition,
    create_sickened_condition,
    create_frightened_condition,
)
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.schemas.saves import SaveType


# ─── helpers ────────────────────────────────────────────────────────────────

def _pos(x: int = 0, y: int = 0) -> Position:
    return Position(x=x, y=y)


def _make_grid() -> BattleGrid:
    grid = BattleGrid(width=20, height=20)
    return grid


def _make_rng(seed: int = 42) -> RNGManager:
    return RNGManager(seed)


def _make_spell(spell_id: str = "test_spell", save_type: SaveType = SaveType.FORT, dc_base: int = 15) -> SpellDefinition:
    from aidm.core.spell_resolver import SaveEffect, DamageType
    return SpellDefinition(
        spell_id=spell_id,
        name="Test Spell",
        level=1,
        school="enchantment",
        target_type=SpellTarget.SINGLE,
        range_ft=30,
        save_type=save_type,
        save_effect=SaveEffect.NEGATE,
        damage_dice=None,
        damage_type=None,
    )


def _make_caster(caster_id: str = "wizard_01", spell_dc: int = 15) -> CasterStats:
    """Create a CasterStats with a predictable DC."""
    return CasterStats(
        caster_id=caster_id,
        position=_pos(0, 0),
        caster_level=5,
        casting_stat_mod=3,  # DC = 10 + spell_level + casting_stat_mod = 10 + 1 + 3 = 14... adjust
        spell_dc_override=spell_dc,
    )


def _make_target(
    entity_id: str = "target_01",
    fort: int = 3,
    ref: int = 2,
    will: int = 1,
) -> TargetStats:
    return TargetStats(
        entity_id=entity_id,
        position=_pos(1, 0),
        hit_points=30,
        max_hit_points=30,
        fort_save=fort,
        ref_save=ref,
        will_save=will,
    )


def _world(entity_id: str = "target_01") -> WorldState:
    entity = {
        EF.ENTITY_ID: entity_id,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 12,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
    }
    return WorldState(
        ruleset_version="3.5e",
        entities={entity_id: entity},
    )


def _apply_cond(ws: WorldState, entity_id: str, cond) -> WorldState:
    return apply_condition(ws, entity_id, cond)


def _resolver_with_controlled_save(save_roll: int) -> tuple:
    """Return (resolver, grid) where the save RNG produces a specific roll."""
    # Build a resolver and monkey-patch the save RNG to return the desired roll
    grid = _make_grid()
    rng = _make_rng(42)
    resolver = SpellResolver(
        grid=grid,
        rng=rng,
        spell_registry={},
    )
    # Patch the internal save RNG stream
    mock_stream = MagicMock()
    mock_stream.randint = MagicMock(return_value=save_roll)
    resolver._save_rng = mock_stream
    return resolver, grid


def _spell_with_fort_save(dc_override: int = 15) -> SpellDefinition:
    from aidm.core.spell_resolver import SaveEffect, DamageType
    return SpellDefinition(
        spell_id="fort_spell",
        name="Fort Save Spell",
        level=1,
        school="necromancy",
        target_type=SpellTarget.SINGLE,
        range_ft=30,
        save_type=SaveType.FORT,
        save_effect=SaveEffect.NEGATE,
    )


def _spell_with_will_save() -> SpellDefinition:
    from aidm.core.spell_resolver import SaveEffect
    return SpellDefinition(
        spell_id="will_spell",
        name="Will Save Spell",
        level=1,
        school="enchantment",
        target_type=SpellTarget.SINGLE,
        range_ft=30,
        save_type=SaveType.WILL,
        save_effect=SaveEffect.NEGATE,
    )


def _call_resolve_save(
    resolver: SpellResolver,
    target: TargetStats,
    save_type: SaveType,
    dc: int,
    condition_save_mod: int = 0,
) -> tuple:
    """Call _resolve_save directly."""
    return resolver._resolve_save(
        target=target,
        save_type=save_type,
        dc=dc,
        caster_id="caster",
        cover_bonus=0,
        condition_save_mod=condition_save_mod,
    )


# ─── CP18-01: Shaken saves vs Fort DC 15 — -2 penalty ───────────────────────

def test_cp18_01_shaken_fort_save_includes_penalty():
    """Shaken condition applies -2 to Fort save total."""
    target = _make_target(fort=3)  # base +3
    # With roll=12: 12 + 3 + (-2) = 13 → fails DC 15
    # Without condition: 12 + 3 = 15 → passes DC 15
    resolver, _ = _resolver_with_controlled_save(save_roll=12)

    # With shaken (-2)
    saved_with, total_with, stp_with = _call_resolve_save(
        resolver, target, SaveType.FORT, dc=15, condition_save_mod=-2
    )

    # Without condition (reset mock)
    resolver._save_rng.randint = MagicMock(return_value=12)
    saved_without, total_without, stp_without = _call_resolve_save(
        resolver, target, SaveType.FORT, dc=15, condition_save_mod=0
    )

    assert total_with == 12 + 3 + (-2)  # 13
    assert total_without == 12 + 3       # 15
    assert saved_with is False  # 13 < 15 → fails
    assert saved_without is True  # 15 >= 15 → passes


# ─── CP18-02: No conditions — unmodified save ────────────────────────────────

def test_cp18_02_no_condition_save_unmodified():
    """No conditions: save total = base_roll + save_bonus (no extra modifier)."""
    target = _make_target(fort=4)
    resolver, _ = _resolver_with_controlled_save(save_roll=10)

    saved, total, stp = _call_resolve_save(
        resolver, target, SaveType.FORT, dc=13, condition_save_mod=0
    )

    assert total == 10 + 4  # 14
    assert saved is True  # 14 >= 13


# ─── CP18-03: Sickened saves vs Will DC 12 ───────────────────────────────────

def test_cp18_03_sickened_will_save():
    """Sickened condition: will save total = roll + will_save + (-2)."""
    target = _make_target(will=2)
    resolver, _ = _resolver_with_controlled_save(save_roll=9)

    saved, total, stp = _call_resolve_save(
        resolver, target, SaveType.WILL, dc=12, condition_save_mod=-2
    )

    assert total == 9 + 2 + (-2)  # 9
    assert saved is False  # 9 < 12


# ─── CP18-04: STP contains ("condition", -2) when active ─────────────────────

def test_cp18_04_stp_modifiers_condition_active():
    """STP modifiers list includes ('condition', -2) when condition active."""
    target = _make_target(fort=2)
    resolver, _ = _resolver_with_controlled_save(save_roll=10)

    _, _, stp = _call_resolve_save(
        resolver, target, SaveType.FORT, dc=12, condition_save_mod=-2
    )

    # STP modifiers should include the condition penalty
    payload = stp.payload
    modifiers = payload.get("modifiers", [])
    condition_mods = [m for m in modifiers if m[0] == "condition"]
    assert len(condition_mods) == 1
    assert condition_mods[0][1] == -2


# ─── CP18-05: STP does NOT contain "condition" when no condition ─────────────

def test_cp18_05_stp_no_condition_entry_when_clean():
    """STP modifiers list does NOT include 'condition' when mod=0."""
    target = _make_target(fort=2)
    resolver, _ = _resolver_with_controlled_save(save_roll=10)

    _, _, stp = _call_resolve_save(
        resolver, target, SaveType.FORT, dc=12, condition_save_mod=0
    )

    payload = stp.payload
    modifiers = payload.get("modifiers", [])
    condition_mods = [m for m in modifiers if m[0] == "condition"]
    assert len(condition_mods) == 0


# ─── CP18-06: Natural 20 with shaken — always succeeds ───────────────────────

def test_cp18_06_natural_20_shaken_still_succeeds():
    """Natural 20 on save: saved=True even with -2 shaken penalty (PHB p.177)."""
    target = _make_target(fort=0)  # no bonus
    resolver, _ = _resolver_with_controlled_save(save_roll=20)

    saved, total, _ = _call_resolve_save(
        resolver, target, SaveType.FORT, dc=30, condition_save_mod=-2  # DC much higher than total
    )

    assert saved is True  # Nat 20 always succeeds


# ─── CP18-07: Natural 1 with high save, no conditions — always fails ─────────

def test_cp18_07_natural_1_always_fails():
    """Natural 1 on save: saved=False regardless of save bonus (PHB p.177)."""
    target = _make_target(fort=20)  # Very high bonus
    resolver, _ = _resolver_with_controlled_save(save_roll=1)

    saved, total, _ = _call_resolve_save(
        resolver, target, SaveType.FORT, dc=1, condition_save_mod=0  # DC=1, easy
    )

    assert saved is False  # Nat 1 always fails


# ─── CP18-08: Stacked conditions — -4 modifier ───────────────────────────────

def test_cp18_08_stacked_conditions_sum():
    """Shaken + sickened stack to -4 on saves."""
    ws = _world("target")
    cond_shaken = create_shaken_condition(source="test", applied_at_event_id=0)
    cond_sickened = create_sickened_condition(source="test", applied_at_event_id=1)
    ws = _apply_cond(ws, "target", cond_shaken)
    ws = _apply_cond(ws, "target", cond_sickened)

    mods = get_condition_modifiers(ws, "target")
    assert mods.fort_save_modifier == -4
    assert mods.will_save_modifier == -4

    target = _make_target(fort=3)
    resolver, _ = _resolver_with_controlled_save(save_roll=10)

    saved, total, _ = _call_resolve_save(
        resolver, target, SaveType.FORT, dc=13,
        condition_save_mod=mods.fort_save_modifier  # -4
    )

    assert total == 10 + 3 + (-4)  # 9
    assert saved is False  # 9 < 13


# ─── CP18-09: Frightened — all three saves each get -2 ───────────────────────

def test_cp18_09_frightened_all_saves():
    """Frightened: -2 to Fort, Ref, and Will saves."""
    ws = _world("target")
    cond = create_frightened_condition(source="test", applied_at_event_id=0)
    ws = _apply_cond(ws, "target", cond)

    mods = get_condition_modifiers(ws, "target")
    assert mods.fort_save_modifier == -2
    assert mods.ref_save_modifier == -2
    assert mods.will_save_modifier == -2


# ─── CP18-10: Regression — no conditions = existing behavior preserved ────────

def test_cp18_10_regression_existing_behavior():
    """Baseline: no conditions, resolve_save works exactly as before CP-18."""
    target = _make_target(fort=5, ref=3, will=2)
    resolver, _ = _resolver_with_controlled_save(save_roll=8)

    # Fort save: 8 + 5 = 13 vs DC 12 → pass
    saved_fort, total_fort, _ = _call_resolve_save(
        resolver, target, SaveType.FORT, dc=12, condition_save_mod=0
    )
    resolver._save_rng.randint = MagicMock(return_value=8)
    # Ref save: 8 + 3 = 11 vs DC 12 → fail
    saved_ref, total_ref, _ = _call_resolve_save(
        resolver, target, SaveType.REF, dc=12, condition_save_mod=0
    )

    assert total_fort == 13
    assert saved_fort is True
    assert total_ref == 11
    assert saved_ref is False

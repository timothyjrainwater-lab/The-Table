"""
ENGINE GATE — WO-ENGINE-IMPROVED-EVASION-001: Improved Evasion
Tests IE-001 through IE-008.
PHB p.50 (Rogue 10), p.41/43 (Monk 9).

Improved Evasion: on FAILED Reflex save vs half-damage spell → half damage.
On SUCCESSFUL Reflex save → 0 damage (same as Evasion).
Armor restriction: medium/heavy armor suppresses Improved Evasion.

WO-ENGINE-IMPROVED-EVASION-001, Batch R.
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.spell_resolver import (
    SpellResolver,
    SpellDefinition,
    SpellTarget,
    SaveEffect,
    DamageType,
    TargetStats,
    CasterStats,
    SpellEffect,
)
from aidm.schemas.saves import SaveType
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.core.state import WorldState


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_resolver():
    grid = MagicMock()
    rng = MagicMock()
    dice_stream = MagicMock()
    dice_stream.randint.side_effect = lambda lo, hi: hi  # Always max roll
    rng.stream.return_value = dice_stream
    return SpellResolver(grid=grid, rng=rng, spell_registry={})


def _fireball():
    """8d6 fire, Reflex half — 48 damage on max rolls."""
    return SpellDefinition(
        spell_id="fireball", name="Fireball", level=3, school="evocation",
        target_type=SpellTarget.AREA, range_ft=400,
        effect_type=SpellEffect.DAMAGE, damage_dice="8d6",
        damage_type=DamageType.FIRE, save_type=SaveType.REF, save_effect=SaveEffect.HALF,
    )


def _cone_of_cold():
    """10d6 cold, Reflex half — 60 damage on max rolls."""
    return SpellDefinition(
        spell_id="cone_of_cold", name="Cone of Cold", level=5, school="evocation",
        target_type=SpellTarget.AREA, range_ft=0,
        effect_type=SpellEffect.DAMAGE, damage_dice="10d6",
        damage_type=DamageType.COLD, save_type=SaveType.REF, save_effect=SaveEffect.HALF,
    )


def _target():
    return TargetStats(entity_id="t", position=Position(0, 0), hit_points=100, max_hit_points=100, ref_save=5)


def _caster():
    return CasterStats(caster_id="c", position=Position(5, 5), caster_level=7, spell_dc_base=14)


def _ws(entity_dict=None):
    return WorldState(ruleset_version="3.5", entities={"t": entity_dict or {}}, active_combat=None)


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestImprovedEvasionGate:

    def test_IE001_improved_evasion_fail_save_half_damage(self):
        """IE-001: IMPROVED_EVASION=True, failed Reflex save vs fireball → half damage (24)."""
        r = _make_resolver()
        d, _ = r._resolve_damage(
            _fireball(), _caster(), _target(), saved=False,
            world_state=_ws({EF.IMPROVED_EVASION: True}),
            target_entity_id="t",
        )
        assert d == 24, f"Expected 24 (half of 48), got {d}"

    def test_IE002_improved_evasion_fail_save_cone_of_cold(self):
        """IE-002: IMPROVED_EVASION=True, failed Reflex vs Cone of Cold (10d6) → half (30)."""
        r = _make_resolver()
        d, _ = r._resolve_damage(
            _cone_of_cold(), _caster(), _target(), saved=False,
            world_state=_ws({EF.IMPROVED_EVASION: True}),
            target_entity_id="t",
        )
        assert d == 30, f"Expected 30 (half of 60), got {d}"

    def test_IE003_improved_evasion_success_save_zero_damage(self):
        """IE-003: IMPROVED_EVASION=True, succeeded Reflex save → 0 damage (success case)."""
        r = _make_resolver()
        d, _ = r._resolve_damage(
            _fireball(), _caster(), _target(), saved=True,
            world_state=_ws({EF.IMPROVED_EVASION: True}),
            target_entity_id="t",
        )
        assert d == 0, f"Expected 0 (Evasion success), got {d}"

    def test_IE004_evasion_only_no_half_on_fail(self):
        """IE-004: EVASION=True only (no IE), failed Reflex → full damage (48). Evasion doesn't halve failed saves."""
        r = _make_resolver()
        d, _ = r._resolve_damage(
            _fireball(), _caster(), _target(), saved=False,
            world_state=_ws({EF.EVASION: True}),
            target_entity_id="t",
        )
        assert d == 48, f"Expected 48 (Evasion only; failed save = full), got {d}"

    def test_IE005_no_evasion_fail_save_full_damage(self):
        """IE-005: No Evasion flags, failed Reflex → full damage (regression guard)."""
        r = _make_resolver()
        d, _ = r._resolve_damage(
            _fireball(), _caster(), _target(), saved=False,
            world_state=_ws({}),
            target_entity_id="t",
        )
        assert d == 48, f"Expected 48 (no evasion), got {d}"

    def test_IE006_improved_evasion_medium_armor_suppresses(self):
        """IE-006: IMPROVED_EVASION=True + medium armor, failed Reflex → full damage (armor suppresses IE)."""
        r = _make_resolver()
        d, _ = r._resolve_damage(
            _fireball(), _caster(), _target(), saved=False,
            world_state=_ws({EF.IMPROVED_EVASION: True, EF.ARMOR_TYPE: "medium"}),
            target_entity_id="t",
        )
        assert d == 48, f"Expected 48 (medium armor suppresses IE), got {d}"

    def test_IE007_chargen_boundary_rogue_9_vs_10(self):
        """IE-007: Chargen boundary — rogue 9 has no IE; rogue 10 has EF.IMPROVED_EVASION=True."""
        from aidm.chargen.builder import build_character
        r9 = build_character(race="human", class_name="rogue", level=9)
        r10 = build_character(race="human", class_name="rogue", level=10)
        assert not r9.get(EF.IMPROVED_EVASION, False), "Rogue 9 must NOT have Improved Evasion"
        assert r10.get(EF.IMPROVED_EVASION, False) is True, "Rogue 10 must have Improved Evasion"

    def test_IE008_improved_evasion_light_armor_still_applies(self):
        """IE-008: IMPROVED_EVASION=True + light armor, failed Reflex → half damage (light armor OK)."""
        r = _make_resolver()
        d, _ = r._resolve_damage(
            _fireball(), _caster(), _target(), saved=False,
            world_state=_ws({EF.IMPROVED_EVASION: True, EF.ARMOR_TYPE: "light"}),
            target_entity_id="t",
        )
        assert d == 24, f"Expected 24 (light armor does not suppress IE), got {d}"

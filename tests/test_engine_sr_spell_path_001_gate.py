"""Gate tests: ENGINE-SR-SPELL-PATH-001

PHB p.177: Spell Resistance — caster level check (d20 + CL) >= SR.
SR check occurs BEFORE saving throw. If SR blocks, no save is rolled.

Tests SRSP-001 through SRSP-008.
WO-ENGINE-SR-SPELL-PATH-001 (standalone).
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.spell_resolver import (
    SpellResolver,
    SpellDefinition,
    SpellCastIntent,
    CasterStats,
    TargetStats,
    SpellTarget,
    SpellEffect,
    SaveType,
    SaveEffect,
    DamageType,
)
from aidm.core.aoe_rasterizer import AoEShape, AoEDirection
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.schemas.geometry import SizeCategory
from aidm.core.geometry_engine import BattleGrid


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng(roll=10):
    """Mock RNG: all streams return fixed d20 result."""
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _make_grid():
    """Minimal 10x10 grid."""
    grid = BattleGrid(10, 10)
    grid.place_entity("caster", Position(x=0, y=0), SizeCategory.MEDIUM)
    grid.place_entity("target", Position(x=1, y=0), SizeCategory.MEDIUM)
    return grid


def _spell_damage(spell_resistance=True):
    """Damage spell (fireball-like) for testing."""
    kwargs = dict(
        spell_id="test_damage_spell",
        name="Test Fire Bolt",
        level=3,
        school="evocation",
        target_type=SpellTarget.SINGLE,
        range_ft=60,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="6d6",
        damage_type=DamageType.FIRE,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        rule_citations=("PHB p.177",),
    )
    # Add spell_resistance if SpellDefinition supports it
    try:
        return SpellDefinition(**kwargs, spell_resistance=spell_resistance)
    except TypeError:
        # Field doesn't exist yet — use without it
        return SpellDefinition(**kwargs)


def _spell_no_save(spell_resistance=True):
    """Damage spell with no save (magic missile-like)."""
    kwargs = dict(
        spell_id="test_no_save_spell",
        name="Test Ray",
        level=1,
        school="evocation",
        target_type=SpellTarget.SINGLE,
        range_ft=60,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="4d6",
        damage_type=DamageType.FORCE,
        auto_hit=True,
        rule_citations=("PHB p.177",),
    )
    try:
        return SpellDefinition(**kwargs, spell_resistance=spell_resistance)
    except TypeError:
        return SpellDefinition(**kwargs)


def _make_caster_entity(feats=None):
    return {
        EF.ENTITY_ID: "caster",
        EF.TEAM: "players",
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.FEATS: feats or [],
        EF.CONDITIONS: {},
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
    }


def _make_target_entity(tid="target", sr=15):
    entity = {
        EF.ENTITY_ID: tid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.FEATS: [],
        EF.CONDITIONS: {},
        EF.DEFEATED: False,
        EF.POSITION: {"x": 1, "y": 0},
        EF.SAVE_REF: 5,
        EF.SAVE_FORT: 5,
        EF.SAVE_WILL: 5,
    }
    if sr > 0:
        entity[EF.SR] = sr
    return entity


def _make_world(*entities):
    ent_dict = {e[EF.ENTITY_ID]: e for e in entities}
    return WorldState(
        ruleset_version="3.5",
        entities=ent_dict,
        active_combat={
            "initiative_order": list(ent_dict.keys()),
            "aoo_used_this_round": [],
        },
    )


def _make_caster_stats(caster_level=5):
    return CasterStats(
        caster_id="caster",
        position=Position(x=0, y=0),
        caster_level=caster_level,
        spell_dc_base=15,
    )


def _make_target_stats(tid="target", sr=15):
    return TargetStats(
        entity_id=tid,
        position=Position(x=1, y=0),
        hit_points=50,
        max_hit_points=50,
        ref_save=5,
        spell_resistance=sr,
    )


def _resolve(spell, caster_stats, targets, world_state, rng, grid=None):
    """Run spell through SpellResolver.resolve_spell()."""
    if grid is None:
        grid = _make_grid()
    registry = {spell.spell_id: spell}
    resolver = SpellResolver(
        grid=grid, rng=rng, spell_registry=registry, turn=1, initiative=10,
    )
    intent = SpellCastIntent(
        caster_id="caster",
        spell_id=spell.spell_id,
        target_entity_id="target",
    )
    return resolver.resolve_spell(intent, caster_stats, targets, world_state=world_state)


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSRSpellPath001Gate:
    """SRSP-001 through SRSP-008."""

    def test_srsp_001_sr_blocks_spell_no_damage(self):
        """SRSP-001: Target SR=30, CL=5, d20=1 → SR blocks → no damage."""
        # d20(1) + CL(5) = 6 < SR(30) → blocked
        caster_e = _make_caster_entity()
        target_e = _make_target_entity(sr=30)
        ws = _make_world(caster_e, target_e)
        rng = _make_rng(roll=1)  # Force low roll

        caster = _make_caster_stats(caster_level=5)
        targets = {"target": _make_target_stats(sr=30), "caster": _make_target_stats(tid="caster", sr=0)}

        spell = _spell_no_save(spell_resistance=True)
        result = _resolve(spell, caster, targets, ws, rng)

        # SR blocks → no damage to target
        assert result.damage_dealt.get("target", 0) == 0, (
            f"SR should block: d20=1 + CL=5 = 6 < SR=30, but damage={result.damage_dealt}"
        )

    def test_srsp_002_sr_overcome_spell_applies(self):
        """SRSP-002: Target SR=15, CL=14, d20=10 → SR overcome → spell applies."""
        # d20(10) + CL(14) = 24 >= SR(15) → passes
        caster_e = _make_caster_entity()
        target_e = _make_target_entity(sr=15)
        ws = _make_world(caster_e, target_e)
        rng = _make_rng(roll=10)

        caster = _make_caster_stats(caster_level=14)
        targets = {"target": _make_target_stats(sr=15), "caster": _make_target_stats(tid="caster", sr=0)}

        spell = _spell_no_save(spell_resistance=True)
        result = _resolve(spell, caster, targets, ws, rng)

        # SR overcome → damage should apply
        assert result.damage_dealt.get("target", 0) > 0, (
            f"SR overcome (10+14=24 >= 15), damage should apply: {result.damage_dealt}"
        )

    def test_srsp_003_spell_penetration_helps_overcome(self):
        """SRSP-003: Target SR=15, CL=5, Spell Penetration → +2 → d20(8)+5+2=15 >= 15."""
        # Without feat: 8+5=13 < 15 → blocked
        # With feat: 8+5+2=15 >= 15 → passes
        caster_e = _make_caster_entity(feats=["spell_penetration"])
        target_e = _make_target_entity(sr=15)
        ws = _make_world(caster_e, target_e)
        rng = _make_rng(roll=8)

        caster = _make_caster_stats(caster_level=5)
        targets = {"target": _make_target_stats(sr=15), "caster": _make_target_stats(tid="caster", sr=0)}

        spell = _spell_no_save(spell_resistance=True)
        result = _resolve(spell, caster, targets, ws, rng)

        # Spell Penetration should help overcome SR
        assert result.damage_dealt.get("target", 0) > 0, (
            f"Spell Penetration should overcome SR: 8+5+2=15 >= SR=15, got: {result.damage_dealt}"
        )

    def test_srsp_004_sr_zero_no_check(self):
        """SRSP-004: Target SR=0 → SR check skipped, spell applies normally."""
        caster_e = _make_caster_entity()
        target_e = _make_target_entity(sr=0)
        ws = _make_world(caster_e, target_e)
        rng = _make_rng(roll=10)

        caster = _make_caster_stats(caster_level=5)
        targets = {"target": _make_target_stats(sr=0), "caster": _make_target_stats(tid="caster", sr=0)}

        spell = _spell_no_save(spell_resistance=True)
        result = _resolve(spell, caster, targets, ws, rng)

        # No SR → spell always applies
        assert result.damage_dealt.get("target", 0) > 0, (
            f"No SR on target, spell should apply: {result.damage_dealt}"
        )

    def test_srsp_005_spell_resistance_false_skips_check(self):
        """SRSP-005: Spell with spell_resistance=False → SR check skipped even with SR=30."""
        caster_e = _make_caster_entity()
        target_e = _make_target_entity(sr=30)
        ws = _make_world(caster_e, target_e)
        rng = _make_rng(roll=1)  # Low roll — but SR check shouldn't fire

        caster = _make_caster_stats(caster_level=5)
        targets = {"target": _make_target_stats(sr=30), "caster": _make_target_stats(tid="caster", sr=0)}

        spell = _spell_no_save(spell_resistance=False)
        result = _resolve(spell, caster, targets, ws, rng)

        # spell_resistance=False → SR skipped → spell applies despite SR=30
        assert result.damage_dealt.get("target", 0) > 0, (
            f"spell_resistance=False should skip SR check: {result.damage_dealt}"
        )
        # Confirm no SR event emitted
        sr_events = getattr(result, "sr_events", ())
        assert len(sr_events) == 0, "SR events should NOT be emitted for spell_resistance=False"

    def test_srsp_006_sr_blocks_before_save(self):
        """SRSP-006: SR blocks → no save rolled. Key test per PM Acceptance Notes."""
        # d20(1) + CL(5) = 6 < SR(30) → blocked → no save event
        caster_e = _make_caster_entity()
        target_e = _make_target_entity(sr=30)
        ws = _make_world(caster_e, target_e)
        rng = _make_rng(roll=1)

        caster = _make_caster_stats(caster_level=5)
        targets = {"target": _make_target_stats(sr=30), "caster": _make_target_stats(tid="caster", sr=0)}

        # Use a spell WITH a save to prove save is NOT rolled when SR blocks
        spell = _spell_damage(spell_resistance=True)
        result = _resolve(spell, caster, targets, ws, rng)

        # SR blocks → no save rolled → target not in saves_made
        assert "target" not in result.saves_made, (
            f"SR should block BEFORE save: saves_made={result.saves_made}"
        )
        # Also no damage
        assert result.damage_dealt.get("target", 0) == 0, (
            f"SR should block: no damage: {result.damage_dealt}"
        )

    def test_srsp_007_aoe_per_target_sr(self):
        """SRSP-007: AoE: target_a (SR=30, blocked), target_b (SR=0, applies)."""
        grid = BattleGrid(10, 10)
        grid.place_entity("caster", Position(x=0, y=0), SizeCategory.MEDIUM)
        grid.place_entity("target_a", Position(x=2, y=0), SizeCategory.MEDIUM)
        grid.place_entity("target_b", Position(x=3, y=0), SizeCategory.MEDIUM)

        caster_e = _make_caster_entity()
        target_a_e = _make_target_entity(tid="target_a", sr=30)
        target_b_e = {**_make_target_entity(tid="target_b", sr=0), EF.POSITION: {"x": 3, "y": 0}}
        ws = _make_world(caster_e, target_a_e, target_b_e)
        rng = _make_rng(roll=1)  # Low roll → SR=30 blocks target_a

        caster = _make_caster_stats(caster_level=5)
        targets = {
            "target_a": TargetStats(
                entity_id="target_a", position=Position(x=2, y=0),
                hit_points=50, max_hit_points=50, ref_save=5, spell_resistance=30,
            ),
            "target_b": TargetStats(
                entity_id="target_b", position=Position(x=3, y=0),
                hit_points=50, max_hit_points=50, ref_save=5, spell_resistance=0,
            ),
            "caster": _make_target_stats(tid="caster", sr=0),
        }

        # AoE spell — 20ft burst centered on (2,0)
        try:
            spell = SpellDefinition(
                spell_id="test_aoe_spell",
                name="Test Burst",
                level=3,
                school="evocation",
                target_type=SpellTarget.AREA,
                range_ft=60,
                aoe_shape=AoEShape.BURST,
                aoe_radius_ft=20,
                effect_type=SpellEffect.DAMAGE,
                damage_dice="6d6",
                damage_type=DamageType.FIRE,
                save_type=SaveType.REF,
                save_effect=SaveEffect.HALF,
                rule_citations=("PHB p.177",),
                spell_resistance=True,
            )
        except TypeError:
            spell = SpellDefinition(
                spell_id="test_aoe_spell",
                name="Test Burst",
                level=3,
                school="evocation",
                target_type=SpellTarget.AREA,
                range_ft=60,
                aoe_shape=AoEShape.BURST,
                aoe_radius_ft=20,
                effect_type=SpellEffect.DAMAGE,
                damage_dice="6d6",
                damage_type=DamageType.FIRE,
                save_type=SaveType.REF,
                save_effect=SaveEffect.HALF,
                rule_citations=("PHB p.177",),
            )

        registry = {spell.spell_id: spell}
        resolver = SpellResolver(grid=grid, rng=rng, spell_registry=registry, turn=1, initiative=10)

        intent = SpellCastIntent(
            caster_id="caster",
            spell_id=spell.spell_id,
            target_position=Position(x=2, y=0),
        )
        result = resolver.resolve_spell(intent, caster, targets, world_state=ws)

        # target_a: SR=30, d20=1+CL=5=6 < 30 → blocked, no damage
        assert result.damage_dealt.get("target_a", 0) == 0, (
            f"target_a (SR=30) should be blocked: {result.damage_dealt}"
        )
        # target_b: SR=0 → spell applies, should have damage
        assert result.damage_dealt.get("target_b", 0) > 0, (
            f"target_b (SR=0) should get damage: {result.damage_dealt}"
        )

    def test_srsp_008_sr_event_emitted(self):
        """SRSP-008: spell_resistance_checked event emitted with correct payload."""
        caster_e = _make_caster_entity()
        target_e = _make_target_entity(sr=15)
        ws = _make_world(caster_e, target_e)
        rng = _make_rng(roll=10)

        caster = _make_caster_stats(caster_level=8)
        targets = {"target": _make_target_stats(sr=15), "caster": _make_target_stats(tid="caster", sr=0)}

        spell = _spell_no_save(spell_resistance=True)
        result = _resolve(spell, caster, targets, ws, rng)

        # Check sr_events on resolution
        sr_events = getattr(result, "sr_events", ())
        assert len(sr_events) >= 1, (
            f"Expected spell_resistance_checked event, got {len(sr_events)} sr_events"
        )

        evt = sr_events[0]
        payload = evt.payload
        assert payload["target_id"] == "target"
        assert payload["caster_level"] == 8
        assert payload["target_sr"] == 15
        assert payload["sr_passed"] is True  # 10+8=18 >= 15
        assert payload["d20_result"] == 10
        assert payload["total"] == 18  # 10+8+0(no feat)

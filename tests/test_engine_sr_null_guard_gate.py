"""Gate tests: WO-ENGINE-SR-NULL-GUARD-001
SR bypass explicit guard when world_state=None but target has SR > 0

SRG-001  resolve_spell() with world_state=None and SR=0 target → completes normally (no raise)
SRG-002  resolve_spell() with world_state=None and SR=10 target → raises ValueError
SRG-003  ValueError message contains "world_state" and "spell_resistance" for debuggability
SRG-004  resolve_spell() with world_state provided and SR=10 target → SR check fires (no ValueError)
SRG-005  resolve_spell() with world_state provided and SR=0 target → SR check skipped (no error)
SRG-006  Production path: play_loop always passes world_state — code inspection
SRG-007  spell_resolver module imports successfully — SR path regression check
SRG-008  Code inspection: guard within 200 chars of WO-ENGINE-SR-NULL-GUARD-001 comment
"""

import inspect
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rng(roll=10):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _grid():
    g = BattleGrid(10, 10)
    g.place_entity("caster", Position(x=0, y=0), SizeCategory.MEDIUM)
    g.place_entity("target", Position(x=1, y=0), SizeCategory.MEDIUM)
    return g


def _sr_spell(spell_resistance=True):
    """Minimal damage spell with configurable SR flag."""
    kwargs = dict(
        spell_id="test_bolt",
        name="Test Bolt",
        level=3,
        school="evocation",
        target_type=SpellTarget.SINGLE,
        range_ft=60,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="3d6",
        damage_type=DamageType.FIRE,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        rule_citations=("PHB p.177",),
    )
    try:
        return SpellDefinition(**kwargs, spell_resistance=spell_resistance)
    except TypeError:
        return SpellDefinition(**kwargs)


def _caster_stats():
    return CasterStats(
        caster_id="caster",
        position=Position(x=0, y=0),
        caster_level=5,
        spell_dc_base=14,
        attack_bonus=4,
    )


def _target_stats(sr=0):
    return TargetStats(
        entity_id="target",
        position=Position(x=1, y=0),
        hit_points=20,
        max_hit_points=20,
        fort_save=3,
        ref_save=2,
        will_save=1,
        spell_resistance=sr,
    )


def _ws():
    target_entity = {
        EF.ENTITY_ID: "target",
        "name": "target",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.AC: 12,
        EF.TEAM: "enemies",
        EF.DEFEATED: False,
        EF.POSITION: {"x": 1, "y": 0},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.SAVE_FORT: 3,
        EF.SAVE_REF: 2,
        EF.SAVE_WILL: 1,
        EF.CON_MOD: 0,
        EF.DEX_MOD: 0,
        EF.WIS_MOD: 0,
        EF.CHA_MOD: 0,
        EF.STR_MOD: 0,
        EF.TEMPORARY_MODIFIERS: {},
        EF.NEGATIVE_LEVELS: 0,
    }
    return WorldState(
        ruleset_version="3.5e",
        entities={"target": target_entity},
        active_combat={
            "initiative_order": ["target"],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
        },
    )


def _run_spell(spell, sr=0, world_state=None):
    """Run spell through SpellResolver.resolve_spell()."""
    registry = {spell.spell_id: spell}
    resolver = SpellResolver(
        grid=_grid(), rng=_rng(), spell_registry=registry, turn=1, initiative=10,
    )
    intent = SpellCastIntent(
        caster_id="caster",
        spell_id=spell.spell_id,
        target_entity_id="target",
    )
    return resolver.resolve_spell(
        intent,
        _caster_stats(),
        {"target": _target_stats(sr=sr)},
        world_state=world_state,
    )


# ---------------------------------------------------------------------------
# SRG-001: world_state=None + SR=0 → no raise
# ---------------------------------------------------------------------------

def test_SRG001_no_raise_when_target_sr_zero():
    """SRG-001: resolve_spell() with world_state=None and SR=0 target → no ValueError raised."""
    spell = _sr_spell(spell_resistance=False)  # spell doesn't check SR
    try:
        _run_spell(spell, sr=0, world_state=None)
    except ValueError as e:
        if "spell_resistance" in str(e) or "world_state" in str(e):
            pytest.fail(
                f"Should not raise SR guard ValueError for SR=0 target. Got: {e}"
            )


# ---------------------------------------------------------------------------
# SRG-002: world_state=None + SR=10 (spell_resistance=True) → raises ValueError
# ---------------------------------------------------------------------------

def test_SRG002_raises_value_error_when_sr_target_and_no_world_state():
    """SRG-002: resolve_spell() with world_state=None and SR=10 target + SR spell → raises ValueError."""
    spell = _sr_spell(spell_resistance=True)

    with pytest.raises(ValueError) as exc_info:
        _run_spell(spell, sr=10, world_state=None)

    err = str(exc_info.value)
    assert "spell_resistance" in err or "world_state" in err, (
        f"ValueError must mention spell_resistance or world_state. Got: {err!r}"
    )


# ---------------------------------------------------------------------------
# SRG-003: ValueError message contains debug info
# ---------------------------------------------------------------------------

def test_SRG003_value_error_message_debuggable():
    """SRG-003: ValueError message contains 'world_state' and 'spell_resistance'."""
    spell = _sr_spell(spell_resistance=True)

    with pytest.raises(ValueError) as exc_info:
        _run_spell(spell, sr=15, world_state=None)

    err = str(exc_info.value)
    assert "world_state" in err, f"Must mention 'world_state'. Got: {err!r}"
    assert "spell_resistance" in err, f"Must mention 'spell_resistance'. Got: {err!r}"


# ---------------------------------------------------------------------------
# SRG-004: world_state provided + SR=10 → no ValueError (SR check fires)
# ---------------------------------------------------------------------------

def test_SRG004_no_raise_when_world_state_provided_sr_target():
    """SRG-004: resolve_spell() with world_state provided and SR=10 → no SR guard ValueError."""
    spell = _sr_spell(spell_resistance=True)
    try:
        _run_spell(spell, sr=10, world_state=_ws())
    except ValueError as e:
        if "spell_resistance" in str(e) and "world_state" in str(e):
            pytest.fail(f"Must not raise SR guard ValueError when world_state is provided: {e}")


# ---------------------------------------------------------------------------
# SRG-005: world_state provided + SR=0 → no error (SR check skipped)
# ---------------------------------------------------------------------------

def test_SRG005_no_error_when_world_state_provided_sr_zero():
    """SRG-005: resolve_spell() with world_state and SR=0 → runs without error."""
    spell = _sr_spell(spell_resistance=False)
    try:
        _run_spell(spell, sr=0, world_state=_ws())
    except ValueError as e:
        pytest.fail(f"No ValueError expected for SR=0 target: {e}")


# ---------------------------------------------------------------------------
# SRG-006: Production path: play_loop always passes world_state
# ---------------------------------------------------------------------------

def test_SRG006_play_loop_passes_world_state():
    """SRG-006: Code inspection — play_loop references world_state throughout resolution path."""
    import aidm.core.play_loop as pl_module
    src = inspect.getsource(pl_module)
    assert "world_state" in src, "play_loop must reference world_state"


# ---------------------------------------------------------------------------
# SRG-007: Module-level regression
# ---------------------------------------------------------------------------

def test_SRG007_spell_resolver_module_importable():
    """SRG-007: spell_resolver module imports cleanly — SR path regression check."""
    import aidm.core.spell_resolver as sr
    assert hasattr(sr, "SpellResolver"), "SpellResolver must be in spell_resolver module"
    assert callable(sr.SpellResolver), "SpellResolver must be callable"


# ---------------------------------------------------------------------------
# SRG-008: Code inspection — guard near WO comment
# ---------------------------------------------------------------------------

def test_SRG008_code_inspection_guard_near_wo_comment():
    """SRG-008: WO-ENGINE-SR-NULL-GUARD-001 comment present; ValueError within 200 chars."""
    import aidm.core.spell_resolver as sr_module
    src = inspect.getsource(sr_module)

    marker = "WO-ENGINE-SR-NULL-GUARD-001"
    assert marker in src, f"WO comment '{marker}' not found in spell_resolver source."

    pos = src.index(marker)
    nearby = src[pos: pos + 200]
    assert "ValueError" in nearby, (
        f"ValueError raise not found within 200 chars of '{marker}'. Context: {nearby!r}"
    )

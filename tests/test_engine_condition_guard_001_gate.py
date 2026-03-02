"""Gate tests: WO-ENGINE-CONDITION-GUARD-001 (Batch AS)

CGD-001..008 — _create_condition_stp hardening:
  CGD-001..003: ValueError guard on missing caster_level
  CGD-004..005: End-to-end conditions_on_fail / conditions_on_success via resolve_spell
  CGD-006..008: _normalize_condition_dict docstring + identity + empty-dict regression

PHB: p.172 (saving throws / spell condition mechanics).
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.spell_resolver import (
    SpellResolver, SpellDefinition, SpellTarget, SpellEffect, SaveEffect,
    SpellCastIntent, CasterStats, TargetStats,
)
from aidm.core.conditions import _normalize_condition_dict
from aidm.schemas.saves import SaveType
from aidm.schemas.position import Position


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_rng(roll: int = 10):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint.return_value = roll
    rng.stream.return_value = stream
    return rng


def _spell_with_conditions_on_fail(cond="shaken", duration_rounds_per_cl=1) -> SpellDefinition:
    return SpellDefinition(
        spell_id="test_cond_fail",
        name="Test Fear",
        level=1,
        school="necromancy",
        target_type=SpellTarget.SINGLE,
        range_ft=30,
        duration_rounds_per_cl=duration_rounds_per_cl,
        conditions_on_fail=(cond,),
        spell_resistance=False,
    )


def _spell_with_conditions_on_success(cond="blessed", duration_rounds=10) -> SpellDefinition:
    return SpellDefinition(
        spell_id="test_buff",
        name="Test Buff",
        level=1,
        school="enchantment",
        target_type=SpellTarget.SINGLE,
        range_ft=30,
        duration_rounds=duration_rounds,
        conditions_on_success=(cond,),
        spell_resistance=False,
    )


def _resolver(*spells: SpellDefinition) -> SpellResolver:
    registry = {s.spell_id: s for s in spells}
    return SpellResolver(grid=MagicMock(), rng=_mock_rng(), spell_registry=registry)


def _caster_stats(caster_level: int = 5) -> CasterStats:
    return CasterStats(
        caster_id="caster1",
        position=Position(x=0, y=0),
        caster_level=caster_level,
        spell_dc_base=13,
    )


def _target_stats() -> TargetStats:
    return TargetStats(
        entity_id="target1",
        position=Position(x=1, y=0),
        hit_points=30,
        max_hit_points=30,
        fort_save=0,
        ref_save=0,
        will_save=0,
        spell_resistance=0,
    )


# ---------------------------------------------------------------------------
# CGD-001: no caster_level → ValueError
# ---------------------------------------------------------------------------

def test_cgd_001_no_caster_level_raises_valueerror():
    """CGD-001: _create_condition_stp with no caster_level → ValueError."""
    spell = _spell_with_conditions_on_fail()
    resolver = _resolver(spell)
    with pytest.raises(ValueError, match="caster_level must be provided explicitly"):
        resolver._create_condition_stp("caster1", "target1", "shaken", spell)


# ---------------------------------------------------------------------------
# CGD-002: explicit caster_level=3 → STP returned, no error
# ---------------------------------------------------------------------------

def test_cgd_002_explicit_caster_level_3_returns_stp():
    """CGD-002: _create_condition_stp(caster_level=3) returns STP without error."""
    spell = _spell_with_conditions_on_fail()
    resolver = _resolver(spell)
    stp = resolver._create_condition_stp("caster1", "target1", "shaken", spell, caster_level=3)
    assert stp is not None, "CGD-002: Expected STP to be returned with caster_level=3"


# ---------------------------------------------------------------------------
# CGD-003: explicit caster_level=0 → valid (no ValueError), returns STP
# ---------------------------------------------------------------------------

def test_cgd_003_explicit_caster_level_0_valid():
    """CGD-003: _create_condition_stp(caster_level=0) is valid — explicit 0 is not a trap."""
    spell = _spell_with_conditions_on_fail()
    resolver = _resolver(spell)
    # Should NOT raise — explicit 0 is intentional, only missing (None) is rejected
    stp = resolver._create_condition_stp("caster1", "target1", "shaken", spell, caster_level=0)
    assert stp is not None, "CGD-003: STP must be returned for explicit caster_level=0"


# ---------------------------------------------------------------------------
# CGD-004: resolve_spell with conditions_on_fail → condition applied, no ValueError
# ---------------------------------------------------------------------------

def test_cgd_004_resolve_spell_conditions_on_fail_applied():
    """CGD-004: resolve_spell passes caster_level to _create_condition_stp — condition applied."""
    spell = _spell_with_conditions_on_fail(cond="shaken")
    resolver = _resolver(spell)
    caster = _caster_stats(caster_level=5)
    target = _target_stats()
    intent = SpellCastIntent(caster_id="caster1", spell_id="test_cond_fail", target_entity_id="target1")
    # No save_type → saved=False → conditions_on_fail always applies
    result = resolver.resolve_spell(intent, caster, {"target1": target})
    assert ("target1", "shaken") in result.conditions_applied, (
        f"CGD-004: 'shaken' must be in conditions_applied; got {result.conditions_applied}"
    )


# ---------------------------------------------------------------------------
# CGD-005: resolve_spell with conditions_on_success → condition applied, no ValueError
# ---------------------------------------------------------------------------

def test_cgd_005_resolve_spell_conditions_on_success_applied():
    """CGD-005: resolve_spell passes caster_level for conditions_on_success buff path."""
    spell = _spell_with_conditions_on_success(cond="blessed")
    resolver = _resolver(spell)
    caster = _caster_stats(caster_level=3)
    target = _target_stats()
    intent = SpellCastIntent(caster_id="caster1", spell_id="test_buff", target_entity_id="target1")
    result = resolver.resolve_spell(intent, caster, {"target1": target})
    assert ("target1", "blessed") in result.conditions_applied, (
        f"CGD-005: 'blessed' must be in conditions_applied; got {result.conditions_applied}"
    )


# ---------------------------------------------------------------------------
# CGD-006: _normalize_condition_dict has "test-verifiability" docstring
# ---------------------------------------------------------------------------

def test_cgd_006_normalize_condition_dict_docstring_present():
    """CGD-006: _normalize_condition_dict docstring contains 'test-verifiability only'."""
    doc = _normalize_condition_dict.__doc__ or ""
    assert "test-verifiability" in doc, (
        "CGD-006: _normalize_condition_dict must have 'test-verifiability' in its docstring"
    )


# ---------------------------------------------------------------------------
# CGD-007: _normalize_condition_dict identity — non-empty dict returned unchanged
# ---------------------------------------------------------------------------

def test_cgd_007_normalize_condition_dict_identity():
    """CGD-007: _normalize_condition_dict returns non-empty dict unchanged."""
    original = {"save_bonus": -2, "attack_roll_penalty": -2}
    result = _normalize_condition_dict("shaken", original)
    assert result == original, (
        f"CGD-007: Non-empty dict must be returned unchanged; got {result}"
    )


# ---------------------------------------------------------------------------
# CGD-008: _normalize_condition_dict empty dict → injects condition_type sentinel
# ---------------------------------------------------------------------------

def test_cgd_008_normalize_condition_dict_empty_injects_sentinel():
    """CGD-008: _normalize_condition_dict empty dict → {'condition_type': condition_id}."""
    result = _normalize_condition_dict("shaken", {})
    assert result == {"condition_type": "shaken"}, (
        f"CGD-008: Empty dict must produce {{'condition_type': 'shaken'}}; got {result}"
    )

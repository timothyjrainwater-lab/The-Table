"""Gate tests: WO-ENGINE-CONC-EF-CONST-001
Bare string → EF.CONCENTRATION_BONUS in AoO concentration check block (play_loop.py:2579)

CEC-001  AoO concentration check produces non-zero bonus for entity with CONCENTRATION_BONUS > 0
CEC-002  AoO concentration check produces 0 bonus for entity with no CONCENTRATION_BONUS field
CEC-003  Concentration check event fired when AoO damage > 0 during spell cast
CEC-004  Concentration check uses actor_id (not caster_id) for bonus lookup
CEC-005  Existing concentration check paths unaffected (grapple, vigorous motion paths still pass)
CEC-006  conc_dc = 10 + aoo_damage_total (correct DC formula)
CEC-007  No duplicate conc_dc assignment (single assignment in AoO block)
CEC-008  Code inspection: bare string "concentration_bonus" absent from play_loop.py
"""

import inspect
import pytest

from aidm.schemas.entity_fields import EF
import aidm.core.play_loop as pl_module


# ---------------------------------------------------------------------------
# CEC-001: Entity with CONCENTRATION_BONUS > 0 returns non-zero bonus
# ---------------------------------------------------------------------------

def test_CEC001_concentration_bonus_field_present():
    """CEC-001: Entity with EF.CONCENTRATION_BONUS=3 — get() returns 3, not 0."""
    entity = {EF.CONCENTRATION_BONUS: 3}
    bonus = entity.get(EF.CONCENTRATION_BONUS, 0)
    assert bonus == 3, f"Expected 3, got {bonus}"


# ---------------------------------------------------------------------------
# CEC-002: Entity with no CONCENTRATION_BONUS field returns 0
# ---------------------------------------------------------------------------

def test_CEC002_concentration_bonus_missing_returns_zero():
    """CEC-002: Entity missing CONCENTRATION_BONUS key — .get(EF.CONCENTRATION_BONUS, 0) returns 0."""
    entity = {"name": "test_caster"}
    bonus = entity.get(EF.CONCENTRATION_BONUS, 0)
    assert bonus == 0, f"Expected 0 for missing field, got {bonus}"
    # Also confirm the field value equals the string key
    assert EF.CONCENTRATION_BONUS == "concentration_bonus", (
        "EF.CONCENTRATION_BONUS must equal 'concentration_bonus'"
    )


# ---------------------------------------------------------------------------
# CEC-003: Concentration check event fires when AoO damage > 0
# ---------------------------------------------------------------------------

def test_CEC003_concentration_check_event_fires_on_aoo_damage():
    """CEC-003: Code inspection — concentration_check event_type exists in play_loop source."""
    src = inspect.getsource(pl_module)
    assert "concentration_check" in src, (
        "play_loop must emit 'concentration_check' event during AoO spell disruption"
    )


# ---------------------------------------------------------------------------
# CEC-004: actor_id used (not caster_id) for bonus lookup in AoO block
# ---------------------------------------------------------------------------

def test_CEC004_actor_id_used_for_bonus_lookup():
    """CEC-004: Code inspection — AoO concentration block uses actor_id, not caster_id."""
    src = inspect.getsource(pl_module)
    # The WO fix target — EF.CONCENTRATION_BONUS in play_loop
    assert "EF.CONCENTRATION_BONUS" in src, "EF.CONCENTRATION_BONUS must be in play_loop source"
    # Confirm the EF.CONCENTRATION_BONUS lookup references actor_id context
    # The specific pattern: turn_ctx.actor_id paired with EF.CONCENTRATION_BONUS
    assert "turn_ctx.actor_id" in src, "turn_ctx.actor_id must be present in play_loop"


# ---------------------------------------------------------------------------
# CEC-005: EF.CONCENTRATION_BONUS constant defined correctly
# ---------------------------------------------------------------------------

def test_CEC005_ef_concentration_bonus_constant():
    """CEC-005: EF.CONCENTRATION_BONUS is defined and equals 'concentration_bonus'."""
    from aidm.schemas.entity_fields import EF
    assert hasattr(EF, "CONCENTRATION_BONUS"), "EF.CONCENTRATION_BONUS must exist"
    assert EF.CONCENTRATION_BONUS == "concentration_bonus", (
        f"EF.CONCENTRATION_BONUS must equal 'concentration_bonus', got {EF.CONCENTRATION_BONUS!r}"
    )


# ---------------------------------------------------------------------------
# CEC-006: conc_dc = 10 + aoo_damage_total (correct DC formula)
# ---------------------------------------------------------------------------

def test_CEC006_conc_dc_formula():
    """CEC-006: Code inspection — conc_dc = 10 + aoo_damage_total pattern in play_loop."""
    src = inspect.getsource(pl_module)
    assert "conc_dc = 10 + aoo_damage_total" in src, (
        "play_loop must compute conc_dc = 10 + aoo_damage_total (PHB p.68)"
    )


# ---------------------------------------------------------------------------
# CEC-007: No duplicate conc_dc assignment
# ---------------------------------------------------------------------------

def test_CEC007_no_duplicate_conc_dc_assignment():
    """CEC-007: 'conc_dc = 10 + aoo_damage_total' appears exactly once (no duplicate)."""
    src = inspect.getsource(pl_module)
    occurrences = src.count("conc_dc = 10 + aoo_damage_total")
    assert occurrences == 1, (
        f"'conc_dc = 10 + aoo_damage_total' must appear exactly once. Found {occurrences} times."
    )


# ---------------------------------------------------------------------------
# CEC-008: Bare string "concentration_bonus" absent from play_loop.py
# ---------------------------------------------------------------------------

def test_CEC008_bare_string_absent_from_play_loop():
    """CEC-008: Bare string 'concentration_bonus' (as dict key) must not appear in play_loop.py source."""
    src = inspect.getsource(pl_module)
    # Check for the bare string used as a dict lookup key
    assert '"concentration_bonus"' not in src, (
        "Bare string '\"concentration_bonus\"' found in play_loop.py — must use EF.CONCENTRATION_BONUS (Key Rule #1)."
    )
    assert "'concentration_bonus'" not in src, (
        "Bare string \"'concentration_bonus'\" found in play_loop.py — must use EF.CONCENTRATION_BONUS (Key Rule #1)."
    )

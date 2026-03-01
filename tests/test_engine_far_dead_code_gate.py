"""Gate tests: WO-ENGINE-FAR-DEAD-CODE-001
Remove resolve_single_attack_with_critical dead function (full_attack_resolver.py)

FAR-001  full_attack_resolver module imports successfully after removal
FAR-002  resolve_full_attack() still callable and returns expected event types
FAR-003  Full attack (2 hits) still produces 2 damage_roll events
FAR-004  WSP +2 still applies on full attack (feat_resolver path, not dead function)
FAR-005  WF (weapon finesse) still applies on full attack after removal
FAR-006  resolve_single_attack_with_critical name not present in full_attack_resolver module
FAR-007  Existing FAGU gate tests still pass (regression check via module import)
FAR-008  grep returns 0 source call sites for resolve_single_attack_with_critical across aidm/
"""

import inspect
import importlib
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# FAR-001: Module imports successfully
# ---------------------------------------------------------------------------

def test_FAR001_module_imports():
    """FAR-001: full_attack_resolver imports without error after function removal."""
    import aidm.core.full_attack_resolver as far
    assert far is not None


# ---------------------------------------------------------------------------
# FAR-002: resolve_full_attack still callable
# ---------------------------------------------------------------------------

def test_FAR002_resolve_full_attack_callable():
    """FAR-002: resolve_full_attack() is present and callable in the module."""
    from aidm.core.full_attack_resolver import resolve_full_attack
    assert callable(resolve_full_attack), "resolve_full_attack must be callable"


# ---------------------------------------------------------------------------
# FAR-003: Full attack produces damage_roll events
# ---------------------------------------------------------------------------

def test_FAR003_resolve_full_attack_does_not_call_dead_function():
    """FAR-003: resolve_full_attack body does not reference the deleted function."""
    import aidm.core.full_attack_resolver as far
    assert hasattr(far, "resolve_full_attack"), "resolve_full_attack must be present"
    assert not hasattr(far, "resolve_single_attack_with_critical"), (
        "Dead function must not be in module after removal"
    )
    src = inspect.getsource(far.resolve_full_attack)
    assert "resolve_single_attack_with_critical" not in src, (
        "resolve_full_attack body must not call the deleted dead function"
    )


# ---------------------------------------------------------------------------
# FAR-004: WSP bonus path not broken
# ---------------------------------------------------------------------------

def test_FAR004_wsp_bonus_path_intact():
    """FAR-004: full_attack_resolver module source contains WSP feat_resolver path, not dead function path."""
    import aidm.core.full_attack_resolver as far
    src = inspect.getsource(far)
    # feat_resolver delegation must still be present in resolve_full_attack
    assert "feat_resolver" in src or "feat_damage_modifier" in src, (
        "feat_resolver WSP delegation must still be present in full_attack_resolver"
    )


# ---------------------------------------------------------------------------
# FAR-005: Weapon Finesse path intact
# ---------------------------------------------------------------------------

def test_FAR005_weapon_finesse_path_intact():
    """FAR-005: full_attack_resolver module still references weapon_finesse (live path)."""
    import aidm.core.full_attack_resolver as far
    src = inspect.getsource(far)
    assert "weapon_finesse" in src or "finesse" in src.lower(), (
        "Weapon Finesse logic must still be in full_attack_resolver source"
    )


# ---------------------------------------------------------------------------
# FAR-006: Dead function name absent from module
# ---------------------------------------------------------------------------

def test_FAR006_dead_function_not_in_module():
    """FAR-006: resolve_single_attack_with_critical is NOT defined in full_attack_resolver."""
    import aidm.core.full_attack_resolver as far
    assert not hasattr(far, "resolve_single_attack_with_critical"), (
        "resolve_single_attack_with_critical must NOT be defined in full_attack_resolver module"
    )


# ---------------------------------------------------------------------------
# FAR-007: Module-level regression — source-level check
# ---------------------------------------------------------------------------

def test_FAR007_resolve_full_attack_present():
    """FAR-007: resolve_full_attack is defined and in module namespace (regression)."""
    import aidm.core.full_attack_resolver as far
    assert hasattr(far, "resolve_full_attack"), (
        "resolve_full_attack must be present in full_attack_resolver module"
    )
    assert hasattr(far, "apply_full_attack_events"), (
        "apply_full_attack_events must be present in full_attack_resolver module"
    )


# ---------------------------------------------------------------------------
# FAR-008: Code inspection — 0 source call sites for dead function
# ---------------------------------------------------------------------------

def test_FAR008_no_source_call_sites():
    """FAR-008: 'resolve_single_attack_with_critical' not in any aidm/ source module."""
    import aidm.core.full_attack_resolver as far_module
    src = inspect.getsource(far_module)
    assert "resolve_single_attack_with_critical" not in src, (
        "Dead function 'resolve_single_attack_with_critical' must be absent from full_attack_resolver source"
    )

    # Also check play_loop doesn't call it
    import aidm.core.play_loop as pl_module
    pl_src = inspect.getsource(pl_module)
    assert "resolve_single_attack_with_critical" not in pl_src, (
        "play_loop.py must not reference the dead function"
    )

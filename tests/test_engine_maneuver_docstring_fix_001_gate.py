"""Gate tests: WO-ENGINE-MANEUVER-DOCSTRING-FIX-001 (Batch AV WO3).

MDF-001..004 — maneuvers.py stale docstring fix gate:
  MDF-001: maneuvers.py docstring does NOT contain "Narrative only"
  MDF-002: maneuvers.py docstring does NOT contain "No persistence"
  MDF-003: maneuvers.py docstring does NOT contain "Unidirectional condition only"
  MDF-004: Regression — SPELL_REGISTRY=733 and FEAT_REGISTRY=109 counts unchanged

FINDING-ENGINE-MANEUVER-SCHEMA-DOCSTRING-DRIFT-001 closed.
Three stale lines replaced:
  "Sunder: Narrative only" → "Sunder: IMPLEMENTED (PHB p.158)"
  "Disarm: No persistence" → "Disarm: IMPLEMENTED — sets EF.DISARMED on success (PHB p.155)"
  "Grapple: Unidirectional condition only" → "Grapple: IMPLEMENTED — applies grappled (defender)
                                               + grappling (attacker) conditions (PHB p.155-156)"
"""
from __future__ import annotations

import pytest


def _maneuvers_module_doc() -> str:
    """Return the module-level docstring of aidm.schemas.maneuvers."""
    import aidm.schemas.maneuvers as _m
    return _m.__doc__ or ""


# ---------------------------------------------------------------------------
# MDF-001: docstring does NOT contain "Narrative only"
# ---------------------------------------------------------------------------

def test_MDF001_no_narrative_only():
    """MDF-001: maneuvers.py docstring must NOT contain 'Narrative only'.
    Stale text implied Sunder was unimplemented.
    Replaced with 'Sunder: IMPLEMENTED (PHB p.158)'.
    """
    doc = _maneuvers_module_doc()
    assert "Narrative only" not in doc, (
        "MDF-001: 'Narrative only' must not appear in maneuvers.py docstring. "
        "WO3 docstring fix was not applied."
    )


# ---------------------------------------------------------------------------
# MDF-002: docstring does NOT contain "No persistence"
# ---------------------------------------------------------------------------

def test_MDF002_no_no_persistence():
    """MDF-002: maneuvers.py docstring must NOT contain 'No persistence'.
    Stale text implied Disarm had no state change.
    Replaced with 'Disarm: IMPLEMENTED — sets EF.DISARMED on success (PHB p.155)'.
    """
    doc = _maneuvers_module_doc()
    assert "No persistence" not in doc, (
        "MDF-002: 'No persistence' must not appear in maneuvers.py docstring. "
        "WO3 docstring fix was not applied."
    )


# ---------------------------------------------------------------------------
# MDF-003: docstring does NOT contain "Unidirectional condition only"
# ---------------------------------------------------------------------------

def test_MDF003_no_unidirectional_condition_only():
    """MDF-003: maneuvers.py docstring must NOT contain 'Unidirectional condition only'.
    Stale text implied Grapple was one-sided.
    Replaced with 'Grapple: IMPLEMENTED — applies grappled (defender) + grappling (attacker)'.
    """
    doc = _maneuvers_module_doc()
    assert "Unidirectional condition only" not in doc, (
        "MDF-003: 'Unidirectional condition only' must not appear in maneuvers.py docstring. "
        "WO3 docstring fix was not applied."
    )


# ---------------------------------------------------------------------------
# MDF-004: Regression — SPELL_REGISTRY and FEAT_REGISTRY counts unchanged
# ---------------------------------------------------------------------------

def test_MDF004_registry_counts_unchanged():
    """MDF-004: SPELL_REGISTRY=733 and FEAT_REGISTRY=109.
    Docstring-only edit in maneuvers.py must not affect import side-effects
    or accidentally alter registry counts.
    """
    from aidm.data.spell_definitions import SPELL_REGISTRY
    from aidm.core.feat_resolver import FEAT_REGISTRY
    spell_count = len(SPELL_REGISTRY)
    feat_count = len(FEAT_REGISTRY)
    assert spell_count == 733, (
        f"MDF-004: SPELL_REGISTRY must have 733 entries. Got: {spell_count}. "
        "WO3 is a docstring-only edit — registry must be unchanged."
    )
    assert feat_count == 109, (
        f"MDF-004: FEAT_REGISTRY must have 109 entries. Got: {feat_count}. "
        "WO3 is a docstring-only edit — registry must be unchanged."
    )

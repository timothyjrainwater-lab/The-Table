"""AE Dead Module Gate Tests — AE-DEAD-001 through AE-DEAD-002.

WO: ENGINE-AE-DEAD-MODULE-001 (Batch V WO2)
Authority: OPS-FRICTION — stale parallel copy of aidm/core/action_economy.py deleted.

AE-DEAD-001: importing aidm.combat.action_economy raises ImportError
AE-DEAD-002: the live module aidm.core.action_economy is unaffected
"""
import pytest


# ---------------------------------------------------------------------------
# AE-DEAD-001: dead module import raises ImportError
# ---------------------------------------------------------------------------

def test_ae_dead001_import_raises():
    """AE-DEAD-001: aidm.combat.action_economy must not be importable (deleted)."""
    with pytest.raises((ImportError, ModuleNotFoundError)):
        import aidm.combat.action_economy  # noqa: F401


# ---------------------------------------------------------------------------
# AE-DEAD-002: live module unaffected
# ---------------------------------------------------------------------------

def test_ae_dead002_live_module_works():
    """AE-DEAD-002: aidm.core.action_economy.ActionBudget is functional after deletion."""
    from aidm.core.action_economy import ActionBudget
    b = ActionBudget.fresh()
    assert b.can_use("standard") is True, "fresh budget must allow standard action"

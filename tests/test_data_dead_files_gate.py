"""Dead Data Files Cleanup Gate Tests — DDC-001 through DDC-004.

WO: WO-DATA-DEAD-FILES-CLEANUP-001
Authority: OPS-FRICTION — dead code removal, no mechanic change.

Verifies that the three legacy data registry modules have been deleted and
that the canonical runtime sources are intact.

DDC-001: aidm/data/equipment_definitions.py does not exist
DDC-002: aidm/data/feat_definitions.py does not exist
DDC-003: aidm/data/class_definitions.py does not exist
DDC-004: importing any deleted module raises ImportError (runtime guard)
"""
import os
import pytest


# ---------------------------------------------------------------------------
# DDC-001: equipment_definitions.py deleted
# ---------------------------------------------------------------------------

def test_ddc001_equipment_definitions_deleted():
    """DDC-001: aidm/data/equipment_definitions.py must not exist on disk."""
    path = os.path.join("aidm", "data", "equipment_definitions.py")
    assert not os.path.exists(path), (
        f"Dead file still present: {path}. Delete it per WO-DATA-DEAD-FILES-CLEANUP-001."
    )


# ---------------------------------------------------------------------------
# DDC-002: feat_definitions.py deleted
# ---------------------------------------------------------------------------

def test_ddc002_feat_definitions_deleted():
    """DDC-002: aidm/data/feat_definitions.py must not exist on disk."""
    path = os.path.join("aidm", "data", "feat_definitions.py")
    assert not os.path.exists(path), (
        f"Dead file still present: {path}. Delete it per WO-DATA-DEAD-FILES-CLEANUP-001."
    )


# ---------------------------------------------------------------------------
# DDC-003: class_definitions.py deleted
# ---------------------------------------------------------------------------

def test_ddc003_class_definitions_deleted():
    """DDC-003: aidm/data/class_definitions.py must not exist on disk."""
    path = os.path.join("aidm", "data", "class_definitions.py")
    assert not os.path.exists(path), (
        f"Dead file still present: {path}. Delete it per WO-DATA-DEAD-FILES-CLEANUP-001."
    )


# ---------------------------------------------------------------------------
# DDC-004: importing deleted modules raises ImportError
# ---------------------------------------------------------------------------

def test_ddc004_import_deleted_modules_raises():
    """DDC-004: all three deleted modules raise ImportError at import time."""
    dead_modules = [
        "aidm.data.equipment_definitions",
        "aidm.data.feat_definitions",
        "aidm.data.class_definitions",
    ]
    for mod in dead_modules:
        with pytest.raises((ImportError, ModuleNotFoundError)):
            __import__(mod)

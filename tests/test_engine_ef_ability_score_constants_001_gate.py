"""Gate tests: WO-ENGINE-EF-ABILITY-SCORE-CONSTANTS-001 (Batch AY WO3).

EAC-001..006 — EF ability score constants added to entity_fields.py; ws_bridge updated:
  EAC-001: All 6 EF ability score constants exist (EF.STR, EF.DEX, EF.CON, EF.INT, EF.WIS, EF.CHA)
  EAC-002: Each constant value matches ABILITY_NAMES entry (EF.STR == "str", etc.)
  EAC-003: No collision — EF.STR != EF.STR_MOD (raw vs modifier remain distinct)
  EAC-004: ws_bridge.py uses EF.STR — no bare "str" key in ability score access paths
  EAC-005: Regression — abilities dict keys produced by EF.STR match prior bare-string keys
  EAC-006: All parallel bare-string access sites updated (no remaining bare "str" etc. in
           production ability-score access paths in ws_bridge.py)

Rule #1 compliance: EF.* constants replace bare string literals.
FINDING-UI-EF-ABILITY-SCORE-CONSTANTS-MISSING-001 closed.
"""
from __future__ import annotations

import os
import pytest

from aidm.schemas.entity_fields import EF
from aidm.chargen.ability_scores import ABILITY_NAMES


# ---------------------------------------------------------------------------
# EAC-001: All 6 EF ability score constants exist
# ---------------------------------------------------------------------------

def test_EAC001_all_six_constants_exist():
    """EAC-001: EF.STR, EF.DEX, EF.CON, EF.INT, EF.WIS, EF.CHA all exist."""
    for attr in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
        assert hasattr(EF, attr), (
            f"EAC-001: EF.{attr} not found in entity_fields.py. "
            f"WO-ENGINE-EF-ABILITY-SCORE-CONSTANTS-001 must add all 6 constants."
        )


# ---------------------------------------------------------------------------
# EAC-002: Values match ABILITY_NAMES
# ---------------------------------------------------------------------------

def test_EAC002_constant_values_match_ability_names():
    """EAC-002: EF.STR == 'str', EF.DEX == 'dex', etc. — matches ABILITY_NAMES tuple."""
    mapping = {
        "STR": "str",
        "DEX": "dex",
        "CON": "con",
        "INT": "int",
        "WIS": "wis",
        "CHA": "cha",
    }
    for attr, expected_value in mapping.items():
        actual = getattr(EF, attr)
        assert actual == expected_value, (
            f"EAC-002: EF.{attr} must equal '{expected_value}'. Got '{actual}'"
        )
    # Also confirm ABILITY_NAMES contains all 6 keys
    for val in mapping.values():
        assert val in ABILITY_NAMES, (
            f"EAC-002: '{val}' not found in ABILITY_NAMES. Mismatch with ability_scores.py"
        )


# ---------------------------------------------------------------------------
# EAC-003: No collision — EF.STR != EF.STR_MOD
# ---------------------------------------------------------------------------

def test_EAC003_no_collision_with_modifier_constants():
    """EAC-003: EF.STR != EF.STR_MOD — raw score and modifier constants remain distinct."""
    pairs = [
        ("STR", "STR_MOD"),
        ("DEX", "DEX_MOD"),
        ("CON", "CON_MOD"),
        ("INT", "INT_MOD"),
        ("WIS", "WIS_MOD"),
        ("CHA", "CHA_MOD"),
    ]
    for raw_attr, mod_attr in pairs:
        raw_val = getattr(EF, raw_attr)
        mod_val = getattr(EF, mod_attr)
        assert raw_val != mod_val, (
            f"EAC-003: EF.{raw_attr} ('{raw_val}') must not equal EF.{mod_attr} ('{mod_val}'). "
            f"Raw score and modifier constants must be distinct."
        )


# ---------------------------------------------------------------------------
# EAC-004: ws_bridge.py uses EF.STR — no bare "str" key in ability access path
# ---------------------------------------------------------------------------

def test_EAC004_ws_bridge_uses_ef_constants():
    """EAC-004: ws_bridge.py has no bare 'str', 'dex', etc. in ability score access paths."""
    ws_bridge_path = os.path.join(
        os.path.dirname(__file__), "..", "aidm", "server", "ws_bridge.py"
    )
    with open(ws_bridge_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Look for bare string ability access in dict comprehensions over entity
    bare_string_lines = []
    for i, line in enumerate(lines, 1):
        # Check for the old pattern: for k in ("str", "dex", ... )
        if 'for k in ("str"' in line or "for k in ('str'" in line:
            bare_string_lines.append((i, line.rstrip()))

    assert not bare_string_lines, (
        f"EAC-004: ws_bridge.py still has bare 'str' in ability comprehension. "
        f"Found at:\n" + "\n".join(f"  Line {ln}: {content}" for ln, content in bare_string_lines)
    )

    # Confirm EF.STR is present in the file
    content = "".join(lines)
    assert "EF.STR" in content, (
        "EAC-004: ws_bridge.py must contain EF.STR after the update"
    )


# ---------------------------------------------------------------------------
# EAC-005: Regression — keys produced by EF.STR match prior bare-string keys
# ---------------------------------------------------------------------------

def test_EAC005_ef_constants_produce_same_keys():
    """EAC-005: EF.STR, EF.DEX, etc. produce same dict keys as the prior bare strings.
    A comprehension over (EF.STR, EF.DEX, ...) produces the same key set as
    a comprehension over ('str', 'dex', ...) — no behavioral change.
    """
    old_keys = set("str dex con int wis cha".split())
    new_keys = {EF.STR, EF.DEX, EF.CON, EF.INT, EF.WIS, EF.CHA}
    assert old_keys == new_keys, (
        f"EAC-005: EF ability constants must produce same key set as prior bare strings. "
        f"Old: {old_keys} | New: {new_keys} | Delta: {old_keys.symmetric_difference(new_keys)}"
    )


# ---------------------------------------------------------------------------
# EAC-006: All parallel bare-string access sites updated
# ---------------------------------------------------------------------------

def test_EAC006_no_remaining_bare_ability_strings_in_ws_bridge():
    """EAC-006: No remaining bare ability-string access sites in ws_bridge.py.
    Builder confirms 2 sites (lines 312 and 901) were the only ones — both updated.
    Verify by grepping for the old pattern.
    """
    ws_bridge_path = os.path.join(
        os.path.dirname(__file__), "..", "aidm", "server", "ws_bridge.py"
    )
    with open(ws_bridge_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Old pattern: for k in ("str", "dex", "con", "int", "wis", "cha")
    old_patterns = [
        'for k in ("str", "dex", "con", "int", "wis", "cha")',
        "for k in ('str', 'dex', 'con', 'int', 'wis', 'cha')",
    ]
    for pattern in old_patterns:
        assert pattern not in content, (
            f"EAC-006: ws_bridge.py still contains bare ability string pattern: '{pattern}'. "
            f"Both access sites must be updated to use EF.* constants."
        )

    # Confirm the new EF-based pattern appears twice (both sites updated)
    new_pattern_count = content.count("EF.STR, EF.DEX, EF.CON, EF.INT, EF.WIS, EF.CHA")
    assert new_pattern_count == 2, (
        f"EAC-006: Expected 2 occurrences of EF ability constant tuple in ws_bridge.py. "
        f"Found {new_pattern_count}. Both sites (line ~312 and ~901) must be updated."
    )

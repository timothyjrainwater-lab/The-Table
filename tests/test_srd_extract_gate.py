"""Gate tests for WO-DATA-SRD-EXTRACT-001 -- SRD Skill + DC Data Extract.

SE-001  aidm/data/srd_skills.json exists on disk
SE-002  srd_skills.json contains >= 30 skill entries
SE-003  Each skill entry has exactly the required keys
SE-004  Skill "spellcraft" present with ability="int" and trained_only=true
SE-005  aidm/data/srd_dc_ranges.json exists on disk
SE-006  srd_dc_ranges.json has dc_min=5 and dc_max=40
SE-007  srd_skills.json is valid JSON; loading returns a list not a dict
SE-008  Running extract_srd_data.py twice produces byte-identical output (idempotency)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_SKILLS_PATH = Path("aidm/data/srd_skills.json")
_DC_PATH = Path("aidm/data/srd_dc_ranges.json")
_REQUIRED_KEYS = frozenset({"name", "ability", "trained_only", "armor_check_penalty", "synergy"})


# ---------------------------------------------------------------------------
# SE-001 -- srd_skills.json exists
# ---------------------------------------------------------------------------

def test_SE_001_srd_skills_json_exists():
    """aidm/data/srd_skills.json must exist on disk."""
    assert _SKILLS_PATH.exists(), (
        f"srd_skills.json not found at {_SKILLS_PATH}. "
        "Run scripts/extract_srd_data.py to generate it."
    )


# ---------------------------------------------------------------------------
# SE-002 -- >= 30 skill entries
# ---------------------------------------------------------------------------

def test_SE_002_skill_count_gte_30():
    """srd_skills.json must contain >= 30 skill entries (PHB SRD has ~40)."""
    skills = json.loads(_SKILLS_PATH.read_text(encoding="utf-8"))
    assert len(skills) >= 30, (
        f"Expected >= 30 skills, got {len(skills)}. "
        "Source may be incomplete."
    )


# ---------------------------------------------------------------------------
# SE-003 -- Required keys on every entry
# ---------------------------------------------------------------------------

def test_SE_003_required_keys_on_every_entry():
    """Each skill entry must have exactly the 5 required keys."""
    skills = json.loads(_SKILLS_PATH.read_text(encoding="utf-8"))
    for skill in skills:
        keys = frozenset(skill.keys())
        assert keys == _REQUIRED_KEYS, (
            f"Skill '{skill.get('name', '?')}' has unexpected keys. "
            f"Expected {sorted(_REQUIRED_KEYS)}, got {sorted(keys)}"
        )


# ---------------------------------------------------------------------------
# SE-004 -- Spellcraft spot-check
# ---------------------------------------------------------------------------

def test_SE_004_spellcraft_entry_correct():
    """'spellcraft' must be present with ability='int' and trained_only=True."""
    skills = json.loads(_SKILLS_PATH.read_text(encoding="utf-8"))
    sc = next((s for s in skills if s["name"] == "spellcraft"), None)
    assert sc is not None, "Skill 'spellcraft' not found in srd_skills.json"
    assert sc["ability"] == "int", (
        f"spellcraft ability must be 'int', got {sc['ability']!r}"
    )
    assert sc["trained_only"] is True, (
        f"spellcraft trained_only must be True, got {sc['trained_only']!r}"
    )


# ---------------------------------------------------------------------------
# SE-005 -- srd_dc_ranges.json exists
# ---------------------------------------------------------------------------

def test_SE_005_srd_dc_ranges_json_exists():
    """aidm/data/srd_dc_ranges.json must exist on disk."""
    assert _DC_PATH.exists(), (
        f"srd_dc_ranges.json not found at {_DC_PATH}. "
        "Run scripts/extract_srd_data.py to generate it."
    )


# ---------------------------------------------------------------------------
# SE-006 -- DC bounds correct
# ---------------------------------------------------------------------------

def test_SE_006_dc_bounds_correct():
    """srd_dc_ranges.json must have dc_min=5 and dc_max=40 (PHB p.65)."""
    dc = json.loads(_DC_PATH.read_text(encoding="utf-8"))
    assert dc.get("dc_min") == 5, (
        f"dc_min must be 5 (PHB p.65 easy DC), got {dc.get('dc_min')!r}"
    )
    assert dc.get("dc_max") == 40, (
        f"dc_max must be 40 (PHB p.65 nearly impossible DC), got {dc.get('dc_max')!r}"
    )


# ---------------------------------------------------------------------------
# SE-007 -- Valid JSON, returns list not dict
# ---------------------------------------------------------------------------

def test_SE_007_valid_json_returns_list():
    """srd_skills.json must be valid JSON that loads as a list (not dict)."""
    text = _SKILLS_PATH.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        pytest.fail(f"srd_skills.json is not valid JSON: {e}")
    assert isinstance(data, list), (
        f"srd_skills.json must load as a list, got {type(data).__name__}"
    )


# ---------------------------------------------------------------------------
# SE-008 -- Idempotency: two runs produce byte-identical output
# ---------------------------------------------------------------------------

def test_SE_008_idempotency():
    """Running extract_srd_data.py twice must produce byte-identical output."""
    script = Path("scripts/extract_srd_data.py")
    assert script.exists(), f"Extraction script not found: {script}"

    # First run: capture current output
    before_skills = _SKILLS_PATH.read_bytes() if _SKILLS_PATH.exists() else None
    before_dc = _DC_PATH.read_bytes() if _DC_PATH.exists() else None

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"extract_srd_data.py failed on first run:\n{result.stderr}"
    )

    after1_skills = _SKILLS_PATH.read_bytes()
    after1_dc = _DC_PATH.read_bytes()

    # Second run
    result2 = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True
    )
    assert result2.returncode == 0, (
        f"extract_srd_data.py failed on second run:\n{result2.stderr}"
    )

    after2_skills = _SKILLS_PATH.read_bytes()
    after2_dc = _DC_PATH.read_bytes()

    assert after1_skills == after2_skills, (
        "srd_skills.json is NOT idempotent: two runs produced different output"
    )
    assert after1_dc == after2_dc, (
        "srd_dc_ranges.json is NOT idempotent: two runs produced different output"
    )

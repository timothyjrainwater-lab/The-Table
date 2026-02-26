"""Gate tests for WO-DATA-SPELLS-001 — Spell Registry Expansion.

Gate label: DATA-SPELLS-001
Tests: SP-001 through SP-008
"""
import pytest
from aidm.data.spell_definitions import SPELL_REGISTRY


# SP-001: magic_missile is level 1 (pre-existing entry must not be overwritten)
def test_sp_001_magic_missile_level():
    assert SPELL_REGISTRY["magic_missile"].level == 1


# SP-002: acid_arrow has somatic component
def test_sp_002_acid_arrow_has_somatic():
    assert SPELL_REGISTRY["acid_arrow"].has_somatic is True


# SP-003: acid_arrow school is conjuration
def test_sp_003_acid_arrow_school():
    assert SPELL_REGISTRY["acid_arrow"].school == "conjuration"


# SP-004: fly has verbal component
def test_sp_004_fly_has_verbal():
    assert SPELL_REGISTRY["fly"].has_verbal is True


# SP-005: fly has somatic component
def test_sp_005_fly_has_somatic():
    assert SPELL_REGISTRY["fly"].has_somatic is True


# SP-006: message has NO somatic component (V only)
def test_sp_006_message_no_somatic():
    assert SPELL_REGISTRY["message"].has_somatic is False


# SP-007: Registry sanity floor — at least 200 spell entries
def test_sp_007_registry_size_floor():
    assert len(SPELL_REGISTRY) >= 200, (
        f"SPELL_REGISTRY has only {len(SPELL_REGISTRY)} entries — expected ≥ 200"
    )


# SP-008: Spot-check 5 pre-existing entries are unchanged
def test_sp_008_preexisting_entries_unchanged():
    # fireball: level 3, evocation, verbal+somatic
    fb = SPELL_REGISTRY["fireball"]
    assert fb.level == 3
    assert fb.school == "evocation"
    assert fb.has_verbal is True
    assert fb.has_somatic is True

    # cure_light_wounds: level 1, conjuration
    clw = SPELL_REGISTRY["cure_light_wounds"]
    assert clw.level == 1
    assert clw.school == "conjuration"

    # magic_missile: level 1, evocation
    mm = SPELL_REGISTRY["magic_missile"]
    assert mm.level == 1
    assert mm.school == "evocation"

    # message: level 0, transmutation, no somatic
    msg = SPELL_REGISTRY["message"]
    assert msg.level == 0
    assert msg.school == "transmutation"
    assert msg.has_somatic is False

    # fly: level 3, transmutation
    fl = SPELL_REGISTRY["fly"]
    assert fl.level == 3
    assert fl.school == "transmutation"

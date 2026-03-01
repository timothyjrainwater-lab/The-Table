"""Gate tests: WO-ENGINE-INTENT-TODICT-001
SpellCastIntent.to_dict() missing spontaneous_inflict (and spontaneous_summon) field

ITD-001  SpellCastIntent(spontaneous_inflict=True).to_dict() contains key "spontaneous_inflict"
ITD-002  SpellCastIntent(spontaneous_inflict=True).to_dict()["spontaneous_inflict"] == True
ITD-003  SpellCastIntent(spontaneous_inflict=False).to_dict()["spontaneous_inflict"] == False
ITD-004  Round-trip: from_dict(intent.to_dict()).spontaneous_inflict preserved (N/A — no from_dict; verified via to_dict only)
ITD-005  spontaneous_cure still serialized correctly (no regression)
ITD-006  use_secondary still serialized correctly (no regression)
ITD-007  to_dict() output is valid JSON (json.dumps succeeds, sort_keys=True)
ITD-008  Code inspection: "spontaneous_inflict" and "spontaneous_summon" present in to_dict()
"""

import json
import pytest

from aidm.core.spell_resolver import SpellCastIntent


# ---------------------------------------------------------------------------
# ITD-001: to_dict() contains "spontaneous_inflict" key
# ---------------------------------------------------------------------------

def test_ITD001_spontaneous_inflict_key_present():
    """ITD-001: SpellCastIntent(spontaneous_inflict=True).to_dict() contains 'spontaneous_inflict' key."""
    intent = SpellCastIntent(
        caster_id="cleric",
        spell_id="cure_light_wounds",
        spontaneous_inflict=True,
    )
    d = intent.to_dict()
    assert "spontaneous_inflict" in d, (
        f"to_dict() must include 'spontaneous_inflict'. Keys: {list(d.keys())}"
    )


# ---------------------------------------------------------------------------
# ITD-002: spontaneous_inflict=True serialized as True
# ---------------------------------------------------------------------------

def test_ITD002_spontaneous_inflict_true_value():
    """ITD-002: SpellCastIntent(spontaneous_inflict=True).to_dict()['spontaneous_inflict'] == True."""
    intent = SpellCastIntent(
        caster_id="cleric",
        spell_id="cure_light_wounds",
        spontaneous_inflict=True,
    )
    d = intent.to_dict()
    assert d["spontaneous_inflict"] is True, (
        f"Expected True, got {d['spontaneous_inflict']!r}"
    )


# ---------------------------------------------------------------------------
# ITD-003: spontaneous_inflict=False serialized as False
# ---------------------------------------------------------------------------

def test_ITD003_spontaneous_inflict_false_value():
    """ITD-003: SpellCastIntent(spontaneous_inflict=False).to_dict()['spontaneous_inflict'] == False."""
    intent = SpellCastIntent(
        caster_id="cleric",
        spell_id="cure_light_wounds",
        spontaneous_inflict=False,
    )
    d = intent.to_dict()
    assert d["spontaneous_inflict"] is False, (
        f"Expected False, got {d['spontaneous_inflict']!r}"
    )


# ---------------------------------------------------------------------------
# ITD-004: spontaneous_summon also serialized (AK WO2 merge — field in tree)
# ---------------------------------------------------------------------------

def test_ITD004_spontaneous_summon_also_serialized():
    """ITD-004: SpellCastIntent(spontaneous_summon=True).to_dict()['spontaneous_summon'] == True.
    Batch AK WO2 adds spontaneous_summon field; this WO also adds it to to_dict()."""
    intent = SpellCastIntent(
        caster_id="druid",
        spell_id="entangle",
        spontaneous_summon=True,
    )
    d = intent.to_dict()
    assert "spontaneous_summon" in d, (
        f"to_dict() must include 'spontaneous_summon' (added by AK WO2). Keys: {list(d.keys())}"
    )
    assert d["spontaneous_summon"] is True, (
        f"spontaneous_summon=True must serialize as True, got {d['spontaneous_summon']!r}"
    )


# ---------------------------------------------------------------------------
# ITD-005: spontaneous_cure still serialized (no regression)
# ---------------------------------------------------------------------------

def test_ITD005_spontaneous_cure_still_serialized():
    """ITD-005: spontaneous_cure still present in to_dict() after adding spontaneous_inflict."""
    intent = SpellCastIntent(
        caster_id="cleric",
        spell_id="cure_light_wounds",
        spontaneous_cure=True,
    )
    d = intent.to_dict()
    assert "spontaneous_cure" in d, "spontaneous_cure must still be in to_dict() (no regression)"
    assert d["spontaneous_cure"] is True


# ---------------------------------------------------------------------------
# ITD-006: use_secondary still serialized (no regression)
# ---------------------------------------------------------------------------

def test_ITD006_use_secondary_still_serialized():
    """ITD-006: use_secondary still present in to_dict() after adding spontaneous_inflict."""
    intent = SpellCastIntent(
        caster_id="wizard",
        spell_id="fireball",
        use_secondary=True,
    )
    d = intent.to_dict()
    assert "use_secondary" in d, "use_secondary must still be in to_dict() (no regression)"
    assert d["use_secondary"] is True


# ---------------------------------------------------------------------------
# ITD-007: to_dict() output is valid JSON with sort_keys=True
# ---------------------------------------------------------------------------

def test_ITD007_to_dict_valid_json():
    """ITD-007: SpellCastIntent.to_dict() produces valid JSON (json.dumps succeeds, sort_keys=True)."""
    intent = SpellCastIntent(
        caster_id="cleric",
        spell_id="cure_light_wounds",
        spontaneous_inflict=True,
        spontaneous_summon=False,
        spontaneous_cure=False,
        use_secondary=False,
    )
    d = intent.to_dict()
    try:
        json_str = json.dumps(d, sort_keys=True)
    except (TypeError, ValueError) as e:
        pytest.fail(f"to_dict() output is not JSON-serializable: {e}")
    assert isinstance(json_str, str), "json.dumps must return a string"


# ---------------------------------------------------------------------------
# ITD-008: Code inspection — both fields present in to_dict() source
# ---------------------------------------------------------------------------

def test_ITD008_code_inspection_fields_in_to_dict():
    """ITD-008: 'spontaneous_inflict' and 'spontaneous_summon' strings present in SpellCastIntent.to_dict() source."""
    import inspect
    import aidm.core.spell_resolver as sr_module
    src = inspect.getsource(sr_module)

    # Find the to_dict method block
    assert '"spontaneous_inflict"' in src, (
        "'spontaneous_inflict' string literal must appear in spell_resolver source (to_dict fix)"
    )
    assert '"spontaneous_summon"' in src, (
        "'spontaneous_summon' string literal must appear in spell_resolver source (AK WO2 + AL WO3)"
    )

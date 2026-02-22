"""Gate S — Prosodic Fields on VoicePersona (WO-VOICE-PAS-FIELDS-001).

12 tests validating the 6 prosodic fields and 4 enum types added to
VoicePersona. All fields have safe defaults and silent clamping.
"""

import pytest

from aidm.schemas.immersion import (
    ClarityMode,
    EmphasisLevel,
    PauseProfile,
    ToneMode,
    VoicePersona,
)


# ---------------------------------------------------------------------------
# S-01: VoicePersona has all 6 new fields with correct defaults
# ---------------------------------------------------------------------------

class TestProsodicDefaults:
    """S-01: All 6 prosodic fields present with correct defaults."""

    def test_pace_default(self):
        vp = VoicePersona()
        assert vp.pace == 1.0

    def test_emphasis_level_default(self):
        vp = VoicePersona()
        assert vp.emphasis_level is EmphasisLevel.NONE

    def test_tone_mode_default(self):
        vp = VoicePersona()
        assert vp.tone_mode is ToneMode.NEUTRAL

    def test_pause_profile_default(self):
        vp = VoicePersona()
        assert vp.pause_profile is PauseProfile.MINIMAL

    def test_pitch_offset_default(self):
        vp = VoicePersona()
        assert vp.pitch_offset == 0

    def test_clarity_mode_default(self):
        vp = VoicePersona()
        assert vp.clarity_mode is ClarityMode.NORMAL


# ---------------------------------------------------------------------------
# S-02: All 4 enum types exist with correct members
# ---------------------------------------------------------------------------

class TestEnumMembers:
    """S-02: Enum types have the expected members."""

    def test_emphasis_level_members(self):
        assert set(EmphasisLevel) == {
            EmphasisLevel.NONE,
            EmphasisLevel.LOW,
            EmphasisLevel.MEDIUM,
            EmphasisLevel.HIGH,
        }

    def test_tone_mode_members(self):
        assert set(ToneMode) == {
            ToneMode.NEUTRAL,
            ToneMode.CALM,
            ToneMode.DIRECTIVE,
            ToneMode.REFLECTIVE,
            ToneMode.COMBAT,
        }

    def test_pause_profile_members(self):
        assert set(PauseProfile) == {
            PauseProfile.MINIMAL,
            PauseProfile.MODERATE,
            PauseProfile.DRAMATIC,
        }

    def test_clarity_mode_members(self):
        assert set(ClarityMode) == {
            ClarityMode.NORMAL,
            ClarityMode.HIGH,
        }

    def test_enums_are_str_subclass(self):
        """str,Enum pattern — values usable as plain strings."""
        assert isinstance(EmphasisLevel.NONE, str)
        assert isinstance(ToneMode.NEUTRAL, str)
        assert isinstance(PauseProfile.MINIMAL, str)
        assert isinstance(ClarityMode.NORMAL, str)


# ---------------------------------------------------------------------------
# S-03: pace clamps to [0.8, 1.2] silently
# ---------------------------------------------------------------------------

class TestPaceClamping:
    """S-03: pace silently clamped by validate()."""

    def test_pace_low_clamps_up(self):
        vp = VoicePersona(persona_id="t", name="T", pace=0.5)
        vp.validate()
        assert vp.pace == 0.8

    def test_pace_high_clamps_down(self):
        vp = VoicePersona(persona_id="t", name="T", pace=1.5)
        vp.validate()
        assert vp.pace == 1.2

    def test_pace_in_range_unchanged(self):
        vp = VoicePersona(persona_id="t", name="T", pace=1.0)
        vp.validate()
        assert vp.pace == 1.0


# ---------------------------------------------------------------------------
# S-04: pitch_offset clamps to [-2, +2] silently
# ---------------------------------------------------------------------------

class TestPitchOffsetClamping:
    """S-04: pitch_offset silently clamped by validate()."""

    def test_pitch_offset_low_clamps_up(self):
        vp = VoicePersona(persona_id="t", name="T", pitch_offset=-5)
        vp.validate()
        assert vp.pitch_offset == -2

    def test_pitch_offset_high_clamps_down(self):
        vp = VoicePersona(persona_id="t", name="T", pitch_offset=10)
        vp.validate()
        assert vp.pitch_offset == 2

    def test_pitch_offset_in_range_unchanged(self):
        vp = VoicePersona(persona_id="t", name="T", pitch_offset=1)
        vp.validate()
        assert vp.pitch_offset == 1


# ---------------------------------------------------------------------------
# S-05: to_dict() serializes enum fields as strings
# ---------------------------------------------------------------------------

class TestToDict:
    """S-05: Enum fields serialize as their .value string."""

    def test_enum_fields_are_strings_in_dict(self):
        vp = VoicePersona(
            persona_id="t",
            name="T",
            emphasis_level=EmphasisLevel.HIGH,
            tone_mode=ToneMode.COMBAT,
            pause_profile=PauseProfile.DRAMATIC,
            clarity_mode=ClarityMode.HIGH,
        )
        d = vp.to_dict()
        assert d["emphasis_level"] == "high"
        assert d["tone_mode"] == "combat"
        assert d["pause_profile"] == "dramatic"
        assert d["clarity_mode"] == "high"

    def test_numeric_fields_in_dict(self):
        vp = VoicePersona(persona_id="t", name="T", pace=0.9, pitch_offset=-1)
        d = vp.to_dict()
        assert d["pace"] == 0.9
        assert d["pitch_offset"] == -1


# ---------------------------------------------------------------------------
# S-06: from_dict() round-trips all fields correctly
# ---------------------------------------------------------------------------

class TestRoundTrip:
    """S-06: Full prosodic round-trip via to_dict / from_dict."""

    def test_full_roundtrip(self):
        vp = VoicePersona(
            persona_id="npc_1",
            name="Narrator",
            voice_model="model_x",
            speed=1.2,
            pitch=0.9,
            pace=1.1,
            emphasis_level=EmphasisLevel.MEDIUM,
            tone_mode=ToneMode.REFLECTIVE,
            pause_profile=PauseProfile.MODERATE,
            pitch_offset=2,
            clarity_mode=ClarityMode.HIGH,
        )
        d = vp.to_dict()
        vp2 = VoicePersona.from_dict(d)
        assert vp2.pace == 1.1
        assert vp2.emphasis_level is EmphasisLevel.MEDIUM
        assert vp2.tone_mode is ToneMode.REFLECTIVE
        assert vp2.pause_profile is PauseProfile.MODERATE
        assert vp2.pitch_offset == 2
        assert vp2.clarity_mode is ClarityMode.HIGH
        # Original fields also survive
        assert vp2.persona_id == "npc_1"
        assert vp2.speed == 1.2


# ---------------------------------------------------------------------------
# S-07: from_dict() with missing prosodic fields uses defaults
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    """S-07: Old dicts (no prosodic keys) deserialize cleanly."""

    def test_missing_prosodic_fields_use_defaults(self):
        old_dict = {
            "persona_id": "dm",
            "name": "DM",
            "voice_model": "default",
            "speed": 1.0,
            "pitch": 1.0,
        }
        vp = VoicePersona.from_dict(old_dict)
        assert vp.pace == 1.0
        assert vp.emphasis_level is EmphasisLevel.NONE
        assert vp.tone_mode is ToneMode.NEUTRAL
        assert vp.pause_profile is PauseProfile.MINIMAL
        assert vp.pitch_offset == 0
        assert vp.clarity_mode is ClarityMode.NORMAL


# ---------------------------------------------------------------------------
# S-08: from_dict() with unknown enum value falls back to default
# ---------------------------------------------------------------------------

class TestEnumFallback:
    """S-08: Unknown enum strings in dict → safe default."""

    def test_unknown_emphasis_falls_back(self):
        d = {"emphasis_level": "extreme"}
        vp = VoicePersona.from_dict(d)
        assert vp.emphasis_level is EmphasisLevel.NONE

    def test_unknown_tone_falls_back(self):
        d = {"tone_mode": "angry"}
        vp = VoicePersona.from_dict(d)
        assert vp.tone_mode is ToneMode.NEUTRAL

    def test_unknown_pause_falls_back(self):
        d = {"pause_profile": "chaotic"}
        vp = VoicePersona.from_dict(d)
        assert vp.pause_profile is PauseProfile.MINIMAL

    def test_unknown_clarity_falls_back(self):
        d = {"clarity_mode": "ultra"}
        vp = VoicePersona.from_dict(d)
        assert vp.clarity_mode is ClarityMode.NORMAL


# ---------------------------------------------------------------------------
# S-09: validate() returns no errors for valid prosodic fields
# ---------------------------------------------------------------------------

class TestValidateClean:
    """S-09: Valid prosodic fields produce no validation errors."""

    def test_valid_prosodic_no_errors(self):
        vp = VoicePersona(
            persona_id="t",
            name="T",
            pace=1.0,
            emphasis_level=EmphasisLevel.LOW,
            tone_mode=ToneMode.CALM,
            pause_profile=PauseProfile.MODERATE,
            pitch_offset=1,
            clarity_mode=ClarityMode.HIGH,
        )
        errors = vp.validate()
        assert errors == []


# ---------------------------------------------------------------------------
# S-10: validate() clamps out-of-range values (does not error)
# ---------------------------------------------------------------------------

class TestValidateClamps:
    """S-10: Out-of-range prosodic values clamped, not errored."""

    def test_clamp_does_not_produce_errors(self):
        vp = VoicePersona(
            persona_id="t",
            name="T",
            pace=0.3,
            pitch_offset=99,
        )
        errors = vp.validate()
        # No prosodic-related errors — only silent clamping
        assert errors == []
        assert vp.pace == 0.8
        assert vp.pitch_offset == 2


# ---------------------------------------------------------------------------
# S-11: Existing adapter persona lists still load without error
# ---------------------------------------------------------------------------

class TestAdapterRegression:
    """S-11: Adapter persona lists construct without error."""

    def test_chatterbox_personas_importable(self):
        from aidm.immersion.chatterbox_tts_adapter import _CHATTERBOX_PERSONAS
        for persona in _CHATTERBOX_PERSONAS:
            assert isinstance(persona, VoicePersona)
            # New fields should have defaults
            assert persona.pace == 1.0
            assert persona.emphasis_level is EmphasisLevel.NONE

    def test_kokoro_personas_importable(self):
        from aidm.immersion.kokoro_tts_adapter import _KOKORO_PERSONAS
        for persona in _KOKORO_PERSONAS:
            assert isinstance(persona, VoicePersona)
            assert persona.pace == 1.0
            assert persona.tone_mode is ToneMode.NEUTRAL


# ---------------------------------------------------------------------------
# S-12: Full suite regression
# ---------------------------------------------------------------------------

class TestFullRegression:
    """S-12: Full suite regression — schema import and basic contract."""

    def test_immersion_module_imports_cleanly(self):
        from aidm.schemas.immersion import (
            AttributionLedger,
            AttributionRecord,
            AudioTrack,
            ClarityMode,
            EmphasisLevel,
            GridEntityPosition,
            GridRenderState,
            ImageRequest,
            ImageResult,
            PauseProfile,
            SceneAudioState,
            ToneMode,
            Transcript,
            VoicePersona,
        )
        # All types importable
        assert VoicePersona is not None
        assert EmphasisLevel is not None

    def test_default_persona_validates_clean(self):
        """Default VoicePersona (empty) still validates with expected errors only."""
        vp = VoicePersona()
        errors = vp.validate()
        # Only persona_id and name errors — no prosodic errors
        error_fields = " ".join(errors)
        assert "persona_id" in error_fields
        assert "name" in error_fields
        assert "pace" not in error_fields
        assert "pitch_offset" not in error_fields

"""Gate V — Pressure-to-Prosodic Modulation (WO-IMPL-PRESSURE-ALERTS-001).

14 tests validating pressure modulation on top of mode presets,
_generate_narration 3-tuple return, and _synthesize_tts signature.
"""

import inspect
from unittest.mock import MagicMock, patch

import pytest

from aidm.immersion.prosodic_preset_manager import ProsodicPresetManager
from aidm.runtime.session_orchestrator import (
    SessionOrchestrator,
    SessionState,
    _SESSION_TO_PRESET_MODE,
)
from aidm.schemas.boundary_pressure import PressureLevel
from aidm.schemas.immersion import (
    ClarityMode,
    EmphasisLevel,
    PauseProfile,
    ToneMode,
    VoicePersona,
)


@pytest.fixture
def manager():
    return ProsodicPresetManager()


@pytest.fixture
def base_persona():
    """A persona with non-default identity fields for merge testing."""
    return VoicePersona(
        persona_id="npc_1",
        name="Bartender",
        voice_model="kokoro",
        speed=1.1,
        pitch=0.9,
        reference_audio="/voices/barkeep.wav",
        exaggeration=0.7,
    )


# ---------------------------------------------------------------------------
# V-01: GREEN returns persona unchanged
# ---------------------------------------------------------------------------

class TestGreenNoOp:
    """V-01: apply_pressure_modulation(persona, GREEN) returns unchanged."""

    def test_green_returns_same_object(self, manager, base_persona):
        result = manager.apply_pressure_modulation(base_persona, PressureLevel.GREEN)
        assert result is base_persona

    def test_green_preserves_all_fields(self, manager):
        persona = VoicePersona(
            persona_id="x", name="X",
            pace=0.92, tone_mode=ToneMode.CALM,
            clarity_mode=ClarityMode.NORMAL,
            pause_profile=PauseProfile.MODERATE,
            emphasis_level=EmphasisLevel.HIGH,
        )
        result = manager.apply_pressure_modulation(persona, PressureLevel.GREEN)
        assert result.pace == 0.92
        assert result.tone_mode is ToneMode.CALM
        assert result.clarity_mode is ClarityMode.NORMAL
        assert result.pause_profile is PauseProfile.MODERATE
        assert result.emphasis_level is EmphasisLevel.HIGH


# ---------------------------------------------------------------------------
# V-02: YELLOW sets clarity_mode=HIGH
# ---------------------------------------------------------------------------

class TestYellowClarity:
    """V-02: YELLOW pressure sets clarity_mode to HIGH."""

    def test_yellow_sets_clarity_high(self, manager, base_persona):
        result = manager.apply_pressure_modulation(base_persona, PressureLevel.YELLOW)
        assert result.clarity_mode is ClarityMode.HIGH


# ---------------------------------------------------------------------------
# V-03: YELLOW raises emphasis from LOW to MEDIUM
# ---------------------------------------------------------------------------

class TestYellowEmphasisFloor:
    """V-03: YELLOW raises emphasis below MEDIUM up to MEDIUM."""

    def test_yellow_raises_low_to_medium(self, manager):
        persona = VoicePersona(emphasis_level=EmphasisLevel.LOW)
        result = manager.apply_pressure_modulation(persona, PressureLevel.YELLOW)
        assert result.emphasis_level is EmphasisLevel.MEDIUM

    def test_yellow_raises_none_to_medium(self, manager):
        persona = VoicePersona(emphasis_level=EmphasisLevel.NONE)
        result = manager.apply_pressure_modulation(persona, PressureLevel.YELLOW)
        assert result.emphasis_level is EmphasisLevel.MEDIUM


# ---------------------------------------------------------------------------
# V-04: YELLOW keeps emphasis at HIGH if already HIGH
# ---------------------------------------------------------------------------

class TestYellowEmphasisCeiling:
    """V-04: YELLOW keeps emphasis >= MEDIUM unchanged."""

    def test_yellow_keeps_high(self, manager):
        persona = VoicePersona(emphasis_level=EmphasisLevel.HIGH)
        result = manager.apply_pressure_modulation(persona, PressureLevel.YELLOW)
        assert result.emphasis_level is EmphasisLevel.HIGH

    def test_yellow_keeps_medium(self, manager):
        persona = VoicePersona(emphasis_level=EmphasisLevel.MEDIUM)
        result = manager.apply_pressure_modulation(persona, PressureLevel.YELLOW)
        assert result.emphasis_level is EmphasisLevel.MEDIUM


# ---------------------------------------------------------------------------
# V-05: RED sets tone_mode=DIRECTIVE
# ---------------------------------------------------------------------------

class TestRedTone:
    """V-05: RED pressure sets tone_mode to DIRECTIVE."""

    def test_red_sets_directive(self, manager, base_persona):
        result = manager.apply_pressure_modulation(base_persona, PressureLevel.RED)
        assert result.tone_mode is ToneMode.DIRECTIVE


# ---------------------------------------------------------------------------
# V-06: RED sets clarity_mode=HIGH, pause_profile=MINIMAL
# ---------------------------------------------------------------------------

class TestRedClarityPause:
    """V-06: RED sets clarity and pause."""

    def test_red_clarity_high(self, manager, base_persona):
        result = manager.apply_pressure_modulation(base_persona, PressureLevel.RED)
        assert result.clarity_mode is ClarityMode.HIGH

    def test_red_pause_minimal(self, manager, base_persona):
        result = manager.apply_pressure_modulation(base_persona, PressureLevel.RED)
        assert result.pause_profile is PauseProfile.MINIMAL


# ---------------------------------------------------------------------------
# V-07: RED sets emphasis_level=LOW, pace=1.0
# ---------------------------------------------------------------------------

class TestRedEmphasisPace:
    """V-07: RED sets emphasis and pace."""

    def test_red_emphasis_low(self, manager, base_persona):
        result = manager.apply_pressure_modulation(base_persona, PressureLevel.RED)
        assert result.emphasis_level is EmphasisLevel.LOW

    def test_red_pace_one(self, manager, base_persona):
        result = manager.apply_pressure_modulation(base_persona, PressureLevel.RED)
        assert result.pace == 1.0


# ---------------------------------------------------------------------------
# V-08: Full pipeline: mode preset + GREEN = same as mode preset alone
# ---------------------------------------------------------------------------

class TestPipelineGreen:
    """V-08: Mode preset + GREEN pressure = mode preset alone."""

    def test_combat_plus_green(self, manager):
        persona = VoicePersona(persona_id="npc", name="NPC")
        after_preset = manager.apply_preset(persona, "combat")
        after_pressure = manager.apply_pressure_modulation(
            after_preset, PressureLevel.GREEN,
        )
        assert after_pressure is after_preset
        assert after_pressure.tone_mode is ToneMode.COMBAT
        assert after_pressure.pace == 1.05


# ---------------------------------------------------------------------------
# V-09: Full pipeline: combat preset + YELLOW
# ---------------------------------------------------------------------------

class TestPipelineCombatYellow:
    """V-09: Combat preset + YELLOW = combat fields + HIGH clarity + MEDIUM+ emphasis."""

    def test_combat_plus_yellow(self, manager):
        persona = VoicePersona(persona_id="npc", name="NPC")
        after_preset = manager.apply_preset(persona, "combat")
        result = manager.apply_pressure_modulation(
            after_preset, PressureLevel.YELLOW,
        )
        # Combat fields preserved
        assert result.tone_mode is ToneMode.COMBAT
        assert result.pace == 1.05
        assert result.pause_profile is PauseProfile.MINIMAL
        # YELLOW adjustments
        assert result.clarity_mode is ClarityMode.HIGH
        # Combat emphasis is HIGH, which is >= MEDIUM, so kept
        assert result.emphasis_level is EmphasisLevel.HIGH


# ---------------------------------------------------------------------------
# V-10: Full pipeline: operator preset + YELLOW (floor applied)
# ---------------------------------------------------------------------------

class TestPipelineOperatorYellow:
    """V-10: Operator preset + YELLOW = operator fields + HIGH clarity + MEDIUM emphasis."""

    def test_operator_plus_yellow(self, manager):
        persona = VoicePersona(persona_id="npc", name="NPC")
        after_preset = manager.apply_preset(persona, "operator")
        # Operator emphasis is LOW (clamped by mode ceiling)
        assert after_preset.emphasis_level is EmphasisLevel.LOW
        result = manager.apply_pressure_modulation(
            after_preset, PressureLevel.YELLOW,
        )
        # Operator fields preserved
        assert result.tone_mode is ToneMode.DIRECTIVE
        assert result.pace == 1.0
        assert result.pause_profile is PauseProfile.MINIMAL
        # YELLOW adjustments
        assert result.clarity_mode is ClarityMode.HIGH
        # LOW raised to MEDIUM floor
        assert result.emphasis_level is EmphasisLevel.MEDIUM


# ---------------------------------------------------------------------------
# V-11: Full pipeline: reflection preset + RED
# ---------------------------------------------------------------------------

class TestPipelineReflectionRed:
    """V-11: Reflection preset + RED = RED overrides all prosodic fields."""

    def test_reflection_plus_red(self, manager):
        persona = VoicePersona(
            persona_id="npc_bard", name="Elara",
            voice_model="af_bella", speed=1.3,
            reference_audio="/voices/elara.wav", exaggeration=0.8,
        )
        after_preset = manager.apply_preset(persona, "reflection")
        result = manager.apply_pressure_modulation(
            after_preset, PressureLevel.RED,
        )
        # RED overrides
        assert result.tone_mode is ToneMode.DIRECTIVE
        assert result.clarity_mode is ClarityMode.HIGH
        assert result.emphasis_level is EmphasisLevel.LOW
        assert result.pause_profile is PauseProfile.MINIMAL
        assert result.pace == 1.0
        # Identity preserved
        assert result.persona_id == "npc_bard"
        assert result.name == "Elara"
        assert result.voice_model == "af_bella"
        assert result.speed == 1.3
        assert result.reference_audio == "/voices/elara.wav"
        assert result.exaggeration == 0.8


# ---------------------------------------------------------------------------
# V-12: _generate_narration() returns 3-tuple
# ---------------------------------------------------------------------------

class TestGenerateNarrationReturnType:
    """V-12: _generate_narration() return type annotation includes PressureLevel."""

    def test_return_annotation_is_3_tuple(self):
        hints = inspect.get_annotations(SessionOrchestrator._generate_narration)
        ret = hints.get("return")
        # Should be Tuple[str, str, PressureLevel]
        assert ret is not None
        # Check the args of the Tuple type
        args = getattr(ret, "__args__", None)
        assert args is not None
        assert len(args) == 3
        assert args[0] is str
        assert args[1] is str
        assert args[2] is PressureLevel


# ---------------------------------------------------------------------------
# V-13: _synthesize_tts() accepts pressure_level, defaults to GREEN
# ---------------------------------------------------------------------------

class TestSynthesizeTtsSignature:
    """V-13: _synthesize_tts() has pressure_level param defaulting to GREEN."""

    def test_pressure_level_param_exists(self):
        sig = inspect.signature(SessionOrchestrator._synthesize_tts)
        assert "pressure_level" in sig.parameters

    def test_pressure_level_default_is_green(self):
        sig = inspect.signature(SessionOrchestrator._synthesize_tts)
        param = sig.parameters["pressure_level"]
        assert param.default is PressureLevel.GREEN


# ---------------------------------------------------------------------------
# V-14: Full suite regression (import + basic contract)
# ---------------------------------------------------------------------------

class TestFullRegression:
    """V-14: Full regression — imports, basic contract."""

    def test_pressure_modulation_importable(self):
        from aidm.immersion.prosodic_preset_manager import ProsodicPresetManager
        mgr = ProsodicPresetManager()
        assert hasattr(mgr, "apply_pressure_modulation")

    def test_all_pressure_levels_handled(self, manager, base_persona):
        """All 3 PressureLevel values produce a valid VoicePersona."""
        for level in PressureLevel:
            result = manager.apply_pressure_modulation(base_persona, level)
            assert isinstance(result, VoicePersona)

    def test_pressure_modulation_returns_new_object_for_non_green(self, manager):
        """Non-GREEN returns a new VoicePersona, not a mutation."""
        persona = VoicePersona(persona_id="t", name="T")
        for level in (PressureLevel.YELLOW, PressureLevel.RED):
            result = manager.apply_pressure_modulation(persona, level)
            assert result is not persona

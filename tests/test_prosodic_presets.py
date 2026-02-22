"""Gate T — Prosodic Presets (WO-VOICE-PAS-PRESETS-001).

15 tests validating mode-based prosodic preset selection, emphasis
clamping, preset merge behavior, and SessionState → preset mapping.
"""

import pytest

from aidm.immersion.prosodic_preset_manager import ProsodicPresetManager
from aidm.runtime.session_orchestrator import SessionState, _SESSION_TO_PRESET_MODE
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


# ---------------------------------------------------------------------------
# T-01: Operator preset
# ---------------------------------------------------------------------------

class TestOperatorPreset:
    """T-01: ProsodicPresetManager returns correct preset for operator."""

    def test_operator_preset(self, manager):
        p = manager.get_preset("operator")
        assert p.pace == 1.0
        assert p.tone_mode is ToneMode.DIRECTIVE
        assert p.clarity_mode is ClarityMode.HIGH
        assert p.pause_profile is PauseProfile.MINIMAL
        assert p.emphasis_level is EmphasisLevel.LOW


# ---------------------------------------------------------------------------
# T-02: Combat preset
# ---------------------------------------------------------------------------

class TestCombatPreset:
    """T-02: ProsodicPresetManager returns correct preset for combat."""

    def test_combat_preset(self, manager):
        p = manager.get_preset("combat")
        assert p.pace == 1.05
        assert p.tone_mode is ToneMode.COMBAT
        assert p.clarity_mode is ClarityMode.NORMAL
        assert p.pause_profile is PauseProfile.MINIMAL
        assert p.emphasis_level is EmphasisLevel.HIGH


# ---------------------------------------------------------------------------
# T-03: Scene preset
# ---------------------------------------------------------------------------

class TestScenePreset:
    """T-03: ProsodicPresetManager returns correct preset for scene."""

    def test_scene_preset(self, manager):
        p = manager.get_preset("scene")
        assert p.pace == 0.92
        assert p.tone_mode is ToneMode.CALM
        assert p.clarity_mode is ClarityMode.NORMAL
        assert p.pause_profile is PauseProfile.MODERATE
        assert p.emphasis_level is EmphasisLevel.MEDIUM


# ---------------------------------------------------------------------------
# T-04: Reflection preset
# ---------------------------------------------------------------------------

class TestReflectionPreset:
    """T-04: ProsodicPresetManager returns correct preset for reflection."""

    def test_reflection_preset(self, manager):
        p = manager.get_preset("reflection")
        assert p.pace == 0.9
        assert p.tone_mode is ToneMode.REFLECTIVE
        assert p.clarity_mode is ClarityMode.NORMAL
        assert p.pause_profile is PauseProfile.MODERATE
        assert p.emphasis_level is EmphasisLevel.MEDIUM


# ---------------------------------------------------------------------------
# T-05: Unknown mode falls back to scene
# ---------------------------------------------------------------------------

class TestUnknownModeFallback:
    """T-05: Unknown mode falls back to scene preset."""

    def test_unknown_mode_returns_scene(self, manager):
        p = manager.get_preset("nonexistent")
        scene = manager.get_preset("scene")
        assert p.pace == scene.pace
        assert p.tone_mode is scene.tone_mode
        assert p.clarity_mode is scene.clarity_mode
        assert p.pause_profile is scene.pause_profile


# ---------------------------------------------------------------------------
# T-06: apply_preset overlays prosodic fields
# ---------------------------------------------------------------------------

class TestApplyPresetOverlay:
    """T-06: apply_preset overlays prosodic fields onto persona."""

    def test_overlay_changes_prosodic_fields(self, manager):
        persona = VoicePersona(
            persona_id="npc_1",
            name="Bartender",
            voice_model="kokoro",
            speed=1.1,
            pitch=0.9,
            pace=1.0,
            tone_mode=ToneMode.NEUTRAL,
        )
        result = manager.apply_preset(persona, "combat")
        assert result.pace == 1.05
        assert result.tone_mode is ToneMode.COMBAT
        assert result.clarity_mode is ClarityMode.NORMAL
        assert result.pause_profile is PauseProfile.MINIMAL
        assert result.emphasis_level is EmphasisLevel.HIGH


# ---------------------------------------------------------------------------
# T-07: apply_preset preserves voice identity
# ---------------------------------------------------------------------------

class TestApplyPresetPreservesIdentity:
    """T-07: apply_preset preserves voice identity fields."""

    def test_identity_fields_preserved(self, manager):
        persona = VoicePersona(
            persona_id="npc_bard",
            name="Elara the Bard",
            voice_model="af_bella",
            speed=1.3,
            pitch=1.1,
            reference_audio="/voices/elara.wav",
            exaggeration=0.8,
        )
        result = manager.apply_preset(persona, "reflection")
        assert result.persona_id == "npc_bard"
        assert result.name == "Elara the Bard"
        assert result.voice_model == "af_bella"
        assert result.speed == 1.3
        assert result.pitch == 1.1
        assert result.reference_audio == "/voices/elara.wav"
        assert result.exaggeration == 0.8


# ---------------------------------------------------------------------------
# T-08: Emphasis clamping — combat allows HIGH
# ---------------------------------------------------------------------------

class TestEmphasisClampingCombat:
    """T-08: Combat mode ceiling is HIGH — allows HIGH through."""

    def test_combat_allows_high(self, manager):
        result = manager.clamp_emphasis("combat", EmphasisLevel.HIGH)
        assert result is EmphasisLevel.HIGH

    def test_combat_allows_medium(self, manager):
        result = manager.clamp_emphasis("combat", EmphasisLevel.MEDIUM)
        assert result is EmphasisLevel.MEDIUM


# ---------------------------------------------------------------------------
# T-09: Emphasis clamping — operator clamps HIGH → LOW
# ---------------------------------------------------------------------------

class TestEmphasisClampingOperator:
    """T-09: Operator mode ceiling is LOW — clamps HIGH down."""

    def test_operator_clamps_high_to_low(self, manager):
        result = manager.clamp_emphasis("operator", EmphasisLevel.HIGH)
        assert result is EmphasisLevel.LOW

    def test_operator_clamps_medium_to_low(self, manager):
        result = manager.clamp_emphasis("operator", EmphasisLevel.MEDIUM)
        assert result is EmphasisLevel.LOW

    def test_operator_allows_low(self, manager):
        result = manager.clamp_emphasis("operator", EmphasisLevel.LOW)
        assert result is EmphasisLevel.LOW


# ---------------------------------------------------------------------------
# T-10: Emphasis clamping — scene clamps HIGH → MEDIUM
# ---------------------------------------------------------------------------

class TestEmphasisClampingScene:
    """T-10: Scene mode ceiling is MEDIUM — clamps HIGH down."""

    def test_scene_clamps_high_to_medium(self, manager):
        result = manager.clamp_emphasis("scene", EmphasisLevel.HIGH)
        assert result is EmphasisLevel.MEDIUM

    def test_scene_allows_medium(self, manager):
        result = manager.clamp_emphasis("scene", EmphasisLevel.MEDIUM)
        assert result is EmphasisLevel.MEDIUM

    def test_scene_allows_low(self, manager):
        result = manager.clamp_emphasis("scene", EmphasisLevel.LOW)
        assert result is EmphasisLevel.LOW


# ---------------------------------------------------------------------------
# T-11: SessionState.COMBAT → "combat"
# ---------------------------------------------------------------------------

class TestSessionCombatMapping:
    """T-11: COMBAT session maps to combat preset."""

    def test_combat_maps(self):
        assert _SESSION_TO_PRESET_MODE[SessionState.COMBAT] == "combat"


# ---------------------------------------------------------------------------
# T-12: SessionState.EXPLORATION → "scene"
# ---------------------------------------------------------------------------

class TestSessionExplorationMapping:
    """T-12: EXPLORATION session maps to scene preset."""

    def test_exploration_maps(self):
        assert _SESSION_TO_PRESET_MODE[SessionState.EXPLORATION] == "scene"


# ---------------------------------------------------------------------------
# T-13: SessionState.REST → "reflection"
# ---------------------------------------------------------------------------

class TestSessionRestMapping:
    """T-13: REST session maps to reflection preset."""

    def test_rest_maps(self):
        assert _SESSION_TO_PRESET_MODE[SessionState.REST] == "reflection"


# ---------------------------------------------------------------------------
# T-14: SessionState.DIALOGUE → "scene"
# ---------------------------------------------------------------------------

class TestSessionDialogueMapping:
    """T-14: DIALOGUE session maps to scene preset."""

    def test_dialogue_maps(self):
        assert _SESSION_TO_PRESET_MODE[SessionState.DIALOGUE] == "scene"


# ---------------------------------------------------------------------------
# T-15: Full suite regression
# ---------------------------------------------------------------------------

class TestFullRegression:
    """T-15: Full regression — imports, basic contract."""

    def test_preset_manager_importable(self):
        from aidm.immersion.prosodic_preset_manager import ProsodicPresetManager
        assert ProsodicPresetManager is not None

    def test_all_session_states_mapped(self):
        """Every SessionState has a preset mapping."""
        for state in SessionState:
            assert state in _SESSION_TO_PRESET_MODE

    def test_apply_preset_returns_new_object(self, manager):
        """apply_preset returns a new VoicePersona, not a mutation."""
        original = VoicePersona(persona_id="t", name="T")
        result = manager.apply_preset(original, "combat")
        assert result is not original
        # Original unchanged
        assert original.tone_mode is ToneMode.NEUTRAL

    def test_all_preset_modes_valid(self, manager):
        """All 4 preset modes return valid presets."""
        for mode in ("operator", "combat", "scene", "reflection"):
            p = manager.get_preset(mode)
            assert isinstance(p, VoicePersona)

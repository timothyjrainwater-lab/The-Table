"""Mode-based prosodic preset selection with emphasis clamping.

WO-VOICE-PAS-PRESETS-001 — Tier 4.2

Defines 4 prosodic mode presets (operator, combat, scene, reflection)
and provides merge logic to overlay preset fields onto an existing
VoicePersona while preserving voice identity.

Emphasis is clamped per-mode ceiling to prevent over-dramatization.
"""

import copy
from dataclasses import replace
from typing import Dict

from aidm.schemas.immersion import (
    ClarityMode,
    EmphasisLevel,
    PauseProfile,
    ToneMode,
    VoicePersona,
)


# Emphasis level ordering for ceiling comparison
_EMPHASIS_ORDER = {
    EmphasisLevel.NONE: 0,
    EmphasisLevel.LOW: 1,
    EmphasisLevel.MEDIUM: 2,
    EmphasisLevel.HIGH: 3,
}

# Per-mode emphasis ceiling
_EMPHASIS_CEILING: Dict[str, EmphasisLevel] = {
    "operator": EmphasisLevel.LOW,
    "combat": EmphasisLevel.HIGH,
    "scene": EmphasisLevel.MEDIUM,
    "reflection": EmphasisLevel.MEDIUM,
}

# 4 mode presets — prosodic field overlays
_PRESETS: Dict[str, VoicePersona] = {
    "operator": VoicePersona(
        pace=1.0,
        tone_mode=ToneMode.DIRECTIVE,
        clarity_mode=ClarityMode.HIGH,
        pause_profile=PauseProfile.MINIMAL,
        emphasis_level=EmphasisLevel.LOW,
        pitch_offset=0,
    ),
    "combat": VoicePersona(
        pace=1.05,
        tone_mode=ToneMode.COMBAT,
        clarity_mode=ClarityMode.NORMAL,
        pause_profile=PauseProfile.MINIMAL,
        emphasis_level=EmphasisLevel.HIGH,
        pitch_offset=0,
    ),
    "scene": VoicePersona(
        pace=0.92,
        tone_mode=ToneMode.CALM,
        clarity_mode=ClarityMode.NORMAL,
        pause_profile=PauseProfile.MODERATE,
        emphasis_level=EmphasisLevel.MEDIUM,
        pitch_offset=0,
    ),
    "reflection": VoicePersona(
        pace=0.9,
        tone_mode=ToneMode.REFLECTIVE,
        clarity_mode=ClarityMode.NORMAL,
        pause_profile=PauseProfile.MODERATE,
        emphasis_level=EmphasisLevel.MEDIUM,
        pitch_offset=0,
    ),
}

_DEFAULT_MODE = "scene"


class ProsodicPresetManager:
    """Mode-based prosodic preset selection with emphasis clamping."""

    def get_preset(self, mode: str) -> VoicePersona:
        """Return preset VoicePersona for the given mode.

        Unknown modes fall back to "scene" (safe default).
        """
        return _PRESETS.get(mode, _PRESETS[_DEFAULT_MODE])

    def apply_preset(self, persona: VoicePersona, mode: str) -> VoicePersona:
        """Overlay preset prosodic fields onto persona, preserving voice identity.

        Overwrites: pace, tone_mode, clarity_mode, pause_profile,
                    emphasis_level (clamped), pitch_offset
        Preserves: persona_id, name, voice_model, speed, pitch,
                   reference_audio, exaggeration
        """
        preset = self.get_preset(mode)
        clamped_emphasis = self.clamp_emphasis(mode, preset.emphasis_level)

        return replace(
            persona,
            pace=preset.pace,
            tone_mode=preset.tone_mode,
            clarity_mode=preset.clarity_mode,
            pause_profile=preset.pause_profile,
            emphasis_level=clamped_emphasis,
            pitch_offset=preset.pitch_offset,
        )

    def clamp_emphasis(
        self, mode: str, requested: EmphasisLevel
    ) -> EmphasisLevel:
        """Clamp emphasis to the mode's ceiling.

        If requested emphasis exceeds the ceiling for the active mode,
        silently returns the ceiling value.
        """
        ceiling = _EMPHASIS_CEILING.get(mode, _EMPHASIS_CEILING[_DEFAULT_MODE])
        if _EMPHASIS_ORDER.get(requested, 0) > _EMPHASIS_ORDER.get(ceiling, 0):
            return ceiling
        return requested

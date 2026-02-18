"""Emotion Register Router — Deterministic mood-to-reference-clip selection.

Maps (persona_id, AudioMood) to a specific acted reference clip path.
The hypothesis: swapping the reference clip changes Chatterbox's vocal
performance more reliably than emotion tags or exaggeration knobs.

DESIGN CONSTRAINTS:
- Deterministic: same inputs always produce same clip selection.
- Fixed register set: neutral, tense, angry, grief. No invention from text.
- Mood mapping is boring on purpose:
    neutral  -> neutral register
    peaceful -> neutral register
    tense    -> tense register
    combat   -> angry register
    dramatic -> grief register (default), neutral if scene_tag == "triumph"
- File naming: {persona_id}__{register}__v1.wav

Phase 1 personas: dm_narrator, npc_male, npc_female, villainous
Phase 2 adds: npc_elderly, heroic, npc_young

Atmospheric only — never mechanical authority.
"""

import os
from typing import Dict, List, Optional, Tuple

# ==============================================================================
# REGISTER TAXONOMY (fixed set — do not extend without Phase 2/3 decision)
# ==============================================================================

EMOTION_REGISTERS: Tuple[str, ...] = ("neutral", "tense", "angry", "grief")
"""Valid emotion registers for reference clip selection."""

# Phase 1 personas that have multi-register clips
PHASE1_PERSONAS: Tuple[str, ...] = ("dm_narrator", "npc_male", "npc_female", "villainous")

# ==============================================================================
# MOOD → REGISTER MAPPING (deterministic, no LLM involvement)
# ==============================================================================

_MOOD_TO_REGISTER: Dict[str, str] = {
    "neutral": "neutral",
    "peaceful": "neutral",
    "tense": "tense",
    "combat": "angry",
    "dramatic": "grief",
}

# Scene tags that override the dramatic→grief default
_DRAMATIC_OVERRIDES: Dict[str, str] = {
    "triumph": "neutral",
}


def mood_to_register(
    mood: str,
    scene_tag: Optional[str] = None,
) -> str:
    """Map an AudioMood to an emotion register.

    Args:
        mood: Scene mood from AudioMood taxonomy
              ("neutral", "peaceful", "tense", "combat", "dramatic")
        scene_tag: Optional scene sub-tag for overrides (e.g., "triumph").
                   Only affects "dramatic" mood currently.

    Returns:
        Emotion register string from EMOTION_REGISTERS.
        Falls back to "neutral" for unknown moods.
    """
    register = _MOOD_TO_REGISTER.get(mood, "neutral")

    # Handle dramatic overrides (e.g., dramatic + triumph → neutral)
    if mood == "dramatic" and scene_tag and scene_tag in _DRAMATIC_OVERRIDES:
        register = _DRAMATIC_OVERRIDES[scene_tag]

    return register


# ==============================================================================
# CLIP PATH RESOLUTION
# ==============================================================================

def _clip_filename(persona_id: str, register: str, version: int = 1) -> str:
    """Build clip filename from components.

    Format: {persona_id}__{register}__v{version}.wav

    Args:
        persona_id: Voice persona identifier
        register: Emotion register
        version: Clip version number

    Returns:
        Filename string (no directory)
    """
    return f"{persona_id}__{register}__v{version}.wav"


def resolve_emotion_clip(
    persona_id: str,
    mood: str,
    voices_dir: str,
    scene_tag: Optional[str] = None,
) -> Optional[str]:
    """Resolve the acted reference clip for a persona + mood combination.

    Looks for a register-specific clip first. If not found, falls back
    to the persona's neutral register clip, then to the legacy single
    reference clip ({persona_id}.wav).

    Args:
        persona_id: Voice persona identifier (e.g., "dm_narrator")
        mood: Scene mood from AudioMood taxonomy
        voices_dir: Directory containing reference audio clips
        scene_tag: Optional scene sub-tag for dramatic overrides

    Returns:
        Absolute path to the reference clip, or None if no clip found.
    """
    if not voices_dir or not os.path.isdir(voices_dir):
        return None

    register = mood_to_register(mood, scene_tag)

    # Try register-specific clip
    register_clip = os.path.join(voices_dir, _clip_filename(persona_id, register))
    if os.path.isfile(register_clip):
        return register_clip

    # Fallback: neutral register clip
    if register != "neutral":
        neutral_clip = os.path.join(voices_dir, _clip_filename(persona_id, "neutral"))
        if os.path.isfile(neutral_clip):
            return neutral_clip

    # Fallback: legacy single clip ({persona_id}.wav)
    legacy_clip = os.path.join(voices_dir, f"{persona_id}.wav")
    if os.path.isfile(legacy_clip):
        return legacy_clip

    return None


def list_available_clips(
    voices_dir: str,
    persona_id: Optional[str] = None,
) -> List[str]:
    """List all emotion register clips in voices_dir.

    Args:
        voices_dir: Directory containing reference audio clips
        persona_id: If provided, filter to this persona only

    Returns:
        List of filenames matching the register clip naming convention
    """
    if not voices_dir or not os.path.isdir(voices_dir):
        return []

    clips = []
    for f in sorted(os.listdir(voices_dir)):
        if not f.endswith(".wav"):
            continue
        if "__" not in f:
            continue
        parts = f.rsplit(".wav", 1)[0].split("__")
        if len(parts) < 2:
            continue
        pid = parts[0]
        reg = parts[1]
        if reg not in EMOTION_REGISTERS:
            continue
        if persona_id and pid != persona_id:
            continue
        clips.append(f)

    return clips


def get_clip_coverage(voices_dir: str) -> Dict[str, List[str]]:
    """Report which registers are covered per persona.

    Returns:
        Dict of persona_id -> list of available registers
        e.g., {"dm_narrator": ["neutral", "tense", "angry"], ...}
    """
    coverage: Dict[str, List[str]] = {}
    for clip in list_available_clips(voices_dir):
        parts = clip.rsplit(".wav", 1)[0].split("__")
        pid = parts[0]
        reg = parts[1]
        if pid not in coverage:
            coverage[pid] = []
        if reg not in coverage[pid]:
            coverage[pid].append(reg)
    return coverage

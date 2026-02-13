"""Audio module package for M3 Audio Pipeline.

Provides music generation, SFX library, and audio mixing for AIDM runtime.

Modules:
- music_generator: ACE-Step wrapper for prep-time music generation
- sfx_library: Curated SFX library loader with semantic key mapping
- audio_mixer: Multi-channel audio mixer (music, ambient, SFX)
- tier_detection: Hardware tier detection for adapter selection

Reference: WO-M3-AUDIO-INT-01
"""

__all__ = [
    "MusicGenerator",
    "SFXLibrary",
    "AudioMixer",
    "detect_audio_tier",
]

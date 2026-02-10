"""Audio mixer for M3 Audio Pipeline — Multi-channel runtime playback.

Provides multi-channel audio mixing for:
- Music channel (looping, crossfade support)
- Ambient channel (looping background SFX)
- SFX channels (8-16 simultaneous one-shot sounds)

Backend: Stub implementation (real implementation requires sounddevice or pygame.mixer).

EVAL-05 recommends sounddevice (custom mixer, ~300-500 lines) to avoid TTS/STT device contention.
pygame.mixer is fallback if custom mixer cost is too high.

Reference: EVAL-05 Integration Planning, lines 191-215
"""

from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from enum import Enum

from aidm.schemas.audio import AudioTrack


# ═════════════════════════════════════════════════════════════════════════
# Audio Mixer Configuration
# ═════════════════════════════════════════════════════════════════════════


class AudioMixerBackend(str, Enum):
    """Audio mixer backend selection."""
    SOUNDDEVICE = "sounddevice"  # Custom mixer (EVAL-05 recommended)
    PYGAME = "pygame"  # pygame.mixer fallback
    STUB = "stub"  # Stub (no actual playback)


@dataclass
class AudioMixerConfig:
    """Configuration for audio mixer."""

    backend: AudioMixerBackend = AudioMixerBackend.STUB
    """Mixer backend selection."""

    channels: int = 16
    """Number of simultaneous audio channels (8-16 per EVAL-05)."""

    sample_rate: int = 44100
    """Audio sample rate in Hz."""

    music_volume: float = 0.5
    """Default music volume (0.0-1.0)."""

    sfx_volume: float = 0.7
    """Default SFX volume (0.0-1.0)."""

    ambient_volume: float = 0.3
    """Default ambient SFX volume (0.0-1.0)."""


# ═════════════════════════════════════════════════════════════════════════
# Audio Mixer
# ═════════════════════════════════════════════════════════════════════════


class AudioMixer:
    """Multi-channel audio mixer for music, ambient, and SFX playback.

    Manages:
    - Music channel (channel 0): Looping, crossfade support
    - Ambient channel (channel 1): Looping background SFX
    - SFX channels (channels 2-15): One-shot sounds, multiple simultaneous

    STUB IMPLEMENTATION: Tracks playback state without real audio output.
    Real implementation requires sounddevice or pygame.mixer integration (M3 Sprint 4).
    """

    def __init__(self, config: AudioMixerConfig):
        """Initialize audio mixer.

        Args:
            config: Mixer configuration
        """
        self.config = config
        self._music_channel: Optional[AudioTrack] = None
        self._ambient_channel: Optional[AudioTrack] = None
        self._sfx_channels: Dict[int, Optional[AudioTrack]] = {
            i: None for i in range(2, config.channels)
        }

    def play_music(
        self,
        track: AudioTrack,
        loop: bool = True,
        volume: Optional[float] = None
    ) -> None:
        """Play music track on music channel.

        Stops current music (if any) and plays new track.

        Args:
            track: Music track to play
            loop: If True, loop track indefinitely
            volume: Volume override (0.0-1.0), or None for default
        """
        # STUB: Track playback state without real audio
        # Real implementation:
        # self._load_audio_file(track.source_file)
        # self._play_on_channel(0, track, loop=loop, volume=volume or self.config.music_volume)

        self._music_channel = track

    def crossfade_music(
        self,
        new_track: AudioTrack,
        duration_ms: int = 2000,
        volume: Optional[float] = None
    ) -> None:
        """Crossfade from current music to new track.

        EVAL-05 recommends 2-4 second crossfade for mood transitions.

        Args:
            new_track: New music track
            duration_ms: Crossfade duration in milliseconds (default: 2000ms = 2s)
            volume: Target volume for new track (0.0-1.0)
        """
        # STUB: Track playback state
        # Real implementation:
        # old_channel = 0
        # new_channel = self._allocate_temp_channel()
        # self._fade_out(old_channel, duration_ms)
        # self._play_on_channel(new_channel, new_track, loop=True, volume=0.0)
        # self._fade_in(new_channel, duration_ms, target_volume=volume or self.config.music_volume)
        # # After fade completes, reassign music channel
        # time.sleep(duration_ms / 1000)
        # self._music_channel_id = new_channel
        # self._stop_channel(old_channel)

        self._music_channel = new_track

    def stop_music(self) -> None:
        """Stop current music playback."""
        # STUB: Clear music channel
        # Real implementation:
        # self._stop_channel(0)

        self._music_channel = None

    def play_ambient(
        self,
        track: AudioTrack,
        loop: bool = True,
        volume: Optional[float] = None
    ) -> None:
        """Play ambient SFX on ambient channel.

        Args:
            track: Ambient track to play
            loop: If True, loop track indefinitely
            volume: Volume override (0.0-1.0)
        """
        # STUB: Track playback state
        # Real implementation:
        # self._play_on_channel(1, track, loop=loop, volume=volume or self.config.ambient_volume)

        self._ambient_channel = track

    def stop_ambient(self) -> None:
        """Stop current ambient playback."""
        # STUB: Clear ambient channel
        self._ambient_channel = None

    def play_sfx(
        self,
        track: AudioTrack,
        volume: Optional[float] = None
    ) -> Optional[int]:
        """Play one-shot SFX on available SFX channel.

        Args:
            track: SFX track to play
            volume: Volume override (0.0-1.0)

        Returns:
            Channel ID if SFX was played, or None if all channels busy
        """
        # STUB: Find free SFX channel and track playback
        # Real implementation:
        # channel_id = self._allocate_sfx_channel()
        # if channel_id is None:
        #     return None  # All channels busy
        # self._play_on_channel(channel_id, track, loop=False, volume=volume or self.config.sfx_volume)
        # return channel_id

        # Find free channel
        for channel_id, current_track in self._sfx_channels.items():
            if current_track is None:
                self._sfx_channels[channel_id] = track
                return channel_id

        return None  # All channels busy

    def stop_all(self) -> None:
        """Stop all playback (music, ambient, SFX)."""
        # STUB: Clear all channels
        # Real implementation:
        # for channel_id in range(self.config.channels):
        #     self._stop_channel(channel_id)

        self._music_channel = None
        self._ambient_channel = None
        for channel_id in self._sfx_channels:
            self._sfx_channels[channel_id] = None

    def get_music_status(self) -> Optional[str]:
        """Get current music track status.

        Returns:
            Current music track kind, or None if no music playing
        """
        if self._music_channel:
            return self._music_channel.kind
        return None

    def get_ambient_status(self) -> Optional[str]:
        """Get current ambient track status.

        Returns:
            Current ambient track kind, or None if no ambient playing
        """
        if self._ambient_channel:
            return self._ambient_channel.kind
        return None

    def get_active_sfx_count(self) -> int:
        """Get number of active SFX channels.

        Returns:
            Number of SFX channels currently playing
        """
        return sum(1 for track in self._sfx_channels.values() if track is not None)


# ═════════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═════════════════════════════════════════════════════════════════════════


def create_audio_mixer(
    backend: str = "stub",
    channels: int = 16
) -> AudioMixer:
    """Create audio mixer with specified backend.

    Args:
        backend: Backend selection ("sounddevice", "pygame", "stub")
        channels: Number of simultaneous channels

    Returns:
        AudioMixer instance
    """
    config = AudioMixerConfig(
        backend=AudioMixerBackend(backend),
        channels=channels,
    )
    return AudioMixer(config)

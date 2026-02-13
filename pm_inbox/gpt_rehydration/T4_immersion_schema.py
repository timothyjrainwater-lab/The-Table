"""M3 Immersion schemas — Voice, audio, image, grid, and attribution contracts.

Schema-first definitions for the immersion layer:
- Transcript: STT output (text, confidence, adapter_id)
- VoicePersona: TTS persona config (persona_id, name, voice_model, speed, pitch)
- AudioTrack: Single audio track reference (track_id, kind, semantic_key, volume, loop)
- SceneAudioState: Full audio state (active_tracks, mood, transition_reason)
- ImageRequest: Image generation request (kind, semantic_key, prompt_context, dimensions)
- ImageResult: Image generation result (status, asset_id, path, content_hash)
- GridEntityPosition: Entity on grid (entity_id, x, y, label, team)
- GridRenderState: Grid visibility (visible, reason, entity_positions, dimensions)
- AttributionRecord: Asset attribution (asset_id, source, license, author)
- AttributionLedger: Collection of attribution records with schema_version

All immersion outputs are atmospheric only — never mechanical authority.
Immersion state is excluded from deterministic replay.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Voice I/O
# ---------------------------------------------------------------------------

@dataclass
class Transcript:
    """STT output — result of speech-to-text transcription.

    Atmospheric only. Never used as mechanical authority.
    """

    text: str = ""
    """Transcribed text."""

    confidence: float = 1.0
    """Confidence score (0.0–1.0)."""

    adapter_id: str = "stub"
    """Identifier of the STT adapter that produced this transcript."""

    def validate(self) -> List[str]:
        """Validate transcript fields. Returns list of errors."""
        errors = []
        if not isinstance(self.confidence, (int, float)):
            errors.append("confidence must be a number.")
        elif not (0.0 <= self.confidence <= 1.0):
            errors.append(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}."
            )
        if not self.adapter_id:
            errors.append("adapter_id must not be empty.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "adapter_id": self.adapter_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transcript":
        """Create from dictionary."""
        return cls(
            text=data.get("text", ""),
            confidence=data.get("confidence", 1.0),
            adapter_id=data.get("adapter_id", "stub"),
        )


@dataclass
class VoicePersona:
    """TTS persona configuration.

    Defines voice characteristics for text-to-speech synthesis.
    """

    persona_id: str = ""
    """Unique persona identifier."""

    name: str = ""
    """Human-readable persona name (e.g., 'Dungeon Master')."""

    voice_model: str = "default"
    """Voice model identifier for the TTS backend."""

    speed: float = 1.0
    """Speech speed multiplier (0.5–2.0)."""

    pitch: float = 1.0
    """Pitch adjustment multiplier (0.5–2.0)."""

    reference_audio: str = ""
    """Path to reference audio WAV for voice cloning (optional).

    Used by voice-cloning backends (e.g., Chatterbox). The reference clip
    should be 5–15 seconds of clean speech in the target voice.
    Backends that don't support cloning ignore this field.
    """

    exaggeration: float = 0.5
    """Emotion/expression intensity (0.0–1.0).

    Controls how expressive the synthesized voice sounds.
    Only used by backends that support emotion control (e.g., Chatterbox Original).
    Backends that don't support this ignore the field.
    """

    def validate(self) -> List[str]:
        """Validate persona fields. Returns list of errors."""
        errors = []
        if not self.persona_id:
            errors.append("persona_id must not be empty.")
        if not self.name:
            errors.append("name must not be empty.")
        if not (0.5 <= self.speed <= 2.0):
            errors.append(
                f"speed must be between 0.5 and 2.0, got {self.speed}."
            )
        if not (0.5 <= self.pitch <= 2.0):
            errors.append(
                f"pitch must be between 0.5 and 2.0, got {self.pitch}."
            )
        if not (0.0 <= self.exaggeration <= 1.0):
            errors.append(
                f"exaggeration must be between 0.0 and 1.0, got {self.exaggeration}."
            )
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d: Dict[str, Any] = {
            "persona_id": self.persona_id,
            "name": self.name,
            "voice_model": self.voice_model,
            "speed": self.speed,
            "pitch": self.pitch,
        }
        if self.reference_audio:
            d["reference_audio"] = self.reference_audio
        if self.exaggeration != 0.5:
            d["exaggeration"] = self.exaggeration
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoicePersona":
        """Create from dictionary."""
        return cls(
            persona_id=data.get("persona_id", ""),
            name=data.get("name", ""),
            voice_model=data.get("voice_model", "default"),
            speed=data.get("speed", 1.0),
            pitch=data.get("pitch", 1.0),
            reference_audio=data.get("reference_audio", ""),
            exaggeration=data.get("exaggeration", 0.5),
        )


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

_VALID_AUDIO_TRACK_KINDS = ("ambient", "combat", "sfx", "music")
_VALID_SCENE_MOODS = ("neutral", "tense", "combat", "peaceful", "dramatic")

@dataclass
class AudioTrack:
    """Single audio track reference.

    Represents one layer in the audio mix (ambient, combat music, SFX, etc.).
    """

    track_id: str = ""
    """Unique track identifier."""

    kind: str = "ambient"
    """Track kind: 'ambient' | 'combat' | 'sfx' | 'music'."""

    semantic_key: str = ""
    """Semantic identifier (e.g., 'tavern:fireplace:loop')."""

    volume: float = 1.0
    """Volume level (0.0–1.0)."""

    loop: bool = False
    """Whether the track should loop."""

    def validate(self) -> List[str]:
        """Validate track fields. Returns list of errors."""
        errors = []
        if not self.track_id:
            errors.append("track_id must not be empty.")
        if self.kind not in _VALID_AUDIO_TRACK_KINDS:
            errors.append(
                f"Invalid kind: '{self.kind}'. "
                f"Must be one of {_VALID_AUDIO_TRACK_KINDS}."
            )
        if not self.semantic_key:
            errors.append("semantic_key must not be empty.")
        if not (0.0 <= self.volume <= 1.0):
            errors.append(
                f"volume must be between 0.0 and 1.0, got {self.volume}."
            )
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "track_id": self.track_id,
            "kind": self.kind,
            "semantic_key": self.semantic_key,
            "volume": self.volume,
            "loop": self.loop,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioTrack":
        """Create from dictionary."""
        return cls(
            track_id=data.get("track_id", ""),
            kind=data.get("kind", "ambient"),
            semantic_key=data.get("semantic_key", ""),
            volume=data.get("volume", 1.0),
            loop=data.get("loop", False),
        )


@dataclass
class SceneAudioState:
    """Full audio state for a scene.

    Computed from world state by compute_scene_audio_state().
    Atmospheric only — never mechanical authority.
    """

    active_tracks: List[AudioTrack] = field(default_factory=list)
    """Currently active audio tracks."""

    mood: str = "neutral"
    """Scene mood: 'neutral' | 'tense' | 'combat' | 'peaceful' | 'dramatic'."""

    transition_reason: str = ""
    """Why the mood changed from the previous state (empty if no change)."""

    def validate(self) -> List[str]:
        """Validate audio state fields. Returns list of errors."""
        errors = []
        if self.mood not in _VALID_SCENE_MOODS:
            errors.append(
                f"Invalid mood: '{self.mood}'. "
                f"Must be one of {_VALID_SCENE_MOODS}."
            )
        for i, track in enumerate(self.active_tracks):
            track_errors = track.validate()
            for err in track_errors:
                errors.append(f"active_tracks[{i}]: {err}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "active_tracks": [t.to_dict() for t in self.active_tracks],
            "mood": self.mood,
            "transition_reason": self.transition_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneAudioState":
        """Create from dictionary."""
        tracks = [
            AudioTrack.from_dict(t) for t in data.get("active_tracks", [])
        ]
        return cls(
            active_tracks=tracks,
            mood=data.get("mood", "neutral"),
            transition_reason=data.get("transition_reason", ""),
        )


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------

_VALID_IMAGE_KINDS = ("portrait", "scene", "backdrop")

@dataclass
class ImageRequest:
    """Image generation request.

    Atmospheric only — images are never mechanical authority.
    Does NOT write to AssetStore directly (caller orchestrates storage).
    """

    kind: str = "scene"
    """Image kind: 'portrait' | 'scene' | 'backdrop'."""

    semantic_key: str = ""
    """Semantic identifier (e.g., 'npc:theron:portrait:v1')."""

    prompt_context: str = ""
    """Contextual description for image generation."""

    dimensions: Tuple[int, int] = (512, 512)
    """Target dimensions (width, height) in pixels."""

    def validate(self) -> List[str]:
        """Validate request fields. Returns list of errors."""
        errors = []
        if self.kind not in _VALID_IMAGE_KINDS:
            errors.append(
                f"Invalid kind: '{self.kind}'. "
                f"Must be one of {_VALID_IMAGE_KINDS}."
            )
        if not self.semantic_key:
            errors.append("semantic_key must not be empty.")
        if (
            not isinstance(self.dimensions, (tuple, list))
            or len(self.dimensions) != 2
        ):
            errors.append("dimensions must be a (width, height) pair.")
        elif self.dimensions[0] <= 0 or self.dimensions[1] <= 0:
            errors.append("dimensions must be positive integers.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "kind": self.kind,
            "semantic_key": self.semantic_key,
            "prompt_context": self.prompt_context,
            "dimensions": list(self.dimensions),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageRequest":
        """Create from dictionary."""
        dims = data.get("dimensions", [512, 512])
        return cls(
            kind=data.get("kind", "scene"),
            semantic_key=data.get("semantic_key", ""),
            prompt_context=data.get("prompt_context", ""),
            dimensions=tuple(dims),
        )


@dataclass
class ImageResult:
    """Image generation result.

    Returned by image adapters. Caller is responsible for
    storing in AssetStore if desired.
    """

    status: str = "placeholder"
    """Result status: 'placeholder' | 'generated' | 'cached' | 'error'."""

    asset_id: str = ""
    """Asset identifier (empty for placeholders)."""

    path: str = ""
    """Relative path to generated image file."""

    content_hash: str = ""
    """SHA256 hash of image content (empty for placeholders)."""

    error_message: str = ""
    """Error description if status == 'error'."""

    def validate(self) -> List[str]:
        """Validate result fields. Returns list of errors."""
        errors = []
        valid_statuses = ("placeholder", "generated", "cached", "error")
        if self.status not in valid_statuses:
            errors.append(
                f"Invalid status: '{self.status}'. "
                f"Must be one of {valid_statuses}."
            )
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "asset_id": self.asset_id,
            "path": self.path,
            "content_hash": self.content_hash,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageResult":
        """Create from dictionary."""
        return cls(
            status=data.get("status", "placeholder"),
            asset_id=data.get("asset_id", ""),
            path=data.get("path", ""),
            content_hash=data.get("content_hash", ""),
            error_message=data.get("error_message", ""),
        )


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------

_VALID_GRID_REASONS = ("combat_active", "combat_ended", "no_combat")

@dataclass
class GridEntityPosition:
    """Entity position on the tactical grid.

    Grid coordinates are in 5-foot squares (standard D&D 3.5 grid).
    """

    entity_id: str = ""
    """Entity identifier."""

    x: int = 0
    """X coordinate (column)."""

    y: int = 0
    """Y coordinate (row)."""

    label: str = ""
    """Display label (e.g., creature name)."""

    team: str = ""
    """Team identifier (e.g., 'party', 'hostile', 'neutral')."""

    def validate(self) -> List[str]:
        """Validate position fields. Returns list of errors."""
        errors = []
        if not self.entity_id:
            errors.append("entity_id must not be empty.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "entity_id": self.entity_id,
            "x": self.x,
            "y": self.y,
            "label": self.label,
            "team": self.team,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridEntityPosition":
        """Create from dictionary."""
        return cls(
            entity_id=data.get("entity_id", ""),
            x=data.get("x", 0),
            y=data.get("y", 0),
            label=data.get("label", ""),
            team=data.get("team", ""),
        )


@dataclass
class GridRenderState:
    """Grid visibility and entity positions.

    Computed from world state by compute_grid_state().
    Grid is visible only during active combat.
    """

    visible: bool = False
    """Whether the grid should be displayed."""

    reason: str = "no_combat"
    """Visibility reason: 'combat_active' | 'combat_ended' | 'no_combat'."""

    entity_positions: List[GridEntityPosition] = field(default_factory=list)
    """Positioned entities (sorted by entity_id for determinism)."""

    dimensions: Tuple[int, int] = (0, 0)
    """Grid dimensions (width, height) computed from entity positions."""

    def validate(self) -> List[str]:
        """Validate grid state fields. Returns list of errors."""
        errors = []
        if self.reason not in _VALID_GRID_REASONS:
            errors.append(
                f"Invalid reason: '{self.reason}'. "
                f"Must be one of {_VALID_GRID_REASONS}."
            )
        for i, pos in enumerate(self.entity_positions):
            pos_errors = pos.validate()
            for err in pos_errors:
                errors.append(f"entity_positions[{i}]: {err}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "visible": self.visible,
            "reason": self.reason,
            "entity_positions": [p.to_dict() for p in self.entity_positions],
            "dimensions": list(self.dimensions),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridRenderState":
        """Create from dictionary."""
        positions = [
            GridEntityPosition.from_dict(p)
            for p in data.get("entity_positions", [])
        ]
        dims = data.get("dimensions", [0, 0])
        return cls(
            visible=data.get("visible", False),
            reason=data.get("reason", "no_combat"),
            entity_positions=positions,
            dimensions=tuple(dims),
        )


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------

@dataclass
class AttributionRecord:
    """Asset attribution record.

    Tracks provenance and licensing for generated/bundled assets.
    """

    asset_id: str = ""
    """Asset identifier this attribution applies to."""

    source: str = ""
    """Source of the asset (e.g., 'stub_generator', 'shared_cache')."""

    license: str = ""
    """License identifier (e.g., 'CC-BY-4.0', 'proprietary', 'generated')."""

    author: str = ""
    """Author or generator identifier."""

    def validate(self) -> List[str]:
        """Validate attribution fields. Returns list of errors."""
        errors = []
        if not self.asset_id:
            errors.append("asset_id must not be empty.")
        if not self.license:
            errors.append("license must not be empty.")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "asset_id": self.asset_id,
            "source": self.source,
            "license": self.license,
            "author": self.author,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttributionRecord":
        """Create from dictionary."""
        return cls(
            asset_id=data.get("asset_id", ""),
            source=data.get("source", ""),
            license=data.get("license", ""),
            author=data.get("author", ""),
        )


@dataclass
class AttributionLedger:
    """Collection of attribution records with schema versioning.

    Saved/loaded as JSON for portability.
    """

    schema_version: str = "1.0"
    """Schema version for forward compatibility."""

    records: List[AttributionRecord] = field(default_factory=list)
    """Attribution records."""

    def validate(self) -> List[str]:
        """Validate ledger and all records. Returns list of errors."""
        errors = []
        if not self.schema_version:
            errors.append("schema_version must not be empty.")
        for i, record in enumerate(self.records):
            rec_errors = record.validate()
            for err in rec_errors:
                errors.append(f"records[{i}]: {err}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema_version": self.schema_version,
            "records": [r.to_dict() for r in self.records],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttributionLedger":
        """Create from dictionary."""
        records = [
            AttributionRecord.from_dict(r)
            for r in data.get("records", [])
        ]
        return cls(
            schema_version=data.get("schema_version", "1.0"),
            records=records,
        )

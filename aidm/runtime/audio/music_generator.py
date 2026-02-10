"""Music generator for M3 Audio Pipeline — ACE-Step and curated backends.

Provides two music generation strategies:
1. ACE-Step (generative): Text-to-music generation during prep-time (Recommended/Enhanced tiers)
2. Curated library: Royalty-free tracks from Kevin MacLeod, OpenGameArt, FreePD (Baseline tier)

Sequential loading: ACE-Step loads in Phase 4 of prep pipeline after image critique unloads.

Reference: EVAL-01 ACE-Step Validation, EVAL-02 Curated Music Library, EVAL-05 Integration Planning
"""

from pathlib import Path
from typing import Dict, List, Optional, Protocol
from dataclasses import dataclass

from aidm.schemas.audio import AudioTrack, AudioMood, AudioEnvironment


# ═════════════════════════════════════════════════════════════════════════
# Music Adapter Protocol
# ═════════════════════════════════════════════════════════════════════════


class MusicAdapter(Protocol):
    """Protocol for music generation adapters (generative or curated).

    Adapters must implement:
    - generate_track: Generate or select music for a given mood + environment
    - supports_generation: Return True if adapter can generate new tracks
    - load: Load model/library resources
    - unload: Unload model/library to free memory
    """

    def generate_track(
        self,
        mood: AudioMood,
        environment: AudioEnvironment,
        output_dir: Path,
        seed: Optional[int] = None,
    ) -> AudioTrack:
        """Generate or select music track for mood + environment.

        Args:
            mood: Scene mood (peaceful, tense, combat, dramatic, neutral)
            environment: Environment subtype (tavern, dungeon, battle, etc.)
            output_dir: Directory to write generated audio files
            seed: Random seed for deterministic generation (generative only)

        Returns:
            AudioTrack with file path and metadata
        """
        ...

    def supports_generation(self) -> bool:
        """Return True if adapter supports generative music.

        Returns:
            True for ACE-Step adapter, False for curated adapter
        """
        ...

    def load(self) -> None:
        """Load model weights or library resources.

        For ACE-Step: Load model to GPU/CPU
        For curated: Load library index from disk
        """
        ...

    def unload(self) -> None:
        """Unload model/library to free memory.

        For ACE-Step: Unload model weights, clear GPU cache
        For curated: Clear library index (minimal impact)
        """
        ...


# ═════════════════════════════════════════════════════════════════════════
# ACE-Step Music Adapter (Generative)
# ═════════════════════════════════════════════════════════════════════════


@dataclass
class ACEStepConfig:
    """Configuration for ACE-Step music generation."""

    model_path: str
    """Path to ACE-Step model weights."""

    device: str = "auto"
    """Device placement ('auto', 'cuda', 'cpu')."""

    duration_seconds: int = 60
    """Generated track duration in seconds (default: 60s for 60-120s loops)."""

    output_format: str = "ogg"
    """Output audio format (default: OGG Vorbis per EVAL-02)."""


class ACEStepMusicAdapter:
    """ACE-Step generative music adapter (Recommended/Enhanced tiers).

    Wraps ACE-Step model for prep-time music generation.
    Generates unique tracks per mood + environment combination.

    STUB IMPLEMENTATION: Returns stub AudioTrack without real generation.
    Real implementation requires ACE-Step model integration (M3.5+).
    """

    def __init__(self, config: ACEStepConfig):
        """Initialize ACE-Step adapter.

        Args:
            config: ACE-Step configuration
        """
        self.config = config
        self.model = None  # Loaded during load()
        self._track_counter = 0  # For unique file naming

    def generate_track(
        self,
        mood: AudioMood,
        environment: AudioEnvironment,
        output_dir: Path,
        seed: Optional[int] = None,
    ) -> AudioTrack:
        """Generate music track using ACE-Step.

        STUB: Returns stub track without real generation.

        Args:
            mood: Scene mood
            environment: Environment subtype
            output_dir: Output directory for generated OGG file
            seed: Random seed for deterministic generation

        Returns:
            AudioTrack with generated file metadata
        """
        # Build ACE-Step prompt from mood + environment
        prompt = self._build_prompt(mood, environment)

        # Generate unique filename
        self._track_counter += 1
        filename = f"{mood}_{environment}_{self._track_counter:03d}.ogg"
        output_path = output_dir / filename

        # STUB: Write stub OGG file (minimal header)
        # Real implementation would call ACE-Step model here:
        # audio_data = self.model.generate(prompt=prompt, duration=self.config.duration_seconds, seed=seed)
        # audio_data.save(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00")  # Stub OGG header

        # Return AudioTrack metadata
        return AudioTrack(
            kind=f"music:{mood}:{environment}",
            source_file=str(output_path.relative_to(output_path.parent.parent)),
            file_format="ogg",
            generated=True,
            model_id="ace-step-3.5b",  # EVAL-01 model selection
            generation_prompt=prompt,
            generation_seed=seed,
            duration_seconds=float(self.config.duration_seconds),
            mood_intensity=self._get_mood_intensity(mood),
        )

    def supports_generation(self) -> bool:
        """Return True (ACE-Step supports generative music)."""
        return True

    def load(self) -> None:
        """Load ACE-Step model weights.

        STUB: No-op (real implementation would load model to GPU).
        """
        # Real implementation:
        # from ace_step import ACEStepModel
        # self.model = ACEStepModel.from_pretrained(self.config.model_path, device=self.config.device)
        pass

    def unload(self) -> None:
        """Unload ACE-Step model to free GPU VRAM.

        STUB: No-op (real implementation would delete model and clear cache).
        """
        # Real implementation:
        # del self.model
        # if torch.cuda.is_available():
        #     torch.cuda.empty_cache()
        self.model = None

    def _build_prompt(self, mood: AudioMood, environment: AudioEnvironment) -> str:
        """Build ACE-Step text-to-music prompt from mood + environment.

        Uses prompt templates from EVAL-01 mood mapping matrix.

        Args:
            mood: Scene mood
            environment: Environment subtype

        Returns:
            ACE-Step prompt string
        """
        # EVAL-01 mood mapping matrix (simplified for stub)
        MOOD_PROMPTS: Dict[AudioMood, Dict[str, str]] = {
            "peaceful": {
                "tavern": "peaceful acoustic folk, medieval tavern ambience, lute and flute",
                "village": "calm village life, pastoral melody, soft percussion",
                "forest": "serene nature sounds, gentle strings, birds chirping",
            },
            "tense": {
                "dungeon": "ominous orchestral strings, dark dungeon atmosphere, low drone",
                "cave": "eerie echoes, subtle dissonance, suspenseful pads",
                "crypt": "chilling ambient, ghostly whispers, minor key strings",
            },
            "combat": {
                "battle": "epic battle music, fast drums, heroic brass, action intensity",
                "boss_fight": "intense orchestral climax, heavy percussion, dramatic tension",
                "skirmish": "aggressive tempo, clashing swords rhythm, adrenaline",
            },
            "dramatic": {
                "revelation": "dramatic orchestral swell, emotional strings, cinematic climax",
                "tragedy": "melancholic piano, sorrowful strings, slow tempo",
                "triumph": "victorious fanfare, celebratory brass, uplifting melody",
            },
            "neutral": {
                "ambient": "soft ambient pad, minimal melody, background atmosphere",
            },
        }

        # Lookup prompt or fallback to generic
        mood_prompts = MOOD_PROMPTS.get(mood, {})
        prompt = mood_prompts.get(environment, f"{mood} {environment} music")
        return prompt

    def _get_mood_intensity(self, mood: AudioMood) -> float:
        """Get mood intensity (0-10 scale) for crossfade matching.

        Args:
            mood: Scene mood

        Returns:
            Intensity value (0-10)
        """
        INTENSITIES: Dict[AudioMood, float] = {
            "peaceful": 2.0,
            "neutral": 3.0,
            "tense": 5.5,
            "dramatic": 7.0,
            "combat": 9.0,
        }
        return INTENSITIES.get(mood, 5.0)


# ═════════════════════════════════════════════════════════════════════════
# Curated Music Adapter (Fallback)
# ═════════════════════════════════════════════════════════════════════════


@dataclass
class CuratedMusicConfig:
    """Configuration for curated music library."""

    library_dir: Path
    """Path to curated music library directory."""


class CuratedMusicAdapter:
    """Curated music library adapter (Baseline tier fallback).

    Selects pre-recorded royalty-free tracks from library.
    No generation — instant track selection.

    Library sources (EVAL-02):
    - Kevin MacLeod / Incompetech (CC BY 3.0)
    - OpenGameArt.org (CC0/CC-BY)
    - FreePD.com (CC0)

    STUB IMPLEMENTATION: Returns stub track paths.
    Real implementation requires curated library curation (M3 Sprint 2).
    """

    def __init__(self, config: CuratedMusicConfig):
        """Initialize curated adapter.

        Args:
            config: Curated library configuration
        """
        self.config = config
        self.library_index: Dict[str, List[AudioTrack]] = {}

    def generate_track(
        self,
        mood: AudioMood,
        environment: AudioEnvironment,
        output_dir: Path,
        seed: Optional[int] = None,
    ) -> AudioTrack:
        """Select curated track for mood + environment.

        STUB: Returns stub track metadata.

        Args:
            mood: Scene mood
            environment: Environment subtype
            output_dir: Not used (tracks already exist in library)
            seed: Not used (deterministic selection by mood)

        Returns:
            AudioTrack for selected curated track
        """
        # STUB: Return stub track metadata
        # Real implementation would lookup from library index:
        # tracks = self.library_index.get(f"{mood}:{environment}", [])
        # selected_track = tracks[0] if tracks else self._get_fallback_track(mood)
        # return selected_track

        filename = f"curated_{mood}_{environment}.ogg"
        file_path = self.config.library_dir / filename

        return AudioTrack(
            kind=f"music:{mood}:{environment}",
            source_file=str(file_path),
            file_format="ogg",
            generated=False,
            curated_source="Kevin MacLeod",  # EVAL-02 primary source
            license="CC BY 3.0",
            attribution="Kevin MacLeod (incompetech.com)",
            duration_seconds=120.0,  # EVAL-02: 60-120s loops
            mood_intensity=self._get_mood_intensity(mood),
        )

    def supports_generation(self) -> bool:
        """Return False (curated adapter does not generate new tracks)."""
        return False

    def load(self) -> None:
        """Load curated library index from disk.

        STUB: No-op (real implementation would build index from library metadata).
        """
        # Real implementation:
        # self.library_index = self._build_library_index(self.config.library_dir)
        pass

    def unload(self) -> None:
        """Unload library index (minimal memory impact).

        STUB: No-op.
        """
        self.library_index = {}

    def _get_mood_intensity(self, mood: AudioMood) -> float:
        """Get mood intensity (0-10 scale) for crossfade matching.

        Args:
            mood: Scene mood

        Returns:
            Intensity value (0-10)
        """
        INTENSITIES: Dict[AudioMood, float] = {
            "peaceful": 2.0,
            "neutral": 3.0,
            "tense": 5.5,
            "dramatic": 7.0,
            "combat": 9.0,
        }
        return INTENSITIES.get(mood, 5.0)


# ═════════════════════════════════════════════════════════════════════════
# Music Generator (Orchestrator)
# ═════════════════════════════════════════════════════════════════════════


class MusicGenerator:
    """Music generator orchestrator for prep-time asset generation.

    Selects ACE-Step or curated adapter based on hardware tier.
    Manages model loading/unloading during sequential prep pipeline.

    Usage (prep pipeline Phase 4):
        generator = MusicGenerator.from_tier_config(tier_config)
        generator.load()
        for scene in campaign.scenes:
            track = generator.generate_track(scene.mood, scene.environment, output_dir)
        generator.unload()
    """

    def __init__(self, adapter: MusicAdapter):
        """Initialize music generator with adapter.

        Args:
            adapter: Music adapter (ACE-Step or curated)
        """
        self.adapter = adapter

    @classmethod
    def from_tier_config(
        cls,
        tier_config,  # AudioTierConfig
        ace_step_model_path: Optional[str] = None,
        curated_library_dir: Optional[Path] = None,
    ) -> "MusicGenerator":
        """Create music generator from hardware tier config.

        Args:
            tier_config: AudioTierConfig from tier detection
            ace_step_model_path: Path to ACE-Step model weights (if generative enabled)
            curated_library_dir: Path to curated library (fallback)

        Returns:
            MusicGenerator with appropriate adapter
        """
        if tier_config.use_generative_music and ace_step_model_path:
            # Use ACE-Step adapter
            config = ACEStepConfig(model_path=ace_step_model_path)
            adapter = ACEStepMusicAdapter(config)
        else:
            # Use curated adapter (fallback)
            library_dir = curated_library_dir or Path("assets/music/curated")
            config = CuratedMusicConfig(library_dir=library_dir)
            adapter = CuratedMusicAdapter(config)

        return cls(adapter=adapter)

    def generate_track(
        self,
        mood: AudioMood,
        environment: AudioEnvironment,
        output_dir: Path,
        seed: Optional[int] = None,
    ) -> AudioTrack:
        """Generate or select music track.

        Delegates to underlying adapter (ACE-Step or curated).

        Args:
            mood: Scene mood
            environment: Environment subtype
            output_dir: Output directory for generated files
            seed: Random seed for deterministic generation

        Returns:
            AudioTrack metadata
        """
        return self.adapter.generate_track(mood, environment, output_dir, seed)

    def supports_generation(self) -> bool:
        """Return True if adapter supports generative music.

        Returns:
            True for ACE-Step, False for curated
        """
        return self.adapter.supports_generation()

    def load(self) -> None:
        """Load adapter resources (model weights or library index)."""
        self.adapter.load()

    def unload(self) -> None:
        """Unload adapter to free memory (GPU VRAM or RAM)."""
        self.adapter.unload()

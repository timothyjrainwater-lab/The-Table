"""SFX library for M3 Audio Pipeline — Curated sound effects with semantic key lookup.

Provides curated SFX library with:
- Semantic key taxonomy (combat:melee:sword:hit, ambient:peaceful:tavern, etc.)
- Round-robin variant selection (3-5 variants per key to prevent repetition)
- Pre-loading for low-latency runtime playback

Library sources (EVAL-03):
- Sonniss GDC Bundles (royalty-free, primary)
- Freesound.org CC0 (gap-filling)
- Kenney.nl (UI/feedback)
- OpenGameArt.org (fantasy-specific)

Generative SFX is BLOCKED by licensing (no Apache 2.0 / MIT models exist as of Feb 2026).

Reference: EVAL-03 SFX Library Specification
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from aidm.schemas.audio import AudioTrack


# ═════════════════════════════════════════════════════════════════════════
# SFX Semantic Key Taxonomy
# ═════════════════════════════════════════════════════════════════════════


# EVAL-03 defines 3-5 level hierarchy for semantic keys:
# combat:melee:sword:hit
# combat:magic:fire:impact
# ambient:peaceful:tavern
# event:door:open:wood
# creature:dragon:roar

# Full taxonomy implemented in EVAL-03 lines 406-422.
# Stub implementation supports basic keys for integration testing.


# ═════════════════════════════════════════════════════════════════════════
# SFX Library
# ═════════════════════════════════════════════════════════════════════════


@dataclass
class SFXLibraryConfig:
    """Configuration for curated SFX library."""

    library_dir: Path
    """Path to curated SFX library directory."""

    preload_all: bool = True
    """If True, preload all SFX into RAM for instant playback (20-65 MB per EVAL-03)."""


class SFXLibrary:
    """Curated SFX library with semantic key lookup and round-robin variant selection.

    Manages curated sound effects library (200-500 sounds, EVAL-03).
    Supports semantic key lookup (e.g., "combat:melee:sword:hit") with 3-5 variants per key.

    STUB IMPLEMENTATION: Returns stub AudioTrack without real file loading.
    Real implementation requires SFX library curation (M3 Sprint 3).
    """

    def __init__(self, config: SFXLibraryConfig):
        """Initialize SFX library.

        Args:
            config: SFX library configuration
        """
        self.config = config
        self.library_index: Dict[str, List[AudioTrack]] = {}  # semantic_key → variants
        self.round_robin_state: Dict[str, int] = {}  # semantic_key → current variant index

    def get_sfx(self, semantic_key: str) -> Optional[AudioTrack]:
        """Get SFX by semantic key with round-robin variant selection.

        Automatically rotates through variants to prevent immediate repetition.

        Args:
            semantic_key: Semantic key (e.g., "combat:melee:sword:hit")

        Returns:
            AudioTrack for selected variant, or None if key not found
        """
        variants = self.library_index.get(semantic_key, [])
        if not variants:
            return None

        # Get current round-robin index
        current_index = self.round_robin_state.get(semantic_key, 0)

        # Select variant
        variant = variants[current_index % len(variants)]

        # Increment round-robin index for next call
        self.round_robin_state[semantic_key] = current_index + 1

        return variant

    def get_sfx_variant(self, semantic_key: str, variant_index: int) -> Optional[AudioTrack]:
        """Get specific SFX variant by index (for testing/debugging).

        Args:
            semantic_key: Semantic key
            variant_index: Variant index (0-based)

        Returns:
            AudioTrack for specified variant, or None if not found
        """
        variants = self.library_index.get(semantic_key, [])
        if not variants or variant_index >= len(variants):
            return None

        return variants[variant_index]

    def get_variant_count(self, semantic_key: str) -> int:
        """Get number of variants for a semantic key.

        Args:
            semantic_key: Semantic key

        Returns:
            Number of variants (0 if key not found)
        """
        variants = self.library_index.get(semantic_key, [])
        return len(variants)

    def load(self) -> None:
        """Load SFX library index and optionally preload audio files.

        STUB: Builds stub library index with basic keys.
        Real implementation would scan library_dir and build index from metadata.
        """
        # STUB: Build minimal library index for integration testing
        # Real implementation:
        # self.library_index = self._build_library_index(self.config.library_dir)
        # if self.config.preload_all:
        #     self._preload_audio_files()

        self.library_index = self._build_stub_index()

    def unload(self) -> None:
        """Unload SFX library (free RAM).

        STUB: Clears library index.
        """
        self.library_index = {}
        self.round_robin_state = {}

    def _build_stub_index(self) -> Dict[str, List[AudioTrack]]:
        """Build stub library index for integration testing.

        Returns:
            Stub library index with basic semantic keys
        """
        # EVAL-03 semantic key examples (subset for stub)
        stub_keys = [
            # Combat SFX
            "combat:melee:sword:hit",
            "combat:melee:sword:miss",
            "combat:melee:axe:hit",
            "combat:ranged:bow:release",
            "combat:ranged:bow:impact",
            "combat:magic:fire:impact",
            "combat:magic:lightning:crack",
            "combat:hit:critical",
            "combat:death:humanoid",
            # Ambient SFX
            "ambient:peaceful:tavern",
            "ambient:peaceful:nature",
            "ambient:tense:dungeon",
            "ambient:fire:hearth",
            # Event SFX
            "event:door:open:wood",
            "event:door:open:stone",
            "event:chest:open",
            "event:trap:trigger",
            "event:dice:roll",
            "event:gold:coins",
            "event:footstep:stone",
            # Creature SFX
            "creature:dragon:roar",
            "creature:wolf:growl",
        ]

        index = {}
        for key in stub_keys:
            # Create 3 variants per key (EVAL-03 specifies 3-5 variants)
            variants = []
            for i in range(3):
                filename = f"{key.replace(':', '_')}_variant_{i+1:02d}.ogg"
                file_path = self.config.library_dir / filename

                track = AudioTrack(
                    kind=f"sfx:{key}",
                    source_file=str(file_path),
                    file_format="ogg",
                    generated=False,
                    curated_source="Sonniss GDC 2024",  # EVAL-03 primary source
                    license="Royalty-free",
                    duration_seconds=2.0,  # EVAL-03: most SFX <2s
                    variant_group=key,
                    variant_index=i,
                )
                variants.append(track)

            index[key] = variants

        return index


# ═════════════════════════════════════════════════════════════════════════
# SFX Event Mapping Helpers
# ═════════════════════════════════════════════════════════════════════════


# EVAL-05 defines event-to-SFX mapping for combat and environment events.
# These mappings are used by the runtime narrative engine to trigger SFX.


COMBAT_SFX_MAP: Dict[str, str] = {
    "attack_hit_melee_sword": "combat:melee:sword:hit",
    "attack_miss_melee_sword": "combat:melee:sword:miss",
    "attack_hit_melee_axe": "combat:melee:axe:hit",
    "attack_hit_ranged_bow": "combat:ranged:bow:impact",
    "spell_cast_fire": "combat:magic:fire:impact",
    "spell_cast_lightning": "combat:magic:lightning:crack",
    "hit_critical": "combat:hit:critical",
    "death_humanoid": "combat:death:humanoid",
}
"""Combat event to SFX semantic key mapping.

Maps game events (attack_hit_melee_sword) to semantic keys (combat:melee:sword:hit).
"""


ENVIRONMENT_SFX_MAP: Dict[str, str] = {
    "door_open_wood": "event:door:open:wood",
    "door_open_stone": "event:door:open:stone",
    "chest_open": "event:chest:open",
    "trap_trigger": "event:trap:trigger",
    "footstep_stone": "event:footstep:stone",
    "gold_coins": "event:gold:coins",
    "dice_roll": "event:dice:roll",
}
"""Environment event to SFX semantic key mapping."""


AMBIENT_SFX_MAP: Dict[tuple, str] = {
    ("peaceful", "tavern"): "ambient:peaceful:tavern",
    ("peaceful", "forest"): "ambient:peaceful:nature",
    ("tense", "dungeon"): "ambient:tense:dungeon",
}
"""Ambient SFX mapping by (mood, environment) tuple."""


def get_combat_sfx_key(event_type: str) -> Optional[str]:
    """Get SFX semantic key for combat event.

    Args:
        event_type: Combat event type (e.g., "attack_hit_melee_sword")

    Returns:
        Semantic key or None if event not mapped
    """
    return COMBAT_SFX_MAP.get(event_type)


def get_environment_sfx_key(event_type: str) -> Optional[str]:
    """Get SFX semantic key for environment event.

    Args:
        event_type: Environment event type (e.g., "door_open_wood")

    Returns:
        Semantic key or None if event not mapped
    """
    return ENVIRONMENT_SFX_MAP.get(event_type)


def get_ambient_sfx_key(mood: str, environment: str) -> Optional[str]:
    """Get SFX semantic key for ambient sound by mood + environment.

    Args:
        mood: Scene mood (e.g., "peaceful", "tense")
        environment: Environment type (e.g., "tavern", "dungeon")

    Returns:
        Semantic key or None if combination not mapped
    """
    return AMBIENT_SFX_MAP.get((mood, environment))

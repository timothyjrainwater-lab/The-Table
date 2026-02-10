"""Tests for M3 Audio Pipeline modules.

Tests audio schemas, tier detection, music generator, SFX library, and audio mixer stubs.

Reference: WO-M3-AUDIO-INT-01
"""

import pytest
from pathlib import Path

from aidm.schemas.audio import (
    AudioTrack,
    AudioTierConfig,
    AudioAttribution,
    AudioAttributionLedger,
)
from aidm.runtime.audio.tier_detection import detect_audio_tier
from aidm.runtime.audio.music_generator import (
    MusicGenerator,
    ACEStepMusicAdapter,
    CuratedMusicAdapter,
    ACEStepConfig,
    CuratedMusicConfig,
)
from aidm.runtime.audio.sfx_library import (
    SFXLibrary,
    SFXLibraryConfig,
    COMBAT_SFX_MAP,
    get_combat_sfx_key,
)
from aidm.runtime.audio.audio_mixer import AudioMixer, AudioMixerConfig, AudioMixerBackend


# ═════════════════════════════════════════════════════════════════════════
# Audio Schema Tests
# ═════════════════════════════════════════════════════════════════════════


def test_audio_track_creation():
    """Test AudioTrack creation with minimal fields."""
    track = AudioTrack(
        kind="music:peaceful:tavern",
        source_file="Music/peaceful_tavern_001.ogg",
    )

    assert track.kind == "music:peaceful:tavern"
    assert track.source_file == "Music/peaceful_tavern_001.ogg"
    assert track.file_format == "ogg"
    assert track.generated is False


def test_audio_track_generative_metadata():
    """Test AudioTrack with generative metadata."""
    track = AudioTrack(
        kind="music:combat:boss_fight",
        source_file="Music/combat_boss_fight_001.ogg",
        generated=True,
        model_id="ace-step-3.5b",
        generation_prompt="intense orchestral climax, heavy percussion",
        generation_seed=42,
    )

    assert track.generated is True
    assert track.model_id == "ace-step-3.5b"
    assert track.generation_prompt == "intense orchestral climax, heavy percussion"
    assert track.generation_seed == 42


def test_audio_track_curated_metadata():
    """Test AudioTrack with curated metadata."""
    track = AudioTrack(
        kind="music:peaceful:village",
        source_file="Music/curated_peaceful_village.ogg",
        generated=False,
        curated_source="Kevin MacLeod",
        license="CC BY 3.0",
        attribution="Kevin MacLeod (incompetech.com)",
    )

    assert track.generated is False
    assert track.curated_source == "Kevin MacLeod"
    assert track.license == "CC BY 3.0"
    assert track.attribution == "Kevin MacLeod (incompetech.com)"


def test_audio_track_serialization():
    """Test AudioTrack to_dict/from_dict round-trip."""
    original = AudioTrack(
        kind="sfx:combat:melee:sword:hit",
        source_file="SFX/combat_sword_hit_01.ogg",
        variant_group="combat:melee:sword:hit",
        variant_index=0,
    )

    data = original.to_dict()
    restored = AudioTrack.from_dict(data)

    assert restored.kind == original.kind
    assert restored.source_file == original.source_file
    assert restored.variant_group == original.variant_group
    assert restored.variant_index == original.variant_index


def test_audio_tier_config():
    """Test AudioTierConfig creation."""
    config = AudioTierConfig(
        tier="recommended",
        vram_gb=7.5,
        use_generative_music=True,
        use_generative_sfx=False,
    )

    assert config.tier == "recommended"
    assert config.vram_gb == 7.5
    assert config.use_generative_music is True
    assert config.use_generative_sfx is False


def test_audio_attribution():
    """Test AudioAttribution formatting."""
    attr = AudioAttribution(
        asset_id="music_peaceful_tavern.ogg",
        asset_type="music",
        title="Minstrel Dance",
        artist="Kevin MacLeod",
        source="incompetech.com",
        license="CC BY 3.0",
        url="https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100731",
    )

    formatted = attr.format_attribution()
    assert "Minstrel Dance" in formatted
    assert "Kevin MacLeod" in formatted
    assert "CC BY 3.0" in formatted
    assert "incompetech.com" in formatted


def test_audio_attribution_ledger():
    """Test AudioAttributionLedger."""
    ledger = AudioAttributionLedger()

    # Add music attribution
    ledger.add_attribution(AudioAttribution(
        asset_id="track_001.ogg",
        asset_type="music",
        title="Test Track",
        artist="Test Artist",
        source="Test Source",
        license="CC BY 3.0",
    ))

    # Add SFX attribution
    ledger.add_attribution(AudioAttribution(
        asset_id="sfx_001.ogg",
        asset_type="sfx",
        source="Sonniss GDC",
        license="Royalty-free",
    ))

    music_attrs = ledger.get_attributions_by_type("music")
    sfx_attrs = ledger.get_attributions_by_type("sfx")

    assert len(music_attrs) == 1
    assert len(sfx_attrs) == 1

    # Generate attribution text
    attribution_text = ledger.generate_attribution_text()
    assert "MUSIC:" in attribution_text
    assert "SOUND EFFECTS:" in attribution_text


# ═════════════════════════════════════════════════════════════════════════
# Tier Detection Tests
# ═════════════════════════════════════════════════════════════════════════


def test_tier_detection_cpu_only():
    """Test tier detection returns baseline for CPU-only systems."""
    # detect_audio_tier will return baseline if no GPU detected
    config = detect_audio_tier()

    # On CPU-only systems, tier should be baseline
    if config.vram_gb == 0.0:
        assert config.tier == "baseline"
        assert config.use_generative_music is False


def test_tier_detection_user_override():
    """Test user override forces curated mode."""
    config = detect_audio_tier(user_override="curated_only")

    assert config.use_generative_music is False
    assert config.user_override == "curated_only"


# ═════════════════════════════════════════════════════════════════════════
# Music Generator Tests
# ═════════════════════════════════════════════════════════════════════════


def test_ace_step_adapter_stub(tmp_path):
    """Test ACE-Step adapter stub generation."""
    config = ACEStepConfig(model_path="/tmp/ace-step")
    adapter = ACEStepMusicAdapter(config)

    assert adapter.supports_generation() is True

    # Load (stub no-op)
    adapter.load()

    # Generate track (stub)
    track = adapter.generate_track(
        mood="peaceful",
        environment="tavern",
        output_dir=tmp_path,
        seed=42,
    )

    assert track.kind == "music:peaceful:tavern"
    assert track.generated is True
    assert track.model_id == "ace-step-3.5b"
    assert track.generation_seed == 42
    assert "peaceful acoustic folk" in track.generation_prompt

    # Unload (stub no-op)
    adapter.unload()


def test_curated_adapter_stub():
    """Test curated music adapter stub selection."""
    config = CuratedMusicConfig(library_dir=Path("/tmp/music"))
    adapter = CuratedMusicAdapter(config)

    assert adapter.supports_generation() is False

    # Load (stub no-op)
    adapter.load()

    # Select track (stub)
    track = adapter.generate_track(
        mood="tense",
        environment="dungeon",
        output_dir=Path("/tmp"),
        seed=None,
    )

    assert track.kind == "music:tense:dungeon"
    assert track.generated is False
    assert track.curated_source == "Kevin MacLeod"
    assert track.license == "CC BY 3.0"

    # Unload (stub no-op)
    adapter.unload()


def test_music_generator_orchestrator(tmp_path):
    """Test MusicGenerator orchestrator with ACE-Step adapter."""
    from aidm.schemas.audio import AudioTierConfig

    tier_config = AudioTierConfig(
        tier="recommended",
        vram_gb=7.0,
        use_generative_music=True,
    )

    generator = MusicGenerator.from_tier_config(
        tier_config=tier_config,
        ace_step_model_path="/tmp/ace-step",
    )

    assert generator.supports_generation() is True

    generator.load()

    track = generator.generate_track(
        mood="combat",
        environment="battle",
        output_dir=tmp_path,
        seed=42,
    )

    assert track.kind == "music:combat:battle"
    assert track.generated is True

    generator.unload()


# ═════════════════════════════════════════════════════════════════════════
# SFX Library Tests
# ═════════════════════════════════════════════════════════════════════════


def test_sfx_library_stub():
    """Test SFX library stub with semantic key lookup."""
    config = SFXLibraryConfig(library_dir=Path("/tmp/sfx"))
    library = SFXLibrary(config)

    # Load stub library
    library.load()

    # Check variant count (doesn't consume round-robin counter)
    variant_count = library.get_variant_count("combat:melee:sword:hit")
    assert variant_count == 3  # Stub creates 3 variants per key

    # Test round-robin selection (starts at index 0)
    sfx1 = library.get_sfx("combat:melee:sword:hit")
    sfx2 = library.get_sfx("combat:melee:sword:hit")
    sfx3 = library.get_sfx("combat:melee:sword:hit")
    sfx4 = library.get_sfx("combat:melee:sword:hit")  # Should wrap to variant 0

    assert sfx1 is not None
    assert sfx1.kind == "sfx:combat:melee:sword:hit"
    assert sfx1.variant_group == "combat:melee:sword:hit"
    assert sfx1.generated is False

    # Verify round-robin progression (first call returns index 0)
    assert sfx1.variant_index == 0
    assert sfx2.variant_index == 1
    assert sfx3.variant_index == 2
    assert sfx4.variant_index == 0  # Wrapped back to start

    # Unload
    library.unload()


def test_sfx_library_missing_key():
    """Test SFX library returns None for missing keys."""
    config = SFXLibraryConfig(library_dir=Path("/tmp/sfx"))
    library = SFXLibrary(config)
    library.load()

    sfx = library.get_sfx("nonexistent:key")
    assert sfx is None


def test_combat_sfx_mapping():
    """Test combat event to SFX key mapping."""
    key = get_combat_sfx_key("attack_hit_melee_sword")
    assert key == "combat:melee:sword:hit"

    key = get_combat_sfx_key("spell_cast_fire")
    assert key == "combat:magic:fire:impact"

    key = get_combat_sfx_key("nonexistent_event")
    assert key is None


# ═════════════════════════════════════════════════════════════════════════
# Audio Mixer Tests
# ═════════════════════════════════════════════════════════════════════════


def test_audio_mixer_stub():
    """Test audio mixer stub playback tracking."""
    config = AudioMixerConfig(backend=AudioMixerBackend.STUB, channels=16)
    mixer = AudioMixer(config)

    # Play music
    music_track = AudioTrack(
        kind="music:peaceful:tavern",
        source_file="Music/peaceful_tavern.ogg",
    )
    mixer.play_music(music_track, loop=True, volume=0.5)

    assert mixer.get_music_status() == "music:peaceful:tavern"

    # Play ambient
    ambient_track = AudioTrack(
        kind="ambient:peaceful:tavern",
        source_file="SFX/ambient_tavern.ogg",
    )
    mixer.play_ambient(ambient_track, loop=True, volume=0.3)

    assert mixer.get_ambient_status() == "ambient:peaceful:tavern"

    # Play SFX
    sfx_track = AudioTrack(
        kind="sfx:combat:melee:sword:hit",
        source_file="SFX/sword_hit_01.ogg",
    )
    channel_id = mixer.play_sfx(sfx_track, volume=0.7)

    assert channel_id is not None
    assert mixer.get_active_sfx_count() == 1

    # Crossfade music
    new_music = AudioTrack(
        kind="music:combat:battle",
        source_file="Music/combat_battle.ogg",
    )
    mixer.crossfade_music(new_music, duration_ms=2000)

    assert mixer.get_music_status() == "music:combat:battle"

    # Stop all
    mixer.stop_all()

    assert mixer.get_music_status() is None
    assert mixer.get_ambient_status() is None
    assert mixer.get_active_sfx_count() == 0


def test_audio_mixer_sfx_channel_exhaustion():
    """Test SFX playback when all channels are busy."""
    config = AudioMixerConfig(backend=AudioMixerBackend.STUB, channels=4)  # Only 2 SFX channels
    mixer = AudioMixer(config)

    sfx_track = AudioTrack(kind="sfx:test", source_file="test.ogg")

    # Play SFX on both available channels (channels 2-3)
    channel1 = mixer.play_sfx(sfx_track)
    channel2 = mixer.play_sfx(sfx_track)

    assert channel1 is not None
    assert channel2 is not None
    assert mixer.get_active_sfx_count() == 2

    # All channels busy — next SFX should fail
    channel3 = mixer.play_sfx(sfx_track)
    assert channel3 is None  # No free channels

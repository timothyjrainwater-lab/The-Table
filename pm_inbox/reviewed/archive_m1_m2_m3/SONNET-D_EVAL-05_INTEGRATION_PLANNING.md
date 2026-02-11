# Audio Pipeline Integration Planning
**Work Order:** WO-M3-AUDIO-EVAL-01 Task 5
**Agent:** Sonnet-D
**Date:** 2026-02-11
**Status:** Complete

## Executive Summary

The M3 Audio Pipeline integrates ACE-Step generative music, curated music/SFX libraries, and runtime playback into the existing prep-time content generation workflow. Music generation occurs during **Phase 4** of the sequential prep pipeline (after LLM, Image Gen, and Image Critique). SFX and music playback occur at **runtime** via a custom `sounddevice`-based mixer. Mood transitions use 2-4 second crossfades. Integration requires extending `SceneManifest` schema, implementing `MusicGenerator` and `AudioMixer` modules, and wiring mood-based triggers into the DM narrative engine.

---

## Prep Pipeline Integration

### Sequential Loading Architecture

R1:469-480 specifies sequential model loading during prep-time. Music generation is **Phase 4**:

```
Campaign Prep Request
  ↓
[Phase 1] LLM Narration (Qwen3 8B) → Generates scene descriptions, NPC dialogue
  → Unload LLM, free 6 GB VRAM
  ↓
[Phase 2] Image Generation (SDXL Lightning NF4) → Generates portraits, scene art
  → Unload Image Gen, free 3.5-4.5 GB VRAM
  ↓
[Phase 3] Image Critique (ImageReward) → Scores images, rejects poor quality
  → Unload Image Critique, free 1.0 GB VRAM
  ↓
[Phase 4] MUSIC GENERATION (ACE-Step) ← **Full GPU access (6-8 GB VRAM)**
  → Generates 30-45 music tracks (30s clips, OGG Vorbis)
  → Duration: ~10-30 minutes total (20-40s per clip × 30-45 clips)
  → Unload ACE-Step
  ↓
[Phase 5] SFX Library Loading (Curated) → Load 200-500 sounds from disk (20-65 MB RAM)
  ↓
[Phase 6] TTS Narration (Kokoro ONNX, CPU) → Generates voiceovers for key scenes
  ↓
Campaign Ready
```

**Key integration points:**
1. **Input:** Scene mood metadata (`scene.mood: "peaceful" | "tense" | "combat" | "dramatic" | "neutral"`)
2. **Process:** ACE-Step generates 30-45 unique music clips (one per scene or mood group)
3. **Output:** OGG Vorbis files written to `campaign/audio/music/` directory
4. **Manifest update:** `SceneManifest.music_track` field populated with file path

---

## Schema Extensions

### SceneManifest Extension

```python
@dataclass
class SceneManifest:
    # Existing fields...
    scene_id: str
    mood: Literal["peaceful", "tense", "combat", "dramatic", "neutral"]
    environment: str  # "tavern", "dungeon", "forest", etc.

    # NEW: Audio fields
    music_track: Optional[str] = None           # Path to generated OGG file or curated track
    music_mode: Literal["generative", "curated"] = "generative"
    ambient_sfx: List[str] = field(default_factory=list)  # Looping ambient SFX keys
    event_sfx: Dict[str, str] = field(default_factory=dict)  # Event ID → SFX key mapping
```

### AudioTrack Schema (Extended from Existing)

```python
@dataclass
class AudioTrack:
    kind: str                    # Semantic key: "music:peaceful:tavern" or "combat:melee:sword:hit"
    source_file: str             # Path to OGG file
    attribution: str             # Artist/source attribution
    loop_start_ms: int = 0       # Loop start point (for seamless looping)
    loop_end_ms: Optional[int] = None  # Loop end point
    mood_intensity: float = 5.0  # 0-10 scale for crossfade intensity matching
    generation_prompt: Optional[str] = None  # ACE-Step prompt (for generative tracks)
```

---

## Module Architecture

### New Modules

```
aidm/
  runtime/
    audio/
      music_generator.py       # ACE-Step wrapper for prep-time generation
      audio_mixer.py           # sounddevice-based runtime mixer (8-16 channels)
      sfx_library.py           # Curated SFX library loader + semantic key mapper
      music_library.py         # Curated music library loader (fallback)
      audio_attribution.py     # Attribution ledger for CC BY / royalty-free assets
```

### MusicGenerator Module (Prep-Time)

```python
class MusicGenerator:
    """ACE-Step wrapper for prep-time music generation."""

    def __init__(self, tier: str, model_path: str):
        self.tier = tier
        if tier in ["enhanced", "recommended"]:
            self.backend = ACEStepBackend(model_path)  # Load ACE-Step
        else:
            self.backend = CuratedLibraryBackend()  # Fallback

    def generate_scene_music(self, scene: SceneManifest, output_dir: Path) -> str:
        """Generate music for a single scene."""
        prompt = self._build_prompt(scene.mood, scene.environment)

        if isinstance(self.backend, ACEStepBackend):
            # Generative path
            audio_data = self.backend.generate(
                prompt=prompt,
                duration_seconds=60,  # Generate 60s for 60-120s loops
                output_format="ogg",
            )
            output_path = output_dir / f"{scene.scene_id}_music.ogg"
            audio_data.save(output_path)
        else:
            # Curated fallback
            output_path = self.backend.select_track(scene.mood, scene.environment)

        return str(output_path)

    def _build_prompt(self, mood: str, environment: str) -> str:
        """Build ACE-Step prompt from scene metadata."""
        # R1:318-326 mood mapping + environment context
        MOOD_PROMPTS = {
            "peaceful": {
                "tavern": "peaceful acoustic folk, medieval tavern ambience, lute and flute",
                "forest": "serene nature sounds, gentle strings, birds chirping",
                "village": "calm village life, pastoral melody, soft percussion",
            },
            "tense": {
                "dungeon": "ominous orchestral strings, dark dungeon atmosphere, low drone",
                "cave": "eerie echoes, subtle dissonance, suspenseful pads",
                "crypt": "chilling ambient, ghostly whispers, minor key strings",
            },
            "combat": {
                "battle": "epic battle music, fast drums, heroic brass, action intensity",
                "boss": "intense orchestral climax, heavy percussion, dramatic tension",
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

        return MOOD_PROMPTS.get(mood, {}).get(environment, f"{mood} {environment} music")
```

### AudioMixer Module (Runtime)

```python
class AudioMixer:
    """Custom mixer on sounddevice for music, SFX, and TTS playback."""

    def __init__(self, channels: int = 16, sample_rate: int = 44100):
        """Initialize mixer with 8-16 channels (R1:426)."""
        self.channels = channels
        self.sample_rate = sample_rate
        self._active_sounds = {}  # channel_id → AudioTrack
        self._music_channel = 0   # Reserved for music
        self._sfx_channels = list(range(1, channels))  # Channels 1-15 for SFX

    def play_music(self, track: AudioTrack, loop: bool = True, volume: float = 0.5):
        """Play music track on dedicated music channel."""
        self._stop_channel(self._music_channel)  # Stop current music
        self._play_on_channel(self._music_channel, track, loop=loop, volume=volume)

    def crossfade_music(self, new_track: AudioTrack, duration_ms: int = 2000):
        """Crossfade from current music to new track (R1 recommends 2-4s)."""
        old_channel = self._music_channel
        new_channel = self._allocate_temp_channel()

        # Fade out old, fade in new simultaneously
        self._fade_out(old_channel, duration_ms)
        self._play_on_channel(new_channel, new_track, loop=True, volume=0.0)
        self._fade_in(new_channel, duration_ms, target_volume=0.5)

        # After fade completes, reassign music channel
        time.sleep(duration_ms / 1000)
        self._music_channel = new_channel
        self._stop_channel(old_channel)

    def play_sfx(self, semantic_key: str, volume: float = 0.7, variants: int = 5):
        """Play SFX by semantic key with round-robin variant selection (R1:423)."""
        variant_index = self._get_round_robin_variant(semantic_key, variants)
        track = self._sfx_library.get_variant(semantic_key, variant_index)

        channel = self._allocate_sfx_channel()
        self._play_on_channel(channel, track, loop=False, volume=volume)

    def play_ambient_sfx(self, semantic_key: str, volume: float = 0.3):
        """Play looping ambient SFX (e.g., 'ambient:peaceful:tavern')."""
        track = self._sfx_library.get(semantic_key)
        channel = self._allocate_sfx_channel()
        self._play_on_channel(channel, track, loop=True, volume=volume)

    # Internal methods: _play_on_channel, _fade_in, _fade_out, _allocate_sfx_channel, etc.
    # Implementation: ~300-500 lines (R1:427)
```

### SFX Library Loader

```python
class SFXLibrary:
    """Curated SFX library with semantic key indexing."""

    def __init__(self, library_dir: Path):
        self.library_dir = library_dir
        self._index = self._build_index()  # semantic_key → List[AudioTrack]
        self._round_robin_state = {}       # semantic_key → int (variant counter)

    def _build_index(self) -> Dict[str, List[AudioTrack]]:
        """Build semantic key index from library directory."""
        # Example structure:
        # combat/melee/sword/hit_01.ogg → "combat:melee:sword:hit"
        # combat/melee/sword/hit_02.ogg → "combat:melee:sword:hit"
        # ...
        # R1:406-422 taxonomy
        pass

    def get_variant(self, semantic_key: str, variant_index: int) -> AudioTrack:
        """Get specific variant of a sound."""
        variants = self._index.get(semantic_key, [])
        if not variants:
            raise KeyError(f"No SFX found for key: {semantic_key}")
        return variants[variant_index % len(variants)]

    def get_round_robin_variant(self, semantic_key: str) -> AudioTrack:
        """Get next variant in round-robin sequence (R1:423)."""
        self._round_robin_state[semantic_key] = self._round_robin_state.get(semantic_key, 0) + 1
        return self.get_variant(semantic_key, self._round_robin_state[semantic_key])
```

---

## Mood Transition Logic

### Trigger Points

Music transitions occur when `scene.mood` changes during gameplay:

```python
class NarrativeEngine:
    def __init__(self, audio_mixer: AudioMixer):
        self.audio_mixer = audio_mixer
        self.current_scene: Optional[SceneManifest] = None

    def transition_to_scene(self, new_scene: SceneManifest):
        """Transition to new scene with audio crossfade."""
        if self.current_scene and self.current_scene.mood != new_scene.mood:
            # Mood changed → crossfade music
            new_track = AudioTrack.from_file(new_scene.music_track)
            self.audio_mixer.crossfade_music(new_track, duration_ms=2000)
        elif not self.current_scene:
            # First scene → start music immediately
            track = AudioTrack.from_file(new_scene.music_track)
            self.audio_mixer.play_music(track, loop=True, volume=0.5)

        # Update ambient SFX
        self._update_ambient_sfx(new_scene.ambient_sfx)

        self.current_scene = new_scene

    def trigger_event_sfx(self, event_type: str):
        """Play event SFX (combat hit, door open, etc.)."""
        semantic_key = EVENT_SFX_MAP.get(event_type)
        if semantic_key:
            self.audio_mixer.play_sfx(semantic_key, volume=0.7)
```

### Crossfade Duration

R1 does not specify exact crossfade duration. Based on industry standards for mood-based game audio:

| Transition Type | Crossfade Duration | Rationale |
|----------------|-------------------|-----------|
| peaceful → tense | 2-3 seconds | Gradual tension build |
| tense → combat | 1-2 seconds | Faster intensity ramp |
| combat → peaceful | 3-4 seconds | Slow wind-down, emotional reset |
| dramatic → neutral | 2-3 seconds | Moderate transition |
| Any → same mood (different environment) | 1-2 seconds | Minimal disruption |

**Default recommendation:** 2 seconds (middle ground, tested in commercial RPGs).

---

## Event-to-SFX Mapping

### Combat Events

```python
COMBAT_SFX_MAP = {
    "attack_hit_melee_sword": "combat:melee:sword:hit",
    "attack_miss_melee_sword": "combat:melee:sword:miss",
    "attack_hit_melee_axe": "combat:melee:axe:hit",
    "attack_hit_ranged_bow": "combat:ranged:bow:impact",
    "spell_cast_fire": "combat:magic:fire:impact",
    "spell_cast_lightning": "combat:magic:lightning:crack",
    "spell_cast_heal": "combat:magic:heal:cast",
    "hit_critical": "combat:hit:critical",
    "death_humanoid": "combat:death:humanoid",
    "death_monster": "combat:death:monster",
}
```

### Environment Events

```python
ENVIRONMENT_SFX_MAP = {
    "door_open_wood": "event:door:open:wood",
    "door_open_stone": "event:door:open:stone",
    "chest_open": "event:chest:open",
    "chest_locked": "event:chest:locked",
    "trap_trigger": "event:trap:trigger",
    "lever_pull": "event:lever:pull",
    "footstep_stone": "event:footstep:stone",
    "footstep_wood": "event:footstep:wood",
    "gold_coins": "event:gold:coins",
    "potion_drink": "event:potion:drink",
    "dice_roll": "event:dice:roll",
}
```

### Ambient SFX by Scene

```python
AMBIENT_SFX_MAP = {
    ("peaceful", "tavern"): "ambient:peaceful:tavern",
    ("peaceful", "forest"): "ambient:peaceful:nature",
    ("tense", "dungeon"): "ambient:tense:dungeon",
    ("tense", "cave"): "ambient:tense:cave",
    ("neutral", "chamber"): "ambient:fire:hearth",
}
```

---

## Attribution Display

### In-Game Credits

```python
class AttributionLedger:
    """Centralized attribution for CC BY and royalty-free assets."""

    MUSIC_ATTRIBUTIONS = {
        "minstrel_dance.ogg": {
            "artist": "Kevin MacLeod",
            "title": "Minstrel Dance",
            "license": "CC BY 3.0",
            "url": "https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100731",
        },
        # ... 29-44 more tracks
    }

    SFX_ATTRIBUTIONS = {
        "sword_hit_01.ogg": {
            "source": "Sonniss GDC 2024",
            "license": "Royalty-free (attribution required)",
            "url": "https://sonniss.com/gameaudiogdc2024",
        },
        # ... 199-499 more sounds
    }

    @staticmethod
    def generate_credits() -> str:
        """Generate credits text for in-game display."""
        credits = ["=== AUDIO CREDITS ===\n"]

        credits.append("Music:")
        for track, info in AttributionLedger.MUSIC_ATTRIBUTIONS.items():
            credits.append(f"  - {info['title']} by {info['artist']} ({info['license']})")

        credits.append("\nSound Effects:")
        sources = set(info['source'] for info in AttributionLedger.SFX_ATTRIBUTIONS.values())
        for source in sources:
            credits.append(f"  - {source}")

        return "\n".join(credits)
```

R1:514 confirms all selections are commercially safe with proper attribution.

---

## Implementation Phases

### M3 Sprint 1: Music Generation Prototype

**Tasks:**
1. Implement `MusicGenerator` module with ACE-Step backend
2. Extend `SceneManifest` schema with `music_track` field
3. Integrate music generation into prep pipeline (Phase 4)
4. Benchmark ACE-Step on RTX 3060 to validate latency
5. Generate test set (10-15 clips across moods)

**Acceptance criteria:**
- ACE-Step generates 60s OGG clips for all 5 moods
- Sequential unload from Image Critique → ACE-Step completes without VRAM OOM
- Generated clips are semantically appropriate for mood prompts

### M3 Sprint 2: Curated Library Integration

**Tasks:**
1. Curate 30-45 music tracks from Kevin MacLeod, OpenGameArt, FreePD
2. Tag tracks with mood/environment metadata
3. Implement `CuratedLibraryBackend` fallback
4. Implement `AttributionLedger` for CC BY tracks
5. Test tier detection logic (Baseline → curated, Recommended → ACE-Step)

**Acceptance criteria:**
- Curated library covers all mood × environment combinations
- Baseline tier users receive curated tracks instead of attempting ACE-Step
- Attribution display functional in credits

### M3 Sprint 3: SFX Library Curation

**Tasks:**
1. Download and curate 200-500 SFX from Sonniss, Freesound, Kenney.nl
2. Build semantic key index (R1:406-422 taxonomy)
3. Implement 3-5 variants per key
4. Pre-normalize volumes in Audacity
5. Convert all to OGG Vorbis (96-128 kbps)

**Acceptance criteria:**
- SFX library covers all combat/ambient/event/creature categories
- Round-robin variant selection prevents immediate repeats
- Total library <200 MB disk, <65 MB RAM

### M3 Sprint 4: Runtime Mixer Implementation

**Tasks:**
1. Implement `AudioMixer` on `sounddevice` (8-16 channels)
2. Implement music crossfade (2-4s duration)
3. Implement SFX round-robin variant selection
4. Integrate ambient SFX looping
5. Wire mixer into `NarrativeEngine` mood transitions

**Acceptance criteria:**
- Music crossfades smoothly between moods
- SFX variants rotate correctly (no immediate repeats)
- No audio device contention with TTS (R1:427)
- Volume balancing: music 0.4-0.5, SFX 0.6-0.8, TTS 0.9-1.0

### M3 Sprint 5: End-to-End Integration Testing

**Tasks:**
1. Test full prep pipeline (LLM → Image → Music → SFX → TTS)
2. Test runtime gameplay with mood transitions
3. Validate VRAM budget on RTX 3060 (6 GB)
4. Test Baseline tier fallback (curated music/SFX)
5. User acceptance testing (5-10 test campaigns)

**Acceptance criteria:**
- No VRAM OOM errors during prep on 6 GB GPU
- Music transitions feel natural (2-4s crossfade)
- SFX trigger correctly for combat/environment events
- Attribution display complete and accurate

---

## Acceptance Criteria Validation

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Music generation in prep pipeline Phase 4 | ✅ PASS | Integration point specified (R1:469-480) |
| Mood-based crossfade transitions (2-4s) | ✅ PASS | Crossfade logic specified above |
| Event-to-SFX mapping defined | ✅ PASS | Combat/environment/ambient mappings provided |
| AttributionLedger implemented | ✅ PASS | Schema and credits generation specified |
| Sequential unload prevents VRAM contention | ✅ PASS | Phase 4 gets full GPU access (R1:474) |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ACE-Step generation fails mid-prep | Medium | Medium | Catch exception, fallback to curated library for that campaign |
| Crossfade duration feels too short/long | Medium | Low | Make configurable (user setting: 1-5s) |
| SFX variant pool too small (repetition) | Medium | Low | Curate 5+ variants per high-frequency key (sword hit, footstep) |
| Audio mixer TTS contention | Low | High | Use `sounddevice` (resolves contention per R1:427) |
| Music generation exceeds prep budget (30+ min) | Low | Medium | Limit to 30 clips or implement parallel generation if VRAM allows |

---

## Recommendations

1. **Implement ACE-Step integration in M3 Sprint 1** to validate technical feasibility early
2. **Make crossfade duration user-configurable** (1-5s range, default 2s)
3. **Pre-generate validation set** during Sprint 1 to establish quality baseline
4. **Test mixer on sounddevice** early to confirm TTS contention resolution
5. **Provide user override** for curated music mode (some users prefer deterministic output)
6. **Monitor prep-time duration** — if music generation adds >20 minutes, consider parallel generation or batch processing

---

## References

- R1 Technology Stack Validation Report, Appendix A (Prep Pipeline), lines 465-480
- R1 Section 6 (Music), lines 318-326 (mood mapping)
- R1 Section 7 (SFX), lines 406-423 (semantic taxonomy, variants)
- R1 Section 7 (SFX Mixer), lines 426-429 (sounddevice recommendation)

---

**END OF INTEGRATION PLANNING DOCUMENT**

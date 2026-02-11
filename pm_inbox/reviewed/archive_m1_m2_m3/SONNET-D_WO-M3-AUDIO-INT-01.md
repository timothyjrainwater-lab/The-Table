# Work Order: M3 Audio Pipeline Integration

**Work Order ID:** WO-M3-AUDIO-INT-01
**Agent:** Agent D (M3 Preparation)
**Milestone:** M3 (Immersion Layer v1)
**Priority:** 2 (following M3.1-M3.4 voice pipeline and WO-M3-AUDIO-EVAL-01)
**Status:** BLOCKED (awaiting WO-M3-AUDIO-EVAL-01 completion)
**Created:** 2026-02-11

---

## Strategic Intent

**Generative content creation during prep-time is the primary approach for capable hardware. Curated content is the fallback for minimum spec.**

This work order implements the audio pipeline integration based on the evaluation findings from WO-M3-AUDIO-EVAL-01, delivering runtime audio transitions (music + SFX) tied to scene state.

---

## Objective

Integrate the M3 Audio Pipeline into AIDM's runtime, providing:

1. **Music playback** (generative or curated) with scene-driven transitions
2. **SFX playback** (curated) triggered by game events
3. **Hardware tier detection** and automatic fallback (ACE-Step → curated library)
4. **Attribution tracking** for all bundled curated assets
5. **Audio mixer** with multi-channel support (music + ambient + SFX layers)

Implementation follows the evaluation findings from WO-M3-AUDIO-EVAL-01, using model selections and tier assignments validated during evaluation.

---

## Scope

### In Scope

**Music Integration:**
- Implement `MusicAdapter` protocol with two backends:
  - `ACEStepMusicAdapter` (generative, for Recommended/Enhanced tiers)
  - `CuratedMusicAdapter` (fallback, for Baseline tier)
- Hardware tier detection and automatic adapter selection
- Music generation during prep-time (sequential pipeline, Phase 4)
- Music playback during runtime with scene transitions
- Mood-to-music mapping (peaceful, tense, combat, dramatic, neutral)
- Crossfade between tracks on scene mood changes

**SFX Integration:**
- Implement `SFXAdapter` with curated library backend
- Semantic key-based SFX selection (`combat:melee:sword:hit`, `ambient:peaceful:tavern`, etc.)
- Variant round-robin (3-5 variants per key to prevent repetition)
- Event-driven SFX triggers (combat hit, door open, dice roll, etc.)

**Audio Mixer:**
- Implement multi-channel mixer (based on evaluation recommendation):
  - Music channel (looping, crossfade support)
  - Ambient channel (looping, lower priority than music)
  - SFX channels (8-16 simultaneous, one-shot playback)
- Volume control per channel
- Fade in/out support for music transitions
- Backend: `sounddevice` (custom) or `pygame.mixer` (based on eval decision)

**Attribution Tracking:**
- Extend `AttributionLedger` for audio assets
- Generate ATTRIBUTION.txt for bundled curated music/SFX
- Track CC BY 3.0/4.0 assets (Kevin MacLeod music, CC-BY SFX)
- Include attribution in world exports

**Runtime Integration:**
- Audio transition triggers from scene state changes
- `AudioTrack` dataclass extensions (generative + curated metadata)
- Persistence: save/load music/SFX state with campaign
- Graceful degradation when audio unavailable (headless mode, missing files)

### Out of Scope

- Voice I/O integration (handled by M3.1-M3.4)
- Image generation integration (separate M3 deliverable)
- Spatial audio (no spatial frame in text RPG)
- Real-time music generation (prep-time only)
- Procedural MIDI generation (deferred to M1-M2 enhancement)
- Bundled asset curation (evaluation phase delivers library specs; this WO implements loading/playback)

---

## Prerequisites

### Required Inputs from WO-M3-AUDIO-EVAL-01

This work order **cannot proceed** until WO-M3-AUDIO-EVAL-01 delivers:

1. **ACE-Step Validation Report:**
   - VRAM budget confirmation (fits within 6-8 GB)
   - Latency measurements (30s clip, 2-4min track)
   - Mood mapping matrix (D&D moods → ACE-Step prompts)
   - License verification (Apache 2.0)

2. **Curated Music Library Specification:**
   - Source list (Kevin MacLeod, OpenGameArt, FreePD)
   - Track distribution (30-45 tracks by mood)
   - File format (OGG Vorbis)
   - Attribution requirements

3. **SFX Library Specification:**
   - Source list (Sonniss, Freesound, Kenney.nl, OpenGameArt)
   - Semantic key taxonomy (3-level hierarchy)
   - Variant count (3-5 per key)
   - File format (OGG Vorbis)

4. **Hardware Tier Assignment:**
   - Music approach by tier (ACE-Step vs curated)
   - Sequential VRAM budget validation

5. **Integration Planning Document:**
   - Audio transition triggers
   - `AudioTrack` schema extensions
   - `AttributionLedger` requirements
   - Mixer architecture recommendation (sounddevice vs pygame)
   - Playback strategy (streaming vs preload)

**Status:** BLOCKED until evaluation complete.

---

## Implementation Tasks

*NOTE: Task details will be populated after WO-M3-AUDIO-EVAL-01 completion. The structure below is a template based on expected evaluation outputs.*

### Task 1: Music Adapter Implementation

**Objective:** Implement `MusicAdapter` protocol with ACE-Step and curated backends.

**Actions:**
1. Define `MusicAdapter` protocol:
   ```python
   class MusicAdapter(Protocol):
       def generate_music(self, prompt: str, duration: int, seed: int) -> AudioTrack: ...
       def get_track_for_mood(self, mood: SceneMood) -> AudioTrack: ...
       def supports_generation(self) -> bool: ...
   ```
2. Implement `ACEStepMusicAdapter`:
   - Load ACE-Step model during prep (Phase 4, after image critique unloads)
   - Generate music from D&D mood prompts (use eval-provided mapping)
   - Save generated tracks to asset store (OGG format, deterministic seed)
   - Unload model after generation phase
3. Implement `CuratedMusicAdapter`:
   - Load curated library from bundled assets (eval-provided track list)
   - Map moods to curated tracks (eval-provided distribution)
   - Return preselected tracks by mood
4. Implement tier detection and adapter selection:
   - Detect VRAM (nvidia-smi, fallback to CPU detection)
   - Select ACE-Step if VRAM ≥6 GB, curated otherwise
   - Respect user override (config setting)

**Outputs:**
- `aidm/runtime/music_adapter.py` (protocol + implementations)
- Music adapter registry in prep pipeline
- Unit tests (adapter selection, mood mapping)

---

### Task 2: SFX Adapter Implementation

**Objective:** Implement `SFXAdapter` with curated library backend.

**Actions:**
1. Define `SFXAdapter` protocol:
   ```python
   class SFXAdapter(Protocol):
       def get_sfx(self, semantic_key: str) -> AudioTrack: ...
       def get_sfx_variant(self, semantic_key: str, variant_index: int) -> AudioTrack: ...
   ```
2. Implement `CuratedSFXAdapter`:
   - Load curated SFX library (eval-provided taxonomy)
   - Semantic key lookup (e.g., `combat:melee:sword:hit`)
   - Variant round-robin (3-5 variants per key)
   - Preload SFX into RAM (20-65 MB, eval-provided footprint)
3. Add future hook for generative SFX (currently no-op):
   - Placeholder for when permissively-licensed model emerges
   - Same semantic key interface

**Outputs:**
- `aidm/runtime/sfx_adapter.py` (protocol + implementation)
- SFX variant round-robin logic
- Unit tests (semantic key lookup, variant selection)

---

### Task 3: Audio Mixer Implementation

**Objective:** Implement multi-channel audio mixer with music/ambient/SFX separation.

**Actions:**
1. Implement mixer backend (based on eval recommendation):
   - **Option A:** Custom mixer via `sounddevice` (if eval recommends)
     - 8-16 channels
     - Volume control per channel
     - Looping support (music, ambient)
     - Crossfade support (music transitions)
   - **Option B:** `pygame.mixer` wrapper (if eval recommends)
     - Channel allocation (music=0, ambient=1, SFX=2-15)
     - Volume control
     - Loop/fade via pygame API
2. Implement channel management:
   - Music channel: exclusive, looping, crossfade on transitions
   - Ambient channel: looping, lower priority than music
   - SFX channels: one-shot, multiple simultaneous
3. Implement playback strategy (based on eval recommendation):
   - Music: Streaming OGG (if eval recommends) or preload (if faster transitions needed)
   - SFX: Preload (20-65 MB RAM, instant playback)

**Outputs:**
- `aidm/runtime/audio_mixer.py` (mixer implementation)
- Playback tests (load OGG, loop, crossfade, simultaneous SFX)

---

### Task 4: Runtime Audio Integration

**Objective:** Connect audio pipeline to scene state transitions.

**Actions:**
1. Extend `AudioTrack` dataclass (based on eval schema):
   ```python
   @dataclass
   class AudioTrack:
       kind: str  # "music", "sfx", "ambient"
       source: str  # "generative" or "curated"
       file_path: Path | None
       # Generative metadata
       generated: bool = False
       model: str | None = None
       prompt: str | None = None
       seed: int | None = None
       # Curated metadata
       license: str | None = None
       attribution: str | None = None
       # Variant support
       variant_group: str | None = None
       variant_index: int | None = None
   ```
2. Implement audio transition triggers (based on eval trigger list):
   - Scene mood change (peaceful → combat): crossfade music, play combat SFX
   - Combat start: swap to combat music, play initiative SFX
   - Combat end: crossfade back to peaceful music
   - Location change (tavern → dungeon): crossfade ambient loops
3. Add audio playback to runtime loop:
   - Load music for current scene mood
   - Play SFX on game events (attack hit, door open, dice roll)
   - Update mixer state (play, stop, crossfade)
4. Implement graceful degradation:
   - Headless mode: no audio (silent)
   - Missing files: log warning, continue without audio
   - Audio device unavailable: log error, continue without audio

**Outputs:**
- Audio transition logic in scene controller
- Event-to-SFX mapping (combat hit → `combat:hit:critical`, door open → `event:door:open:wood`)
- Integration tests (scene change triggers music, attack triggers SFX)

---

### Task 5: Attribution Tracking

**Objective:** Track all bundled curated assets in `AttributionLedger`.

**Actions:**
1. Extend `AttributionLedger` for audio assets:
   - Track CC BY 3.0/4.0 music (Kevin MacLeod, CC-BY OpenGameArt)
   - Track CC-BY SFX (any Freesound CC-BY sounds)
   - Separate ledger entries for music vs SFX
2. Generate ATTRIBUTION.txt:
   - List all curated assets requiring attribution
   - Format: "Track Title by Artist (Source) — CC BY 3.0"
   - Include in world exports
3. Add attribution to bundled asset manifest:
   - Music library (30-45 tracks): licenses, sources, attribution
   - SFX library (200-500 sounds): licenses, sources, attribution

**Outputs:**
- `aidm/core/attribution_ledger.py` (audio extensions)
- ATTRIBUTION.txt generation logic
- Unit tests (ledger tracks audio, exports to ATTRIBUTION.txt)

---

### Task 6: Prep Pipeline Integration

**Objective:** Integrate music generation into WO-M3-PREP-01 sequential pipeline.

**Actions:**
1. Add music generation to prep orchestrator (Phase 4):
   - Unload LLM/image models
   - Load ACE-Step (if Recommended/Enhanced tier)
   - Generate music for all campaign scenes (mood-based prompts)
   - Save to asset store (OGG, with metadata: seed, prompt, model)
   - Unload ACE-Step
2. Add tier detection to prep pipeline:
   - Detect VRAM before prep starts
   - Select music adapter (ACE-Step vs curated)
   - Log adapter selection
3. Add curated library fallback:
   - If Baseline tier: copy curated tracks to asset store
   - Link tracks to scenes by mood
   - No generation (instant prep completion for music phase)

**Outputs:**
- Music generation phase in prep pipeline
- Tier detection logic
- Prep tests (ACE-Step generates tracks, curated copies tracks)

---

## Deliverables

1. **Music Adapter Implementations**
   - `ACEStepMusicAdapter` (generative)
   - `CuratedMusicAdapter` (fallback)
   - Tier detection and adapter selection

2. **SFX Adapter Implementation**
   - `CuratedSFXAdapter` (curated library)
   - Semantic key lookup
   - Variant round-robin

3. **Audio Mixer**
   - Multi-channel mixer (music, ambient, SFX)
   - Volume control, looping, crossfade
   - Backend: `sounddevice` or `pygame.mixer` (per eval)

4. **Runtime Integration**
   - Audio transition triggers (scene mood → music/SFX)
   - `AudioTrack` dataclass extensions
   - Graceful degradation (headless, missing files)

5. **Attribution Tracking**
   - `AttributionLedger` audio extensions
   - ATTRIBUTION.txt generation
   - Bundled asset manifest

6. **Prep Pipeline Integration**
   - Music generation phase (ACE-Step, Phase 4)
   - Tier detection
   - Curated library fallback

7. **Tests**
   - Unit tests (adapter selection, mood mapping, SFX lookup, attribution)
   - Integration tests (scene change triggers audio, combat triggers SFX)
   - Prep tests (ACE-Step generation, curated fallback)

8. **Documentation**
   - Audio pipeline architecture (adapters, mixer, transitions)
   - Bundled asset licenses (ATTRIBUTION.txt)
   - User-facing: audio settings (tier override, volume control)

---

## Acceptance Criteria

- [ ] Music playback functional (generative for Recommended tier, curated for Baseline tier)
- [ ] SFX playback functional (curated library, semantic key lookup, variant round-robin)
- [ ] Audio transitions tied to scene state (mood changes, combat start/end, location changes)
- [ ] Hardware tier detection works (VRAM ≥6 GB → ACE-Step, <6 GB → curated)
- [ ] Attribution tracking complete (all CC-BY assets in `AttributionLedger`, ATTRIBUTION.txt generated)
- [ ] Graceful degradation works (headless mode, missing files, no audio device)
- [ ] Prep pipeline generates music (ACE-Step during Phase 4, sequential loading)
- [ ] Curated library fallback works (Baseline tier gets curated tracks instantly)
- [ ] All tests pass (unit, integration, prep)
- [ ] No audio device contention with TTS/STT (mixer backend resolves conflicts)
- [ ] Documentation complete (architecture, licenses, user settings)

---

## Dependencies

**Requires:**
- WO-M3-AUDIO-EVAL-01 (evaluation) — **BLOCKS THIS WO**
- WO-M3-PREP-01 (prep pipeline prototype) — complete
- R1 Technology Stack Validation (ACE-Step selection) — complete
- AIDM_EXECUTION_ROADMAP_V3.md v3.2 (M3 audio language) — complete

**Parallel to:**
- M3.1-M3.4 (voice I/O integration)
- M3 Image Pipeline integration

**Unblocks:**
- M3 Immersion Layer acceptance (audio pipeline is M3 deliverable)

---

## Notes

### Why This WO Is Blocked

This work order **cannot proceed** until WO-M3-AUDIO-EVAL-01 completes. The evaluation phase answers critical questions:
1. Does ACE-Step fit the VRAM budget? (If no, fallback to MusicGen or curated-only)
2. What is the curated library specification? (Track list, sources, licensing)
3. What is the SFX taxonomy? (Semantic keys, variants)
4. What mixer architecture should we use? (sounddevice vs pygame)
5. What is the playback strategy? (streaming vs preload)

Without these answers, implementation cannot begin. This follows the pattern of M3.1 (STT eval) → M3.2 (STT integration), M3.3 (TTS eval) → M3.4 (TTS integration).

### Alignment with Roadmap v3.2

This work order implements the M3 Audio Pipeline deliverable from AIDM_EXECUTION_ROADMAP_V3.md v3.2:

> "**Music:** AI-generated (ACE-Step) during prep for capable hardware (≥6 GB VRAM); curated royalty-free library as fallback for minimum spec"

> "**SFX:** Curated library (primary); generative remains blocked by licensing until permissively-licensed model emerges"

Implementation delivers hardware tier detection, automatic fallback, and prep-time generation aligned with the strategic intent.

### Sequential Prep Pipeline (Phase 4)

Music generation happens **during prep-time**, not runtime:
1. User triggers campaign prep ("build me a campaign")
2. Prep pipeline runs sequentially:
   - Phase 1: LLM (Qwen3 8B, ~6 GB VRAM) generates content, unloads
   - Phase 2: Image Gen (SDXL Lightning NF4, ~4 GB VRAM) generates portraits/scenes, unloads
   - Phase 3: Image Critique (ImageReward, ~1 GB VRAM) scores images, unloads
   - **Phase 4: Music Gen (ACE-Step, ~6-8 GB VRAM) generates scene music, unloads**
   - Phase 5: SFX (curated library, 0 GB VRAM) loads from disk
3. User returns to play with pre-generated assets

At runtime, music playback is simple file streaming (no generation). This eliminates latency concerns and VRAM contention.

### Why SFX Remains Curated

As of February 2026, no permissively-licensed generative SFX model exists (see WO-M3-AUDIO-EVAL-01 licensing blocker statement). The prep pipeline **is ready** for generative SFX (~6-8 GB VRAM budget during Phase 5). When a model emerges, this WO will be amended to add `GenerativeSFXAdapter` alongside `CuratedSFXAdapter`.

---

## Change Log

- **2026-02-11:** Work order created, blocked on WO-M3-AUDIO-EVAL-01 completion

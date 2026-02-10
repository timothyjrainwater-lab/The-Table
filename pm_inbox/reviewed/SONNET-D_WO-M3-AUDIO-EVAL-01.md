# Work Order: M3 Audio Pipeline Evaluation

**Work Order ID:** WO-M3-AUDIO-EVAL-01
**Agent:** Agent D (M3 Preparation)
**Milestone:** M3 (Immersion Layer v1)
**Priority:** 2 (following M3.1-M3.4 voice pipeline)
**Status:** DRAFT
**Created:** 2026-02-11
**Blocks:** WO-M3-AUDIO-INT-01

---

## Strategic Intent

**Generative content creation during prep-time is the primary approach for capable hardware. Curated content is the fallback for minimum spec.**

This applies to music. SFX remains curated-primary only because no permissively-licensed generative model exists yet — when one does, generative becomes primary for SFX too.

---

## Objective

Evaluate music generation and sound effects approaches for the M3 Audio Pipeline against AIDM's hardware tiers, identifying the optimal combination of generative and curated strategies that:

1. **Delivers generative music as primary** for systems with ≥6 GB VRAM
2. **Provides curated music fallback** for systems with <6 GB VRAM or no GPU
3. **Uses curated SFX** as primary (licensing blocks generative)
4. **Validates technical viability** of ACE-Step (Apache 2.0) in the prep pipeline

The evaluation output will inform WO-M3-AUDIO-INT-01 (integration) with concrete model selections, VRAM requirements, latency measurements, and tier assignments.

---

## Scope

### In Scope

**Music Generation (Primary Focus):**
- Benchmark **ACE-Step** (Apache 2.0, 3.5B params) on target hardware:
  - VRAM usage during prep-time sequential loading
  - Generation latency (30s clips, 2-4min tracks)
  - Quality assessment (genre coverage, mood mapping)
  - License verification (Apache 2.0 compliance)
- Evaluate fallback to **MusicGen-small** (CC-BY-NC) if ACE-Step fails technical benchmarks
- Define curated music library requirements for Baseline tier:
  - Source selection (Kevin MacLeod/Incompetech, OpenGameArt CC0, FreePD)
  - Track count and distribution by mood (`_VALID_SCENE_MOODS`)
  - Disk/RAM footprint
  - Licensing/attribution requirements

**Sound Effects (Curated Only):**
- Define curated SFX library requirements:
  - Source selection (Sonniss GDC, Freesound CC0, Kenney.nl)
  - Semantic key taxonomy (combat, ambient, event, creature)
  - Variant count (3-5 per SFX key)
  - Disk/RAM footprint
  - Licensing/attribution requirements
- Document why generative SFX is blocked (no Apache 2.0/MIT models as of Feb 2026)
- Identify future-watch models (TangoFlux, AudioLDM 2) for licensing landscape monitoring

**Hardware Tier Validation:**
- Map music approaches to existing hardware tiers:
  - **Recommended (8GB VRAM):** ACE-Step generative (primary)
  - **Baseline (<6GB VRAM / CPU-only):** Curated library (fallback)
  - **Enhanced (16GB+ VRAM):** ACE-Step generative (enhanced settings if applicable)
- Verify sequential pipeline VRAM budget (Phase 4 in R1 Appendix A)

**Integration Points:**
- Audio transition triggers from scene state (peaceful → combat, tense → dramatic)
- `AudioTrack` dataclass extensions needed for generative metadata
- `AttributionLedger` requirements for curated assets
- Mixer architecture decision (custom `sounddevice` mixer vs `pygame.mixer`)

### Out of Scope

- Implementation (handled by WO-M3-AUDIO-INT-01)
- Spatial audio (no spatial frame in text RPG)
- Real-time music generation (prep-time only)
- Procedural MIDI generation (deferred to M1-M2 enhancement)
- Voice I/O integration (handled by M3.1-M3.4)
- Image generation integration (separate M3 deliverable)

---

## Background

### R1 Technology Stack Validation Findings

The **R1 Technology Stack Validation Report** (pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md, Section 6-7) established:

1. **Music generation is viable during prep-time:**
   - Sequential pipeline eliminates VRAM contention (LLM/image models unload before music phase)
   - ACE-Step (Apache 2.0) generates 4min tracks in ~20-40s on RTX 3060
   - ~6-8 GB VRAM during music phase (within Recommended tier budget)
   - Prep-time eliminates latency concerns (user is AFK during campaign build)

2. **ACE-Step resolves MusicGen licensing blocker:**
   - MusicGen weights are CC-BY-NC (non-commercial)
   - ACE-Step is Apache 2.0 (commercially safe)
   - Quality: state-of-art, supports vocals + instrumental, 19 languages

3. **Curated library is viable fallback:**
   - Kevin MacLeod/Incompetech: CC BY 3.0, ~2000+ tracks
   - OpenGameArt CC0: fantasy/RPG category
   - FreePD.com: CC0 (public domain)
   - 30-45 tracks distributed by mood, 60-120s loops

4. **SFX remains curated-primary:**
   - TangoFlux (Stability AI Community License) — blocked
   - Tango 2 (CC-BY-NC-SA-4.0) — blocked
   - AudioGen (CC-BY-NC) — blocked
   - No permissively-licensed SFX model exists (Feb 2026)
   - Curated sources: Sonniss GDC (royalty-free), Freesound CC0, Kenney.nl CC0

### Existing Prep Pipeline Prototype

**WO-M3-PREP-01** (complete) established:
- Sequential model loading pattern (LLM → Image Gen → Music Gen stub → SFX Gen stub)
- "Music Gen" placeholder exists but not implemented
- Prep orchestrator handles offline batch generation
- Asset store persistence for generated content

### Execution Roadmap v3.2 Language

Updated M3 Audio Pipeline deliverable (AIDM_EXECUTION_ROADMAP_V3.md:265-267):
> "**Music:** AI-generated (ACE-Step) during prep for capable hardware (≥6 GB VRAM); curated royalty-free library as fallback for minimum spec"

---

## Evaluation Tasks

### Task 1: ACE-Step Technical Validation

**Objective:** Verify ACE-Step meets VRAM, latency, and quality requirements on target hardware.

**Actions:**
1. Research ACE-Step implementation libraries (Hugging Face `transformers`, standalone repos)
2. Identify quantization options (FP16, INT8, NF4) and VRAM impact
3. Estimate VRAM usage for sequential loading (unload LLM/image before ACE-Step loads)
4. Estimate generation latency:
   - 30s ambient clip (peaceful, tense, neutral moods)
   - 2-4min combat track (combat, dramatic moods)
   - Hardware targets: RTX 3060 (8GB), RTX 4060 (8GB), GTX 1660 Ti (6GB)
5. Assess genre/mood coverage:
   - Map D&D moods (`peaceful`, `tense`, `combat`, `dramatic`, `neutral`) to ACE-Step prompts
   - Identify prompt engineering patterns for fantasy tavern, dungeon ambience, battle music
6. Verify Apache 2.0 license compliance (model weights, code, output artifacts)

**Outputs:**
- VRAM budget table (FP16 vs quantized)
- Latency estimates (30s clip, 2-4min track) by hardware tier
- Mood mapping matrix (D&D mood → ACE-Step prompt examples)
- License verification statement

**Success Criteria:**
- ACE-Step fits within 6-8 GB VRAM during sequential prep phase
- Latency acceptable for prep-time (user is AFK, no hard limit)
- Apache 2.0 license confirmed for commercial use

**Fallback:** If ACE-Step fails technical benchmarks, evaluate MusicGen-small (CC-BY-NC) with licensing caveat.

---

### Task 2: Curated Music Library Specification

**Objective:** Define curated music library requirements for Baseline tier fallback.

**Actions:**
1. Identify primary sources:
   - Kevin MacLeod/Incompetech (CC BY 3.0)
   - OpenGameArt.org (CC0, fantasy/RPG category)
   - FreePD.com (CC0, public domain)
2. Define track distribution by mood:
   - Peaceful (village/tavern, forest/nature, travel): 8-10 tracks
   - Tense (dungeon/cave, suspense, supernatural): 7-9 tracks
   - Combat (standard battle, boss/epic, skirmish): 7-9 tracks
   - Dramatic (revelation/climax, tragedy/loss): 5-7 tracks
   - Neutral (quiet ambient): 2-3 tracks
3. Specify technical requirements:
   - Duration: 60-120s seamless loops
   - Format: OGG Vorbis (lower disk footprint than WAV/MP3)
   - Disk footprint: estimate for 30-45 tracks
   - Runtime RAM: streaming (low memory) vs preload (faster transitions)
4. Document attribution requirements (CC BY 3.0 requires credit)

**Outputs:**
- Curated library specification (track count, sources, licensing)
- Mood distribution matrix (30-45 tracks across 5 moods)
- Disk/RAM footprint estimate
- `AttributionLedger` entry format for bundled music

**Success Criteria:**
- 30-45 tracks cover all `_VALID_SCENE_MOODS`
- All sources are CC0 or CC BY 3.0/4.0 (commercially safe)
- Disk footprint <100 MB (OGG compressed)

---

### Task 3: Sound Effects Library Specification

**Objective:** Define curated SFX library requirements (generative blocked by licensing).

**Actions:**
1. Identify primary sources:
   - Sonniss GDC Bundles (royalty-free, 150-300 sounds)
   - Freesound.org CC0 (gap-filling, 30-80 sounds)
   - Kenney.nl (CC0, UI/feedback, 10-20 sounds)
   - OpenGameArt.org (CC0/CC-BY, fantasy packs, 10-30 sounds)
2. Define semantic key taxonomy (extend `AudioTrack.kind`):
   - Combat: `combat:melee:sword:hit`, `combat:magic:fire:impact`, `combat:ranged:bow:release`
   - Ambient: `ambient:peaceful:tavern`, `ambient:tense:dungeon`, `ambient:weather:rain`
   - Event: `event:door:open:wood`, `event:chest:open`, `event:dice:roll`, `event:trap:trigger`
   - Creature: `creature:dragon:roar`, `creature:wolf:howl`
3. Specify variant strategy:
   - 3-5 variants per semantic key (round-robin to prevent repetition)
4. Estimate disk/RAM footprint:
   - Total sounds: 200-500
   - Disk (OGG Vorbis): 50-200 MB
   - RAM (preloaded): 20-65 MB
5. Document why generative SFX is blocked:
   - TangoFlux (Stability AI Community License) — non-commercial
   - Tango 2 (CC-BY-NC-SA-4.0) — non-commercial
   - AudioGen (CC-BY-NC) — non-commercial
   - No Apache 2.0/MIT model exists as of Feb 2026
6. Identify future-watch models for licensing landscape monitoring

**Outputs:**
- SFX library specification (sources, taxonomy, variant count)
- Semantic key taxonomy (3-level hierarchy: category:subcategory:specific)
- Disk/RAM footprint estimate
- Licensing blocker statement (why generative is deferred)
- Future-watch list (TangoFlux, AudioLDM 2)

**Success Criteria:**
- 200-500 sounds cover core D&D scenarios (combat, ambient, events, creatures)
- All sources are royalty-free or CC0/CC-BY (commercially safe)
- Disk footprint <200 MB
- Licensing blocker clearly documented

---

### Task 4: Hardware Tier Mapping

**Objective:** Assign music/SFX approaches to AIDM hardware tiers based on VRAM budget.

**Actions:**
1. Review existing hardware tiers (R1 Appendix A):
   - **Baseline:** CPU/optional GPU, 16GB RAM, 20GB storage, <6GB VRAM
   - **Recommended:** 8GB VRAM, 32GB RAM, 40GB storage
   - **Enhanced:** 16GB+ VRAM, 64GB+ RAM, 80GB+ storage
2. Map music generation to tiers:
   - Recommended/Enhanced (≥6 GB VRAM): ACE-Step generative (primary)
   - Baseline (<6 GB VRAM / CPU-only): Curated library (fallback)
3. Map SFX to tiers:
   - All tiers: Curated library (generative blocked by licensing)
4. Validate sequential prep pipeline VRAM budget:
   - Phase 1 (LLM): Qwen3 8B = ~6 GB VRAM, unload
   - Phase 2 (Image Gen): SDXL Lightning NF4 = ~4 GB VRAM, unload
   - Phase 3 (Image Critique): ImageReward = ~1 GB VRAM, unload
   - **Phase 4 (Music Gen): ACE-Step = ~6-8 GB VRAM**, unload
   - Phase 5 (SFX): Curated library = 0 GB VRAM (disk load)
   - Peak VRAM: max(6 GB LLM, 6-8 GB Music) = **6-8 GB**
5. Confirm Recommended tier (8GB VRAM) supports full generative pipeline

**Outputs:**
- Hardware tier assignment table (music/SFX by tier)
- Sequential VRAM budget validation (peak = 6-8 GB)
- Tier compatibility matrix (which tiers support ACE-Step)

**Success Criteria:**
- ACE-Step fits within Recommended tier (8GB VRAM) during sequential loading
- Baseline tier fallback clearly defined (curated library)
- No tier left without a viable audio strategy

---

### Task 5: Integration Planning

**Objective:** Identify integration points and technical decisions for WO-M3-AUDIO-INT-01.

**Actions:**
1. Audio transition triggers from scene state:
   - Scene mood changes (peaceful → combat, tense → dramatic)
   - Combat start/end (music swap + SFX)
   - Location changes (tavern → dungeon)
2. `AudioTrack` dataclass extensions:
   - Generative metadata: `generated: bool`, `model: str`, `prompt: str`, `seed: int`
   - Curated metadata: `source: str`, `license: str`, `attribution: str`
   - Variant support: `variant_group: str`, `variant_index: int`
3. `AttributionLedger` requirements:
   - Track all CC BY 3.0/4.0 assets (Kevin MacLeod music, CC-BY SFX)
   - Generate ATTRIBUTION.txt for bundled assets
4. Mixer architecture decision:
   - **Option A:** Custom mixer via `sounddevice` (8-16 channels, volume, loop, fade)
     - Pros: Avoids pygame dependency, no TTS device contention
     - Cons: ~300-500 lines of code to implement
   - **Option B:** `pygame.mixer` (mature library)
     - Pros: Battle-tested, minimal code
     - Cons: Adds pygame dependency, potential TTS audio device conflict
5. Playback strategy:
   - Music: Streaming OGG (<5 MB RAM) vs preload (faster transitions)
   - SFX: Preload (20-65 MB RAM) for instant playback

**Outputs:**
- Audio transition trigger list (scene state → audio actions)
- `AudioTrack` schema extensions (generative + curated metadata)
- `AttributionLedger` requirements
- Mixer architecture recommendation (Option A vs B)
- Playback strategy recommendation (streaming vs preload)

**Success Criteria:**
- All integration points identified (no gaps for INT work order)
- Technical decisions documented with clear rationale
- No architectural conflicts with existing TTS/STT pipeline

---

## Deliverables

1. **ACE-Step Validation Report**
   - VRAM budget (FP16, INT8, NF4)
   - Latency estimates (30s clip, 2-4min track, by hardware)
   - Mood mapping matrix (D&D moods → ACE-Step prompts)
   - License verification (Apache 2.0 confirmed)

2. **Curated Music Library Specification**
   - Source list (Kevin MacLeod, OpenGameArt, FreePD)
   - Track distribution (30-45 tracks by mood)
   - Disk/RAM footprint estimate
   - Attribution requirements

3. **SFX Library Specification**
   - Source list (Sonniss, Freesound, Kenney.nl, OpenGameArt)
   - Semantic key taxonomy (3-level hierarchy)
   - Variant strategy (3-5 per key)
   - Disk/RAM footprint estimate
   - Licensing blocker statement + future-watch list

4. **Hardware Tier Assignment**
   - Music/SFX approach by tier (Baseline, Recommended, Enhanced)
   - Sequential VRAM budget validation (peak = 6-8 GB)
   - Tier compatibility matrix

5. **Integration Planning Document**
   - Audio transition triggers (scene state → audio actions)
   - `AudioTrack` schema extensions
   - `AttributionLedger` requirements
   - Mixer architecture recommendation
   - Playback strategy recommendation

---

## Acceptance Criteria

- [ ] ACE-Step validated as technically viable (VRAM, latency, quality) for Recommended tier
- [ ] Curated music library specified (30-45 tracks, all commercially licensed)
- [ ] SFX library specified (200-500 sounds, all commercially licensed)
- [ ] Licensing blocker for generative SFX documented (no Apache 2.0/MIT models)
- [ ] Hardware tier assignments complete (music/SFX by tier)
- [ ] Sequential prep pipeline VRAM budget validated (peak ≤8 GB for Recommended tier)
- [ ] All integration points identified for WO-M3-AUDIO-INT-01
- [ ] No architectural conflicts with existing voice/image pipeline
- [ ] All deliverables use R1-validated model selections (ACE-Step, not MusicGen)
- [ ] Strategic intent affirmed: **generative primary for capable hardware, curated fallback for minimum spec**

---

## Dependencies

**Requires:**
- R1 Technology Stack Validation Report (pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md) — complete
- WO-M3-PREP-01 (prep pipeline prototype) — complete
- AIDM_EXECUTION_ROADMAP_V3.md v3.2 (updated M3 audio language) — complete
- Existing hardware tier definitions (R0_MODEL_BUDGETS.md or equivalent)

**Blocks:**
- WO-M3-AUDIO-INT-01 (audio pipeline integration)

**Parallel to:**
- M3.1-M3.4 (voice I/O evaluation and integration)
- M3 Image Pipeline evaluation/integration

---

## Notes

### Why Evaluation Phase Is Required

Following the pattern established by M3.1 (STT eval), M3.3 (TTS eval), and M3.5 (image eval), this work order performs **evaluation before integration**. The evaluation answers:
1. Does ACE-Step fit the VRAM budget?
2. Is latency acceptable for prep-time?
3. What curated library is needed for fallback?
4. How do we map D&D moods to generative prompts?

The **recommendation matrix is an output of this evaluation**, not an input. WO-M3-AUDIO-INT-01 will implement based on these findings.

### Why ACE-Step (Not MusicGen)

The R1 report identified ACE-Step as the primary model because:
- **Apache 2.0 license** (MusicGen is CC-BY-NC)
- **State-of-art quality** (beats MusicGen on blind evaluations)
- **Fits VRAM budget** (~6-8 GB, same as MusicGen-small)
- **Fast generation** (20-40s for 4min track on RTX 3060)

MusicGen-small remains a fallback option if ACE-Step fails technical validation, but carries licensing risk for commercial use.

### Why SFX Remains Curated

As of February 2026, **no permissively-licensed generative SFX model exists**:
- TangoFlux (Stability AI Community License) — non-commercial
- Tango 2 (CC-BY-NC-SA-4.0) — non-commercial
- AudioGen (CC-BY-NC) — non-commercial

The prep-time sequential pipeline **is architecturally ready** for generative SFX (~6-8 GB VRAM budget, latency irrelevant). The blocker is **licensing only**. When a permissively-licensed model emerges, generative becomes primary for SFX too.

### Alignment with Roadmap v3.2

This work order implements the strategic intent stated in AIDM_EXECUTION_ROADMAP_V3.md v3.2:

> "**Music:** AI-generated (ACE-Step) during prep for capable hardware (≥6 GB VRAM); curated royalty-free library as fallback for minimum spec"

And clarifies that SFX remains curated-primary due to licensing constraints, not technical limitations.

---

## Change Log

- **2026-02-11:** Work order created with generative-primary framing (ACE-Step), curated fallback, based on R1 findings and Thunder's strategic guidance

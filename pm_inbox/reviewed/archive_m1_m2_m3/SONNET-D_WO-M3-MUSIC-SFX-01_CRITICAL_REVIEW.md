# WO-M3-MUSIC-SFX-01: Critical Review and Rejection

**Reviewer:** Sonnet D
**Date:** 2026-02-10
**Status:** REJECTED — Multiple Critical Violations

---

## Executive Summary

Work order **WO-M3-MUSIC-SFX-01** contains **CRITICAL VIOLATIONS** of project governance and architectural boundaries. The work order proposes integrating generative music (MusicGen) and SFX (AudioGen/Tango 2) models into the prep pipeline, but this approach:

1. **Violates project scope boundaries** (Coherence Doctrine Section 1)
2. **Contradicts canonical M3 deliverables** (Execution Roadmap v3.1)
3. **Introduces unauthorized technology dependencies** without evaluation phase
4. **Misunderstands prep pipeline architecture** (out-of-scope for M3)
5. **Lacks acceptance criteria alignment** with frozen M3 requirements

**Recommendation:** REJECT work order. Return to PM for re-scoping against canonical M3 deliverables.

---

## Violation Analysis

### VIOLATION 1: Misalignment with Canonical M3 Deliverables

**Canonical M3 Deliverables** (per `AIDM_EXECUTION_ROADMAP_V3.md` lines 253-280):

> **M3 — Immersion Layer v1**
>
> 1. **Voice Pipeline**: Local STT adapter (pluggable) + Local TTS voice persona
> 2. **Image Pipeline**: Local image generator adapter (or bundled placeholders) + NPC portraits + scene backdrops
> 3. **Audio Pipeline**: Ambient loops + SFX (bundled library acceptable) + **Optional** local music generator; otherwise curated generative-safe library
> 4. **Contextual Grid**: Grid appears only when spatial precision matters

**What the Roadmap Actually Says About Audio (lines 265-267):**

> 3. **Audio Pipeline**
>    - Ambient loops + SFX (**bundled library acceptable**)
>    - **Optional** local music generator; otherwise **curated generative-safe library**
>    - Licensing/attribution tracked for bundled assets

**Work Order Violation:**

The work order makes MusicGen/AudioGen **mandatory** and places them in the **prep pipeline** (which is M2, not M3). The canonical roadmap says:
- **"bundled library acceptable"** — curated library is PRIMARY, not fallback
- **"Optional local music generator"** — generative models are OPTIONAL enhancement, not core deliverable
- Audio is part of **M3 Immersion Layer**, not **M2 Prep Pipeline**

### VIOLATION 2: LLM/Generative Model Dependency at Wrong Layer

**Coherence Doctrine Section 1** (lines 14-29):

> ### 1. No LLM Dependency in Deterministic Runtime
>
> **Allowed**:
> - LLMs in **prep phase** as untrusted generators (scene creation, NPC generation, narration drafts)
> - LLM outputs MUST be gated by fail-closed validators before entering bundles
> - LLM-generated content stored as static data in bundles (becomes deterministic input)
>
> **Forbidden**:
> - LLM inference during gameplay/replay

**Work Order Violation:**

The work order proposes generating **30-45 music tracks** and **multiple SFX** during prep using MusicGen/AudioGen. While technically allowed under "prep phase generators," this:

1. **Adds massive disk footprint** (30-45 tracks × ~10MB/track = 300-450MB per campaign minimum)
2. **Introduces model loading overhead** during prep without hardware tier evaluation
3. **Creates dependency on models not yet vetted** (no M3.1/M3.2 evaluation task completed)
4. **Assumes prep pipeline orchestration exists** (M2 is NOT complete — only persistence layer is frozen)

### VIOLATION 3: Wrong Milestone Dependency Chain

**Execution Roadmap Milestone Order** (lines 64-94):

```
M0 — Design Closeout (✅ COMPLETE)
  ↓
M1 — Solo Vertical Slice v0 (NOT STARTED)
  ↓
M2 — Campaign Prep Pipeline v0 (PERSISTENCE LAYER COMPLETE v1.1)
  ↓
M3 — Immersion Layer v1 (NOT STARTED)
  ↓
M4 — Offline Packaging + Shareability (NOT STARTED)
```

**Work Order Claims:**

> **DEPENDENCIES:**
> - Depends on: **WO-M3-PREP-01** (Sonnet B's prep pipeline prototype for model loading and asset generation)
> - Blocks: **M3 Immersion Layer** (music and SFX are part of the Immersion Layer)

**Violation:**

1. **WO-M3-PREP-01 does not exist** — no such work order appears in project documents
2. **M3 depends on M1 completion** — per roadmap, M1 must be complete before M3 begins
3. **M2 prep pipeline is NOT complete** — only persistence layer is frozen, orchestration does not exist
4. **"Blocks M3 Immersion Layer"** is backwards — this work IS part of M3, it doesn't block M3

### VIOLATION 4: Missing Technology Evaluation Phase

**M3 Supporting Tasks** (Roadmap lines 284-300):

| Task | Description |
|------|-------------|
| M3.1 | **Evaluate and select** local STT library |
| M3.2 | Integrate STT adapter |
| M3.3 | **Evaluate and select** local TTS library |
| M3.4 | Integrate TTS adapter |
| M3.5 | **Evaluate and select** local image generation |
| M3.6 | Implement image generation adapter |
| M3.10 | Integrate audio playback system |
| M3.11 | Implement ambient sound selection |
| M3.12 | Implement music transitions |
| M3.13 | **Bundle initial sound effects** |

**Work Order Violation:**

The work order jumps directly to integration (MusicGen, AudioGen/Tango 2) without completing:
- **M3.10** (Evaluate and select audio generation approach)
- **M3.11** (Evaluate licensing/attribution for bundled vs. generated)
- **M3.12** (Compare disk footprint: curated library vs. per-campaign generation)

This skips the **evaluation phase** that M3.1/M3.3/M3.5 demonstrate is required for ALL M3 components.

### VIOLATION 5: Acceptance Criteria Do Not Match M3 Requirements

**Canonical M3 Acceptance Criteria** (Roadmap lines 274-280):

> - [ ] Offline voice I/O functional
> - [ ] Audio transitions tied to scene state
> - [ ] Images are atmospheric only (no mechanics depend on them)
> - [ ] Grid appears for combat, disappears after
> - [ ] **Licensing/attribution record for bundled assets**

**Work Order Acceptance Criteria:**

> 1. **Generative Music**: MusicGen successfully generates 30-45 custom tracks specific to the campaign, saved in OGG format.
> 2. **Generative SFX**: AudioGen/Tango 2 successfully generates custom SFX for campaign elements and is saved in the correct format.
> 3. **Curated Library Fallback**: The curated library correctly functions as a fallback for music and SFX when generative models fail.

**Violation:**

1. Does not verify **"audio transitions tied to scene state"** (core M3 requirement)
2. Does not produce **"licensing/attribution record"** (mandatory M3 deliverable)
3. Treats curated library as **fallback** when roadmap says it's **acceptable primary approach**
4. No verification that audio is **atmospheric only** (no mechanics depend on it)

---

## Architectural Concerns

### Concern 1: Prep Pipeline Does Not Exist Yet

**M2 Status** (per Roadmap lines 180-186):

> **Status:** PERSISTENCE LAYER COMPLETE (v1.1)
> **Goal:** "Start Campaign" triggers a preparation phase producing campaign scaffolding + assets.
>
> **Architecture Status:** M2 Persistence Architecture is **FROZEN** (v1.1)

The work order assumes a prep pipeline orchestrator exists to:
- Load MusicGen/AudioGen models
- Queue 30-45 track generation tasks
- Monitor generation progress
- Validate output quality
- Store tracks in campaign directory

**NONE OF THIS EXISTS.** The M2 persistence layer provides `CampaignStore`, `EventLog`, `SessionLog` — it does NOT provide orchestration, model loading, or asset generation queues.

### Concern 2: Disk Footprint Not Evaluated

Generating **30-45 tracks per campaign** means:
- At ~10MB/track (OGG compressed): **300-450MB per campaign**
- For 5 campaigns: **1.5-2.25GB** just for music
- Plus SFX (unknown count × ~1-5MB): **additional 100MB-1GB per campaign**

This has **NOT been evaluated** against M4 hardware tiers:

| Tier | Storage Budget |
|------|---------------|
| Baseline | 20GB |
| Recommended | 40GB |
| Enhanced | 80GB+ |

If each campaign consumes 500MB-1GB just for audio assets, this is **2.5-5% of baseline storage budget** for audio alone.

### Concern 3: Model Loading Time Not Evaluated

MusicGen/AudioGen models are **multi-gigabyte neural networks**:
- MusicGen (small): ~1.5GB
- MusicGen (medium): ~3GB
- AudioGen: ~1-2GB

Loading these models during prep adds **30-60 seconds** to prep time, **per model**, on CPU-only hardware (M4 baseline tier).

This has **NOT been evaluated** against M2 prep UX requirements:

> **M2 Deliverables:**
> - Ambient visuals/audio during prep (avoid "frozen" feel)

Loading 3GB models creates the exact "frozen" feel M2 is designed to avoid.

---

## Correct Scope for M3 Audio Work

Based on canonical roadmap, the CORRECT M3 audio work order should:

### Phase 1: Evaluation (M3.10-equivalent)

1. **Evaluate three approaches:**
   - **A**: Curated library only (e.g., FreeSound, public domain)
   - **B**: Generative models (MusicGen, AudioGen) with curated fallback
   - **C**: Hybrid (generic tracks curated, campaign-specific tracks generated)

2. **Compare on:**
   - Disk footprint per campaign
   - Prep time overhead (model loading + generation)
   - Quality (subjective, but testable)
   - Licensing complexity (attribution tracking)
   - Hardware tier compatibility (baseline vs. recommended)

3. **Produce evaluation report** for PM review

### Phase 2: Integration (M3.11-M3.13)

Based on approved evaluation approach:

1. **M3.11**: Implement ambient sound selection logic
   - Read scene state (combat/exploration/dialogue)
   - Select appropriate ambient loop
   - Handle transitions (fade in/out)

2. **M3.12**: Implement music transitions
   - Trigger music changes on scene state changes
   - Crossfade between tracks
   - Handle silence (theatre-of-the-mind default)

3. **M3.13**: Bundle initial sound effects
   - Curate 20-30 essential SFX (sword hit, spell cast, door open)
   - Create attribution ledger
   - Verify licensing for distribution

### Phase 3: Optional Generative Enhancement (If Evaluation Approves)

Only if Phase 1 evaluation shows generative approach is viable:

1. **Implement adapter pattern** (like image/voice adapters)
2. **Create stub adapter** (returns curated library)
3. **Create MusicGen adapter** (loads model, generates tracks)
4. **Test on hardware tiers** (baseline, recommended, enhanced)
5. **Document disk/time tradeoffs**

---

## Required Corrections

To bring this work order into compliance:

1. **Split into evaluation + integration phases**
   - WO-M3-AUDIO-EVAL-01 (evaluate approaches)
   - WO-M3-AUDIO-INT-01 (implement approved approach)

2. **Align acceptance criteria with canonical M3 requirements**
   - Audio transitions tied to scene state ✅
   - Licensing/attribution record ✅
   - Atmospheric only (no mechanics depend on it) ✅

3. **Remove prep pipeline dependency**
   - M3 audio integration does NOT require M2 prep orchestrator
   - Audio selection happens at RUNTIME (scene state changes)
   - Only asset BUNDLING happens at prep time (if using curated library)

4. **Add hardware tier evaluation**
   - Test on M4 baseline tier (CPU-only, 20GB storage)
   - Document model loading time
   - Document disk footprint per campaign

5. **Make generative models OPTIONAL, not mandatory**
   - Per roadmap: "Optional local music generator"
   - Curated library is acceptable primary approach

---

## Recommendation

**REJECT** WO-M3-MUSIC-SFX-01 for the following reasons:

1. ❌ Violates canonical M3 deliverables (treats optional as mandatory)
2. ❌ Misplaces work in M2 prep pipeline (should be M3 runtime integration)
3. ❌ Skips required evaluation phase (M3.10-equivalent)
4. ❌ Lacks acceptance criteria alignment with frozen roadmap
5. ❌ Assumes non-existent prep orchestrator infrastructure
6. ❌ No hardware tier / disk footprint evaluation

**Return to PM** with the following guidance:

> M3 audio work should begin with an **evaluation work order** comparing curated library vs. generative approaches across hardware tiers. Integration work should follow the adapter pattern established for voice/image (stub + real implementations). Generative models are OPTIONAL per roadmap — curated library is acceptable as primary approach.

---

## References

- [AIDM_EXECUTION_ROADMAP_V3.md](../docs/AIDM_EXECUTION_ROADMAP_V3.md) (lines 248-301: M3 deliverables and supporting tasks)
- [PROJECT_COHERENCE_DOCTRINE.md](../PROJECT_COHERENCE_DOCTRINE.md) (lines 14-29: LLM/generative model boundaries)
- [PROJECT_STATE_DIGEST.md](../PROJECT_STATE_DIGEST.md) (M2 status: persistence layer only)
- [AGENT_DEVELOPMENT_GUIDELINES.md](../AGENT_DEVELOPMENT_GUIDELINES.md) Section 10 (deliverable routing)

---

**Logged:** 2026-02-10
**Reviewer:** Sonnet D
**Action Required:** Return to PM for re-scoping

# WO-M3-AUDIO-EVAL-01: Audio Approach Evaluation

**Agent:** Sonnet D
**Work Order:** WO-M3-AUDIO-EVAL-01
**Date:** 2026-02-10
**Status:** DRAFT — Awaiting PM Approval
**Depends On:** None (evaluation only)
**Blocks:** WO-M3-AUDIO-INT-01 (integration phase)

---

## Objective

Evaluate **three audio sourcing approaches** for M3 Immersion Layer audio pipeline, comparing disk footprint, model loading time, quality, and licensing complexity across M4 hardware tiers. Produce recommendation report for PM approval before integration work begins.

This follows the evaluation pattern established by M3.1 (STT evaluation), M3.3 (TTS evaluation), and M3.5 (image generation evaluation).

---

## Background

Per Execution Roadmap v3.1 M3 Deliverables (lines 265-267):

> **3. Audio Pipeline**
> - Ambient loops + SFX (**bundled library acceptable**)
> - **Optional** local music generator; otherwise curated generative-safe library
> - Licensing/attribution tracked for bundled assets

The roadmap specifies that:
1. **Curated library is acceptable as primary approach** (not just fallback)
2. **Generative models are optional** enhancement
3. **Licensing/attribution tracking is mandatory** deliverable

This evaluation will determine which approach best serves M4 hardware tier requirements while maintaining M3 acceptance criteria.

---

## Scope

### In Scope

1. **Evaluate Three Approaches:**
   - **Approach A**: Curated library only (public domain/licensed assets)
   - **Approach B**: Generative models (MusicGen + AudioGen) with curated fallback
   - **Approach C**: Hybrid (generic tracks curated, campaign-specific tracks generated)

2. **Comparison Metrics:**
   - **Disk Footprint**: Per-campaign storage requirements
   - **Model Load Time**: Initial load time for generative models (if applicable)
   - **Generation Time**: Time to produce campaign audio set (if applicable)
   - **Quality**: Subjective assessment (atmospheric fit, variety)
   - **Licensing Complexity**: Attribution tracking, distribution constraints
   - **Hardware Tier Compatibility**: Baseline vs. Recommended vs. Enhanced

3. **Test on M4 Hardware Tiers:**
   - **Baseline**: CPU-only, 16GB RAM, 20GB storage
   - **Recommended**: GPU (8GB VRAM), 32GB RAM, 40GB storage
   - **Enhanced**: GPU (16GB+ VRAM), 64GB+ RAM, 80GB+ storage

4. **Deliverables:**
   - Evaluation report with quantitative measurements
   - Recommendation matrix (which approach for which tier)
   - Licensing/attribution ledger prototype (if curated approach selected)

### Out of Scope

- **Integration work** (deferred to WO-M3-AUDIO-INT-01)
- **Runtime audio playback** (deferred to WO-M3-AUDIO-INT-01)
- **Scene state → audio transitions** (deferred to WO-M3-AUDIO-INT-01)
- **Prep pipeline orchestration** (M2 work, not M3)

---

## Approach Details

### Approach A: Curated Library Only

**Description:** Use pre-selected, licensed audio assets from public domain or licensed sources (e.g., FreeSound, OpenGameArt, commissioned tracks).

**Test Parameters:**
- Curate **20-30 ambient loops** (combat, exploration, dialogue, tension)
- Curate **20-30 SFX** (sword hit, spell cast, door open, footsteps)
- Total disk footprint: ~50-100MB per campaign (shared across campaigns)
- Model load time: N/A (no models)
- Generation time: N/A (assets pre-bundled)
- Licensing: Create attribution ledger for all assets

**Pros:**
- Zero prep time overhead
- Minimal disk footprint
- Works on all hardware tiers
- Predictable quality (curated by humans)

**Cons:**
- Less variety (same tracks across campaigns)
- No campaign-specific customization

### Approach B: Generative Models (MusicGen + AudioGen)

**Description:** Generate campaign-specific audio during prep using MusicGen (music) and AudioGen/Tango 2 (SFX).

**Test Parameters:**
- Generate **30-45 music tracks** (5-10 per mood: combat, exploration, dialogue, tension)
- Generate **20-30 SFX** (campaign-specific: dragon roar, magic missile sound, etc.)
- Model footprint: MusicGen (~3GB) + AudioGen (~2GB) = ~5GB
- Model load time: Measure on baseline/recommended/enhanced tiers
- Generation time: Measure track generation rate (tracks per minute)
- Total disk footprint: Models (5GB) + Generated audio (300-450MB per campaign)

**Pros:**
- Campaign-specific variety
- Unique audio per campaign

**Cons:**
- Large disk footprint (5GB models + 300-450MB per campaign)
- Long prep time (model loading + generation)
- May not work on baseline tier (CPU inference too slow)

### Approach C: Hybrid (Generic Curated + Campaign-Specific Generated)

**Description:** Use curated library for generic tracks (tavern, road, forest), generate campaign-specific tracks for unique encounters/locations.

**Test Parameters:**
- Curate **15-20 generic tracks** (common scenarios)
- Generate **10-15 campaign-specific tracks** (unique to campaign theme)
- Curate **20-30 generic SFX**
- Generate **5-10 campaign-specific SFX**
- Model footprint: MusicGen (~3GB) + AudioGen (~2GB) = ~5GB
- Model load time: Measure on baseline/recommended/enhanced tiers
- Generation time: Measure for reduced track count
- Total disk footprint: Models (5GB) + Curated library (50MB) + Generated audio (100-200MB per campaign)

**Pros:**
- Balance between variety and disk footprint
- Shorter prep time (fewer tracks generated)

**Cons:**
- Still requires models (5GB)
- Complexity in managing two audio sources

---

## Evaluation Tasks

### Task 1: Curated Library Prototype

1. **Source Selection:**
   - Identify 3-5 public domain/licensed audio sources
   - Verify licensing allows distribution (no attribution-only restrictions)
   - Download 20-30 ambient loops + 20-30 SFX

2. **Quality Assessment:**
   - Subjective rating (atmospheric fit, variety, production quality)
   - Test transitions between tracks (crossfade smoothness)

3. **Attribution Ledger:**
   - Create JSON ledger with asset metadata:
     - `asset_id`, `filename`, `source`, `license`, `attribution_text`
   - Verify ledger meets M3 acceptance criteria (licensing/attribution tracked)

4. **Disk Footprint:**
   - Measure total library size
   - Calculate per-campaign overhead (if shared) vs. per-campaign copy

**Deliverable:** Curated library prototype + attribution ledger + disk footprint report

### Task 2: Generative Model Evaluation

1. **Model Setup:**
   - Install MusicGen (small/medium/large variants)
   - Install AudioGen or Tango 2
   - Measure model disk footprint

2. **Hardware Tier Testing:**
   - **Baseline Tier** (CPU-only, 16GB RAM):
     - Measure model load time
     - Measure track generation rate (tracks per minute)
     - Assess feasibility (is 10-20 min prep acceptable?)
   - **Recommended Tier** (GPU 8GB VRAM, 32GB RAM):
     - Measure model load time
     - Measure track generation rate
   - **Enhanced Tier** (GPU 16GB+ VRAM, 64GB+ RAM):
     - Measure model load time
     - Measure track generation rate

3. **Quality Assessment:**
   - Generate 10 sample tracks (varied moods: combat, exploration, tension)
   - Generate 10 sample SFX (sword hit, spell cast, door open)
   - Subjective rating (atmospheric fit, variety, production quality)

4. **Disk Footprint:**
   - Measure models + generated audio per campaign
   - Calculate storage budget impact (% of M4 baseline 20GB tier)

**Deliverable:** Model performance report (load times, generation rates) + quality samples + disk footprint analysis

### Task 3: Hybrid Approach Evaluation

1. **Combined Testing:**
   - Use curated library from Task 1 (15-20 generic tracks)
   - Generate 10-15 campaign-specific tracks using MusicGen
   - Measure total prep time (model load + generation)
   - Measure total disk footprint (models + curated + generated)

2. **Complexity Assessment:**
   - Document selection logic (when to use curated vs. generated)
   - Identify edge cases (fallback behavior if generation fails)

**Deliverable:** Hybrid approach report + complexity analysis

### Task 4: Recommendation Matrix

Based on Tasks 1-3 results, produce recommendation matrix:

| Hardware Tier | Recommended Approach | Rationale |
|---------------|---------------------|-----------|
| Baseline (CPU, 20GB) | Approach A (Curated) | Model load time too high, disk budget too tight |
| Recommended (GPU, 40GB) | Approach C (Hybrid) | Balance between variety and disk footprint |
| Enhanced (GPU 16GB+, 80GB+) | Approach B (Generative) | Sufficient resources for full generative pipeline |

**Deliverable:** Recommendation matrix + detailed rationale document

---

## Acceptance Criteria

- [ ] All three approaches evaluated on at least 2 hardware tiers (Baseline + Recommended)
- [ ] Quantitative measurements documented:
  - [ ] Disk footprint (MB) per approach per campaign
  - [ ] Model load time (seconds) for generative approaches
  - [ ] Track generation rate (tracks/minute) for generative approaches
- [ ] Subjective quality assessment completed for each approach
- [ ] Attribution ledger prototype created for curated approach
- [ ] Recommendation matrix produced with rationale
- [ ] Report delivered to pm_inbox/ for PM review

---

## Success Metrics

1. **Evaluation completeness**: All three approaches tested on ≥2 hardware tiers
2. **Data quality**: Measurements repeatable (3× runs per test, report mean ± stddev)
3. **Recommendation clarity**: PM can make informed decision based on report
4. **No integration work**: Evaluation remains isolated (no runtime code changes)

---

## Dependencies

- **Hardware Access**: Need baseline tier (CPU-only) + recommended tier (GPU) for testing
- **Model Access**: MusicGen, AudioGen/Tango 2 installation (eval only, not integrated)
- **Audio Sources**: Public domain/licensed sources for curated library

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Generative models too slow on baseline tier | High | Document clearly, recommend curated for baseline |
| Curated library quality insufficient | Medium | Test multiple sources, select best 20-30 assets |
| Licensing restrictions on curated assets | High | Verify licenses allow distribution before inclusion |
| Disk footprint exceeds M4 budget | High | Document tradeoffs, recommend per-tier approaches |

---

## Timeline Estimate

- **Task 1** (Curated Library): 2-3 hours (sourcing + testing + ledger)
- **Task 2** (Generative Models): 4-6 hours (installation + testing on 2-3 tiers)
- **Task 3** (Hybrid Approach): 2-3 hours (combined testing)
- **Task 4** (Recommendation Matrix): 1-2 hours (synthesis + report writing)

**Total Estimate**: 9-14 hours

---

## References

- [AIDM_EXECUTION_ROADMAP_V3.md](../docs/AIDM_EXECUTION_ROADMAP_V3.md) (M3 Deliverables, M4 Hardware Tiers)
- [PROJECT_COHERENCE_DOCTRINE.md](../PROJECT_COHERENCE_DOCTRINE.md) (Section 1: LLM/Generative Model Boundaries)
- [AGENT_DEVELOPMENT_GUIDELINES.md](../AGENT_DEVELOPMENT_GUIDELINES.md) (Section 10: Deliverable Routing)

---

**Next Step After Approval**: Create WO-M3-AUDIO-INT-01 (integration phase) based on approved approach from this evaluation.

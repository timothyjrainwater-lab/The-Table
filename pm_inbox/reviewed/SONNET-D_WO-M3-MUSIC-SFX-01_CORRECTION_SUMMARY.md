# WO-M3-MUSIC-SFX-01: Correction Summary

**Date:** 2026-02-10
**Reviewer:** Sonnet D
**Status:** Original Work Order REJECTED → Corrected Work Orders Drafted

---

## What Happened

**Original Work Order:** WO-M3-MUSIC-SFX-01 proposed integrating MusicGen and AudioGen into the prep pipeline to generate 30-45 music tracks and campaign-specific SFX during prep time.

**Critical Issues Identified:**
1. Treated optional generative models as mandatory (violates Execution Roadmap v3.1)
2. Placed audio generation in M2 prep pipeline (should be M3 runtime integration)
3. Skipped required evaluation phase (M3.1/M3.3/M3.5 pattern)
4. Assumed non-existent prep orchestrator (M2 only has persistence layer frozen)
5. No hardware tier analysis (disk footprint, model load time)
6. Acceptance criteria misaligned with canonical M3 requirements

---

## What Changed

The original work order has been **split into two phases** following the established M3 pattern:

### Phase 1: Evaluation (WO-M3-AUDIO-EVAL-01)

**Objective:** Evaluate three audio approaches (curated, generative, hybrid) across M4 hardware tiers.

**Key Changes:**
- ✅ **Curated library as primary approach** (not fallback)
- ✅ **Generative models as optional enhancement** (not mandatory)
- ✅ **Hardware tier testing** (baseline, recommended, enhanced)
- ✅ **Quantitative measurements** (disk footprint, model load time, generation rate)
- ✅ **Licensing/attribution ledger** (M3 acceptance criteria)

**Deliverable:** Recommendation report for PM approval

**Status:** DRAFT — Awaiting PM Approval

### Phase 2: Integration (WO-M3-AUDIO-INT-01)

**Objective:** Implement M3 audio pipeline based on approved evaluation approach.

**Key Changes:**
- ✅ **Runtime integration** (M3 immersion layer, not M2 prep pipeline)
- ✅ **Scene state → audio transitions** (M3 acceptance criteria)
- ✅ **Adapter pattern** (stub + real, like voice/image adapters)
- ✅ **Blocked until evaluation completes** (no premature integration)

**Deliverable:** M3 audio pipeline (scene state transitions, licensing record)

**Status:** BLOCKED — Awaiting WO-M3-AUDIO-EVAL-01 Results

---

## Alignment with Canonical Roadmap

### Before (WO-M3-MUSIC-SFX-01):

```
❌ M2 Prep Pipeline:
   - Install MusicGen (mandatory)
   - Install AudioGen (mandatory)
   - Generate 30-45 tracks per campaign
   - Curated library as fallback
```

### After (WO-M3-AUDIO-EVAL-01 + WO-M3-AUDIO-INT-01):

```
✅ M3 Immersion Layer:
   Phase 1: Evaluate curated vs. generative vs. hybrid
   Phase 2: Integrate approved approach

   - Curated library as acceptable primary (per roadmap)
   - Generative models as optional enhancement (per roadmap)
   - Audio transitions tied to scene state (M3 acceptance criteria)
   - Licensing/attribution record (M3 acceptance criteria)
```

---

## Canonical Roadmap Citations

### What the Roadmap Actually Says (Lines 265-267):

> **3. Audio Pipeline**
> - Ambient loops + SFX (**bundled library acceptable**)
> - **Optional** local music generator; otherwise curated generative-safe library
> - Licensing/attribution tracked for bundled assets

### M3 Acceptance Criteria (Lines 274-280):

> - [ ] Offline voice I/O functional
> - [ ] **Audio transitions tied to scene state**
> - [ ] Images are atmospheric only (no mechanics depend on them)
> - [ ] Grid appears for combat, disappears after
> - [ ] **Licensing/attribution record for bundled assets**

### M3 Supporting Task Pattern (Lines 284-300):

| Task | Description |
|------|-------------|
| M3.1 | **Evaluate and select** local STT library |
| M3.3 | **Evaluate and select** local TTS library |
| M3.5 | **Evaluate and select** local image generation |

**Audio follows same pattern:**
- M3.10-equivalent: **Evaluate and select** audio approach
- M3.11-M3.13: Implement approved approach

---

## Hardware Tier Considerations

### M4 Hardware Tiers (Roadmap Lines 332-338):

| Tier | Storage | RAM | GPU |
|------|---------|-----|-----|
| Baseline | 20GB | 16GB | Optional (CPU) |
| Recommended | 40GB | 32GB | 8GB VRAM |
| Enhanced | 80GB+ | 64GB+ | 16GB+ VRAM |

### Disk Footprint Impact (If Generative):

- **Models**: MusicGen (~3GB) + AudioGen (~2GB) = 5GB
- **Per Campaign**: 300-450MB (30-45 tracks at ~10MB/track)
- **5 Campaigns**: 1.5-2.25GB
- **Total**: 5GB + 2GB = **7GB (35% of baseline 20GB tier)**

### Evaluation Will Determine:

- Is 35% of baseline storage acceptable for audio alone?
- Is 10-20 min prep time acceptable on baseline tier (CPU generation)?
- Should baseline tier use curated library only?

---

## Next Steps

1. **PM Review** of WO-M3-AUDIO-EVAL-01 draft
2. **PM Approval** to begin evaluation phase
3. **Execute Evaluation** (9-14 hour estimate)
4. **PM Review** of evaluation results
5. **PM Approval** of recommended approach
6. **Finalize WO-M3-AUDIO-INT-01** with specific implementation tasks
7. **Execute Integration** (4-12 hours depending on approach)

---

## Files Delivered

- [pm_inbox/SONNET-D_WO-M3-MUSIC-SFX-01_CRITICAL_REVIEW.md](./SONNET-D_WO-M3-MUSIC-SFX-01_CRITICAL_REVIEW.md) — Detailed violation analysis and rejection rationale
- [pm_inbox/SONNET-D_WO-M3-AUDIO-EVAL-01_DRAFT.md](./SONNET-D_WO-M3-AUDIO-EVAL-01_DRAFT.md) — Evaluation phase work order (follows M3.1/M3.3/M3.5 pattern)
- [pm_inbox/SONNET-D_WO-M3-AUDIO-INT-01_DRAFT.md](./SONNET-D_WO-M3-AUDIO-INT-01_DRAFT.md) — Integration phase work order (blocked until evaluation completes)
- [pm_inbox/SONNET-D_WO-M3-MUSIC-SFX-01_CORRECTION_SUMMARY.md](./SONNET-D_WO-M3-MUSIC-SFX-01_CORRECTION_SUMMARY.md) — This document

---

## References

- [AIDM_EXECUTION_ROADMAP_V3.md](../docs/AIDM_EXECUTION_ROADMAP_V3.md) (M3 Deliverables, M4 Hardware Tiers)
- [PROJECT_COHERENCE_DOCTRINE.md](../PROJECT_COHERENCE_DOCTRINE.md) (Section 1: LLM/Generative Model Boundaries)
- [PROJECT_STATE_DIGEST.md](../PROJECT_STATE_DIGEST.md) (M2 Status: Persistence Layer Only)
- [AGENT_DEVELOPMENT_GUIDELINES.md](../AGENT_DEVELOPMENT_GUIDELINES.md) (Section 10: Deliverable Routing)

---

**Logged:** 2026-02-10
**Reviewer:** Sonnet D
**Recommendation:** Approve WO-M3-AUDIO-EVAL-01 to begin M3 audio work

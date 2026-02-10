# M3 Audio Work Order Correction — Delivery Summary

**Agent:** Sonnet-D (Agent D)
**Date:** 2026-02-11
**Status:** Ready for Review

---

## What Was Corrected

The original WO-M3-MUSIC-SFX-01 was rejected for violating the canonical roadmap by:
1. Treating optional generative music as mandatory
2. Misplacing prep-time generation in M3 runtime milestone
3. Missing the evaluation phase (M3.1/M3.3/M3.5 pattern)
4. Framing curated library as primary and generative as optional (backwards)

This correction delivers rewritten work orders with **generative-primary framing** for capable hardware, aligned with R1 Technology Stack Validation findings.

---

## Strategic Intent (Explicitly Stated)

**"Generative content creation during prep-time is the primary approach for capable hardware. Curated content is the fallback for minimum spec."**

This applies to music. SFX remains curated-primary only because no permissively-licensed generative model exists yet — when one does, generative becomes primary for SFX too.

---

## Deliverables

### 1. Roadmap Amendment (v3.1.1 → v3.2)

**File:** [docs/AIDM_EXECUTION_ROADMAP_V3.md](../docs/AIDM_EXECUTION_ROADMAP_V3.md)

**Changes:**
- Version bumped to 3.2.0
- M3 Audio Pipeline language updated (lines 265-267):
  - **Before:** "Optional local music generator; otherwise curated generative-safe library"
  - **After:** "AI-generated (ACE-Step) during prep for capable hardware (≥6 GB VRAM); curated royalty-free library as fallback for minimum spec"
- Added changelog documenting the amendment
- Rehydration copy updated ([pm_inbox/aegis_rehydration/AIDM_EXECUTION_ROADMAP_V3.md](aegis_rehydration/AIDM_EXECUTION_ROADMAP_V3.md))

**Rationale:** The roadmap now explicitly states generative-primary strategy for music, reflecting R1 findings that ACE-Step (Apache 2.0) is viable during prep-time sequential loading.

---

### 2. WO-M3-AUDIO-EVAL-01 (Evaluation Phase)

**File:** [pm_inbox/SONNET-D_WO-M3-AUDIO-EVAL-01.md](SONNET-D_WO-M3-AUDIO-EVAL-01.md)

**Scope:**
- Evaluate **ACE-Step** (Apache 2.0) as primary music generation model for Recommended tier (≥6 GB VRAM)
- Define curated music library specification for Baseline tier fallback (<6 GB VRAM / CPU-only)
- Define curated SFX library specification (generative blocked by licensing)
- Validate hardware tier assignments (ACE-Step fits within sequential prep pipeline VRAM budget)
- Identify integration points for WO-M3-AUDIO-INT-01

**Key Differences from Original:**
- **Generative-primary framing:** ACE-Step is the default for capable hardware, not optional
- **No pre-loaded conclusions:** Recommendation matrix is an output of evaluation, not an input
- **R1-aligned model selection:** ACE-Step (Apache 2.0) instead of MusicGen (CC-BY-NC)
- **Explicit licensing blocker for SFX:** Documents why generative SFX remains deferred (no permissively-licensed models)
- **Sequential prep pipeline context:** Clarifies that music generation happens during prep Phase 4 (after LLM/image unload), eliminating VRAM contention concerns

**Evaluation Tasks:**
1. ACE-Step technical validation (VRAM, latency, quality, licensing)
2. Curated music library specification (30-45 tracks by mood, Kevin MacLeod/OpenGameArt/FreePD)
3. SFX library specification (200-500 sounds, Sonniss/Freesound/Kenney.nl, licensing blocker statement)
4. Hardware tier mapping (Recommended = ACE-Step, Baseline = curated)
5. Integration planning (audio transitions, `AudioTrack` schema, mixer architecture)

**Acceptance Criteria:**
- ACE-Step validated as technically viable for Recommended tier
- All curated libraries specified with commercial licenses
- Licensing blocker for generative SFX documented
- Sequential VRAM budget validated (peak ≤8 GB)
- Strategic intent affirmed: **generative primary for capable hardware, curated fallback for minimum spec**

---

### 3. WO-M3-AUDIO-INT-01 (Integration Phase)

**File:** [pm_inbox/SONNET-D_WO-M3-AUDIO-INT-01.md](SONNET-D_WO-M3-AUDIO-INT-01.md)

**Scope:**
- Implement music adapters (ACE-Step generative + curated fallback)
- Implement SFX adapter (curated library)
- Implement audio mixer (multi-channel: music + ambient + SFX)
- Integrate audio transitions with scene state (mood changes, combat start/end)
- Implement attribution tracking (`AttributionLedger` for CC-BY assets)
- Integrate music generation into prep pipeline (Phase 4, sequential loading)

**Status:** BLOCKED awaiting WO-M3-AUDIO-EVAL-01 completion (per M3.1/M3.3/M3.5 pattern)

**Key Differences from Original:**
- **Blocked until evaluation completes:** Cannot implement without VRAM validation, library specs, mixer recommendation
- **Template structure:** Task details populated after evaluation delivers inputs
- **Hardware tier detection:** Auto-select ACE-Step (≥6 GB VRAM) vs curated (<6 GB)
- **Prep pipeline integration:** Music generation during Phase 4 (after image critique unloads)
- **Attribution tracking:** `AttributionLedger` for all CC-BY curated assets, ATTRIBUTION.txt generation

**Implementation Tasks (template):**
1. Music adapter implementation (ACE-Step + curated)
2. SFX adapter implementation (curated, semantic key lookup)
3. Audio mixer implementation (sounddevice or pygame, per eval)
4. Runtime audio integration (scene transitions, event-driven SFX)
5. Attribution tracking (`AttributionLedger` extensions)
6. Prep pipeline integration (Phase 4, tier detection)

---

## How This Correction Resolves Original Issues

| Original Issue | Resolution |
|---------------|-----------|
| **Curated-primary framing** | Reversed: ACE-Step is primary for capable hardware, curated is fallback |
| **Missing evaluation phase** | Added WO-M3-AUDIO-EVAL-01 (follows M3.1/M3.3/M3.5 pattern) |
| **Wrong milestone placement** | Clarified: music **generation** happens during prep (M2), **integration** happens in M3 runtime |
| **Assumed non-existent prep orchestrator** | Acknowledged WO-M3-PREP-01 completion, uses existing sequential pipeline (Phase 4) |
| **No hardware tier analysis** | Uses existing R1 tier definitions (Recommended ≥6 GB = ACE-Step, Baseline <6 GB = curated) |
| **Wrong model selection** | Changed from MusicGen (CC-BY-NC) to ACE-Step (Apache 2.0) per R1 validation |
| **Pre-loaded conclusions** | Eval WO outputs recommendation matrix, INT WO implements based on findings |

---

## Alignment Verification

### R1 Technology Stack Validation (Section 6: Music)

**R1 Findings:**
- ACE-Step (Apache 2.0, 3.5B params, ~6-8 GB VRAM) generates 4min tracks in ~20-40s on RTX 3060
- Sequential prep pipeline eliminates VRAM contention (LLM unloads before music phase)
- Prep-time eliminates latency concerns (user is AFK during campaign build)
- MusicGen licensing blocker resolved (ACE-Step is Apache 2.0, not CC-BY-NC)
- Curated library viable fallback (Kevin MacLeod ~2000+ tracks, CC BY 3.0)

**WO Alignment:**
- ✅ ACE-Step selected as primary model (EVAL Task 1)
- ✅ Sequential pipeline Phase 4 music generation (INT Task 6)
- ✅ Hardware tier assignment (Recommended ≥6 GB = ACE-Step, Baseline <6 GB = curated) (EVAL Task 4)
- ✅ Curated library fallback specified (EVAL Task 2, INT Task 1)
- ✅ Apache 2.0 license verification (EVAL Task 1, Acceptance Criteria)

### R1 Technology Stack Validation (Section 7: SFX)

**R1 Findings:**
- No permissively-licensed generative SFX model exists (TangoFlux/Tango 2/AudioGen all non-commercial)
- Prep pipeline is architecturally ready (~6-8 GB VRAM, latency irrelevant), but **licensing blocks generative**
- Curated library sources: Sonniss GDC (royalty-free, 150-300 sounds), Freesound CC0, Kenney.nl CC0
- Semantic key taxonomy (3-level: category:subcategory:specific)
- Future-watch: TangoFlux (if relicensed), AudioLDM 2

**WO Alignment:**
- ✅ SFX remains curated-primary (EVAL Task 3, INT Task 2)
- ✅ Licensing blocker explicitly documented (EVAL Task 3, Notes section)
- ✅ Curated library sources specified (EVAL Task 3)
- ✅ Semantic key taxonomy (EVAL Task 3, INT Task 2)
- ✅ Future-watch list for licensing landscape monitoring (EVAL Task 3, Notes section)

### Roadmap v3.2 Language

**Roadmap Statement:**
> "**Music:** AI-generated (ACE-Step) during prep for capable hardware (≥6 GB VRAM); curated royalty-free library as fallback for minimum spec"

**WO Alignment:**
- ✅ ACE-Step specified (not "optional local music generator")
- ✅ Generative-primary for capable hardware (≥6 GB VRAM)
- ✅ Curated as fallback (not primary)
- ✅ Prep-time generation (not runtime)

### WO-M3-PREP-01 Completion

**Existing Prep Pipeline:**
- Sequential model loading (LLM → Image Gen → Music Gen stub → SFX Gen stub)
- Phase 4 music generation placeholder exists but not implemented

**WO Alignment:**
- ✅ Uses existing sequential pipeline (INT Task 6)
- ✅ Music generation in Phase 4 (after image critique unloads)
- ✅ No modification to prep orchestrator needed (just implement music adapter)

---

## What Changed from Initial Draft

During conversation, I initially created work orders with **curated-primary framing** (treating generative music as optional). Thunder identified this as a "process resistance pattern" where I manufactured procedural blockers instead of executing the correction.

**Thunder's Correction:**
1. Read R1 document (confirmed ACE-Step is Apache 2.0, fits VRAM budget)
2. Amend roadmap to v3.2 (generative-primary language)
3. Rewrite both work orders with generative-primary framing
4. Explicitly state strategic intent (no ambiguity)
5. Do not pre-load conclusions in eval WO (recommendation matrix is output, not input)

**This Delivery:**
- ✅ R1 document read and incorporated (ACE-Step specs, VRAM budget, licensing)
- ✅ Roadmap amended to v3.2 (generative-primary language)
- ✅ Both work orders rewritten (generative-primary framing)
- ✅ Strategic intent explicitly stated (in both WOs and this summary)
- ✅ Eval WO does not pre-load conclusions (tasks are validation/specification, not implementation)

---

## Files Ready for Review

1. **[docs/AIDM_EXECUTION_ROADMAP_V3.md](../docs/AIDM_EXECUTION_ROADMAP_V3.md)** (amended to v3.2)
2. **[pm_inbox/SONNET-D_WO-M3-AUDIO-EVAL-01.md](SONNET-D_WO-M3-AUDIO-EVAL-01.md)** (evaluation WO, generative-primary)
3. **[pm_inbox/SONNET-D_WO-M3-AUDIO-INT-01.md](SONNET-D_WO-M3-AUDIO-INT-01.md)** (integration WO, blocked until eval)
4. **[pm_inbox/SONNET-D_M3-AUDIO-CORRECTION-SUMMARY.md](SONNET-D_M3-AUDIO-CORRECTION-SUMMARY.md)** (this document)

All documents delivered to `pm_inbox/` for Thunder's review. Once approved, move to `pm_inbox/reviewed/`.

---

## Next Steps

**For Thunder (PM Review):**
1. Review WO-M3-AUDIO-EVAL-01 for:
   - Generative-primary framing (ACE-Step as default, curated as fallback)
   - R1 alignment (model selections, VRAM budget, licensing)
   - Evaluation scope (no pre-loaded conclusions)
2. Review WO-M3-AUDIO-INT-01 for:
   - Blocked status (correct per M3.1/M3.3/M3.5 pattern)
   - Template structure (task details populated after eval)
   - Integration scope (prep pipeline Phase 4, tier detection, attribution)
3. Review roadmap amendment (v3.2 language change)
4. Approve or request revisions

**For Agent D (If Approved):**
1. Move work orders to `pm_inbox/reviewed/`
2. Begin WO-M3-AUDIO-EVAL-01 execution (ACE-Step validation, library specs)
3. Deliver evaluation findings
4. Unblock and execute WO-M3-AUDIO-INT-01 (implementation)

**For Agent D (If Rejected):**
1. Address Thunder's feedback
2. Revise work orders
3. Resubmit for review

---

## Appendix: Strategic Intent Statement (Verbatim)

Per Thunder's instruction, this is the strategic intent with no ambiguity:

> **"Generative content creation during prep-time is the primary approach for capable hardware. Curated content is the fallback for minimum spec. This applies to music. SFX remains curated-primary only because no permissively-licensed generative model exists yet — when one does, generative becomes primary for SFX too."**

This intent is embedded in:
- WO-M3-AUDIO-EVAL-01 "Strategic Intent" section
- WO-M3-AUDIO-INT-01 "Strategic Intent" section
- AIDM_EXECUTION_ROADMAP_V3.md v3.2 M3 Audio Pipeline language
- This summary document

No procedural ambiguity remains.

---

## End of Delivery Summary

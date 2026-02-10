# Bounded Regeneration Policy — R0 Research Draft

**Status:** R0 / DRAFT / NON-BINDING
**Purpose:** Define regeneration attempts, backoff strategy, and fallback policy for failed image generation
**Authority:** Advisory — requires validation against actual performance
**Last Updated:** 2026-02-10
**Research Context:** Image critique viability analysis for AIDM immersion pipeline

---

## ⚠️ DRAFT NOTICE

This document is a **research draft** defining regeneration policy for automated image validation. It is **not binding** until:

1. Error rate analysis validates rejection thresholds
2. User testing confirms UX acceptability of max attempts
3. Fallback strategies tested and approved
4. Formal approval locks regeneration policy

**Do not use for implementation** until validated.

---

## Executive Summary

**Problem:** Automated image critique may reject generated images. How many times should we regenerate before giving up?

**TL;DR Answer:**
- **Max attempts:** 3 regenerations per image (4 total generations: original + 3 retries)
- **Backoff strategy:** Adjust generation parameters after each failure (increase guidance scale, reduce creativity)
- **Fallback hierarchy:** Shipped art pack → User manual accept → Alternate generation settings → Abort and use placeholder
- **Time budget:** Max 60 seconds total (prep-time constraint, not real-time)

**Key Principle:** **Fail gracefully.** Never leave user with no image. Always provide fallback.

---

## Regeneration Policy

### Max Attempts

**Recommendation:** **3 regeneration attempts** (4 total generations: original + 3 retries)

**Rationale:**
- **Attempt 1 (original):** Default generation settings (base case)
- **Attempt 2 (retry 1):** Increase guidance scale by 20% (tighter adherence to prompt)
- **Attempt 3 (retry 2):** Reduce creativity/variation, increase CFG scale further
- **Attempt 4 (retry 3):** Minimal creativity, maximum prompt adherence

**If all 4 attempts fail:** Escalate to fallback hierarchy (see below)

**Trade-offs:**
- **Too few attempts (1-2):** High chance of fallback to shipped art (poor UX if generation viable)
- **Too many attempts (5+):** Wastes time/compute (each generation ~2-5s on GPU, 30-60s on CPU)
- **3 attempts:** Balances UX (reasonable effort) vs cost (acceptable time budget)

### Time Budget

**Total time budget for image generation + critique:** **60 seconds max**

**Breakdown (GPU):**
- Attempt 1: Generation ~3s + Critique ~0.125s = ~3.125s
- Attempt 2: Generation ~3s + Critique ~0.125s = ~3.125s
- Attempt 3: Generation ~3s + Critique ~0.125s = ~3.125s
- Attempt 4: Generation ~3s + Critique ~0.125s = ~3.125s
- **Total: ~12.5 seconds (GPU, 4 attempts)**

**Breakdown (CPU):**
- Attempt 1: Generation ~45s + Critique ~0.085s = ~45.085s
- Attempt 2: Generation ~45s + Critique ~0.085s = ~45.085s
- **Total: ~90 seconds (CPU, 2 attempts) — EXCEEDS BUDGET**

**Implication:** **CPU-only users limited to 1-2 attempts max** (or longer time budget).

**Recommendation:** Set time budget based on hardware:
- **GPU:** 60 seconds (allows 4 attempts)
- **CPU:** 120 seconds (allows 2 attempts) OR 60 seconds (allows 1 attempt)

### Rejection Threshold

**When to regenerate:**
- Critique returns **CRITICAL** or **MAJOR** failure (see R0_IMAGE_CRITIQUE_RUBRIC.md)
- Critique score below acceptable threshold (e.g., F1 score <0.70)

**When to accept:**
- Critique returns **ACCEPTABLE** (all critical/major checks pass)
- Critique score above threshold (e.g., F1 score ≥0.70)

**When to escalate to fallback:**
- All max attempts exhausted (3 retries) AND critique still fails
- Time budget exceeded (60s GPU, 120s CPU)
- User manually aborts regeneration

---

## Backoff Strategy (Parameter Adjustment)

### Principle

**Each retry adjusts generation parameters to fix likely causes of failure.**

**Goal:** Increase likelihood of passing critique with each attempt.

### Adjustment Schedule

**Attempt 1 (Original):**
- **CFG Scale (Classifier-Free Guidance):** 7.5 (default)
- **Sampling Steps:** 50 (default)
- **Creativity/Variation:** 0.8 (default)
- **Prompt:** Original prompt (e.g., "dwarf warrior with red beard, fantasy art")

**Attempt 2 (Retry 1 — Tighter Adherence):**
- **CFG Scale:** 9.0 (+20%, tighter adherence to prompt)
- **Sampling Steps:** 60 (+20%, more refinement)
- **Creativity/Variation:** 0.7 (-0.1, less random variation)
- **Prompt:** Same prompt (no change)

**Rationale:** Most failures due to weak adherence to prompt (style drift, composition issues). Increasing CFG/steps forces model to follow prompt more closely.

**Attempt 3 (Retry 2 — Maximum Adherence):**
- **CFG Scale:** 11.0 (+47% from original, very tight)
- **Sampling Steps:** 70 (+40%, maximum refinement)
- **Creativity/Variation:** 0.5 (-0.3, minimal variation)
- **Prompt:** Enhanced prompt (add negative prompt: "blurry, deformed, cropped, low quality")

**Rationale:** If retry 1 failed, assume model needs stronger constraints. Add negative prompt to explicitly forbid common artifacts.

**Attempt 4 (Retry 3 — Conservative Settings):**
- **CFG Scale:** 13.0 (+73% from original, extreme adherence)
- **Sampling Steps:** 80 (+60%, overkill refinement)
- **Creativity/Variation:** 0.3 (-0.5, near-deterministic)
- **Prompt:** Enhanced prompt + style anchor (e.g., "in the style of D&D Player's Handbook art")

**Rationale:** Last attempt before fallback. Use extreme settings to force model compliance. Risk: May produce "stiff" or "over-processed" images, but better than total failure.

### Failure-Specific Adjustments

**If critique fails on specific dimension, adjust accordingly:**

**Readability (blur/detail):**
- Increase sampling steps by +30%
- Add negative prompt: "blurry, low detail, soft focus"

**Composition (centering/framing):**
- Add prompt guidance: "centered, full body, medium shot, rule of thirds"
- Increase CFG scale by +20%

**Artifacting (hands/eyes):**
- Add negative prompt: "deformed hands, extra fingers, asymmetric eyes, anatomical error"
- Increase sampling steps by +40%
- Reduce creativity by -0.2

**Style adherence:**
- Add style anchor: "in the style of [reference artist/style]"
- Increase CFG scale by +30%

**Identity match (NPC continuity):**
- Include anchor image as reference (if model supports img2img)
- Add descriptive tags from anchor: "red hair, scar on left cheek, blue eyes"
- Increase CFG scale by +20%

---

## Fallback Hierarchy

**If all regeneration attempts fail, escalate through fallback hierarchy:**

### Level 1: Shipped Art Pack (Recommended Fallback)

**Description:** Pre-vetted, curated art assets shipped with AIDM.

**Coverage:**
- **Portraits:** 50-100 generic NPC portraits (races: human, elf, dwarf, halfling, gnome, orc, tiefling)
- **Tokens:** 50-100 generic creature tokens (common monsters from MM)
- **Scenes:** 20-30 generic scene cards (dungeon, forest, tavern, castle, etc.)

**Quality:** Professional or high-quality community art, manually vetted for quality/style consistency.

**Pros:**
- Always available (no generation required)
- Guaranteed quality (manually vetted)
- Deterministic (same asset every time)

**Cons:**
- Generic (not tailored to specific NPC/scene)
- Limited variety (50-100 assets vs infinite generation)
- Breaks immersion (user sees same portrait for different NPCs)

**Acceptance Criteria:**
- User accepts shipped art as "good enough" for placeholder
- DM plans to replace with custom art later
- Session can proceed without blocking on image generation

**UX Flow:**
```
Generation failed after 3 retries.
[Fallback: Shipped Art Pack]
Using generic dwarf warrior portrait (Art Pack #23).
[Accept] [Try Custom Settings] [Use Placeholder]
```

### Level 2: User Manual Accept (Override)

**Description:** Show user the rejected image and allow manual override.

**Use Case:** Critique rejected image, but user judges it "good enough" for their needs.

**Pros:**
- User has final say (respects user agency)
- May accept images with minor flaws (e.g., slight blur acceptable for background NPC)

**Cons:**
- Requires user interaction (breaks prep automation)
- User must judge quality manually (defeats purpose of automated critique)

**UX Flow:**
```
Generation failed critique (MAJOR: slight blur detected).
[Show Image]
Quality issue detected: Image slightly blurry at UI size.
[Accept Anyway] [Regenerate with Custom Settings] [Use Shipped Art]
```

**Recommendation:** Offer this option only if critique failure is MINOR (not CRITICAL). Do not show obviously broken images (e.g., 6-fingered hands).

### Level 3: Alternate Generation Settings (User-Defined)

**Description:** Allow user to specify custom generation parameters (CFG, steps, prompt).

**Use Case:** Automated backoff strategy failed, but user knows specific tweaks that might work.

**Pros:**
- Gives expert users control
- May succeed where automated backoff failed

**Cons:**
- Requires technical knowledge (CFG scale, sampling steps, negative prompts)
- Breaks prep automation (requires user intervention)
- May still fail (no guarantee custom settings work)

**UX Flow:**
```
Automated regeneration failed (3 attempts).
[Advanced] Try custom generation settings?
CFG Scale: [___] Sampling Steps: [___] Negative Prompt: [___]
[Generate] [Cancel]
```

**Recommendation:** Hide behind "Advanced" option (expert users only).

### Level 4: Placeholder (Abort)

**Description:** Use a generic placeholder image (e.g., silhouette, "?" icon).

**Use Case:** All fallbacks exhausted or user aborts.

**Pros:**
- Always available (no dependencies)
- Deterministic (same placeholder every time)

**Cons:**
- Poor UX (generic placeholder breaks immersion)
- User must replace manually later

**UX Flow:**
```
Image generation aborted.
Using placeholder silhouette for [NPC Name].
You can upload a custom image later.
[OK]
```

**Recommendation:** Last resort only. Prefer shipped art pack over placeholder.

---

## Fallback Decision Tree

```
Start: Generate image
  ↓
Critique: Pass/Fail?
  ↓
[PASS] → Accept image, done ✓
  ↓
[FAIL] → Attempts left?
  ↓
[YES] → Retry with adjusted parameters → Critique again
  ↓
[NO] → Fallback Hierarchy:
  ↓
1. Shipped Art Pack available for this type?
   [YES] → Offer shipped art → User accepts? → Done ✓
   [NO] → Continue to Level 2
  ↓
2. Critique failure is MINOR?
   [YES] → Offer manual override → User accepts? → Done ✓
   [NO] → Continue to Level 3
  ↓
3. User wants custom settings?
   [YES] → Offer custom generation → Generate → Critique again
   [NO] → Continue to Level 4
  ↓
4. Use placeholder silhouette → Done ⚠️ (user warned)
```

---

## Edge Cases & Special Handling

### Case 1: Identity Match Failure (NPC Anchor Drift)

**Problem:** Generated NPC portrait drifts from anchor (species change, age change).

**Special Handling:**
- **Attempt 1-2:** Use standard backoff (increase CFG, add negative prompt)
- **Attempt 3:** Include anchor image as reference (img2img, if supported)
- **Attempt 4:** Explicitly add anchor features to prompt: "red hair, scar on left cheek, blue eyes, male dwarf, age 40"
- **Fallback:** Use original anchor image (reuse previous portrait) OR shipped art pack

**Rationale:** Identity drift is CRITICAL for NPC continuity. Prefer reusing anchor over accepting drifted image.

### Case 2: Style Adherence Failure (Campaign Style Mismatch)

**Problem:** Generated image violates campaign art style (e.g., anime in fantasy realism).

**Special Handling:**
- **Attempt 1-2:** Add style anchor to prompt: "in the style of D&D Player's Handbook"
- **Attempt 3:** Add negative prompt: "anime, cartoon, modern, photograph"
- **Attempt 4:** Use style reference image (if model supports ControlNet/style transfer)
- **Fallback:** Shipped art pack (manually vetted for style consistency)

**Rationale:** Style consistency is HIGH priority for campaign coherence. Shipped art pack preferred over style-mismatched generation.

### Case 3: Critical Artifacting (6 Fingers, Wall Eyes)

**Problem:** Generated image has obvious AI artifacts (hands, eyes).

**Special Handling:**
- **DO NOT offer manual override** (CRITICAL failures are non-negotiable)
- **Attempt 1-2:** Add negative prompt: "deformed hands, extra fingers, asymmetric eyes"
- **Attempt 3:** Reduce creativity to 0.3 (near-deterministic)
- **Attempt 4:** Use conservative settings (CFG 13.0, steps 80)
- **Fallback:** Shipped art pack OR placeholder (do not show broken image to user)

**Rationale:** 6-fingered hands, wall eyes are instant immersion-breakers. Better to use shipped art than show broken image.

### Case 4: CPU-Only User (Slow Generation)

**Problem:** CPU-only user cannot afford 4 attempts (time budget ~120s for 2 attempts).

**Special Handling:**
- **Limit to 2 attempts max** (1 original + 1 retry)
- **Use aggressive backoff** (CFG 11.0, steps 70 on retry 1)
- **Fallback earlier:** Offer shipped art pack after 2 failures
- **Alternative:** Allow user to opt into longer time budget (e.g., 180s for 3 attempts)

**Rationale:** CPU users have limited compute. Respect time budget, fail gracefully.

### Case 5: GPU VRAM Exhausted (OOM)

**Problem:** GPU runs out of VRAM during generation (e.g., batch generation + CLIP critique).

**Special Handling:**
- **Degrade to CPU generation** (if time budget allows)
- **Reduce batch size** (generate 1 image at a time instead of batching)
- **Skip CLIP critique** (use heuristics-only to save VRAM)
- **Fallback:** Shipped art pack OR restart with lower memory settings

**Rationale:** Out-of-memory errors are hardware constraints. Degrade gracefully, warn user.

---

## User Experience Recommendations

### Transparent Feedback

**Always inform user of regeneration status:**
- "Generating portrait for Thorin Ironforge... (Attempt 1/4)"
- "Critique failed (blur detected). Retrying with higher detail... (Attempt 2/4)"
- "Critique failed (anatomical error). Retrying with conservative settings... (Attempt 3/4)"
- "All attempts failed. Using shipped art pack (Dwarf Warrior #12)."

**Rationale:** Transparency builds trust, shows progress, explains failures.

### Progress Indicators

**Show visual progress during generation:**
- Progress bar: [▓▓▓▓▓▓▓░░░] 70% (Attempt 2/4)
- Estimated time remaining: ~5 seconds
- Current status: "Critiquing image..."

**Rationale:** Long waits (60-120s) feel shorter with progress feedback.

### User Control

**Allow user to abort or skip:**
- [Abort] button: Immediately stop generation, use fallback
- [Skip Critique] button: Accept image without critique (expert users only)
- [Use Shipped Art] button: Skip generation entirely, go straight to fallback

**Rationale:** Respect user time, provide escape hatch if generation stuck.

---

## Performance Targets

### Latency

**Total time budget (generation + critique):**
- **GPU:** 60 seconds max (4 attempts at ~3s each + critique)
- **CPU:** 120 seconds max (2 attempts at ~45s each + critique)

**If time budget exceeded:** Abort remaining attempts, escalate to fallback.

### Throughput (Batch Generation)

**Prep-time batch generation (e.g., 10 NPC portraits):**
- **GPU:** 10 images × 4 attempts × 3s = ~120 seconds (2 minutes)
- **CPU:** 10 images × 2 attempts × 45s = ~900 seconds (15 minutes)

**Optimization:** Parallelize generation (generate multiple images simultaneously if VRAM/RAM allows).

**Rationale:** Prep-time generation is async (not real-time). 2-15 minutes acceptable for batch generation.

---

## Validation & Monitoring

### Metrics to Track

**Rejection Rate:**
- % of generated images rejected by critique (by attempt number)
- Target: <30% rejection rate on attempt 1, <10% on attempt 4

**Fallback Rate:**
- % of images that escalate to fallback (shipped art pack or placeholder)
- Target: <5% fallback rate (95% success within 4 attempts)

**User Override Rate:**
- % of users who manually accept rejected images
- Target: <10% override rate (critique mostly agrees with user judgment)

**Time to Accept:**
- Average time from generation start to accepted image
- Target: <10 seconds (GPU), <60 seconds (CPU)

### A/B Testing

**Test different policies:**
- **Policy A:** 3 attempts, aggressive backoff
- **Policy B:** 5 attempts, conservative backoff
- **Policy C:** 2 attempts, immediate fallback to shipped art

**Measure:**
- User satisfaction (survey: "Were you happy with the generated image?")
- Fallback rate (how often do users get shipped art vs custom generation?)
- Time to completion (how long did prep take?)

**Goal:** Find optimal balance between attempts (quality) and time budget (UX).

---

## Open Questions (Require Empirical Validation)

1. **Is 3 attempts optimal?** Or should we allow 4-5 for high-priority images (e.g., main villain portrait)?
2. **Should CPU users get longer time budget (120s)?** Or is 60s hard limit acceptable?
3. **How often will users override critique?** If >20%, critique may be too strict.
4. **Is shipped art pack acceptance rate high?** If <50%, users may prefer placeholder over shipped art.
5. **Should we cache successful generation parameters?** E.g., if CFG 11.0 succeeds for one dwarf, use it for all dwarves?

---

## Decision: Bounded Regeneration Policy

**RECOMMENDED POLICY:**

**Max Attempts:** 3 retries (4 total generations)
**Time Budget:** 60 seconds (GPU) / 120 seconds (CPU)
**Backoff Strategy:** Progressive parameter adjustment (CFG +20% → +47% → +73%, steps +20% → +40% → +60%)
**Fallback Hierarchy:** Shipped Art Pack → User Manual Accept → Custom Settings → Placeholder

**"Good Enough" Threshold:** F1 score ≥0.70 (critique accepts image)

**Shippable Alternative (If All Fails):**
- **Primary:** Shipped art pack (50-100 pre-vetted assets per type)
- **Secondary:** User manual accept (for MINOR failures only)
- **Tertiary:** Placeholder silhouette (last resort)

**Blocking Issues:** None (policy covers all failure modes acceptably)

---

## Next Steps

1. **Prototype regeneration loop:** Implement 4-attempt backoff strategy, measure rejection rates
2. **User testing:** Validate time budget acceptability (60s GPU, 120s CPU)
3. **Shipped art pack curation:** Collect/vet 50-100 assets per type (portraits, tokens, scenes)
4. **Threshold calibration:** Empirically determine "good enough" F1 score threshold
5. **A/B testing:** Compare 3-attempt vs 5-attempt policy on user satisfaction

---

## References

- **Stable Diffusion Guidance Scale:** https://huggingface.co/docs/diffusers/using-diffusers/write_your_own_pipeline#classifier-free-guidance
- **Sampling Steps (DDIM):** Song et al., "Denoising Diffusion Implicit Models"
- **Negative Prompts:** https://stable-diffusion-art.com/negative-prompt/
- **Steam Hardware Survey:** https://store.steampowered.com/hwsurvey

---

## Document Governance

**Status:** R0 / DRAFT
**Approval Required From:** Project owner (human)
**Depends On:** R0_IMAGE_CRITIQUE_RUBRIC.md, R0_IMAGE_CRITIQUE_FEASIBILITY.md, HARDWARE_BASELINE_REPORT.md
**Unblocks:** Immersion pipeline image generation integration (future CP)
**Future Work:** Empirical validation, user testing, shipped art pack curation

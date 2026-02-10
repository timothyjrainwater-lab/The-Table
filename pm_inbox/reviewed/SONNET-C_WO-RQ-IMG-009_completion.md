# Work Order Completion Report: WO-RQ-IMG-009

**Agent:** Sonnet-C
**Work Order:** WO-RQ-IMG-009 (Image Generation Failure Fallback Design)
**Date:** 2026-02-11
**Status:** Design Phase Complete ✅

---

## 1. Executive Summary

Successfully completed design phase for image generation failure fallback strategy. Comprehensive design specification delivered to `docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md`.

**Core Achievement:** Four-tier graceful degradation system ensuring game remains playable without images (M3 principle: "No mechanical dependence on images").

**Total Deliverable:** ~1,100 lines of design documentation covering all 7 tasks from approved work order draft.

---

## 2. Acceptance Criteria Verification

### From WO-RQ-IMG-009 Draft:

- [x] **Placeholder strategy options defined** (4 strategies: shipped art pack, generic category, solid color + text, text-only)
  - Section 1: Complete comparison table, pros/cons, use cases
  - Shipped art pack prioritized as first fallback (highest quality)
  - Text-only mode as last resort (always available, zero dependencies)

- [x] **Failure trigger conditions defined** (5 triggers: max attempts, timeout, user abort, hardware failure, bad prompt)
  - Section 2: Complete trigger detection logic, example logs
  - Hardware-specific limits: GPU 4 attempts, CPU 2-3 attempts
  - Bad prompt detection: Flag prompts with scores <0.30 across all attempts

- [x] **User notification design specified** (3 notification types: log entry, summary report, UI notification)
  - Section 3: Complete examples for each notification type
  - Real-time log during prep execution
  - Summary report at end of prep (Markdown format)
  - M1+ UI notification design (toast/modal)

- [x] **Persistence of failed attempts specified** (error logging, regeneration history, idempotent re-run)
  - Section 4: Complete error record schema, regeneration history persistence
  - Manual review queue for bad prompts (`failed_prompts.json`)
  - Idempotent prep re-run workflow (regenerate failed only, regenerate placeholders)

- [x] **Graceful degradation across tiers defined** (Tier 1-5 behavior, consistent fallback system)
  - Section 5: Complete tier comparison table, config examples
  - Tier 5 placeholder-by-default with opt-in generation
  - Consistent fallback hierarchy across all tiers

- [x] **Asset store integration specified** (placeholder storage, generation method marking, upgrade path)
  - Section 6: Complete schema extensions, placeholder storage format
  - `generation_method="placeholder"` marker for querying
  - Placeholder upgrade workflow for re-runs

- [x] **Fallback hierarchy decision tree documented** (archetype matching logic, example walkthroughs)
  - Section 7: Complete decision tree flowchart, 4 example walkthroughs
  - Archetype matching logic for NPC portraits, scenes, items
  - Graceful degradation: shipped art pack → generic → solid color → text-only

---

## 3. Deliverable Summary

### 3.1 Design Document Created

**File:** [docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md](../../docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md)

**Length:** ~1,100 lines

**Sections:**
1. Executive Summary
2. Placeholder Strategy Options (4 strategies with comparison table)
3. Failure Trigger Conditions (5 triggers with detection logic)
4. User Notification Design (3 notification types with examples)
5. Persistence of Failed Attempts (error logging, idempotent re-run)
6. Graceful Degradation Across Tiers (Tier 1-5 behavior)
7. Asset Store Integration (schema extensions, upgrade path)
8. Fallback Hierarchy Decision Tree (flowchart + 4 example walkthroughs)
9. Schema Extensions (GeneratedAsset, PrepPipelineConfig)
10. Integration Notes (prep pipeline, critique system, shipped art pack)
11. Future Work (M1+ scope: manual accept/reject, custom settings, retry later)
12. Acceptance Criteria (all 7 tasks complete)
13. References

### 3.2 Design Highlights

#### Four-Tier Fallback Hierarchy

```
Fallback Hierarchy (Ordered by Quality):
1. Shipped Art Pack (archetype-specific)
   - 50-100 NPC portraits, 20-30 scenes, 10-20 items
   - Manually vetted, professionally created
   - Archetype matching: exact → partial → species-only → generic

2. Generic Category Placeholder
   - 3 images total (NPC, scene, item)
   - Silhouette/abstract visuals
   - Always available

3. Solid Color + Text Overlay
   - Dynamically generated (Pillow)
   - Asset-specific (shows name + description)
   - Color-coded by type (NPC: blue, scene: green, item: purple)

4. Text-Only Mode (Last Resort)
   - No image file created
   - UI shows text description only
   - Zero dependencies, always available
```

#### Five Failure Triggers

1. **Max Regeneration Attempts Exhausted** — GPU: 4 attempts, CPU: 2-3 attempts (per WO-RQ-IMG-010)
2. **Time Budget Exceeded** — GPU: 60s, CPU: 120s per asset
3. **User Manual Abort** — Ctrl+C or UI "Cancel" button (M1+ scope)
4. **Hardware Failure** — GPU OOM, model loading failure, CUDA error
5. **Bad Prompt Detection** — All attempts score <0.30 (flag for manual review)

#### Graceful Degradation Across Tiers

| Tier | Hardware | Generation Mode | Max Attempts | Time Budget | Expected Success | Fallback Preference |
|------|----------|-----------------|--------------|-------------|------------------|---------------------|
| **1-2** | RTX 4060+, 8+ GB | SDXL Lightning NF4 | 4 | 60s | 90%+ | Shipped Art Pack |
| **3** | RTX 3060, 4-6 GB | SDXL NF4 (512×512) | 3 | 60s | 70-80% | Shipped Art Pack |
| **4** | CPU-only, <4 GB | SD 1.5 OpenVINO | 2 | 120s | 50-60% | Shipped Art Pack |
| **5** | Old CPU | **Skip generation** | 0 | 0s | 0% (default) | Shipped Art Pack |

#### Archetype Matching Logic

**For NPC Portraits:**
1. Exact match: species + class + gender → `human_fighter_male.png`
2. Partial match: species + class → `human_fighter.png`
3. Species-only: species → `human_generic.png`
4. No match: generic → `generic_npc_portrait.png`

**For Scene Backgrounds:**
1. Exact match: location_type → `tavern_interior.png`
2. Generic match: indoor/outdoor → `generic_indoor_scene.png`
3. No match: generic → `generic_scene_background.png`

**For Item Icons:**
1. Exact match: item_type + item_subtype → `weapon_sword.png`
2. Type-only: item_type → `generic_weapon.png`
3. No match: generic → `generic_item_icon.png`

---

## 4. Key Design Decisions

### 4.1 Shipped Art Pack as Primary Fallback

**Rationale:** Highest quality, immersive, manually vetted.

**Coverage:** 50-100 NPC portraits, 20-30 scenes, 10-20 items (common archetypes only).

**Trade-off:** Requires content creation (someone must curate 100+ images), but provides professional fallback experience.

**Recommendation:** Prioritize curation of most common archetypes (human fighter, elf wizard, dwarf cleric, tavern interior, dungeon corridor).

### 4.2 Placeholder-by-Default for Tier 5 (CPU-only)

**Rationale:** Very old CPUs cannot afford 8-20 sec/image generation time for 15-30 images (total: 2-10 minutes).

**Behavior:** Skip image generation entirely by default, use shipped art pack immediately.

**Opt-In Generation:** User can enable slow CPU generation via config flag (`skip_image_generation=False`).

**Trade-off:** Tier 5 users miss out on custom images by default, but gain faster prep time (<2 minutes vs 10+ minutes).

### 4.3 Bad Prompt Detection and Manual Review Queue

**Rationale:** If all attempts score <0.30, the problem is likely the prompt (contradictory, malformed, unknown concepts), not the generation model.

**Action:** Flag prompt for manual review, log to `failed_prompts.json`, escalate to fallback.

**Use Case:** DM reviews bad prompts after prep, rewrites them, re-runs prep with corrected prompts.

**Example Bad Prompt:** "A dwarf elf hybrid with transparent skin and four arms" (contradictory species, unrealistic features).

### 4.4 Idempotent Prep Re-Run with Placeholder Upgrade

**Rationale:** User may want to retry failed assets after adjusting config (increase time budget, fix bad prompts).

**Workflow:**
1. Initial prep: 15 assets, 12 succeed, 3 fail → `status="partial"`
2. User reviews failures, increases time budget
3. Re-run with `regenerate_failed_only=True` → Only attempts 3 failed assets
4. Final prep: 14 succeed, 1 fail → `status="partial"` (acceptable)

**Config Flags (M1+ scope):**
- `regenerate_failed_only: bool` — Skip successful assets, regenerate only failed
- `regenerate_placeholders: bool` — Upgrade placeholders to real assets
- `regenerate_all: bool` — Regenerate all assets (overwrite previous)

---

## 5. Integration Points

### 5.1 Prep Pipeline Integration

**Execution Flow:**
```
Prep Pipeline:
  1. Load LLM → Generate NPCs, encounters
  2. Unload LLM
  3. Load Image Gen → Generate portraits, scenes
     For each image:
       a. Generate (attempt 1)
       b. Critique (graduated: Heuristics → ImageReward → SigLIP)
       c. If FAIL: Retry with adjusted parameters (attempt 2-4)
       d. If all attempts fail: → TRIGGER FALLBACK HIERARCHY
  4. Unload Image Gen
  5. Continue with music/SFX generation
```

**Integration Point:** After all regeneration attempts exhausted, call `select_and_store_fallback(asset_descriptor, failed_attempts, config)`.

### 5.2 Critique System Integration

**Graduated Filtering (3 layers per WO-M3-IMAGE-CRITIQUE-02):**
- Layer 1 (Heuristics): CPU, <100ms — Blur, format issues
- Layer 2 (ImageReward): GPU, ~1.5s — Text-image alignment
- Layer 3 (SigLIP): GPU, ~0.5s — Identity consistency

**Failure Triggers Retry:** If any layer fails, trigger retry with adjusted parameters (per WO-RQ-IMG-010 backoff strategy).

**Fallback Triggers After Max Attempts:** If all retries fail, escalate to fallback hierarchy.

### 5.3 Asset Store Integration

**Placeholder Storage:**
```python
GeneratedAsset(
    file_path="shipped_art_pack/human_fighter_male.png",
    generation_method="placeholder",  # Marker for querying
    metadata={
        "fallback_reason": "max_attempts_exhausted",
        "fallback_type": "shipped_art_pack",
        "archetype_match": "human_fighter_male",
        "regeneration_attempts": [...]  # Failed attempts
    }
)
```

**Query Placeholders:**
```python
placeholders = [asset for asset in manifest.assets if asset.generation_method == "placeholder"]
```

**Upgrade Path:** Re-run prep with `regenerate_placeholders=True` to upgrade placeholders to real assets.

---

## 6. Schema Extensions Proposed

### 6.1 GeneratedAsset Metadata Extensions (M1+ scope)

**Existing fields (do not modify):**
- `asset_id`, `asset_type`, `semantic_key`, `file_path`, `file_format`, `content_hash`, `generation_method`, `metadata`

**Proposed new metadata fields:**
```python
metadata: {
    # NEW: Fallback-specific fields
    "fallback_reason": Optional[str],  # "max_attempts_exhausted", "timeout", etc.
    "fallback_type": Optional[str],    # "shipped_art_pack", "generic_category_placeholder", etc.
    "archetype_match": Optional[str],  # If shipped art pack: archetype matched
    "regeneration_attempts": List[RegenerationAttempt],  # Already exists
    "bad_prompt_flagged": bool,        # True if bad prompt detected
    "error_details": Optional[str]     # Exception message if hardware failure
}
```

### 6.2 PrepPipelineConfig Extensions (M1+ scope)

**Proposed new fields:**
```python
PrepPipelineConfig:
    # NEW: Image generation control
    skip_image_generation: bool = False  # If True, use placeholders immediately (Tier 5)
    time_budget_per_asset_sec: int = 60  # Time budget per asset
    max_regeneration_attempts: int = 4   # Max attempts

    # NEW: Fallback control
    fallback_preference: str = "shipped_art_pack"
    enable_solid_color_fallback: bool = True
    enable_text_only_fallback: bool = True

    # NEW: Re-run control (M1+ scope)
    regenerate_failed_only: bool = False
    regenerate_placeholders: bool = False
    regenerate_all: bool = False
```

---

## 7. Future Work (M1+ Scope)

Features deferred to M1+ Session Zero UX (documented in Section 10 of design doc):

1. **Manual Accept/Reject (User Override)**
   - Show user rejected image, allow manual override
   - Only for MINOR failures (not CRITICAL like 6-fingered hands)

2. **Custom Generation Settings (Expert Mode)**
   - Allow user to specify custom CFG, steps, negative prompts
   - Hidden behind "Advanced" option

3. **Retry Later (Session Zero UX)**
   - Allow user to manually retry failed assets in UI
   - Upload custom images to replace placeholders

---

## 8. Dependencies and References

### 8.1 Existing Infrastructure (No Modifications)

✅ **Asset Store** (`aidm/core/asset_store.py`):
- Already supports placeholder assets via `put()` and `resolve()` methods
- No modifications required

✅ **Prep Pipeline** (`aidm/core/prep_pipeline.py`):
- Sequential model loading orchestrator exists
- Integration point: After regeneration attempts exhausted

✅ **Image Critique Schemas** (`aidm/schemas/image_critique.py`):
- `RegenerationAttempt` schema already exists
- `CritiqueResult` schema already exists

✅ **Prep Pipeline Schemas** (`aidm/schemas/prep_pipeline.py`):
- `GeneratedAsset` schema exists (proposed extensions do NOT modify existing fields)
- `PrepPipelineConfig` schema exists (proposed extensions do NOT modify existing fields)

### 8.2 Related Work Orders

**Parallel WO (Sonnet-B):**
- WO-RQ-IMG-010 (Bounded Regeneration Policy) — Defines max attempts (GPU: 4, CPU: 3), backoff strategy, parameter adjustment
- **Integration:** This WO (RQ-IMG-009) picks up AFTER RQ-IMG-010 exhausts all attempts

**Previous WO (Sonnet-C):**
- WO-M3-IMAGE-CRITIQUE-02 — Graduated critique pipeline (Heuristics → ImageReward → SigLIP)
- **Integration:** Fallback triggers after all 3 layers fail across all attempts

### 8.3 Research Foundation

- [docs/research/R0_BOUNDED_REGEN_POLICY.md](../../docs/research/R0_BOUNDED_REGEN_POLICY.md) — Non-binding research (fallback hierarchy preliminary design)
- [docs/AIDM_EXECUTION_ROADMAP_V3.md](../../docs/AIDM_EXECUTION_ROADMAP_V3.md) — M3 deliverables: "No mechanical dependence on images"
- [pm_inbox/reviewed/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md](../../pm_inbox/reviewed/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md) — R1 model selections

---

## 9. Risks and Mitigations

### 9.1 Identified Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Shipped art pack coverage incomplete** | Medium | Prioritize common archetypes (human, elf, dwarf, tavern, dungeon), fall back to generic |
| **Archetype matching too strict** | Low | Three-tier matching: exact → partial → species-only → generic |
| **Users dislike placeholders** | Medium | User can manually retry or upload custom images (M1+ scope) |
| **Solid color generation fails** | Low | Fallback to text-only mode (always available) |
| **Bad prompt detection false positives** | Low | Manual review queue allows DM to correct flagged prompts |

### 9.2 Critical Assumptions

1. **Shipped art pack creation is feasible:** Assumes 100+ images can be curated/created for distribution (content work, not design work).
2. **Users accept placeholder fallback:** Assumes users prefer shipped art pack over nothing (validated by M3 principle: "No mechanical dependence on images").
3. **Pillow available for solid color generation:** Assumes Pillow library can be included in dependencies (lightweight, widely used).
4. **Tier 5 users accept placeholder-by-default:** Assumes very old CPU users prefer fast prep time over custom images.

---

## 10. Next Steps (Implementation Phase)

### 10.1 Immediate (Week 1)

1. **Create shipped art pack manifest schema**:
   - File: `aidm/assets/shipped_art_pack/manifest.json`
   - Schema: archetype metadata, license, attribution

2. **Implement fallback selection logic**:
   - File: `aidm/core/prep_pipeline.py` or new `aidm/core/image_fallback.py`
   - Function: `select_and_store_fallback(asset_descriptor, failed_attempts, config)`
   - Implements decision tree from Section 7

3. **Add error logging to PrepPipelineResult**:
   - Extend `PrepPipelineResult.errors` to include fallback error records
   - Schema matches Section 4.1

### 10.2 Short-term (Week 2)

4. **Implement solid color + text generation**:
   - File: `aidm/core/image_fallback.py`
   - Function: `generate_solid_color_placeholder(asset_descriptor)`
   - Uses Pillow to generate PNG with text overlay

5. **Implement archetype matching logic**:
   - File: `aidm/core/shipped_art_pack.py`
   - Function: `find_archetype_match(asset_metadata, manifest)`
   - Implements three-tier matching logic

6. **Add bad prompt detection**:
   - File: `aidm/core/prep_pipeline.py`
   - Function: `detect_bad_prompt(failed_attempts)`
   - Writes to `failed_prompts.json`

### 10.3 Medium-term (Week 3)

7. **Implement idempotent re-run**:
   - Extend `PrepPipelineConfig` with `regenerate_failed_only`, `regenerate_placeholders`, `regenerate_all` flags
   - Update `prep_pipeline.py` to check `generation_method="placeholder"` and skip/regenerate accordingly

8. **Write integration tests**:
   - File: `tests/test_image_fallback.py`
   - Test all 5 failure triggers
   - Test all 4 fallback strategies
   - Test archetype matching logic

### 10.4 Long-term (Week 4)

9. **Curate shipped art pack** (content work, not dev work):
   - Collect/create 50-100 NPC portraits (common archetypes)
   - Collect/create 20-30 scene backgrounds (tavern, dungeon, forest, castle)
   - Collect/create 10-20 item icons (sword, potion, scroll, treasure)
   - Verify licenses (CC0, CC-BY, MIT, etc.)
   - Create manifest.json

10. **Documentation and handoff**:
   - Update IMMERSION_HANDOFF.md with fallback system details
   - Add troubleshooting guide (shipped art pack missing, Pillow not installed)
   - Create DM guide for reviewing failed prompts

---

## 11. Comparison with R0 Research Draft

### 11.1 Alignment with R0_BOUNDED_REGEN_POLICY.md

**R0 Draft Fallback Hierarchy:**
1. Shipped Art Pack
2. User Manual Accept (Override)
3. Alternate Generation Settings (User-Defined)
4. Placeholder (Abort)

**This Design (WO-RQ-IMG-009):**
1. Shipped Art Pack (archetype-specific) ✅ **MATCHES R0**
2. Generic Category Placeholder **NEW** (added tier)
3. Solid Color + Text Overlay **NEW** (added tier)
4. Text-Only Mode ✅ **MATCHES R0 "Placeholder"**

**Key Differences:**
- **User Manual Accept** → Deferred to M1+ scope (requires Session Zero UX)
- **Alternate Generation Settings** → Deferred to M1+ scope (expert mode)
- **Generic + Solid Color tiers** → Added for graceful degradation

**Rationale:** R0 draft assumed M1+ UI features (manual accept, custom settings). This design focuses on M0 automated fallback, defers user intervention to M1+.

### 11.2 New Contributions Beyond R0 Draft

1. **Archetype matching logic** — Three-tier matching for shipped art pack (exact → partial → species-only → generic)
2. **Solid color + text generation** — Dynamically generated placeholder with asset-specific info
3. **Bad prompt detection** — Flag prompts with scores <0.30 for manual review
4. **Tier-specific behavior** — Tier 5 placeholder-by-default, opt-in generation
5. **Idempotent re-run workflow** — Regenerate failed only, upgrade placeholders
6. **Manual review queue** — `failed_prompts.json` for DM post-prep review

---

## 12. Conclusion

### 12.1 Summary

Design phase for WO-RQ-IMG-009 is **complete and ready for implementation**. Comprehensive design specification delivered to `docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md`.

**Core Achievement:** Four-tier graceful degradation system ensures game remains playable without images (M3 principle).

**Total Deliverable:** ~1,100 lines covering all 7 tasks from approved work order draft.

### 12.2 Acceptance Criteria Met

All 7 tasks from WO-RQ-IMG-009 draft are **COMPLETE**:

- [x] Placeholder strategy options defined (4 strategies)
- [x] Failure trigger conditions defined (5 triggers)
- [x] User notification design specified (3 notification types)
- [x] Persistence of failed attempts specified (error logging, idempotent re-run)
- [x] Graceful degradation across tiers defined (Tier 1-5 behavior)
- [x] Asset store integration specified (placeholder storage, upgrade path)
- [x] Fallback hierarchy decision tree documented (archetype matching, 4 example walkthroughs)

### 12.3 Ready for PM Approval

**Status:** Awaiting PM approval to proceed to **Implementation Phase**.

**Estimated Implementation Time:** 3-4 weeks (per Next Steps section)

**Dependencies:** WO-RQ-IMG-010 (Bounded Regeneration Policy) — must define max attempts before fallback can trigger

**Risk Level:** Low (all technologies proven, no blocking dependencies)

---

**END OF COMPLETION REPORT**

**Agent:** Sonnet-C
**Date:** 2026-02-11
**Deliverable:** Design specification (~1,100 lines)
**Status:** ✅ Design Phase Complete

# Work Order: WO-RQ-IMG-009 — Image Generation Failure Fallback Design

**Work Order ID:** WO-RQ-IMG-009
**Agent:** TBD (Agent B recommended)
**Milestone:** R0 Critical Research
**Priority:** 2 (Critical Path)
**Status:** DRAFT
**Research Question:** RQ-IMG-009 — Image Generation Failure Fallback
**Deliverable Type:** Design Documentation

---

## Objective

Design the fallback strategy for image generation failures after all regeneration attempts are exhausted during prep time. This WO defines placeholder strategies, failure triggers, user notification, persistence of failed attempts, graceful degradation across hardware tiers, and integration with asset storage.

**Core Questions:**
- What does the user see when image generation fails? (Placeholder strategies: text description, solid color, generic category image, text-only mode)
- When is fallback triggered? (After max regeneration attempts, after timeout, user abort)
- How is the user notified of generation failure? Can they manually retry later?
- Are failed attempts logged? Can prep be re-run for just failed assets?
- How does graceful degradation work across tiers? (Baseline tier with no GPU always uses placeholders — same system?)
- How are placeholders stored in asset store? (Marked differently from real assets?)

---

## Background

### Existing Infrastructure

**Asset Storage:**
- [aidm/core/asset_store.py](../aidm/core/asset_store.py) — Asset storage system (supports placeholder assets)
- [aidm/schemas/prep_pipeline.py](../aidm/schemas/prep_pipeline.py) — GeneratedAsset schema (asset_id, asset_type, file_path, content_hash, generation_method, metadata)

**Prep Pipeline:**
- [aidm/core/prep_pipeline.py](../aidm/core/prep_pipeline.py) — Sequential model loading orchestrator (LLM → Image Gen → Music Gen → SFX Gen)
- [aidm/schemas/prep_pipeline.py](../aidm/schemas/prep_pipeline.py) — PrepPipelineConfig, PrepPipelineResult (status: success/failed/partial, errors, warnings)

**Image Critique:**
- [aidm/schemas/image_critique.py](../aidm/schemas/image_critique.py) — RegenerationAttempt schema (tracks regeneration history)
- [docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md](../docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md) — Three-layer graduated filtering

**Research Foundation:**
- [docs/research/R0_BOUNDED_REGEN_POLICY.md](../docs/research/R0_BOUNDED_REGEN_POLICY.md) — Non-binding research draft on regeneration policy (includes fallback hierarchy: shipped art pack → user manual accept → placeholder)
- [docs/AIDM_EXECUTION_ROADMAP_V3.md](../docs/AIDM_EXECUTION_ROADMAP_V3.md) M3 deliverables — "No mechanical dependence on images" (game playable without images)

**Hardware Tiers:**
- Tier 1-2 (GPU, ≥2 GB VRAM): Full image generation
- Tier 3 (GPU, 1-2 GB VRAM): Limited image generation (lower quality/resolution)
- Tier 4-5 (CPU-only): Placeholder mode by default (image generation optional, slow)

---

## Scope

### IN SCOPE

1. **Placeholder Strategy Design**
   - Text description placeholder (e.g., "A tall half-orc warrior with a battle axe")
   - Solid color with text overlay (asset type label + description)
   - Generic category placeholder (one fallback image per asset type: NPC, scene, item)
   - Text-only mode (no image displayed, description only)
   - Shipped art pack (manually vetted fallback images for common archetypes)

2. **Failure Trigger Definition**
   - After max regeneration attempts exhausted (per RQ-IMG-010 policy)
   - After time budget exceeded (60s GPU, 120s CPU per RQ-IMG-010)
   - User manual abort (Session Zero UX, M1+ scope but design should accommodate)
   - Hardware failure (GPU OOM, model loading failure)

3. **User Notification Design**
   - How is user notified of generation failure? (Prep log entry, UI notification, prep summary report)
   - What information is shown? (Asset ID, asset type, failure reason, attempted retries)
   - Can user manually retry later? (M1+ Session Zero UX, but design should accommodate)

4. **Persistence of Failed Attempts**
   - Are failed attempts logged? (Yes, in PrepPipelineResult.errors)
   - Can prep be re-run for just failed assets? (Idempotent prep with partial re-run)
   - Is regeneration history saved? (Yes, RegenerationAttempt list in asset metadata)

5. **Graceful Degradation Across Tiers**
   - Tier 1-2 (GPU): Attempt generation, fallback on failure
   - Tier 3 (GPU, limited): Attempt generation with lower quality, fallback on failure
   - Tier 4-5 (CPU): Use placeholders by default (skip generation), allow opt-in generation
   - Consistent placeholder system across all tiers

6. **Asset Store Integration**
   - How are placeholders stored? (Same GeneratedAsset schema, marked with generation_method="placeholder")
   - Are placeholders marked differently? (Yes, metadata includes fallback_reason field)
   - Can placeholders be upgraded later? (Yes, prep re-run with updated config)

### OUT OF SCOPE

1. **Implementation**: This is design documentation only. No code changes to `asset_store.py` or `prep_pipeline.py`.
2. **Regeneration Policy**: Max attempts, backoff strategy covered by RQ-IMG-010 (separate WO).
3. **User Intervention**: Manual accept/reject, Session Zero retry UI is M1+ scope.
4. **Shipped Art Pack Creation**: Manually creating fallback art assets is content work, not design work.
5. **Text-to-Image Prompt Improvement**: Improving prompts to reduce failure rate is separate optimization work.

---

## Tasks

### Task 1: Define Placeholder Strategy Options

**Action:** Design four placeholder strategies with trade-offs analysis.

**Subtasks:**
1. **Text Description Placeholder**:
   - **Description**: Show text description only, no image displayed
   - **Format**: Plain text (e.g., "A tall half-orc warrior with a battle axe")
   - **Pros**: Zero compute cost, always available, works on all hardware tiers
   - **Cons**: Least immersive, requires user to imagine visuals
   - **Use Case**: Tier 4-5 (CPU-only) default mode

2. **Solid Color with Text Overlay**:
   - **Description**: Display solid color background (asset-type specific) with text overlay
   - **Format**: PNG image (512×512 or 256×256) with centered text (asset name + description)
   - **Color Scheme**: NPC portraits (blue), scenes (green), items (purple)
   - **Pros**: Visual consistency, low compute cost, professional appearance
   - **Cons**: Generic, not specific to individual asset
   - **Use Case**: Tier 3 fallback, Tier 4-5 opt-in mode

3. **Generic Category Placeholder**:
   - **Description**: Use one fallback image per asset type (shipped with AIDM)
   - **Format**: Manually vetted PNG images (e.g., "generic_npc_portrait.png", "generic_dungeon_scene.png")
   - **Examples**: Generic knight portrait (for failed NPC portraits), generic tavern scene (for failed scenes)
   - **Pros**: More immersive than text-only, professional artwork
   - **Cons**: Not specific to individual asset, requires shipped art pack
   - **Use Case**: Tier 1-5 fallback (best placeholder option)

4. **Shipped Art Pack (Archetype-Specific)**:
   - **Description**: Use manually vetted fallback images for common archetypes
   - **Format**: Shipped PNG images for common NPC types (fighter, wizard, rogue), common scenes (tavern, dungeon, forest)
   - **Examples**: "fighter_male_human.png", "tavern_interior.png"
   - **Pros**: High quality, archetype-specific, immersive
   - **Cons**: Requires content creation, limited coverage (only common archetypes)
   - **Use Case**: Tier 1-5 first fallback (before generic category placeholder)

**Output:**
- `PLACEHOLDER_STRATEGIES.md` section with all four strategies
- Trade-offs table (compute cost, immersion, coverage)
- Recommended hierarchy: Shipped Art Pack (archetype match) → Generic Category Placeholder → Solid Color + Text → Text-Only

---

### Task 2: Define Failure Trigger Conditions

**Action:** Specify when fallback is triggered (criteria for giving up on generation).

**Subtasks:**
1. **Max Regeneration Attempts Exhausted**:
   - Trigger: After N retries fail critique (N defined by RQ-IMG-010: GPU 3 retries, CPU 2 retries)
   - Condition: All attempts scored below acceptable threshold (critique score <0.70)
   - Action: Escalate to fallback hierarchy

2. **Time Budget Exceeded**:
   - Trigger: After time budget per asset exceeded (60s GPU, 120s CPU per RQ-IMG-010)
   - Condition: Generation + critique time exceeds budget
   - Action: Terminate regeneration, escalate to fallback

3. **User Manual Abort** (M1+ Session Zero UX):
   - Trigger: User clicks "Cancel" or sends interrupt signal (Ctrl+C)
   - Condition: User intervention during prep
   - Action: Terminate regeneration immediately, escalate to fallback
   - Note: Design should accommodate future abort feature

4. **Hardware Failure**:
   - Trigger: GPU OOM error, model loading failure, CUDA error
   - Condition: Exception during model loading or generation
   - Action: Log error, escalate to fallback (CPU mode if available, else placeholder)

5. **Bad Prompt Detection**:
   - Trigger: Critique score <0.30 across all attempts (suggests prompt issue, not generation issue)
   - Condition: All retries fail with very low scores
   - Action: Flag prompt as problematic, escalate to fallback, log for review

**Output:**
- `FAILURE_TRIGGERS.md` section with all five trigger conditions
- Trigger detection logic for each condition
- Recommended action per trigger

---

### Task 3: Define User Notification Design

**Action:** Specify how users are notified of generation failures and what information is shown.

**Subtasks:**
1. **Prep Log Entry**:
   - Format: Text log entry in prep execution log (PrepPipelineResult.execution_log)
   - Content: "[WARN] Image generation failed for asset {asset_id} ({asset_type}) after {N} attempts. Using fallback: {fallback_type}"
   - Example: "[WARN] Image generation failed for asset npc_portrait_001 (npc_portrait) after 4 attempts. Using fallback: generic_category_placeholder"

2. **Prep Summary Report**:
   - Format: Markdown summary at end of prep (PrepPipelineResult.warnings)
   - Content: List of failed assets with failure reasons, fallback used, regeneration attempts
   - Example:
     ```
     ## Image Generation Failures (3 assets)
     - npc_portrait_001: Failed after 4 attempts (artifacting), fallback: shipped_art_pack
     - scene_background_002: Failed after 3 attempts (timeout), fallback: generic_category_placeholder
     - item_icon_003: Failed after 4 attempts (bad prompt), fallback: solid_color_text
     ```

3. **UI Notification (M1+ Session Zero UX)**:
   - Format: In-app notification during prep (toast, modal, progress bar annotation)
   - Content: "Image generation failed for {asset_type}. Using placeholder."
   - User Action: Option to retry later (M1+ scope)

4. **Information Shown**:
   - Asset ID, asset type (NPC portrait, scene background, etc.)
   - Failure reason (max attempts, timeout, hardware failure, bad prompt)
   - Number of regeneration attempts made
   - Fallback strategy used (shipped art pack, generic placeholder, text-only)
   - Option to retry later (M1+ scope)

**Output:**
- `USER_NOTIFICATION.md` section with notification design
- Example log entry, summary report, UI notification (future)
- Information fields for each notification type

---

### Task 4: Define Persistence of Failed Attempts

**Action:** Specify how failed attempts are logged and whether prep can be re-run for failed assets only.

**Subtasks:**
1. **Failed Attempt Logging**:
   - Log in PrepPipelineResult.errors (list of error records)
   - Error record format: `{"asset_id": str, "asset_type": str, "failure_reason": str, "attempts": int, "fallback_used": str}`
   - Regeneration history saved in GeneratedAsset.metadata (list of RegenerationAttempt objects)

2. **Idempotent Prep Re-Run**:
   - Prep pipeline is idempotent (can be re-run safely)
   - Failed assets can be re-generated on re-run (skip successful assets)
   - PrepPipelineConfig includes `regenerate_failed_only: bool` flag (M1+ feature, design should accommodate)

3. **Partial Prep Status**:
   - PrepPipelineResult.status can be "partial" (some assets succeeded, some failed)
   - User can inspect failures, adjust config (increase time budget, switch to shipped art pack), re-run prep
   - Example workflow:
     1. Initial prep: 15 assets, 12 succeed, 3 fail → status="partial"
     2. User reviews failures, increases time budget to 90s CPU
     3. Re-run prep with `regenerate_failed_only=True` → 3 assets re-attempted
     4. Final prep: 14 succeed, 1 fail → status="partial" (acceptable)

4. **Regeneration History Persistence**:
   - Each GeneratedAsset includes `regeneration_attempts: List[RegenerationAttempt]` in metadata
   - Allows post-mortem analysis (which parameters worked, which failed)
   - Useful for debugging bad prompts, model issues

**Output:**
- `PERSISTENCE.md` section with logging and re-run design
- Error record schema
- Idempotent re-run workflow example
- Regeneration history persistence specification

---

### Task 5: Define Graceful Degradation Across Tiers

**Action:** Specify how placeholder system works consistently across all hardware tiers.

**Subtasks:**
1. **Tier 1-2 (GPU, ≥2 GB VRAM)**:
   - Mode: Full image generation (SDXL Lightning NF4, 4-6 sec/image)
   - Fallback: On failure → shipped art pack (archetype match) → generic category placeholder → solid color + text
   - Expectation: 90%+ success rate (most images generated successfully)

2. **Tier 3 (GPU, 1-2 GB VRAM)**:
   - Mode: Limited image generation (SD 1.5 + LCM LoRA, lower resolution 512×512 instead of 768×768)
   - Fallback: On failure → shipped art pack → generic category placeholder → solid color + text
   - Expectation: 70-80% success rate (lower quality model, more failures)

3. **Tier 4-5 (CPU-only)**:
   - Mode: Placeholder by default (skip image generation to save time)
   - Fallback: Shipped art pack (archetype match) → generic category placeholder → solid color + text
   - Opt-in generation: User can enable slow CPU generation (SD 1.5 OpenVINO, 8-20 sec/image) via PrepPipelineConfig flag
   - Expectation: 0% generation by default (all placeholders), 50-60% success rate if opt-in enabled

4. **Consistent Placeholder System**:
   - Same placeholder hierarchy across all tiers (shipped art pack → generic → solid color → text)
   - Same GeneratedAsset schema (generation_method="placeholder", metadata.fallback_reason)
   - Same asset storage format (PNG images for solid color, text files for text-only)

**Output:**
- `TIER_DEGRADATION.md` section with tier-specific behavior
- Mode and fallback hierarchy per tier
- Success rate expectations per tier
- Opt-in generation flag for CPU-only tiers

---

### Task 6: Define Asset Store Integration

**Action:** Specify how placeholders are stored in asset store and marked differently from real assets.

**Subtasks:**
1. **Placeholder Storage Format**:
   - Stored as GeneratedAsset objects (same schema as real assets)
   - File path points to placeholder image file (shipped art pack, generic placeholder, or solid color PNG)
   - Content hash computed from placeholder file (allows deduplication)

2. **Generation Method Marking**:
   - Real assets: `generation_method="sdxl_lightning_nf4"` (or other model name)
   - Placeholders: `generation_method="placeholder"` (special marker)
   - Allows asset store to distinguish real vs placeholder assets

3. **Fallback Reason Metadata**:
   - Real assets: `metadata.fallback_reason=None`
   - Placeholders: `metadata.fallback_reason="max_attempts_exhausted"` (or "timeout", "hardware_failure", "bad_prompt")
   - Allows post-mortem analysis of why placeholder was used

4. **Regeneration Attempts Metadata**:
   - Real assets: `metadata.regeneration_attempts=[...]` (may be empty if first attempt succeeded)
   - Placeholders: `metadata.regeneration_attempts=[...]` (list of failed attempts with critique results)
   - Allows debugging (which parameters were tried, which critique scores resulted)

5. **Placeholder Upgrade Path**:
   - Placeholders can be upgraded to real assets on prep re-run
   - Asset store checks `generation_method="placeholder"` to identify upgrade candidates
   - PrepPipelineConfig includes `regenerate_placeholders: bool` flag (M1+ feature)

**Output:**
- `ASSET_STORE_INTEGRATION.md` section with storage format
- GeneratedAsset schema extensions (generation_method, fallback_reason, regeneration_attempts)
- Placeholder upgrade workflow

---

### Task 7: Define Fallback Hierarchy Decision Tree

**Action:** Create a decision tree showing fallback hierarchy: shipped art pack → generic → solid color → text.

**Subtasks:**
1. **Decision Tree Logic**:
   - Step 1: Check if shipped art pack has archetype match (e.g., "fighter_male_human.png" for NPC fighter)
     - YES → Use shipped art pack
     - NO → Go to Step 2
   - Step 2: Check if generic category placeholder exists (e.g., "generic_npc_portrait.png")
     - YES → Use generic category placeholder
     - NO → Go to Step 3
   - Step 3: Check if solid color + text generation available (requires image generation disabled, but text rendering available)
     - YES → Generate solid color PNG with text overlay
     - NO → Go to Step 4
   - Step 4: Fall back to text-only mode (no image, description only)

2. **Archetype Matching Logic**:
   - Extract archetype from asset metadata (species, class, gender for NPCs; location type for scenes)
   - Check shipped art pack manifest for matching archetype
   - Example: NPC (species=human, class=fighter, gender=male) → Check for "fighter_male_human.png"
   - Fallback to species-only match if class+species combo not found (e.g., "human_male.png")

3. **Example Decision Tree**:
   ```
   Asset: npc_portrait_001 (species=human, class=fighter, gender=male)
   → Check shipped art pack for "fighter_male_human.png" → FOUND → Use shipped art pack
   → Asset stored with generation_method="placeholder", fallback_reason="max_attempts_exhausted", file_path="shipped_art_pack/fighter_male_human.png"
   ```

**Output:**
- `FALLBACK_HIERARCHY.md` section with decision tree
- Archetype matching logic
- Example decision tree walkthroughs for NPC, scene, item assets

---

## Deliverables

1. **Design Document:** `docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md` (150-250 lines)
   - Placeholder strategy options (text-only, solid color, generic, shipped art pack)
   - Failure trigger conditions (max attempts, timeout, user abort, hardware failure, bad prompt)
   - User notification design (log entry, summary report, UI notification)
   - Persistence of failed attempts (error logging, idempotent re-run, regeneration history)
   - Graceful degradation across tiers (Tier 1-5 behavior, consistent placeholder system)
   - Asset store integration (placeholder storage, generation method marking, upgrade path)
   - Fallback hierarchy decision tree (shipped art pack → generic → solid color → text)

2. **Fallback Hierarchy Decision Tree:** Visual flowchart showing fallback selection logic
   - Step 1: Shipped art pack (archetype match)
   - Step 2: Generic category placeholder
   - Step 3: Solid color + text
   - Step 4: Text-only

3. **Integration Notes:** Reference existing schema fields and prep pipeline config
   - GeneratedAsset schema extensions (generation_method, fallback_reason, regeneration_attempts)
   - PrepPipelineConfig extensions (regenerate_failed_only, regenerate_placeholders)

---

## Acceptance Criteria

1. ✅ **Design document complete** with all seven task sections (strategies, triggers, notification, persistence, tiers, asset store, hierarchy)
2. ✅ **Fallback hierarchy decision tree** showing shipped art pack → generic → solid color → text progression
3. ✅ **User notification design** with log entry, summary report, and future UI notification examples
4. ✅ **Tier-specific behavior** defined for Tiers 1-5 (GPU full, GPU limited, CPU placeholder-by-default)
5. ✅ **Asset store integration** shows how placeholders are marked differently (generation_method="placeholder", fallback_reason metadata)
6. ✅ **Integration notes** reference GeneratedAsset schema extensions and PrepPipelineConfig flags

---

## Dependencies

**Depends On:**
- RQ-IMG-010 (Bounded Regeneration Policy) — Fallback triggered after max attempts exhausted (defined by RQ-IMG-010)
- WO-M3-PREP-01 (Prep Pipeline Prototype) — COMPLETE (idempotent execution, partial status support)
- Asset store implementation (aidm/core/asset_store.py) — EXISTS (supports placeholder assets)

**Blocks:**
- WO-M3-PREP-CRITIQUE-INTEGRATION (implementation) — Cannot implement fallback without policy definition
- M1+ Session Zero UX — User retry, manual accept/reject depends on fallback strategy design

**Related:**
- R0_BOUNDED_REGEN_POLICY.md (non-binding research) — Includes preliminary fallback hierarchy
- AIDM_EXECUTION_ROADMAP_V3.md M3 deliverables — "No mechanical dependence on images"

---

## Stop Conditions

**STOP and report if:**
1. **Existing design found**: A complete failure fallback strategy already exists in `docs/design/` or `pm_inbox/reviewed/`
2. **Asset store changed**: Asset storage contracts are revised in a way that conflicts with placeholder design
3. **Scope overlap**: Another WO overlaps significantly with this work (e.g., prep pipeline integration already includes fallback strategy)
4. **Shipped art pack scope**: If shipped art pack creation is in scope (content work), flag as out of scope for design WO

---

## Notes for Agent

**Recommended Agent:** Agent B (Image & Asset Generation Architect)

**Key Considerations:**
- This is a **design WO**, not an implementation WO. Output is documentation, not code.
- Focus on **graceful degradation** (AIDM playable without images, per M3 deliverables).
- Prioritize **shipped art pack** as first fallback (highest quality, manually vetted).
- Use R0_BOUNDED_REGEN_POLICY.md fallback hierarchy as research foundation, but make binding design decisions.
- Reference GeneratedAsset schema to ensure fallback design aligns with existing contracts.

**Estimated Effort:** 3-5 hours (review existing research, draft design document, create fallback decision tree)

---

**END OF WORK ORDER DRAFT**

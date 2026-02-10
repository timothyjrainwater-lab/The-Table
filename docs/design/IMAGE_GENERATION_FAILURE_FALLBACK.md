# Image Generation Failure Fallback Design

**Work Order:** WO-RQ-IMG-009
**Agent:** Sonnet-C
**Date:** 2026-02-11
**Status:** Design Specification
**Authority:** NON-BINDING until formal approval

---

## Executive Summary

This document defines the fallback strategy for image generation failures after all regeneration attempts are exhausted during prep time. The game must remain **playable without images** (M3 principle), so fallback is graceful degradation, not a blocking error.

**Core Strategy:** Four-tier fallback hierarchy prioritizing shipped art pack → generic category placeholder → solid color + text → text-only mode.

**Key Principle:** "No mechanical dependence on images." Images are atmospheric only. Players can complete sessions with placeholders.

---

## 1. Placeholder Strategy Options

Four placeholder strategies, ordered by quality and immersion level.

### 1.1 Shipped Art Pack (Archetype-Specific)

**Description:** Manually vetted fallback images for common archetypes (fighter, wizard, tavern, dungeon).

**Format:** PNG images (512×512 or 768×768) shipped with AIDM distribution.

**Coverage:**
- **NPC Portraits:** 50-100 images covering common D&D archetypes (human fighter, elf wizard, dwarf cleric, etc.)
- **Scenes:** 20-30 generic locations (tavern interior, dungeon corridor, forest clearing, castle throne room)
- **Items:** 10-20 generic item icons (sword, potion, scroll, treasure chest)

**Archetype Matching Logic:**
- Extract metadata from failed asset: species, class, gender (for NPCs); location type (for scenes)
- Check shipped art pack manifest for best match
- Fallback hierarchy: exact match (species+class+gender) → partial match (species+class) → species-only match → generic category

**Example Matches:**
- `npc_portrait_001` (species=human, class=fighter, gender=male) → `shipped_art_pack/human_fighter_male.png`
- `scene_background_002` (location_type=tavern) → `shipped_art_pack/tavern_interior_01.png`
- `item_icon_003` (item_type=weapon, subtype=sword) → `shipped_art_pack/generic_sword.png`

**Pros:**
- High quality (professionally created or manually vetted)
- Immersive (archetype-specific)
- Always available (shipped with distribution, no generation required)

**Cons:**
- Limited coverage (only common archetypes)
- Not specific to individual asset (multiple NPCs may share same portrait)
- Requires content creation (someone must create/curate 100+ images)

**Use Case:** First fallback choice for Tier 1-5 (all hardware tiers).

### 1.2 Generic Category Placeholder

**Description:** Single fallback image per asset type (NPC, scene, item).

**Format:** PNG images (512×512) with generic visual for category.

**Examples:**
- `generic_npc_portrait.png` — Silhouette of humanoid figure
- `generic_scene_background.png` — Abstract fantasy landscape
- `generic_item_icon.png` — Question mark icon

**Pros:**
- Always available (3 images total, minimal distribution size)
- Professional appearance (designed placeholder, not ad-hoc)
- Low compute cost (no generation required)

**Cons:**
- Generic (no archetype specificity)
- Least immersive (all NPCs use same placeholder)
- Requires manual creation (design 3 placeholder images)

**Use Case:** Second fallback choice when shipped art pack has no archetype match.

### 1.3 Solid Color with Text Overlay

**Description:** Dynamically generated solid color background with asset name and description overlaid.

**Format:** PNG image (512×512 or 256×256) generated at fallback time using PIL/Pillow.

**Color Scheme by Asset Type:**
- NPC portraits: Blue background (#4A90E2)
- Scenes: Green background (#7ED321)
- Items: Purple background (#BD10E0)

**Text Overlay:**
- Line 1: Asset type (centered, bold, 24pt)
- Line 2: Asset name (centered, regular, 18pt)
- Line 3: Description snippet (centered, italic, 14pt, truncated to 80 chars)

**Example:**
```
[Blue background]
NPC PORTRAIT
Thorin Ironforge
"A grizzled dwarf cleric with a red beard..."
```

**Pros:**
- Asset-specific (shows name and description)
- Low compute cost (~50ms generation using Pillow)
- Professional appearance (better than blank image)

**Cons:**
- Not immersive (clearly a placeholder)
- Requires text rendering library (Pillow + TrueType font)

**Use Case:** Third fallback choice when generic category placeholder unavailable or tier downgrade needed.

### 1.4 Text-Only Mode (No Image)

**Description:** No image displayed, only text description shown in UI.

**Format:** No image file created. UI shows description text in placeholder area.

**UI Behavior:**
- Image slot shows text block instead of image
- Text includes asset type, name, and full description
- Optional: Icon glyph to indicate "no image available"

**Example UI:**
```
┌────────────────────────────┐
│ [📷] NO IMAGE AVAILABLE    │
│                            │
│ Thorin Ironforge           │
│ Dwarf Cleric               │
│                            │
│ A grizzled dwarf cleric    │
│ with a red beard and       │
│ battle-worn armor...       │
└────────────────────────────┘
```

**Pros:**
- Zero compute cost
- Always available (no dependencies)
- Works on all hardware tiers

**Cons:**
- Least immersive (no visual at all)
- Requires UI to handle "no image" case gracefully

**Use Case:** Last resort fallback (Tier 5 CPU-only with no image rendering support, or all other fallbacks failed).

### 1.5 Comparison Table

| Strategy | Immersion | Specificity | Compute Cost | Distribution Size | Always Available? |
|----------|-----------|-------------|--------------|-------------------|-------------------|
| **Shipped Art Pack** | High | Archetype-level | 0 | ~50-200 MB | Yes (if archetype exists) |
| **Generic Category** | Low | Type-level | 0 | <1 MB | Yes |
| **Solid Color + Text** | Low | Asset-level | ~50ms | 0 (generated) | Yes (requires Pillow) |
| **Text-Only** | Very Low | Asset-level | 0 | 0 | Yes |

---

## 2. Failure Trigger Conditions

When to give up on image generation and escalate to fallback.

### 2.1 Max Regeneration Attempts Exhausted

**Trigger:** All retry attempts failed critique (per WO-RQ-IMG-010 policy).

**Hardware-Specific Limits:**
- **GPU (Tier 1-3):** 4 attempts (1 original + 3 retries)
- **CPU (Tier 4-5):** 2-3 attempts (1 original + 1-2 retries, based on time budget)

**Condition:** After final attempt, critique result still shows `passed=False`.

**Action:** Escalate to fallback hierarchy (see Section 7).

**Example Log:**
```
[WARN] Image generation failed for asset npc_portrait_001 after 4 attempts.
       Attempt 1: FAIL (blur detected, score=0.55)
       Attempt 2: FAIL (composition poor, score=0.62)
       Attempt 3: FAIL (artifacting, score=0.68)
       Attempt 4: FAIL (blur detected, score=0.69)
       → Escalating to fallback hierarchy.
```

### 2.2 Time Budget Exceeded

**Trigger:** Total generation + critique time exceeds per-asset budget (per WO-RQ-IMG-010).

**Time Budgets:**
- **GPU:** 60 seconds per asset
- **CPU:** 120 seconds per asset

**Condition:** `total_time_ms > time_budget_ms` after any attempt.

**Action:** Terminate remaining attempts immediately, escalate to fallback.

**Example Log:**
```
[WARN] Time budget exceeded for asset scene_background_002 (62.3s > 60s).
       Completed 3 of 4 attempts.
       → Escalating to fallback hierarchy.
```

**Rationale:** Prep time budget is ~30 minutes for full campaign. Cannot allow indefinite generation time per asset.

### 2.3 User Manual Abort (M1+ Session Zero UX)

**Trigger:** User sends interrupt signal (Ctrl+C, UI "Cancel" button).

**Condition:** User interaction during generation.

**Action:** Terminate current generation immediately, escalate to fallback.

**Example Log:**
```
[INFO] User manually aborted generation for asset item_icon_003.
       → Escalating to fallback hierarchy.
```

**Design Accommodation:** System must support graceful shutdown:
- Cancel pending model inference (if possible)
- Clean up temp files
- Mark asset as "user_aborted" in metadata
- Allow re-run on next prep execution

### 2.4 Hardware Failure

**Trigger:** GPU OOM error, model loading failure, CUDA error, disk full.

**Condition:** Exception during model loading or inference.

**Action:** Log error, attempt CPU fallback (if available), else escalate to placeholder.

**Example Errors:**
- `torch.cuda.OutOfMemoryError` — GPU VRAM exhausted
- `RuntimeError: CUDA out of memory` — GPU VRAM exhausted during generation
- `FileNotFoundError: Model weights not found` — Model loading failure
- `OSError: [Errno 28] No space left on device` — Disk full

**Action Tree:**
```
GPU OOM detected
  ↓
CPU available?
  YES → Degrade to CPU generation (SD 1.5 OpenVINO)
  NO → Escalate to fallback (shipped art pack or placeholder)
```

**Example Log:**
```
[ERROR] GPU OOM during generation for asset npc_portrait_001.
        VRAM peak: 6.8 GB (exceeded 6.0 GB limit).
        → Attempting CPU fallback with SD 1.5 OpenVINO...
        [SUCCESS] CPU generation completed in 18.2s.
```

### 2.5 Bad Prompt Detection

**Trigger:** Critique score consistently very low (<0.30) across all attempts.

**Condition:** All attempts score below minimum viable threshold, suggesting prompt issue (not generation issue).

**Action:** Flag prompt as problematic, escalate to fallback, log for manual review.

**Rationale:** If first attempt scores 0.25 and all retries also score 0.25-0.30, the problem is likely the prompt itself (e.g., contradictory descriptions, unknown concepts).

**Example Log:**
```
[WARN] Bad prompt detected for asset npc_portrait_001.
       All 4 attempts scored <0.30 (average: 0.28).
       Prompt: "A dwarf elf hybrid with transparent skin and four arms"
       → Flagged for manual review. Escalating to fallback.
```

**Manual Review Queue:** Store bad prompts in `failed_prompts.json` for post-prep review.

---

## 3. User Notification Design

How users are informed of generation failures.

### 3.1 Prep Execution Log (Real-Time)

**Format:** Text log entries during prep pipeline execution (`PrepPipelineResult.execution_log`).

**Content:**
```
[WARN] Image generation failed for asset {asset_id} ({asset_type}) after {N} attempts. Using fallback: {fallback_type}
```

**Example:**
```
[INFO] Generating npc_portrait_001 (Thorin Ironforge)...
[INFO]   Attempt 1: FAIL (blur detected, score=0.55)
[INFO]   Attempt 2: FAIL (composition poor, score=0.62)
[INFO]   Attempt 3: FAIL (artifacting, score=0.68)
[INFO]   Attempt 4: FAIL (blur detected, score=0.69)
[WARN] Image generation failed for asset npc_portrait_001 (npc_portrait) after 4 attempts. Using fallback: shipped_art_pack
[INFO]   → Using shipped art pack: human_fighter_male.png
```

### 3.2 Prep Summary Report (End of Prep)

**Format:** Markdown summary in `PrepPipelineResult.warnings`.

**Content:** List of all failed assets with failure reasons, fallback used, regeneration attempts.

**Example:**
```markdown
## Image Generation Failures (3 assets)

### Failed Assets
- **npc_portrait_001** (Thorin Ironforge): Failed after 4 attempts (blur detected)
  - Fallback: shipped_art_pack (human_fighter_male.png)
  - Total time: 24.3s
- **scene_background_002** (Tavern Interior): Failed after 3 attempts (time budget exceeded)
  - Fallback: generic_category_placeholder
  - Total time: 62.1s
- **item_icon_003** (Magic Sword): Failed after 4 attempts (bad prompt suspected)
  - Fallback: solid_color_text
  - Total time: 18.7s
  - **ACTION REQUIRED:** Prompt flagged for manual review

### Summary
- Total assets: 15
- Successful: 12 (80%)
- Failed: 3 (20%)
- Fallback usage: 2 shipped art pack, 1 generic, 1 solid color
```

### 3.3 UI Notification (M1+ Session Zero UX)

**Format:** In-app notification during prep (toast, modal, progress bar annotation).

**Content:**
- Notification type: Warning (not error)
- Message: "Image generation failed for {asset_type}. Using placeholder."
- Action: Option to retry later (M1+ scope)

**Example UI:**
```
┌────────────────────────────────────────┐
│ ⚠️  Image Generation Warning           │
│                                        │
│ Failed to generate portrait for        │
│ Thorin Ironforge after 4 attempts.     │
│                                        │
│ Using shipped art pack as placeholder. │
│                                        │
│ [View Details] [Retry Later] [OK]     │
└────────────────────────────────────────┘
```

**M1+ Retry Later:** Allow user to manually retry failed assets in Session Zero UI.

### 3.4 Information Fields

**For each failure notification, include:**
- **Asset ID:** Unique identifier (e.g., `npc_portrait_001`)
- **Asset Type:** Category (npc_portrait, scene_background, item_icon)
- **Asset Name:** Human-readable name (e.g., "Thorin Ironforge")
- **Failure Reason:** Why generation failed (max attempts, timeout, hardware failure, bad prompt)
- **Attempts Made:** Number of regeneration attempts (e.g., "4 attempts")
- **Fallback Used:** Which fallback strategy was selected (shipped_art_pack, generic_category_placeholder, solid_color_text, text_only)
- **Total Time:** Time spent on generation + critique (e.g., "24.3s")
- **Manual Review Flag:** If bad prompt detected, flag for review

---

## 4. Persistence of Failed Attempts

How failed attempts are logged and whether prep can be re-run for failed assets.

### 4.1 Failed Attempt Logging

**Storage Location:** `PrepPipelineResult.errors` (list of error records).

**Error Record Schema:**
```python
{
    "asset_id": str,                  # e.g., "npc_portrait_001"
    "asset_type": str,                # e.g., "npc_portrait"
    "asset_name": str,                # e.g., "Thorin Ironforge"
    "failure_reason": str,            # e.g., "max_attempts_exhausted"
    "attempts": int,                  # e.g., 4
    "fallback_used": str,             # e.g., "shipped_art_pack"
    "total_time_ms": int,             # e.g., 24300
    "bad_prompt_flagged": bool,       # True if bad prompt detected
    "error_details": Optional[str]    # Exception message if hardware failure
}
```

**Example:**
```python
{
    "asset_id": "npc_portrait_001",
    "asset_type": "npc_portrait",
    "asset_name": "Thorin Ironforge",
    "failure_reason": "max_attempts_exhausted",
    "attempts": 4,
    "fallback_used": "shipped_art_pack",
    "total_time_ms": 24300,
    "bad_prompt_flagged": False,
    "error_details": None
}
```

### 4.2 Regeneration History Persistence

**Storage Location:** `GeneratedAsset.metadata["regeneration_attempts"]` (list of `RegenerationAttempt` objects).

**Schema:** See `aidm/schemas/image_critique.py` — `RegenerationAttempt` already defined.

**Example:**
```python
{
    "asset_id": "npc_portrait_001",
    "metadata": {
        "regeneration_attempts": [
            {
                "attempt_number": 1,
                "cfg_scale": 7.5,
                "sampling_steps": 50,
                "creativity": 0.8,
                "negative_prompt": "",
                "critique_result": {"passed": False, "overall_score": 0.55, ...},
                "generation_time_ms": 5800
            },
            {
                "attempt_number": 2,
                "cfg_scale": 9.0,
                "sampling_steps": 60,
                "creativity": 0.7,
                "negative_prompt": "blurry, low detail",
                "critique_result": {"passed": False, "overall_score": 0.62, ...},
                "generation_time_ms": 6200
            },
            # ... attempts 3 and 4
        ]
    }
}
```

**Use Case:** Post-mortem analysis of why generation failed, parameter tuning feedback.

### 4.3 Idempotent Prep Re-Run

**Design Principle:** Prep pipeline must be idempotent (can be re-run safely).

**Behavior:**
- **First run:** Generate all assets. Some fail → use placeholders.
- **Second run (re-run failed only):** Skip successful assets, regenerate only failed assets.
- **Third run (full re-run):** Regenerate all assets (overwrite previous).

**Configuration Flag (M1+ scope):**
```python
PrepPipelineConfig:
    regenerate_failed_only: bool = False  # If True, skip successful assets
    regenerate_placeholders: bool = False  # If True, upgrade placeholders to real assets
```

**Workflow Example:**
1. **Initial prep:** 15 assets requested, 12 succeed, 3 fail → `status="partial"`
2. **User reviews failures:** Increases time budget from 60s to 90s CPU, adjusts problematic prompt
3. **Re-run prep with `regenerate_failed_only=True`:** Only attempts 3 failed assets
4. **Final prep:** 14 succeed, 1 fail → `status="partial"` (acceptable)

**Asset Store Query:** Check `GeneratedAsset.generation_method`:
- `"sdxl_lightning_nf4"` or other model name → Real asset (skip on re-run if `regenerate_failed_only=True`)
- `"placeholder"` → Placeholder asset (regenerate if `regenerate_placeholders=True`)

### 4.4 Manual Review Queue

**Storage Location:** `failed_prompts.json` in campaign output directory.

**Schema:**
```json
{
    "failed_prompts": [
        {
            "asset_id": "npc_portrait_001",
            "prompt": "A dwarf elf hybrid with transparent skin and four arms",
            "failure_reason": "bad_prompt_suspected",
            "average_score": 0.28,
            "attempts": 4,
            "timestamp": "2026-02-11T10:30:45Z"
        }
    ]
}
```

**Use Case:** DM reviews bad prompts, rewrites them, re-runs prep with corrected prompts.

---

## 5. Graceful Degradation Across Tiers

How placeholder system works consistently across all hardware tiers.

### 5.1 Tier 1-2 (GPU, ≥6 GB VRAM)

**Hardware:** RTX 4060+, RTX 3070+

**Image Generation Mode:** Full generation (SDXL Lightning NF4, 4-6 sec/image)

**Fallback Hierarchy:**
1. Shipped art pack (archetype match)
2. Generic category placeholder
3. Solid color + text

**Expected Success Rate:** 90%+ (most images generated successfully)

**Example Config:**
```python
PrepPipelineConfig:
    model_sequence: [
        ModelLoadConfig(model_type="image_gen", model_id="sdxl-lightning-nf4", device="cuda")
    ]
    time_budget_per_asset_sec: 60
    max_regeneration_attempts: 4
```

### 5.2 Tier 3 (GPU, 4-6 GB VRAM)

**Hardware:** RTX 3060, GTX 1660 Ti

**Image Generation Mode:** Full generation (SDXL Lightning NF4 with reduced resolution 512×512, or SD 1.5 + LCM LoRA)

**Fallback Hierarchy:**
1. Shipped art pack (archetype match)
2. Generic category placeholder
3. Solid color + text

**Expected Success Rate:** 70-80% (lower quality model, more failures)

**Example Config:**
```python
PrepPipelineConfig:
    model_sequence: [
        ModelLoadConfig(model_type="image_gen", model_id="sdxl-lightning-nf4", device="cuda")
    ]
    time_budget_per_asset_sec: 60
    max_regeneration_attempts: 3  # Reduced attempts (VRAM constraint)
```

### 5.3 Tier 4 (GPU <4 GB or CPU-only)

**Hardware:** Integrated GPU, older hardware

**Image Generation Mode:** Limited generation (SD 1.5 OpenVINO, 8-20 sec/image, CPU-only)

**Fallback Hierarchy:**
1. Shipped art pack (archetype match)
2. Generic category placeholder
3. Solid color + text
4. Text-only

**Expected Success Rate:** 50-60% (slow CPU generation, limited attempts)

**Example Config:**
```python
PrepPipelineConfig:
    model_sequence: [
        ModelLoadConfig(model_type="image_gen", model_id="sd-1.5-openvino", device="cpu")
    ]
    time_budget_per_asset_sec: 120  # Doubled time budget for CPU
    max_regeneration_attempts: 2  # Reduced attempts (time constraint)
```

### 5.4 Tier 5 (CPU-only, placeholder-by-default)

**Hardware:** Very old CPU, no GPU

**Image Generation Mode:** **Placeholder by default** (skip generation to save time)

**Fallback Hierarchy (used immediately, no generation):**
1. Shipped art pack (archetype match)
2. Generic category placeholder
3. Solid color + text
4. Text-only

**Expected Success Rate:** 0% generation by default (all placeholders)

**Opt-In Generation:** User can enable slow CPU generation via config flag.

**Example Config:**
```python
PrepPipelineConfig:
    model_sequence: []  # Empty (no image generation)
    skip_image_generation: True  # Use placeholders immediately
    fallback_preference: "shipped_art_pack"  # First choice
```

**Opt-In Config (user explicitly requests generation):**
```python
PrepPipelineConfig:
    model_sequence: [
        ModelLoadConfig(model_type="image_gen", model_id="sd-1.5-openvino", device="cpu")
    ]
    skip_image_generation: False
    time_budget_per_asset_sec: 180  # Extended time budget
    max_regeneration_attempts: 1  # Single attempt only
```

### 5.5 Tier Comparison Table

| Tier | Hardware | Generation Mode | Max Attempts | Time Budget | Expected Success | Fallback Preference |
|------|----------|-----------------|--------------|-------------|------------------|---------------------|
| **1-2** | RTX 4060+, 8+ GB | SDXL Lightning NF4 | 4 | 60s | 90%+ | Shipped Art Pack |
| **3** | RTX 3060, 4-6 GB | SDXL NF4 (512×512) | 3 | 60s | 70-80% | Shipped Art Pack |
| **4** | CPU-only, <4 GB | SD 1.5 OpenVINO | 2 | 120s | 50-60% | Shipped Art Pack |
| **5** | Old CPU | **Skip generation** | 0 | 0s | 0% (default) | Shipped Art Pack |

---

## 6. Asset Store Integration

How placeholders are stored in asset store and marked differently from real assets.

### 6.1 Placeholder Storage Format

**Storage:** Stored as `GeneratedAsset` objects (same schema as real assets).

**File Path:** Points to placeholder file (shipped art pack, generic placeholder, or solid color PNG).

**Content Hash:** Computed from placeholder file (allows deduplication — multiple assets may share same placeholder).

**Example:**
```python
GeneratedAsset(
    asset_id="npc_portrait_001",
    asset_type="npc",
    semantic_key="npc:thorin:portrait:v1",
    file_path="shipped_art_pack/human_fighter_male.png",  # Not in campaign dir
    file_format="png",
    content_hash="a1b2c3d4...",  # Hash of shipped art pack file
    generation_method="placeholder",  # Special marker
    metadata={
        "fallback_reason": "max_attempts_exhausted",
        "fallback_type": "shipped_art_pack",
        "archetype_match": "human_fighter_male",
        "regeneration_attempts": [...]  # Failed attempts
    }
)
```

### 6.2 Generation Method Marking

**Real Assets:**
```python
generation_method="sdxl_lightning_nf4"  # Or other model name
```

**Placeholders:**
```python
generation_method="placeholder"  # Special marker
```

**Use Case:** Asset store can query for placeholders to identify upgrade candidates:
```python
placeholders = [asset for asset in manifest.assets if asset.generation_method == "placeholder"]
```

### 6.3 Fallback Reason Metadata

**Real Assets:**
```python
metadata: {
    "fallback_reason": None  # No fallback used
}
```

**Placeholders:**
```python
metadata: {
    "fallback_reason": str,  # One of: "max_attempts_exhausted", "timeout", "hardware_failure", "bad_prompt", "user_aborted", "tier_default"
    "fallback_type": str,    # One of: "shipped_art_pack", "generic_category_placeholder", "solid_color_text", "text_only"
    "archetype_match": str,  # If shipped art pack used: archetype matched (e.g., "human_fighter_male")
    "regeneration_attempts": List[RegenerationAttempt]  # Failed attempts (for analysis)
}
```

**Example Fallback Reasons:**
- `"max_attempts_exhausted"` — All 4 attempts failed critique
- `"timeout"` — Time budget exceeded before max attempts reached
- `"hardware_failure"` — GPU OOM, model loading failure
- `"bad_prompt"` — Prompt flagged as problematic (all scores <0.30)
- `"user_aborted"` — User manually canceled generation
- `"tier_default"` — Tier 5 CPU-only, skipped generation by default

### 6.4 Regeneration Attempts Metadata

**Real Assets (successful first attempt):**
```python
metadata: {
    "regeneration_attempts": []  # Empty (first attempt succeeded)
}
```

**Real Assets (successful after retries):**
```python
metadata: {
    "regeneration_attempts": [
        {"attempt_number": 1, "critique_result": {"passed": False, ...}},
        {"attempt_number": 2, "critique_result": {"passed": True, ...}}
    ]
}
```

**Placeholders:**
```python
metadata: {
    "regeneration_attempts": [
        {"attempt_number": 1, "critique_result": {"passed": False, ...}},
        {"attempt_number": 2, "critique_result": {"passed": False, ...}},
        {"attempt_number": 3, "critique_result": {"passed": False, ...}},
        {"attempt_number": 4, "critique_result": {"passed": False, ...}}
    ]
}
```

**Use Case:** Debug why generation failed, which parameters were tried, which critique scores resulted.

### 6.5 Placeholder Upgrade Path

**Workflow:**
1. Initial prep: 15 assets, 3 placeholders → `status="partial"`
2. User identifies placeholders: Query `generation_method="placeholder"`
3. User adjusts config (increase time budget, fix bad prompts)
4. Re-run prep with `regenerate_placeholders=True`
5. Asset store regenerates placeholder assets, overwrites with real assets if successful

**Config Flag (M1+ scope):**
```python
PrepPipelineConfig:
    regenerate_placeholders: bool = False  # If True, upgrade placeholders to real assets
```

**Asset Store Logic:**
```python
def should_regenerate(asset: GeneratedAsset, config: PrepPipelineConfig) -> bool:
    if config.regenerate_placeholders and asset.generation_method == "placeholder":
        return True
    if config.regenerate_failed_only and asset.generation_method == "placeholder":
        return True
    if config.regenerate_all:
        return True
    return False
```

---

## 7. Fallback Hierarchy Decision Tree

Visual flowchart showing fallback selection logic.

### 7.1 Decision Tree Logic

```
Image Generation Failed
  ↓
Step 1: Check Shipped Art Pack
  ↓
  Archetype match exists?
    YES → Use shipped art pack → DONE ✅
    NO → Go to Step 2
  ↓
Step 2: Check Generic Category Placeholder
  ↓
  Generic placeholder exists for asset type?
    YES → Use generic category placeholder → DONE ⚠️
    NO → Go to Step 3
  ↓
Step 3: Check Solid Color + Text Rendering
  ↓
  Pillow available? (text rendering library)
    YES → Generate solid color PNG with text overlay → DONE ⚠️
    NO → Go to Step 4
  ↓
Step 4: Text-Only Mode (Last Resort)
  ↓
  Use text-only mode (no image displayed) → DONE ⚠️
```

### 7.2 Archetype Matching Logic

**For NPC Portraits:**

```
Extract metadata from asset:
  - species (human, elf, dwarf, halfling, etc.)
  - class (fighter, wizard, rogue, cleric, etc.)
  - gender (male, female, non-binary)

Check shipped art pack manifest:
  1. Exact match: species + class + gender
     → e.g., "human_fighter_male.png"
  2. Partial match: species + class (ignore gender)
     → e.g., "human_fighter.png"
  3. Species-only match: species (ignore class + gender)
     → e.g., "human_generic.png"
  4. No match: Use generic NPC placeholder
     → "generic_npc_portrait.png"
```

**For Scene Backgrounds:**

```
Extract metadata from asset:
  - location_type (tavern, dungeon, forest, castle, etc.)

Check shipped art pack manifest:
  1. Exact match: location_type
     → e.g., "tavern_interior.png"
  2. Generic match: location_category (indoor vs outdoor)
     → e.g., "generic_indoor_scene.png"
  3. No match: Use generic scene placeholder
     → "generic_scene_background.png"
```

**For Item Icons:**

```
Extract metadata from asset:
  - item_type (weapon, armor, consumable, treasure, etc.)
  - item_subtype (sword, potion, scroll, etc.)

Check shipped art pack manifest:
  1. Exact match: item_type + item_subtype
     → e.g., "weapon_sword.png"
  2. Type-only match: item_type
     → e.g., "generic_weapon.png"
  3. No match: Use generic item placeholder
     → "generic_item_icon.png"
```

### 7.3 Example Walkthroughs

**Example 1: NPC Portrait Fallback (Shipped Art Pack Match)**

```
Asset: npc_portrait_001
Metadata: species=human, class=fighter, gender=male
Generation: FAILED (4 attempts, max_attempts_exhausted)

Fallback Decision Tree:
  Step 1: Check shipped art pack
    → Check for "human_fighter_male.png"
    → FOUND in shipped art pack
    → Use "shipped_art_pack/human_fighter_male.png"

Result:
  GeneratedAsset(
    file_path="shipped_art_pack/human_fighter_male.png",
    generation_method="placeholder",
    metadata={
      "fallback_reason": "max_attempts_exhausted",
      "fallback_type": "shipped_art_pack",
      "archetype_match": "human_fighter_male"
    }
  )
```

**Example 2: Scene Background Fallback (Generic Placeholder)**

```
Asset: scene_background_002
Metadata: location_type=underwater_cave
Generation: FAILED (3 attempts, timeout)

Fallback Decision Tree:
  Step 1: Check shipped art pack
    → Check for "underwater_cave.png"
    → NOT FOUND (uncommon location type)
  Step 2: Check generic category placeholder
    → Check for "generic_scene_background.png"
    → FOUND
    → Use "placeholders/generic_scene_background.png"

Result:
  GeneratedAsset(
    file_path="placeholders/generic_scene_background.png",
    generation_method="placeholder",
    metadata={
      "fallback_reason": "timeout",
      "fallback_type": "generic_category_placeholder"
    }
  )
```

**Example 3: Item Icon Fallback (Solid Color + Text)**

```
Asset: item_icon_003
Metadata: item_type=artifact, item_subtype=mysterious_orb
Generation: FAILED (4 attempts, bad_prompt)

Fallback Decision Tree:
  Step 1: Check shipped art pack
    → Check for "artifact_mysterious_orb.png"
    → NOT FOUND (unique item)
  Step 2: Check generic category placeholder
    → Check for "generic_item_icon.png"
    → NOT FOUND (Tier 5 system, generic placeholders not shipped)
  Step 3: Check solid color + text rendering
    → Pillow available? YES
    → Generate solid color PNG (purple background)
    → Text: "ITEM ICON / Mysterious Orb / A glowing artifact..."
    → Save to "generated_placeholders/item_icon_003_placeholder.png"

Result:
  GeneratedAsset(
    file_path="generated_placeholders/item_icon_003_placeholder.png",
    generation_method="placeholder",
    metadata={
      "fallback_reason": "bad_prompt",
      "fallback_type": "solid_color_text"
    }
  )
```

**Example 4: Text-Only Fallback (Last Resort)**

```
Asset: npc_portrait_004
Metadata: species=aberration, class=warlock, gender=unknown
Generation: FAILED (1 attempt, hardware_failure)

Fallback Decision Tree:
  Step 1: Check shipped art pack
    → Check for "aberration_warlock.png"
    → NOT FOUND (uncommon species)
  Step 2: Check generic category placeholder
    → Check for "generic_npc_portrait.png"
    → NOT FOUND (Tier 5 minimal system)
  Step 3: Check solid color + text rendering
    → Pillow available? NO (minimal dependencies)
  Step 4: Text-only mode
    → No image file created
    → UI shows text description only

Result:
  GeneratedAsset(
    file_path="",  # Empty (no image file)
    generation_method="placeholder",
    metadata={
      "fallback_reason": "hardware_failure",
      "fallback_type": "text_only",
      "error_details": "GPU OOM: CUDA out of memory"
    }
  )
```

---

## 8. Schema Extensions

Proposed extensions to existing schemas (do NOT modify existing schemas directly).

### 8.1 GeneratedAsset Schema Extensions

**Existing fields (do not modify):**
- `asset_id`, `asset_type`, `semantic_key`, `file_path`, `file_format`, `content_hash`, `generation_method`, `metadata`

**Proposed metadata extensions (M1+ scope):**
```python
metadata: {
    # Existing fields
    "model_id": str,  # Already exists

    # NEW: Fallback-specific fields
    "fallback_reason": Optional[str],  # One of: "max_attempts_exhausted", "timeout", "hardware_failure", "bad_prompt", "user_aborted", "tier_default"
    "fallback_type": Optional[str],    # One of: "shipped_art_pack", "generic_category_placeholder", "solid_color_text", "text_only"
    "archetype_match": Optional[str],  # If shipped art pack: archetype matched (e.g., "human_fighter_male")
    "regeneration_attempts": List[RegenerationAttempt],  # Already exists in schema
    "bad_prompt_flagged": bool,        # True if bad prompt detected
    "error_details": Optional[str]     # Exception message if hardware failure
}
```

### 8.2 PrepPipelineConfig Extensions

**Existing fields (do not modify):**
- `campaign_descriptor`, `output_dir`, `model_sequence`, `enable_stub_mode`

**Proposed extensions (M1+ scope):**
```python
PrepPipelineConfig:
    # Existing fields
    campaign_descriptor: CampaignDescriptor
    output_dir: str
    model_sequence: List[ModelLoadConfig]
    enable_stub_mode: bool

    # NEW: Image generation control
    skip_image_generation: bool = False  # If True, use placeholders immediately (Tier 5)
    time_budget_per_asset_sec: int = 60  # Time budget per asset (GPU: 60s, CPU: 120s)
    max_regeneration_attempts: int = 4   # Max attempts (GPU: 4, CPU: 2)

    # NEW: Fallback control
    fallback_preference: str = "shipped_art_pack"  # First fallback choice
    enable_solid_color_fallback: bool = True       # Allow solid color + text generation
    enable_text_only_fallback: bool = True         # Allow text-only mode

    # NEW: Re-run control (M1+ scope)
    regenerate_failed_only: bool = False     # If True, skip successful assets
    regenerate_placeholders: bool = False    # If True, upgrade placeholders to real assets
    regenerate_all: bool = False             # If True, regenerate all assets (overwrite)
```

---

## 9. Integration Notes

How fallback integrates with existing prep pipeline and critique system.

### 9.1 Prep Pipeline Integration

**Execution Flow:**
```
Prep Pipeline: Sequential Model Loading
  1. Load LLM → Generate NPCs, encounters
  2. Unload LLM
  3. Load Image Gen (SDXL Lightning) → Generate portraits, scenes
     ↓
     For each image:
       3a. Generate image (attempt 1)
       3b. Critique image (graduated pipeline: Heuristics → ImageReward → SigLIP)
       3c. If critique FAIL:
           - Retry with adjusted parameters (attempt 2-4)
           - Repeat critique
       3d. If all attempts fail:
           → TRIGGER FALLBACK HIERARCHY
           → Select fallback (shipped art pack → generic → solid color → text-only)
           → Store placeholder asset
       3e. If any attempt passes:
           → Store real asset
  4. Unload Image Gen
  5. Load Music Gen → Generate music
  6. Unload Music Gen
  7. Load SFX Gen → Generate sound effects
  8. Unload SFX Gen
```

**Code Integration Point (pseudocode):**
```python
def generate_and_validate_image(asset_descriptor, config):
    for attempt in range(1, config.max_regeneration_attempts + 1):
        # Generate image
        image_bytes = generate_image(asset_descriptor, attempt_params)

        # Critique image
        critique_result = run_graduated_critique(image_bytes, asset_descriptor)

        if critique_result.passed:
            # Success! Store real asset
            return store_real_asset(asset_descriptor, image_bytes)

        # Check timeout
        if total_time > config.time_budget_per_asset_sec:
            break  # Time budget exceeded

    # All attempts failed → FALLBACK
    return select_and_store_fallback(asset_descriptor, failed_attempts, config)
```

### 9.2 Critique System Integration

**Graduated Filtering (3 layers):**
- **Layer 1 (Heuristics):** CPU-only, <100ms — Catches blur, format issues
- **Layer 2 (ImageReward):** GPU, ~1.5s — Text-image alignment
- **Layer 3 (SigLIP):** GPU, ~0.5s (optional) — Identity consistency

**Failure Triggers Retry:**
```python
if not layer1_result.passed:
    # Heuristics failed (blur, format) → retry with adjusted parameters
    return trigger_retry(reason="blur_detected", adjust_sampling_steps=True)

if not layer2_result.passed:
    # ImageReward failed (text-image misalignment) → retry with higher CFG
    return trigger_retry(reason="alignment_poor", adjust_cfg_scale=True)

if not layer3_result.passed:
    # SigLIP failed (identity drift) → retry with anchor features
    return trigger_retry(reason="identity_mismatch", add_anchor_features=True)
```

**Fallback Triggers After Max Attempts:**
```python
if all_attempts_failed:
    return select_fallback(asset_descriptor, failed_attempts)
```

### 9.3 Shipped Art Pack Distribution

**Directory Structure:**
```
aidm/
  assets/
    shipped_art_pack/
      manifest.json          # List of all shipped assets with metadata
      npc_portraits/
        human_fighter_male.png
        human_wizard_female.png
        elf_rogue_male.png
        dwarf_cleric_male.png
        ...
      scenes/
        tavern_interior_01.png
        dungeon_corridor_01.png
        forest_clearing_01.png
        ...
      items/
        generic_sword.png
        generic_potion.png
        generic_scroll.png
        ...
    placeholders/
      generic_npc_portrait.png
      generic_scene_background.png
      generic_item_icon.png
```

**Manifest Schema (`shipped_art_pack/manifest.json`):**
```json
{
  "version": "1.0",
  "npc_portraits": [
    {
      "filename": "human_fighter_male.png",
      "archetype": {
        "species": "human",
        "class": "fighter",
        "gender": "male"
      },
      "license": "CC-BY-SA 4.0",
      "attribution": "Artist Name"
    },
    ...
  ],
  "scenes": [
    {
      "filename": "tavern_interior_01.png",
      "location_type": "tavern",
      "indoor": true,
      "license": "CC0",
      "attribution": "Public Domain"
    },
    ...
  ],
  "items": [
    {
      "filename": "generic_sword.png",
      "item_type": "weapon",
      "item_subtype": "sword",
      "license": "MIT",
      "attribution": "Icon Library"
    },
    ...
  ]
}
```

---

## 10. Future Work (M1+ Scope)

Features deferred to M1+ Session Zero UX.

### 10.1 Manual Accept/Reject (User Override)

**Feature:** Show user the rejected image and allow manual override.

**Use Case:** User judges slightly blurry image as "good enough" for background NPC.

**UX Flow:**
```
Generation failed critique (MINOR: slight blur detected).
[Show Image Preview]
Quality issue detected: Image slightly blurry at UI size.
[Accept Anyway] [Regenerate with Custom Settings] [Use Placeholder]
```

**Constraint:** Only offer override for MINOR failures (not CRITICAL failures like 6-fingered hands).

### 10.2 Custom Generation Settings (Expert Mode)

**Feature:** Allow user to specify custom generation parameters (CFG, steps, prompt).

**UX Flow:**
```
Automated regeneration failed (3 attempts).
[Advanced] Try custom generation settings?
CFG Scale: [___] Sampling Steps: [___] Negative Prompt: [___]
[Generate] [Cancel]
```

**Constraint:** Hide behind "Advanced" option (expert users only).

### 10.3 Retry Later (Session Zero UX)

**Feature:** Allow user to manually retry failed assets in Session Zero UI.

**UX Flow:**
```
[Session Zero UI — Asset Browser]
┌───────────────────────────────────────┐
│ Failed Assets (3)                     │
│                                       │
│ ⚠️ Thorin Ironforge (NPC Portrait)    │
│   Status: Placeholder                 │
│   Fallback: Shipped Art Pack          │
│   [Retry Generation] [Upload Custom] │
│                                       │
│ ⚠️ Tavern Interior (Scene)            │
│   Status: Placeholder                 │
│   Fallback: Generic                   │
│   [Retry Generation] [Upload Custom] │
└───────────────────────────────────────┘
```

---

## 11. Acceptance Criteria

This design is complete when:

- [x] Four placeholder strategies defined (shipped art pack, generic, solid color, text-only)
- [x] Five failure trigger conditions defined (max attempts, timeout, user abort, hardware failure, bad prompt)
- [x] User notification design specified (log entry, summary report, UI notification)
- [x] Persistence of failed attempts specified (error logging, regeneration history, idempotent re-run)
- [x] Graceful degradation across tiers defined (Tier 1-5 behavior, consistent fallback system)
- [x] Asset store integration specified (placeholder storage, generation method marking, upgrade path)
- [x] Fallback hierarchy decision tree documented (archetype matching logic, example walkthroughs)

---

## 12. References

**Existing Infrastructure:**
- [aidm/core/asset_store.py](../../aidm/core/asset_store.py) — Asset storage system
- [aidm/schemas/prep_pipeline.py](../../aidm/schemas/prep_pipeline.py) — GeneratedAsset, PrepPipelineConfig, PrepPipelineResult
- [aidm/core/prep_pipeline.py](../../aidm/core/prep_pipeline.py) — Sequential model loading orchestrator
- [aidm/schemas/image_critique.py](../../aidm/schemas/image_critique.py) — RegenerationAttempt schema

**Research Foundation:**
- [docs/research/R0_BOUNDED_REGEN_POLICY.md](../research/R0_BOUNDED_REGEN_POLICY.md) — Non-binding research (max 3 retries, fallback hierarchy)
- [docs/AIDM_EXECUTION_ROADMAP_V3.md](../AIDM_EXECUTION_ROADMAP_V3.md) — M3 deliverables: "No mechanical dependence on images"

**R1 Technology Stack:**
- [pm_inbox/reviewed/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md](../../pm_inbox/reviewed/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md) — R1 model selections (SDXL Lightning NF4, ImageReward, SigLIP)

**Parallel Work Orders:**
- WO-RQ-IMG-010 (Bounded Regeneration Policy) — Defines max attempts (GPU: 4, CPU: 3), backoff strategy

---

**END OF DESIGN SPECIFICATION**

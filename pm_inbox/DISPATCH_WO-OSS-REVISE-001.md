# Instruction Packet: Documentation Agent

**Work Order:** WO-OSS-REVISE-001 (OSS Shortlist Corrections)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 2
**Deliverable Type:** Document edits

---

## YOUR TASK

Revise `docs/research/OSS_SHORTLIST.md` to correct two errors identified during project rehydration.

### Correction 1: Bucket 5.4 — Three.js

**Current text (line ~497-499):**
> **Red flags:** 3D engine for a 2D grid game. Massive bundle. Overkill by an order of magnitude.
> **Recommendation:** **Skip.** Wrong tool. If we ever need 3D (dice roll animations, dungeon fly-throughs), revisit then.

**Corrected text:**

Replace the entire §5.4 entry with:

```markdown
### 5.4 Three.js

| Field | Detail |
|-------|--------|
| Repo | https://github.com/mrdoob/three.js |
| License | **MIT** |
| Stars | ~104,000+ |
| Size | ~600KB+ gzipped (full), tree-shakeable |
| Status | Very actively maintained |

**What we'd reuse:** 3D scene renderer for the table surface. Camera rig (seated player angle, smooth stand-up transition to top-down). Table plane geometry, material system, lighting. Post-processing for crystal ball glow, ambient lighting changes.

**Why it fits doctrine:** MIT license. The product UI IS a 3D table — the battle map scroll, notebook, dice tower, crystal ball, and character sheet are physical objects ON a 3D table surface. Three.js is the right tool for this. Pixi.js handles the 2D grid rendering as a canvas texture applied to the scroll surface within the Three.js scene.

**Red flags:** Larger bundle than Pixi.js alone. Requires WebGL2 (broad support, but not universal). Learning curve for shader/material work (crystal ball glass effect, glow pulse). Must be combined with a 2D renderer (Pixi.js or Canvas) for the actual grid content.

**Recommendation:** **Adopt** (table surface renderer). Three.js owns the 3D scene (table, camera, objects, lighting). Pixi.js owns the 2D battle map grid as a texture on the scroll plane. This is a complementary pairing, not an either/or choice.
```

Also update the **Grid Visualization Bucket Summary** table (around line 521-527) to change Three.js from "Skip (3D)" to "**Adopt** (table surface)":

```markdown
| Three.js | MIT | WebGL | N/A (3D scene) | ~600KB+ | **Adopt** (table surface) |
```

Also update the **Master Recommendation Matrix** entry for Bucket 5 (around line 941):

Change from:
```
| **5. Grid (visualization)** | Pixi.js + `@pixi/tilemap` | (reference PlanarAlly) | MIT | browser-only |
```

To:
```
| **5. Grid (visualization)** | Three.js (table) + Pixi.js (grid) | (reference PlanarAlly) | MIT | browser-only |
```

### Correction 2: Bucket 9.2 — Visual Assets

**Current text (line ~822):**
> **Recommendation:** **Adopt** (primary visual asset source). Immediate content for Pixi.js map renderer. No legal overhead.

**Replace the Kenney recommendation with:**

```markdown
**Recommendation:** **Use as development placeholder** (minimum-spec fallback). Kenney tiles are useful for early development and for machines that cannot run image generation models. The product vision requires self-generated assets via the World Compiler (Stages 6-8) — Kenney tiles are NOT the shipping asset source. Downgrade from "Adopt" to "Placeholder."
```

**Update the Content & Assets Bucket Summary** table (around line 870-877):

Change Kenney from:
```
| **Kenney** | CC0 | Tiles, tokens, UI, icons | **Adopt** (primary visual) |
```
To:
```
| **Kenney** | CC0 | Tiles, tokens, UI, icons | **Placeholder** (dev + min-spec fallback) |
```

Also update the Master Recommendation Matrix Bucket 9 entry:

Change from:
```
| **9. Content** | d20srd.org + Kenney CC0 + Tiled | PCGen (reference) | OGL + CC0 + GPL(tool) | none |
```
To:
```
| **9. Content** | d20srd.org + Tiled + diffusers (self-gen) | PCGen (reference), Kenney (placeholder) | OGL + GPL(tool) + Apache-2 | none |
```

### Correction 3: Add Bucket 12 — Image/Audio Generation (NEW SECTION)

After Bucket 11, add a new section:

```markdown
## Bucket 12: Image & Audio Generation (World Compiler Stages 6-8)

> Current state: `aidm/core/prep_pipeline.py` has stub mode for image/music generation. `aidm/schemas/immersion.py` defines `ImageRequest`/`ImageResult`. World bundle schema defines asset pool categories with `generation_prompt_template`. **No real model integration exists.**

### 12.1 diffusers (Hugging Face)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/huggingface/diffusers |
| License | **Apache-2.0** |
| Stars | ~27,000+ |
| Deps | torch, transformers, safetensors |
| Status | Very actively maintained |

**What we'd reuse:** Unified inference pipeline for Stable Diffusion, SDXL, FLUX, and future image generation models. Handles model loading, scheduler selection, prompt encoding, denoising loop, and image output. Supports CPU fallback (slow but functional).

**Why it fits doctrine:** Apache-2.0 license. Model-agnostic — swap SD 1.5 → SDXL → FLUX without changing pipeline code. Hardware-aware: auto-selects precision (fp16/fp32) based on GPU capability. The product generates its own assets; diffusers is the inference engine.

**Model tiers by hardware:**

| Model | VRAM | Quality | Speed | License |
|-------|------|---------|-------|---------|
| SD 1.5 | ~2GB | Good | Fast | CreativeML Open RAIL-M |
| SDXL | ~6GB | Very Good | Medium | SDXL-1.0 (permissive) |
| FLUX.1-schnell | ~12GB (quantized ~8GB) | Excellent | Medium | Apache-2.0 |

**Red flags:** Large download sizes (2-12GB per model). GPU memory contention with LLM and TTS models — requires sequential loading (prep_pipeline.py already handles this). Model licenses vary — must audit each model's license card.

**Recommendation:** **Adopt** (image generation engine). Start with SD 1.5 for median hardware, upgrade path to SDXL/FLUX for capable machines. CPU fallback for minimum spec.

### 12.2 AudioCraft / MusicGen (Meta)

| Field | Detail |
|-------|--------|
| Repo | https://github.com/facebookresearch/audiocraft |
| License | **MIT** |
| Stars | ~21,000+ |
| Models | MusicGen-small (300M), MusicGen-medium (1.5B) |

**What we'd reuse:** Text-to-music generation. Scene descriptions → ambient music tracks. Theme-consistent background audio for different environments (tavern, dungeon, forest, combat).

**Model tiers:**

| Model | VRAM | Quality | License |
|-------|------|---------|---------|
| MusicGen-small | ~1.5GB | Good | MIT |
| MusicGen-medium | ~3.5GB | Very Good | MIT |

**Red flags:** GPU memory contention. Audio generation is lower priority than image generation for MVP. MVP spec explicitly says "voice only" for audio — music is post-MVP.

**Recommendation:** **Adopt** (post-MVP, World Compiler Stage 8). Lower priority than diffusers. Wire into prep_pipeline.py's sequential loading architecture.

### Image/Audio Generation Bucket Summary

| Candidate | License | Type | VRAM | Recommendation |
|-----------|---------|------|------|----------------|
| **diffusers** | Apache-2 | Image gen pipeline | 2-12GB | **Adopt** (core asset gen) |
| **SD 1.5** | RAIL-M | Image model (median) | ~2GB | **Adopt** (default tier) |
| **SDXL** | SDXL-1.0 | Image model (high) | ~6GB | **Adopt** (upgrade tier) |
| FLUX.1-schnell | Apache-2 | Image model (top) | ~12GB | Adopt when feasible |
| **MusicGen** | MIT | Music generation | 1.5-3.5GB | **Adopt** (post-MVP) |
```

Also update the **Recommended Adoption Phases** section to include the new bucket. Add to Phase 3:

```markdown
| diffusers + SD 1.5 | Image generation pipeline | World Compiler Stage 6 |
```

---

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/research/OSS_SHORTLIST.md` | Document to modify |
| 2 | `docs/specs/UX_VISION_PHYSICAL_TABLE.md` | Confirms Three.js for table surface |
| 2 | `docs/planning/REVISED_PROGRAM_SEQUENCING_2026_02_12.md` | Phase 3 specifies Three.js |
| 2 | `docs/contracts/WORLD_COMPILER.md` | Stages 6-8 require image/audio gen |
| 2 | `docs/planning/ACTION_PLAN_GAP_ANALYSIS.md` | GAP-019, GAP-020 reference these |

## STOP CONDITIONS

- None expected. This is a documentation correction.

## DELIVERY

- Modified: `docs/research/OSS_SHORTLIST.md`
- No code changes
- No test run needed
- Completion report: `pm_inbox/AGENT_WO-OSS-REVISE-001_completion.md`

## RULES

- Preserve all existing content that is NOT corrected
- Do not change recommendations for other buckets
- Keep the same formatting style as existing entries

---

END OF INSTRUCTION PACKET

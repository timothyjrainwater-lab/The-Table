# AIDM Project — PM Knowledge Base

> **Purpose:** Single-source PM rehydration document. Contains every critical detail,
> threshold, constraint, architectural decision, and technology selection needed to
> manage the AIDM project without context loss.
>
> **Last Updated:** 2026-02-11
> **Compiled By:** Opus (Acting PM)
> **Source Coverage:** 100% of docs/research/, docs/design/, docs/doctrine/,
> docs/governance/, docs/specs/, docs/planning/, docs/audits/, docs/analysis/,
> pm_inbox/reviewed/, pm_inbox/aegis_rehydration/, and root-level project files.

---

## TABLE OF CONTENTS

1. [Project Identity & Philosophy](#1-project-identity--philosophy)
2. [Architectural Pillars](#2-architectural-pillars)
3. [Milestone Status & Roadmap](#3-milestone-status--roadmap)
4. [R1 Technology Stack (LOCKED)](#4-r1-technology-stack-locked)
5. [Hardware Specifications (BINDING)](#5-hardware-specifications-binding)
6. [VRAM & RAM Budgets](#6-vram--ram-budgets)
7. [Performance Targets & Thresholds](#7-performance-targets--thresholds)
8. [Image Critique Pipeline (Three-Layer)](#8-image-critique-pipeline-three-layer)
9. [Bounded Regeneration Policy](#9-bounded-regeneration-policy)
10. [Image Generation Failure Fallback](#10-image-generation-failure-fallback)
11. [LLM Query Interface](#11-llm-query-interface)
12. [Audio Pipeline](#12-audio-pipeline)
13. [Determinism Contract](#13-determinism-contract)
14. [Authority Boundaries (Spark/Lens/Box)](#14-authority-boundaries-sparklensbox)
15. [LLM Safeguards & Kill Switches](#15-llm-safeguards--kill-switches)
16. [Governance & PR Gate Checklists](#16-governance--pr-gate-checklists)
17. [Immersion Layer Contract](#17-immersion-layer-contract)
18. [Session Zero & Design Layer](#18-session-zero--design-layer)
19. [Prep Pipeline Architecture](#19-prep-pipeline-architecture)
20. [Known Technical Debt](#20-known-technical-debt)
21. [R0 Research Status](#21-r0-research-status)
22. [Agent Operations & Standing Contract](#22-agent-operations--standing-contract)
23. [Completed Work Orders](#23-completed-work-orders)
24. [Ready-to-Dispatch Work Orders](#24-ready-to-dispatch-work-orders)
25. [Key File Locations](#25-key-file-locations)

---

## 1. Project Identity & Philosophy

**AIDM** = AI Dungeon Master for D&D 3.5e.

**Core Experience:** A solo player sits at a virtual table with an AI DM that has clearly
prepared. Voice-first interaction. Character sheet is the primary UI. Grid appears only
during combat. The experience feels like a prepared tabletop session, not a video game.

**Five Sacred Principles:**

1. **Determinism is sacred.** Same inputs produce identical mechanical outcomes. 10x
   replay verification required. Narration text may vary (presentation layer).

2. **Authority split is sacred.** The engine DEFINES reality (rolls, damage, legality).
   The LLM DESCRIBES reality (narration, dialogue, flavor). The LLM is never trusted
   with mechanical authority.

3. **Solo-first, prep-first, voice-first.** Solo player is the design target. Campaign
   preparation happens before play begins (like a real DM). Voice is the primary input
   modality.

4. **Local-first, offline-capable.** All computation runs locally. No cloud dependencies.
   No telemetry. No phone-home. Campaigns started today must be playable in 10+ years.

5. **Design layer is frozen.** Philosophical decisions are locked during build. No
   relitigation of adopted design documents.

**Target Audience:** Solo D&D player with median gaming hardware (Steam survey baseline).

**M0 Feature Scope:** Fighter, Wizard, Cleric, Rogue. Levels 1-5. Core combat (attack,
move, AoO). Voice-first. Prep-based asset generation. Save/resume with deterministic
replay.

---

## 2. Architectural Pillars

### 2.1 Spark / Lens / Box Doctrine (BINDING)

Three foundational layers with strict separation:

**SPARK (Generative Intelligence):**
- Raw LLM output BEFORE validation
- Pure text generation with zero constraints
- MUST NEVER refuse generation (refusal is LENS/BOX responsibility)
- MUST NEVER assert mechanical authority
- Non-authoritative and ephemeral until validated

**LENS (Presentation & Adaptation):**
- Post-generation filtering, tone adaptation, content gating
- Adapts verbosity/pacing per player expertise
- Routes output to appropriate UI channels
- Cannot invent mechanical claims or alter authority source

**BOX (Deterministic Rules Engine):**
- D&D 3.5e mechanical authority (sole arbiter)
- Computes attack rolls, saves, damage, legality
- Maintains authoritative WorldState via event sourcing
- All computations logged with provenance
- Cannot delegate decisions to SPARK

**Provenance Labels (ALL output must carry one):**
- `[BOX]` = Authoritative mechanical truth
- `[DERIVED]` = Inferred from BOX state (e.g., "appears injured" from HP < 50%)
- `[NARRATIVE]` = SPARK-generated flavor (no mechanical authority)
- `[UNCERTAIN]` = System guessing/paraphrasing (non-binding)

### 2.2 Event Sourcing

- All state changes are events (append-only log)
- Events include RNG seeds + roll results
- Replay event log = reconstruct identical state
- No in-place edits, reordering, or deletions

### 2.3 Protocol + Stub + Factory Pattern

Every adapter follows this pattern:
- **Protocol:** Defines interface (e.g., `ImageCritiqueAdapter`)
- **Stub:** Zero-dependency default (always works in CI)
- **Factory:** Pluggable backends via registry (`create_image_critic("heuristics")`)

### 2.4 Spark Swappability (BINDING for M2+)

- SPARK provider MUST be user-swappable via config (models.yaml)
- Each SPARK declares capability manifest
- Determinism preserved on swap (BOX outcomes identical)
- Fallback chain: 14B -> 8B -> 4B -> template narration

### 2.5 Capability Gates

| Gate | Name | Status |
|------|------|--------|
| G-T1 | Tier 1 Mechanics | OPEN |
| G-T2A | Permanent Stat Mutation | CLOSED |
| G-T2B | XP Economy | CLOSED |
| G-T3A-D | Entity Forking, Agency, Relations, Transform | CLOSED |

Only G-T1 is open. All others require explicit PM approval.

---

## 3. Milestone Status & Roadmap

**Canonical Roadmap:** `docs/AIDM_EXECUTION_ROADMAP_V3.md` (v3.2.0)

### Current Phase: M3 (Immersion Layer v1)

- Design phase: COMPLETE
- Implementation phase: ACTIVE
- All agents on standby, awaiting dispatch

### Milestone Summary

| Milestone | Status | Key Output |
|-----------|--------|------------|
| **M0** | FROZEN | Design closeout, doctrine adoption, CP-001 Position unification |
| **M1** | FROZEN | Solo vertical slice v0 (intent -> clarify -> resolve -> narrate -> update) |
| **M2** | FROZEN | Campaign prep pipeline v0, Persistence v1.1 (72 tests) |
| **M3** | ACTIVE | Immersion Layer v1 (voice, images, audio, grid) |
| **M4** | PLANNED | Offline packaging + shareability |

### M3 Supporting Tasks (15 total)

- M3.1-M3.4: Voice pipeline (STT/TTS integration)
- M3.5-M3.9: Image pipeline (generation, critique, bounded regen, fallback)
- M3.10-M3.13: Audio system (music gen, SFX, mixer, attribution)
- M3.14-M3.15: Grid rendering (contextual grid, combat visualization)

### Test Suite

- **Current:** 1823 tests passing, 0 failures
- **Runtime:** <5 seconds
- **Coverage:** Determinism canary tests (100x replay), authority boundary tests,
  immersion hardening tests, protocol compliance tests

---

## 4. R1 Technology Stack (LOCKED)

All 7 technology areas resolved. These selections are LOCKED.

| Area | Model | License | VRAM | Notes |
|------|-------|---------|------|-------|
| **LLM** | Qwen3 8B (median) / 14B (high) / 4B (low) | Apache 2.0 | 6 / 10 / 3 GB | 85% human preference in roleplay |
| **Image Gen** | SDXL Lightning NF4 | Apache 2.0 | 3.5-4.5 GB | 4-6s at 768x768 |
| **Image Critique L1** | HeuristicsImageCritic | CPU-only | 0 GB | OpenCV, <100ms |
| **Image Critique L2** | ImageReward v1.0 | MIT | ~1.0 GB | NeurIPS 2023, text-image alignment |
| **Image Critique L3** | SigLIP ViT-B-16 | Apache 2.0 | ~0.6 GB | Google, identity consistency |
| **TTS** | Kokoro (ONNX) | Apache 2.0 | 0 GB (CPU) | 4.0/5.0 quality, 150-300 MB RAM |
| **STT** | faster-whisper small.en | MIT | 0 GB (CPU) | CTranslate2 INT8, 400-700 MB RAM |
| **Music** | ACE-Step (PRIMARY) | Apache 2.0 | 6-8 GB | 3.5B params, prep-time generation |
| **Music Fallback** | Curated library | CC BY 3.0 / CC0 | 0 GB | 30-45 tracks, Baseline tier |
| **SFX** | Curated library | Various CC0/RF | 0 GB | Licensing blocker on generative |

**Key Decisions Reversed from R0:**
- R0-DEC-025 (SDXL NO-GO) -> REVERSED to GO (NF4 quantization makes it viable)
- R0-DEC-020 (LLM Median: Mistral 7B) -> Updated to Qwen3 8B
- R0-DEC-026 (TTS: Coqui/Piper) -> Updated to Kokoro
- R0-DEC-028 (STT: Whisper Base) -> Updated to faster-whisper small.en

**Strategic Intent (Thunder-confirmed):**
- Music: Generative (ACE-Step) is PRIMARY for Recommended tier (6+ GB VRAM)
- Music: Curated library is FALLBACK for Baseline tier (no GPU)
- SFX: Curated is PRIMARY (no permissive generative SFX models exist as of Feb 2026)

---

## 5. Hardware Specifications (BINDING)

Source: Steam Hardware Survey (January 2026)

### Median Spec (50th Percentile)

| Component | Specification |
|-----------|--------------|
| CPU | 6-8 cores, 3.0-3.5 GHz (i5-10400 / Ryzen 5 3600) |
| RAM | 16 GB |
| GPU | GTX 1660 Ti / RX 6600 XT (6-8 GB VRAM) |
| Storage | 512 GB SATA SSD |
| OS | Windows 10/11 |

### Minimum Spec (30th Percentile)

| Component | Specification |
|-----------|--------------|
| CPU | 4 cores, 2.5-3.0 GHz (i3-9100 / Ryzen 3 3200G) |
| RAM | 8 GB |
| GPU | Integrated (Intel UHD / AMD Vega) |
| Storage | 256 GB SSD/HDD |
| OS | Windows 10 (64-bit) |

### Hardware Tier Classification

| Tier | VRAM | GPU | Model Size | Use Case |
|------|------|-----|-----------|----------|
| HIGH (Enhanced) | >= 8 GB | Yes | 14B | RTX 3060 12GB, RTX 3090, RTX 4080 |
| MEDIUM (Recommended) | 6-8 GB | Yes | 8B | RTX 2060, GTX 1070, RX 6600 XT |
| FALLBACK (Baseline) | < 6 GB | Optional | 4B/3B | GTX 1050 Ti, CPU-only |

**Critical Finding:** 15% of Steam users have NO discrete GPU. CPU fallback is MANDATORY.

### Storage Budgets

- Install size: < 20 GB (median), < 10 GB (minimum)
- Campaign data: < 2 GB per campaign
- Asset cache: 5-15 GB (auto-pruned)

---

## 6. VRAM & RAM Budgets

### Sequential Pipeline VRAM Budget

AIDM is a **prep-time sequential pipeline**. Models load one at a time. Peak VRAM =
single largest model, NOT sum of all models.

```
Phase 1: LLM (Qwen3 8B)           -> 6 GB    -> Unloads
Phase 2: Image Gen (SDXL NF4)     -> 3.5-4.5 GB -> Unloads
Phase 3: Image Critique (ImgReward)-> 1.0 GB  -> Unloads
Phase 4: Music Gen (ACE-Step)      -> 6-8 GB  -> Unloads
Phase 5: SFX (curated)            -> 0 GB    (disk load)
Phase 6: TTS (Kokoro)             -> CPU only (150-300 MB RAM)
Phase 7: STT (faster-whisper)     -> CPU only (400-700 MB RAM)
```

**Peak VRAM:** ~6-8 GB (Phase 1 or Phase 4, never concurrent)

### RAM Allocation (16 GB Median)

| Component | Budget | % |
|-----------|--------|---|
| OS Overhead | 2.5 GB | 15.6% |
| LLM (Qwen3 8B Q4_K_M) | 6 GB | 37.5% |
| TTS (Kokoro ONNX) | 0.3 GB | 1.9% |
| STT (faster-whisper INT8) | 0.7 GB | 4.4% |
| Asset Cache | 2.5 GB | 15.6% |
| Application Runtime | 1.5 GB | 9.4% |
| **TOTAL** | **16.0 GB** | **100%** |

### RAM Allocation (8 GB Minimum)

| Component | Budget | % |
|-----------|--------|---|
| OS Overhead | 2.0 GB | 25.0% |
| LLM (Qwen3 4B Q4_K_M) | 3.5 GB | 43.8% |
| TTS (Kokoro) | 0.3 GB | 3.8% |
| STT (faster-whisper base.en) | 0.5 GB | 6.3% |
| Asset Cache | 0.7 GB | 8.8% |
| Application Runtime | 0.5 GB | 6.3% |
| **TOTAL** | **8.0 GB** | **100% (TIGHT)** |

---

## 7. Performance Targets & Thresholds

### Latency Targets

| Component | Target | Acceptable | Minimum Spec |
|-----------|--------|-----------|-------------|
| LLM tokens/sec | 15-25 | 10-30 | 5-10 (min spec) |
| Image generation | 5-8s (GPU) | 5-20s | 15-60s (CPU) |
| Image critique (Layer 1) | < 100ms | < 150ms | < 250ms |
| Image critique (Layer 2) | ~1.5s | < 2s | N/A (GPU only) |
| Image critique (Layer 3) | ~0.5s | < 1s | N/A (GPU only) |
| TTS latency | < 500ms | < 1000ms | < 1000ms |
| STT latency | < 1000ms | < 2000ms | < 2000ms |
| Memory query | < 200ms | < 500ms | < 500ms |

### Quality Thresholds

| Metric | Target | NO-GO Trigger |
|--------|--------|---------------|
| Image critique F1 (L1+L2+L3) | 0.85-0.90 | F1 < 0.70 |
| Image critique F1 (L1+L2) | 0.80-0.85 | — |
| Image critique F1 (L1 only) | 0.60-0.65 | — |
| False Positive Rate | < 10% | > 20% |
| False Negative Rate | < 15% | > 25% |
| TTS quality | > 70% acceptable | < 70% |
| TTS intelligibility | > 95% | < 90% |
| Indexed memory accuracy | > 90% | < 80% |
| LLM constraint adherence | 100% (0 violations/100 narrations) | Any violation |
| LLM JSON parsing success | > 95% | < 90% |
| Hallucination rate | < 5% | > 5% (triggers KILL-003) |

### Prep Pipeline Timing

| Scenario | Median Spec | Minimum Spec | Target |
|----------|-------------|-------------|--------|
| Minimal (1-hour session) | ~3.5 min | ~7 min | <= 30 min |
| **Full (2-hour session)** | **~9 min** | **~17 min** | **<= 30 min** |
| Long campaign | ~18 min | ~34 min | <= 60 min |

**Bottleneck:** LLM content generation (39% median, 71% minimum)

---

## 8. Image Critique Pipeline (Three-Layer)

### Architecture

```
Generated Image
    |
    v
Layer 1: Heuristics (CPU, <100ms, 0 VRAM)
    |-- FAIL --> Retry (no GPU models loaded yet)
    |-- PASS --> Layer 2
    v
Layer 2: ImageReward (GPU, ~1.5s, ~1.0 GB)
    |-- FAIL --> Retry
    |-- PASS --> Layer 3
    v
Layer 3: SigLIP (GPU, ~0.5s, ~0.6 GB, optional)
    |-- FAIL --> Retry
    |-- PASS --> ACCEPT
```

**Optimization:** Early rejection saves GPU time. 60-70% of bad images fail Layer 1
alone (<100ms, no GPU overhead).

### Layer 1: HeuristicsImageCritic (IMPLEMENTED)

**File:** `aidm/core/heuristics_image_critic.py` (558 lines)
**Tests:** `tests/test_heuristics_image_critic.py` (499 lines, 29 tests)
**Status:** IMPLEMENTED, TESTED, FACTORY-REGISTERED

Five heuristic checks:

| Check | Method | Maps To | Threshold |
|-------|--------|---------|-----------|
| Blur Detection | Laplacian variance | READABILITY | variance >= 100.0 |
| Composition | Center of mass + edge density | COMPOSITION | CoM centered, density 0.05-0.25 |
| Format Validation | Resolution, aspect ratio, color space | ARTIFACTING | 512-2048px, +/-15% aspect |
| Corruption Detection | Uniformity, extreme values | ARTIFACTING | std dev > 5.0 |
| Skipped (Identity/Style) | Pass-through (score 1.0) | IDENTITY_MATCH, STYLE_ADHERENCE | Requires ML |

**Factory usage:** `create_image_critic("heuristics")`
**Performance:** ~85ms per 512x512 image

### Layer 2: ImageReward (DESIGN COMPLETE)

**Model:** THUDM/ImageReward (NeurIPS 2023)
**License:** MIT
**Input:** Generated image + generation prompt text
**Output:** Score -1.0 to +2.0, normalized to [0.0, 1.0] via `(score + 1.0) / 3.0`
**Superiority:** 40% better than raw CLIP on human preference alignment
**Maps To:** IDENTITY_MATCH + STYLE_ADHERENCE dimensions
**VRAM:** ~1.0 GB FP16
**Performance:** ~1.5s per image on GPU

### Layer 3: SigLIP (DESIGN COMPLETE)

**Model:** Google SigLIP ViT-B-16
**License:** Apache 2.0
**Input:** Generated image + reference anchor image
**Output:** Cosine similarity [0.0, 1.0]
**Use Case:** Only invoked when anchor image exists (NPC portrait regeneration)
**Threshold:** similarity > 0.70 (balance FPR/FNR)
**VRAM:** ~0.6 GB FP16
**Performance:** ~0.5s per comparison on GPU

### Hardware Tier Support

| Tier | Layers Active | Expected F1 |
|------|--------------|------------|
| HIGH/MEDIUM (6+ GB VRAM) | All 3 layers | 0.85-0.90 |
| LOW GPU (1-2 GB) | Layers 1+2 (skip SigLIP) | 0.80-0.85 |
| CPU-only | Layer 1 only (heuristics) | 0.60-0.65 |

### Quality Dimensions (5 Core)

| ID | Dimension | Criticality | Heuristic-Checkable |
|----|-----------|-------------|---------------------|
| DIM-01 | Readability | CRITICAL | YES (Laplacian, contrast) |
| DIM-02 | Composition | HIGH | YES (CoM, bounding box) |
| DIM-03 | Artifacting | CRITICAL | PARTIAL (needs ML for anatomy) |
| DIM-04 | Style Adherence | MEDIUM | NO (needs CLIP/SigLIP) |
| DIM-05 | Identity Continuity | HIGH | YES (pHash), BETTER (SigLIP) |

### Severity Mapping

```
score >= 0.90 -> ACCEPTABLE
score >= threshold -> ACCEPTABLE
score >= 0.50 -> MINOR
score >= 0.30 -> MAJOR
score < 0.30  -> CRITICAL
```

---

## 9. Bounded Regeneration Policy

**Design Doc:** `docs/design/BOUNDED_REGENERATION_POLICY.md` (~410 lines)

### Maximum Attempts

| Tier | Max Attempts | Time Budget | Rationale |
|------|-------------|------------|-----------|
| GPU (Tiers 1-2) | 4 (1 original + 3 retries) | 60s/asset | 5s/attempt x 4 = 20s |
| CPU (Tiers 4-5) | 3 (1 original + 2 retries) | 120s/asset | 15s/attempt x 3 = 45s |

### Parameter Adjustment Backoff

| Attempt | CFG Scale | Steps (GPU) | Steps (CPU) | Creativity |
|---------|-----------|-------------|-------------|-----------|
| Original | 7.5 | 50 | 6 | 0.8 |
| Retry 1 | 9.0 | 60 | 8 | 0.65 |
| Retry 2 | 10.5 | 70 | 10 | 0.50 |
| Retry 3 | 12.0 | 80 | — | 0.35 |

### Dimension-Specific Negative Prompts

- **Readability failure:** "blurry, out of focus, low contrast"
- **Composition failure:** "off-center, cropped face, bad framing"
- **Artifacting failure:** "malformed hands, extra fingers, anatomical errors"
- **Style failure:** "inconsistent style, wrong genre"
- **Identity failure:** "different person, wrong species"

### Convergence Detection

1. **Acceptance:** Score >= 0.70 AND no CRITICAL dimensions
2. **Plateau:** Score doesn't improve for 2 consecutive retries -> terminate early
3. **Time exceeded:** GPU 60s / CPU 120s -> escalate to fallback
4. **Max attempts exhausted:** -> escalate to fallback

### Resource Budget (Typical 2-Hour Session: 15 images)

- GPU: ~15 min (50% of 30 min target)
- CPU: ~30 min (100% of target)

---

## 10. Image Generation Failure Fallback

**Design Doc:** `docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md` (~1,100 lines)
**Core Principle:** Game remains playable without images (no mechanical dependence).

### Four-Tier Fallback Hierarchy

| Tier | Strategy | Quality | Availability |
|------|----------|---------|-------------|
| 1. Shipped Art Pack | 50-100 NPC portraits, 20-30 scenes, 10-20 items | High | Always |
| 2. Generic Placeholder | Silhouette/abstract per category (3 total) | Medium | Always |
| 3. Solid Color + Text | Pillow-rendered PNG with name + description | Low | Always |
| 4. Text-Only | No image, description only | Minimal | Always |

### Archetype Matching (Tier 1)

Extract metadata: species, class, gender (NPCs); location_type (scenes).
Match hierarchy: exact -> partial -> species-only -> generic.

### Failure Triggers

1. Max regeneration attempts exhausted (GPU 4, CPU 2-3)
2. Time budget exceeded (GPU 60s, CPU 120s per asset)
3. User manual abort (Ctrl+C / UI cancel, M1+ scope)
4. Hardware failure (GPU OOM, model load exception)
5. Bad prompt detection (all attempts score < 0.30)

### Tier-Specific Behavior

| Tier | Hardware | Gen Mode | Max Attempts | Expected Success |
|------|----------|----------|-------------|-----------------|
| 1-2 | RTX 4060+, 8+ GB | SDXL Lightning | 4 | 90%+ |
| 3 | RTX 3060, 4-6 GB | SDXL NF4 512x512 | 3 | 70-80% |
| 4 | CPU-only | SD 1.5 OpenVINO | 2 | 50-60% |
| 5 | Old CPU | Skip (placeholder-first) | 0 | 0% |

### Regeneration Upgrade Path

1. User identifies placeholders via query: `generation_method="placeholder"`
2. User adjusts config (increase time budget, fix bad prompts)
3. Re-runs prep with `regenerate_placeholders=True`
4. Placeholder assets regenerated, overwritten if successful

---

## 11. LLM Query Interface

**Design Doc:** `docs/design/LLM_QUERY_INTERFACE.md` (~798 lines)
**Approach:** Pure prompt engineering (no RAG, no function calling)

### Three Prompt Template Types

| Template | Purpose | Token Budget | Output |
|----------|---------|-------------|--------|
| Narration | Generate flavor text for actions | <= 500 total | 2-4 sentences natural language |
| Query | Retrieve entity/event IDs from memory | <= 800 total | JSON {entity_ids, event_ids, summary} |
| Structured | Generate NPC stats / item properties | <= 600 total | Valid JSON conforming to schema |

### System Prompt Architecture (Total <= 1000 tokens)

- Role definition (narrator/memory system)
- World state summary (<= 300 tokens): Active NPCs, player location, threads, events
- Character context (<= 200 tokens): PC names, classes, levels, HP, equipment
- Tone guidance (<= 100 tokens): Fantasy genre, D&D 3.5e, concise
- Constraints (<= 100 tokens): No ability invention, no stat assignment, respect world state

### Structured Output Enforcement

- **GBNF Grammar:** Grammar-based finite constraints for llama.cpp
- **Stop sequences:** `}\n`
- **Fallback parsing:** JSON5 lenient parser, schema defaults for missing fields
- **Expected success:** >95% JSON parsing rate

### GuardedNarrationService Integration

```
IF narration_mode == "template_only" -> template
IF world_state.complexity < threshold -> template
IF LLM unavailable -> template
IF player_action in [ATTACK, MOVE, USE_ITEM] -> hybrid (template mechanics + LLM flavor)
ELSE -> pure LLM narration (exploration, social, environmental)
```

### Error Handling & Retry Budget

| Error Type | Detection | Response |
|-----------|-----------|----------|
| Unparseable output | JSON parse fails | Retry (max 2), then template fallback |
| Off-topic response | Unknown NPCs/abilities | Reject, retry with stricter constraints |
| Constraint violation | HP/stat assignments | Reject, retry with enforcement |

- **Max retries:** 2 per invocation (3 total attempts)
- **Timeout:** GPU 5s / CPU 10s per attempt
- **Total budget:** GPU 15s / CPU 30s per narration
- **Ultimate fallback:** Template narration (always succeeds)

### Temperature Isolation (HARD CONSTRAINT)

- **Query functions:** temperature <= 0.5 (deterministic recall)
- **Narration functions:** temperature >= 0.7 (generative flexibility)
- Separate code paths required. No shared temperature parameter.

---

## 12. Audio Pipeline

### Music Strategy

**PRIMARY (Recommended tier, 6+ GB VRAM):** ACE-Step generative music
- Apache 2.0 license, 3.5B parameters
- ~20-40 seconds per 60s clip on RTX 3060
- Supports all mainstream styles
- Loads during Phase 4 of prep pipeline (full GPU access after SDXL unloads)

**FALLBACK (Baseline tier, no GPU):** Curated royalty-free library
- Kevin MacLeod (CC BY 3.0), OpenGameArt (CC0), FreePD (CC0)
- 30-45 tracks, mood-tagged, 50-200 MB
- Zero compute cost

### SFX Strategy

**PRIMARY:** Curated library (licensing blocker on generative)
- Sonniss GDC, Freesound (CC0), Kenney.nl (CC0)
- 200-500 sounds, semantic key taxonomy
- 3-5 variants per key, round-robin selection
- Semantic keys: `combat:melee:sword:hit`, `ambient:peaceful:tavern`, etc.

**No permissive-license generative SFX models exist (Feb 2026).**

### Audio Implementation Status (Stubs)

**Files delivered (WO-M3-AUDIO-INT-01):**
- `aidm/schemas/audio.py` (510 lines) — AudioTrack, AudioMood, AudioTierConfig, AudioAttribution
- Tier detection (92 lines) — Enhanced/Recommended/Baseline classification
- Music generator (453 lines) — ACEStepMusicAdapter + CuratedMusicAdapter stubs
- SFX library (346 lines) — 23-key stub index, round-robin variants
- Audio mixer (218 lines) — 16-channel mixer stub (Ch 0 music, Ch 1 ambient, 2-15 SFX)
- 17 tests, all passing

### Audio Remaining Work

- **M3 Sprint 2:** Curated music library curation (30-45 tracks) — CONTENT TASK (human)
- **M3 Sprint 3:** SFX library curation (200-500 sounds) — CONTENT TASK (human)
- **M3 Sprint 4:** Real audio mixer (sounddevice integration)
- **M3.5+:** ACE-Step model integration (model download required)

---

## 13. Determinism Contract

**Source:** `docs/research/R0_DETERMINISM_CONTRACT.md`

### Layer 1: Mechanical Core (MUST Be Identical)

Dice rolls, damage calculation, HP updates, position changes, distance calculation
(1-2-1-2 diagonal), attack resolution, save resolution, initiative ordering, condition
application, action legality, event log.

### Layer 2: Presentation Layer (MAY Vary)

LLM narration text, narration tone/style, asset appearance, audio mix, UI animations,
display names.

### Layer 3: Metadata (MAY Vary, But Logged)

Timestamps, client hardware, model versions, generation attempts.

### Forbidden Sources of Non-Determinism

- Unseeded random (`random.random()`, `np.random.rand()`)
- System time (`time.time()`, `datetime.now()`)
- UUIDs (`uuid.uuid4()`)
- OS entropy (`os.urandom()`)
- Network requests during resolution
- User input during resolution (must freeze before resolution)
- Floating-point math in position/distance (causes drift)

### RNG Stream Isolation

| Stream | Purpose | Seed Source |
|--------|---------|------------|
| combat | Attack/damage rolls | Campaign seed + encounter ID |
| initiative | Initiative rolls | Campaign seed + combat start |
| saves | Saving throws | Campaign seed + save event ID |
| skill_checks | Skill checks | Campaign seed + check event ID |
| weather | Environmental | Campaign seed + day counter |

### Verification

10x replay test: Execute intents, record outcomes. Replay 9x from event log. Assert
all replays identical (HP, positions, conditions, dice rolls).

---

## 14. Authority Boundaries (Spark/Lens/Box)

### The LLM-Engine Boundary Contract (LEB-001, ADOPTED)

**Core Axiom:** The LLM may describe reality. The engine defines reality.

**Engine (BOX) alone may:**
- Resolve actions, roll dice, apply modifiers, enforce ordering
- Update world state, determine success/failure/consequence

**LLM (SPARK) may:**
- Interpret player intent, ask clarification, narrate outcomes
- Generate NPC dialogue, write campaigns/lore
- Be expressive, emotional, dark, humorous, strange
- Portray evil characters, gods, morally ambiguous scenarios

**LLM (SPARK) MUST NEVER:**
- Invent modifiers, adjust rolls, change distances, override outcomes
- "Soften" consequences, apply hidden bonuses/penalties
- Decide whether an action "should" be allowed
- Refuse an in-fiction action for moral/ideological reasons
- Resolve ambiguity silently
- Hide or rewrite engine output

**Refusal Authority:** LLM may NOT refuse unless Engine determines action impossible OR
Session Zero config explicitly forbids it. No "I'm not allowed to..." language.

**All resolved actions must log:** Raw player input, clarification exchanges, final intent
object, engine resolution, LLM narration, ruleset references.

---

## 15. LLM Safeguards & Kill Switches

### Five Determinism Invariants (HARD)

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| INV-DET-001 | Memory immutable during narration | Hash pre/post comparison |
| INV-DET-002 | All memory writes event-sourced | event_id required for writes |
| INV-DET-003 | Temperature isolation (query <= 0.5, narration >= 0.7) | Function entry assertion |
| INV-DET-004 | No narration-to-memory writes (EVER) | Code review gate |
| INV-DET-005 | Replay stability (10x identical) | CI test suite |

### Five Kill Switches

| Switch | Trigger | Auto-Action | Severity |
|--------|---------|------------|----------|
| KILL-001 | Memory hash changed during narration | Halt narration, disable generative mode | CRITICAL |
| KILL-002 | Unauthorized memory write (no event_id) | Reject write, require DM confirmation | CRITICAL |
| KILL-003 | Hallucination rate > 5% | Reduce temp to 0.2, require DM review | HIGH |
| KILL-004 | High-temp query (> 0.7) | Clamp to 0.5, log violation | MEDIUM |
| KILL-005 | Invention during context overflow | Disable speculation, aggressive truncation | CRITICAL |

### Forbidden Memory Write Paths

- LLM narration -> indexed memory (NEVER)
- LLM query -> indexed memory (NEVER)
- Fact extraction -> indexed memory (without validation, NEVER)
- Template expansion -> indexed memory (NEVER)
- Player input -> indexed memory (without intent confirmation, NEVER)

### Allowed Memory Write Paths

- Event log writer -> indexed memory (with event_id)
- DM manual override -> indexed memory (with confirmation + event log)
- Schema migration -> indexed memory (PM approved)

---

## 16. Governance & PR Gate Checklists

### M1 PR Gate Checklist (7 Mandatory Checks)

| Check | Requirement | Cannot Exempt |
|-------|-------------|---------------|
| CHECK-001 | No schema diff without PM approval | YES |
| CHECK-002 | No narration write path without validation | — |
| CHECK-003 | Temperature clamps enforced | YES |
| CHECK-004 | Hash freeze enforced (pre/post + assertion) | — |
| CHECK-005 | Kill switch tests present | YES |
| CHECK-006 | Test coverage >= 90% | — |
| CHECK-007 | Spark/Lens/Box separation preserved | YES |

### M2 PR Gate Checklist (10 Mandatory Checks)

All M1 checks plus:
| CHECK-008 | Spark Swappability (no hard-coded model paths) | YES |
| CHECK-009 | Documentation updated | — |
| CHECK-010 | No breaking changes without migration path | — |

### M1 Unlock Criteria (6 Hard Gates)

1. M0 shipped to production/beta (playtest completed)
2. Policy gaps resolved (GAP-POL-01 through GAP-POL-04)
3. M0 lessons learned documented
4. Indexed memory validated in M0 context
5. M1 planning approved by PM
6. M0 critical fixes deployed (zero CRITICAL bugs)

### M1 Slice Certification

**Status:** CERTIFIED (9/9 tests passed)
- Frozen snapshot immutability enforced
- No memory write methods present
- Hash unchanged pre/post narration
- Temperature boundary enforced
- Kill-001 triggers on hash mismatch
- Kill switch manual reset functional

---

## 17. Immersion Layer Contract

**Source:** `docs/IMMERSION_HANDOFF.md`

### Non-Authoritative Principle

Immersion READS engine state, NEVER WRITES. Mechanically enforced via:
1. AST-based import analysis (whitelisted imports only)
2. Deepcopy mutation tests (WorldState checked pre/post)
3. Output isolation tests (immersion outputs don't leak into WorldState)

### Components (243 tests, all passing)

| Component | Tests | Purpose |
|-----------|-------|---------|
| Schemas | 64 | 10 dataclasses for immersion data |
| Voice Pipeline | 19 | STT/TTS adapters |
| Audio System | 22 | Scene audio state computation |
| Image Pipeline | 11 | Image generation adapters |
| Grid Rendering | 17 | Combat grid visibility |
| Attribution | 14 | License compliance ledger |
| Integration | 18 | Full lifecycle acceptance |
| Hardening | 38 | Import safety, determinism |
| Authority Contract | 12 | Non-mutation enforcement |
| Determinism Canary | 28 | 100x regression detector |

### API Stability (PUBLIC_STABLE)

- May ADD new exports
- May ADD optional parameters (with defaults)
- Must NOT REMOVE or RENAME existing exports without migration
- Must NOT CHANGE existing signatures in breaking ways

---

## 18. Session Zero & Design Layer

### Session Zero Ruleset (SZ-RBC-001, ADOPTED)

Session Zero produces a **Ruleset Manifest** (versioned, immutable once play begins).

Configurable areas:
- Ruleset foundation (DND_3.5_RAW, errata version, optional rules)
- Variant/homebrew rules (explicit declarations only)
- Alignment system (strict / inferred / narrative-only)
- Deities and divine power (doctrine constraints, violation consequences)
- Class restrictions (alignment locks on/off, multiclass penalties)
- Narrative tone (grimdark / heroic / mythic, lethality)
- Creative boundaries (table-defined, not model ethics)
- Preparation depth (light / standard / deep)

### LLM Obedience Hierarchy

When narrating, LLM defers in order:
1. Deterministic engine output
2. Session Zero ruleset config
3. Campaign state & history
4. Player intent
5. Narrative style preferences

### Design Layer Adoption Record (FROZEN 2026-02-09)

Frozen documents:
- SZ-RBC-001: Session Zero Ruleset
- CS-UI-001: Character Sheet UI Contract
- VICP-001: Voice Intent & Clarification
- LEB-001: LLM-Engine Boundary Contract
- LRP-001: Local Runtime Packaging
- SF-PDM-001: Solo-First Preparatory DM Model

**No changes without formal amendment process.**

---

## 19. Prep Pipeline Architecture

### Sequential Loading (Phase-by-Phase)

```
Phase 1: LLM Content Generation (Qwen3 8B)
   - 8 NPCs, 3 encounters, 5 scenes, 8 dialogues, 10 narrations
   - ~4,850 tokens, ~3.5 min median / ~12 min minimum
   - Unload LLM

Phase 2: Image Generation (SDXL Lightning NF4)
   - 8 portraits + 5 scenes = 13 images
   - ~5s/image GPU, ~15s/image CPU
   - ~1.5 min median / ~3.5 min minimum
   - Unload SDXL

Phase 3: Image Critique (Three-Layer)
   - 13 images + ~20% fail rate (3 regenerations)
   - L1: <100ms, L2: ~1.5s, L3: ~0.5s
   - ~0.4 min median / ~0.9 min minimum

Phase 4: Music Generation (ACE-Step or curated)
   - 5 tracks x 30s = 150s generation
   - ~3 min median / 0s minimum (curated fallback)
   - Unload ACE-Step

Phase 5: SFX Loading (curated library)
   - File copy/indexing only
   - <5 seconds all specs

Phase 6: TTS Narration (Kokoro)
   - 10 clips x 200ms = ~2s median
   - CPU-only, concurrent possible
```

### Timing Projection (Full 2-Hour Session)

- **Median:** ~9 min (well within 30 min target)
- **Minimum:** ~17 min (within 30 min target)
- **Long campaign:** ~18 min median / ~34 min minimum

### Bottleneck Analysis

| Phase | % of Median | % of Minimum |
|-------|------------|-------------|
| LLM Content | 39% | **71% (DOMINANT)** |
| Image Gen | 17% | 21% |
| Music Gen | 33% | 0% (curated) |
| Image Critique | 4% | 5% |
| SFX/TTS | < 2% | < 1% |

---

## 20. Known Technical Debt

| ID | Item | Severity | Status |
|----|------|----------|--------|
| TD-001 | Three GridPoint types | HIGH | RESOLVED (CP-001) |
| TD-002 | Replay runner handles 4/41 events | HIGH | By design |
| TD-003 | play_loop.py 419 lines | MEDIUM | Deferred |
| TD-004 | Bare string entity fields | MEDIUM | CLOSED (FIX-08) |
| TD-005 | AoO incomplete (ranged/spellcasting) | MEDIUM | Blocked by CP-18A |
| TD-006 | Temp modifier stub | LOW | Blocked by CP-16 |
| TD-007 | AC/HP recalc stubs | LOW | Blocked |
| TD-008 | WORKSPACE_MANIFEST stale | LOW | Use PSD instead |
| TD-009 | Hard-coded weapon range | LOW | Needs weapon schema |
| TD-010 | Interaction.py target candidates | LOW | Needs voice bridge |
| TD-011-016 | Various audit fixes | LOW-HIGH | ALL CLOSED (FIX-01 thru FIX-18) |

**Rule:** Do NOT fix items without explicit PM approval.

---

## 21. R0 Research Status

### Overall: 49 Questions

| Category | Count |
|----------|-------|
| R1-Answered | 7 |
| R1-Partially-Answered | 6 |
| Already Complete | 2 |
| In Progress | 4 |
| **Critical Open** | **6** |
| Important Open | 13 |
| Deferred (M1+) | 11 |

### Critical Open Questions (6)

| Question | What's Needed | Who |
|----------|--------------|-----|
| RQ-PREP-001 | Prep time budget (hardware benchmarking) | Thunder (hardware access) |
| RQ-LLM-002 | LLM query interface | DESIGN COMPLETE |
| RQ-LLM-006 | Qwen3 rules adherence testing | Agent A (model needed) |
| RQ-IMG-003 | Image quality thresholds | Thunder + Agent B (user testing) |
| RQ-IMG-010 | Bounded regen policy | DESIGN COMPLETE |
| RQ-IMG-009 | Failure fallback strategy | DESIGN COMPLETE |

### GO/NO-GO Criteria for M0 (6 Gates)

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Canonical ID Schema | IN PROGRESS (7 critical Qs pending) |
| 2 | Indexed Memory Architecture | VALIDATED (certified for M1) |
| 3 | Hardware Baseline | ESTABLISHED (Steam survey locked) |
| 4 | Image Critique | ANSWERABLE (model selection resolved) |
| 5 | Prep Pipeline | PROJECTED PASS (~9 min median) |
| 6 | MVP Scope | IN PROGRESS (draft exists) |

### NO-GO Triggers (Any ONE triggers pivot)

| Trigger | Threshold | Current Status |
|---------|-----------|---------------|
| Image critique F1 < 0.70 | Quality unacceptable | NOT TRIGGERED |
| Indexed memory < 80% accuracy | Unreliable | NOT TRIGGERED |
| Prep time > 60 min | UX failure | NOT TRIGGERED |
| Models don't fit median spec | Infeasible | NOT TRIGGERED |
| TTS quality < 70% acceptable | Unacceptable | NOT TRIGGERED |

---

## 22. Agent Operations & Standing Contract

### Authority Map

| Role | Agent | Decides |
|------|-------|---------|
| Project Owner | Thunder | Dispatch, acceptance, scope, gate openings |
| PM | Aegis (or Opus acting) | Sequencing, WO drafting, delivery acceptance |
| Principal Engineer | Opus | Audits, architectural adjudication |
| Implementers | Sonnet A-F | Bounded execution per WO scope only |

### Standing Ops Rules (Key Points)

- PM proposes specific actions with deliverables (never asks for approval)
- PM never declares work "in progress" without explicit WO dispatch by Thunder
- PM never drafts code. PM drafts scope, acceptance, sequencing.
- Opus audits AFTER delivery. No pre-audit or speculation.
- Opus makes irreversible architectural decisions (freezes, boundary laws, gates)
- Sonnet agents execute within WO scope ONLY. Out-of-scope documented, not fixed.
- Sonnet agents run full test suite before completion. Zero regressions required.
- Thunder dispatches by pasting WO text (not verbal descriptions)
- Precise verbs: "planned" != "dispatched", "drafted" != "approved"

### Rehydration Protocol

1. Read SESSION_BOOTSTRAP.md (posture + state)
2. Read AEGIS_REHYDRATION_STATE.md (pipeline details)
3. Read STANDING_OPS_CONTRACT.md (behavioral rules)
4. Read R1_TECHNOLOGY_STACK_SUMMARY.md (model selections)
5. Read OPUS_ACTION_REPORT (action items)
6. Read PM_KNOWLEDGE_BASE.md (THIS FILE)
7. Confirm: "I see [N] active items, waiting on [X]. State: [status]."
8. Resume from current state. Do NOT re-plan.

---

## 23. Completed Work Orders

| WO ID | Agent | Date | Key Output |
|-------|-------|------|------------|
| WO-M2-01 | Sonnet A | 2026-02-10 | M2 Persistence Architecture Freeze v1.1 |
| WO-M3-PREP-01 | Sonnet B | 2026-02-11 | Prep pipeline prototype (sequential loading) |
| WO-R1-RESEARCH-UPDATE-01 | Opus | 2026-02-11 | R1 Technology Stack Validation (7 areas) |
| WO-M3-IMAGE-CRITIQUE-02 | Sonnet C | 2026-02-11 | 4 design docs: Heuristics + ImageReward + SigLIP + Prep Integration |
| WO-R0-CRITICAL-RESEARCH-DESIGN-01 | Sonnet B | 2026-02-11 | 3 draft WOs: RQ-LLM-002, RQ-IMG-010, RQ-IMG-009 |
| WO-M3-AUDIO-EVAL-01 | Sonnet D | 2026-02-11 | 5 eval docs: ACE-Step validated, curated spec, tier mapping |
| WO-M3-MODEL-REF-CLEANUP-01 | Sonnet A | 2026-02-11 | 47 stale model refs replaced across 4 governance docs |
| WO-RQ-IMG-010 | Sonnet B | 2026-02-11 | Bounded Regeneration Policy design (~410 lines) |
| WO-RQ-IMG-009 | Sonnet C | 2026-02-11 | Failure Fallback design (~1,100 lines) |
| WO-M3-HEURISTICS-IMPL-01 | Sonnet E | 2026-02-11 | HeuristicsImageCritic implementation (558 lines, 29 tests) |
| WO-RQ-LLM-002 | Sonnet A | 2026-02-11 | LLM Query Interface Design (~798 lines) |
| WO-M3-AUDIO-INT-01 | Sonnet D | 2026-02-11 | Audio pipeline integration (2,054 lines, 17 tests, stubs) |

**Total tests:** 1823 passing, 0 failures

---

## 24. Ready-to-Dispatch Work Orders

Implementation WOs (all designs approved, agents available):

| WO ID | Description | Agent | Dependencies |
|-------|-------------|-------|-------------|
| WO-M3-BOUNDED-REGEN-IMPL | Bounded Regeneration implementation | — | Design approved |
| WO-M3-FAILURE-FALLBACK-IMPL | Failure Fallback implementation | — | Design approved |
| WO-M3-IMAGEREWARD-IMPL-02 | Layer 2 ImageReward adapter | — | Design approved, ~1 GB VRAM |
| WO-M3-SIGLIP-IMPL-03 | Layer 3 SigLIP adapter | — | Design approved, ~0.6 GB VRAM |
| WO-M3-CRITIQUE-ORCHESTRATOR | Graduated critique pipeline orchestrator | — | L1 implemented, L2/L3 designs |
| WO-M3-LLM-QUERY-IMPL | LLM Query Interface implementation | — | Design approved |

### Backlog (Not Ready)

- R0 critical research requiring hardware (RQ-PREP-001, RQ-LLM-006, RQ-IMG-003) — needs Thunder
- Audio curated music library (30-45 tracks) — CONTENT TASK (human)
- Audio SFX library curation (200-500 sounds) — CONTENT TASK (human)
- Real audio mixer (M3 Sprint 4, needs sounddevice)
- ACE-Step model integration (M3.5+, needs model download)

---

## 25. Key File Locations

### Doctrine (Foundation)

| File | Purpose |
|------|---------|
| `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` | Core architecture separation |
| `docs/doctrine/SPARK_LENS_BOX_DEFINITIONS.md` | Technical definitions |
| `docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md` | Model swappability requirement |

### Governance (Enforcement)

| File | Purpose |
|------|---------|
| `docs/governance/M1_PR_GATE_CHECKLIST.md` | 7 mandatory checks |
| `docs/governance/M1_MONITORING_PROTOCOL.md` | Kill switches & invariants |
| `docs/governance/M1_UNLOCK_CRITERIA.md` | 6 hard gates for M1 |
| `docs/governance/M1_SLICE_CERTIFICATION.md` | Minimal viable slice |
| `docs/governance/M2_PR_GATE_CHECKLIST.md` | 10 mandatory checks |

### Design (Architecture)

| File | Purpose |
|------|---------|
| `docs/design/BOUNDED_REGENERATION_POLICY.md` | Image retry policy (~410 lines) |
| `docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md` | Fallback hierarchy (~1,100 lines) |
| `docs/design/LLM_QUERY_INTERFACE.md` | Prompt templates + constraints (~798 lines) |
| `docs/design/HARDWARE_DETECTION_SYSTEM.md` | Three-tier hardware classification |
| `docs/design/SPARK_ADAPTER_ARCHITECTURE.md` | LLM adapter protocol |
| `docs/design/IMAGE_CRITIQUE_ADAPTERS_DESIGN.md` | Three-layer critique pipeline |
| `docs/design/M1_IMPLEMENTATION_GUARDRAILS.md` | Determinism invariants |
| `docs/design/M1_LLM_SAFEGUARD_ARCHITECTURE.md` | 6 core safeguards |

### Research

| File | Purpose |
|------|---------|
| `docs/research/R0_MASTER_TRACKER.md` | 49 research questions registry |
| `docs/research/R0_DECISION_REGISTER.md` | GO/NO-GO decisions |
| `docs/research/R0_MODEL_BUDGETS.md` | VRAM/RAM allocation |
| `docs/research/R0_HARDWARE_BASELINE_SOURCES.md` | Steam survey data |
| `docs/research/R0_DETERMINISM_CONTRACT.md` | Determinism requirements |
| `docs/research/R0_IMAGE_CRITIQUE_FEASIBILITY.md` | Three-layer pipeline feasibility |
| `docs/research/R0_PREP_PIPELINE_TIMING_STUDY.md` | Timing projections |

### Implementation

| File | Purpose |
|------|---------|
| `aidm/core/heuristics_image_critic.py` | Layer 1 critique (558 lines) |
| `aidm/core/image_critique_adapter.py` | Protocol + factory (248 lines) |
| `aidm/schemas/image_critique.py` | CritiqueResult, CritiqueRubric (LOCKED) |
| `aidm/schemas/audio.py` | Audio schemas (510 lines) |
| `aidm/schemas/position.py` | Canonical Position type (CP-001) |
| `aidm/schemas/campaign_memory.py` | SessionLedger, Evidence, Threads |
| `tests/test_heuristics_image_critic.py` | 29 Layer 1 tests |

### PM / Rehydration

| File | Purpose |
|------|---------|
| `pm_inbox/aegis_rehydration/SESSION_BOOTSTRAP.md` | Context window startup |
| `pm_inbox/aegis_rehydration/AEGIS_REHYDRATION_STATE.md` | Pipeline state |
| `pm_inbox/aegis_rehydration/STANDING_OPS_CONTRACT.md` | Behavioral rules |
| `pm_inbox/aegis_rehydration/R1_TECHNOLOGY_STACK_SUMMARY.md` | R1 selections |
| `pm_inbox/aegis_rehydration/OPUS_ACTION_REPORT_2026-02-11.md` | Action items |
| `pm_inbox/aegis_rehydration/PM_KNOWLEDGE_BASE.md` | THIS FILE |

### Roadmap & Handoff

| File | Purpose |
|------|---------|
| `docs/AIDM_EXECUTION_ROADMAP_V3.md` | Canonical roadmap (v3.2) |
| `docs/IMMERSION_HANDOFF.md` | Immersion layer handoff (243 tests) |
| `KNOWN_TECH_DEBT.md` | Deferred work tracking |
| `PROJECT_STATE_DIGEST.md` | Implementation snapshot |

---

**END OF PM KNOWLEDGE BASE**

**Compiled:** 2026-02-11
**Agent:** Opus (Acting PM)
**Source:** 100% documentation coverage (170+ files, ~150,000+ lines)
**Status:** Ready for PM rehydration use

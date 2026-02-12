# Action Plan: Gap Analysis & OSS Fill Strategy

**Author:** PM (Opus) + PO (Thunder)
**Date:** 2026-02-13
**HEAD:** `d4edf47`
**Status:** DRAFT — Awaiting PO ratification
**Purpose:** Map every gap between current state and destination product (MVP: Session Zero → One Combat). Classify each gap by fill strategy. Provide a decision matrix for PO approval.

**References:**
- `REVISED_PROGRAM_SEQUENCING_2026_02_12.md` — 5-phase roadmap
- `MVP_SESSION_ZERO_TO_ONE_COMBAT.md` — 10 acceptance criteria
- `UX_VISION_PHYSICAL_TABLE.md` — Table metaphor spec
- `RQ-TABLE-FOUNDATIONS-001.md` — 7 research topics
- `WORLD_COMPILER.md` — 825-line compile contract
- `OPUS_AUDIT_POSTLAND_001.md` — Test suite status (4,601 pass, 71/71 BL)
- `OSS_SHORTLIST.md` — OSS research (11 buckets)

---

## Classification Key

| Tag | Meaning |
|-----|---------|
| **OSS-DROP** | Install a library, write adapter glue, done. No novel logic. |
| **OSS-MODEL** | OSS provides the ML model; we build the pipeline, scheduling, and integration. |
| **CUSTOM** | No OSS shortcut. Must be designed and built from scratch. |
| **DONE** | Already implemented with tests. |
| **PARTIAL** | Code exists but incomplete or stub-only in critical paths. |

---

## 1. Current State Summary

### What's Built (DONE)

| System | Evidence | Tests |
|--------|----------|-------|
| Deterministic combat engine (Box) | 67 files, 69K lines in aidm/core/ | 4,601 pass |
| Boundary law enforcement | 71 AST-scan tests | 71/71 |
| Intent bridge (combat mode) | 520 lines, entity/weapon/spell resolution | 1,242 lines |
| Narrative brief pipeline | NarrativeBrief → one-way valve to Spark | Comprehensive |
| Context assembler | Token-budget context retrieval, salience ranking | Yes |
| Prompt pack builder | Five-channel PromptPack (Truth/Memory/Task/Style/OutputContract) | Yes |
| Scene manager | Scene state, ambience, NPC tracking, transitions | Yes |
| Segment summarizer | Session segment tracking + recency decay | Yes |
| Template narration (M1) | Template-based narration from EngineResult | Yes |
| Guarded narration service | Spark safety guardrails, contradiction checking | Yes |
| Contradiction checker | Validates Spark output vs Box truth | Yes |
| Kill switch registry | Content filtering, per-table customization | Yes |
| Spark adapter + llama.cpp | LLM inference, grammar shield, model registry | Yes |
| DM persona | Tone control, NPC voice mapping, system prompts | Yes |
| Session orchestrator | Full turn cycle: STT → Intent → Box → Lens → Spark → TTS | Yes |
| Play controller | Single-turn integration with fallbacks | Yes |
| Campaign schemas | SessionZeroConfig, CampaignManifest, PrepJob, AssetRecord | Yes |
| Prep orchestrator | Deterministic job queue, idempotency via content hash | Yes |
| Prep pipeline | Sequential model loading (stub/real), asset generation | Yes |
| TTS: Kokoro (ONNX, CPU) | 8 personas, 24kHz, lazy init, graceful fallback | Yes |
| TTS: Chatterbox (GPU) | Voice cloning, turbo + original modes, emotion | Yes |
| STT: Whisper adapter | Whisper integration + stub fallback | Yes |
| TTS/STT adapter factory | Protocol + lazy loading + stub fallback | Yes |
| Provenance tracking | W3C PROV-DM, chain queries, serialization | Yes |
| Knowledge mask progression | HEARD_OF → SEEN → FOUGHT → STUDIED, 35 tests | Yes |
| Flanking geometry | 29 tests, wired into attack resolvers | Yes |
| Event log + replay | Deterministic replay, state hashing | Yes |
| FrozenWorldStateView | Immutability at non-engine boundaries | 14 tests |

### What's Partially Built (PARTIAL)

| System | What Exists | What's Missing |
|--------|-------------|----------------|
| Voice resolver | Archetype mapping tables, VoiceRoster cache | Actual LLM voice description parsing — returns default |
| Character sheet UI | 14.5K line display component | No interaction, no web rendering |
| Prep pipeline (real mode) | Stub mode fully tested | Real model loading for image/music gen not wired |

### What's Spec-Only or Missing (GAP)

| System | Spec Exists? | Code? |
|--------|-------------|-------|
| AD-007 Presentation Semantics dataclass | Schema JSON ✓, AD ratified ✓ | **No Python dataclass, no enforcement tests** |
| Rulebook object model | Contract §0.4 | No code |
| World compiler | 825-line contract, 4 JSON schemas | No code |
| MVP World "Ashenmoor" | Defined in roadmap §1.3 | No content |
| Play loop voice integration | Defined in roadmap §2.2 | STT/TTS adapters exist but not wired into turn cycle as primary input |
| Session Zero flow | Defined in roadmap §2.4, MVP spec | No code |
| Discovery Log backend | 764-line contract | Schema only, no backend |
| Non-combat authority model | Research Topic D | No spec, no code |
| Table UI (Three.js) | 80+ concept UX spec | No code |
| WebSocket bridge | Defined in roadmap §3.7 | No code |
| Battle map renderer | Defined as scroll on table | No code |
| Notebook (3D book) | Defined in UX spec | No code |
| Dice bag + tower | Defined in UX spec | No code |
| Crystal ball (DM presence) | Defined in UX spec | No code |
| Character sheet (table object) | Defined in UX spec | Display only, not table object |
| Handout system | Defined in UX spec | No code |
| Rulebook (table object) | Defined in UX spec §3.6b | No code |
| Asset pool binding runtime | Schema in world_bundle.json | No runtime code |
| Image generation pipeline | prep_pipeline has stub | No real model integration |
| Music/SFX generation | prep_pipeline has stub | No real model integration |
| Vocabulary decoupling | Research Topic E | Glossary not started |
| STM clear-on-transition | Identified in audit Risk #10 | No code |
| Clarification loop max rounds | Identified in audit Risk #4 | No enforcement |

---

## 2. Gap-by-Gap Analysis

### Phase 0: Foundation Alignment

#### GAP-001: AD-007 Presentation Semantics Python Implementation
**Phase:** 0.3
**Classification:** CUSTOM
**What exists:** Ratified AD-007 decision, complete JSON schema (`presentation_semantics_registry.schema.json`), enum definitions for `delivery_mode`, `staging`, `origin_rule`, `scale`
**What's missing:** Frozen Python dataclass, validation logic, tests that enforce Layer B existence, tests that verify Spark respects Layer B constraints
**OSS needed:** None
**Effort profile:** Pure code. Schema→dataclass translation + enforcement tests.
**Blocks:** Everything downstream — world compiler, rulebook, battle map animations, narration constraints

#### GAP-002: Rulebook Object Model
**Phase:** 0.4
**Classification:** CUSTOM
**What exists:** World compiler contract §0.4 references it. `rule_registry.schema.json` defines RuleEntry, RuleParameters, RuleTextSlots, RuleProvenance.
**What's missing:** Python storage format, indexing, query API. How does the runtime look up "show me that fire ability"?
**OSS needed:** None (or sqlite3 from stdlib for indexing if volume warrants it)
**Effort profile:** Medium. Schema exists; need the query layer.
**Blocks:** World compiler (produces rulebook), table UI rulebook object (§3.6b)

#### GAP-003: Vocabulary Decoupling (Phase 0.1)
**Phase:** 0.1
**Classification:** CUSTOM
**What exists:** Research Topic E scoped. Content pack concept defined in world compiler contract.
**What's missing:** Neutral terminology glossary, migration plan for 4,601+ tests, "bone vs skin" audit
**OSS needed:** None
**Effort profile:** Large but mechanical. Rename operations across codebase.
**Blocks:** Content independence (no IP in shipped product), world compiler inputs

---

### Phase 1: World Compile

#### GAP-004: World Compiler Pipeline
**Phase:** 1.1–1.2
**Classification:** CUSTOM + OSS-MODEL (for LLM stage)
**What exists:** 825-line contract, 4 JSON schemas (world_bundle, rule_registry, vocabulary_registry, presentation_semantics_registry), DEC-WORLD-001 ratified, existing prep_orchestrator/prep_pipeline infrastructure
**What's missing:** The actual compile pipeline — stages 0-8: validate → lexicon → rulebook → presentation semantics → NPC archetypes → bestiary → assets → maps → music/SFX
**OSS needed:**
- **llama-cpp-python** (already in project) — LLM inference for lexicon/rulebook/semantics generation
- **diffusers** (Apache-2.0) — Image generation for Stage 6 (portraits, tokens, tiles)
- **audiocraft / musicgen** — Music/SFX generation for Stage 8
**What we build:** The pipeline orchestration, stage sequencing, determinism enforcement (seed → cache → hash → freeze), compile certificate, resume-on-failure, and the prompt engineering for each stage
**Effort profile:** Largest single gap. Contract is thorough; implementation is greenfield.
**Blocks:** MVP World "Ashenmoor" (§1.3), all downstream phases

#### GAP-005: MVP World "Ashenmoor"
**Phase:** 1.3
**Classification:** CUSTOM (content authoring) + OSS-MODEL (generation)
**What exists:** Scope defined in MVP spec: 1 town, 1 shop, 1 encounter area, 3 NPC types, 3 abilities
**What's missing:** Authored content pack input + successful compile run
**OSS needed:** Same as GAP-004 (this is the first compile run)
**Effort profile:** Content authoring + integration testing. Proves the compiler works.
**Blocks:** Phase 2 play loop (needs a world to play in)

---

### Phase 2: Play Loop Integration

#### GAP-006: Voice Pipeline Integration (STT → Intent → Box → Lens → Spark → TTS)
**Phase:** 2.2
**Classification:** OSS-DROP (for audio I/O) + CUSTOM (for wiring)
**What exists:** SessionOrchestrator already wires STT→Intent→Box→Lens→Spark→TTS in code. Whisper STT adapter exists. Kokoro/Chatterbox TTS adapters exist. Turn cycle functional in demo_combat_turn.py and demo_micro_scenario.py.
**What's missing:** Real-time audio capture from browser microphone, streaming TTS playback to browser, push-to-talk / VAD integration, latency optimization
**OSS needed:**
- **sounddevice** (MIT) — Python audio capture/playback (server-side, for local mode)
- **Silero VAD** (MIT) — Voice Activity Detection for utterance boundary detection
- **Web Audio API** — Browser-side audio capture (built into browsers, no library)
- **howler.js** (MIT) — Browser audio playback with format abstraction
**What we build:** WebSocket audio streaming bridge, VAD-triggered utterance segmentation, playback queue management
**Effort profile:** Medium. Components exist; wiring + latency tuning is the work.
**Blocks:** Session Zero flow (§2.4)

#### GAP-007: Discovery Log Backend
**Phase:** 2.3
**Classification:** CUSTOM
**What exists:** 764-line Discovery Log contract, knowledge mask schema + 35 enforcement tests, four-tier progression (HEARD→SEEN→FOUGHT→STUDIED)
**What's missing:** Backend that applies knowledge events to mask state, persists per-player discovery state, connects to bestiary display in notebook
**OSS needed:** None
**Effort profile:** Medium. Contract is thorough; schema/mask logic exists. Need the state machine + persistence layer.
**Blocks:** Notebook bestiary section (§3.2 enrichment)

#### GAP-008: Session Zero Flow
**Phase:** 2.4
**Classification:** CUSTOM + OSS-MODEL (for image gen)
**What exists:** MVP spec defines the full flow: name → notebook cover → character creation → stat rolling → world entry. Campaign schemas (SessionZeroConfig) exist. Voice pipeline exists.
**What's missing:** Conversational flow controller, character substrate construction, stat rolling integration, notebook cover image generation
**OSS needed:**
- **diffusers** (Apache-2.0) — Notebook cover art generation on player description
**What we build:** Conversational state machine for Session Zero, character creation logic, integration with dice tower, image generation trigger
**Effort profile:** Large. Touches voice, image gen, character creation, and the first player-facing interaction.
**Blocks:** MVP acceptance criteria #1 (full loop without crashes)

#### GAP-009: Non-Combat Authority Model
**Phase:** 2.4 (entangled)
**Classification:** CUSTOM
**What exists:** Research Topic D scoped (the "hardest authority problem in the system"). NeedFact/WorldPatch protocol defined in AD-001.
**What's missing:** Scene Fact Authority model (compiled facts / runtime facts / unknowns), NPC conversation authority contract, shop interaction loop, unknown handling policy
**OSS needed:** None
**Effort profile:** Design-heavy. This is the architectural unknown — who owns facts that don't exist until generated?
**Blocks:** Any non-combat interaction in MVP (shop, conversation, exploration)

---

### Phase 3: Table UI Prototype

#### GAP-010: Table Surface + Camera (Three.js)
**Phase:** 3.1
**Classification:** OSS-DROP
**What exists:** UX spec defines layout (player side / DM side), camera behavior (seated angle, stand-up top-down), smooth transitions
**What's missing:** All frontend code
**OSS needed:**
- **Three.js** (MIT) — 3D scene, camera, lighting, materials, post-processing
- **vite** (MIT) — Build tooling, HMR for development
**What we build:** Table surface geometry, camera rig, lighting setup, material system. This is the foundation for all other table objects.
**Effort profile:** Medium. Three.js is well-documented. Core scene is straightforward geometry.
**Blocks:** Every other table object (§3.2–3.8)

#### GAP-011: Notebook (3D Book Object)
**Phase:** 3.2
**Classification:** OSS-DROP (Three.js) + CUSTOM (interaction model)
**What exists:** UX spec defines: 3D book, canvas pages, drawing tools, page flipping, torn pages, bestiary section, transcript section, handout storage
**What's missing:** All frontend code. Book geometry, page turning animation, canvas rendering on 3D surface, drawing tools, radial menu
**OSS needed:**
- **Three.js** (MIT) — 3D book geometry, animation
- **Canvas API** — Drawing/text on page surfaces (built into browsers)
**What we build:** Book open/close mechanics, page flip physics, pen/brush radial menu, canvas-to-texture pipeline, section management (personal/transcript/bestiary/handouts)
**Effort profile:** Large. Most complex table object. Multiple interaction modes.
**Blocks:** Handout system (§3.8), bestiary display, transcript display

#### GAP-012: Dice Bag + Tower
**Phase:** 3.3
**Classification:** OSS-DROP (Three.js) + CUSTOM (cosmetic-over-deterministic)
**What exists:** UX spec defines: bag open/close, tower drop, tray display, cosmetic animation over deterministic RNG. Deterministic RNG engine is fully built (BL-005, BL-006, BL-009).
**What's missing:** All frontend code. Dice mesh, bag container, tower geometry, drop animation, result display tray
**OSS needed:**
- **Three.js** (MIT) — 3D dice geometry, physics animation
- **cannon-es** (MIT) or **Rapier** (Apache-2.0) — Lightweight physics for dice tumble (cosmetic only, result is pre-determined by Box RNG)
**What we build:** Dice mesh generation, tower drop animation that converges on predetermined result, bag UI, tray display
**Effort profile:** Medium. Cosmetic physics over deterministic result is the interesting constraint.
**Blocks:** Nothing critical (dice already resolve server-side)

#### GAP-013: Crystal Ball (DM Presence)
**Phase:** 3.4
**Classification:** OSS-DROP (Three.js) + CUSTOM
**What exists:** UX spec defines: glow-on-speak, NPC portrait display inside, voice emanation. TTS adapters exist. DM persona with NPC voice switching exists.
**What's missing:** Crystal ball mesh, glow shader, portrait-inside-sphere rendering, audio spatialization
**OSS needed:**
- **Three.js** (MIT) — Sphere geometry, custom shaders, post-processing glow
- **Web Audio API** — Spatial audio (built into browsers)
**What we build:** Crystal ball material/shader, portrait rendering inside distorted glass, glow pulse synced to TTS output
**Effort profile:** Medium. Shader work for the glass/glow effect. Portrait display is texture mapping.
**Blocks:** Handout system (§3.8 — DM slides paper from crystal ball area)

#### GAP-014: Battle Map Scroll
**Phase:** 3.5
**Classification:** OSS-DROP (renderer) + CUSTOM (fog of war, tokens, stencils)
**What exists:** UX spec defines: 2D scroll surface on DM side, fog of war, token display, AoE stencil overlays, tile swap for terrain changes. Grid combat engine is fully built.
**What's missing:** All frontend rendering. Scroll unroll animation, grid rendering, token placement, fog of war mask, AoE stencil visualization, tile swap animation
**OSS needed:**
- **Pixi.js** (MIT) — 2D grid rendering on canvas texture (applied to scroll surface in Three.js scene)
  OR render directly in Three.js with sprite batching
- **Three.js** (MIT) — Scroll geometry, unroll animation
**What we build:** Grid renderer, token sprites from asset pool, fog of war shader, stencil overlays from presentation semantics (AD-007 vfx_tags), tile swap system
**Effort profile:** Large. Most mechanically complex table object — connects to Box state, presentation semantics, asset pools.
**Blocks:** MVP acceptance criteria #8 (dice map to backend RNG), #9 (all state changes in event log)

#### GAP-015: Character Sheet (Table Paper Object)
**Phase:** 3.6
**Classification:** OSS-DROP (Three.js) + CUSTOM
**What exists:** 14.5K line character_sheet.py display component (data layer). UX spec defines: read-only paper, system-populated, spell/ability click triggers
**What's missing:** Rendering as a 3D paper object on the table, data binding to box state, click-to-trigger ability integration
**OSS needed:**
- **Three.js** (MIT) — Paper geometry, texture
- **Canvas API** — Render sheet data to texture
**What we build:** Paper mesh, canvas rendering of character data, click event routing to intent bridge
**Effort profile:** Small-Medium. Data layer exists; rendering is the gap.
**Blocks:** MVP (player needs to see their stats)

#### GAP-016: WebSocket Bridge
**Phase:** 3.7
**Classification:** OSS-DROP
**What exists:** Starlette identified as web framework. Session orchestrator handles the server-side turn cycle.
**What's missing:** WebSocket server, message protocol, state sync, audio streaming, event push
**OSS needed:**
- **Starlette** (BSD-3) — WebSocket server, ASGI lifecycle
- **uvicorn** (BSD-3) — ASGI server
- **msgpack** (Apache-2.0, already in deps) — Binary message serialization
**What we build:** Message protocol schema (turn events, state deltas, audio chunks, asset URLs), connection lifecycle, reconnection handling
**Effort profile:** Medium. Standard WebSocket architecture but message protocol needs design.
**Blocks:** Any browser ↔ server communication

#### GAP-017: Handout System
**Phase:** 3.8
**Classification:** CUSTOM
**What exists:** UX spec defines: DM-to-player paper objects, pick up, store in notebook, discard. Paper slides across table from DM side.
**What's missing:** All code. Paper object creation, slide animation, pickup interaction, notebook insertion
**OSS needed:**
- **Three.js** (MIT) — Paper geometry, slide animation
**What we build:** Handout content rendering (shop menus, loot lists, letters), slide animation from crystal ball area to player side, pickup/store/discard interaction
**Effort profile:** Medium. Depends on notebook (§3.2) and crystal ball (§3.4).
**Blocks:** MVP shop interaction (menu as handout)

#### GAP-018: Rulebook Table Object
**Phase:** 3.6b
**Classification:** CUSTOM
**What exists:** AD-007 defines Layer A + B → rulebook entries. Schema exists (rule_registry.schema.json).
**What's missing:** 3D book object on table, page lookup, AI-navigable query, bookmark system. Generated from world compiler output.
**OSS needed:**
- **Three.js** (MIT) — Book geometry (similar to notebook)
**What we build:** Book rendering, page navigation, search/query interface connected to rulebook object model (GAP-002)
**Effort profile:** Medium. Similar to notebook geometry but simpler (read-only, no drawing tools). Query integration is the novel work.
**Blocks:** MVP acceptance criteria #4 (stable rulebook entries)

---

### Phase 4: MVP Integration

#### GAP-019: Image Generation Pipeline
**Phase:** 4.2 (but needed by 1.2 for world compile, and 2.4 for session zero)
**Classification:** OSS-MODEL
**What exists:** prep_pipeline.py has stub mode for image generation. AssetCategory schema with `generation_prompt_template`. Asset pool binding rules in world_bundle.schema.json. VoicePersona, ImageRequest/ImageResult schemas in aidm/schemas/immersion.py.
**What's missing:** Real model loading, inference pipeline, prompt construction from presentation semantics, output validation, pool management, binding enforcement
**OSS needed:**
- **diffusers** (Apache-2.0, Hugging Face) — Inference pipeline for SD/SDXL/FLUX models
- **Stable Diffusion 1.5** or **SDXL** (CreativeML Open RAIL-M / SDXL-1.0 license) — Base model
  - SD 1.5: ~2GB VRAM, fits median hardware budget
  - SDXL: ~6GB VRAM, higher quality, tight on median budget
- **FLUX.1-dev** (non-commercial) or **FLUX.1-schnell** (Apache-2.0) — Latest architecture, best quality
  - FLUX.1-schnell: Apache-2.0, ~12GB VRAM (above median budget, possible with quantization)
- **transformers** (Apache-2.0, already in project) — Tokenizer, model loading
- **safetensors** (Apache-2.0) — Safe model weight loading
**What we build:**
- Prompt construction from AD-007 presentation semantics (vfx_tags + scale + world theme → image prompt)
- Category-aware generation (portraits vs tokens vs tiles vs environments need different prompts/sizes)
- Pool rotation: generate → validate → hash → store → bind-on-use → queue replacement
- Knowledge-level-aware generation for bestiary (silhouette → partial → full)
- Identity preservation across knowledge levels (same creature, increasing detail)
- Hardware-aware model selection (SD 1.5 for 4GB VRAM, SDXL for 6-8GB, FLUX for 12GB+)
- CPU fallback (very slow but functional)
**Effort profile:** Large. Model integration is straightforward (diffusers handles it); prompt engineering and pool management are the custom work.
**Blocks:** World compile Stage 6 (assets), session zero (notebook cover), bestiary images

#### GAP-020: Music/SFX Generation Pipeline
**Phase:** 4.2 (Stage 8 of world compile)
**Classification:** OSS-MODEL
**What exists:** prep_pipeline.py has stub for music/SFX. SceneAudioState schema in immersion.py.
**What's missing:** Real model loading, music generation, SFX generation, scene-aware audio management
**OSS needed:**
- **audiocraft / MusicGen** (MIT) — Meta's music generation model
  - MusicGen-small: ~1.5GB VRAM
  - MusicGen-medium: ~3.5GB VRAM
- **bark** (MIT) — Sound effect generation
- **miniaudio** (MIT/public domain) — Audio playback (server-side)
**What we build:** Scene-to-music-prompt pipeline (ambience tags from scene manager → MusicGen prompt), crossfade/loop management, SFX trigger from event types, compute scheduling (sequential with image gen to fit VRAM budget)
**Effort profile:** Medium. Lower priority than image gen for MVP (MVP spec says "voice only" for audio).
**Note:** MVP explicitly excludes music/ambient audio. This is post-MVP enrichment.
**Blocks:** Nothing for MVP. Enriches post-MVP experience.

#### GAP-021: Asset Pool Binding Runtime
**Phase:** 4.2
**Classification:** CUSTOM
**What exists:** AssetPools schema in world_bundle.schema.json (categories, binding_rules, fallback_policy). AssetRecord in campaign.py with deterministic ID. Research Topic F scoped.
**What's missing:** Runtime binding registry, no-reuse enforcement, pool exhaustion handling, replacement queue, background generation scheduler
**OSS needed:** None
**Effort profile:** Medium. Schema is thorough; need the runtime state machine.
**Blocks:** MVP (each NPC needs unique portrait and voice)

#### GAP-022: End-to-End Integration
**Phase:** 4.1
**Classification:** CUSTOM
**What exists:** All individual components exist (some partially). Session orchestrator wires the server-side loop. Demo scripts prove individual subsystems.
**What's missing:** Browser ↔ server integration, table UI ↔ session orchestrator, asset delivery, state sync, error recovery across the full stack
**OSS needed:** Covered by GAP-016 (WebSocket bridge)
**Effort profile:** Large. Integration is where hidden bugs live.
**Blocks:** MVP acceptance criteria #1 (player completes full loop)

---

### Cross-Cutting Gaps

#### GAP-023: Voice Resolver Completion
**Phase:** 2.1 (parallel)
**Classification:** CUSTOM
**What exists:** Archetype mapping tables (pitch, pace, timbre, accent), VoiceRoster cache, VoicePersona schema. Currently returns default persona.
**What's missing:** Actual LLM voice description parsing. World compiler generates voice descriptions for NPCs; voice resolver must map those to available TTS personas.
**OSS needed:** None (uses existing Spark/LLM infrastructure)
**Effort profile:** Small. Tables exist; need the parsing logic.
**Blocks:** NPC voice distinctiveness in MVP

#### GAP-024: STM Clear-on-Transition
**Phase:** Parallel (bugfix)
**Classification:** CUSTOM
**What exists:** STMContext exists but has no `clear()` or transition-triggered reset.
**What's missing:** Pronoun carryover guard. "Attack him" after room transition should not reference previous room's entity.
**OSS needed:** None
**Effort profile:** Small. Add clear() method + wire to scene transition.
**Blocks:** Nothing critical, but prevents confusing pronoun resolution bugs.

#### GAP-025: Clarification Loop Max Rounds
**Phase:** Parallel (bugfix)
**Classification:** CUSTOM
**What exists:** Clarification loop in aidm/immersion/clarification_loop.py. Contract §4.6 specifies max 3 rounds.
**What's missing:** `max_rounds` parameter, enforcement, RETRACTED state after limit.
**OSS needed:** None
**Effort profile:** Trivial. Add counter, enforce limit.
**Blocks:** Nothing critical, but prevents infinite loops.

#### GAP-026: AoO weapon_data Type Guard
**Phase:** Parallel (bugfix)
**Classification:** CUSTOM
**What exists:** `aidm/core/aoo.py:544` calls `.get()` on weapon_data without isinstance check.
**What's missing:** `if weapon_data is None or not isinstance(weapon_data, dict): continue` guard.
**OSS needed:** None
**Effort profile:** Trivial. One-line fix.
**Blocks:** Nothing (all current tests pass), but latent AttributeError risk.

#### GAP-027: Intent Bridge Candidate Ordering (Delta D-01)
**Phase:** Parallel
**Classification:** CUSTOM
**What exists:** xfail test tracks it. `_resolve_entity_name()` uses dict insertion order, not lexicographic sort.
**What's missing:** `sorted()` call. Contract §2.3 requires lexicographic ordering.
**OSS needed:** None
**Effort profile:** Trivial. Add sorted() call, remove xfail.
**Blocks:** Replay determinism if entity construction order changes.

---

## 3. OSS Dependency Matrix

### OSS-DROP: Install and Wire

These are libraries where the integration work is adapter glue, not novel engineering.

| Library | License | Purpose | Fills Gap(s) | Phase | VRAM | Already in project? |
|---------|---------|---------|-------------|-------|------|---------------------|
| **Three.js** | MIT | 3D table scene, all table objects | 010–018 | 3 | 0 | No |
| **Starlette** | BSD-3 | WebSocket server, HTTP, ASGI | 016 | 3 | 0 | No |
| **uvicorn** | BSD-3 | ASGI server for Starlette | 016 | 3 | 0 | No |
| **Vite** | MIT | Frontend build tooling, HMR | 010 | 3 | 0 | No |
| **howler.js** | MIT | Browser audio playback | 006 | 2 | 0 | No |
| **sounddevice** | MIT | Server-side audio I/O | 006 | 2 | 0 | No |
| **Silero VAD** | MIT | Voice activity detection | 006 | 2 | 0 | No |
| **cannon-es** | MIT | Cosmetic dice physics | 012 | 3 | 0 | No |
| **Rich** | MIT | Terminal output (dev/debug) | — | — | 0 | No |
| **python-tcod** | BSD-2 | Pathfinding (A*, Dijkstra) | — | Mech | 0 | No |
| **msgpack** | Apache-2.0 | Binary serialization | 016 | 3 | 0 | **Yes** |
| **llama-cpp-python** | MIT | LLM inference | 004 | 1 | 2-6GB | **Yes** |

**Count: 12 libraries, 10 new installs**

### OSS-MODEL: Model + Our Pipeline

These provide the ML model but we build everything around it.

| Model/Library | License | Purpose | Fills Gap(s) | Phase | VRAM |
|---------------|---------|---------|-------------|-------|------|
| **diffusers** | Apache-2.0 | SD/SDXL/FLUX inference pipeline | 019 | 1,2,4 | 2-12GB |
| **SD 1.5** | CreativeML Open RAIL-M | Image gen (median hardware) | 019 | 1,2,4 | ~2GB |
| **SDXL** | SDXL-1.0 | Image gen (higher quality) | 019 | 1,2,4 | ~6GB |
| **FLUX.1-schnell** | Apache-2.0 | Image gen (best quality) | 019 | 4+ | ~12GB |
| **MusicGen-small** | MIT | Music generation | 020 | Post-MVP | ~1.5GB |
| **Kokoro ONNX** | Apache-2.0 | TTS (CPU) | DONE | — | 0 |
| **Chatterbox** | Proprietary/Research | TTS (GPU, voice cloning) | DONE | — | ~6GB |
| **faster-whisper** | MIT | STT | DONE | — | 1-3GB |

**Count: 8 model families, 5 new (3 already integrated)**

---

## 4. Decision Matrix

### What Can Be Filled Without Custom Code

| # | Gap | Fill Strategy | Decision Needed |
|---|-----|---------------|-----------------|
| 1 | Table scene foundation | Three.js (MIT) — install, scene setup | **Adopt** |
| 2 | Web server | Starlette + uvicorn — install, route setup | **Adopt** |
| 3 | Frontend build | Vite — install, config | **Adopt** |
| 4 | Browser audio | howler.js — install, wire to WebSocket | **Adopt** |
| 5 | Server audio I/O | sounddevice — install, wire to STT | **Adopt** |
| 6 | VAD | Silero VAD — install, wire to utterance segmenter | **Adopt** |
| 7 | Dice physics (cosmetic) | cannon-es or Rapier — install, cosmetic sim | **Adopt** |
| 8 | Binary messages | msgpack (already installed) | **Done** |
| 9 | Pathfinding | python-tcod — install, wire to movement resolver | **Adopt when needed** |

**Total OSS-DROP gaps: 9 (7 new installs, 1 already done, 1 deferred)**

### What Needs OSS Models + Custom Pipeline

| # | Gap | Model | Pipeline We Build |
|---|-----|-------|-------------------|
| 1 | Portraits/tokens/tiles | SD 1.5 → SDXL → FLUX via diffusers | Prompt construction from AD-007, pool rotation, knowledge-level rendering, identity preservation |
| 2 | Notebook cover art | Same as above | Session zero trigger, player description → prompt |
| 3 | Music/ambience | MusicGen via audiocraft | Scene → prompt, loop/crossfade, compute scheduling (POST-MVP) |
| 4 | World compile text gen | llama.cpp (already integrated) | Lexicon/rulebook/semantics generation stages, determinism enforcement |

**Total OSS-MODEL gaps: 4 (1 already integrated, 2 new model families, 1 post-MVP)**

### What Must Be Built From Scratch

| # | Gap | Why No OSS Shortcut |
|---|-----|---------------------|
| 1 | AD-007 dataclass + enforcement | Project-specific architectural contract |
| 2 | Rulebook object model | Project-specific query/display model |
| 3 | Vocabulary decoupling | Project-specific codebase migration |
| 4 | World compiler pipeline | Project-specific 8-stage compilation |
| 5 | MVP world "Ashenmoor" | Content authoring |
| 6 | Session Zero flow | Project-specific conversational state machine |
| 7 | Non-combat authority model | Novel architectural design (hardest problem) |
| 8 | Discovery Log backend | Project-specific state machine |
| 9 | Notebook interaction model | Novel 3D book interaction (not just Three.js geometry) |
| 10 | Battle map integration | Connects Box state to visual rendering |
| 11 | Crystal ball shader/behavior | Custom shader + audio sync |
| 12 | WebSocket message protocol | Project-specific event schema |
| 13 | Handout system | Project-specific paper object lifecycle |
| 14 | Asset pool binding runtime | Project-specific state machine |
| 15 | Voice resolver parsing | Project-specific NLP → persona mapping |
| 16 | End-to-end integration | Wiring everything together |

**Total CUSTOM gaps: 16**

---

## 5. Summary Scorecard

| Category | Count | Effort Profile |
|----------|-------|---------------|
| **DONE** (built, tested, shipping) | 28 major systems | — |
| **PARTIAL** (code exists, needs completion) | 3 systems | Small each |
| **OSS-DROP** (install + wire) | 9 gaps | Small-Medium each |
| **OSS-MODEL** (model + custom pipeline) | 4 gaps | Medium-Large each |
| **CUSTOM** (design + build from scratch) | 16 gaps | Small to Large |
| **Bugfix** (known issues, trivial) | 4 items | Trivial each |

### Ratio

- **~48% of MVP is already built** (28 of ~59 major components)
- **~15% can be filled by dropping in OSS** (9 gaps)
- **~7% needs OSS models + custom pipeline** (4 gaps, 1 post-MVP)
- **~27% must be built from scratch** (16 gaps)
- **~3% is trivial bugfixes** (4 items)

### Critical Path (shortest route to MVP)

```
GAP-001 (AD-007 dataclass)
  → GAP-002 (Rulebook model)
    → GAP-004 (World compiler)
      → GAP-005 (Ashenmoor)
        → GAP-019 (Image gen — at least stub/SD 1.5)
          → GAP-006 (Voice pipeline wiring)
            → GAP-009 (Non-combat authority — minimum)
              → GAP-008 (Session Zero)
                → GAP-010 (Table surface)
                  → GAP-016 (WebSocket bridge)
                    → GAP-014 (Battle map)
                      → GAP-013 (Crystal ball)
                        → GAP-015 (Character sheet)
                          → GAP-012 (Dice)
                            → GAP-022 (Integration)
```

**Items that can proceed in parallel with the critical path:**
- GAP-003 (Vocabulary decoupling) — parallel track
- GAP-007 (Discovery Log) — parallel after GAP-004
- GAP-011 (Notebook) — parallel after GAP-010
- GAP-017 (Handouts) — parallel after GAP-011 + GAP-013
- GAP-021 (Asset pool runtime) — parallel after GAP-019
- GAP-023–027 (cross-cutting fixes) — any time

---

## 6. Immediate Next Actions

1. **Ratify this document** — PO reviews gap classifications and priorities
2. **Run research sweep on image generation models** — Quantified comparison of SD 1.5 vs SDXL vs FLUX on median hardware (6-8GB VRAM), quality vs speed vs VRAM tradeoffs, license implications
3. **Begin GAP-001** — Implement AD-007 Presentation Semantics Python dataclass + enforcement tests. This unblocks the entire critical path.
4. **Begin GAP-024–027** — Trivial bugfixes that can be knocked out immediately
5. **Revise OSS_SHORTLIST.md** — Upgrade Three.js from "Skip" to "Adopt", downgrade static art packs, add image/music generation bucket

---

*This document is a snapshot. It will be updated as gaps are filled and new information emerges from research sprints.*

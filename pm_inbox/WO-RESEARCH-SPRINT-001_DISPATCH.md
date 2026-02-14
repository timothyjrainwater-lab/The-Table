# WO-RESEARCH-SPRINT-001: Critical Path Research Sprint — Bone-to-Skin Pipeline

**From:** Builder (Opus 4.6, post-preflight context) + Operator review
**To:** PM (Aegis)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Status:** READY for PM review and dispatch
**Scope:** Research only — no code changes. Produces findings documents with architectural recommendations.

---

## Context

The bone-layer verification is complete. 338 formulas verified, 30 WRONG fixed, 28 AMBIGUOUS resolved, RED block lifted. The deterministic engine — the referee — is proven.

The next mountain is the **bone-to-skin pipeline**: taking verified mechanical procedures and generating a complete, evocative, content-independent player experience. This is where the product thesis ("creative in voice, strict in truth") either delivers or doesn't.

This research sprint identifies and investigates the critical difficulties standing between the verified engine and a shippable product. Each research question targets a specific gap where the architecture is sound but the implementation path is unclear or untested.

**Origin:** Initial draft by builder (Opus 4.6) from post-preflight inspection context. Operator provided a 3rd-party auditor framing that expanded scope in three key areas: (1) runtime content validation and player-facing trust, (2) dynamic skin-swapping as a live operation not just recompilation, (3) bone-layer versioning and patch management for existing worlds. Sprint structure revised to integrate both perspectives.

---

## Strategic Frame: What's Actually Hard

The project has three layers (bone/muscle/skin) and four architectural tiers (Box/Lens/Spark/Immersion). The bone and muscle are verified. The difficulties ahead cluster into **eight areas**, organized by the pipeline stage they affect:

### Generation Quality (Compile Time)
1. **World Compiler Output Quality** — Can the compile pipeline produce presentation semantics and rulebook language that feels *authored* rather than *generated*?
2. **Rulebook Generation** — Can a generated manual teach a player how to play without ever referencing the donor system?

### Mechanical Integrity (Foundation)
3. **IP Extraction Completeness** — When D&D vocabulary is stripped, do any bones or muscles break? Are there hidden IP dependencies in the procedural layer?
4. **Bone-Layer Versioning** — When the engine is patched, what happens to existing worlds compiled against the old bones?

### Runtime Robustness (Play Time)
5. **Skin Consistency Under Play** — Once a world's skin is frozen, does it remain coherent across sessions, edge cases, and unexpected player actions?
6. **Spark Constraint Enforcement** — Can the narration layer be creative without ever asserting mechanical truth or contradicting frozen presentation semantics?
7. **Content Validation and Player Trust** — Can the player verify that what they see matches the underlying mechanics? Is the generation process auditable?

### Player Experience (Product Layer)
8. **Voice Pipeline Reliability** — Can the STT→Intent→Box→Narration→TTS loop run at conversational pace with acceptable quality?
9. **Dynamic Skin-Swapping** — Can a player change world themes without recompiling from scratch or losing play history?
10. **World Customization Interface** — What does the player actually interact with when defining their world?
11. **Community Mechanical Literacy** — How do players discuss shared mechanics when they have different words for everything?

### Product Longevity (Infrastructure)
12. **Component Modularity and Hardware Sensitivity** — Can every AI component be swapped for a better version without architectural changes? Can the system sense hardware and auto-select the best tier per component?

---

## Research Questions

---

### RQ-SPRINT-001: IP Extraction Audit — Hidden Dependencies in Bone and Muscle

**Problem:** The bone layer was verified against D&D 3.5e SRD. When IP is stripped, we need confidence that no mechanical procedures depend on D&D-specific concepts that can't be generalized. For example: does the condition system assume D&D-specific condition names? Do feat prerequisites reference D&D class names? Does the XP table only make sense in D&D progression curves?

**Scope:**
- Audit all `aidm/core/` modules for hardcoded D&D terminology in *mechanical* logic (not comments/docstrings)
- Audit all `aidm/schemas/` for field values, enum members, or validation rules that assume D&D-specific content
- Classify each dependency as: (a) already abstracted via content pack, (b) needs extraction to content pack, (c) structural — requires architectural change
- Special attention to: condition names in `conditions.py`, class names in `leveling.py`, spell school names in `spell_resolver.py`, creature type names in content pack schemas
- Cross-reference against RQ-PRODUCT-001 extraction surface audit (10 files flagged, 15 clean)

**Deliverable:** `docs/research/RQ-SPRINT-001_IP_EXTRACTION_AUDIT.md` — Dependency matrix with classification and extraction path for each item.

**Key question:** After extraction, does any bone or muscle module need to *know* what game system it's running?

---

### RQ-SPRINT-002: Skin Quality Assurance — Presentation Semantics Generation

**Problem:** AD-007 defines the three-layer description model (Behavior / Presentation Semantics / Narration). The world compiler must generate Layer B — frozen presentation semantics — for every ability, creature, and item in the world. This is the keystone: if Layer B output is low quality, the rulebook reads like slop, the battle map effects feel generic, and the discovery log loses its wonder. The output must feel *authored* — internally consistent, thematically resonant, and learnable by the player.

**Scope:**
- **Quality Criteria**: Define measurable standards for generated presentation semantics:
  - Consistency: same delivery_mode family across similar abilities within a world
  - Distinctiveness: abilities feel different from each other within a world
  - Learnability: player can predict behavior from description after seeing 3-5 examples
  - Evocativeness: descriptions create mental imagery, feel lived-in and contextually rich
  - Tonal coherence: all generated content maintains the world's theme and mood
- **Prototype Evaluation**: Take 10 mechanical abilities from the bone layer (ranged touch attack, area burst, melee full attack, save-or-suck, buff, healing, condition application, movement effect, environmental hazard, progression milestone) and author Layer B for 3 world themes (fantasy, sci-fi, horror)
- **Generation Strategy**: Identify which Layer B fields are trivially derivable from bone-layer mechanics (e.g., `delivery_mode` from spell targeting type) vs. which require genuine creative generation (e.g., `vfx_tags`, `ui_description`, world-specific names)
- **NLG Research**: Investigate natural language generation techniques for producing presentation text that doesn't read as machine-generated — sentence variety, contextual phrasing, tonal control
- **Template vs. LLM vs. Hybrid**: Assess whether template-based generation can produce acceptable Layer B, or whether LLM generation at compile time is required. If hybrid, define the boundary (what's templated, what's generated)
- **MVP Minimum**: Define the minimum Layer B field set required for MVP (per MVP_SESSION_ZERO_TO_ONE_COMBAT.md: 3 abilities with frozen presentation semantics)

**Deliverable:** `docs/research/RQ-SPRINT-002_SKIN_QUALITY_ASSURANCE.md` — Quality criteria framework, 3-theme prototype with evaluation, NLG technique assessment, generation strategy recommendation, MVP minimum spec.

**Key question:** What is the minimum viable Layer B that makes a world feel authored, not generated?

---

### RQ-SPRINT-003: Skin Coherence Under Stress — Cross-Session Consistency

**Problem:** A world's skin is frozen at compile time. But play is dynamic. When a player does something unexpected — using an ability in a novel context, combining effects the compiler didn't anticipate, encountering an edge case in the bone layer — the skin must remain coherent. The frozen presentation semantics must be sufficient to generate consistent narration for *any* valid mechanical outcome, not just the ones anticipated at compile time. Across multiple sessions, the narrative voice, theme, and tone must remain stable.

**Scope:**
- Enumerate all mechanical event types that require narration (~30 in box_events.py)
- For each event type, identify what Layer B information is needed to narrate it coherently in any skin
- **Stress test**: Take a frozen Layer B for one world theme and attempt to narrate 20 edge-case scenarios (e.g., critical hit with concealment miss, AoO during forced movement into a hazard, sneak attack on a flanked grappled target, spell save with cover bonus, defeat during counter-trip)
- **Cross-session drift**: Simulate 5 consecutive sessions within one world — does the Spark output remain tonally and thematically consistent with the frozen Layer B, or does it drift?
- **Procedural consistency**: For mechanically identical situations occurring in different sessions, does the narration remain internally consistent? (Same ability should always be described with the same delivery mode, staging, and visual character)
- Identify gaps: which edge cases produce narration that contradicts or cannot reference the frozen Layer B?
- Assess: does the current NarrativeBrief schema carry enough Layer B data for Spark to narrate consistently?

**Deliverable:** `docs/research/RQ-SPRINT-003_SKIN_COHERENCE_STRESS_TEST.md` — Edge case matrix, cross-session drift analysis, gap analysis, NarrativeBrief schema extension recommendations.

**Key question:** What breaks first when a frozen skin meets an unforeseen mechanical interaction?

---

### RQ-SPRINT-004: Spark Containment — Narration Quality vs. Authority Bleed

**Problem:** The Spark layer must be creative without asserting mechanical truth. Existing defenses: GrammarShield, ContradictionChecker (250+ keywords), kill switch registry (5 regex patterns), typed call contract (6 CallTypes), boundary pressure detection (GREEN/YELLOW/RED). But these defenses are currently anchored to D&D vocabulary. In a content-independent world, the forbidden terms change with every world compilation. The containment system must evolve from a static blocklist to a world-aware validation layer.

**Scope:**
- Inventory all existing Spark containment mechanisms and their coverage
- Identify the gap between current containment (forbids D&D terms, entity IDs, raw numbers) and content-independent containment (forbids *any* mechanical assertion regardless of vocabulary)
- **World-aware containment design**: How does the ContradictionChecker evolve when vocabulary is world-specific? Should the world compiler generate a per-world forbidden claims list at compile time?
- Assess: does the typed call contract need world-specific forbidden claim lists?
- **Prototype**: Take 5 NarrativeBriefs from existing test fixtures, skin them with a non-D&D world theme, run through the narration pipeline, document every containment failure
- **Content validation pipeline**: Design a system where generated narration can be validated against the frozen Layer B — not just forbidden content scanning, but *positive* validation that the narration is consistent with the declared presentation semantics

**Deliverable:** `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` — Containment mechanism inventory, gap analysis, world-aware containment generation spec, content validation pipeline design, prototype failure log.

**Key question:** When D&D vocabulary is gone, what does the containment layer anchor to?

---

### RQ-SPRINT-005: Content Verification and Player Trust

**Problem:** The No Opaque DM doctrine requires that every outcome traces to RAW or House Policy. This extends to the skin layer: the player must be able to trust that the content they see (rulebook entries, narration, ability descriptions) accurately represents the underlying mechanics. If "Void Lance" says it "always finds its mark," the bone layer must actually implement auto-hit. The audit trail must flow all the way through to the player.

**Scope:**
- **Compile-time validation**: Design checks that verify every generated Layer B entry is mechanically accurate against its bone-layer procedure. For example: if the bone says "ranged touch attack," the skin cannot describe it as an area effect
- **Runtime validation**: Design a system where narration output can be spot-checked against the mechanical events that produced it. If the Box says "hit for 7 damage," the Spark cannot narrate a miss
- **Player-facing auditability**: How can a player inspect the relationship between what they see (skin) and what happened (bone)? Options: event log viewer, "why did that happen?" query, mechanical replay with skin stripped
- **Transparency without breaking immersion**: The player should be *able* to verify, not *forced* to. The audit capability must exist without cluttering the play experience
- **Traceability spec**: Define provenance requirements for generated content — every rulebook entry traces to a bone-layer procedure ID, every narration traces to a Box event sequence

**Deliverable:** `docs/research/RQ-SPRINT-005_CONTENT_TRUST_VERIFICATION.md` — Compile-time validation spec, runtime validation design, player-facing audit UX concepts, traceability requirements.

**Key question:** How does the No Opaque DM doctrine extend through the skin layer to the player?

---

### RQ-SPRINT-006: Rulebook Generation — Player-Facing Documentation Quality

**Problem:** Each world generates its own rulebook at compile time. This rulebook is the player's reference — the equivalent of the PHB for their world. It must explain abilities, conditions, combat procedures, and progression in the world's own vocabulary. This is fundamentally different from narration (ephemeral, varied) — the rulebook must be stable, precise, and learnable. A player should be able to read their rulebook entry for "Void Lance" and understand exactly what it does mechanically, described in their world's language.

**Scope:**
- Define rulebook entry structure: what fields does a player-facing ability entry need? (Name, description, mechanical summary in world language, usage constraints, interaction notes)
- Assess the existing rulebook object model (WO-RULEBOOK-MODEL-001, `aidm/schemas/rulebook.py`, `aidm/lens/rulebook_registry.py`) — is the schema sufficient for generated content, or was it designed for static D&D entries?
- Prototype: generate 5 rulebook entries for abilities across 2 world themes. Evaluate: can a player understand the mechanical behavior from the description alone? Does it feel like a real game manual?
- Identify: which parts of a rulebook entry can be deterministically derived from bone-layer mechanics + Layer B semantics (most of it), and which require creative generation (flavor text, thematic framing)?
- Cross-reference with discovery log progressive revelation — rulebook entries must be revealable incrementally as player discovers abilities

**Deliverable:** `docs/research/RQ-SPRINT-006_RULEBOOK_GENERATION_QUALITY.md` — Entry structure spec, schema gap analysis, 2-theme prototype with player comprehension assessment, generation pipeline recommendation.

**Key question:** Can a generated rulebook teach a player how to play without ever referencing the donor system?

---

### RQ-SPRINT-007: Bone-Layer Versioning — Patch Management for Living Worlds

**Problem:** The bone layer will continue to receive fixes and improvements. The recent verification pass found 30 WRONG verdicts and applied 13 fix WOs. Future play will reveal more. But worlds are compiled against a specific bone-layer version. When the engine is patched, existing worlds face a compatibility question: does the skin survive a bone update? Do save states remain valid? Can a player's campaign continue after an engine patch?

**Scope:**
- **Version contract**: Define what a bone-layer version includes (procedure definitions, schema versions, parameter ranges, event type catalog). What's the minimum metadata a world bundle needs to declare its bone-layer dependency?
- **Compatibility classification**: Categorize bone-layer changes into: (a) backward-compatible (bug fix that doesn't change valid outcomes), (b) behavior-changing (different outcomes for same inputs), (c) schema-breaking (new fields, removed events, changed types)
- **World bundle migration**: For each change category, define the migration path. Can type (a) changes be applied without recompilation? Does type (b) require world recompile? Does type (c) require world recompile + content regeneration?
- **Save state continuity**: When an engine patch lands, can in-progress campaigns continue? Event sourcing and replay should help here — can the replay runner detect version mismatches and handle them?
- **Rollback strategy**: If a patch breaks a world, can the player roll back to a previous engine version for that world while using the new version for new worlds?

**Deliverable:** `docs/research/RQ-SPRINT-007_BONE_VERSIONING.md` — Version contract spec, compatibility classification framework, migration path for each category, save state continuity analysis, rollback design.

**Key question:** When the bones change, what happens to the worlds built on top of them?

---

### RQ-SPRINT-008: Dynamic Skin-Swapping — Live World Theme Transitions

**Problem:** The current architecture freezes skin at compile time. But the product vision includes a player who can choose a sci-fi adventure one day and a horror theme the next — potentially with the same character progression and mechanical state. This is harder than "compile two worlds" — it's "re-skin a live mechanical state while preserving event history, save data, and player context."

**Scope:**
- **Feasibility assessment**: Is dynamic skin-swapping architecturally possible given event sourcing? Events are recorded with bone-layer IDs, not skin vocabulary. Can events be replayed through a different skin without loss?
- **State preservation**: What mechanical state must survive a skin swap? (HP, conditions, inventory, progression, combat state, position) What skin-specific state is lost? (NPC names, ability names, narration history, presentation semantics references in the log)
- **Transition UX**: What does the player experience during a skin swap? Instant? Loading screen with "world compiling"? Gradual (elements change over a session boundary)?
- **Event sourcing for multi-world**: Can the event log track which skin was active for each event, enabling replay in either skin?
- **Skin customization interface**: What does the player interact with when designing or selecting a skin? Theme picker? Vocabulary editor? Full world compiler parameters? Research accessible, user-friendly approaches that don't require technical knowledge
- **Partial skin swaps**: Can a player modify *parts* of a skin (rename an ability, change a creature's appearance) without full recompilation?

**Deliverable:** `docs/research/RQ-SPRINT-008_DYNAMIC_SKIN_SWAPPING.md` — Feasibility analysis, state preservation matrix, transition UX concepts, event log multi-skin design, customization interface research.

**Key question:** Can you change the flavor of a living world without losing its history?

---

### RQ-SPRINT-009: Voice Loop Latency Budget — Conversational Pace Feasibility

**Problem:** The UX vision specifies voice as primary input. The pipeline is: STT (Whisper) → Intent Parse → Box Resolution → NarrativeBrief → Spark Narration → TTS (Kokoro/Chatterbox). Each stage has latency. Known issues: Chatterbox TTS truncation on >60 words (TD-023), Spark LLM latency unknown for real-world models, STT accuracy on tabletop-specific vocabulary unknown.

**Scope:**
- Profile each pipeline stage individually on target hardware (CPU-only baseline, GPU-optional ceiling)
- Define latency budget allocation per stage (target: 2-4s simple actions, 5-8s complex resolution)
- Identify bottlenecks and mitigation strategies (streaming TTS, pre-generation, parallel pipeline stages)
- Assess: is the template narration path (no LLM) fast enough for conversational pace? If so, is LLM narration a luxury or a requirement?
- Document Chatterbox truncation (TD-023) severity in typical play
- STT accuracy assessment for game-specific vocabulary (ability names, creature names, command keywords)

**Deliverable:** `docs/research/RQ-SPRINT-009_VOICE_LOOP_LATENCY.md` — Per-stage profiling data, latency budget proposal, bottleneck analysis, mitigation recommendations.

**Key question:** Can the voice loop hit conversational pace on consumer hardware?

---

### RQ-SPRINT-010: Community Mechanical Literacy — Cross-World Communication

**Problem:** When players share strategies, builds, and discoveries across different world themes, they need a common language for discussing mechanics. Player A's "Void Lance" and Player B's "Thread of Unmaking" resolve to the same procedure. The community needs tools and conventions for recognizing, discussing, and collaborating around the shared mechanical substrate.

**Scope:**
- **Mechanical fingerprint design**: How does a player recognize that two differently-named abilities share the same bone-layer procedure? Hash of mechanical parameters? Canonical procedure ID? "Ability class" taxonomy?
- **World bundle sharing**: Define the sharing format — what's in a shareable bundle, what's the minimum metadata for community discovery? Privacy boundaries: shareable rulebook vs. spoiler-sensitive campaign content
- **Community vocabulary emergence**: What words will players naturally invent for mechanical concepts? Does the system facilitate this (e.g., displaying procedure IDs alongside skin names) or let it emerge organically?
- **Educational content**: How does the system teach mechanical literacy? In-game discovery log? Cross-world comparison tools? "Mechanical view" toggle that shows bone-layer structure alongside skin?
- **Cross-world communication tools**: Forums, shared build planners, strategy discussions — what infrastructure supports a community centered on mechanics rather than lore?

**Deliverable:** `docs/research/RQ-SPRINT-010_COMMUNITY_MECHANICAL_LITERACY.md` — Mechanical fingerprint spec, bundle sharing design, community vocabulary analysis, educational UX concepts, cross-world tooling recommendations.

**Key question:** How do players build expertise around a system where everyone has different words for everything?

---

### RQ-SPRINT-011: Component Modularity — Swappable AI and Hardware Sensitivity

**Problem:** The system currently has a SPARK_SWAPPABLE invariant and Protocol-based adapters in the immersion layer (STT, TTS, Image). But these are binary: an adapter is present or it's stubbed. The product's longevity depends on a stronger guarantee — that *any* AI component (LLM, STT, TTS, image generation) can be swapped for a newer, better, or more hardware-appropriate version without affecting the bone/muscle/skin layers. As AI technology advances rapidly, the system must absorb improvements without requiring architectural changes or product overhauls. Equally important: the system must sense consumer hardware capabilities and automatically select the best available tier for each component, degrading along a quality gradient rather than a cliff.

**Scope:**
- **Adapter boundary audit**: Inventory all current Protocol-based adapters (STTAdapter, TTSAdapter/TTSProtocol, ImageAdapter, SparkAdapter/LlamacppAdapter). For each, assess: is the interface contract tight enough that a new implementation can be dropped in without changing callers? Are there implicit assumptions about model capabilities, output format, or latency?
- **Swappability gaps**: Identify components that are *not* currently behind a swappable interface but should be. Candidates: RNG implementation, pathfinding algorithm, AoE rasterizer, event log storage backend, NLG engine at compile time
- **Hardware detection and tiering**: Design a hardware capability detection system that profiles the consumer's machine at startup (CPU cores, RAM, GPU presence/VRAM, disk speed) and selects the appropriate tier for each component:
  - **Tier 0 (minimal)**: CPU-only, no GPU, no LLM. Template narration, Kokoro TTS or text-only, no image generation. Full mechanical fidelity preserved.
  - **Tier 1 (standard)**: CPU + modest GPU. Kokoro TTS, Whisper STT, Llamacpp narration with small model. Image generation deferred to prep time.
  - **Tier 2 (full)**: GPU with sufficient VRAM. Chatterbox TTS (voice cloning), real-time image, larger LLM for richer narration.
  - Tiers are per-component, not global — a player might have Tier 2 TTS but Tier 0 image generation
- **Quality gradient design**: For each component, define what the player experience looks like at each tier. The key constraint: the *mechanical* experience must be identical across all tiers. Only the sensory presentation changes. A Tier 0 player and a Tier 2 player rolling the same dice with the same seed must get the same outcomes.
- **Future-proofing contract**: Define the interface contracts such that when a new STT model (e.g., next-gen Whisper), a new TTS engine, or a new LLM becomes available, the integration work is: (a) implement the adapter protocol, (b) register it in the component registry, (c) define its hardware tier requirements. No changes to Box, Lens, Spark boundaries, or any other adapter.
- **Hot-swapping vs. restart**: Can components be swapped during a session (e.g., if GPU becomes available mid-play), or only at session boundaries? What are the implications for determinism if the narration engine changes mid-session?

**Deliverable:** `docs/research/RQ-SPRINT-011_COMPONENT_MODULARITY.md` — Adapter boundary audit, swappability gap analysis, hardware tiering design, quality gradient spec per component, future-proofing interface contract, hot-swap feasibility assessment.

**Key question:** Can the system absorb a generational leap in AI technology with nothing more than a new adapter implementation?

---

## Execution Protocol

### Priority Order

| Priority | RQ | Area | Rationale |
|----------|----|------|-----------|
| P0 | RQ-SPRINT-001 | Foundation | IP extraction must be understood before any skin work begins. Hidden dependencies could invalidate the architecture. |
| P0 | RQ-SPRINT-002 | Generation | Presentation semantics quality gates everything downstream. If Layer B generation doesn't work, nothing else matters. |
| P1 | RQ-SPRINT-003 | Runtime | Skin coherence under stress validates the frozen-at-compile model. Must be tested before committing to world compiler implementation. |
| P1 | RQ-SPRINT-004 | Runtime | Spark containment must evolve for content independence. Current guards are D&D-anchored. |
| P1 | RQ-SPRINT-005 | Trust | Content verification extends No Opaque DM through the skin layer. Architectural implications for compile and runtime. |
| P1 | RQ-SPRINT-006 | Generation | Rulebook is the player's first impression. Quality bar must be defined early. |
| P1 | RQ-SPRINT-007 | Foundation | Patch management affects every world ever compiled. Must be designed before worlds start shipping. |
| P2 | RQ-SPRINT-008 | Experience | Dynamic skin-swapping is a major differentiator but not MVP-blocking. Research now informs bundle schema design. |
| P2 | RQ-SPRINT-009 | Experience | Voice latency is important but solvable with known techniques. Less architectural risk. |
| P2 | RQ-SPRINT-010 | Community | World sharing is a future feature. Research now informs bundle and fingerprint design. |
| P1 | RQ-SPRINT-011 | Foundation | Component modularity is a product longevity guarantee. Must be designed before locking adapter interfaces. |

### Dispatch Model

Each RQ can be dispatched as an independent research WO to a builder agent. No code changes. All deliverables are markdown findings documents in `docs/research/`.

**P0 items** should be dispatched first and can run in parallel.
**P1 items** depend on P0 findings (especially RQ-SPRINT-002 output feeding into RQ-SPRINT-003, -004, -005, and -006). Dispatch after P0 deliverables are reviewed.
**P2 items** can run anytime but benefit from P1 context.

### Success Criteria

The sprint is complete when:
1. All 11 deliverables exist in `docs/research/`
2. Each deliverable contains concrete recommendations (not just analysis)
3. PM has reviewed all findings and produced a synthesis memo identifying:
   - Architectural changes needed (if any)
   - Schema extensions needed (world bundle, NarrativeBrief, event log, rulebook)
   - Quality gates for world compiler implementation
   - Updated MVP scope (if findings change what's feasible)
   - Community/sharing infrastructure requirements
   - Versioning and patch management policy
   - Component modularity and hardware tiering strategy

---

## Relationship to Existing Research

This sprint extends, not duplicates, existing research:

| Existing Artifact | This Sprint Extends It |
|-------------------|----------------------|
| RQ-PRODUCT-001 (content independence) | RQ-SPRINT-001 operationalizes the extraction surface audit |
| AD-007 (presentation semantics) | RQ-SPRINT-002 tests whether the spec produces quality output |
| WORLD_COMPILER.md (contract) | RQ-SPRINT-002, -003, -006, -008 validate the contract against reality |
| RQ_LLM_TYPED_CALL_CONTRACT | RQ-SPRINT-004 extends containment to content-independent worlds |
| RQ_SPARK_BOUNDARY_PRESSURE | RQ-SPRINT-004 tests boundary pressure with real skin data |
| UX_VISION_PHYSICAL_TABLE | RQ-SPRINT-009 profiles the voice loop against the UX north star |
| RQ_NARR_001 (narrative balance) | RQ-SPRINT-003 stress-tests consistency under edge cases |
| No Opaque DM (AD-006) | RQ-SPRINT-005 extends the doctrine through the skin layer |
| Bone-layer verification | RQ-SPRINT-007 addresses what happens when verified bones get patched |
| SPARK_SWAPPABLE_INVARIANT | RQ-SPRINT-011 generalizes swappability from Spark to all AI components |

---

## End of Dispatch
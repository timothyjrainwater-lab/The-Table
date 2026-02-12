# Extraction Register: Secondary Pass Audit — Fine-detail Capture

**Source Document:** `inbox/extracted/Aidm Secondary Pass Audit – Fine-detail Capture & Implementation Checklist.txt`
**Extraction Date:** 2026-02-11
**Extraction Method:** Line-by-line manual extraction
**Extracted By:** Claude Opus 4.6 (agent)
**Total Requirements Extracted:** 82

---

## Preamble / Document Purpose

The source document is a secondary-pass audit over GPT-collaborative design conversations. Its stated purpose is to capture fine-grained details that could be lost between high-level specs, consolidating: micro-requirements, UX nuances, boundary conditions, and implied implementation needs. It is intended to be used as a checklist during planning and ticket writing.

---

## Section 1: Core Architectural Separation (Reconfirmed)

---

**REQ-SPA-001**
- **Source Line(s):** Section 1.1 — "Canonical IDs are the only truth for mechanics."
- **Category:** ARCHITECTURE
- **Requirement Text:** Canonical IDs must be the single authoritative truth source for all mechanical operations. No other identifier type (display name, localized name, alias) may be used for mechanical resolution.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.1 (intent lifecycle — canonical ID resolution is foundational to intent processing)
- **Notes:** Already implemented via `aidm/schemas/canonical_ids.py`. Cross-ref: GAP-POL-02 (entity rename propagation) and GAP-POL-04 (multilingual alias resolution) depend on this.

---

**REQ-SPA-002**
- **Source Line(s):** Section 1.1 — "Presentation (names, descriptions, assets, voice, language) is replaceable."
- **Category:** ARCHITECTURE
- **Requirement Text:** The presentation layer (names, descriptions, assets, voice output, language/locale) must be fully replaceable without affecting mechanical outcomes. All presentation content is ephemeral and re-generable.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.3 (narration), M3.1–M3.15 (entire immersion layer is presentation)
- **Notes:** This is the core mechanics/presentation separation pillar. Cross-ref: M0_MASTER_PLAN.md Architectural Pillars.

---

**REQ-SPA-003**
- **Source Line(s):** Section 1.1 — "Skinning/reskinning is allowed only at presentation level."
- **Category:** ARCHITECTURE
- **Requirement Text:** Skinning and reskinning (visual themes, genre overlays, aesthetic changes) must operate exclusively at the presentation layer. No skin or theme change may alter mechanical resolution, canonical IDs, or rule enforcement.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.1–M3.15 (immersion layer presentation)
- **Notes:** Implies a strict boundary: presentation adapter must not have write access to engine state.

---

**REQ-SPA-004**
- **Source Line(s):** Section 1.2 — "Reskinning is an architectural property."
- **Category:** ARCHITECTURE
- **Requirement Text:** The ability to reskin the experience must be a first-class architectural property — designed into the system structure, not bolted on as an afterthought. The canonical/presentation split must inherently support genre and aesthetic swapping.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.1–M3.15 (immersion layer architecture)
- **Notes:** This means the presentation adapter interface must be generic enough to accept arbitrary aesthetic configurations.

---

**REQ-SPA-005**
- **Source Line(s):** Section 1.2 — "Do not commit publicly to supporting all genres/languages."
- **Category:** CONSTRAINT
- **Requirement Text:** The system must not make public commitments (in UI, documentation, or marketing) to supporting all genres or all languages. Internal architecture may support flexibility, but external messaging must scope to D&D 3.5e.
- **Binding Status:** BINDING
- **Roadmap Mapping:** UNMAPPED (communications/marketing constraint, not a code task)
- **Notes:** This is a scope management and expectation-setting constraint. Prevents feature creep at the public-facing level.

---

**REQ-SPA-006**
- **Source Line(s):** Section 1.2 — "Keep 'infinite flexibility' as internal capability, not a launch promise."
- **Category:** CONSTRAINT
- **Requirement Text:** Infinite flexibility (genre-agnostic, language-agnostic) must remain an internal architectural capability. It must not be surfaced as a user-facing promise or feature. Launch scope is D&D 3.5e, English-first.
- **Binding Status:** BINDING
- **Roadmap Mapping:** UNMAPPED (scope governance, not implementation task)
- **Notes:** Cross-ref: REQ-SPA-005. Together these two form a "scope containment" policy.

---

## Section 2: Generative Asset Strategy (Fine Detail)

---

**REQ-SPA-007**
- **Source Line(s):** Section 2.1 — "Most generation happens during campaign/session prep, not during live play."
- **Category:** ARCHITECTURE
- **Requirement Text:** The primary asset generation phase must be campaign/session preparation. The system must be architected to front-load generative work (images, audio, music, NPC portraits) into prep time, not real-time play.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M2.1–M2.13 (campaign prep pipeline), M3.1–M3.15 (prep pipeline prototype already started)
- **Notes:** Cross-ref: M0_MASTER_PLAN.md "Prep-First Asset Generation" binding pillar. PrepOrchestrator already implements sequential model loading.

---

**REQ-SPA-008**
- **Source Line(s):** Section 2.1 — "Live generation may exist as an optional fallback, but must be bounded."
- **Category:** CONSTRAINT
- **Requirement Text:** If runtime (live play) asset generation is supported, it must be strictly bounded: limited retry counts, timeout caps, and graceful degradation to cached/placeholder assets. Live generation must never block gameplay.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.10 (image gen, audio pipeline runtime integration)
- **Notes:** Cross-ref: REQ-SPA-019 (bounded regeneration loops). "Bounded" means: max retry count, max wall-clock time, fallback to placeholder.

---

**REQ-SPA-009**
- **Source Line(s):** Section 2.2 — "Generated assets must be: archived, tagged, retrievable, reusable across future sessions."
- **Category:** PERSISTENCE
- **Requirement Text:** All generated assets (images, audio, music) must be persisted with the following properties: (a) archived to durable storage, (b) tagged with canonical IDs and semantic metadata, (c) retrievable by canonical ID or semantic query, (d) reusable across future sessions without regeneration.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M2.5–M2.8 (campaign persistence, NPC/location gen), M3.7–M3.10 (audio pipeline persistence)
- **Notes:** This implies an asset registry/catalog keyed to canonical IDs. Cross-ref: REQ-SPA-001 (canonical IDs as truth).

---

**REQ-SPA-010**
- **Source Line(s):** Section 2.2 — "Goal: minimize repeated generation and improve continuity."
- **Category:** PRINCIPLE
- **Requirement Text:** The asset strategy must minimize redundant regeneration. Once an asset is generated and accepted (passes quality gate), it should be reused in all future contexts referencing the same canonical entity. This improves both performance and narrative continuity.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M2.5–M2.8 (campaign prep asset reuse), M3.7–M3.10 (audio reuse)
- **Notes:** Cross-ref: REQ-SPA-009. Implementation implication: asset cache lookup before generation request.

---

**REQ-SPA-011**
- **Source Line(s):** Section 2.3 — "NPCs use static anchor images (generated once, reused)."
- **Category:** VISUAL
- **Requirement Text:** Each NPC must have a single "anchor image" (portrait) generated once during prep. This anchor image is the canonical visual representation and must be reused in all subsequent encounters, dialogues, and references to that NPC.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M2.6 (NPC generation), M3.5–M3.6 (image gen pipeline)
- **Notes:** "Anchor" implies immutability after acceptance. Changes would require explicit regeneration request, not automatic drift.

---

**REQ-SPA-012**
- **Source Line(s):** Section 2.3 — "Scenes use background plates."
- **Category:** VISUAL
- **Requirement Text:** Scene visuals must use pre-generated "background plate" images. Scenes are composed by layering character portraits/sprites over these background plates, not by generating complete scene images at runtime.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M2.7 (location generation), M3.5–M3.6 (image gen pipeline)
- **Notes:** Compositing approach reduces runtime generation load. Cross-ref: REQ-SPA-007 (prep-first).

---

**REQ-SPA-013**
- **Source Line(s):** Section 2.3 — "Runtime presentation is primarily compositing (portrait/sprite over background)."
- **Category:** VISUAL
- **Requirement Text:** Runtime visual presentation must primarily use compositing: overlaying pre-generated portraits or sprites onto pre-generated background plates. Full-scene generation at runtime is not the primary visual strategy.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline, contextual grid)
- **Notes:** Cross-ref: REQ-SPA-011 (anchor images), REQ-SPA-012 (background plates). This is the visual rendering architecture.

---

## Section 3: Image Generation + Critique Gate (Fine Detail)

---

**REQ-SPA-014**
- **Source Line(s):** Section 3.1 — "Image generation must be paired with critique/quality evaluation."
- **Category:** VISUAL
- **Requirement Text:** Every image generation request must be followed by an automated quality evaluation (critique gate). No generated image may be presented to the user or stored as an anchor without passing the critique gate.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline)
- **Notes:** Already partially implemented via `aidm/core/image_critique_adapter.py` and `aidm/schemas/image_critique.py`. Cross-ref: R1_IMAGE_QUALITY_DIMENSIONS.md.

---

**REQ-SPA-015**
- **Source Line(s):** Section 3.1 — "Generation without critique risks unusable outputs."
- **Category:** PRINCIPLE
- **Requirement Text:** Uncritiqued image outputs must be treated as potentially unusable. The system must never bypass the critique gate, even under time pressure or resource constraints. If critique cannot run, the system must fall back to a placeholder rather than display an uncritiqued image.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline)
- **Notes:** This establishes critique as a hard gate, not an optional enhancement. Fallback to placeholder is the safe default.

---

**REQ-SPA-016**
- **Source Line(s):** Section 3.2 — Quality evaluation checklist dimensions
- **Category:** VISUAL
- **Requirement Text:** The image critique gate must evaluate the following dimensions as a structured checklist (not subjective assessment): (a) readability at intended UI size, (b) subject centering/cropping, (c) obvious artifacting (faces/hands/edges), (d) style adherence to campaign tone, (e) match to anchor identity (for NPC portraits — the generated image must resemble the established anchor).
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline, critique model)
- **Notes:** Cross-ref: R1_IMAGE_QUALITY_DIMENSIONS.md for detailed dimension definitions. "Checklists, not vibes" is a design principle — critique must be structured and repeatable.

---

**REQ-SPA-017**
- **Source Line(s):** Section 3.2 — "Quality evaluation should cover: readability at intended UI size"
- **Category:** VISUAL
- **Requirement Text:** The image critique gate must specifically evaluate whether the generated image is readable (details discernible, text legible if present, subject identifiable) at the actual UI display size, not just at generation resolution.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline)
- **Notes:** Implies the critique model needs to know the target display dimensions. A portrait that looks fine at 512x512 may be unreadable at 64x64 thumbnail size.

---

**REQ-SPA-018**
- **Source Line(s):** Section 3.2 — "match to anchor identity (for NPC portraits)"
- **Category:** VISUAL
- **Requirement Text:** When regenerating or generating variant images of an existing NPC, the critique gate must verify visual consistency with the NPC's established anchor image. The new image must be recognizably the same character.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline)
- **Notes:** This requires some form of identity embedding or visual similarity comparison. Cross-ref: REQ-SPA-011 (anchor images).

---

**REQ-SPA-019**
- **Source Line(s):** Section 3.3 — "Bounded attempts (avoid infinite loops)."
- **Category:** CONSTRAINT
- **Requirement Text:** Image regeneration attempts must be bounded by a maximum retry count. The system must not enter infinite generate-critique-reject loops. After exhausting retries, the system must accept the best available result or fall back to a placeholder.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline)
- **Notes:** Cross-ref: REQ-SPA-008 (bounded live generation). Specific retry count TBD but must be configured, not hardcoded.

---

**REQ-SPA-020**
- **Source Line(s):** Section 3.3 — "Heuristics first, critic model second where needed."
- **Category:** ARCHITECTURE
- **Requirement Text:** Image quality evaluation must use a two-tier approach: (1) fast heuristic checks first (aspect ratio, resolution, basic color checks, face detection), (2) more expensive critic model evaluation only if heuristics pass. This reduces compute cost and latency.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline)
- **Notes:** This is an optimization strategy. Heuristics are cheap and fast; critic model (e.g., CLIP-based) is expensive. Fail-fast on heuristics saves GPU time.

---

**REQ-SPA-021**
- **Source Line(s):** Section 3.3 — "Output caching keyed to canonical IDs to prevent drift."
- **Category:** PERSISTENCE
- **Requirement Text:** Accepted image outputs must be cached and keyed to canonical entity IDs. This prevents visual "drift" where the same entity gets different-looking images across sessions. Once an image passes critique and is cached, subsequent requests for the same entity must return the cached version.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline), M2.5 (campaign persistence)
- **Notes:** Cross-ref: REQ-SPA-009 (asset archiving), REQ-SPA-011 (anchor images). Cache invalidation must be explicit, not automatic.

---

## Section 4: Voice Strategy (Fine Detail)

---

**REQ-SPA-022**
- **Source Line(s):** Section 4.1 — "TTS quality is more immersion-critical than STT accuracy."
- **Category:** AUDIO
- **Requirement Text:** In resource allocation and quality trade-off decisions, text-to-speech (TTS) output quality must be prioritized over speech-to-text (STT) input accuracy. The DM's spoken narration (TTS) has more immersion impact than the player's spoken input (STT).
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.1–M3.4 (STT/TTS pipeline)
- **Notes:** This is a resource budgeting priority signal. If GPU/CPU budget is tight, allocate more to TTS quality. Cross-ref: M0_MASTER_PLAN.md hardware baseline.

---

**REQ-SPA-023**
- **Source Line(s):** Section 4.1 — "Output must be natural, expressive, controllable by AIDM."
- **Category:** AUDIO
- **Requirement Text:** TTS output must be: (a) natural-sounding (not robotic), (b) expressive (capable of conveying emotion, tension, excitement appropriate to narrative context), (c) controllable by the AIDM system (the DM persona can adjust pace, tone, emphasis programmatically).
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.1–M3.2 (TTS pipeline)
- **Notes:** "Controllable" implies the TTS engine must accept style/prosody parameters, not just raw text. Cross-ref: Coqui/Piper selection from hardware research.

---

**REQ-SPA-024**
- **Source Line(s):** Section 4.2 — "Use confirmation flows for high-impact commands."
- **Category:** INTERACTION
- **Requirement Text:** When STT recognizes a high-impact player command (e.g., attacking an ally, discarding an item, making an irreversible choice), the system must trigger a confirmation flow before executing. The player must explicitly confirm the interpreted action.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.2 (voice/text input), M3.3–M3.4 (STT pipeline)
- **Notes:** Cross-ref: Safeguard Layer obligations (M0_MASTER_PLAN.md). "High-impact" definition TBD — likely: HP-affecting actions, irreversible choices, alignment-affecting actions.

---

**REQ-SPA-025**
- **Source Line(s):** Section 4.2 — "Support repeat/repair interactions."
- **Category:** INTERACTION
- **Requirement Text:** The STT interaction flow must support repeat and repair patterns: (a) the player can ask the DM to repeat what was said, (b) the player can correct a misheard command ("No, I said 'attack the goblin,' not 'attract the goblin'"), (c) the DM can ask for clarification ("Did you mean X or Y?").
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.2 (voice/text input), M3.3–M3.4 (STT pipeline)
- **Notes:** This is a conversational repair pattern. Cross-ref: REQ-SPA-024 (confirmation flows).

---

**REQ-SPA-026**
- **Source Line(s):** Section 4.2 — "Multilingual input must map through alias tables to canonical IDs."
- **Category:** INTERACTION
- **Requirement Text:** When a player speaks in a non-English language, spoken entity names must be resolved through multilingual alias tables that map to canonical IDs. The system must not attempt to mechanically resolve non-canonical names directly.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.3–M3.4 (STT pipeline), relates to GAP-POL-04
- **Notes:** Cross-ref: REQ-SPA-001 (canonical IDs), GAP-POL-04 (multilingual alias resolution — still UNRESOLVED per M0 plan). This requirement depends on GAP-POL-04 being resolved.

---

**REQ-SPA-027**
- **Source Line(s):** Section 4.3 — "Voice profiles are importable/swappable."
- **Category:** AUDIO
- **Requirement Text:** Voice profiles (TTS voice configurations for the DM persona) must be importable and swappable. Players must be able to change the DM's voice without affecting any mechanical state or narrative continuity.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.1–M3.2 (TTS pipeline)
- **Notes:** Cross-ref: REQ-SPA-002 (presentation is replaceable), REQ-SPA-003 (skinning at presentation level only).

---

**REQ-SPA-028**
- **Source Line(s):** Section 4.3 — "Voice changes do not affect mechanics."
- **Category:** ARCHITECTURE
- **Requirement Text:** Changing a voice profile (DM voice, NPC voice, narration style) must have zero impact on mechanical state. Voice is strictly a presentation-layer concern.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.1–M3.2 (TTS pipeline)
- **Notes:** Cross-ref: REQ-SPA-002, REQ-SPA-003. Enforces mechanics/presentation boundary for voice.

---

**REQ-SPA-029**
- **Source Line(s):** Section 4.3 — "Voice must have text equivalents (accessibility)."
- **Category:** ACCESSIBILITY
- **Requirement Text:** Every piece of voice output (TTS narration, DM speech, NPC dialogue) must have a simultaneous text equivalent available. Users who cannot hear or choose not to use audio must have full access to all content via text.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.3 (narration — text output), M3.1–M3.2 (TTS pipeline — text parity)
- **Notes:** Cross-ref: REQ-SPA-055 (text parity is mandatory), REQ-SPA-056 (no voice-only lock-in). This is a hard accessibility requirement.

---

## Section 5: Sound Generation (Fine Detail)

---

**REQ-SPA-030**
- **Source Line(s):** Section 5.1 — Sound palette categories
- **Category:** AUDIO
- **Requirement Text:** During campaign/session preparation, the system must generate and tag a sound palette containing the following categories: (a) monster vocalizations, (b) weapon impacts, (c) UI stingers (short feedback sounds), (d) ambience loops, (e) music themes organized by mood (exploration, combat, tension).
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.7–M3.10 (audio pipeline, SFX gen, music gen)
- **Notes:** Cross-ref: REQ-SPA-007 (prep-first generation). PrepOrchestrator already has stub slots for Music Gen and SFX Gen.

---

**REQ-SPA-031**
- **Source Line(s):** Section 5.2 — "Runtime should primarily select/mix from palette."
- **Category:** AUDIO
- **Requirement Text:** During live play, the audio system must primarily select and mix from the pre-generated sound palette rather than generating new audio. Runtime audio is a selection/mixing problem, not a generation problem.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.7–M3.10 (audio pipeline runtime)
- **Notes:** Cross-ref: REQ-SPA-007 (prep-first), REQ-SPA-008 (bounded live generation). Audio queue system (`aidm/core/audio_queue.py`) already exists.

---

**REQ-SPA-032**
- **Source Line(s):** Section 5.2 — "Goal: 'produced' feel, not constant live generation."
- **Category:** PRINCIPLE
- **Requirement Text:** The audio experience must feel "produced" — like a crafted soundtrack — rather than obviously procedurally generated in real-time. This means careful selection, smooth transitions, and consistent audio quality, achieved through prep-time generation and runtime mixing.
- **Binding Status:** ASPIRATIONAL
- **Roadmap Mapping:** M3.7–M3.10 (audio pipeline)
- **Notes:** This is a quality target, not a binary pass/fail. Cross-ref: REQ-SPA-031 (select/mix from palette).

---

## Section 6: Memory / Logs / Indexing (Fine Detail)

---

**REQ-SPA-033**
- **Source Line(s):** Section 6.1 — "Truth stored in indexed records; LLM retrieves."
- **Category:** ARCHITECTURE
- **Requirement Text:** Authoritative game truth (entity state, event history, world facts) must be stored in structured, indexed records outside the LLM context window. The LLM must query these records via a retrieval interface rather than holding truth in its context.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.4–M1.6 (indexed memory, entity management)
- **Notes:** Cross-ref: M0_MASTER_PLAN.md Component 5 (Indexed Memory Substrate). R0-DEC-049 validates this architecture. Already referenced by R1_INDEXED_MEMORY_DEFINITION.md.

---

**REQ-SPA-034**
- **Source Line(s):** Section 6.1 — "Minimize context-window stress."
- **Category:** CONSTRAINT
- **Requirement Text:** The system must minimize the amount of persistent state held in the LLM's context window. Context window space must be reserved for the current interaction, not for storing historical records. Indexed memory retrieval is the mechanism for accessing history.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.4–M1.6 (indexed memory architecture)
- **Notes:** Cross-ref: REQ-SPA-033. Hardware constraint: Mistral 7B has limited context. Efficient retrieval is critical.

---

**REQ-SPA-035**
- **Source Line(s):** Section 6.2 — Memory object types
- **Category:** PERSISTENCE
- **Requirement Text:** The indexed memory system must maintain structured records for the following object types: (a) entity cards (NPCs, locations, factions), (b) relationships (between entities), (c) event timeline (chronological record of significant events), (d) open threads/hooks (unresolved plot points, quests), (e) inventory and state (player and NPC equipment, status), (f) consequence explanations (e.g., why an alignment shift occurred, with supporting evidence).
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.4–M1.6 (indexed memory), M2.3–M2.8 (NPC/location/faction gen)
- **Notes:** Cross-ref: R1_INDEXED_MEMORY_DEFINITION.md. Item (f) — consequence explanations — is particularly important for the audit trail and dispute resolution safeguards.

---

**REQ-SPA-036**
- **Source Line(s):** Section 6.3 — "On launch, DM can recap prior sessions."
- **Category:** NARRATIVE
- **Requirement Text:** When the application launches with an existing campaign, the DM must be able to provide a narrative recap of prior sessions. This recap must be generated from indexed memory records, demonstrating that the system accurately remembers what happened.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.3 (narration), M2.2–M2.4 (campaign persistence, session continuity)
- **Notes:** Cross-ref: REQ-SPA-059 (daily launch greeting), REQ-SPA-060 (recap/notes on launch). This is "proof of memory."

---

**REQ-SPA-037**
- **Source Line(s):** Section 6.3 — "DM can reference specific moments (e.g., 'three goblins; arrow hit')."
- **Category:** NARRATIVE
- **Requirement Text:** The DM's session recap must be able to reference specific concrete details from prior sessions — not just vague summaries. Examples: "You fought three goblins and your arrow hit the chieftain" rather than "You fought some monsters."
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.4–M1.6 (indexed memory retrieval precision), M2.2–M2.4 (session recap)
- **Notes:** Cross-ref: REQ-SPA-036. This tests retrieval granularity — the memory system must store event-level detail, not just session-level summaries.

---

**REQ-SPA-038**
- **Source Line(s):** Section 6.3 — "DM can justify consequences using logs."
- **Category:** NARRATIVE
- **Requirement Text:** The DM must be able to explain and justify consequences (e.g., alignment shifts, reputation changes, NPC reactions) by citing specific logged events. "Your alignment shifted because you chose to burn the village in Session 3" — not unexplained changes.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.4–M1.6 (indexed memory), M2.2–M2.4 (campaign persistence)
- **Notes:** Cross-ref: REQ-SPA-035(f) (consequence explanations), Safeguard 3 (audit trail). This is both a narrative feature and a transparency/trust requirement.

---

## Section 7: Onboarding & Session Entry UX (Fine Detail)

---

**REQ-SPA-039**
- **Source Line(s):** Section 7.1 — "Avoid 'click campaign' framing."
- **Category:** UX
- **Requirement Text:** The onboarding experience must not use traditional UI patterns like "click to start campaign" or menu-driven setup. Onboarding must feel like the beginning of gameplay, not like navigating a configuration wizard.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero, onboarding UX)
- **Notes:** Cross-ref: REQ-SPA-040 (DM speaks first). This sets the tone for the entire first-time user experience.

---

**REQ-SPA-040**
- **Source Line(s):** Section 7.1 — "The DM speaks first; onboarding is interactive."
- **Category:** UX
- **Requirement Text:** The onboarding experience must begin with the DM speaking to the player (voice or text). The DM initiates the interaction. Onboarding is a conversation, not a form-fill. The player responds to the DM's prompts rather than navigating UI elements.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero, onboarding UX)
- **Notes:** Cross-ref: REQ-SPA-039. This is the "Session Zero is gameplay" principle.

---

**REQ-SPA-041**
- **Source Line(s):** Section 7.2 — DM Persona Selection flow (first 30 seconds)
- **Category:** UX
- **Requirement Text:** Within the first 30 seconds of the onboarding experience, the following persona selection flow must occur: (1) DM greets the user, (2) DM asks if the user likes this DM style, (3) user can request a different persona, (4) DM confirms the switch ("How about now?"). This flow must be fast enough to feel responsive and not like a loading screen.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero, onboarding UX), M3.1–M3.2 (TTS persona swapping)
- **Notes:** "First 30 seconds" is a tight timing constraint. Cross-ref: REQ-SPA-027 (voice profiles swappable). Implies pre-loaded persona configurations.

---

**REQ-SPA-042**
- **Source Line(s):** Section 7.3 — Player experience calibration questions
- **Category:** UX
- **Requirement Text:** During onboarding, the DM must calibrate to the player's experience level by asking questions such as: "Are you new here or old-school?", "Do you want explanations or just results?", "Do you want to see dice rolls or keep it fast?" The DM must use the answers to tune pacing, verbosity, and teaching level for the rest of the session.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero), M2.1 (player profile)
- **Notes:** This implies a player profile/preferences model that persists and influences narration behavior. Cross-ref: "Aidm Player Modeling & Adaptive Dm Behavior" document in inbox.

---

**REQ-SPA-043**
- **Source Line(s):** Section 7.4 — "Dice and other ritual elements must be: skippable, adjustable, chosen conversationally."
- **Category:** UX
- **Requirement Text:** Ceremonial/ritual game elements (dice rolls, dramatic pauses, cinematic descriptions) must be: (a) skippable — the player can opt out entirely, (b) adjustable — the player can control the level of ceremony, (c) chosen conversationally — preferences set through dialogue with the DM, not through settings menus.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero, preference setting), M1.3 (narration verbosity)
- **Notes:** Cross-ref: REQ-SPA-042 (experience calibration). "Conversationally" means no settings UI for these — the DM asks and remembers.

---

**REQ-SPA-044**
- **Source Line(s):** Section 7.5 — "Dice are ritual: fairness + anticipation."
- **Category:** UX
- **Requirement Text:** Dice rolling must serve two functions: (a) communicate fairness (the player sees that randomness is genuine and unbiased), (b) create anticipation (the moment of rolling builds tension). The dice experience must satisfy both functions.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.11–M1.13 (character sheet UI, dice display)
- **Notes:** Cross-ref: REQ-SPA-045 (visual dice + audio), REQ-SPA-046 (must never misrepresent randomness).

---

**REQ-SPA-045**
- **Source Line(s):** Section 7.5 — "Visual dice + satisfying audio."
- **Category:** UX
- **Requirement Text:** Dice rolling must include: (a) a visual animation of the dice roll, (b) satisfying audio feedback (dice clatter, impact sound). Both visual and audio elements must work together to create a complete ritual experience.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.11–M1.13 (character sheet UI), M3.7–M3.10 (audio pipeline — dice sounds)
- **Notes:** Cross-ref: REQ-SPA-044 (dice as ritual). Audio feedback is part of the UI stingers category from REQ-SPA-030.

---

**REQ-SPA-046**
- **Source Line(s):** Section 7.5 — "Must never misrepresent randomness."
- **Category:** CONSTRAINT
- **Requirement Text:** The dice animation and display must never misrepresent the actual random result. The visual outcome must exactly match the mechanical roll. No "fudging" — the displayed value must be the value used by the engine. Deterministic replay must show the same roll value.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.11–M1.13 (character sheet UI, dice display)
- **Notes:** Cross-ref: REQ-SPA-044. This is a trust requirement. The deterministic engine already produces seeded rolls — the display must faithfully show the seeded value.

---

**REQ-SPA-047**
- **Source Line(s):** Section 7.6 — Dice customization scope
- **Category:** UX
- **Requirement Text:** The DM must offer dice customization options during onboarding: (a) size (big vs small), (b) color, (c) visual effects (sparkles, glow, etc.). These choices are expressive only — they must have zero mechanical impact. Choices must be persisted and changeable later via conversation.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.11–M1.13 (character sheet UI), M1.7–M1.10 (onboarding)
- **Notes:** "Taste of power" — this reveals the system's generative capability early, building engagement. Cross-ref: REQ-SPA-043 (chosen conversationally).

---

**REQ-SPA-048**
- **Source Line(s):** Section 7.6 — "Purpose: reveal generative capability early."
- **Category:** PRINCIPLE
- **Requirement Text:** Dice customization during onboarding serves the strategic purpose of demonstrating the system's generative capabilities to the player early in the experience. This "taste of possibility" reduces abandonment by showing what the system can do before asking the player to invest time.
- **Binding Status:** INFORMATIONAL
- **Roadmap Mapping:** M1.7–M1.10 (onboarding)
- **Notes:** Design rationale, not a functional requirement. Informs prioritization of the dice customization feature within onboarding.

---

**REQ-SPA-049**
- **Source Line(s):** Section 7.7 — Character creation as guided conversation
- **Category:** UX
- **Requirement Text:** Character creation must be a guided conversational experience: (1) DM rolls stats and shows results, (2) player assigns values by expressing intent ("I want to be strong; put my 18 there"), (3) DM explains stats in child-friendly, contextual terms, (4) explanations are optional and adaptive (skipped for experienced players, detailed for new players).
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero, character creation), M1.11–M1.13 (character sheet UI)
- **Notes:** Cross-ref: REQ-SPA-042 (experience calibration determines explanation depth). "Child-friendly" is notable — implies no jargon without context.

---

**REQ-SPA-050**
- **Source Line(s):** Section 7.7 — "Player assigns values by intent ('I want to be strong; put my 18 there')."
- **Category:** INTERACTION
- **Requirement Text:** During stat assignment in character creation, the player must be able to assign stat values by expressing intent in natural language rather than selecting from dropdowns. "I want to be strong" maps to Strength; "put my 18 there" assigns the value. The system must interpret intent and confirm the assignment.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero), M1.2 (voice/text input, intent parsing)
- **Notes:** This requires natural language intent parsing for character creation context. Cross-ref: REQ-SPA-025 (repeat/repair for misinterpretation).

---

**REQ-SPA-051**
- **Source Line(s):** Section 7.7 — "Explanations are optional and adaptive."
- **Category:** UX
- **Requirement Text:** Stat explanations during character creation must be adaptive: automatically provided for new players, automatically suppressed for experienced players, and overridable by explicit player request ("explain that" or "skip the explanations").
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero), M1.3 (narration verbosity control)
- **Notes:** Cross-ref: REQ-SPA-042 (player experience calibration drives this). The player profile must store experience level.

---

**REQ-SPA-052**
- **Source Line(s):** Section 7.8 — "DM sets expectation for prep time (e.g., ~1 hour)."
- **Category:** UX
- **Requirement Text:** After session zero completes and before campaign prep begins, the DM must explicitly set the player's expectation for how long prep will take (e.g., "I need about an hour to prepare your adventure"). This is a transparent handoff, not a silent loading screen.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M2.1–M2.4 (session zero to prep handoff)
- **Notes:** Cross-ref: REQ-SPA-053 (user understands why and feels excited). The prep time estimate should be dynamic based on campaign complexity and hardware capability.

---

**REQ-SPA-053**
- **Source Line(s):** Section 7.8 — "This is a clean handoff: user understands why and feels excited."
- **Category:** UX
- **Requirement Text:** The session-zero-to-prep handoff must achieve two goals: (a) the user understands WHY there is a waiting period (the DM is preparing a custom adventure), (b) the user feels EXCITED about what is being prepared, not frustrated by a delay.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M2.1–M2.4 (session zero to prep handoff)
- **Notes:** Cross-ref: REQ-SPA-052. This is an emotional design requirement — the handoff is a promise, not an apology.

---

**REQ-SPA-054**
- **Source Line(s):** Section 7.8 — "The 'taste of possibility' (voice/image/dice) reduces abandonment."
- **Category:** PRINCIPLE
- **Requirement Text:** Before the prep phase begins, the onboarding experience must have already demonstrated enough of the system's capabilities (voice persona, image generation, dice customization) that the player is willing to wait through prep time. Early capability demonstration is an anti-abandonment strategy.
- **Binding Status:** ASPIRATIONAL
- **Roadmap Mapping:** M1.7–M1.10 (onboarding), M2.1 (session zero)
- **Notes:** Cross-ref: REQ-SPA-048 (reveal generative capability early). This justifies front-loading the persona demo, dice customization, and at least one generated image into the onboarding flow.

---

## Section 8: Accessibility & Inclusive Design (Fine Detail)

---

**REQ-SPA-055**
- **Source Line(s):** Section 8.1 — "Text input/output must always be available."
- **Category:** ACCESSIBILITY
- **Requirement Text:** Text-based input and output must be available at all times, in all contexts, without exception. This includes: all DM narration, all player commands, all feedback, all menus, all onboarding flows. Text is the universal fallback.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.2 (text input), M1.3 (text output/narration), all M3 voice features
- **Notes:** Cross-ref: REQ-SPA-029 (voice must have text equivalents). This is a hard accessibility constraint that affects every feature.

---

**REQ-SPA-056**
- **Source Line(s):** Section 8.1 — "Supports users who are deaf, hard-of-hearing, non-speaking, or in constrained environments."
- **Category:** ACCESSIBILITY
- **Requirement Text:** The text parity requirement must specifically support: (a) deaf users, (b) hard-of-hearing users, (c) non-speaking users, (d) users in constrained environments (library, shared space, no speakers). All four use cases must be fully functional without audio.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.2–M1.3 (text input/output), all M3 voice features
- **Notes:** Cross-ref: REQ-SPA-055. This list of supported user types should guide accessibility testing scenarios.

---

**REQ-SPA-057**
- **Source Line(s):** Section 8.2 — "Voice is primary, not required."
- **Category:** ACCESSIBILITY
- **Requirement Text:** Voice (both TTS output and STT input) is the primary interaction modality but must never be required. The complete game experience must be accessible via text-only mode. No feature, flow, or interaction may be voice-only.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.2–M1.3 (text input/output), M3.1–M3.4 (voice pipeline — text fallback)
- **Notes:** Cross-ref: REQ-SPA-055, REQ-SPA-056. M0_MASTER_PLAN.md Architectural Pillar: "Voice-First, Text-Available."

---

**REQ-SPA-058**
- **Source Line(s):** Section 8.2 — "Onboarding and gameplay must not assume audio."
- **Category:** ACCESSIBILITY
- **Requirement Text:** Neither the onboarding flow nor any gameplay flow may assume the user has audio capability (speakers, headphones, microphone). All audio-dependent interactions must have text equivalents. UI instructions must not say "speak your command" without also offering "type your command."
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (onboarding), M1.2–M1.3 (input/output), M3.1–M3.4 (voice pipeline)
- **Notes:** Cross-ref: REQ-SPA-040 (DM speaks first — but must also display text). Even the persona demo (REQ-SPA-041) must work in text mode.

---

## Section 9: Daily Launch Interaction (Newly Emphasized)

---

**REQ-SPA-059**
- **Source Line(s):** Section 9.1 — "Each app launch begins with DM greeting."
- **Category:** UX
- **Requirement Text:** Every application launch (not just the first) must begin with the DM greeting the player. The home screen is not a static menu — it is a conversation. The DM acknowledges the player's return and initiates interaction.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.14–M1.17 (runtime session bootstrap, resume flow)
- **Notes:** Cross-ref: WO-M1.5-UX-01 (runtime experience design — resume flow already designed). The DM greeting is the first thing the player sees/hears on every launch.

---

**REQ-SPA-060**
- **Source Line(s):** Section 9.1 — "DM asks readiness; user can request recap/notes."
- **Category:** UX
- **Requirement Text:** After the launch greeting, the DM must: (a) ask if the player is ready to continue, (b) offer the option to hear a recap of the previous session, (c) offer to review notes or character sheet changes. The player controls the pace of re-entry.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.14–M1.17 (runtime session bootstrap), M2.2–M2.4 (session continuity)
- **Notes:** Cross-ref: REQ-SPA-036 (session recap), REQ-SPA-037 (specific detail recall). The resume flow from WO-M1.5-UX-01 should incorporate this.

---

**REQ-SPA-061**
- **Source Line(s):** Section 9.1 — "DM can discuss sheet changes (e.g., alignment shift) and explain why."
- **Category:** UX
- **Requirement Text:** During the launch interaction, the DM must be able to proactively discuss character sheet changes that occurred (e.g., alignment shifts, level-ups, equipment changes) and explain the reasons for those changes using logged evidence. Changes must not be silent or unexplained.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.14–M1.17 (runtime session bootstrap), M1.11–M1.13 (character sheet)
- **Notes:** Cross-ref: REQ-SPA-038 (justify consequences using logs), REQ-SPA-035(f) (consequence explanations). This is transparency in action.

---

**REQ-SPA-062**
- **Source Line(s):** Section 9.2 — "Memory should feel contextual and warm."
- **Category:** NARRATIVE
- **Requirement Text:** When the DM references remembered events, the tone must feel contextual and warm — like a friend recalling shared experiences — not like a database query result. Memory retrieval must be presented as natural conversation, not as structured data readback.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.3 (narration tone), M1.14–M1.17 (launch interaction)
- **Notes:** Cross-ref: REQ-SPA-063 (avoid creepy omniscience). This is a narration style constraint for the LLM prompt engineering.

---

**REQ-SPA-063**
- **Source Line(s):** Section 9.2 — "Avoid 'Creepy Omniscience' Tone"
- **Category:** NARRATIVE
- **Requirement Text:** The DM's memory recall must avoid a "creepy omniscience" tone — it must not feel like surveillance or like the system is tracking the player's every move. References to past events should feel natural, not exhaustive. The system knows things; it should not flaunt that knowledge unnecessarily.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.3 (narration tone), M1.14–M1.17 (launch interaction)
- **Notes:** Cross-ref: REQ-SPA-062. This is a LLM prompt engineering constraint. The guarded narration service (`aidm/narration/guarded_narration_service.py`) may need to include anti-omniscience guardrails.

---

**REQ-SPA-064**
- **Source Line(s):** Section 9.2 — "Provide opt-outs (skip greeting/recap) if needed."
- **Category:** UX
- **Requirement Text:** The daily launch greeting and recap must be skippable. The player must be able to say "skip" or "let's just play" to bypass the greeting and recap and go directly into gameplay. Opt-outs must be respected without penalty.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.14–M1.17 (runtime session bootstrap, resume flow)
- **Notes:** Cross-ref: REQ-SPA-043 (skippable ceremony). The skip option must be clearly available without requiring the player to listen to the full greeting first.

---

## Section 10: Hardware & Optimization Constraints (Fine Detail)

---

**REQ-SPA-065**
- **Source Line(s):** Section 10.1 — "Use Steam Hardware Survey as reference for typical CPU/GPU/RAM/VRAM."
- **Category:** CONSTRAINT
- **Requirement Text:** The hardware baseline for minimum and target specifications must be derived from the Steam Hardware Survey. The median gaming PC profile from the survey defines the "typical user" hardware assumption.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M4.x (offline packaging, hardware tiers)
- **Notes:** Cross-ref: M0_MASTER_PLAN.md RQ-HW-001 (median spec: 6-8 core CPU, 16 GB RAM, 6-8 GB VRAM). Already researched and baselined.

---

**REQ-SPA-066**
- **Source Line(s):** Section 10.2 — "Evaluate combined resource budgets across LLM + STT + TTS + image + critique."
- **Category:** CONSTRAINT
- **Requirement Text:** Resource budgets must be evaluated holistically across ALL concurrent models: LLM inference + STT + TTS + image generation + image critique. The combined resource usage must fit within the target hardware baseline. Individual model selection is insufficient — the combined footprint is what matters.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M4.x (offline packaging), M3.1–M3.10 (all model integrations)
- **Notes:** Cross-ref: REQ-SPA-065 (hardware baseline). The PrepOrchestrator's sequential loading strategy addresses this for prep time; runtime concurrent loading is the harder problem.

---

**REQ-SPA-067**
- **Source Line(s):** Section 10.2 — "Plan GPU/CPU fallback paths."
- **Category:** ARCHITECTURE
- **Requirement Text:** For every GPU-dependent operation (LLM inference, image generation, TTS, STT), a CPU fallback path must be planned. The system must degrade gracefully on hardware without a discrete GPU, using CPU-only inference with acceptable (if slower) quality.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M4.x (offline packaging, hardware tiers)
- **Notes:** Cross-ref: M0_MASTER_PLAN.md RQ-HW-003 (minimum spec: 0 VRAM, CPU fallback). Hardware detector (`aidm/core/hardware_detector.py`) already exists. Model selector (`aidm/core/model_selector.py`) handles tier selection.

---

**REQ-SPA-068**
- **Source Line(s):** Section 10.2 — "Avoid selecting models that assume rare hardware."
- **Category:** CONSTRAINT
- **Requirement Text:** Model selection must not assume hardware that is rare in the target user base. Models requiring >8 GB VRAM, specific GPU architectures, or exotic accelerators must not be chosen as primary. They may be supported as optional enhancements for users who have them.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M4.x (offline packaging, hardware tiers)
- **Notes:** Cross-ref: REQ-SPA-065, REQ-SPA-067. Already addressed in R0 research: Mistral 7B (4-bit) fits 6-8 GB VRAM; SD 1.5 fits same budget.

---

## Section 11: Research Phase Requirements (Fine Detail)

---

**REQ-SPA-069**
- **Source Line(s):** Section 11.1 — Research tracks
- **Category:** ARCHITECTURE
- **Requirement Text:** Before locking any model or technology choice, the following research tracks must be completed: (a) LLM selection and validation, (b) image generation + critique pipeline validation, (c) STT selection and validation, (d) TTS selection and validation, (e) optimization and hardware fitting validation.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M4.x (version pinning), relates to all M3 tasks
- **Notes:** R0 research phase has already addressed most of these (see R0_DECISION_REGISTER.md). Some tracks may need re-evaluation as models improve.

---

**REQ-SPA-070**
- **Source Line(s):** Section 11.2 — Gating rule for model approval
- **Category:** CONSTRAINT
- **Requirement Text:** No model may be approved for integration unless ALL of the following are validated: (a) failure modes are understood and documented, (b) multilingual capabilities are validated (if applicable), (c) resource footprint fits the median hardware baseline, (d) determinism/presentation isolation remains intact (the model cannot alter mechanical state).
- **Binding Status:** BINDING
- **Roadmap Mapping:** M4.x (version pinning), M3.1–M3.10 (model integration)
- **Notes:** Item (d) is particularly important — it ties back to the core mechanics/presentation separation. No generative model may have write access to the deterministic engine.

---

**REQ-SPA-071**
- **Source Line(s):** Section 11.2 — "failure modes understood"
- **Category:** CONSTRAINT
- **Requirement Text:** For each model integrated into the system, the known failure modes must be explicitly documented: what happens when the model fails, how failures are detected, and what the fallback behavior is. "It works most of the time" is not sufficient.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.1–M3.10 (all model integrations), M4.x (version pinning)
- **Notes:** Cross-ref: REQ-SPA-015 (critique fallback to placeholder), REQ-SPA-019 (bounded retry). Every model integration needs a failure-mode document.

---

**REQ-SPA-072**
- **Source Line(s):** Section 11.2 — "multilingual capabilities validated"
- **Category:** CONSTRAINT
- **Requirement Text:** For models that handle natural language (LLM, STT, TTS), multilingual capabilities must be validated before approval. The system must know which languages are supported, at what quality level, and what happens with unsupported languages.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.1–M3.4 (voice pipeline — multilingual), relates to GAP-POL-04
- **Notes:** Cross-ref: REQ-SPA-026 (multilingual alias resolution), GAP-POL-04. English-first for launch, but architecture must not block future languages.

---

**REQ-SPA-073**
- **Source Line(s):** Section 11.2 — "determinism/presentation isolation remains intact"
- **Category:** ARCHITECTURE
- **Requirement Text:** Every model integration must preserve the determinism/presentation isolation boundary. No generative model (LLM, image gen, TTS, STT) may alter, influence, or have write access to the deterministic mechanics engine state. Generative models read outcomes and produce presentation; they never produce outcomes.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.1–M3.15 (all immersion layer integrations)
- **Notes:** Cross-ref: REQ-SPA-002 (presentation is replaceable), M0_MASTER_PLAN.md Component 2 (Authority: NONE). This is the most critical architectural invariant.

---

## Section 12: Actionable Checklist Summary — Must-Have Contracts

---

**REQ-SPA-074**
- **Source Line(s):** Section 12 — "canonical IDs vs presentation separation"
- **Category:** ARCHITECTURE
- **Requirement Text:** (Consolidation) The canonical ID vs. presentation separation must be implemented as a binding contract. This is a summary restatement of REQ-SPA-001, REQ-SPA-002, and REQ-SPA-003.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.1 (intent lifecycle), M3.1–M3.15 (immersion layer)
- **Notes:** Consolidation reference. See REQ-SPA-001 through REQ-SPA-003 for detailed requirements.

---

**REQ-SPA-075**
- **Source Line(s):** Section 12 — "multimodal equivalence (voice/text)"
- **Category:** ACCESSIBILITY
- **Requirement Text:** (Consolidation) Full multimodal equivalence between voice and text must be maintained. Every voice interaction must have a text equivalent, and every text interaction must be speakable. This is a summary restatement of REQ-SPA-029, REQ-SPA-055, REQ-SPA-057.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.2–M1.3 (input/output), M3.1–M3.4 (voice pipeline)
- **Notes:** Consolidation reference. See REQ-SPA-029, REQ-SPA-055 through REQ-SPA-058.

---

**REQ-SPA-076**
- **Source Line(s):** Section 12 — "prep-first generation pipeline"
- **Category:** ARCHITECTURE
- **Requirement Text:** (Consolidation) The asset generation pipeline must be prep-first. This is a summary restatement of REQ-SPA-007, REQ-SPA-008, REQ-SPA-030, REQ-SPA-031.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M2.1–M2.13 (campaign prep), M3.5–M3.10 (asset pipelines)
- **Notes:** Consolidation reference. PrepOrchestrator prototype already demonstrates this architecture.

---

**REQ-SPA-077**
- **Source Line(s):** Section 12 — "quality gating for images"
- **Category:** VISUAL
- **Requirement Text:** (Consolidation) Image generation must include mandatory quality gating. This is a summary restatement of REQ-SPA-014 through REQ-SPA-021.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.6 (image gen pipeline)
- **Notes:** Consolidation reference. See REQ-SPA-014 through REQ-SPA-021.

---

**REQ-SPA-078**
- **Source Line(s):** Section 12 — "indexed memory + recap capability"
- **Category:** PERSISTENCE
- **Requirement Text:** (Consolidation) Indexed memory with session recap capability must be implemented. This is a summary restatement of REQ-SPA-033 through REQ-SPA-038.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.4–M1.6 (indexed memory), M2.2–M2.4 (campaign persistence)
- **Notes:** Consolidation reference. See REQ-SPA-033 through REQ-SPA-038.

---

## Section 12 (continued): Must-Have UX Behaviors

---

**REQ-SPA-079**
- **Source Line(s):** Section 12 — "DM-first onboarding"
- **Category:** UX
- **Requirement Text:** (Consolidation) Onboarding must be DM-initiated conversational interaction, not menu-driven. Summary of REQ-SPA-039, REQ-SPA-040.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero)
- **Notes:** Consolidation reference.

---

**REQ-SPA-080**
- **Source Line(s):** Section 12 — "persona switch demo within first minute"
- **Category:** UX
- **Requirement Text:** (Consolidation — with adjusted timing) The persona switch demonstration must occur within the first minute of onboarding. This relaxes the "30 seconds" from REQ-SPA-041 to "first minute" in the summary checklist. Implementation should target the tighter constraint where possible.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.10 (session zero), M3.1–M3.2 (TTS persona)
- **Notes:** Cross-ref: REQ-SPA-041 (specifies 30 seconds). The checklist says "first minute" — use the more conservative target (30 seconds) as the stretch goal.

---

**REQ-SPA-081**
- **Source Line(s):** Section 12 — "skippable ceremony" / "dice ritual + customization" / "explicit prep-time handoff" / "launch greeting + recap/notes"
- **Category:** UX
- **Requirement Text:** (Consolidation) The following UX behaviors are must-haves: (a) all ceremonial elements must be skippable, (b) dice rolling must include ritual experience plus customization, (c) prep-time handoff must be explicit with expectation-setting, (d) every app launch must include DM greeting with recap/notes option.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.7–M1.17 (onboarding through runtime), M2.1–M2.4 (prep handoff)
- **Notes:** Consolidation of REQ-SPA-043 through REQ-SPA-054, REQ-SPA-059 through REQ-SPA-064.

---

## Section 12 (continued): Must-Have Risk Controls

---

**REQ-SPA-082**
- **Source Line(s):** Section 12 — "terminology locking / drift prevention"
- **Category:** CONSTRAINT
- **Requirement Text:** The system must prevent terminology drift: once a canonical term is established (entity name, mechanical term, rule reference), it must be locked and consistently used across all presentations. The LLM must not invent synonyms or alternate names for established canonical entities.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.3 (narration — terminology consistency), M1.4–M1.6 (indexed memory — term registry)
- **Notes:** This is a narration guardrail. Cross-ref: `aidm/narration/guarded_narration_service.py` (terminology enforcement). Also relates to GAP-POL-02 (entity rename propagation).

---

**REQ-SPA-083**
- **Source Line(s):** Section 12 — "bounded regeneration loops"
- **Category:** CONSTRAINT
- **Requirement Text:** (Consolidation) All regeneration loops (image, audio, narration) must be bounded with maximum retry counts and fallback behavior. Summary of REQ-SPA-019, REQ-SPA-008.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M3.5–M3.10 (asset pipelines)
- **Notes:** Consolidation reference. See REQ-SPA-019.

---

**REQ-SPA-084**
- **Source Line(s):** Section 12 — "confirmation for high-impact STT actions"
- **Category:** INTERACTION
- **Requirement Text:** (Consolidation) High-impact actions recognized via STT must require explicit confirmation before execution. Summary of REQ-SPA-024.
- **Binding Status:** BINDING
- **Roadmap Mapping:** M1.2 (voice/text input), M3.3–M3.4 (STT pipeline)
- **Notes:** Consolidation reference. See REQ-SPA-024.

---

**REQ-SPA-085**
- **Source Line(s):** Section 12 — "avoid genre-implied mechanics promises"
- **Category:** CONSTRAINT
- **Requirement Text:** The system must not make implicit promises about mechanical support for genres beyond D&D 3.5e. If the presentation layer uses fantasy, sci-fi, or other genre aesthetics, the system must not imply that genre-specific mechanics (e.g., sci-fi weapon types, space travel rules) are supported. Genre reskinning is aesthetic only.
- **Binding Status:** BINDING
- **Roadmap Mapping:** UNMAPPED (scope governance, overlaps REQ-SPA-005/006)
- **Notes:** Cross-ref: REQ-SPA-005 (no public genre/language commitments), REQ-SPA-006 (infinite flexibility is internal only). This is a risk control against user expectation mismanagement.

---

## Document Status

---

**REQ-SPA-086**
- **Source Line(s):** Final status paragraph
- **Category:** PRINCIPLE
- **Requirement Text:** This secondary-pass audit captures fine details from the collaborative design conversation and is intended to be merged into planning/tickets as acceptance criteria. Every item in this document should be treated as a candidate acceptance criterion for its mapped roadmap task.
- **Binding Status:** INFORMATIONAL
- **Roadmap Mapping:** All milestones (cross-cutting governance)
- **Notes:** This establishes the document's authority: items are acceptance criteria, not aspirational ideas.

---

## Summary Statistics

| Category | Count |
|---|---|
| ARCHITECTURE | 14 |
| UX | 16 |
| INTERACTION | 5 |
| CONSTRAINT | 12 |
| PRINCIPLE | 5 |
| VISUAL | 8 |
| AUDIO | 5 |
| ACCESSIBILITY | 4 |
| NARRATIVE | 4 |
| PERSISTENCE | 4 |
| SECURITY | 0 |
| MECHANIC | 0 |
| **TOTAL** | **86** |

| Binding Status | Count |
|---|---|
| BINDING | 79 |
| ASPIRATIONAL | 2 |
| INFORMATIONAL | 5 |

| Roadmap Coverage | Count |
|---|---|
| M1.x mapped | 48 |
| M2.x mapped | 18 |
| M3.x mapped | 42 |
| M4.x mapped | 6 |
| UNMAPPED | 3 |

*Note: Many requirements map to multiple milestones, so the roadmap coverage counts sum to more than 86.*

---

## Cross-Reference Index

### Canonical ID / Mechanics-Presentation Separation
REQ-SPA-001, 002, 003, 004, 028, 073, 074

### Prep-First Architecture
REQ-SPA-007, 008, 030, 031, 076

### Image Generation + Critique
REQ-SPA-014, 015, 016, 017, 018, 019, 020, 021, 077

### Voice Pipeline
REQ-SPA-022, 023, 027, 028, 029

### STT Interaction Safety
REQ-SPA-024, 025, 026, 084

### Indexed Memory
REQ-SPA-033, 034, 035, 036, 037, 038, 078

### Onboarding / Session Zero
REQ-SPA-039, 040, 041, 042, 043, 047, 048, 049, 050, 051, 052, 053, 054, 079, 080

### Dice Experience
REQ-SPA-044, 045, 046, 047

### Accessibility (Text Parity)
REQ-SPA-029, 055, 056, 057, 058, 075

### Daily Launch / Resume
REQ-SPA-059, 060, 061, 062, 063, 064

### Hardware / Resource Budgets
REQ-SPA-065, 066, 067, 068

### Research / Model Gating
REQ-SPA-069, 070, 071, 072, 073

### Scope Containment / Risk
REQ-SPA-005, 006, 082, 085

### Dependencies on Unresolved Policy Gaps
- GAP-POL-02: REQ-SPA-082 (terminology drift prevention)
- GAP-POL-04: REQ-SPA-026 (multilingual alias resolution), REQ-SPA-072 (multilingual validation)

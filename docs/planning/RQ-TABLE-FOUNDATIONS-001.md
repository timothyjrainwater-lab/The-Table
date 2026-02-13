# RQ-TABLE-FOUNDATIONS-001: Contracts That Make "The Table" Playable

**Author:** PM (Opus) + PO (Thunder) + Third-party review
**Date:** 2026-02-12
**Status:** SCOPED (research topics defined, not yet dispatched)
**Umbrella for:** Research Topics A through G

---

## Purpose

Define the contracts, schemas, and policies for systems that don't exist yet but are required before MVP (Session Zero → One Combat) can ship. Each topic produces a spec + examples + violation checklist that can be unit-tested.

---

## Tier 1: Blocks MVP

### Research Topic A: Intent Bridge Contract (Voice → Action IR)

**What we know:**
- Voice is primary input channel
- Combat actions are constrained (attack/cast/move/use item with finite target set on grid)
- Non-combat intent is open-ended ("ask the shopkeeper about rumors")
- Dice tower drop is the physical "commit" for actions requiring rolls
- No coaching — disambiguation is allowed, hinting is not
- Player cannot manipulate DM-side assets

**What we don't know:**
- Exact schema for structured intent (verbs, arguments, references, spatial deixis)
- Allowed failure modes (clarify vs fail-closed vs require dice commit)
- Disambiguation doctrine: what counts as neutral disambiguation ("which goblin?") vs forbidden coaching ("that goblin is flanking you, are you sure?")
- Whether combat intent bridge and non-combat intent bridge need separate contracts (likely yes)
- Determinism rules: same scene state + same utterance → same IR?

**Deliverables:**
- Intent IR schema (JSON) + annotated examples
- Disambiguation policy (when to ask, allowed phrasing, maximum turns)
- Combat vs non-combat mode distinction
- Test suite spec (golden utterance corpus, property tests, fuzz tests)

**Blocked by:** Nothing
**Blocks:** Phase 2.2 (voice pipeline integration), Phase 2.4 (session zero flow)

---

### Research Topic C: Deterministic World Compilation (LLM-as-Compiler)

**What we know:**
- World compile is expensive and frozen ("come back tomorrow" is a feature)
- Pre-world: abilities are IDs + math. Post-compile: IDs bind to names, taxonomy, presentation semantics, rulebook text
- Output is a frozen world bundle: stable names, stable semantics, stable rulebook
- Compiler must produce: vocabulary, presentation semantics (AD-007), doctrine profiles, map seeds, rulebook entries, bestiary templates
- This is compilation, not live improvisation
- Re-compilation produces a NEW world, not the same world — idempotency is wrong goal, deterministic freezing is right goal

**What we don't know:**
- How to make compile outputs stable enough to freeze when using an LLM:
  - Run once → cache/hash → verify → freeze the bundle
  - What verification means (human review? automated checks? both?)
- Minimum viable compiler for MVP world ("Ashenmoor"):
  - What gets compiled first
  - What can remain hand-authored placeholders
  - What must be machine-generated to prove the pipeline
- WorldBundle artifact format: file structure, hashing, versioning
- Failure policy: fail-closed vs partial compile; resume semantics

**Deliverables:**
- WorldBundle spec: artifact list + hashes + versioning policy
- Compile pipeline architecture: inputs → LLM steps → outputs → freeze
- Determinism strategy: seed management, caching, canonicalization, diff checks
- Compile certificate format ("World Build Certificate" — proves what was compiled, when, from what inputs)
- Failure + resume policy
- Minimum viable compiler definition for MVP

**Blocked by:** AD-007 (Presentation Semantics Schema — Phase 0.3)
**Blocks:** Phase 1.1 (World Model Schema), Phase 1.2 (Minimum World Compiler)

---

### Research Topic D: Non-Combat Contracts (Exploration/Social/Investigation)

**What we know:**
- Physical table metaphor covers non-combat via handouts, notebook, crystal ball, rulebook, voice conversation
- The AI does not invent mechanics
- Player can sit and talk to the crystal ball outside gameplay
- Conversational queries can be backed by provenance (session log, world model)
- Shopkeeper interaction: menu as handout, voice/click to buy, auto-update sheet

**What we don't know — THE HARD PROBLEM:**
- Who owns scene facts outside combat?
  - World model owns pre-authored facts (this town has a blacksmith)
  - Event log owns historical facts (you visited the blacksmith yesterday)
  - But "what does the blacksmith say when you ask about the dragon?" is a fact that doesn't exist until generated — and once generated, it must become permanent truth
  - This is the hardest authority problem in the system
- Contracts for social/exploration loops:
  - "Talk to NPC" is stateful interaction with constraints, memory, and world facts — not just narration
  - How does the system prevent Spark from becoming an oracle that invents world truth?
- Scene Fact Authority model:
  - WorldBundle facts (compiled, frozen) vs runtime observations (event log) vs unknowns (not yet determined)
  - What happens when a player asks about something the world model is silent on?
- Unknown handling policy for non-combat:
  - Defer to human author? Generate and freeze? Fail-closed? Ask player to rephrase?

**Deliverables:**
- Scene Fact Authority model (three-tier: compiled facts / runtime facts / unknowns)
- Interaction loop schemas: shop, conversation, search, travel, rest
- NPC conversation authority contract: what can an NPC assert vs what requires world model backing?
- Unknown handling policy with strict phrasing rules
- Tests: Spark cannot assert facts that aren't backed by world model or event log

**Blocked by:** Research Topic C (world compiler defines what facts exist)
**Blocks:** Phase 2.4 (session zero flow includes non-combat interaction)

---

## Tier 2: Enriches MVP

### Research Topic B: Knowledge Mask Schema (Bestiary Progressive Revelation)

**What we know:**
- Four progressive states: heard → seen → fought → studied
- Lives in notebook bestiary section
- Entries permanently bound to assets (portrait/token/voice from pool)
- Knowledge driven by: encounter history, skill checks, NPC conversations
- Enforces DM/player information boundary
- Image generator updates entry image at each knowledge level
- Reward system for investing in identification skills

**What we don't know:**
- Exact field gating by knowledge level:
  - What becomes visible at each level (size, type, movement, abilities observed, resistances inferred, etc.)
  - Which fields are "free" (name at heard-of) vs gated (resistances at studied)
- How "told about it" vs "seen it" vs "fought it" differ in data exposure
- Image generation prompt contracts:
  - Must produce consistent images across levels (same creature, increasing detail)
  - No identity drift between silhouette and full portrait
  - This is a non-trivial image generation constraint
- BestiaryEntry schema with per-level visibility masks

**Deliverables:**
- BestiaryEntry schema + KnowledgeMask schema
- Knowledge events taxonomy + mapping to mask reveals
- Image generation prompt contracts (silhouette → partial → full) with identity preservation rules
- Unit-testable checklist for information leaks

**Blocked by:** Research Topic C (bestiary templates come from world compiler)
**Blocks:** Phase 2.3 (discovery log backend)

---

### Research Topic F: Asset Pool + Binding System

**What we know:**
- Pool-based rotation: categories (goblin_portrait, gruff_voice, forest_tile, etc.)
- Use one → bind permanently to entity → queue replacement generation
- System generates its own asset library (no external assets required)
- Priority queue: critical path → near-term → speculative
- Background generation during gameplay, session N+1 prep during session N
- Binding registry: NPC_042 → voice_profile_17 + portrait_goblin_09, permanent
- Bestiary images tied to knowledge level, not individual binds

**What we don't know:**
- Category taxonomy: what categories exist, how fine-grained
- Pool sizing heuristics: how many assets per category to maintain readiness
- Compute scheduling under GPU contention (rendering + LLM + TTS + image generation)
- No-reuse constraints: can two NPCs ever share an asset? (probably no for portraits/voices)
- Deterministic fallback representations when pools are empty
- Storage format and lifecycle management (when do unbound assets expire?)

**Deliverables:**
- Category taxonomy + pool sizing recommendations
- Binding registry schema
- No-reuse constraint enforcement
- Background generation scheduler spec (priority queue + compute budget)
- Fallback policy for empty pools
- Storage lifecycle management

**Blocked by:** Image/voice generation infrastructure
**Blocks:** Phase 4.2 (asset pipeline)

---

### Research Topic G: No-Coaching Compliance

**What we know:**
- No AoO warnings — player learns by getting hit
- No "are you sure?" prompts
- No mercy, no hand-holding
- The system resolves consequences without warning

**What we don't know:**
- Bright line between disambiguation and coaching:
  - "Which goblin?" → allowed (neutral disambiguation)
  - "That goblin is flanking you, are you sure?" → forbidden (coaching)
  - "You can't reach that goblin this turn" → allowed? forbidden? (movement constraint is mechanical fact, not coaching)
  - "The shopkeeper looks nervous" → allowed (narration) vs "The shopkeeper is about to attack" → forbidden (telegraphing)
- How to test narration output for coaching violations
- Policy for Spark: what phrases/patterns are forbidden in generated narration

**Deliverables:**
- Coaching vs disambiguation bright-line definitions with examples
- Allowed/forbidden response taxonomy
- Narration compliance checker: phrase/pattern classifiers for violations
- Test corpus: golden examples of allowed vs forbidden AI responses

**Blocked by:** Nothing
**Blocks:** Nothing (enrichment, not critical path)

---

## Parallel Track: Vocabulary Decoupling

### Research Topic E: Vocabulary Decoupling Plan (Rename + Abstraction Strategy)

**What we know:**
- D&D is the mine, not the product. Bone and muscle are extracted; skin is discarded
- Product ships no copyrighted vocabulary
- Internal codebase currently references D&D concepts (spell names, feat names, PHB citations, "RAW_3.5")
- Tests reference D&D concepts in descriptions and assertions

**What we don't know:**
- Migration plan: how to rename without losing meaning in 3,753+ tests
- Neutral terminology glossary for internal naming (stable across game systems)
- Which references are "bone" (keep, just rename) vs "skin" (remove entirely)
- How to preserve test intent while removing IP surface

**Deliverables:**
- Glossary mapping (current D&D term → neutral internal term)
- Test migration strategy (preserve coverage; remove IP surface)
- Layer boundary audit: ensure no "skin" leaks into bone/muscle layers
- Phased migration plan (what renames first, what waits)

**Blocked by:** Nothing
**Blocks:** Phase 0.1 (strip source material references)

---

## Priority Order for Research Dispatch

| Priority | Topic | Rationale |
|----------|-------|-----------|
| 1 | A (Intent Bridge — combat mode) | Critical path for playability; combat is tractable |
| 2 | C (World Compiler — minimum viable) | Critical path for content independence |
| 3 | D (Non-Combat Authority) | Prevents Spark from becoming an oracle |
| 4 | B (Discovery Log Schema) | Locks the knowledge boundary |
| 5 | F (Asset Pool + Binding) | Makes the table feel alive without drift |
| 6 | E (Vocabulary Decoupling) | Prevents long-term IP entanglement |
| 7 | G (No-Coaching Compliance) | Makes doctrine enforceable |
| — | A (Intent Bridge — non-combat mode) | Entangled with D; deferred until D is resolved |

---

## Relationship to Existing Documents

- **AD-007** defines the Presentation Semantics contract that Topics A, C, and D must respect
- **UX_VISION_PHYSICAL_TABLE.md** defines the interaction model that Topics A, F, and G must serve
- **MVP_SESSION_ZERO_TO_ONE_COMBAT.md** defines the acceptance criteria that all Tier 1 topics must satisfy
- **REVISED_PROGRAM_SEQUENCING_2026_02_12.md** defines the phase ordering that determines dispatch priority

---

*These research topics define the contracts between what exists (the deterministic engine) and what must be built (the world compiler, intent bridge, and authority model). Each topic produces testable artifacts, not prose. The standard is: if you can't write a test for it, the spec isn't done.*

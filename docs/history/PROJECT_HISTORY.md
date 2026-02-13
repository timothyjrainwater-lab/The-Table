# Project History Archive

> **Purpose:** Historical CP summaries, module inventory, frozen contracts, and governance docs.
> **Archived from:** `pm_inbox/aegis_rehydration/PROJECT_STATE_DIGEST.md`
> **Archive date:** 2026-02-11

This file contains comprehensive historical documentation. For current operational state, see `pm_inbox/aegis_rehydration/PROJECT_STATE_DIGEST.md`.

---

## Locked Systems (Implemented & Tested)

### Core Engine (Deterministic Foundation)
- **RNGManager**: Stream-isolated deterministic RNG with hash-based seed derivation
- **EventLog**: Append-only event sourcing with monotonic ID enforcement, JSONL serialization
- **WorldState**: Deterministic hashing with stable JSON key ordering
- **ReplayRunner**: Single reducer function pattern for all state mutations
- **LegalityChecker**: Fail-closed validation gate with structured ReasonCode enum

### Source Layer (Provenance & Rule Lookup)
- **SourceRegistry**: Access to 647 D&D 3.5e sources, 966 pages of extracted text (PHB/DMG/MM)
- **Citation Schema**: Structured source references (sourceId + page + span)
- **RuleLookup v0**: Page-level keyword search with SearchHit results
- **RulingHelpers**: Integration between rule lookup and event log citations

### Voice-First Tabletop Contracts
- **Intent Schemas**: CastSpellIntent, MoveIntent, DeclaredAttackIntent, BuyIntent, RestIntent
- **InteractionEngine**: Declare→Point→Confirm two-phase commit pattern
- **Position (CP-001)**: Canonical 2D grid position type with 1-2-1-2 diagonal distance

### M1 Runtime Layer
- **IntentObject**: Player intent with lifecycle management
- **EngineResult**: Immutable authoritative resolution output
- **SessionLog**: Intent-to-result correlation with JSONL serialization
- **ReplayHarness**: Deterministic replay verification with 10× capability
- **Narrator**: Template-based narration (55 templates)

### M2 Campaign Prep Pipeline
- **CampaignStore**: Filesystem-backed campaign persistence
- **PrepOrchestrator**: Deterministic prep job queue
- **AssetStore**: Campaign asset management with shared cache
- **WorldArchive**: Campaign export/import bundle

### M3 Immersion Layer
- **STT/TTS/Image adapters**: Protocol-based with stub implementations
- **Audio mixer**: Mood-based scene audio (combat/tense/peaceful)
- **Contextual grid**: Combat-visibility-aware grid state
- **Attribution store**: Fail-closed asset attribution

---

## Module Inventory

### aidm/core/
- event_log.py, rng_manager.py, state.py, replay_runner.py
- source_registry.py, rule_lookup.py, ruling_helpers.py
- interaction.py, obsidian_links.py, bundle_validator.py
- doctrine_rules.py, tactical_policy.py, play_loop.py
- attack_resolver.py, full_attack_resolver.py
- initiative.py, combat_controller.py, aoo.py
- conditions.py, save_resolver.py, targeting_resolver.py
- mounted_combat.py, maneuver_resolver.py, permanent_stats.py
- terrain_resolver.py, session_log.py
- campaign_store.py, prep_orchestrator.py, prep_pipeline.py
- asset_store.py, world_archive.py
- geometry_engine.py, cover_resolver.py, los_resolver.py
- aoe_rasterizer.py, ranged_resolver.py, reach_resolver.py
- combat_reflexes.py, lens_index.py, fact_acquisition.py
- provenance.py, box_lens_bridge.py, truth_packets.py
- stp_emitter.py, spell_resolver.py, duration_tracker.py

### aidm/schemas/
- citation.py, intents.py, bundles.py, doctrine.py
- visibility.py, terrain.py, policy_config.py
- time.py, timers.py, durations.py, hazards.py, exposure.py
- policy.py, campaign_memory.py, rulings_conflicts.py
- attack.py, conditions.py, saves.py, targeting.py
- mounted_combat.py, maneuvers.py, permanent_stats.py
- entity_fields.py, entity_state.py
- intent_lifecycle.py, engine_result.py, campaign.py
- prep_pipeline.py, immersion.py, position.py
- geometry.py, spell_definitions.py

### aidm/immersion/
- stt_adapter.py, tts_adapter.py, audio_mixer.py
- image_adapter.py, contextual_grid.py, attribution.py

---

## Completion Packet History

### CP-05 through CP-16: Combat Foundation
- CP-05: Time, Clocks, Deadlines, Durations
- CP-06: Environmental Hazards & Exposure
- CP-07: Tactical Policy Engine
- CP-08: Campaign Memory & Character Evidence Ledger
- CP-09: Vertical Slice V1 Implementation
- CP-10: Attack Resolution Proof
- CP-11: Full Attack Sequence Proof
- CP-12: Play Loop Combat Integration
- CP-13: Monster Combat Integration
- CP-14: Initiative & Action Economy Kernel
- CP-15: Attacks of Opportunity Kernel
- CP-16: Conditions & Status Effects Kernel

### CP-17 through CP-19: Advanced Combat
- CP-17: Save Resolution Kernel
- CP-18A: Mounted Combat & Rider-Mount Coupling
- CP-18A-T&V: Targeting & Visibility Resolver
- CP-18: Combat Maneuvers (Bull Rush, Trip, Overrun, Sunder, Disarm, Grapple-lite)
- CP-19: Environment & Terrain (difficult terrain, cover, higher ground, falling)
- CP-19B: Failure-Path Hazard Resolution

### Milestones
- M1: Solo Vertical Slice v0 (Runtime Layer)
- M2: Campaign Prep Pipeline v0
- M3: Immersion Layer v1
- M3 Plan C: Immersion Hardening

### Special Work Orders
- SKR-002: Permanent Stat Modification Core
- CP-001: Position Type Unification (Phase 1)
- WO-M3-PREP-01: M3 Prep Pipeline Prototype
- POST-AUDIT: Engine & Combat Corrections (10 fixes)

---

## Frozen Contracts (v0.3.0-post-audit-m3)

### Frozen Immersion Layer
All modules in `aidm/immersion/` and `aidm/schemas/immersion.py` are frozen.

### Frozen Replay & Determinism Semantics
- Event sourcing append-only contract
- RNG stream isolation
- State hash determinism
- Entity field access via EF.* constants
- State mutation via deepcopy() only

### Frozen Narration Layer
55 templates in `aidm/narration/narrator.py` are frozen.

---

## Capability Gate Status

| Gate ID | Gate Name | Status |
|---------|-----------|--------|
| G-T1 | Tier 1 Mechanics | ✅ OPEN |
| G-T2A | Permanent Stat Mutation | 🔒 CLOSED |
| G-T2B | XP Economy | 🔒 CLOSED |
| G-T3A | Entity Forking | 🔒 CLOSED |
| G-T3B | Agency Delegation | 🔒 CLOSED |
| G-T3C | Relational Conditions | 🔒 CLOSED |
| G-T3D | Transformation History | 🔒 CLOSED |

---

## Vault/ Directory

The `Vault/` directory is a **structured D&D 3.5e rules reference** extracted from core rulebooks. It is NOT AIDM application code. ~23,750 files, ~20MB. Skeleton notes exist but are unfilled. Do NOT modify without specific work order.

---

## Key Design Principles (Locked)

1. **Determinism First**: All randomness deterministic, stable serialization, reproducible replay
2. **Event Sourcing**: State derived from append-only log, monotonic IDs
3. **Fail-Closed**: Unknown types rejected, missing state causes errors
4. **Provenance & Citations**: All rulings traceable to source material
5. **Data-Only Schemas**: Contracts defined before algorithms
6. **Prep vs Play Separation**: Async prep, sync play
7. **Voice-First Contracts**: Structured intents, not free-form NLU
8. **No Mercy Caps**: Doctrine is capability gating, not fairness balancing

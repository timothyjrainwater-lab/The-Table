<!--
PROJECT STATE DIGEST — CANONICAL STATE SNAPSHOT

UPDATE RULES:
- Updated at the end of every instruction packet (CP-XX)
- Factual only — no discussion, no design speculation
- Single source of truth for project state
- Paste this file to refresh any agent completely
- Format: Markdown with stable section ordering
- REHYDRATION COPY: After editing this file, also update pm_inbox/aegis_rehydration/PROJECT_STATE_DIGEST.md

LAST UPDATED: 2026-02-11 — PSD HYGIENE PASS: trimmed from 1750 to ~590 lines. Phase 2 Batch 2 DISPATCHED: WO-033 (Spark Stress Test) + WO-036 (Expanded Spells). Batch 1 COMPLETE: WO-032/034/035/037 all INTEGRATED.
-->

# Project State Digest

## Project Governance

**Product Owner (PO):** Thunder — Design decisions, implementation vision, research delivery. Does not control coding.
**Project Manager (PM):** Opus — Project management, work order creation, coding direction, agent coordination. Full PM authority delegated by Thunder on 2026-02-11.

**Authority model:** PM issues work orders and manages execution autonomously. PO is consulted for design decisions and vision changes only. All architectural doctrine (Spark/Lens/Box) remains binding regardless of role.

**Effective date:** 2026-02-11 (whiteboard session closeout)

---

## Locked Systems (Implemented & Tested)

> **Note:** Each subsystem below is summarized. For detailed field-level documentation, read the source code or the relevant CP decision document in `docs/`.

### Core Engine (Deterministic Foundation)
- **RNGManager**: Stream-isolated deterministic RNG with hash-based seed derivation
- **EventLog**: Append-only event sourcing with monotonic ID enforcement, JSONL serialization
- **WorldState**: Deterministic hashing with stable JSON key ordering
- **ReplayRunner**: Single reducer function pattern for all state mutations
- **LegalityChecker**: Fail-closed validation gate with structured ReasonCode enum

### Source Layer (Provenance & Rule Lookup)
- **SourceRegistry**: 647 D&D 3.5e sources, 966 pages extracted text (PHB/DMG/MM)
- **RuleLookup v0**: Page-level keyword search with SearchHit results
- **Citation Schema + RulingHelpers**: Structured source references integrated with event log

### Voice-First Tabletop Contracts
- **Intent Schemas**: CastSpellIntent, MoveIntent, DeclaredAttackIntent, BuyIntent, RestIntent
- **InteractionEngine**: Declare→Point→Confirm two-phase commit pattern
- **Position (CP-001)**: Canonical 2D grid position, 1-2-1-2 diagonal distance (PHB p.148), immutable, hashable
- **Legacy types (DEPRECATED)**: GridPoint, GridPosition — to be removed in CP-002

### M1 Runtime Layer (Solo Vertical Slice v0)
- **IntentObject**: Player intent with lifecycle (PENDING → CLARIFYING → CONFIRMED → RESOLVED)
- **EngineResult**: Immutable authoritative resolution output + EngineResultBuilder
- **SessionLog**: Intent-to-result correlation with JSONL serialization
- **ReplayHarness**: 10x deterministic replay verification
- **CharacterSheet/PartySheet UI**: Read-only character view with derived values
- **NarrationTemplates**: 55 deterministic fallback templates (attack, maneuver, save, environmental, mounted)
- **SessionBootstrap**: Campaign load, replay-first reconstruction, partial write recovery, log sync checks
- **RuntimeSession**: Intent → result → log flow manager (per IPC_CONTRACT.md)
- **Runtime Experience Design**: Text-only solo UX spec (design only, NOT implemented)

### M2 Campaign Prep Pipeline v0
- **SessionZeroConfig/CampaignManifest/CampaignPaths**: Ruleset capture + directory layout + version-pinned metadata
- **PrepJob/PrepOrchestrator**: Deterministic prep queue (4 phases), idempotent execution, append-only logging
- **AssetStore**: Campaign asset management with shared cache, content hash integrity
- **WorldArchive**: Campaign export/import bundle with validation
- **CampaignStore**: Filesystem-backed campaign persistence

### M3 Prep Pipeline Prototype (WO-M3-PREP-01)
- **PrepPipeline**: Sequential model loading (LLM → Image → Music → SFX), stub mode for testing
- **Asset types**: NPCs (JSON), Portraits (PNG), Scenes (PNG), Music (OGG), SFX (OGG)
- **SessionBundle/CampaignBundle/ReadinessCertificate**: Scene cards, NPC cards, world facts, validation

### M3 Immersion Layer v1
- **Adapters**: STT, TTS, Image, AudioMixer — all Protocol-based with stub implementations
- **Pure functions**: compute_scene_audio_state(), compute_grid_state() — deterministic, side-effect-free
- **Attribution**: AttributionStore with fail-closed validation
- **Non-authoritative**: All immersion outputs atmospheric only, excluded from deterministic replay
- **API stability**: 16 PUBLIC_STABLE exports, frozen via Plan C (38 authority contract tests)
- **Determinism canary**: 28 tests × 100 iterations = 2800 function calls

### CP-001: Position Type Unification (Phase 1)
- **Canonical Position**: Consolidates 3 legacy types, frozen dataclass, distance_to() + is_adjacent_to()
- **34 tests** including PBHA determinism proof. Phase 1 COMPLETE. Phase 2 (migration) pending.

### WO-034: Core Feat System (15 Combat Feats)
- **FeatDefinition/FeatID/FEAT_REGISTRY**: 15 PHB feats (Power Attack, Cleave, Dodge, Mobility, TWF chain, etc.)
- **Prerequisite validation**: Ability scores, BAB, required feats, fighter level
- **Modifier computation**: Attack (+1 Weapon Focus, +1 PBS), Damage (+2 WSpec, +1 PBS), AC (+1 Dodge, +4 Mobility), Initiative (+4 Improved Initiative)
- **Integration**: attack_resolver.py (feat_modifier), aoo.py (Mobility +4 AC)
- **41 tests** in test_feat_resolver.py

### WO-037: Experience and Leveling System
- **LEVEL_THRESHOLDS/XP_TABLE/CLASS_PROGRESSIONS**: DMG Tables 3-2 and 2-6, 4 core classes
- **BAB/Save progressions**: Full/three-quarters/half BAB, good/poor save tables (levels 1-20)
- **Level-up**: Atomic via deepcopy — hit die + CON mod, BAB, saves, skill points, feat/ability slots
- **Multiclass penalty**: PHB p.60 XP penalty calculation
- **34 tests** in test_experience_resolver.py

### WO-032: NarrativeBrief Assembler (Lens Layer)
- **NarrativeBrief**: Frozen dataclass — one-way valve from Box STPs to Spark-safe context
- **Containment**: No entity IDs, raw HP, AC, attack bonuses, or grid coordinates
- **Severity mapping**: HP percentage → minor/moderate/severe/devastating/lethal
- **ContextAssembler**: Token-budget-aware context window (word_count * 1.3 estimation)
- **45 tests** across test_narrative_brief.py (25) + test_context_assembler.py (20)

### WO-035: Skill System (7 Combat-Adjacent Skills)
- **7 skills**: Tumble (DEX), Concentration (CON), Hide (DEX), Move Silently (DEX), Spot (WIS), Listen (WIS), Balance (DEX)
- **resolve_skill_check()**: d20 + ability_mod + ranks + circumstance - ACP vs DC
- **resolve_opposed_check()**: Actor vs opponent, ties favor active checker
- **Integrations**: Tumble DC 15 in aoo.py, Concentration DC (10+damage) in spell_resolver.py
- **30 tests** across test_skill_resolver.py (25) + test_concentration_integration.py (5)

### Combat Resolution Stack (CP-10 through CP-19)
- **Attack Resolution (CP-10)**: Single attack d20 + bonus vs AC, natural 20/1, damage on hit
- **Full Attack (CP-11)**: BAB iterative attacks, critical hits (nat 20 → confirm → multiply)
- **Play Loop Integration (CP-12)**: Intent validation → combat routing → event application
- **Monster Combat (CP-13)**: Doctrine → policy → AttackIntent mapping
- **Initiative (CP-14)**: d20 + Dex, deterministic tie-breaking, flat-footed management, combat controller
- **AoO (CP-15)**: Movement-triggered, one per reactor/round, action abortion on defeat
- **Conditions (CP-16)**: 8 conditions (Prone, Flat-Footed, Grappled, Helpless, Stunned, Dazed, Shaken, Sickened), modifier stacking
- **Save Resolution (CP-17)**: Fort/Ref/Will saves with condition modifiers
- **Targeting/Visibility (CP-18A-T&V)**: LoS/LoE validation, cover computation
- **Mounted Combat (CP-18A)**: Rider-mount coupling, mounted attack resolution
- **Combat Maneuvers (CP-18)**: Bull Rush, Disarm, Grapple, Overrun, Sunder, Trip — opposed checks, AoO provocation
- **Environment/Terrain (CP-19)**: Terrain effects, elevation, environmental damage, hazard resolution
- **Permanent Stats (SKR-002)**: Stat modification algorithms (Phase 3 complete)

### Additional Schema Systems
- **Temporal Contracts**: TimeScale, GameClock, Deadlines, EffectDuration, AmbientLightSchedule
- **Environmental Hazards**: HazardProgression, ExposureType, EnvironmentalCondition
- **Tactical Policy Engine**: Integer-based heuristic scoring, policy RNG isolation, doctrine-filtered candidates
- **Campaign Memory**: SessionLedger, EvidenceLedger, ClueCard, ThreadRegistry (descriptive only)
- **Rulings & Conflicts**: RulesQuestion, RulingConflict, RulingDecision (descriptive only)
- **Monster Doctrine**: 13 behavioral tags, INT/WIS bands, tactic class gates
- **Visibility/Terrain**: LightLevel, VisionMode, OcclusionTag, TerrainTag, TraversalRequirement
- **Policy Config**: top_k + temperature + score_band for variety

### Spellcasting System (WO-014/WO-015, Plan v1)
- **SpellResolver** (1078 lines): Full resolution pipeline — targeting, saves, damage, healing, conditions, STPs
- **DurationTracker** (492 lines): Effect lifecycle, concentration management, expiration, dispelling
- **AoE Rasterizer** (593 lines): Burst/cone/line geometry per RQ-BOX-001
- **20 existing spells** in spell_definitions.py (levels 0-5)
- **Concentration integration** (WO-035): check_concentration_on_damage() DC = 10 + damage

---

## Test Count

**Total: 3452 tests** (all passing in ~46 seconds, 0 failed, 11 skipped hardware-gated)

> Per-subsystem breakdown omitted for context weight. Run `pytest --co -q` for current counts. Phase 2 Batch 1 WOs added 150 tests (WO-032: 45, WO-034: 41, WO-035: 30, WO-037: 34).

---

## Module Inventory

> Per-file listings omitted for context weight. Use `ls aidm/core/`, `ls aidm/schemas/`, etc. for current inventory.

**Directory structure:**
- `aidm/core/` — 28 modules: resolvers (attack, full_attack, save, skill, feat, experience, maneuver, targeting, terrain, mounted_combat, aoo, conditions, spell_resolver), engine (play_loop, combat_controller, initiative, permanent_stats), infrastructure (event_log, rng_manager, state, replay_runner, source_registry, rule_lookup, ruling_helpers, interaction, obsidian_links, bundle_validator, doctrine_rules, tactical_policy), pipeline (session_log, campaign_store, prep_orchestrator, prep_pipeline, asset_store, world_archive, duration_tracker)
- `aidm/schemas/` — 24 modules: data contracts for all subsystems
- `aidm/rules/` — legality_checker.py
- `aidm/ui/` — character_sheet.py (CharacterData, CharacterSheetUI, PartySheet)
- `aidm/narration/` — narrator.py (55 templates), play_loop_adapter.py, guarded_narration_service.py
- `aidm/lens/` — narrative_brief.py, context_assembler.py (WO-032)
- `aidm/immersion/` — 7 modules: stt/tts/image adapters, audio_mixer, contextual_grid, attribution
- `tests/` — 80+ test files
- `Vault/` — D&D 3.5e rules knowledge base (~23,750 files, NOT AIDM code, do NOT modify without WO)

---

## Instruction Packet History

> **TRIMMED:** Full CP/WO history removed for context weight reduction. All completed work is reflected in the Locked Systems section above. For detailed CP history, see individual CP decision documents in `docs/` or the git log.

---

## MANDATORY FIRST READ FOR ALL AGENTS

**START HERE:**
- [AGENT_ONBOARDING_CHECKLIST.md](AGENT_ONBOARDING_CHECKLIST.md) — **READ THIS FIRST** — step-by-step reading order, verification steps, and quick-reference rules

**Required Reading (in order per onboarding checklist):**
1. This file (`PROJECT_STATE_DIGEST.md`) — What's built, test counts, module inventory
2. [AGENT_DEVELOPMENT_GUIDELINES.md](AGENT_DEVELOPMENT_GUIDELINES.md) — Coding standards, pitfall avoidance
3. [AGENT_COMMUNICATION_PROTOCOL.md](AGENT_COMMUNICATION_PROTOCOL.md) — How to flag concerns, gates, scope creep
4. [PROJECT_COHERENCE_DOCTRINE.md](PROJECT_COHERENCE_DOCTRINE.md) — Architectural constraints, scope boundaries
5. [KNOWN_TECH_DEBT.md](KNOWN_TECH_DEBT.md) — Things that look broken but are intentionally deferred

**Failure to follow the onboarding checklist results in code reverts and scope reductions.**

---

## Canonical Project Plan Reference

**CANONICAL EXECUTION PLAN (Plan v2 — ACTIVE):**
- [EXECUTION_PLAN_V2_POST_AUDIT.md](docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md) — Active execution plan (4 phases: Brain→Content Breadth→Session Playability→Playtest). Approved by PO 2026-02-11. Phase 1 COMPLETE (A8 PASSED). Phase 2 Batch 1 COMPLETE. Phase 2 Batch 2 DISPATCHED.

**PRIOR PLANS (Historical):**
- [EXECUTION_PLAN_DRAFT_2026_02_11.md](docs/planning/EXECUTION_PLAN_DRAFT_2026_02_11.md) — Plan v1 (7-step). All 26 WOs complete. Closed.
- [AIDM_EXECUTION_ROADMAP_V3.md](docs/AIDM_EXECUTION_ROADMAP_V3.md) — Prior roadmap. M0-M4 milestones. Superseded by execution plan but capability gates remain in force.

**DESIGN LAYER (FROZEN):**
- [DESIGN_LAYER_ADOPTION_RECORD.md](docs/design/DESIGN_LAYER_ADOPTION_RECORD.md) — Formal design freeze
- docs/design/*.md — 6 frozen design documents

**No ambiguity. The Execution Plan is the active source of truth for project direction and work order sequencing. Capability gates from Roadmap V3 remain enforced.**

---

## Capability Gate Status (Current)

| Gate ID | Gate Name | Status |
|---------|-----------|--------|
| G-T1 | Tier 1 Mechanics | OPEN |
| G-T2A | Permanent Stat Mutation | CLOSED |
| G-T2B | XP Economy | CLOSED |
| G-T3A | Entity Forking | CLOSED |
| G-T3B | Agency Delegation | CLOSED |
| G-T3C | Relational Conditions | CLOSED |
| G-T3D | Transformation History | CLOSED |

**Gate enforcement:** Implementation of mechanics blocked by CLOSED gates is FORBIDDEN.

---

## Currently Legal Capabilities

**Only Tier 1 mechanics are currently legal.** Unlocked by G-T1:
- Combat resolution (attack, full attack, critical hits)
- Initiative and action economy
- Attacks of opportunity (movement-triggered)
- Conditions and status effects (non-relational, non-permanent)
- Targeting and visibility
- Saving throws and defensive resolution
- Spellcasting (20 spells, levels 0-5, SpellResolver pipeline)

**All Tier 2 and Tier 3 mechanics are FORBIDDEN.**

---

## Frozen Contracts (v0.3.0-post-audit-m3)

**Effective Date:** 2026-02-09 (commit f720744, tag v0.3.0-post-audit-m3)

Frozen modules may NOT be modified without an explicit CP (design rationale + breaking change assessment + migration path + full test coverage).

- **Immersion Layer**: All `aidm/immersion/` modules + `aidm/schemas/immersion.py` (hardened via Plan C)
- **Audit Remediation Schemas**: targeting.py, visibility.py, entity_fields.py, engine_result.py, intent_lifecycle.py, campaign.py
- **Replay & Determinism**: event_log.py, rng_manager.py, state.py, replay_runner.py (foundational invariant)
- **Narration Layer**: narrator.py (55 templates, stable structure)

**Contract Violation Protocol:** Create CP design doc → breaking change assessment → migration path → test plan → approval → update this section. Violations result in code reverts.

---

## Structural Kernel Register (SKR) Status

**Tier 0:** SKR-002 (Permanent Stat Modification) — Phase 3 COMPLETE. SKR-008, SKR-001 — Design only.
**Tier 1:** SKR-003, SKR-005, SKR-010 — Deferred.
**Tier 2+:** SKR-004, SKR-011, SKR-007, SKR-009, SKR-012 — Deferred.

---

## Key Design Principles (Locked)

1. **Determinism First**: All randomness deterministic, stable serialization, reproducible replay
2. **Event Sourcing**: State derived from append-only log, monotonic IDs
3. **Fail-Closed**: Unknown types rejected, missing state causes errors, no silent fallbacks
4. **Provenance & Citations**: All rulings traceable to source material pages
5. **Data-Only Schemas**: Contracts defined before algorithms, validation before implementation
6. **Prep vs Play Separation**: Async prep (slow, thorough), sync play (fast, deterministic)
7. **Voice-First Contracts**: Structured intents, not free-form NLU
8. **No Mercy Caps**: Doctrine is capability gating, not fairness balancing

---

## Non-Goals (Explicitly Out of Scope)

- Real-time gameplay optimization
- NLP/semantic search (keyword-based only)
- Rule interpretation (retrieves text, doesn't parse rules)
- Campaign planning UI/workflows
- Production ASR/TTS (structured intents only)
- UI implementation (contracts only)
- LLM dependency in deterministic runtime

---

## Critical Invariants

- All tests must pass in < 5 seconds (currently ~46s at 3452 tests — rule predates scale)
- All serialization must use sorted keys (deterministic JSON)
- Event IDs must be strictly monotonic
- RNG streams must remain isolated (combat, initiative, policy, saves)
- State mutations only through replay runner's single reducer
- Entity field access via EF.* constants (bare strings FORBIDDEN)
- State mutation via deepcopy() (shallow copy FORBIDDEN)
- Bundle validation must be fail-closed
- **M2 Invariant: SPARK_SWAPPABLE = ACTIVE** — SPARK must be user-swappable via config

---

## Governance Documents (M2+)

- [SPARK_SWAPPABLE_INVARIANT.md](docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md) — Core M2 invariant
- [SPARK_PROVIDER_CONTRACT.md](docs/specs/SPARK_PROVIDER_CONTRACT.md) — Provider interface contract
- [M2_PR_GATE_CHECKLIST.md](docs/governance/M2_PR_GATE_CHECKLIST.md) — 10 mandatory PR gate checks
- [audit_spark_swappability.sh](scripts/audit_spark_swappability.sh) — Automated audit script

---

## Future Work Queue

**No work items are greenlit for implementation.** All future work requires explicit authorization.

### Phase 2 Batch 1 — COMPLETE (2026-02-11)

All Batch 1 WOs integrated and tested. 3452 tests passing, 0 failed, 11 skipped (hardware-gated).

| WO | Description | Dispatch File | Status |
|----|-------------|---------------|--------|
| WO-032 | NarrativeBrief Assembler (Lens layer) | pm_inbox/reviewed/OPUS_WO-032_NARRATIVE_BRIEF_DISPATCH.md | **INTEGRATED** (45 tests, 3452 total) |
| WO-034 | Core Feat System (15 feats) | pm_inbox/reviewed/OPUS_WO-034_CORE_FEAT_SYSTEM_DISPATCH.md | **INTEGRATED** (41 tests, 3452 total) |
| WO-035 | Skill System (7 skills) | pm_inbox/reviewed/OPUS_WO-035_SKILL_SYSTEM_DISPATCH.md | **INTEGRATED** (30 tests, 3452 total) |
| WO-037 | Experience and Leveling | pm_inbox/reviewed/OPUS_WO-037_EXPERIENCE_LEVELING_DISPATCH.md | **INTEGRATED** (34 tests, 3452 total) |

### Phase 2 Batch 2 — DISPATCHED (2026-02-11)

Dependencies satisfied. Both WOs dispatched for parallel implementation.

| WO | Description | Dispatch File | Dependency | Status |
|----|-------------|---------------|-----------|--------|
| WO-033 | Spark Integration Stress Test (~40 tests) | pm_inbox/OPUS_WO-033_SPARK_STRESS_TEST_DISPATCH.md | WO-032 | **DISPATCHED** |
| WO-036 | Expanded Spell Registry (~33 new spells, ~50 tests) | pm_inbox/OPUS_WO-036_EXPANDED_SPELLS_DISPATCH.md | WO-035 | **DISPATCHED** |

### Phases 3-4 — FUTURE (awaiting Phase 2 A9 gate)

See EXECUTION_PLAN_V2_POST_AUDIT.md for full WO definitions (WO-038 through WO-044).

---

## Completion Protocol

Every instruction packet completion summary must include:

1. **Packet ID**: CP-XX identifier
2. **Tasks Completed**: List of all tasks in packet
3. **Files Changed**: New/modified modules and tests
4. **Tests Affected**: Count change (e.g., 164 → 199)
5. **PSD Update Block**: Exact text to append to this file

Format:
```
## CP-XX Update

### Changes
- [List of locked systems added]
- [Test count: X → Y]
- [Module inventory changes]

### Packet History Entry
- CP-XX: [Brief description]
- Status: COMPLETE
```

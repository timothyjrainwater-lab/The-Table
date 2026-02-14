<!--
PROJECT STATE DIGEST — CANONICAL STATE SNAPSHOT

UPDATE RULES:
- Factual only — no discussion, no design speculation
- Single source of truth for operational project state
- Fresh agents should start with PROJECT_COMPASS.md (rehydration hub), then use this file for operational detail
- Format: Markdown with stable section ordering
- REHYDRATION COPY: After editing this file, also update pm_inbox/aegis_rehydration/PROJECT_STATE_DIGEST.md

SIZE GATE: This file must not exceed 500 lines. If an update would push
it past 500, compress existing sections before adding new content. The PM
is responsible for enforcing this gate on every PSD update.

PSD UPDATE PROTOCOL (compression-on-integration):
When a WO is INTEGRATED, the PM updates the PSD as follows:
  1. Add a COMPRESSED entry (3-5 lines max) to Locked Systems
  2. Update the test count total in Test Count section
  3. Update the Future Work Queue status table
  4. Do NOT add a detailed history entry — the Locked Systems summary IS the record
  5. If the update would breach 500 lines, compress older Locked Systems entries first
  6. Sync the rehydration copy (pm_inbox/aegis_rehydration/PROJECT_STATE_DIGEST.md)
Field-level detail belongs in source code and WO dispatch docs, not here.

LAST UPDATED: 2026-02-14 — **RED BLOCK: Bone-layer formula verification in progress. ALL feature work, bug fixes, playtesting, and builder dispatches BLOCKED until verification GREEN.** See `docs/verification/BONE_LAYER_VERIFICATION_PLAN.md`. 303 formulas across 9 domains, 22 files. 5510 tests collected, 16 skipped (hardware-gated).
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
- **20 existing spells** + **33 new spells (WO-036)** = 53 total in spell_definitions.py (levels 0-5)
- **Concentration integration** (WO-035): check_concentration_on_damage() DC = 10 + damage

### WO-036: Expanded Spell Registry (33 New Spells)
- **53 total spells** (levels 0-5): 4 cantrips, 6 L1, 7 L2, 5 L3, 6 L4, 5 L5
- **Purely declarative**: SpellDefinition entries only, no resolver/tracker/rasterizer changes
- **3 concentration spells**: Stinking Cloud, Wall of Fire, Telekinesis
- **50 tests** in test_expanded_spells.py

### WO-033: Spark Integration Stress Test (Complete)
- **40 tests** in test_spark_integration_stress.py: NarrativeBrief containment (8), kill switch registry (8), template fallback (4), gold master compatibility (4), mock adapter (4), determinism verification (8), GPU performance (4 — hardware-gated skip)
- **Full coverage**: All 6 test categories delivered. 36 pass, 4 skipped (GPU-gated).

### WO-038: Intent Bridge (Phase 3)
- **IntentBridge**: Translates player-facing names → entity IDs, weapon objects, spell IDs
- **ClarificationRequest**: Frozen dataclass for ambiguity handling (target/weapon/spell not found or ambiguous)
- **BL-020 compliant**: FrozenWorldStateView for all lookups, no state mutation
- **27 tests** in test_intent_bridge.py

### WO-040: Scene Management (Phase 3)
- **SceneManager**: Scene transitions, encounter triggers (delegates to Box initiative), D&D 3.5e rest healing
- **Rest mechanics**: 1 HP/level (8hrs), 2 HP/level (long-term care), 1.5x/level (bed rest) — PHB p.146, NOT 5e
- **Data structures**: SceneState, Exit, EncounterDef, LootDef, TransitionResult, EncounterResult, RestResult
- **31 tests** in test_scene_manager.py

### WO-041: DM Personality Layer (Phase 3)
- **DMPersona**: System prompt builder with ToneConfig (gravity/verbosity/drama 0-1), NPC voice mapping (Kokoro TTS)
- **Containment**: No entity IDs, HP, AC in prompts — NarrativeBrief containment enforced
- **Presets**: default, gritty, theatrical, humorous, terse DM personas
- **32 tests** in test_dm_persona.py

### WO-039 + WO-045: Session Orchestrator with Box Integration (Phase 3)
- **SessionOrchestrator**: Full turn cycle conductor — STT → IntentBridge → Box (`play_loop.execute_turn`) → NarrativeBrief → DMPersona + Narration → TTS
- **Box wiring (WO-045)**: Attack/spell commands delegate to canonical `play_loop.execute_turn()` — real d20 rolls, HP mutations, defeat detection. NarrativeBrief built from real Box events (hit/miss, damage, severity, defeat), not declared intents.
- **Keyword parser**: parse_text_command() for attack/cast/move/rest/go (NOT NLU)
- **Error recovery**: STT failure → text fallback, TTS failure → text-only, Spark failure → template narration
- **Windshield tests**: Determinism (same seed), HP mutation proof, narration-reflects-outcome, real d20 data, defeat propagation, RNG variance
- **42 tests** in test_session_orchestrator.py (36 original + 6 windshield), lives in `aidm/runtime/` (BL-004 compliant)

### WO-046: Box Event Contracts (Phase 3)
- **box_events.py**: 10 frozen dataclass schemas for Box→Lens boundary events (attack_roll, damage_roll, hp_changed, entity_defeated, spell_cast, save_rolled, turn_start/end, condition_applied/removed)
- **Boundary validation**: `validate_event_payload()` at orchestrator extraction point — typed payloads replace raw dict access
- **Contract registry**: PAYLOAD_SCHEMAS maps event_type strings to schema classes; unknown events pass through as dicts
- **24 tests** in test_box_event_contracts.py (10 construction + 8 validation + 6 integration)

### P2: Multi-Room Scene Persistence Stress Test (Phase 3)
- **3-room mini dungeon**: Room A (combat) → Room B (rest) → Room C (encounter trigger)
- **State continuity**: HP/defeat status persists across transitions, state hash stable through navigation, rapid round-trips produce no drift
- **Determinism**: Same seed + same actions → identical final state after full dungeon traversal
- **18 tests** in test_multi_room_persistence.py (6 persistence + 5 combat/rest flow + 4 full traversal + 3 edge cases)

### P1: Integration-Layer Replay Stability (Phase 3)
- **Event payload equality**: Same seed + same commands → identical event payloads (full dict comparison, not just state hash)
- **NarrativeBrief round-trip**: to_dict → JSON → from_dict preserves all 13 fields; real orchestrator briefs survive serialization
- **Event ordering invariants**: turn_start always first, turn_end always last, attack_roll→damage_roll→hp_changed→entity_defeated causal order enforced
- **Finding**: spell_cast `cast_id` uses uuid.uuid4() (non-deterministic correlation ID) — excluded from payload equality, documented
- **13 tests** in test_replay_stability.py (4 payload equality + 4 serialization round-trip + 5 ordering invariants)

### P3: Box Fallback Validation (Phase 3)
- **Box error handling**: try/except added around both `box_execute_turn()` calls in SessionOrchestrator (`_process_attack`, `_process_spell`)
- **State preservation**: Box exception → world_state remains unchanged, no partial mutation
- **Session continuity**: Session remains usable for subsequent turns after Box failure recovery
- **5 tests** in test_session_orchestrator.py Category 7 (attack/spell failure, state preservation, session recovery, turn count integrity)

### WO-048: Template Interpolation Fix (Post-A10)
- **Pipeline fix**: `_build_template_context()` pure function maps NarrativeBrief + events → template placeholders (actor/target/weapon/damage)
- **Entity names**: Real names (not "The attacker"/"the target") flow through metadata to template system
- **weapon_name fix**: Uses `EF.WEAPON` (e.g. "longsword") instead of `damage_type` ("slashing")
- **Coverage**: Added templates for `movement`, `scene_transition`, `rest` tokens
- **14 tests** in test_template_narration_contract.py (5 context + 5 snapshot + 3 forbidden-token + 1 provenance)

### WO-049: Severity-Branched Template Narration (Post-A10)
- **SEVERITY_TEMPLATES**: Combat tokens branch by severity (minor/moderate/severe/devastating/lethal)
- **Deterministic selection**: Severity from `compute_severity()` (HP percentage), no RNG
- **Scoped**: Only combat tokens (`attack_hit`, `attack_miss`) branched; all other tokens use flat templates
- **Flavor upgrade**: Movement/transition/rest templates use atmospheric language
- **4 tests** in test_template_narration_contract.py (severity branch + flat fallback + non-combat ignore + lethal integration)

### WO-050: Kokoro TTS Wiring (Post-A10)
- **KokoroTTSAdapter**: Updated for real model paths (model_path, voices_path), per-instance lazy loader
- **Protocol compatibility**: synthesize() accepts VoicePersona, str, or None — satisfies both TTSAdapter and TTSProtocol
- **Model**: kokoro-v1.0.int8.onnx (88MB, CPU-only), voices-v1.0.bin (27MB), ~1x real-time on CPU
- **5 integration tests** in test_kokoro_tts.py (real synthesis, all 8 personas, speed variation, long text, string persona)

### Wave 1: Foundation Schemas & Bugfixes (2026-02-13)
- 6 WOs: AD007-IMPL (presentation semantics, 37 tests), BUGFIX-BATCH (STM/clarification/AoO/intent fixes, 13 tests), CONTENT-PACK-SCHEMA (creature/feat templates + loader, 42 tests), RULEBOOK-MODEL (rule entries + registry, 31 tests), VOCAB-REGISTRY (vocabulary + taxonomy, 36 tests), OSS-REVISE (docs only).

### Wave 2: Content Extraction (2026-02-13)
- 3 WOs: CONTENT-EXTRACT-001 (605 spells, 25 tests), CONTENT-EXTRACT-002 (273 creatures, 36 tests), CONTENT-EXTRACT-003 (109 feats, 35 tests). All IP-clean templates in `aidm/data/content_pack/`.

### Wave 3: World Compiler + Backend (2026-02-13)
- 7 WOs: WORLDCOMPILE-SCAFFOLD-001 (pipeline harness + Stage 0/8, 52 tests), WORLDCOMPILE-LEXICON-001 (Stage 1 name gen, 25 tests), WORLDCOMPILE-SEMANTICS-001 (Stage 3 mechanical→semantics, 58 tests), WORLDCOMPILE-NPC-001 (Stage 4 archetypes + doctrine, 44 tests), DISCOVERY-BACKEND-001 (knowledge events + tier progression, 39 tests), VOICE-RESOLVER-001 (keyword extraction, 23 tests), WEBSOCKET-BRIDGE-001 (ws protocol + ASGI app, 28 tests).

### Playable CLI + Playtest Infrastructure (2026-02-13)
- **play.py**: Terminal combat CLI — keyword parser (attack/cast/move/status/help), IntentBridge resolution, execute_turn wiring, enemy AI, event formatting, transcript autologging to `runtime_logs/`. 3v3 party fixture (Fighter/Cleric/Rogue vs 3 Goblins).
- **WO-ENCOUNTER-01**: Expanded fixture from 1v1 to 3v3 with alternating initiative, unique goblin names, standalone 1v1 test fixtures for unit test isolation.
- **WO-OPS-HYGIENE-01**: Session bootstrap hardened — play.py process detection, dirty-tree RED warnings for tracked files.
- **Playtest tooling**: `scripts/verify_session_start.py` (session bootstrap + hygiene gate), `scripts/record_playtest.py`, `scripts/triage_latest_playtest.py`.
- **89 tests** in test_play_cli.py (parser, combat logic, display formatting, CLI smoke, golden transcript, determinism, crash regression, round tracking, full attack, maneuvers, expanded status, AoO display).

### Phase 4C Waves A+B: CLI Capability Wiring (2026-02-13)
- **Wave A**: WO-CONDFIX-01 (condition storage format fix), WO-ROUND-TRACK-01 (round counter display).
- **Wave B**: WO-FULLATTACK-CLI-01 (full attack pipeline), WO-MANEUVER-CLI-01 (6 maneuver commands), WO-STATUS-EXPAND-01 (HP/AC/BAB/conditions display), WO-AOO-DISPLAY-01 (AoO event rendering), WO-VOICE-SIGNAL-01 (440Hz chime + sentence chunking).
- **133 tests** across test_play_cli.py (89) + test_speak_signal.py (18) + test_initiative_cli.py (15) + condition gold masters.

### Movement v1 — CP-16: Multi-Square Movement (2026-02-13)
- **FullMoveIntent**: Schema with path contiguity validation, 5/10/5 diagonal cost rule (PHB p.148), terrain cost multiplier support.
- **Dijkstra pathfinding**: Cost-optimal pathfinding in `movement_resolver.py` — enemy blocking, ally pass-through, speed enforcement via `EF.BASE_SPEED`, orthogonal-first deterministic tie-breaking.
- **Integration**: `play_loop.py` routes FullMoveIntent with per-square AoO + defeat abort. `play.py` CLI `move X Y` command, enemy AI moves toward closest target before attacking. `play_controller.py` fixture entities populated with `EF.BASE_SPEED` (30ft standard, 20ft cleric heavy armor).
- **49 tests** in test_movement_v1.py (schema, pathfinding, build_full_move_intent, play_loop execution, enemy AI, CLI integration, step cost, occupied squares).

### Action Economy Audit (2026-02-13)
- **docs/research/ACTION_ECONOMY_AUDIT.md**: Complete mechanical inventory — 13 sections covering movement, action economy, attacks, AoO, maneuvers, combat state machine, entity model, feats, spellcasting.
- **10 correctness bugs identified** (4 HIGH): BUG-1 two-handed STR 1.5x, BUG-2 full attack overkill, BUG-3 prone AC not melee/ranged-differentiated, BUG-4 helpless AC same issue. Tier 0-4 priority ranking.
- **Contamination matrix**: Documents which systems can/cannot be meaningfully playtested with current movement implementation.

### Signal Voice — Operator TTS Pipeline (2026-02-13)
- **scripts/speak.py**: Three-engine pipeline — Kokoro (voice design, CPU) -> Chatterbox (GPU render, voice cloning) -> winsound (playback). Kokoro CPU fallback if no GPU.
- **Voice profile "Arbor"**: am_michael seed, speed 0.88, exaggeration 0.15, Chatterbox Original tier. Calm, grounded, neutral-operational readback.
- **Reference clips**: Kokoro fp32 24kHz native (no downsample) in `models/voices/signal_reference_*.wav`. Three voice seeds tracked (michael, adam, george).
- **Volume**: 50% default, PCM-level attenuation. CLI: `python scripts/speak.py "message"`.

---

## Test Count

**Total: 5510 tests collected** (16 skipped hardware-gated)

> **Canonical counts are machine-generated.** Run `python scripts/audit_snapshot.py` or see [`docs/STATE.md`](docs/STATE.md) for verified numbers. The counts above may be stale.

---

## Module Inventory

> Per-file listings omitted for context weight. Use `ls aidm/core/`, `ls aidm/schemas/`, etc. for current inventory.

**Directory structure:**
- `aidm/core/` — 28+ modules: resolvers, engine, infrastructure, pipeline + `world_compiler.py`, `compile_stages/` (lexicon, semantics, npc_archetypes)
- `aidm/schemas/` — 30+ modules: data contracts for all subsystems + content_pack, rulebook, vocabulary, presentation_semantics, npc_archetype, world_compile, knowledge_mask, asset_binding, ws_protocol
- `aidm/rules/` — legality_checker.py
- `aidm/ui/` — character_sheet.py (CharacterData, CharacterSheetUI, PartySheet)
- `aidm/narration/` — narrator.py (55 templates), play_loop_adapter.py, guarded_narration_service.py
- `aidm/lens/` — narrative_brief.py, context_assembler.py, scene_manager.py, content_pack_loader.py, discovery_log.py, presentation_registry.py, rulebook_registry.py, vocabulary_registry.py, voice_resolver.py
- `aidm/interaction/` — intent_bridge.py (WO-038)
- `aidm/runtime/` — session.py, session_orchestrator.py, bootstrap.py, runner.py, display.py, ipc_serialization.py, play_controller.py
- `play.py` — Playable CLI entry point (keyword parser, turn execution, enemy AI, event display, transcript autologging)
- `scripts/` — verify_session_start.py, record_playtest.py, triage_latest_playtest.py, audit_snapshot.py, speak.py (operator signal voice)
- `aidm/immersion/` — 8 modules: stt/tts/image adapters, audio_mixer, contextual_grid, attribution, clarification_loop, voice_intent_parser, chatterbox_tts_adapter
- `aidm/spark/` — model_registry, spark_adapter, llamacpp_adapter, grammar_shield, dm_persona
- `aidm/server/` — app.py (Starlette ASGI + WebSocket route)
- `aidm/services/` — discovery_log.py (services-tier)
- `aidm/data/content_pack/` — spells.json (605), creatures.json (273), feats.json (109)
- `tools/` — extract_spells.py, extract_monsters.py, extract_feats.py, verify_spell_bridge.py + data/
- `tests/` — 100+ test files
- `Vault/` — D&D 3.5e rules knowledge base (~23,750 files, NOT AIDM code, do NOT modify without WO)

---

## Instruction Packet History

> **TRIMMED:** Full CP/WO history removed for context weight reduction. All completed work is reflected in the Locked Systems section above. For detailed CP history, see individual CP decision documents in `docs/` or the git log.

---

## MANDATORY FIRST READ FOR ALL AGENTS

**START HERE:**
- [PROJECT_COMPASS.md](PROJECT_COMPASS.md) — **READ THIS FIRST** — rehydration hub covering thesis, architecture, what's real, roadmap, conventions, and deep dive pointers
- [AGENT_ONBOARDING_CHECKLIST.md](AGENT_ONBOARDING_CHECKLIST.md) — Step-by-step reading order, verification steps, and quick-reference rules

**Required Reading (in order per onboarding checklist):**
1. [PROJECT_COMPASS.md](PROJECT_COMPASS.md) — Rehydration hub (summary of everything)
2. This file (`PROJECT_STATE_DIGEST.md`) — Detailed operational state, locked systems, capability gates
3. [AGENT_DEVELOPMENT_GUIDELINES.md](AGENT_DEVELOPMENT_GUIDELINES.md) — Coding standards, pitfall avoidance
4. [AGENT_COMMUNICATION_PROTOCOL.md](AGENT_COMMUNICATION_PROTOCOL.md) — How to flag concerns, gates, scope creep
5. [KNOWN_TECH_DEBT.md](KNOWN_TECH_DEBT.md) — Things that look broken but are intentionally deferred

**Failure to follow the onboarding checklist results in code reverts and scope reductions.**

---

## Canonical Project Plan Reference

**Active plan:** [EXECUTION_PLAN_V2_POST_AUDIT.md](docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md) — Phases 1-3 COMPLETE. Phase 4 ACTIVE.
**Phase 4C detail:** [PHASE4C_FORWARD_PROGRESSION.md](docs/planning/PHASE4C_FORWARD_PROGRESSION.md) — 10-WO package, 3 waves.
**Prior plans:** Plan v1 (closed), Roadmap V3 (superseded, capability gates still enforced).
**Design layer:** Frozen. See [DESIGN_LAYER_ADOPTION_RECORD.md](docs/design/DESIGN_LAYER_ADOPTION_RECORD.md).

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
- Spellcasting (53 spells, levels 0-5, SpellResolver pipeline)

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

Real-time gameplay optimization, NLP/semantic search, rule interpretation (retrieves text only), campaign planning UI, production ASR/TTS (structured intents only), UI implementation (contracts only), LLM dependency in deterministic runtime.

---

## Critical Invariants

- All tests must pass within <25ms avg / <120s total (see docs/STATE.md for current actuals)
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

### Phases 1-3 + Post-A10 + Waves 1-3 + Phase 4A/4B — COMPLETE

All Phase 1-3, Post-A10, Wave 1-3, and Phase 4A/4B integrated. See Locked Systems for details. Canceled: WO-CODE-INTENT-002, WO-INTENT-002 (superseded).

### Phase 4C — CLI Capability Wiring — See `docs/planning/PHASE4C_FORWARD_PROGRESSION.md`

| WO | Wave | Description | Status |
|----|------|-------------|--------|
| WO-CONDFIX-01 | A | Fix condition storage format mismatch | INTEGRATED |
| WO-ROUND-TRACK-01 | A | Round counter display in CLI | INTEGRATED |
| WO-FULLATTACK-CLI-01 | B | Full attack action in CLI | INTEGRATED |
| WO-MANEUVER-CLI-01 | B | Combat maneuver parsing (6 types) | INTEGRATED |
| WO-STATUS-EXPAND-01 | B | Expanded status display (AC, BAB, conditions) | INTEGRATED |
| WO-AOO-DISPLAY-01 | B | AoO event display in CLI | INTEGRATED |
| WO-VOICE-SIGNAL-01 | B | Agent-triggered voice signal on WO completion | INTEGRATED |
| CP-16 (retroactive) | — | Movement v1: multi-square Dijkstra pathfinding | INTEGRATED |
| WO-SPELLSLOTS-01 | C | Spell slot tracking (blocked — CP for entity_fields.py) | BLOCKED |
| WO-SPELLLIST-CLI-01 | C | Spell list display in CLI | QUEUED |
| WO-CHARSHEET-CLI-01 | C | Character sheet display in CLI | QUEUED |

### Tier 0 Correctness Bugs — See `docs/research/ACTION_ECONOMY_AUDIT.md` Section X

| Bug ID | Description | Severity | WO Status |
|--------|-------------|----------|-----------|
| BUG-1 | Two-handed STR 1.5x not applied | HIGH | WO-BUGFIX-TIER0-001 DISPATCHED |
| BUG-2 | Full attack doesn't stop on target death | HIGH | WO-BUGFIX-TIER0-001 DISPATCHED |
| BUG-3 | Prone AC not differentiated melee/ranged | HIGH | WO-BUGFIX-TIER0-001 DISPATCHED |
| BUG-4 | Helpless AC not differentiated melee/ranged | HIGH | WO-BUGFIX-TIER0-001 DISPATCHED |

### Standalone + Research — WO-OSS-DICE-001 FUTURE. 5 WO-RQ research artifacts anchored (see `docs/planning/research/`). Voice research fleet (WO-VOICE-RESEARCH-01..05) delivered.

---

## Completion Protocol

When a WO is INTEGRATED, the PM updates this file per the PSD Update Protocol in the header:

1. **Locked Systems**: Add 3-5 line compressed entry (name, key capabilities, test count, files)
2. **Test Count**: Update total
3. **Future Work Queue**: Update status table (DISPATCHED → INTEGRATED)
4. **Size gate**: Verify file stays under 500 lines. If not, compress older entries first.
5. **Sync**: Copy to pm_inbox/aegis_rehydration/PROJECT_STATE_DIGEST.md

**Do NOT:**
- Add detailed field-by-field, method-by-method history entries
- Duplicate information already in source code or WO dispatch docs
- Append without checking the 500-line gate

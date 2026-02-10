<!--
PROJECT STATE DIGEST — CANONICAL STATE SNAPSHOT

UPDATE RULES:
- Updated at the end of every instruction packet (CP-XX)
- Factual only — no discussion, no design speculation
- Single source of truth for project state
- Paste this file to refresh any agent completely
- Format: Markdown with stable section ordering

LAST UPDATED: M1 Infrastructure (1725 tests passing in ~7s)
NOTE: M1 work orders WO-M1-01 through WO-M1-06 complete. Replay reducer, BL-017/018/020 boundary laws, spark adapter, hardware detection, audio queue, guarded narration, IPC serialization, IPC runtime integration, pm_inbox workflow. Documentation spring cleaning removed 17 superseded files (6,775 lines). Root cleanup: torrent remnants deleted, REUSE_DECISION.json moved to config/. All 1725 tests passing with zero regressions.
-->

# Project State Digest

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
- **Position (CP-001)**: Canonical 2D grid position type with 1-2-1-2 diagonal distance (PHB p.148), immutable, hashable
- **Legacy types (DEPRECATED)**: GridPoint (targeting.py, intents.py), GridPosition (attack.py) - will be removed in CP-002
- **NOTE**: DeclaredAttackIntent (voice layer) is distinct from attack.AttackIntent (combat resolution)

### M1 Runtime Layer (Solo Vertical Slice v0)
- **IntentObject**: Player intent with lifecycle management (PENDING → CLARIFYING → CONFIRMED → RESOLVED)
- **IntentStatus**: 5 lifecycle states with transition validation
- **ActionType**: M1 action types (ATTACK, MOVE, USE_ABILITY, END_TURN, CAST_SPELL, BUY, REST)
- **Immutability enforcement**: Intent frozen after CONFIRMED status, only resolution fields modifiable
- **Required field validation**: Per-action-type field requirements (ATTACK needs target_id + method, etc.)
- **EngineResult**: Immutable authoritative resolution output (result_id, status, events, rolls, state_changes)
- **EngineResultBuilder**: Mutable builder for incremental result construction
- **RollResult**: Individual dice roll with RNG offset for replay verification
- **StateChange**: Atomic state change (entity_id, field, old_value, new_value)
- **SessionLog**: Intent-to-result correlation with JSONL serialization
- **ReplayHarness**: Deterministic replay verification with 10× verification capability
- **CharacterSheet UI**: Read-only character view with derived value computation
- **PartySheet**: Aggregate party status display
- **Narrator**: Template-based narration from EngineResult narration tokens
- **NarrationTemplates**: Deterministic fallback templates (55 templates: attack, maneuver, save, environmental, mounted, etc.)
- **Contract docs**: IPC_CONTRACT.md, INTENT_LIFECYCLE.md, ENGINE_RESULT_CONTRACT.md
- **Reference**: docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md (LLM cage doctrine)

### M2 Campaign Prep Pipeline v0
- **SessionZeroConfig**: Ruleset capture + boundary configuration (alignment mode, prep depth, amendments)
- **CampaignPaths**: Directory layout convention (events.jsonl, intents.jsonl, assets/, prep/)
- **CampaignManifest**: Version-pinned campaign metadata (campaign_id, title, engine_version, master_seed, session_zero)
- **PrepJob**: Deterministic prep task with idempotency (sha256-based job_id, content_hash for skip detection)
- **AssetRecord**: Campaign asset with deterministic ID and provenance (GENERATED, BUNDLED, MANUAL, SHARED_CACHE)
- **Deterministic IDs**: compute_job_id(), compute_asset_id() — sha256(campaign_id + type + key)[:16], never RNG-driven
- **CampaignStore**: Filesystem-backed campaign persistence (create, load, save, list campaigns)
- **Campaign directory layout**: campaigns/&lt;campaign_id&gt;/manifest.json + events.jsonl + intents.jsonl + assets/ + prep/
- **PrepOrchestrator**: Deterministic prep job queue (INIT_SCAFFOLD → SEED_ASSETS → BUILD_START_STATE → VALIDATE_READY)
- **Idempotent execution**: Jobs store content_hash; re-run skips completed jobs with matching hash
- **Append-only logging**: All job state changes logged to prep/prep_jobs.jsonl (no in-place mutation)
- **Prep depth variation**: Light (2 assets), Standard (4 assets), Deep (6 assets)
- **AssetStore**: Campaign asset management with shared cache resolution
- **Shared cache**: Reusable generic assets across campaigns (copy-on-resolve with provenance tracking)
- **Integrity verification**: Content hash checking for all assets (detect missing/corrupted files)
- **Asset index**: JSON-based index persistence (save_index/load_index)
- **WorldArchive**: Campaign export/import bundle (export → validate → import lifecycle)
- **ExportOptions**: Configurable export (include_assets, include_prep_log)
- **ArchiveValidation**: Pre-import validation (manifest, logs, schema version compatibility)
- **Export/import roundtrip**: Manifest, event logs, and assets survive export → import identically
- **G-T1 only**: No LLM integration, no content generation (all assets are placeholders in M2)
- **Reference**: docs/design/LOCAL_RUNTIME_PACKAGING_STRATEGY.md (LRP-001)
- **SessionBundle**: Scene cards, NPC cards, encounters, assets, citations
- **CampaignBundle**: World facts, factions, NPC index, policy config
- **ReadinessCertificate**: Prep-time validation with ready/blocked status
- **BundleValidator**: Fail-closed validation of all bundle components

### M3 Immersion Layer v1
- **Immersion schemas**: Transcript, VoicePersona, AudioTrack, SceneAudioState, ImageRequest, ImageResult, GridEntityPosition, GridRenderState, AttributionRecord, AttributionLedger
- **STT adapter**: STTAdapter Protocol, StubSTTAdapter (canned transcript, confidence=1.0), create_stt_adapter() factory
- **TTS adapter**: TTSAdapter Protocol, StubTTSAdapter (empty bytes, default "Dungeon Master" persona), create_tts_adapter() factory
- **Audio mixer**: compute_scene_audio_state() pure function (mood from world state: combat/tense/peaceful), StubAudioMixerAdapter (records history)
- **Mood rules**: active_combat → combat, hazards → tense, dark → tense, else → peaceful (checked in order)
- **Transition tracking**: transition_reason recorded when mood changes from previous state
- **Image adapter**: ImageAdapter Protocol, StubImageAdapter (returns placeholder), create_image_adapter() factory
- **Contextual grid**: compute_grid_state() pure function (visible only during active combat)
- **Grid rules**: active_combat → visible/combat_active, was visible → hidden/combat_ended, else → hidden/no_combat
- **Entity positions**: Extracted from entities[*].position, sorted by entity_id, dimensions from max x/y
- **Attribution store**: AttributionStore (add/get_by_asset_id/list_records/save/load), fail-closed validation (asset_id + license required)
- **Attribution JSON**: assets/ATTRIBUTION.json (schema_version 1.0, sorted keys)
- **Protocol pattern**: typing.Protocol with @runtime_checkable for all adapter interfaces
- **Factory pattern**: Registry dict mapping backend names to callables, ValueError for unknown backends
- **Pure functions**: compute_scene_audio_state() and compute_grid_state() are deterministic, side-effect-free
- **Non-authoritative**: All immersion outputs atmospheric only, excluded from deterministic replay, engine never consults immersion state
- **G-T1 only**: No real STT/TTS/image backends (stubs only), real adapters deferred to later milestones
- **Boundary contract**: docs/IMMERSION_BOUNDARY.md (authoritative scope rules for immersion layer)
- **Hardening tests**: Import integrity, 10× determinism proofs across all moods, dependency isolation, non-authority enforcement, attribution validation
- **API stability**: PUBLIC_STABLE annotations in aidm/immersion/__init__.py (16 frozen exports, no removal/rename without migration)
- **Authority contract**: AST-based import boundary analysis (whitelisted/forbidden imports), deepcopy non-mutation tests, output isolation tests
- **Determinism canary**: test_immersion_determinism_canary.py (28 tests × 100 iterations = 2800 function calls, regression detector for RNG/timestamps/UUIDs)
- **Forward-compatibility**: FUTURE_HOOK comments in audio_mixer.py (condition-driven cues, concentration moods) and contextual_grid.py (AoE overlays, terrain rendering)
- **M4 integration notes**: docs/M4_INTEGRATION_NOTES.md (spellcasting integration guidance, schema extension patterns, testing requirements, rollout strategy)
- **Handoff document**: docs/IMMERSION_HANDOFF.md (243 immersion tests, file inventory, API reference, maintenance guide, troubleshooting)
- **Test markers**: @pytest.mark.immersion_fast on all 243 immersion tests (registered in pyproject.toml), sub-millisecond runtime, zero external deps

### CP-001: Position Type Unification (Phase 1)
- **Canonical Position**: Single Position class consolidates 3 legacy types (GridPoint from intents.py, GridPoint from targeting.py, GridPosition from attack.py)
- **Location**: aidm/schemas/position.py (180 lines, fully documented)
- **Immutability**: frozen=True dataclass (hashable, usable in sets/dicts)
- **Methods**: distance_to() with 1-2-1-2 diagonal math (PHB p.145), is_adjacent_to() for 8-directional adjacency (PHB p.137)
- **Serialization**: to_dict() and from_dict() for JSON/event storage with deterministic key ordering
- **Backward compatibility**: from_legacy_gridpoint_intents(), from_legacy_gridpoint_targeting(), from_legacy_gridposition_attack(), to_legacy_dict() conversion helpers (DEPRECATED, remove in CP-002)
- **Validation**: Type checking in __post_init__ (rejects non-integer coordinates)
- **String representation**: __str__ for human-readable "(x, y)" format, __repr__ for debug "Position(x=..., y=...)" format
- **Tests**: 34 unit tests in tests/test_position.py (creation, validation, distance, adjacency, serialization, immutability, equality, hashing, legacy conversion, determinism)
- **Determinism**: PBHA test verifies 10× identical results for distance/adjacency calculations (no floating-point drift, no randomness)
- **Resolves**: TD-001 (Three Duplicate Grid Position Types)
- **Status**: Phase 1 COMPLETE (canonical type introduced, backward-compatible, all 1393 tests passing)
- **Next**: Phase 2 (migrate existing code to use Position, deprecate legacy types in CP-002)

### Monster Tactical Envelope (Doctrine Layer)
- **DoctrineTag**: 13 behavioral tags (mindless_feeder, fanatical, cowardly, etc.)
- **IntelligenceBand**: 9 INT score bands (NO_INT through INT_17_PLUS)
- **WisdomBand**: 4 WIS score bands (LOW through EXCELLENT)
- **TacticClass**: 12 tactical capability gates (focus_fire, retreat_regroup, etc.)
- **MonsterDoctrine**: INT/WIS/tags → allowed/forbidden tactics derivation
- **Doctrine Binding**: Dict-based monster_doctrines_by_id (deterministic, no duplicates)

### Visibility & Targeting Contracts
- **LightLevel**: bright, dim, dark
- **VisionMode**: normal, low_light, darkvision, blindsense, blindsight
- **OcclusionTag**: opaque, heavy_obscurement, light_obscurement
- **VisibilityProfile**: Vision capabilities per creature
- **VisibilityBlockReason**: CANONICAL (in targeting.py): los_blocked, loe_blocked, out_of_range, not_in_line, target_not_visible, out_of_vision_range — re-exported by visibility.py (FIX-02: single source of truth)

### Terrain & Traversal Contracts
- **TerrainTag**: 16 terrain property tags (difficult_terrain, wall_smooth, half_cover, pit, ledge, etc.)
- **TraversalCheckType**: climb, balance, swim, jump
- **TraversalRequirement**: check_type + dc_base + dc_modifiers + citation
- **TerrainCell**: Full terrain properties per grid cell (position, elevation, movement_cost, cover_type, hazards)
- **ElevationDifference**: Query result for elevation comparison (higher ground bonus)
- **FallingResult**: Result of falling event (damage dice, damage rolls, landing position)
- **CoverCheckResult**: Result of checking cover between entities (ac_bonus, reflex_bonus, blocks_aoo, blocks_targeting)

### Policy Variety Config
- **PolicyVarietyConfig**: top_k + temperature + score_band for policy engine variety
- Integrated into CampaignBundle (campaign-wide config)
- Validation: top_k >= 1, temperature > 0, score_band >= 0

### Temporal Contracts (Time, Clocks, Durations)
- **TimeScale**: combat_round, narrative, exploration
- **TimeSpan**: Duration in seconds with common constants (ROUND, MINUTE, HOUR, DAY)
- **GameClock**: Monotonic campaign-global clock (t_seconds + scale)
- **TimeAdvanceEvent**: Time progression events (delta + reason + scale)
- **Deadline**: Time-sensitive events (due_at_t_seconds + failure_consequence + visibility)
- **TimerStatus**: Computed deadline status (remaining_seconds + is_expired)
- **EffectDuration**: Spell/buff/debuff durations (rounds/minutes/hours/days/until_discharged/permanent)
- **AmbientLightSchedule**: Scheduled light level changes (strictly increasing times)
- **LightSource**: Point light sources with radius and optional expiration
- Integrated into SessionBundle: initial_clock, deadlines, active_effects
- Integrated into SceneCard: ambient_light_schedule

### Environmental Hazards & Exposure (Schema-Only)
- **HazardIntervalUnit**: round, minute, hour, day
- **HazardEffectType**: damage, condition, visibility, mixed
- **EnvironmentalHazard**: Deterministic time-indexed hazards (interval + effect type + escalation)
- **HazardStage**: Single stage in hazard progression
- **HazardProgression**: Ordered escalating stages (strictly increasing indices)
- **ExposureType**: heat, cold, smoke, toxic_fumes, suffocation, drowning
- **EnvironmentalCondition**: Exposure with hazard reference and mitigation sources (descriptive only)
- Integrated into SceneCard: environmental_hazards, environmental_conditions
- Validator: hazard ID uniqueness, hazard_ref validity, DMG citation requirements

### Obsidian Integration (Optional)
- **Obsidian URI Helpers**: build_obsidian_uri, build_rulebook_page_note_path
- **Citation Enhancement**: with_obsidian_uri helper
- No runtime dependency on Obsidian

### Tactical Policy Engine (Deterministic Tactic Selection)
- **TacticCandidate**: Data-only tactic candidate (tactic_class + target_ids + position_ref)
- **ScoredTactic**: Candidate with integer score + reasons (no floating point)
- **TacticalPolicyTrace**: Full evaluation trace (inputs, features, scoring, selection)
- **TacticalPolicyResult**: Status (ok/requires_clarification/no_legal_tactics) + ranked + selected + trace
- **evaluate_tactics()**: Main entrypoint for tactic evaluation
- **extract_features()**: WorldState feature extraction (HP bands, nearby threats, conditions)
- **generate_candidates()**: Doctrine-filtered candidate generation (deterministic ordering)
- **score_candidate()**: Integer-based heuristic scoring (basis points scale)
- **select_tactic()**: Greedy or variety-based selection with policy RNG stream isolation
- Policy RNG stream completely isolated from combat RNG
- Fail-closed: missing actor returns requires_clarification
- Deterministic: same inputs → identical ranked list and selection
- NO RESOLUTION LOGIC: produces scored choices only, does not apply effects

### Campaign Memory & Character Evidence Ledger (Schema-Only)
- **SessionLedgerEntry**: High-level session summary (write-once record)
- **EvidenceType**: 15 descriptive evidence types (harm_inflicted, mercy_shown, betrayal, etc.)
- **AlignmentAxisTag**: 6 alignment axis tags (lawful, chaotic, good, evil, neutral_lc, neutral_ge)
- **CharacterEvidenceEntry**: Behavioral evidence for characters (descriptive, no alignment scoring)
- **EvidenceLedger**: Campaign-wide evidence ledger (deterministic ordering by character_id, session_id, id)
- **ClueCard**: Investigation clue tracking (unresolved/partial/resolved status)
- **ThreadRegistry**: Campaign mystery and clue thread registry (deterministic ordering by id)
- Integrated into CampaignBundle: session_ledger, evidence_ledger, thread_registry
- Validator: unique ID checks, session reference validation, event_id range validation
- Fail-closed: unknown evidence types/alignment tags/clue statuses rejected
- NO EVALUATION LOGIC: descriptive only, no alignment scoring, no divine consequences

### Rulings & Conflicts Record (Schema-Only)
- **RulesQuestion**: Rules questions requiring clarification (question text + context refs + citations)
- **RulingConflict**: Detected conflicts between rules/citations (question + conflict notes + conflicting citations)
- **RulingDecision**: Resolution of rules questions (resolution text + precedence rationale + citations used)
- Deterministic citation sorting in RulingDecision
- NO RESOLUTION/INTERPRETATION LOGIC: descriptive only, no rule engine

### Vertical Slice V1 (Execution Proof)
- **Play Loop**: Minimal deterministic turn execution engine (execute_turn, execute_scenario)
- **TurnContext**: Turn metadata (turn_index, actor_id, actor_team)
- **TurnResult**: Turn outcome (updated WorldState, emitted events)
- Wires together: intent → policy evaluation → event emission → state mutation stub
- State mutation stub: turn counter in active_combat dict (no mechanics)
- Integration with SessionBundle, MonsterDoctrine, PolicyEngine, EventLog
- Runnable script: scripts/vertical_slice_v1.py (demonstrates 3-turn scenario)
- Artifacts: JSONL event log + human-readable transcript
- Deterministic replay verified: same inputs → identical final state hash
- 5 integration tests verify determinism, event ID monotonicity, turn counter, policy events, PC stubs
- NO MECHANICS: No damage, no movement, no time advancement (execution proof only)

### Attack Resolution (CP-10 Proof)
- **Weapon Schema**: damage_dice + damage_bonus + damage_type + critical_multiplier (default ×2)
- **AttackIntent**: Single attack action contract (attacker_id + target_id + attack_bonus + weapon)
- **resolve_attack()**: Deterministic single attack resolution (d20 + bonus vs AC, damage on hit, defeat check)
- **apply_attack_events()**: ONLY function that mutates WorldState from attack events
- RAW D&D 3.5e mechanics: natural 20 auto-hit, natural 1 auto-miss, hit if total >= AC
- HP tracking: integer HP, can go negative, entity_defeated when HP <= 0
- RNG discipline: all combat randomness uses "combat" stream, strict ordering (attack roll → damage roll)
- Event types: attack_roll, damage_roll, hp_changed, entity_defeated
- Event payload completeness: all resolution inputs recorded (d20, AC, bonuses, damage dice, etc.)
- No direct state mutation: resolve_attack returns events only
- 16 tests (9 Tier-1, 7 Tier-2), all passing in < 0.1 seconds
- Decisions doc: docs/CP10_ATTACK_RESOLUTION_DECISIONS.md (locked constraints for future packets)

### Full Attack Sequence (CP-11 Proof)
- **FullAttackIntent**: Full attack action contract (base_attack_bonus instead of single attack_bonus)
- **calculate_iterative_attacks()**: BAB progression (BAB/BAB-5/BAB-10/BAB-15, min +1 per attack)
- **resolve_full_attack()**: Deterministic multi-attack resolution with critical hits
- **Critical hit mechanics**: natural 20 threatens, confirmation roll vs AC, damage × critical_multiplier
- **RNG consumption order**: attack roll → [IF threat: confirm roll] → [IF hit: damage roll]
- Deterministic branching: threat/no-threat paths maintain strict RNG ordering
- Damage accumulation: all attacks resolve independently, damage accumulates, single HP change event
- Event types: full_attack_start, attack_roll (with is_threat/is_critical/confirmation_total), damage_roll (with base_damage/critical_multiplier), hp_changed, entity_defeated, full_attack_end
- Backward compatibility: CP-11 events use optional fields with defaults, CP-10 handlers work on CP-11 events
- Critical multiplier validation: must be 2, 3, or 4 (fail-fast on invalid values)
- No expanded threat range yet (only natural 20 threatens, deferred to CP-12)
- 16 tests (9 Tier-1 blocking, 7 Tier-2), all passing in < 0.1 seconds
- Decisions doc: docs/CP11_FULL_ATTACK_DECISIONS.md (locked constraints for critical hits, RNG ordering)

### Play Loop Combat Integration (CP-12)
- **TurnResult extended**: status ("ok"/"invalid_intent"/"requires_clarification") + failure_reason + narration
- **execute_turn() extended**: Optional combat_intent parameter (AttackIntent or FullAttackIntent)
- **Intent validation**: actor must match turn, target must exist, target must not be defeated
- **Combat routing**: AttackIntent → resolve_attack(), FullAttackIntent → resolve_full_attack()
- **Event application**: apply_attack_events() / apply_full_attack_events() called after resolution
- **Narration tokens**: "attack_hit", "attack_miss", "full_attack_complete" (deterministic, token-based)
- **Validation events**: intent_validation_failed with reason payload (actor_mismatch, target_not_found, target_already_defeated)
- **Turn enforcement**: combat intents must execute during actor's turn (actor ID match required)
- **No direct mutation**: execute_turn() does not mutate WorldState, only returns updated state via events
- **Backward compatible**: CP-09 vertical slice tests still pass (policy-based resolution preserved)
- **Monster combat deferred**: Monsters continue using policy stubs, tactic→intent mapping deferred to CP-13
- **No range/LoS validation**: Target validation only checks existence and defeat status
- 13 integration tests (8 Tier-1, 5 Tier-2), all passing in < 0.1 seconds
- Decisions doc: docs/CP12_PLAY_LOOP_INTEGRATION.md (locked constraints for play loop architecture)

### Monster Combat Integration (CP-13)
- **MonsterDoctrine extended**: weapon: Optional[Weapon] + attack_bonus: Optional[int]
- **resolve_monster_combat_intent()**: Maps policy output to AttackIntent or returns None
- **Tactic mapping**: attack_nearest/focus_fire → AttackIntent (unmapped tactics return None)
- **Target selection**: Finds enemies from WorldState, sorts lexicographically, picks first valid
- **Missing combat parameters**: weapon=None or attack_bonus=None → returns None (preserves CP-09 stub)
- **execute_turn() doctrine branch extended**: Calls resolve_monster_combat_intent(), routes to resolve_attack() if intent created
- **RNG requirement**: If monster_combat_intent returned, rng must be provided (raises ValueError if None)
- **Narration tokens**: Monster combat generates "attack_hit"/"attack_miss" (same as player combat)
- **Backward compatible**: Unmapped tactics emit tactic_selected stub, CP-09 behavior preserved
- **Deterministic replay**: Same RNG seed → identical monster attack events → identical final state hash
- **RNG stream isolation**: Policy RNG does not affect combat RNG ("combat" stream used exclusively)
- 9 integration tests (6 Tier-1, 3 Tier-2), all passing in < 0.1 seconds
- Decisions doc: docs/CP13_MONSTER_COMBAT_INTEGRATION.md (locked constraints for monster combat mapping)

### Initiative & Action Economy Kernel (CP-14)
- **Initiative System**: d20 + Dex modifier + misc modifiers, dedicated "initiative" RNG stream
- **InitiativeRoll**: Dataclass with actor_id, d20_roll, dex_modifier, misc_modifier, total
- **roll_initiative()**: Single actor initiative roll using "initiative" stream
- **sort_initiative_order()**: Deterministic tie-breaking (total → Dex → lexicographic actor_id)
- **roll_initiative_for_all_actors()**: Batch initiative with stable lexicographic RNG consumption order
- **Combat Controller**: Wrapper pattern (execute_combat_round calls execute_turn for each actor)
- **start_combat()**: Rolls initiative, emits combat_started + initiative_rolled events, initializes active_combat
- **execute_combat_round()**: Iterates initiative_order, executes turns, manages flat-footed, increments round_index
- **WorldState.active_combat extended**: initiative_order (List[str]), round_index (int, 1-indexed), flat_footed_actors (List[str])
- **Flat-footed state**: All actors start flat-footed, cleared after first successful action (status="ok" + action events)
- **Flat-footed event**: flat_footed_cleared emitted immediately after first action
- **TurnContext extended**: action_type: Optional[Literal["move", "standard", "move_and_standard", "full"]]
- **TurnResult extended**: round_index: Optional[int], action_type: Optional[str]
- **Round indexing**: 1-indexed (PHB convention, first round = round_index: 1)
- **Event sequence**: combat_started → initiative_rolled (per actor) → combat_round_started → turn_start/turn_end
- **Action economy framework**: Schema-only (validation deferred to CP-15+)
- **Backward compatible**: CP-09 manual turn execution preserved (no active_combat required), execute_turn() works standalone
- **RNG discipline**: "initiative" stream isolated from "combat" and "policy" streams
- **Deterministic replay**: Same seed → identical initiative order → identical final state hash through full combat round
- 11 integration tests (8 Tier-1, 2 Tier-2), all passing in < 0.1 seconds
- Decisions doc: docs/CP14_INITIATIVE_DECISIONS.md (locked constraints for initiative, flat-footed, action economy)
- **Out of scope**: Readied actions, delay, AoOs, interrupts, 5-foot step, movement validation (deferred to CP-15+)

### Attacks of Opportunity (AoO) Kernel (CP-15)
- **GridPosition schema**: 2D grid position with is_adjacent_to() method (5-ft reach, 8 directions)
- **StepMoveIntent**: Minimal single-step movement intent (from_pos → to_pos, adjacency validated)
- **AooTrigger**: Single AoO opportunity (reactor_id, provoker_id, provoking_action, positions)
- **AooSequenceResult**: AoO resolution result (provoker_defeated, events, aoo_reactors list)
- **get_threatened_squares()**: Returns all adjacent squares threatened by actor (fail-closed if no position)
- **check_aoo_triggers()**: Detects provoking actions (movement out of threatened square), returns sorted trigger list
- **resolve_aoo_sequence()**: Resolves AoO sequence in deterministic order (initiative → lexicographic)
- **Movement provocation**: Leaving threatened square triggers AoO (from_pos → to_pos, not state diff)
- **AoO eligibility**: One AoO per reactor per round, tracked in active_combat["aoo_used_this_round"]
- **AoO usage reset**: Cleared at combat_round_started (before turns execute)
- **Deterministic ordering**: Initiative order (primary), lexicographic actor_id (tie-breaking)
- **Action abortion**: Provoker defeated by AoO → action_aborted event + narration="action_aborted_by_aoo"
- **Interrupt model**: Synchronous event-driven (AoOs resolve before main action, no event interleaving)
- **Attack pipeline reuse**: AoO attacks resolved via resolve_attack() (same RNG discipline, same events)
- **RNG discipline**: AoO attacks use "combat" stream in reactor resolution order
- **Play loop integration**: AoO checks after validation, before main action resolution
- **Event types**: aoo_triggered, action_aborted, movement_declared (stub)
- **Backward compatible**: All 518 CP-09–CP-14 tests pass unchanged (AoO only for StepMoveIntent)
- 6 integration tests (5 Tier-1, 1 Tier-2), all passing in < 0.1 seconds
- Decisions doc: docs/CP15_AOO_DECISIONS.md (locked constraints for interrupt system, precedent for all future interrupts)
- **Out of scope**: Combat Reflexes, reach weapons, 5-foot step immunity, withdraw, readied actions, full movement legality (CP-16+)

### Conditions & Status Effects Kernel (CP-16)
- **Condition schemas**: ConditionType enum, ConditionInstance, ConditionModifiers
- **Modifier query system**: get_condition_modifiers(actor_id, context) returns aggregate modifiers
- **Numeric modifiers**: AC, attack, damage, Dex (stack additively)
- **Boolean flags**: movement_prohibited, actions_prohibited, standing_triggers_aoo, auto_hit_if_helpless, loses_dex_to_ac (OR logic)
- **Attack integration**: Attacker/defender condition modifiers affect attack rolls, AC, damage
- **Event payload extension**: attack_roll/damage_roll events include condition_modifier fields
- **Condition set**: Prone, Flat-Footed, Grappled, Helpless, Stunned, Dazed, Shaken, Sickened
- **Factory functions**: create_prone_condition(), create_shaken_condition(), etc. (PHB-compliant modifiers)
- **Storage**: Conditions stored in entities[actor_id]["conditions"] dict keyed by condition type
- **Lifecycle**: Manual application/removal only (no automatic expiration, deferred to CP-17+)
- **Stacking**: Same condition type overwrites, different types stack additively
- **Fail-closed queries**: Missing entities return zero modifiers (no exceptions)
- **No RNG consumption**: Condition queries and application consume zero RNG (deterministic)
- **Metadata-only flags**: Boolean flags are descriptive only, no enforcement logic in CP-16
- **CRITICAL SCOPE (OPTION A)**: Conditions declare mechanical truth but do NOT enforce legality (enforcement deferred to CP-17+)
- **Backward compatible**: All 524 CP-09–CP-15 tests pass unchanged
- 14 integration tests (5 Tier-1, 9 Tier-2), all passing in < 0.1 seconds
- Decisions doc: docs/CP16_CONDITIONS_DECISIONS.md (locked constraints for condition system, metadata-only pattern)
- **Out of scope**: Event-driven lifecycle, duration tracking, saving throws, spell effects, enforcement logic (CP-17+)

## Test Count

**Total: 1393 tests** (all passing in ~3.5 seconds)

Breakdown by subsystem:
- RNGManager: 8 tests
- EventLog: 7 tests
- EventLog Citations: 5 tests
- State: 9 tests
- ReplayRunner: 7 tests
- LegalityChecker: 11 tests
- SourceRegistry: 13 tests
- Citation: 10 tests
- RuleLookup: 9 tests
- RulingHelpers: 4 tests
- Intents: 15 tests
- Interaction: 12 tests
- ObsidianLinks: 8 tests
- Bundles: 9 tests
- BundleValidator: 11 tests
- Doctrine: 17 tests
- BundleValidatorDoctrine: 9 tests
- Visibility: 30 tests (includes lighting-over-time)
- Terrain: 10 tests
- PolicyConfig: 13 tests
- Time: 17 tests
- Timers: 16 tests
- Durations: 25 tests
- BundleValidatorTemporal: 14 tests
- Hazards: 27 tests
- Exposure: 12 tests
- BundleValidatorHazards: 11 tests
- PolicySchemas: 18 tests
- TacticalPolicy: 29 tests
- CampaignMemorySchemas: 33 tests
- BundleValidatorCampaignMemory: 17 tests
- RulingsConflicts: 13 tests
- VerticalSliceV1Integration: 5 tests
- AttackResolution: 16 tests (CP-10)
- FullAttackResolution: 16 tests (CP-11)
- PlayLoopCombatIntegration: 13 tests (CP-12)
- MonsterCombatIntegration: 9 tests (CP-13)
- InitiativeAndCombatRounds: 11 tests (CP-14)
- AooKernel: 6 tests (CP-15)
- ConditionsKernel: 14 tests (CP-16)
- SaveResolution: 20 tests (CP-17)
- TargetingResolver: 20 tests (CP-18A-T&V)
- MountedCombatCore: 24 tests (CP-18A)
- MountedCombatIntegration: 8 tests (CP-18A)
- ManeuversCore: 36 tests (CP-18)
- ManeuversIntegration: 17 tests (CP-18)
- TerrainCP19Core: 41 tests (CP-19)
- TerrainCP19Integration: 10 tests (CP-19 + CP-19B)
- PermanentStatsCore: 16 tests (SKR-002)
- PBHA_SKR002: 6 tests (SKR-002 PBHA)
- IntentLifecycle: 31 tests (M1)
- EngineResult: 26 tests (M1)
- SessionLog: 19 tests (M1)
- CharacterSheetUI: 26 tests (M1)
- Narrator: 21 tests (M1)
- CampaignSchemas: 40 tests (M2)
- CampaignStore: 27 tests (M2)
- PrepOrchestrator: 22 tests (M2)
- AssetStore: 23 tests (M2)
- WorldArchive: 23 tests (M2)
- ImmersionSchemas: 64 tests (M3)
- VoicePipeline: 19 tests (M3)
- AudioTransitions: 22 tests (M3)
- ImagePipeline: 11 tests (M3)
- ContextualGrid: 17 tests (M3)
- AttributionLedger: 14 tests (M3)
- ImmersionIntegration: 18 tests (M3)
- ImmersionHardening: 38 tests (M3 Plan C)
- ImmersionAuthorityContract: 12 tests (M3 Plan C)
- ImmersionDeterminismCanary: 28 tests (M3 Plan C)
- Position: 34 tests (CP-001 Phase 1)

## Module Inventory

### aidm/core/
- event_log.py
- rng_manager.py
- state.py
- replay_runner.py
- source_registry.py
- rule_lookup.py
- ruling_helpers.py
- interaction.py
- obsidian_links.py
- bundle_validator.py
- doctrine_rules.py
- tactical_policy.py
- play_loop.py
- attack_resolver.py
- full_attack_resolver.py
- initiative.py (CP-14)
- combat_controller.py (CP-14)
- aoo.py (CP-15)
- conditions.py (CP-16)
- save_resolver.py (CP-17)
- targeting_resolver.py (CP-18A-T&V)
- mounted_combat.py (CP-18A)
- maneuver_resolver.py (CP-18)
- permanent_stats.py (SKR-002)
- terrain_resolver.py (CP-19)
- session_log.py (M1 — replay harness)
- campaign_store.py (M2 — campaign persistence)
- prep_orchestrator.py (M2 — deterministic prep queue)
- asset_store.py (M2 — asset management with shared cache)
- world_archive.py (M2 — export/import bundle)

### aidm/rules/
- legality_checker.py

### aidm/schemas/
- citation.py
- intents.py
- bundles.py
- doctrine.py
- visibility.py
- terrain.py
- policy_config.py
- time.py
- timers.py
- durations.py
- hazards.py
- exposure.py
- policy.py
- campaign_memory.py
- rulings_conflicts.py
- attack.py
- conditions.py (CP-16)
- saves.py (CP-17)
- targeting.py (CP-18A-T&V)
- mounted_combat.py (CP-18A)
- maneuvers.py (CP-18)
- permanent_stats.py (SKR-002)
- entity_fields.py (Canonical entity field name constants)
- entity_state.py (SKR-002)
- intent_lifecycle.py (M1 — IntentObject, IntentStatus, ActionType)
- engine_result.py (M1 — EngineResult, RollResult, StateChange, EngineResultBuilder)
- campaign.py (M2 — SessionZeroConfig, CampaignManifest, PrepJob, AssetRecord, CampaignPaths)
- immersion.py (M3 — Transcript, VoicePersona, AudioTrack, SceneAudioState, ImageRequest, ImageResult, GridEntityPosition, GridRenderState, AttributionRecord, AttributionLedger)
- position.py (CP-001 — Canonical Position type consolidating 3 legacy grid position types)

### aidm/ui/
- character_sheet.py (M1 — CharacterData, CharacterSheetUI, PartySheet)

### aidm/narration/
- narrator.py (M1 — Narrator, NarrationTemplates, NarrationContext)

### aidm/immersion/
- __init__.py (M3 — re-exports all public symbols)
- stt_adapter.py (M3 — STTAdapter Protocol, StubSTTAdapter, create_stt_adapter)
- tts_adapter.py (M3 — TTSAdapter Protocol, StubTTSAdapter, create_tts_adapter)
- audio_mixer.py (M3 — compute_scene_audio_state, AudioMixerAdapter, StubAudioMixerAdapter)
- image_adapter.py (M3 — ImageAdapter Protocol, StubImageAdapter, create_image_adapter)
- contextual_grid.py (M3 — compute_grid_state)
- attribution.py (M3 — AttributionStore)

### tests/ (74 files)
- test_event_log.py
- test_event_log_citations.py
- test_rng_manager.py
- test_state.py
- test_replay_runner.py
- test_legality_checker.py
- test_source_registry.py
- test_citation.py
- test_rule_lookup.py
- test_ruling_helpers.py
- test_intents.py
- test_interaction.py
- test_obsidian_links.py
- test_bundles.py
- test_bundle_validator.py
- test_doctrine.py
- test_bundle_validator_doctrine.py
- test_visibility.py
- test_terrain.py
- test_policy_config.py
- test_time.py
- test_timers.py
- test_durations.py
- test_bundle_validator_temporal.py
- test_hazards.py
- test_exposure.py
- test_bundle_validator_hazards.py
- test_policy_schemas.py
- test_tactical_policy.py
- test_campaign_memory_schemas.py
- test_bundle_validator_campaign_memory.py
- test_rulings_conflicts.py
- test_vertical_slice_v1_integration.py (CP-09)
- test_attack_resolution.py (CP-10)
- test_full_attack_resolution.py (CP-11)
- test_play_loop_combat_integration.py (CP-12)
- test_monster_combat_integration.py (CP-13)
- test_initiative_and_combat_rounds.py (CP-14)
- test_aoo_kernel.py (CP-15)
- test_conditions_kernel.py (CP-16)
- test_save_resolution.py (CP-17)
- test_targeting_resolver.py (CP-18A-T&V)
- test_targeting_resolver_unit.py (POST-AUDIT FIX-06)
- test_mounted_combat_core.py (CP-18A)
- test_mounted_combat_integration.py (CP-18A)
- test_maneuvers_core.py (CP-18)
- test_maneuvers_integration.py (CP-18)
- test_terrain_cp19_core.py (CP-19)
- test_terrain_cp19_integration.py (CP-19)
- test_permanent_stats_core.py (SKR-002)
- test_pbha_skr002.py (SKR-002 PBHA)
- test_intent_lifecycle.py (M1)
- test_engine_result.py (M1)
- test_session_log.py (M1)
- test_character_sheet_ui.py (M1)
- test_narrator.py (M1)
- test_campaign_schemas.py (M2)
- test_campaign_store.py (M2)
- test_prep_orchestrator.py (M2)
- test_asset_store.py (M2)
- test_world_archive.py (M2)
- test_immersion_schemas.py (M3)
- test_voice_pipeline.py (M3)
- test_audio_transitions.py (M3)
- test_image_pipeline.py (M3)
- test_contextual_grid.py (M3)
- test_attribution_ledger.py (M3)
- test_edge_cases_35e.py (M3 Edge Case Hardening)
- test_immersion_hardening.py (M3 Plan C)
- test_immersion_integration.py (M3)
- test_immersion_authority_contract.py (M3 Plan C)
- test_immersion_determinism_canary.py (M3 Plan C)
- test_position.py (CP-001 Phase 1)

## Instruction Packet History

### Tasks 0-5: Foundation (Initial Implementation)
- Project skeleton, RNG, EventLog, WorldState, ReplayRunner, LegalityChecker
- **Status**: COMPLETE

### Tasks 9-13: Voice-First Tabletop Contracts
- Intent schemas, InteractionEngine, Obsidian links, SessionBundle, README updates
- **Status**: COMPLETE

### Tasks 14-17: Monster Tactical Envelope
- Doctrine schemas, tactical envelope derivation, bundle integration, validator extensions
- **Status**: COMPLETE

### Tasks 18-22: Visibility, Terrain, Policy Config
- Visibility/targeting contracts, terrain/traversal contracts, policy variety config, doctrine binding hardening
- **Status**: COMPLETE

### CP-00: Project State Anchoring (META)
- PROJECT_STATE_DIGEST.md creation
- README coordination section
- Completion protocol documentation
- **Status**: COMPLETE

### CP-05: Time, Clocks, Deadlines, Durations
- Temporal schemas (TimeScale, TimeSpan, GameClock, TimeAdvanceEvent)
- Deadline/timer schemas (Deadline, TimerStatus)
- Effect duration contracts (DurationUnit, EffectDuration with compute_end_time)
- Lighting-over-time contracts (AmbientLightSchedule, LightSource with expiration)
- Bundle integration (initial_clock, deadlines, active_effects, ambient_light_schedule)
- Validator extensions (temporal validation: deadlines vs clock, effects vs clock, schedule ordering)
- 89 new tests (199 → 288)
- **Status**: COMPLETE

### CP-06: Environmental Hazards & Exposure
- Hazard schemas (HazardIntervalUnit, HazardEffectType, EnvironmentalHazard)
- Hazard progression (HazardStage, HazardProgression with strictly increasing indices)
- Exposure schemas (ExposureType, EnvironmentalCondition with mitigation sources)
- Bundle integration (environmental_hazards, environmental_conditions in SceneCard)
- Validator extensions (hazard ID uniqueness, hazard_ref validation, DMG citation requirements)
- 50 new tests (288 → 338)
- **Status**: COMPLETE

### CP-07: Tactical Policy Engine
- Policy schemas (TacticCandidate, ScoredTactic, TacticalPolicyTrace, TacticalPolicyResult)
- Core policy engine (evaluate_tactics, extract_features, generate_candidates, score_candidate, select_tactic)
- Integer-based heuristic scoring (basis points scale, no floating point)
- Policy RNG stream isolation (variety selection does not affect combat RNG)
- Fail-closed: missing actor returns requires_clarification
- Deterministic: same inputs → identical ranked list and selection
- Doctrine integration: only allowed tactics are scored
- Feature extraction: HP bands, conditions, nearby threats, allies
- Greedy + variety selection modes (top-k with uniform sampling)
- Full trace output with serialization
- 47 new tests (338 → 385)
- **Status**: COMPLETE

### CP-08: Campaign Memory & Character Evidence Ledger
- Campaign memory schemas (SessionLedgerEntry, CharacterEvidenceEntry, EvidenceLedger, ClueCard, ThreadRegistry)
- Evidence type enumeration (15 descriptive types: harm_inflicted, mercy_shown, betrayal, loyalty, etc.)
- Alignment axis tags (6 tags: lawful, chaotic, good, evil, neutral_lc, neutral_ge)
- Clue status enumeration (unresolved, partial, resolved)
- Deterministic ordering: EvidenceLedger by (character_id, session_id, id), ThreadRegistry by id
- CampaignBundle integration (session_ledger, evidence_ledger, thread_registry)
- Campaign bundle validator (unique ID checks, session reference validation, event_id range validation)
- Fail-closed: unknown evidence types/alignment tags/clue statuses rejected
- NO EVALUATION LOGIC: descriptive only, no alignment scoring, no divine consequences
- 50 new tests (385 → 435)
- **Status**: COMPLETE

### CP-07D: Coherence Fixes + Vertical Slice Plan + Rulings Record
- Coherence fixes to README.md and PROJECT_STATE_DIGEST.md (LLM scope, campaign continuity, stable hashing)
- VERTICAL_SLICE_V1.md milestone definition (1 scene, 1 monster, 2 PCs, 3 turns, deterministic replay)
- Rulings/conflicts record schema (RulesQuestion, RulingConflict, RulingDecision)
- PROJECT_COHERENCE_DOCTRINE.md governance document
- 13 new tests (435 → 448)
- **Status**: COMPLETE

### CP-09: Vertical Slice V1 Implementation
- Play loop module (execute_turn, execute_scenario in aidm/core/play_loop.py)
- Turn execution contracts (TurnContext, TurnResult)
- Integration: SessionBundle → MonsterDoctrine → Policy → EventLog → WorldState
- State mutation stub: turn counter in active_combat dict (no mechanics)
- Runnable script: scripts/vertical_slice_v1.py (3-turn scenario with goblin + 2 PCs)
- Artifacts generation: JSONL event log + human-readable transcript
- Deterministic replay verification: identical final state hash across multiple runs
- 5 integration tests: determinism, event ID monotonicity, turn counter, policy events, PC stubs
- Final state hash verified: 9f338195031e90addb2533761fb433b7b9366f5c6af96ded6f6fd62619b654f9
- Test runtime: 453 tests in ~1.5 seconds
- NO MECHANICS: No damage, no movement, no time advancement (execution proof only)
- **Status**: COMPLETE

### CP-10: Attack Resolution Proof
- Attack schemas (Weapon with damage_dice/damage_bonus/damage_type/critical_multiplier, AttackIntent)
- Attack resolver module (resolve_attack, apply_attack_events, parse_damage_dice, roll_dice)
- RAW D&D 3.5e single attack mechanics (d20 + bonus vs AC, natural 20/1, damage on hit, HP tracking)
- Event-driven state mutations (resolve_attack returns events only, apply_attack_events is only mutator)
- RNG discipline (all combat randomness uses "combat" stream, strict ordering: attack → damage)
- Event types: attack_roll, damage_roll, hp_changed, entity_defeated
- 16 tests (9 Tier-1, 7 Tier-2), all passing in < 0.1 seconds
- Decisions document: docs/CP10_ATTACK_RESOLUTION_DECISIONS.md (locked constraints)
- Files added: aidm/schemas/attack.py, aidm/core/attack_resolver.py, tests/test_attack_resolution.py, docs/CP10_ATTACK_RESOLUTION_DECISIONS.md
- Test count: 453 → 469
- **Status**: COMPLETE

### CP-11: Full Attack Sequence Proof
- Full attack schemas (FullAttackIntent with base_attack_bonus)
- Full attack resolver module (resolve_full_attack, apply_full_attack_events, calculate_iterative_attacks, resolve_single_attack_with_critical)
- RAW D&D 3.5e iterative attack progression (BAB/BAB-5/BAB-10/BAB-15)
- Critical hit mechanics (natural 20 threatens, confirmation roll vs AC, damage × critical_multiplier)
- RNG consumption order (attack → [IF threat: confirm] → [IF hit: damage]) with deterministic branching
- Weapon schema extension (critical_multiplier: int = 2, validated as 2/3/4 only)
- Event schema backward compatibility (optional fields with defaults: is_threat, is_critical, confirmation_total, base_damage, critical_multiplier)
- Event types: full_attack_start, attack_roll (extended), damage_roll (extended), hp_changed, entity_defeated, full_attack_end
- Damage accumulation (all attacks resolve, single HP change event)
- 16 tests (9 Tier-1 blocking including RNG consumption order, 7 Tier-2), all passing in < 0.1 seconds
- Backward compatibility verified (CP-10 handlers work on CP-11 events)
- Decisions document: docs/CP11_FULL_ATTACK_DECISIONS.md (locked constraints for critical hits, RNG ordering)
- Files modified: aidm/schemas/attack.py (added critical_multiplier field)
- Files added: aidm/core/full_attack_resolver.py, tests/test_full_attack_resolution.py, docs/CP11_FULL_ATTACK_DECISIONS.md
- Test count: 469 → 485
- **Status**: COMPLETE

### CP-12: Play Loop Combat Integration
- TurnResult schema extension (status field: "ok"/"invalid_intent"/"requires_clarification", failure_reason, narration)
- execute_turn() extension (optional combat_intent parameter: AttackIntent or FullAttackIntent)
- Intent validation (actor must match turn, target must exist, target must not be defeated)
- Combat routing (AttackIntent → resolve_attack(), FullAttackIntent → resolve_full_attack())
- Event application (apply_attack_events() / apply_full_attack_events() called within execute_turn())
- Narration token generation ("attack_hit", "attack_miss", "full_attack_complete")
- Validation event (intent_validation_failed with reason: actor_mismatch, target_not_found, target_already_defeated)
- Turn enforcement (combat intents execute during actor's turn only, actor ID match required)
- No direct mutation (execute_turn() returns updated state via events, does not mutate WorldState directly)
- Backward compatibility (CP-09 vertical slice tests still pass, policy-based resolution preserved)
- Monster combat deferred (monsters continue using policy stubs, tactic→intent mapping deferred to CP-13)
- No range/LoS validation (target validation only checks existence and defeat status, deferred)
- 13 integration tests (8 Tier-1, 5 Tier-2), all passing in < 0.1 seconds
- Decisions document: docs/CP12_PLAY_LOOP_INTEGRATION.md (locked constraints for play loop architecture)
- Files modified: aidm/core/play_loop.py (extended execute_turn() with combat routing)
- Files added: tests/test_play_loop_combat_integration.py, docs/CP12_PLAY_LOOP_INTEGRATION.md
- Test count: 485 → 498
- **Status**: COMPLETE

### CP-13: Monster Combat Integration (Policy → Intent Mapping)
- MonsterDoctrine schema extension (weapon: Optional[Weapon], attack_bonus: Optional[int])
- resolve_monster_combat_intent() helper function (maps policy result to AttackIntent or returns None)
- Tactic mapping (attack_nearest/focus_fire → AttackIntent, unmapped tactics return None)
- Target selection (finds enemies from WorldState, sorts lexicographically, picks first valid)
- Missing combat parameters (weapon=None or attack_bonus=None → returns None, preserves CP-09 stub behavior)
- execute_turn() doctrine branch extension (calls resolve_monster_combat_intent(), routes to resolve_attack() if intent created)
- RNG requirement (if monster_combat_intent returned, rng must be provided, raises ValueError if None)
- Narration tokens (monster combat generates "attack_hit"/"attack_miss", same as player combat)
- Backward compatibility (unmapped tactics emit tactic_selected stub, CP-09 behavior preserved)
- Deterministic replay (same RNG seed → identical monster attack events → identical final state hash)
- RNG stream isolation (policy RNG does not affect combat RNG, "combat" stream used exclusively)
- 9 integration tests (6 Tier-1, 3 Tier-2), all passing in < 0.1 seconds
- Decisions document: docs/CP13_MONSTER_COMBAT_INTEGRATION.md (locked constraints for monster combat mapping)
- Files modified: aidm/schemas/doctrine.py (added weapon/attack_bonus fields), aidm/core/play_loop.py (added resolve_monster_combat_intent() and doctrine branch extension)
- Files added: tests/test_monster_combat_integration.py, docs/CP13_MONSTER_COMBAT_INTEGRATION.md
- Test count: 498 → 507
- **Status**: COMPLETE

### CP-14: Initiative & Action Economy Kernel
- Initiative system (d20 + Dex modifier + misc modifiers, dedicated "initiative" RNG stream)
- InitiativeRoll dataclass (actor_id, d20_roll, dex_modifier, misc_modifier, total)
- roll_initiative() (single actor initiative roll using "initiative" stream)
- sort_initiative_order() (deterministic tie-breaking: total → Dex → lexicographic actor_id)
- roll_initiative_for_all_actors() (batch initiative with stable lexicographic RNG consumption order)
- Combat controller (wrapper pattern: execute_combat_round calls execute_turn for each actor)
- start_combat() (rolls initiative, emits combat_started + initiative_rolled events, initializes active_combat)
- execute_combat_round() (iterates initiative_order, executes turns, manages flat-footed, increments round_index)
- WorldState.active_combat extension (initiative_order: List[str], round_index: int, flat_footed_actors: List[str])
- Flat-footed state (all actors start flat-footed, cleared after first successful action)
- Flat-footed event (flat_footed_cleared emitted immediately after first action with status="ok" + action events)
- TurnContext extension (action_type: Optional[Literal["move", "standard", "move_and_standard", "full"]])
- TurnResult extension (round_index: Optional[int], action_type: Optional[str])
- Round indexing (1-indexed, PHB convention, first round = round_index: 1)
- Event sequence (combat_started → initiative_rolled (per actor) → combat_round_started → turn_start/turn_end)
- Action economy framework (schema-only, validation deferred to CP-15+)
- Backward compatibility (CP-09 manual turn execution preserved, no active_combat required, execute_turn() works standalone)
- RNG discipline ("initiative" stream isolated from "combat" and "policy" streams)
- Deterministic replay (same seed → identical initiative order → identical final state hash through full combat round)
- Out of scope: Readied actions, delay, AoOs, interrupts, 5-foot step, movement validation (deferred to CP-15+)
- 11 integration tests (8 Tier-1, 2 Tier-2), all passing in < 0.1 seconds
- Decisions document: docs/CP14_INITIATIVE_DECISIONS.md (locked constraints for initiative, flat-footed, action economy)
- Files modified: aidm/core/play_loop.py (extended TurnContext and TurnResult with optional fields)
- Files added: aidm/core/initiative.py, aidm/core/combat_controller.py, tests/test_initiative_and_combat_rounds.py, docs/CP14_INITIATIVE_DECISIONS.md
- Test count: 507 → 518
- **Status**: COMPLETE

### CP-15: Attacks of Opportunity (AoO) Kernel
- Movement intent schema (GridPosition with is_adjacent_to(), StepMoveIntent with adjacency validation)
- AoO schemas (AooTrigger, AooSequenceResult)
- AoO detection module (check_aoo_triggers, get_threatened_squares with fail-closed position handling)
- AoO resolution module (resolve_aoo_sequence with deterministic ordering)
- Movement provocation (leaving threatened square via StepMoveIntent from_pos → to_pos)
- AoO eligibility (one per reactor per round, tracked in active_combat["aoo_used_this_round"])
- AoO usage lifecycle (initialized in start_combat, reset at combat_round_started, updated in execute_turn)
- Deterministic ordering (initiative order → lexicographic actor_id)
- Action abortion (provoker defeated → action_aborted event + narration="action_aborted_by_aoo")
- Interrupt model (synchronous event-driven, AoOs resolve before main action, no event interleaving)
- Attack pipeline reuse (AoO attacks via resolve_attack, same RNG discipline, same event structure)
- RNG discipline (AoO attacks use "combat" stream in reactor resolution order, no RNG for trigger detection)
- Play loop integration (AoO checks after validation, before main action resolution in execute_turn)
- Event types (aoo_triggered, action_aborted, movement_declared stub)
- WorldState.active_combat extension (aoo_used_this_round: List[str])
- Backward compatibility (all 518 CP-09–CP-14 tests pass unchanged, AoO only for StepMoveIntent)
- Architectural precedent (interrupt system pattern for all future interrupt-capable mechanics)
- RAW fidelity (declared intent timing, not state diffs; PHB p. 137-138)
- Out of scope: Combat Reflexes, reach weapons, 5-foot step immunity, withdraw, readied actions, full movement legality (CP-16+)
- 6 integration tests (5 Tier-1, 1 Tier-2), all passing in < 0.1 seconds
- Decisions document: docs/CP15_AOO_DECISIONS.md (locked constraints for interrupt system, precedent for future interrupts)
- Files modified: aidm/schemas/attack.py (added GridPosition, StepMoveIntent), aidm/core/play_loop.py (added AoO integration), aidm/core/combat_controller.py (added aoo_used_this_round lifecycle)
- Files added: aidm/core/aoo.py, tests/test_aoo_kernel.py, docs/CP15_AOO_DECISIONS.md
- Test count: 518 → 524
- **Status**: COMPLETE

### CP-16: Conditions & Status Effects Kernel
- Condition schemas (ConditionType enum with 8 conditions, ConditionInstance, ConditionModifiers)
- Modifier query system (get_condition_modifiers returns aggregate modifiers for actor)
- Numeric modifiers (ac_modifier, attack_modifier, damage_modifier, dex_modifier, stack additively)
- Boolean flags (movement_prohibited, actions_prohibited, standing_triggers_aoo, auto_hit_if_helpless, loses_dex_to_ac, OR logic)
- Attack resolver integration (attacker/defender condition modifiers affect attack rolls, AC, damage)
- Event payload extension (attack_roll/damage_roll events include condition_modifier, target_base_ac, target_ac_modifier fields)
- Condition set (Prone, Flat-Footed, Grappled, Helpless, Stunned, Dazed, Shaken, Sickened with PHB-compliant modifiers)
- Factory functions (create_prone_condition, create_shaken_condition, etc. with PHB citations baked in)
- Storage (conditions stored in entities[actor_id]["conditions"] dict keyed by condition_type.value)
- Lifecycle (manual application/removal only, no automatic expiration, event-driven deferred to CP-17+)
- Stacking (same condition type overwrites, different types stack additively, no suppression)
- Fail-closed queries (missing entities return zero modifiers, no exceptions raised)
- No RNG consumption (condition queries and application consume zero RNG, deterministic)
- Metadata-only flags (boolean flags are descriptive only, no enforcement logic in CP-16)
- CRITICAL SCOPE (OPTION A - LOCKED): Conditions declare mechanical truth but do NOT enforce legality, enforcement deferred to CP-17+
- Context parameter (reserved for future context-specific filtering, unused in CP-16)
- Backward compatibility (all 524 CP-09–CP-15 tests pass unchanged, new event fields optional with defaults)
- Out of scope: Event-driven lifecycle, duration tracking, saving throws, spell effects, context-specific modifiers, enforcement logic (CP-17+)
- 14 integration tests (5 Tier-1, 9 Tier-2), all passing in < 0.1 seconds
- Decisions document: docs/CP16_CONDITIONS_DECISIONS.md (locked constraints for condition system, metadata-only pattern)
- Files modified: aidm/core/attack_resolver.py (added condition modifier queries and event payload fields)
- Files added: aidm/schemas/conditions.py, aidm/core/conditions.py, tests/test_conditions_kernel.py, docs/CP16_CONDITIONS_DECISIONS.md
- Test count: 524 → 538
- **Status**: COMPLETE

### CP-17: Save Resolution Kernel
- Save resolver module (resolve_save, apply_save_effects)
- SaveContext: DC, save type (fort/ref/will), on_success/on_failure/on_partial
- SaveOutcome: SUCCESS, FAILURE, PARTIAL (success with reduced effect)
- Dedicated "saves" RNG stream, isolated from combat/initiative/policy
- RAW D&D 3.5e mechanics: d20 + save bonus vs DC, natural 20 always succeeds, natural 1 always fails
- Integration with conditions (condition modifiers applied to save rolls)
- Spell resistance checks (SR vs caster level check)
- Event types: save_rolled, save_effect_applied
- Deterministic: same RNG seed → identical save results
- Files added: aidm/core/save_resolver.py, aidm/schemas/saves.py, tests/test_save_resolution.py
- Test count: 538 → 558
- **Status**: COMPLETE

### CP-18A: Mounted Combat & Rider-Mount Coupling
- **Rider-mount coupling**: Bidirectional references (mounted_state on rider, rider_id on mount)
- **Position derivation**: Rider position derived from mount, not stored independently
- **Movement delegation**: Mount moves, rider is carried (PHB p.157)
- **AoO routing**: Mount provokes for movement, not rider (provoker_id = mount_id)
- **Higher ground bonus**: +1 melee vs smaller on-foot targets (mount_size > target_size)
- **Single attack restriction**: Only single attack when mount moves >5 feet
- **Condition propagation**: Unidirectional (mount conditions → rider dismount)
- **Voluntary dismount**: Normal (move action) and fast (free action, DC 20)
- **Forced dismount**: Mount defeated/prone triggers Ride check (DC 15 soft fall)
- **Unconscious saddle check**: 50% stay (riding saddle), 75% stay (military saddle)
- **Schemas**: MountedState, MountType, SaddleType, MountedMoveIntent, DismountIntent, MountIntent
- **Entity fields**: MOUNTED_STATE, RIDER_ID, MOUNT_SIZE, IS_MOUNT_TRAINED
- **Core functions**: get_entity_position, is_mounted, get_rider_for_mount, validate_mounted_coupling
- **Resolution functions**: resolve_mount, resolve_dismount, trigger_forced_dismount, check_unconscious_fall
- **Attack bonus**: get_mounted_attack_bonus (higher ground calculation)
- **AoO extension**: check_aoo_triggers handles MountedMoveIntent (mount as provoker)
- **Attack resolver extension**: mounted_bonus field in attack_roll event payload
- **Play loop integration**: MountedMoveIntent, DismountIntent, MountIntent routing
- **Determinism**: 10× replay verified, all RNG uses "combat" stream only
- **Gate safety**: G-T1 only (no spellcasting, no relational conditions, no entity forking)
- Files added: aidm/schemas/mounted_combat.py, aidm/core/mounted_combat.py, tests/test_mounted_combat_core.py, tests/test_mounted_combat_integration.py
- Files modified: aidm/schemas/entity_fields.py, aidm/core/aoo.py, aidm/core/attack_resolver.py, aidm/core/play_loop.py
- Test count: 594 → 626 (32 new tests: 24 unit + 8 integration)
- **Status**: COMPLETE

### CP-18A-T&V: Targeting & Visibility Resolver
- TargetingResolver: validates targeting legality (range, LoS, LoE, visibility)
- TargetingLegalityResult: legal/illegal with block_reasons and citations
- GridPoint (targeting.py): distance_to() for range calculations
- Integration with VisibilityProfile and VisionMode
- Fail-closed: unknown target or missing position → illegal
- No RNG consumption (purely deterministic geometric checks)
- Files added: aidm/core/targeting_resolver.py, tests/test_targeting_resolver.py
- Test count: 558 → 578
- **Status**: COMPLETE

### Combat Maneuvers Kernel (CP-18)
- **Maneuver Schemas**: BullRushIntent, TripIntent, OverrunIntent, SunderIntent, DisarmIntent, GrappleIntent
- **Result Schemas**: OpposedCheckResult, ManeuverResult, TouchAttackResult
- **Size Modifiers**: PHB p.154 scale (Fine -16 to Colossal +16), get_size_modifier() helper
- **Bull Rush**: Opposed Str check, push distance 5 ft + 5 per 5 margin, charge bonus +2
- **Trip**: Touch attack → opposed check (Str vs max(Str, Dex)), counter-trip on failure
- **Overrun**: Opposed check, defender may avoid (AI-controlled), failure by 5+ = attacker prone
- **Sunder** (degraded): Opposed attack rolls, damage logged narratively only
- **Disarm** (degraded): Opposed attack rolls, weapon "drops" narratively only, counter-disarm on failure
- **Grapple-lite** (degraded): Touch attack → opposed check, unidirectional condition (target only gets Grappled)
- **AoO Integration**: Bull Rush provokes from ALL threatening enemies; others provoke from TARGET only
- **AoO Damage Auto-Fail**: Disarm and Grapple auto-fail if AoO deals any damage
- **Condition Application**: Trip/Overrun/Grapple apply Prone/Grappled via create_*_condition factories
- **Entity Fields**: SIZE_CATEGORY, STABILITY_BONUS, GRAPPLE_SIZE_MODIFIER (added to entity_fields.py)
- **RNG Discipline**: All maneuvers use "combat" stream exclusively
- **RNG Consumption Order**: Documented per maneuver (attacker roll first, then defender)
- **Determinism**: 10× replay verified, identical final state hashes
- **Gate Safety**: G-T1 only (Grapple-lite avoids G-T3C by being unidirectional)
- **Unified Dispatcher**: resolve_maneuver() routes by intent type
- **Play Loop Integration**: All 6 intent types validated and routed in execute_turn()
- Files added: aidm/schemas/maneuvers.py, aidm/core/maneuver_resolver.py, tests/test_maneuvers_core.py, tests/test_maneuvers_integration.py
- Files modified: aidm/schemas/entity_fields.py, aidm/core/aoo.py, aidm/core/play_loop.py
- Test count: 626 → 679 (53 new tests: 36 unit + 17 integration)
- **Status**: COMPLETE

### CP-19: Environment & Terrain
- Terrain schema extensions (TerrainCell, ElevationDifference, FallingResult, CoverCheckResult)
- Entity field extensions (ELEVATION added to entity_fields.py)
- Terrain resolver module (terrain_resolver.py)
- **Difficult terrain**: Movement cost calculation (1x normal, 2x difficult, 4x very difficult)
- **Movement restrictions**: Run/charge blocked in difficult terrain, 5-foot step blocked in very difficult
- **Cover system**: Standard (+4 AC, +2 Reflex, blocks AoO), Improved (+8 AC, +4 Reflex), Total (blocks targeting), Soft (+4 AC melee only, does NOT block AoO)
- **Higher ground**: +1 melee attack when attacker elevation > defender elevation (stacks with mounted bonus)
- **Falling damage**: 1d6 per 10 feet, max 20d6, intentional jump first 10 feet free
- **Hazard detection**: Pit and ledge hazards trigger falling on forced movement
- **Forced movement integration**: Bull Rush push path evaluated cell-by-cell, first hazard triggers falling
- **Attack resolver integration**: Cover AC bonus applied to target AC, higher ground bonus added to attack
- **AoO cover blocking**: Standard/improved cover blocks AoO, soft cover does not
- **Maneuver resolver integration**: Bull Rush with hazard checking along push path
- RNG discipline: Only falling damage uses "combat" stream (terrain queries are deterministic)
- Ordering contract: AoO → movement → environmental effects (T-19-03)
- Gate safety: G-T1 only (no persistent terrain, no environmental agents)
- Determinism: 10× replay verified, identical final state hashes
- 49 new tests (41 Tier-1, 8 Tier-2), all passing in < 0.2 seconds
- Files added: aidm/core/terrain_resolver.py, tests/test_terrain_cp19_core.py, tests/test_terrain_cp19_integration.py
- Files modified: aidm/schemas/terrain.py, aidm/schemas/entity_fields.py, aidm/core/attack_resolver.py, aidm/core/aoo.py, aidm/core/maneuver_resolver.py
- Test count: 679 → 728
- **Status**: COMPLETE

### CP-19B: Failure-Path Hazard Resolution (Corrective Patch)
- **Bull Rush failure path**: Now routes through `resolve_forced_movement_with_hazards()` for hazard checking
- **Overrun failure path**: Now routes through `resolve_forced_movement_with_hazards()` for hazard checking
- **Semantic consistency**: All forced movement (success and failure) now uses same hazard resolution path
- 2 new tests: `test_bull_rush_failure_into_pit()`, `test_overrun_failure_into_ledge()`
- Files modified: aidm/core/maneuver_resolver.py, tests/test_terrain_cp19_integration.py
- Docs updated: CP19 docs renamed from DRAFT to FINAL
- Test count: 728 → 730
- **Status**: COMPLETE (CP-19 now FROZEN)

### SKR-002 Phase 3: Permanent Stat Modification Core
- Core algorithms: apply_permanent_modifier, calculate_effective_ability_score, restore_permanent_modifier
- Derived stat recalculation: HP max from CON, attack/damage from STR, AC from DEX, saves from ability mods
- HP clamping: current HP clamped to new HP max on CON drain
- Ability score death: score reaches 0 → ability_score_death event
- Inherent bonuses (Wish): stacks independently from drain
- Restoration: removes drain, capped at actual drain amount
- No RNG consumption (deterministic arithmetic only)
- Event types: permanent_stat_modified, derived_stats_recalculated, hp_changed, ability_score_death
- PBHA verification: 10× replay produces identical results
- Files added: aidm/core/permanent_stats.py, aidm/schemas/permanent_stats.py, tests/test_permanent_stats_core.py, tests/test_pbha_skr002.py
- Test count: 578 → 594
- **Status**: COMPLETE

### CP-18A: Mounted Combat & Rider-Mount Coupling (Implementation)
- Full mounted combat implementation per CP18A_MOUNTED_COMBAT_DECISIONS.md
- Rider-mount coupling with bidirectional references and validation
- Position derivation (rider from mount), movement delegation, AoO routing
- Higher ground bonus (+1 melee vs smaller on-foot), single attack restriction (>5 ft)
- Voluntary/forced dismount, unconscious saddle check
- Condition propagation (mount → rider only)
- Play loop integration for all mounted intents
- Attack resolver integration (mounted_bonus in event payload)
- AoO extension (MountedMoveIntent with mount as provoker)
- Determinism: 10× replay verified, "combat" RNG stream only
- Gate safety: G-T1 only (no spellcasting, no relational conditions, no entity forking)
- Files added: aidm/schemas/mounted_combat.py, aidm/core/mounted_combat.py, tests/test_mounted_combat_core.py, tests/test_mounted_combat_integration.py, docs/CP18A_MOUNTED_COMBAT_DECISIONS.md, docs/CP18A_RULES_COVERAGE_LEDGER.md, docs/CP18A_GATE_SAFETY_AUDIT.md
- Files modified: aidm/schemas/entity_fields.py, aidm/core/aoo.py, aidm/core/attack_resolver.py, aidm/core/play_loop.py
- Test count: 594 → 626 (32 new tests)
- **Status**: COMPLETE

### CP-18: Combat Maneuvers
- Combat maneuver schemas (BullRushIntent, TripIntent, OverrunIntent, SunderIntent, DisarmIntent, GrappleIntent)
- Result schemas (OpposedCheckResult, ManeuverResult, TouchAttackResult)
- Size modifier scale (PHB p.154: Fine -16 to Colossal +16)
- Entity field extensions (SIZE_CATEGORY, STABILITY_BONUS, GRAPPLE_SIZE_MODIFIER)
- **Bull Rush** (full): Opposed Str check, push 5 ft + 5 per 5 margin, +2 charge bonus
- **Trip** (full): Touch attack → opposed check (Str vs max(Str, Dex)), counter-trip on failure, applies Prone
- **Overrun** (full): Opposed check, AI-controlled avoidance, failure by 5+ = attacker prone
- **Sunder** (degraded): Opposed attack rolls, damage logged narratively, no persistent state change
- **Disarm** (degraded): Opposed attack rolls, weapon "drops" narratively, counter-disarm on failure
- **Grapple-lite** (degraded): Touch attack → opposed check, unidirectional Grappled condition (target only)
- AoO integration: Bull Rush provokes from ALL threatening; others provoke from TARGET only
- AoO damage auto-fail: Disarm and Grapple auto-fail if any AoO deals damage
- RNG discipline: All maneuvers use "combat" stream, documented consumption order
- Unified dispatcher (resolve_maneuver) routes by intent type
- Play loop integration: All 6 intent types validated and routed
- Gate safety: G-T1 only (Grapple-lite avoids G-T3C via unidirectional design)
- Determinism: 10× replay verified, identical final state hashes
- 53 new tests (36 Tier-1, 17 Tier-2), all passing in < 0.1 seconds
- Decisions document: docs/CP18_COMBAT_MANEUVERS_DECISIONS.md
- Files added: aidm/schemas/maneuvers.py, aidm/core/maneuver_resolver.py, tests/test_maneuvers_core.py, tests/test_maneuvers_integration.py
- Files modified: aidm/schemas/entity_fields.py, aidm/core/aoo.py, aidm/core/play_loop.py
- Test count: 626 → 679
- **Status**: COMPLETE

### M1: Solo Vertical Slice v0 (Runtime Layer)
- **Intent lifecycle schemas**: IntentObject with status transitions (PENDING → CLARIFYING → CONFIRMED → RESOLVED)
- **Immutability enforcement**: Intent frozen after CONFIRMED, only resolution fields modifiable
- **ActionType enum**: M1 action types (ATTACK, MOVE, USE_ABILITY, END_TURN, CAST_SPELL, BUY, REST)
- **Required field validation**: Per-action-type field requirements with get_missing_fields()
- **EngineResult schema**: Immutable authoritative resolution output (frozen in __post_init__)
- **EngineResultBuilder**: Mutable builder pattern for incremental result construction
- **RollResult**: Individual dice roll with RNG offset tracking for replay verification
- **StateChange**: Atomic state change (entity_id, field, old_value, new_value)
- **SessionLog**: Intent-to-result correlation with JSONL serialization
- **ReplayHarness**: Deterministic replay verification with 10× verification capability
- **CharacterSheet UI**: Read-only character view with derived value computation
- **PartySheet**: Aggregate party status display
- **Narrator**: Template-based narration from EngineResult narration tokens
- **NarrationTemplates**: Deterministic fallback templates (55 templates: attack, maneuver, save, environmental, mounted, etc.)
- **IPC Contract**: docs/runtime/IPC_CONTRACT.md (authority boundaries, data flow)
- **Intent Lifecycle**: docs/runtime/INTENT_LIFECYCLE.md (status transitions, immutability rules)
- **Engine Result Contract**: docs/runtime/ENGINE_RESULT_CONTRACT.md (result structure, replay requirements)
- **Reference**: docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md (LLM cage doctrine)
- Files added: aidm/schemas/intent_lifecycle.py, aidm/schemas/engine_result.py, aidm/core/session_log.py, aidm/ui/character_sheet.py, aidm/narration/narrator.py
- Test files added: tests/test_intent_lifecycle.py, tests/test_engine_result.py, tests/test_session_log.py, tests/test_character_sheet_ui.py, tests/test_narrator.py
- Docs added: docs/runtime/IPC_CONTRACT.md, docs/runtime/INTENT_LIFECYCLE.md, docs/runtime/ENGINE_RESULT_CONTRACT.md
- Test count: 751 → 893 (142 new tests across 5 test files)
- **Status**: COMPLETE

### M2: Campaign Prep Pipeline v0
- **Campaign schemas**: SessionZeroConfig, CampaignManifest, CampaignPaths, PrepJob, AssetRecord
- **Deterministic IDs**: compute_job_id(), compute_asset_id() — sha256-based, never RNG-driven
- **CampaignStore**: Filesystem-backed campaign persistence (create/load/save/list)
- **Campaign directory layout**: campaigns/&lt;campaign_id&gt;/manifest.json + events.jsonl + intents.jsonl + assets/ + prep/
- **PrepOrchestrator**: Deterministic job queue (INIT_SCAFFOLD → SEED_ASSETS → BUILD_START_STATE → VALIDATE_READY)
- **Idempotent execution**: Content hash checking, skip completed jobs on re-run
- **Append-only logging**: Job state changes logged to prep/prep_jobs.jsonl
- **AssetStore**: Asset management with shared cache resolution, integrity verification
- **WorldArchive**: Export/import bundle with pre-import validation
- **All deterministic, G-T1 only**: No LLM integration, all assets are placeholders
- Files added: aidm/schemas/campaign.py, aidm/core/campaign_store.py, aidm/core/prep_orchestrator.py, aidm/core/asset_store.py, aidm/core/world_archive.py
- Test files added: tests/test_campaign_schemas.py, tests/test_campaign_store.py, tests/test_prep_orchestrator.py, tests/test_asset_store.py, tests/test_world_archive.py
- Test count: 893 → 1028 (135 new tests across 5 test files)
- **Status**: COMPLETE

### M3: Immersion Layer v1
- **Immersion schemas**: Transcript, VoicePersona, AudioTrack, SceneAudioState, ImageRequest, ImageResult, GridEntityPosition, GridRenderState, AttributionRecord, AttributionLedger
- **STT adapter**: STTAdapter Protocol + StubSTTAdapter + create_stt_adapter() factory
- **TTS adapter**: TTSAdapter Protocol + StubTTSAdapter + create_tts_adapter() factory
- **Audio mixer**: compute_scene_audio_state() pure function (mood: combat/tense/peaceful from WorldState)
- **Mood rules**: active_combat → combat > hazards → tense > dark → tense > peaceful (priority order)
- **Transition tracking**: transition_reason tracks mood changes between states
- **Image adapter**: ImageAdapter Protocol + StubImageAdapter + create_image_adapter() factory
- **Contextual grid**: compute_grid_state() pure function (visible only during active combat)
- **Grid rules**: active_combat → visible/combat_active, was_visible → hidden/combat_ended, else → hidden/no_combat
- **Entity positions**: Extracted from entities[*].position, sorted by entity_id, dimensions from max x/y
- **Attribution store**: AttributionStore with fail-closed validation (asset_id + license required), JSON persistence
- **Protocol pattern**: typing.Protocol with @runtime_checkable (new pattern in codebase)
- **All atmospheric, non-authoritative**: Immersion never mutates WorldState, excluded from deterministic replay
- **All deterministic**: Pure functions produce identical output for identical input (10× verified)
- Files added: aidm/schemas/immersion.py, aidm/immersion/__init__.py, aidm/immersion/stt_adapter.py, aidm/immersion/tts_adapter.py, aidm/immersion/audio_mixer.py, aidm/immersion/image_adapter.py, aidm/immersion/contextual_grid.py, aidm/immersion/attribution.py, assets/ATTRIBUTION.json
- Test files added: tests/test_immersion_schemas.py, tests/test_voice_pipeline.py, tests/test_audio_transitions.py, tests/test_image_pipeline.py, tests/test_contextual_grid.py, tests/test_attribution_ledger.py, tests/test_immersion_integration.py
- Test count: 1028 → 1214 (165 new M3 tests across 7 test files; total reflects inclusion of previously untracked test files)
- **Status**: COMPLETE

### M3 Plan C: Immersion Hardening
- Authority contract testing: 38 tests for LLM boundary enforcement (immersion layer NEVER calls engine functions, NO RNG access)
- Forbidden call prevention: get_combat_state, resolve_attack, modify_entity, etc. verified as absent
- Contract violation scenarios: All 38 tests verify immersion modules cannot breach authority boundaries
- Stub-only LLM: All LLM adapters are stubs, no API keys, no remote calls
- Files added: tests/test_immersion_hardening.py, docs/IMMERSION_BOUNDARY.md
- Test count: 1214 → 1252 (38 new Plan C hardening tests)
- **Status**: COMPLETE

### M3 Plan C (Part 2): Post-M3 Hardening & Transition Readiness
- **Scope**: API freeze, authority contract enforcement, forward-compatibility, M4 integration notes, handoff documentation
- **API Stability**: PUBLIC_STABLE annotations in aidm/immersion/__init__.py (16 frozen exports, no removal/rename without migration)
- **Authority Contract**: AST-based import boundary analysis (whitelisted/forbidden imports), deepcopy non-mutation tests, output isolation tests — 12 tests in test_immersion_authority_contract.py
- **Determinism Canary**: test_immersion_determinism_canary.py (28 tests × 100 iterations = 2800 function calls, regression detector for RNG/timestamps/UUIDs)
- **Forward-Compatibility**: FUTURE_HOOK comments in audio_mixer.py (condition-driven cues, concentration moods) and contextual_grid.py (AoE overlays, terrain rendering)
- **M4 Integration Notes**: docs/M4_INTEGRATION_NOTES.md (spellcasting integration guidance, schema extension patterns, testing requirements, rollout strategy, 478 lines)
- **Handoff Document**: docs/IMMERSION_HANDOFF.md (complete API reference, maintenance guide, troubleshooting, file inventory, 12 sections)
- **Test Markers**: @pytest.mark.immersion_fast on all 243 immersion tests (registered in pyproject.toml), enables pytest -m immersion_fast
- **Files modified**: aidm/immersion/__init__.py (PUBLIC_STABLE annotations), audio_mixer.py (FUTURE_HOOK comments), contextual_grid.py (FUTURE_HOOK comments), pyproject.toml (marker registration)
- **Files added**: tests/test_immersion_authority_contract.py (12 tests), tests/test_immersion_determinism_canary.py (28 tests), docs/M4_INTEGRATION_NOTES.md, docs/IMMERSION_HANDOFF.md
- **Test count**: 1331 → 1359 (28 new determinism canary tests)
- **Runtime**: ~3.5 seconds (sub-millisecond for immersion layer)
- **Status**: COMPLETE

### M3 Edge Case Hardening: D&D 3.5e Corner Cases
- Edge case testing: 24 tests for obscure RAW mechanics (drowning while mounted, dismount during AoO, etc.)
- Ambiguous rules clarification: Documented rulings for edge cases not explicitly covered in PHB
- Coverage: Mounted combat (unconscious rider), terrain (falling while prone), conditions (stun + AoO), maneuvers (trip counter-trip while grappled)
- Files added: tests/test_edge_cases_35e.py
- Test count: 1252 → 1276 (24 new edge case tests)
- **Status**: COMPLETE

### CP-001: Position Type Unification (Phase 1)
- **Implementation date**: 2026-02-10
- **Scope**: Canonical Position type to consolidate 3 legacy grid position types
- **Resolves**: TD-001 (Three Duplicate Grid Position Types)
- **Test count impact**: 1359 → 1393 (34 new Position tests)
- **Runtime**: ~3.5 seconds (no significant change)

**Implementation:**
- **Canonical Position class**: aidm/schemas/position.py (180 lines)
  - Immutable dataclass (frozen=True) with integer x, y coordinates
  - distance_to() method using 1-2-1-2 diagonal math (PHB p.145)
  - is_adjacent_to() method for 8-directional adjacency (PHB p.137)
  - to_dict()/from_dict() for JSON serialization with deterministic key ordering
  - Type validation in __post_init__ (rejects non-integer coordinates)
  - __str__ and __repr__ for human-readable and debug representations
  - Hashable (can be used in sets and as dict keys)

**Backward Compatibility:**
- from_legacy_gridpoint_intents() — converts GridPoint (intents.py) to Position
- from_legacy_gridpoint_targeting() — converts GridPoint (targeting.py) to Position
- from_legacy_gridposition_attack() — converts GridPosition (attack.py) to Position
- to_legacy_dict() — converts Position to legacy dict format
- All helpers marked DEPRECATED (remove in CP-002)

**Test Coverage:**
- **Creation & validation**: 4 tests (valid coords, negative coords, zero coords, type rejection)
- **Distance calculation**: 6 tests (orthogonal, diagonal, mixed, self, negative coords, 1-2-1-2 math verification)
- **Adjacency checks**: 7 tests (orthogonal, diagonal, non-adjacent, self, all 8 directions)
- **Serialization**: 6 tests (to_dict, from_dict, roundtrip, missing keys, invalid types)
- **Immutability**: 2 tests (cannot modify x or y after creation)
- **Equality & hashing**: 3 tests (equality, inequality, hashable in sets/dicts)
- **String representation**: 2 tests (__str__, __repr__)
- **Legacy conversion**: 3 tests (GridPoint conversions, GridPosition conversion, to_legacy_dict)
- **Determinism (PBHA)**: 1 test (10× identical results for distance/adjacency)

**Files Added:**
- aidm/schemas/position.py (canonical Position type)
- tests/test_position.py (34 unit tests)

**Legacy Types (Not Modified, Will Deprecate in CP-002):**
- GridPoint in aidm/schemas/intents.py (bare x/y, no methods)
- GridPoint in aidm/schemas/targeting.py (has distance_to())
- GridPosition in aidm/schemas/attack.py (has is_adjacent_to())
- All legacy types emit DeprecationWarning when imported

**Next Steps:**
- **CP-002 Phase 2**: Migrate existing code to use Position, remove legacy types
- **CP-002 Phase 3**: Remove backward compatibility helpers

**Status**: COMPLETE (Phase 1)

### POST-AUDIT REMEDIATION (Plan A: Engine & Combat Corrections)
- **Audit completion date**: 2026-02-09
- **Scope**: 10 fixes (FIX-01 through FIX-18, excluding FIX-03, 04, 05, 12, 13, 14, 15, 16)
- **Severity**: 2 S1-CRITICAL, 6 S2-HIGH, 2 S3-MEDIUM
- **Test count impact**: 1276 → 1331 (55 new tests: 43 targeting resolver unit tests, 7 soft cover geometry tests, 5 miscellaneous)
- **Runtime**: ~3.4 seconds (no significant change)

**Fixes Applied:**
- **FIX-01** (S1): process_input() return type mismatch — retraction now returns (EngineResult, "action_retracted")
- **FIX-02** (S2): VisibilityBlockReason duplicate enum — merged into targeting.py canonical definition with 6 members
- **FIX-06** (S2): Missing direct tests for targeting_resolver.py — added test_targeting_resolver_unit.py with 43 tests
- **FIX-07** (S3): Missing EF.* constants — added ATTACK_BONUS, BAB, TEMPORARY_MODIFIERS, WEAPON to entity_fields.py
- **FIX-08** (S2): Bare string entity field accesses — replaced ~40+ accesses with EF.* constants across 8 files
- **FIX-09** (S2): Soft cover _is_between() geometry bug — replaced bounding-box algorithm with cross-product proximity test
- **FIX-10** (S3): Narration template coverage — expanded from 24 to 55 templates (attack, maneuver, save, environmental, mounted)
- **FIX-11** (S2): Shallow copy state mutation — replaced all shallow .copy() with deepcopy() across 9 files
- **FIX-17** (S2): Non-deterministic metadata — added timestamp injection parameters to campaign_store, engine_result, intent_lifecycle
- **FIX-18** (S2): Silent entity lookup defaults — added logging.warning() to targeting_resolver and maneuver_resolver

**Files Modified:**
- Core: session.py, targeting_resolver.py, maneuver_resolver.py, attack_resolver.py, save_resolver.py, combat_controller.py, conditions.py, aoo.py, tactical_policy.py, environmental_damage_resolver.py, mounted_combat.py, terrain_resolver.py, play_loop.py, full_attack_resolver.py
- Schemas: targeting.py, visibility.py, entity_fields.py, engine_result.py, intent_lifecycle.py, campaign.py
- Narration: narrator.py
- Tests: test_runtime_session.py, test_visibility.py, test_terrain_cp19_core.py
- New test file: tests/test_targeting_resolver_unit.py (43 tests)

**Tech Debt Closed:**
- TD-004 (bare string entity field accesses)
- TD-011 (process_input return type mismatch)
- TD-012 (duplicate VisibilityBlockReason)
- TD-013 (soft cover geometry)
- TD-014 (narration template coverage)
- TD-015 (shallow copy state mutation)

**Baseline Freeze:**
- All Plan A scope complete
- Test count: 1331 passing in ~3.4 seconds
- No further cleanup or small fixes allowed without explicit CP
- Next required CP: CP-001 Position Type Unification (TD-001)

- **Status**: COMPLETE

## ⚠️ MANDATORY FIRST READ FOR ALL AGENTS

**START HERE:**
- [AGENT_ONBOARDING_CHECKLIST.md](AGENT_ONBOARDING_CHECKLIST.md) — **READ THIS FIRST** — step-by-step reading order, verification steps, and quick-reference rules

**Required Reading (in order per onboarding checklist):**
1. This file (`PROJECT_STATE_DIGEST.md`) — What's built, test counts, module inventory
2. [AGENT_DEVELOPMENT_GUIDELINES.md](AGENT_DEVELOPMENT_GUIDELINES.md) — Coding standards, pitfall avoidance
3. [AGENT_COMMUNICATION_PROTOCOL.md](AGENT_COMMUNICATION_PROTOCOL.md) — How to flag concerns, gates, scope creep
4. [PROJECT_COHERENCE_DOCTRINE.md](PROJECT_COHERENCE_DOCTRINE.md) — Architectural constraints, scope boundaries
5. [KNOWN_TECH_DEBT.md](KNOWN_TECH_DEBT.md) — Things that look broken but are intentionally deferred

**Additional Resources:**
- [CP_TEMPLATE.md](CP_TEMPLATE.md) — Standard template for new completion packet decision documents
- [docs/AIDM_EXECUTION_ROADMAP_V3.md](docs/AIDM_EXECUTION_ROADMAP_V3.md) — Canonical roadmap and capability gates

**Failure to follow the onboarding checklist results in code reverts and scope reductions.**

---

## Canonical Project Plan Reference

**CANONICAL ROADMAP:**
- [AIDM_EXECUTION_ROADMAP_V3.md](docs/AIDM_EXECUTION_ROADMAP_V3.md) — Sole canonical roadmap, governance authority, capability gate definitions, M0-M4 milestone naming

**DESIGN LAYER (FROZEN):**
- [DESIGN_LAYER_ADOPTION_RECORD.md](docs/design/DESIGN_LAYER_ADOPTION_RECORD.md) — Formal design freeze declaration
- docs/design/*.md — 6 frozen design documents (SESSION_ZERO, CHARACTER_SHEET_UI, VOICE_INTENT, LLM_ENGINE_BOUNDARY, LOCAL_RUNTIME, SOLO_FIRST)

**NON-CANONICAL (Historical — Deleted):**
- ~~docs/AIDM_PROJECT_MASTER_PLAN.md~~ — Deleted (superseded by Execution Roadmap V3)
- ~~docs/AIDM_PROJECT_ACTION_PLAN_V2.md~~ — Deleted (superseded by Execution Roadmap V3)

**No ambiguity. No "see also." Execution Roadmap V3 is the sole source of truth for project direction, capability gates, and kernel requirements.**

---

## Capability Gate Status (Current)

All capability gates are defined in [AIDM_EXECUTION_ROADMAP_V3.md](docs/AIDM_EXECUTION_ROADMAP_V3.md).

**Current Gate Status:**

| Gate ID | Gate Name | Status |
|---------|-----------|--------|
| G-T1 | Tier 1 Mechanics | ✅ OPEN |
| G-T2A | Permanent Stat Mutation | 🔒 CLOSED |
| G-T2B | XP Economy | 🔒 CLOSED |
| G-T3A | Entity Forking | 🔒 CLOSED |
| G-T3B | Agency Delegation | 🔒 CLOSED |
| G-T3C | Relational Conditions | 🔒 CLOSED |
| G-T3D | Transformation History | 🔒 CLOSED |

**Gate enforcement:** Implementation of mechanics blocked by CLOSED gates is FORBIDDEN. See Action Plan V2 Section 1.4 for prohibited mechanics and acceptance criteria for each gate.

---

## Currently Legal Capabilities

**Only Tier 1 mechanics are currently legal for implementation and execution.**

Tier 1 capabilities unlocked by G-T1 (OPEN):
- Combat resolution (attack, full attack, critical hits)
- Initiative and action economy
- Attacks of opportunity (movement-triggered)
- Conditions and status effects (non-relational, non-permanent)
- Targeting and visibility
- Saving throws and defensive resolution (CP-17)

**Tier 1 spellcasting is NOT yet implemented.** CP-18A (Tier 1 Spellcasting Core) is defined and approved by DR-001 but not yet greenlit for implementation.

**All Tier 2 and Tier 3 mechanics are FORBIDDEN** until their respective capability gates open. See Action Plan V2 Section 6 for comprehensive deferred features list.

---

## Spellcasting Status

**CP-18A: Tier 1 Spellcasting Core**
- Status: Defined, approved by DR-001
- Scope: ~245 Tier 1 spells (damage, healing, buffs, detection, utility)
- Implementation: NOT yet greenlit
- Blocked mechanics: All Tier 2/3 spells (summoning, polymorph, dominate, resurrection, ability drain, XP-cost mechanics)

**No Tier 2 or Tier 3 spells are legal for implementation.** See Action Plan V2 Section 3 (DR-001) for spell exclusion list and gate requirements.

---

## Frozen Contracts (v0.3.0-post-audit-m3)

**Effective Date:** 2026-02-09 (commit f720744, tag v0.3.0-post-audit-m3)

The following modules, schemas, and subsystems are **contractually frozen** and may NOT be modified without an explicit Completion Packet (CP) that includes:
- Design rationale document
- Breaking change impact assessment
- Migration path for dependent systems
- Full test coverage of modifications

### Frozen Immersion Layer

**Scope:** All immersion layer modules and contracts

**Modules:**
- `aidm/immersion/__init__.py`
- `aidm/immersion/stt_adapter.py`
- `aidm/immersion/tts_adapter.py`
- `aidm/immersion/audio_mixer.py`
- `aidm/immersion/image_adapter.py`
- `aidm/immersion/contextual_grid.py`
- `aidm/immersion/attribution.py`

**Schemas:**
- `aidm/schemas/immersion.py` (all classes: Transcript, VoicePersona, AudioTrack, SceneAudioState, ImageRequest, ImageResult, GridEntityPosition, GridRenderState, AttributionRecord, AttributionLedger)

**Rationale:** Immersion layer is complete per M3 and hardened via Plan C (38 authority contract tests). Any changes risk breaking the LLM/engine boundary contract.

### Frozen Audit Remediation Schemas

**Scope:** All schemas modified during audit remediation (Plan A)

**Schemas:**
- `aidm/schemas/targeting.py` (VisibilityBlockReason enum — canonical definition)
- `aidm/schemas/visibility.py` (re-export contract from targeting.py)
- `aidm/schemas/entity_fields.py` (EF.* constant additions: ATTACK_BONUS, BAB, TEMPORARY_MODIFIERS, WEAPON)
- `aidm/schemas/engine_result.py` (timestamp injection parameters)
- `aidm/schemas/intent_lifecycle.py` (timestamp injection parameters)
- `aidm/schemas/campaign.py` (timestamp injection parameters)

**Rationale:** These schemas were stabilized during audit remediation. Any modification requires full regression testing across all 1331 tests.

### Frozen Replay & Determinism Semantics

**Scope:** Core determinism and replay contracts

**Semantics:**
- Event sourcing append-only contract (events NEVER modified after emission)
- RNG stream isolation (combat, initiative, policy, saves — NEVER mixed)
- State hash determinism (sorted keys, no sets, no floats)
- Replay re-execution strategy (TD-002 design: 4 event types in reducer, full re-execution for combat)
- Entity field access via EF.* constants (bare strings FORBIDDEN)
- State mutation via deepcopy() (shallow copy FORBIDDEN)
- EngineResult immutability (frozen dataclass with __setattr__ override)

**Modules:**
- `aidm/core/event_log.py`
- `aidm/core/rng_manager.py`
- `aidm/core/state.py`
- `aidm/core/replay_runner.py`

**Rationale:** Determinism is the foundational invariant. Any change to replay semantics invalidates all existing event logs and test fixtures.

### Frozen Narration Layer

**Scope:** Narrator module and template contract

**Modules:**
- `aidm/narration/narrator.py` (55 templates organized by category)

**Rationale:** Template coverage expanded to 55 templates during FIX-10. Template structure is now stable. Future work should externalize templates to data files (requires dedicated CP) rather than modifying in-code templates.

### Contract Violation Protocol

**If modification is required:**

1. **Create a CP design document** using [CP_TEMPLATE.md](CP_TEMPLATE.md)
2. **Include breaking change assessment**: Document ALL dependent systems affected
3. **Include migration path**: Provide backward compatibility strategy or deprecation timeline
4. **Include test plan**: Full regression test suite + new tests for modifications
5. **Get explicit approval** from project owner before implementation
6. **Update this section** to reflect new frozen state after CP completion

**Violation consequences:**
- Code reverts
- Loss of approval for future CPs
- Escalation to project governance review

---

## Structural Kernel Register (SKR) Status

**Tier 0 Kernels (Highest Priority):**
- **SKR-002 (Permanent Stat Modification)** — ✅ Phase 3 COMPLETE (Core algorithms implemented, 36 tests passing)
- SKR-008 (XP Economy & Permanence) — Design phase only
- SKR-001 (Entity Forking & Lineage) — Design phase only

**Tier 1 Kernels (Deferred):**
- SKR-003 (Agency Delegation & Control) — Deferred
- SKR-005 (Relational Conditions) — Deferred
- SKR-010 (Transformation History) — Deferred

**Tier 2+ Kernels (Deferred):**
- SKR-004 (Interrupt & Readied Actions) — Deferred
- SKR-011 (Negative Levels & Level Drain) — Deferred
- SKR-007 (Timeline Branching) — Deferred
- SKR-009 (Entity Suspension & Rejuvenation) — Deferred
- SKR-012 (Service Contracts & Obligations) — Deferred

See Action Plan V2 Section 5 for kernel catalog and development protocol.

---

## Non-Binding Design Docs

The following documents exist for reference but are **not authoritative** for current system state:
- AUDIT_REPORT.md (historical Vault ingestion audit)
- REUSE_DECISION.json (source reuse decisions)
- EXTRACTED_SOURCES_QUICK_REF.md (extracted source quick reference)
- WORKSPACE_MANIFEST.md (file inventory snapshot)
- SOURCE_LAYER_PLAN.md (historical migration plan)
- ~~docs/AIDM_PROJECT_MASTER_PLAN.md~~ (deleted — superseded by Execution Roadmap V3)

**Authoritative sources:**
- This file (PROJECT_STATE_DIGEST.md)
- [docs/AIDM_EXECUTION_ROADMAP_V3.md](docs/AIDM_EXECUTION_ROADMAP_V3.md)
- [PROJECT_COHERENCE_DOCTRINE.md](PROJECT_COHERENCE_DOCTRINE.md)
- README.md (user-facing documentation)
- Test suite (executable specification)
- Source code (ground truth)

## Key Design Principles (Locked)

1. **Determinism First**: All randomness deterministic, stable serialization, reproducible replay
2. **Event Sourcing**: State derived from append-only log, monotonic IDs
3. **Fail-Closed**: Unknown types rejected, missing state causes errors, no silent fallbacks
4. **Provenance & Citations**: All rulings traceable to source material pages
5. **Data-Only Schemas**: Contracts defined before algorithms, validation before implementation
6. **Prep vs Play Separation**: Async prep (slow, thorough), sync play (fast, deterministic)
7. **Voice-First Contracts**: Structured intents, not free-form NLU
8. **No Mercy Caps**: Doctrine is capability gating, not fairness balancing

## Non-Goals (Explicitly Out of Scope)

- Real-time gameplay optimization
- NLP/semantic search (current search is keyword-based)
- Rule interpretation (system retrieves text, doesn't parse rules)
- Campaign planning UI/workflows (campaign continuity records like session ledger, evidence ledger, and thread registry are allowed)
- Production ASR/TTS (voice layer is structured intents only)
- UI implementation (contracts only)
- LLM dependency in deterministic runtime (LLMs may be used in prep/narration layers as untrusted generators, gated by validators)

## Known Constraints

- **Page-level retrieval only**: No rule atomization or semantic chunking
- **Simple keyword search**: Token counting, no embeddings or ranking models
- **Core rulebooks only**: PHB, DMG, MM (966 pages total)
- **No Obsidian runtime dependency**: URIs generated but Obsidian not required
- **Voice intent schemas only**: No actual ASR/NLU integration
- **No UI implementation**: Interaction engine provides contracts only

## Critical Invariants

- All tests must pass in < 5 seconds
- All serialization must use sorted keys (deterministic JSON)
- Event IDs must be strictly monotonic
- RNG streams must remain isolated (combat, loot, narration)
- State mutations only through replay runner's single reducer
- Bundle validation must be fail-closed
- Doctrine enforcement blocks readiness by default (doctrine_required=True)
- Citation sourceId must be 12-character hex
- INT/WIS scores must be >= 1 or None (mindless)
- Policy config: top_k >= 1, temperature > 0
- **M2 Invariant: SPARK_SWAPPABLE = ACTIVE (binding)** — SPARK (LLM provider) MUST be user-swappable via configuration, NOT hard-coded (docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md)

## Governance Documents (M2+)

**Spark Swappability Enforcement:**
- [docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md](docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md) — Core M2 invariant: SPARK must be user-swappable via configuration, 5 STOP conditions with enforcement
- [docs/specs/SPARK_PROVIDER_CONTRACT.md](docs/specs/SPARK_PROVIDER_CONTRACT.md) — Interface contract for all SPARK providers (request/response schemas, capability manifests, model registry, adapter responsibilities)
- [docs/governance/M2_ACCEPTANCE_SPARK_SWAPPABILITY.md](docs/governance/M2_ACCEPTANCE_SPARK_SWAPPABILITY.md) — 6 binary pass/fail acceptance tests (TEST-001 through TEST-006), M2 completion gate
- [docs/governance/PR_GATE_CHECK_008_SPARK_SWAPPABILITY.md](docs/governance/PR_GATE_CHECK_008_SPARK_SWAPPABILITY.md) — PR gate CHECK-008 specification (audit script, violation patterns, enforcement workflow)
- [docs/governance/M2_ACCEPTANCE_TEST_MONITOR.md](docs/governance/M2_ACCEPTANCE_TEST_MONITOR.md) — Test execution tracking framework (status table, evidence archive, certification checklist)
- [docs/governance/M2_PR_GATE_CHECKLIST.md](docs/governance/M2_PR_GATE_CHECKLIST.md) — 10 mandatory PR gate checks (CHECK-001 through CHECK-010), submitter/reviewer workflows
- [scripts/audit_spark_swappability.sh](scripts/audit_spark_swappability.sh) — Automated grep audit script (6 checks: hard-coded paths, provider names, capability assumptions, LENS/BOX bypass)

**Enforcement Status:**
- ✅ CHECK-008 (Spark Swappability) — ACTIVE (M2+ gate requirement)
- ✅ Acceptance test framework — ACTIVE (0/6 tests passed, pending M2 implementation)
- ✅ Audit script — DEPLOYED (ready for PR gate execution)

## Future Work Queue (Not Started)

**No work items are greenlit for implementation.** All future work requires explicit authorization.

The following capabilities are defined but NOT authorized for implementation:
- CP-18A (Tier 1 Spellcasting Core) — Defined by DR-001, not yet greenlit
- SKR-002 (Permanent Stat Modification) — Design phase only
- SKR-008 (XP Economy & Permanence) — Design phase only
- SKR-001 (Entity Forking & Lineage) — Design phase only

## Design Complete / Implementation Authorized

(None at this time — CP-19 has been implemented)

Deferred capabilities (see Action Plan V2 Section 6):
- All Tier 2/3 spells (summoning, polymorph, dominate, resurrection, ability drain, XP-cost mechanics)
- All Tier 1+ kernels (SKR-003, SKR-005, SKR-010, SKR-004, SKR-011, SKR-007, SKR-009, SKR-012)

Additional candidates for future instruction packets:
- LLM-based prep pipeline (scene generation, NPC creation)
- Actual voice integration (ASR → intent parser)
- UI implementation (grid, token display, point selection)
- Rule atom extraction (structured rule database)
- Semantic search with embeddings

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

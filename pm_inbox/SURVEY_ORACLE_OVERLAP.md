# Oracle v5.2 Overlap Survey

**WO:** WO-ORACLE-SURVEY
**Date:** 2026-02-18
**Scope:** Map Oracle v5.2 data objects onto existing `aidm/` codebase. Identify SATISFIED, PARTIAL, and GREENFIELD gaps.

---

## 1. FactsLedger

**Oracle v5.2 contract:** Append-only canon facts with provenance. Every fact is content-addressed, immutable once written, and linked to its producing activity/agent.

**Existing code overlap:**

- [event_log.py:18-49](aidm/core/event_log.py#L18-L49) — `Event` dataclass: `event_id` (monotonic int), `event_type`, `timestamp`, `payload` (Dict), `rng_offset`, `citations` (List[Dict]), `event_schema_version`. Formal schema with versioning.
- [event_log.py:52-107](aidm/core/event_log.py#L52-L107) — `EventLog` class: append-only with monotonic ID enforcement (BL-008). `append()` rejects out-of-order/duplicate IDs via ValueError. `events` property returns `.copy()` to prevent external mutation. JSONL serialization with `sort_keys=True`.
- [provenance.py:32-42](aidm/core/provenance.py#L32-L42) — `compute_value_hash()`: SHA-256 (16-char prefix) of `json.dumps(value, sort_keys=True)`. Content-addressed hashing for any JSON-serializable value.
- [provenance.py:49-285](aidm/core/provenance.py#L49-L285) — Full W3C PROV-DM implementation: `ProvenanceEntity` (value_hash, created_at), `ProvenanceActivity` (activity_type: spark_generation/box_calculation/player_input), `ProvenanceAgent` (agent_type: spark/box/player/system), plus relation classes `WasGeneratedBy`, `WasAttributedTo`, `WasDerivedFrom`.
- [provenance.py:342-735](aidm/core/provenance.py#L342-L735) — `ProvenanceStore`: central registry with `register_entity()`, `record_generation()`, `record_attribution()`, `record_derivation()`, `get_provenance_chain()` (full ancestry), `explain()` (human-readable).

**Covering tests:**

- [test_event_log.py](tests/test_event_log.py) — `test_append_enforces_monotonic_event_id`, `test_append_rejects_non_sequential_ids`, `test_jsonl_roundtrip`, `test_event_to_dict_from_dict`
- [test_provenance.py](tests/test_provenance.py) — `TestComputeValueHash`, `TestProvenanceEntity`, `TestProvenanceActivity`, `TestProvenanceAgent`, `TestWasGeneratedBy`, `TestWasAttributedTo`, `TestWasDerivedFrom`, `TestProvenanceChain`, `TestExplain`, `TestSerialization`

**Gap assessment:**

- **SATISFIED:** Append-only event log with monotonic IDs, JSONL persistence, schema versioning. W3C PROV-DM provenance model with entity/activity/agent tracking and derivation chains.
- **SATISFIED:** Content-addressed hashing via `compute_value_hash()` (SHA-256, 16-char prefix).
- **PARTIAL:** Events carry `citations` (rule references with `source_id` + `page`) and optionally `content_id` (spell provenance), but provenance.py's ProvenanceStore is not wired into the EventLog — they are parallel systems. Events don't automatically register as ProvenanceEntities.
- **GREENFIELD:** No "fact" abstraction distinct from "event." Oracle's FactsLedger implies extracting durable facts from transient events (e.g., "Goblin is dead" persists; "Fireball was cast" is historical). The codebase has events but no fact extraction/persistence layer.

**Notes:** The building blocks exist (EventLog + ProvenanceStore), but they aren't connected. Oracle implementation would need to either (a) unify them by making EventLog entries register in ProvenanceStore, or (b) build a FactsLedger that reads from EventLog and extracts durable facts with provenance links.

---

## 2. StoryState

**Oracle v5.2 contract:** Evented pointers tracking world_id, campaign_id, scene_id, active threads, clocks, and mode (combat/exploration/roleplay). Changes via events, not direct mutation.

**Existing code overlap:**

- [state.py:26-75](aidm/core/state.py#L26-L75) — `WorldState`: `ruleset_version`, `entities` (Dict), `active_combat` (Optional Dict with `round_index`, `turn_counter`, `initiative_order`, `flat_footed_actors`, `aoo_used_this_round`, `duration_tracker`). Deterministic `state_hash()` via SHA-256 of sorted JSON.
- [campaign.py:191-269](aidm/schemas/campaign.py#L191-L269) — `CampaignManifest`: `campaign_id` (BL-017), `engine_version`, `config_schema_version`, `session_zero` (SessionZeroConfig), `paths` (CampaignPaths), `tool_versions`.
- [campaign.py:24-137](aidm/schemas/campaign.py#L24-L137) — `SessionZeroConfig`: `ruleset_id`, `optional_rules`, `alignment_mode`, `preparation_depth`, `visibility_prefs`, `creative_boundaries`, `doctrine_enforcement`. Frozen after campaign start; `amendments` list is append-only.
- [scene_manager.py](aidm/lens/scene_manager.py) — Scene transitions, encounters, rest mechanics, loot. Uses FrozenWorldStateView for reads. D&D 3.5e rest rules.
- [campaign_store.py:59-100](aidm/core/campaign_store.py#L59-L100) — `CampaignStore`: filesystem-backed persistence at `campaigns/<campaign_id>/` with `manifest.json`, `events.jsonl`, `intents.jsonl`, `assets/`, `prep/`.
- [session.py](aidm/runtime/session.py) — `SessionLog` with `IntentEntry` (intent + result + timestamp), append-only, `master_seed`.
- [session_log.py](aidm/core/session_log.py) — `SessionLog`: intent-to-result correlation, `master_seed`, `initial_state_hash`, JSONL serialization.

**Covering tests:**

- [test_state.py](tests/test_state.py) — `test_identical_state_produces_identical_hash`, `test_hash_stable_despite_dict_insertion_order`, `test_frozen_view_blocks_nested_dict_mutation`
- [test_campaign_store.py](tests/test_campaign_store.py) — `TestCampaignCreation`, `TestCampaignLoading`, `TestManifestSave`
- [test_session_log.py](tests/test_session_log.py) — `TestSessionLogEntry`, `TestSessionLog`, `TestVerifyResultMatch`, `TestReplayHarness`

**Gap assessment:**

- **SATISFIED:** Campaign-level identity (`campaign_id`, manifest, session zero config). Session-level logging with intent-result correlation. Filesystem-backed persistence.
- **SATISFIED:** WorldState carries combat mode implicitly (`active_combat` present/absent). Scene transitions exist in Lens layer.
- **PARTIAL:** No explicit `world_id` pointer in StoryState — WorldCompiler produces a `world_id` during compilation, but runtime doesn't track a mutable pointer to "current world." Campaign manifest has `campaign_id` but no `world_id` field.
- **PARTIAL:** No formal "mode" enum (combat/exploration/roleplay). The presence of `active_combat` in WorldState implies combat mode, but exploration and roleplay are not modeled.
- **GREENFIELD:** No "threads" or "clocks" concept. Oracle's active threads (quest lines, NPC arcs) and clocks (timers, deadlines) have no existing representation.
- **GREENFIELD:** No evented pointer mutation. WorldState changes happen through event reduction (replay_runner.py), but there's no StoryState object that updates its own pointers via events.

**Notes:** Campaign and session management exist, but they're storage-focused (persisting intents/events to disk), not pointer-focused (tracking "where are we in the story"). A StoryState object would sit between CampaignStore (persistence) and WorldState (mechanics), tracking narrative position.

---

## 3. Compactions

**Oracle v5.2 contract:** Non-canon accelerators that are reproducible from inputs. Derived views, caches, and summaries that speed up queries but can be rebuilt from source data.

**Existing code overlap:**

- [segment_summarizer.py:46-76](aidm/lens/segment_summarizer.py#L46-L76) — `SessionSegmentSummary`: frozen dataclass summarizing 10-turn segments. Fields: `segment_id`, `turn_range` (Tuple[int,int]), `summary_text`, `key_facts` (Tuple), `entity_states` (Tuple[Tuple[str,str],...]), `defeated_entities` (FrozenSet), `content_hash`, `schema_version`. Generated from NarrativeBrief history via **deterministic templates** (not LLM). Drift detection rebuilds from raw sources.
- [context_assembler.py:42-116](aidm/lens/context_assembler.py#L42-L116) — `ContextAssembler`: salience-ranked retrieval with token budget enforcement. `RetrievedItem` tracks provenance (`source`, `turn_number`, `relevance_score`, `dropped`, `drop_reason`). Heuristic ranking formula: `recency * 0.5 + actor_match * 0.3 + severity * 0.2`. Hard caps: MAX_RECENT_NARRATIONS=3, MAX_SESSION_SUMMARIES=5.
- [state.py:34-54](aidm/core/state.py#L34-L54) — `WorldState.state_hash()`: deterministic SHA-256 of sorted JSON. Functions as a state fingerprint for change detection.
- [campaign.py:285-385](aidm/schemas/campaign.py#L285-L385) — `PrepJob`: deterministic prep tasks with `compute_job_id()` (SHA256 of inputs) and `compute_output_hash()` (SHA256 of outputs). Idempotent via content hash.

**Covering tests:**

- [test_segment_summarizer_060.py](tests/test_segment_summarizer_060.py) — `TestSessionSegmentSummary`, `TestSegmentSummarizer`, `TestDriftDetection`, `TestRebuildFromSources`, `TestSegmentTracker`
- [test_context_assembler.py](tests/test_context_assembler.py) — `test_budget_enforced_*`, `test_priority_*`, `test_assemble_*`

**Gap assessment:**

- **SATISFIED:** SessionSegmentSummary is a textbook compaction — deterministic, reproducible from source NarrativeBriefs, with content_hash and drift detection. ContextAssembler's salience-ranked retrieval with budget enforcement is another compaction pattern.
- **SATISFIED:** PrepJob's idempotent content hashing ensures prep outputs are reproducible.
- **PARTIAL:** No explicit "rebuild all compactions" command. Segment summarizer has drift detection + rebuild, but there's no system-wide compaction invalidation/rebuild mechanism.
- **GREENFIELD:** No general-purpose compaction registry. Each module manages its own derived views independently. Oracle would need a registry that knows "these are all the compactions, here's how to invalidate and rebuild each one."

**Notes:** The codebase has compaction-shaped objects but no compaction-aware infrastructure. The segment summarizer is the closest match — it's explicitly designed to be rebuilt from source data. A Compaction registry would formalize what already exists informally.

---

## 4. UnlockState

**Oracle v5.2 contract:** Precision + artifact unlocks with default-deny semantics. Controls what information is visible to which consumer (player, DM, Spark). Mask safety ensures no accidental leakage.

**Existing code overlap:**

- [knowledge_mask.py:34-105](aidm/schemas/knowledge_mask.py#L34-L105) — `KnowledgeTier` IntEnum: UNKNOWN(0) < HEARD_OF(1) < SEEN(2) < FOUGHT(3) < STUDIED(4). `REVEAL_SPEC` maps tier → allowed fields. Progressive revelation: each tier unlocks specific entity fields (HEARD_OF: entity_type, display_name; STUDIED: ac, hp_max, hit_dice, special_abilities, cr, etc.).
- [knowledge_mask.py:120-244](aidm/schemas/knowledge_mask.py#L120-L244) — `DiscoveryEvent` (frozen, types: ENCOUNTER_SEEN, COMBAT_OBSERVED, STUDY_SUCCESS, NPC_TOLD_YOU), `KnowledgeEntry` (per-player per-entity tier + event_log + observed_facts), `MaskedEntityView` (filtered view — **absent fields, not redacted**).
- [narrative_brief.py](aidm/lens/narrative_brief.py) — One-way valve (BL-003): NarrativeBrief **excludes** entity IDs, raw HP, AC, bonuses, damage numbers, grid coordinates, RNG state. Default-deny for mechanical data flowing to Spark.
- [state.py:95-272](aidm/core/state.py#L95-L272) — `FrozenWorldStateView` (BL-020): `MappingProxyType` wrapping prevents mutation. `__setattr__`/`__delattr__` raise `WorldStateImmutabilityError`.

**Covering tests:**

- [test_discovery_log_knowledge_mask.py](tests/test_discovery_log_knowledge_mask.py) — `TestTierTransitions`, `TestMaskedView`, `TestFieldLeakage`, `TestRevealSpec`, `TestObservedFacts`, `TestSerialization`, `TestMultiEntity`
- [test_narrative_brief.py](tests/test_narrative_brief.py) — Tests for severity mapping, entity name resolution (excludes raw entity IDs)

**Gap assessment:**

- **SATISFIED:** KnowledgeMask implements progressive revelation with default-deny (absent fields, not redacted). KnowledgeTier ordering is monotonic (can only go up). Discovery events are frozen/immutable.
- **SATISFIED:** NarrativeBrief acts as a default-deny containment boundary — mechanical data cannot reach Spark. FrozenWorldStateView prevents mutation.
- **PARTIAL:** KnowledgeMask is per-entity visibility for players. Oracle's UnlockState may be broader — controlling visibility of world facts, locations, quest information, not just entity stats. The current system is entity-focused, not fact-focused.
- **GREENFIELD:** No "artifact unlocks" concept — unlocking a magic item's properties, revealing a map region, or granting access to a lore entry. KnowledgeMask handles entity stat revelation, but not arbitrary content unlocks.
- **GREENFIELD:** No per-consumer unlock differentiation beyond player/DM/Spark. Oracle implies finer-grained consumers.

**Notes:** Entity-level unlock is well-implemented. The gap is generalizing from "entity stat visibility" to "arbitrary content visibility." The KnowledgeMask pattern (tier enum + reveal spec + discovery events) is extensible — a content-level UnlockState could follow the same architecture.

---

## 5. WorkingSet

**Oracle v5.2 contract:** Deterministic bytes built from stores, producing byte-equal output on rebuild. The assembled context window that feeds downstream consumers (LLM, narration, UI).

**Existing code overlap:**

- [prompt_pack.py:58-401](aidm/schemas/prompt_pack.py#L58-L401) — Five-channel `PromptPack`: TruthChannel (hard constraints from NarrativeBrief), MemoryChannel (retrieved facts, session summaries, token budget), TaskChannel (task definition, output bounds, forbidden content), StyleChannel (tone parameters, persona), OutputContract (machine-checkable constraints). `to_json()` uses `json.dumps(sort_keys=True, ensure_ascii=True)` for **byte-level reproducibility**. `serialize()` produces deterministic text with explicit channel markers.
- [prompt_pack_builder.py:67-276](aidm/lens/prompt_pack_builder.py#L67-L276) — `PromptPackBuilder.build()`: assembles five-channel PromptPack from NarrativeBrief + session_facts + segment_summaries + style + contract. `_build_truth()` maps NarrativeBrief → TruthChannel. `_build_memory()` enforces token budget with truncation priority (previous_narrations > segment_summaries > session_facts).
- [narrative_brief.py](aidm/lens/narrative_brief.py) — `assemble_narrative_brief()`: deterministic event → brief transformation. One-way valve, no mechanical data leakage.
- [ipc_serialization.py:45-93](aidm/runtime/ipc_serialization.py#L45-L93) — `IPCEnvelope`: versioned message envelope with explicit key ordering, byte-for-byte deterministic round trips, strict type preservation, MessagePack transport.

**Covering tests:**

- [test_prompt_pack.py](tests/test_prompt_pack.py) — `test_serialize_deterministic`, `test_serialize_deterministic_10x`, `test_to_json_deterministic`, `test_to_dict_structure`, `test_serialize_has_channel_markers`
- [test_prompt_pack_builder.py](tests/test_prompt_pack_builder.py) — PromptPackBuilder assembly tests
- [test_narrative_brief.py](tests/test_narrative_brief.py) — Brief assembly, severity mapping, field population

**Gap assessment:**

- **SATISFIED:** PromptPack five-channel structure with deterministic serialization (`sort_keys=True`, `ensure_ascii=True`). Byte-equal output verified by `test_serialize_deterministic_10x`. PromptPackBuilder assembles from multiple stores (NarrativeBrief + memory + style).
- **SATISFIED:** NarrativeBrief assembly is deterministic (same events + token → same brief). Token-budget-aware memory assembly with deterministic truncation.
- **SATISFIED:** IPC serialization with byte-for-byte deterministic round trips.
- **PARTIAL:** The WorkingSet is implicitly the PromptPack, but there's no formal "rebuild from stores" mechanism that takes Oracle stores as input and produces a WorkingSet. The PromptPackBuilder takes pre-assembled components, not store references.
- **GREENFIELD:** No byte-equal rebuild verification (checksumming the output and comparing across rebuilds). The determinism tests exist in the test suite, but runtime doesn't verify "this rebuild matches the previous build."

**Notes:** This is the strongest overlap area. PromptPack is essentially a WorkingSet — deterministic bytes assembled from multiple sources. The gap is formalization: Oracle would name this pattern, add rebuild-from-stores semantics, and add runtime checksum verification.

---

## 6. Event Sourcing Infrastructure

**Contract summary:** The Box emits events (spell_cast, hp_changed, entity_defeated, etc.). How close is this to Oracle's EventLog — append-only, provenance-linked?

**Existing code overlap:**

- [event_log.py:18-107](aidm/core/event_log.py#L18-L107) — Append-only EventLog with monotonic IDs (BL-008), JSONL persistence with `sort_keys=True`, schema versioning (`event_schema_version`), `.copy()` on read.
- [play_loop.py](aidm/core/play_loop.py) — Primary event emitter. 50+ event types across spell resolution (spell_cast, spell_cast_failed, condition_applied, condition_removed, concentration_broken), HP changes (hp_changed, entity_defeated), turn flow (turn_start, turn_end, action_declared, movement_declared), and policy evaluation.
- [attack_resolver.py](aidm/core/attack_resolver.py) — attack_roll, damage_roll, hp_changed, entity_defeated, targeting_failed, concealment_miss events. Detailed payloads (flanking, cover, critical, sneak attack).
- [maneuver_resolver.py](aidm/core/maneuver_resolver.py) — 20+ maneuver event types (bull_rush_declared/success/failure, trip_declared/success/failure, grapple_declared/success/failure, etc.) plus opposed_check, touch_attack_roll.
- [spell_resolver.py:164-170](aidm/core/spell_resolver.py#L164-L170) — `content_id` field on spell definitions, propagated into event payloads for Layer B presentation lookup.
- [replay_runner.py](aidm/core/replay_runner.py) — Deterministic replay (BL-012). `reduce_event()` is the canonical state reducer. 34 mutating event types, 20+ informational event types classified separately. Replay from EventLog produces identical WorldState.
- [rng_manager.py:57-79](aidm/core/rng_manager.py#L57-L79) — Deterministic RNG with hash-based seed derivation: `SHA256(master_seed:stream_name)` → first 8 bytes as int. Only module allowed to import stdlib `random`.

**Covering tests:**

- [test_event_log.py](tests/test_event_log.py) — Monotonic enforcement, JSONL roundtrip
- [test_replay_runner.py](tests/test_replay_runner.py) — `test_replay_twice_produces_identical_hashes`, `test_replay_detects_divergence_on_event_order_change`, `test_reduce_event_does_not_mutate_original_state`
- [test_session_log.py](tests/test_session_log.py) — Intent-result correlation, 10x replay validation

**Gap assessment:**

- **SATISFIED:** Append-only event log with monotonic ordering, JSONL persistence, schema versioning. Deterministic replay via `reduce_event()`. RNG determinism via hash-based seed derivation.
- **SATISFIED:** Events carry provenance via `citations` (rule references: source_id + page) and `content_id` (spell content pack identifier). 50+ event types with rich payloads.
- **PARTIAL:** Events carry citations but are not linked to ProvenanceStore. The two systems (EventLog for ordering/replay, ProvenanceStore for derivation chains) exist independently.
- **PARTIAL:** No event-level content addressing. Individual events are not hashed — only WorldState is hashed via `state_hash()`. Oracle may want per-event content hashes for fine-grained verification.

**Notes:** Event sourcing is the most mature infrastructure in the codebase. The append-only EventLog + deterministic replay_runner + RNG manager form a solid foundation. The main gap is connecting events to provenance (linking each event to its producing activity/agent in the W3C PROV-DM model).

---

## 7. Canonical Serialization

**Contract summary:** Does existing code do deterministic JSON serialization with stable ordering? Or is this fully greenfield?

**Existing code overlap:**

- [event_log.py:74-79](aidm/core/event_log.py#L74-L79) — `to_jsonl()`: `json.dump(event.to_dict(), f, sort_keys=True)`. Deterministic JSONL output.
- [provenance.py:32-42](aidm/core/provenance.py#L32-L42) — `compute_value_hash()`: `json.dumps(value, sort_keys=True, default=str)` → SHA-256.
- [prompt_pack.py:395-401](aidm/schemas/prompt_pack.py#L395-L401) — `PromptPack.to_json()`: `json.dumps(sort_keys=True, ensure_ascii=True)`. Byte-level reproducibility.
- [state.py:34-54](aidm/core/state.py#L34-L54) — `WorldState.state_hash()`: `json.dumps(sort_keys=True)` → SHA-256 (full hex digest).
- [campaign.py:276-339](aidm/schemas/campaign.py#L276-L339) — `PrepJob.compute_job_id()`: `SHA256(campaign_id:job_type:stable_key)[:16]`. `compute_output_hash()`: `SHA256(json.dumps(outputs, sort_keys=True))`.
- [rng_manager.py:73-79](aidm/core/rng_manager.py#L73-L79) — RNG seed derivation: `SHA256(f"{master_seed}:{stream_name}")` → first 8 bytes as int64.
- [ipc_serialization.py:45-93](aidm/runtime/ipc_serialization.py#L45-L93) — `IPCEnvelope`: explicit key ordering, byte-for-byte deterministic round trips, MessagePack with strict_types=True.
- [world_archive.py](aidm/core/world_archive.py) — Campaign export uses sorted keys for determinism.

**Covering tests:**

- [test_prompt_pack.py](tests/test_prompt_pack.py) — `test_serialize_deterministic`, `test_serialize_deterministic_10x`, `test_to_json_deterministic`
- [test_state.py](tests/test_state.py) — `test_identical_state_produces_identical_hash`, `test_hash_stable_despite_dict_insertion_order`
- [test_provenance.py](tests/test_provenance.py) — `TestComputeValueHash`
- [test_replay_runner.py](tests/test_replay_runner.py) — `test_replay_twice_produces_identical_hashes`
- [test_immutability_gate.py](tests/test_immutability_gate.py) — Automated gate scanning all frozen dataclasses for mutable container fields

**Gap assessment:**

- **SATISFIED:** `json.dumps(sort_keys=True)` is the canonical serialization pattern across the codebase. Used in: EventLog, ProvenanceStore, WorldState.state_hash(), PromptPack.to_json(), PrepJob hashing. Consistent and deliberate.
- **SATISFIED:** SHA-256 is the universal hash algorithm (16-char prefix for IDs, full hex digest for state hashes).
- **SATISFIED:** Immutability gate (`test_immutability_gate.py`) automatically verifies all frozen dataclasses protect mutable container fields.
- **PARTIAL:** No canonical serialization module — each module independently uses `json.dumps(sort_keys=True)`. Oracle could formalize this into a shared `canonical_serialize()` utility.
- **GREENFIELD:** No MessagePack or Protobuf for compact binary canonical form. IPC uses MessagePack, but it's transport-only, not a storage canonical form.

**Notes:** Canonical serialization is a strength of this codebase. The pattern `json.dumps(sort_keys=True) → SHA-256` is used consistently. The gap is formalization — a single `canonical_serialize()` function that all modules call, rather than each repeating the pattern. This is a low-risk refactor.

---

## Summary Matrix

| Oracle Object | SATISFIED | PARTIAL | GREENFIELD |
|---|---|---|---|
| **FactsLedger** | EventLog (append-only, monotonic, JSONL), ProvenanceStore (W3C PROV-DM, content hashing) | Provenance not wired to EventLog | Fact extraction from events (durable facts vs transient events) |
| **StoryState** | Campaign manifest + session zero + session log, WorldState with combat mode | No world_id pointer, no formal mode enum | Threads, clocks, evented pointer mutation |
| **Compactions** | SessionSegmentSummary (deterministic, content_hash, drift detection, rebuild), PrepJob (idempotent content hashing) | No system-wide rebuild command | General-purpose compaction registry |
| **UnlockState** | KnowledgeMask (progressive revelation, default-deny, absent fields), NarrativeBrief (containment boundary), FrozenWorldStateView | Entity-focused only, not fact/content-focused | Artifact unlocks, per-consumer differentiation |
| **WorkingSet** | PromptPack (5-channel, byte-equal serialization, deterministic assembly), NarrativeBrief, IPC envelope | No formal rebuild-from-stores, no runtime checksum verification | — |
| **Event Sourcing** | EventLog + replay_runner + RNG determinism, 50+ event types, citations + content_id | EventLog not linked to ProvenanceStore, no per-event hashing | — |
| **Canonical Serialization** | json.dumps(sort_keys=True) + SHA-256 used consistently, immutability gate | No shared canonical_serialize() utility | No compact binary canonical form for storage |

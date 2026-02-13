# RWO-005: Seam Protocol Analysis

**Status:** COMPLETE
**Date:** 2026-02-12
**Author:** Opus (RWO-005 Agent)
**Scope:** Three architectural seams — Box-Lens, Lens-Spark, Spark-Immersion

---

## 1. Executive Summary

The AIDM system's four-layer architecture (Box / Lens / Spark / Immersion) is connected by three boundary seams. This analysis audited each seam for: typed contract coverage, enforcement rigor, containment gaps, determinism guarantees, and error handling.

**Overall Health Assessment: YELLOW (Structurally Sound, Operationally Incomplete)**

The structural foundations are strong. Import-boundary enforcement via AST-scanning tests (`test_boundary_law.py` BL-001 through BL-020) prevents the most dangerous coupling violations. Frozen dataclasses and immutability proxies protect Box authority. Kill switches provide fail-closed enforcement at the Lens-Spark boundary.

However, three critical integration gaps exist:

1. **Seam 1 (Box to Lens):** The NarrativeBrief assembler consumes events as `List[Dict[str, Any]]`, not as typed `StructuredTruthPacket` instances. The typed payload schemas in `aidm/schemas/box_events.py` are defined but not wired into the NarrativeBrief assembly path. Unknown event types pass through as raw dicts without validation.

2. **Seam 2 (Lens to Spark):** There is no canonical PromptPack schema. Context assembly produces a plain `str` without versioning, channel separation, or deterministic serialization. AD-002 specifies a five-channel wire protocol; current implementation is a monolithic string builder.

3. **Seam 3 (Spark to Immersion):** There is no ImmersionPlan schema connecting narration output to immersion adapter invocations. TTS, STT, and image adapters exist as isolated protocol interfaces but nothing orchestrates when or how narration text flows into them.

**Severity Summary:**
- 2 gaps rated CRITICAL (GAP-002, GAP-004)
- 3 gaps rated HIGH (GAP-001, GAP-003, GAP-005)
- 3 gaps rated MEDIUM (GAP-006, ~~GAP-007 RESOLVED~~, GAP-008)

---

## 2. Seam 1: Box to Lens

### 2.1 Current Contract

**Data Flow:** Box produces mechanical events (attack rolls, damage, conditions, defeats) as `Dict[str, Any]` payloads inside `Event` objects. Lens transforms these into `NarrativeBrief` instances for downstream consumption by Spark.

**Typed Interfaces:**

| Interface | File | Status |
|---|---|---|
| `StructuredTruthPacket` | `aidm/core/truth_packets.py:447` | Defined, 11 STP types with frozen payload dataclasses |
| `STPType` enum | `aidm/core/truth_packets.py:31` | 11 members: ATTACK_ROLL through CONDITION_REMOVED |
| Box event schemas | `aidm/schemas/box_events.py:29-256` | 10 frozen payload dataclasses with `PAYLOAD_SCHEMAS` registry |
| `NarrativeBrief` | `aidm/lens/narrative_brief.py:42` | Frozen dataclass, 13 fields, all Spark-safe |
| `FrozenWorldStateView` | `aidm/core/state.py:91` | Read-only proxy with MappingProxyType wrapping |
| `BoxLensBridge` | `aidm/core/box_lens_bridge.py:46` | Sync layer: Grid entities/cells to LensIndex facts |
| `validate_event_payload()` | `aidm/schemas/box_events.py:273` | Schema validation, returns typed dataclass or None |

**What Crosses the Boundary:**
- Event dicts with `event_type` string and `payload` dict (Box to Lens)
- `FrozenWorldStateView` for entity name resolution and HP data (Box to Lens, read-only)
- `NarrativeBrief` as the output of the transformation (Lens produces, Spark consumes)

### 2.2 Enforcement

**STRONG — Structurally enforced at import level, partially enforced at runtime.**

Import enforcement:
- BL-003 (`test_boundary_law.py:121`): `aidm/narration/` must never import from `aidm.core` — enforced via AST scanning
- BL-004 (`test_boundary_law.py:145`): `aidm/core/` must never import from `aidm.narration` — enforced via AST scanning
- BL-020 (`test_boundary_law.py:799`): Non-engine modules receive `FrozenWorldStateView`, not raw `WorldState`

Data containment:
- `NarrativeBrief` is `frozen=True` (line 42) — immutable after creation
- `NarrativeBrief` docstring explicitly lists forbidden fields: entity IDs, raw HP, AC, attack bonuses, damage numbers, grid coordinates, RNG state (lines 7-20)
- `resolve_entity_name()` (line 192) converts entity IDs to display names
- `compute_severity()` (line 142) converts raw HP damage to categorical severity strings

**Runtime validation gap:** The `assemble_narrative_brief()` function (line 244) processes events by matching `event.get("type")` or `event.get("event_type")` against hardcoded strings (`"attack_roll"`, `"damage_dealt"`, `"hp_changed"`, `"entity_defeated"`, `"condition_applied"`). Events with unrecognized types are silently ignored — their data does not enter the NarrativeBrief. This is safe-by-default (unrecognized events cannot contaminate Spark context) but means new Box event types require manual NarrativeBrief assembler updates.

### 2.3 Gaps

**GAP-001: Unknown Box events pass through as raw dicts (HIGH)**

The `validate_event_payload()` function in `aidm/schemas/box_events.py:273` returns `None` for unregistered event types — by design ("everything else stays Dict[str, Any] until it breaks twice", line 281). The `assemble_narrative_brief()` function in `aidm/lens/narrative_brief.py:277` iterates events and only processes five known types. Unknown types are silently skipped, which is fail-safe for containment but means:
- New event types added by Box resolvers will produce no narration until NarrativeBrief is updated
- There is no logging or alerting when unknown event types are encountered
- The `PAYLOAD_SCHEMAS` registry in `box_events.py:245` has 10 entries, but `assemble_narrative_brief` only handles 5 event types — the other 5 (`turn_start`, `turn_end`, `spell_cast`, `save_rolled`, `condition_removed`) are defined but not consumed

**GAP-003: NarrativeBrief containment matrix is incomplete (HIGH)**

The NarrativeBrief docstring (lines 7-20) defines what it must NOT contain, and the `assemble_narrative_brief()` function strips entity IDs to display names and converts damage to severity. However:
- **Spell names** are not extracted — the `"spell"` branch in `_build_outcome_summary()` (line 395) says only "casts a spell" without extracting spell_name from the event
- **Distance/range** is never populated — no event type provides distance data to NarrativeBrief
- **DCs** (difficulty classes) from saving throw events are not surfaced — `save_rolled` events are not processed by `assemble_narrative_brief`
- **Condition duration** from `condition_applied` events is not forwarded — only the condition name reaches NarrativeBrief

**GAP-006: Dual STP systems are not unified (MEDIUM)**

Two parallel STP systems exist:
1. `aidm/core/truth_packets.py` — `StructuredTruthPacket` with `STPBuilder`, `STPLog`, typed payloads (1141 lines)
2. `aidm/schemas/box_events.py` — frozen payload dataclasses with `PAYLOAD_SCHEMAS` registry (351 lines)

The `StructuredTruthPacket` system includes `packet_id`, `turn`, `initiative_count`, `rule_citations`, and a formal `PAYLOAD_REGISTRY`. The `box_events.py` system has simpler flat dataclasses matching what resolvers actually emit. Neither system is wired end-to-end: `StructuredTruthPacket` instances are never constructed by actual resolvers in the codebase, and `box_events.py` validation is "opt-in at the orchestrator extraction point" (line 8). The NarrativeBrief assembler uses neither — it reads raw dicts directly.

### 2.4 Determinism

**Deterministic.** The Box-to-Lens data flow is fully deterministic:
- Box events are produced by deterministic resolvers consuming `DeterministicRNG` streams (BL-005, BL-009)
- `NarrativeBrief` assembly is a pure function of events + `FrozenWorldStateView` — no randomness, no timestamps, no I/O
- `compute_severity()` uses fixed percentage thresholds
- Entity name resolution reads from frozen state
- `EngineResult` is immutable after creation (BL-007, `__post_init__` freeze)

**Replay impact:** NarrativeBrief is not part of the replay hash (it is a derived view, not authoritative state). This is correct — narration is downstream of Box authority and does not feed back.

### 2.5 Error Handling

- **Missing entity:** `resolve_entity_name()` (line 207) falls back to returning the raw entity_id string
- **Missing HP data:** `get_entity_hp_data()` (line 229) returns `(0, 0)` for unknown entities
- **Division by zero:** `compute_severity()` (line 169) returns `"minor"` when `target_hp_max <= 0`
- **Unknown event types:** Silently ignored in `assemble_narrative_brief()` — no crash, but no narration
- **Missing event fields:** `event.get("attacker", actor_id)` pattern preserves previous values — degraded but functional

**Failure mode:** Silent degradation. If Box emits events with unexpected shapes, NarrativeBrief will contain default values ("someone", severity="minor") rather than crash. This is appropriate for a containment boundary but should be logged.

---

## 3. Seam 2: Lens to Spark

### 3.1 Current Contract

**Data Flow:** Lens assembles context from `NarrativeBrief` into a plain text prompt string. Spark generates narration text. Lens validates the output through `GrammarShield` (mechanical assertion detection) and `GuardedNarrationService` kill switches.

**Typed Interfaces:**

| Interface | File | Status |
|---|---|---|
| `ContextAssembler` | `aidm/lens/context_assembler.py:27` | Token-budget-aware string builder |
| `NarrationRequest` | `aidm/narration/guarded_narration_service.py:152` | Wraps EngineResult + FrozenMemorySnapshot |
| `NarrationResult` | `aidm/narration/guarded_narration_service.py:183` | Text + provenance tag |
| `SparkRequest` | `aidm/spark/spark_adapter.py:38` | Validated prompt + temperature + max_tokens |
| `SparkResponse` | `aidm/spark/spark_adapter.py:72` | Text + finish_reason + tokens_used |
| `GrammarShield` | `aidm/spark/grammar_shield.py:144` | Output validator with retry |
| `KillSwitchRegistry` | `aidm/narration/kill_switch_registry.py:118` | 6 kill switches, fail-closed |
| `NarrationTemplates` | `aidm/narration/narrator.py:82` | 55+ deterministic template strings |

**What Crosses the Boundary:**
- `NarrativeBrief` to `ContextAssembler` — Lens input
- Plain text string (assembled prompt) — Lens to Spark
- Plain text string (generated narration) — Spark to Lens
- `EngineResult` (frozen) — Lens input for template fallback
- Kill switch state — Lens-internal enforcement

### 3.2 Enforcement

**STRONG on output validation, WEAK on input schema.**

Output enforcement (Spark to Lens):
- `GrammarShield` (`grammar_shield.py:144`) validates all Spark output against 8 compiled regex patterns for mechanical assertions: damage quantities, AC values, HP values, rule citations, attack bonuses, DCs, die rolls, dice notation (lines 77-86)
- `GrammarShield.validate_and_retry()` retries up to 2 times with stricter prompts, then raises `MechanicalAssertionError`
- `detect_mechanical_assertions()` in `kill_switch_registry.py:90` provides a second layer with 5 patterns (damage, AC, HP, rule citations, attack bonus) — used by `GuardedNarrationService` to trigger KILL-002
- KILL-001 through KILL-006 provide comprehensive fail-closed enforcement:
  - KILL-001: Memory hash mutation detection
  - KILL-002: Mechanical assertion in output
  - KILL-003: Token overflow (> 110% of max_tokens)
  - KILL-004: Latency > 10 seconds
  - KILL-005: Consecutive rejections > 3
  - KILL-006: World state hash drift

Input enforcement (Lens to Spark):
- `SparkRequest.__post_init__()` (line 63) validates: non-empty prompt, temperature in [0.0, 2.0], positive max_tokens (BL-013)
- `NarrationRequest.__post_init__()` (line 167) validates: temperature >= 0.7 for narration (LLM-002)
- `FrozenMemorySnapshot.create()` (line 101) hashes memory before narration for KILL-001 drift detection

**Template fallback:**
- When any kill switch fires, or when Spark is unavailable, `GuardedNarrationService` falls back to `NarrationTemplates.get_template()` (55+ deterministic templates)
- Template narration uses `format_map(safe_defaults)` with a `defaultdict(lambda: "something")` (line 728-739) — never crashes on missing data

### 3.3 Gaps

**GAP-002: No canonical PromptPack schema for Lens-to-Spark prompt assembly (CRITICAL)**

AD-002 (`docs/decisions/AD-002_LENS_CONTEXT_ORCHESTRATION.md`) specifies a five-channel PromptPack wire protocol:
1. Truth Channel (hard constraints from Box)
2. Memory Channel (retrieved, scoped facts)
3. Task Channel (narration/dialogue/summary)
4. Style Channel (persona, tone)
5. Output Contract (machine-checkable schema)

Current implementation in `ContextAssembler.assemble()` (line 41) produces a single plain text string with:
- Priority 1: NarrativeBrief formatted as pipe-delimited key-value pairs (line 113-129)
- Priority 2: Scene description as "Location: {text}" (line 72)
- Priority 3: Recent narrations as bullet list (line 131-172)
- Priority 4: Session history summaries (line 174-213)

This is a monolithic string with no channel markers, no schema versioning, no output contract, and no deterministic serialization guarantee. The token budget estimator (line 215-228) uses `len(text.split()) * 1.3` — a rough heuristic, not a tokenizer.

**Consequences:**
- Cannot verify prompt determinism (same inputs may produce different byte-level prompts if formatting varies)
- Cannot enforce truncation priority (AD-002 says Truth channel is NEVER truncated, but all channels are in the same string)
- Cannot validate Spark output against a per-task schema
- Cannot version the prompt format for migration

Additionally, `GuardedNarrationService._build_llm_prompt()` (line 622) constructs a SECOND, independent prompt format that is not coordinated with `ContextAssembler`. Two prompt assembly paths exist without shared schema.

**GAP-007: Two independent prompt assembly paths (MEDIUM) — RESOLVED (WO-057)**

`GuardedNarrationService` previously had two prompt paths:
1. `_build_llm_prompt()` (line 622) — builds a prompt from `NarrationRequest` with session facts from `FrozenMemorySnapshot`, ignoring `ContextAssembler` entirely
2. `ContextAssembler.assemble()` — builds from `NarrativeBrief`, never used by `GuardedNarrationService`

**Resolution:** WO-057 introduced `PromptPackBuilder` (`aidm/lens/prompt_pack_builder.py`) which assembles all five PromptPack channels from NarrativeBrief + session_facts. When `narrative_brief` is present on `NarrationRequest`, both `GuardedNarrationService` and `SessionOrchestrator` use the PromptPack path. `_build_llm_prompt()` is deprecated but preserved for backward compatibility (used when `narrative_brief` is absent). `ContextAssembler` is retained but no longer called from the main narration pipeline.

### 3.4 Determinism

**Partially deterministic.** Template narration is fully deterministic (same NarrativeBrief + same EngineResult = same text). LLM narration is inherently non-deterministic (temperature >= 0.7 per LLM-002), but this is by design — narration is non-authoritative.

`ContextAssembler.assemble()` is deterministic given identical inputs (no randomness, no timestamps, no I/O in the assembly path). Token estimation is deterministic (word count * 1.3).

**Replay concern:** Narration text is not part of the replay hash, so LLM non-determinism does not break replay. However, if narration text is stored in session logs and used as `previous_narrations` input for future calls, LLM non-determinism creates session divergence across replays. This is acceptable for atmospheric purposes but should be documented.

### 3.5 Error Handling

**Comprehensive fail-closed cascade:**

1. **Spark unavailable:** `SPARK_AVAILABLE = False` at import time (line 58) — falls back to template narration
2. **LLM generation fails:** Caught by `except Exception` (line 369) — falls back to template narration
3. **Token overflow (KILL-003):** Triggers kill switch, falls back to template (line 341-351)
4. **Latency exceeded (KILL-004):** Triggers kill switch, falls back to template (line 328-338)
5. **Mechanical assertion (KILL-002):** Triggers kill switch, falls back to template (line 354-367)
6. **Memory mutation (KILL-001):** Raises `NarrationBoundaryViolation` — halts narration entirely (line 397-400)
7. **Consecutive failures (KILL-005):** Triggers after 3 consecutive rejections — permanent halt until manual reset (line 440-451)
8. **World state drift (KILL-006):** Triggers via `check_world_state_drift()` callback (line 416-438)

**Template fallback is always available:** `NarrationTemplates.get_template()` (line 211) returns `TEMPLATES["unknown"]` = `"Something happens..."` for any unrecognized token.

---

## 4. Seam 3: Spark to Immersion

### 4.1 Current Contract

**Data Flow:** Spark produces narration text. Immersion adapters (TTS, STT, image generation) consume text or narration context to produce audiovisual output. Currently, there is no orchestration layer connecting Spark output to Immersion input.

**Typed Interfaces:**

| Interface | File | Status |
|---|---|---|
| `TTSAdapter` Protocol | `aidm/immersion/tts_adapter.py:17` | `synthesize(text, persona) -> bytes` |
| `STTAdapter` Protocol | `aidm/immersion/stt_adapter.py:17` | `transcribe(audio_bytes, sample_rate) -> Transcript` |
| `ImageAdapter` Protocol | `aidm/immersion/image_adapter.py:18` | `generate(request) -> ImageResult` |
| `VoicePersona` | `aidm/schemas/immersion.py:75` | Persona config: voice_model, speed, pitch, reference_audio |
| `ImageRequest` | `aidm/schemas/immersion.py:290` | kind, semantic_key, prompt_context, dimensions |
| `ImageResult` | `aidm/schemas/immersion.py:349` | status, asset_id, path, content_hash |
| `Transcript` | `aidm/schemas/immersion.py:28` | text, confidence, adapter_id |
| `SceneAudioState` | `aidm/schemas/immersion.py:231` | active_tracks, mood, transition_reason |
| `TriGemSocket` | `aidm/immersion/tri_gem_socket.py:1072` | Transparency filter for Box events |
| `CombatReceipt` | `aidm/immersion/combat_receipt.py` | Table-native formatted combat output |

**What Should Cross the Boundary:**
- Narration text (Spark output) to TTS adapter for synthesis
- Narration context (scene description, characters, mood) to image adapter for generation
- Box event stream (via TriGemSocket) to transparency UI

### 4.2 Enforcement

**STRONG on boundary isolation, ABSENT on orchestration.**

Import/authority enforcement:
- BL-001 (`test_boundary_law.py:74`): Spark must never import from `aidm.core`
- BL-005 (`test_boundary_law.py:207`): Immersion must never import RNGManager
- BL-006 (`test_boundary_law.py:247`): Immersion must never import stdlib random
- BL-020 (`test_boundary_law.py:910`): Non-engine modules (including Immersion) must not import `WorldState`
- `IMMERSION_BOUNDARY.md`: Explicit contract — immersion may NOT mutate WorldState, affect engine decisions, consume RNG, or appear in replay hash

Adapter enforcement:
- All adapters use `typing.Protocol` with `@runtime_checkable` — structural typing
- All adapters have `StubXAdapter` defaults that return safe empty/placeholder values
- Factory functions default to `"stub"` backend — zero external dependencies required
- Real backends are lazy-loaded inside factory functions, never at module level
- `ImageRequest.validate()` and `VoicePersona.validate()` provide field-level validation

**What is NOT enforced:**
- No schema defines WHEN to invoke TTS after narration
- No schema defines HOW narration context maps to `ImageRequest.prompt_context`
- No schema defines orchestration order (TTS before/after/parallel with image?)
- No schema partitions log entries into authoritative vs atmospheric

### 4.3 Gaps

**GAP-004: No ImmersionPlan schema for Spark-to-Immersion orchestration (CRITICAL)**

There is no typed interface connecting narration output to immersion adapter calls. The adapter protocols are well-defined in isolation:
- `TTSAdapter.synthesize(text, persona)` — but who calls it? With what text?
- `ImageAdapter.generate(request)` — but who builds the `ImageRequest`? From what context?
- `STTAdapter.transcribe(audio_bytes)` — but how does transcribed text enter the game loop?

A hypothetical `ImmersionPlan` would specify:
```
ImmersionPlan {
    narration_text: str           # From Spark/GuardedNarrationService
    tts_request: Optional[TTSRequest]   # Should TTS synthesize this?
    image_request: Optional[ImageRequest] # Should an image be generated?
    audio_state: Optional[SceneAudioState] # What ambient audio to play?
    transparency_mode: TransparencyMode   # How to filter events for display
}
```

Without this schema, each integration point (UI, CLI, web frontend) must independently:
1. Receive narration text from `GuardedNarrationService`
2. Decide whether to invoke TTS
3. Build an `ImageRequest` from... somewhere (no mapping exists)
4. Compute `SceneAudioState` from world state
5. Filter events through `TriGemSocket`

This ad hoc integration is the primary risk for the Spark-to-Immersion seam.

**GAP-005: No authoritative vs atmospheric log partition spec (HIGH)**

The system produces two types of output:
1. **Authoritative:** Box events, STPs, EngineResults — these constitute the game record
2. **Atmospheric:** Narration text, TTS audio, generated images, ambient audio — these enhance presentation

Currently there is no formal specification for how these are partitioned in logs or session records. The `IMMERSION_BOUNDARY.md` states "immersion outputs are excluded from deterministic replay verification" but does not define:
- Where atmospheric outputs are stored
- Whether atmospheric outputs are included in session save files
- How to distinguish authoritative events from atmospheric annotations in a combined log
- Whether narration text (which bridges both — it is Lens output derived from Box events) is authoritative or atmospheric

The `TriGemSocket` provides per-player transparency filtering of Box events, but this is a read-only view layer, not a log partitioning spec.

**GAP-008: STT-to-game-loop path undefined (MEDIUM)**

`STTAdapter.transcribe()` returns a `Transcript` with text and confidence. But:
- No interface defines how transcribed text becomes a player intent
- No validation ensures transcribed text is parseable as a game command
- No confidence threshold determines when to accept vs reject transcription
- The `Transcript.adapter_id` field tracks provenance but nothing consumes it

STT is an atmospheric input adapter with no upstream integration. This is appropriate for M3 (immersion layer launch) but creates a gap for voice-command gameplay.

### 4.4 Determinism

**Not applicable — by design.** Immersion output is explicitly excluded from deterministic replay per `IMMERSION_BOUNDARY.md`:
- "immersion outputs are excluded from deterministic replay verification"
- "immersion state is excluded from deterministic replay" (`aidm/schemas/immersion.py:17`)

Pure functions (`compute_scene_audio_state`, `compute_grid_state`) are deterministic (verified 10x in tests per `IMMERSION_BOUNDARY.md`). Adapter outputs (TTS audio bytes, generated images) are inherently non-deterministic and are correctly excluded from replay.

### 4.5 Error Handling

**Graceful degradation via stub pattern:**

- **TTS backend unavailable:** `create_tts_adapter("stub")` returns `StubTTSAdapter` which returns `b""` (empty bytes) — narration continues without audio
- **Image backend unavailable:** `create_image_adapter("sdxl")` catches `ImportError` and returns `StubImageAdapter` which returns `ImageResult(status="placeholder")` (line 97-108)
- **STT backend unavailable:** `create_stt_adapter("stub")` returns `StubSTTAdapter` which returns `Transcript(text="[stub transcription]", confidence=1.0)`
- **Backend crash:** Not explicitly handled — adapter callers should wrap in try/except. No circuit breaker or retry mechanism exists at the adapter level.

**Missing:** No timeout enforcement on adapter calls. If TTS synthesis hangs, there is no equivalent of KILL-004 (Spark latency threshold). Real backends (Kokoro TTS, SDXL image) may block indefinitely.

---

## 5. Gap Register

| ID | Seam | Severity | Summary | Affected Files |
|---|---|---|---|---|
| GAP-001 | Box-Lens | HIGH | Unknown Box events pass through as raw dicts; NarrativeBrief assembler handles only 5 of 10 registered event types | `narrative_brief.py:277`, `box_events.py:245` |
| GAP-002 | Lens-Spark | CRITICAL | No canonical PromptPack schema; prompt assembly is a monolithic string without versioning, channels, or deterministic serialization (AD-002 violation) | `context_assembler.py:41`, `guarded_narration_service.py:622` |
| GAP-003 | Box-Lens | HIGH | NarrativeBrief containment matrix incomplete: spell names, distances, DCs, condition durations not surfaced | `narrative_brief.py:244-407` |
| GAP-004 | Spark-Immersion | CRITICAL | No ImmersionPlan schema orchestrating narration output to TTS/image/audio adapters | `aidm/immersion/__init__.py` (no orchestrator exists) |
| GAP-005 | Spark-Immersion | HIGH | No authoritative vs atmospheric log partition specification | Cross-cutting (affects session persistence design) |
| GAP-006 | Box-Lens | MEDIUM | Dual STP systems (`truth_packets.py` and `box_events.py`) not unified; neither wired end-to-end | `truth_packets.py`, `box_events.py` |
| GAP-007 | Lens-Spark | ~~MEDIUM~~ RESOLVED | Two independent prompt assembly paths — **RESOLVED by WO-057 PromptPackBuilder** | `aidm/lens/prompt_pack_builder.py` |
| GAP-008 | Spark-Immersion | MEDIUM | STT transcription to game-loop intent path undefined | `stt_adapter.py:17` |

---

## 6. Priority-Ordered Remediation Plan

### P0 — Must Fix Before Campaign Play

**R-001: Define PromptPack v1 Schema (addresses GAP-002)**

Implement the five-channel PromptPack wire protocol specified in AD-002:
1. Define `PromptPack` frozen dataclass in `aidm/schemas/prompt_pack.py` with:
   - `schema_version: str` (e.g., "1.0")
   - `truth_channel: TruthPayload` (NarrativeBrief + Box event summary)
   - `memory_channel: MemoryPayload` (scoped facts, capped by token budget)
   - `task_channel: TaskPayload` (task type enum + per-task output schema)
   - `style_channel: StylePayload` (persona, verbosity, tone knobs)
   - `output_contract: OutputContract` (required fields, forbidden content, max length)
2. Replace `ContextAssembler.assemble()` return type from `str` to `PromptPack`
3. Add `PromptPack.serialize()` with deterministic byte-level output
4. Add golden tests proving identical inputs produce identical bytes
5. Retire `GuardedNarrationService._build_llm_prompt()` in favor of PromptPack path

**Estimated effort:** 3-5 days
**Dependency:** AD-002, RD-001

**R-002: Define ImmersionPlan Schema (addresses GAP-004)**

Create `aidm/schemas/immersion_plan.py` defining:
1. `ImmersionPlan` dataclass linking narration output to adapter invocations
2. `ImmersionOrchestrator` that receives `NarrationResult` + `SceneAudioState` + event stream and produces:
   - Optional TTS request (narration text + persona selection)
   - Optional image request (scene context mapping)
   - Transparency-filtered event display (TriGemSocket output)
   - Audio state transition
3. Define invocation ordering (TTS and image in parallel, after narration, before next turn)
4. Add timeout enforcement for adapter calls (equivalent to KILL-004)

**Estimated effort:** 2-3 days
**Dependency:** Adapter protocols are already frozen (PUBLIC_STABLE)

### P1 — Should Fix for Stability

**R-003: Wire NarrativeBrief to Typed Event Schemas (addresses GAP-001, GAP-006)**

1. Modify `assemble_narrative_brief()` to use `validate_event_payload()` from `box_events.py` instead of raw dict access
2. Add the 5 missing event type handlers: `turn_start`, `turn_end`, `spell_cast`, `save_rolled`, `condition_removed`
3. Log a warning when `validate_event_payload()` returns None (unknown event type) — currently silent
4. Decision: retire `StructuredTruthPacket` (truth_packets.py) in favor of `box_events.py` schemas, or integrate both. Recommend retiring `truth_packets.py` since resolvers emit dict payloads and `box_events.py` validates at the extraction point.

**Estimated effort:** 2 days
**Dependency:** None (all schemas exist)

**R-004: Expand NarrativeBrief Containment Matrix (addresses GAP-003)**

1. Add `spell_name: Optional[str]` field to `NarrativeBrief`
2. Add `save_dc_category: Optional[str]` field (e.g., "easy", "moderate", "hard" — categorical, not numeric)
3. Add `condition_duration_category: Optional[str]` field (e.g., "brief", "sustained", "permanent")
4. Wire `spell_cast`, `save_rolled`, `condition_applied` events into assembler
5. Update `_build_outcome_summary()` for spell outcomes

**Estimated effort:** 1-2 days
**Dependency:** R-003

**R-005: Define Log Partition Specification (addresses GAP-005)**

1. Define two log streams in session persistence:
   - `authoritative_log`: Box events, EngineResults, state changes — included in replay hash
   - `atmospheric_log`: narration text, TTS timestamps, image references — excluded from replay hash
2. Define which fields bridge both (e.g., narration_token is authoritative, narration_text is atmospheric)
3. Add provenance tags to log entries: `[BOX]`, `[DERIVED]`, `[NARRATIVE]`, `[IMMERSION]`

**Estimated effort:** 1-2 days
**Dependency:** Session persistence design

### P2 — Can Defer to Later Milestone

**R-006: Unify Prompt Assembly Paths (addresses GAP-007) — DONE (WO-057)**

~~Once PromptPack v1 is defined (R-001), both `GuardedNarrationService._build_llm_prompt()` and `ContextAssembler.assemble()` should be replaced by a single `PromptPack.assemble()` path. This is a natural consequence of R-001 and does not require separate work.~~

**Completed:** WO-057 introduced `PromptPackBuilder` in `aidm/lens/prompt_pack_builder.py`. NarrativeBrief → PromptPack → serialize() is now the canonical prompt path. 31 tests added. See `docs/work_orders/WO-057_PROMPTPACK_CONSOLIDATION.md`.

**R-007: Define STT Intent Pipeline (addresses GAP-008)**

1. Define `TranscriptInterpreter` that maps `Transcript.text` to `IntentObject` candidates
2. Add confidence threshold (reject below 0.7)
3. Add disambiguation flow (ask player to confirm ambiguous transcriptions)
4. Wire into game loop input path

**Estimated effort:** 3-5 days
**Dependency:** Voice command gameplay milestone (post-M3)

---

## 7. Relationship to Architectural Decisions

### AD-001: Authority Resolution Protocol (NeedFact / WorldPatch)

**Seam 1 impact:** AD-001 defines a halt-and-resolve protocol for Box when it encounters missing facts. The Box-Lens bridge (`box_lens_bridge.py`) currently provides one-way sync (Grid to Lens), but the `NeedFact` halt mechanism is not integrated into the combat resolution path (as noted in AD-001 Section "Missing: The Integration Gap"). This is an AD-001 implementation gap, not a seam protocol gap — the seam itself is correctly designed to carry the data once the halt mechanism exists.

**Seam 2 impact:** AD-001 restricts Spark from supplying authoritative facts. The `GrammarShield` mechanical assertion patterns (line 77-86 in `grammar_shield.py`) enforce this at the output boundary by rejecting Spark text containing damage quantities, AC values, HP values, DCs, etc. However, there is no input-side enforcement preventing Spark-sourced facts from entering the `LensIndex` at SPARK tier. AD-001 calls for explicit enforcement: "`LensIndex.set_fact()` rejects SPARK-tier facts for mechanics-relevant attributes." This boundary is not yet implemented.

### AD-002: Lens Context Orchestration Architecture

**Seam 2 is the primary implementation surface for AD-002.** The current `ContextAssembler` implements a subset of AD-002's vision (token budgets, priority ordering) but lacks the full five-channel PromptPack architecture. GAP-002 is a direct AD-002 implementation gap.

AD-002 specifies five non-negotiable PromptPack properties:
1. **Deterministic** — same inputs = same bytes: NOT CURRENTLY VERIFIED
2. **Versioned** — schema_version field: NOT PRESENT
3. **Sectioned** — explicit channel markers: NOT PRESENT (monolithic string)
4. **Budgeted** — per-channel token allocation: PARTIALLY PRESENT (total budget only)
5. **Truncation-safe** — Truth/Task/Style never truncated: NOT ENFORCED

Remediation R-001 directly addresses all five properties.

---

## 8. Summary of Findings

| Seam | Health | Contract | Enforcement | Determinism | Error Handling |
|---|---|---|---|---|---|
| Box to Lens | YELLOW | Typed schemas exist but not wired end-to-end | Strong (import AST + frozen types) | Fully deterministic | Silent degradation (should log) |
| Lens to Spark | RED | No PromptPack schema; two assembly paths | Strong on output (GrammarShield + KillSwitches); weak on input | Template: deterministic; LLM: non-deterministic by design | Comprehensive fail-closed cascade |
| Spark to Immersion | RED | Adapters defined but no orchestration schema | Strong on boundary; absent on orchestration | N/A (excluded from replay by design) | Graceful stub degradation; no timeout enforcement |

The system's structural integrity is solid — import boundaries, frozen types, and kill switches prevent the most dangerous failure modes. The gaps are in integration and orchestration: the pipes exist but the plumbing is not connected end-to-end. The two CRITICAL gaps (GAP-002: PromptPack, GAP-004: ImmersionPlan) should be addressed before campaign-length play.

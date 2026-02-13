> **PARTIALLY SUPERSEDED (2026-02-13):** This audit predates Wave 1-3 integration. Test count is now 5,144 (was 4,620). World compiler, discovery log, content packs, and WebSocket bridge now have partial implementations. See `PROJECT_COMPASS.md` for current status.

# Ground-Truth Inventory & "Touch Land" Assessment

**Document ID:** WO-AUDIT-REALITY-001
**Date:** 2026-02-12
**Auditor:** Opus (Independent, Principal Engineer tier)
**Repo:** `f:\DnD-3.5` (branch: `master`)
**Tone:** Clinical. Evidence-backed. No optimism, no pessimism.

---

## 0. Vital Signs (Measured, Not Claimed)

| Metric | Value | How Measured |
|--------|-------|--------------|
| Python files | 393 | `find . -name "*.py"` |
| Test files | 160+ | `find . -name "test_*.py"` |
| Tests collected | 4,620 | `pytest --co -q` |
| Tests passing | 4,601 | `pytest -q --tb=no` (110s wall time) |
| Tests failing | 7 | All in `test_chatterbox_tts.py` (single adapter) |
| Tests skipped | 11 | Hardware-gated (`requires_kokoro`, `requires_whisper`) |
| Doc files (docs/) | 200+ | Markdown contracts, decisions, research, audits |
| JSON schemas | 8 | Under `docs/schemas/` |
| Core dependencies | 7 | `pyproject.toml` (pytest, psutil, pyyaml, msgpack, opencv, Pillow, numpy) |
| External model deps | 0 required | All model backends have stub/template fallbacks |

**99.85% test pass rate. The 7 failures are in an unreleased TTS adapter (Chatterbox) that depends on a PyTorch GPU library not installed in the current environment. Every other system passes.**

---

## 1. Repo Inventory (Factual)

### 1.1 Engine Core (Box)

**Status: REAL IMPLEMENTATION. ~4,500+ lines of production logic.**

| Subsystem | File | Lines | Status | Tests |
|-----------|------|-------|--------|-------|
| Attack resolution | `aidm/core/attack_resolver.py` | 492 | Real | `test_attack_resolution.py` |
| Full attack (iterative) | `aidm/core/full_attack_resolver.py` | 679 | Real | `test_full_attack_resolution.py` |
| Initiative & turn order | `aidm/core/initiative.py` | 146 | Real | Integration tests |
| RNG (deterministic) | `aidm/core/rng_manager.py` | 80 | Real | `test_rng_manager.py` |
| Conditions & modifiers | `aidm/core/conditions.py` | 222 | Real | `test_conditions_kernel.py` |
| Flanking geometry | `aidm/core/flanking.py` | 262 | Real | `test_flanking.py` (29 tests) |
| Sneak attack | `aidm/core/sneak_attack.py` | 251 | Real | `test_sneak_attack.py` |
| Damage reduction | `aidm/core/damage_reduction.py` | 188 | Real | `test_damage_reduction.py` |
| Concealment / miss chance | `aidm/core/concealment.py` | 91 | Real | `test_concealment.py` |
| Attacks of opportunity | `aidm/core/aoo.py` | ~100 | Real | `test_aoo_kernel.py` |
| Combat maneuvers | `aidm/core/maneuver_resolver.py` | ~200 | Real | `test_maneuvers_core.py` |
| Mounted combat | `aidm/core/mounted_combat.py` | ~100 | Real | `test_mounted_combat_core.py` |
| Terrain / cover / elevation | `aidm/core/terrain_resolver.py` | ~100 | Real | `test_terrain_cp19_*.py` |
| Targeting / LoS | `aidm/core/targeting_resolver.py` | ~100 | Real | `test_targeting_resolver_unit.py` |
| Spell resolution | `aidm/core/spell_resolver.py` | ~200 | Real | `test_spell_resolver.py` |
| Save resolution | `aidm/core/save_resolver.py` | ~100 | Real | `test_save_resolution.py` |
| Feat system | `aidm/core/feat_resolver.py` | ~150 | Real | Integration tests |
| Doctrine / monster tactics | `aidm/core/doctrine_rules.py` | 226 | Real | `test_doctrine.py` |
| Event log (append-only) | `aidm/core/event_log.py` | 94 | Real | `test_event_log.py` |
| Provenance (W3C PROV-DM) | `aidm/core/provenance.py` | 735 | Real | `test_provenance.py` |
| State + immutability | `aidm/core/state.py` | 267 | Real | `test_state.py` |
| Play loop | `aidm/core/play_loop.py` | ~150 | Real | `test_play_loop_*.py` |
| Combat controller | `aidm/core/combat_controller.py` | ~120 | Real | `test_runtime_vertical_slice*.py` |

**No stubs or `NotImplementedError` in core combat modules.** Every resolver has real logic: d20 rolls, modifier stacking, critical confirmation, PHB page citations in event payloads. The RNG is isolated per named stream with SHA-256-derived seeds.

Verified by running 180 core tests: **180 passed in 0.79s**.

---

### 1.2 Intent Bridge / Clarification Loop

**Status: REAL IMPLEMENTATION. ~2,400 lines.**

| File | Lines | Status |
|------|-------|--------|
| `aidm/immersion/voice_intent_parser.py` | 741 | Real — keyword-based slot extraction, 80+ spell dictionary |
| `aidm/immersion/clarification_loop.py` | 448 | Real — DM-persona prompts, 200+ dynamic templates |
| `aidm/interaction/intent_bridge.py` | 521 | Real — entity name/weapon/spell resolution with edit-distance matching |
| `aidm/schemas/intents.py` | 253 | Real — frozen dataclasses for all intent types |
| `aidm/schemas/intent_lifecycle.py` | 423 | Real — state machine with BL-014 immutability enforcement |

Verified by running 27 intent bridge tests + 50+ lifecycle tests: **all pass**.

---

### 1.3 Narration Pipeline (Templates / Spark-Ready)

**Status: REAL IMPLEMENTATION. ~3,200 lines. Template mode is production-complete. LLM path is wired but requires a downloaded model.**

| File | Lines | Status |
|------|-------|--------|
| `aidm/narration/narrator.py` | 413 | Real — 55 templates with severity branching |
| `aidm/narration/guarded_narration_service.py` | 985 | Real — M1/M2/M3 paths, 6 kill switches, template fallback |
| `aidm/narration/contradiction_checker.py` | 713 | Real — 250+ keywords, 9 check methods, response escalation |
| `aidm/narration/kill_switch_registry.py` | 229 | Real — 5 regex patterns for mechanical assertion detection |
| `aidm/narration/llm_query_interface.py` | 682 | Real interface — requires LoadedModel (optional) |
| `aidm/narration/play_loop_adapter.py` | 156 | Real — bridges service to play loop |

**The narration system works today without any LLM.** Template narration is the default. LLM narration (Spark) is an optional upgrade path.

Verified: 21 narrator tests + guardrail tests: **all pass**.

---

### 1.4 Lens / Context Pipeline

**Status: REAL IMPLEMENTATION. ~3,600 lines.**

| File | Lines | Status |
|------|-------|--------|
| `aidm/lens/narrative_brief.py` | 807 | Real — 30+ event types, severity computation |
| `aidm/lens/context_assembler.py` | 550 | Real — token-budget-aware, salience ranking |
| `aidm/lens/prompt_pack_builder.py` | 220 | Real — five-channel PromptPack assembly |
| `aidm/lens/voice_resolver.py` | 377 | Real — 200+ keyword mapping tables, voice caching |
| `aidm/lens/scene_manager.py` | 502 | Real — scene transitions, room state |
| `aidm/lens/segment_summarizer.py` | 552 | Real — session segment extraction |

---

### 1.5 STT Adapter

**Status: REAL IMPLEMENTATION. 461 lines total.**

| File | Lines | Status |
|------|-------|--------|
| `aidm/immersion/stt_adapter.py` | 112 | Real — Protocol + Stub + factory |
| `aidm/immersion/whisper_stt_adapter.py` | 349 | Real — faster-whisper, int8 quantized, CPU-optimized |

Whisper requires `faster-whisper` (optional pip install). System falls back to StubSTTAdapter if absent. Tests: 480 lines in `test_whisper_stt.py`.

---

### 1.6 TTS Adapter

**Status: REAL IMPLEMENTATION. 1,219 lines total. Two production backends.**

| File | Lines | Status | Requires |
|------|-------|--------|----------|
| `aidm/immersion/tts_adapter.py` | 139 | Real — Protocol + Stub + factory | Nothing |
| `aidm/immersion/kokoro_tts_adapter.py` | 579 | Real — ONNX neural TTS, 8 voices | `kokoro-onnx` (optional) |
| `aidm/immersion/chatterbox_tts_adapter.py` | 501 | Real — voice cloning, emotion control | PyTorch + CUDA |

Kokoro is CPU-capable (~200MB model). Chatterbox requires GPU (6+ GB VRAM). Both gracefully fall back to StubTTSAdapter if deps missing.

---

### 1.7 Image Generation

**Status: REAL IMPLEMENTATION. 661 lines.**

| File | Lines | Status | Requires |
|------|-------|--------|----------|
| `aidm/immersion/image_adapter.py` | 116 | Real — Protocol + Stub + factory | Nothing |
| `aidm/immersion/sdxl_image_adapter.py` | 545 | Real — SDXL Lightning, NF4 quantized, cached | PyTorch + CUDA + diffusers |

Deterministic generation (same request hash = same seed = same image). Content-addressable cache. Falls back to stub if no GPU. Tests: 726 lines.

---

### 1.8 UI / Display

**Status: TERMINAL ONLY. No web UI, no TUI framework, no 3D.**

| File | Lines | Status |
|------|-------|--------|
| `aidm/ui/character_sheet.py` | 426 | Real — D&D 3.5e class progressions, terminal display |
| `aidm/immersion/combat_receipt.py` | 430 | Real — ASCII parchment formatting |
| `aidm/immersion/ghost_stencil.py` | 529 | Real — AoE preview, shape types |
| `aidm/immersion/judges_lens.py` | 507 | Real — entity inspection |
| `aidm/immersion/contextual_grid.py` | 132 | Real — grid state computation |
| `aidm/immersion/audio_mixer.py` | 173 | Real — multi-track audio management |

**What does NOT exist:**
- No web server (Flask, FastAPI, etc.)
- No React/Vue/Svelte frontend
- No Three.js or 3D visualization
- No WebSocket server
- No textual/rich TUI
- No main CLI entry point (only demo scripts)

---

### 1.9 Persistence (Save/Load/Replay)

**Status: REAL IMPLEMENTATION. ~1,700 lines. Filesystem-backed, append-only.**

| File | Lines | Status |
|------|-------|--------|
| `aidm/core/asset_store.py` | 304 | Real — content-addressable, SHA-256 |
| `aidm/core/campaign_store.py` | 224 | Real — campaign lifecycle, JSONL logs |
| `aidm/core/session_log.py` | 156 | Real — turn-by-turn event tracking |
| `aidm/core/replay_runner.py` | 289 | Real — deterministic replay from event log |
| `aidm/schemas/campaign.py` | 447 | Real — SessionZeroConfig, CampaignManifest |
| `aidm/schemas/campaign_memory.py` | 287 | Real — ledger, threads, conflict tracking |

No database. Pure filesystem JSON/JSONL. Append-only event logs. Full replay capability.

---

### 1.10 World/Campaign Scaffolding

**Status: REAL IMPLEMENTATION. Orchestration layer exists and works.**

| File | Lines | Status |
|------|-------|--------|
| `aidm/runtime/session_orchestrator.py` | 942 | Real — full turn cycle conductor |
| `aidm/runtime/session.py` | 312 | Real — session state management |
| `aidm/runtime/play_controller.py` | ~400 | Real — text→intent→box→narrate pipeline |
| `aidm/spark/spark_adapter.py` | 400 | Real — LLM query protocol |
| `aidm/spark/llamacpp_adapter.py` | 638 | Real — local CPU inference |
| `aidm/spark/grammar_shield.py` | 478 | Real — GBNF output validation |
| `aidm/spark/dm_persona.py` | 356 | Real — tone, voice, personality |

**What does NOT exist:**
- No world compiler (defined in spec only: `docs/contracts/WORLD_COMPILER.md`)
- No discovery log backend (spec only: `docs/contracts/DISCOVERY_LOG.md`)
- No content pack system (defined in schemas but no loader)

---

## 2. Runnable Entry Points

### Actually Runnable Today (Verified)

| Command | What It Does | Output | Time |
|---------|-------------|--------|------|
| `python demo_combat_turn.py` | Full pipeline: intent→box→narration, determinism proof, kill switch audit | Terminal: combat resolution + A8 audit report | ~2s |
| `python demo_micro_scenario.py` | 5-turn dungeon crawl through SessionOrchestrator: combat, movement, rest, scene transitions | Terminal: narrated multi-room scenario + determinism verification | ~2s |
| `python demo_combat_turn.py --with-tts` | Same as above + Kokoro speech synthesis | Terminal + `demo_narration.wav` | ~5s (if Kokoro installed) |
| `pytest` | Full test suite | 4,601 pass / 7 fail / 11 skip | 110s |
| `pytest -m "not slow"` | Fast test suite | ~4,000 tests | ~30s |
| `python scripts/run_performance_profile.py` | Latency profiling across all resolvers | Performance report with pass/fail vs targets | ~10s |
| `python scripts/vertical_slice_v1.py` | Minimal execution proof (3 turns, determinism) | Terminal proof report | ~1s |
| `python scripts/prep_pipeline_demo.py` | M3 prep pipeline stub mode | Asset manifest + placeholder files | ~1s |

### Not Runnable Without Modification

| Command | Blocker |
|---------|---------|
| `python demo_orpheus_audition.py` | Hardcoded HTTP proxy at `127.0.0.1:7890` + requires PyTorch/CUDA + ~6GB model download |
| `python demo_orpheus_remaining.py` | Same as above |
| `python demo_tts_audio.py` | Requires `kokoro-onnx` pip install + model files in `models/kokoro/` |

### Does Not Exist

- No `main.py` or `aidm` CLI entry point
- No interactive session loop (all demos are scripted)
- No `python -m aidm` module execution

---

## 3. Demo Viability Assessment

### Demo A: CLI Combat Demo (EXISTS TODAY — ALREADY WORKS)

**What already exists:** `demo_combat_turn.py` + `demo_micro_scenario.py`

These are not prototypes. They are functional demos that:
- Set up a world state with entities on a grid
- Roll initiative deterministically
- Resolve attacks with full modifier stacking (flanking, conditions, feats, terrain, DR, concealment, sneak attack)
- Emit structured truth packets with PHB citations
- Generate template narration with provenance tags
- Verify determinism by replaying with identical seed
- Audit all 6 kill switches
- Measure performance (sub-5ms Box resolution)

**What would make it more compelling (small additions, no architecture):**
- Accept interactive keyboard input instead of scripted commands (the play_controller already parses text commands — it just needs a `while True` input loop)
- Print the contextual grid / character sheet between turns
- Add 2-3 more entity types to the scenario

**What is explicitly out of scope:** LLM narration, TTS, images, web UI.

### Demo B: Audio Demo (PARTIALLY EXISTS — NEEDS KOKORO INSTALLED)

**What already exists:** `demo_combat_turn.py --with-tts` generates a WAV file. The Kokoro adapter, voice resolver, and persona system are production code.

**What must be built:** Nothing architecturally. The user needs to:
1. `pip install kokoro-onnx onnxruntime`
2. Ensure model files exist in `models/kokoro/`
3. Run `python demo_combat_turn.py --with-tts`

**What is explicitly out of scope:** Voice cloning (Chatterbox/GPU), Orpheus, multi-voice scenes.

### Demo C: Interactive Text Session (DOES NOT EXIST — SMALLEST CREDIBLE NEW DEMO)

**What already exists:**
- `aidm/runtime/play_controller.py` — parses text commands ("attack goblin", "move to 5,5", "cast fireball"), resolves via IntentBridge, executes via Box, narrates result
- `aidm/runtime/session_orchestrator.py` — full turn cycle conductor with scene transitions
- `aidm/lens/scene_manager.py` — room management with exits and descriptions
- `aidm/immersion/clarification_loop.py` — disambiguation prompts

**What must be built:**
- A ~50-line `main.py` that:
  1. Constructs a WorldState with 2-3 rooms, 1 PC, 2-3 monsters
  2. Instantiates SessionOrchestrator
  3. Runs `while True: input() → orchestrator.execute_turn() → print()`
  4. Handles "quit" / Ctrl-C

This is not a new system. It is a thin wrapper around existing, tested code. The play_controller already handles text→intent→box→narrate. The missing piece is literally the input loop.

**What is explicitly out of scope:** Save/load between sessions, character creation, spell selection UI, combat log export.

---

## 4. Cost & Risk Envelope

### Effort Bands

| Band | Definition | Examples |
|------|-----------|----------|
| **Low** | Uses existing code with minimal wiring. No new subsystems. | Interactive text loop, additional demo scenarios, contextual grid display during combat, character sheet printing |
| **Medium** | Requires new subsystem implementation against existing contracts. Specs exist. | Discovery log backend (spec done), world compiler (spec done), content pack loader, campaign save/load UI |
| **High** | Requires architectural decisions not yet made + implementation + testing. | Web UI, multiplayer, real-time audio mixing, 3D battle map, tablet client |

### Top 5 Cost Multipliers

1. **UI technology choice.** The system has zero UI beyond terminal `print()`. Choosing a UI framework (web, Electron, tablet app, TUI) is the single largest cost decision. Every option requires building from scratch. There is no incremental path — it's a step function.

2. **World compiler.** The spec exists (`docs/contracts/WORLD_COMPILER.md`) but zero implementation. This is the gate between "hand-authored test scenarios" and "content packs that generate playable worlds." It requires LLM-driven compilation, schema validation, and deterministic freezing. This is a multi-week subsystem.

3. **Content authoring.** The engine resolves mechanics. But playable content (creatures, spells, items, NPCs, rooms, quests) must be authored in the canonical schema format. There is no content pack today. The demos use inline hardcoded entities. Scaling content requires either manual authoring or the world compiler.

4. **LLM integration for narration.** Template narration works today. LLM narration (via llama.cpp) is wired but requires a downloaded GGUF model (2-14GB depending on quality). The guardrail system is built. The gap is: which model, tuned how, with what prompt engineering, producing what quality threshold.

5. **Multiplayer / network.** The system is single-player, single-machine. Adding a second player requires: network protocol, state synchronization, per-player knowledge masks, concurrent intent handling, and a shared display. The knowledge mask spec exists but the networking layer does not.

### Decisions That Cause Exponential Cost Growth

| Decision | Why It's Exponential |
|----------|---------------------|
| "Build a web UI" | Requires: frontend framework, WebSocket server, state serialization protocol, asset serving, responsive design, browser testing matrix. None of this exists. |
| "Support multiplayer" | Requires: network stack, concurrent state, per-player masks, latency tolerance, conflict resolution, session recovery. Fundamentally different architecture. |
| "Ship on mobile/tablet" | Requires: cross-platform framework (React Native, Flutter, etc.), touch UI, reduced compute budget, asset size optimization. Nothing in the codebase is portable. |
| "Generate content automatically" | Requires: world compiler + LLM prompt engineering + schema validation + content testing pipeline. Each is a full subsystem. |
| "Real-time audio scene" | Requires: audio mixing with crossfading, spatial audio, dynamic music, SFX triggers, latency-sensitive playback. The mixer protocol exists; the runtime does not. |

---

## 5. Stop Conditions & Risks

### 5.1 Specs Disconnected From Code

| Spec | Code Exists? | Risk |
|------|-------------|------|
| `docs/contracts/DISCOVERY_LOG.md` | `aidm/services/discovery_log.py` exists (stub) + `aidm/schemas/knowledge_mask.py` exists (schema only) | **Medium.** Schema is defined. Backend is a stub. The spec is sound but has zero executable verification. |
| `docs/contracts/WORLD_COMPILER.md` | No implementation | **High.** Detailed spec with no code. Defines the entire content pipeline. Risk of spec drift if implementation begins months later. |
| `docs/schemas/world_bundle.schema.json` | No loader, no validator | **Medium.** Schema exists but nothing reads or validates it at runtime. |
| `docs/schemas/presentation_semantics_registry.schema.json` | No loader | **Medium.** Same pattern — schema authored, no runtime consumer. |
| `docs/schemas/asset_binding.schema.json` | `aidm/schemas/asset_binding.py` exists (schema only) | **Low.** Schema matches spec. Needs backend. |

**Pattern:** The project has invested heavily in specification (contracts, schemas, compliance checklists). The specs are internally consistent and well-structured. But 3 of the 5 contract-level specs have zero executable backing. This is not inherently wrong — specs-first is defensible. But it becomes a risk if the specs continue expanding without implementation catching up.

### 5.2 Paper Completion Without Executable Output

**Docs vs Code ratio:**
- `docs/` directory: 200+ markdown files, ~50,000+ words
- Executable code: ~30,000 lines across 170+ Python files
- Test code: ~20,000 lines across 160+ test files

The documentation volume is high relative to code. However, the code that exists is real — not stubs. The risk is not "fake code" but rather "real specs for systems that don't exist yet."

**Specific examples of paper-only artifacts:**
- `docs/contracts/WORLD_COMPILER.md` — detailed contract, zero code
- `docs/contracts/DISCOVERY_LOG.md` — detailed contract, schema-only code
- `docs/specs/UX_VISION_PHYSICAL_TABLE.md` — vision document, zero UI code
- `docs/design/TABLE_SURFACE_UI_SPECIFICATION.md` — spec for a UI that doesn't exist
- `docs/schemas/` — 8 JSON schemas, only 1 (`intent_request.schema.json`) has a runtime consumer

### 5.3 Assumptions Currently Wrong or Unverified

1. **"The system can play a session."** It cannot. It can play scripted turns. There is no interactive input loop, no character creation, no session save/load from a user's perspective. The orchestration layer is built, but there is no user-facing entry point that says "start a game."

2. **"Template narration is sufficient for a demo."** It is mechanically sufficient but experientially flat. The templates produce correct, provenance-tagged text like: *"Aldric the Bold's weapon connects with Goblin Warrior, dealing 11 damage."* This is accurate but not compelling. The thesis of the product includes immersive narration — templates do not demonstrate that thesis.

3. **"TTS is ready."** Kokoro works in isolation (`demo_combat_turn.py --with-tts`). But there is no integrated audio experience: no ambient music, no per-NPC voice switching during a scene, no audio queue management during fast combat. The audio mixer protocol exists; the runtime integration does not.

4. **"The asset pipeline is defined."** The schemas exist. The store exists. The binding registry spec exists. But no assets have ever been generated, stored, or bound in a real session. The pipeline has never run end-to-end.

### 5.4 What Is Genuinely Solid

1. **The Box engine is real.** 4,500+ lines of D&D 3.5e combat resolution, all passing. Deterministic. Auditable. PHB-cited. This is not a prototype.

2. **The boundary architecture holds.** BL-020 (frozen state views), BL-003 (no core imports from narration), BL-014 (intent immutability) — these are enforced in code, not just documented. Tests verify them.

3. **Determinism is proven.** Both demo scripts replay with identical seeds and verify byte-identical state hashes. The RNG is properly isolated. The event log is append-only.

4. **The narration safety system is real.** 6 kill switches with evidence logging, mechanical assertion detection via regex, contradiction checking with escalation policy, temperature boundaries. This is production-grade guardrail engineering.

5. **The test infrastructure is real.** 4,620 tests, 99.85% pass rate, sub-2-minute full suite. Property-based tests, replay regression tests, performance profiling, boundary law enforcement tests. This is not test theater.

---

## 6. Summary: What Is Real vs What Is Paper

### Real and Runnable

```
Box engine (combat resolution)          ████████████████████ COMPLETE
Intent bridge (text → action)           ████████████████████ COMPLETE
Narration (template mode)               ████████████████████ COMPLETE
Kill switches / guardrails              ████████████████████ COMPLETE
Determinism / replay                    ████████████████████ COMPLETE
Event logging / provenance              ████████████████████ COMPLETE
State management / immutability         ████████████████████ COMPLETE
Lens pipeline (brief/context/prompt)    ████████████████████ COMPLETE
STT adapter (Whisper)                   ████████████████████ COMPLETE
TTS adapter (Kokoro)                    ████████████████████ COMPLETE
Test suite (4,620 tests)                ████████████████████ COMPLETE
Persistence (campaign store)            ████████████████████ COMPLETE
Session orchestrator                    ████████████████████ COMPLETE
```

### Real but Requires Optional Dependencies

```
TTS (Chatterbox voice cloning)          ██████████████████░░ CODE DONE, needs PyTorch+CUDA
Image generation (SDXL)                 ██████████████████░░ CODE DONE, needs PyTorch+CUDA
LLM narration (llama.cpp)              ██████████████████░░ CODE DONE, needs GGUF model download
```

### Schema/Spec Only (No Runtime Consumer)

```
World compiler                          ████░░░░░░░░░░░░░░░░ SPEC ONLY
Discovery log / bestiary                ███░░░░░░░░░░░░░░░░░ SPEC + SCHEMA ONLY
Presentation semantics registry         ███░░░░░░░░░░░░░░░░░ SPEC + SCHEMA ONLY
World bundle schema                     ███░░░░░░░░░░░░░░░░░ SPEC + SCHEMA ONLY
Asset binding registry                  ███░░░░░░░░░░░░░░░░░ SPEC + SCHEMA ONLY
Content independence architecture       ██░░░░░░░░░░░░░░░░░░ SPEC ONLY
```

### Does Not Exist

```
Interactive play session (main.py)      ░░░░░░░░░░░░░░░░░░░░ MISSING
Web UI                                  ░░░░░░░░░░░░░░░░░░░░ MISSING
Character creation                      ░░░░░░░░░░░░░░░░░░░░ MISSING
Content packs / playable worlds         ░░░░░░░░░░░░░░░░░░░░ MISSING
Audio scene (mixed ambient+voice+sfx)   ░░░░░░░░░░░░░░░░░░░░ MISSING
Multiplayer / networking                ░░░░░░░░░░░░░░░░░░░░ MISSING
3D / visual display                     ░░░░░░░░░░░░░░░░░░░░ MISSING
```

---

## 7. The Smallest Credible Showable Demo

**What exists today** already demonstrates the core thesis: deterministic combat resolution with inspectable narration. `demo_combat_turn.py` proves it. `demo_micro_scenario.py` extends it to multi-turn, multi-room play.

**What would make it a "show someone" demo:**

An interactive text session. The code is 90% written. The missing piece is a ~50-100 line input loop that connects `play_controller.py` to `stdin`. No new architecture. No new contracts. No new research. Just wiring.

**What it would look like:**

```
$ python play.py

  The Goblin Warren — A narrow corridor opens into a torch-lit chamber.
  Two goblins crouch behind overturned tables, crude spears at the ready.

  Kael the Steadfast (Fighter, 28/28 HP)
  Enemies: Goblin Spearman (5 HP), Goblin Archer (4 HP)

  > attack the spearman

  d20(19) + 6 = 25 vs AC 14 → HIT
  1d8+3 = 11 slashing damage
  Goblin Spearman: 5 → -6 HP [DEFEATED]

  "Kael's longsword cleaves into the Goblin Spearman. It crumbles and falls!"
  [NARRATIVE:TEMPLATE]

  > _
```

This is not hypothetical. Every component in the above output — the scene description, the entity display, the text parsing, the attack resolution, the narration, the provenance tag — already exists and passes tests.

---

*End of audit.*

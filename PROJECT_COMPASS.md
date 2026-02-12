# Project Compass — Agent Rehydration Hub

**Purpose:** Single entry point for any fresh agent context window. Read this first. Everything else is a deep dive.
**Last grounded:** 2026-02-13 (Post Wave 1-3 integration, 5,144 tests collected)

---

## 1. What This Is

**The Table** is a local-first, deterministic tabletop RPG engine. It uses D&D 3.5e as scaffolding to extract the *physics* of tabletop play, then skins them through content-independent world compilation.

**Core thesis:** Creative in voice, strict in truth, accountable in every outcome. The system executes rules deterministically (the referee) and generates meaning creatively (the storyteller) — and never confuses the two. No opaque DM. Every outcome traces to Rules As Written or declared House Policy. Nothing else.

**What it refuses to be:** A chatbot that roleplays authority. A black box. A system that trades truth for vibes. A referee that silently invents rules. A UI that looks like software instead of a table.

> Full vision: `MANIFESTO.md`

---

## 2. Architecture (Box / Lens / Spark / Immersion)

```
  Player Input (voice/text)
        │
        ▼
  ┌─────────────┐
  │ Intent Bridge│  Text → structured intent (keyword, no LLM)
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │   BOX        │  Deterministic mechanics. d20 + modifiers. PHB citations.
  │  (Referee)   │  Same state + same input + same seed = same output. ALWAYS.
  └──────┬──────┘
         │ Events (append-only, typed)
         ▼
  ┌─────────────┐
  │   LENS       │  NarrativeBrief: sanitizes Box events into Spark-safe context.
  │  (Boundary)  │  One-way valve. No entity IDs, raw HP, or grid coords leak through.
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │   SPARK      │  Narration generation. Template mode (default) or LLM (optional).
  │ (Storyteller)│  Zero mechanical authority. If it fails, truth survives.
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  IMMERSION   │  TTS, STT, images, audio mixer. All atmospheric, non-authoritative.
  │  (Senses)    │  Adapters with stub fallbacks. No adapter = text-only graceful degrade.
  └─────────────┘
```

**Critical boundary law:** Spark never queries Box. Lens never mutates state. Information flows DOWN only: Box → Lens → Spark → Immersion.

> Full doctrine: `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md`

---

## 3. Binding Architectural Decisions

These are **ratified and non-negotiable**. All code must comply.

| ID | Name | One-Line Rule | Doc |
|----|------|---------------|-----|
| AD-001 | Authority Resolution | Spark MUST NEVER supply mechanical truth. Box halts on missing facts. | `docs/decisions/AD-001_*.md` |
| AD-002 | Lens Context Orchestration | Five-channel PromptPack wire protocol. Lens is the OS for context. | `docs/decisions/AD-002_*.md` |
| AD-003 | Self-Sufficiency | System self-sufficiency via Policy Default Library, not LLM invention. | `docs/decisions/AD-003_*.md` |
| AD-004 | Mechanical Evidence Gate | No rule enters Box without local corpus evidence (PHB page citation). | `docs/decisions/AD-004_*.md` |
| AD-005 | Physical Affordance | Four-layer inventory (weight/container/gear/complication). HOUSE_POLICY provenance. | `docs/decisions/AD-005_*.md` |
| AD-006 | House Policy Governance | No-Opaque-DM. Two authorities only (RAW + House Policy). Fail-closed. | `docs/decisions/AD-006_*.md` |
| AD-007 | Presentation Semantics | Three-layer description: Behavior (Box) / Presentation (frozen) / Narration (ephemeral). | `docs/decisions/AD-007_*.md` |

---

## 4. What Is Real (Grounded, Tested, Runnable)

**5,144 tests collected. 5,121 passing (99.55%). 7 fail (Chatterbox TTS, external dep). 16 skipped (hardware-gated).**

### Engine Core (~4,500 lines, 180+ core tests)

| Subsystem | File | Status |
|-----------|------|--------|
| Attack resolution (single + full/iterative) | `aidm/core/attack_resolver.py`, `full_attack_resolver.py` | Complete |
| Flanking geometry (135-degree check) | `aidm/core/flanking.py` | Complete (29 tests) |
| Sneak attack (precision damage) | `aidm/core/sneak_attack.py` | Complete (52 tests) |
| Damage reduction / concealment | `aidm/core/damage_reduction.py`, `concealment.py` | Complete |
| Conditions (8 types, modifier stacking) | `aidm/core/conditions.py` | Complete |
| Combat maneuvers (6 types) | `aidm/core/maneuver_resolver.py` | Complete |
| Spellcasting (53 spells, AoE rasterizer) | `aidm/core/spell_resolver.py` | Complete |
| Initiative, AoO, save resolution | `aidm/core/initiative.py`, `aoo.py`, `save_resolver.py` | Complete |
| Targeting / LoS / terrain / mounted combat | `aidm/core/targeting_resolver.py`, `terrain_resolver.py`, `mounted_combat.py` | Complete |
| Deterministic RNG (SHA-256 stream isolation) | `aidm/core/rng_manager.py` | Complete |
| Event log (append-only, JSONL) | `aidm/core/event_log.py` | Complete |
| Provenance (W3C PROV-DM, 735 lines) | `aidm/core/provenance.py` | Complete |
| State + immutability + hashing | `aidm/core/state.py` | Complete |
| Deterministic replay | `aidm/core/replay_runner.py` | Complete |

### Intent Bridge (~2,400 lines)

| Subsystem | File | Status |
|-----------|------|--------|
| Voice intent parser (keyword, 80+ spells) | `aidm/immersion/voice_intent_parser.py` | Complete |
| Clarification loop (200+ templates) | `aidm/immersion/clarification_loop.py` | Complete |
| Intent bridge (name→ID, edit-distance) | `aidm/interaction/intent_bridge.py` | Complete |
| Intent schemas (frozen dataclasses) | `aidm/schemas/intents.py`, `intent_lifecycle.py` | Complete |

### Narration Pipeline (~3,200 lines)

| Subsystem | File | Status |
|-----------|------|--------|
| Narrator (55 templates, severity branching) | `aidm/narration/narrator.py` | Complete |
| Guarded narration (6 kill switches) | `aidm/narration/guarded_narration_service.py` | Complete |
| Contradiction checker (250+ keywords) | `aidm/narration/contradiction_checker.py` | Complete |
| Kill switch registry (5 regex patterns) | `aidm/narration/kill_switch_registry.py` | Complete |

### Lens Pipeline (~3,600 lines)

| Subsystem | File | Status |
|-----------|------|--------|
| Narrative brief (30+ event types) | `aidm/lens/narrative_brief.py` | Complete |
| Context assembler (token-budget-aware) | `aidm/lens/context_assembler.py` | Complete |
| PromptPack builder (5-channel assembly) | `aidm/lens/prompt_pack_builder.py` | Complete |
| Scene manager (rooms, exits, transitions) | `aidm/lens/scene_manager.py` | Complete |
| Segment summarizer (drift detection) | `aidm/lens/segment_summarizer.py` | Complete |

### Runtime / Orchestration

| Subsystem | File | Status |
|-----------|------|--------|
| Session orchestrator (full turn cycle) | `aidm/runtime/session_orchestrator.py` (942 lines) | Complete |
| Play controller (text→intent→box→narrate) | `aidm/runtime/play_controller.py` | Complete |
| Session state management | `aidm/runtime/session.py` | Complete |

### Immersion Adapters (all have stub fallbacks)

| Subsystem | File | Requires |
|-----------|------|----------|
| STT (Whisper, int8, CPU) | `aidm/immersion/whisper_stt_adapter.py` | `faster-whisper` (optional) |
| TTS (Kokoro, ONNX, CPU) | `aidm/immersion/kokoro_tts_adapter.py` | `kokoro-onnx` (optional) |
| TTS (Chatterbox, voice cloning) | `aidm/immersion/chatterbox_tts_adapter.py` | PyTorch + CUDA |
| Image (SDXL Lightning, NF4) | `aidm/immersion/sdxl_image_adapter.py` | PyTorch + CUDA |

### Persistence (filesystem, no database)

| Subsystem | File | Status |
|-----------|------|--------|
| Asset store (content-addressable, SHA-256) | `aidm/core/asset_store.py` | Complete |
| Campaign store (lifecycle, JSONL logs) | `aidm/core/campaign_store.py` | Complete |
| Replay runner (deterministic from event log) | `aidm/core/replay_runner.py` | Complete |

### Runnable Demos (verified 2026-02-12)

| Command | What It Does |
|---------|-------------|
| `python demo_combat_turn.py` | Full pipeline: intent→box→narration + determinism proof + kill switch audit (~2s) |
| `python demo_micro_scenario.py` | 5-turn dungeon crawl: combat, movement, rest, scene transitions (~2s) |
| `pytest` | Full suite: 5,121 pass / 7 fail / 16 skip (~100s) |
| `pytest -m "not slow"` | Fast suite: ~4,000 tests (~30s) |

> Full inventory with line counts: `docs/audits/WO-AUDIT-REALITY-001_GROUND_TRUTH.md`

---

## 5. What Is Paper or Missing

### Spec/Schema Only (no runtime consumer)

| System | Spec Exists | Code Status |
|--------|------------|-------------|
| World compiler | `docs/contracts/WORLD_COMPILER.md` | Scaffold + 3 stages implemented (Lexicon, Semantics, NPC). Stub mode only. |
| Discovery log / bestiary | `docs/contracts/DISCOVERY_LOG.md` + 3 JSON schemas | Lens-tier backend implemented (`aidm/lens/discovery_log.py`). Services-tier exists. |
| Presentation semantics registry | `docs/schemas/presentation_semantics_registry.schema.json` | Python implementation complete (`aidm/schemas/presentation_semantics.py` + `aidm/lens/presentation_registry.py`) |
| World bundle | `docs/schemas/world_bundle.schema.json` | Schema only, no loader |
| Asset binding registry | `docs/schemas/asset_binding.schema.json` | Schema only, no runtime |
| Rulebook registry | `docs/schemas/rule_registry.schema.json` | Python implementation complete (`aidm/schemas/rulebook.py` + `aidm/lens/rulebook_registry.py`) |
| Vocabulary registry | `docs/schemas/vocabulary_registry.schema.json` | Python implementation complete (`aidm/schemas/vocabulary.py` + `aidm/lens/vocabulary_registry.py`) |

### Does Not Exist

| System | Notes |
|--------|-------|
| Interactive play session (`main.py`) | ~50-100 lines of wiring needed. All components exist. |
| Web UI / Three.js table | `aidm/server/app.py` exists (Starlette stub). No frontend. |
| Character creation | No flow exists. |
| Multiplayer / networking | Single-player, single-machine only. |
| Audio scene (ambient + voice + SFX mixed) | Mixer protocol exists, runtime does not. |
| MVP world ("Ashenmoor") | World compiler stages 1/3/4 in stub mode. No real world compiled yet. |

> Full gap analysis: `docs/audits/WO-AUDIT-REALITY-001_GROUND_TRUTH.md` sections 5-6

---

## 6. Roadmap: Where We Are

**Current phase: 0 (Foundation Alignment).** Per `docs/planning/REVISED_PROGRAM_SEQUENCING_2026_02_12.md`:

```
Phase 0: Foundation Alignment        ◄── WE ARE HERE (mostly complete)
  0.1 Strip source material IP refs         [ ] (content packs are IP-clean)
  0.3 AD-007 Presentation Semantics Schema  [✓] (WO-AD007-IMPL-001)
  0.4 Rulebook Object Model                 [✓] (WO-RULEBOOK-MODEL-001)

Phase 1: World Compile                ◄── PARTIALLY STARTED
  1.1 World Model Schema                    [~] (schemas + 3 compile stages in stub mode)
  1.2 Minimum World Compiler                [~] (scaffold + stages 0/1/3/4/8, stage 2 missing)
  1.3 MVP World ("Ashenmoor")               [ ]

Phase 2: Play Loop Integration
  2.1 Wire Spark narration into game loop   [ ]
  2.2 Voice pipeline integration            [ ]
  2.3 Discovery Log backend                 [✓] (WO-DISCOVERY-BACKEND-001)
  2.4 Session Zero flow                     [ ]

Phase 3: Table UI Prototype
  3.1-3.8 Three.js table surface, notebook, dice, crystal ball, battle map, WebSocket bridge

Phase 4: MVP Integration
  4.1-4.3 End-to-end Session Zero → One Combat

Parallel: Mechanical coverage extraction   [✓] (605 spells, 273 creatures, 109 feats extracted)
```

> Full roadmap: `docs/planning/REVISED_PROGRAM_SEQUENCING_2026_02_12.md`
> MVP acceptance criteria: `docs/specs/MVP_SESSION_ZERO_TO_ONE_COMBAT.md`

---

## 7. Conventions (Compressed)

### Must Do

1. **Entity fields via `EF.*` constants** — never bare strings. `from aidm.schemas.entity_fields import EF`
2. **Resolvers return events, never mutate state** — state mutation only through the replay runner's single reducer
3. **All `json.dumps` use `sort_keys=True`** — deterministic serialization is load-bearing
4. **No `set()` in WorldState** — use `list()`. Sets crash `json.dumps` in `state_hash()`
5. **Deep copy state** — `deepcopy()` always. Shallow copy is forbidden.
6. **Data-only schemas first** — define contracts and validation before implementing algorithms
7. **Fail-closed** — unknown types rejected, missing state causes errors, no silent fallbacks

### Must Not Do

1. **No 5e terminology** — no advantage/disadvantage, no short/long rest, no "electric" (it's "electricity"), no at-will cantrips
2. **No LLM in deterministic runtime** — LLMs are untrusted generators in prep/narration only
3. **No imports from narration/immersion into core** — boundary law BL-003
4. **No state mutation inside resolvers** — boundary law BL-020 (FrozenWorldStateView)
5. **No "fixing" known tech debt** — check `KNOWN_TECH_DEBT.md` first
6. **No modifying `Vault/`** — 23,750 source files, not AIDM code

### Two Attack Intent Types (Common Pitfall)

- `DeclaredAttackIntent` (in `aidm/schemas/intents.py`) = player-facing, voice/interaction layer
- `AttackIntent` (in `aidm/schemas/attack.py`) = engine-facing, combat resolution layer
- Never import `AttackIntent` from `aidm/schemas/intents` — it doesn't exist there

> Full guidelines: `AGENT_DEVELOPMENT_GUIDELINES.md`
> Full onboarding: `AGENT_ONBOARDING_CHECKLIST.md`

---

## 8. Directory Map

```
aidm/
  core/           28+ modules — resolvers, engine, infrastructure, pipeline
    compile_stages/  Lexicon (stage 1), Semantics (stage 3), NPC Archetypes (stage 4)
    world_compiler.py  Pipeline harness + Stage 0/8
  schemas/        30+ modules — data contracts for all subsystems
  rules/          legality_checker.py
  interaction/    intent_bridge.py
  lens/           narrative_brief, context_assembler, scene_manager, prompt_pack_builder,
                  content_pack_loader, discovery_log, presentation_registry, rulebook_registry,
                  vocabulary_registry, voice_resolver
  narration/      narrator (55 templates), guarded_narration_service, contradiction_checker
  spark/          spark_adapter, llamacpp_adapter, grammar_shield, dm_persona
  runtime/        session_orchestrator, play_controller, session, bootstrap
  immersion/      stt/tts/image adapters, audio_mixer, clarification_loop, voice_intent_parser
  server/         app.py (Starlette ASGI + WebSocket route)
  services/       discovery_log (services-tier)
  data/
    content_pack/ spells.json (605), creatures.json (273), feats.json (109)
    policy_defaults, scene_generator
  evaluation/     evaluation harness (Scenarios 1+4)
  ui/             character_sheet (terminal only)

docs/
  decisions/      AD-001 through AD-007 (binding architectural decisions)
  contracts/      INTENT_BRIDGE, WORLD_COMPILER, DISCOVERY_LOG (system interface specs)
  schemas/        8 JSON schemas (intent_request, world_bundle, discovery, asset_binding, etc.)
  specs/          UX_VISION, MVP, RQ-* research specs
  planning/       PM_SESSION_STATUS, REVISED_PROGRAM_SEQUENCING, RQ-TABLE-FOUNDATIONS-001
  audits/         Ground truth, 5e contamination, mechanical coverage, seam analysis
  research/       Phase 1 research syntheses, RAW silence catalog, community surveys, OSS shortlist
  evidence/       Per-subsystem PHB page evidence maps (AD-004)

tools/            extract_spells.py, extract_monsters.py, extract_feats.py, verify_spell_bridge.py
tests/            160+ test files, 5,144 tests
sources/          647 D&D 3.5e source metadata, 966 pages extracted text (PHB/DMG/MM)
pm_inbox/         Deliverables awaiting PM review (agents write here)
  reviewed/       PM-approved deliverables (agents do NOT write here)
```

---

## 9. Deep Dive Index

| Topic | Read |
|-------|------|
| Product identity & vision | `MANIFESTO.md` |
| Full system inventory | `docs/audits/WO-AUDIT-REALITY-001_GROUND_TRUTH.md` |
| What's built (operational detail) | `PROJECT_STATE_DIGEST.md` |
| Coding standards & pitfalls | `AGENT_DEVELOPMENT_GUIDELINES.md` |
| Onboarding step-by-step | `AGENT_ONBOARDING_CHECKLIST.md` |
| Document precedence | `docs/CURRENT_CANON.md` |
| Known tech debt | `KNOWN_TECH_DEBT.md` |
| PM session history | `docs/planning/PM_SESSION_STATUS_2026_02_13.md` |
| Roadmap (5-phase) | `docs/planning/REVISED_PROGRAM_SEQUENCING_2026_02_12.md` |
| MVP definition | `docs/specs/MVP_SESSION_ZERO_TO_ONE_COMBAT.md` |
| UX north star (physical table) | `docs/specs/UX_VISION_PHYSICAL_TABLE.md` |
| Content independence arch | `docs/specs/RQ-PRODUCT-001_CONTENT_INDEPENDENCE_ARCHITECTURE.md` |
| Intent Bridge contract | `docs/contracts/INTENT_BRIDGE.md` |
| World Compiler contract | `docs/contracts/WORLD_COMPILER.md` |
| Discovery Log contract | `docs/contracts/DISCOVERY_LOG.md` |
| Mechanical coverage gaps | `docs/audits/MECHANICAL_COVERAGE_AUDIT.md` |
| Seam protocol health | `docs/audits/SEAM_PROTOCOL_ANALYSIS.md` |
| Research agenda | `docs/planning/RQ-TABLE-FOUNDATIONS-001.md` |
| Governance roles (PO/PM) | `PROJECT_STATE_DIGEST.md` → Project Governance |
| Agent communication protocol | `AGENT_COMMUNICATION_PROTOCOL.md` |

---

*This document is the rehydration entry point. It summarizes; it does not replace. For any topic, follow the deep dive pointer. When this document contradicts a source document, the source wins — and this file should be updated.*

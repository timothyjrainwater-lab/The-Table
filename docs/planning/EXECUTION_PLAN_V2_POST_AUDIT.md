# Execution Plan v2 — From Combat Calculator to AI Dungeon Master

**Status:** DRAFT — Awaiting PO approval
**Author:** Opus (PM)
**Date:** 2026-02-11
**Prerequisite:** WO-026 Full System Audit must PASS before Phase 1 dispatch
**Predecessor:** EXECUTION_PLAN_DRAFT_2026_02_11.md (7-step plan, 25/26 WOs complete)

---

## Context

The 7-step execution plan built the engine room: deterministic Box, Lens membrane, immersion adapters, 3170 tests. What's missing is the brain (real LLM integration) and game content (feats, skills, leveling). Both are required for a playable D&D 3.5e session.

### What the Codebase Exploration Revealed

The infrastructure is more complete than the high-level discussion assumed:

1. **LlamaCppAdapter exists** — real GGUF model loading, GPU acceleration, CPU offloading. But it uses a legacy `generate_text()` interface, not the canonical `SparkRequest`/`SparkResponse` contract.

2. **LLMQueryInterface exists** (683 lines) — full prompt templates for narration (500 tokens), queries (800 tokens), structured output (600 tokens). Three methods: `generate_narration()`, `query_memory()`, `generate_structured_output()`. But it raises `LLMQueryError` with no template fallback if no model is loaded.

3. **GuardedNarrationService exists** (543 lines) — FREEZE-001 (memory hash verification), BL-003 (no core imports), LLM-002 (temperature boundaries). One kill switch (KILL-001, memory hash mismatch). But only 4 fallback templates, not connected to the full 55 in narrator.py.

4. **Play loop emits narration tokens** — every combat action returns a narration_token string (attack_hit, spell_damage_dealt, etc.). But no call to actual narration generation exists. The token → text pipeline is unwired.

5. **Canonical SparkRequest/SparkResponse** — fully specified with stop_sequences, temperature bounds, json_mode, streaming. But LlamaCppAdapter bridges to legacy interface; canonical contract not integrated.

6. **Kill switches** — only KILL-001 implemented (memory hash mismatch). KILL-002 through KILL-006 are documented but not built.

7. **DeclaredAttackIntent → AttackIntent bridge** — voice layer produces DeclaredAttackIntent (string names), combat resolution needs AttackIntent (integer IDs, Weapon dataclass). Bridge not implemented.

8. **Lens subsystems** — Campaign Memory Index, Player Model, Alignment Tracker, Environmental Data Index, Context Assembler all specified in architecture doc but not implemented. These are the stateful focus system that mediates between Box and Spark.

### Research Block Decision

RQ-SPARK-001 and RQ-NARR-001 remain NOT DELIVERED. This plan proceeds without them by building the minimum viable integration from existing infrastructure:

- **Grammar Shield** from RQ-PERF-001 (partial) + LLMQueryInterface prompt templates
- **Basic narration** via LLMQueryInterface.generate_narration() with 55-template fallback
- **No Scene Fact Pack** — use existing Lens schemas + NarrativeBrief pattern instead

If RQ-SPARK-001/RQ-NARR-001 deliver during execution, findings integrate into existing WOs without replanning.

---

## Design Constraints (Inherited — Non-Negotiable)

All work orders in this plan must respect:

| Constraint | Source | Enforcement |
|-----------|--------|-------------|
| No SPARK→State writes | Axiom 5, BL-020 | AST scan in test_boundary_law.py |
| BOX is sole mechanical authority | Axiom 2 | All mechanical claims must cite RAW |
| LENS adapts stance, not authority | Axiom 3 | No new mechanical logic in Lens |
| Provenance labeling on all output | Axiom 4 | [BOX]/[DERIVED]/[NARRATIVE]/[UNCERTAIN] tags |
| All Spark↔Box communication routes through Lens | Architecture spec | CHECK-007 separation gate |
| UUID/timestamp injection only (BL-017/018) | Agent guidelines | test_boundary_law.py |
| RNG stream isolation (4 streams) | Agent guidelines | Determinism verification |
| Entity field access via EF.* constants | Agent guidelines | No bare string literals |
| D&D 3.5e rules only (no 5e contamination) | Agent guidelines | Review gate |
| Tests under 2 seconds, zero regressions | Agent guidelines | CI gate |
| FrozenWorldStateView for non-engine code | BL-020 | Immersion authority contract |

---

## Phase 1: Wire the Brain (Critical Path)

**Goal:** Real LLM generates narration through the existing pipeline. Template fallback works when LLM fails. Kill switches halt on boundary violations.

**Dependency:** WO-026 PASS verdict.

### WO-027: Canonical SparkAdapter Integration
**Step:** 1.1 | **Files:** `aidm/spark/llamacpp_adapter.py`, `aidm/spark/spark_adapter.py`

Wire LlamaCppAdapter to use canonical `SparkRequest`/`SparkResponse` contract instead of legacy `generate_text()`:
- `generate(request: SparkRequest) -> SparkResponse` with full field mapping
- Stop sequence enforcement during generation
- Token counting (actual, not returning 0)
- Finish reason tracking (COMPLETED/LENGTH_LIMIT/STOP_SEQUENCE/ERROR)
- BL-013 temperature bounds enforced at request construction

**Acceptance Criteria:**
- Load Qwen3-8B GGUF, send SparkRequest, receive SparkResponse with accurate token count
- Stop sequences halt generation correctly
- Invalid temperature raises at construction time
- All existing SparkAdapter tests pass
- Determinism: same seed + same prompt → same output (10x verification)

**Tests:** ~25 new tests
**Parallel conflicts:** None (spark/ layer only)

---

### WO-028: Template Fallback Chain
**Step:** 1.2 | **Files:** `aidm/narration/guarded_narration_service.py`, `aidm/narration/narrator.py`

Connect the full 55-template dictionary to the GuardedNarrationService fallback path:
- GuardedNarrationService._generate_template_narration() expands from 4 → 55 templates
- LLMQueryInterface falls back to templates when model unavailable or on guardrail rejection
- Fallback is silent and seamless (player sees narration, not error)
- Provenance tag switches from [NARRATIVE] to [NARRATIVE:TEMPLATE] on fallback

**Acceptance Criteria:**
- With no model loaded: all 55 narration tokens produce template text
- With model loaded but guardrail rejection: falls back to template
- Provenance tags correctly distinguish LLM vs template narration
- BL-003 boundary intact (no core imports)
- FREEZE-001 hash verification still enforced

**Tests:** ~20 new tests
**Parallel conflicts:** None (narration/ layer only)

---

### WO-029: Kill Switch Suite (KILL-002 through KILL-006)
**Step:** 1.3 | **Files:** `aidm/narration/guarded_narration_service.py`, `aidm/core/monitoring.py` (new)

Implement the 5 remaining kill switches documented in M1_MONITORING_PROTOCOL:
- KILL-002: Spark output contains mechanical assertion (regex detection for damage numbers, AC values, rule citations not sourced from STP)
- KILL-003: Spark output exceeds max_tokens by >10% (generation runaway)
- KILL-004: Spark latency exceeds 10s (hang detection)
- KILL-005: Consecutive guardrail rejections > 3 (pattern failure)
- KILL-006: State hash drift detected post-narration (broader than FREEZE-001's memory-only check)

Each kill switch: triggers alert, blocks further Spark calls, falls back to templates, logs incident with full context.

**Acceptance Criteria:**
- Each kill switch testable in isolation
- Kill switch state persists across turns (not reset per-call)
- Manual reset only (no auto-recovery)
- Template fallback activates on any kill switch trigger
- Monitoring dashboard data emitted (structured log events)

**Tests:** ~30 new tests
**Parallel conflicts:** Shares guarded_narration_service.py with WO-028 — **SERIALIZE after WO-028**

---

### WO-030: Narration Pipeline Wiring
**Step:** 1.4 | **Files:** `aidm/core/play_loop.py`, `aidm/narration/guarded_narration_service.py`

Connect play_loop.py narration tokens to actual narration generation:
- After each combat action, play loop calls GuardedNarrationService with:
  - narration_token (string)
  - Relevant STP data (attack roll, damage, target, conditions changed)
  - FrozenWorldStateView snapshot
- GuardedNarrationService routes to LLM or template based on availability
- TurnResult gains `narration_text: str` field (populated string, not just token)
- NarrativeBrief assembler: extracts safe-to-show mechanical data from STP for Spark context

**Acceptance Criteria:**
- Every narration_token in play_loop.py produces narration_text in TurnResult
- With LLM: narration is generated from STP data (not raw game state — containment boundary)
- Without LLM: template narration identical to current behavior
- FrozenWorldStateView enforced (BL-020) — narration cannot mutate state
- Performance: <500ms p95 for template path, <3s p95 for LLM path
- All existing play_loop tests pass unchanged
- Determinism: Box state identical regardless of narration path taken

**Tests:** ~20 new tests
**Parallel conflicts:** Touches play_loop.py — **SERIALIZE after WO-029**

---

### WO-031: Grammar Shield v1
**Step:** 1.5 | **Files:** `aidm/spark/grammar_shield.py` (new), `aidm/spark/llamacpp_adapter.py`

Basic output validation layer between LlamaCppAdapter and callers:
- JSON mode enforcement: if SparkRequest.json_mode=True, validate output parses as JSON
- Schema validation: if structured output template specifies schema, validate against it
- Mechanical assertion detection: flag outputs containing unauthorized damage numbers, AC values, or rule citations
- Re-generation on validation failure (max 2 retries, then template fallback)

**Acceptance Criteria:**
- json_mode=True request with non-JSON output triggers retry
- Schema mismatch triggers retry then fallback
- Mechanical assertion in narrative output triggers KILL-002
- Retry budget tracked per-request (not global)
- All retries logged with original and retry outputs

**Tests:** ~25 new tests
**Parallel conflicts:** Shares llamacpp_adapter.py with WO-027 — **SERIALIZE after WO-027**

---

### Phase 1 Sequencing

```
WO-027 (SparkAdapter canonical)  ─────────────────→ WO-031 (Grammar Shield)
WO-028 (Template fallback)       → WO-029 (Kill switches) → WO-030 (Pipeline wiring)
```

**Parallel batch 1:** WO-027 + WO-028 (no file overlap)
**Parallel batch 2:** WO-029 + WO-031 (after their respective dependencies)
**Serial:** WO-030 last (depends on WO-028, WO-029 completing)

### Phase 1 Audit Gate: A8 — Spark Integration Proof

**After:** WO-030 complete
**What Gets Verified:**
- Real LLM generates narration from STP data
- Template fallback works seamlessly
- All 6 kill switches operational
- Box state determinism unaffected by narration path
- No SPARK→State writes (BL-020, Axiom 5)
- Performance: LLM narration <3s p95, template <500ms p95
- Grammar Shield catches mechanical assertions

**Pass criteria:** All above verified with test evidence. This is a formal gate — Phase 2 does not begin until A8 passes.

---

## Phase 2: Content Breadth + Narration Bridge (Parallel Tracks)

**Goal:** Playable D&D 3.5e content (feats, skills, expanded spells) built in parallel with the narration bridge that lets Spark see NarrativeBriefs.

**Dependency:** Phase 1 complete (A8 passed).

### Track 2A: Narration Bridge

### WO-032: NarrativeBrief Assembler
**Step:** 2A.1 | **Files:** `aidm/lens/narrative_brief.py` (new), `aidm/lens/context_assembler.py` (new)

Build the one-way valve that transforms STPs into Spark-safe context:
- NarrativeBrief dataclass: subset of STP mechanical data safe for Spark to see
  - What happened (attack hit/miss, damage dealt, condition applied)
  - Who was involved (names, not internal IDs)
  - Where it happened (location descriptions, not grid coordinates)
  - NOT included: raw game state, entity internals, future options
- Context Assembler: builds minimum-necessary context window for each Spark call
  - Token budget awareness (respect SparkRequest.max_tokens)
  - Relevance filtering (recent events weighted higher)
  - Session continuity (previous narrations for consistency)

**Acceptance Criteria:**
- NarrativeBrief contains no internal IDs, no raw HP values, no entity dictionaries
- Context Assembler respects token budget (never exceeds)
- Provenance: NarrativeBrief tagged as [DERIVED] from [BOX] STPs
- Spark receives NarrativeBrief, not FrozenWorldStateView
- Lens mediation enforced (Box→Lens→Spark, no shortcuts)

**Tests:** ~30 new tests
**Parallel conflicts:** None (new lens/ files)

---

### WO-033: Spark Integration Stress Test
**Step:** 2A.2 | **Files:** `tests/test_spark_integration_stress.py` (new)

Run all 4 existing scenarios (tavern, dungeon, field, boss) with real Spark backend:
- Box state determinism verified: same seed → same mechanical outcome regardless of LLM narration
- Kill switches trigger correctly on injected boundary violations
- Performance under real LLM load: full action resolution <3s p95
- Gold Masters still replay correctly (Box layer unaffected)
- Template fallback activates cleanly on simulated failures
- NarrativeBrief containment: Spark never sees raw game state

**Acceptance Criteria:**
- All 4 scenarios complete with real LLM narration
- Determinism: 10x replay produces identical Box state
- Kill switch injection tests: each of KILL-001 through KILL-006 triggers correctly
- Latency: p95 <3s with LLM, p95 <500ms template fallback
- Zero Box state divergence between LLM and template narration paths

**Tests:** ~40 new tests
**Parallel conflicts:** Read-only test — parallel-safe with Track 2B

---

### Track 2B: Content Breadth (All Box-layer, highly parallel)

### WO-034: Core Feat System
**Step:** 2B.1 | **Files:** `aidm/box/feat_resolver.py` (new), `aidm/schemas/feats.py` (new)

15 core combat feats following the AoOTracker pattern (WO-011):
- **Melee chain:** Power Attack, Cleave, Great Cleave
- **Defense chain:** Dodge, Mobility, Spring Attack
- **Ranged chain:** Point Blank Shot, Precise Shot, Rapid Shot
- **Weapon chain:** Weapon Focus, Weapon Specialization
- **Two-Weapon Fighting:** TWF, Improved TWF, Greater TWF
- **Initiative:** Improved Initiative

Each feat: prerequisite validation, combat modifier application, integration with existing resolvers.

**Acceptance Criteria:**
- All 15 feats resolve correctly per D&D 3.5e PHB
- Prerequisites enforced (BAB requirements, ability score minimums, feat chains)
- Modifiers apply during combat resolution (not as separate step)
- No 5e contamination (no advantage/disadvantage, no proficiency bonus)
- EF.* constants for any new entity fields
- RNG stream: combat (existing stream)

**Tests:** ~60 new tests
**Parallel conflicts:** None (new box/ files, no play_loop changes)

---

### WO-035: Skill System
**Step:** 2B.2 | **Files:** `aidm/box/skill_resolver.py` (new), `aidm/schemas/skills.py` (new)

Combat-adjacent skills per D&D 3.5e PHB:
- **Tumble** — DC 15 to avoid AoO when moving through threatened square
- **Concentration** — maintain spells under damage/distraction
- **Hide/Move Silently** — stealth with opposed checks
- **Spot/Listen** — perception with opposed checks
- **Use Magic Device** — UMD checks for restricted items
- **Balance** — move on difficult surfaces without falling

Integration points: Tumble→AoO resolver, Concentration→spell duration tracker, Hide/Spot→initiative.

**Acceptance Criteria:**
- All 7 skills resolve per PHB chapter 4
- Opposed checks use correct modifiers (ability mod + ranks + misc)
- Integration with existing resolvers verified (AoO, spellcasting, initiative)
- Skill ranks respect class/cross-class distinction
- RNG stream: combat (for opposed checks in combat)

**Tests:** ~40 new tests
**Parallel conflicts:** None (new box/ files)

---

### WO-036: Expanded Spell Registry
**Step:** 2B.3 | **Files:** `aidm/box/spell_definitions.py` (extend), `aidm/schemas/spells.py` (extend)

Expand from 17 spells to ~50 covering levels 0-5:
- **Level 0:** Light, Mending, Detect Magic, Read Magic, Resistance, Guidance
- **Level 1:** Cure Light Wounds, Shield, Magic Missile (already exists), Bless, Bane, Grease, Sleep
- **Level 2:** Cure Moderate Wounds, Bull's Strength, Cat's Grace, Web, Invisibility, Scorching Ray
- **Level 3:** Cure Serious Wounds, Haste, Slow, Dispel Magic, Lightning Bolt
- **Level 4:** Cure Critical Wounds, Stoneskin, Wall of Fire, Dimension Door
- **Level 5:** Cone of Cold, Hold Monster, Wall of Stone, Raise Dead

Each spell: targeting mode, save type/DC, damage/effect, duration, concentration flag, AoE template (if applicable).

**Acceptance Criteria:**
- All ~33 new spells resolve through existing SpellResolver framework
- AoE spells use existing AoE rasterizer (WO-004)
- Duration tracking via existing DurationTracker (WO-015)
- Concentration checks integrated with Skill system (WO-035 dependency for Concentration skill)
- Healing spells correctly modify HP within HP_MAX bounds
- Buff/debuff spells correctly apply/remove conditions

**Tests:** ~50 new tests
**Parallel conflicts:** None (extends existing spell files, no structural changes)
**Note:** Concentration skill integration deferred if WO-035 not yet complete — stub with fixed DC check.

---

### WO-037: Experience and Leveling
**Step:** 2B.4 | **Files:** `aidm/box/experience_resolver.py` (new), `aidm/schemas/leveling.py` (new)

CR-based XP calculation and level-up mechanics:
- XP awards per D&D 3.5e DMG Table 2-6 (CR vs party level)
- Level thresholds per DMG Table 3-2
- Level-up grants: hit die roll, skill points, feat slots (every 3rd level), ability score increase (every 4th level), spell slots per class table
- Multi-class XP penalty rules (PHB p.60)

**Acceptance Criteria:**
- XP calculation correct for all CR/level combinations in DMG tables
- Level-up applies all mechanical changes atomically
- New entity fields (EF.XP, EF.LEVEL, EF.CLASS_LEVELS) via EF.* constants
- State mutation only through authorized engine modules (BL-020)
- RNG stream: combat (for hit die rolls)

**Tests:** ~35 new tests
**Parallel conflicts:** None (new box/ files)

---

### Phase 2 Sequencing

```
Track 2A (Narration):
  WO-032 (NarrativeBrief) → WO-033 (Stress Test)

Track 2B (Content — all parallel):
  WO-034 (Feats)
  WO-035 (Skills)
  WO-036 (Spells)      ← soft dependency on WO-035 for Concentration
  WO-037 (XP/Leveling)
```

**Parallel batch 1:** WO-032 + WO-034 + WO-035 + WO-037 (no file overlap)
**Parallel batch 2:** WO-033 + WO-036 (after WO-032 and WO-035)

### Phase 2 Audit Gate: A9 — Content Integration Proof

**After:** All Phase 2 WOs complete
**What Gets Verified:**
- Real LLM narration works through NarrativeBrief (not raw state)
- 4 scenarios pass with real Spark under stress
- All 15 feats resolve correctly with existing combat engine
- All 7 skills integrate with existing resolvers
- ~50 spells resolve through SpellResolver
- XP/leveling mechanics correct per DMG tables
- Box determinism holds across all new content
- All kill switches tested under real load
- No 5e contamination in any new content

**Pass criteria:** All above verified. Formal gate — Phase 3 does not begin until A9 passes.

---

## Phase 3: Session Playability

**Goal:** Connect all pieces into a playable session loop. A player speaks, the system understands, resolves, narrates, and speaks back.

**Dependency:** Phase 2 complete (A9 passed).

### WO-038: Intent Bridge (DeclaredAttackIntent → AttackIntent)
**Step:** 3.1 | **Files:** `aidm/interaction/intent_bridge.py` (new)

Bridge the voice layer to combat resolution:
- Translate DeclaredAttackIntent (string target_ref, string weapon) → AttackIntent (entity_id, Weapon dataclass)
- Entity name resolution against current WorldState entity roster
- Weapon name resolution against entity equipment
- Ambiguity handling: if multiple matches, return clarification request (not guess)
- Same bridge for spell intents: DeclaredSpellIntent → SpellIntent

**Acceptance Criteria:**
- Exact name match resolves correctly
- Partial name match with single candidate resolves correctly
- Ambiguous match returns clarification request (no silent wrong target)
- Unknown target returns error with helpful message
- FrozenWorldStateView used for lookups (BL-020)

**Tests:** ~25 new tests
**Parallel conflicts:** None (new interaction/ file)

---

### WO-039: Session Orchestrator
**Step:** 3.2 | **Files:** `aidm/core/session_orchestrator.py` (new)

Full session loop connecting all subsystems:
- STT → Voice Intent Parser → Intent Bridge → Box (combat resolution) → STP → NarrativeBrief → Spark (narration) → TTS
- VRAM budget management: Spark and SDXL cannot be loaded simultaneously on <12GB GPU
  - Lazy model loading/unloading based on current need
  - Model priority: Spark (narration) > SDXL (images) > ACE-Step (music)
- Turn pacing: natural rhythm between player input and system response
- Error recovery: any subsystem failure falls back gracefully (STT failure → text input, Spark failure → template narration, TTS failure → text output)

**Acceptance Criteria:**
- Full turn cycle completes: voice in → narration out
- Text fallback works when voice unavailable
- Template fallback works when Spark unavailable
- VRAM budget never exceeded (model swap when needed)
- Session state persists across turns (who spoke last, what happened)
- FrozenWorldStateView enforced throughout pipeline

**Tests:** ~30 new tests
**Parallel conflicts:** None (new core/ file)

---

### WO-040: Scene Management
**Step:** 3.3 | **Files:** `aidm/lens/scene_manager.py` (new)

Dungeon crawl scene transitions:
- Room-to-room movement (exit detection, loading next room)
- Encounter triggers (enter room → roll initiative → combat begins)
- Rest mechanics (short rest: 1 hour, heal 1 HD; long rest: 8 hours, full recovery — 3.5e rules)
- Loot placement from room definitions
- Environmental data population (Lens Environmental Data Index)

**Acceptance Criteria:**
- Scene transitions preserve all entity state
- Encounter triggers follow D&D 3.5e wandering monster rules
- Rest mechanics apply correct 3.5e healing (not 5e short/long rest)
- Loot items added to entity inventory through Box event sourcing
- Environmental data queryable by Box during combat

**Tests:** ~25 new tests
**Parallel conflicts:** None (new lens/ file)

---

### WO-041: DM Personality Layer
**Step:** 3.4 | **Files:** `aidm/spark/dm_persona.py` (new)

Consistent DM voice using existing Spark infrastructure:
- System prompt engineering for DM persona (authoritative, fair, dramatic)
- Tone control parameter (serious ↔ humorous, verbose ↔ terse) — affects Spark prompt, not mechanics
- NPC voice differentiation: map NPC names to Kokoro voice personas
- Session memory: previous narrations summarized for consistency (Context Assembler integration)
- Tone control lives in Lens Player Model (never affects Box)

**Acceptance Criteria:**
- DM persona maintains consistent voice across a full scenario
- Tone parameter changes narration style without affecting mechanical outcomes
- NPC voice mapping produces distinct TTS output per character
- Session memory window respects token budget
- No mechanical authority in persona output (Axiom 2)
- Provenance: all DM output tagged [NARRATIVE]

**Tests:** ~20 new tests
**Parallel conflicts:** None (new spark/ file)

---

### Phase 3 Sequencing

```
WO-038 (Intent Bridge) → WO-039 (Session Orchestrator)
WO-040 (Scene Management)     ← parallel with WO-038
WO-041 (DM Personality)       ← parallel with WO-038
```

**Parallel batch 1:** WO-038 + WO-040 + WO-041 (no file overlap)
**Serial:** WO-039 after WO-038 (orchestrator needs intent bridge)

### Phase 3 Audit Gate: A10 — Playability Proof

**After:** All Phase 3 WOs complete
**What Gets Verified:**
- Full session loop works: voice in → combat resolution → narrated response out
- Scene transitions work across multi-room dungeon
- Rest mechanics and loot work per 3.5e rules
- DM maintains consistent persona across full session
- VRAM budget management works under real hardware constraints
- All fallback paths functional (text, template, silence)
- No mechanical authority leak from Spark/DM persona
- All previous audit gates (A1-A9) still pass

**Pass criteria:** All above verified. Formal gate — Phase 4 does not begin until A10 passes.

---

## Phase 4: Playtest Gate + Documentation

**Goal:** First real play session. User feedback. Documentation for deployment.

**Dependency:** Phase 3 complete (A10 passed).

### WO-042: First Full Session Playtest
**Step:** 4.1 | **Files:** `tests/test_full_session_playtest.py` (new)

Automated playtest scenario:
- 4 PCs, 3-room dungeon, 2 combat encounters, 1 rest, 1 boss fight
- Full pipeline: STT → Intent → Box → STP → Spark → TTS
- Record: latency per turn, narration quality (length, provenance tags, no mechanical leaks), VRAM usage
- Generate playtest report with metrics

**Acceptance Criteria:**
- Full session completes without crashes or kill switch triggers
- Average turn latency <5s (including LLM)
- All narration properly provenance-tagged
- Box state deterministic across replay
- VRAM stays within budget throughout

**Tests:** ~15 new tests (scenario + metrics)
**Parallel conflicts:** Read-only test — parallel-safe

---

### WO-043: Fallback UX Polish
**Step:** 4.2 | **Files:** `aidm/immersion/fallback_ux.py` (new)

Player-facing communication when system degrades:
- Model swap notification: "Switching to faster model..." (not raw error)
- Template fallback: seamless, no notification (player shouldn't notice)
- Hardware limit: "Image generation paused to prioritize narration"
- Recovery notification: "Full capabilities restored"
- All notifications are [UNCERTAIN] provenance (system status, not game content)

**Acceptance Criteria:**
- Each degradation mode produces appropriate player-facing message
- Messages are in-character where possible (DM voice, not system voice)
- No raw error messages or stack traces reach player
- Notifications don't interrupt combat flow

**Tests:** ~15 new tests
**Parallel conflicts:** None (new immersion/ file)

---

### WO-044: Technical Documentation
**Step:** 4.3 | **Files:** `docs/deployment/` (new directory)

- Architecture overview for new contributors
- Hardware requirements (minimum, recommended, optimal)
- Deployment guide (Python venv, model downloads, GPU setup)
- API reference for session orchestrator
- Configuration guide (model selection, voice personas, tone control)

**Acceptance Criteria:**
- New contributor can set up and run the system from docs alone
- Hardware tiers documented with expected performance at each tier
- All configuration options documented with defaults and valid ranges

**Tests:** None (documentation only)
**Parallel conflicts:** None

---

### Phase 4 Audit Gate: A11 — Ship Gate

**After:** All Phase 4 WOs complete
**What Gets Verified:**
- Full session playtest passes with metrics
- All fallback UX paths tested
- Documentation complete and accurate
- All previous gates (A1-A10) still pass
- Full pytest suite green
- KNOWN_TECH_DEBT.md reviewed and current
- Final test count documented

**Pass criteria:** All above verified. This is the M3 transition gate. System is deployment-ready.

---

## Complete Audit Checkpoint Registry

| Gate | After | What | Status |
|------|-------|------|--------|
| A1: Foundation | Plan v1 Step 1 | BL-001→012, geometry | **PASSED** |
| A2: Membrane | Plan v1 Step 2 | Lens read-only, provenance | **PASSED** |
| A3: Safety | Plan v1 Step 3 | Spark one-way valve | **PASSED** |
| A4: Vertical Slice | Plan v1 Step 4 | Box→Lens→Spark proof | **PASSED** |
| A5: Regression | Plan v1 Step 6 | Gold Masters, perf baselines | **PASSED** |
| A6: Boundary | Plan v1 Step 7 | BL-020 with real backends | **PENDING — WO-026** |
| A7: Full System | Plan v1 closure | All above re-verified | **PENDING — WO-026** |
| A8: Spark Integration | Plan v2 Phase 1 | Real LLM narration, kill switches, Grammar Shield | **FUTURE** |
| A9: Content Integration | Plan v2 Phase 2 | Feats/skills/spells + NarrativeBrief stress test | **FUTURE** |
| A10: Playability | Plan v2 Phase 3 | Full session loop, scene management, DM persona | **FUTURE** |
| A11: Ship Gate | Plan v2 Phase 4 | Playtest, fallback UX, documentation, M3 transition | **FUTURE** |

---

## Work Order Summary

| WO | Phase | Description | Dependencies | Files |
|----|-------|-------------|-------------|-------|
| WO-027 | 1.1 | Canonical SparkAdapter Integration | WO-026 pass | spark/ |
| WO-028 | 1.2 | Template Fallback Chain | WO-026 pass | narration/ |
| WO-029 | 1.3 | Kill Switch Suite (KILL-002→006) | WO-028 | narration/, core/ |
| WO-030 | 1.4 | Narration Pipeline Wiring | WO-029 | core/, narration/ |
| WO-031 | 1.5 | Grammar Shield v1 | WO-027 | spark/ |
| WO-032 | 2A.1 | NarrativeBrief Assembler | Phase 1 pass | lens/ |
| WO-033 | 2A.2 | Spark Integration Stress Test | WO-032 | tests/ |
| WO-034 | 2B.1 | Core Feat System (15 feats) | Phase 1 pass | box/, schemas/ |
| WO-035 | 2B.2 | Skill System (7 skills) | Phase 1 pass | box/, schemas/ |
| WO-036 | 2B.3 | Expanded Spell Registry (~33 new) | WO-035 (soft) | box/, schemas/ |
| WO-037 | 2B.4 | Experience and Leveling | Phase 1 pass | box/, schemas/ |
| WO-038 | 3.1 | Intent Bridge | Phase 2 pass | interaction/ |
| WO-039 | 3.2 | Session Orchestrator | WO-038 | core/ |
| WO-040 | 3.3 | Scene Management | Phase 2 pass | lens/ |
| WO-041 | 3.4 | DM Personality Layer | Phase 2 pass | spark/ |
| WO-042 | 4.1 | Full Session Playtest | Phase 3 pass | tests/ |
| WO-043 | 4.2 | Fallback UX Polish | Phase 3 pass | immersion/ |
| WO-044 | 4.3 | Technical Documentation | Phase 3 pass | docs/ |

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Qwen3 output violates boundary laws | HIGH | Kill switches (KILL-001→006), Grammar Shield, template fallback |
| LLM latency blows 3s p95 budget | MEDIUM | Qwen3-4B fallback, response streaming, shorter prompts |
| RQ-SPARK-001 never delivers | MEDIUM | Grammar Shield + existing LLMQueryInterface replaces Scene Fact Pack |
| RQ-NARR-001 never delivers | LOW | Basic tone control via DM persona, iterate empirically |
| Content volume overwhelming | LOW | Prioritize SRD core; data-entry work is parallelizable |
| VRAM contention (Spark + SDXL) | MEDIUM | Session orchestrator manages model loading/unloading |
| play_loop.py exceeds 500 lines | LOW | WO-030 adds ~20 lines; monitor but don't preemptively refactor |

---

## Open Questions

1. **Lens persistence format** — SQLite vs append-only log vs hybrid. Affects WO-032 (NarrativeBrief) and WO-040 (Scene Management). Decision needed before Phase 2 dispatch.

2. **Model fallback ladder** — Qwen3-8B (default) → Qwen3-4B (VRAM constrained) → Qwen3-0.5B (emergency). Exact quantization levels TBD during WO-027.

3. **Context window budget** — How to allocate tokens across NarrativeBrief, session memory, player model. Decision needed before WO-032.

4. **Concentration skill dependency** — WO-036 (spells) soft-depends on WO-035 (skills) for Concentration checks. If WO-035 is delayed, WO-036 uses fixed DC stub.

---

## Cross-References

| Document | Purpose |
|----------|---------|
| `EXECUTION_PLAN_DRAFT_2026_02_11.md` | Predecessor plan (7-step, now closing) |
| `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` | Binding architectural axioms |
| `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` | Operational architecture (Lens subsystems) |
| `AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards, boundary laws |
| `KNOWN_TECH_DEBT.md` | Intentional deferrals |
| `PROJECT_STATE_DIGEST.md` | Current project state |

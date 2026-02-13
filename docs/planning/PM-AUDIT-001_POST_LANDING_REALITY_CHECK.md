# PM-AUDIT-001 — Post-Landing Reality Check (AUTHORITATIVE RERUN)

**Author:** Opus (PM)
**Date:** 2026-02-12 (rerun against frozen repo state)
**Scope:** Read-only. No code changes. No new specs. No refactors.
**Method:** File-backed evidence from repo grep, test runs, and contract review.
**Baseline:** `pytest` run at `d4edf47`: 4601 passed, 11 skipped, 1 xfailed, 7 failed (chatterbox/torch)

---

## Invariant Enforcement Table

| # | Invariant / Claim | Where Enforced (file + test) | Status |
|---|-------------------|------------------------------|--------|
| **BOUNDARY LAWS** | | | |
| 1 | BL-001: Spark never imports aidm.core | `tests/test_boundary_law.py::TestBL001_SparkMustNotImportCore` — AST scan | **Enforced** |
| 2 | BL-002: Spark never imports aidm.narration | `tests/test_boundary_law.py::TestBL002_SparkMustNotImportNarration` — AST scan | **Enforced** |
| 3 | BL-003: Narration never imports aidm.core | `tests/test_boundary_law.py::TestBL003_NarrationMustNotImportCore` — AST scan | **Enforced** |
| 4 | BL-004: Box never imports aidm.narration | `tests/test_boundary_law.py::TestBL004_BoxMustNotImportNarration` — AST scan | **Enforced** |
| 5 | BL-005: Only aidm.core imports RNGManager | `tests/test_boundary_law.py::TestBL005_OnlyCoreImportsRNG` — 3 subtests | **Enforced** |
| 6 | BL-006: No stdlib random outside rng_manager | `tests/test_boundary_law.py::TestBL006_NoStdlibRandomOutsideRNGManager` — 5 subtests | **Enforced** |
| 7 | BL-007: EngineResult immutable after creation | `tests/test_boundary_law.py::TestBL007_EngineResultImmutable` — 3 subtests | **Enforced** |
| 8 | BL-008: EventLog monotonic IDs | `tests/test_boundary_law.py::TestBL008_EventLogMonotonicIDs` — 3 subtests | **Enforced** |
| 9 | BL-009: RNG seed rejects non-int (inc. bool) | `tests/test_boundary_law.py::TestBL009_RNGSeedValidation` — 7 subtests | **Enforced** |
| 10 | BL-010: Frozen dataclass mutation rejected | `tests/test_boundary_law.py::TestBL010_FrozenDataclassMutation` — 4 subtests | **Enforced** |
| 11 | BL-011: WorldState.state_hash() deterministic | `tests/test_boundary_law.py::TestBL011_WorldStateHashDeterminism` — 3 subtests (100x) | **Enforced** |
| 12 | BL-012: Replay deterministic 10x across runs | `tests/test_boundary_law.py::TestBL012_ReplayDeterminism` + `test_replay_regression.py` | **Enforced** |
| 13 | BL-013: SparkRequest schema validation | `tests/test_boundary_law.py::TestBL013_SparkRequestValidation` — 6 subtests | **Enforced** |
| 14 | BL-014: IntentObject frozen on CONFIRMED | `tests/test_boundary_law.py::TestBL014` + `test_intent_bridge_contract_compliance.py::TestLifecycleImmutability` | **Enforced** |
| 15 | BL-015: EntityState.base_stats immutable | `tests/test_boundary_law.py::TestBL015_EntityStateDeepImmutability` — MappingProxyType, 4 subtests | **Enforced** |
| 16 | BL-017: UUID inject-only (no default_factory) | `tests/test_boundary_law.py::TestBL017_UUIDInjectionOnly` — 3 subtests | **Enforced** |
| 17 | BL-018: Timestamp inject-only | `tests/test_boundary_law.py::TestBL018_TimestampInjectionOnly` — 5 subtests | **Enforced** |
| 18 | BL-020: FrozenWorldStateView rejects mutation | `tests/test_boundary_law.py::TestBL020` — 14 subtests (T-020-01 through T-020-14) | **Enforced** |
| **DETERMINISM** | | | |
| 19 | Same seed → identical events (single turn) | `tests/runtime/test_replay_determinism_one_turn.py::TestReplayDeterminism` — 25x replay, 5 tests | **Enforced** |
| 20 | Same seed → identical events (1000+ turns) | `tests/integration/test_replay_regression.py::TestThousandTurnGate` — 4 scenarios × 1000 turns | **Enforced** |
| 21 | Gold masters: tavern, dungeon, field, boss | `tests/integration/test_replay_regression.py::TestPersistedGoldMasters` — 9 tests, hash-verified | **Enforced** |
| 22 | RNG stream isolation (combat ≠ narration) | `tests/integration/test_replay_regression.py::TestRNGIsolation` — 3 tests + `test_attack_resolution.py::test_combat_rng_does_not_affect_policy_rng` | **Enforced** |
| **ATTACK MECHANICS** | | | |
| 23 | d20 + bonus vs AC | `tests/test_attack_resolution.py` — 24 tests | **Enforced** |
| 24 | Natural 20 auto-hit, natural 1 auto-miss | `tests/test_attack_resolution.py::test_natural_20_always_hits`, `::test_natural_1_always_misses` | **Enforced** |
| 25 | Critical confirmation roll | `tests/test_attack_resolution.py::test_single_attack_critical_confirmation` + `test_full_attack_resolution.py::test_critical_confirmation_logic` | **Enforced** |
| 26 | Critical damage multiplication | `tests/test_attack_resolution.py::test_single_attack_critical_damage_multiplied` + `test_full_attack_resolution.py::test_critical_damage_multiplication` | **Enforced** |
| 27 | Flanking geometry (+2, 135° angle) | `tests/test_flanking.py` — 7 classes, 29 tests | **Enforced** |
| 28 | Sneak attack precision damage (not multiplied on crit) | `tests/test_sneak_attack.py` — 8 classes, 47 tests; key: `test_sneak_attack_not_multiplied_on_critical` | **Enforced** |
| 29 | Damage Reduction post-crit | `tests/test_damage_reduction.py` — 19 tests (14 unit + 5 integration) | **Enforced** |
| 30 | Concealment miss chance | `tests/test_concealment.py` — 19 tests (9 unit + 4 single-attack + 6 full-attack) | **Enforced** |
| 31 | Full attack iterative BAB | `tests/test_full_attack_resolution.py` — 25 tests; key: `test_high_bab_character_four_attacks` (BAB+20 → +20/+15/+10/+5) | **Enforced** |
| **INTENT BRIDGE** | | | |
| 32 | No-coaching in clarification prompts | `tests/spec/test_intent_bridge_contract_compliance.py::TestNoCoaching` — 19 regex patterns, 17 fixtures + 2 direct tests | **Enforced** |
| 33 | Bridge does not import resolvers or RNG | `tests/spec/test_intent_bridge_contract_compliance.py::TestAuthorityBoundary` — 7 forbidden imports checked | **Enforced** |
| 34 | Bridge uses FrozenWorldStateView | `tests/spec/test_intent_bridge_contract_compliance.py::TestAuthorityBoundary::test_bridge_uses_frozen_view` | **Enforced** |
| 35 | Bridge does not mutate world state | `tests/spec/test_intent_bridge_contract_compliance.py::TestAuthorityBoundary::test_bridge_does_not_mutate_world_state` | **Enforced** |
| 36 | Pipeline determinism (10x replay) | `tests/spec/test_intent_bridge_contract_compliance.py::TestDeterminism` — 17 fixtures × 10 runs = 170 checks | **Enforced** |
| 37 | No source material refs in clarification | `tests/spec/test_intent_bridge_contract_compliance.py::TestContentIndependence` — 6 patterns, 17 fixtures | **Enforced** |
| 38 | Candidate ordering: lexicographic | `tests/spec/test_intent_bridge_contract_compliance.py::TestCandidateOrdering` — **xfail (strict): Delta D-01** | **Not Enforced** |
| 39 | Clarification loop max 3 rounds | Contract §4.6 states max 3 rounds → RETRACTED. `clarification_loop.py` has no round counter. | **Not Enforced** |
| 40 | STM clear on scene/combat transitions | Contract §6C states it. `STMContext` has no clear-on-transition method. No test. | **Not Enforced** |
| **IMMERSION LAYER** | | | |
| 41 | Immersion imports only from whitelist | `tests/test_immersion_authority_contract.py::test_only_allowed_aidm_imports` — 18+ allowed packages, AST scan | **Enforced** |
| 42 | Immersion never imports RNG | `tests/test_immersion_authority_contract.py::test_no_rng_imports` | **Enforced** |
| 43 | Immersion never imports stdlib random | `tests/test_immersion_authority_contract.py::test_no_random_stdlib_import` | **Enforced** |
| **PHYSICAL AFFORDANCE (AD-005)** | | | |
| 44 | Encumbrance load tiers match PHB | `tests/test_encumbrance.py` — 26 tests (PHB Table 9-1/9-2) | **Enforced** |
| 45 | Container capacity enforcement | `tests/test_container_resolver.py` — 21 tests (size, weight, slot, draw cost) | **Enforced** |
| 46 | Gear affordance tags in NarrativeBrief | `tests/test_gear_affordance_056.py` — 20 tests (visible_gear field + pipeline) | **Enforced** |
| **PREVIOUSLY UNENFORCEABLE — RE-ASSESSED** | | | |
| 47 | AD-007 Layer B frozen at world compile | No test verifies Layer B schema exists per ability. 0 tests reference AD-007. | **Not Enforced** |
| 48 | PromptPack v1 five-channel assembly | `tests/test_prompt_pack.py::test_to_dict_structure` verifies all 5 channels present. `test_prompt_pack_builder.py` — 66 tests including 10x determinism. | **Enforced** |
| 49 | World Compiler determinism (same inputs → identical bundle) | `tests/test_asset_pool_determinism_replay.py` — 35 tests verify asset/knowledge determinism (50x replay). Full world-compile idempotency not tested. | **Partially Enforced** |
| 50 | Knowledge mask progressive revelation (4 stages) | `tests/test_discovery_log_knowledge_mask.py` — 35 tests verify HEARD_OF→SEEN→FOUGHT→STUDIED progression + field leakage masking. | **Enforced** |
| **RUNTIME PLAY LOOP** | | | |
| 51 | End-to-end attack play loop | `tests/runtime/test_play_one_turn_attack.py` — 13 tests, all pass | **Enforced** |
| 52 | End-to-end move play loop | `tests/runtime/test_play_one_turn_move.py` — 13 tests, all pass | **Enforced** |
| 53 | Runtime no-coaching constraint | `tests/runtime/test_no_coaching_clarification_prompts.py` — 9 tests | **Enforced** |

---

## Risk Register (max 5)

| # | Risk | Evidence |
|---|------|----------|
| **R1** | **Candidate ordering is insertion-order, not lexicographic.** The Intent Bridge contract (§2.3) requires lexicographic sorting. Implementation uses `dict.items()` iteration. xfail test at `test_intent_bridge_contract_compliance.py::TestCandidateOrdering`. Replay may diverge if world state construction order changes. | `aidm/interaction/intent_bridge.py:_resolve_entity_name()` — no `sorted()` call on candidates |
| **R2** | **AoO weapon_data lacks isinstance guard.** `aoo.py:544` calls `.get()` on `weapon_data` without verifying it is a dict. If `weapon_data` is a string (e.g., `"longsword"`), `.get()` raises `AttributeError`. Runtime tests pass because fixtures use dict-style weapon data, masking the latent bug. | `aidm/core/aoo.py:536-548` — `weapon_data.get()` without `isinstance(weapon_data, dict)` check |
| **R3** | **No test enforces clarification loop round limit.** Contract §4.6 specifies max 3 rounds then RETRACTED. `clarification_loop.py` has no round counter, no `max_rounds` parameter. Infinite clarification loops are possible. | `aidm/immersion/clarification_loop.py` — grep for "round\|max\|limit" returns only narrative text, no enforcement logic |
| **R4** | **Gold masters are fragile.** Every new event payload field (flanking, sneak attack) requires gold master regeneration. No CI gate prevents accidental drift merge. A contributor adding a field without regenerating will see test failures across all 4 scenario files. | `tests/fixtures/gold_masters/*.jsonl` — 4 files, regenerated multiple times this session |
| **R5** | **AD-007 Presentation Semantics has no test enforcement.** The three-layer model (A/B/C) is ratified as an architectural decision, but no test verifies that abilities carry Layer B bindings, that Layer B is frozen, or that Spark validates against Layer B tags. Search for "AD-007" across test files returns 0 results. | `docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md` — 0 dedicated tests |

---

## Corrections from Prior Audit

| Item | Prior Audit (moving repo) | This Audit (frozen repo) | Change |
|------|---------------------------|--------------------------|--------|
| R2 | 9 runtime play-controller tests fail (aoo.py:544 AttributeError) | 40/40 runtime tests pass. Bug is latent: `isinstance` guard still absent but fixtures now use dict weapon data. | **Downgraded** from "broken play loop" to "latent type mismatch" |
| #48 | PromptPack five-channel: "Not Enforced" | `test_prompt_pack.py::test_to_dict_structure` verifies all 5 channels + 66 builder tests | **Upgraded** to Enforced |
| #49 | World Compiler determinism: "Not Enforced" | `test_asset_pool_determinism_replay.py` covers asset/knowledge (50x), but not full world bundle | **Upgraded** to Partially Enforced |
| #50 | Knowledge mask 4-stage: "Not Enforced" | `test_discovery_log_knowledge_mask.py` — 35 tests for 4-tier progression + field masking | **Upgraded** to Enforced |
| #32 | 16 no-coaching regex patterns | Actual count is 19 patterns in `COACHING_VIOLATION_PATTERNS` | **Corrected** count |
| #36 | 20 fixtures × 10 runs | Actual count is 17 fixtures × 10 runs = 170 checks | **Corrected** count |

---

## Recommended Next Single Action

**Add `isinstance(weapon_data, dict)` guard in `aidm/core/aoo.py:538`.** The current check `if weapon_data is None: continue` does not handle string-typed weapon references (e.g., `"longsword"`). When a string reaches line 544, `.get()` raises `AttributeError`. The fix is a 1-line change: `if weapon_data is None or not isinstance(weapon_data, dict): continue`. This is the same pattern applied in `flanking.py:92`.

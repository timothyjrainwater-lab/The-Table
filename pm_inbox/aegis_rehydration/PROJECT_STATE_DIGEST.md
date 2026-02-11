<!--
PROJECT STATE DIGEST — LEAN OPERATIONAL STATE
Last Updated: 2026-02-11
Tests: 3170 passing
Execution Plan: Steps 1-6 COMPLETE, Step 7 IN PROGRESS (WO-026 audit pending)
Historical content archived to: docs/history/PROJECT_HISTORY.md
-->

# Project State Digest

## Project Governance

**Product Owner (PO):** Thunder — Design decisions, implementation vision, research delivery.
**Project Manager (PM):** Opus — Full PM authority. Work orders, coding direction, agent coordination.

---

## Execution Plan Status (7 Steps)

| Step | Name | Status | WOs |
|------|------|--------|-----|
| 1 | Box Geometric Engine | **COMPLETE** | WO-001 to WO-006, WO-011 |
| 2 | Lens Structured Output | **COMPLETE** | WO-007 to WO-009, WO-012 |
| 3 | Spark/Trust | **PARTIAL** — STP delivered; real Spark LLM blocked by RQ-SPARK-001 | WO-010 |
| 4 | Vertical Slice Gate | **COMPLETE — GO GATE PASSED** | WO-013 |
| 5 | Spellcasting | **PARTIAL** — spellcasting delivered; narration upgrade blocked by RQ-NARR-001 | WO-014, WO-015 |
| 6 | Integration Testing | **COMPLETE** | WO-016, WO-017, WO-018, WO-019 |
| 7 | Immersion Layer | **IN PROGRESS** | WO-020 to WO-025 |

---

## Research-Blocked Gaps

| Gap | Step | Blocked By | Infrastructure Ready? |
|-----|------|-----------|----------------------|
| Real Spark LLM integration | 3.1 | RQ-SPARK-001 (NOT DELIVERED) | Yes — SparkAdapter framework exists |
| Constrained scene generation | 3.3 | RQ-SPARK-001 (NOT DELIVERED) | Yes — Lens validation, Room Schemas exist |
| Guarded LLM narration | 5.2 | RQ-NARR-001 (NOT DELIVERED) | Yes — STP pipeline, guardrails (FREEZE-001, BL-003) exist |

These are tracked deferrals, not failures. All infrastructure is built and tested; only the research inputs are missing.

---

## Audit Checkpoint Status

| Checkpoint | After | Status |
|------------|-------|--------|
| A1: Foundation | Step 1 | **PASSED** (implicit — BL-001→BL-012, 395 tests) |
| A2: Membrane | Step 2 | **PASSED** (implicit — Lens read-only, provenance valid, 210 tests) |
| A3: Safety | Step 3 | **PASSED** (implicit — BL-001/002 enforced, Spark one-way valve) |
| A4: Vertical Slice Gate | Step 4 | **PASSED** (formal gate — WO-013) |
| A5: Regression Baseline | Step 6 | **PASSED** (implicit — Gold Masters, 1000-turn determinism, perf baselines) |
| A6: Boundary Integrity | Step 7 | **PENDING** |
| A7: Full System Audit | Plan closure | **PENDING — WO-026** |

---

## Step 1: Box Geometric Engine (COMPLETE)

| WO | Module | Lines | Tests |
|----|--------|-------|-------|
| WO-001 | geometry_engine.py, geometry.py | 914 | 69 |
| WO-002 | cover_resolver.py | 531 | 58 |
| WO-003 | los_resolver.py | 644 | 43 |
| WO-004 | aoe_rasterizer.py | 441 | 55 |
| WO-005 | ranged_resolver.py | 460 | 60 |
| WO-006 | reach_resolver.py | 451 | 58 |
| WO-011 | combat_reflexes.py | 371 | 52 |

---

## Step 2: Lens Structured Output (COMPLETE)

| WO | Module | Lines | Tests |
|----|--------|-------|-------|
| WO-007 | lens_index.py | 598 | 42 |
| WO-008 | fact_acquisition.py | 480 | 58 |
| WO-009 | provenance.py | 734 | 59 |
| WO-012 | box_lens_bridge.py | 364 | 51 |

---

## Step 3: Spark/Trust (PARTIAL)

| WO | Module | Lines | Tests |
|----|--------|-------|-------|
| WO-010 | truth_packets.py | 798 | 47 |

**Delivered:** Structured Truth Packets (11 STP types, audit trail).
**Blocked:** Real Spark LLM (RQ-SPARK-001), constrained scene generation (RQ-SPARK-001).

---

## Step 4: Vertical Slice Gate (COMPLETE)

| WO | Module | Lines | Tests |
|----|--------|-------|-------|
| WO-013 | stp_emitter.py, test_vertical_slice_tavern.py | 1440 | 20 |

**GO GATE PASSED** — Box→Lens→Spark pipeline verified working.

---

## Step 5: Spellcasting (PARTIAL)

| WO | Module | Lines | Tests | Status |
|----|--------|-------|-------|--------|
| WO-014 | spell_resolver.py, spell_definitions.py, duration_tracker.py | 1433 | 51 | **COMPLETE** |
| WO-015 | play_loop.py (extended), combat_controller.py (extended) | 1730 | 17 | **COMPLETE** |

**Delivered:** Spellcasting resolution (17 spells), play loop integration.
**Blocked:** Narration upgrade (RQ-NARR-001).

---

## Step 6: Integration Testing (COMPLETE)

| WO | Module | Lines | Tests | Status |
|----|--------|-------|-------|--------|
| WO-016 | scenario_runner.py, test_multi_encounter_stress.py | 2261 | 24 | **COMPLETE** |
| WO-017 | performance_profiler.py, test_performance_profiling.py | 1746 | 46 | **COMPLETE** |
| WO-018 | replay_regression.py, test_replay_regression.py, Gold Masters | 4482 | 52 | **COMPLETE** |
| WO-019 | property_testing.py, test_property_based.py | 1151 | 48 | **COMPLETE** |

4 scenarios verified: Tavern (5v3), Dungeon (4v4), Field Battle (6v6), Boss Fight (5v1).
All deterministic, Lens-consistent, STPs validated.
All latency targets met: Box p95 5.08ms (target 50ms), Lens p95 0.06ms (target 20ms).
Thousand-Fold Fireball: 1000 iterations, all geometric invariants hold.
1000-turn determinism gate: All scenarios pass with Gold Master replay.

---

## Step 7: Immersion Layer (IN PROGRESS)

| WO | Module | Lines | Tests | Status |
|----|--------|-------|-------|--------|
| WO-020 | kokoro_tts_adapter.py, test_kokoro_tts.py | 1069 | 38 | **COMPLETE** |
| WO-021 | whisper_stt_adapter.py, test_whisper_stt.py | 850 | 31 | **COMPLETE** |
| WO-022 | sdxl_image_adapter.py, test_sdxl_image.py | 1303 | 50 | **COMPLETE** |
| WO-023 | tri_gem_socket.py, transparency.py, test_tri_gem_socket.py | 2553 | 59 | **COMPLETE** |
| WO-024 | voice_intent_parser.py, clarification_loop.py | 1797 | 39 | **COMPLETE** |
| WO-025 | combat_receipt.py, ghost_stencil.py, judges_lens.py | 2131 | 40 | **COMPLETE** |

Real backends: Kokoro TTS (CPU), faster-whisper STT (CPU), SDXL Lightning (NF4 GPU).
Tri-Gem Socket: RUBY/SAPPHIRE/DIAMOND transparency modes on STP streams.
Voice-first intent parser: Deterministic NLU at 50ms, STM context, DM-persona clarification.
Table-native UX: Combat receipts, ghost stencils (burst/cone/line), Judge's Lens (3-tier inspection).
All adapters use lazy loading, graceful fallback to stubs when deps unavailable.

---

## Test Summary

**Total: 3170 tests passing**

Recent additions:
- Geometry engine: 395 tests
- Lens layer: 210 tests
- Truth packets: 47 tests
- Vertical slice: 20 tests
- Spellcasting: 68 tests
- Multi-encounter stress: 24 tests
- Performance profiling: 46 tests
- Property-based testing: 48 tests
- Replay regression: 52 tests
- Kokoro TTS: 38 tests
- Whisper STT: 31 tests
- SDXL Image: 50 tests
- Tri-Gem Socket: 59 tests
- Voice intent parser: 39 tests
- Table-native UX: 40 tests

---

## Key References

| Document | Purpose |
|----------|---------|
| `docs/planning/EXECUTION_PLAN_DRAFT_2026_02_11.md` | Active 7-step execution plan (includes audit framework) |
| `docs/history/PROJECT_HISTORY.md` | Archived CP summaries, module inventory, frozen contracts |
| `AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards |
| `KNOWN_TECH_DEBT.md` | Intentionally deferred issues |
| `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` | Architectural axioms |

---

## Critical Invariants

- All tests pass in < 5 seconds
- Deterministic JSON (sorted keys)
- Event IDs strictly monotonic
- RNG streams isolated (combat, initiative, policy, saves)
- State mutations only through replay runner
- Entity field access via EF.* constants
- State mutation via deepcopy() only

# WO-AUDIT-POSTLAND-001 — Clean Project Inventory + Post-Land Health Check

**Author:** Opus (PM)
**Date:** 2026-02-13
**HEAD:** `d4edf47`
**Method:** Full pytest run, boundary-law AST scan, repo grep, file counts, demo verification
**Scope:** Read-only. No code changes.

---

## 1. Test Suite Status

### Full Suite

```
Command:  pytest --tb=short -q
Result:   4601 passed, 11 skipped, 1 xfailed, 7 failed
Duration: 104.67s
Platform: Python 3.11.1, pytest 9.0.2, Windows 11
```

### Failures (7) — All Chatterbox TTS, All Environment-Dependent

```
FAILED tests/immersion/test_chatterbox_tts.py::TestSynthesis::test_synthesize_returns_bytes
FAILED tests/immersion/test_chatterbox_tts.py::TestSynthesis::test_synthesize_increments_count
FAILED tests/immersion/test_chatterbox_tts.py::TestSynthesis::test_synthesize_with_persona
FAILED tests/immersion/test_chatterbox_tts.py::TestWavFormat::test_output_is_valid_wav
FAILED tests/immersion/test_chatterbox_tts.py::TestWavFormat::test_wav_has_riff_header
FAILED tests/immersion/test_chatterbox_tts.py::TestWavFormat::test_wav_sample_rate_is_24khz
FAILED tests/immersion/test_chatterbox_tts.py::TestErrorHandling::test_synthesis_with_special_characters
```

**Root cause:** `No module named 'torch.nn'` — torch install incomplete or GPU-only path not available in this environment.

**Confirmation re-run:** Isolated chatterbox suite re-run (32 tests collected) passes **32/32** when torch loads correctly. These 7 failures are environment flakes, not code bugs.

### xfail (1) — Expected, Tracked

```
tests/spec/test_intent_bridge_contract_compliance.py::TestCandidateOrdering::test_bridge_candidates_sorted_lexicographically
```

Delta D-01: `_resolve_entity_name()` uses dict insertion order, not lexicographic sort. Contract §2.3 requires sorting. xfail is strict — test will break (correctly) if someone adds a `sorted()` call.

### Skip (11) — Conditional Dependencies

All skips are `requires_kokoro`, `requires_whisper`, or similar hardware-gated markers. Expected behavior on machines without those models installed.

---

## 2. Boundary / Governance Status

### Boundary Law AST Scan

```
Command:  pytest tests/test_boundary_law.py -v
Result:   71 passed in 1.24s
```

| BL | Description | Tests | Status |
|----|-------------|-------|--------|
| BL-001 | Spark never imports aidm.core | 1 (AST scan) | PASS |
| BL-002 | Spark never imports aidm.narration | 1 (AST scan) | PASS |
| BL-003 | Narration never imports aidm.core | 1 (AST scan) | PASS |
| BL-004 | Box never imports aidm.narration | 1 (AST scan) | PASS |
| BL-005 | Only aidm.core imports RNGManager | 3 subtests | PASS |
| BL-006 | No stdlib random outside rng_manager | 5 subtests | PASS |
| BL-007 | EngineResult immutable after creation | 3 subtests | PASS |
| BL-008 | EventLog monotonic IDs | 3 subtests | PASS |
| BL-009 | RNG seed rejects non-int (inc. bool) | 7 subtests | PASS |
| BL-010 | Frozen dataclass mutation rejected | 4 subtests | PASS |
| BL-011 | WorldState.state_hash() deterministic | 3 subtests (100x) | PASS |
| BL-012 | Replay deterministic 10x across runs | multi | PASS |
| BL-013 | SparkRequest schema validation | 6 subtests | PASS |
| BL-014 | IntentObject frozen on CONFIRMED | multi | PASS |
| BL-015 | EntityState.base_stats immutable | 4 subtests | PASS |
| BL-017 | UUID inject-only (no default_factory) | 3 subtests | PASS |
| BL-018 | Timestamp inject-only | 5 subtests | PASS |
| BL-020 | FrozenWorldStateView rejects mutation | 14 subtests | PASS |

**71/71 boundary law tests pass. Zero violations.**

### Immersion Authority Contract

```
Command:  pytest tests/test_immersion_authority_contract.py -v
Result:   12 passed in 0.25s
```

All import whitelist, RNG prohibition, and mutation prohibition checks pass.

### Intent Bridge Compliance

```
Command:  pytest tests/spec/test_intent_bridge_contract_compliance.py -v
Result:   62 passed, 1 xfailed in 3.81s
```

Determinism (17 fixtures × 10 runs = 170 checks), no-coaching (19 regex patterns × 17 fixtures), authority boundary (7 forbidden imports), lifecycle immutability (4 tests), content independence (6 patterns × 17 fixtures) — all pass.

---

## 3. Repo Inventory Snapshot

### Code Volume

| Category | Files | Lines |
|----------|-------|-------|
| Production code (aidm/) | 180 | 69,603 |
| Test code (tests/) | 181 | 88,100 |
| **Total** | **393** | **157,703** |

Test-to-source ratio: **1.27:1**

### Module Breakdown

| Module | Files | Description |
|--------|-------|-------------|
| aidm/core/ | 67 | Deterministic combat engine, state, RNG, rules |
| aidm/schemas/ | 47 | Frozen dataclasses, entity fields, event payloads |
| aidm/immersion/ | 17 | STT/TTS adapters, voice parser, audio queue |
| aidm/runtime/ | 8 | Session orchestrator, play controller, bootstrap |
| aidm/lens/ | 7 | Narrative brief, context assembler, scene manager |
| aidm/narration/ | 7 | Guarded narration, templates, contradiction checker |
| aidm/spark/ | 6 | LlamaCpp adapter, grammar shield, DM persona |
| aidm/services/ | 4 | Service layer |
| aidm/data/ | 4 | Data loading |
| aidm/interaction/ | 2 | Intent bridge |
| aidm/ui/ | 2 | Terminal character sheet, contextual grid |
| aidm/testing/ | 5 | Test utilities |
| aidm/rules/ | 2 | Rule definitions |
| aidm/evaluation/ | 2 | Evaluation harness |
| aidm/examples/ | 1 | Example code |

### JSON Schemas (docs/schemas/)

8 schema files: `asset_binding`, `discovery_entry`, `intent_request`, `knowledge_mask`, `presentation_semantics_registry`, `rule_registry`, `vocabulary_registry`, `world_bundle`

### Architecture Documents

- **Contracts (docs/contracts/):** 3 — INTENT_BRIDGE, DISCOVERY_LOG, WORLD_COMPILER
- **Decisions (docs/decisions/):** 11 — AD-001 through AD-007 + DEC-WORLD-001 + others

### Dependencies (pyproject.toml — required)

```
pytest>=7.0.0, psutil>=5.9.0, pyyaml>=6.0, msgpack>=1.0.0,
opencv-python-headless>=4.8.0, Pillow>=10.0.0, numpy>=1.24.0
```

Optional (demo/TTS): `kokoro-onnx`, `onnxruntime`, `torch`, `transformers`, `snac`, `llama-cpp-python`

### Uncommitted State

- **14 files modified** (638 insertions, 636 deletions) — mostly immersion/TTS refactoring
- **20+ files untracked** — new features: chatterbox adapter, voice resolver, demo scripts, schemas
- **2 files deleted** — completed audit artifacts from pm_inbox/
- **Critical path (aidm/core/) has zero uncommitted changes**

---

## 4. Playable Now

### Demo A: Single Combat Turn (zero optional deps)

```
cd F:\DnD-3.5
python demo_combat_turn.py
```

**Expected output:** One full combat turn through the pipeline: intent parsing, Box resolution (d20 roll, attack vs AC, damage), truth packet emission, template narration, determinism verification (state hash). Prints attack events, HP changes, and narration text to terminal. Exit code 0.

### Demo B: Single Combat Turn + TTS Audio

```
python demo_combat_turn.py --with-tts
```

**Requires:** `kokoro-onnx`, `onnxruntime`
**Expected output:** Same as Demo A, plus synthesized WAV file (`demo_narration.wav`) with DM narration audio.

### Demo C: 5-Turn Micro Scenario

```
python demo_micro_scenario.py
```

**Expected output:** 5-turn dungeon crawl through SessionOrchestrator:
1. Attack goblin (Room A: Goblin Ambush)
2. Attack goblin (finish it)
3. Move east (transition to Rest Chamber)
4. Rest (heal up)
5. Move north (transition to Boss Room)

Each turn prints: player speech, Box events, DM narration, before/after HP, running state hash.

### Demo D: Kokoro TTS Voice Audition

```
python demo_tts_audio.py
```

**Requires:** `kokoro-onnx`, `onnxruntime`
**Expected output:** 54 voice samples + blends + narration samples in `auditions/` and `narration/` directories.

### Demo E: Orpheus Neural TTS Audition

```
python demo_orpheus_audition.py
```

**Requires:** `torch`, `transformers`, `bitsandbytes`, `snac`, `torchaudio` + GPU (~3GB VRAM)
**Expected output:** 16 emotion-tagged voice samples in `output/tts_audition_orpheus/`.

### Test Suite

```
pytest --tb=short -q                    # Full suite (4601 pass, ~105s)
pytest tests/test_boundary_law.py -v    # Boundary laws only (71 pass, ~1s)
pytest tests/spec/ -v                   # Intent bridge compliance (63 pass, ~4s)
```

---

## 5. Risks / Notes

1. **Chatterbox 7 failures are environment-only.** Torch import path issue. Isolated re-run passes 32/32 when torch loads correctly. Not a code bug. Consider adding `requires_torch` skip marker for CI portability.

2. **Delta D-01: Candidate ordering is insertion-order, not lexicographic.** Intent bridge contract §2.3 requires sorted candidates. `_resolve_entity_name()` in `aidm/interaction/intent_bridge.py` has no `sorted()` call. xfail test tracks this. Replay determinism is unaffected only as long as entity construction order is stable.

3. **AoO weapon_data latent type mismatch.** `aidm/core/aoo.py:544` calls `.get()` on `weapon_data` without `isinstance(weapon_data, dict)` guard. If weapon_data is a string (e.g., `"longsword"`), `.get()` raises `AttributeError`. Tests pass because all fixtures use dict-style weapon data. Fix: add `if weapon_data is None or not isinstance(weapon_data, dict): continue`.

4. **Clarification loop has no round counter.** `aidm/immersion/clarification_loop.py` has no `max_rounds` parameter. Contract §4.6 specifies max 3 rounds then RETRACTED, but no enforcement exists. Infinite clarification loops are theoretically possible.

5. **Gold masters are fragile to event payload expansion.** Every new event field (flanking, sneak attack) requires regeneration of 4 gold master files under `tests/fixtures/gold_masters/`. No CI gate prevents accidental drift.

6. **AD-007 Presentation Semantics has zero test enforcement.** Three-layer model (A/B/C) is ratified as an architectural decision, but no test verifies Layer B bindings exist, are frozen at compile, or that Spark validates against them. 0 tests reference AD-007.

7. **High-risk seam: `aidm/schemas/immersion.py`.** This file appears in both recent commits (b79a652) and uncommitted changes. The uncommitted changes add `reference_audio` and `exaggeration` fields to `VoicePersona`. All downstream consumers are already updated. Risk is controlled but this file should be committed promptly to avoid merge conflicts.

8. **aidm/core/ has zero uncommitted changes.** The critical path (attack resolution, state management, RNG, combat controller) is clean. All uncommitted work is in immersion/TTS/narration — non-critical path.

9. **World Compiler and Discovery Log are spec-only.** 825-line World Compiler contract and 764-line Discovery Log contract exist with zero implementation code. These are the two largest unbuilt systems.

10. **STM clear-on-transition is unimplemented.** `STMContext` has no `clear()` or transition-triggered reset method. Cross-scene pronoun carryover ("attack him" referring to an entity from the previous room) is not guarded.

---

*Report generated against HEAD `d4edf47` with 14 uncommitted files. All commands executed on Windows 11, Python 3.11.1.*

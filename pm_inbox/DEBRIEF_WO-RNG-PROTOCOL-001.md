# DEBRIEF: WO-RNG-PROTOCOL-001 — RNGProvider Protocol Extraction

**From:** Builder (Opus 4.6)
**To:** PM (Aegis), via PO (Thunder)
**Date:** 2026-02-14
**Lifecycle:** NEW
**WO:** WO-RNG-PROTOCOL-001
**Result:** COMPLETED — all 7 success criteria met

---

## Pass 1 — Full Context Dump

### What Was Done

Type-level refactor extracting `RNGProvider` and `RandomStream` Protocols from the concrete `RNGManager` / `DeterministicRNG` classes. Zero logic changes, zero behavioral changes.

### Files Created

1. **`aidm/core/rng_protocol.py`** — Two `@runtime_checkable` Protocol classes:
   - `RandomStream`: Protocol for stream objects (`randint`, `choice`, `random`, `shuffle`)
   - `RNGProvider`: Protocol for managers that vend named streams (`stream(name) -> RandomStream`)
   - Follows existing adapter pattern (`TTSAdapter`, `ImageAdapter`, `ImageCritiqueAdapter`)

2. **`tests/test_rng_protocol.py`** — 3 conformance tests:
   - `isinstance(RNGManager(42), RNGProvider)` → True
   - `isinstance(DeterministicRNG(42), RandomStream)` → True
   - All 4 required stream methods exist and are callable

### Files Modified (19 total)

All changes are import line + type annotation replacements. No logic touched.

**Core resolvers (`rng: RNGManager` → `rng: RNGProvider`):**
- `aidm/core/attack_resolver.py`
- `aidm/core/full_attack_resolver.py`
- `aidm/core/maneuver_resolver.py`
- `aidm/core/combat_controller.py`
- `aidm/core/initiative.py`
- `aidm/core/aoo.py`
- `aidm/core/environmental_damage_resolver.py`
- `aidm/core/experience_resolver.py`
- `aidm/core/save_resolver.py`
- `aidm/core/skill_resolver.py`
- `aidm/core/sneak_attack.py`
- `aidm/core/spell_resolver.py`
- `aidm/core/terrain_resolver.py`
- `aidm/core/mounted_combat.py`
- `aidm/core/play_loop.py`

**Core files that also instantiate RNGManager (dual import — Protocol for annotations, concrete for construction):**
- `aidm/core/replay_runner.py`
- `aidm/core/session_log.py`

**Stream-level annotation (`DeterministicRNG` → `RandomStream`):**
- `aidm/core/tactical_policy.py`

**Lens layer:**
- `aidm/lens/scene_manager.py`

### Files NOT Changed (per WO constraints)

- `aidm/core/rng_manager.py` — implementation stays, already structurally conforms
- All runtime files (`bootstrap.py`, `session.py`, `runner.py`, `play_controller.py`, `session_orchestrator.py`) — they instantiate concrete `RNGManager`, no annotation changes needed
- All 40+ test files — they construct `RNGManager(42)` directly, keep concrete imports
- Gold masters, schemas, presentation files — no RNG interface exposure

### Test Results

- **5,615 tests collected** (excluding pre-existing chatterbox CUDA failure)
- **5,609 passed, 6 failed** — all 6 failures are pre-existing:
  - 3× `test_tts_chunking.py` — TTS chunking tests (unrelated)
  - 1× `test_immersion_authority_contract.py` — import boundary for `tts_chunking` module (unrelated)
  - 2× `test_pm_inbox_hygiene.py` — inbox housekeeping (unrelated)
- **Zero regressions introduced by this WO**

### Import Graph Verification

After the refactor, `grep "from aidm.core.rng_manager import RNGManager" aidm/core/` returns zero results. All core resolvers now import the Protocol, not the concrete class. Only `replay_runner.py` and `session_log.py` retain the concrete import (for instantiation), alongside the Protocol import (for annotations).

### Boundary Laws

- BL-005, BL-006 (RNG monopoly): **PRESERVED** — all 103 boundary law tests pass
- BL-011 (deterministic hashing): **NOT AFFECTED**
- Full boundary matrix: **PASS**

### Mid-Session Course Correction

Initial `replace_all` of `RNGManager` → `RNGProvider` in `replay_runner.py` and `session_log.py` accidentally replaced instantiation calls (`RNGManager(master_seed)` → `RNGProvider(master_seed)`). This caused `TypeError: Protocols cannot be instantiated` in 5 replay tests. Caught immediately in the first test run, fixed by adding dual imports (concrete for construction, Protocol for annotations). Second test run confirmed all clear.

---

## Pass 2 — PM Summary

**WO-RNG-PROTOCOL-001: COMPLETED.** RNGProvider + RandomStream Protocols extracted to `aidm/core/rng_protocol.py`. 19 files updated (type annotations only). 3 conformance tests added. Zero regressions. All 103 boundary law tests pass. Import graph clean: core resolvers depend on Protocol, not concrete class. Ready for future WOs to introduce alternative RNG implementations (mock, crypto, replay).

---

## Retrospective (Pass 3 — Operational Judgment)

### Fragility
- **`replace_all` on class names is dangerous when the same name appears as both a type annotation AND a constructor call.** The `RNGManager` → `RNGProvider` replacement hit instantiation sites in `replay_runner.py` and `session_log.py`. The test suite caught it immediately, but a more careful approach would have been to grep for `RNGManager(` (with parenthesis) before doing blanket replacements, and handle files with constructor calls separately from pure-annotation files.

### Process Feedback
- The WO dispatch was well-written. Binary decisions were pre-made, the contract spec was precise, and the "Files NOT to Change" section prevented scope creep. This is the ideal WO format for type-level refactors.
- The WO listed 8 specific files but said "All other core resolvers" — the actual count was 19 files including `play_loop.py`, `replay_runner.py`, `session_log.py`, `mounted_combat.py`, `tactical_policy.py`, and `scene_manager.py`. The "all other" clause was correct but vague. For future WOs of this type, an exhaustive list (even if long) prevents missed files.

### Methodology
- Running tests after each logical step (not just at the end) caught the instantiation bug before it compounded. The staged approach (conformance tests first → core tests → full suite) was the right call.
- Using `replace_all` edits was efficient for the 15 pure-annotation files. The 2 dual-purpose files needed manual handling.

### Concerns
- None. The refactor is clean, the Protocol conforms at runtime, and the test suite validates it. No risk items carried forward.

# DEBRIEF: WO-DIRECTOR-03

**Lifecycle:** DELIVERED
**WO:** WO-DIRECTOR-03 — Director Phase 3: TableMood + StyleCapsule + Scene Lifecycle
**Commit:** `7a1d5cb`
**Gate result:** 149/149 gate tests PASS (133 existing + 16 new Gate H). 0 regressions (5,893 suite pass; 4 pre-existing failures unchanged).

---

## 0 — Scope Accuracy

WO scope was partially accurate — scene lifecycle events (Change 5) already existed, requiring no new implementation; all other 6 changes delivered as specified.

## 1 — Discovery Log

Validated before writing code:
- `aidm/oracle/` contains 9 standalone modules (facts_ledger, story_state, unlock_state, canonical, cold_boot, compaction, save_snapshot, working_set, __init__). Adding `table_mood.py` required zero structural changes.
- DirectorPromptPack is `@dataclass(frozen=True)` with no default fields — added `style_capsule: Optional[StyleCapsule] = None` after `bytes_hash` (last position, avoids non-default-after-default violation).
- `_reduce_oracle_event()` uses simple if/elif cascade. Added optional `table_mood_store` parameter with `None` default for backward compatibility — existing callers (3 test files) pass 4 positional args and are unaffected.
- `scene_start` and `scene_end` events already exist and are handled by StoryStateLog.apply() and BeatHistory.from_events(). No new event types needed.
- `compile_director_promptpack()` accepts keyword arguments — added `style_capsule=None` parameter. Pre-hash dict conditionally includes capsule data only when present, ensuring byte-identical hashes with Phase 2 when capsule is None.
- `select_beat()` and `select_beat_with_audit()` both had hardcoded `pacing_mode="NORMAL"` in all P3 and P7 branches. Extracted `_resolve_pacing_mode(dpp)` helper that maps StyleCapsule pacing to BeatIntent pacing (push→ACCELERATE, breathe→SLOW_BURN, normal/None→NORMAL).
- Used `TYPE_CHECKING` guard for StyleCapsule import in models.py to avoid circular import (aidm.lens.style_capsule imports from aidm.oracle.canonical, which is fine, but models.py is in aidm.lens.director).
- PromptPack.to_dict() returns keys {schema_version, truth, memory, task, style, contract} — not {world, entities, rules}. Adjusted DIR-H1b test accordingly.

## 2 — Methodology Challenge

Change 5 (scene lifecycle events) was specified as a creation task, but these events already existed with correct semantics in story_state.py and BeatHistory.from_events(). The WO should have included an assumption-to-validate: "scene_start/scene_end events may already exist" instead of presenting the change as greenfield. The existing implementation was complete and correct — no modifications needed. This wasted discovery time confirming a non-gap.

## 3 — Field Manual Entry

**#34. Optional field on frozen dataclass — position matters.** When adding an optional field to a frozen dataclass where ALL existing fields lack defaults, the new field MUST go at the end (after the last non-default field). Python dataclass ordering requires non-default fields before default fields. If you try to insert `style_capsule: Optional[X] = None` between existing non-default fields, you get `TypeError: non-default argument follows default argument`. Always append optional extensions to the tail.

## 4 — Builder Radar

- **Trap.** `_reduce_oracle_event()` is imported and called directly by 3 test files (test_oracle_gate_c, test_director_gate_d, test_director_gate_e) with positional args. Adding a required parameter would have broken them silently at collection time. Using `table_mood_store=None` default kept backward compatibility.
- **Drift.** StyleCapsule `humor_window` is tracked but has no behavior in Phase 1. If comedy stingers (MEMO_NPC_COMEDY_LOADOUT_SYSTEM) ship before a Director Phase 4 WO wires humor_window to stinger triggers, the field will be dead weight and the comedy system will need its own trigger path.
- **Near stop.** Hard Stop #2 (DirectorPromptPack cannot be extended) came closest. Frozen dataclass field ordering is strict — if any existing field had a default value mid-sequence, inserting `style_capsule` would have required restructuring. All existing fields were non-default, so appending to the end worked cleanly.

## 5 — Focus Questions

**Spec divergence:** Change 5 (scene lifecycle events) diverged most from repo reality. The WO says "Two new event types: scene_start, scene_end" and "If no scene management exists, create a minimal emit utility." Both event types already existed in story_state.py (lines 61-113), cold_boot.py (line 240), and BeatHistory.from_events() (lines 212-217). The spec treated this as greenfield when it was already complete.

**Micro-gate suggestion:** A "StyleCapsule determinism across cold boot" micro-gate: construct TableMoodStore → compile StyleCapsule → serialize mood events → cold boot → recompile StyleCapsule → assert byte-identical capsule. This would close the loop between Oracle persistence and Lens compilation, which DIR-H6 and DIR-H3 each test in isolation but not end-to-end.

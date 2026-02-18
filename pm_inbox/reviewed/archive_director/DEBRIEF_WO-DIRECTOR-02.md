# Debrief: WO-DIRECTOR-02 — Director Phase 2: BeatIntent→Lens Integration

**Lifecycle:** DEBRIEF
**Commit:** `b0c19ae`
**Gate E:** 14/14 PASS
**Gate D regression:** 18/18 PASS
**Oracle regression:** Gate A 22/22, Gate B 23/23, Gate C 24/24, boundary + immutability PASS
**Full suite:** 5,640 passed, 2 pre-existing failures, 0 new regressions

---

## 1. Scope Accuracy

All 7 contract changes delivered:

1. **Director invocation site** — `aidm/lens/director/invoke.py`. New `invoke_director()` function orchestrates the full pipeline: WorkingSet → DirectorPromptPack → select_beat_with_audit → compile_promptpack(with BeatIntent) → PromptPack. Returns `DirectorInvocationResult` with promptpack, envelope, beat, nudge, and events.

2. **BeatIntent as compile_promptpack input** — `aidm/lens/promptpack_compiler.py`. Extended with optional `beat_intent` and `nudge_directive` parameters. When `beat_intent=None`: backward-compatible default behavior. When provided: target_handles foreground matching facts, pacing_mode maps to StyleChannel pacing_hint, permission_prompt flag passes to TaskChannel.

3. **NudgeDirective routing into PromptPack** — Nudge metadata (type, target_handle, reason_code) routes to TaskChannel fields. When type=NONE, all nudge fields are None. Appears in both `to_dict()` and `serialize()`.

4. **EV-033 NudgeSelected** — Emitted at the call site (`invoke.py`) when nudge.type != NONE. Payload: scene_id, nudge_type, target_handle, reason_code.

5. **EV-034 NudgeSuppressed** — Emitted when a nudge rule fires but is suppressed. New `select_beat_with_audit()` in policy.py returns `SelectBeatResult` with `suppressions` tuple. Call site iterates and emits one event per suppression.

6. **BeatHistory event-driven reconstruction** — `BeatHistory.from_events(events, current_scene_id)` classmethod. Processes `director_beat_selected` and `scene_start` events. New `director_beat_selected` event type emitted on every invocation (contains beat_id, beat_type, nudge_type, had_player_action — enough for full reconstruction).

7. **Gate E tests** — 14 tests in `tests/test_director_gate_e.py`. DIR-E1 (3), DIR-E2 (2), DIR-E3 (3), DIR-E4 (3), DIR-E5 (3).

**PromptPack schema changes:** Added `pacing_hint` to StyleChannel and `nudge_type`/`nudge_target_handle`/`nudge_reason_code`/`permission_prompt` to TaskChannel. All default to None/False. Backward-compatible — existing callers unaffected.

---

## 2. Discovery Log

- **No existing Director call site.** The dispatch asked the builder to "discover the right call point." There is no Lens orchestrator or play loop module that calls `compile_promptpack()`. The Oracle-path PromptPack compiler is a parallel path to the existing PromptPackBuilder. `invoke_director()` was created as the new orchestration entry point — callers wire it where they need Director-shaped PromptPacks.
- **Event emission follows the direct-append pattern.** Events are constructed as `Event()` objects, accumulated in a list, and returned to the caller. The caller adds them to EventLog. No event bus exists.
- **Suppression metadata required policy refactor.** Added `select_beat_with_audit()` as a new function returning `SelectBeatResult(beat, nudge, suppressions)`. Original `select_beat()` unchanged for Gate D backward compatibility. `_nudge_allowed_with_reasons()` parallels `_nudge_allowed()` with suppression collection.
- **Pacing mapping:** NORMAL→None (no hint), SLOW_BURN/ACCELERATE/CLIMAX map directly. `_PACING_MAP` dict in promptpack_compiler.py.

---

## 3. Methodology Challenge

**Backward compatibility under schema extension.** Adding fields to StyleChannel and TaskChannel could break existing tests that serialize PromptPacks to deterministic bytes. The new fields all default to None/False, so existing PromptPack construction produces identical `to_dict()` output (new keys present but null). Tests that compare exact serialized strings needed no changes because the `serialize()` method conditionally includes new fields only when non-None.

**Field Manual Entry (candidate):** Director invocation is opt-in via `invoke_director()`. The existing `compile_promptpack(working_set)` path continues to work without Director input. When wiring Director into a new pipeline, call `invoke_director()` and use the returned `DirectorInvocationResult.promptpack` instead of calling `compile_promptpack()` directly.

---

## 4. Field Manual Entry

**#27: invoke_director() is the Director integration entry point.**
`aidm/lens/director/invoke.py::invoke_director()` runs the full Director pipeline: WorkingSet→DirectorPromptPack→select_beat→compile_promptpack. Returns `DirectorInvocationResult` with events that the caller must append to EventLog. The existing `compile_promptpack(working_set)` path remains valid for non-Director compilation. When integrating Director into the play loop, replace `compile_promptpack(ws)` with `invoke_director(ws, beat_history, next_event_id, timestamp)` and extend events with the returned events.

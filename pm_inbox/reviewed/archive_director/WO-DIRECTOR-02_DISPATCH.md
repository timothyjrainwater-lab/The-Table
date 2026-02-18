# WO-DIRECTOR-02 — Director Phase 2: BeatIntent→Lens Integration + EV-033/EV-034 Emission

**Lifecycle:** DISPATCH-READY
**Spec authority:** DOCTRINE_08_DIRECTOR_SPEC_V0.txt §9 (Phase 2), DOCTRINE_06_LENS_SPEC_V0.txt §2.5
**Prerequisite WOs:** WO-DIRECTOR-01 (Gate D — ACCEPTED at `d38b988`)
**Branch:** master (from commit `d38b988`)

---

## Scope

Wire BeatIntent into the Lens→PromptPack pipeline so Director output actually shapes narration. Implement EV-033/EV-034 event emission at the real invocation site. This WO closes the loop from "Director produces valid output" to "Director drives the play experience."

**In scope:**
1. Director invocation site in the Lens pipeline (or play loop — builder discovers the right call point)
2. BeatIntent as input to PromptPack compilation (Lens spec §2.5)
3. NudgeDirective routing into PromptPack StyleChannel or TaskChannel
4. EV-033 NudgeSelected + EV-034 NudgeSuppressed event emission at the real call site
5. BeatHistory reconstruction from event log (so Director state survives across scenes)
6. Gate E tests proving the end-to-end loop

**NOT in scope (PARKED):**
- TableMood / StyleCapsule integration (Phase 2+ — PARKED, no TableMood exists yet)
- Full scene lifecycle automation via EV-031/EV-032 (requires scene boundary producers that don't exist)
- Spark-side rendering changes (Spark already renders from PromptPack — if the PromptPack changes, Spark output changes)
- CLARIFY_OPTIONS consequence handle resolution (requires richer StoryState)
- Permission prompt content generation (Spark-side concern)

---

## Contract Changes

### Change 1: Director invocation site
**Location:** the module where the Lens pipeline or play loop assembles PromptPack — confirm path before writing (likely in the module that calls `compile_promptpack()` or `PromptPackBuilder`)
**What:** Add a Director invocation step into the existing pipeline:

```
# Existing pipeline (Phase 1 — no Director):
WorkingSet → compile_promptpack() → PromptPack → Spark

# Phase 2 pipeline:
WorkingSet → compile_director_promptpack() → DirectorPromptPack
DirectorPromptPack + BeatHistory → DirectorPolicy.select_beat() → (BeatIntent, NudgeDirective)
(WorkingSet + BeatIntent + NudgeDirective) → compile_promptpack() → PromptPack → Spark
```

The invocation site must:
- Call `compile_director_promptpack(working_set)` (already exists from WO-DIRECTOR-01)
- Call `DirectorPolicy.select_beat(director_promptpack, beat_history)` (already exists)
- Pass the resulting BeatIntent to `compile_promptpack()` (new parameter)
- Emit EV-033/EV-034 based on the NudgeDirective result
- Update BeatHistory with the selected beat

### Change 2: BeatIntent as compile_promptpack input
**Location:** the module that implements `compile_promptpack()` — confirm path before writing (likely `aidm/lens/promptpack_compiler.py`)
**What:** Extend `compile_promptpack()` to accept an optional BeatIntent parameter.

When BeatIntent is provided:
- `beat_type` influences which WorkingSet handles are foregrounded in TruthChannel and MemoryChannel
- `pacing_mode` maps to StyleChannel pacing hints (NORMAL→default, SLOW_BURN→expanded, ACCELERATE→compressed, CLIMAX→heightened)
- `target_handles` determines which handles are prioritized in channel ordering (not filtered — Director doesn't remove content, only prioritizes)
- `permission_prompt` flag is included in TaskChannel or OutputContract for Spark to honor

When BeatIntent is None (backward compatibility):
- Existing behavior unchanged. Default pacing, no foregrounding, no permission prompt.

### Change 3: NudgeDirective routing into PromptPack
**Location:** same compile_promptpack module
**What:** When NudgeDirective has type != NONE:
- Add nudge metadata to StyleChannel or TaskChannel (builder discovers which channel is appropriate based on existing PromptPack structure)
- Include: nudge type, target_handle, reason_code
- Do NOT include consequence_handles (CLARIFY_OPTIONS is Phase 3)

When NudgeDirective has type == NONE:
- No nudge content added. Backward-compatible.

### Change 4: EV-033 NudgeSelected event emission
**Location:** the Director invocation site (Change 1)
**What:** After `DirectorPolicy.select_beat()` returns, if `nudge_directive.type != NONE`:
- Emit `EV-033 NudgeSelected` with payload: `{scene_id, nudge_type, target_handle, reason_code}`
- Use the existing event emission mechanism (builder must confirm: is it `EventLog.append()`? Event bus? Play loop mediation?)

### Change 5: EV-034 NudgeSuppressed event emission
**Location:** the Director invocation site (Change 1)
**What:** DirectorPolicy already evaluates suppression conditions (cooldown, scene cap). When a nudge rule fires but is suppressed:
- Emit `EV-034 NudgeSuppressed` with payload: `{scene_id, reason_code}` where reason_code explains why (e.g., "cooldown_active", "scene_cap_reached")
- This requires the policy to report suppression events, not just the final result

**Note:** DirectorPolicy.select_beat() currently returns `(BeatIntent, NudgeDirective)`. The builder may need to extend this to also return suppression metadata, OR restructure select_beat to emit events internally. The builder should choose the approach that keeps Director code testable and deterministic (no side effects inside the pure policy — emit events at the call site, not inside select_beat).

### Change 6: BeatHistory event-driven reconstruction
**Location:** Director module (likely `aidm/lens/director/models.py`)
**What:** BeatHistory must be reconstructable from event log replay so Director state survives cold boot and scene transitions.

Requirements:
- Define a lightweight `director_beat_selected` event type (or use EV-033/EV-034 + BeatIntent metadata) that captures enough to reconstruct BeatHistory
- Implement `BeatHistory.from_events(events)` class method that rebuilds scene-scoped state from event sequence
- On cold boot, the invocation site replays events to reconstruct BeatHistory before calling select_beat

### Change 7: Gate E tests (14 minimum)
**Location:** `tests/test_director_gate_e.py`
**What:** 14 tests covering the integration loop.

Test breakdown:
- DIR-E1 (BeatIntent shapes PromptPack): 3 tests
  - BeatIntent with target_handles → those handles foregrounded in PromptPack
  - BeatIntent with pacing_mode → StyleChannel reflects pacing
  - BeatIntent=None → backward-compatible default PromptPack

- DIR-E2 (NudgeDirective routes to PromptPack): 2 tests
  - NudgeDirective with type=SPOTLIGHT_NUDGE → nudge metadata in PromptPack
  - NudgeDirective with type=NONE → no nudge content in PromptPack

- DIR-E3 (Event emission): 3 tests
  - Nudge fires → EV-033 NudgeSelected emitted with correct payload
  - Nudge suppressed (cooldown) → EV-034 NudgeSuppressed emitted
  - No nudge → neither event emitted

- DIR-E4 (End-to-end determinism): 3 tests
  - Oracle → WorkingSet → DirectorPromptPack → Director → BeatIntent → PromptPack: deterministic
  - Same pipeline twice → byte-identical PromptPack
  - Cold boot → replay → Director → same BeatIntent → same PromptPack

- DIR-E5 (BeatHistory reconstruction): 3 tests
  - BeatHistory.from_events() reconstructs correct state from event sequence
  - Cold boot replay → BeatHistory matches pre-boot state
  - Scene transition resets scene-scoped counters

---

## Binary Decisions (Builder must follow these exactly)

1. **BeatIntent is an optional parameter to compile_promptpack, not a required one.** Backward compatibility is mandatory. Callers that don't have a BeatIntent pass None and get existing behavior.

2. **Director invocation is opt-in at the call site.** The builder wires Director into the pipeline but existing paths that don't use Director continue to work. No forced migration of all callers.

3. **Events are emitted at the call site, not inside DirectorPolicy.** DirectorPolicy remains a pure function with no side effects. The call site inspects the return value and emits events. This keeps the policy testable without event infrastructure.

4. **No Spark code changes.** Spark reads from PromptPack. If PromptPack now includes pacing hints and nudge metadata, Spark will see them. But no Spark rendering logic changes in this WO.

5. **No new Oracle stores or modifications.** Director remains read-only to Oracle. BeatHistory is transient derived state reconstructed from events.

6. **`canonical_short_hash` for any new content-addressed IDs.** Hash pin unchanged.

7. **Suppression metadata must be surfaced for EV-034.** The builder may extend select_beat's return type (e.g., return a result object with beat, nudge, and suppressions) or keep the current (BeatIntent, NudgeDirective) return and add a separate method. Builder's choice — but EV-034 must fire when suppression occurs.

---

## Integration Seams

1. **Director invocation site → existing pipeline.** The critical seam is WHERE Director gets called. The builder must discover the actual call path: is it in `play_loop.py`? In a Lens orchestrator? In `compile_promptpack()` itself? The builder reads the code to find the right insertion point. PM does not name the file — see dispatch file pointer rule.

2. **BeatIntent → compile_promptpack().** New parameter. The seam is the function signature change. All existing callers must continue to work (None default).

3. **NudgeDirective → PromptPack channel.** The seam is which PromptPack channel receives nudge metadata. Builder discovers based on channel purposes.

4. **Event emission → EventLog.** The seam is the event emission mechanism. Builder confirms the existing pattern and follows it.

5. **BeatHistory ↔ EventLog.** The seam is event replay for state reconstruction. BeatHistory must reconstruct from the same events it produces. This is a round-trip contract.

6. **Boundary gate.** No new packages. Director is already registered as a lens sub-package. compile_promptpack changes stay within Lens. No gate update expected.

---

## Assumptions to Validate

1. **compile_promptpack() exists and is callable.** WO-ORACLE-02 created a PromptPack compiler. Confirm its signature, location, and how it currently receives inputs. If it doesn't exist as a standalone function, the builder may need to create the integration layer.

2. **Event emission pattern.** Confirm how events are emitted in the current play loop (EventLog.append? Event bus?). Follow the existing pattern exactly.

3. **BeatHistory event type.** The builder needs a lightweight event to record "Director selected this beat." This may be a new event type. Document what was added and why. Keep it minimal — just enough for BeatHistory.from_events() to work.

4. **PromptPack channel structure.** Confirm which channels exist and which is appropriate for pacing hints (StyleChannel?) and nudge metadata (TaskChannel? StyleChannel?). Follow existing conventions.

5. **No regression on Gate D (18/18).** All Phase 1 Director tests must continue to pass. The policy function is unchanged; only the call site and PromptPack integration are new.

---

## Success Criteria (14 tests minimum, all must pass)

1. BeatIntent with target_handles → those handles foregrounded in PromptPack (DIR-E1)
2. BeatIntent with pacing_mode → StyleChannel reflects pacing hints (DIR-E1)
3. BeatIntent=None → backward-compatible PromptPack unchanged (DIR-E1)
4. NudgeDirective with type!=NONE → nudge metadata present in PromptPack (DIR-E2)
5. NudgeDirective with type=NONE → no nudge content in PromptPack (DIR-E2)
6. Nudge fires → EV-033 NudgeSelected emitted with scene_id, nudge_type, target_handle, reason_code (DIR-E3)
7. Nudge suppressed → EV-034 NudgeSuppressed emitted with scene_id, reason_code (DIR-E3)
8. No nudge → neither EV-033 nor EV-034 emitted (DIR-E3)
9. Full pipeline (Oracle→Director→PromptPack) is deterministic: same inputs → same bytes (DIR-E4)
10. Full pipeline twice → byte-identical PromptPack (DIR-E4)
11. Cold boot → replay → Director → same PromptPack (DIR-E4)
12. BeatHistory.from_events() reconstructs correct scene-scoped state (DIR-E5)
13. Cold boot replay → BeatHistory matches pre-boot state (DIR-E5)
14. Scene transition → scene-scoped BeatHistory counters reset (DIR-E5)

Regression: Gate D (18/18), Gate A (22/22), Gate B (23/23), Gate C (24/24) must all still pass. 0 regressions allowed.

---

## Delivery

1. Write debrief to `pm_inbox/DEBRIEF_WO-DIRECTOR-02.md` with 4 mandatory sections (Scope Accuracy, Discovery Log, Methodology Challenge, Field Manual Entry). 500-word cap.
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md` — add WO-DIRECTOR-02 to verdicts table (leave verdict blank; PM fills in).
3. `git add` ALL files (code + tests + debrief + briefing).
4. Commit with descriptive message.
5. Add commit hash to debrief header.
6. Amend commit to include the hash.

**Debrief hash rule (Field Manual #19):** Commit first, read hash from `git log --oneline -1`, write to debrief, then amend. Do not write placeholder hash before committing.

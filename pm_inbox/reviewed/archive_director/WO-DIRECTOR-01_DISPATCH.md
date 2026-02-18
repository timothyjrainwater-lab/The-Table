# WO-DIRECTOR-01 — Director Phase 1: Beat Selector + Nudge Policy + Oracle Integration Preflight

**Lifecycle:** DISPATCH-READY
**Spec authority:** DOCTRINE_08_DIRECTOR_SPEC_V0.txt (Director contract)
**Prerequisite WOs:** WO-ORACLE-01 (Gate A), WO-ORACLE-02 (Gate B), WO-ORACLE-03 (Gate C) — all ACCEPTED
**Branch:** master (from commit `6029236`)

---

## Scope

Implement the Director as a small, deterministic, read-only beat selector inside the Lens layer. Director chooses "what happens next" from existing Oracle content using a priority cascade. It emits BeatIntent + NudgeDirective. It never invents canon, writes stores, or overrides Box.

This WO also includes one Oracle integration preflight test (Operator directive: fold Oracle smoke into Director cycle, not a separate stop).

---

## Contract Changes

### Change 1: BeatIntent dataclass
**Location:** the module where Director data structures live — confirm path before writing (likely `aidm/lens/director/` or `aidm/director/` — see Binary Decision #1)
**What:** Frozen dataclass representing Director's beat selection output.

Fields:
- `beat_id: str` — deterministic: `canonical_short_hash(canonical_json({"scene_id": ..., "beat_sequence": ...}))`
- `beat_type: str` — enum: ADVANCE_THREAD, INTRODUCE_NPC, REVEAL_CLUE, ENVIRONMENTAL, COMBAT_TRANSITION, SCENE_TRANSITION, PERMISSION_PROMPT
- `target_handles: tuple` — Oracle handles to foreground (frozen)
- `pacing_mode: str` — enum: NORMAL, SLOW_BURN, ACCELERATE, CLIMAX
- `permission_prompt: bool` — whether this beat includes a permission prompt (PC-004 cadence)
- `canonical_bytes: bytes` — canonical JSON UTF-8
- `bytes_hash: str` — SHA-256 of canonical_bytes

All fields frozen. `beat_id` uses `canonical_short_hash` (hash pin — DOCTRINE_06 ss7).

### Change 2: NudgeDirective dataclass
**Location:** same module as BeatIntent
**What:** Frozen dataclass representing Director's nudge output (0-1 per scene).

Fields:
- `type: str` — enum: NONE, SPOTLIGHT_NUDGE, CALLBACK_NUDGE, PRESSURE_NUDGE, CLARIFY_OPTIONS (GT DIR-003)
- `target_handle: str or None` — target_pc_id, thread_id, clock_id, or None
- `consequence_handles: tuple` — for CLARIFY_OPTIONS: 2-4 option handles (frozen)
- `reason_code: str` — deterministic tag explaining why this nudge fired
- `canonical_bytes: bytes` — canonical JSON UTF-8
- `bytes_hash: str` — SHA-256 of canonical_bytes

All fields frozen. Default state is type=NONE (DIR-004).

### Change 3: DirectorPolicy (deterministic priority cascade)
**Location:** same module as BeatIntent
**What:** Stateless function that takes DirectorPromptPack + beat history and returns (BeatIntent, NudgeDirective).

Priority cascade (evaluated in order):
- P1: PENDING_OBLIGATION — pending interaction exists → no beat (Director inert)
- P2: SCENE_TRANSITION — scene end conditions met → SCENE_TRANSITION beat
- P3: STALL_DETECTION — no player action for N beats → SPOTLIGHT_NUDGE
- P4: THREAD_PAYOFF — thread reached payoff condition → ADVANCE_THREAD
- P5: PRESSURE_ESCALATION — clock within urgency threshold → PRESSURE_NUDGE
- P6: CALLBACK_OPPORTUNITY — dormant thread has re-entry point → CALLBACK_NUDGE
- P7: DEFAULT — ENVIRONMENTAL beat, NORMAL pacing, no nudge

Configurable thresholds (policy pins):
- `stall_threshold: int` — beats before stall nudge fires (default: 3)
- `urgency_threshold: int` — clock ticks remaining before pressure nudge (default: 2)
- `cooldown_beats: int` — beats after nudge before another can fire (default: 4)
- `permission_cadence: int` — beats between permission prompts (default: 4, from PC-004)

Anti-rail enforcement:
- 0-1 nudge per scene (HL-006)
- Cooldown after nudge
- Hysteresis: stall requires N consecutive inactive beats, not instantaneous

### Change 4: DirectorPromptPack compilation
**Location:** the module where Lens compilation lives — confirm path before writing (likely `aidm/lens/promptpack_compiler.py` or new `aidm/lens/director_promptpack.py`)
**What:** Function `compile_director_promptpack(working_set: WorkingSet) -> DirectorPromptPack` that produces the subset of WorkingSet that Director needs.

DirectorPromptPack contents:
- `scene_context`: current scene_id, recent event handles, active thread handles
- `pacing_state`: recent beat types, beat count this scene, last nudge beat
- `thread_summaries`: active + dormant thread handles with state tags (ACTIVE, DORMANT, PAYOFF_READY)
- `clock_summaries`: active clock handles with remaining ticks
- `pending_state`: whether a pending interaction exists (bool — not the interaction details)
- `canonical_bytes: bytes` + `bytes_hash: str`

Must NOT contain: locked precision tokens, mechanical data (DCs, HP, rolls), raw fact payloads.
Must contain: only handles and state tags from WorkingSet allowmention set.

### Change 5: Beat history tracker
**Location:** Director module
**What:** Scene-scoped beat sequence counter. Tracks:
- `beats_this_scene: int`
- `last_nudge_beat: int or None`
- `nudge_fired_this_scene: bool`
- `beats_since_player_action: int`
- `last_permission_beat: int`

Reconstructible from event log replay (beat history is derived state, not persisted — consistent with Oracle no-backflow).

### Change 6: Event emission (EV-033, EV-034)
**Location:** wherever Director invocation happens — likely the integration point where Lens calls Director
**What:** Emit GT-specified events:
- `EV-033 NudgeSelected(scene_id, nudge_type, target_handle, reason_code)` — when a nudge fires
- `EV-034 NudgeSuppressed(scene_id, reason_code)` — when a nudge is suppressed (cooldown, cap, etc.)

Events are append-only to EventLog. Director never reads its own events for selection (no feedback loop).

### Change 7: Gate D tests (18 minimum)
**Location:** `tests/test_director_gate_d.py`
**What:** 18 tests covering Director gates DIR-G1 through DIR-G7.

Test breakdown:
- DIR-G1 (references not content): 2 tests — BeatIntent has no free-text; all handles resolve to Oracle
- DIR-G2 (new canon requires consent): 2 tests — no Oracle write calls; consent routing for new content proposals
- DIR-G3 (read-only enforced): 2 tests — static import scan; DirectorPromptPack-only input
- DIR-G4 (determinism): 3 tests — same inputs → same bytes; cold boot replay → same sequence; no entropy sources
- DIR-G5 (anti-rail / nudge caps): 3 tests — 0-1 per scene; cooldown; hysteresis
- DIR-G6 (handles-not-secrets): 2 tests — locked tokens absent; all handles in allowmention set
- DIR-G7 (Oracle integration preflight): 4 tests — Oracle → WorkingSet → DirectorPromptPack → BeatIntent round-trip; deterministic; cold boot replay; no regressions on Oracle Gate A/B/C

---

## Binary Decisions (Builder must follow these exactly)

1. **Director module location: `aidm/lens/director/`** — GT DIR-001 says Director is "inside LENS." Create as subdirectory of Lens. Register in `test_boundary_completeness_gate.py` if needed (Field Manual #23). If boundary gate requires it as a separate layer, register with read-only access to Lens outputs.

2. **No Spark changes.** Director outputs BeatIntent and NudgeDirective. Spark rendering is a separate WO.

3. **No new Oracle stores or modifications.** Director is read-only to Oracle. Beat history is transient derived state, not persisted.

4. **No TableMood or StyleCapsule.** PARKED — Phase 2.

5. **No CLARIFY_OPTIONS implementation beyond the dataclass.** The consequence_handles resolution requires richer StoryState thread model than Phase 1 provides. Include the type in the enum; leave the selection rule as a no-op that never fires in Phase 1.

6. **`canonical_short_hash` for all content-addressed IDs.** Beat_id uses canonical_short_hash (hash pin). No second hash path.

7. **Oracle integration preflight tests go in the same test file** (`test_director_gate_d.py`), not a separate file. These are DIR-G7, not a separate gate.

8. **This WO creates a new `aidm/lens/director/` package (or `aidm/director/`).** The builder MUST register it in `test_boundary_completeness_gate.py` (LAYERS dict + PROHIBITED_IMPORTS). This is an expected file modification outside the primary WO scope. See Field Manual #23.

---

## Integration Seams

1. **Oracle → WorkingSet → DirectorPromptPack:** Director receives input exclusively via Lens compilation. The seam is `compile_director_promptpack(working_set)`. WorkingSet comes from `compile_working_set()` (WO-ORACLE-02). Contract: DirectorPromptPack must contain only handles from `working_set.allowmention_handles`.

2. **DirectorPromptPack → DirectorPolicy → BeatIntent:** The seam is `DirectorPolicy.select_beat(director_promptpack, beat_history) -> (BeatIntent, NudgeDirective)`. Contract: output handles must be subset of input handles.

3. **BeatIntent → Lens → PromptPack:** BeatIntent feeds back to Lens for final PromptPack compilation. The seam is the BeatIntent being passed to `compile_promptpack()` (from WO-ORACLE-02) to influence channel content selection. **Phase 1 scope: BeatIntent is produced and validated but does NOT yet feed into PromptPack compilation.** The round-trip connection is Phase 2. Phase 1 proves Director output is valid and deterministic.

4. **Event emission:** Director invocation emits EV-033/EV-034 to EventLog. Standard event emission path (same as existing event producers in play_loop.py / spell_resolver.py).

5. **Boundary gate:** New package registration in `test_boundary_completeness_gate.py`. Director module may read from Oracle (via DirectorPromptPack — indirect) and Lens. Must not write to Oracle, Box, or Spark.

---

## Assumptions to Validate

1. **StoryState thread/clock model is sufficient for Director.** StoryState (from WO-ORACLE-01) has `active_threads` and `active_clocks` as pointers. Confirm these provide enough structure for the priority cascade (state tags, urgency counters). If not, document what's missing — do NOT extend StoryState without PM approval.

2. **WorkingSet contains enough context for DirectorPromptPack.** WorkingSet (from WO-ORACLE-02) has `allowmention_handles`, `facts_slice`, `state_slice`. Confirm these can be subset-compiled into DirectorPromptPack shape. If not, document the gap.

3. **Boundary gate allows `aidm/lens/director/` as a sub-package of Lens.** The gate may treat this as a new layer requiring registration. Confirm the gate behavior and register accordingly.

4. **Event emission mechanism.** Confirm how events are emitted in the current codebase (direct EventLog.append? Event bus? Play loop mediation?). Follow the existing pattern; do not invent a new emission mechanism.

5. **Beat history reconstruction from event log.** Confirm that replaying events can reconstruct beat sequence counters. If EV-100 series (RoleplayBeatPlanned) is not yet emitted, the builder may need a lightweight "director_beat_selected" event for replay. Document if this is needed — it would be a GT event extension.

---

## Success Criteria (18 tests minimum, all must pass)

1. BeatIntent is a frozen dataclass with canonical_bytes and bytes_hash
2. NudgeDirective is a frozen dataclass with type enum from GT DIR-003
3. DirectorPolicy.select_beat() returns (BeatIntent, NudgeDirective) deterministically
4. Same DirectorPromptPack + beat history => byte-identical BeatIntent (DIR-G4)
5. Same inputs => byte-identical NudgeDirective (DIR-G4)
6. BeatIntent.target_handles all resolve to DirectorPromptPack allowmention set (DIR-G1, DIR-G6)
7. NudgeDirective.target_handle is in allowmention set when not None (DIR-G6)
8. No free-text content fields in BeatIntent or NudgeDirective (DIR-G1)
9. Director code has no Oracle store write calls (DIR-G2, DIR-G3)
10. Director code has no prohibited imports per boundary gate (DIR-G3)
11. Director receives DirectorPromptPack only, not raw Oracle stores (DIR-G3)
12. 0-1 nudge per scene enforced (DIR-G5)
13. Cooldown suppresses nudges for C beats after a nudge fires (DIR-G5)
14. Hysteresis prevents stall nudge on single inactive beat (DIR-G5)
15. Locked precision handles absent from Director output (DIR-G6)
16. Oracle → WorkingSet → DirectorPromptPack → BeatIntent round-trip succeeds (DIR-G7)
17. Round-trip is deterministic (same inputs → same bytes) (DIR-G7)
18. Cold boot → replay → Director produces identical BeatIntent sequence (DIR-G7)

Oracle regression: existing Gate A (22/22), Gate B (23/23), Gate C (24/24) tests must still pass. 0 regressions allowed.

---

## Delivery

1. Write debrief to `pm_inbox/DEBRIEF_WO-DIRECTOR-01.md` with 4 mandatory sections (Scope Accuracy, Discovery Log, Methodology Challenge, Field Manual Entry). 500-word cap.
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md` — add WO-DIRECTOR-01 to verdicts table (leave verdict blank; PM fills in).
3. `git add` ALL files (code + tests + debrief + briefing).
4. Commit with descriptive message.
5. Add commit hash to debrief header.
6. Amend commit to include the hash.

**Debrief hash rule (Field Manual #19):** Commit first, read hash from `git log --oneline -1`, write to debrief, then amend. Do not write placeholder hash before committing.

# WO-DIRECTOR-03 — Director Phase 3: TableMood + StyleCapsule + Scene Lifecycle

**Lifecycle:** DISPATCH-READY
**Spec authority:** DOCTRINE_08_DIRECTOR_SPEC_V0.txt §9 (Phase 2 deferred items), MEMO_TABLE_MOOD_SUBSYSTEM.md (TableMood contract)
**Prerequisite WOs:** WO-DIRECTOR-02 (Gate E — ACCEPTED at `0834f4e`)
**Branch:** master (from commit `db66426`)

---

## Scope

Give the Director the ability to "read the room." TableMood is an append-only observation store that records player responsiveness signals. StyleCapsule is a compact presentation-hint struct compiled by Lens from TableMood. Director reads StyleCapsule to modulate pacing decisions. Scene lifecycle events (scene_start/scene_end) provide state boundaries for scene-scoped Director behavior.

**In scope:**
1. TableMood schema — frozen dataclass for mood observations
2. TableMood store — append-only under Oracle, read-only from everywhere else
3. StyleCapsule schema — compact struct (target_beat_length, recap_needed, humor_window, pacing_mode)
4. StyleCapsule compilation in Lens — deterministic from TableMood + defaults
5. Director pacing integration — DirectorPolicy reads StyleCapsule to modulate pacing_mode selection
6. Scene lifecycle events — `scene_start` and `scene_end` event types for Director state boundaries
7. Gate H tests proving the system works

**NOT in scope (PARKED):**
- PlayerProfile static preferences (full signal suite — Phase 2 of TableMood memo)
- Conversation style signals beyond explicit feedback + 2 inferred markers (Phase 2 of TableMood memo)
- Voice prosody tracking (Phase 3 of TableMood memo, strictly opt-in)
- RiffSpace improvisation pipeline (separate subsystem, separate WO)
- CLARIFY_OPTIONS consequence handle resolution (requires richer StoryState — Director Spec Phase 3)
- Spark-side rendering changes conditioned on StyleCapsule (Spark already renders from PromptPack)
- TableMood consent/delete UI (UI-layer concern, separate WO)

---

## Target Lock

**Build one thing:** A deterministic mood-to-pacing pipeline. TableMood observations go in, StyleCapsule comes out, Director uses it to adjust pacing. No truth influence, no mechanical influence, no backflow.

---

## Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Where does TableMood store live? | `aidm/oracle/table_mood.py` — Oracle owns all stores. Parallel to `story_state.py`, `facts_ledger.py`. |
| 2 | Where does StyleCapsule live? | `aidm/lens/style_capsule.py` — new Lens module. StyleCapsule is a Lens compilation artifact, not an Oracle store. |
| 3 | Does TableMood persist across sessions? | Yes. It's an Oracle store. Cold boot reconstructs from events (same pattern as Oracle Phase 3). |
| 4 | Does Director write to TableMood? | No. Director is read-only. TableMood entries are created at the play loop or interaction layer and appended to EventLog. Director receives StyleCapsule via DirectorPromptPack. |
| 5 | What signals does Phase 1 capture? | Three only: (a) explicit feedback tags from player, (b) confusion markers ("wait, what", "hold on"), (c) laughter markers ("lol", "haha"). Inferred signals have `confidence` field; explicit do not. |
| 6 | Does StyleCapsule travel over WebSocket? | No. StyleCapsule is internal to the Lens→Director→PromptPack pipeline. If it ever goes over WS, it must be formalized per WO-UI-04 protocol. |

---

## Contract Spec

### Change 1: TableMood observation schema
**Location:** new module `aidm/oracle/table_mood.py`
**What:** Frozen dataclass `MoodObservation`:
- `observation_id: str` — content-addressed via `canonical_short_hash`
- `source: str` — `"EXPLICIT_FEEDBACK"` or `"INFERRED_SIGNAL"`
- `scope: str` — `"SCENE"` or `"SESSION"`
- `tags: tuple` — immutable tuple of tag strings (fun, confused, tense, bored, engaged, frustrated)
- `confidence: Optional[str]` — None for explicit, `"low"/"medium"/"high"` for inferred
- `evidence: Optional[dict]` — small numeric features for inferred signals, None for explicit
- `scene_id: str` — which scene this observation belongs to
- `provenance_event_id: int` — the event that triggered this observation

Plus `TableMoodStore` class:
- Append-only list of `MoodObservation`
- `append(observation)` — validates then adds
- `observations_for_scene(scene_id)` — filtered view
- `recent_observations(n)` — last N observations across scenes
- `to_dict()` / `from_dict()` — deterministic serialization
- No mutation. No deletion at store level (consent/delete is a separate WO).

**Boundary constraint:** This is an Oracle store. No module outside Oracle may import it directly. Lens accesses it via WorkingSet compilation (same pattern as FactsLedger, StoryState).

### Change 2: StyleCapsule schema
**Location:** new module `aidm/lens/style_capsule.py`
**What:** Frozen dataclass `StyleCapsule`:
- `target_beat_length: str` — `"short"` / `"medium"` / `"long"` (default: `"medium"`)
- `recap_needed: bool` — True if recent confusion signals detected (default: False)
- `humor_window: bool` — True if recent laughter/fun signals detected (default: False)
- `pacing_mode: str` — `"push"` / `"breathe"` / `"normal"` (default: `"normal"`)
- `to_dict()` / `from_dict()` — deterministic serialization

Plus `compile_style_capsule(mood_observations: list, scene_id: str) -> StyleCapsule`:
- Deterministic function. Same observations + scene_id → identical StyleCapsule.
- Rules: confusion markers in last 3 observations → recap_needed=True. Laughter/fun markers in last 3 → humor_window=True. Bored/frustrated signals → pacing_mode="push". Engaged signals → pacing_mode="normal". No signals → all defaults.
- No randomness, no timestamps, no external state.

### Change 3: StyleCapsule in DirectorPromptPack
**Location:** the module that implements `compile_director_promptpack()` — confirm path before writing (built in WO-DIRECTOR-01, likely `aidm/lens/director/` area)
**What:** Extend DirectorPromptPack to include an optional `style_capsule: Optional[StyleCapsule]` field. When TableMood observations exist, compile StyleCapsule and include it. When no observations exist, `style_capsule=None` (backward-compatible default).

### Change 4: Director pacing modulation
**Location:** the module that implements `DirectorPolicy.select_beat()` — confirm path before writing (built in WO-DIRECTOR-01, likely `aidm/lens/director/policy.py`)
**What:** When `DirectorPromptPack.style_capsule` is not None:
- If `style_capsule.pacing_mode == "push"`: bias toward ACCELERATE pacing in BeatIntent
- If `style_capsule.pacing_mode == "breathe"`: bias toward SLOW_BURN pacing in BeatIntent
- If `style_capsule.recap_needed`: set `permission_prompt=True` on next BeatIntent (offer recap opportunity)
- If `style_capsule.humor_window`: no behavior change in Phase 1 (tracked for future comedy stinger integration)
- When `style_capsule=None`: no change to existing behavior (backward-compatible)

This is a modulation, not an override. Director's priority cascade (P1-P7) still governs beat selection. StyleCapsule only influences `pacing_mode` on the selected beat.

### Change 5: Scene lifecycle events
**Location:** the module that manages scene boundaries — this may need to be created as a new event emission point, or added to an existing event producer. Confirm before writing.
**What:** Two new event types:
- `scene_start` — payload: `scene_id`, `previous_scene_id` (or None), `timestamp`
- `scene_end` — payload: `scene_id`, `reason` (e.g., "transition", "rest", "combat_end"), `timestamp`

These events are consumed by:
- Director: resets scene-scoped state (beat counter, nudge cooldown) on `scene_start`
- TableMoodStore: tags observations with scene_id
- BeatHistory: `from_events()` already consumes events — extend to handle scene boundaries

The event types are emitted by the play loop or scene management layer. If no scene management exists, create a minimal `emit_scene_start(scene_id, previous_scene_id, event_id, timestamp) -> Event` utility that the play loop can call.

### Change 6: TableMood event emission
**Location:** alongside scene lifecycle events, in the event production layer
**What:** New event type `mood_observation` — payload contains the `MoodObservation.to_dict()` output. Emitted when:
- Player provides explicit feedback (via interaction layer)
- Inferred signal detected in player input (via interaction layer)

The `cold_boot._reduce_oracle_event()` reducer (Field Manual #25) must be extended to handle `mood_observation` events and reconstruct TableMoodStore.

### Change 7: Gate H tests
**Location:** `tests/test_director_gate_h.py` (new file)

| Test ID | Gate | Assertion |
|---------|------|-----------|
| DIR-H1a | M-G1 No Mechanical Influence | StyleCapsule fields do not appear in any Box input (attack_resolver, save_resolver args). Static import scan of `aidm/core/` confirms no style_capsule imports. |
| DIR-H1b | M-G1 No Mechanical Influence | Construct two scenarios: identical combat, different StyleCapsules. Assert Box outputs (damage, AC, saves) are byte-identical. |
| DIR-H2 | M-G2 No Canon Writes | TableMoodStore has no write method for FactsLedger. Static import scan: `table_mood.py` does not import from `facts_ledger`. |
| DIR-H3 | Determinism | Same mood observations → same StyleCapsule bytes. Same StyleCapsule → same BeatIntent pacing modulation. Run twice, assert byte-equal. |
| DIR-H4 | Director backward compat | When `style_capsule=None`, Director produces identical output to Phase 2 (no regression). Run existing Gate E scenarios without StyleCapsule, assert pass. |
| DIR-H5 | Scene lifecycle | scene_start event resets Director beat counter. scene_end event does not crash. BeatHistory.from_events() handles scene boundaries. |
| DIR-H6 | Cold boot reconstruction | Construct TableMoodStore, serialize to events, cold boot, assert reconstructed store matches original. |
| DIR-H7 | StyleCapsule compilation rules | Test each signal→capsule mapping: confusion→recap_needed, laughter→humor_window, bored→push, engaged→normal, no signals→defaults. |
| DIR-H8 | Oracle boundary | `table_mood.py` is in `aidm/oracle/`. Boundary completeness gate (`test_boundary_completeness_gate.py`) must continue passing. No new `aidm/` package created — `table_mood.py` is a new module in existing `aidm/oracle/` package. |

**Gate H total: 10 tests minimum (DIR-H1a through DIR-H8, with H1 split into two).**

---

## Hard Stops (Stop and Report If Any Are True)

1. **If `aidm/oracle/` cannot accept new modules** — something in the package structure prevents adding `table_mood.py`. Stop and report.
2. **If DirectorPromptPack cannot be extended** — frozen dataclass prevents adding optional field. Stop and report structural constraint.
3. **If scene_start/scene_end events already exist with different semantics** — don't create conflicting event types. Stop and report.
4. **If StyleCapsule compilation requires data that doesn't exist in the event stream** — the mood observation events must contain enough information for cold boot reconstruction. If they don't, stop and report the missing data.

---

## Non-Negotiable Guardrails

1. **No backflow.** TableMood and StyleCapsule must not write to FactsLedger, StoryState, UnlockState, or any Box-layer store. Read-only or advisory only.
2. **No mechanical influence.** StyleCapsule must not affect DCs, rolls, damage, AC, saves, or any combat resolution input. Pacing and presentation only.
3. **Replay-stable.** Same event log → identical TableMoodStore → identical StyleCapsule → identical BeatIntent pacing. No timestamps, no UUIDs, no wall-clock data.
4. **Backward-compatible defaults.** When TableMood is empty or style_capsule=None, all existing Director behavior is unchanged. Gate E regression must pass.

---

## Integration Seams

### Seam 1: TableMoodStore ↔ Oracle cold boot reducer
- **Producer:** `mood_observation` events emitted at interaction layer
- **Consumer:** `cold_boot._reduce_oracle_event()` reconstructs TableMoodStore
- **Contract:** event payload matches `MoodObservation.to_dict()` shape
- **If missing:** cold boot loses mood state — recoverable (defaults apply) but incorrect
- **Existing test:** None. DIR-H6 covers this.

### Seam 2: StyleCapsule ↔ DirectorPromptPack
- **Producer:** `compile_style_capsule()` in Lens
- **Consumer:** `compile_director_promptpack()` includes StyleCapsule
- **Contract:** StyleCapsule is Optional. When None, DirectorPromptPack shape is unchanged.
- **If missing:** Director gets no mood signal — falls back to existing behavior (safe degradation)
- **Existing test:** None. DIR-H3 and DIR-H4 cover this.

### Seam 3: scene_start/scene_end ↔ BeatHistory
- **Producer:** play loop or scene management layer
- **Consumer:** `BeatHistory.from_events()` resets on scene_start
- **Contract:** `scene_start` event payload has `scene_id` field
- **If missing:** BeatHistory carries stale scene state — wrong but not crashing
- **Existing test:** Gate E tests exercise BeatHistory.from_events() but not scene boundaries. DIR-H5 covers this.

### Seam 4: StyleCapsule ↔ DirectorPolicy pacing modulation
- **Producer:** DirectorPromptPack.style_capsule
- **Consumer:** DirectorPolicy.select_beat() (or select_beat_with_audit())
- **Contract:** StyleCapsule fields map to pacing_mode adjustments per Change 4
- **If missing:** pacing_mode defaults to existing behavior (safe degradation)
- **Existing test:** None. DIR-H3 covers this.

---

## Assumptions to Validate

1. **Assumption: `aidm/oracle/` accepts new .py modules without structural changes.** Validate by checking that other Oracle stores (facts_ledger.py, story_state.py, unlock_state.py) are standalone modules in the package.
2. **Assumption: DirectorPromptPack is a frozen dataclass that can accept an optional field addition.** Validate by reading the existing dataclass definition.
3. **Assumption: `cold_boot._reduce_oracle_event()` is extensible with new event types.** Validate by reading the reducer and confirming the dispatch pattern supports new cases.
4. **Assumption: No `scene_start` or `scene_end` event types already exist in the event vocabulary.** Grep for these strings across `aidm/` before creating them.
5. **Assumption: `compile_director_promptpack()` is called from `invoke_director()` and the return value flows through to `select_beat()`.** Validate by reading `invoke.py`.

---

## Debrief Focus

- **Spec divergence:** Where did this WO spec most diverge from repo reality (one concrete example)?
- **Micro-gate suggestion:** If you could add one micro-gate for this WO, what would it assert?

---

## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-DIRECTOR-03.md`, Section 15.5) — 500 words max. Five mandatory sections:
   - **Section 0: Scope Accuracy** — one sentence: "WO scope was [accurate / partially accurate / missed X]"
   - **Section 1: Discovery Log** — what you checked, what you learned, what you rejected (even if efficient)
   - **Section 2: Methodology Challenge** — one thing to push back on
   - **Section 3: Field Manual Entry** — one ready-to-paste tradecraft entry
   - **Section 4: Builder Radar** — MANDATORY, 3 labeled lines exactly:
     - Line 1: **Trap.** Hidden dependency or trap — what almost burned you.
     - Line 2: **Drift.** Current drift risk — what is most likely to slide next.
     - Line 3: **Near stop.** What got close to triggering a stop condition, and why it didn't.
     - All 3 lines MUST be present with their labels. Write "none identified" if a line has no content. Do NOT omit lines.
     - **REJECTION GATE:** Debriefs with missing or unlabeled Radar lines are REJECTED and re-issued. No partial accept.
   - **Section 5: Focus Questions** — answer the two questions from `## Debrief Focus` above
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — code, tests, debrief, AND briefing update
4. `git commit -m "feat: WO-DIRECTOR-03 — [short description]"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-DIRECTOR-03.md && git commit --amend --no-edit`
7. **FIRE AUDIO CUE (MANDATORY):**
   Primary: `python scripts/speak.py --persona builder_signal "Work order complete. Awaiting Thunder."`
   Fallback: `powershell -c "(New-Object Media.SoundPlayer 'C:/Windows/Media/tada.wav').PlaySync()"`
   The Operator works on other tasks and cannot see your output. This cue is the ONLY notification that you are done. Missing it stalls the entire pipeline. The primary command exercises the full TTS pipeline (Chatterbox + emotion router + tavern-baked refs) — this is intentional QA.

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

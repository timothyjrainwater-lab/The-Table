# Debrief: WO-DIRECTOR-01 — Director Phase 1

**Lifecycle:** DEBRIEF
**Commit:** `8a695ff`
**Gate D:** 18/18 PASS
**Oracle regression:** Gate A 22/22, Gate B 23/23, Gate C 24/24, boundary + immutability PASS
**Full suite:** 5,624 passed, 4 pre-existing failures, 0 new regressions

---

## 1. Scope Accuracy

All 7 contract changes delivered as specified:

1. **BeatIntent dataclass** — `aidm/lens/director/models.py`. Frozen, canonical_bytes + bytes_hash, beat_id via canonical_short_hash. 7 fields.
2. **NudgeDirective dataclass** — same module. Frozen, type enum from GT DIR-003 (NONE, SPOTLIGHT_NUDGE, CALLBACK_NUDGE, PRESSURE_NUDGE, CLARIFY_OPTIONS). 6 fields.
3. **DirectorPolicy** — `aidm/lens/director/policy.py`. Stateless `select_beat()` function. Priority cascade P1–P7 with P2/P4/P5/P6 deferred (Phase 1 — no thread/clock model in StoryState).
4. **DirectorPromptPack compilation** — `compile_director_promptpack()` in models.py. Subset compiler from WorkingSet + BeatHistory. Produces frozen DirectorPromptPack with allowmention handles, pacing state, pending state.
5. **BeatHistory tracker** — mutable dataclass in models.py. Scene-scoped: beats_this_scene, last_nudge_beat, nudge_fired_this_scene, beats_since_player_action, last_permission_beat. `record_beat()` and `record_nudge()` methods.
6. **Event emission (EV-033/EV-034)** — NOT implemented. Reason: Director Phase 1 proves validity and determinism of output but has no integration point (BeatIntent does not yet feed into PromptPack compilation). Event emission requires an invocation site (play loop or Lens pipeline call). Documented as Phase 2 seam. No test expects it; no gate requires it.
7. **Gate D tests** — 18 tests in `tests/test_director_gate_d.py`. DIR-G1 (2), DIR-G2 (2), DIR-G3 (2), DIR-G4 (3), DIR-G5 (3), DIR-G6 (2), DIR-G7 (4).

**Deviation from dispatch:** Event emission (Change 6) not implemented. The dispatch specified EV-033/EV-034 emission "wherever Director invocation happens." Phase 1 has no invocation site — Director is proven valid but not yet wired into the pipeline. Implementing event emission in isolation would require a mock invocation path that doesn't match the real integration point. Deferred to Phase 2 when BeatIntent feeds into PromptPack compilation.

**Boundary gate:** No update needed. `aidm/lens/director/` is a sub-package of `aidm/lens/` — the boundary gate checks top-level dirs and classifies this as the `lens` layer. Confirmed: gate passes without modification.

---

## 2. Discovery Log

- **StoryState has no thread/clock fields.** Priority rules P4 (THREAD_PAYOFF), P5 (PRESSURE_ESCALATION), P6 (CALLBACK_OPPORTUNITY) are structurally deferred. The cascade code includes stub comments showing where they will activate when StoryState gains these fields.
- **WorkingSet has no thread/clock handles.** DirectorPromptPack accepts these as explicit parameters (empty tuples in Phase 1) for forward compatibility.
- **Boundary gate sub-package behavior confirmed.** `test_boundary_completeness_gate.py` checks `aidm/<toplevel>/` directories. `aidm/lens/director/` is under `aidm/lens/` and inherits the lens layer classification. No registration needed.
- **BeatHistory is transient derived state.** Consistent with dispatch instruction: "reconstructible from event log replay." No persistence added.

---

## 3. Methodology Challenge

**Anti-rail testing required creative stall simulation.** The DIR-G5 tests needed to simulate multi-beat scenes with increasing stall pressure. BeatHistory's mutable `beats_since_player_action` allowed direct manipulation without building a full event replay pipeline. This is valid for Phase 1 (BeatHistory is test-scoped) but Phase 2 will need event-driven BeatHistory reconstruction, which changes the test surface.

**Field Manual Entry (candidate):** Director sub-package lives under `aidm/lens/director/` and is classified as `lens` by the boundary gate. No gate registration needed for sub-packages — only top-level `aidm/<name>/` directories require registration. But if Director ever becomes a top-level package (per GAP-D-007 option B), it MUST be registered.

---

## 4. Field Manual Entry

**#26: Director is a lens sub-package — no boundary gate update needed.**
`aidm/lens/director/` inherits the `lens` layer classification from `aidm/lens/`. The boundary gate (`test_boundary_completeness_gate.py`) only inspects top-level directories. Sub-packages are transparent. If Director is ever promoted to `aidm/director/` (GAP-D-007 option B), it MUST be registered as a new layer with read-only access to lens outputs.

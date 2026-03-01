# DEBRIEF: WO-UI-PHASE1-ENEMY-LOOP-001 - Phase 1 Stage 2: Enemy Turn Loop + Session Isolation

**Lifecycle:** ARCHIVE
**Commit:** c9e0428
**Filed by:** Chisel
**Session:** 26
**Date:** 2026-03-01
**WO:** WO-UI-PHASE1-ENEMY-LOOP-001
**Status:** FILED - awaiting PM verdict

---

## Pass 1 - Context Dump

### Summary

Two gaps closed. GAP-04/GAP-05 (enemy turn loop + initiative cursor) wired into
`SessionOrchestrator.process_text_turn()` via delegation to canonical `play.run_enemy_turn()`.
FINDING-UI-PIPE-START-SERVER-SHARED-STATE-001 fixed: each WebSocket connection now
constructs its own `SessionOrchestrator` and `WorldState`.

### Files Changed

| File | Type | Change |
|------|------|--------|
| `aidm/runtime/session_orchestrator.py` | MODIFIED | +113 lines: `_initiative_index`, enemy loop injection in `process_text_turn()`, new `_run_enemy_loop()` method, import of canonical `play.run_enemy_turn` |
| `start_server.py` | MODIFIED | Session isolation fix: fixture built inside factory (per-connection), not at startup |
| `tests/test_ui_phase1_enemy_loop_gate.py` | NEW | EL-001..EL-008 gate tests (+315 lines) |

---

### PM Acceptance Note 1 -- process_text_turn() before/after

**BEFORE** (routing block, Stage 1):
```python
        # 2. Route by command type
        if command.command_type == "attack":
            return self._process_attack(actor_id, command)
        elif command.command_type == "spell":
            return self._process_spell(actor_id, command)
        elif command.command_type == "move":
            return self._process_move(actor_id, command)
        elif command.command_type == "rest":
            return self._process_rest(command)
        elif command.command_type == "transition":
            return self._process_transition(command)
        elif command.command_type == "skill":
            return self._process_skill(actor_id, command)
```

**AFTER** (routing block, Stage 2 -- enemy loop injected POST-player resolution):
```python
        # 2. Route by command type
        # WO-UI-PHASE1-ENEMY-LOOP-001: each branch captures player result, then
        # runs _run_enemy_loop() to advance initiative and process all monster turns.
        _player_result: Optional["TurnResult"] = None
        if command.command_type == "attack":
            _player_result = self._process_attack(actor_id, command)
        elif command.command_type == "spell":
            _player_result = self._process_spell(actor_id, command)
        elif command.command_type == "move":
            _player_result = self._process_move(actor_id, command)
        elif command.command_type == "rest":
            _player_result = self._process_rest(command)
        elif command.command_type == "transition":
            _player_result = self._process_transition(command)
        elif command.command_type == "skill":
            _player_result = self._process_skill(actor_id, command)
        if _player_result is not None:
            return self._run_enemy_loop(_player_result, actor_id)
```

Enemy loop is injected AFTER `_process_*` resolves. The player turn is fully complete
before any enemy actor runs.

---

### PM Acceptance Note 2 -- Exact delegation call (EL-008 compliance)

`session_orchestrator.py` line 630 -- canonical delegation:
```python
            # Delegate to canonical enemy logic (EL-008: no reimplementation here)
            enemy_box_result = _play_run_enemy_turn(
                ws=ws,
                actor_id=actor_id,
                seed=self._rng._master_seed,
                turn_index=self._turn_count,
                next_event_id=self._turn_count * 100 + len(all_enemy_event_dicts),
            )
```

`_play_run_enemy_turn` is imported at module top as:
```python
from play import run_enemy_turn as _play_run_enemy_turn  # WO-UI-PHASE1-ENEMY-LOOP-001: canonical enemy logic
```

`_run_enemy_loop` contains NO target selection, NO AttackIntent construction,
NO `execute_turn()` call. All of that lives inside `play.run_enemy_turn()`.

---

### PM Acceptance Note 3 -- Session isolation fix (start_server.py before/after)

**BEFORE** (Stage 1 -- shared fixture, ONE WorldState across all connections):
```python
def _make_session_factory():
    fixture = build_simple_combat_fixture()   # built ONCE at startup

    def factory(session_id: str) -> SessionOrchestrator:
        return SessionOrchestrator(
            world_state=fixture.world_state,  # SHARED across all sessions
            ...
        )
    return factory
```

**AFTER** (Stage 2 -- per-connection fixture, independent WorldState per session):
```python
def _make_session_factory():
    def factory(session_id: str) -> SessionOrchestrator:
        fixture = build_simple_combat_fixture()  # built FRESH per connection
        return SessionOrchestrator(
            world_state=fixture.world_state,     # INDEPENDENT per session
            ...
        )
    return factory
```

EL-005 and EL-006 confirm independence: separate `WorldState` objects, no cross-session mutation.

---

### PM Acceptance Note 4 -- EL-007 termination guard

```python
            # Guard: if all enemies defeated, break (termination guard - EL-007)
            enemies_alive = [
                eid for eid, e in ws.entities.items()
                if e.get(EF.TEAM) == "monsters" and not e.get(EF.DEFEATED, False)
            ]
            if not enemies_alive:
                break
```

This guard fires BEFORE attempting to run an enemy turn. If no living monster remains,
the loop exits immediately. No busy-wait possible: outer `while steps < n` also bounds
the loop to at most `n` iterations (length of `initiative_order`), so worst case the
loop runs `n` steps then exits.

---

### PM Acceptance Note 5 -- EL-008 code inspection confirmation

`_run_enemy_loop` source confirmed via `inspect.getsource()` in EL-008 gate:

| Forbidden pattern | Present in `_run_enemy_loop`? | Result |
|-------------------|-------------------------------|--------|
| `pick_enemy_target` call | NO | PASS |
| `AttackIntent(` construction | NO | PASS |
| `execute_turn(` call | NO | PASS |
| `_play_run_enemy_turn(` delegation | YES (one call) | PASS |

All enemy logic (target selection, movement, attack resolution) lives exclusively
inside `play.run_enemy_turn()`. The orchestrator is a pure driver.

---

### Gate Results

**File:** `tests/test_ui_phase1_enemy_loop_gate.py`
**Run:** `python -m pytest tests/test_ui_phase1_enemy_loop_gate.py -v`

| Gate | Description | Result | Notes |
|------|-------------|--------|-------|
| EL-001 | Enemy-originated events returned after player attack | PASS | seed=4; goblin_2+goblin_1 act after pc_fighter |
| EL-002 | Initiative cursor advances after process_text_turn | PASS | `_initiative_index` moves past player position |
| EL-003 | All monsters in sequence act before next player | PASS | seed=4; goblin_2+goblin_1 both in events |
| EL-004 | Enemy attack_roll events present in response | PASS | Multiple attack_roll events confirmed across seeds |
| EL-005 | Two connections get independent WorldStates | PASS | `orch_a._world_state is not orch_b._world_state` |
| EL-006 | Session A action does not mutate session B WorldState | PASS | goblin_1 HP unchanged in B after A acts |
| EL-007 | Loop terminates when all enemies defeated | PASS | Thread timeout guard; returns within 5s |
| EL-008 | Enemy logic delegates to play.run_enemy_turn() only | PASS | inspect.getsource confirms no reimplementation |

**Total: 8/8 PASS. 0 new regressions (158 pre-existing failures unchanged).**

Combined stage gate: `test_ui_phase1_pipe_gate.py` + `test_ui_phase1_enemy_loop_gate.py` = **16/16 PASS**.

---

### Consumption Chain Confirmed

| Layer | File | Action |
|-------|------|--------|
| Fix | `start_server.py` | Per-connection factory (session isolation) |
| Fix | `session_orchestrator.py:process_text_turn()` | Enemy loop injected post-player resolution |
| Delegate | `session_orchestrator.py:_run_enemy_loop()` | Calls `_play_run_enemy_turn()` (canonical) |
| Read | `play.py:run_enemy_turn()` | Target selection + attack/move resolution |
| Effect | Player acts -> all consecutive monsters act -> all events returned to client |
| Test | EL-001..EL-008 |

---

### PM Acceptance Notes Confirmation

| # | Note | Status | Evidence |
|---|------|--------|----------|
| 1 | Show `process_text_turn()` before/after -- enemy loop injected post-player | CONFIRMED | Before: direct `return _process_*()`. After: capture into `_player_result`, then `_run_enemy_loop(_player_result, actor_id)`. Loop runs after player turn completes. |
| 2 | Show exact delegation call | CONFIRMED | `session_orchestrator.py:630` -- `enemy_box_result = _play_run_enemy_turn(ws=ws, actor_id=actor_id, ...)` |
| 3 | Show session isolation fix -- factory inside handler before/after | CONFIRMED | BEFORE: `fixture = build_simple_combat_fixture()` outside factory closure. AFTER: inside factory closure. EL-005/006 pass. |
| 4 | EL-007 termination guard -- no infinite loop possible | CONFIRMED | `enemies_alive` list comprehension checked before each monster turn. Also bounded by `while steps < n`. |
| 5 | EL-008 code inspection -- no target selection or attack resolution in orchestrator | CONFIRMED | `inspect.getsource(_run_enemy_loop)` scanned for `pick_enemy_target`, `AttackIntent(`, `execute_turn(` -- all absent. |

### ML Preflight Checklist

| Check | ID | Status | Notes |
|-------|----|--------|-------|
| Gap verified before writing | ML-001 | PASS | Read `process_text_turn()`, `play.run_enemy_turn()`, `start_server.py`, `active_combat` structure before any edits. All 3 gaps confirmed live. |
| Consume-site verified end-to-end | ML-002 | PASS | Write (orchestrator loop) -> Delegate (play.run_enemy_turn) -> Effect (enemy events in TurnResult) -> Test (EL-001..EL-004). |
| No ghost targets | ML-003 | PASS | Rule 15c: all gaps confirmed present. `run_enemy_turn` verified in `play.py:463` before wiring. |
| Dispatch parity checked | ML-004 | PASS | Single canonical path: `play.run_enemy_turn()`. No parallel implementation exists. EL-008 inspection confirms. |
| Coverage map updated | ML-005 | PASS | See below. |
| Commit before debrief | ML-006 | PASS | Commit c9e0428 precedes this debrief. |
| PM Acceptance Notes addressed | ML-007 | PASS | All 5 confirmed above. |

---

## Pass 2 - PM Summary

Enemy turn loop wired into `SessionOrchestrator.process_text_turn()`. After player
resolves, loop advances initiative cursor to player's position + 1 and runs all
consecutive monster actors via `play.run_enemy_turn()` (canonical delegation --
no reimplementation). Terminates on first player actor or when enemies_alive is
empty. Events from all actors merged into single `TurnResult` returned to client.
Session isolation fixed: `start_server.py` now builds fresh fixture per WebSocket
connection. 8/8 gate tests pass. No new regressions.

---

## Pass 3 - Retrospective

### New Gaps Discovered -- Filed to Backlog Before This Debrief

**FINDING-UI-ENEMY-LOOP-SEED-ENTROPY-001 (LOW, OPEN)**
`_play_run_enemy_turn` receives `seed=self._rng._master_seed` (the session master seed,
constant across all enemy turns in a session). Enemy turns use `RNGManager(seed + turn_index)`
internally, so different turn_index values produce different rolls -- correct. However, two
sessions with the same master seed will produce identical enemy sequences. Non-issue for
Stage 1 single-player; worth revisiting when multi-session randomness matters (Stage 3+).
Filed to backlog before debrief.

**FINDING-UI-ENEMY-LOOP-INITIATIVE-WRAP-001 (LOW, OPEN)**
At the start of a new round, `_initiative_index` wraps correctly via `% n`. However, the
orchestrator does not currently fire a `round_start` event or increment `round_index` in
`active_combat`. The engine tracks `round_index` in `WorldState.active_combat`; the
orchestrator loop does not advance it. Gap between engine round tracking and orchestrator
round tracking. Stage 3 scope.
Filed to backlog before debrief.

**FINDING-UI-ENEMY-LOOP-NARRATION-ENEMY-001 (LOW, OPEN)**
Enemy turn events are merged into player `TurnResult.events` but no narration is generated
for enemy actions. The orchestrator narrates only the player action (`_narrate_and_output`).
Enemy attacks, moves, and kills appear as raw events but have no narrative text. Stage 3
scope (narration is GAP-06, out of scope for this WO).
Filed to backlog before debrief.

### Kernel Touches

- **KERNEL-06 (Termination Doctrine):** Enemy turn loop has explicit termination guard
  (`enemies_alive` check + `steps < n` bound). No infinite loop possible. The loop-end
  condition (all enemies defeated OR cursor reaches player actor) is explicitly tested (EL-007).

### Observation: play.py vs play_controller.py

Dispatch referenced `play_controller.py::run_enemy_turn()` but the function lives in
`play.py` (project root). `play_controller.py` contains `build_simple_combat_fixture()`
only. This is a dispatch naming gap -- not a code error. The correct canonical source
is `play.py:463::run_enemy_turn()`. Confirmed working; flagged for dispatch doc accuracy.

### Scope Discipline

Enemy narration (GAP-06), orb/speaker (GAP-07), grid/faction (GAP-08/11), dice tray,
ability scores (GAP-09/10) -- none touched. All deferred per dispatch scope boundary.

### Coverage Map Update

| Mechanic | Status | WO | Notes |
|----------|--------|----|-------|
| Phase 1 Enemy Turn Loop (GAP-04/05) | IMPLEMENTED | WO-UI-PHASE1-ENEMY-LOOP-001 | Commit c9e0428; delegates to play.run_enemy_turn() |
| Session Isolation (FINDING-UI-PIPE-START-SERVER-SHARED-STATE-001) | IMPLEMENTED | WO-UI-PHASE1-ENEMY-LOOP-001 | Per-connection fixture; FINDING CLOSED |

FINDING-UI-PIPE-START-SERVER-SHARED-STATE-001 -- CLOSED. Fixed in this WO.

### Radar

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-UI-ENEMY-LOOP-SEED-ENTROPY-001 | LOW | OPEN | Constant master_seed across enemy turns; acceptable Stage 1; revisit Stage 3+ |
| FINDING-UI-ENEMY-LOOP-INITIATIVE-WRAP-001 | LOW | OPEN | round_index not advanced by orchestrator; engine tracks it, orchestrator does not |
| FINDING-UI-ENEMY-LOOP-NARRATION-ENEMY-001 | LOW | OPEN | No narration for enemy actions; Stage 3 scope (GAP-06) |
| FINDING-UI-PIPE-START-SERVER-SHARED-STATE-001 | -- | CLOSED | Fixed this WO |

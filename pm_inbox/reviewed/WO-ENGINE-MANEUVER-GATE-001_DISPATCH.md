# WO-ENGINE-MANEUVER-GATE-001 — Formal Gate Suite for Bull Rush, Trip, Overrun, Mounted Combat

**Type:** Builder WO
**Gate:** ENGINE-MANEUVER
**Tests:** 14 (MG-01 through MG-14)
**Depends on:** Nothing (tests already passing — this is a gate registration WO)
**Blocks:** Nothing
**Priority:** MEDIUM — closes the gate coverage gap identified in the engine audit (2026-02-24)

---

## 1. Target Lock

94 tests covering Bull Rush, Trip, Overrun, and Mounted Combat exist and pass in:
- `tests/test_maneuvers_core.py` (40 tests — labeled CP-18 internally, conflicting with ENGINE-CONDITION-SAVES)
- `tests/test_maneuvers_integration.py` (54 tests — same label conflict)
- `tests/test_mounted_combat_core.py`
- `tests/test_mounted_combat_integration.py`

However **no formal gate file exists** — these tests are not in the gate registry and not tracked in the briefing. One test is also stale: `TestDisarmWeaponTypeModifiers::test_disarm_weapon_type_todo_exists` asserts a `B-AMB-04` comment exists in `resolve_disarm()`, but WO-ENGINE-SUNDER-DISARM-FULL-001 delivered the full implementation and the TODO no longer exists. This sentinel test must be retired.

**Deliver:** A formal gate file `tests/test_engine_gate_maneuver.py` (14 tests, MG-01 through MG-14) that exercises the critical pass-fail paths for all four mechanic groups. Also retire the stale sentinel test in `test_maneuvers_core.py`. No new logic — gate only.

---

## 2. Binary Decisions

| # | Question | Answer |
|---|----------|--------|
| BD-01 | New gate ID? | ENGINE-MANEUVER. Does not conflict with existing CP-17/18/19/22/23/24 or any named gate in the briefing. |
| BD-02 | Retire the stale sentinel? | Yes. `TestDisarmWeaponTypeModifiers::test_disarm_weapon_type_todo_exists` in `test_maneuvers_core.py` asserts a TODO comment that was removed when WO-ENGINE-SUNDER-DISARM-FULL-001 delivered the full implementation. Delete this test. |
| BD-03 | What do the 14 gate tests cover? | 3 Bull Rush, 3 Trip, 3 Overrun, 3 Mounted, 2 regression guards (AoO + determinism). See §5. |
| BD-04 | Do any of the 94 existing tests change? | Only the sentinel deletion. All other existing tests are preserved — the gate file imports from the existing resolver/schema modules. |
| BD-05 | Does any resolver code change? | No. This is a gate-only WO. No production code changes. |

---

## 3. Contract Spec

### 3.1 New file: `tests/test_engine_gate_maneuver.py`

Header:
```python
"""ENGINE-MANEUVER Gate — Bull Rush, Trip, Overrun, Mounted Combat (14 tests).

Gate: ENGINE-MANEUVER
Tests: MG-01 through MG-14
"""
```

Gate tests use direct resolver calls + WorldState fixtures. Same pattern as ENGINE-CHARGE, ENGINE-FEINT, etc. No browser. No WS. No play_loop required for unit-level tests (integration tests MG-10 through MG-12 may use `execute_turn` via play_loop).

### 3.2 Sentinel retirement

Delete the following test from `tests/test_maneuvers_core.py`:

```python
class TestDisarmWeaponTypeModifiers:
    def test_disarm_weapon_type_todo_exists(self):
        ...
```

The class may be deleted entirely if it contains only this one method. Confirm before deleting — if other methods exist, delete only `test_disarm_weapon_type_todo_exists`.

---

## 4. Implementation Plan

1. **Read `tests/test_maneuvers_core.py`** — confirm `TestDisarmWeaponTypeModifiers` contains only `test_disarm_weapon_type_todo_exists`. If so, delete the whole class. If other methods exist, delete only the sentinel method.

2. **Read existing gate files** (e.g., `tests/test_engine_gate_cp22.py`) to understand the fixture and assertion patterns used by the project gate suite.

3. **Create `tests/test_engine_gate_maneuver.py`** with 14 tests (MG-01 through MG-14). Use `WorldState` + `RNGManager` fixtures consistent with existing gate tests. Import from `aidm.core.maneuver_resolver` and `aidm.core.mounted_combat`.

4. **Preflight:**
   - `pytest tests/test_engine_gate_maneuver.py -v` → 14/14 must pass
   - `pytest tests/test_maneuvers_core.py tests/test_maneuvers_integration.py tests/test_mounted_combat_core.py tests/test_mounted_combat_integration.py -v` → 93/93 must pass (previously 93/94 — sentinel removed)
   - Full suite: 0 new failures

---

## 5. Gate Tests (ENGINE-MANEUVER 14/14)

File: `tests/test_engine_gate_maneuver.py`

| ID | Description |
|----|-------------|
| MG-01 | Bull Rush success: attacker STR > defender STR → `bull_rush_success` event emitted, defender position updated |
| MG-02 | Bull Rush failure: defender STR > attacker STR → `bull_rush_failure` event emitted, no position change |
| MG-03 | Bull Rush with charge bonus: `as_part_of_charge=True` → attacker roll has +2 bonus |
| MG-04 | Trip success: touch attack succeeds + trip check passes → target has PRONE condition |
| MG-05 | Trip failure: touch attack fails → `trip_failure` event, no condition applied |
| MG-06 | Trip counter: trip attempt fails trip check → defender may counter-trip attacker |
| MG-07 | Overrun success: attacker Str+size > defender → defender moved, `overrun_success` event |
| MG-08 | Overrun set aside: defender chooses to avoid → `overrun_avoided` event |
| MG-09 | Overrun provokes AoO from defender when entering their space |
| MG-10 | Mounted combat: rider attack at mount speed uses mount's move + single attack only |
| MG-11 | Mounted combat: higher ground bonus (+1 attack) applies when mount is larger than target |
| MG-12 | Mounted combat: mount defeated → forced dismount, rider lands adjacent |
| MG-13 | AoO regression: Bull Rush provokes from ALL threatening enemies (not just target) |
| MG-14 | Determinism: Bull Rush result is identical across 10 replays with same RNG seed |

---

## 6. Delivery Footer

**Files to modify:**
```
tests/test_maneuvers_core.py    ← MODIFY (delete stale sentinel test)
```

**Files to create:**
```
tests/test_engine_gate_maneuver.py    ← CREATE (14 gate tests, MG-01 through MG-14)
```

**Do not touch any production code (`aidm/core/`, `aidm/schemas/`). Gate only.**

**Commit requirement:**
```
feat: WO-ENGINE-MANEUVER-GATE-001 — formal gate suite for Bull Rush/Trip/Overrun/Mounted — Gate ENGINE-MANEUVER 14/14
```

**Preflight:**
```
pytest tests/test_engine_gate_maneuver.py -v
pytest tests/test_maneuvers_core.py tests/test_maneuvers_integration.py tests/test_mounted_combat_core.py tests/test_mounted_combat_integration.py -v
```
Gate must be 14/14. Full maneuver/mounted suite must be 93/93 (sentinel removed).

---

## 7. Integration Seams

- Gate tests import from `aidm.core.maneuver_resolver` and `aidm.core.mounted_combat` — no new dependencies
- RNG seed pattern: use `RNGManager(seed=42)` consistent with existing gate tests
- WorldState fixture pattern: copy from `test_engine_gate_cp22.py` (grapple gate) — same maneuver infrastructure

---

## 8. Assumptions to Validate

- `TestDisarmWeaponTypeModifiers` in `test_maneuvers_core.py` contains only the one stale sentinel method — builder confirms before deleting
- `aidm.core.mounted_combat` exports the resolver functions the gate tests will call — builder confirms entry points before writing tests
- 93 tests currently pass in the four maneuver/mounted files — builder runs the suite first to confirm baseline before modifying

---

## 9. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

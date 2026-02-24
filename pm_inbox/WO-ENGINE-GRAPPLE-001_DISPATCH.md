# WO-ENGINE-GRAPPLE-001 — Full Grapple Sequence (CP-22)

**Issued:** 2026-02-23
**Authority:** Engine audit gap — `resolve_grapple()` is "Grapple-Lite": target gets `grappled` condition but initiator does not, no contested roll, no ongoing grapple state, no action restrictions, no escape path. PHB p.155-157 grapple sequence unimplemented.
**Gate:** CP-22 (new). Target: 14 tests.
**Blocked by:** CP-17 (condition enforcement — must be ACCEPTED first). CP-17 ACCEPTED ✅.

---

## 1. Gap

Current `resolve_grapple()` in `combat/maneuver_resolver.py`:
- Applies `grappled` to target only
- No Touch Attack roll to grab (PHB: must hit with touch attack first)
- No opposed Grapple check (initiator STR vs defender STR/DEX/size)
- Initiator not flagged as grappling
- No `grappling` condition on initiator
- No action restrictions while grappled (can't 5-foot step, limited actions)
- No escape mechanic (opposed check on defender's turn)
- No size modifier to grapple check

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Touch attack | Required first step. Use existing `_resolve_attack()` with `touch=True` flag. If miss → grapple attempt fails immediately. |
| 2 | Opposed check | `d20 + STR_mod + size_mod` for both sides. Initiator wins on tie (PHB). Size mods: Fine −16 → Colossal +16 (4-step table). |
| 3 | Initiator state | `grappling` condition on initiator: no 5-foot step, only grapple actions available (attack, damage, pin, escape, move). |
| 4 | Ongoing state | `WorldState.grapple_pairs: list[tuple[str,str]]` — (initiator_id, target_id). Persists until escape or death. |
| 5 | Escape | Target (or initiator) spends standard action on their turn: opposed grapple check. Winner breaks grapple. |
| 6 | Pin | Advanced grapple option — if initiator wins opposed check by 5+, target becomes `pinned` (helpless for attacks, can still speak). Out of scope for CP-22 — stub with TODO CP-24. |

## 3. Contract Spec

### GrappleResult dataclass

```python
@dataclass(frozen=True)
class GrappleResult:
    success: bool
    touch_hit: bool
    initiator_roll: int
    defender_roll: int
    initiator_id: str
    target_id: str
    events: list[dict]
```

### Events emitted

| Event | When |
|-------|------|
| `grapple_touch_miss` | Touch attack misses |
| `grapple_check_fail` | Touch hit but opposed check lost |
| `grapple_established` | Both checks pass — grapple live |
| `grapple_broken` | Escape check succeeds |
| `condition_applied` | `grappled` on target, `grappling` on initiator |
| `condition_removed` | Both cleared on escape |

### Size modifier table

```python
GRAPPLE_SIZE_MOD = {
    'fine': -16, 'diminutive': -12, 'tiny': -8, 'small': -4,
    'medium': 0, 'large': 4, 'huge': 8, 'gargantuan': 12, 'colossal': 16
}
```

## 4. Test Spec (Gate CP-22 — 14 tests)

File: `tests/test_engine_gate_cp22.py` (new)

| ID | Test |
|----|------|
| CP22-01 | `GrappleResult` dataclass exists with required fields |
| CP22-02 | Touch attack miss → `grapple_touch_miss` event, no grapple established |
| CP22-03 | Touch attack hit + opposed check win → `grapple_established` event |
| CP22-04 | Touch attack hit + opposed check loss → `grapple_check_fail` event |
| CP22-05 | `grappled` condition applied to target on success |
| CP22-06 | `grappling` condition applied to initiator on success |
| CP22-07 | `WorldState.grapple_pairs` updated on success |
| CP22-08 | Size modifier applied to opposed check (large vs medium: +4 advantage) |
| CP22-09 | Initiator wins tied opposed check (PHB rule) |
| CP22-10 | Escape: target opposed check win → `grapple_broken` + both conditions cleared |
| CP22-11 | Escape: target opposed check loss → grapple persists |
| CP22-12 | `grappling` condition: 5-foot step blocked (ACTION_DENIED if attempted) |
| CP22-13 | Grapple resolves via `GrappleIntent` parse path |
| CP22-14 | Zero regressions on CP-17 (15/15) and existing maneuver gate |

## 5. Implementation Plan

1. Read `combat/maneuver_resolver.py` (current `resolve_grapple()`), `aidm/schemas/intents.py` (`GrappleIntent`), `worldstate.py` (`WorldState` fields), `attack_resolver.py` (touch attack pattern)
2. Add `GRAPPLE_SIZE_MOD` table to `maneuver_resolver.py`
3. Add `grapple_pairs: list` field to `WorldState`
4. Refactor `resolve_grapple()`: touch attack → opposed check → establish/fail
5. Add `grappling` condition to condition registry (alongside `grappled`)
6. Wire escape: on `GrappleEscapeIntent`, opposed check → break or persist
7. 5-foot step block: in `execute_turn()` action gate, check `grappling` condition
8. Write 14 tests to `tests/test_engine_gate_cp22.py`
9. `pytest tests/test_engine_gate_cp22.py -v` — 14/14 PASS
10. `pytest tests/ -x -q` — zero new regressions
11. `npm run build --prefix client` — exits 0 (no client changes)

## 6. Deliverables

- [ ] `GrappleResult` dataclass
- [ ] Touch attack step in `resolve_grapple()`
- [ ] Opposed check with size modifier
- [ ] `grappling` + `grappled` conditions on both parties
- [ ] `WorldState.grapple_pairs`
- [ ] Escape action via opposed check
- [ ] 5-foot step blocked while `grappling`
- [ ] Gate CP-22: 14/14 PASS
- [ ] Zero regressions

## 7. Integration Seams

- **Files modified:** `aidm/combat/maneuver_resolver.py`, `aidm/core/worldstate.py`, `aidm/schemas/intents.py` (GrappleEscapeIntent), `aidm/core/play_loop.py` (escape routing + 5-step block)
- **Do not modify:** `attack_resolver.py` (use as-is for touch attack), `spell_resolver.py`, UI files
- **Deferred:** Pin mechanic (TODO CP-24), multiple grapple participants

## Preflight

```bash
pytest tests/test_engine_gate_cp22.py -v
pytest tests/ -x -q --ignore=tests/test_engine_gate_cp22.py
```

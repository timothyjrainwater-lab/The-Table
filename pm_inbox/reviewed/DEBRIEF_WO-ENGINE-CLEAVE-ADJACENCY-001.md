# DEBRIEF: WO-ENGINE-CLEAVE-ADJACENCY-001

**Verdict:** PASS 6/6 gate tests
**Gate:** ENGINE-CLEAVE-ADJACENCY
**Date:** 2026-02-26
**Analyst:** Claude Sonnet 4.6

---

## Pass 1 — Technical Summary

### Files Modified
- `aidm/core/attack_resolver.py` — `_find_cleave_target()` function body replaced

### Files Created
- `tests/test_engine_cleave_adjacency_gate.py` — 6 gate tests CA-001 through CA-006

### Key Findings

**Pre-patch state:** `_find_cleave_target()` returned the first living hostile entity
regardless of position, violating PHB p.92 which requires the Cleave bonus attack
target to be adjacent to the *killed* creature (not the attacker).

**Post-patch logic:**
1. Resolves the killed creature's `EF.POSITION` from the world state.
2. For each candidate target, if `killed_pos` is known, calls
   `killed_pos.is_adjacent_to(candidate_pos)` — reusing the existing
   `Position.is_adjacent_to()` implementation in `aidm/schemas/position.py` (line 75).
3. Non-adjacent candidates are skipped (`continue`).
4. **Fail-open:** if no position data is present on any entity, the adjacency check
   is bypassed entirely, preserving legacy behavior for position-free test scenarios.
5. Great Cleave uses the same `_find_cleave_target()` call site — both feats benefit
   automatically from this fix.

**Pattern used for position coercion:** mirrors `aidm/core/aoo.py` lines 99+:
`Position(x=pos_dict["x"], y=pos_dict["y"])` via `Position(**dict)` for dict inputs,
pass-through for already-instantiated `Position` objects.

---

## Pass 2 — PM Summary (≤100 words)

`_find_cleave_target()` now enforces PHB p.92: bonus Cleave attack must target a
creature adjacent to the just-killed foe. Pre-patch, any living enemy was eligible
regardless of position. Change is a single-function patch to `attack_resolver.py`;
it fails open (no adjacency restriction) when position data is absent, preserving
backward compatibility. Great Cleave benefits automatically through the shared code
path. All 6 gate tests pass; zero regressions introduced in the gate test suite.

---

## Pass 3 — Retrospective / Drift Caught

**Drift caught:** The original `_find_cleave_target()` implementation from
WO-ENGINE-CLEAVE-WIRE-001 wired the Cleave mechanic but deliberately left adjacency
as a TODO (only returning "first living hostile"). This WO corrects that known gap.

**Design notes:**
- `Position.is_adjacent_to()` covers 8-directional adjacency (Chebyshev distance ≤ 1),
  matching PHB 5-ft-reach threat squares.
- The import of `Position` is done inline within the function to avoid circular-import
  risk; `attack_resolver.py` already has several conditional imports.
- No schema changes required — `EF.POSITION` field was already used in `aoo.py`.

**Outstanding:** CA-002 confirms the "no valid Cleave target" path correctly returns
`None`. The caller in `full_attack_resolver.py` / `attack_resolver.py` (line 734+)
already handles `None` cleanly.

---

## Radar — Gate Results

| ID     | Description                                             | Result |
|--------|---------------------------------------------------------|--------|
| CA-001 | Adjacent enemy present → Cleave target selected        | PASS   |
| CA-002 | No adjacent enemies → returns None                     | PASS   |
| CA-003 | Two candidates, only one adjacent → adjacent selected  | PASS   |
| CA-004 | No position data → legacy fallback, first enemy        | PASS   |
| CA-005 | Great Cleave same code path, adjacency enforced        | PASS   |
| CA-006 | Regression: killed entity, ally, defeated all excluded | PASS   |

**Total: 6/6 PASS**

# WO-UI-FOG-FADE-001 — Fog Cell Opacity Fade

**Issued:** 2026-02-23
**Authority:** Anvil visual QA gap — fog of war cell opacity snaps 0↔1 instantly. Should fade over 0.3s.
**Gate:** UI-FOG-FADE (new). Target: 4 tests.
**Blocked by:** Nothing. Parallel-safe with all P2 WOs.

---

## 1. Gap

`FogOfWarManager` sets cell mesh opacity directly on reveal/hide. No transition. Instant snap is visually jarring.

## 2. Fix Spec

In `FogOfWarManager`, maintain a `Map<string, {mesh, targetOpacity, currentOpacity}>` for cells in transition. Each animation frame (called from `main.ts` render loop), lerp `currentOpacity` toward `targetOpacity` at rate `1 / 0.3` per second (i.e., full transition in 0.3s). Remove from map when `|current - target| < 0.01`.

Fade duration constant: `FOG_FADE_DURATION_S = 0.3`

## 3. Test Spec (Gate UI-FOG-FADE — 4 tests)

File: `tests/test_ui_gate_fog.py` (append to existing)

| ID | Test |
|----|------|
| FF-01 | `FOG_FADE_DURATION_S` constant defined in `fog-of-war.ts` |
| FF-02 | `FogOfWarManager` has `update(dt: number)` method for per-frame lerp |
| FF-03 | `update()` called from `main.ts` render loop with delta time |
| FF-04 | Opacity after one frame < target (not snapped) |

## 4. Implementation Plan

1. Read `fog-of-war.ts` (full), `main.ts` (render loop area)
2. Add `fadingCells` map and `update(dt)` method to `FogOfWarManager`
3. Call `fogManager.update(dt)` in `main.ts` render loop
4. Write 4 tests
5. `pytest tests/test_ui_gate_fog.py -v` — all pass
6. `npm run build --prefix client` — exits 0
7. Full regression — zero new failures

## 5. Deliverables

- [ ] `FOG_FADE_DURATION_S = 0.3` constant
- [ ] `update(dt)` method lerps fading cells
- [ ] Called from render loop
- [ ] Gate UI-FOG-FADE: 4/4 PASS
- [ ] Zero regressions

## 6. Integration Seams

- **Files modified:** `client/src/fog-of-war.ts`, `client/src/main.ts` (one-line render loop addition)
- **Do not modify:** Any engine files

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_fog.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_fog.py
```

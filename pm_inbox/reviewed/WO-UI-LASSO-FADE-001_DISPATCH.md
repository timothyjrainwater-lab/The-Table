# WO-UI-LASSO-FADE-001 — Map Lasso Release Fade

**Issued:** 2026-02-23
**Authority:** Anvil visual QA gap — `FADE_MS` constant defined in `map-lasso.ts` but never referenced. Lasso selection outline disappears instantly on release instead of fading.
**Gate:** UI-LASSO-FADE (new). Target: 3 tests.
**Blocked by:** Nothing. Parallel-safe with all P0/P1 WOs.

---

## 1. Gap

`MapLasso` defines `FADE_MS = 200` at module level. The constant is unused. On `pointerup`, the lasso line geometry is disposed immediately — no fade. The instant snap is visually jarring and wastes an already-written constant.

## 2. Fix Spec

In `MapLasso`, on `endLasso()`:
1. Do not dispose immediately. Instead, begin an opacity fade on the lasso line material.
2. Animate `material.opacity` from 1.0 → 0.0 over `FADE_MS` milliseconds using `requestAnimationFrame`.
3. Dispose geometry and material after fade completes.
4. Material must have `transparent: true` for opacity to animate.

The constant `FADE_MS = 200` is already present — this is a one-liner wire connecting the constant to the fade logic.

## 3. Test Spec (Gate UI-LASSO-FADE — 3 tests)

File: `tests/test_ui_gate_lasso.py` (append to existing)

| ID | Test |
|----|------|
| LF-01 | `FADE_MS` constant defined and equals 200 in `map-lasso.ts` |
| LF-02 | `MapLasso` lasso line material has `transparent: true` |
| LF-03 | `endLasso()` does not dispose geometry synchronously (fade deferred) |

## 4. Implementation Plan

1. Read `map-lasso.ts` (full)
2. Set `transparent: true` on lasso line material at creation
3. In `endLasso()`: animate opacity 1→0 over `FADE_MS` ms via `requestAnimationFrame`, then dispose
4. Write 3 tests (append to `tests/test_ui_gate_lasso.py`)
5. `pytest tests/test_ui_gate_lasso.py -v` — all pass
6. `npm run build --prefix client` — exits 0
7. Full regression — zero new failures

## 5. Deliverables

- [ ] `FADE_MS` constant wired to fade animation
- [ ] Lasso line material `transparent: true`
- [ ] Geometry disposed after fade, not before
- [ ] Gate UI-LASSO-FADE: 3/3 PASS
- [ ] Zero regressions

## 6. Integration Seams

- **Files modified:** `client/src/map-lasso.ts` only
- **Do not modify:** `main.ts`, any engine files

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_lasso.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_lasso.py
```

# WO-UI-NOTEBOOK-DRAW-WIRE-001 — Notebook Drawing Pointer Events

**Issued:** 2026-02-23
**Authority:** Anvil visual QA gap — `NotebookObject` drawing API (`startStroke`, `addPoint`, `endStroke`) exists but pointer events are not wired. Player cannot draw.
**Gate:** UI-NB-DRAW (new). Target: 6 tests.
**Blocked by:** Nothing. Parallel-safe with all P0 WOs.

---

## 1. Gap

`NotebookObject` exposes a complete drawing API. No pointer events in `main.ts` route canvas interactions to it. Drawing is impossible.

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Event attachment | `pointerdown`/`pointermove`/`pointerup` on `renderer.domElement` in `main.ts` |
| 2 | Hit detection | Raycast against notebook meshes (`notebook_*` name prefix). UV coordinate from intersect maps to canvas position |
| 3 | Active condition | Only active when `notebook.currentSection === 'notes'`. Transcript/bestiary/handouts are read-only |
| 4 | UV mapping | UV (0–1) × canvas dimensions gives pixel position passed to drawing API |

## 3. Contract Spec

### main.ts additions

```typescript
let _drawingActive = false;

renderer.domElement.addEventListener('pointerdown', (ev) => {
  const hit = raycastNotebook(ev);
  if (!hit || notebook.currentSection !== 'notes') return;
  _drawingActive = true;
  notebook.startStroke(uvToCanvas(hit.uv!));
});

renderer.domElement.addEventListener('pointermove', (ev) => {
  if (!_drawingActive) return;
  const hit = raycastNotebook(ev);
  if (!hit) return;
  notebook.addPoint(uvToCanvas(hit.uv!));
});

renderer.domElement.addEventListener('pointerup', () => {
  if (!_drawingActive) return;
  _drawingActive = false;
  notebook.endStroke();
});
```

## 4. Test Spec (Gate UI-NB-DRAW — 6 tests)

File: `tests/test_ui_gate_nb_draw.py` (new file)

| ID | Test |
|----|------|
| NB-D-01 | `NotebookObject.startStroke()` method exists |
| NB-D-02 | `NotebookObject.addPoint()` method exists |
| NB-D-03 | `NotebookObject.endStroke()` method exists |
| NB-D-04 | `currentSection` property exists on `NotebookObject` |
| NB-D-05 | `main.ts` registers `pointerdown`/`pointermove`/`pointerup` on renderer domElement |
| NB-D-06 | Drawing guard: strokes only accepted when `currentSection === 'notes'` |

## 5. Implementation Plan

1. Read `notebook-object.ts` (drawing API signatures), `main.ts` (existing pointer/raycast handling)
2. Add three pointer event listeners in `main.ts` with notebook raycast + UV mapping + section guard
3. Write 6 tests to `tests/test_ui_gate_nb_draw.py`
4. `pytest tests/test_ui_gate_nb_draw.py -v` — 6/6 PASS
5. `npm run build --prefix client` — exits 0
6. Full regression — zero new failures

## 6. Deliverables

- [ ] `pointerdown`/`pointermove`/`pointerup` wired to notebook drawing API in `main.ts`
- [ ] Section guard: only `notes` section accepts strokes
- [ ] Gate UI-NB-DRAW: 6/6 PASS
- [ ] Zero regressions

## 7. Integration Seams

- **Files modified:** `client/src/main.ts` only
- **Do not modify:** `notebook-object.ts` — the API is complete, only the wiring is missing

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_nb_draw.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_nb_draw.py
```

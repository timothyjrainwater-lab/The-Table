# WO-UI-SHEET-LIVE-001 — Character Sheet Live Binding

**Issued:** 2026-02-23
**Authority:** Anvil visual QA gap — character sheet texture is static canvas baked at scene build. HP changes do not update display. Clicks not wired.
**Gate:** UI-CS-LIVE (new). Target: 8 tests.
**Blocked by:** Nothing. Parallel-safe with all P0 WOs.

---

## 1. Gap

`makeCharacterSheetTexture()` in `scene-builder.ts` renders a static canvas at scene init with placeholder values. `CharacterSheetController` receives live `character_sheet_update` and `entity_delta` events but has no 3D mesh reference — it cannot update the display. The stub mesh `stub_character_sheet` is a `PlaneGeometry` with a baked texture. Clicks on it do nothing.

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Texture ownership | `CharacterSheetController` owns the canvas + texture. `scene-builder.ts` creates the mesh and exports it; controller holds the canvas ref and calls `texture.needsUpdate = true` on each update |
| 2 | Click wiring | Raycast in `main.ts` — on hit against `stub_character_sheet`, call `characterSheetController.onMeshClick(intersect.uv)` which emits `REQUEST_DECLARE_ACTION` via WS bridge |
| 3 | Render cadence | Re-render canvas on every `character_sheet_update` event only — not every frame |
| 4 | Exported ref | Export `characterSheetMesh` from `scene-builder.ts` so `main.ts` can pass it to controller |

## 3. Test Spec (Gate UI-CS-LIVE — 8 tests)

File: `tests/test_ui_gate_cs.py`

| ID | Test |
|----|------|
| CS-L-01 | `characterSheetMesh` exported from scene-builder, not null |
| CS-L-02 | `CharacterSheetController` constructor accepts mesh param |
| CS-L-03 | `update()` method exists and accepts CharacterSheetData |
| CS-L-04 | `update()` sets `texture.needsUpdate = True` |
| CS-L-05 | `onMeshClick()` calls `onDeclareAction` callback |
| CS-L-06 | HP value reflected in canvas after `update()` call |
| CS-L-07 | Mesh material map is the controller canvas texture (not baked) |
| CS-L-08 | Zero regressions on existing UI-CS gate |

## 4. Implementation Plan

1. Read `scene-builder.ts` (character sheet section), `character-sheet-controller.ts` (full), `main.ts` (controller instantiation + raycast)
2. Add `characterSheetMesh` export to `scene-builder.ts`
3. Refactor `CharacterSheetController`: accept mesh, own canvas/texture, implement `update()` + `onMeshClick()`
4. Update `main.ts`: pass mesh to controller, wire raycast click
5. Write 8 tests to `tests/test_ui_gate_cs.py`
6. `pytest tests/test_ui_gate_cs.py -v` — 8/8 PASS
7. `npm run build --prefix client` — exits 0
8. Full regression — zero new failures

## 5. Deliverables

- [ ] `characterSheetMesh` exported from `scene-builder.ts`
- [ ] `CharacterSheetController` owns canvas/texture, updates on data change
- [ ] Click on mesh emits `REQUEST_DECLARE_ACTION`
- [ ] Gate UI-CS-LIVE: 8/8 PASS
- [ ] Zero regressions

## 6. Integration Seams

- **Files modified:** `client/src/scene-builder.ts`, `client/src/character-sheet-controller.ts`, `client/src/main.ts`
- **Tests:** `tests/test_ui_gate_cs.py`
- **Do not modify:** Engine files, `entity-renderer.ts`

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_cs.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_cs.py
```

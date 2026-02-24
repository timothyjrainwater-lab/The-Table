# WO-UI-TOKEN-CHIP-001 — Flat 2D Token Chips (Doctrine Compliance)

**Issued:** 2026-02-23
**Authority:** UX Vision doctrine — "NO 3D tokens on battle map." Current `EntityRenderer` uses `CylinderGeometry` (3D). Doctrine violation.
**Gate:** UI-TOKEN-CHIP (new). Target: 8 tests.
**Blocked by:** Nothing. Parallel-safe with other P1 WOs.

---

## 1. Gap

`EntityRenderer` creates faction-colored `CylinderGeometry` tokens. The UX vision north star specifies flat 2D chip tokens. The 3D cylinders are also harder to read at tabletop camera angles.

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Geometry | `CircleGeometry(0.22, 32)` — flat disk, matches PHB token aesthetic |
| 2 | Orientation | `rotation.x = -Math.PI / 2` — flat on table at `y = 0.08` (same as current gridToScene y) |
| 3 | Material | `MeshBasicMaterial` with canvas texture — faction color ring (8px border) + HP arc + entity initial letter. Unlit so it reads clearly |
| 4 | HP display | Bake HP arc into canvas texture. Arc from 0 to `(hp/maxHp) * 2π`. Green → red lerp. Remove separate HP bar mesh |
| 5 | `gridToScene()` | Unchanged — same coordinate transform |

## 3. Test Spec (Gate UI-TOKEN-CHIP — 8 tests)

File: `tests/test_ui_gate_cb.py` (append) or new `tests/test_ui_gate_token_chip.py`

| ID | Test |
|----|------|
| TC-01 | Token mesh geometry is `CircleGeometry`, not `CylinderGeometry` |
| TC-02 | Token `rotation.x` = `-Math.PI / 2` (flat) |
| TC-03 | Token `y` position = 0.08 (via gridToScene) |
| TC-04 | Token material is `MeshBasicMaterial` |
| TC-05 | Token canvas has faction color ring (border present) |
| TC-06 | HP arc angle = `(hp/maxHp) * 2π` |
| TC-07 | No separate HP bar mesh in scene after `upsert()` |
| TC-08 | Zero regressions on existing Gate UI-06 (10/10) |

## 4. Implementation Plan

1. Read `entity-renderer.ts` (full)
2. Replace `CylinderGeometry` with `CircleGeometry(0.22, 32)` + `rotation.x = -Math.PI/2`
3. Replace `MeshStandardMaterial` with `MeshBasicMaterial` backed by canvas texture
4. Canvas renderer: faction color ring + HP arc + entity initial
5. Remove separate HP bar mesh
6. Write 8 tests
7. `pytest` — 8/8 PASS + Gate UI-06 still 10/10
8. `npm run build --prefix client` — exits 0
9. Full regression — zero new failures

## 5. Deliverables

- [ ] `CircleGeometry` flat chips replacing `CylinderGeometry` cylinders
- [ ] HP baked into canvas arc, no separate HP mesh
- [ ] Faction color ring on canvas border
- [ ] Gate UI-TOKEN-CHIP: 8/8 PASS
- [ ] Gate UI-06: still 10/10
- [ ] Zero regressions

## 6. Integration Seams

- **Files modified:** `client/src/entity-renderer.ts`
- **Do not modify:** `gridToScene()` transform, `main.ts` wiring, `zones.json`

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_token_chip.py -v
pytest tests/test_ui_gate_ui06.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_token_chip.py
```

# WO-UI-TOKEN-LABEL-001 — Entity Name Label on Token Canvas

**Issued:** 2026-02-23
**Authority:** Anvil visual QA gap — token chips (post WO-UI-TOKEN-CHIP-001) have faction ring + HP arc but no entity name. Tokens are unidentifiable without external reference.
**Gate:** UI-TOKEN-LABEL (new). Target: 3 tests.
**Blocked by:** WO-UI-TOKEN-CHIP-001 (geometry + canvas refactor must land first).

---

## 1. Gap

After TOKEN-CHIP-001, the canvas texture has faction color ring and HP arc. The entity name is not rendered. At tabletop scale, tokens cannot be identified by appearance alone.

## 2. Fix Spec

In the `EntityRenderer` canvas draw function (introduced by TOKEN-CHIP-001):

1. After drawing faction ring and HP arc, render entity name text.
2. Text: `entity.name.substring(0, 8)` — truncated to 8 characters.
3. Font: `"bold 18px sans-serif"`, fill white, centered at canvas center.
4. Render order: ring → HP arc → name text (name on top).

No geometry changes. Canvas-only addition.

## 3. Test Spec (Gate UI-TOKEN-LABEL — 3 tests)

File: `tests/test_ui_gate_cb.py` (append) or new `tests/test_ui_gate_token_chip.py` (append)

| ID | Test |
|----|------|
| TL-01 | Canvas draw function calls `fillText` with entity name |
| TL-02 | Name truncated to 8 characters (`substring(0, 8)`) |
| TL-03 | Text rendered centered (`textAlign = 'center'`) |

## 4. Implementation Plan

1. Read `entity-renderer.ts` (canvas draw function, post TOKEN-CHIP-001)
2. Add `fillText` call after HP arc draw — center, white, bold 18px, truncate to 8 chars
3. Write 3 tests
4. `pytest tests/test_ui_gate_token_chip.py -v` (or whichever file TOKEN-CHIP tests landed in) — all pass
5. `npm run build --prefix client` — exits 0
6. Full regression — zero new failures

## 5. Deliverables

- [ ] Entity name rendered on token canvas, centered, truncated to 8 chars
- [ ] Gate UI-TOKEN-LABEL: 3/3 PASS
- [ ] Zero regressions

## 6. Integration Seams

- **Files modified:** `client/src/entity-renderer.ts` (canvas draw function only)
- **Depends on:** WO-UI-TOKEN-CHIP-001 landed (canvas texture established)
- **Do not modify:** Geometry, material, `gridToScene()`, `main.ts`

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_token_chip.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_token_chip.py
```

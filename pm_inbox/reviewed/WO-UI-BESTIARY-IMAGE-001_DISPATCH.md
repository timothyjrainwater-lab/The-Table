# WO-UI-BESTIARY-IMAGE-001 — Bestiary Image URL Binding

**Issued:** 2026-02-23
**Authority:** Anvil visual QA gap — bestiary entry schema has no `image_url` field. Creature art cannot be displayed.
**Gate:** UI-BESTIARY-IMG (new). Target: 6 tests.
**Blocked by:** Nothing. Parallel-safe with other P1 WOs.

---

## 1. Gap

`BestiaryBindController` receives `bestiary_entry_reveal` events. The entry schema has no `image_url` field. The notebook bestiary section shows procedural placeholder only — no actual creature art binding is possible.

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Schema addition | Add `image_url?: string` to bestiary entry type in `bestiary-bind.ts` |
| 2 | Texture load | `THREE.TextureLoader().load(image_url)` when present. Applied to a `PlaneGeometry` inside the notebook bestiary section |
| 3 | Fallback | If `image_url` absent or load fails, procedural placeholder remains. Graceful — no error thrown |
| 4 | Plane size | `PlaneGeometry(0.8, 0.8)` centered in bestiary section view area |

## 3. Test Spec (Gate UI-BESTIARY-IMG — 6 tests)

File: `tests/test_ui_gate_bestiary.py` (append to existing)

| ID | Test |
|----|------|
| BI-01 | `BestiaryEntry` type accepts `image_url` optional string field |
| BI-02 | `handleReveal()` does not throw when `image_url` absent |
| BI-03 | `handleReveal()` does not throw when `image_url` present (load attempted) |
| BI-04 | Texture load triggered when `image_url` is a non-empty string |
| BI-05 | Fallback to procedural when `image_url` is undefined |
| BI-06 | Zero regressions on existing bestiary gate |

## 4. Implementation Plan

1. Read `bestiary-bind.ts` (full), `notebook-object.ts` (bestiary section)
2. Add `image_url?: string` to `BestiaryEntry` type
3. In `handleReveal()`: if `image_url` present, `TextureLoader.load()` → apply to bestiary plane mesh
4. Graceful fallback if absent/load fails
5. Write 6 tests
6. `pytest tests/test_ui_gate_bestiary.py -v` — 6/6 PASS
7. `npm run build --prefix client` — exits 0
8. Full regression — zero new failures

## 5. Deliverables

- [ ] `image_url?: string` on `BestiaryEntry` type
- [ ] Texture load + plane mesh when `image_url` present
- [ ] Graceful fallback when absent
- [ ] Gate UI-BESTIARY-IMG: 6/6 PASS
- [ ] Zero regressions

## 6. Integration Seams

- **Files modified:** `client/src/bestiary-bind.ts`, `client/src/notebook-object.ts` (bestiary section plane)
- **Do not modify:** Engine files, `entity-renderer.ts`

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_bestiary.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_bestiary.py
```

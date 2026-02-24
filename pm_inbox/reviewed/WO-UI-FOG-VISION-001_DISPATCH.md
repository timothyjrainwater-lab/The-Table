# WO-UI-FOG-VISION-001 — Fog of War Vision Type Differentiation

**Issued:** 2026-02-23
**Authority:** North Star gap audit — `FogOfWarManager` has binary revealed/visible/hidden states. Vision type differentiation (normal, darkvision, low-light) is unimplemented. Darkvision should render in grayscale; low-light should extend reveal radius vs. normal vision.
**Gate:** UI-FOG-VISION (new). Target: 5 tests.
**Blocked by:** Nothing. Parallel-safe with all current WOs. Depends on WO-UI-FOG-FADE-001 being landed first (opacity lerp infrastructure must exist).

---

## 1. Gap

`FogOfWarManager` treats all player tokens identically — binary fog reveal with no vision type. D&D 3.5e has three vision types:
- **Normal:** Standard reveal within light radius.
- **Low-light:** Treat dim light as bright light — effectively double range in dim conditions.
- **Darkvision:** See in total darkness up to range limit, but in grayscale (no color).

Currently the fog layer applies identical white opacity to all hidden cells. No grayscale rendering, no radius differentiation.

## 2. Fix Spec

Extend `FogOfWarManager` with vision type support:

1. **Vision type enum:** `type VisionType = 'normal' | 'low_light' | 'darkvision'` in `fog-of-war.ts`.
2. **Player vision registry:** `Map<string, VisionType>` keyed by entity ID. Set via `setEntityVision(entityId, visionType)`.
3. **Cell reveal coloring:**
   - Normal/low-light: existing white fog (opacity lerp as before).
   - Darkvision: use a dark blue-gray tint (`color: 0x1a1a2e`, opacity ~0.3) instead of pure white — indicates grayscale vision in darkness.
4. **Radius modifier:** `getRevealRadius(entityId): number` returns base radius × 2 for `low_light` entities.
5. **WS event wire:** On `entity_state` events, extract `VISION_TYPE` EF field and call `setEntityVision()`.

No geometry changes. Material color + opacity only.

## 3. Test Spec (Gate UI-FOG-VISION — 5 tests)

File: `tests/test_ui_gate_fog.py` (append to existing) or `tests/test_ui_gate_fog_vision.py` (new)

| ID | Test |
|----|------|
| FV-01 | `VisionType` union type defined in `fog-of-war.ts` with `normal`, `low_light`, `darkvision` |
| FV-02 | `setEntityVision(entityId, visionType)` method exists on `FogOfWarManager` |
| FV-03 | Darkvision cells use different material color than normal fog cells |
| FV-04 | `getRevealRadius()` returns 2× base for `low_light` vision type |
| FV-05 | `main.ts` calls `setEntityVision()` on `entity_state` event (extracts VISION_TYPE field) |

## 4. Implementation Plan

1. Read `fog-of-war.ts` (full, current state post FOG-FADE-001), `main.ts` (entity_state handler)
2. Add `VisionType` type and `entityVisions` map to `FogOfWarManager`
3. Implement `setEntityVision()` and `getRevealRadius()`
4. In cell material creation: branch on darkvision → dark blue-gray color
5. In `main.ts` entity_state handler: extract `VISION_TYPE` EF, call `setEntityVision()`
6. Write 5 tests (append to existing fog test file or new file)
7. `pytest tests/test_ui_gate_fog_vision.py -v` — 5/5 PASS
8. `npm run build --prefix client` — exits 0
9. Full regression — zero new failures

## 5. Deliverables

- [ ] `VisionType` union: `normal | low_light | darkvision`
- [ ] `setEntityVision()` + `getRevealRadius()` on `FogOfWarManager`
- [ ] Darkvision cells: dark blue-gray tint, not white fog
- [ ] Low-light: 2× reveal radius
- [ ] `main.ts` wires VISION_TYPE EF on entity_state
- [ ] Gate UI-FOG-VISION: 5/5 PASS
- [ ] Zero regressions

## 6. Integration Seams

- **Files modified:** `client/src/fog-of-war.ts`, `client/src/main.ts`
- **Do not modify:** Engine files, `entity-renderer.ts`, geometry
- **Depends on:** WO-UI-FOG-FADE-001 landed (opacity lerp infrastructure)

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_fog_vision.py -v
pytest tests/test_ui_gate_fog.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_fog_vision.py
```

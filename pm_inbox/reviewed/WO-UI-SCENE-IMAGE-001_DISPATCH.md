# WO-UI-SCENE-IMAGE-001 — DM-Side Scene Image Display

**Issued:** 2026-02-23
**Authority:** North Star gap audit — non-combat scenes show no imagery in the DM-side scroll/map area. Vision: AI-generated scene images appear on the DM side during exploration, rest, and dialogue. Currently nothing renders there outside combat.
**Gate:** UI-SCENE-IMG (new). Target: 6 tests.
**Blocked by:** Nothing. Parallel-safe with all current WOs.

---

## 1. Gap

The battle scroll (`BattleScrollObject`) is combat-only — it unrolls on `combat_start` and rolls up on `combat_end`. Non-combat scenes have no image surface. The DM side of the table (the far z area in front of the dice tower, roughly z=0 to z=2) has no display mechanism. Scene images from the AI (asset pipeline) have nowhere to appear.

## 2. Fix Spec

Introduce a `SceneImagePlane` — a `PlaneGeometry` in the DM-side table area that:
1. Starts invisible (opacity 0, `transparent: true`).
2. On `scene_image` WS event: loads the image URL via `THREE.TextureLoader`, applies to plane material, fades in over 0.4s.
3. On `combat_start`: fades out (battle scroll takes over DM-side space).
4. On `combat_end`: fades back in with last loaded texture (or stays hidden if none).
5. Plane dimensions: `PlaneGeometry(3.0, 2.0)`, laid flat (`rotation.x = -Math.PI / 2`), positioned at `(0, 0.02, 1.5)` (center of DM-side table, just above surface).

### WS event contract

```typescript
// scene_image event payload
{ type: "scene_image", image_url: string, caption?: string }
```

`caption` is optional — if present, render as small text below the plane (HTML overlay, not Three.js text).

## 3. Test Spec (Gate UI-SCENE-IMG — 6 tests)

File: `tests/test_ui_gate_scene_img.py` (new)

| ID | Test |
|----|------|
| SI-01 | `SceneImagePlane` class exists in `scene-builder.ts` or dedicated file |
| SI-02 | Plane geometry is `PlaneGeometry(3.0, 2.0)`, `rotation.x = -Math.PI/2` |
| SI-03 | Plane starts with `material.opacity = 0` |
| SI-04 | `onSceneImage(url)` triggers `TextureLoader.load()` |
| SI-05 | `onCombatStart()` fades plane out |
| SI-06 | `main.ts` registers `scene_image` WS event → `sceneImagePlane.onSceneImage()` |

## 4. Implementation Plan

1. Read `scene-builder.ts` (DM-side area), `main.ts` (WS event handlers)
2. Add `SceneImagePlane` class (or function) in `scene-builder.ts` — creates plane, exposes `onSceneImage(url)`, `onCombatStart()`, `onCombatEnd()`
3. Export from `scene-builder.ts`, import and wire in `main.ts`
4. Register `scene_image` WS event handler alongside existing handlers
5. Write 6 tests to `tests/test_ui_gate_scene_img.py`
6. `pytest tests/test_ui_gate_scene_img.py -v` — 6/6 PASS
7. `npm run build --prefix client` — exits 0
8. Full regression — zero new failures

## 5. Deliverables

- [ ] `SceneImagePlane` plane at DM-side table position, starts transparent
- [ ] `onSceneImage(url)` loads texture, fades in
- [ ] `onCombatStart()` fades out; `onCombatEnd()` restores
- [ ] `scene_image` WS event wired in `main.ts`
- [ ] Gate UI-SCENE-IMG: 6/6 PASS
- [ ] Zero regressions

## 6. Integration Seams

- **Files modified:** `client/src/scene-builder.ts`, `client/src/main.ts`
- **Do not modify:** `BattleScrollObject`, `entity-renderer.ts`, engine files
- **Caption overlay:** If caption support is included, use an HTML div — not Three.js text geometry

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_scene_img.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_scene_img.py
```

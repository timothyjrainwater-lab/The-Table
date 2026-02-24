# WO-UI-PORTRAIT-MESH-001 — Crystal Ball Inner Portrait Sphere

**Issued:** 2026-02-23
**Authority:** Anvil visual QA gap — portraits load but display nowhere. `stub_crystal_ball` outer orb is transparent glass with no inner surface to receive texture.
**Gate:** UI-CB-PORTRAIT (new). Target: 6 tests.
**Blocked by:** Nothing. Parallel-safe with all P0 WOs.

---

## 1. Gap

`CrystalBallController.onPortraitDisplay()` receives NPC portrait data and loads a canvas texture. There is no mesh inside the crystal ball to display it. The outer orb (`stub_crystal_ball`, radius 0.70, opacity 0.78) is transparent — the inner void is empty.

## 2. Binary Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | Inner mesh geometry | `SphereGeometry(0.52, 32, 20)` — inside the outer orb, small enough not to clip |
| 2 | Material | `MeshBasicMaterial` with canvas `map` — unaffected by scene lighting, portrait reads clearly |
| 3 | Export | Export `crystalBallInnerMesh` from `scene-builder.ts` alongside existing `crystalBallOrbMesh` |
| 4 | Controller binding | `CrystalBallController` accepts `innerMesh` as second constructor param, writes portrait canvas to `innerMesh.material.map` |
| 5 | Fade | `onPortraitDisplay` → fade inner mesh opacity 0→1 over 0.4s. `onSpeakingStop` → fade 1→0 over 0.8s |

## 3. Contract Spec

### scene-builder.ts
Add inside `buildObjectStubs()` after the outer orb:
```typescript
export let crystalBallInnerMesh: THREE.Mesh | null = null;

const innerGeo = new THREE.SphereGeometry(0.52, 32, 20);
const innerMat = new THREE.MeshBasicMaterial({
  transparent: true,
  opacity: 0.0,  // hidden until portrait loads
});
const innerMesh = new THREE.Mesh(innerGeo, innerMat);
innerMesh.position.copy(orb.position);
innerMesh.name = 'crystal_ball_inner';
group.add(innerMesh);
crystalBallInnerMesh = innerMesh;
```

### crystal-ball-controller.ts
```typescript
constructor(orbMesh: THREE.Mesh, innerMesh: THREE.Mesh) { ... }

onPortraitDisplay(data: { image_url?: string; label?: string }): void {
  // render label/image to canvas, set as innerMesh.material.map
  // fade innerMesh opacity 0→1 over 0.4s
}

onSpeakingStop(): void {
  // fade innerMesh opacity 1→0 over 0.8s
}
```

### main.ts
Update constructor call:
```typescript
const crystalBallController = new CrystalBallController(
  crystalBallOrbMesh!,
  crystalBallInnerMesh!,
);
```

## 4. Test Spec (Gate UI-CB-PORTRAIT — 6 tests)

File: `tests/test_ui_gate_cb.py` (append to existing)

| ID | Test |
|----|------|
| CB-P-01 | `crystalBallInnerMesh` exported from scene-builder, not null |
| CB-P-02 | Inner mesh name = `crystal_ball_inner` |
| CB-P-03 | Inner mesh radius < outer orb radius (0.52 < 0.70) |
| CB-P-04 | `CrystalBallController` constructor accepts 2 mesh params |
| CB-P-05 | `onPortraitDisplay()` sets `material.map` on inner mesh |
| CB-P-06 | `onSpeakingStop()` triggers opacity fade toward 0 |

## 5. Implementation Plan

1. Read `scene-builder.ts` (crystal ball section) and `crystal-ball-controller.ts` (full)
2. Add inner sphere in `buildObjectStubs()`, export `crystalBallInnerMesh`
3. Update `CrystalBallController` constructor + `onPortraitDisplay` + fade logic
4. Update `main.ts` constructor call
5. Append 6 tests to `tests/test_ui_gate_cb.py`
6. `pytest tests/test_ui_gate_cb.py -v` — all pass
7. `npm run build --prefix client` — exits 0
8. Full regression — zero new failures

## 6. Deliverables

- [ ] `crystalBallInnerMesh` exported from `scene-builder.ts`
- [ ] Inner sphere at radius 0.52, name `crystal_ball_inner`, opacity 0.0 initial
- [ ] `CrystalBallController` binds portrait canvas to inner mesh
- [ ] Fade wired on display/stop
- [ ] Gate UI-CB-PORTRAIT: 6/6 PASS
- [ ] Zero regressions

## 7. Integration Seams

- **Files modified:** `client/src/scene-builder.ts`, `client/src/crystal-ball-controller.ts`, `client/src/main.ts`
- **Files modified (tests):** `tests/test_ui_gate_cb.py`
- **Do not modify:** `entity-renderer.ts`, `fog-of-war.ts`, any engine files

## Preflight

```bash
npm run build --prefix client
pytest tests/test_ui_gate_cb.py -v
pytest tests/ -x -q --ignore=tests/test_ui_gate_cb.py
```

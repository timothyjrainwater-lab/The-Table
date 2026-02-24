# WO-UI-LIGHTING-V1 — Environment + Lighting Baseline

**Issued:** 2026-02-23
**Authority:** PM — AI2AI Exec Packet (TABLE UI NORTH STAR)
**Sequence:** 4 of 6. Parallel-safe with WO-UI-OBJECT-LAYOUT-V1.
**Gate:** UI-LIGHTING (new gate, defined below)

---

## 1. Target Lock

Remove the black void. Add minimal room geometry that grounds the table in a space. Tune existing lighting so wood grain reads clearly, rail edges show depth highlights, and orb reads as presence anchor without overpowering glow. Fix walnut texture repeat so grain is visible.

**Done means:** Scene reads as a dim library/tavern room — warm, not a void. Wood grain visible. Rail edges have specular highlights. Depth cues present. Screenshot diff stable.

---

## 2. Binary Decisions — Locked

| Decision | Answer |
|----------|--------|
| Room geometry approach | Minimal: back wall + floor plane only. No ceiling, no side walls (they're dark and out of frame in most postures). |
| Back wall Z | z = −8.0 (behind orb, behind far rail at z=−4.1) |
| Wall material | Dark stone/plaster — rough, very dark, warm undertone. Not black. |
| Floor plane | Extends from z=−8 to z=+8, x=±7. Dark stone, barely visible. |
| Walnut texture repeat | Fix repeat to show grain: `repeat.set(1, 0.75)` (was 2×1.5 which tiles too tightly and erases grain) |
| Scene background | Change from `0x08060a` (near-black) to `0x100c0a` (very dark brown — room air, not void) |
| Fog | Keep fog, but push start distance: `Fog(0x100c0a, 16, 26)` (was 14, 22) so rails don't fog out |

---

## 3. Implementation Spec

### 3.1 Room geometry — `buildAtmosphere()` or new `buildRoom()` function

Add to `scene-builder.ts`:

```typescript
export function buildRoom(scene: THREE.Scene): void {
  // Back wall — dark rough stone behind DM side
  const wallGeo = new THREE.PlaneGeometry(16, 6);
  const wallMat = new THREE.MeshStandardMaterial({
    color: 0x1a1008,   // very dark warm brown — stone/plaster
    roughness: 0.97,
    metalness: 0.0,
  });
  const backWall = new THREE.Mesh(wallGeo, wallMat);
  backWall.position.set(0, 2.0, -8.0);  // y=2.0 = wall center at 4m height
  backWall.name = 'room_back_wall';
  backWall.receiveShadow = true;
  scene.add(backWall);

  // Floor plane — stone floor visible at room edges
  const floorGeo = new THREE.PlaneGeometry(16, 16);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x0e0a06,
    roughness: 0.98,
    metalness: 0.0,
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, -0.7, 0);  // below table legs (table surface at y=0)
  floor.name = 'room_floor';
  floor.receiveShadow = true;
  scene.add(floor);
}
```

Call `buildRoom(scene)` in `main.ts` after `buildAtmosphere()`.

Update `scene.background` and `scene.fog` in `main.ts`:
```typescript
scene.background = new THREE.Color(0x100c0a);  // was 0x08060a
scene.fog = new THREE.Fog(0x100c0a, 16, 26);   // was Fog(0x08060a, 14, 22)
```

### 3.2 Walnut texture grain fix

In `makeWalnutTexture()` in `scene-builder.ts`:
```typescript
// Change:
tex.repeat.set(2, 1.5);   // current — tiles too tightly, grain invisible
// To:
tex.repeat.set(1, 0.75);  // fix — shows individual grain bands clearly
```

This is the single change that makes wood grain readable. The procedural grain lines are there; they're just tiled into invisibility.

### 3.3 Lighting tuning

Current lights from `buildAtmosphere()`:
- Ambient: `0x1a1520`, intensity 0.70 — slightly purple cast. Fix to warm.
- Hemi: `0x3d1f08` / `0x080510`, intensity 0.65 — OK
- Lantern center: `0xffb347`, intensity 55 — may be blowing out table center
- Lantern left/right: `0xffa030` / `0xffb866`, intensity 42 each
- DM candle: `0x4466ff`, intensity 8 — blue cast on DM side
- Tray fill: `0xffcc88`, intensity 18
- Map spot: `0xffaa44`, intensity 38

Adjustments:

```typescript
// Ambient — remove purple cast, warm it
const ambient = new THREE.AmbientLight(0x1a1208, 0.55);  // was 0x1a1520, 0.70

// Lantern center — reduce slightly to avoid blow-out
// position(0, 5.5, 0), color 0xffb347, intensity: 42  (was 55)

// DM candle — reduce blue; makes DM side feel cold not magical
// color: 0x3344cc, intensity: 5  (was 0x4466ff, 8)
// Keep it as a subtle blue hint, not dominant source

// Map spot — position closer to vault, boost slightly for readability
// position(0, 3.5, -0.5), color 0xffaa44, intensity: 44  (was 38 at y=4.0)
```

**Rail highlight:** The far rail at z=−4.1 should catch specular from the overhead center lantern. No geometry change needed — the roughness on `walnutMat(WALNUT_LIGHT)` at 0.65 should already catch highlights. Confirm visually: the far rail top edge should show a warm amber highlight in STANDARD posture.

### 3.4 Character sheet parchment — not too bright (VQ-006)

The sheet uses `color: '#c8b483'` (parchment). The QA flagged it as reading too bright / too modern. Darken the parchment base:

In `makeCharacterSheetTexture()`:
```typescript
// Change:
ctx.fillStyle = '#c8b483';  // was — too bright
// To:
ctx.fillStyle = '#b8a06a';  // darker aged parchment
```

---

## 4. Gate Spec

**Gate name:** `UI-LIGHTING`
**Test file:** `client/tests/screenshot.spec.ts` (skeleton — full suite in WO-UI-GATES-V1)

Gate passes when (Playwright + screenshot check):

1. `room_back_wall` mesh exists in scene (via `?dump=1`)
2. `room_floor` mesh exists in scene
3. Scene background color is not `#08060a` (pure void black)
4. `makeWalnutTexture` repeat is (1, 0.75) — testable by checking the texture object at startup
5. Ambient light color is not `#1a1520` (purple cast) — testable via `window.__SCENE_DEBUG__` if exposed
6. Screenshot of STANDARD posture shows pixel value at the back wall region (estimated screen region x=900-1000, y=200-300) that is NOT pure black (R+G+B > 15)

**Test count target:** 6 checks → Gate `UI-LIGHTING` 6/6.

Note: Check 6 is a loose pixel brightness test — it fails if the back wall is still a void, passes if it has any non-zero luminance. This is not a full perceptual diff; that's in WO-UI-GATES-V1.

---

## 5. What This WO Does NOT Do

- Does not add side walls (not needed; rails and room air at edges are sufficient)
- Does not add candles or other practical light sources as geometry (scoped to WO)
- Does not add physics (WO-UI-PHYSICALITY-BASELINE-V1)
- Does not add screenshot diff tests (WO-UI-GATES-V1)

---

## 6. Preflight

```bash
npm run dev --prefix client
# Press 1 (STANDARD) — confirm back wall visible behind orb. No pure black void.
# Confirm wood grain visible on table surface.
# Confirm far rail top edge has specular highlight (warm amber line).
# Press 2 (DOWN) — confirm shelf lit, parchment readable but aged (not white).
```

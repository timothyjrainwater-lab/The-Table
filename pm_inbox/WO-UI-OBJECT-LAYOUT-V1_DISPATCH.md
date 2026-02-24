# WO-UI-OBJECT-LAYOUT-V1 — Object Placement + Shelf Layout

**Issued:** 2026-02-23
**Authority:** PM — AI2AI Exec Packet (TABLE UI NORTH STAR)
**Sequence:** 3 of 6. Depends on WO-UI-LAYOUT-PACK-V1 ACCEPTED.
**Gate:** UI-OBJECT-LAYOUT (new gate, defined below)

---

## 1. Target Lock

Move all physical object stubs to the positions and scales specified in `table_objects.json`. Fix shelf overlap (clear lateral separation between sheet/notebook/rulebook). Enforce notebook dominance. Ensure vault is visibly recessed below rail level. Clean up dice station layout. Confirm golden frames match after changes.

**Done means:** Zone parity passes (all objects in declared zones). Shelf reads as three clearly separated objects in DOWN posture. Orb is the dominant DM-side anchor in STANDARD posture. Golden frames updated if positions changed.

---

## 2. Binary Decisions — Locked

| Decision | Answer |
|----------|--------|
| Object position source | `table_objects.json` anchor positions — do not edit JSON to match broken scene |
| Notebook dominance rule | Notebook footprint must be largest OR most central on shelf. Minimum size: 1.4×1.9 (matches char sheet). |
| Shelf lateral separation | Minimum 2.0 units clear gap between centroids of sheet/notebook/rulebook in X |
| Vault depth | Vault felt surface must be at least 0.04 units below table rail top |
| Orphan objects | stub_parchment hidden (done by LAYOUT-PACK-V1). d6 stubs removed (done by LAYOUT-PACK-V1). |

---

## 3. Current State (from QA inspection)

| Object | Current position | Problem |
|--------|-----------------|---------|
| stub_character_sheet | (−2.6, 0.005, 4.5) | z=4.5 vs shelf centerZ=4.75 — slightly off |
| stub_notebook | (−0.2, 0.01, 4.8) | z=4.8 slightly off. Size 1.1×1.5 — too small for dominant object |
| stub_tome | (2.0, 0.04, 4.8) | z=4.8 OK. Overlaps notebook in STANDARD view (same Z, similar X gap) |
| stub_crystal_ball | (0, 1.45, −3.2) | Position correct. Radius OK. |
| felt_vault | (0, −0.04, −0.5) | Present but featureless dark maroon — needs grid canvas |
| stub_dice_tower | (4.5, 0.62, 0.5) | Position OK. Tower opening already modeled. |

---

## 4. Implementation Spec

### 4.1 Shelf objects — canonical positions

Apply these exact positions (from `table_objects.json`, committed by WO-UI-LAYOUT-PACK-V1):

**Character Sheet (`stub_character_sheet`)**
```
position: (−2.6, 0.005, 4.75)
rotation.y: 0.06
geometry: PlaneGeometry(1.4, 1.9)  — unchanged
```

**Notebook (`stub_notebook`)**
```
position: (−0.2, 0.01, 4.75)
rotation.y: −0.08
geometry: BoxGeometry(1.4, 0.08, 1.9)  ← CHANGE: was 1.1×0.08×1.5. Grow to 1.4×1.9 to match sheet footprint and assert dominance.
```
Notebook must be the dominant player object. Footprint 1.4×1.9 makes it equal to the sheet. Central position (x=−0.2) makes it focal. Add a subtle canvas texture label on the cover face ("NOTEBOOK" in aged ink) so it reads as distinct from the rulebook.

**Rulebook (`stub_tome`)**
```
position: (2.0, 0.04, 4.75)
rotation.y: 0.12
geometry: BoxGeometry(1.2, 0.18, 1.6)  ← CHANGE: height 0.14→0.18 to read as thicker than notebook. Width/depth unchanged.
```

**Dice Bag (`stub_dice_bag`)**
Confirm mesh exists and is positioned at (−4.0, 0.01, 4.75). If `DiceBagObject` from `dice-bag.ts` manages this mesh, confirm it is placed at the `shelf_dice_bag` anchor. If no mesh exists at this position, add a simple stub sphere (radius 0.25, leather-brown color) as a placeholder.

### 4.2 Vault — faint grid canvas

The vault felt surface is currently `MeshStandardMaterial` with solid dark green color. Add a canvas texture to the vault with a faint 1-unit grid drawn on it:

```typescript
function makeVaultTexture(width = 512, height = 512): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = width; canvas.height = height;
  const ctx = canvas.getContext('2d')!;

  // Base: dark green felt
  ctx.fillStyle = '#162210';
  ctx.fillRect(0, 0, width, height);

  // Faint grid — 1 unit = 512/6 ≈ 85px (vault is 6.2 wide)
  ctx.strokeStyle = 'rgba(80,120,60,0.25)';
  ctx.lineWidth = 1;
  const cellPx = width / 6;
  for (let x = 0; x <= width; x += cellPx) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
  }
  const cellPxH = height / 4; // vault is 4.2 deep
  for (let y = 0; y <= height; y += cellPxH) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
  }

  return new THREE.CanvasTexture(canvas);
}
```

Apply this texture to the vault `felt_vault` mesh material.

### 4.3 Vault recess depth check

Vault mesh is at y=−0.04. Rail top is at y=railH=0.18. Gap = 0.22 units — sufficient for visible recess. No geometry change needed. Confirm visually in LEAN_FORWARD posture that the recess reads clearly.

### 4.4 Felt vault visible when scroll rolled up (VQ-001)

The vault felt is always visible regardless of combat state. During exploration (scroll rolled up), the vault should appear as walnut table surface, not green felt. Fix:

In `buildTableSurface()`, add a cover plane over the vault that:
- Matches walnut color/texture exactly
- Is visible by default (non-combat)
- Becomes invisible on `combat_start` WS event (reveal the felt vault)
- Returns to visible on `combat_end`

```typescript
// Vault cover — walnut plane that hides felt during non-combat
const vaultCoverGeo = new THREE.PlaneGeometry(6.2, 4.2);
const vaultCover = new THREE.Mesh(vaultCoverGeo, walnutMat());
vaultCover.rotation.x = -Math.PI / 2;
vaultCover.position.set(0, 0.002, -0.5); // just above vault surface
vaultCover.name = 'vault_cover';
group.add(vaultCover);
```

In `main.ts`, on `combat_start`: `vaultCoverMesh.visible = false`. On `combat_end`: `vaultCoverMesh.visible = true`. Export `vaultCoverMesh` from `scene-builder.ts` (same pattern as `characterSheetMesh`).

### 4.5 Orb idle state (VQ-005)

Currently `emissiveIntensity: 0.3` at idle — described in QA as "pulses constantly at intensity that reads as 'always active.'" Reduce idle emissive:

```typescript
// In buildObjectStubs(), orb material:
emissiveIntensity: 0.08,  // was 0.3 — dim at idle, CrystalBallController ramps on speech
```

The `CrystalBallController` already handles the speech animation. This change only affects the idle baseline.

---

## 5. Gate Spec

**Gate name:** `UI-OBJECT-LAYOUT`
**Test file:** `client/tests/zone_parity.spec.ts` (extends the skeleton from LAYOUT-PACK-V1)

Gate passes when (via `?dump=1` scene dump + Playwright):

1. `stub_character_sheet` center within SHELF_ZONE bounds
2. `stub_notebook` center within SHELF_ZONE bounds. Geometry x-extent ≥ 1.3 (dominant footprint).
3. `stub_tome` center within SHELF_ZONE bounds
4. `stub_crystal_ball` center within DM_ZONE bounds
5. `stub_dice_tower` center within DICE_STATION_ZONE bounds
6. `dice_tray_bottom` center within DICE_STATION_ZONE bounds
7. X-distance between stub_character_sheet and stub_notebook centroids ≥ 2.0
8. X-distance between stub_notebook and stub_tome centroids ≥ 2.0
9. `vault_cover` mesh exists and is visible (non-combat default)
10. `stub_parchment.visible === false` (carried from LAYOUT-PACK-V1 gate)

**Test count target:** 10 checks → Gate `UI-OBJECT-LAYOUT` 10/10.

---

## 6. Golden Frame Update

After completing this WO, re-examine the STANDARD and DOWN golden frames (captured by WO-UI-CAMERAS-V1). If object positions changed materially, recapture those golden frames and commit updated versions with a comment: "WO-UI-OBJECT-LAYOUT-V1: shelf positions corrected."

---

## 7. What This WO Does NOT Do

- Does not change camera postures (WO-UI-CAMERAS-V1 owns those)
- Does not add room geometry (WO-UI-LIGHTING-V1)
- Does not add physics constraints (WO-UI-PHYSICALITY-BASELINE-V1)
- Does not add screenshot diff tests (WO-UI-GATES-V1)

---

## 8. Preflight

```bash
npm run dev --prefix client
# Press 2 (DOWN posture) — confirm three shelf objects clearly separated
# Press 1 (STANDARD) — confirm orb dominant, vault recess visible, no green tray in frame
# Press 3 (LEAN_FORWARD) — confirm vault recess reads clearly
# Press 4 (DICE_TRAY) — confirm tower + tray dominate
```

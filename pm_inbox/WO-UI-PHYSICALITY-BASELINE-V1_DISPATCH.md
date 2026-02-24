# WO-UI-PHYSICALITY-BASELINE-V1 — Kinematic Drag + Shelf Constraints

**Issued:** 2026-02-23
**Authority:** PM — AI2AI Exec Packet (TABLE UI NORTH STAR)
**Sequence:** 5 of 6. Depends on WO-UI-OBJECT-LAYOUT-V1 ACCEPTED.
**Gate:** UI-PHYSICALITY-BASELINE (new gate, defined below)

---

## 1. Target Lock

Convert shelf artifacts (character sheet, notebook, rulebook) to `KINEMATIC_DRAG` physics class: draggable within their allowed zone with smooth weighted motion. Nothing floats, nothing snaps, nothing crosses into DM zone. The drag should feel like sliding a piece of paper on a real table — slight inertia, settles naturally.

**Done means:** You can click and drag the notebook/sheet/rulebook on the shelf. Motion is smooth with weight feel. Releasing the object settles with slight damping. Object stays within SHELF_ZONE bounds. Dice bag draggable in SHELF_ZONE. No object can be dragged into VAULT_ZONE or DM_ZONE.

---

## 2. Scope — Minimum Viable Physicality

This WO does NOT implement full rigid-body simulation. It implements:
- Pointer-based drag (mousedown + mousemove + mouseup)
- Zone-constrained movement (objects can't leave declared zones)
- Weighted easing (lerp toward pointer at rate that feels "heavy paper" — not floaty)
- Settle damping on release (velocity decays to zero)

Dice physics (rolling, tumbling in tower) are deferred. Tokens are deferred. This WO is shelf artifacts only.

---

## 3. Binary Decisions — Locked

| Decision | Answer |
|----------|--------|
| Drag objects | CHAR_SHEET, NOTEBOOK, RULEBOOK, DICE_BAG |
| Drag constraint | SHELF_ZONE bounds (from zones.json). Hard clamp — no soft spring at boundary. |
| Drag feel | lerp factor: 0.18 per frame at 60fps. Settled velocity half-life: 8 frames. |
| Y-axis during drag | Fixed at object's initial Y — no lifting off the table surface |
| Mouse button | Left mouse only (button 0) |
| Raycast target | Objects must have `userData.draggable = true` and `userData.zone = 'SHELF_ZONE'` |
| DM zone crossing | Hard blocked — zone bounds are enforced, no object can enter VAULT_ZONE or DM_ZONE |

---

## 4. Implementation Spec

### 4.1 Architecture

Add a new file `client/src/shelf-drag.ts`:

```typescript
/**
 * Shelf drag — kinematic drag for SHELF_ZONE artifacts.
 * Physics class: KINEMATIC_DRAG. Constraint: SHELF_ZONE bounds.
 */

import * as THREE from 'three';
import type { Zone } from './zones';

export interface DragConfig {
  lerpFactor: number;      // 0.18 — how fast object tracks pointer
  settleFrames: number;    // 8 — velocity half-life frames on release
}

const DEFAULT_CONFIG: DragConfig = {
  lerpFactor: 0.18,
  settleFrames: 8,
};

export class ShelfDragController {
  private _dragging: THREE.Object3D | null = null;
  private _dragTarget = new THREE.Vector3();
  private _velocity = new THREE.Vector3();
  private _planeY = 0;
  private _shelfBounds: { minX: number; maxX: number; minZ: number; maxZ: number };
  private _config: DragConfig;
  private _raycaster = new THREE.Raycaster();
  private _dragPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  private _pointerWorld = new THREE.Vector3();

  constructor(
    private _camera: THREE.PerspectiveCamera,
    private _renderer: THREE.WebGLRenderer,
    shelfZone: Zone,
    config: DragConfig = DEFAULT_CONFIG,
  ) {
    this._config = config;
    this._shelfBounds = {
      minX: shelfZone.centerX - shelfZone.halfWidth,
      maxX: shelfZone.centerX + shelfZone.halfWidth,
      minZ: shelfZone.centerZ - shelfZone.halfHeight,
      maxZ: shelfZone.centerZ + shelfZone.halfHeight,
    };
    this._bindEvents();
  }

  /** Register a mesh as draggable. */
  register(mesh: THREE.Object3D, zoneY: number = 0.005): void {
    mesh.userData.draggable = true;
    mesh.userData.zone = 'SHELF_ZONE';
    mesh.userData.dragY = zoneY;
  }

  /** Call each frame. dt = delta time in seconds. */
  update(draggables: THREE.Object3D[], dt: number): void {
    if (this._dragging) {
      // Lerp object toward drag target
      this._dragging.position.lerp(this._dragTarget, this._config.lerpFactor);
      this._velocity.copy(this._dragTarget).sub(this._dragging.position);
    } else if (this._velocity.length() > 0.001) {
      // Settle — decay velocity
      const decay = Math.pow(0.5, 1 / this._config.settleFrames);
      this._velocity.multiplyScalar(decay);
    }
  }

  private _bindEvents(): void {
    const canvas = this._renderer.domElement;
    canvas.addEventListener('pointerdown', this._onPointerDown);
    canvas.addEventListener('pointermove', this._onPointerMove);
    canvas.addEventListener('pointerup', this._onPointerUp);
    canvas.addEventListener('pointercancel', this._onPointerUp);
  }

  private _onPointerDown = (e: PointerEvent): void => {
    if (e.button !== 0) return;
    // Raycast against draggable meshes
    const ndc = this._toNDC(e);
    this._raycaster.setFromCamera(ndc, this._camera);
    // Caller must pass draggables list — handled via update loop
    // Simple approach: store pointer position, resolve in first pointermove
    this._planeY = 0.005; // shelf surface Y
    this._dragPlane.constant = -this._planeY;
    this._raycaster.ray.intersectPlane(this._dragPlane, this._pointerWorld);
  }

  private _onPointerMove = (e: PointerEvent): void => {
    if (!this._dragging) return;
    const ndc = this._toNDC(e);
    this._raycaster.setFromCamera(ndc, this._camera);
    this._raycaster.ray.intersectPlane(this._dragPlane, this._pointerWorld);

    // Clamp to shelf bounds
    const cx = Math.max(this._shelfBounds.minX, Math.min(this._shelfBounds.maxX, this._pointerWorld.x));
    const cz = Math.max(this._shelfBounds.minZ, Math.min(this._shelfBounds.maxZ, this._pointerWorld.z));
    this._dragTarget.set(cx, this._planeY, cz);
  }

  private _onPointerUp = (_e: PointerEvent): void => {
    this._dragging = null;
  }

  private _toNDC(e: PointerEvent): THREE.Vector2 {
    const rect = this._renderer.domElement.getBoundingClientRect();
    return new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1,
    );
  }

  /** Called from outside when raycast hit confirms a draggable mesh. */
  startDrag(mesh: THREE.Object3D): void {
    this._dragging = mesh;
    this._dragTarget.copy(mesh.position);
    this._velocity.set(0, 0, 0);
  }
}
```

**Integration in `main.ts`:**

```typescript
import { ShelfDragController } from './shelf-drag';

// After objects are built:
const _shelfDrag = new ShelfDragController(
  camera,
  renderer,
  ZONES.find(z => z.name === 'SHELF_ZONE')!,
);

// Register draggable objects
_shelfDrag.register(characterSheetMesh!);
_shelfDrag.register(notebookMesh!);
_shelfDrag.register(tomeMesh!);
_shelfDrag.register(diceBagMesh!);

// In animation loop:
_shelfDrag.update([...draggables], dt);

// In pointerdown handler on canvas (after raycast):
const hits = raycaster.intersectObjects([characterSheetMesh!, notebookMesh!, tomeMesh!, diceBagMesh!]);
if (hits.length > 0 && hits[0].object.userData.draggable) {
  _shelfDrag.startDrag(hits[0].object);
}
```

### 4.2 Zone enforcement

The `ShelfDragController` clamps to SHELF_ZONE bounds on every move event. No object can cross into VAULT_ZONE or DM_ZONE — the clamp is a hard constraint, not a spring.

### 4.3 Exposed mesh references

Currently `characterSheetMesh` is exported from `scene-builder.ts`. Add exports for notebook and tome meshes (same pattern):

```typescript
// In scene-builder.ts:
export let notebookMesh: THREE.Mesh | null = null;  // assigned in buildObjectStubs
export let tomeMesh: THREE.Mesh | null = null;       // assigned in buildObjectStubs
export let diceBagMesh: THREE.Object3D | null = null; // assigned in buildObjectStubs or DiceBagObject
```

---

## 5. Gate Spec

**Gate name:** `UI-PHYSICALITY-BASELINE`
**Test file:** `client/tests/shelf_drag.spec.ts`

Gate passes when (Playwright):

1. Pointerdown on notebook mesh → mesh userData.draggable is true
2. Drag notebook 1.0 unit in X → position changed (mesh moved)
3. Drag notebook to x=−10 (outside shelf bounds) → position clamped to SHELF_ZONE.minX
4. Drag notebook to z=+10 (outside shelf bounds) → position clamped to SHELF_ZONE.maxZ
5. Release at any valid position → mesh settles (no continued motion after 500ms)
6. Character sheet is draggable (same test: drag 0.5 units, confirm position changes)
7. Rulebook is draggable
8. No object can be dragged past z < (SHELF_ZONE.centerZ − SHELF_ZONE.halfHeight)
   — i.e., objects cannot leave the shelf toward the vault

**Test count target:** 8 checks → Gate `UI-PHYSICALITY-BASELINE` 8/8.

---

## 6. What This WO Does NOT Do

- Dice are not draggable from bag to tower (that is a future WO)
- Token drag is not included (EntityRenderer owns tokens)
- Handouts are not constrained (they slide from DM side by design)
- No collision between shelf objects — they can overlap if dragged onto each other
- No screenshot tests (WO-UI-GATES-V1)

---

## 7. Preflight

```bash
npm run dev --prefix client
# Press 2 (DOWN posture — best view for shelf interaction)
# Click and drag notebook — should slide with weight feel
# Drag to edge of shelf — should clamp, not escape
# Release — should settle without bouncing
```

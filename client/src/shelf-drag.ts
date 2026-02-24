/**
 * ShelfDragController — kinematic drag for SHELF_ZONE artifacts.
 *
 * Physics class: KINEMATIC_DRAG (per table_objects.json).
 * Constraint: SHELF_ZONE bounds — hard clamp, no spring at boundary.
 * Feel: lerp factor 0.18/frame → "heavy paper on wood" weight.
 * Settle: 8-frame velocity half-life on release.
 *
 * Authority: WO-UI-PHYSICALITY-BASELINE-V1
 */

import * as THREE from 'three';
import type { ZoneDef } from './zones';

export interface DragConfig {
  lerpFactor: number;   // 0.18 — how fast object tracks pointer
  settleFrames: number; // 8 — velocity half-life frames on release
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
  private _registeredMeshes: THREE.Object3D[] = [];

  constructor(
    private _camera: THREE.PerspectiveCamera,
    private _renderer: THREE.WebGLRenderer,
    shelfZone: ZoneDef,
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

  /**
   * Register a mesh as draggable in SHELF_ZONE.
   * Sets userData.draggable = true, userData.zone = 'SHELF_ZONE'.
   */
  register(mesh: THREE.Object3D): void {
    mesh.userData.draggable = true;
    mesh.userData.zone = 'SHELF_ZONE';
    mesh.userData.dragY = mesh.position.y;
    this._registeredMeshes.push(mesh);
  }

  /**
   * Call each frame in the animation loop.
   * dt = delta time in seconds (unused here — lerp is frame-rate dependent by design
   * to match the "heavy paper" feel specified in the dispatch: 0.18/frame at 60fps).
   */
  update(_dt: number): void {
    if (this._dragging) {
      // Weighted lerp toward drag target
      this._dragging.position.lerp(this._dragTarget, this._config.lerpFactor);
      // Track velocity as difference between target and current
      this._velocity
        .copy(this._dragTarget)
        .sub(this._dragging.position);
    } else if (this._velocity.lengthSq() > 1e-6) {
      // Settle — exponential decay toward zero
      const decay = Math.pow(0.5, 1 / this._config.settleFrames);
      this._velocity.multiplyScalar(decay);
      if (this._velocity.lengthSq() < 1e-6) {
        this._velocity.set(0, 0, 0);
      }
    }
  }

  /** True if an object is currently being dragged. */
  get isDragging(): boolean {
    return this._dragging !== null;
  }

  /** The object currently being dragged, or null. */
  get dragging(): THREE.Object3D | null {
    return this._dragging;
  }

  private _toNDC(e: PointerEvent): THREE.Vector2 {
    const rect = this._renderer.domElement.getBoundingClientRect();
    return new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1,
    );
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
    if (this._registeredMeshes.length === 0) return;

    const ndc = this._toNDC(e);
    this._raycaster.setFromCamera(ndc, this._camera);

    // Raycast against all registered draggable meshes
    const hits = this._raycaster.intersectObjects(this._registeredMeshes, false);
    if (hits.length === 0) return;

    const hitObj = hits[0].object;
    if (!hitObj.userData.draggable) return;

    // Store resting Y and renderOrder before lift
    this._planeY = hitObj.userData.dragY ?? hitObj.position.y;
    hitObj.userData.restRenderOrder = hitObj.renderOrder;

    // Lift-on-grab: raise 0.08 units + bring to front via renderOrder
    const LIFT = 0.08;
    const liftY = this._planeY + LIFT;
    this._dragPlane.constant = -liftY;
    hitObj.position.y = liftY;
    hitObj.renderOrder = 999;  // paint on top of all shelf objects

    // Snap target to current position; let lerp close the gap
    this._dragTarget.copy(hitObj.position);
    this._velocity.set(0, 0, 0);
    this._dragging = hitObj;
  };

  private _onPointerMove = (e: PointerEvent): void => {
    if (!this._dragging) return;

    const ndc = this._toNDC(e);
    this._raycaster.setFromCamera(ndc, this._camera);
    this._raycaster.ray.intersectPlane(this._dragPlane, this._pointerWorld);

    // Hard clamp to SHELF_ZONE bounds
    const cx = Math.max(this._shelfBounds.minX, Math.min(this._shelfBounds.maxX, this._pointerWorld.x));
    const cz = Math.max(this._shelfBounds.minZ, Math.min(this._shelfBounds.maxZ, this._pointerWorld.z));
    this._dragTarget.set(cx, this._planeY, cz);
  };

  private _onPointerUp = (_e: PointerEvent): void => {
    if (this._dragging) {
      // Snap back to resting Y and restore renderOrder on release
      this._dragging.position.y = this._planeY;
      this._dragging.renderOrder = this._dragging.userData.restRenderOrder ?? 0;
    }
    this._dragging = null;
    // velocity decays naturally in update() — no snap on release
  };
}

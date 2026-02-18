/**
 * Drag interaction system — pick/drag/drop for TableObjects.
 *
 * Uses Three.js raycasting against a table-surface plane for drag positioning.
 * Enforces zone constraints with snap-back on invalid drops.
 * Disables camera controls during drag.
 * Supports keyboard-only path (Tab/Enter/Arrow/Escape).
 *
 * Authority: WO-UI-02, DOCTRINE_04_TABLE_UI_MEMO_V4 §6, §17, §19.
 */

import * as THREE from 'three';
import { TableObject, TableObjectRegistry, TableObjectPosition } from './table-object';
import { zoneAtPosition } from './zones';
import { WsBridge } from './ws-bridge';

const TABLE_Y = 0.0;
const LIFT_HEIGHT = 0.15;
const KEYBOARD_STEP = 0.5;

export interface DragCallbacks {
  /** Called when drag starts — disable camera controls. */
  onDragStart?: () => void;
  /** Called when drag ends — re-enable camera controls. */
  onDragEnd?: () => void;
}

/**
 * DragInteraction manages pointer and keyboard pick/drag/drop for all
 * TableObjects in a registry.
 */
export class DragInteraction {
  private registry: TableObjectRegistry;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private scene: THREE.Scene;
  private bridge: WsBridge;
  private callbacks: DragCallbacks;

  private raycaster = new THREE.Raycaster();
  private pointer = new THREE.Vector2();
  private tablePlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  private intersection = new THREE.Vector3();

  private pickOrigin: TableObjectPosition | null = null;
  private pickZone: string | null = null;
  private isDragging = false;
  private dragMoved = false;

  // Keyboard focus
  private _focusIndex = -1;
  private _focusHighlight: THREE.Mesh | null = null;

  constructor(
    registry: TableObjectRegistry,
    camera: THREE.PerspectiveCamera,
    renderer: THREE.WebGLRenderer,
    scene: THREE.Scene,
    bridge: WsBridge,
    callbacks: DragCallbacks = {},
  ) {
    this.registry = registry;
    this.camera = camera;
    this.renderer = renderer;
    this.scene = scene;
    this.bridge = bridge;
    this.callbacks = callbacks;

    this._bindPointerEvents();
    this._bindKeyboardEvents();
  }

  /** Whether a drag is currently in progress. */
  get dragging(): boolean {
    return this.isDragging;
  }

  // -----------------------------------------------------------------------
  // Pointer events
  // -----------------------------------------------------------------------

  private _bindPointerEvents(): void {
    const el = this.renderer.domElement;

    el.addEventListener('pointerdown', (e) => this._onPointerDown(e));
    el.addEventListener('pointermove', (e) => this._onPointerMove(e));
    el.addEventListener('pointerup', (e) => this._onPointerUp(e));
    el.addEventListener('contextmenu', (e) => {
      if (this.isDragging) {
        e.preventDefault();
        this._cancelDrag();
      }
    });
  }

  private _updatePointer(e: PointerEvent): void {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  }

  private _hitTableObject(e: PointerEvent): TableObject | null {
    this._updatePointer(e);
    this.raycaster.setFromCamera(this.pointer, this.camera);

    const pickables = this.registry.pickables();
    const meshes = pickables.map(o => o.object3D);
    const hits = this.raycaster.intersectObjects(meshes, true);
    if (hits.length === 0) return null;

    // Find which TableObject owns the hit mesh
    for (const hit of hits) {
      let obj3d: THREE.Object3D | null = hit.object;
      while (obj3d) {
        for (const to of pickables) {
          if (to.object3D === obj3d) return to;
        }
        obj3d = obj3d.parent;
      }
    }
    return null;
  }

  private _tablePlaneIntersection(e: PointerEvent): THREE.Vector3 | null {
    this._updatePointer(e);
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hit = this.raycaster.ray.intersectPlane(this.tablePlane, this.intersection);
    return hit;
  }

  private _onPointerDown(e: PointerEvent): void {
    if (e.button !== 0) return; // left button only
    if (this.isDragging) return;

    const obj = this._hitTableObject(e);
    if (!obj) return;

    const picked = this.registry.pick(obj.id);
    if (!picked) return;

    this.pickOrigin = { ...picked.position };
    this.pickZone = picked.zone;
    this.isDragging = true;
    this.dragMoved = false;
    picked.onPick();

    if (this.callbacks.onDragStart) this.callbacks.onDragStart();
    this._clearFocus();
  }

  private _onPointerMove(e: PointerEvent): void {
    if (!this.isDragging) return;
    const picked = this.registry.picked;
    if (!picked) return;

    const pt = this._tablePlaneIntersection(e);
    if (!pt) return;

    this.dragMoved = true;
    const zone = zoneAtPosition(pt.x, pt.z);
    const newPos: TableObjectPosition = {
      x: pt.x,
      y: TABLE_Y + LIFT_HEIGHT,
      z: pt.z,
    };
    picked.onDrag(newPos);
    picked.position = newPos;

    // Visual feedback: update zone color/glow based on validity
    if (zone) {
      picked.zone = zone;
    }
  }

  private _onPointerUp(e: PointerEvent): void {
    if (e.button !== 0) return;
    if (!this.isDragging) return;

    const picked = this.registry.picked;
    if (!picked) {
      this._endDrag();
      return;
    }

    // If pointer didn't move, this is a click — not a drag
    if (!this.dragMoved) {
      this._endDrag();
      return;
    }

    const zone = zoneAtPosition(picked.position.x, picked.position.z);
    if (zone) {
      // Valid drop
      const dropPos: TableObjectPosition = {
        x: picked.position.x,
        y: TABLE_Y + 0.05,
        z: picked.position.z,
      };
      picked.position = dropPos;
      picked.zone = zone;
      picked.onDrop(zone);
      this._sendPositionUpdate(picked, dropPos, zone);
    } else {
      // Invalid zone — snap back
      this._snapBack(picked);
    }

    this._endDrag();
  }

  private _cancelDrag(): void {
    const picked = this.registry.picked;
    if (picked && this.pickOrigin) {
      this._snapBack(picked);
    }
    this._endDrag();
  }

  private _snapBack(obj: TableObject): void {
    if (this.pickOrigin && this.pickZone) {
      obj.position = { ...this.pickOrigin };
      obj.zone = this.pickZone;
      obj.object3D.position.set(this.pickOrigin.x, this.pickOrigin.y, this.pickOrigin.z);
      obj.onDrop(this.pickZone);
    }
  }

  private _endDrag(): void {
    this.registry.drop();
    this.isDragging = false;
    this.dragMoved = false;
    this.pickOrigin = null;
    this.pickZone = null;
    if (this.callbacks.onDragEnd) this.callbacks.onDragEnd();
  }

  private _sendPositionUpdate(
    obj: TableObject,
    pos: TableObjectPosition,
    zone: string,
  ): void {
    this.bridge.send({
      msg_type: 'player_action',
      msg_id: crypto.randomUUID(),
      timestamp: Date.now() / 1000,
      action_type: 'object_position_update',
      payload: {
        type: 'OBJECT_POSITION_UPDATE',
        object_id: obj.id,
        new_position: [pos.x, pos.y, pos.z],
        new_zone: zone,
      },
    });
  }

  // -----------------------------------------------------------------------
  // Keyboard interaction (doctrine §6)
  // -----------------------------------------------------------------------

  private _bindKeyboardEvents(): void {
    window.addEventListener('keydown', (e) => this._onKeyDown(e));
  }

  private _onKeyDown(e: KeyboardEvent): void {
    // Don't intercept camera posture keys (1/2/3) when not dragging
    if (['1', '2', '3'].includes(e.key) && !this.isDragging) return;

    switch (e.key) {
      case 'Tab':
        e.preventDefault();
        this._cycleFocus(e.shiftKey ? -1 : 1);
        break;

      case 'Enter':
      case ' ':
        e.preventDefault();
        if (this.isDragging) {
          this._keyboardDrop();
        } else {
          this._keyboardPick();
        }
        break;

      case 'Escape':
        if (this.isDragging) {
          e.preventDefault();
          this._cancelDrag();
        }
        break;

      case 'ArrowUp':
        if (this.isDragging) { e.preventDefault(); this._keyboardMove(0, -KEYBOARD_STEP); }
        break;
      case 'ArrowDown':
        if (this.isDragging) { e.preventDefault(); this._keyboardMove(0, KEYBOARD_STEP); }
        break;
      case 'ArrowLeft':
        if (this.isDragging) { e.preventDefault(); this._keyboardMove(-KEYBOARD_STEP, 0); }
        break;
      case 'ArrowRight':
        if (this.isDragging) { e.preventDefault(); this._keyboardMove(KEYBOARD_STEP, 0); }
        break;
    }
  }

  private _cycleFocus(dir: number): void {
    if (this.isDragging) return;

    const pickables = this.registry.pickables();
    if (pickables.length === 0) return;

    this._focusIndex += dir;
    if (this._focusIndex < 0) this._focusIndex = pickables.length - 1;
    if (this._focusIndex >= pickables.length) this._focusIndex = 0;

    this._showFocusHighlight(pickables[this._focusIndex]);
  }

  private _showFocusHighlight(obj: TableObject): void {
    this._clearFocus();

    // Create a ring/outline around the focused object
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(0.9, 1.0, 32),
      new THREE.MeshBasicMaterial({ color: 0xffe066, side: THREE.DoubleSide }),
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.set(obj.position.x, obj.position.y + 0.02, obj.position.z);
    ring.name = '__focus_highlight__';
    this.scene.add(ring);
    this._focusHighlight = ring;
  }

  private _clearFocus(): void {
    if (this._focusHighlight) {
      this.scene.remove(this._focusHighlight);
      this._focusHighlight.geometry.dispose();
      (this._focusHighlight.material as THREE.Material).dispose();
      this._focusHighlight = null;
    }
  }

  private _keyboardPick(): void {
    const pickables = this.registry.pickables();
    if (this._focusIndex < 0 || this._focusIndex >= pickables.length) return;

    const obj = pickables[this._focusIndex];
    const picked = this.registry.pick(obj.id);
    if (!picked) return;

    this.pickOrigin = { ...picked.position };
    this.pickZone = picked.zone;
    this.isDragging = true;
    this.dragMoved = false;
    picked.onPick();

    if (this.callbacks.onDragStart) this.callbacks.onDragStart();
    this._clearFocus();
  }

  private _keyboardMove(dx: number, dz: number): void {
    const picked = this.registry.picked;
    if (!picked) return;

    this.dragMoved = true;
    const newPos: TableObjectPosition = {
      x: picked.position.x + dx,
      y: TABLE_Y + LIFT_HEIGHT,
      z: picked.position.z + dz,
    };
    picked.onDrag(newPos);
    picked.position = newPos;

    const zone = zoneAtPosition(newPos.x, newPos.z);
    if (zone) picked.zone = zone;
  }

  private _keyboardDrop(): void {
    const picked = this.registry.picked;
    if (!picked) return;

    const zone = zoneAtPosition(picked.position.x, picked.position.z);
    if (zone) {
      const dropPos: TableObjectPosition = {
        x: picked.position.x,
        y: TABLE_Y + 0.05,
        z: picked.position.z,
      };
      picked.position = dropPos;
      picked.zone = zone;
      picked.onDrop(zone);
      this._sendPositionUpdate(picked, dropPos, zone);
    } else {
      this._snapBack(picked);
    }

    this._endDrag();
  }

  /** Apply server acknowledgment — update object position from server response. */
  applyServerAck(objectId: string, position: [number, number, number], zone: string): void {
    const obj = this.registry.get(objectId);
    if (!obj) return;
    obj.position = { x: position[0], y: position[1], z: position[2] };
    obj.zone = zone;
    obj.object3D.position.set(position[0], position[1], position[2]);
  }

  /** Apply server rejection — snap object back (already handled by optimistic snap-back). */
  applyServerReject(objectId: string): void {
    // Optimistic snap-back already handled in drop logic.
    // This is a no-op unless the server sends a corrected position later.
  }

  /** Update focus highlight position each frame (if visible). */
  updateFocusHighlight(): void {
    if (!this._focusHighlight) return;
    const pickables = this.registry.pickables();
    if (this._focusIndex >= 0 && this._focusIndex < pickables.length) {
      const obj = pickables[this._focusIndex];
      this._focusHighlight.position.set(obj.position.x, obj.position.y + 0.02, obj.position.z);
    }
  }
}

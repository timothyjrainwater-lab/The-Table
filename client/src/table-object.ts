/**
 * TableObject — base interface and registry for objects on the table surface.
 *
 * Every TableObject has an id, kind, position, zone, pickable flag, and
 * a Three.js Object3D for rendering. Lifecycle: spawn, pick, drag, drop, destroy.
 *
 * Only one object may be picked at a time (single-selection constraint).
 *
 * Authority: WO-UI-02, DOCTRINE_04_TABLE_UI_MEMO_V4 §19 Slice 1.
 */

import * as THREE from 'three';

export interface TableObjectPosition {
  x: number;
  y: number;
  z: number;
}

/**
 * TableObject interface — implemented by every object type on the table.
 */
export interface TableObject {
  readonly id: string;
  readonly kind: string;
  position: TableObjectPosition;
  zone: string;
  pickable: boolean;
  readonly object3D: THREE.Object3D;

  /** Called when the object is added to the scene. */
  onSpawn(): void;

  /** Called when the object is picked up. */
  onPick(): void;

  /** Called each frame while dragged. */
  onDrag(position: TableObjectPosition): void;

  /** Called when the object is dropped in a zone. */
  onDrop(zone: string): void;

  /** Called when the object is removed from the scene. */
  onDestroy(): void;
}

/**
 * Registry of all TableObjects on the table.
 * Lookup by id, iteration, single-selection enforcement.
 */
export class TableObjectRegistry {
  private objects: Map<string, TableObject> = new Map();
  private _pickedId: string | null = null;

  add(obj: TableObject): void {
    this.objects.set(obj.id, obj);
  }

  get(id: string): TableObject | undefined {
    return this.objects.get(id);
  }

  remove(id: string): TableObject | undefined {
    const obj = this.objects.get(id);
    if (obj) {
      this.objects.delete(id);
      if (this._pickedId === id) {
        this._pickedId = null;
      }
    }
    return obj;
  }

  all(): TableObject[] {
    return Array.from(this.objects.values());
  }

  pickables(): TableObject[] {
    return this.all().filter(o => o.pickable);
  }

  /** The currently picked object, or null. */
  get picked(): TableObject | null {
    if (this._pickedId === null) return null;
    return this.objects.get(this._pickedId) ?? null;
  }

  /** Pick an object by id. Enforces single-selection. */
  pick(id: string): TableObject | null {
    if (this._pickedId !== null) return null; // already picking
    const obj = this.objects.get(id);
    if (!obj || !obj.pickable) return null;
    this._pickedId = id;
    return obj;
  }

  /** Drop the currently picked object. */
  drop(): TableObject | null {
    if (this._pickedId === null) return null;
    const obj = this.objects.get(this._pickedId) ?? null;
    this._pickedId = null;
    return obj;
  }

  /** Whether an object is currently picked. */
  get isPicking(): boolean {
    return this._pickedId !== null;
  }

  get size(): number {
    return this.objects.size;
  }
}

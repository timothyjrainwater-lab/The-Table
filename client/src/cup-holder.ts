import * as THREE from 'three';

const MAX_STACK = 5;

export interface SoftDeleteItem {
  id: string;
  object3D: THREE.Object3D;
  originalOpacity: number;
}

/**
 * SoftDeleteStack — cup holder soft delete system.
 *
 * Drag any table object to cup holder → dims + stores (max 5).
 * Click cup holder → retrieve last item.
 *
 * Gate: 3 tests (regression guard).
 * Gate G compliant.
 */
export class SoftDeleteStack {
  private _stack: SoftDeleteItem[] = [];
  private _onStackChange: (count: number) => void;

  constructor(onStackChange: (count: number) => void = () => {}) {
    this._onStackChange = onStackChange;
  }

  /** Push an item onto the soft-delete stack. Dims it. Max 5 items. */
  push(id: string, object3D: THREE.Object3D): boolean {
    if (this._stack.length >= MAX_STACK) return false;

    // Dim the object
    let originalOpacity = 1.0;
    object3D.traverse((child) => {
      if ((child as THREE.Mesh).material) {
        const mat = (child as THREE.Mesh).material as THREE.MeshStandardMaterial;
        if (mat.opacity !== undefined) {
          originalOpacity = mat.opacity;
          mat.transparent = true;
          mat.opacity = 0.25;
        }
      }
    });

    this._stack.push({ id, object3D, originalOpacity });
    this._onStackChange(this._stack.length);
    return true;
  }

  /** Pop the last item — restores opacity and returns it. */
  pop(): SoftDeleteItem | null {
    const item = this._stack.pop() ?? null;
    if (item) {
      item.object3D.traverse((child) => {
        if ((child as THREE.Mesh).material) {
          const mat = (child as THREE.Mesh).material as THREE.MeshStandardMaterial;
          mat.opacity = item.originalOpacity;
          mat.transparent = item.originalOpacity < 1.0;
        }
      });
      this._onStackChange(this._stack.length);
    }
    return item;
  }

  get count(): number { return this._stack.length; }
  get isFull(): boolean { return this._stack.length >= MAX_STACK; }
  get isEmpty(): boolean { return this._stack.length === 0; }
}

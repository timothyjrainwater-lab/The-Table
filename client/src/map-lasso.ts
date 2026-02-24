import * as THREE from 'three';

const LASSO_Y       = -0.03;   // just above felt vault
const LINGER_MS     = 8000;    // 8s before fade
const FADE_MS       = 500;     // fade duration

/**
 * MapLassoManager — click-hold + drag on map draws ephemeral lasso.
 *
 * PENDING gate (WO-UI-MAP-01): intent is only emitted when a PENDING kind is
 * active. Drag without PENDING is cosmetic-only (lasso drawn, no intent sent).
 * Call setPending(kind) before the drag to enable intent emission.
 *
 * Emits MAP_AREA_INTENT with polygon on drag complete (PENDING required).
 * Overlay lingers 8s then fades.
 *
 * Gate: 4 tests (regression guard).
 * Gate G compliant.
 */
export class MapLassoManager {
  private _scene: THREE.Scene;
  private _onIntent: (kind: string, polygon: Array<{x: number; z: number}>) => void;
  private _isDragging: boolean = false;
  private _points: Array<{x: number; z: number}> = [];
  private _lassoMesh: THREE.Line | null = null;
  private _lingerTimer: ReturnType<typeof setTimeout> | null = null;
  private _activePending: string | null = null;

  constructor(
    scene: THREE.Scene,
    onIntent: (kind: string, polygon: Array<{x: number; z: number}>) => void,
  ) {
    this._scene = scene;
    this._onIntent = onIntent;
  }

  /** Activate a PENDING kind — unlocks intent emission on drag complete. */
  setPending(kind: string): void {
    this._activePending = kind;
  }

  /** Clear active PENDING — drag becomes cosmetic-only again. */
  clearPending(): void {
    this._activePending = null;
  }

  get activePending(): string | null {
    return this._activePending;
  }

  /** Called on pointerdown over map area. worldPos = Three.js XZ coords. */
  startDrag(worldPos: {x: number; z: number}): void {
    this._isDragging = true;
    this._points = [worldPos];
    this._clearExisting();
  }

  /** Called on pointermove while dragging. */
  updateDrag(worldPos: {x: number; z: number}): void {
    if (!this._isDragging) return;
    this._points.push(worldPos);
    this._updateLassoMesh();
  }

  /** Called on pointerup — finalize lasso; emit intent only if PENDING active. */
  endDrag(kind: 'SEARCH' | 'AIM' | 'DISCUSS' = 'SEARCH'): void {
    if (!this._isDragging) return;
    this._isDragging = false;
    if (this._points.length < 2) { this._clearExisting(); return; }
    // Close the polygon
    this._points.push(this._points[0]);
    this._updateLassoMesh();
    // PENDING gate: only emit intent when a PENDING kind is active
    if (this._activePending !== null) {
      this._onIntent(kind, [...this._points]);
    }
    // Linger then fade (cosmetic — always happens regardless of PENDING)
    this._startLinger();
  }

  get isDragging(): boolean { return this._isDragging; }
  get pointCount(): number { return this._points.length; }

  dispose(): void {
    this._clearExisting();
  }

  private _updateLassoMesh(): void {
    if (this._lassoMesh) {
      this._scene.remove(this._lassoMesh);
      this._lassoMesh.geometry.dispose();
    }
    if (this._points.length < 2) return;
    const positions: number[] = [];
    for (const p of this._points) {
      positions.push(p.x, LASSO_Y, p.z);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const mat = new THREE.LineBasicMaterial({ color: 0xffee44, linewidth: 2 });
    this._lassoMesh = new THREE.Line(geo, mat);
    this._lassoMesh.name = 'map_lasso';
    this._scene.add(this._lassoMesh);
  }

  private _startLinger(): void {
    if (this._lingerTimer) clearTimeout(this._lingerTimer);
    this._lingerTimer = setTimeout(() => {
      this._lingerTimer = null;
      // Fade opacity 1→0 over FADE_MS using rAF loop
      if (!this._lassoMesh) return;
      const mat = this._lassoMesh.material as THREE.LineBasicMaterial;
      mat.transparent = true;
      const startTime = performance.now();
      const mesh = this._lassoMesh;
      const step = (now: number): void => {
        const t = Math.min((now - startTime) / FADE_MS, 1.0);
        mat.opacity = 1.0 - t;
        mat.needsUpdate = true;
        if (t < 1.0) {
          requestAnimationFrame(step);
        } else {
          this._scene.remove(mesh);
          mesh.geometry.dispose();
          (mesh.material as THREE.Material).dispose();
          if (this._lassoMesh === mesh) this._lassoMesh = null;
        }
      };
      requestAnimationFrame(step);
    }, LINGER_MS);
  }

  private _clearExisting(): void {
    if (this._lingerTimer) { clearTimeout(this._lingerTimer); this._lingerTimer = null; }
    if (this._lassoMesh) {
      this._scene.remove(this._lassoMesh);
      this._lassoMesh.geometry.dispose();
      (this._lassoMesh.material as THREE.Material).dispose();
      this._lassoMesh = null;
    }
    this._points = [];
    this._isDragging = false;
  }
}

export { LINGER_MS, FADE_MS };

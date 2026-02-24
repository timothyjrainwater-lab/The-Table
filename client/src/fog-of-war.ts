import * as THREE from 'three';

/** 1 grid unit = 0.5 Three.js scene units (same as entity-renderer scale). */
const GRID_SCALE = 0.5;

/** Y position of fog overlay — just above table surface. */
const FOG_Y = 0.01;

/** Opacity values for fog states. */
const OPACITY_HIDDEN    = 0.9;  // never seen
const OPACITY_REVEALED  = 0.3;  // seen but not currently visible
const OPACITY_VISIBLE   = 0.0;  // currently in vision range

const FADE_DURATION = 0.3; // seconds for opacity transitions

/**
 * WO-UI-FOG-VISION-001: Vision type differentiation.
 * normal     — standard sight, black fog overlay.
 * low_light  — treats dim light as bright; 2× reveal radius.
 * darkvision — sees in darkness up to range; dark blue-gray tint.
 */
export type VisionType = 'normal' | 'low_light' | 'darkvision';

/** Fog color per vision type. */
const FOG_COLOR_NORMAL     = 0x000000; // black — standard obscurement
const FOG_COLOR_DARKVISION = 0x1a1a2e; // dark blue-gray — colorless darkvision tint

interface FogCell {
  mesh: THREE.Mesh;
  mat: THREE.MeshBasicMaterial;
  revealed: boolean;
  targetOpacity: number;  // lerp destination
}

/**
 * FogOfWarManager — grid-cell opacity overlay.
 *
 * Gate UI-FOG: 10 tests.
 * Gate UI-FOG-VISION: 5 tests.
 * Seeded PRNG only (Gate G compliant).
 */
export class FogOfWarManager {
  private scene: THREE.Scene;
  private cells: Map<string, FogCell> = new Map();
  private mapGroup: THREE.Group = new THREE.Group();

  /** WO-UI-FOG-VISION-001: Entity vision type registry. */
  private entityVisions: Map<string, VisionType> = new Map();

  constructor(scene: THREE.Scene) {
    this.scene = scene;
    this.scene.add(this.mapGroup);
  }

  /**
   * WO-UI-FOG-VISION-001: Register or update an entity's vision type.
   * Called from main.ts on entity_state events with VISION_TYPE field.
   */
  setEntityVision(entityId: string, visionType: VisionType): void {
    this.entityVisions.set(entityId, visionType);
  }

  /**
   * WO-UI-FOG-VISION-001: Return the reveal radius multiplier for an entity.
   * low_light entities treat dim light as bright — 2× effective radius.
   */
  getRevealRadius(entityId: string, baseRadius = 1): number {
    const vision = this.entityVisions.get(entityId);
    return vision === 'low_light' ? baseRadius * 2 : baseRadius;
  }

  /**
   * WO-UI-FOG-VISION-001: Return the dominant vision type across all registered entities.
   * Used to decide fog cell color (darkvision → dark blue-gray tint).
   */
  private _dominantVision(): VisionType {
    for (const v of this.entityVisions.values()) {
      if (v === 'darkvision') return 'darkvision';
    }
    return 'normal';
  }

  /**
   * Handle fog_update WS event.
   * revealed_cells: ever seen (dim). visible_cells: currently in vision (clear).
   * unrevealed cells stay dark.
   */
  handleFogUpdate(data: {
    revealed_cells: Array<{x: number; y: number}>;
    visible_cells: Array<{x: number; y: number}>;
    map_bounds: {x: number; y: number; width: number; height: number};
  }): void {
    const { revealed_cells, visible_cells, map_bounds } = data;

    // Ensure all cells in bounds exist
    this._ensureCells(map_bounds);

    // Apply darkvision color tint if any entity has darkvision
    const vision = this._dominantVision();
    const fogColor = vision === 'darkvision' ? FOG_COLOR_DARKVISION : FOG_COLOR_NORMAL;
    for (const cell of this.cells.values()) {
      cell.mat.color.set(fogColor);
    }

    // Build lookup sets
    const visibleSet  = new Set(visible_cells.map(c => this._key(c.x, c.y)));
    const revealedSet = new Set(revealed_cells.map(c => this._key(c.x, c.y)));

    // Update cell states — set targetOpacity, let tick() lerp to it
    for (const [key, cell] of this.cells) {
      if (visibleSet.has(key)) {
        cell.revealed = true;
        cell.targetOpacity = OPACITY_VISIBLE;
      } else if (revealedSet.has(key) || cell.revealed) {
        // Accumulate: once revealed, stays dim
        cell.revealed = true;
        cell.targetOpacity = OPACITY_REVEALED;
      } else {
        cell.targetOpacity = OPACITY_HIDDEN;
      }
    }
  }

  /**
   * Call from the render loop each frame to animate fog opacity fades.
   * dt = frame delta in seconds.
   */
  tick(dt: number): void {
    const step = dt / FADE_DURATION;
    for (const cell of this.cells.values()) {
      const cur = cell.mat.opacity;
      const tgt = cell.targetOpacity;
      if (Math.abs(cur - tgt) < 0.001) {
        cell.mat.opacity = tgt;
      } else {
        cell.mat.opacity = cur + Math.sign(tgt - cur) * Math.min(Math.abs(tgt - cur), step);
        cell.mat.needsUpdate = true;
      }
    }
  }

  /** Get cell count for a given map_bounds (for testing). */
  getCellCount(): number {
    return this.cells.size;
  }

  /** Get cell at grid coords (for testing). */
  getCell(x: number, y: number): FogCell | undefined {
    return this.cells.get(this._key(x, y));
  }

  /** Remove all fog meshes from scene. */
  dispose(): void {
    for (const cell of this.cells.values()) {
      cell.mat.dispose();
      cell.mesh.geometry.dispose();
      this.mapGroup.remove(cell.mesh);
    }
    this.cells.clear();
    this.scene.remove(this.mapGroup);
  }

  private _key(x: number, y: number): string {
    return `${x},${y}`;
  }

  private _ensureCells(bounds: {x: number; y: number; width: number; height: number}): void {
    for (let gx = bounds.x; gx < bounds.x + bounds.width; gx++) {
      for (let gy = bounds.y; gy < bounds.y + bounds.height; gy++) {
        const key = this._key(gx, gy);
        if (!this.cells.has(key)) {
          this._createCell(gx, gy, key);
        }
      }
    }
  }

  private _createCell(gx: number, gy: number, key: string): void {
    const geo = new THREE.PlaneGeometry(GRID_SCALE, GRID_SCALE);
    const mat = new THREE.MeshBasicMaterial({
      color: FOG_COLOR_NORMAL,
      transparent: true,
      opacity: OPACITY_HIDDEN,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    // Position cell at grid center, rotate flat
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(
      gx * GRID_SCALE + GRID_SCALE / 2,
      FOG_Y,
      gy * GRID_SCALE + GRID_SCALE / 2,
    );
    mesh.name = `fog_cell_${gx}_${gy}`;
    this.mapGroup.add(mesh);
    this.cells.set(key, { mesh, mat, revealed: false, targetOpacity: OPACITY_HIDDEN });
  }
}

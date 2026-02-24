/**
 * MapOverlay — Slice 6: Ephemeral map overlays for the 3D table scene.
 *
 * Doctrine authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §16, §19 Slice 6.
 * UX authority: UX_VISION_PHYSICAL_TABLE.md — battlemap / tokens section.
 *
 * Ephemeral overlays are COSMETIC ONLY. They visualize only what the runtime
 * has requested via PENDING_* events. The UI never infers hidden facts (§17).
 *
 * Overlay types:
 *   1. MeasureLine — glowing line from source token to target point/token.
 *      Shown during target selection (pending_target_select event).
 *   2. AoEOverlay — translucent shape (circle/cone/line) on the felt vault.
 *      Shown during AoE confirmation (aoe_preview event from runtime).
 *   3. AreaIndicator — highlighted square or polygon on the map grid.
 *      Shown for AoE squares, zone of control, etc.
 *
 * WS events consumed:
 *   - aoe_preview { shape, origin_x, origin_y, radius, direction_deg? }
 *   - aoe_cleared
 *   - measure_show { from: [x,y], to: [x,y] }
 *   - measure_hide
 *   - area_highlight { squares: [[x,y], ...], color_hint? }
 *   - area_clear
 *
 * No Math.random in procedural content (Gate G — deterministic only).
 */

import * as THREE from 'three';

// ---------------------------------------------------------------------------
// Grid constants (must match entity-renderer.ts)
// ---------------------------------------------------------------------------

const GRID_SCALE = 0.5; // 1 grid square = 0.5 scene units
const MAP_Y = -0.035;   // Just above the felt vault surface (vault top ≈ -0.04)

/** Convert grid coords (int) to scene-space Vector3 (XZ plane, Y = MAP_Y). */
function gridToScene(gx: number, gy: number): THREE.Vector3 {
  // Grid origin is at scene center (0, 0). gy maps to -z (DM side = negative z).
  return new THREE.Vector3(gx * GRID_SCALE, MAP_Y, -gy * GRID_SCALE);
}

// ---------------------------------------------------------------------------
// AoE shape types
// ---------------------------------------------------------------------------

export type AoEShape = 'circle' | 'cone' | 'line' | 'cylinder' | 'sphere';

export interface AoEPreviewData {
  shape:         AoEShape;
  origin_x:      number;
  origin_y:      number;
  radius?:       number;   // for circle/sphere/cylinder — in grid units
  length?:       number;   // for cone/line — in grid units
  angle_deg?:    number;   // for cone — spread angle
  direction_deg?: number;  // for cone/line — direction from origin
  color_hint?:   string;   // 'fire' | 'cold' | 'lightning' | 'acid' | 'force' | default
}

// AoE color palette by damage type
const AOE_COLORS: Record<string, number> = {
  fire:      0xff4400,
  cold:      0x44aaff,
  lightning: 0xffee44,
  acid:      0x44ff44,
  force:     0xaa66ff,
  default:   0xff6622,
};

// ---------------------------------------------------------------------------
// Measure line
// ---------------------------------------------------------------------------

/**
 * Glowing line overlay between two scene-space points.
 * Renders as a thin emissive cylinder lying on the map surface.
 */
export class MeasureLine {
  readonly group: THREE.Group;
  private _lineMesh: THREE.Mesh;
  private _visible = false;

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'measure_line';

    // Build as a thin box (line-like) — no BufferGeometry line needed
    const geo = new THREE.BoxGeometry(1, 0.008, 0.018);
    const mat = new THREE.MeshStandardMaterial({
      color: 0xffd700,
      emissive: new THREE.Color(0xffd700),
      emissiveIntensity: 1.2,
      roughness: 0.4,
      metalness: 0.6,
      transparent: true,
      opacity: 0.85,
    });
    this._lineMesh = new THREE.Mesh(geo, mat);
    this._lineMesh.name = 'measure_line_mesh';
    this.group.add(this._lineMesh);
    this.group.visible = false;
  }

  /**
   * Show a measurement line from grid point (fx, fy) to (tx, ty).
   */
  show(fromX: number, fromY: number, toX: number, toY: number): void {
    const from = gridToScene(fromX, fromY);
    const to   = gridToScene(toX, toY);

    // Center between the two points
    const mid = from.clone().lerp(to, 0.5);
    this._lineMesh.position.copy(mid);
    this._lineMesh.position.y = MAP_Y + 0.004;

    // Length and direction
    const delta = to.clone().sub(from);
    const length = delta.length();
    this._lineMesh.scale.x = length;

    // Rotate to face the direction (XZ plane)
    const angle = Math.atan2(delta.x, delta.z);
    this._lineMesh.rotation.y = angle;

    this.group.visible = true;
    this._visible = true;
  }

  /** Hide the measure line. */
  hide(): void {
    this.group.visible = false;
    this._visible = false;
  }

  get isVisible(): boolean { return this._visible; }
}

// ---------------------------------------------------------------------------
// AoE overlay
// ---------------------------------------------------------------------------

/**
 * Translucent shape overlay on the map vault surface.
 * Circle: flat disc. Cone: flat wedge. Line: long thin box.
 */
export class AoEOverlay {
  readonly group: THREE.Group;
  private _mesh: THREE.Mesh | null = null;
  private _visible = false;

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'aoe_overlay';
    this.group.visible = false;
  }

  /**
   * Show an AoE preview at the given origin with the given shape.
   */
  show(data: AoEPreviewData): void {
    // Remove previous mesh
    if (this._mesh) {
      this.group.remove(this._mesh);
      this._mesh.geometry.dispose();
      (this._mesh.material as THREE.Material).dispose();
      this._mesh = null;
    }

    const colorHex = AOE_COLORS[data.color_hint ?? 'default'] ?? AOE_COLORS.default;
    const origin = gridToScene(data.origin_x, data.origin_y);

    const mat = new THREE.MeshStandardMaterial({
      color: colorHex,
      emissive: new THREE.Color(colorHex),
      emissiveIntensity: 0.55,
      transparent: true,
      opacity: 0.30,
      side: THREE.DoubleSide,
      roughness: 0.9,
      metalness: 0.0,
      depthWrite: false,
    });

    let geo: THREE.BufferGeometry;
    let mesh: THREE.Mesh;
    const dirRad = ((data.direction_deg ?? 0) * Math.PI) / 180;

    if (data.shape === 'circle' || data.shape === 'sphere' || data.shape === 'cylinder') {
      // Flat disc
      const radiusGrid = data.radius ?? 4; // default 4 grid units = 20ft
      const radiusScene = radiusGrid * GRID_SCALE;
      geo = new THREE.CircleGeometry(radiusScene, 32);
      mesh = new THREE.Mesh(geo, mat);
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.set(origin.x, MAP_Y + 0.002, origin.z);

    } else if (data.shape === 'cone') {
      // Wedge — build using CircleGeometry sector trick
      // A cone in 3.5e is typically 60° spread
      const lengthGrid  = data.length ?? 6;
      const angleDeg    = data.angle_deg ?? 60;
      const lengthScene = lengthGrid * GRID_SCALE;
      const halfAngle   = (angleDeg / 2) * (Math.PI / 180);

      // Use CircleGeometry with theta arc to approximate a cone sector
      geo = new THREE.CircleGeometry(lengthScene, 24, -halfAngle, halfAngle * 2);
      mesh = new THREE.Mesh(geo, mat);
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.set(origin.x, MAP_Y + 0.002, origin.z);
      mesh.rotation.z = -dirRad;

    } else {
      // line shape — long thin box
      const lengthGrid  = data.length ?? 12; // 60ft line = 12 squares
      const widthGrid   = 1;                 // 1 square wide
      const lengthScene = lengthGrid * GRID_SCALE;
      const widthScene  = widthGrid  * GRID_SCALE;
      geo = new THREE.PlaneGeometry(lengthScene, widthScene);
      mesh = new THREE.Mesh(geo, mat);
      mesh.rotation.x = -Math.PI / 2;
      // Center the line so origin is at one end
      mesh.position.set(
        origin.x + Math.sin(dirRad) * lengthScene / 2,
        MAP_Y + 0.002,
        origin.z - Math.cos(dirRad) * lengthScene / 2,
      );
      mesh.rotation.z = -dirRad;
    }

    mesh.name = 'aoe_shape';
    this.group.add(mesh);
    this._mesh = mesh;
    this.group.visible = true;
    this._visible = true;
  }

  /** Hide and dispose the AoE overlay. */
  hide(): void {
    if (this._mesh) {
      this.group.remove(this._mesh);
      this._mesh.geometry.dispose();
      (this._mesh.material as THREE.Material).dispose();
      this._mesh = null;
    }
    this.group.visible = false;
    this._visible = false;
  }

  get isVisible(): boolean { return this._visible; }
}

// ---------------------------------------------------------------------------
// Area indicator — highlighted grid squares
// ---------------------------------------------------------------------------

/**
 * Highlights a set of grid squares on the map surface.
 * Used for AoE confirmation (which squares are hit), zone of control, etc.
 */
export class AreaIndicator {
  readonly group: THREE.Group;
  private _meshes: THREE.Mesh[] = [];

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'area_indicator';
    this.group.visible = false;
  }

  /**
   * Highlight a set of grid squares.
   * color_hint: optional hex number for fill color.
   */
  show(squares: Array<[number, number]>, colorHex = 0xff4400): void {
    this.clear();

    const mat = new THREE.MeshStandardMaterial({
      color:            colorHex,
      emissive:         new THREE.Color(colorHex),
      emissiveIntensity: 0.45,
      transparent:      true,
      opacity:          0.22,
      side:             THREE.DoubleSide,
      depthWrite:       false,
      roughness:        0.9,
      metalness:        0.0,
    });

    // Square size slightly smaller than the grid cell so gaps are visible
    const sqSize = GRID_SCALE * 0.88;
    const geo = new THREE.PlaneGeometry(sqSize, sqSize);

    for (const [gx, gy] of squares) {
      const pos = gridToScene(gx, gy);
      const mesh = new THREE.Mesh(geo, mat.clone());
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.set(pos.x, MAP_Y + 0.002, pos.z);
      mesh.name = `area_sq_${gx}_${gy}`;
      this.group.add(mesh);
      this._meshes.push(mesh);
    }

    this.group.visible = true;
  }

  /** Remove all highlighted squares. */
  clear(): void {
    for (const mesh of this._meshes) {
      this.group.remove(mesh);
      mesh.geometry.dispose();
      (mesh.material as THREE.Material).dispose();
    }
    this._meshes = [];
    this.group.visible = false;
  }
}

// ---------------------------------------------------------------------------
// MapOverlayManager — top-level coordinator (use this in main.ts)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// PENDING state registry — WO-UI-MAP-01
// ---------------------------------------------------------------------------

/** Active PENDING kinds that may activate overlays or emit intents. */
export type OverlayPendingKind = 'PENDING_AOE' | 'PENDING_POINT' | 'PENDING_SEARCH';

/**
 * Manages all ephemeral map overlays: measure line, AoE shape, area highlights.
 *
 * PENDING gate (WO-UI-MAP-01): overlays only activate when a matching PENDING
 * kind is active. Activation without PENDING is a no-op (no overlay shown).
 * Call setPending(kind) before routing WS events; call clearPending() on resolve.
 *
 * Usage in main.ts:
 *   const overlayMgr = new MapOverlayManager(scene);
 *   // Set PENDING before enabling overlays:
 *   overlayMgr.setPending('PENDING_AOE');
 *   bridge.on('aoe_preview',   (data) => overlayMgr.showAoE(data));
 *   bridge.on('aoe_cleared',   ()     => overlayMgr.hideAoE());
 *   overlayMgr.setPending('PENDING_POINT');
 *   bridge.on('measure_show',  (data) => overlayMgr.showMeasure(data));
 *   bridge.on('measure_hide',  ()     => overlayMgr.hideMeasure());
 *   overlayMgr.setPending('PENDING_SEARCH');
 *   bridge.on('area_highlight',(data) => overlayMgr.showArea(data));
 *   bridge.on('area_clear',    ()     => overlayMgr.clearArea());
 *   // In render loop: overlayMgr.update(elapsed); (for pulsing)
 */
export class MapOverlayManager {
  private _measure:  MeasureLine;
  private _aoe:      AoEOverlay;
  private _area:     AreaIndicator;
  private _activePending: OverlayPendingKind | null = null;

  constructor(scene: THREE.Scene) {
    this._measure = new MeasureLine();
    this._aoe     = new AoEOverlay();
    this._area    = new AreaIndicator();

    scene.add(this._measure.group);
    scene.add(this._aoe.group);
    scene.add(this._area.group);
  }

  // ── PENDING gate ─────────────────────────────────────────────────────────

  /** Activate a PENDING kind — unlocks matching overlay calls. */
  setPending(kind: OverlayPendingKind): void {
    this._activePending = kind;
  }

  /** Resolve/cancel active PENDING — clears all overlays and re-locks gate. */
  clearPending(): void {
    this._activePending = null;
    // Ephemeral: clear all overlays on PENDING resolve (doctrine §16: TTL-only)
    this._aoe.hide();
    this._measure.hide();
    this._area.clear();
  }

  get activePending(): OverlayPendingKind | null {
    return this._activePending;
  }

  // ── AoE ─────────────────────────────────────────────────────────────────

  /** Show AoE preview — no-op if PENDING_AOE is not active. */
  showAoE(data: AoEPreviewData): void {
    if (this._activePending !== 'PENDING_AOE') return;
    this._aoe.show(data);
  }

  hideAoE(): void {
    this._aoe.hide();
  }

  // ── Measure line ─────────────────────────────────────────────────────────

  /** Show measure line — no-op if PENDING_POINT is not active. */
  showMeasure(fromX: number, fromY: number, toX: number, toY: number): void {
    if (this._activePending !== 'PENDING_POINT') return;
    this._measure.show(fromX, fromY, toX, toY);
  }

  hideMeasure(): void {
    this._measure.hide();
  }

  // ── Area highlight ───────────────────────────────────────────────────────

  /** Show area highlight — no-op if PENDING_SEARCH is not active. */
  showArea(squares: Array<[number, number]>, colorHex?: number): void {
    if (this._activePending !== 'PENDING_SEARCH') return;
    this._area.show(squares, colorHex);
  }

  clearArea(): void {
    this._area.clear();
  }

  /**
   * Per-frame update — gentle pulse on AoE and area emissive intensity.
   * Call with elapsed time (seconds).
   */
  update(elapsed: number): void {
    // Pulse AoE emissive
    if (this._aoe.isVisible && this._aoe.group.children.length > 0) {
      const mesh = this._aoe.group.children[0] as THREE.Mesh;
      if (mesh && mesh.material) {
        const mat = mesh.material as THREE.MeshStandardMaterial;
        mat.emissiveIntensity = 0.45 + Math.sin(elapsed * 2.2) * 0.15;
        mat.opacity           = 0.26 + Math.sin(elapsed * 2.2) * 0.06;
      }
    }

    // Pulse measure line
    if (this._measure.isVisible) {
      const mesh = this._measure.group.children[0] as THREE.Mesh;
      if (mesh && mesh.material) {
        const mat = mesh.material as THREE.MeshStandardMaterial;
        mat.emissiveIntensity = 1.0 + Math.sin(elapsed * 4.0) * 0.3;
      }
    }
  }
}

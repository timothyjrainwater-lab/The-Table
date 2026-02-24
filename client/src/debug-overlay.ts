/**
 * debug-overlay.ts — Scene debug visualization.
 * Only active when URL contains ?debug=1.
 * NEVER import this in production paths — only called from main.ts behind isDebug guard.
 */
import * as THREE from 'three';
import zonesJson from '../../docs/design/LAYOUT_PACK_V1/zones.json';
import type { CameraPostureController } from './camera';

export function isDebugMode(): boolean {
  return new URLSearchParams(window.location.search).get('debug') === '1';
}

export function isZonesMode(): boolean {
  return new URLSearchParams(window.location.search).get('zones') === '1';
}

/**
 * Add AxesHelper to every named mesh in the scene whose name matches
 * the debug prefix list. Size 0.5 = half a scene unit (readable at table scale).
 */
export function addAxesHelpers(scene: THREE.Scene): void {
  const PREFIXES = ['stub_', 'rail_', 'felt_', 'table_', 'player_', 'dice_', 'cup_', 'trash_'];
  scene.traverse((obj) => {
    if (!obj.name) return;
    if (!PREFIXES.some((p) => obj.name.startsWith(p))) return;
    const axes = new THREE.AxesHelper(0.5);
    axes.name = `__debug_axes_${obj.name}`;
    obj.add(axes); // attach to object so axes move with it
  });
}

/**
 * Add a 12×12 unit GridHelper at y=0.01 (just above table surface).
 * 24 divisions = 0.5-unit cells, matching gridToScene() coordinate transform.
 */
export function addGridHelper(scene: THREE.Scene): void {
  const grid = new THREE.GridHelper(12, 24, 0x444444, 0x222222);
  grid.position.set(0, 0.01, 0);
  grid.name = '__debug_grid';
  scene.add(grid);
}

/**
 * Build a DOM overlay listing all named scene objects with positions.
 * Appended to document.body as #debug-hud.
 */
export function addDebugHUD(scene: THREE.Scene): void {
  const hud = document.createElement('div');
  hud.id = 'debug-hud';
  hud.style.cssText = [
    'position:fixed', 'top:8px', 'right:8px',
    'background:rgba(0,0,0,0.75)', 'color:#00ff88',
    'font:11px/1.4 monospace', 'padding:8px 12px',
    'max-height:80vh', 'overflow-y:auto',
    'border:1px solid #00ff88', 'z-index:9999',
    'pointer-events:none',
  ].join(';');

  const lines: string[] = ['=== DEBUG MESH LIST ==='];
  scene.traverse((obj) => {
    if (!obj.name || obj.name.startsWith('__debug')) return;
    const p = obj.position;
    lines.push(`${obj.name.padEnd(28)} (${p.x.toFixed(2)}, ${p.y.toFixed(2)}, ${p.z.toFixed(2)})`);
  });

  hud.textContent = lines.join('\n');
  document.body.appendChild(hud);
}

// ---------------------------------------------------------------------------
// Zones debug overlay — drawn when ?zones=1 in URL
// ---------------------------------------------------------------------------

interface _ZoneEntry {
  name: string;
  centerX: number;
  centerZ: number;
  halfWidth: number;
  halfHeight: number;
  color?: string; // optional — not all zones.json variants include color
}

interface _AnchorEntry {
  x: number;
  y: number;
  z: number;
}

/**
 * Draw zone AABB outlines + anchor spheres from zones.json.
 * Each zone gets a LineSegments box outline at y=0.02 (just above table surface).
 * Each anchor gets a small sphere at its exact world position.
 * Active when ?zones=1 in URL.
 */
export function addZonesOverlay(scene: THREE.Scene): void {
  const data = zonesJson as {
    zones: _ZoneEntry[];
    anchors: Record<string, _AnchorEntry>;
  };

  for (const zone of data.zones) {
    // Parse color string "0xRRGGBB" → number (default white if absent)
    const colorNum = zone.color ? parseInt(zone.color.replace('0x', ''), 16) : 0xffffff;
    const mat = new THREE.LineBasicMaterial({ color: colorNum, linewidth: 1 });

    // Box outline: width=halfWidth*2, height (depth in scene Z)=halfHeight*2, 0.01 tall
    const w = zone.halfWidth * 2;
    const d = zone.halfHeight * 2;
    const boxGeo = new THREE.BoxGeometry(w, 0.01, d);
    const edges = new THREE.EdgesGeometry(boxGeo);
    const outline = new THREE.LineSegments(edges, mat);
    outline.position.set(zone.centerX, 0.02, zone.centerZ);
    outline.name = `__zone_${zone.name}`;
    scene.add(outline);

    // Label: DOM element positioned via zone center (approximate — not projected)
    // We attach a small sphere marker at center for visual reference
    const markerGeo = new THREE.SphereGeometry(0.06, 8, 6);
    const markerMat = new THREE.MeshBasicMaterial({ color: colorNum });
    const marker = new THREE.Mesh(markerGeo, markerMat);
    marker.position.set(zone.centerX, 0.06, zone.centerZ);
    marker.name = `__zone_marker_${zone.name}`;
    scene.add(marker);
  }

  // Anchor spheres — small bright white spheres at each anchor point
  for (const [anchorName, pos] of Object.entries(data.anchors)) {
    const aGeo = new THREE.SphereGeometry(0.04, 8, 6);
    const aMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const aMesh = new THREE.Mesh(aGeo, aMat);
    aMesh.position.set(pos.x, pos.y + 0.04, pos.z);
    aMesh.name = `__anchor_${anchorName}`;
    scene.add(aMesh);
  }
}

/**
 * Mount all debug helpers. Call once after scene is fully constructed.
 */
export function mountDebugOverlay(scene: THREE.Scene): void {
  addGridHelper(scene);
  addAxesHelpers(scene);
  addDebugHUD(scene);
  if (isZonesMode()) {
    addZonesOverlay(scene);
  }
}

// ---------------------------------------------------------------------------
// Camera debug HUD — visible when ?debug=1, positioned top-left
// ---------------------------------------------------------------------------

let _cameraHudEl: HTMLDivElement | null = null;

/**
 * Create the camera debug HUD DOM element.
 * Call once after the camera controller is constructed.
 */
export function mountCameraDebugHUD(): void {
  const el = document.createElement('div');
  el.id = 'camera-debug-hud';
  el.style.cssText = [
    'position:fixed', 'top:8px', 'left:8px',
    'background:rgba(0,0,0,0.78)', 'color:#fff',
    'font:12px/1.6 monospace', 'padding:8px 12px',
    'border:1px solid #555', 'z-index:9999',
    'pointer-events:none', 'white-space:pre',
  ].join(';');
  el.textContent = 'POSTURE: --';
  document.body.appendChild(el);
  _cameraHudEl = el;
}

/**
 * Update the camera debug HUD each frame.
 * Call from the main render loop (after controller.update(dt)) when isDebugMode().
 */
export function updateCameraDebugHUD(
  controller: CameraPostureController,
  camera: THREE.PerspectiveCamera,
): void {
  if (!_cameraHudEl) return;
  const p   = camera.position;
  const pct = Math.round(controller.transitProgress * 100);
  const arrived = pct >= 100;
  _cameraHudEl.textContent = [
    `POSTURE:  ${controller.posture.padEnd(12)}  [SOURCE: camera_poses.json]`,
    `POS:      (${p.x.toFixed(2)}, ${p.y.toFixed(2)}, ${p.z.toFixed(2)})`,
    `FOV:      ${camera.fov.toFixed(1)}°`,
    `NEAR:     ${camera.near.toFixed(2)}`,
    `FAR:      ${camera.far.toFixed(1)}`,
    `TRANSIT:  ${arrived ? '100% (arrived)' : `${pct}%`}`,
  ].join('\n');
}

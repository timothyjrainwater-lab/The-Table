/**
 * dump_scene.mjs — WO-UI-TOOLING-SCENE-DUMP-001
 *
 * Dumps the Three.js scene graph as JSON without a browser.
 *
 * Strategy:
 *   1. Install a minimal DOM mock (canvas, document, window) before any import
 *      that touches the DOM (makeWalnutTexture calls document.createElement).
 *   2. Import Three.js (CJS build) and the scene-builder logic inline (the
 *      TS source is not directly importable from Node, so we duplicate the
 *      geometry/mesh construction here using the same names and positions).
 *   3. Walk the resulting scene graph and emit a JSON structure listing every
 *      named mesh with its world position and geometry type.
 *
 * Run:
 *   node scripts/dump_scene.mjs [--out path/to/output.json]
 *
 * Gate TOOLS-01:
 *   - Output parses as valid JSON
 *   - All named meshes from scene-builder.ts are present
 */

import * as fs from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// 1. Minimal DOM mock — must be set before THREE is imported
// ---------------------------------------------------------------------------

/**
 * Fake HTMLCanvasElement backed by a simple pixel buffer.
 * makeWalnutTexture() and makeCharacterSheetTexture() call:
 *   document.createElement('canvas')
 *   canvas.getContext('2d')
 *   ctx.fillRect / ctx.strokeStyle / etc.
 * We provide no-op implementations so the code runs without crashing.
 */
function makeCanvasMock(width = 300, height = 150) {
  const ctx2d = {
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 1,
    globalAlpha: 1,
    textAlign: 'left',
    font: '',
    fillRect: () => {},
    strokeRect: () => {},
    beginPath: () => {},
    moveTo: () => {},
    lineTo: () => {},
    arc: () => {},
    fill: () => {},
    stroke: () => {},
    fillText: () => {},
  };
  return {
    width,
    height,
    getContext: (type) => {
      if (type === '2d') return ctx2d;
      return null;
    },
    // Three.js CanvasTexture accesses .style on the element
    style: {},
  };
}

global.document = {
  createElement: (tag) => {
    if (tag === 'canvas') return makeCanvasMock();
    return { style: {} };
  },
  body: { appendChild: () => {} },
  getElementById: () => null,
};

global.window = {
  innerWidth: 1280,
  innerHeight: 720,
  devicePixelRatio: 1,
  addEventListener: () => {},
  location: { search: '' },
  performance: { now: () => 0 },
};

global.performance = { now: () => 0 };

// Three.js WebGLRenderer etc. need these stubs
Object.defineProperty(global, 'navigator', {
  value: { userAgent: 'node', platform: 'node' },
  writable: true,
  configurable: true,
});
global.HTMLCanvasElement = function () {};
global.ImageData = function (data, w, h) { this.data = data; this.width = w; this.height = h; };
global.Image = function () {};

// ---------------------------------------------------------------------------
// 2. Import Three.js CJS build
// ---------------------------------------------------------------------------

const threePath = path.join(__dirname, '..', 'client', 'node_modules', 'three', 'build', 'three.cjs');
const { createRequire } = await import('node:module');
const require = createRequire(import.meta.url);
const THREE = require(threePath);

// ---------------------------------------------------------------------------
// 3. Replicate the scene construction from scene-builder.ts + main.ts
//    (positions and names must match exactly)
// ---------------------------------------------------------------------------

const WALNUT_COLOR  = 0x2e1505;
const WALNUT_LIGHT  = 0x3d1f0a;
const FELT_COLOR    = 0x162210;
const FELT_TRAY     = 0x0d1a1a;
const BRASS_COLOR   = 0xb5832a;

function walnutMat(color = WALNUT_COLOR) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.65, metalness: 0.04 });
}
function feltMat(color = FELT_COLOR) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.98, metalness: 0.0 });
}

function buildTableSurface() {
  const group = new THREE.Group();
  group.name = 'table_surface';

  const add = (name, geo, mat, px, py, pz) => {
    const m = new THREE.Mesh(geo, mat);
    m.name = name;
    m.position.set(px, py, pz);
    group.add(m);
    return m;
  };

  add('table_top',          new THREE.BoxGeometry(12, 0.12, 8),   walnutMat(),        0,    -0.06, 0);
  add('felt_vault',         new THREE.BoxGeometry(6.2, 0.08, 4.2), feltMat(),         0,    -0.04, -0.5);
  add('dice_tray_bottom',   new THREE.BoxGeometry(2.4, 0.06, 1.4), walnutMat(),       4.5,   0.03, 3.2);

  // Walls
  [
    ['dice_tray_wall_far',   2.4, 0.12, 0.05, 4.5,  2.53],
    ['dice_tray_wall_near',  2.4, 0.12, 0.05, 4.5,  3.87],
    ['dice_tray_wall_left',  0.05,0.12, 1.3,  3.33, 3.2],
    ['dice_tray_wall_right', 0.05,0.12, 1.3,  5.67, 3.2],
  ].forEach(([n, w, h, d, wx, wz]) => {
    add(n, new THREE.BoxGeometry(w, h, d), walnutMat(WALNUT_LIGHT), wx, 0.12, wz);
  });

  add('dice_tray_felt',  new THREE.BoxGeometry(2.28, 0.01, 1.28), feltMat(FELT_TRAY), 4.5, 0.065, 3.2);
  add('rail_far',        new THREE.BoxGeometry(12.4, 0.18, 0.3),  walnutMat(WALNUT_LIGHT), 0, 0.09, -4.1);
  add('rail_left',       new THREE.BoxGeometry(0.3, 0.18, 9.0),   walnutMat(WALNUT_LIGHT), -6.2, 0.09, 0.7);
  add('rail_right',      new THREE.BoxGeometry(0.3, 0.18, 9.0),   walnutMat(WALNUT_LIGHT),  6.2, 0.09, 0.7);
  add('shelf_edge',      new THREE.BoxGeometry(12.4, 0.06, 0.08), walnutMat(WALNUT_LIGHT), 0, 0.03, 4.1);
  add('player_shelf',    new THREE.BoxGeometry(12, 0.12, 2.5),    walnutMat(),          0, -0.09, 5.35);
  add('cup_holder',      new THREE.CylinderGeometry(0.22, 0.20, 0.28, 16),
    new THREE.MeshStandardMaterial({ color: BRASS_COLOR, roughness: 0.3, metalness: 0.8 }),
    4.8, -0.03, 5.5);
  add('trash_hole',      new THREE.CylinderGeometry(0.22, 0.22, 0.14, 24), feltMat(0x050505), 2.7, 0.005, 3.6);
  add('trash_hole_ring',
    new THREE.TorusGeometry(0.24, 0.04, 8, 24),
    new THREE.MeshStandardMaterial({ color: BRASS_COLOR, roughness: 0.25, metalness: 0.9 }),
    2.7, 0.065, 3.6);

  return group;
}

function buildObjectStubs() {
  const group = new THREE.Group();
  group.name = 'object_stubs';

  const add = (name, geo, mat, px, py, pz) => {
    const m = new THREE.Mesh(geo, mat);
    m.name = name;
    m.position.set(px, py, pz);
    group.add(m);
    return m;
  };

  // Character sheet (PlaneGeometry — no canvas texture needed for dump)
  add('stub_character_sheet', new THREE.PlaneGeometry(1.4, 1.9),
    new THREE.MeshStandardMaterial({ roughness: 0.90, metalness: 0.0 }),
    -2.0, -0.024, 4.8);

  // Notebook
  add('stub_notebook', new THREE.BoxGeometry(1.1, 0.08, 1.5),
    new THREE.MeshStandardMaterial({ color: 0x1c1008, roughness: 0.85, metalness: 0.05 }),
    -0.2, 0.01, 4.8);

  // Tome
  add('stub_tome', new THREE.BoxGeometry(1.2, 0.14, 1.6),
    new THREE.MeshStandardMaterial({ color: 0x4a0f0f, roughness: 0.8, metalness: 0.06 }),
    2.0, 0.04, 4.8);

  // Crystal ball
  const ORB_Z = -3.2, ORB_Y = 0.95;
  add('stub_crystal_ball', new THREE.SphereGeometry(0.70, 32, 20),
    new THREE.MeshStandardMaterial({ color: 0x6070b8, roughness: 0.02, transparent: true, opacity: 0.78 }),
    0, ORB_Y, ORB_Z);

  // Pedestal
  add('pedestal', new THREE.CylinderGeometry(0.18, 0.28, 0.5, 16),
    new THREE.MeshStandardMaterial({ color: WALNUT_COLOR, roughness: 0.7 }),
    0, 0.25, ORB_Z);

  // Dice tower
  add('stub_dice_tower', new THREE.BoxGeometry(0.55, 1.1, 0.55),
    new THREE.MeshStandardMaterial({ color: 0x2a1508, roughness: 0.85 }),
    4.5, 0.62, 3.2);

  // Parchment
  add('stub_parchment', new THREE.BoxGeometry(0.9, 0.01, 1.1),
    new THREE.MeshStandardMaterial({ color: 0xd4c8a4, roughness: 0.95 }),
    -0.8, 0.005, 2.2);

  return group;
}

// ---------------------------------------------------------------------------
// 4. Build scene and walk graph
// ---------------------------------------------------------------------------

const scene = new THREE.Scene();
scene.name = 'scene';

const tableSurface = buildTableSurface();
scene.add(tableSurface);

const objectStubs = buildObjectStubs();
scene.add(objectStubs);

// ---------------------------------------------------------------------------
// 5. Walk and serialize
// ---------------------------------------------------------------------------

function geoType(obj) {
  if (!obj.geometry) return null;
  const ctor = obj.geometry.constructor.name;
  return ctor.replace('BufferGeometry', '') || 'Buffer';
}

function walk(obj, parentName = '') {
  const entries = [];
  const name = obj.name || '(anonymous)';
  const fullName = parentName ? `${parentName}/${name}` : name;

  if (obj.isMesh) {
    const wp = new THREE.Vector3();
    obj.getWorldPosition(wp);
    entries.push({
      name: obj.name,
      path: fullName,
      type: 'Mesh',
      geometry: geoType(obj),
      position: { x: +wp.x.toFixed(4), y: +wp.y.toFixed(4), z: +wp.z.toFixed(4) },
    });
  } else if (obj.isGroup || obj.isScene) {
    // Groups themselves have no mesh — recurse into children
  }

  if (obj.children) {
    for (const child of obj.children) {
      entries.push(...walk(child, obj.isScene ? '' : fullName));
    }
  }

  return entries;
}

const meshEntries = walk(scene);
const namedMeshes = meshEntries.filter(e => e.name && e.name !== '(anonymous)');

const output = {
  _meta: {
    generated: new Date().toISOString(),
    totalMeshes: meshEntries.length,
    namedMeshes: namedMeshes.length,
    tool: 'dump_scene.mjs',
    wo: 'WO-UI-TOOLING-SCENE-DUMP-001',
  },
  meshes: namedMeshes,
  allMeshes: meshEntries,
};

// ---------------------------------------------------------------------------
// 6. Write output
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);
const outIdx = args.indexOf('--out');
const outPath = outIdx >= 0
  ? path.resolve(args[outIdx + 1])
  : path.join(__dirname, '..', 'client', 'tests', 'scene-dump.json');

fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, JSON.stringify(output, null, 2), 'utf8');

console.log(`[dump_scene] Wrote ${outPath}`);
console.log(`[dump_scene] Total meshes: ${meshEntries.length}, named: ${namedMeshes.length}`);
console.log('[dump_scene] Named meshes:');
for (const m of namedMeshes) {
  const p = m.position;
  console.log(`  ${m.name.padEnd(28)} ${m.geometry?.padEnd(20)} pos=(${p.x}, ${p.y}, ${p.z})`);
}

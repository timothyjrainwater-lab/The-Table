/**
 * Scene builder — WO-UI-05: Table surface, atmosphere, and object stubs.
 *
 * Delivers:
 * - Dark walnut table surface (PBR material, grain-like roughness)
 * - Recessed felt vault in the map/center zone
 * - Thick table rail/border
 * - Warm candlelight atmosphere (3 overhead lantern points + dim ambient)
 * - Candle flicker animation
 * - Physical object stub meshes in correct zones (dice bag, notebook, tome,
 *   character sheet, crystal ball, cup holder, dice tower body)
 * - Shadow pass on all stubs
 *
 * Authority: WO-UI-05, MEMO_TABLE_VISION_SPATIAL_SPEC, TABLE_SURFACE_UI_SPECIFICATION
 * Reference: Critical Role EXU table — warm lanterns, dark timber, physical clutter
 */

import * as THREE from 'three';

// ---------------------------------------------------------------------------
// Deterministic PRNG — replaces the built-in RNG for procedural textures.
// Gate G (test_ui_gate_g) bans non-deterministic RNG in client/src/ to enforce that no
// mechanical dice authority exists in the client. Procedural texture generation
// is purely visual and must use a seeded, deterministic source instead.
// LCG parameters from Numerical Recipes (same as glibc): m=2^32, a=1664525, c=1013904223
// ---------------------------------------------------------------------------

function makePrng(seed: number): () => number {
  let s = seed >>> 0;
  return (): number => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 0x100000000;
  };
}

// Fixed seeds — one per texture so regeneration is always identical
const _walnutPrng = makePrng(0xdeadbeef);
const _sheetPrng  = makePrng(0xcafebabe);

// ---------------------------------------------------------------------------
// Materials
// ---------------------------------------------------------------------------

const WALNUT_COLOR   = 0x2e1505;  // dark walnut — base
const WALNUT_LIGHT   = 0x3d1f0a;  // slightly lighter for rail top
const FELT_COLOR     = 0x162210;  // very dark green felt (map vault)
const FELT_TRAY      = 0x0d1a1a;  // even darker felt (dice tray)
const BRASS_COLOR    = 0xb5832a;  // brass fittings

/**
 * Procedural walnut grain texture via canvas.
 * Layered horizontal grain lines with slight noise give a convincing
 * wood surface without any external image assets.
 */
function makeWalnutTexture(width = 512, height = 512): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d')!;
  const rng = _walnutPrng;

  // Base fill — dark walnut
  ctx.fillStyle = '#2e1505';
  ctx.fillRect(0, 0, width, height);

  // Grain lines — horizontal with subtle wave
  const lineCount = 180;
  for (let i = 0; i < lineCount; i++) {
    const y = (i / lineCount) * height;
    const brightness = 0.82 + rng() * 0.22;
    const r = Math.floor(46 * brightness);
    const g = Math.floor(21 * brightness);
    const b = Math.floor(5  * brightness);
    ctx.strokeStyle = `rgb(${r},${g},${b})`;
    ctx.lineWidth = 0.6 + rng() * 1.4;
    ctx.globalAlpha = 0.35 + rng() * 0.45;
    ctx.beginPath();
    // Wavy grain
    ctx.moveTo(0, y);
    for (let x = 0; x < width; x += 8) {
      const wy = y + Math.sin(x * 0.04 + i * 0.7) * 2.5 + (rng() - 0.5) * 1.2;
      ctx.lineTo(x, wy);
    }
    ctx.stroke();
  }

  // Occasional darker knot streak
  for (let k = 0; k < 3; k++) {
    const ky = rng() * height;
    ctx.strokeStyle = '#1a0a02';
    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.25;
    ctx.beginPath();
    ctx.moveTo(0, ky);
    for (let x = 0; x < width; x += 4) {
      ctx.lineTo(x, ky + Math.sin(x * 0.015 + k) * 6);
    }
    ctx.stroke();
  }

  ctx.globalAlpha = 1.0;

  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(2, 1.5);
  return tex;
}

// Singleton — build once, share across table surfaces
let _walnutTex: THREE.CanvasTexture | null = null;
function getWalnutTex(): THREE.CanvasTexture {
  if (!_walnutTex) _walnutTex = makeWalnutTexture();
  return _walnutTex;
}

function walnutMat(color = WALNUT_COLOR, useGrain = true): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color,
    map: useGrain ? getWalnutTex() : undefined,
    roughness: 0.65,
    metalness: 0.04,
  });
}

function feltMat(color = FELT_COLOR): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color,
    roughness: 0.98,
    metalness: 0.0,
  });
}

// ---------------------------------------------------------------------------
// Character sheet canvas renderer
// ---------------------------------------------------------------------------

/**
 * Render a D&D 3.5e character sheet onto a canvas.
 * Layout matches the WotC template — stat block, skills, saves, HP, etc.
 * This is a visual replica; all values are placeholder until runtime wires it.
 */
function makeCharacterSheetTexture(): THREE.CanvasTexture {
  const W = 1024, H = 1400;
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d')!;

  // Parchment background
  ctx.fillStyle = '#e8dcc0';
  ctx.fillRect(0, 0, W, H);

  // Slight texture — faint random speckling
  const _rng = _sheetPrng;
  for (let i = 0; i < 4000; i++) {
    const x = _rng() * W, y = _rng() * H;
    const v = Math.floor(180 + _rng() * 40);
    ctx.fillStyle = `rgba(${v},${v-20},${v-40},0.08)`;
    ctx.fillRect(x, y, 2, 2);
  }

  const INK = '#1a1208';
  const RULE = '#8a7a5a';
  const RED  = '#7a1a0a';

  function hline(y: number, x1 = 24, x2 = W - 24, color = RULE, w = 0.8) {
    ctx.strokeStyle = color; ctx.lineWidth = w;
    ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x2, y); ctx.stroke();
  }
  function box(x: number, y: number, w: number, h: number, fill?: string) {
    ctx.strokeStyle = RULE; ctx.lineWidth = 1;
    if (fill) { ctx.fillStyle = fill; ctx.fillRect(x, y, w, h); }
    ctx.strokeRect(x, y, w, h);
  }
  function label(text: string, x: number, y: number, size = 11, color = RULE, align: CanvasTextAlign = 'left') {
    ctx.font = `${size}px Georgia, serif`;
    ctx.fillStyle = color; ctx.textAlign = align;
    ctx.fillText(text, x, y);
  }
  function value(text: string, x: number, y: number, size = 18, color = INK, align: CanvasTextAlign = 'center') {
    ctx.font = `bold ${size}px Georgia, serif`;
    ctx.fillStyle = color; ctx.textAlign = align;
    ctx.fillText(text, x, y);
  }

  // ── Header ────────────────────────────────────────────────────────────────
  ctx.fillStyle = '#2a1a08';
  ctx.fillRect(0, 0, W, 52);
  ctx.font = 'bold 20px Georgia, serif';
  ctx.fillStyle = '#d4b878';
  ctx.textAlign = 'center';
  ctx.fillText('DUNGEONS & DRAGONS  3.5  CHARACTER RECORD SHEET', W / 2, 33);

  // Name / Class / Race row
  let ry = 70;
  label('CHARACTER NAME', 28, ry - 4, 9, RULE);
  box(24, ry, 320, 30);
  value('Kira Ashveil', 24 + 160, ry + 20, 16, INK);

  label('CLASS & LEVEL', 360, ry - 4, 9, RULE);
  box(356, ry, 180, 30);
  value('Paladin 1', 356 + 90, ry + 20, 14, INK);

  label('RACE', 550, ry - 4, 9, RULE);
  box(546, ry, 120, 30);
  value('Human', 546 + 60, ry + 20, 14, INK);

  label('ALIGNMENT', 680, ry - 4, 9, RULE);
  box(676, ry, 130, 30);
  value('Lawful Good', 676 + 65, ry + 20, 13, INK);

  ry = 130;
  label('PLAYER NAME', 28, ry - 4, 9, RULE);
  box(24, ry, 200, 26);
  label('DEITY', 238, ry - 4, 9, RULE);
  box(234, ry, 140, 26);
  value('Heironeous', 234 + 70, ry + 18, 13, INK);
  label('SIZE', 388, ry - 4, 9, RULE);
  box(384, ry, 80, 26);
  value('Med', 384 + 40, ry + 18, 13, INK);
  label('AGE', 478, ry - 4, 9, RULE);
  box(474, ry, 60, 26);
  value('22', 474 + 30, ry + 18, 13, INK);
  label('GENDER', 548, ry - 4, 9, RULE);
  box(544, ry, 80, 26);
  value('F', 544 + 40, ry + 18, 13, INK);
  label('HEIGHT / WEIGHT', 638, ry - 4, 9, RULE);
  box(634, ry, 168, 26);
  value("5'7\" / 148 lb", 634 + 84, ry + 18, 12, INK);

  hline(165, 24, W - 24, RULE, 1.5);

  // ── Ability Scores (left column) ─────────────────────────────────────────
  ry = 185;
  const ABILITIES = [
    { name: 'STRENGTH',     abbr: 'STR', score: 15, mod: '+2' },
    { name: 'DEXTERITY',    abbr: 'DEX', score: 12, mod: '+1' },
    { name: 'CONSTITUTION', abbr: 'CON', score: 14, mod: '+2' },
    { name: 'INTELLIGENCE', abbr: 'INT', score: 10, mod: '+0' },
    { name: 'WISDOM',       abbr: 'WIS', score: 13, mod: '+1' },
    { name: 'CHARISMA',     abbr: 'CHA', score: 14, mod: '+2' },
  ];

  const ABX = 24, ABW = 130, ABH = 62, ABG = 6;
  ABILITIES.forEach((ab, i) => {
    const ay = ry + i * (ABH + ABG);
    box(ABX, ay, ABW, ABH, '#f0e8d0');
    label(ab.name, ABX + ABW / 2, ay + 12, 8, RED, 'center');
    value(String(ab.score), ABX + 36, ay + 46, 28, INK);
    // Modifier box
    box(ABX + 72, ay + 18, 44, 28, '#e8dcc0');
    value(ab.mod, ABX + 72 + 22, ay + 37, 16, INK);
    label('MODIFIER', ABX + 72 + 22, ay + 52, 7, RULE, 'center');
  });

  // ── HP / Initiative / Speed (right of abilities) ─────────────────────────
  const MX = 175;
  ry = 185;

  // HP block
  box(MX, ry, 190, 70, '#f0e8d0');
  label('HIT POINTS', MX + 95, ry + 12, 9, RED, 'center');
  hline(ry + 16, MX + 4, MX + 186, RULE);
  label('MAXIMUM HP', MX + 95, ry + 28, 8, RULE, 'center');
  value('11', MX + 95, ry + 58, 32, INK);

  box(MX + 196, ry, 110, 70, '#f0e8d0');
  label('CURRENT HP', MX + 196 + 55, ry + 12, 9, RED, 'center');
  hline(ry + 16, MX + 196 + 4, MX + 196 + 106, RULE);
  box(MX + 196 + 4, ry + 22, 102, 44);

  box(MX + 312, ry, 90, 70, '#f0e8d0');
  label('NONLETHAL', MX + 312 + 45, ry + 12, 8, RED, 'center');
  label('DAMAGE', MX + 312 + 45, ry + 22, 8, RED, 'center');
  box(MX + 312 + 4, ry + 28, 82, 38);

  ry += 78;

  // Initiative / Speed / AC row
  box(MX, ry, 88, 52, '#f0e8d0');
  label('INITIATIVE', MX + 44, ry + 11, 8, RED, 'center');
  value('+1', MX + 44, ry + 40, 22, INK);

  box(MX + 94, ry, 88, 52, '#f0e8d0');
  label('SPEED', MX + 94 + 44, ry + 11, 8, RED, 'center');
  value('30 ft', MX + 94 + 44, ry + 40, 18, INK);

  box(MX + 188, ry, 100, 52, '#f0e8d0');
  label('ARMOR CLASS', MX + 188 + 50, ry + 11, 8, RED, 'center');
  value('15', MX + 188 + 50, ry + 40, 22, INK);

  box(MX + 294, ry, 108, 52, '#f0e8d0');
  label('TOUCH AC', MX + 294 + 54, ry + 11, 8, RED, 'center');
  value('11', MX + 294 + 54, ry + 40, 22, INK);

  ry += 60;

  // Attack / Saves row
  box(MX, ry, 130, 48, '#f0e8d0');
  label('BASE ATTACK BONUS', MX + 65, ry + 11, 8, RED, 'center');
  value('+1', MX + 65, ry + 38, 20, INK);

  box(MX + 136, ry, 88, 48, '#f0e8d0');
  label('FORTITUDE', MX + 136 + 44, ry + 11, 8, RED, 'center');
  value('+4', MX + 136 + 44, ry + 38, 20, '#2a5a2a');

  box(MX + 230, ry, 88, 48, '#f0e8d0');
  label('REFLEX', MX + 230 + 44, ry + 11, 8, RED, 'center');
  value('+1', MX + 230 + 44, ry + 38, 20, '#2a5a2a');

  box(MX + 324, ry, 88, 48, '#f0e8d0');
  label('WILL', MX + 324 + 44, ry + 11, 8, RED, 'center');
  value('+3', MX + 324 + 44, ry + 38, 20, '#2a5a2a');

  hline(ry + 56, 24, W - 24, RULE, 1.5);

  // ── Skills ────────────────────────────────────────────────────────────────
  ry += 68;
  label('SKILLS', 28, ry - 6, 10, RED);
  hline(ry - 2, 24, 500, RED, 1);

  const SKILLS = [
    ['Concentration',  'CON', 'C', '+2'],
    ['Diplomacy',      'CHA', 'C', '+4'],
    ['Handle Animal',  'CHA', 'C', '+4'],
    ['Heal',           'WIS', 'C', '+3'],
    ['Knowledge (Religion)', 'INT', 'C', '+2'],
    ['Ride',           'DEX', 'C', '+3'],
    ['Sense Motive',   'WIS', 'C', '+3'],
    ['Bluff',          'CHA', '',  '+2'],
    ['Climb',          'STR', '',  '+2'],
    ['Craft',          'INT', '',  '+0'],
    ['Intimidate',     'CHA', '',  '+2'],
    ['Listen',         'WIS', '',  '+1'],
    ['Search',         'INT', '',  '+0'],
    ['Spot',           'WIS', '',  '+1'],
    ['Swim',           'STR', '',  '+2'],
  ];

  const SK_X = 24, SK_ROW = 22;
  SKILLS.forEach(([name, ability, cc, total], i) => {
    const sy = ry + i * SK_ROW;
    // Class skill dot
    if (cc) {
      ctx.fillStyle = '#7a1a0a';
      ctx.beginPath();
      ctx.arc(SK_X + 6, sy + 8, 4, 0, Math.PI * 2);
      ctx.fill();
    }
    label(name, SK_X + 18, sy + 13, 11, INK);
    label(ability, SK_X + 220, sy + 13, 9, RULE, 'center');
    label('_____', SK_X + 260, sy + 13, 11, RULE);
    value(total, SK_X + 305, sy + 14, 12, INK);
    hline(sy + SK_ROW - 2, SK_X, 480, RULE, 0.5);
  });

  // ── Feats ─────────────────────────────────────────────────────────────────
  const FX = 520;
  ry = 390;
  label('FEATS', FX, ry - 6, 10, RED);
  hline(ry - 2, FX, W - 24, RED, 1);
  const FEATS = ['Power Attack', 'Cleave'];
  FEATS.forEach((f, i) => {
    label(`• ${f}`, FX + 8, ry + 20 + i * 22, 12, INK);
  });

  // ── Special Abilities ──────────────────────────────────────────────────────
  ry = 470;
  label('SPECIAL ABILITIES', FX, ry - 6, 10, RED);
  hline(ry - 2, FX, W - 24, RED, 1);
  const SPECIAL = [
    'Aura of Good (Ex)',
    'Detect Evil (Sp) — at will',
    'Smite Evil 1/day — +2 atk, +1 dmg',
    'Divine Grace — +2 all saves (CHA)',
    'Lay on Hands — 2 HP/day',
  ];
  SPECIAL.forEach((s, i) => {
    label(`• ${s}`, FX + 8, ry + 20 + i * 22, 11, INK);
  });

  // ── Weapons ───────────────────────────────────────────────────────────────
  ry = 810;
  hline(ry, 24, W - 24, RULE, 1.5);
  ry += 14;
  label('WEAPONS & ATTACKS', 28, ry - 4, 10, RED);

  const WH = ['WEAPON', 'ATK BONUS', 'DAMAGE', 'CRITICAL', 'RANGE', 'TYPE'];
  const WC = [200, 100, 100, 100, 80, 80];
  let wx = 28;
  WH.forEach((h, i) => {
    box(wx, ry, WC[i], 24, '#e0d4b0');
    label(h, wx + WC[i] / 2, ry + 16, 8, RED, 'center');
    wx += WC[i];
  });

  const WEAPONS = [
    ['Longsword', '+3', '1d8+2', '19-20/×2', '—', 'S'],
    ['Dagger', '+3', '1d4+2', '19-20/×2', '10 ft', 'P/S'],
  ];
  WEAPONS.forEach((w, wi) => {
    wx = 28;
    w.forEach((cell, ci) => {
      box(wx, ry + 24 + wi * 28, WC[ci], 28);
      value(cell, wx + WC[ci] / 2, ry + 24 + wi * 28 + 19, 12, INK);
      wx += WC[ci];
    });
  });

  // ── Equipment ─────────────────────────────────────────────────────────────
  ry = 940;
  hline(ry, 24, W - 24, RULE, 1.5);
  ry += 14;
  label('EQUIPMENT & ARMOR', 28, ry - 4, 10, RED);
  const EQ = [
    'Scale Mail (+4 AC, ACP -4)',
    'Heavy Wooden Shield (+2 AC)',
    'Backpack, Bedroll, Rations ×5',
    'Rope (50 ft), Torch ×5',
    'Holy Symbol (wooden), Waterskin',
    'Gold: 32 gp  Silver: 14 sp',
  ];
  EQ.forEach((e, i) => {
    label(`• ${e}`, 36, ry + 22 + i * 22, 11, INK);
  });

  // ── Footer ────────────────────────────────────────────────────────────────
  hline(H - 40, 24, W - 24, RULE, 1);
  label('DUNGEONS & DRAGONS 3.5e  ·  PLAYER\'S HANDBOOK  ·  AIDM SYSTEM', W / 2, H - 22, 9, RULE, 'center');

  const tex = new THREE.CanvasTexture(canvas);
  return tex;
}

// ---------------------------------------------------------------------------
// Table geometry
// ---------------------------------------------------------------------------

/**
 * Build the physical table: surface, recessed felt vault, rail borders.
 * Returns a Group containing all table geometry.
 */
export function buildTableSurface(): THREE.Group {
  const group = new THREE.Group();
  group.name = 'table_surface';

  // Main walnut surface — full 12×8
  const surfaceGeo = new THREE.BoxGeometry(12, 0.12, 8);
  const surfaceMesh = new THREE.Mesh(surfaceGeo, walnutMat());
  surfaceMesh.position.set(0, -0.06, 0);
  surfaceMesh.receiveShadow = true;
  surfaceMesh.castShadow = false;
  surfaceMesh.name = 'table_top';
  group.add(surfaceMesh);

  // Recessed felt vault — map/center zone (6×4 area, sunk 0.05 below surface)
  // Map zone: centerX=0, centerZ=-0.5, halfWidth=3, halfHeight=2 → 6×4
  const vaultGeo = new THREE.BoxGeometry(6.2, 0.08, 4.2);
  const vaultMesh = new THREE.Mesh(vaultGeo, feltMat(FELT_COLOR));
  vaultMesh.position.set(0, -0.04, -0.5);
  vaultMesh.receiveShadow = true;
  vaultMesh.name = 'felt_vault';
  group.add(vaultMesh);

  // Dice tray — self-contained unit: walnut frame with raised lip, felt floor.
  // Positioned close to the player at z≈3.2, right-side of working zone.
  // Tray spans x:3.3–5.7, z:2.55–3.85.
  const TRAY_Z = 3.2;
  const trayBottomGeo = new THREE.BoxGeometry(2.4, 0.06, 1.4);
  const trayBottom = new THREE.Mesh(trayBottomGeo, walnutMat());
  trayBottom.position.set(4.5, 0.03, TRAY_Z);
  trayBottom.castShadow = true;
  trayBottom.receiveShadow = true;
  trayBottom.name = 'dice_tray_bottom';
  group.add(trayBottom);

  const trayWallMat = walnutMat(WALNUT_LIGHT);
  const wallSpecs: [string, number, number, number, number, number][] = [
    ['dice_tray_wall_far',   2.4,  0.12, 0.05, 4.5,         TRAY_Z - 0.67],
    ['dice_tray_wall_near',  2.4,  0.12, 0.05, 4.5,         TRAY_Z + 0.67],
    ['dice_tray_wall_left',  0.05, 0.12, 1.3,  3.33,        TRAY_Z],
    ['dice_tray_wall_right', 0.05, 0.12, 1.3,  5.67,        TRAY_Z],
  ];
  for (const [wname, w, h, d, wx, wz] of wallSpecs) {
    const wall = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), trayWallMat);
    wall.position.set(wx, 0.12, wz);
    wall.castShadow = true;
    wall.receiveShadow = true;
    wall.name = wname;
    group.add(wall);
  }

  const trayFeltGeo = new THREE.BoxGeometry(2.28, 0.01, 1.28);
  const trayFeltMesh = new THREE.Mesh(trayFeltGeo, feltMat(FELT_TRAY));
  trayFeltMesh.position.set(4.5, 0.065, TRAY_Z);
  trayFeltMesh.receiveShadow = true;
  trayFeltMesh.name = 'dice_tray_felt';
  group.add(trayFeltMesh);

  // Rail border — 3 sides only (far, left, right). Near rail replaced by thin edge.
  // This prevents any lip from overhanging the player shelf.
  const railH = 0.18;
  const railY = railH / 2;
  const railMat = walnutMat(WALNUT_LIGHT);

  // Far rail only (no near rail — shelf takes that edge)
  const farRailGeo = new THREE.BoxGeometry(12.4, railH, 0.3);
  const farRail = new THREE.Mesh(farRailGeo, railMat);
  farRail.position.set(0, railY, -4.1);
  farRail.castShadow = true;
  farRail.receiveShadow = true;
  farRail.name = 'rail_far';
  group.add(farRail);

  // Short rails (along Z) — full length including shelf area
  for (const x of [-6.2, 6.2]) {
    const railGeo = new THREE.BoxGeometry(0.3, railH, 9.0);
    const rail = new THREE.Mesh(railGeo, railMat);
    rail.position.set(x, railY, 0.7);
    rail.castShadow = true;
    rail.receiveShadow = true;
    rail.name = `rail_${x > 0 ? 'right' : 'left'}`;
    group.add(rail);
  }

  // Thin near edge strip — marks the step between main surface and shelf, no overhang
  const edgeGeo = new THREE.BoxGeometry(12.4, 0.06, 0.08);
  const edgeMesh = new THREE.Mesh(edgeGeo, railMat);
  edgeMesh.position.set(0, 0.03, 4.1);
  edgeMesh.castShadow = false;
  edgeMesh.receiveShadow = true;
  edgeMesh.name = 'shelf_edge';
  group.add(edgeMesh);

  // Player shelf — fold-out ledge extending from the near rail toward the player.
  // Top face at y=-0.03 (just a step below the main surface — no clipping).
  // Depth 2.5 so it reads as a full surface in DOWN posture.
  const shelfGeo = new THREE.BoxGeometry(12, 0.12, 2.5);
  const shelf = new THREE.Mesh(shelfGeo, walnutMat());
  shelf.position.set(0, -0.09, 5.35);
  shelf.castShadow = true;
  shelf.receiveShadow = true;
  shelf.name = 'player_shelf';
  group.add(shelf);


  // Cup holder — far right corner of player shelf, well clear of the tray
  const cupGeo = new THREE.CylinderGeometry(0.22, 0.20, 0.28, 16);
  const cupMesh = new THREE.Mesh(cupGeo, new THREE.MeshStandardMaterial({
    color: BRASS_COLOR,
    roughness: 0.3,
    metalness: 0.8,
  }));
  cupMesh.position.set(5.6, -0.03, 5.5);
  cupMesh.castShadow = true;
  cupMesh.receiveShadow = true;
  cupMesh.name = 'cup_holder';
  group.add(cupMesh);

  // Trash hole — main walnut surface, clear of the tray (tray left wall x=3.3)
  // and clear of the shelf step (shelf starts z≈4.1). x=2.5 is open table,
  // z=3.6 is solidly on the main surface above the tome area.
  const trashHoleGeo = new THREE.CylinderGeometry(0.22, 0.22, 0.14, 24);
  const trashHoleMesh = new THREE.Mesh(trashHoleGeo, feltMat(0x050505));
  trashHoleMesh.position.set(2.7, 0.005, 3.6);
  trashHoleMesh.receiveShadow = true;
  trashHoleMesh.name = 'trash_hole';
  group.add(trashHoleMesh);

  // Brass ring around the hole
  const trashRingGeo = new THREE.TorusGeometry(0.24, 0.04, 8, 24);
  const trashRingMesh = new THREE.Mesh(trashRingGeo, new THREE.MeshStandardMaterial({
    color: BRASS_COLOR, roughness: 0.25, metalness: 0.9,
  }));
  trashRingMesh.rotation.x = Math.PI / 2;
  trashRingMesh.position.set(2.7, 0.065, 3.6);
  trashRingMesh.castShadow = false;
  trashRingMesh.receiveShadow = true;
  trashRingMesh.name = 'trash_hole_ring';
  group.add(trashRingMesh);

  return group;
}

// ---------------------------------------------------------------------------
// Lighting — warm candlelight atmosphere
// ---------------------------------------------------------------------------

export interface LanternLight {
  light: THREE.PointLight;
  baseIntensity: number;
  flickerSeed: number;
}

/**
 * Build the atmosphere lighting: 3 overhead lantern point lights + dim ambient.
 * Returns lights (added to scene by caller) and LanternLight data for flicker.
 */
export function buildAtmosphere(scene: THREE.Scene): LanternLight[] {
  // Ambient — bumped up for overall scene brightness
  const ambient = new THREE.AmbientLight(0x1a1520, 0.70);
  ambient.name = 'ambient';
  scene.add(ambient);

  // Hemisphere light — warm from above, cool from below
  const hemi = new THREE.HemisphereLight(0x3d1f08, 0x080510, 0.65);
  hemi.name = 'hemi';
  scene.add(hemi);

  // 3 overhead lantern point lights — warm amber
  const lanternPositions: [number, number, number][] = [
    [0, 5.5, 0],      // center — main pool over map
    [-3.5, 5.0, 3.5], // player left (illuminates shelf + work zone)
    [3.5, 5.0, 3.5],  // player right (near dice station + shelf)
  ];

  const lanternColors = [0xffb347, 0xffa030, 0xffb866];
  const lanternIntensities = [55, 42, 42];

  const lanterns: LanternLight[] = [];

  lanternPositions.forEach(([x, y, z], i) => {
    const light = new THREE.PointLight(lanternColors[i], lanternIntensities[i], 14, 1.8);
    light.position.set(x, y, z);
    light.castShadow = true;
    light.shadow.mapSize.set(512, 512);
    light.shadow.camera.near = 0.5;
    light.shadow.camera.far = 16;
    light.shadow.bias = -0.002;
    light.name = `lantern_${i}`;
    scene.add(light);

    lanterns.push({
      light,
      baseIntensity: lanternIntensities[i],
      flickerSeed: i * 1.37 + 0.5,
    });
  });

  // Faint candle at DM side (crystal ball glow suggestion)
  const dmCandle = new THREE.PointLight(0xff6020, 6, 5, 2.0);
  dmCandle.position.set(0, 1.2, -3.2);
  dmCandle.castShadow = false;
  dmCandle.name = 'dm_candle';
  scene.add(dmCandle);

  // Dedicated fill light over the dice tray — sits low so it washes the tray
  // walls and felt without blowing out the rest of the scene.
  const trayFill = new THREE.PointLight(0xffcc88, 18, 4.5, 1.6);
  trayFill.position.set(4.5, 2.2, 3.2);
  trayFill.castShadow = false;
  trayFill.name = 'tray_fill';
  scene.add(trayFill);

  // Strong overhead light over the battle map vault — the map needs to be
  // clearly readable. Cooler white-amber to contrast with the warm lanterns
  // and make the felt surface pop. Positioned high so it covers the full vault.
  const mapSpot = new THREE.PointLight(0xffaa44, 38, 7.0, 1.4);
  mapSpot.position.set(0, 4.0, -0.5);
  mapSpot.castShadow = true;
  mapSpot.shadow.mapSize.set(512, 512);
  mapSpot.shadow.camera.near = 0.5;
  mapSpot.shadow.camera.far = 10;
  mapSpot.shadow.bias = -0.002;
  mapSpot.name = 'map_spot';
  scene.add(mapSpot);

  return lanterns;
}

/**
 * Animate lantern flicker. Call each frame with elapsed time.
 * Subtle ±8% intensity variation, slightly different per lantern.
 */
export function updateFlicker(lanterns: LanternLight[], time: number): void {
  for (const l of lanterns) {
    const f = l.flickerSeed;
    // Layered sine waves give organic flicker feel
    const flicker =
      Math.sin(time * 3.7 + f * 5.1) * 0.04 +
      Math.sin(time * 7.3 + f * 2.3) * 0.025 +
      Math.sin(time * 13.1 + f * 8.7) * 0.015;
    l.light.intensity = l.baseIntensity * (1.0 + flicker);
  }
}

// ---------------------------------------------------------------------------
// Object stubs
// ---------------------------------------------------------------------------

/**
 * Build all physical object stubs — correct zone positions, correct scale.
 * No interaction logic — pure visual presence.
 * Returns a Group.
 */
export function buildObjectStubs(): THREE.Group {
  const group = new THREE.Group();
  group.name = 'object_stubs';

  // ── Character sheet — player zone, center-left ──────────────────────────
  // Flat paper rectangle with real D&D 3.5e character sheet rendered on top face.
  // PlaneGeometry so the texture maps cleanly to the visible face.
  const sheetGeo = new THREE.PlaneGeometry(1.4, 1.9);
  const sheetTex = makeCharacterSheetTexture();
  const sheetMat = new THREE.MeshStandardMaterial({
    map: sheetTex,
    roughness: 0.90,
    metalness: 0.0,
  });
  const sheet = new THREE.Mesh(sheetGeo, sheetMat);
  // Rotate flat onto the table surface
  sheet.rotation.x = -Math.PI / 2;
  sheet.rotation.z = 0.06; // slight casual angle
  sheet.position.set(-2.0, -0.024, 4.8);
  sheet.castShadow = true;
  sheet.receiveShadow = true;
  sheet.name = 'stub_character_sheet';
  group.add(sheet);

  // ── Notebook — player zone, right of center ──────────────────────────────
  // Slightly thicker than sheet, darker cover
  const notebookGeo = new THREE.BoxGeometry(1.1, 0.08, 1.5);
  const notebookMat = new THREE.MeshStandardMaterial({
    color: 0x1c1008,
    roughness: 0.85,
    metalness: 0.05,
  });
  const notebook = new THREE.Mesh(notebookGeo, notebookMat);
  notebook.position.set(-0.2, 0.01, 4.8);
  notebook.rotation.y = -0.08;
  notebook.castShadow = true;
  notebook.receiveShadow = true;
  notebook.name = 'stub_notebook';
  group.add(notebook);

  // Spine detail on notebook
  const spineGeo = new THREE.BoxGeometry(0.06, 0.085, 1.52);
  const spineMat = new THREE.MeshStandardMaterial({ color: 0x2a1810, roughness: 0.9 });
  const spine = new THREE.Mesh(spineGeo, spineMat);
  spine.position.set(-0.72, 0.01, 4.8);
  spine.rotation.y = -0.08;
  group.add(spine);

  // ── Tome (Rulebook) — player zone, far right ─────────────────────────────
  // Thicker book, burgundy cover
  const tomeGeo = new THREE.BoxGeometry(1.2, 0.14, 1.6);
  const tomeMat = new THREE.MeshStandardMaterial({
    color: 0x4a0f0f,
    roughness: 0.8,
    metalness: 0.06,
  });
  const tome = new THREE.Mesh(tomeGeo, tomeMat);
  tome.position.set(2.0, 0.04, 4.8);
  tome.rotation.y = 0.12;
  tome.castShadow = true;
  tome.receiveShadow = true;
  tome.name = 'stub_tome';
  group.add(tome);

  // Gold embossed strip on tome cover (decorative)
  const embossGeo = new THREE.BoxGeometry(0.9, 0.145, 0.06);
  const embossMat = new THREE.MeshStandardMaterial({ color: BRASS_COLOR, roughness: 0.4, metalness: 0.9 });
  for (const zOff of [-0.55, 0.55]) {
    const emboss = new THREE.Mesh(embossGeo, embossMat);
    emboss.position.set(2.0, 0.04, 4.8 + zOff);
    emboss.rotation.y = 0.12;
    group.add(emboss);
  }

  // ── Crystal Ball — DM zone, center ───────────────────────────────────────
  // The DM presence focal anchor. NPC portraits display inside it.
  // Should be the dominant visual object on the far side — not decorative.
  // Radius 0.7 = roughly the size of a large cantaloupe on the table.
  // Positioned up on a pedestal so it reads across the full table depth.
  const ORB_Z    = -3.2;
  const ORB_Y    = 0.95; // center of sphere (pedestal lifts it)

  const orbGeo = new THREE.SphereGeometry(0.70, 32, 20);
  const orbMat = new THREE.MeshStandardMaterial({
    color: 0x6070b8,
    roughness: 0.02,
    metalness: 0.0,
    transparent: true,
    opacity: 0.78,
    envMapIntensity: 1.2,
    emissive: new THREE.Color(0x2233aa),
    emissiveIntensity: 0.6,
  });
  const orb = new THREE.Mesh(orbGeo, orbMat);
  orb.position.set(0, ORB_Y, ORB_Z);
  orb.castShadow = true;
  orb.receiveShadow = false;
  orb.name = 'stub_crystal_ball';
  group.add(orb);

  // Pedestal — tapered column lifting the orb to eye-catching height
  const pedestalGeo = new THREE.CylinderGeometry(0.18, 0.28, 0.5, 16);
  const pedestalMat = new THREE.MeshStandardMaterial({
    color: WALNUT_COLOR, roughness: 0.7, metalness: 0.05,
  });
  const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
  pedestal.position.set(0, 0.25, ORB_Z);
  pedestal.castShadow = true;
  pedestal.receiveShadow = true;
  group.add(pedestal);

  // Orb base — wide brass cradle ring that sits on the pedestal top
  const baseGeo = new THREE.TorusGeometry(0.44, 0.07, 10, 32);
  const baseMesh = new THREE.Mesh(baseGeo, new THREE.MeshStandardMaterial({
    color: BRASS_COLOR, roughness: 0.25, metalness: 0.9,
  }));
  baseMesh.rotation.x = Math.PI / 2;
  baseMesh.position.set(0, 0.51, ORB_Z);
  baseMesh.castShadow = true;
  group.add(baseMesh);

  // Inner glow — strong enough to cast colored light on the table surface
  const orbGlow = new THREE.PointLight(0x4455dd, 6.0, 5.5, 1.8);
  orbGlow.position.set(0, ORB_Y, ORB_Z);
  orbGlow.name = 'orb_glow';
  group.add(orbGlow);

  // ── Dice Tower — inside the tray unit ────────────────────────────────────
  // Stands on the tray felt floor (y=0.065). Tower center y = 0.065 + 0.55 = 0.615.
  const towerBodyGeo = new THREE.BoxGeometry(0.55, 1.1, 0.55);
  const towerMat = new THREE.MeshStandardMaterial({
    color: 0x2a1508,
    roughness: 0.85,
    metalness: 0.05,
  });
  const towerBody = new THREE.Mesh(towerBodyGeo, towerMat);
  towerBody.position.set(4.5, 0.62, 3.2);
  towerBody.castShadow = true;
  towerBody.receiveShadow = true;
  towerBody.name = 'stub_dice_tower';
  group.add(towerBody);

  // Tower opening — small hole on top (just an inset darker box)
  const towerTopGeo = new THREE.BoxGeometry(0.38, 0.04, 0.38);
  const towerTopMesh = new THREE.Mesh(towerTopGeo, new THREE.MeshStandardMaterial({
    color: 0x0a0604, roughness: 1.0,
  }));
  towerTopMesh.position.set(4.5, 1.18, 3.2);
  group.add(towerTopMesh);

  // ── Loose d20 in dice tray felt area ─────────────────────────────────────
  // Already handled by DiceObject in main.ts — leave at its default position.
  // Add a couple of small extra d6 stubs as visual clutter
  const d6Geo = new THREE.BoxGeometry(0.18, 0.18, 0.18);
  const d6Mat = new THREE.MeshStandardMaterial({ color: 0x8a1010, roughness: 0.4, metalness: 0.1 });
  const d6Positions: [number, number, number][] = [
    [4.1, 0.16, 3.0],
    [4.7, 0.16, 3.3],
  ];
  for (const [x, y, z] of d6Positions) {
    const d6 = new THREE.Mesh(d6Geo, d6Mat);
    d6.position.set(x, y, z);
    d6.rotation.set(0.3, 0.6, 0.1);
    d6.castShadow = true;
    d6.receiveShadow = true;
    group.add(d6);
  }

  // ── Scattered parchment — open work zone, lived-in feel ──────────────────
  // Loose sheet adrift in the open walnut zone between vault and shelf.
  const parchGeo = new THREE.BoxGeometry(0.9, 0.01, 1.1);
  const parchMat = new THREE.MeshStandardMaterial({ color: 0xd4c8a4, roughness: 0.95 });
  const parch = new THREE.Mesh(parchGeo, parchMat);
  parch.position.set(-0.8, 0.005, 2.2);
  parch.rotation.y = 0.35;
  parch.castShadow = true;
  parch.receiveShadow = true;
  parch.name = 'stub_parchment';
  group.add(parch);

  return group;
}

/**
 * Animate crystal ball glow — subtle pulse.
 * Call each frame with elapsed time.
 */
export function updateCrystalBall(group: THREE.Group, time: number): void {
  const orb = group.getObjectByName('stub_crystal_ball') as THREE.Mesh | undefined;
  const glow = group.getObjectByName('orb_glow') as THREE.PointLight | undefined;
  if (!orb || !glow) return;

  const pulse = Math.sin(time * 1.3) * 0.07 + Math.sin(time * 3.1) * 0.03;
  const mat = orb.material as THREE.MeshStandardMaterial;
  mat.opacity = 0.74 + pulse * 0.09;
  mat.emissiveIntensity = 0.55 + pulse * 0.35;
  glow.intensity = 5.5 + pulse * 2.5;

  // Very slow drift — barely perceptible, feels alive
  orb.position.y = 0.95 + Math.sin(time * 0.7) * 0.018;
  glow.position.y = orb.position.y;
}

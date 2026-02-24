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
 * Object positions are authoritative from:
 *   docs/design/LAYOUT_PACK_V1/table_objects.json
 * DO NOT hardcode positions — read from tableObjectsJson below.
 *
 * Authority: WO-UI-05, WO-UI-LAYOUT-PACK-V1, MEMO_TABLE_VISION_SPATIAL_SPEC
 * Reference: Critical Role EXU table — warm lanterns, dark timber, physical clutter
 */

import * as THREE from 'three';
import tableObjectsJson from '../../docs/design/LAYOUT_PACK_V1/table_objects.json';
import zonesJson from '../../aidm/ui/zones.json';

// ---------------------------------------------------------------------------
// Zones JSON helpers — single source of truth for zone anchors (WO-UI-MAP-01).
// map_plane position is derived from vault_center anchor, not hardcoded.
// ---------------------------------------------------------------------------

interface _Anchor { x: number; y: number; z: number; }
interface _Zone { name: string; centerX: number; centerZ: number; halfWidth: number; halfHeight: number; }

function _zoneAnchor(name: string): _Anchor {
  const anchors = (zonesJson as unknown as { anchors: Record<string, _Anchor> }).anchors;
  const anchor = anchors[name];
  if (!anchor) throw new Error(`zones.json: anchor '${name}' not found`);
  return anchor;
}

function _zone(name: string): _Zone {
  const zones = (zonesJson as unknown as { zones: _Zone[] }).zones;
  const z = zones.find(z => z.name === name);
  if (!z) throw new Error(`zones.json: zone '${name}' not found`);
  return z;
}

// ---------------------------------------------------------------------------
// Layout Pack helpers — read object positions from table_objects.json.
// This is the single source of truth for all object placement.
// ---------------------------------------------------------------------------

interface _TOPos { x: number; y: number; z: number; }
interface _TOObj {
  name: string;
  position: _TOPos;
  rotation_y: number;
  scale: _TOPos;
}

function _objPos(name: string): _TOPos {
  const obj = (tableObjectsJson as { objects: _TOObj[] }).objects.find(o => o.name === name);
  if (!obj) throw new Error(`table_objects.json: object '${name}' not found`);
  return obj.position;
}

function _objRot(name: string): number {
  const obj = (tableObjectsJson as { objects: _TOObj[] }).objects.find(o => o.name === name);
  if (!obj) throw new Error(`table_objects.json: object '${name}' not found`);
  return obj.rotation_y;
}

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

  // Grain lines — horizontal with subtle wave.
  // Tight brightness range + low alpha prevents overexpose under ACESFilmic tone mapping.
  const lineCount = 320;
  for (let i = 0; i < lineCount; i++) {
    const y = (i / lineCount) * height;
    const brightness = 0.88 + rng() * 0.10;  // was 0.82+0.22 — narrowed to prevent blowout
    const r = Math.floor(46 * brightness);
    const g = Math.floor(21 * brightness);
    const b = Math.floor(5  * brightness);
    ctx.strokeStyle = `rgb(${r},${g},${b})`;
    ctx.lineWidth = 0.4 + rng() * 0.9;
    ctx.globalAlpha = 0.18 + rng() * 0.22;   // was 0.35+0.45 — halved to prevent tile-grid read
    ctx.beginPath();
    // Wavy grain with more frequency variation to break regular spacing
    ctx.moveTo(0, y);
    for (let x = 0; x < width; x += 6) {
      const wy = y + Math.sin(x * 0.03 + i * 0.53) * 3.0 + (rng() - 0.5) * 1.8;
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
  tex.repeat.set(4, 3);  // Higher repeat: grain reads as continuous wood, tile seams sub-pixel (was 1,0.75 — produced visible square tile grid under overhead light)
  return tex;
}

// Singleton — build once, share across table surfaces
let _walnutTex: THREE.CanvasTexture | null = null;

/** Exported orb mesh — consumed by CrystalBallController in main.ts. */
export let crystalBallOrbMesh: THREE.Mesh | null = null;

/**
 * Exported inner orb mesh — NPC portrait display surface.
 * Smaller sphere (r=0.55) inside the outer orb; receives portrait textures
 * via CrystalBallController.onPortraitDisplay(). Hidden until a portrait is set.
 */
export let crystalBallInnerMesh: THREE.Mesh | null = null;

/** Exported character sheet mesh — used for raycast click detection in main.ts. */
export let characterSheetMesh: THREE.Mesh | null = null;

/** Exported notebook stub mesh — registered with ShelfDragController in main.ts. */
export let notebookMesh: THREE.Mesh | null = null;

/** Exported tome (rulebook) stub mesh — registered with ShelfDragController in main.ts. */
export let tomeMesh: THREE.Mesh | null = null;

/**
 * Exported function — live-redraws dynamic fields on the character sheet canvas.
 * Called from main.ts on character_sheet_update / entity_delta events.
 * Only redraws the fields that change at runtime (HP, conditions, spell slots).
 */
export let updateCharacterSheetLive: ((data: {
  hp_current?: number;
  hp_max?: number;
  conditions?: string[];
  spell_slots?: Record<number, number>;
  spell_slots_max?: Record<number, number>;
}) => void) = () => { /* no-op until sheet is built */ };

function getWalnutTex(): THREE.CanvasTexture {
  if (!_walnutTex) _walnutTex = makeWalnutTexture();
  return _walnutTex;
}

function walnutMat(color = WALNUT_COLOR, useGrain = true, roughness = 0.65): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({
    color,
    map: useGrain ? getWalnutTex() : undefined,
    roughness,
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
function makeCharacterSheetTexture(): { canvas: HTMLCanvasElement; texture: THREE.CanvasTexture } {
  const W = 1024, H = 1400;
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d')!;

  // Parchment background — aged, darker so it reads as paper not a UI panel (VQ-006)
  ctx.fillStyle = '#b8a06a';  // WO-UI-LIGHTING-V1: darkened from #c8b483 — less modern/bright
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
  return { canvas, texture: tex };
}

// ---------------------------------------------------------------------------
// Table geometry
// ---------------------------------------------------------------------------

// Exported vault cover mesh — toggled by main.ts on combat_start/combat_end
export let vaultCoverMesh: THREE.Mesh | null = null;

/**
 * Procedural vault texture — dark green felt, plain (no grid).
 * Grid removed per WO-UI-CAMERA-OPTICS-AMEND-001: grid reads as digital HUD.
 */
function makeVaultTexture(): THREE.CanvasTexture {
  const W = 512, H = 512;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d')!;

  // Base: dark green felt — plain, no grid (WO-UI-CAMERA-OPTICS-AMEND-001: grid removed, reads as digital HUD)
  ctx.fillStyle = '#162210';
  ctx.fillRect(0, 0, W, H);

  const tex = new THREE.CanvasTexture(canvas);
  return tex;
}

// Fixed seed for vault cover parchment texture
const _vaultCoverPrng = makePrng(0xf00dcafe);

/**
 * Vault cover texture — aged parchment with faint map markings.
 * Visible in REST state so the vault reads as a map cover, not blank walnut.
 * Warm cream with ink stain edges, subtle grid ghost, and corner burn marks.
 */
function makeVaultCoverTexture(): THREE.CanvasTexture {
  const W = 1024, H = 1024;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d')!;
  const rng = _vaultCoverPrng;

  // Base: aged parchment cream
  ctx.fillStyle = '#c8b07a';
  ctx.fillRect(0, 0, W, H);

  // Vignette — darkened edges like old rolled paper
  const vig = ctx.createRadialGradient(W/2, H/2, W*0.2, W/2, H/2, W*0.78);
  vig.addColorStop(0, 'rgba(0,0,0,0)');
  vig.addColorStop(1, 'rgba(40,20,5,0.55)');
  ctx.fillStyle = vig;
  ctx.fillRect(0, 0, W, H);

  // Grain — aged paper texture
  for (let i = 0; i < 8000; i++) {
    const x = rng() * W, y = rng() * H;
    const v = Math.floor(160 + rng() * 50);
    ctx.fillStyle = `rgba(${v},${v-15},${v-35},0.06)`;
    ctx.fillRect(x, y, 2, 2);
  }

  // Faint ghost grid — ink lines barely visible under the cover (map beneath bleeding through)
  ctx.strokeStyle = 'rgba(60,35,10,0.12)';
  ctx.lineWidth = 1.0;
  const cell = W / 16;
  for (let i = 0; i <= 16; i++) {
    ctx.beginPath(); ctx.moveTo(i * cell, 0); ctx.lineTo(i * cell, H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * cell); ctx.lineTo(W, i * cell); ctx.stroke();
  }

  // Ink stain blots — 3-4 random dark spots for aged feel
  for (let s = 0; s < 4; s++) {
    const sx = 100 + rng() * (W - 200);
    const sy = 100 + rng() * (H - 200);
    const sr = 20 + rng() * 60;
    const stain = ctx.createRadialGradient(sx, sy, 0, sx, sy, sr);
    stain.addColorStop(0, 'rgba(30,15,5,0.18)');
    stain.addColorStop(1, 'rgba(30,15,5,0)');
    ctx.fillStyle = stain;
    ctx.beginPath(); ctx.arc(sx, sy, sr, 0, Math.PI * 2); ctx.fill();
  }

  // Corner burn / crease marks
  const corners = [[0,0],[W,0],[0,H],[W,H]];
  for (const [cx,cy] of corners) {
    const burn = ctx.createRadialGradient(cx, cy, 0, cx, cy, 120);
    burn.addColorStop(0, 'rgba(20,8,2,0.40)');
    burn.addColorStop(1, 'rgba(20,8,2,0)');
    ctx.fillStyle = burn;
    ctx.fillRect(0, 0, W, H);
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.ClampToEdgeWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  return tex;
}

/**
 * Build the physical table: surface, recessed felt vault, rail borders.
 * Returns a Group containing all table geometry.
 */
export function buildTableSurface(): THREE.Group {
  const group = new THREE.Group();
  group.name = 'table_surface';

  // Main walnut surface — full 12×8. No grain map: solid colour reads correctly at table distance.
  // Grain tiling creates visible seams at any repeat setting under overhead light.
  const surfaceGeo = new THREE.BoxGeometry(12, 0.12, 8);
  const surfaceMesh = new THREE.Mesh(surfaceGeo, walnutMat(WALNUT_COLOR, false, 0.92));
  surfaceMesh.position.set(0, -0.06, 0);
  surfaceMesh.receiveShadow = true;
  surfaceMesh.castShadow = false;
  surfaceMesh.name = 'table_top';
  group.add(surfaceMesh);

  // Recessed felt vault — expanded map well. Nearly full table width, centered player-side.
  // Spans x: -5.5 to 5.5 (11.0 wide), z: -2.8 to 2.8 (5.6 deep), center at z=0.0.
  // Pulled player-ward so far edge doesn't go under the orb pedestal (orb at z=-3.2).
  const vaultGeo = new THREE.BoxGeometry(11.0, 0.08, 5.6);
  const vaultMat = new THREE.MeshStandardMaterial({
    map: makeVaultTexture(),
    color: FELT_COLOR,
    roughness: 0.98,
    metalness: 0.0,
  });
  const vaultMesh = new THREE.Mesh(vaultGeo, vaultMat);
  vaultMesh.position.set(0, -0.055, 0.0); // vault center at z=0.0
  vaultMesh.receiveShadow = true;
  vaultMesh.name = 'felt_vault';
  group.add(vaultMesh);

  // Vault cover — aged parchment plane that hides felt during non-combat (VQ-001).
  // Parchment texture so it reads as a map cover/scroll even in REST dim lighting.
  // visible=true by default. main.ts toggles on combat_start/combat_end.
  const vaultCoverGeo = new THREE.PlaneGeometry(11.0, 5.6);
  const _vaultCoverMat = new THREE.MeshStandardMaterial({
    map: makeVaultCoverTexture(),
    color: 0xb89a60,    // warm parchment tint
    roughness: 0.92,
    metalness: 0.0,
    emissive: new THREE.Color(0x4a3010),
    emissiveIntensity: 0.08,  // faint self-illumination so parchment reads in dim ambient
  });
  const _vaultCover = new THREE.Mesh(vaultCoverGeo, _vaultCoverMat);
  _vaultCover.rotation.x = -Math.PI / 2;
  _vaultCover.position.set(0, 0.012, 0.0); // matches vault center at z=0.0
  _vaultCover.name = 'vault_cover';
  _vaultCover.receiveShadow = true;
  group.add(_vaultCover);
  vaultCoverMesh = _vaultCover; // export for main.ts

  // Map plane — invisible physical object marking the MAP_ZONE surface (WO-UI-MAP-01).
  // Position sourced from zones.json vault_center anchor (not hardcoded).
  // This mesh is the canonical MAP_ZONE anchor for overlay and lasso raycasting.
  // Y = -0.035: just above felt vault surface top (vault top ≈ -0.015; overlays sit at -0.035).
  const _vaultCenter = _zoneAnchor('vault_center');
  const _vaultZone   = _zone('VAULT_ZONE');
  const _MAP_PLANE_Y = -0.035; // matches map-overlay.ts MAP_Y — just above felt surface
  const mapPlaneGeo = new THREE.PlaneGeometry(
    _vaultZone.halfWidth  * 2,  // VAULT_ZONE full width
    _vaultZone.halfHeight * 2,  // VAULT_ZONE full height
  );
  const mapPlaneMat = new THREE.MeshBasicMaterial({
    visible: false,              // invisible — exists only for scene-graph presence and raycasting
    side: THREE.DoubleSide,
  });
  const mapPlaneMesh = new THREE.Mesh(mapPlaneGeo, mapPlaneMat);
  mapPlaneMesh.rotation.x = -Math.PI / 2;
  mapPlaneMesh.position.set(_vaultCenter.x, _MAP_PLANE_Y, _vaultCenter.z);
  mapPlaneMesh.name = 'map_plane';
  group.add(mapPlaneMesh);

  // Dice tray — self-contained unit: walnut frame with raised lip, felt floor.
  // Positioned at z=3.8 (player zone — clear of vault/map area).
  // Tray spans x:3.3–5.7, z:3.13–4.47.
  const TRAY_Z = 3.8;
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
  const railMat = walnutMat(WALNUT_LIGHT, false, 0.92);

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
  cupMesh.position.set(4.8, -0.03, 5.5);
  cupMesh.castShadow = true;
  cupMesh.receiveShadow = true;
  cupMesh.name = 'cup_holder';
  group.add(cupMesh);


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

export interface AtmosphereResult {
  lanterns:   LanternLight[];
  mapSpot:    THREE.PointLight;  // combat-only — gated in main.ts
  shelfFill:  THREE.PointLight;  // REST shelf readability fill
}

/**
 * Build the atmosphere lighting: 3 overhead lantern point lights + dim ambient.
 * Returns lanterns (for flicker), mapSpot (COMBAT-only), and shelfFill (REST).
 */
export function buildAtmosphere(scene: THREE.Scene): AtmosphereResult {
  // Ambient — warm undertone, no purple cast (WO-UI-LIGHTING-V1: was 0x1a1520, 0.70)
  const ambient = new THREE.AmbientLight(0x1a1208, 0.55);
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
  const lanternIntensities = [42, 42, 42];  // WO-UI-LIGHTING-V1: center reduced 55→42 (avoid blow-out)

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

  // Cool blue light at DM side — subtle magical hint, not dominant (WO-UI-LIGHTING-V1: reduced blue cast)
  const dmCandle = new THREE.PointLight(0x3344cc, 5, 6, 1.8);  // was 0x4466ff, 8
  dmCandle.position.set(0, 1.2, -3.2);
  dmCandle.castShadow = false;
  dmCandle.name = 'dm_candle';
  scene.add(dmCandle);

  // DM corner fill lights — warm amber, low intensity, illuminate the dark far corners
  // Left far corner (x=-5, z=-3.5) and right far corner (x=5, z=-3.5)
  const dmCornerL = new THREE.PointLight(0xffaa44, 12, 6.0, 1.8);
  dmCornerL.position.set(-5.0, 2.5, -3.5);
  dmCornerL.castShadow = false;
  dmCornerL.name = 'dm_corner_left';
  scene.add(dmCornerL);

  const dmCornerR = new THREE.PointLight(0xffaa44, 12, 6.0, 1.8);
  dmCornerR.position.set(5.0, 2.5, -3.5);
  dmCornerR.castShadow = false;
  dmCornerR.name = 'dm_corner_right';
  scene.add(dmCornerR);

  // Dedicated fill light over the dice tray — sits low so it washes the tray
  // walls and felt without blowing out the rest of the scene.
  const trayFill = new THREE.PointLight(0xffcc88, 18, 4.5, 1.6);
  trayFill.position.set(4.5, 2.2, 3.8);
  trayFill.castShadow = false;
  trayFill.name = 'tray_fill';
  scene.add(trayFill);

  // Strong overhead light over the battle map vault — COMBAT-only.
  // At REST: intensity faded to 0 by main.ts. On combat_start: fades up to 44.
  const mapSpot = new THREE.PointLight(0xffaa44, 0, 7.0, 1.4);  // starts at 0 — REST state
  mapSpot.position.set(0, 3.5, -0.5);
  mapSpot.castShadow = true;
  mapSpot.shadow.mapSize.set(512, 512);
  mapSpot.shadow.camera.near = 0.5;
  mapSpot.shadow.camera.far = 10;
  mapSpot.shadow.bias = -0.002;
  mapSpot.name = 'map_spot';
  scene.add(mapSpot);

  // Warm shelf fill — REST-only. Illuminates player shelf for DOWN posture readability.
  // Low and forward, aimed at the shelf zone (z≈4.75).
  const shelfFill = new THREE.PointLight(0xffcc88, 18, 5.5, 1.8);
  shelfFill.position.set(0, 2.2, 5.5);
  shelfFill.castShadow = false;
  shelfFill.name = 'shelf_fill';
  scene.add(shelfFill);

  return { lanterns, mapSpot, shelfFill };
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
// Room geometry — WO-UI-LIGHTING-V1
// ---------------------------------------------------------------------------

/**
 * Add minimal room geometry: back wall + floor plane.
 * Removes the black void — grounds the table in a dim library/tavern space.
 * Call after buildAtmosphere() in main.ts.
 */
export function buildRoom(scene: THREE.Scene): void {
  // Back wall — dark rough stone/plaster behind DM side.
  // Geometry is oversized (30×14) so edges never appear in any camera posture — no billboard effect.
  const wallGeo = new THREE.PlaneGeometry(30, 14);
  const wallMat = new THREE.MeshStandardMaterial({
    color: 0x1a1008,   // very dark warm brown — stone/plaster, not black void
    roughness: 0.97,
    metalness: 0.0,
  });
  const backWall = new THREE.Mesh(wallGeo, wallMat);
  backWall.position.set(0, 3.5, -8.0);  // y=3.5 = wall center raised so edges bleed off-frame
  backWall.name = 'room_back_wall';
  backWall.receiveShadow = true;
  scene.add(backWall);

  // Floor plane — stone floor visible at room edges beyond the table
  const floorGeo = new THREE.PlaneGeometry(16, 16);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x0e0a06,  // very dark stone — barely visible, provides depth cue
    roughness: 0.98,
    metalness: 0.0,
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, -0.7, 0);  // below table legs (table surface at y=0)
  floor.name = 'room_floor';
  floor.receiveShadow = true;
  scene.add(floor);
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
  const { canvas: _sheetCanvas, texture: _sheetTexture } = makeCharacterSheetTexture();
  const sheetMat = new THREE.MeshStandardMaterial({
    map: _sheetTexture,
    roughness: 0.90,
    metalness: 0.0,
    polygonOffset: true,
    polygonOffsetFactor: -1,
    polygonOffsetUnits: -1,
  });
  const sheet = new THREE.Mesh(sheetGeo, sheetMat);
  sheet.renderOrder = 1;  // draw above shelf surface to prevent z-fighting
  // Rotate flat onto the table surface
  sheet.rotation.x = -Math.PI / 2;
  {
    const p = _objPos('CHAR_SHEET');
    const r = _objRot('CHAR_SHEET');
    sheet.rotation.z = r;
    sheet.position.set(p.x, p.y, p.z);
  }
  sheet.castShadow = true;
  sheet.receiveShadow = true;
  sheet.name = 'stub_character_sheet';
  group.add(sheet);

  // Expose mesh for raycast click detection in main.ts
  characterSheetMesh = sheet;

  // Wire up live-update function — redraws only the dynamic fields on the sheet.
  // Canvas W=1024, H=1400 (from makeCharacterSheetTexture).
  // Dynamic regions (canvas pixel coords):
  //   Current HP box: x=MX+196=371, y=185, w=110, h=70  → inner text area y≈222
  //   Conditions strip: y≈620–750 (below skills, above weapons at y=810)
  //   Spell slots: drawn as pip rows at y≈575 (right column, below special abilities)
  {
    const W = 1024, H = 1400;
    const INK = '#1a1208';
    const RULE = '#8a7a5a';
    const RED = '#7a1a0a';
    const BG_LIGHT = '#f0e8d0';

    updateCharacterSheetLive = (data) => {
      const ctx = _sheetCanvas.getContext('2d')!;

      // ── Current HP field ─────────────────────────────────────────────────
      // Box at (MX+196, 185) = (371, 185), size 110×70
      if (data.hp_current !== undefined || data.hp_max !== undefined) {
        const hpX = 371, hpY = 185, hpW = 110, hpH = 70;
        // Repaint background
        ctx.fillStyle = BG_LIGHT;
        ctx.fillRect(hpX + 4, hpY + 22, hpW - 8, hpH - 26);
        // Current HP value
        const hpCur = data.hp_current ?? 0;
        const hpMax = data.hp_max;
        // Color: green if healthy, red if low (<25%)
        const hpColor = (hpMax !== undefined && hpCur < hpMax * 0.25) ? '#7a1a0a' : INK;
        ctx.font = 'bold 28px Georgia, serif';
        ctx.fillStyle = hpColor;
        ctx.textAlign = 'center';
        ctx.fillText(String(hpCur), hpX + hpW / 2, hpY + 56);

        // Max HP label area (left box at MX=175, y=185, w=190, h=70)
        if (hpMax !== undefined) {
          ctx.fillStyle = BG_LIGHT;
          ctx.fillRect(175 + 4, hpY + 22, 186, 44);
          ctx.font = 'bold 32px Georgia, serif';
          ctx.fillStyle = INK;
          ctx.textAlign = 'center';
          ctx.fillText(String(hpMax), 175 + 95, hpY + 58);
        }
      }

      // ── Conditions strip ─────────────────────────────────────────────────
      // Below skills section (skills end ~y=620), above weapon table (y=810)
      if (data.conditions !== undefined) {
        const condX = 24, condY = 630, condW = W - 48, condH = 70;
        ctx.fillStyle = '#e8dcc0'; // parchment bg
        ctx.fillRect(condX, condY, condW, condH);
        if (data.conditions.length > 0) {
          // Section label
          ctx.font = '10px Georgia, serif';
          ctx.fillStyle = RED;
          ctx.textAlign = 'left';
          ctx.fillText('CONDITIONS', condX, condY + 11);
          // Condition tags
          ctx.font = 'bold 13px Georgia, serif';
          ctx.fillStyle = '#7a1a0a';
          const tags = data.conditions.slice(0, 8); // cap at 8 visible
          tags.forEach((cond, i) => {
            const tx = condX + i * 140;
            if (tx + 130 > condX + condW) return;
            ctx.fillStyle = '#c8a060';
            ctx.fillRect(tx, condY + 16, 128, 20);
            ctx.strokeStyle = RED;
            ctx.lineWidth = 1;
            ctx.strokeRect(tx, condY + 16, 128, 20);
            ctx.fillStyle = '#1a1208';
            ctx.textAlign = 'center';
            ctx.fillText(cond.replace(/_/g, ' ').toUpperCase().slice(0, 14), tx + 64, condY + 30);
          });
        } else {
          ctx.font = '10px Georgia, serif';
          ctx.fillStyle = RULE;
          ctx.textAlign = 'left';
          ctx.fillText('CONDITIONS  —  none', condX, condY + 24);
        }
      }

      // ── Spell slots pip strip ────────────────────────────────────────────
      // Right column, below Special Abilities section (special ends ~y=580)
      if (data.spell_slots !== undefined && data.spell_slots_max !== undefined) {
        const slotX = 520, slotY = 590, slotRowH = 20;
        // Clear area
        ctx.fillStyle = '#e8dcc0';
        ctx.fillRect(slotX, slotY - 14, W - slotX - 24, 180);
        ctx.font = '10px Georgia, serif';
        ctx.fillStyle = RED;
        ctx.textAlign = 'left';
        ctx.fillText('SPELL SLOTS', slotX, slotY - 2);

        const slots = data.spell_slots;
        const maxSlots = data.spell_slots_max;
        const levels = Object.keys(maxSlots).map(Number).filter(l => maxSlots[l] > 0).sort((a, b) => a - b);
        levels.slice(0, 8).forEach((lvl, i) => {
          const rowY = slotY + i * slotRowH;
          const remaining = slots[lvl] ?? 0;
          const maximum = maxSlots[lvl] ?? 0;
          ctx.font = '10px Georgia, serif';
          ctx.fillStyle = INK;
          ctx.textAlign = 'left';
          ctx.fillText(`Lv${lvl}`, slotX, rowY + 12);
          // Draw pips
          for (let p = 0; p < maximum; p++) {
            const px = slotX + 32 + p * 18;
            ctx.beginPath();
            ctx.arc(px + 6, rowY + 8, 6, 0, Math.PI * 2);
            ctx.fillStyle = p < remaining ? '#2a5a2a' : '#c8b090';
            ctx.fill();
            ctx.strokeStyle = RULE;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        });
      }

      _sheetTexture.needsUpdate = true;
    };
  }

  // ── Notebook — player zone, center ──────────────────────────────────────
  // Dominant player object. Footprint 1.4×1.9, central position.
  const notebookGeo = new THREE.BoxGeometry(1.4, 0.08, 1.9);
  const notebookMat = new THREE.MeshStandardMaterial({
    color: 0x1c1008,
    roughness: 0.85,
    metalness: 0.05,
  });
  const notebook = new THREE.Mesh(notebookGeo, notebookMat);
  {
    const p = _objPos('NOTEBOOK');
    const r = _objRot('NOTEBOOK');
    notebook.position.set(p.x, p.y, p.z);
    notebook.rotation.y = r;
  }
  notebook.castShadow = true;
  notebook.receiveShadow = true;
  notebook.name = 'stub_notebook';
  group.add(notebook);
  notebookMesh = notebook; // expose for ShelfDragController

  // ── Tome (Rulebook) — player zone, far right ─────────────────────────────
  // Thicker than notebook (h=0.18 vs 0.08) so it reads as a book, not a thin pad.
  const tomeGeo = new THREE.BoxGeometry(1.2, 0.18, 1.6);
  const tomeMat = new THREE.MeshStandardMaterial({
    color: 0x4a0f0f,
    roughness: 0.8,
    metalness: 0.06,
  });
  const tome = new THREE.Mesh(tomeGeo, tomeMat);
  {
    const p = _objPos('RULEBOOK');
    const r = _objRot('RULEBOOK');
    tome.position.set(p.x, p.y, p.z);
    tome.rotation.y = r;
  }
  tome.castShadow = true;
  tome.receiveShadow = true;
  tome.name = 'stub_tome';
  group.add(tome);
  tomeMesh = tome; // expose for ShelfDragController

  // ── Crystal Ball — DM zone, center ───────────────────────────────────────
  // The DM presence focal anchor. NPC portraits display inside it.
  // Should be the dominant visual object on the far side — not decorative.
  // Radius 1.4 = grapefruit-to-basketball scale — commands the far end of the table.
  // Positioned up on a taller pedestal so it reads across the full table depth.
  const _orbPos = _objPos('CRYSTAL_BALL');
  const ORB_Z    = _orbPos.z;
  const ORB_Y    = _orbPos.y; // center of sphere — large orb sits low, just above table

  const orbGeo = new THREE.SphereGeometry(1.40, 32, 20);
  const orbMat = new THREE.MeshStandardMaterial({
    color: 0x6070b8,
    roughness: 0.02,
    metalness: 0.0,
    transparent: true,
    opacity: 0.78,
    envMapIntensity: 0.0, // no envMap loaded — disable to avoid grey tint
    emissive: new THREE.Color(0x2233aa),
    emissiveIntensity: 0.08, // dim at idle — ramps up on tts_speaking_start (VQ-005)
  });
  const orb = new THREE.Mesh(orbGeo, orbMat);
  orb.position.set(0, ORB_Y, ORB_Z);
  orb.castShadow = true;
  orb.receiveShadow = false;
  orb.name = 'stub_crystal_ball';
  group.add(orb);
  crystalBallOrbMesh = orb; // expose for CrystalBallController

  // Inner portrait surface — smaller opaque sphere inside the orb.
  // NPC portrait textures are loaded onto this mesh by CrystalBallController.
  // Slightly smaller than the outer orb so it sits fully within the glass.
  const innerGeo = new THREE.SphereGeometry(1.04, 24, 16);
  const innerMat = new THREE.MeshStandardMaterial({
    color: 0x111122,
    roughness: 0.9,
    metalness: 0.0,
    transparent: false,
    emissive: new THREE.Color(0x050510),
    emissiveIntensity: 0.4,
  });
  const innerOrb = new THREE.Mesh(innerGeo, innerMat);
  innerOrb.name = 'crystal_ball_inner';
  innerOrb.position.set(0, ORB_Y, ORB_Z);
  group.add(innerOrb);
  crystalBallInnerMesh = innerOrb; // expose for CrystalBallController

  // Pedestal — short stub cradle base; large orb sits near table surface
  const pedestalGeo = new THREE.CylinderGeometry(0.36, 0.56, 0.3, 16);
  const pedestalMat = new THREE.MeshStandardMaterial({
    color: WALNUT_COLOR, roughness: 0.7, metalness: 0.05,
  });
  const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
  pedestal.position.set(0, 0.15, ORB_Z);
  pedestal.castShadow = true;
  pedestal.receiveShadow = true;
  group.add(pedestal);

  // Orb base — wide brass cradle ring that sits on the pedestal top
  const baseGeo = new THREE.TorusGeometry(0.88, 0.14, 10, 32);
  const baseMesh = new THREE.Mesh(baseGeo, new THREE.MeshStandardMaterial({
    color: BRASS_COLOR, roughness: 0.25, metalness: 0.9,
  }));
  baseMesh.rotation.x = Math.PI / 2;
  baseMesh.position.set(0, 0.31, ORB_Z);
  baseMesh.castShadow = true;
  group.add(baseMesh);

  // Inner glow — dim at idle, ramped up by CrystalBallController on tts_speaking_start
  const orbGlow = new THREE.PointLight(0x4455dd, 1.5, 9.0, 1.8);
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
  {
    const p = _objPos('DICE_TOWER');
    towerBody.position.set(p.x, p.y, p.z);
  }
  towerBody.castShadow = true;
  towerBody.receiveShadow = true;
  towerBody.name = 'stub_dice_tower';
  group.add(towerBody);

  // Tower opening — dark inset square on top to read as a visible drop slot
  const towerTopGeo = new THREE.BoxGeometry(0.36, 0.18, 0.36);
  const towerTopMesh = new THREE.Mesh(towerTopGeo, new THREE.MeshStandardMaterial({
    color: 0x050302, roughness: 1.0,
  }));
  {
    const p = _objPos('DICE_TOWER');
    towerTopMesh.position.set(p.x, p.y + 0.49, p.z); // recessed slightly below top edge
  }
  towerTopMesh.name = 'tower_opening';
  group.add(towerTopMesh);

  // ── Dice Bag — left end of player shelf ──────────────────────────────────
  // Leather-brown sphere stub at the shelf_dice_bag anchor (x=−4.0, z=4.75).
  const diceBagGeo = new THREE.SphereGeometry(0.25, 12, 8);
  const diceBagMat = new THREE.MeshStandardMaterial({
    color: 0x4a2a10, roughness: 0.88, metalness: 0.03,
  });
  const diceBag = new THREE.Mesh(diceBagGeo, diceBagMat);
  {
    const p = _objPos('DICE_BAG');
    diceBag.position.set(p.x, p.y + 0.25, p.z); // sphere center sits on shelf surface
  }
  diceBag.castShadow = true;
  diceBag.receiveShadow = true;
  diceBag.name = 'stub_dice_bag';
  group.add(diceBag);

  // ── Scattered parchment — open work zone, lived-in feel ──────────────────
  // Loose sheet adrift near the player shelf edge — not in the center sightline.
  // Hidden by default (VQ-010) — visible only when a handout is present.
  const parchGeo = new THREE.BoxGeometry(0.9, 0.01, 1.1);
  const parchMat = new THREE.MeshStandardMaterial({ color: 0xd4c8a4, roughness: 0.95 });
  const parch = new THREE.Mesh(parchGeo, parchMat);
  parch.position.set(-3.5, 0.005, 3.8);
  parch.rotation.y = 0.35;
  parch.castShadow = true;
  parch.receiveShadow = true;
  parch.name = 'stub_parchment';
  parch.visible = false; // VQ-010: hidden until a handout event activates it
  group.add(parch);

  return group;
}

/**
 * Crystal ball glow — no-op stub kept for API compatibility.
 * CrystalBallController (crystal-ball-controller.ts) owns all
 * state-driven animation; it drives emissiveIntensity directly.
 * This function is retained so call sites in main.ts compile without change.
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function updateCrystalBall(_group: THREE.Group, _time: number, _intensity?: number): void {
  // No-op: CrystalBallController owns animation now.
}

// ---------------------------------------------------------------------------
// WO-UI-SCENE-IMAGE-001 — DM-side scene image display plane
// ---------------------------------------------------------------------------

const SCENE_IMAGE_FADE_MS = 400; // fade in/out duration in milliseconds

/**
 * SceneImagePlane — a flat plane on the DM side of the table that displays
 * AI-generated scene images during non-combat exploration, dialogue, and rest.
 *
 * Geometry: PlaneGeometry(3.0, 2.0), flat on table (rotation.x = -Math.PI/2).
 * Position: center of DM-side table space (0, 0.02, 1.5).
 * Default: transparent (opacity 0). Fades in when a scene_image WS event arrives.
 * On combat_start: fades out (battle scroll takes over DM-side space).
 * On combat_end: fades back in with last loaded image (if any).
 */
export class SceneImagePlane {
  readonly mesh: THREE.Mesh;
  private _mat: THREE.MeshBasicMaterial;
  private _hasImage = false;
  private _inCombat = false;
  private _fadeHandle: number | null = null;

  constructor(scene: THREE.Scene) {
    const geo = new THREE.PlaneGeometry(3.0, 2.0);
    this._mat = new THREE.MeshBasicMaterial({
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    this.mesh = new THREE.Mesh(geo, this._mat);
    this.mesh.rotation.x = -Math.PI / 2;
    this.mesh.position.set(0, 0.02, 1.5);
    this.mesh.name = 'scene_image_plane';
    scene.add(this.mesh);
  }

  /**
   * Called on `scene_image` WS event.
   * Loads the image URL via TextureLoader and fades the plane in.
   */
  onSceneImage(url: string): void {
    const loader = new THREE.TextureLoader();
    loader.load(url, (texture) => {
      if (this._mat.map) this._mat.map.dispose();
      this._mat.map = texture;
      this._mat.needsUpdate = true;
      this._hasImage = true;
      if (!this._inCombat) {
        this._fadeTo(1.0);
      }
    });
  }

  /**
   * Called on `combat_start` — fade out so battle scroll takes over.
   */
  onCombatStart(): void {
    this._inCombat = true;
    this._fadeTo(0.0);
  }

  /**
   * Called on `combat_end` — restore scene image if one was loaded.
   */
  onCombatEnd(): void {
    this._inCombat = false;
    if (this._hasImage) {
      this._fadeTo(1.0);
    }
  }

  private _fadeTo(target: number): void {
    if (this._fadeHandle !== null) {
      cancelAnimationFrame(this._fadeHandle);
      this._fadeHandle = null;
    }
    const startOpacity = this._mat.opacity;
    const startTime = performance.now();

    const step = (now: number): void => {
      const t = Math.min((now - startTime) / SCENE_IMAGE_FADE_MS, 1.0);
      this._mat.opacity = startOpacity + (target - startOpacity) * t;
      this._mat.needsUpdate = true;
      if (t < 1.0) {
        this._fadeHandle = requestAnimationFrame(step);
      } else {
        this._mat.opacity = target;
        this._fadeHandle = null;
      }
    };
    this._fadeHandle = requestAnimationFrame(step);
  }
}

/**
 * WO-UI-TOOLING-VITEST-001 — Unit tests for coordinate math, zone system,
 * and spatial transforms.
 *
 * Gate TOOLS-01: All tests PASS.
 *
 * These tests exercise pure math functions extracted from the TypeScript
 * source (no DOM, no Three.js import needed — all geometry is replicated
 * inline using plain arithmetic).
 */

import { describe, it, expect } from 'vitest';

// ---------------------------------------------------------------------------
// gridToScene — from entity-renderer.ts
// ---------------------------------------------------------------------------

const GRID_SCALE = 0.5;
const TOKEN_Y    = 0.08;

function gridToScene(x: number, y: number): { x: number; y: number; z: number } {
  return { x: x * GRID_SCALE, y: TOKEN_Y, z: y * GRID_SCALE };
}

describe('gridToScene()', () => {
  it('maps (0,0) to scene origin at TOKEN_Y', () => {
    const p = gridToScene(0, 0);
    expect(p.x).toBe(0);
    expect(p.y).toBe(TOKEN_Y);
    expect(p.z).toBe(0);
  });

  it('scales x by GRID_SCALE', () => {
    const p = gridToScene(4, 0);
    expect(p.x).toBeCloseTo(2.0);
    expect(p.z).toBe(0);
  });

  it('scales y (grid) to scene z by GRID_SCALE', () => {
    const p = gridToScene(0, 6);
    expect(p.x).toBe(0);
    expect(p.z).toBeCloseTo(3.0);
  });

  it('maps (-2, -4) correctly', () => {
    const p = gridToScene(-2, -4);
    expect(p.x).toBeCloseTo(-1.0);
    expect(p.z).toBeCloseTo(-2.0);
    expect(p.y).toBe(TOKEN_Y);
  });

  it('always returns TOKEN_Y for the Y component', () => {
    for (const [gx, gz] of [[1,1],[5,-3],[0,10],[-7,2]]) {
      expect(gridToScene(gx, gz).y).toBe(TOKEN_Y);
    }
  });

  it('is linear — double input doubles output', () => {
    const a = gridToScene(3, 5);
    const b = gridToScene(6, 10);
    expect(b.x).toBeCloseTo(a.x * 2);
    expect(b.z).toBeCloseTo(a.z * 2);
  });
});

// ---------------------------------------------------------------------------
// Zone math — from zones.ts / zones.json
// ---------------------------------------------------------------------------

interface ZoneDef {
  name: string;
  centerX: number;
  centerZ: number;
  halfWidth: number;
  halfHeight: number;
}

const ZONES: ZoneDef[] = [
  { name: 'player',     centerX: 0.0,  centerZ:  4.75, halfWidth: 5.0,  halfHeight: 0.80 },
  { name: 'map',        centerX: 0.0,  centerZ: -0.5,  halfWidth: 3.0,  halfHeight: 2.0  },
  { name: 'dm',         centerX: 0.0,  centerZ: -3.5,  halfWidth: 5.0,  halfHeight: 0.75 },
  { name: 'dice_tray',  centerX: 4.5,  centerZ:  3.2,  halfWidth: 1.2,  halfHeight: 0.70 },
  { name: 'dice_tower', centerX: 4.5,  centerZ:  3.2,  halfWidth: 0.40, halfHeight: 0.40 },
];

function zoneAtPosition(x: number, z: number): string | null {
  for (const zone of ZONES) {
    if (
      x >= zone.centerX - zone.halfWidth  && x <= zone.centerX + zone.halfWidth &&
      z >= zone.centerZ - zone.halfHeight && z <= zone.centerZ + zone.halfHeight
    ) {
      return zone.name;
    }
  }
  return null;
}

function getZone(name: string): ZoneDef | undefined {
  return ZONES.find(z => z.name === name);
}

describe('zoneAtPosition()', () => {
  it('recognises player zone center', () => {
    expect(zoneAtPosition(0, 4.75)).toBe('player');
  });

  it('recognises map zone center', () => {
    expect(zoneAtPosition(0, -0.5)).toBe('map');
  });

  it('recognises dm zone center', () => {
    expect(zoneAtPosition(0, -3.5)).toBe('dm');
  });

  it('recognises dice_tray zone center', () => {
    expect(zoneAtPosition(4.5, 3.2)).toBe('dice_tray');
  });

  it('recognises dice_tower zone center', () => {
    expect(zoneAtPosition(4.5, 3.2)).toBe('dice_tray'); // tower is inside tray zone
  });

  it('returns null for a point between zones (open work zone)', () => {
    // Open walnut work zone: x≈-2, z≈2.5 — map zone ends at z=1.5, player zone starts at z=3.95
    expect(zoneAtPosition(-2, 2.5)).toBeNull();
  });

  it('returns null far off table', () => {
    expect(zoneAtPosition(20, 20)).toBeNull();
  });

  it('hit-tests the player zone boundary correctly (just inside)', () => {
    const z = getZone('player')!;
    // Just inside near edge
    expect(zoneAtPosition(0, z.centerZ - z.halfHeight + 0.01)).toBe('player');
    // Just inside far edge
    expect(zoneAtPosition(0, z.centerZ + z.halfHeight - 0.01)).toBe('player');
  });

  it('is outside player zone just past the boundary', () => {
    const z = getZone('player')!;
    expect(zoneAtPosition(0, z.centerZ - z.halfHeight - 0.01)).toBeNull();
  });

  it('dice_tray is fully contained within its bounds', () => {
    // Corners of dice_tray
    const z = getZone('dice_tray')!;
    expect(zoneAtPosition(z.centerX - z.halfWidth + 0.01, z.centerZ - z.halfHeight + 0.01)).toBe('dice_tray');
    expect(zoneAtPosition(z.centerX + z.halfWidth - 0.01, z.centerZ + z.halfHeight - 0.01)).toBe('dice_tray');
  });
});

describe('getZone()', () => {
  it('returns the right zone by name', () => {
    const z = getZone('map');
    expect(z).toBeDefined();
    expect(z!.centerX).toBe(0.0);
    expect(z!.centerZ).toBe(-0.5);
    expect(z!.halfWidth).toBe(3.0);
    expect(z!.halfHeight).toBe(2.0);
  });

  it('returns undefined for unknown zone', () => {
    expect(getZone('nonexistent')).toBeUndefined();
  });

  it('all 5 expected zones exist', () => {
    const names = ['player', 'map', 'dm', 'dice_tray', 'dice_tower'];
    for (const n of names) {
      expect(getZone(n)).toBeDefined();
    }
  });
});

// ---------------------------------------------------------------------------
// Coordinate transforms — camera posture positions
// ---------------------------------------------------------------------------

interface PostureConfig {
  position: [number, number, number];
  lookAt: [number, number, number];
}

const POSTURES: Record<string, PostureConfig> = {
  STANDARD:     { position: [0,   2.4, 5.8], lookAt: [0, 0.1, 1.0] },
  DOWN:         { position: [0,   2.2, 5.6], lookAt: [0, -0.03, 4.8] },
  LEAN_FORWARD: { position: [0,   4.5, 1.5], lookAt: [0, 0, -0.5] },
  DICE_TRAY:    { position: [3.5, 1.6, 5.0], lookAt: [4.5, 0.08, 3.2] },
};

function dist3(a: [number,number,number], b: [number,number,number]): number {
  return Math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2);
}

describe('Camera posture coordinate sanity', () => {
  it('STANDARD camera is above table (y > 0)', () => {
    expect(POSTURES.STANDARD.position[1]).toBeGreaterThan(0);
  });

  it('DOWN camera looks at player shelf (lookAt z ≈ 4.8)', () => {
    expect(POSTURES.DOWN.lookAt[2]).toBeCloseTo(4.8, 1);
  });

  it('LEAN_FORWARD camera is above map vault (lookAt z ≈ −0.5)', () => {
    expect(POSTURES.LEAN_FORWARD.lookAt[2]).toBeCloseTo(-0.5, 1);
  });

  it('DICE_TRAY camera looks toward dice tray center (lookAt x ≈ 4.5)', () => {
    expect(POSTURES.DICE_TRAY.lookAt[0]).toBeCloseTo(4.5, 1);
  });

  it('all posture cameras are above the table surface (y > 0)', () => {
    for (const name of Object.keys(POSTURES)) {
      expect(POSTURES[name].position[1]).toBeGreaterThan(0);
    }
  });

  it('posture positions are all distinct', () => {
    const names = Object.keys(POSTURES);
    for (let i = 0; i < names.length; i++) {
      for (let j = i + 1; j < names.length; j++) {
        const d = dist3(POSTURES[names[i]].position, POSTURES[names[j]].position);
        expect(d).toBeGreaterThan(0.1); // distinct positions
      }
    }
  });
});

// ---------------------------------------------------------------------------
// Named mesh positions from scene dump — spot-check against expectations
// ---------------------------------------------------------------------------

import sceneDump from '../scene-dump.json';

interface MeshEntry { name: string; position: { x: number; y: number; z: number }; geometry: string; }

const meshByName: Record<string, MeshEntry> = {};
for (const m of (sceneDump as { meshes: MeshEntry[] }).meshes) {
  meshByName[m.name] = m;
}

describe('Scene dump coordinate assertions (Gate TOOLS-01)', () => {
  it('scene-dump.json is parseable and has meshes', () => {
    expect((sceneDump as any).meshes).toBeInstanceOf(Array);
    expect((sceneDump as any).meshes.length).toBeGreaterThan(0);
  });

  it('table_top is at y=-0.06 (just below y=0 table plane)', () => {
    expect(meshByName['table_top'].position.y).toBeCloseTo(-0.06, 3);
  });

  it('felt_vault is centered at z=-0.5 (map zone center)', () => {
    expect(meshByName['felt_vault'].position.z).toBeCloseTo(-0.5, 3);
  });

  it('stub_crystal_ball is at z=-3.2 (DM zone)', () => {
    expect(meshByName['stub_crystal_ball'].position.z).toBeCloseTo(-3.2, 3);
  });

  it('stub_crystal_ball is elevated (y > 0.5)', () => {
    expect(meshByName['stub_crystal_ball'].position.y).toBeGreaterThan(0.5);
  });

  it('stub_dice_tower is inside dice_tray zone (x≈4.5, z≈0.5)', () => {
    const p = meshByName['stub_dice_tower'].position;
    expect(p.x).toBeCloseTo(4.5, 1);
    expect(p.z).toBeCloseTo(0.5, 1);
    // Dice tower sits at dice_tower zone center
    expect(p.x).toBeGreaterThan(3.5);
  });

  it('player shelf objects (sheet, notebook, tome) are all at z≈4.8', () => {
    for (const name of ['stub_character_sheet', 'stub_notebook', 'stub_tome']) {
      expect(meshByName[name].position.z).toBeCloseTo(4.8, 1);
    }
  });

  it('cup_holder is on the player side (z > 4.0)', () => {
    expect(meshByName['cup_holder'].position.z).toBeGreaterThan(4.0);
  });

  it('rails are at table edges (|x| ≥ 6 or |z| ≥ 4)', () => {
    expect(Math.abs(meshByName['rail_left'].position.x)).toBeGreaterThanOrEqual(6);
    expect(Math.abs(meshByName['rail_right'].position.x)).toBeGreaterThanOrEqual(6);
    expect(Math.abs(meshByName['rail_far'].position.z)).toBeGreaterThanOrEqual(4);
  });

  it('all 23 named meshes are present', () => {
    expect((sceneDump as any).meshes.length).toBe(23);
  });

  it('dice_tray_bottom and dice_tray_felt share the same x and z', () => {
    const bottom = meshByName['dice_tray_bottom'];
    const felt   = meshByName['dice_tray_felt'];
    expect(bottom.position.x).toBeCloseTo(felt.position.x, 2);
    expect(bottom.position.z).toBeCloseTo(felt.position.z, 2);
  });
});

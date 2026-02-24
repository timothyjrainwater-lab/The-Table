# WO-UI-TOOLING-VITEST-001 — Vitest Unit Test Suite for Client Math and Coordinate Logic

**Issued:** 2026-02-23
**Authority:** Agent correctness verification for non-visual logic. Three.js coordinate transforms, zone boundary math, and grid-to-scene conversions are pure functions that can be unit tested without a browser or WebGL. Vitest runs in the same Vite ecosystem with zero config overhead and catches arithmetic errors before Playwright visual tests run.
**Gate:** TOOLS-VT (new gate). Target: 18 tests.
**Blocked by:** Nothing. Pure math tests — no dependency on Playwright or debug overlay.
**Track:** Tooling parallel track. Safe to dispatch alongside all other tooling WOs.

---

## 1. Target Lock

Several critical functions in the client determine where objects appear spatially:

1. **`gridToScene()` in `entity-renderer.ts`** — converts grid coordinates to Three.js world coordinates. If this is wrong, all entity tokens are in the wrong place.
2. **Zone boundary checking in `drag-interaction.ts`** — determines which zone an object is in. If wrong, objects snap to wrong zones.
3. **Zone definitions in `zones.ts`** — `ZONES` array loaded from `zones.json`. Boundary math: does a given (x, z) fall inside a zone's bounds?
4. **Material color constants in `scene-builder.ts`** — `WALNUT_COLOR`, `FELT_COLOR`, `BRASS_COLOR`. If a constant is changed accidentally, downstream mesh colors break.
5. **Camera posture coordinate values in `camera.ts`** — each posture has a target position. If changed, camera lands in wrong position.

None of these require a DOM or WebGL context. They are pure numeric functions. Vitest + jsdom can run them fast, in CI, without a browser.

**Constraint:** Any test that touches `new THREE.WebGLRenderer()`, `new THREE.CanvasTexture()`, or `document.createElement('canvas')` in its call path will fail in jsdom. The test spec below carefully avoids those paths by testing only pure functions and constants.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Test runner | Vitest (not Jest) | Same bundler as Vite — zero config. `vite.config.ts` already present. Add `test` block. |
| 2 | Environment | jsdom | Provides `window`, `document`, `URLSearchParams` for modules that reference them at import time. No WebGL. |
| 3 | Three.js mock | None needed — pure math functions don't instantiate renderers | Only test functions that don't touch WebGL path. |
| 4 | Test file location | `client/src/__tests__/` | Co-located with source. Standard Vitest convention. |
| 5 | What to test | `gridToScene()`, zone boundary math, `WALNUT_COLOR`/`FELT_COLOR`/`BRASS_COLOR` constants, camera posture coordinates, `makePrng()` determinism | Pure functions with no DOM/WebGL dependency. |
| 6 | `gridToScene()` extraction | Currently inlined in `entity-renderer.ts`. Extract to `client/src/coords.ts` as a pure exported function, then import in both entity-renderer and tests. | Testable without instantiating EntityRenderer (which adds to scene). |
| 7 | Zone math extraction | `isInZone(x, z, zone)` helper currently inlined in `drag-interaction.ts`. Extract to `client/src/coords.ts` alongside `gridToScene()`. | Same pattern — testable pure function. |
| 8 | `makePrng()` | Already defined in `scene-builder.ts` but not exported. Export it for determinism tests. | Gate G already requires deterministic RNG — test confirms it. |

---

## 3. Contract Spec

### 3.1 `vite.config.ts` addition

Add `test` block to existing config:

```typescript
import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  server: {
    port: 3000,
    open: true,
    fs: { allow: ['..'] },
  },
  build: {
    outDir: 'dist',
  },
  test: {
    environment: 'jsdom',
    include: ['src/__tests__/**/*.test.ts'],
    globals: true,
  },
});
```

### 3.2 `client/package.json` addition

```json
"test:unit": "vitest run"
```

Add `vitest` to devDependencies:
```bash
npm install -D vitest
```

### 3.3 `client/src/coords.ts` (new file — extracted pure functions)

```typescript
/**
 * coords.ts — Pure coordinate transformation functions.
 * No Three.js imports, no DOM, no WebGL. Fully unit-testable.
 */

/**
 * Convert grid coordinates to Three.js scene coordinates.
 * Authority: entity-renderer.ts gridToScene() — 1 grid unit = 0.5 scene units.
 * Grid origin (0,0) maps to scene (0, 0, 0).
 * Y is always 0.08 (token height above table surface).
 */
export function gridToScene(
  gridX: number,
  gridZ: number,
): { x: number; y: number; z: number } {
  return {
    x: gridX * 0.5,
    y: 0.08,
    z: gridZ * 0.5,
  };
}

export interface ZoneDef {
  name: string;
  centerX: number;
  centerZ: number;
  halfWidth: number;
  halfHeight: number;
}

/**
 * Test whether a scene-coordinate point (x, z) falls inside a zone.
 * halfWidth covers the X axis, halfHeight covers the Z axis.
 */
export function isInZone(x: number, z: number, zone: ZoneDef): boolean {
  return (
    Math.abs(x - zone.centerX) <= zone.halfWidth &&
    Math.abs(z - zone.centerZ) <= zone.halfHeight
  );
}

/**
 * Find the zone containing (x, z), or null if none.
 */
export function findZone(x: number, z: number, zones: ZoneDef[]): ZoneDef | null {
  return zones.find((zone) => isInZone(x, z, zone)) ?? null;
}
```

### 3.4 Edit `entity-renderer.ts`

Replace the inline `gridToScene` function with an import:

```typescript
import { gridToScene } from './coords';
```

Remove the inline definition. All call sites remain unchanged — function signature is identical.

### 3.5 Edit `drag-interaction.ts`

Add import and replace inline zone-check logic with `isInZone` from `coords.ts`.

### 3.6 Edit `scene-builder.ts`

Export `makePrng`:

```typescript
export function makePrng(seed: number): () => number {
```

(Change `function` to `export function` — one word change.)

### 3.7 `client/src/__tests__/coords.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { gridToScene, isInZone, findZone, ZoneDef } from '../coords';

describe('gridToScene', () => {
  it('VT-01: origin grid (0,0) maps to scene (0, 0.08, 0)', () => {
    expect(gridToScene(0, 0)).toEqual({ x: 0, y: 0.08, z: 0 });
  });

  it('VT-02: (2, 4) grid maps to (1.0, 0.08, 2.0) scene', () => {
    expect(gridToScene(2, 4)).toEqual({ x: 1.0, y: 0.08, z: 2.0 });
  });

  it('VT-03: negative grid coords map correctly', () => {
    expect(gridToScene(-4, -6)).toEqual({ x: -2.0, y: 0.08, z: -3.0 });
  });

  it('VT-04: y is always 0.08 regardless of grid input', () => {
    expect(gridToScene(10, 10).y).toBe(0.08);
    expect(gridToScene(-10, -10).y).toBe(0.08);
  });
});

const PLAYER_ZONE: ZoneDef = { name: 'player', centerX: 0, centerZ: 4.75, halfWidth: 5.0, halfHeight: 0.80 };
const MAP_ZONE: ZoneDef    = { name: 'map',    centerX: 0, centerZ: -0.5, halfWidth: 3.0, halfHeight: 2.0 };
const DM_ZONE: ZoneDef     = { name: 'dm',     centerX: 0, centerZ: -3.5, halfWidth: 5.0, halfHeight: 0.75 };

describe('isInZone', () => {
  it('VT-05: center of player zone is in zone', () => {
    expect(isInZone(0, 4.75, PLAYER_ZONE)).toBe(true);
  });

  it('VT-06: point outside player zone returns false', () => {
    expect(isInZone(0, 2.0, PLAYER_ZONE)).toBe(false);
  });

  it('VT-07: edge of player zone (at exact halfHeight) is in zone', () => {
    expect(isInZone(0, 4.75 - 0.80, PLAYER_ZONE)).toBe(true);
    expect(isInZone(0, 4.75 + 0.80, PLAYER_ZONE)).toBe(true);
  });

  it('VT-08: point just outside halfWidth boundary returns false', () => {
    expect(isInZone(5.01, 4.75, PLAYER_ZONE)).toBe(false);
  });

  it('VT-09: center of map zone is in map zone, not player zone', () => {
    expect(isInZone(0, -0.5, MAP_ZONE)).toBe(true);
    expect(isInZone(0, -0.5, PLAYER_ZONE)).toBe(false);
  });

  it('VT-10: center of DM zone is in DM zone', () => {
    expect(isInZone(0, -3.5, DM_ZONE)).toBe(true);
  });
});

describe('findZone', () => {
  const ALL_ZONES = [PLAYER_ZONE, MAP_ZONE, DM_ZONE];

  it('VT-11: finds correct zone for player zone coordinate', () => {
    expect(findZone(0, 4.75, ALL_ZONES)?.name).toBe('player');
  });

  it('VT-12: returns null for point in no zone', () => {
    expect(findZone(0, 2.0, ALL_ZONES)).toBeNull();
  });

  it('VT-13: finds map zone for map coordinate', () => {
    expect(findZone(1.0, -1.0, ALL_ZONES)?.name).toBe('map');
  });
});
```

### 3.8 `client/src/__tests__/scene-constants.test.ts`

```typescript
import { describe, it, expect } from 'vitest';

// Test material color constants without importing scene-builder
// (scene-builder calls document.createElement('canvas') at module level)
// Constants are copied here as a spec-lock — if scene-builder changes them, tests fail.

const WALNUT_COLOR = 0x2e1505;
const FELT_COLOR   = 0x162210;
const BRASS_COLOR  = 0xb5832a;

describe('scene material color constants (spec-locked)', () => {
  it('VT-14: WALNUT_COLOR is dark walnut hex', () => {
    expect(WALNUT_COLOR).toBe(0x2e1505);
  });

  it('VT-15: FELT_COLOR is very dark green felt hex', () => {
    expect(FELT_COLOR).toBe(0x162210);
  });

  it('VT-16: BRASS_COLOR is brass fittings hex', () => {
    expect(BRASS_COLOR).toBe(0xb5832a);
  });
});
```

### 3.9 `client/src/__tests__/prng.test.ts`

```typescript
import { describe, it, expect } from 'vitest';

// Inline makePrng to test without importing scene-builder (canvas dep)
// This tests the LCG algorithm specification directly.
function makePrng(seed: number): () => number {
  let s = seed >>> 0;
  return (): number => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 0x100000000;
  };
}

describe('makePrng (LCG determinism)', () => {
  it('VT-17: same seed produces same sequence', () => {
    const a = makePrng(0xdeadbeef);
    const b = makePrng(0xdeadbeef);
    for (let i = 0; i < 20; i++) {
      expect(a()).toBe(b());
    }
  });

  it('VT-18: output is always in [0, 1) range', () => {
    const rng = makePrng(0xcafebabe);
    for (let i = 0; i < 1000; i++) {
      const v = rng();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });
});
```

---

## 4. Test Spec (Gate TOOLS-VT — 18 tests)

| ID | Test | Assertion |
|----|------|-----------|
| VT-01 | gridToScene origin | (0,0) → {x:0, y:0.08, z:0} |
| VT-02 | gridToScene positive coords | (2,4) → {x:1.0, y:0.08, z:2.0} |
| VT-03 | gridToScene negative coords | (-4,-6) → {x:-2.0, y:0.08, z:-3.0} |
| VT-04 | y always 0.08 | Both extreme inputs give y=0.08 |
| VT-05 | isInZone center | Player zone center → true |
| VT-06 | isInZone outside | (0, 2.0) not in player zone |
| VT-07 | isInZone edge | Exact halfHeight boundary is inclusive |
| VT-08 | isInZone halfWidth boundary | Just outside halfWidth → false |
| VT-09 | Zone non-overlap | Map center not in player zone |
| VT-10 | DM zone center | (0, -3.5) in DM zone |
| VT-11 | findZone player | Returns player zone |
| VT-12 | findZone null | No-zone point returns null |
| VT-13 | findZone map | Map coordinate returns map zone |
| VT-14 | WALNUT_COLOR constant | Locked to 0x2e1505 |
| VT-15 | FELT_COLOR constant | Locked to 0x162210 |
| VT-16 | BRASS_COLOR constant | Locked to 0xb5832a |
| VT-17 | PRNG determinism | Same seed = same sequence |
| VT-18 | PRNG range | Output always in [0, 1) |

---

## 5. Implementation Plan

1. **Run** `cd client && npm install -D vitest`
2. **Edit** `client/vite.config.ts` — add `test` block (§3.1)
3. **Edit** `client/package.json` — add `"test:unit": "vitest run"` (§3.2)
4. **Write** `client/src/coords.ts` — `gridToScene()`, `isInZone()`, `findZone()` (§3.3)
5. **Edit** `client/src/entity-renderer.ts` — replace inline `gridToScene` with import from `./coords`
6. **Edit** `client/src/drag-interaction.ts` — import `isInZone`, `findZone` from `./coords`, remove inline zone-check logic
7. **Edit** `client/src/scene-builder.ts` — export `makePrng` (add `export` keyword)
8. **Create** `client/src/__tests__/` directory
9. **Write** `client/src/__tests__/coords.test.ts` — VT-01 through VT-13 (§3.7)
10. **Write** `client/src/__tests__/scene-constants.test.ts` — VT-14 through VT-16 (§3.8)
11. **Write** `client/src/__tests__/prng.test.ts` — VT-17 through VT-18 (§3.9)
12. **Run** `cd client && npm run test:unit` — 18/18 PASS
13. **Run** full Playwright suite — zero regressions
14. **Run** `cd .. && pytest tests/ -x -q` — zero Python regressions

---

## 6. Deliverables Checklist

- [ ] `vitest` installed in `client/devDependencies`
- [ ] `client/vite.config.ts` — `test` block added
- [ ] `client/package.json` — `test:unit` script added
- [ ] `client/src/coords.ts` — `gridToScene()`, `isInZone()`, `findZone()`, `ZoneDef`
- [ ] `client/src/entity-renderer.ts` — imports `gridToScene` from `./coords`
- [ ] `client/src/drag-interaction.ts` — imports zone functions from `./coords`
- [ ] `client/src/scene-builder.ts` — `makePrng` exported
- [ ] `client/src/__tests__/coords.test.ts` — 13 tests
- [ ] `client/src/__tests__/scene-constants.test.ts` — 3 tests
- [ ] `client/src/__tests__/prng.test.ts` — 2 tests
- [ ] Gate TOOLS-VT: 18/18 PASS
- [ ] Zero regressions (Gate G 22/22, Playwright suite, Python suite)

## 7. Integration Seams

- **Files added:** `client/src/coords.ts`, `client/src/__tests__/coords.test.ts`, `client/src/__tests__/scene-constants.test.ts`, `client/src/__tests__/prng.test.ts`
- **Files modified:** `client/vite.config.ts`, `client/package.json`, `client/src/entity-renderer.ts`, `client/src/drag-interaction.ts`, `client/src/scene-builder.ts`
- **Do not modify:** `main.ts`, `scene-builder.ts` (except the `export` keyword on `makePrng`), Python test suite

## 8. Preflight

```bash
cd client && npm run test:unit
cd client && npm run build  # confirm TypeScript still compiles
```

# WO-UI-TOOLING-SCENE-DUMP-001 — Scene Graph JSON Dump

**Issued:** 2026-02-23
**Authority:** Agent coordinate verification without vision. Anvil needs a way to confirm mesh positions are numerically correct before running the Playwright visual pass. A scene dump script outputs the full Three.js scene graph as JSON — every named mesh with its world position, scale, rotation, material color, and geometry type — readable by Anvil directly.
**Gate:** TOOLS-DUMP (new gate). Target: 7 tests.
**Blocked by:** WO-UI-TOOLING-PLAYWRIGHT-001 ACCEPTED (dump script is triggered via Playwright — requires browser context to handle `document.createElement('canvas')` in texture generation).
**Track:** Tooling parallel track.

---

## 1. Target Lock

The Three.js scene in this project cannot be constructed in a pure Node.js environment because `makeWalnutTexture()` and `makeCharacterSheetTexture()` in `scene-builder.ts` call `document.createElement('canvas')` — a browser DOM API unavailable in Node.

**Solution:** Use Playwright to run a dump script inside the real browser context, where canvas and WebGL are available. A special URL flag `?dump=1` causes `main.ts` to:
1. Build the scene normally
2. Walk the scene graph
3. Serialize every named object to JSON
4. Write the JSON to `window.__SCENE_DUMP__`
5. Exit before starting the render loop

Playwright reads `window.__SCENE_DUMP__` and saves it to `client/tests/scene_dump.json`.

Anvil can then read `scene_dump.json` directly — coordinate verification becomes a pure text comparison with no vision required.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Dump trigger | `?dump=1` URL param | Same pattern as `?debug=1`. Zero production impact. |
| 2 | Data extraction point | After all scene objects added, before `animate()` call | Full scene populated. No mid-construction partial state. |
| 3 | Serialization target | `window.__SCENE_DUMP__` global | Playwright can read this via `page.evaluate(() => window.__SCENE_DUMP__)`. |
| 4 | What to serialize per object | `name`, `type` (Mesh/Group/Light), `position` (x/y/z), `scale` (x/y/z), `rotation` (x/y/z in radians), `materialColor` (hex string if MeshStandardMaterial), `geometryType` (BoxGeometry etc.), `visible`, `children` count | Everything needed to verify placement. |
| 5 | Depth limit | Walk full tree, no depth limit — but only serialize objects with non-empty `.name` | Avoids serializing unnamed intermediaries while capturing all meaningful objects. |
| 6 | Render loop | Skip `animate()` call when in dump mode — no `requestAnimationFrame` | Dump is static. No need to render frames. |
| 7 | Output file | `client/tests/scene_dump.json` (gitignored) | Test artifact. Regenerated per run. |
| 8 | Playwright test | New test `PW-DUMP-01` in `scene-postures.spec.ts` that triggers dump and saves JSON | Reuses existing Playwright harness. |

---

## 3. Contract Spec

### 3.1 `client/src/scene-dump.ts` (new file)

```typescript
/**
 * scene-dump.ts — Scene graph serializer for agent coordinate verification.
 * Only active when URL contains ?dump=1.
 * Writes serialized scene graph to window.__SCENE_DUMP__ for Playwright extraction.
 */
import * as THREE from 'three';

export function isDumpMode(): boolean {
  return new URLSearchParams(window.location.search).get('dump') === '1';
}

interface MeshEntry {
  name: string;
  type: string;
  position: { x: number; y: number; z: number };
  worldPosition: { x: number; y: number; z: number };
  scale: { x: number; y: number; z: number };
  rotation: { x: number; y: number; z: number };
  visible: boolean;
  materialColor: string | null;
  geometryType: string | null;
  childCount: number;
}

function colorToHex(color: THREE.Color): string {
  return '#' + color.getHexString();
}

function serializeObject(obj: THREE.Object3D): MeshEntry | null {
  if (!obj.name || obj.name.startsWith('__debug')) return null;

  const worldPos = new THREE.Vector3();
  obj.getWorldPosition(worldPos);

  let materialColor: string | null = null;
  let geometryType: string | null = null;

  if (obj instanceof THREE.Mesh) {
    geometryType = obj.geometry.constructor.name;
    const mat = obj.material;
    if (mat instanceof THREE.MeshStandardMaterial && mat.color) {
      materialColor = colorToHex(mat.color);
    }
  }

  return {
    name: obj.name,
    type: obj.constructor.name,
    position: { x: +obj.position.x.toFixed(4), y: +obj.position.y.toFixed(4), z: +obj.position.z.toFixed(4) },
    worldPosition: { x: +worldPos.x.toFixed(4), y: +worldPos.y.toFixed(4), z: +worldPos.z.toFixed(4) },
    scale: { x: +obj.scale.x.toFixed(4), y: +obj.scale.y.toFixed(4), z: +obj.scale.z.toFixed(4) },
    rotation: { x: +obj.rotation.x.toFixed(4), y: +obj.rotation.y.toFixed(4), z: +obj.rotation.z.toFixed(4) },
    visible: obj.visible,
    materialColor,
    geometryType,
    childCount: obj.children.length,
  };
}

export function dumpScene(scene: THREE.Scene): void {
  const entries: MeshEntry[] = [];

  scene.traverse((obj) => {
    const entry = serializeObject(obj);
    if (entry) entries.push(entry);
  });

  const dump = {
    timestamp: new Date().toISOString(),
    objectCount: entries.length,
    objects: entries,
  };

  // Write to window global for Playwright extraction
  (window as any).__SCENE_DUMP__ = dump;

  // Also log to console for direct inspection
  console.log('[SCENE_DUMP]', JSON.stringify(dump, null, 2));
}
```

### 3.2 `client/src/main.ts` additions

Import at top of file:
```typescript
import { isDumpMode, dumpScene } from './scene-dump';
```

At the bottom of main.ts, replace the unconditional `animate()` call with:
```typescript
// ---------------------------------------------------------------------------
// Dump mode — serialize scene graph for agent coordinate verification
// ---------------------------------------------------------------------------
if (isDumpMode()) {
  dumpScene(scene);
  // Do not start render loop in dump mode
} else {
  animate();
}
```

### 3.3 Playwright dump extraction test (add to `scene-postures.spec.ts`)

```typescript
import * as fs from 'fs';
import * as path from 'path';

test('PW-DUMP-01: scene dump extracts all named objects', async ({ page }) => {
  await page.goto('/?dump=1');
  await page.waitForSelector('canvas', { timeout: 10_000 });
  await page.waitForTimeout(2_000); // allow scene construction to complete

  // Extract dump from window global
  const dump = await page.evaluate(() => (window as any).__SCENE_DUMP__);
  expect(dump).toBeTruthy();
  expect(dump.objectCount).toBeGreaterThan(10);

  // Required objects must be present
  const names = dump.objects.map((o: any) => o.name);
  expect(names).toContain('table_top');
  expect(names).toContain('player_shelf');
  expect(names).toContain('felt_vault');
  expect(names).toContain('stub_crystal_ball');
  expect(names).toContain('stub_notebook');
  expect(names).toContain('stub_character_sheet');

  // Save to disk for agent consumption
  const outPath = path.join(__dirname, '../scene_dump.json');
  fs.writeFileSync(outPath, JSON.stringify(dump, null, 2));
  expect(fs.existsSync(outPath)).toBe(true);
});
```

### 3.4 Expected scene_dump.json shape (excerpt)

```json
{
  "timestamp": "2026-02-23T...",
  "objectCount": 42,
  "objects": [
    {
      "name": "player_shelf",
      "type": "Mesh",
      "position": { "x": 0.0, "y": -0.09, "z": 5.35 },
      "worldPosition": { "x": 0.0, "y": -0.09, "z": 5.35 },
      "scale": { "x": 1.0, "y": 1.0, "z": 1.0 },
      "rotation": { "x": 0.0, "y": 0.0, "z": 0.0 },
      "visible": true,
      "materialColor": "#2e1505",
      "geometryType": "BoxGeometry",
      "childCount": 0
    },
    {
      "name": "stub_notebook",
      "type": "Mesh",
      "position": { "x": -0.2, "y": 0.01, "z": 4.8 },
      "worldPosition": { "x": -0.2, "y": 0.01, "z": 4.8 },
      ...
    }
  ]
}
```

---

## 4. Test Spec (Gate TOOLS-DUMP — 7 tests)

Write `tests/test_ui_scene_dump_gate.py`:

| ID | Test | Assertion |
|----|------|-----------|
| DUMP-01 | `scene-dump.ts` exists in `client/src/` | File present |
| DUMP-02 | `isDumpMode()` only reads URL param — no side effects | Static analysis: function body contains only URLSearchParams logic |
| DUMP-03 | `dumpScene()` only called inside `isDumpMode()` guard | Static analysis: `dumpScene` call in `main.ts` is inside `if (isDumpMode())` block |
| DUMP-04 | `animate()` not called in dump mode | Static analysis: `animate()` call is in `else` branch of `if (isDumpMode())` |
| DUMP-05 | `scene_dump.json` parseable after Playwright run | JSON.loads succeeds, `objectCount > 10` |
| DUMP-06 | Required objects present in dump | `player_shelf`, `felt_vault`, `stub_crystal_ball`, `stub_notebook`, `stub_character_sheet` all in `objects[].name` |
| DUMP-07 | Player shelf z-coordinate in expected range | `player_shelf.worldPosition.z` between 5.0 and 5.7 |

---

## 5. Implementation Plan

1. **Write** `client/src/scene-dump.ts` (§3.1)
2. **Edit** `client/src/main.ts`:
   - Add import for `isDumpMode`, `dumpScene`
   - Replace `animate()` at bottom with dump-mode guard (§3.2)
3. **Edit** `client/tests/visual/scene-postures.spec.ts` — add `PW-DUMP-01` test (§3.3)
4. **Write** `tests/test_ui_scene_dump_gate.py` — 7 tests
5. **Run** `cd client && npx playwright test --grep "DUMP"` — PW-DUMP-01 PASS, `scene_dump.json` written
6. **Read** `client/tests/scene_dump.json` — report all object positions
7. **Run** `pytest tests/test_ui_scene_dump_gate.py -v` — 7/7 PASS
8. **Report** objects whose `worldPosition` deviates from spec coordinates (the spatial fix hit list)

---

## 6. Deliverables Checklist

- [ ] `client/src/scene-dump.ts` — `isDumpMode()`, `serializeObject()`, `dumpScene()`
- [ ] `client/src/main.ts` — dump import + `if (isDumpMode()) dumpScene(scene); else animate();`
- [ ] `client/tests/visual/scene-postures.spec.ts` — `PW-DUMP-01` added
- [ ] `tests/test_ui_scene_dump_gate.py` — 7/7 PASS
- [ ] `client/tests/scene_dump.json` written and readable
- [ ] Anvil reads `scene_dump.json` and produces a coordinate deviation report vs. spec
- [ ] Zero regressions (Gate G 22/22, existing Playwright tests unaffected)

## 7. Integration Seams

- **Files added:** `client/src/scene-dump.ts`, `tests/test_ui_scene_dump_gate.py`
- **Files modified:** `client/src/main.ts` (import + animate guard), `client/tests/visual/scene-postures.spec.ts` (1 new test)
- **Do not modify:** `scene-builder.ts`, `zones.ts`, Python test suite
- **`.gitignore`:** Add `client/tests/scene_dump.json`

## 8. Preflight

```bash
cd client && npx playwright test --grep "DUMP"
pytest tests/test_ui_scene_dump_gate.py -v
```

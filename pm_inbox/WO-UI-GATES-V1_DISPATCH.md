# WO-UI-GATES-V1 — Screenshot Tests + Zone Parity + UI Ban Scan

**Issued:** 2026-02-23
**Authority:** PM — AI2AI Exec Packet (TABLE UI NORTH STAR)
**Sequence:** 6 of 6. Depends on WO-UI-CAMERAS-V1 ACCEPTED (golden frames must exist).
**Gate:** UI-GATES (new gate, defined below)

---

## 1. Target Lock

This WO closes the loop. It adds the automated oracle that prevents the camera/layout from drifting again. Three test suites: screenshot diff tests against golden frames, zone parity assertion, and a static UI ban scan. All three run in CI.

**Done means:** CI fails if any camera posture drifts from its golden frame (beyond tolerance). CI fails if any object leaves its declared zone. CI fails if any banned UI component is found in the codebase.

---

## 2. Binary Decisions — Locked

| Decision | Answer |
|----------|--------|
| Screenshot test runner | Playwright (already in stack from TOOLS-PW gate) |
| Diff algorithm | pixelmatch with tolerance 0.03 (3% pixel diff allowed — handles antialiasing variation) |
| Resolution | 1920×1080 (matches golden frames from WO-UI-CAMERAS-V1) |
| Zone parity test runner | Vitest (unit-level, reads scene dump JSON) |
| UI ban scan runner | Vitest (static grep, no browser needed) |
| Golden frame storage | `docs/design/LAYOUT_PACK_V1/golden/` — committed in WO-UI-CAMERAS-V1 |
| Gate name | `UI-GATES` |

---

## 3. Test Suite 1 — Screenshot Tests (`screenshot.spec.ts`)

### 3.1 Setup

```typescript
// client/tests/screenshot.spec.ts
import { test, expect } from '@playwright/test';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import * as fs from 'fs';
import * as path from 'path';

const GOLDEN_DIR = path.resolve(__dirname, '../../docs/design/LAYOUT_PACK_V1/golden');
const VIEWPORT = { width: 1920, height: 1080 };
const DIFF_TOLERANCE = 0.03; // 3% pixel diff
const DEV_URL = 'http://localhost:5173';

const POSTURE_KEYS: Record<string, string> = {
  'STANDARD': '1',
  'DOWN': '2',
  'LEAN_FORWARD': '3',
  'DICE_TRAY': '4',
};
```

### 3.2 Test: per-posture screenshot diff

```typescript
for (const [postureName, hotkey] of Object.entries(POSTURE_KEYS)) {
  test(`screenshot: ${postureName} matches golden frame`, async ({ page }) => {
    await page.setViewportSize(VIEWPORT);
    await page.goto(DEV_URL);
    await page.waitForLoadState('networkidle');

    // Navigate to posture
    await page.keyboard.press(hotkey);
    await page.waitForTimeout(500);  // allow 350ms transition + margin

    // Capture current
    const currentBuf = await page.screenshot({ type: 'png' });
    const current = PNG.sync.read(currentBuf);

    // Load golden
    const goldenPath = path.join(GOLDEN_DIR, `${postureName}_1080.png`);
    if (!fs.existsSync(goldenPath)) {
      throw new Error(`Golden frame missing: ${goldenPath}. Run WO-UI-CAMERAS-V1 first.`);
    }
    const golden = PNG.sync.read(fs.readFileSync(goldenPath));

    // Diff
    const { width, height } = golden;
    const diff = new PNG({ width, height });
    const mismatch = pixelmatch(golden.data, current.data, diff.data, width, height, {
      threshold: 0.12,  // per-pixel color threshold
    });
    const mismatchRatio = mismatch / (width * height);

    if (mismatchRatio > DIFF_TOLERANCE) {
      // Save diff image for inspection
      const diffPath = path.join(GOLDEN_DIR, `DIFF_${postureName}_1080.png`);
      fs.writeFileSync(diffPath, PNG.sync.write(diff));
    }

    expect(mismatchRatio).toBeLessThanOrEqual(DIFF_TOLERANCE);
  });
}
```

### 3.3 Acceptance checks per posture (pixel region assertions)

In addition to full-frame diff, assert specific regions:

```typescript
test('STANDARD: orb visible (upper center frame)', async ({ page }) => {
  await page.setViewportSize(VIEWPORT);
  await page.goto(DEV_URL);
  await page.waitForLoadState('networkidle');
  await page.keyboard.press('1');
  await page.waitForTimeout(500);

  // Orb should appear in upper-center region: x=700-1220, y=150-450
  // Sample pixel brightness in that region — orb has blue glow, not walnut
  const screenshot = await page.screenshot({ type: 'png' });
  const png = PNG.sync.read(screenshot);
  // Check that some pixel in orb region has significant blue channel
  let maxBlue = 0;
  for (let y = 150; y < 450; y++) {
    for (let x = 700; x < 1220; x++) {
      const idx = (y * 1920 + x) * 4;
      maxBlue = Math.max(maxBlue, png.data[idx + 2]); // B channel
    }
  }
  expect(maxBlue).toBeGreaterThan(80); // orb blue glow must be present
});

test('STANDARD: back wall visible (not pure black void)', async ({ page }) => {
  await page.setViewportSize(VIEWPORT);
  await page.goto(DEV_URL);
  await page.waitForLoadState('networkidle');
  await page.keyboard.press('1');
  await page.waitForTimeout(500);

  const screenshot = await page.screenshot({ type: 'png' });
  const png = PNG.sync.read(screenshot);
  // Back wall region: x=400-1500, y=50-200 (above orb, behind table)
  let maxLum = 0;
  for (let y = 50; y < 200; y++) {
    for (let x = 400; x < 1500; x++) {
      const idx = (y * 1920 + x) * 4;
      const lum = png.data[idx] + png.data[idx + 1] + png.data[idx + 2];
      maxLum = Math.max(maxLum, lum);
    }
  }
  expect(maxLum).toBeGreaterThan(15); // not pure black void
});

test('DOWN: shelf fills frame (high center pixel density)', async ({ page }) => {
  await page.setViewportSize(VIEWPORT);
  await page.goto(DEV_URL);
  await page.waitForLoadState('networkidle');
  await page.keyboard.press('2');
  await page.waitForTimeout(500);

  const screenshot = await page.screenshot({ type: 'png' });
  const png = PNG.sync.read(screenshot);
  // In DOWN posture, center of frame should show shelf objects (warm/brown tones)
  // Sample center region x=600-1320, y=300-700
  let nonBlackPixels = 0;
  const total = 720 * 400;
  for (let y = 300; y < 700; y++) {
    for (let x = 600; x < 1320; x++) {
      const idx = (y * 1920 + x) * 4;
      const lum = png.data[idx] + png.data[idx + 1] + png.data[idx + 2];
      if (lum > 30) nonBlackPixels++;
    }
  }
  expect(nonBlackPixels / total).toBeGreaterThan(0.5); // >50% of frame has content
});

test('DICE_TRAY: tray area occupies significant frame area', async ({ page }) => {
  await page.setViewportSize(VIEWPORT);
  await page.goto(DEV_URL);
  await page.waitForLoadState('networkidle');
  await page.keyboard.press('4');
  await page.waitForTimeout(500);

  const screenshot = await page.screenshot({ type: 'png' });
  const png = PNG.sync.read(screenshot);
  // Tray/tower region: center-right, x=800-1500, y=300-800
  let nonBlackPixels = 0;
  const total = 700 * 500;
  for (let y = 300; y < 800; y++) {
    for (let x = 800; x < 1500; x++) {
      const idx = (y * 1920 + x) * 4;
      const lum = png.data[idx] + png.data[idx + 1] + png.data[idx + 2];
      if (lum > 30) nonBlackPixels++;
    }
  }
  expect(nonBlackPixels / total).toBeGreaterThan(0.35);
});
```

**Total screenshot test count:** 4 posture diffs + 4 region assertions = **8 checks**.

---

## 4. Test Suite 2 — Zone Parity (`zone_parity.spec.ts`)

Uses the `?dump=1` scene dump to enumerate all meshes and check zone membership.

```typescript
// client/tests/zone_parity.spec.ts
import { test, expect } from '@playwright/test';

const DEV_URL = 'http://localhost:5173?dump=1';

test('zone parity: all declared objects within their zones', async ({ page }) => {
  await page.goto(DEV_URL);
  await page.waitForTimeout(2000); // allow scene dump to populate

  const dump = await page.evaluate(() => (window as any).__SCENE_DUMP__);
  expect(dump).toBeTruthy();

  const meshes: Array<{ name: string; x: number; y: number; z: number }> = dump.meshes;
  const zones = dump.zones; // if zones are included in dump

  const findMesh = (name: string) => meshes.find(m => m.name === name);

  // SHELF_ZONE bounds: x ±5.0, z 3.95–5.55 (centerZ=4.75, half=0.80)
  const SHELF = { minX: -5.0, maxX: 5.0, minZ: 3.95, maxZ: 5.55 };
  const inShelf = (m: { x: number; z: number }) =>
    m.x >= SHELF.minX && m.x <= SHELF.maxX && m.z >= SHELF.minZ && m.z <= SHELF.maxZ;

  // DICE_STATION_ZONE bounds: x 3.3–5.7, z −0.2–2.45
  const DICE = { minX: 3.3, maxX: 5.7, minZ: -0.2, maxZ: 2.45 };
  const inDice = (m: { x: number; z: number }) =>
    m.x >= DICE.minX && m.x <= DICE.maxX && m.z >= DICE.minZ && m.z <= DICE.maxZ;

  // DM_ZONE: x ±5.0, z −4.25 to −2.75
  const DM = { minX: -5.0, maxX: 5.0, minZ: -4.25, maxZ: -2.75 };
  const inDM = (m: { x: number; z: number }) =>
    m.x >= DM.minX && m.x <= DM.maxX && m.z >= DM.minZ && m.z <= DM.maxZ;

  const sheet = findMesh('stub_character_sheet');
  expect(sheet).toBeTruthy();
  expect(inShelf(sheet!)).toBe(true);

  const notebook = findMesh('stub_notebook');
  expect(notebook).toBeTruthy();
  expect(inShelf(notebook!)).toBe(true);

  const tome = findMesh('stub_tome');
  expect(tome).toBeTruthy();
  expect(inShelf(tome!)).toBe(true);

  const orb = findMesh('stub_crystal_ball');
  expect(orb).toBeTruthy();
  expect(inDM(orb!)).toBe(true);

  const tower = findMesh('stub_dice_tower');
  expect(tower).toBeTruthy();
  expect(inDice(tower!)).toBe(true);

  // Separation check: sheet → notebook ≥ 2.0 units in X
  expect(Math.abs(notebook!.x - sheet!.x)).toBeGreaterThanOrEqual(2.0);
  // notebook → tome ≥ 2.0 units
  expect(Math.abs(tome!.x - notebook!.x)).toBeGreaterThanOrEqual(2.0);

  // stub_parchment must be invisible
  const parch = findMesh('stub_parchment');
  if (parch) {
    const isVisible = await page.evaluate((name) => {
      const scene = (window as any).__THREE_SCENE__;
      const obj = scene?.getObjectByName(name);
      return obj?.visible ?? false;
    }, 'stub_parchment');
    expect(isVisible).toBe(false);
  }
});
```

**Total zone parity test count:** 1 test with 10 internal assertions → **10 checks**.

---

## 5. Test Suite 3 — UI Ban Scan (`ui_bans_scan.spec.ts`)

Static scan — no browser needed. Checks that banned UI patterns are absent from the source tree.

```typescript
// client/tests/ui_bans_scan.spec.ts
import { test, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as glob from 'glob';

const SRC_DIR = path.resolve(__dirname, '../src');

function readAllTS(): string[] {
  return glob.sync('**/*.ts', { cwd: SRC_DIR }).map(f =>
    fs.readFileSync(path.join(SRC_DIR, f), 'utf8')
  );
}

const BANNED_PATTERNS = [
  { pattern: /tooltip/i,           label: 'tooltip component' },
  { pattern: /popover/i,           label: 'popover component' },
  { pattern: /Tooltip/,            label: 'Tooltip import' },
  { pattern: /Popover/,            label: 'Popover import' },
  { pattern: /roll.*button/i,      label: 'roll button' },
  { pattern: /action.*menu/i,      label: 'action menu' },
  { pattern: /ActionMenu/,         label: 'ActionMenu component' },
  { pattern: /HUD/,                label: 'HUD reference' },
];

for (const { pattern, label } of BANNED_PATTERNS) {
  test(`UI ban: no ${label} in source`, () => {
    const sources = readAllTS();
    for (const src of sources) {
      expect(src).not.toMatch(pattern);
    }
  });
}

test('UI ban: no hardcoded camera positions outside camera_poses.json', () => {
  // Check that camera.ts does not contain literal position vectors
  const cameraSrc = fs.readFileSync(path.join(SRC_DIR, 'camera.ts'), 'utf8');
  // Hardcoded position would look like: new THREE.Vector3(0, 0.75, 6.5)
  // After LAYOUT-PACK-V1, camera.ts reads from JSON — no hardcoded Vector3 with 3 non-zero args
  // This is a soft check: confirm the old hardcoded STANDARD position is gone
  expect(cameraSrc).not.toContain('0, 0.75, 6.5');  // old STANDARD y=0.75
  expect(cameraSrc).not.toContain('0, 2.8, 6.0');   // old DOWN position
});
```

**Total UI ban scan test count:** 8 pattern checks + 1 hardcode check = **9 checks**.

---

## 6. Gate Spec

**Gate name:** `UI-GATES`

Combines all three test suites:

| Suite | File | Checks |
|-------|------|--------|
| Screenshot tests | `screenshot.spec.ts` | 8 |
| Zone parity | `zone_parity.spec.ts` | 10 |
| UI ban scan | `ui_bans_scan.spec.ts` | 9 |
| **Total** | | **27** |

Gate `UI-GATES` 27/27.

---

## 7. Dependencies

- `pixelmatch` and `pngjs` packages must be added to `client/package.json` devDependencies
- Golden frames must exist in `docs/design/LAYOUT_PACK_V1/golden/` (WO-UI-CAMERAS-V1)
- Dev server must be running for screenshot tests (Playwright `webServer` config)

### 7.1 Playwright config addition

In `client/playwright.config.ts`, add:

```typescript
webServer: {
  command: 'npm run dev --prefix client',
  url: 'http://localhost:5173',
  reuseExistingServer: !process.env.CI,
}
```

---

## 8. What This WO Does NOT Do

- Does not implement legibility thresholds for text (deferred — requires OCR or UV reference markers, out of scope for this pass)
- Does not test drag physics (that gate is in WO-UI-PHYSICALITY-BASELINE-V1)
- Does not test WS event handling (existing gate infrastructure covers that)

---

## 9. Preflight

```bash
cd client && npm install pixelmatch pngjs
npm run test:playwright  # confirm screenshot tests pass
npm run test:vitest      # confirm ban scan passes
```

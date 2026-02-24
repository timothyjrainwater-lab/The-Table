# WO-UI-TOOLING-PLAYWRIGHT-001 — Playwright Headless Screenshot Harness

**Issued:** 2026-02-23
**Authority:** Agent visual feedback loop. Agents cannot see browser output. Playwright gives Anvil a self-contained vision loop: write code → headless browser renders it → agent reads screenshot via multimodal vision → patch → repeat. No human visual loop required.
**Gate:** TOOLS-PW (new gate). Target: 8 tests.
**Blocked by:** Nothing. Pure tooling addition — no conflict with any engine or UI WO.
**Track:** Tooling parallel track.

---

## 1. Target Lock

Agents currently have zero ability to verify visual output. Every geometry error requires Thunder to open a browser, take a screenshot, and send it manually. This WO installs Playwright and a screenshot harness so Anvil can:

1. Spin up the Vite dev server headlessly
2. Load `localhost:3000` in Chromium (full WebGL, real canvas textures)
3. Take screenshots at each camera posture
4. Save PNGs to `tests/screenshots/`
5. Read those PNGs using multimodal vision to self-verify geometry

This is the highest-leverage single tooling investment. Once live, all remaining UI WOs (spatial fix, Tier 1-3 objects) can be self-verified by Anvil without human visual loops.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Browser engine | Chromium (via Playwright) | Full WebGL 2 support. Free. Headless. Ships with Playwright. |
| 2 | Dev server management | Playwright `webServer` config — auto-starts `npm run dev`, waits for port 3000 | Standard Playwright pattern. No manual server management needed. |
| 3 | Screenshot output dir | `tests/screenshots/` (gitignored) | Keeps test artifacts out of source. |
| 4 | Camera postures captured | All 4: STANDARD (key 1), DOWN (key 2), LEAN_FORWARD (key 3), DICE_TRAY (key 4) | Full spatial coverage of every scene zone. |
| 5 | WS bridge mock | Suppress WebSocket connection errors — the test page loads without a backend | `page.on('console', ...)` suppresses WS disconnect noise. Scene renders without WS. |
| 6 | Wait strategy | Wait for `canvas` element to be present AND a 1-second settle delay | Three.js renders async. 1s covers texture generation and first frame. |
| 7 | Test runner integration | `@playwright/test` package — separate from pytest, runs via `npx playwright test` | Client-side tooling stays in `client/`. Python tests unaffected. |
| 8 | Config file location | `client/playwright.config.ts` | Collocated with the Vite app it tests. |

---

## 3. Contract Spec

### 3.1 Install

```bash
cd client
npm install -D @playwright/test
npx playwright install chromium
```

Add to `client/package.json` scripts:
```json
"test:visual": "playwright test"
```

### 3.2 `client/playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/visual',
  outputDir: './tests/screenshots',
  timeout: 30_000,
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'on',
    video: 'off',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: true,
    timeout: 15_000,
  },
});
```

### 3.3 `client/tests/visual/scene-postures.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOT_DIR = path.join(__dirname, '../screenshots');

test.beforeAll(() => {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
});

// Suppress WebSocket noise — backend not running during visual tests
test.beforeEach(async ({ page }) => {
  page.on('console', (msg) => {
    if (msg.type() === 'error' && msg.text().includes('WebSocket')) return;
  });
});

async function loadScene(page: any): Promise<void> {
  await page.goto('/');
  // Wait for Three.js canvas to exist
  await page.waitForSelector('canvas', { timeout: 10_000 });
  // Settle: allow texture generation + first render frame
  await page.waitForTimeout(1_500);
}

async function setPosture(page: any, key: string, name: string): Promise<void> {
  await page.keyboard.press(key);
  await page.waitForTimeout(800); // camera lerp settle
  const shot = await page.screenshot({ path: `${SCREENSHOT_DIR}/posture_${name}.png` });
  expect(shot).toBeTruthy();
}

test('PW-01: page loads without crash', async ({ page }) => {
  await loadScene(page);
  const canvas = await page.$('canvas');
  expect(canvas).not.toBeNull();
});

test('PW-02: canvas has non-zero dimensions', async ({ page }) => {
  await loadScene(page);
  const dims = await page.$eval('canvas', (c: HTMLCanvasElement) => ({
    w: c.width, h: c.height,
  }));
  expect(dims.w).toBeGreaterThan(0);
  expect(dims.h).toBeGreaterThan(0);
});

test('PW-03: STANDARD posture screenshot', async ({ page }) => {
  await loadScene(page);
  await setPosture(page, '1', 'STANDARD');
});

test('PW-04: DOWN posture screenshot', async ({ page }) => {
  await loadScene(page);
  await setPosture(page, '2', 'DOWN');
});

test('PW-05: LEAN_FORWARD posture screenshot', async ({ page }) => {
  await loadScene(page);
  await setPosture(page, '3', 'LEAN_FORWARD');
});

test('PW-06: DICE_TRAY posture screenshot', async ({ page }) => {
  await loadScene(page);
  await setPosture(page, '4', 'DICE_TRAY');
});

test('PW-07: HUD elements present', async ({ page }) => {
  await loadScene(page);
  const hud = await page.$('#hud');
  expect(hud).not.toBeNull();
  const hudText = await hud!.textContent();
  expect(hudText).toContain('Posture');
});

test('PW-08: no JS errors on load', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (err) => {
    // Ignore WS connection errors — backend not running
    if (!err.message.includes('WebSocket')) {
      errors.push(err.message);
    }
  });
  await loadScene(page);
  expect(errors).toHaveLength(0);
});
```

### 3.4 `.gitignore` additions

Add to root `.gitignore`:
```
client/tests/screenshots/
client/node_modules/.playwright/
```

---

## 4. Test Spec (Gate TOOLS-PW — 8 tests)

| ID | Test | Assertion |
|----|------|-----------|
| PW-01 | Page loads without crash | `<canvas>` element present in DOM |
| PW-02 | Canvas has non-zero dimensions | width > 0, height > 0 |
| PW-03 | STANDARD posture screenshot saved | File written, buffer non-null |
| PW-04 | DOWN posture screenshot saved | File written, buffer non-null |
| PW-05 | LEAN_FORWARD posture screenshot saved | File written, buffer non-null |
| PW-06 | DICE_TRAY posture screenshot saved | File written, buffer non-null |
| PW-07 | HUD elements present | `#hud` contains "Posture" text |
| PW-08 | No JS errors on load | Zero pageerror events (excluding WS) |

---

## 5. Implementation Plan

1. **Run** `cd client && npm install -D @playwright/test && npx playwright install chromium`
2. **Write** `client/playwright.config.ts` (§3.2)
3. **Create** `client/tests/visual/` directory
4. **Write** `client/tests/visual/scene-postures.spec.ts` (§3.3)
5. **Edit** `client/package.json` — add `"test:visual": "playwright test"` to scripts
6. **Edit** `.gitignore` — add screenshot dir and playwright cache
7. **Run** `cd client && npm run test:visual` — all 8 PASS, 4 PNG files written to `tests/screenshots/`
8. **Read** the 4 PNG files using vision — report what each posture shows

---

## 6. Deliverables Checklist

- [ ] `@playwright/test` installed in `client/devDependencies`
- [ ] Chromium browser binary installed (`npx playwright install chromium`)
- [ ] `client/playwright.config.ts` — webServer auto-starts Vite on port 3000
- [ ] `client/tests/visual/scene-postures.spec.ts` — 8 tests
- [ ] `client/package.json` — `test:visual` script added
- [ ] `.gitignore` — screenshot dir excluded
- [ ] Gate TOOLS-PW: 8/8 PASS
- [ ] 4 PNG screenshots written to `client/tests/screenshots/`
- [ ] Anvil reads all 4 screenshots and reports geometry observations

## 7. Integration Seams

- **Files added:** `client/playwright.config.ts`, `client/tests/visual/scene-postures.spec.ts`
- **Files modified:** `client/package.json`, `.gitignore`
- **Do not modify:** Any `src/` TypeScript files — tooling only
- **Do not modify:** Python test suite — this is a separate test runner

## 8. Preflight

```bash
cd client && npm run test:visual
```

Expected: 8 passed, 4 PNG files in `client/tests/screenshots/`.

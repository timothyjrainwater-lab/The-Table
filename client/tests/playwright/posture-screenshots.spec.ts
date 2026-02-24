/**
 * WO-UI-TOOLING-PLAYWRIGHT-001 — 4-posture screenshot harness.
 *
 * Captures one screenshot per camera posture (STANDARD, DOWN, LEAN_FORWARD,
 * DICE_TRAY). Saved as PNG files in tests/playwright-screenshots/.
 *
 * Gate: 4 PNGs saved, each > 0 bytes.
 */

import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOT_DIR = path.join(__dirname, '..', 'playwright-screenshots');

const POSTURES: Array<{ key: string; name: string }> = [
  { key: '1', name: 'STANDARD' },
  { key: '2', name: 'DOWN' },
  { key: '3', name: 'LEAN_FORWARD' },
  { key: '4', name: 'DICE_TRAY' },
];

/** Wait for the Three.js canvas to be present and for the scene to have rendered. */
async function waitForCanvas(page: Page): Promise<void> {
  await page.waitForSelector('canvas', { timeout: 15_000 });
  // Allow Vite HMR + Three.js init + first RAF to complete
  await page.waitForTimeout(2000);
}

/** Press a key to switch camera posture, then wait for the lerp to settle. */
async function switchPosture(page: Page, key: string): Promise<void> {
  await page.keyboard.press(key);
  // Camera lerp speed = 3.0 → full transit ~0.5 s at dt=0.016; 800 ms is safe
  await page.waitForTimeout(800);
}

test.beforeAll(() => {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
});

test('4-posture screenshot harness — all 4 PNGs saved', async ({ page }) => {
  await page.goto('/');
  await waitForCanvas(page);

  for (const posture of POSTURES) {
    await switchPosture(page, posture.key);

    const outPath = path.join(SCREENSHOT_DIR, `posture_${posture.name}.png`);
    const buffer = await page.screenshot({ path: outPath, fullPage: false });

    // Gate: file was written and is non-empty
    expect(buffer.byteLength).toBeGreaterThan(0);
    const stat = fs.statSync(outPath);
    expect(stat.size).toBeGreaterThan(0);

    console.log(`  [SAVED] ${outPath} (${stat.size} bytes)`);
  }
});

// Individual posture tests — useful for targeted re-runs
for (const posture of POSTURES) {
  test(`screenshot: posture ${posture.name}`, async ({ page }) => {
    await page.goto('/');
    await waitForCanvas(page);
    await switchPosture(page, posture.key);

    const outPath = path.join(SCREENSHOT_DIR, `posture_${posture.name}.png`);
    const buffer = await page.screenshot({ path: outPath, fullPage: false });
    expect(buffer.byteLength).toBeGreaterThan(0);
  });
}

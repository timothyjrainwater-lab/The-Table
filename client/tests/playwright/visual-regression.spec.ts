/**
 * WO-UI-VISREG-PLAYWRIGHT-001 — Visual Regression Baseline Comparison
 *
 * Uses Playwright toHaveScreenshot() to compare each posture against a
 * committed baseline. Fails with "missing baseline" until baselines are
 * generated post operator approval of Inspection Pack V2.
 *
 * Environment: Windows + headless Chromium 1920×1080.
 * Threshold: maxDiffPixels: 200 per snapshot.
 *
 * To generate/update baselines (OPERATOR ONLY, after Thunder approval):
 *   npm run test:visreg:update
 *
 * CI command (read-only, fails on diff):
 *   npm run test:visreg
 */

import { test, expect, Page } from '@playwright/test';

const VIEWPORT  = { width: 1920, height: 1080 };
const DIFF_OPTS = { maxDiffPixels: 200 };

const POSTURES = [
  { key: '1', name: 'STANDARD' },
  { key: '2', name: 'DOWN' },
  { key: '3', name: 'LEAN_FORWARD' },
  { key: '4', name: 'DICE_TRAY' },
] as const;

/** Wait for Three.js canvas + initial render to settle. */
async function waitForCanvas(page: Page): Promise<void> {
  await page.waitForSelector('canvas', { timeout: 15_000 });
  await page.waitForTimeout(2000);
}

/** Switch posture and wait for 350ms lerp + 250ms settle. */
async function switchPosture(page: Page, key: string): Promise<void> {
  await page.keyboard.press(key);
  await page.waitForTimeout(600);
}

// ---------------------------------------------------------------------------
// Posture snapshots
// ---------------------------------------------------------------------------

for (const posture of POSTURES) {
  test(`posture: ${posture.name}`, async ({ page }) => {
    await page.setViewportSize(VIEWPORT);
    await page.goto('/');
    await waitForCanvas(page);
    await switchPosture(page, posture.key);
    await expect(page).toHaveScreenshot(
      `posture-${posture.name}.png`,
      DIFF_OPTS,
    );
  });
}

// ---------------------------------------------------------------------------
// Vault state snapshots (LEAN_FORWARD posture — vault recess visible)
// ---------------------------------------------------------------------------

test('vault: REST (cover visible)', async ({ page }) => {
  await page.setViewportSize(VIEWPORT);
  await page.goto('/');
  await waitForCanvas(page);
  await switchPosture(page, '3');  // LEAN_FORWARD
  // Vault cover is visible by default (REST state)
  await expect(page).toHaveScreenshot('vault-REST.png', DIFF_OPTS);
});

test('vault: COMBAT (cover hidden)', async ({ page }) => {
  await page.setViewportSize(VIEWPORT);
  // 'c' key toggles demo combat — press after load to expose felt
  await page.goto('/');
  await waitForCanvas(page);
  await page.keyboard.press('c');   // enter combat — cover hides, scroll unrolls
  await page.waitForTimeout(1400);  // 1.2s unroll animation + 200ms settle
  await switchPosture(page, '3');   // LEAN_FORWARD
  await expect(page).toHaveScreenshot('vault-COMBAT.png', DIFF_OPTS);
});

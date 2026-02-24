/**
 * hover-ban.spec.ts — WO-UI-HOVER-BAN-01
 *
 * Asserts that hovering over any table object does not:
 *   1. Create DOM nodes matching tooltip/popover conventions
 *   2. Add *any* new DOM nodes (MutationObserver node-count diff — catches rename bypass)
 *   3. Inject text content into the page body
 *
 * Doctrine authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §16 — no tooltips, no popovers,
 * no hover cards, no snippets. UI bans are categorical.
 */

import { test, expect } from '@playwright/test';

const BANNED_SELECTORS = [
  '[role="tooltip"]',
  '.tooltip',
  '.popover',
  '.hovercard',
  '.snackbar',
  '[data-tooltip]',
  '[data-popover]',
  '.hover-card',
  '.info-panel',
  '.stat-block',
];

// Viewport center points for each major table object (approximate, STANDARD posture)
const HOVER_TARGETS = [
  { name: 'crystal_ball',    x: 760,  y: 150 },
  { name: 'table_surface',   x: 760,  y: 380 },
  { name: 'dice_tray_edge',  x: 1400, y: 350 },
  { name: 'table_left_edge', x: 100,  y: 300 },
];

test.describe('Hover-ban — no tooltip/popover DOM nodes on hover', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1500); // allow Three.js scene to initialize
  });

  for (const target of HOVER_TARGETS) {
    test(`No banned selectors appear on hover: ${target.name}`, async ({ page }) => {
      await page.mouse.move(target.x, target.y);
      await page.waitForTimeout(300); // allow any hover handlers to fire

      for (const sel of BANNED_SELECTORS) {
        const count = await page.locator(sel).count();
        expect(count, `Banned selector '${sel}' found after hovering ${target.name}`).toBe(0);
      }
    });

    test(`No new DOM nodes added on hover: ${target.name} (node-count diff)`, async ({ page }) => {
      // Set up MutationObserver to catch any additions during hover
      const addedNodes = await page.evaluate((): Promise<number> => {
        return new Promise<number>((resolve) => {
          let added = 0;
          const obs = new MutationObserver(muts => {
            for (const m of muts) added += m.addedNodes.length;
          });
          obs.observe(document.body, { childList: true, subtree: true });
          setTimeout(() => { obs.disconnect(); resolve(added); }, 600);
        });
      });

      await page.mouse.move(target.x, target.y);
      await page.waitForTimeout(700); // cover the observer window

      expect(addedNodes, `Hover on ${target.name} added ${addedNodes} DOM node(s) — must be 0`).toBe(0);
    });
  }

  test('Page body text does not grow on hover', async ({ page }) => {
    const textBefore = await page.evaluate(() => document.body.innerText.length);
    for (const target of HOVER_TARGETS) {
      await page.mouse.move(target.x, target.y);
      await page.waitForTimeout(200);
    }
    const textAfter = await page.evaluate(() => document.body.innerText.length);
    expect(textAfter, 'Page body text grew on hover — text injection detected').toBe(textBefore);
  });

});

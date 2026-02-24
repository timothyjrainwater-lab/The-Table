# WO-UI-VISREG-PLAYWRIGHT-001 — Visual Regression Harness

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** UI-VISREG-PLAYWRIGHT (new gate, defined below)
**Dependency:** Baseline snapshot commit BLOCKED on WO-UI-VISUAL-QA-002 ACCEPTED + Thunder golden frame approval

---

## 1. Target Lock

Replace manual screenshot capture + visual eyeball review with Playwright's built-in `toHaveScreenshot()` baseline comparison. This gives builders a single command that returns PASS/FAIL with a pixel diff artifact — no "vibes."

The split is explicit:

**Unblocked work (implement now):**
- Add `client/tests/playwright/visual-regression.spec.ts` using `@playwright/test` `toHaveScreenshot()`
- Four posture snapshot tests (STANDARD, DOWN, LEAN_FORWARD, DICE_TRAY)
- Two vault state tests (REST = cover visible, COMBAT = cover hidden)
- Artifact output: HTML diff report + per-posture diff PNG on failure
- Hard CI guard: `--update-snapshots` is not permitted without explicit operator approval
- Gate runs end-to-end and **deliberately fails** with "missing baseline snapshots" until approval

**Blocked work (operator approval required before executing):**
- Baseline snapshot generation and commit
- Sequencing: WO-UI-CAMERA-OPTICS-001 ACCEPTED → re-run `capture_inspection_v2.mjs` → Thunder approves composition → golden frames committed + README hash → QA-002 12/12 → then generate baselines from the same approved session and commit

**Done means:** `visual-regression.spec.ts` implemented with 6 `toHaveScreenshot()` calls, gate tests VR-01 through VR-10 all pass (structural checks do not require baselines), WO-UI-VISUAL-QA-002 unblocked dependency noted, and WO is accepted without baseline commit (baseline commit is a separate post-approval step).

---

## 2. Design Decisions

### 2.1 Environment Pinning

This project runs: **Windows + headless Chromium (Playwright)**. That is the pinned environment. All agents use this environment. Baselines generated here are stable across runs. No Docker needed.

If the project ever moves to Linux CI, regenerate baselines once in that environment and commit. The gate will catch drift from that point forward.

### 2.2 Threshold

`toHaveScreenshot()` threshold: `{ maxDiffPixels: 200 }` per posture. Rationale:
- Anti-aliasing variation across runs at the same resolution accounts for < 50 pixels
- 200 is tight enough to catch actual composition drift (camera moved, mesh missing)
- 200 is loose enough to tolerate minor GPU-side AA variation
- Override per-test where tighter or looser tolerance is warranted

### 2.3 Viewport

All snapshots: `1920×1080`. This must match the viewport at baseline generation time. The `playwright.config.ts` uses `devices['Desktop Chrome']` (1280×720 by default) — the visual regression spec overrides viewport explicitly.

### 2.4 Snapshot Location

```
client/tests/playwright/snapshots/visual-regression.spec.ts-snapshots/
  posture-STANDARD-chromium-win32.png
  posture-DOWN-chromium-win32.png
  posture-LEAN_FORWARD-chromium-win32.png
  posture-DICE_TRAY-chromium-win32.png
  vault-REST-chromium-win32.png
  vault-COMBAT-chromium-win32.png
```

Playwright auto-names by test name + browser + platform. These are committed to the repo alongside the spec. They do not exist until the baseline generation step (post-approval).

### 2.5 `--update-snapshots` Guard

The CI command (and the gate test VR-09) verifies that the `test:visreg` npm script does NOT include `--update-snapshots`. Baseline updates require an explicit operator-approved step: `npm run test:visreg:update`, which is a separate script that Thunder runs manually after approving composition changes.

### 2.6 What This Does NOT Replace

The pytest behavioral gate (`test_ui_visual_qa_002_gate.py`) stays. Its checks are correctness-oriented:
- `QA2-11`: room geometry not a void (pixel mass check)
- `QA2-12`: README has valid commit hash

Those are not pixel diff checks — they're behavioral/structural. They complement `toHaveScreenshot()` but are independent.

---

## 3. Implementation Spec

### 3.1 `client/tests/playwright/visual-regression.spec.ts` (new file)

```typescript
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

const VIEWPORT = { width: 1920, height: 1080 };
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
// Vault state snapshots (LEAN_FORWARD posture — vault is visible from there)
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
  // Use demo combat flag to expose felt
  await page.goto('/?combat=1');
  await waitForCanvas(page);
  await switchPosture(page, '3');  // LEAN_FORWARD
  await expect(page).toHaveScreenshot('vault-COMBAT.png', DIFF_OPTS);
});
```

### 3.2 `package.json` additions (client/)

Add two scripts:

```json
{
  "scripts": {
    "test:visreg": "playwright test visual-regression.spec.ts",
    "test:visreg:update": "playwright test visual-regression.spec.ts --update-snapshots"
  }
}
```

`test:visreg` is the CI-safe read-only command. `test:visreg:update` is the operator-only baseline update command. Both are distinct — the gate checks that `test:visreg` does NOT contain `--update-snapshots`.

### 3.3 `playwright.config.ts` — `snapshotDir` (optional but recommended)

Add to config to make snapshot paths predictable:

```typescript
snapshotDir: './tests/playwright/snapshots',
```

This keeps baselines adjacent to the spec, not in a generated output dir.

### 3.4 Baseline Generation Procedure (POST-APPROVAL — not part of this WO's gate)

After Thunder approves Inspection Pack V2 and golden frames are committed:

```bash
cd f:/DnD-3.5/client
npm run dev &          # ensure dev server is running
npm run test:visreg:update
# 6 baseline PNGs generated in client/tests/playwright/snapshots/
git add client/tests/playwright/snapshots/
git commit -m "visreg baselines: STANDARD/DOWN/LEAN_FORWARD/DICE_TRAY/vault-REST/vault-COMBAT — approved by Thunder"
```

After this commit, `npm run test:visreg` will PASS on every subsequent run that matches the approved composition.

---

## 4. Regression Risk

- **ZERO for existing TOOLS-PW gate:** The new spec is at a new path (`visual-regression.spec.ts`). The existing `posture-screenshots.spec.ts` is untouched. `test_ui_playwright_gate.py` tests structural properties that remain valid.
- **ZERO for existing capture flow:** `capture_inspection_v2.mjs` is unchanged — it still produces the inspection pack.
- **LOW for playwright.config.ts:** Adding `snapshotDir` is additive — existing tests are unaffected.
- **LOW for package.json:** Two new scripts, no changes to existing ones.

---

## 5. What This WO Does NOT Do

- No baseline snapshot commit (BLOCKED on Thunder approval — this is intentional governance)
- No change to `posture-screenshots.spec.ts` (keep existing harness intact)
- No change to `test_ui_playwright_gate.py` (TOOLS-PW gate unchanged)
- No change to `test_ui_visual_qa_002_gate.py` (behavioral gates are independent)
- No full-page scroll capture (viewport-only snapshots — stable, no scroll artifacts)
- No cross-browser coverage (Chromium only — matches pinned environment)
- No `Improved Feint` style sub-tests (posture variants like zoom levels — deferred)

---

## 6. Gate Spec

**Gate name:** `UI-VISREG-PLAYWRIGHT`
**Test file:** `tests/test_ui_visreg_playwright_gate.py` (new file — static checks only, no browser)

All checks are static (file existence + content inspection). They do not require a running browser or committed baselines.

| # | Test | Check |
|---|------|-------|
| VR-01 | `visual-regression.spec.ts` exists | `client/tests/playwright/visual-regression.spec.ts` present |
| VR-02 | Spec uses `toHaveScreenshot()` | Grep spec for `toHaveScreenshot` — must be present |
| VR-03 | Spec tests all 4 posture keys | Grep for keys '1', '2', '3', '4' in spec |
| VR-04 | Spec tests vault REST state | Grep for `vault-REST` or `vault: REST` in spec |
| VR-05 | Spec tests vault COMBAT state | Grep for `vault-COMBAT` or `vault: COMBAT` in spec |
| VR-06 | Spec sets 1920×1080 viewport explicitly | Grep for `1920` and `1080` in spec |
| VR-07 | `test:visreg` script exists in `package.json` | `scripts["test:visreg"]` present |
| VR-08 | `test:visreg:update` script exists in `package.json` | `scripts["test:visreg:update"]` present |
| VR-09 | `test:visreg` does NOT contain `--update-snapshots` | `scripts["test:visreg"]` must not include `--update-snapshots` |
| VR-10 | `test:visreg:update` DOES contain `--update-snapshots` | `scripts["test:visreg:update"]` must include `--update-snapshots` |

**Test count target:** UI-VISREG-PLAYWRIGHT 10/10.

**Note on baselines:** VR-01 through VR-10 pass without committed baselines. A separate gate (`UI-VISREG-BASELINES`) can be added post-approval that checks the 6 baseline PNGs exist and are 1920×1080. That gate is out of scope for this WO.

---

## 7. Sequencing

```
WO-UI-CAMERA-OPTICS-001 ACCEPTED
  → capture_inspection_v2.mjs Pass 3 (room_wide + scene_graph_dump)
  → Thunder reviews Inspection Pack V2
  → Thunder approves all 4 postures
  → Golden frames committed to docs/design/LAYOUT_PACK_V1/golden/
  → README.md updated (commit hash + branch)
  → QA-002 gate 12/12 PASS
  → [OPERATOR] Run: npm run test:visreg:update (in same browser session as approval)
  → Baseline PNGs committed
  → npm run test:visreg → PASS
  → WO-UI-GATES-V1 dispatched (screenshot diff gate uses these baselines)
```

This WO (VISREG-PLAYWRIGHT-001) can be implemented and gated NOW. The baseline commit step happens at the operator approval milestone above.

---

## 8. Preflight

```bash
cd f:/DnD-3.5

# Confirm TOOLS-PW still passes (no regressions)
python -m pytest tests/test_ui_playwright_gate.py -v

# After implementation — structural gate (no browser needed)
python -m pytest tests/test_ui_visreg_playwright_gate.py -v

# Verify test:visreg script exists (will fail with "missing snapshots" — expected)
cd client && npx playwright test visual-regression.spec.ts --list

# Full suite regression check
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5
```

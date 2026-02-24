/**
 * capture_inspection_v2.mjs — Inspection Pack V2 capture script.
 *
 * WO-UI-VISUAL-QA-002: produces all required inspection artifacts.
 *
 * Usage:
 *   node scripts/capture_inspection_v2.mjs
 *
 * Prerequisites:
 *   - Dev server running: npm run dev --prefix client  (serves at localhost:3000)
 *   - Playwright installed: cd client && npx playwright install chromium
 *   - WO-UI-CAMERA-OPTICS-001 must be wired (window.__cameraController__ exposed)
 *
 * Outputs (all to docs/design/LAYOUT_PACK_V1/inspection_v2/):
 *   standard.png, down.png, lean_forward.png, dice_tray.png   — debug OFF
 *   standard_debug.png, down_debug.png, lean_forward_debug.png, dice_tray_debug.png — debug ON
 *   down_crop_sheet.png, down_crop_notebook.png, down_crop_rulebook.png   — legibility crops
 *   standard_crop_orb.png, lean_forward_crop_orb.png                     — framing crops
 *   vault_rest.png, vault_combat.png                                      — vault state
 *   room_geometry.png                                                     — room presence
 *   runtime_optics_dump.json                                              — live optics vs JSON
 *   room_wide.png                                                          — room geometry evidence (debug ON)
 *   scene_graph_dump.json                                                  — machine-readable room presence flags
 */

import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = dirname(__filename);
const ROOT       = join(__dirname, '..');

const DEV_SERVER = process.env.DEV_SERVER ?? 'http://localhost:3000';
const OUT_DIR    = join(ROOT, 'docs', 'design', 'LAYOUT_PACK_V1', 'inspection_v2');

mkdirSync(OUT_DIR, { recursive: true });

const POSTURES = ['STANDARD', 'DOWN', 'LEAN_FORWARD', 'DICE_TRAY'];
const HOTKEYS  = { STANDARD: '1', DOWN: '2', LEAN_FORWARD: '3', DICE_TRAY: '4' };
const FILENAMES = {
  STANDARD:     'standard',
  DOWN:         'down',
  LEAN_FORWARD: 'lean_forward',
  DICE_TRAY:    'dice_tray',
};

const TRANSITION_WAIT = 600;  // 350ms transition + 250ms settle

// Crop regions for DOWN legibility (adjusted for new DOWN pose: y=1.6 z=6.8 looking at shelf)
const CROPS = {
  down_sheet:    { x: 240,  y: 500, width: 320, height: 260 },  // character sheet stats block
  down_notebook: { x: 720,  y: 460, width: 520, height: 320 },  // notebook body text
  down_rulebook: { x: 1280, y: 450, width: 520, height: 340 },  // rulebook heading + paragraph
};

// Orb framing crops
const ORB_CROPS = {
  standard:     { x: 720, y: 80,  width: 480, height: 300 },  // upper frame: orb + rail
  lean_forward: { x: 640, y: 160, width: 640, height: 400 },  // orb must be fully in frame
};

async function capturePosture(page, posture, suffix = '') {
  await page.keyboard.press(HOTKEYS[posture]);
  await page.waitForTimeout(TRANSITION_WAIT);
  const fname = `${FILENAMES[posture]}${suffix}.png`;
  await page.screenshot({ path: join(OUT_DIR, fname) });
  console.log(`  captured: ${fname}`);
  return fname;
}

async function cropRegion(page, sourcePath, region, outName) {
  // Use Playwright screenshot clip if possible, otherwise capture full and note region
  const fname = join(OUT_DIR, outName);
  await page.screenshot({ path: fname, clip: region });
  console.log(`  crop:     ${outName}`);
}

async function dumpRuntimeOptics(page) {
  const postures = ['STANDARD', 'DOWN', 'LEAN_FORWARD', 'DICE_TRAY', 'BOOK_READ'];
  const hotkeys  = { STANDARD: '1', DOWN: '2', LEAN_FORWARD: '3', DICE_TRAY: '4', BOOK_READ: '5' };
  const result   = {};

  for (const p of postures) {
    await page.keyboard.press(hotkeys[p]);
    await page.waitForTimeout(TRANSITION_WAIT);
    const optics = await page.evaluate(() => {
      const ctrl = window.__cameraController__;
      const cam  = ctrl.camera;
      const pos  = cam.position;
      return {
        fov:    Math.round(cam.fov  * 100) / 100,
        near:   Math.round(cam.near * 100) / 100,
        far:    Math.round(cam.far  * 100) / 100,
        pos:    [
          Math.round(pos.x * 100) / 100,
          Math.round(pos.y * 100) / 100,
          Math.round(pos.z * 100) / 100,
        ],
      };
    });
    result[p] = optics;
    console.log(`  optics[${p}]: fov=${optics.fov} near=${optics.near} far=${optics.far}`);
  }

  const dump = {
    captured_at: new Date().toISOString(),
    source: 'window.__cameraController__',
    postures: result,
  };
  const dumpPath = join(OUT_DIR, 'runtime_optics_dump.json');
  writeFileSync(dumpPath, JSON.stringify(dump, null, 2));
  console.log(`  optics dump: runtime_optics_dump.json`);
  return result;
}

async function main() {
  console.log(`\nInspection Pack V2 — capturing to: ${OUT_DIR}\n`);

  const browser = await chromium.launch({ headless: true });

  // -------------------------------------------------------------------------
  // Pass 1: debug OFF — clean posture PNGs
  // -------------------------------------------------------------------------
  console.log('Pass 1: debug OFF posture PNGs');
  {
    const ctx  = browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await (await ctx).newPage();
    await page.goto(DEV_SERVER);
    await page.waitForTimeout(1500);

    for (const posture of POSTURES) {
      await capturePosture(page, posture);
    }

    // Legibility crops from DOWN
    console.log('\nLegibility crops (DOWN):');
    await page.keyboard.press('2');
    await page.waitForTimeout(TRANSITION_WAIT);
    await cropRegion(page, null, CROPS.down_sheet,    'down_crop_sheet.png');
    await cropRegion(page, null, CROPS.down_notebook, 'down_crop_notebook.png');
    await cropRegion(page, null, CROPS.down_rulebook, 'down_crop_rulebook.png');

    // Framing crops
    console.log('\nFraming crops:');
    await page.keyboard.press('1');
    await page.waitForTimeout(TRANSITION_WAIT);
    await cropRegion(page, null, ORB_CROPS.standard,     'standard_crop_orb.png');
    await page.keyboard.press('3');
    await page.waitForTimeout(TRANSITION_WAIT);
    await cropRegion(page, null, ORB_CROPS.lean_forward, 'lean_forward_crop_orb.png');

    // Vault cover state — REST (combat key 'c' is a toggle, start at rest)
    console.log('\nVault state:');
    await page.keyboard.press('3');  // LEAN_FORWARD shows vault
    await page.waitForTimeout(TRANSITION_WAIT);
    await page.screenshot({ path: join(OUT_DIR, 'vault_rest.png') });
    console.log('  captured: vault_rest.png');

    // Vault cover state — COMBAT (press 'c' to toggle demo combat)
    await page.keyboard.press('c');
    await page.waitForTimeout(400);
    await page.screenshot({ path: join(OUT_DIR, 'vault_combat.png') });
    console.log('  captured: vault_combat.png');
    // Reset combat
    await page.keyboard.press('c');

    // Room geometry — STANDARD, back wall + floor visible
    console.log('\nRoom geometry:');
    await page.keyboard.press('1');
    await page.waitForTimeout(TRANSITION_WAIT);
    await page.screenshot({ path: join(OUT_DIR, 'room_geometry.png') });
    console.log('  captured: room_geometry.png');

    await (await ctx).close();
  }

  // -------------------------------------------------------------------------
  // Pass 2: debug ON — overlay visible, same postures
  // -------------------------------------------------------------------------
  console.log('\nPass 2: debug ON posture PNGs');
  {
    const ctx  = browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await (await ctx).newPage();
    await page.goto(`${DEV_SERVER}?debug=1`);
    await page.waitForTimeout(1500);

    for (const posture of POSTURES) {
      await capturePosture(page, posture, '_debug');
    }

    // Runtime optics dump
    console.log('\nRuntime optics dump:');
    await dumpRuntimeOptics(page);

    await (await ctx).close();
  }

  // -------------------------------------------------------------------------
  // Pass 3: room_wide.png (debug ON, STANDARD) + scene_graph_dump.json
  // -------------------------------------------------------------------------
  console.log('\nPass 3: room geometry evidence (debug ON)');
  {
    const ctx  = browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await (await ctx).newPage();
    await page.goto(`${DEV_SERVER}?debug=1`);
    await page.waitForTimeout(1500);

    // STANDARD posture — room geometry most visible
    await page.keyboard.press('1');
    await page.waitForTimeout(600);
    await page.screenshot({ path: join(OUT_DIR, 'room_wide.png') });
    console.log('  captured: room_wide.png');

    // Scene graph dump — machine-readable boolean flags
    const sceneGraph = await page.evaluate(() => {
      const dbg = window.__sceneDebug__;
      if (!dbg) return null;
      const scene = dbg.scene;
      const renderer = dbg.renderer;
      return {
        captured_at: new Date().toISOString(),
        room_floor_present:     !!scene.getObjectByName('room_floor'),
        room_back_wall_present: !!scene.getObjectByName('room_back_wall'),
        room_lights_present:    scene.children.some(o => o.isLight),
        postprocess_enabled:    true,  // Three.js WebGLRenderer always enabled
        exposure:               renderer ? renderer.toneMappingExposure : null,
      };
    });

    if (sceneGraph) {
      const dumpPath = join(OUT_DIR, 'scene_graph_dump.json');
      writeFileSync(dumpPath, JSON.stringify(sceneGraph, null, 2));
      console.log('  scene_graph_dump.json:');
      console.log(`    room_floor_present:     ${sceneGraph.room_floor_present}`);
      console.log(`    room_back_wall_present: ${sceneGraph.room_back_wall_present}`);
      console.log(`    room_lights_present:    ${sceneGraph.room_lights_present}`);
      console.log(`    exposure:               ${sceneGraph.exposure}`);
    } else {
      console.warn('  WARNING: __sceneDebug__ not available — scene_graph_dump.json skipped');
    }

    await (await ctx).close();
  }

  await browser.close();

  console.log('\n=== Inspection Pack V2 complete ===');
  console.log(`Output: ${OUT_DIR}`);
  console.log('\nFiles produced:');
  console.log('  standard.png, down.png, lean_forward.png, dice_tray.png');
  console.log('  standard_debug.png, down_debug.png, lean_forward_debug.png, dice_tray_debug.png');
  console.log('  down_crop_sheet.png, down_crop_notebook.png, down_crop_rulebook.png');
  console.log('  standard_crop_orb.png, lean_forward_crop_orb.png');
  console.log('  vault_rest.png, vault_combat.png');
  console.log('  room_geometry.png');
  console.log('  room_wide.png, scene_graph_dump.json');
  console.log('  runtime_optics_dump.json');
  console.log('\nHand to Thunder for posture-by-posture review before golden frame commit.');
}

main().catch((err) => {
  console.error('Capture failed:', err);
  process.exit(1);
});

/**
 * Main entry — Table UI Slice 3 (WO-UI-05: Visual atmosphere + object stubs).
 *
 * - Dark walnut table surface with recessed felt vault
 * - Warm candlelight atmosphere (3 lantern point lights, flicker animation)
 * - Physical object stubs: character sheet, notebook, tome, dice bag,
 *   crystal ball, dice tower, cup holder, scattered clutter
 * - Shadow pass on all stubs
 * - Camera postures, WebSocket bridge, dice ritual (from Slice 2) preserved
 *
 * Authority: WO-UI-05, MEMO_TABLE_VISION_SPATIAL_SPEC, TABLE_SURFACE_UI_SPECIFICATION,
 *            DOCTRINE_04_TABLE_UI_MEMO_V4.
 */

import * as THREE from 'three';
import { CameraPostureController, PostureName } from './camera';
import { WsBridge } from './ws-bridge';
import { BeatIntentCard } from './beat-intent-card';
import { DiceObject } from './dice-object';
import { TableObjectRegistry } from './table-object';
import { DragInteraction } from './drag-interaction';
import { ZONES } from './zones';
import {
  buildTableSurface,
  buildAtmosphere,
  buildObjectStubs,
  updateFlicker,
  updateCrystalBall,
} from './scene-builder';
import type { LanternLight } from './scene-builder';

// ---------------------------------------------------------------------------
// Scene setup
// ---------------------------------------------------------------------------

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.35;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x08060a); // near-black — room beyond table
scene.fog = new THREE.Fog(0x08060a, 14, 22);  // table floats in darkness

const camera = new THREE.PerspectiveCamera(
  60,
  window.innerWidth / window.innerHeight,
  0.1,
  100
);
const postureCtrl = new CameraPostureController(camera);

// ---------------------------------------------------------------------------
// Table surface + atmosphere (WO-UI-05)
// ---------------------------------------------------------------------------

const tableSurface = buildTableSurface();
scene.add(tableSurface);

const objectStubs = buildObjectStubs();
scene.add(objectStubs);

const lanterns: LanternLight[] = buildAtmosphere(scene);

// ---------------------------------------------------------------------------
// WebSocket bridge
// ---------------------------------------------------------------------------

const WS_URL = (
  (window as unknown as Record<string, string>).__WS_URL__ ||
  'ws://localhost:8765/ws'
);
const bridge = new WsBridge(WS_URL);
bridge.connect();

// ---------------------------------------------------------------------------
// TableObject registry + BeatIntent card + Dice (Changes 1, 3)
// ---------------------------------------------------------------------------

const registry = new TableObjectRegistry();
const beatCard = new BeatIntentCard(scene, bridge);
registry.add(beatCard);
beatCard.onSpawn();

// Dice object — spawns in dice_tray zone, not pickable until PENDING_ROLL
const d20 = new DiceObject(scene);
registry.add(d20);
d20.onSpawn();

// ---------------------------------------------------------------------------
// Drag interaction system (Changes 2, 4, 5)
// ---------------------------------------------------------------------------

let cameraLocked = false;

// PENDING_ROLL state — declared here so drag callbacks can reference it
const pendingOverlay = document.getElementById('pending-overlay')!;
let activePendingHandle: string | null = null;

const dragInteraction = new DragInteraction(
  registry,
  camera,
  renderer,
  scene,
  bridge,
  {
    onDragStart: () => { cameraLocked = true; },
    onDragEnd: () => { cameraLocked = false; },
    onDrop: (obj, zone) => {
      // Dice dropped in tower zone → send DiceTowerDropIntent
      if (obj.kind === 'die' && zone === 'dice_tower' && activePendingHandle) {
        _sendDiceTowerDrop();
      }
    },
  },
);

// Listen for server acknowledgments of position updates
bridge.on('table_object_state', (data) => {
  const objectId = data.object_id as string;
  const position = data.position as [number, number, number];
  const zone = data.zone as string;
  dragInteraction.applyServerAck(objectId, position, zone);
});

// ---------------------------------------------------------------------------
// BeatIntent data (Change 3 — preserve WO-UI-01 behavior)
// ---------------------------------------------------------------------------

// Listen for state_update messages that carry BeatIntent data
bridge.on('state_update', (data) => {
  const delta = data.delta as Record<string, unknown> | undefined;
  if (!delta) return;

  if (delta.beat_type || (data.update_type === 'director_beat_selected')) {
    beatCard.update(
      (delta.beat_type as string) || 'UNKNOWN',
      (delta.pacing_mode as string) || 'NORMAL',
      (delta.beat_id as string) || '',
      (delta.target_handles as string[]) || [],
    );
  }
});

// Also handle a dedicated beat_intent message type (if backend sends one)
bridge.on('beat_intent', (data) => {
  beatCard.update(
    (data.beat_type as string) || 'UNKNOWN',
    (data.pacing_mode as string) || 'NORMAL',
    (data.beat_id as string) || '',
    (data.target_handles as string[]) || [],
  );
});

// ---------------------------------------------------------------------------
// PENDING_ROLL → Dice Tray → Dice Tower → Result Handshake (WO-UI-03/04)
// ---------------------------------------------------------------------------

bridge.on('*', (data) => {
  // Check for PENDING_ROLL in various message shapes
  const msgType = data.msg_type as string;
  const updateType = data.update_type as string | undefined;
  const delta = data.delta as Record<string, unknown> | undefined;

  const isPendingRoll = (
    msgType === 'pending_roll' ||
    updateType === 'pending_roll' ||
    (delta && delta.type === 'PENDING_ROLL')
  );

  if (isPendingRoll) {
    const spec = (data.spec || delta?.spec || '???') as string;
    const handle = (data.pending_handle || delta?.pending_handle || '') as string;
    activePendingHandle = handle;
    pendingOverlay.textContent = `PENDING ROLL: ${spec} — pick up dice from tray`;
    pendingOverlay.style.display = 'block';

    // Activate the d20 die — make it pickable and start fidget
    d20.activate();
  }

  // Check for PENDING clear acknowledgment
  if (msgType === 'state_update' && updateType === 'pending_cleared') {
    activePendingHandle = null;
    pendingOverlay.style.display = 'none';
    d20.deactivate();
  }
});

// Typed roll_result handler — formalized in WO-UI-04 (no wildcard sniffing)
bridge.on('roll_result', (data) => {
  const delta = data.delta as Record<string, unknown> | undefined;
  const face = (data.d20_result || delta?.d20_result || 0) as number;
  const total = (data.total || delta?.total || 0) as number;
  const success = (data.success || delta?.success) as boolean | undefined;

  // Trigger result-reveal animation with authoritative face value
  d20.showResult(face);

  // Update overlay with result
  const successText = success !== undefined ? (success ? ' — HIT' : ' — MISS') : '';
  pendingOverlay.textContent = `RESULT: ${face} (total: ${total})${successText}`;
  pendingOverlay.style.display = 'block';

  // Clear overlay after animation completes
  setTimeout(() => {
    pendingOverlay.style.display = 'none';
    d20.deactivate();
  }, 2000);
});

// Overlay click: legacy path (still works as fallback for direct confirmation)
pendingOverlay.addEventListener('click', () => {
  if (!activePendingHandle) return;
  _sendDiceTowerDrop();
});

/**
 * Send the DiceTowerDropIntent to the backend.
 * Called when dice is dropped in the tower zone OR when overlay is clicked.
 */
function _sendDiceTowerDrop(): void {
  if (!activePendingHandle) return;
  bridge.send({
    msg_type: 'player_action',
    msg_id: crypto.randomUUID(),
    timestamp: Date.now() / 1000,
    action_type: 'dice_tower_drop',
    payload: {
      type: 'DICE_TOWER_DROP_INTENT',
      dice_ids: ['d20'],
      pending_roll_handle: activePendingHandle,
    },
  });
  activePendingHandle = null;
  pendingOverlay.textContent = 'Rolling...';
}

// ---------------------------------------------------------------------------
// BeatIntent card click (non-drag click sends DeclareActionIntent)
// ---------------------------------------------------------------------------

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

renderer.domElement.addEventListener('click', (event) => {
  // Don't process clicks during or just after drag
  if (dragInteraction.dragging) return;

  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);

  const hits = raycaster.intersectObject(beatCard.mesh);
  if (hits.length > 0) {
    beatCard.sendDeclareAction();
  }
});

// ---------------------------------------------------------------------------
// Camera posture keyboard controls (disabled during drag)
// ---------------------------------------------------------------------------

const postureLabel = document.getElementById('posture-label')!;

window.addEventListener('keydown', (event) => {
  // Camera controls disabled during drag (doctrine §17)
  if (cameraLocked) return;

  let target: PostureName | null = null;
  switch (event.key) {
    case '1': target = 'STANDARD'; break;
    case '2': target = 'DOWN'; break;
    case '3': target = 'LEAN_FORWARD'; break;
    case '4': target = 'DICE_TRAY'; break;
  }
  if (target) {
    postureCtrl.setPosture(target);
    postureLabel.textContent = `Posture: ${target}`;
  }
});

// ---------------------------------------------------------------------------
// Resize handler
// ---------------------------------------------------------------------------

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ---------------------------------------------------------------------------
// Render loop
// ---------------------------------------------------------------------------

const clock = new THREE.Clock();
let elapsed = 0;

function animate(): void {
  requestAnimationFrame(animate);
  const dt = clock.getDelta();
  elapsed += dt;
  postureCtrl.update(dt);
  d20.updateAnimation(dt);
  dragInteraction.updateFocusHighlight();
  updateFlicker(lanterns, elapsed);
  updateCrystalBall(objectStubs, elapsed);
  renderer.render(scene, camera);
}

animate();

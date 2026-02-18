/**
 * Main entry — Table UI Phase 3 (Slice 2).
 *
 * - Three.js scene with table surface and zone boundaries
 * - 3 camera postures (STANDARD, DOWN, LEAN_FORWARD) with smooth transitions
 * - WebSocket connection to backend
 * - PENDING round trip (PendingRoll -> DiceTowerDropIntent)
 * - BeatIntent card as first TableObject with pick/drag/drop
 * - Dice tray with fidget-ready d20 + dice tower drop target
 * - Result-reveal animation driven by Box authoritative outcome
 * - Zone constraint enforcement
 * - Keyboard-only path for pick/drag/drop
 *
 * Authority: WO-UI-01, WO-UI-02, WO-UI-03, DOCTRINE_04_TABLE_UI_MEMO_V4.
 */

import * as THREE from 'three';
import { CameraPostureController, PostureName } from './camera';
import { WsBridge } from './ws-bridge';
import { BeatIntentCard } from './beat-intent-card';
import { DiceObject } from './dice-object';
import { TableObjectRegistry } from './table-object';
import { DragInteraction } from './drag-interaction';
import { ZONES } from './zones';

// ---------------------------------------------------------------------------
// Scene setup
// ---------------------------------------------------------------------------

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);

const camera = new THREE.PerspectiveCamera(
  60,
  window.innerWidth / window.innerHeight,
  0.1,
  100
);
const postureCtrl = new CameraPostureController(camera);

// ---------------------------------------------------------------------------
// Lighting
// ---------------------------------------------------------------------------

const ambientLight = new THREE.AmbientLight(0x404060, 0.6);
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0xfff5e0, 0.8);
dirLight.position.set(5, 10, 5);
dirLight.castShadow = true;
scene.add(dirLight);

const pointLight = new THREE.PointLight(0xff8844, 0.4, 20);
pointLight.position.set(0, 3, 0);
scene.add(pointLight);

// ---------------------------------------------------------------------------
// Table surface + zone boundaries
// ---------------------------------------------------------------------------

// Main table surface
const tableGeo = new THREE.PlaneGeometry(12, 8);
const tableMat = new THREE.MeshStandardMaterial({
  color: 0x2d1b0e,
  roughness: 0.8,
  metalness: 0.1,
});
const tableMesh = new THREE.Mesh(tableGeo, tableMat);
tableMesh.rotation.x = -Math.PI / 2;
tableMesh.receiveShadow = true;
scene.add(tableMesh);

// Zone boundaries — wireframe rectangles marking table zones
// Uses zone definitions from zones.ts for consistency with backend
for (const z of ZONES) {
  const w = z.halfWidth * 2;
  const h = z.halfHeight * 2;

  const zoneGeo = new THREE.PlaneGeometry(w, h);
  const zoneMat = new THREE.MeshBasicMaterial({
    color: z.color,
    transparent: true,
    opacity: 0.15,
    side: THREE.DoubleSide,
  });
  const zoneMesh = new THREE.Mesh(zoneGeo, zoneMat);
  zoneMesh.rotation.x = -Math.PI / 2;
  zoneMesh.position.set(z.centerX, 0.01, z.centerZ);
  scene.add(zoneMesh);

  // Wireframe border
  const edges = new THREE.EdgesGeometry(zoneGeo);
  const lineMat = new THREE.LineBasicMaterial({ color: z.color, transparent: true, opacity: 0.5 });
  const wireframe = new THREE.LineSegments(edges, lineMat);
  wireframe.rotation.x = -Math.PI / 2;
  wireframe.position.set(z.centerX, 0.02, z.centerZ);
  scene.add(wireframe);
}

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
// PENDING_ROLL → Dice Tray → Dice Tower → Result Handshake (WO-UI-03)
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

  // Check for roll result from Box (authoritative outcome)
  const isRollResult = (
    msgType === 'roll_result' ||
    updateType === 'roll_result' ||
    (delta && delta.type === 'ROLL_RESULT')
  );

  if (isRollResult) {
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
  }
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

function animate(): void {
  requestAnimationFrame(animate);
  const dt = clock.getDelta();
  postureCtrl.update(dt);
  d20.updateAnimation(dt);
  dragInteraction.updateFocusHighlight();
  renderer.render(scene, camera);
}

animate();

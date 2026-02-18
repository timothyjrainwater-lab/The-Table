/**
 * Main entry — Table UI Phase 1 (Slice 0).
 *
 * - Three.js scene with table surface and zone boundaries
 * - 3 camera postures (STANDARD, DOWN, LEAN_FORWARD) with smooth transitions
 * - WebSocket connection to backend
 * - PENDING round trip (PendingRoll → DiceTowerDropIntent)
 * - BeatIntent display on table surface
 *
 * Authority: WO-UI-01, DOCTRINE_04_TABLE_UI_MEMO_V4.
 */

import * as THREE from 'three';
import { CameraPostureController, PostureName } from './camera';
import { WsBridge } from './ws-bridge';
import { BeatIntentCard } from './beat-intent-card';

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
function addZone(
  x: number, z: number,
  w: number, h: number,
  color: number, label: string
): void {
  const zoneGeo = new THREE.PlaneGeometry(w, h);
  const zoneMat = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.15,
    side: THREE.DoubleSide,
  });
  const zoneMesh = new THREE.Mesh(zoneGeo, zoneMat);
  zoneMesh.rotation.x = -Math.PI / 2;
  zoneMesh.position.set(x, 0.01, z);
  scene.add(zoneMesh);

  // Wireframe border
  const edges = new THREE.EdgesGeometry(zoneGeo);
  const lineMat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.5 });
  const wireframe = new THREE.LineSegments(edges, lineMat);
  wireframe.rotation.x = -Math.PI / 2;
  wireframe.position.set(x, 0.02, z);
  scene.add(wireframe);
}

// Map zone (center)
addZone(0, -0.5, 6, 4, 0x4488ff, 'map');
// Player zone (near edge)
addZone(0, 3, 10, 1.5, 0x44ff88, 'player');
// DM zone (far edge)
addZone(0, -3.5, 10, 1.5, 0xff4444, 'dm');

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
// BeatIntent card (Change 6)
// ---------------------------------------------------------------------------

const beatCard = new BeatIntentCard(scene, bridge);

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
// PENDING round trip (Change 5)
// ---------------------------------------------------------------------------

const pendingOverlay = document.getElementById('pending-overlay')!;
let activePendingHandle: string | null = null;

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
    pendingOverlay.textContent = `PENDING ROLL: ${spec} — click to drop dice`;
    pendingOverlay.style.display = 'block';
  }

  // Check for PENDING clear acknowledgment
  if (msgType === 'state_update' && updateType === 'pending_cleared') {
    activePendingHandle = null;
    pendingOverlay.style.display = 'none';
  }
});

pendingOverlay.addEventListener('click', () => {
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
  pendingOverlay.style.display = 'none';
});

// ---------------------------------------------------------------------------
// Raycaster for BeatIntent card click
// ---------------------------------------------------------------------------

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

renderer.domElement.addEventListener('click', (event) => {
  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);

  const hits = raycaster.intersectObject(beatCard.mesh);
  if (hits.length > 0) {
    beatCard.sendDeclareAction();
  }
});

// ---------------------------------------------------------------------------
// Camera posture keyboard controls
// ---------------------------------------------------------------------------

const postureLabel = document.getElementById('posture-label')!;

window.addEventListener('keydown', (event) => {
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
  renderer.render(scene, camera);
}

animate();

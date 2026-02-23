/**
 * Main entry — Table UI Slices 0-7 COMPLETE (Doctrine §19).
 *
 * Slice 0: Scene + camera + WS bridge
 * Slice 1: Dice ritual (PENDING_ROLL handshake, dice tray + tower)
 * Slice 2: Beat intent card
 * Slice 3: Book (PHB rules reference) — open/close, page flip, ? stamps
 * Slice 4: Notebook (player drawing, transcript, bestiary tabs)
 * Slice 5: Handout printer slot + tray + fanstack + discard well
 * Slice 6: Map tokens + ephemeral overlays (AoE, measure, area highlight)
 * Slice 7: Runtime integration (entity click → TOKEN_TARGET_INTENT, AoE confirm gate)
 *
 * Authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §3, §12, §16, §19 Slices 0-7.
 *            UX_VISION_PHYSICAL_TABLE.md north-star.
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
import { BookObject, QuestionStamp } from './book-object';
import { NotebookObject } from './notebook-object';
import { HandoutManager } from './handout-object';
import type { HandoutData } from './handout-object';
import { MapOverlayManager } from './map-overlay';
import type { AoEPreviewData } from './map-overlay';
import { EntityRenderer } from './entity-renderer';
import type { EntityData } from './entity-renderer';

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
// Slice 3 — BookObject (PHB rules reference)
// ---------------------------------------------------------------------------

const book = new BookObject();
scene.add(book.group);

// Page flip keyboard controls: [ and ] advance pages
window.addEventListener('keydown', (ev) => {
  if (ev.key === '[' || ev.key === 'ArrowLeft') book.flipBack();
  if (ev.key === ']' || ev.key === 'ArrowRight') book.flipForward();
  if (ev.key === 'b') book.toggle(); // b = book open/close
});

// WS: jump to page by rule reference
bridge.on('book_page_jump', (data) => {
  const ruleRef = data.rule_ref as string | undefined;
  if (ruleRef) book.openToRef(ruleRef);
});

// Question stamps — populated from WS events
const questionStamps: QuestionStamp[] = [];
bridge.on('question_stamp', (data) => {
  const label = (data.label as string) || '?';
  const x = (data.x as number) ?? 0;
  const y = (data.y as number) ?? 0.01;
  const z = (data.z as number) ?? 0;
  const stamp = new QuestionStamp(label, new THREE.Vector3(x, y, z));
  scene.add(stamp.mesh);
  questionStamps.push(stamp);
});

// ---------------------------------------------------------------------------
// Slice 4 — NotebookObject (player notes, transcript, bestiary)
// ---------------------------------------------------------------------------

const notebook = new NotebookObject();
scene.add(notebook.group);

// WS: add a transcript entry
bridge.on('notebook_entry', (data) => {
  const text = (data.text as string) || '';
  const rawSpeaker = (data.speaker as string) || 'narrator';
  const speaker = (['narrator', 'player', 'npc'].includes(rawSpeaker)
    ? rawSpeaker : 'narrator') as 'narrator' | 'player' | 'npc';
  notebook.addTranscriptEntry({ speaker, text });
});

// WS: switch the active notebook section
bridge.on('notebook_tab', (data) => {
  const sid = data.tab as 'notes' | 'transcript' | 'bestiary' | 'handouts';
  if (sid) notebook.setSection(sid);
});

// n = notebook open/close
window.addEventListener('keydown', (ev) => {
  if (ev.key === 'n') notebook.toggle();
});

// ---------------------------------------------------------------------------
// Slice 5 — HandoutManager (printer slot + tray + fanstack + discard well)
// ---------------------------------------------------------------------------

const handoutMgr = new HandoutManager(scene);

// Receive a handout from the engine
bridge.on('handout_deliver', (data) => {
  const handout_id = (data.handout_id as string) || '';
  const title = (data.title as string) || 'Handout';
  if (handout_id) handoutMgr.deliver({ handout_id, title });
});

// Alias for alternate message naming
bridge.on('handout_received', (data) => {
  const handout_id = (data.handout_id as string) || '';
  const title = (data.title as string) || 'Handout';
  if (handout_id) handoutMgr.deliver({ handout_id, title });
});

// Discard acknowledgment from engine
bridge.on('handout_discarded', (data) => {
  const handout_id = (data.handout_id as string) || '';
  if (handout_id) handoutMgr.removeHandout(handout_id);
});

// ---------------------------------------------------------------------------
// Slice 6 — MapOverlayManager (AoE, measure, area highlight)
// ---------------------------------------------------------------------------

const overlayMgr = new MapOverlayManager(scene);

// AoE preview
bridge.on('aoe_preview', (data) => {
  overlayMgr.showAoE(data as unknown as AoEPreviewData);
});
bridge.on('aoe_cleared', () => {
  overlayMgr.hideAoE();
});

// Measure line
bridge.on('measure_show', (data) => {
  const fromX = (data.from_x as number) ?? 0;
  const fromY = (data.from_y as number) ?? 0;
  const toX = (data.to_x as number) ?? 0;
  const toY = (data.to_y as number) ?? 0;
  overlayMgr.showMeasure(fromX, fromY, toX, toY);
});
bridge.on('measure_hide', () => {
  overlayMgr.hideMeasure();
});

// Area highlight (e.g. fog-of-war reveal)
bridge.on('area_highlight', (data) => {
  const squares = (data.squares as Array<[number, number]>) || [];
  const colorHex = (data.color_hex as number) | 0;
  overlayMgr.showArea(squares, colorHex || undefined);
});
bridge.on('area_clear', () => {
  overlayMgr.clearArea();
});

// ---------------------------------------------------------------------------
// Slice 7 — Entity renderer (live tokens from WS)
// ---------------------------------------------------------------------------

const entityRenderer = new EntityRenderer(scene);

bridge.on('entity_state', (data) => {
  const entities = (data.entities as EntityData[]) || [];
  entityRenderer.syncRoster(entities);
});

bridge.on('entity_delta', (data) => {
  const changes = data.changes as Partial<EntityData> | undefined;
  if (!changes) return;
  if ((changes as { defeated?: boolean }).defeated) {
    entityRenderer.remove(data.entity_id as string);
  } else {
    entityRenderer.upsert({ id: data.entity_id as string, ...changes } as EntityData);
  }
});

// ---------------------------------------------------------------------------
// Slice 7 — AoE confirm gate (doctrine §16: minimal DOM, no popovers)
// ---------------------------------------------------------------------------

const aoeOverlay = document.getElementById('aoe-overlay') as HTMLDivElement | null;
const aoeConfirm = document.getElementById('aoe-confirm') as HTMLButtonElement | null;
const aoeCancel  = document.getElementById('aoe-cancel')  as HTMLButtonElement | null;
let _pendingAoEData: AoEPreviewData | null = null;

// Show AoE confirm gate when engine requests confirmation
bridge.on('aoe_confirm_request', (data) => {
  _pendingAoEData = data as unknown as AoEPreviewData;
  overlayMgr.showAoE(_pendingAoEData);
  if (aoeOverlay) aoeOverlay.style.display = 'flex';
});

if (aoeConfirm) {
  aoeConfirm.addEventListener('click', () => {
    if (!_pendingAoEData) return;
    bridge.send({
      msg_type: 'player_action',
      msg_id: crypto.randomUUID(),
      timestamp: Date.now() / 1000,
      action_type: 'aoe_place',
      payload: {
        type: 'AOE_PLACE_INTENT',
        ..._pendingAoEData,
      },
    });
    _pendingAoEData = null;
    if (aoeOverlay) aoeOverlay.style.display = 'none';
    overlayMgr.hideAoE();
  });
}

if (aoeCancel) {
  aoeCancel.addEventListener('click', () => {
    _pendingAoEData = null;
    if (aoeOverlay) aoeOverlay.style.display = 'none';
    overlayMgr.hideAoE();
    bridge.send({
      msg_type: 'player_action',
      msg_id: crypto.randomUUID(),
      timestamp: Date.now() / 1000,
      action_type: 'aoe_cancel',
      payload: { type: 'AOE_PREVIEW_CANCELLED' },
    });
  });
}

// ---------------------------------------------------------------------------
// BeatIntent card click + handout click + entity token click
// ---------------------------------------------------------------------------

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

renderer.domElement.addEventListener('click', (event) => {
  // Don't process clicks during or just after drag
  if (dragInteraction.dragging) return;

  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);

  // Beat intent card click → DeclareActionIntent
  const beatHits = raycaster.intersectObject(beatCard.mesh);
  if (beatHits.length > 0) {
    beatCard.sendDeclareAction();
    return;
  }

  // Handout click → HANDOUT_READ_INTENT (doctrine §16)
  const handoutId = handoutMgr.handleClick(raycaster);
  if (handoutId) {
    bridge.send({
      msg_type: 'player_action',
      msg_id: crypto.randomUUID(),
      timestamp: Date.now() / 1000,
      action_type: 'handout_read',
      payload: { type: 'HANDOUT_READ_INTENT', handout_id: handoutId },
    });
    return;
  }

  // Entity token click → TOKEN_TARGET_INTENT (Slice 7 — doctrine §16)
  const tokenMeshes = entityRenderer.getTokenMeshes();
  if (tokenMeshes.length > 0) {
    const tokenHits = raycaster.intersectObjects(tokenMeshes, false);
    if (tokenHits.length > 0) {
      const hitMesh = tokenHits[0].object as THREE.Mesh;
      const entityId = entityRenderer.getEntityIdByMesh(hitMesh);
      if (entityId) {
        bridge.send({
          msg_type: 'player_action',
          msg_id: crypto.randomUUID(),
          timestamp: Date.now() / 1000,
          action_type: 'token_target',
          payload: { type: 'TOKEN_TARGET_INTENT', entity_id: entityId },
        });
      }
      return;
    }
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
  book.update(dt);                               // Slice 3: open/close animation
  for (const stamp of questionStamps) stamp.pulse(elapsed);
  notebook.update(dt);                           // Slice 4: open/close animation
  handoutMgr.update(dt);                         // Slice 5: delivery animation
  overlayMgr.update(elapsed);                    // Slice 6: overlay pulse
  renderer.render(scene, camera);
}

animate();

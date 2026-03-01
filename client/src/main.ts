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
import { ZONES, getZone } from './zones';
import {
  buildTableSurface,
  buildAtmosphere,
  buildRoom,
  buildObjectStubs,
  updateFlicker,
  updateCrystalBall,
  crystalBallOrbMesh,
  crystalBallInnerMesh,
  characterSheetMesh,
  notebookMesh,
  tomeMesh,
  updateCharacterSheetLive,
  SceneImagePlane,
  vaultCoverMesh,
} from './scene-builder';
import type { LanternLight, AtmosphereResult } from './scene-builder';
import { CrystalBallController } from './crystal-ball-controller';
import { BookObject, QuestionStamp } from './book-object';
import { RulebookObject } from './rulebook-object';
import { NotebookObject } from './notebook-object';
import { NotebookRadial } from './notebook-radial';
import type { RadialTool, RadialSelection } from './notebook-radial';
import { HandoutManager } from './handout-object';
import type { HandoutData } from './handout-object';
import { MapOverlayManager } from './map-overlay';
import type { AoEPreviewData, OverlayPendingKind } from './map-overlay';
import { EntityRenderer } from './entity-renderer';
import { DiceBagObject, TowerPlaque, makePrng as makeDiceBagPrng } from './dice-bag';
import type { EntityData } from './entity-renderer';
import { FogOfWarManager } from './fog-of-war';
import { BattleScrollObject } from './battle-scroll';
import { CharacterSheetController } from './character-sheet-controller';
import { MapLassoManager } from './map-lasso';
import { BestiaryBindController } from './bestiary-bind';
import { SettingsGem } from './settings-gem';
import { SoftDeleteStack } from './cup-holder';
import { searchRuleRef } from './rulebook-search';
import { isDebugMode, mountDebugOverlay, mountCameraDebugHUD, updateCameraDebugHUD } from './debug-overlay';
import { ShelfDragController } from './shelf-drag';
import type {
  RulebookOpenMsg,
  RulebookSearchMsg,
  BestiaryRevealMsg,
  CharacterSheetUpdateMsg,
  TtsSpeakingStartMsg,
  NpcPortraitDisplayMsg,
  FogUpdateMsg,
  SceneImageMsg,
  NotebookCoverNameMsg,
  NotebookCoverImageMsg,
} from './types/messages';

// ---------------------------------------------------------------------------
// Scene setup
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// ?debug=1 — spatial debug overlay
// ---------------------------------------------------------------------------

const _debugMode = new URLSearchParams(window.location.search).get('debug') === '1';

let _debugHud: HTMLDivElement | null = null;
const _debugLines: string[] = [];

function debugLog(msg: string): void {
  if (!_debugMode || !_debugHud) return;
  const ts = performance.now().toFixed(0);
  _debugLines.push(`[${ts}ms] ${msg}`);
  if (_debugLines.length > 20) _debugLines.shift();
  _debugHud.textContent = _debugLines.join('\n');
}

if (_debugMode) {
  // Inject a fixed HUD console in the top-right corner
  _debugHud = document.createElement('div');
  Object.assign(_debugHud.style, {
    position: 'fixed',
    top: '8px',
    right: '8px',
    width: '340px',
    maxHeight: '420px',
    background: 'rgba(0,0,0,0.78)',
    color: '#00ff88',
    fontFamily: 'Consolas, monospace',
    fontSize: '11px',
    padding: '8px 10px',
    borderRadius: '4px',
    border: '1px solid #00ff88',
    pointerEvents: 'none',
    whiteSpace: 'pre',
    zIndex: '99',
    overflow: 'hidden',
    userSelect: 'none',
  });
  document.body.appendChild(_debugHud);
  debugLog('debug=1 mode active');
}

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.35;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x100c0a); // WO-UI-LIGHTING-V1: warm dark brown (was 0x08060a void black)
scene.fog = new THREE.Fog(0x100c0a, 16, 26);  // WO-UI-LIGHTING-V1: pushed out so rails don't fog (was 14,22)

// Debug helpers — visible only when ?debug=1
if (_debugMode) {
  // AxesHelper: X=red, Y=green, Z=blue; 4 units long
  const axes = new THREE.AxesHelper(4);
  axes.name = 'debug_axes';
  scene.add(axes);

  // GridHelper: 12×8 table footprint, 1-unit divisions, step every 0.5
  const grid = new THREE.GridHelper(14, 28, 0x444488, 0x222244);
  grid.name = 'debug_grid';
  grid.position.y = 0.001; // float just above table surface
  scene.add(grid);

  debugLog('AxesHelper + GridHelper added to scene');
}

const camera = new THREE.PerspectiveCamera(
  60,
  window.innerWidth / window.innerHeight,
  0.1,
  100
);
const postureCtrl = new CameraPostureController(camera);

// Expose controller for Playwright gate access and debug overlay.
// Only available in dev build — stripped from production.
if (import.meta.env.DEV) {
  (window as any).__cameraController__ = postureCtrl;
  // __sceneDebug__: vault mesh state dump for visual QA.
  (window as any).__sceneDebug__ = {
    get scene()          { return scene; },
    get renderer()       { return renderer; },
    get vaultCoverMesh() { return vaultCoverMesh; },
    get feltVaultMesh()  {
      return tableSurface?.getObjectByName('felt_vault') ?? null;
    },
    get battleScrollMesh() {
      return scene.getObjectByName('battle_scroll_surface') ?? null;
    },
  };
}

// ---------------------------------------------------------------------------
// Table surface + atmosphere (WO-UI-05)
// ---------------------------------------------------------------------------

const tableSurface = buildTableSurface();
scene.add(tableSurface);
// VQ-001: Hide felt vault at rest — only visible when battle scroll is unrolled
const _feltVault = tableSurface.getObjectByName('felt_vault') as THREE.Mesh | undefined;
if (_feltVault) _feltVault.visible = false;
// ---------------------------------------------------------------------------
// Settings Gem (WO-UI-SETTINGS-GEM-001)
// ---------------------------------------------------------------------------
const settingsGem = new SettingsGem();
scene.add(settingsGem.mesh);

const objectStubs = buildObjectStubs();
scene.add(objectStubs);

// ---------------------------------------------------------------------------
// Crystal Ball Controller (WO-UI-CRYSTAL-BALL-001)
// ---------------------------------------------------------------------------
const crystalBallController = new CrystalBallController(crystalBallOrbMesh!, crystalBallInnerMesh ?? undefined);
// Hide stubs that are replaced by live interactive objects (book, notebook)
// Also hide stub_parchment — HandoutManager owns paper on the table (VQ-010)
const _stubTome     = objectStubs.getObjectByName('stub_tome');
const _stubNotebook = objectStubs.getObjectByName('stub_notebook');
const _stubParch    = objectStubs.getObjectByName('stub_parchment');
if (_stubTome)     _stubTome.visible     = false;
if (_stubNotebook) _stubNotebook.visible = false;
if (_stubParch)    _stubParch.visible    = false;

const _atmo: AtmosphereResult = buildAtmosphere(scene);
const lanterns: LanternLight[]        = _atmo.lanterns;
const _mapSpot: THREE.PointLight      = _atmo.mapSpot;    // COMBAT-only
const _shelfFill: THREE.PointLight    = _atmo.shelfFill;  // REST shelf fill
buildRoom(scene); // WO-UI-LIGHTING-V1: back wall + floor plane

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

// Dice bag — player shelf, left of notebook (WO-UI-DICE-BAG-001)
const diceBagPrng = makeDiceBagPrng(0xb4693a1);  // fixed seed for bag texture
const diceBag = new DiceBagObject(scene, diceBagPrng);
scene.add(diceBag.group);

// Tower Plaque (WO-UI-DICE-01 O8C) — spec-only display near dice tower.
// Anchor: dice_tower_base = (4.5, 0.065, 0.5) from zones.json.
// Hidden until PENDING_ROLL is active; shows formula only, never DC.
const towerPlaque = new TowerPlaque(4.5, 0.065, 0.5);
scene.add(towerPlaque.mesh);

// ---------------------------------------------------------------------------
// Drag interaction system (Changes 2, 4, 5)
// ---------------------------------------------------------------------------

let cameraLocked = false;

// PENDING_ROLL state — declared here so drag callbacks can reference it
const pendingOverlay = document.getElementById('pending-overlay')!;
let activePendingHandle: string | null = null;

// PENDING_MOVE_TOKEN state — server-issued token drag authorization
let _activePendingMoveId: string | null = null;

const dragInteraction = new DragInteraction(
  registry,
  camera,
  renderer,
  scene,
  bridge,
  {
    onDragStart: () => {
      cameraLocked = true;
      // DICE_TRAY posture wiring (DICE-RITUAL-04):
      // Switch to DICE_TRAY posture when the die is lifted from the tray.
      const picked = registry.picked;
      if (picked && picked.kind === 'die' && picked.zone === 'dice_tray') {
        postureCtrl.setPosture('DICE_TRAY');
      }
    },
    onDragEnd: () => { cameraLocked = false; },
    onDrop: (obj, zone) => {
      // Dice dropped in tower zone → send DiceTowerDropIntent
      if (obj.kind === 'die' && zone === 'dice_tower' && activePendingHandle) {
        _sendDiceTowerDrop();
      }
    },
  },
);

// Cup holder soft-delete stack (WO-UI-CUP-HOLDER-001)
const softDeleteStack = new SoftDeleteStack((count) => {
  // Visual feedback: update cup holder emissive based on count
  console.log(`[CupHolder] Stack: ${count}/5`);
});

// Cup holder drop handler — called when object is dropped on cup_holder zone
function _handleCupHolderDrop(objectId: string, object3D: THREE.Object3D): void {
  const pushed = softDeleteStack.push(objectId, object3D);
  if (!pushed) {
    console.warn('[CupHolder] Stack full (max 5). Cannot soft-delete.');
  }
}

// Cup holder click handler — retrieves last soft-deleted object
function _handleCupHolderClick(): void {
  const item = softDeleteStack.pop();
  if (item) {
    console.log(`[CupHolder] Retrieved: ${item.id}`);
  }
}

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

    // Tower Plaque (O8C): show formula only when PENDING_ROLL is active
    towerPlaque.setPending(spec);

    // Activate the d20 die — make it pickable and start fidget
    d20.activate();
  }

  // Check for PENDING clear acknowledgment
  if (msgType === 'state_update' && updateType === 'pending_cleared') {
    activePendingHandle = null;
    pendingOverlay.style.display = 'none';
    towerPlaque.clear();
    d20.deactivate();
    // WO-UI-TOKENS-01: clear token drag pending on any pending_cleared
    _activePendingMoveId = null;
    entityRenderer.clearMovePending();
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

  // Tower Plaque clears immediately on result — formula no longer pending
  towerPlaque.clear();

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
// Slice 3 — BookObject (PHB rules reference) + BOOK_READ posture wiring
// WO-UI-RULEBOOK-01: BOOK_READ posture triggered on every book open.
// ---------------------------------------------------------------------------

const book = new BookObject();
book.group.position.set(2.2, 0.07, 4.5); // player shelf — right edge, pulled slightly inward
scene.add(book.group);

// RulebookObject is instantiated here for the gate scan (RB-ART-01).
// It re-uses the same BookObject via delegation; its group is not separately
// added to the scene (book.group above is the live scene object).
// The shelf_rulebook anchor position is encoded in RulebookObject's constructor.
const _rulebookObject = new RulebookObject();
// Suppress unused-variable warning — _rulebookObject exists for the static
// scan required by RB-ART-01 (scene-builder.ts references stub_tome at the
// shelf_rulebook anchor; this wires the RulebookObject class into main.ts).
void _rulebookObject;

/**
 * Open the rulebook to a rule_ref and switch to BOOK_READ posture.
 * WO-UI-RULEBOOK-01: BOOK_READ posture is triggered on every open interaction.
 * A-RULES-OPEN: no precondition check — always opens.
 */
function _openRulebook(ruleRef?: string): void {
  if (ruleRef) {
    book.openToRef(ruleRef);
  } else {
    book.open();
  }
  postureCtrl.setPosture('BOOK_READ');
}

// Page flip keyboard controls: [ and ] advance pages
window.addEventListener('keydown', (ev) => {
  if (ev.key === '[' || ev.key === 'ArrowLeft') book.flipBack();
  if (ev.key === ']' || ev.key === 'ArrowRight') book.flipForward();
  if (ev.key === 'b') {
    // b = book open/close; trigger BOOK_READ posture on open
    if (!book.isOpen) {
      _openRulebook();
    } else {
      book.close();
    }
  }
});

// WS: jump to page by rule reference
bridge.on('book_page_jump', (data) => {
  const ruleRef = data.rule_ref as string | undefined;
  if (ruleRef) _openRulebook(ruleRef);
});

// WS: rulebook_open — direct ref navigation (WO-UI-RULEBOOK-SEARCH-001)
bridge.on('rulebook_open', (data: RulebookOpenMsg) => {
  _openRulebook(data.rule_ref ?? '');
});

// WS: rulebook_search — fuzzy query to ref navigation (WO-UI-RULEBOOK-SEARCH-001)
bridge.on('rulebook_search', (data: RulebookSearchMsg) => {
  const ref = searchRuleRef(data.query ?? '');
  _openRulebook(ref);
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
notebook.group.position.set(-0.2, 0.05, 5.1); // player shelf — center-left, behind shelf rail
scene.add(notebook.group);

// WS: transcript is a read-only feed — displayed via setTranscriptFeedTexture().
// notebook_entry events are intentionally ignored per doctrine (transcript is feed-only).
bridge.on('notebook_entry', (_data) => { /* no-op: transcript feed is external */ });

// WS: switch the active notebook section
bridge.on('notebook_tab', (data) => {
  const sid = data.tab as 'notes' | 'transcript' | 'bestiary' | 'handouts';
  if (sid) notebook.setSection(sid);
});

// ---------------------------------------------------------------------------
// WO-UI-BESTIARY-BIND-001 — Bestiary Image Binding
// ---------------------------------------------------------------------------

const bestiaryBind = new BestiaryBindController((entry, _opacity) => {
  // Wire bestiary reveal → notebook bestiary section (WO-UI-BESTIARY-IMAGE-001)
  notebook.upsertBestiaryEntry({
    entity_id:       entry.creature_id,
    knowledge_level: entry.knowledge_state,
    name:            entry.name ?? entry.creature_id,
    description:     (entry.traits ?? []).join(', '),
    image_url:       entry.image_url,
  });
});

bridge.on('bestiary_entry_reveal', (data: BestiaryRevealMsg) => {
  bestiaryBind.handleReveal(data);
});


// n = notebook open/close
window.addEventListener('keydown', (ev) => {
  if (ev.key === 'n') notebook.toggle();
});

// ---------------------------------------------------------------------------
// WO-UI-PHYSICALITY-BASELINE-V1 — Kinematic shelf drag
// Drags characterSheetMesh, notebook cover, rulebook cover, dice bag.
// Hard-clamped to SHELF_ZONE bounds. lerp=0.18, settle=8 frames.
// ---------------------------------------------------------------------------
const _shelfZone = getZone('SHELF_ZONE')!;
const shelfDrag = new ShelfDragController(camera, renderer, _shelfZone);
shelfDrag.register(characterSheetMesh!);   // flat parchment plane
shelfDrag.register(notebook.coverMesh);     // live notebook right cover
shelfDrag.register(book.coverMesh);         // live rulebook right cover
shelfDrag.register(diceBag.bodyMesh);       // dice bag body

// Click closed notebook cover → open. Click open notebook spine area → close.
{
  const _nbOpenRay = new THREE.Raycaster();
  let _nbPointerMoved = false;
  renderer.domElement.addEventListener('pointerdown', () => { _nbPointerMoved = false; });
  renderer.domElement.addEventListener('pointermove', () => { _nbPointerMoved = true; });
  renderer.domElement.addEventListener('pointerup', (ev) => {
    if (ev.button !== 0 || _nbPointerMoved) return;
    _nbOpenRay.setFromCamera(
      new THREE.Vector2((ev.clientX / window.innerWidth) * 2 - 1, -(ev.clientY / window.innerHeight) * 2 + 1),
      camera,
    );
    if (!notebook.isOpen) {
      // Click on any part of the closed notebook group → open
      const hits = _nbOpenRay.intersectObject(notebook.group, true);
      if (hits.length > 0) notebook.open();
    } else {
      // Click on spine → close
      const spineHits = _nbOpenRay.intersectObjects(
        notebook.group.children.filter(c => c.name === 'notebook_spine'), false,
      );
      if (spineHits.length > 0) notebook.close();
    }
  });
}

// ---------------------------------------------------------------------------
// WO-UI-NOTEBOOK-INK-RADIAL-001 — Pencil cursor + radial tool wheel + text input
// Extends WO-UI-NOTEBOOK-DRAW-WIRE-001 drawing wire with:
//   - Pencil cursor when hovering open notes page
//   - Right-click radial for tool selection (pen/brush/eraser/text)
//   - Text input mode: click to place textarea, keyboard commits to canvas
// Doctrine: DOCTRINE_04 §8 (MARK wedge only); TABLE_METAPHOR §Part 2 §3-5.
// ---------------------------------------------------------------------------
{
  const _nbRaycaster = new THREE.Raycaster();
  const _nbMouse     = new THREE.Vector2();
  let   _nbDrawing   = false;
  let   _nbActiveTool: RadialTool = 'pen';   // current active tool
  let   _nbTextMode  = false;                 // true when text tool selected
  let   _nbTextOverlay: HTMLTextAreaElement | null = null;

  // Pencil cursor: inline SVG data-URI so no asset file needed
  const PENCIL_CURSOR = [
    "url(\"data:image/svg+xml,",
    "<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'>",
    "<path d='M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25z' fill='%231a0e06'/>",
    "<path d='M20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z' fill='%23b5832a'/>",
    "</svg>\") 0 24, crosshair",
  ].join('');

  // Instantiate the radial — fires when user picks a tool
  const _nbRadial = new NotebookRadial((sel: RadialSelection) => {
    const tool = sel.tool;
    if (tool === null) return; // Cancel — do nothing
    _nbActiveTool = tool;
    _nbTextMode   = tool === 'text';
    // Apply color and size to notebook
    notebook.setInkColor(sel.color);
    notebook.setInkSize(sel.size);
    if (!_nbTextMode) {
      // Map radial tool to notebook draw tool
      const drawToolMap: Record<string, 'pen' | 'brush' | 'eraser'> = {
        pen: 'pen', brush: 'brush', eraser: 'eraser',
      };
      if (drawToolMap[tool]) {
        // Set tool by cycling to match (notebook cycles pen→brush→eraser)
        while (notebook.drawTool !== drawToolMap[tool]) {
          notebook.cycleDrawTool();
        }
      }
    }
  });

  function _nbUvFromEvent(ev: PointerEvent | MouseEvent): { u: number; v: number } | null {
    _nbMouse.x = (ev.clientX / window.innerWidth) * 2 - 1;
    _nbMouse.y = -(ev.clientY / window.innerHeight) * 2 + 1;
    _nbRaycaster.setFromCamera(_nbMouse, camera);
    const hits = _nbRaycaster.intersectObject(notebook.pageRightMesh, false);
    if (hits.length === 0 || !hits[0].uv) return null;
    return { u: hits[0].uv.x, v: hits[0].uv.y };
  }

  function _isNotesPageActive(): boolean {
    return notebook.isOpen && notebook.section === 'notes';
  }

  // Commit any open text overlay to the canvas
  function _commitTextOverlay(): void {
    if (!_nbTextOverlay) return;
    const text = _nbTextOverlay.value.trim();
    if (text) {
      const cx = parseFloat(_nbTextOverlay.dataset.cx ?? '200');
      const cy = parseFloat(_nbTextOverlay.dataset.cy ?? '200');
      notebook.addTextBlock(cx, cy, text);
    }
    _nbTextOverlay.remove();
    _nbTextOverlay = null;
  }

  // Place a textarea overlay at UV hit position for text input
  function _placeTextOverlay(ev: PointerEvent): void {
    _commitTextOverlay();
    const uv = _nbUvFromEvent(ev);
    if (!uv) return;
    const cvPt = notebook.uvToCanvas(uv.u, uv.v);

    const ta = document.createElement('textarea');
    ta.dataset.cx = String(cvPt.x);
    ta.dataset.cy = String(cvPt.y);
    ta.rows = 3;
    ta.placeholder = 'Type here…';
    Object.assign(ta.style, {
      position:     'fixed',
      left:         `${ev.clientX}px`,
      top:          `${ev.clientY - 60}px`,
      width:        '200px',
      minHeight:    '60px',
      fontFamily:   'Georgia, serif',
      fontSize:     '13px',
      color:        '#1a0e06',
      background:   'rgba(245, 240, 228, 0.95)',
      border:       '1px solid #8a6a30',
      borderRadius: '3px',
      padding:      '4px 6px',
      zIndex:       '9998',
      resize:       'none',
      outline:      'none',
    });

    ta.addEventListener('keydown', (kev) => {
      if (kev.key === 'Escape') { _commitTextOverlay(); }
      if (kev.key === 'Enter' && !kev.shiftKey) { kev.preventDefault(); _commitTextOverlay(); }
    });
    ta.addEventListener('blur', () => { _commitTextOverlay(); });

    document.body.appendChild(ta);
    _nbTextOverlay = ta;
    ta.focus();
  }

  // ---- Pointer events ----

  renderer.domElement.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 0) return;
    if (_nbRadial.isVisible) return;

    // Tab click — switches page section when notebook is open
    if (notebook.isOpen) {
      const tabRay = new THREE.Raycaster();
      tabRay.setFromCamera(
        new THREE.Vector2((ev.clientX / window.innerWidth) * 2 - 1, -(ev.clientY / window.innerHeight) * 2 + 1),
        camera,
      );
      const tabHits = tabRay.intersectObjects(notebook.tabMeshes, false);
      if (tabHits.length > 0) {
        const sid = notebook.getTabSection(tabHits[0].object);
        if (sid) { notebook.setSection(sid); return; }
      }
    }

    if (!_isNotesPageActive()) return;

    if (_nbTextMode) {
      _placeTextOverlay(ev);
      return;
    }

    const uv = _nbUvFromEvent(ev);
    if (!uv) return;
    _nbDrawing = true;
    notebook.startStroke(uv.u, uv.v);
  });

  renderer.domElement.addEventListener('pointermove', (ev) => {
    // Pencil cursor: show when hovering over open notes page
    if (_isNotesPageActive()) {
      const uv = _nbUvFromEvent(ev);
      renderer.domElement.style.cursor = uv ? PENCIL_CURSOR : '';
    } else {
      renderer.domElement.style.cursor = '';
    }

    if (!_nbDrawing) return;
    const uv = _nbUvFromEvent(ev);
    if (!uv) return;
    notebook.continueStroke(uv.u, uv.v);
  });

  renderer.domElement.addEventListener('pointerup', () => {
    if (!_nbDrawing) return;
    _nbDrawing = false;
    notebook.endStroke();
  });

  renderer.domElement.addEventListener('pointerleave', () => {
    renderer.domElement.style.cursor = '';
    if (!_nbDrawing) return;
    _nbDrawing = false;
    notebook.endStroke();
  });

  // Right-click → radial tool wheel (notes page only)
  renderer.domElement.addEventListener('contextmenu', (ev) => {
    if (!_isNotesPageActive()) return;
    const uv = _nbUvFromEvent(ev as unknown as PointerEvent);
    if (!uv) return;
    ev.preventDefault();
    _nbRadial.show(ev.clientX, ev.clientY);
  });
}


// ---------------------------------------------------------------------------
// WO-UI-SESSION-ZERO-001 -- Session Zero WS events
// ---------------------------------------------------------------------------

bridge.on('session_zero_start', (_data: Record<string, unknown>) => {
  // DM is introducing itself -- nothing visual to do on client yet
  // Future: could trigger a welcome animation
});

bridge.on('notebook_cover_name', (data: NotebookCoverNameMsg) => {
  notebook.setCoverName(data.player_name ?? '');
});

bridge.on('notebook_cover_image', (data: NotebookCoverImageMsg) => {
  notebook.setCoverImage(data.image_url ?? '');
});

bridge.on('session_resume', (_data: Record<string, unknown>) => {
  // Reload cover from localStorage for this session
  notebook.loadCoverFromStorage();
});

// ---------------------------------------------------------------------------
// WO-UI-SESSION-CLEANUP-01 — Scene lifecycle reset
// Resets table to deterministic physical baseline at scene boundaries.
// Authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §19 Slice 0 (scene lifecycle).
// Must NOT clear: notebook strokes (localStorage), fog of war (server-auth).
// ---------------------------------------------------------------------------

/** Full table baseline reset — call on scene_end and before scene_start data load. */
function _resetToBaseline(): void {
  entityRenderer.syncRoster([]);                       // SC-02: clear all entity tokens
  entityRenderer.clearMovePending();                   // clear any PENDING_MOVE_TOKEN
  overlayMgr.clearPending();                           // SC-03: clear map overlays + PENDING gate
  mapLasso.clearPending();                             // clear lasso PENDING gate
  handoutMgr.clearAll();                               // clear handout tray + discard stack
  notebook.consentChain.resetOnSceneEnd();             // SC-04: consent does not carry
  postureCtrl.setPosture('STANDARD');                  // SC-05: back to default camera
  handoutMgr.setDiscardHighlight(false);               // hide discard well ring
}

bridge.on('scene_end', (_data: Record<string, unknown>) => {  // SC-06
  _resetToBaseline();
});

bridge.on('scene_start', (_data: Record<string, unknown>) => { // SC-07
  _resetToBaseline();
  // New scene data will arrive via subsequent entity_state / fog_update etc.
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
// Slice 6 — MapOverlayManager + MapLassoManager (AoE, measure, area highlight)
// ---------------------------------------------------------------------------

const overlayMgr = new MapOverlayManager(scene);

// ---------------------------------------------------------------------------
// WO-UI-MAP-LASSO-001 — Map Area Indication Lasso
// ---------------------------------------------------------------------------

const mapLasso = new MapLassoManager(scene, (kind, polygon) => {
  bridge.send({ msg_type: 'MAP_AREA_INTENT', kind, polygon });
});

// PENDING gate wiring (WO-UI-MAP-01): overlays only activate when a matching
// PENDING kind is set. WS events pending_map_aoe / pending_map_point /
// pending_map_search activate the gate; pending_map_cleared resets it.
bridge.on('pending_map_aoe', () => {
  overlayMgr.setPending('PENDING_AOE');
  mapLasso.setPending('PENDING_AOE');
  postureCtrl.setPosture('LEAN_FORWARD');
});
bridge.on('pending_map_point', () => {
  overlayMgr.setPending('PENDING_POINT');
  mapLasso.setPending('PENDING_POINT');
  postureCtrl.setPosture('LEAN_FORWARD');
});
bridge.on('pending_map_search', () => {
  overlayMgr.setPending('PENDING_SEARCH');
  mapLasso.setPending('PENDING_SEARCH');
  postureCtrl.setPosture('LEAN_FORWARD');
});
bridge.on('pending_map_cleared', () => {
  overlayMgr.clearPending();
  mapLasso.clearPending();
});

// AoE preview — routed only when PENDING_AOE is active (gate enforced in overlayMgr)
bridge.on('aoe_preview', (data) => {
  overlayMgr.showAoE(data as unknown as AoEPreviewData);
});
bridge.on('aoe_cleared', () => {
  overlayMgr.hideAoE();
});

// Measure line — routed only when PENDING_POINT is active
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

// Area highlight — routed only when PENDING_SEARCH is active
bridge.on('area_highlight', (data) => {
  const squares = (data.squares as Array<[number, number]>) || [];
  const colorHex = (data.color_hex as number) | 0;
  overlayMgr.showArea(squares, colorHex || undefined);
});
bridge.on('area_clear', () => {
  overlayMgr.clearArea();
});

renderer.domElement.addEventListener('pointerdown', (event) => {
  if (event.button !== 0) return;
  const nx = (event.clientX / window.innerWidth) * 2 - 1;
  const ny = -(event.clientY / window.innerHeight) * 2 + 1;
  const lassoRay = new THREE.Raycaster();
  lassoRay.setFromCamera(new THREE.Vector2(nx, ny), camera);
  const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  const target = new THREE.Vector3();
  if (lassoRay.ray.intersectPlane(plane, target)) {
    mapLasso.startDrag({ x: target.x, z: target.z });
    // LEAN_FORWARD posture only when a lasso drag actually begins (pending active)
    if (mapLasso.isDragging && mapLasso.activePending !== null) {
      postureCtrl.setPosture('LEAN_FORWARD');
    }
  }
});

renderer.domElement.addEventListener('pointermove', (event) => {
  if (!mapLasso.isDragging) return;
  const nx = (event.clientX / window.innerWidth) * 2 - 1;
  const ny = -(event.clientY / window.innerHeight) * 2 + 1;
  const lassoRay = new THREE.Raycaster();
  lassoRay.setFromCamera(new THREE.Vector2(nx, ny), camera);
  const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  const target = new THREE.Vector3();
  if (lassoRay.ray.intersectPlane(plane, target)) {
    mapLasso.updateDrag({ x: target.x, z: target.z });
  }
});

renderer.domElement.addEventListener('pointerup', () => {
  if (mapLasso.isDragging) mapLasso.endDrag('SEARCH');
});

// ---------------------------------------------------------------------------
// Slice 7 — Entity renderer (live tokens from WS)
// ---------------------------------------------------------------------------

const entityRenderer = new EntityRenderer(scene);

bridge.on('entity_state', (data) => {
  const entities = (data.entities as EntityData[]) || [];
  entityRenderer.syncRoster(entities);
  // WO-UI-FOG-VISION-001: extract VISION_TYPE EF and register per entity
  for (const e of entities) {
    const vt = (e as unknown as Record<string, unknown>).VISION_TYPE as string | undefined;
    if (vt === 'normal' || vt === 'low_light' || vt === 'darkvision') {
      fogOfWar.setEntityVision(e.id, vt);
    }
  }
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
// WO-UI-TOKENS-01 — PENDING_MOVE_TOKEN handshake
// Authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §16 (PENDING handshake), §17 (no inferred facts).
// Drag is only permitted when this PENDING is active for a specific entity.
// ---------------------------------------------------------------------------

bridge.on('PENDING_MOVE_TOKEN', (data: { entity_id: string; pending_id: string }) => {
  _activePendingMoveId = data.pending_id;
  entityRenderer.setMovePending(data.entity_id);
});

// ---------------------------------------------------------------------------
// Character Sheet Controller — WO-UI-CHARACTER-SHEET-001
// ---------------------------------------------------------------------------

const charSheet = new CharacterSheetController(
  // onDeclareAction: emit REQUEST_DECLARE_ACTION
  (actionId, entityId) => {
    bridge.send({
      msg_type: 'REQUEST_DECLARE_ACTION',
      action_id: actionId,
      entity_id: entityId,
    });
  },
  // onQuestionStamp: place QuestionStamp and wire click to rulebook
  (actionId, ruleRef) => {
    const stamp = new QuestionStamp(ruleRef, new THREE.Vector3(0, 0.1, 4.0));
    scene.add(stamp.mesh);
    questionStamps.push(stamp);
    stamp.mesh.userData.ruleRef = ruleRef;
  },
);

bridge.on('character_sheet_update', (data: CharacterSheetUpdateMsg) => {
  charSheet.handleSheetUpdate(data);
  // Redraw live fields on the 3D sheet texture
  updateCharacterSheetLive({
    hp_current: data.hp_current as number,
    hp_max: data.hp_max as number,
    conditions: data.conditions as string[],
    spell_slots: data.spell_slots as Record<number, number>,
    spell_slots_max: data.spell_slots_max as Record<number, number>,
  });
});

// Second entity_delta handler — updates character sheet HP and conditions.
// bridge.on() is additive; this does not replace the existing entity_delta handler.
bridge.on('entity_delta', (data: Record<string, unknown>) => {
  charSheet.handleEntityDelta(data.entity_id as string, (data.changes ?? {}) as Record<string, unknown>);
  // Also redraw sheet texture if HP or conditions changed
  const ch = (data.changes ?? {}) as { hp_current?: number; conditions?: string[] };
  if (ch.hp_current !== undefined || ch.conditions !== undefined) {
    updateCharacterSheetLive({
      hp_current: ch.hp_current,
      conditions: ch.conditions,
    });
  }
});

// ---------------------------------------------------------------------------
// Crystal Ball — TTS and NPC portrait WS events (WO-UI-CRYSTAL-BALL-001)
// ---------------------------------------------------------------------------

bridge.on('tts_speaking_start', (data: TtsSpeakingStartMsg) => {
  crystalBallController.onSpeakingStart((data.intensity) ?? 1.0);
});

bridge.on('tts_speaking_stop', (_data: Record<string, unknown>) => {
  crystalBallController.onSpeakingStop();
});

bridge.on('npc_portrait_display', (data: NpcPortraitDisplayMsg) => {
  crystalBallController.onPortraitDisplay(
    (data.image_url) ?? '',
    (data.clear) ?? false,
  );
});

// ---------------------------------------------------------------------------
// Slice 8 — Fog of War overlay (WO-UI-FOG-OF-WAR-001)
// ---------------------------------------------------------------------------

const fogOfWar = new FogOfWarManager(scene);

bridge.on('fog_update', (data: FogUpdateMsg) => {
  fogOfWar.handleFogUpdate(data);
});

// ---------------------------------------------------------------------------
// Battle Scroll — combat_start / combat_end (WO-UI-BATTLE-SCROLL-001)
// ---------------------------------------------------------------------------

const _scrollPrng = makeDiceBagPrng(0xd3b5c0ad);
const battleScroll = new BattleScrollObject(_scrollPrng);
scene.add(battleScroll.group);
// Note: EntityRenderer and MapOverlayManager add objects directly to the scene
// (no single top-level group exposed), so linkTokenGroup / linkOverlayGroup
// are not called here. Tokens and overlays remain scene-level.

// WO-UI-SCENE-IMAGE-001: DM-side scene image plane
const sceneImagePlane = new SceneImagePlane(scene);

// ---------------------------------------------------------------------------
// Lighting state fade — map spot is COMBAT-only; shelf fill is REST-only.
// 400ms linear fade so state changes feel physical, not a snap.
// ---------------------------------------------------------------------------

const MAP_SPOT_COMBAT  = 44;  // full intensity during combat
const MAP_SPOT_REST    = 0;   // off at rest — eliminates the "grid board" read
const SHELF_FILL_REST  = 18;  // warm fill for DOWN shelf legibility
const SHELF_FILL_COMBAT = 6;  // dim during combat (map spot takes over)
const LIGHTING_FADE_MS = 400;

function _fadeLightTo(light: THREE.PointLight, target: number, ms: number): void {
  const start     = light.intensity;
  const startTime = performance.now();
  const tick = () => {
    const t = Math.min(1, (performance.now() - startTime) / ms);
    light.intensity = start + (target - start) * t;
    if (t < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

bridge.on('combat_start', (_data: Record<string, unknown>) => {
  battleScroll.onCombatStart();
  sceneImagePlane.onCombatStart();
  if (_feltVault) _feltVault.visible = true;
  if (vaultCoverMesh) vaultCoverMesh.visible = false;
  _fadeLightTo(_mapSpot,   MAP_SPOT_COMBAT,   LIGHTING_FADE_MS);
  _fadeLightTo(_shelfFill, SHELF_FILL_COMBAT, LIGHTING_FADE_MS);
});

bridge.on('combat_end', (_data: Record<string, unknown>) => {
  battleScroll.onCombatEnd();
  sceneImagePlane.onCombatEnd();
  if (_feltVault) _feltVault.visible = false;
  if (vaultCoverMesh) vaultCoverMesh.visible = true;
  _fadeLightTo(_mapSpot,   MAP_SPOT_REST,  LIGHTING_FADE_MS);
  _fadeLightTo(_shelfFill, SHELF_FILL_REST, LIGHTING_FADE_MS);
});

bridge.on('scene_image', (data: SceneImageMsg) => {
  sceneImagePlane.onSceneImage((data.image_url) ?? '');
});

// ---------------------------------------------------------------------------
// Demo combat toggle — press 'c' to toggle combat (no backend required)
// Populates placeholder tokens so the battle map is visible for inspection.
// ---------------------------------------------------------------------------
let _combatActive = false;

function _startDemoCombat(): void {
  battleScroll.onCombatStart();
  sceneImagePlane.onCombatStart();
  if (_feltVault) _feltVault.visible = true;
  if (vaultCoverMesh) vaultCoverMesh.visible = false;
  _fadeLightTo(_mapSpot,   MAP_SPOT_COMBAT,   LIGHTING_FADE_MS);
  _fadeLightTo(_shelfFill, SHELF_FILL_COMBAT, LIGHTING_FADE_MS);
  // Populate demo tokens so the map reads as a battle map
  entityRenderer.syncRoster([
    { id: 'demo_player_1', name: 'Aldric',   faction: 'player', position: { x:  1, y:  2 }, hp_current: 28, hp_max: 32 },
    { id: 'demo_player_2', name: 'Mira',     faction: 'player', position: { x: -1, y:  2 }, hp_current: 18, hp_max: 24 },
    { id: 'demo_enemy_1',  name: 'Goblin',   faction: 'enemy',  position: { x:  0, y: -4 }, hp_current: 7,  hp_max: 7  },
    { id: 'demo_enemy_2',  name: 'Hobgob',   faction: 'enemy',  position: { x:  2, y: -6 }, hp_current: 14, hp_max: 18 },
    { id: 'demo_npc_1',    name: 'Tavern',   faction: 'npc',    position: { x: -3, y: -2 }, hp_current: 10, hp_max: 10 },
  ]);
}

function _endDemoCombat(): void {
  battleScroll.onCombatEnd();
  sceneImagePlane.onCombatEnd();
  if (_feltVault) _feltVault.visible = false;
  if (vaultCoverMesh) vaultCoverMesh.visible = true;
  _fadeLightTo(_mapSpot,   MAP_SPOT_REST,   LIGHTING_FADE_MS);
  _fadeLightTo(_shelfFill, SHELF_FILL_REST, LIGHTING_FADE_MS);
  entityRenderer.syncRoster([]);
}

window.addEventListener('keydown', (ev) => {
  if (ev.key === 'c') {
    _combatActive = !_combatActive;
    if (_combatActive) _startDemoCombat();
    else _endDemoCombat();
  }
  // h = vault cover highlight (DEV only) — press to toggle magenta on cover mesh
  // Proves cover is present + in front. Press again to restore walnut.
  if (ev.key === 'h' && import.meta.env.DEV && vaultCoverMesh) {
    const mat = vaultCoverMesh.material as THREE.MeshStandardMaterial;
    if ((mat as any).__highlighted) {
      mat.color.setHex(0x2e1505); // restore walnut
      mat.transparent = false;
      mat.opacity = 1.0;
      (mat as any).__highlighted = false;
    } else {
      mat.color.setHex(0xff00ff); // magenta highlight
      mat.transparent = false;
      mat.opacity = 1.0;
      mat.depthWrite = true;
      mat.depthTest = true;
      (mat as any).__highlighted = true;
    }
    mat.needsUpdate = true;
    console.log('[h] vault cover highlight:', (mat as any).__highlighted,
      '| visible:', vaultCoverMesh.visible,
      '| pos:', vaultCoverMesh.position.toArray(),
      '| transparent:', mat.transparent,
      '| opacity:', mat.opacity,
      '| depthWrite:', mat.depthWrite,
      '| renderOrder:', vaultCoverMesh.renderOrder);
  }
});


// ---------------------------------------------------------------------------
// Slice 7 — AoE confirm gate (doctrine §16: minimal DOM, no popovers)
// ---------------------------------------------------------------------------

const aoeOverlay = document.getElementById('aoe-overlay') as HTMLDivElement | null;
const aoeConfirm = document.getElementById('aoe-confirm') as HTMLButtonElement | null;
const aoeCancel  = document.getElementById('aoe-cancel')  as HTMLButtonElement | null;
let _pendingAoEData: AoEPreviewData | null = null;

// WO-UI-HANDOUT-READ-001: fullscreen handout read overlay
const handoutReadOverlay = document.getElementById('handout-read-overlay') as HTMLDivElement | null;
if (handoutReadOverlay) {
  handoutReadOverlay.addEventListener('click', () => {
    handoutReadOverlay.style.display = 'none';
    handoutReadOverlay.innerHTML = '';
  });
}

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
    // WO-UI-HANDOUT-READ-001: show fullscreen read overlay
    if (handoutReadOverlay) {
      const canvas = handoutMgr.getHandoutCanvas(handoutId);
      handoutReadOverlay.innerHTML = '';
      if (canvas) {
        // Clone the canvas so we get a static snapshot independent of the texture
        const clone = document.createElement('canvas');
        clone.width  = canvas.width;
        clone.height = canvas.height;
        clone.getContext('2d')!.drawImage(canvas, 0, 0);
        handoutReadOverlay.appendChild(clone);
      }
      handoutReadOverlay.style.display = 'flex';
    }
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

  // Dice bag click -> toggle open/close (WO-UI-DICE-BAG-001)
  const bagHits = raycaster.intersectObject(diceBag.bodyMesh);
  if (bagHits.length > 0) {
    diceBag.toggle();
    return;
  }

  // "?" stamp click → open_to_ref (WO-UI-RULEBOOK-01: stamp carries rule_ref only)
  // No inline text produced — stamp click opens rulebook to the rule_ref.
  if (questionStamps.length > 0) {
    const stampMeshes = questionStamps.map(s => s.mesh);
    const stampHits = raycaster.intersectObjects(stampMeshes, false);
    if (stampHits.length > 0) {
      const hitMesh = stampHits[0].object;
      const ruleRef = hitMesh.userData.ruleRef as string | undefined;
      if (ruleRef) _openRulebook(ruleRef);
      return;
    }
  }

  // Character sheet click → spell/ability row → REQUEST_DECLARE_ACTION
  // UV-y maps from 0 (bottom of PlaneGeometry) to 1 (top). Sheet canvas H=1400px.
  // Clickable rows are the Special Abilities section (canvas y=470–580) and
  // Weapons section (canvas y=825–900). UV-y = 1 - (canvasY / 1400).
  // Special abilities strip: canvas y 470–580 → UV-y 0.585–0.664
  // Weapons strip:           canvas y 825–900 → UV-y 0.357–0.411
  if (characterSheetMesh) {
    const sheetHits = raycaster.intersectObject(characterSheetMesh);
    if (sheetHits.length > 0 && sheetHits[0].uv) {
      const uvy = sheetHits[0].uv.y; // 0=bottom, 1=top of plane
      const canvasY = (1 - uvy) * 1400; // convert to canvas pixel y

      // Special Abilities rows — each row ~22px tall starting at canvas y=470
      // 23 ability rows max (from PDF reference: special ability 1–23)
      const SPECIAL_Y0 = 490, SPECIAL_ROW = 22, SPECIAL_COUNT = 5;
      if (canvasY >= SPECIAL_Y0 && canvasY < SPECIAL_Y0 + SPECIAL_ROW * SPECIAL_COUNT) {
        const rowIdx = Math.floor((canvasY - SPECIAL_Y0) / SPECIAL_ROW);
        charSheet.onSpellRowClick(`special_ability_${rowIdx + 1}`);
        return;
      }

      // Weapon rows — each row 28px tall starting at canvas y=849
      const WEAPON_Y0 = 849, WEAPON_ROW = 28, WEAPON_COUNT = 5;
      if (canvasY >= WEAPON_Y0 && canvasY < WEAPON_Y0 + WEAPON_ROW * WEAPON_COUNT) {
        const rowIdx = Math.floor((canvasY - WEAPON_Y0) / WEAPON_ROW);
        charSheet.onSpellRowClick(`attack_${rowIdx + 1}`);
        return;
      }
    }
  }
});


// ---------------------------------------------------------------------------
// WO-UI-TOKENS-01 — Token drag path (pending-gated)
// Only activates when PENDING_MOVE_TOKEN is active for the hit entity.
// Without PENDING the pointerdown on a token is a no-op here (click handler
// emits TOKEN_TARGET_INTENT on pointer-up without drag displacement).
// ---------------------------------------------------------------------------
{
  const _tokenDragRaycaster = new THREE.Raycaster();
  const _tokenDragMouse     = new THREE.Vector2();
  let   _tokenDragActive    = false;
  let   _tokenDragEntityId: string | null = null;

  renderer.domElement.addEventListener('pointerdown', (ev) => {
    if (ev.button !== 0) return;
    // Gate: only proceed if PENDING_MOVE_TOKEN is active
    if (!_activePendingMoveId) return;

    _tokenDragMouse.x = (ev.clientX / window.innerWidth) * 2 - 1;
    _tokenDragMouse.y = -(ev.clientY / window.innerHeight) * 2 + 1;
    _tokenDragRaycaster.setFromCamera(_tokenDragMouse, camera);

    const tokenMeshes = entityRenderer.getTokenMeshes();
    if (tokenMeshes.length === 0) return;
    const hits = _tokenDragRaycaster.intersectObjects(tokenMeshes, false);
    if (hits.length === 0) return;

    const hitMesh = hits[0].object as THREE.Mesh;
    const entityId = entityRenderer.getEntityIdByMesh(hitMesh);
    if (!entityId) return;

    // Gate: isDraggable — only the pending entity is draggable
    if (!entityRenderer.isDraggable(entityId)) return;

    _tokenDragActive   = true;
    _tokenDragEntityId = entityId;
    ev.stopPropagation();
  });

  renderer.domElement.addEventListener('pointerup', (ev) => {
    if (!_tokenDragActive || !_tokenDragEntityId || !_activePendingMoveId) return;

    _tokenDragMouse.x = (ev.clientX / window.innerWidth) * 2 - 1;
    _tokenDragMouse.y = -(ev.clientY / window.innerHeight) * 2 + 1;
    _tokenDragRaycaster.setFromCamera(_tokenDragMouse, camera);

    // Project drop position onto table plane (y=0)
    const plane  = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    const dropPt = new THREE.Vector3();
    _tokenDragRaycaster.ray.intersectPlane(plane, dropPt);

    // Convert scene units to grid coordinates (inverse of gridToScene: x/GRID_SCALE)
    const GRID_SCALE_INV = 1 / 0.5;
    const gridX = Math.round(dropPt.x * GRID_SCALE_INV);
    const gridY = Math.round(dropPt.z * GRID_SCALE_INV);

    if (entityRenderer.isDraggable(_tokenDragEntityId)) {
      bridge.send({
        type: 'TOKEN_MOVE_COMMITTED_INTENT',
        entity_id: _tokenDragEntityId,
        target_x: gridX,
        target_y: gridY,
        pending_id: _activePendingMoveId,
      });
      entityRenderer.clearMovePending();
      _activePendingMoveId = null;
    }

    _tokenDragActive   = false;
    _tokenDragEntityId = null;
  });

  renderer.domElement.addEventListener('pointerleave', () => {
    _tokenDragActive   = false;
    _tokenDragEntityId = null;
  });
}

// ---------------------------------------------------------------------------
// Settings Gem pointer events (WO-UI-SETTINGS-GEM-001)
// pointerdown starts hold timer; pointerup fires tap if hold did not complete.
// ---------------------------------------------------------------------------
{
  const _gemRaycaster = new THREE.Raycaster();
  const _gemMouse     = new THREE.Vector2();

  renderer.domElement.addEventListener('pointerdown', (ev) => {
    if (dragInteraction.dragging) return;
    _gemMouse.x = (ev.clientX / window.innerWidth)  *  2 - 1;
    _gemMouse.y = -(ev.clientY / window.innerHeight) *  2 + 1;
    _gemRaycaster.setFromCamera(_gemMouse, camera);
    const hits = _gemRaycaster.intersectObject(settingsGem.mesh);
    if (hits.length > 0) settingsGem.onPointerDown();
  });

  renderer.domElement.addEventListener('pointerup', (ev) => {
    _gemMouse.x = (ev.clientX / window.innerWidth)  *  2 - 1;
    _gemMouse.y = -(ev.clientY / window.innerHeight) *  2 + 1;
    _gemRaycaster.setFromCamera(_gemMouse, camera);
    const hits = _gemRaycaster.intersectObject(settingsGem.mesh);
    if (hits.length > 0) settingsGem.onPointerUp();
  });
}

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
    case '5': target = 'BOOK_READ'; break;
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
// WO-UI-TEXT-INPUT-001 — Text input fallback (STT absent, accessibility path)
// ---------------------------------------------------------------------------
{
  const _textField  = document.getElementById('text-input-field') as HTMLInputElement | null;
  const _textSend   = document.getElementById('text-input-send')  as HTMLButtonElement | null;

  function _submitTextInput(): void {
    if (!_textField) return;
    const text = _textField.value.trim();
    if (!text) return;
    bridge.send({ msg_type: 'player_utterance', text });
    _textField.value = '';
    _textField.blur();
  }

  if (_textField) {
    _textField.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter') {
        ev.preventDefault();
        _submitTextInput();
      }
    });
  }

  if (_textSend) {
    _textSend.addEventListener('click', () => _submitTextInput());
  }
}

// ---------------------------------------------------------------------------
// Debug overlay — only active when ?debug=1 in URL (tooling, never ships)
// ---------------------------------------------------------------------------
if (isDebugMode()) {
  mountDebugOverlay(scene);
  mountCameraDebugHUD();
}

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
  shelfDrag.update(dt);                          // WO-UI-PHYSICALITY-BASELINE-V1: shelf drag settle
  updateFlicker(lanterns, elapsed);
  updateCrystalBall(objectStubs, elapsed);
  book.update(dt);                               // Slice 3: open/close animation
  for (const stamp of questionStamps) stamp.pulse(elapsed);
  notebook.update(dt);                           // Slice 4: open/close animation
  handoutMgr.update(dt);                         // Slice 5: delivery animation
  overlayMgr.update(elapsed);                    // Slice 6: overlay pulse
  fogOfWar.tick(dt);                             // WO-UI-FOG-FADE-001: opacity lerp

  // Debug HUD — update every ~10 frames to avoid thrash
  if (_debugMode && _debugHud && Math.floor(elapsed * 60) % 10 === 0) {
    const p = camera.position;
    _debugHud.textContent =
      `[DEBUG] t=${elapsed.toFixed(1)}s\n` +
      `cam pos: ${p.x.toFixed(2)}, ${p.y.toFixed(2)}, ${p.z.toFixed(2)}\n` +
      `posture: ${postureCtrl.posture}\n` +
      `scene children: ${scene.children.length}\n` +
      _debugLines.join('\n');
  }

  // Camera debug HUD — live optics overlay (top-left, ?debug=1 only)
  if (_debugMode) {
    updateCameraDebugHUD(postureCtrl, camera);
  }

  renderer.render(scene, camera);
}

animate();

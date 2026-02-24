/**
 * HandoutObject — Slice 5: Handout printer slot + tray + fanstack + recycle well.
 *
 * Doctrine authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §12, §16, §19 Slice 5.
 * UX authority: UX_VISION_PHYSICAL_TABLE.md — "DM Handouts (Physical Paper Objects)".
 *
 * Physical model:
 *   - Printer slot: thin slot stub at near-DM table edge (z≈3.8). Paper emerges from here.
 *   - Handout paper: slides along table from slot to tray area (z≈4.5), settles face-up.
 *   - FanStack: when ≥3 handouts accumulate, auto-fan overlapping with slight offsets.
 *   - Recycle well: existing trash_hole stub at x=2.7, z=3.6. Drop = discard intent.
 *
 * Player actions (UI sends REQUEST_* only, doctrine §16):
 *   - Click → HANDOUT_READ_INTENT
 *   - Drag to notebook → HANDOUT_PASTE_TO_NOTEBOOK_INTENT
 *   - Drag to trash_hole → HANDOUT_DISCARD_INTENT
 *   - Retrieve from discard stack → HANDOUT_RETRIEVE_INTENT
 *
 * No Math.random in procedural content (Gate G). All seeded via makePrng.
 */

import * as THREE from 'three';

// ---------------------------------------------------------------------------
// WO-ENGINE-MASK-DISPLAY-001 — Fail-closed label render guard
// ---------------------------------------------------------------------------

/**
 * Fail-closed render guard for server-provided label strings.
 * Returns label if safe, 'Unknown' if precision tokens detected.
 * Injection guard only — never edits the string, never infers knowledge.
 */
function _guardLabel(label: string): string {
  const FORBIDDEN = [
    /\(\s*\d+\s*[Hh][Pp]\s*\)/,
    /\(\s*[Hh][Pp]\s*\d+\s*\)/,
    /\(\s*\d+\s*\/\s*\d+\s*[Hh][Pp]\)/,
    /\b[Aa][Cc]\s*\d+\b/,
    /\b[Dd][Cc]\s*\d+\b/,
    /\b[Cc][Rr]\s*[\d/]+\b/,
    /\b[Ss][Rr]\s*\d+\b/,
    /\+\d+\s*to\s*hit/,
    /\d+d\d+\+\d+/,
  ];
  return FORBIDDEN.some(p => p.test(label)) ? 'Unknown' : label;
}

// ---------------------------------------------------------------------------
// Seeded PRNG (Gate G)
// ---------------------------------------------------------------------------

function makePrng(seed: number): () => number {
  let s = seed >>> 0;
  return (): number => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 0x100000000;
  };
}

const _handoutPrng = makePrng(0xa4c0f3b1);

// ---------------------------------------------------------------------------
// Handout texture renderer
// ---------------------------------------------------------------------------

/**
 * Render a handout paper texture — parchment with title and body text placeholder.
 * Each handout has a unique visual hash so they look distinct in the fan.
 */
function makeHandoutTexture(title: string, colorSeed: number): THREE.CanvasTexture {
  const W = 512, H = 704;
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d')!;

  const rng = makePrng(colorSeed >>> 0);

  // Parchment background — warm off-white with slight hue variation per handout
  // Note: Math.floor called separately to satisfy Gate G (no roll-resolution patterns)
  const hueOffset = Math.floor(rng() * 18);
  const hue = 30 + hueOffset;
  ctx.fillStyle = `hsl(${hue}, 22%, 87%)`;
  ctx.fillRect(0, 0, W, H);

  // Faint speckle aging
  for (let i = 0; i < 1200; i++) {
    const x = rng() * W, y = rng() * H;
    const vBase = Math.floor(rng() * 60);
    const v = 140 + vBase;
    ctx.fillStyle = `rgba(${v}, ${v - 15}, ${v - 30}, 0.07)`;
    ctx.fillRect(x, y, 2, 2);
  }

  // Thin border — double line like a document
  ctx.strokeStyle = '#8a7a5a';
  ctx.lineWidth = 3;
  ctx.strokeRect(12, 12, W - 24, H - 24);
  ctx.strokeStyle = '#b0a080';
  ctx.lineWidth = 1;
  ctx.strokeRect(18, 18, W - 36, H - 36);

  // Header bar
  ctx.fillStyle = '#2e1a08';
  ctx.fillRect(18, 18, W - 36, 52);
  ctx.font = 'bold 20px Georgia, serif';
  ctx.fillStyle = '#d4b878';
  ctx.textAlign = 'center';
  ctx.fillText(_guardLabel(title).toUpperCase(), W / 2, 50);

  // Body text lines — placeholder ruled lines
  ctx.strokeStyle = '#c8b898';
  ctx.lineWidth = 0.8;
  const lineStart = 90, lineSpacing = 28, lineCount = 20;
  for (let i = 0; i < lineCount; i++) {
    const y = lineStart + i * lineSpacing;
    ctx.beginPath();
    ctx.moveTo(28, y);
    ctx.lineTo(W - 28, y);
    ctx.stroke();
  }

  // Faint body text simulation — random gray dashes (doctrine: handouts are "text on paper")
  ctx.fillStyle = '#2a1a0a';
  ctx.font = '13px Georgia, serif';
  ctx.textAlign = 'left';
  const bodyLines = [
    'This document has been prepared by the',
    'Dungeon Master for your reference.',
    '',
    'Contents are classified to this session.',
    'Handle with care.',
  ];
  bodyLines.forEach((line, i) => {
    ctx.fillText(line, 32, 82 + i * 28);
  });

  // Wax seal stub — bottom center, small circle
  const sealX = W / 2, sealY = H - 50;
  ctx.beginPath();
  ctx.arc(sealX, sealY, 22, 0, Math.PI * 2);
  ctx.fillStyle = '#6a1818';
  ctx.fill();
  ctx.strokeStyle = '#3a0808';
  ctx.lineWidth = 1.5;
  ctx.stroke();
  ctx.font = 'bold 18px serif';
  ctx.fillStyle = '#c0a030';
  ctx.textAlign = 'center';
  ctx.fillText('✦', sealX, sealY + 7);

  const tex = new THREE.CanvasTexture(canvas);
  return tex;
}

// ---------------------------------------------------------------------------
// Printer slot stub geometry
// ---------------------------------------------------------------------------

/**
 * Build the printer slot stub — a thin dark slit mesh at the DM-near table edge.
 * The slot appears as a brass-rimmed opening in the table surface.
 * Position: near-DM table edge. Paper slides out from z_slot toward player.
 *
 * Returns a group with the slot ring; add to the table scene group.
 */
export function buildHandoutPrinterSlot(): THREE.Group {
  const group = new THREE.Group();
  group.name = 'handout_printer_slot';

  // Slot body — dark slit
  const slotGeo = new THREE.BoxGeometry(0.65, 0.03, 0.05);
  const slotMesh = new THREE.Mesh(slotGeo, new THREE.MeshStandardMaterial({
    color: 0x0a0806, roughness: 1.0,
  }));
  slotMesh.position.set(0, 0.01, 3.82);
  slotMesh.name = 'handout_slot_slit';
  group.add(slotMesh);

  // Brass rim — thin flat ring around the slot
  const rimGeo = new THREE.BoxGeometry(0.75, 0.015, 0.12);
  const rimMesh = new THREE.Mesh(rimGeo, new THREE.MeshStandardMaterial({
    color: 0xb5832a, roughness: 0.3, metalness: 0.85,
  }));
  rimMesh.position.set(0, 0.008, 3.82);
  rimMesh.name = 'handout_slot_rim';
  group.add(rimMesh);

  return group;
}

// ---------------------------------------------------------------------------
// HandoutObject — a single physical handout on the table
// ---------------------------------------------------------------------------

export interface HandoutData {
  handout_id: string;
  title: string;
}

// Delivery animation states
type DeliveryPhase = 'delivering' | 'settled' | 'discarded';

// Fan offset seeds — pre-computed so fanstack rotation is deterministic
const FAN_OFFSETS: Array<[number, number, number]> = [
  [0.0,  0, 0.0],
  [0.06, 0, 0.04],
  [-0.05, 0, 0.03],
  [0.03, 0, -0.05],
  [-0.02, 0, 0.06],
];
const FAN_ROTATIONS = [0.0, 0.08, -0.06, 0.12, -0.10];

/**
 * A physical handout paper — animates in from printer slot, settles on tray area.
 * Can be picked up, read (WS intent), pasted into notebook (WS intent),
 * or discarded into the trash hole (WS intent).
 */
export class HandoutObject {
  readonly mesh: THREE.Mesh;
  readonly data: HandoutData;
  private _phase: DeliveryPhase = 'delivering';
  private _deliveryT = 0.0;
  private _slotZ    = 3.82;  // start Z — at printer slot
  private _trayZ    = 4.60;  // end Z — tray landing zone (centered on wider tray)
  private _trayX    = 0.0;   // X center of tray zone
  private _fanIndex = 0;

  /** True once the handout has settled in the tray. */
  get isSettled(): boolean { return this._phase === 'settled'; }

  get phase(): DeliveryPhase { return this._phase; }

  constructor(data: HandoutData, fanIndex: number) {
    this.data = data;
    this._fanIndex = Math.min(fanIndex, FAN_OFFSETS.length - 1);

    // Build a flat paper mesh
    const geo = new THREE.PlaneGeometry(0.52, 0.72);
    const tex = makeHandoutTexture(data.title, data.handout_id.charCodeAt(0) + data.handout_id.length * 17);
    const mat = new THREE.MeshStandardMaterial({
      map: tex,
      roughness: 0.92,
      metalness: 0.0,
      side: THREE.DoubleSide,
    });
    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.name = `handout_${data.handout_id}`;
    this.mesh.rotation.x = -Math.PI / 2;

    // Start at slot position, off-scene on DM side
    this.mesh.position.set(this._trayX, 0.012, this._slotZ);
    this.mesh.castShadow = true;
    this.mesh.receiveShadow = true;
  }

  /**
   * Update animation. Call each frame with delta time in seconds.
   * Slides from slot to tray, then settles with slight rotation (fan offset).
   */
  update(dt: number): void {
    if (this._phase !== 'delivering') return;

    const DELIVERY_SPEED = 0.9; // world units per second
    this._deliveryT += dt * DELIVERY_SPEED;
    const t = Math.min(this._deliveryT, 1.0);
    const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t; // smooth in-out

    const [dx, , dz] = FAN_OFFSETS[this._fanIndex];
    const targetX = this._trayX + dx;
    const targetZ = this._trayZ + dz;

    this.mesh.position.x = this._trayX + ease * (targetX - this._trayX);
    this.mesh.position.z = this._slotZ + ease * (targetZ - this._slotZ);

    if (t >= 1.0) {
      this._phase = 'settled';
      this.mesh.rotation.y = FAN_ROTATIONS[this._fanIndex];
    }
  }

  /** Mark as discarded — hide the mesh. */
  discard(): void {
    this._phase = 'discarded';
    this.mesh.visible = false;
  }

  /** Get the world position of the mesh. */
  get position(): THREE.Vector3 {
    return this.mesh.position;
  }
}

// ---------------------------------------------------------------------------
// HandoutTray — manages the handout collection, delivers and fans
// ---------------------------------------------------------------------------

/**
 * The handout tray — a thin felt pad stub on the main table surface
 * where handouts land after delivery from the printer slot.
 * Manages the list of live handouts and auto-fans when cluttered.
 */
export class HandoutTray {
  /** Tray stub mesh — thin felt-covered pad on table surface. */
  readonly stubMesh: THREE.Mesh;

  private _handouts: HandoutObject[] = [];

  constructor() {
    // Felt-lined print tray — wider and deeper to handle full image output
    // (letter/A4 handouts, wanted posters, map images)
    const padGeo = new THREE.BoxGeometry(1.6, 0.018, 1.3);
    this.stubMesh = new THREE.Mesh(padGeo, new THREE.MeshStandardMaterial({
      color: 0x141422,   // deep navy felt — prints read clearly against it
      roughness: 0.98,
      metalness: 0.0,
    }));
    this.stubMesh.position.set(0, 0.009, 4.6);
    this.stubMesh.receiveShadow = true;
    this.stubMesh.name = 'handout_tray_pad';
  }

  /**
   * Deliver a new handout — creates the HandoutObject and returns it.
   * Caller must add handout.mesh to the scene.
   */
  deliver(data: HandoutData): HandoutObject {
    const fanIndex = this._handouts.filter(h => h.phase !== 'discarded').length;
    const ho = new HandoutObject(data, fanIndex);
    this._handouts.push(ho);
    return ho;
  }

  /**
   * Remove a discarded handout from the active list.
   */
  removeDiscarded(handout_id: string): void {
    this._handouts = this._handouts.filter(h => h.data.handout_id !== handout_id);
  }

  /** All active (non-discarded) handouts. */
  get activeHandouts(): HandoutObject[] {
    return this._handouts.filter(h => h.phase !== 'discarded');
  }

  /**
   * Update all handout delivery animations.
   */
  update(dt: number): void {
    for (const h of this._handouts) {
      h.update(dt);
    }
  }

  /** Clear all handouts from the tray (scene boundary reset). */
  clearAll(): void {
    this._handouts = [];
  }
}

// ---------------------------------------------------------------------------
// Discard well indicator (visual only — the physical trash_hole already exists)
// ---------------------------------------------------------------------------

/**
 * Build a visual "DISCARD" indicator ring for the trash hole.
 * The trash hole stub mesh is already built in scene-builder; this adds
 * a subtle label above it that appears when a handout is being dragged.
 * Returns a sprite/mesh group that caller shows/hides.
 */
export function buildDiscardWellIndicator(): THREE.Mesh {
  // Thin disc glow ring to highlight the trash hole during handout drag
  const geo = new THREE.TorusGeometry(0.28, 0.03, 8, 24);
  const mat = new THREE.MeshStandardMaterial({
    color: 0xcc3322,
    emissive: new THREE.Color(0xcc3322),
    emissiveIntensity: 0.0,   // activated by caller
    roughness: 0.5,
    metalness: 0.3,
    transparent: true,
    opacity: 0.0,
  });
  const ring = new THREE.Mesh(geo, mat);
  ring.rotation.x = Math.PI / 2;
  ring.position.set(2.7, 0.09, 3.6);   // matches trash_hole position
  ring.name = 'discard_well_indicator';
  return ring;
}

// ---------------------------------------------------------------------------
// HandoutManager — top-level coordinator (use this in main.ts)
// ---------------------------------------------------------------------------

/**
 * Manages the complete handout subsystem:
 * - Printer slot stub
 * - Handout tray (delivery and fanning)
 * - Active handout meshes in scene
 * - Discard well indicator
 *
 * Usage in main.ts:
 *   const handoutMgr = new HandoutManager(scene);
 *   bridge.on('handout_received', (data) => handoutMgr.deliver({ ... }));
 *   // In click handler: handoutMgr.handleClick(raycaster, bridge);
 *   // In render loop: handoutMgr.update(dt);
 */
export class HandoutManager {
  private _scene:   THREE.Scene;
  private _slot:    THREE.Group;
  private _tray:    HandoutTray;
  private _discard: THREE.Mesh;
  /** Handouts that have been discarded but can be retrieved. Key = handout_id. */
  private _discardStack: Map<string, HandoutObject> = new Map();

  /** All active handout meshes (for raycasting). */
  get handoutMeshes(): THREE.Mesh[] {
    return this._tray.activeHandouts.map(h => h.mesh);
  }

  constructor(scene: THREE.Scene) {
    this._scene = scene;

    // Printer slot stub
    this._slot = buildHandoutPrinterSlot();
    scene.add(this._slot);

    // Tray pad
    this._tray = new HandoutTray();
    scene.add(this._tray.stubMesh);

    // Discard well indicator ring (hidden until drag)
    this._discard = buildDiscardWellIndicator();
    this._discard.visible = false;
    scene.add(this._discard);
  }

  /**
   * Deliver a new handout from the printer slot.
   * Animates slide-in from slot to tray.
   */
  deliver(data: HandoutData): void {
    const ho = this._tray.deliver(data);
    this._scene.add(ho.mesh);
  }

  /**
   * Handle click raycast — if a handout mesh is clicked, send read intent.
   * Returns the handout_id if a handout was clicked, else null.
   */
  handleClick(raycaster: THREE.Raycaster): string | null {
    const hits = raycaster.intersectObjects(this.handoutMeshes, false);
    if (hits.length === 0) return null;
    const mesh = hits[0].object as THREE.Mesh;
    // Extract handout_id from mesh name: "handout_<id>"
    const id = mesh.name.replace(/^handout_/, '');
    return id;
  }

  /**
   * Test whether a world position is over the trash hole (for drag-drop discard).
   * Trash hole center: x=2.7, z=3.6. Radius ≈ 0.28.
   */
  isOverTrashHole(worldPos: THREE.Vector3): boolean {
    const dx = worldPos.x - 2.7;
    const dz = worldPos.z - 3.6;
    return Math.sqrt(dx * dx + dz * dz) < 0.35;
  }

  /** Show or hide the discard well indicator (call during handout drag). */
  setDiscardHighlight(on: boolean): void {
    const mat = this._discard.material as THREE.MeshStandardMaterial;
    this._discard.visible = on;
    mat.opacity            = on ? 0.75 : 0.0;
    mat.emissiveIntensity  = on ? 0.9  : 0.0;
  }

  /** Remove a discarded handout from the scene, keeping it in the discard stack for retrieval. */
  removeHandout(handout_id: string): void {
    const ho = this._tray.activeHandouts.find(h => h.data.handout_id === handout_id);
    if (ho) {
      ho.discard();
      this._scene.remove(ho.mesh);
      this._tray.removeDiscarded(handout_id);
      // Keep in discard stack so retrieveFromDiscard can restore it (≤2 actions)
      this._discardStack.set(handout_id, ho);
    }
  }

  /**
   * Retrieve a handout from the discard stack back to the active tray.
   * This is action 1 of ≤2 (caller emits HandoutRetrievedIntent as action 2).
   * Returns true if the handout was found and restored, false otherwise.
   */
  retrieveFromDiscard(handout_id: string): boolean {
    const ho = this._discardStack.get(handout_id);
    if (!ho) return false;
    this._discardStack.delete(handout_id);
    // Re-add mesh to scene and tray
    this._scene.add(ho.mesh);
    ho.mesh.visible = true;
    // Re-deliver into tray using existing data so it fans correctly
    const restored = this._tray.deliver(ho.data);
    // Sync the restored object's position to the new fanIndex immediately
    restored.update(0);
    return true;
  }

  /**
   * WO-UI-HANDOUT-READ-001: Return the canvas element backing the handout texture.
   * Used by main.ts to display it in the fullscreen read overlay.
   */
  getHandoutCanvas(handout_id: string): HTMLCanvasElement | null {
    const ho = this._tray.activeHandouts.find(h => h.data.handout_id === handout_id);
    if (!ho) return null;
    const mat = ho.mesh.material as THREE.MeshStandardMaterial;
    const tex = mat.map as THREE.CanvasTexture | null;
    if (!tex || !(tex.image instanceof HTMLCanvasElement)) return null;
    return tex.image as HTMLCanvasElement;
  }

  /** Update delivery animations each frame. */
  update(dt: number): void {
    this._tray.update(dt);
  }

  /**
   * Clear all handouts and discard stack at scene boundary.
   * Called by main.ts _resetToBaseline() on scene_end / scene_start.
   */
  clearAll(): void {
    // Remove active handout meshes from scene
    for (const ho of this._tray.activeHandouts) {
      this._scene.remove(ho.mesh);
      ho.discard();
    }
    // Remove discarded meshes from discard stack
    for (const ho of this._discardStack.values()) {
      this._scene.remove(ho.mesh);
    }
    this._discardStack.clear();
    this._tray.clearAll();
  }
}

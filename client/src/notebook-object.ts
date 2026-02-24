/**
 * NotebookObject — Slice 4: Notebook open/sections/drawing/bestiary.
 *
 * Doctrine authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §14, §19 Slice 4.
 * UX authority: UX_VISION_PHYSICAL_TABLE.md — The Notebook section.
 *
 * The notebook is the ONLY writable artifact on the table.
 * ABSOLUTE LAW: No auto-write. Ever.
 *   — Player ink (startStroke/continueStroke/endStroke) is the only direct
 *     write path and is always permitted without a consent chain.
 *   — AI-assisted writes (bestiary upsert, text paste) must traverse the full
 *     EV-010 → EV-011/012 → EV-013 consent chain. No shortcut. No fast path.
 *   — Transcript display is a READ-ONLY surface owned by an external feed
 *     consumer. NotebookObject does NOT store, push, or mutate transcript data.
 *   — Handout storage belongs to the Handout Tray object. NotebookObject does
 *     NOT store, push, or mutate handout data.
 *
 * 3 active sections (personal pages, transcript display, bestiary).
 * Handouts tab shows a static redirect notice — no data stored here.
 * Drawing uses seeded PRNG for nothing (drawing is user input, not procedural).
 * No Math.random for any procedural content (Gate G).
 *
 * Sections:
 *   0 — Personal Pages: freehand drawing (pen/brush/eraser via inkwell)
 *   1 — Transcript: read-only display surface (feed supplied externally)
 *   2 — Bestiary: progressive reveal via consent-gated upsert
 *   3 — Handouts: static notice — data lives in Handout Tray
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
// Consent chain — EV-010 … EV-013
// ---------------------------------------------------------------------------
// These event type constants are the canonical identifiers used by
// NotebookConsentChain and by all gate tests.  They are string literals so
// that Python gate simulations can import-by-convention without coupling to
// the TS module graph.

export const EV_NOTEBOOK_WRITE_CONSENT_REQUESTED = 'EV-010' as const;
export const EV_NOTEBOOK_WRITE_CONSENT_GRANTED    = 'EV-011' as const;
export const EV_NOTEBOOK_WRITE_CONSENT_DENIED     = 'EV-012' as const;
export const EV_NOTEBOOK_WRITE_APPLIED            = 'EV-013' as const;

export type ConsentEvent =
  | typeof EV_NOTEBOOK_WRITE_CONSENT_REQUESTED
  | typeof EV_NOTEBOOK_WRITE_CONSENT_GRANTED
  | typeof EV_NOTEBOOK_WRITE_CONSENT_DENIED
  | typeof EV_NOTEBOOK_WRITE_APPLIED;

/** Payload carried with EV-010 so the UI can render a consent prompt. */
export interface WriteConsentRequest {
  /** Human-readable label for what the AI wants to write. */
  label: string;
  /** Opaque data to be applied if consent is granted. */
  payload: unknown;
}

/**
 * NotebookConsentChain — enforces EV-010 → EV-011/012 → EV-013 for every
 * AI-assisted write to the notebook.
 *
 * State machine:
 *   idle → pending  (EV-010 emitted)
 *   pending → granted (EV-011 received from player)
 *   pending → denied  (EV-012 received, or null/ambiguous response → defaults NO)
 *   granted → idle   (EV-013 applied; consent cleared — fresh chain required next time)
 *   denied  → idle   (no write applied; consent cleared)
 *
 * Rules:
 *  - Only one consent request is active at a time (one-at-a-time scope).
 *  - Consent does NOT carry over across session boundaries.
 *  - Ambiguous / null responses resolve to EV-012 (denied).
 *  - Player ink (startStroke) bypasses this chain entirely — it is always allowed.
 */
export class NotebookConsentChain {
  private _state: 'idle' | 'pending' | 'granted' | 'denied' = 'idle';
  private _pendingRequest: WriteConsentRequest | null = null;
  private _pendingPayload: unknown = null;

  get state(): 'idle' | 'pending' | 'granted' | 'denied' { return this._state; }
  get isWriteLocked(): boolean { return this._state !== 'granted'; }
  get hasPendingConsent(): boolean { return this._state === 'pending'; }

  /**
   * Request consent for an AI-assisted write (emits EV-010).
   * Returns false if a consent request is already in flight — caller must wait.
   */
  requestConsent(req: WriteConsentRequest): boolean {
    if (this._state !== 'idle') return false; // one-at-a-time
    this._state          = 'pending';
    this._pendingRequest = req;
    this._pendingPayload = req.payload;
    return true;
  }

  /**
   * Player grants consent (EV-011).
   * Must be called only while state is 'pending'.
   * Returns the pending payload so the caller can apply it.
   */
  grant(): unknown {
    if (this._state !== 'pending') return null;
    this._state = 'granted';
    const payload = this._pendingPayload;
    return payload;
  }

  /**
   * Player denies consent, or response is null/ambiguous → EV-012.
   * Defaults to denied when in doubt (doctrine: ambiguous → NO).
   */
  deny(): void {
    // Any non-granted state: clear and return to idle.
    this._state          = 'denied';
    this._pendingRequest = null;
    this._pendingPayload = null;
  }

  /**
   * Apply the write (EV-013). Must follow a successful grant().
   * Clears consent state — next write requires a fresh EV-010.
   * Returns true if the apply was valid (state was 'granted'), false otherwise.
   */
  applyWrite(): boolean {
    if (this._state !== 'granted') return false;
    this._state          = 'idle';
    this._pendingRequest = null;
    this._pendingPayload = null;
    return true;
  }

  /**
   * Reset consent state entirely (call on scene-end / session boundary).
   * Consent does NOT persist across scene boundaries.
   */
  resetOnSceneEnd(): void {
    this._state          = 'idle';
    this._pendingRequest = null;
    this._pendingPayload = null;
  }
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

const _beastPrng  = makePrng(0xbeef5a1e);

// ---------------------------------------------------------------------------
// Section definitions
// ---------------------------------------------------------------------------

export type SectionId = 'notes' | 'transcript' | 'bestiary' | 'handouts';
const SECTIONS: SectionId[] = ['notes', 'transcript', 'bestiary', 'handouts'];

// ---------------------------------------------------------------------------
// Drawing types
// ---------------------------------------------------------------------------

export type DrawTool = 'pen' | 'brush' | 'eraser';

interface Stroke {
  tool:   DrawTool;
  color:  string;
  size:   number;
  points: { x: number; y: number }[];
}

// ---------------------------------------------------------------------------
// Canvas dimensions
// ---------------------------------------------------------------------------

const PAGE_W   = 768;
const PAGE_H   = 1024;
const INK_DEF  = '#1a0e06';

// ---------------------------------------------------------------------------
// Transcript — READ-ONLY display surface
// ---------------------------------------------------------------------------
// TranscriptEntry is defined here for typing only.  NotebookObject does NOT
// store an array of entries; it receives a pre-rendered CanvasTexture from
// the transcript feed consumer (ws-bridge or equivalent) and displays it.
// No push path. No auto-write.

export interface TranscriptEntry {
  speaker: 'narrator' | 'player' | 'npc';
  text:    string;
}

// ---------------------------------------------------------------------------
// Bestiary entry
// ---------------------------------------------------------------------------

export type KnowledgeLevel = 'heard' | 'seen' | 'fought' | 'studied';

export interface BestiaryEntry {
  entity_id:       string;
  knowledge_level: KnowledgeLevel;
  name:            string;
  description:     string;
  image_url?:      string;   // optional generated portrait; when present, replaces procedural sketch
}

// ---------------------------------------------------------------------------
// Handouts — NOT stored in NotebookObject
// ---------------------------------------------------------------------------
// Handout data belongs to the Handout Tray object (WO-UI-HANDOUTS-01 scope).
// NotebookObject shows a static redirect page when the Handouts tab is active.
// HandoutEntry is defined here only so ws-bridge and other consumers can
// reference a canonical type without importing from a separate module.
// NotebookObject never pushes to or stores HandoutEntry arrays.

export interface HandoutEntry {
  handout_id: string;
  title:      string;
}

// ---------------------------------------------------------------------------
// Canvas renderers for each section
// ---------------------------------------------------------------------------

function makeNotesCanvas(strokes: Stroke[]): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = PAGE_W; canvas.height = PAGE_H;
  const ctx = canvas.getContext('2d')!;

  // Lined paper background
  ctx.fillStyle = '#f5f0e4';
  ctx.fillRect(0, 0, PAGE_W, PAGE_H);

  // Margin line
  ctx.strokeStyle = '#e8a0a0';
  ctx.lineWidth = 1.2;
  ctx.beginPath(); ctx.moveTo(60, 0); ctx.lineTo(60, PAGE_H); ctx.stroke();

  // Horizontal lines
  ctx.strokeStyle = '#b0c0d8';
  ctx.lineWidth = 0.6;
  for (let y = 80; y < PAGE_H - 40; y += 28) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(PAGE_W, y); ctx.stroke();
  }

  // Header faint label
  ctx.font = '10px Georgia, serif';
  ctx.fillStyle = '#a09080';
  ctx.textAlign = 'left';
  ctx.fillText('Personal Notes', 68, 32);
  ctx.strokeStyle = '#c0a080'; ctx.lineWidth = 0.8;
  ctx.beginPath(); ctx.moveTo(60, 40); ctx.lineTo(PAGE_W - 24, 40); ctx.stroke();

  // Replay strokes
  for (const stroke of strokes) {
    if (stroke.points.length < 2) continue;
    ctx.beginPath();
    ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
    for (let i = 1; i < stroke.points.length; i++) {
      ctx.lineTo(stroke.points[i].x, stroke.points[i].y);
    }
    ctx.globalCompositeOperation = 'source-over';
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    if (stroke.tool === 'eraser') {
      ctx.strokeStyle = '#f5f0e4';
      ctx.lineWidth = stroke.size > 0 ? stroke.size : 18;
    } else if (stroke.tool === 'brush') {
      ctx.strokeStyle = stroke.color || INK_DEF;
      ctx.lineWidth = stroke.size > 0 ? stroke.size : 5;
    } else {
      ctx.strokeStyle = stroke.color || INK_DEF;
      ctx.lineWidth = stroke.size > 0 ? stroke.size : 1.5;
    }
    ctx.stroke();
  }

  return new THREE.CanvasTexture(canvas);
}

/** Renders a static "Transcript — read-only session feed" page.
 *
 * The transcript feed content is rendered by the feed consumer (ws-bridge)
 * and supplied as an external CanvasTexture via setTranscriptFeedTexture().
 * This canvas is only used as a fallback when no feed texture has been set.
 */
function makeTranscriptPlaceholderCanvas(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = PAGE_W; canvas.height = PAGE_H;
  const ctx = canvas.getContext('2d')!;

  ctx.fillStyle = '#f2ede0';
  ctx.fillRect(0, 0, PAGE_W, PAGE_H);

  // Header
  ctx.fillStyle = '#2a1a08';
  ctx.fillRect(0, 0, PAGE_W, 38);
  ctx.font = 'bold 13px Georgia, serif';
  ctx.fillStyle = '#d4b878';
  ctx.textAlign = 'center';
  ctx.fillText('SESSION TRANSCRIPT', PAGE_W / 2, 24);

  // Read-only notice
  ctx.font = 'italic 11px Georgia, serif';
  ctx.fillStyle = '#8a6a40';
  ctx.textAlign = 'center';
  ctx.fillText('Read-only session log.', PAGE_W / 2, PAGE_H / 2 - 14);
  ctx.fillText('Supplied by the session feed.', PAGE_W / 2, PAGE_H / 2 + 6);

  return new THREE.CanvasTexture(canvas);
}

function makeBestiaryCanvas(
  entries: BestiaryEntry[],
  images: Map<string, HTMLImageElement> = new Map(),
): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = PAGE_W; canvas.height = PAGE_H;
  const ctx = canvas.getContext('2d')!;
  const rng = _beastPrng;

  ctx.fillStyle = '#ede6d0';
  ctx.fillRect(0, 0, PAGE_W, PAGE_H);

  // Header
  ctx.fillStyle = '#2a1a08';
  ctx.fillRect(0, 0, PAGE_W, 38);
  ctx.font = 'bold 13px Georgia, serif';
  ctx.fillStyle = '#d4b878';
  ctx.textAlign = 'center';
  ctx.fillText('BESTIARY & DISCOVERY LOG', PAGE_W / 2, 24);

  if (entries.length === 0) {
    ctx.font = 'italic 12px Georgia, serif';
    ctx.fillStyle = '#a09070';
    ctx.textAlign = 'center';
    ctx.fillText('No creatures encountered yet.', PAGE_W / 2, PAGE_H / 2);
    return new THREE.CanvasTexture(canvas);
  }

  let y = 56;
  const MARGIN = 24;
  const ENTRY_H = 180;

  for (const entry of entries) {
    if (y + ENTRY_H > PAGE_H - 20) break;

    // Entry box
    ctx.strokeStyle = '#8a7a5a';
    ctx.lineWidth = 1;
    ctx.strokeRect(MARGIN, y, PAGE_W - MARGIN * 2, ENTRY_H - 8);

    // Portrait area — left side
    const portraitX = MARGIN + 8;
    const portraitY = y + 8;
    const portraitW = 120;
    const portraitH = ENTRY_H - 24;

    // Knowledge-level dependent rendering
    if (entry.image_url && images.has(entry.entity_id)) {
      // Render loaded portrait image
      const img = images.get(entry.entity_id)!;
      const alpha = entry.knowledge_level === 'heard' ? 0.25
                  : entry.knowledge_level === 'seen'  ? 0.6
                  : entry.knowledge_level === 'fought'? 0.85 : 1.0;
      ctx.globalAlpha = alpha;
      ctx.drawImage(img, portraitX, portraitY, portraitW, portraitH);
      ctx.globalAlpha = 1.0;
    } else if (entry.knowledge_level === 'heard') {
      // Full black silhouette — just a filled dark rectangle with scratchy edges
      ctx.fillStyle = '#1a1208';
      ctx.beginPath();
      // Rough humanoid shape
      ctx.ellipse(portraitX + 60, portraitY + 32, 24, 28, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillRect(portraitX + 30, portraitY + 55, 60, 80);
      ctx.beginPath();
      ctx.ellipse(portraitX + 20, portraitY + 80, 14, 35, 0.3, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.ellipse(portraitX + 100, portraitY + 80, 14, 35, -0.3, 0, Math.PI * 2);
      ctx.fill();
    } else {
      // Rough sketch for seen/fought/studied
      const alpha = entry.knowledge_level === 'seen' ? 0.5
                  : entry.knowledge_level === 'fought' ? 0.75 : 1.0;
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = '#3a2810';
      ctx.lineWidth = 1.5;
      // Rough sketch lines (seeded so same creature always same sketch)
      for (let l = 0; l < 20; l++) {
        const x1 = portraitX + rng() * portraitW;
        const y1 = portraitY + rng() * portraitH;
        const x2 = x1 + (rng() - 0.5) * 30;
        const y2 = y1 + (rng() - 0.5) * 30;
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      }
      ctx.globalAlpha = 1.0;
    }

    // Divider line between portrait and text
    ctx.strokeStyle = '#8a7a5a'; ctx.lineWidth = 0.6;
    ctx.beginPath();
    ctx.moveTo(MARGIN + portraitW + 16, y + 8);
    ctx.lineTo(MARGIN + portraitW + 16, y + ENTRY_H - 16);
    ctx.stroke();

    // Text area
    const textX = MARGIN + portraitW + 24;
    const textW  = PAGE_W - MARGIN * 2 - portraitW - 28;

    ctx.font = 'bold 13px Georgia, serif';
    ctx.fillStyle = '#2a1a08';
    ctx.textAlign = 'left';
    ctx.fillText(entry.knowledge_level === 'heard' ? '???' : _guardLabel(entry.name), textX, y + 22);

    // Knowledge badge
    const badge: Record<KnowledgeLevel, string> = {
      heard: 'Heard of it', seen: 'Seen it', fought: 'Fought it', studied: 'Studied',
    };
    ctx.font = '9px Georgia, serif';
    ctx.fillStyle = '#7a5a2a';
    ctx.fillText(`[${badge[entry.knowledge_level]}]`, textX, y + 36);

    if (entry.knowledge_level !== 'heard' && entry.description) {
      ctx.font = '10px Georgia, serif';
      ctx.fillStyle = '#1a1208';
      // Word-wrap description (guard applied to full description before render)
      const words = _guardLabel(entry.description).split(' ');
      let line = '';
      let ty = y + 54;
      for (const word of words) {
        const test = line ? line + ' ' + word : word;
        if (ctx.measureText(test).width > textW && line) {
          ctx.fillText(line, textX, ty);
          ty += 16;
          line = word;
          if (ty > y + ENTRY_H - 16) break;
        } else {
          line = test;
        }
      }
      if (line && ty < y + ENTRY_H - 16) ctx.fillText(line, textX, ty);
    }

    y += ENTRY_H;
  }

  return new THREE.CanvasTexture(canvas);
}

/** Renders a static "Handouts — filed in Handout Tray" redirect page.
 *
 * Handout data is owned by the Handout Tray object (WO-UI-HANDOUTS-01).
 * NotebookObject never stores, pushes, or mutates handout entries.
 */
function makeHandoutsRedirectCanvas(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = PAGE_W; canvas.height = PAGE_H;
  const ctx = canvas.getContext('2d')!;

  ctx.fillStyle = '#f0e8d4';
  ctx.fillRect(0, 0, PAGE_W, PAGE_H);

  // Header
  ctx.fillStyle = '#2a1a08';
  ctx.fillRect(0, 0, PAGE_W, 38);
  ctx.font = 'bold 13px Georgia, serif';
  ctx.fillStyle = '#d4b878';
  ctx.textAlign = 'center';
  ctx.fillText('HANDOUT STORAGE', PAGE_W / 2, 24);

  ctx.font = 'italic 11px Georgia, serif';
  ctx.fillStyle = '#8a6a40';
  ctx.textAlign = 'center';
  ctx.fillText('Handouts are filed in the Handout Tray.', PAGE_W / 2, PAGE_H / 2 - 14);
  ctx.fillText('Open the tray to view received handouts.', PAGE_W / 2, PAGE_H / 2 + 6);

  return new THREE.CanvasTexture(canvas);
}

// ---------------------------------------------------------------------------
// Section tab renderer
// ---------------------------------------------------------------------------

function makeTabTexture(label: string, active: boolean): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 128; canvas.height = 48;
  const ctx = canvas.getContext('2d')!;
  ctx.fillStyle = active ? '#d4b060' : '#7a6040';
  ctx.fillRect(0, 0, 128, 48);
  ctx.font = `${active ? 'bold ' : ''}10px Georgia, serif`;
  ctx.fillStyle = active ? '#1a0e00' : '#d4c090';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(label, 64, 24);
  return new THREE.CanvasTexture(canvas);
}

// ---------------------------------------------------------------------------
// NotebookObject
// ---------------------------------------------------------------------------

const OPEN_DURATION  = 0.40;
const CLOSE_DURATION = 0.30;
const FLIP_DURATION  = 0.20;

const NOTEBOOK_COVER = 0x2e1e0c; // dark leather — slightly warmer for readability
const BRASS_COLOR    = 0xb5832a;

const SECTION_LABELS: Record<SectionId, string> = {
  notes:     'Notes',
  transcript:'Transcript',
  bestiary:  'Bestiary',
  handouts:  'Handouts',
};

export class NotebookObject {
  readonly group: THREE.Group;

  private _isOpen    = false;
  private _section:  SectionId = 'notes';

  // Drawing state
  private _drawTool: DrawTool = 'pen';
  private _inkColor: string   = INK_DEF;
  private _inkSize:  number   = 0;       // 0 = use tool default
  private _strokes:  Stroke[] = [];
  private _currentStroke: Stroke | null = null;

  // Transcript display state — READ-ONLY feed texture, not a data store.
  // The transcript feed consumer (ws-bridge) calls setTranscriptFeedTexture()
  // to push a pre-rendered texture; NotebookObject only displays it.
  // No TranscriptEntry array. No push path. No auto-write.
  private _transcriptFeedTexture: THREE.CanvasTexture;

  // Bestiary state — upsert goes through NotebookConsentChain
  private _bestiaryEntries: BestiaryEntry[] = [];
  /** Pre-loaded portrait images keyed by entity_id. Populated async on upsert. */
  private _bestiaryImages: Map<string, HTMLImageElement> = new Map();

  // Consent chain — gates all AI-assisted writes
  readonly consentChain: NotebookConsentChain = new NotebookConsentChain();

  // Page textures
  private _notesTexture:      THREE.CanvasTexture;
  private _bestiaryTexture:   THREE.CanvasTexture;
  private _handoutsTexture:   THREE.CanvasTexture;

  // Geometry
  private _coverLeft:  THREE.Mesh;
  private _coverRight: THREE.Mesh;
  private _spine:      THREE.Mesh;
  private _pageLeft:   THREE.Mesh;
  private _pageRight:  THREE.Mesh;
  private _clasp:      THREE.Mesh;
  private _tabs:       THREE.Mesh[] = [];

  // Animation
  private _animState:    'idle' | 'opening' | 'closing' = 'idle';
  private _animProgress  = 0;
  private _animDuration  = OPEN_DURATION;

  // The closed-cover mesh for raycasting in main.ts
  readonly coverMesh: THREE.Mesh;

  // Drawing canvas (live drawing surface, separate from page texture)
  private _drawCanvas: HTMLCanvasElement;
  private _drawCtx:    CanvasRenderingContext2D;

  // Persistence
  private _sessionId: string;
  private _saveTimers: Map<string, ReturnType<typeof setTimeout>> = new Map();
  private readonly SAVE_DEBOUNCE_MS = 2000;
  private readonly MAX_STORAGE_BYTES = 500 * 1024; // 500 KB
  private _coverPlayerName: string = '';
  private _coverImageUrl: string = '';

  get isOpen():   boolean  { return this._isOpen; }
  get section():  SectionId { return this._section; }
  get drawTool(): DrawTool  { return this._drawTool; }
  get inkColor(): string    { return this._inkColor; }
  get inkSize():  number    { return this._inkSize; }
  /** Right page mesh — exposed for pointer-event raycasting in main.ts. */
  get pageRightMesh(): THREE.Mesh { return this._pageRight; }

  constructor(sessionId: string = 'default') {
    this.group = new THREE.Group();
    this.group.name = 'notebook';

    // Drawing canvas (persistent surface for notes section)
    this._drawCanvas = document.createElement('canvas');
    this._drawCanvas.width  = PAGE_W;
    this._drawCanvas.height = PAGE_H;
    this._drawCtx = this._drawCanvas.getContext('2d')!;
    this._sessionId = sessionId;
    this._initDrawCanvas();

    // Load persisted strokes for the notes section
    this._strokes = this.loadStrokes('notes');
    this._replayStrokes();

    // Build initial page textures
    this._notesTexture      = makeNotesCanvas(this._strokes);
    this._transcriptFeedTexture = makeTranscriptPlaceholderCanvas();
    this._bestiaryTexture   = makeBestiaryCanvas(this._bestiaryEntries, this._bestiaryImages);
    this._handoutsTexture   = makeHandoutsRedirectCanvas();

    // Spine
    const spineGeo = new THREE.BoxGeometry(0.10, 0.16, 1.65);
    const spineMat = new THREE.MeshStandardMaterial({ color: 0x0e0804, roughness: 0.85, metalness: 0.03 });
    this._spine = new THREE.Mesh(spineGeo, spineMat);
    this._spine.name = 'notebook_spine';
    this._spine.castShadow = true;
    this.group.add(this._spine);

    // Covers — wider and deeper so notebook is dominant on player shelf
    const coverGeo = new THREE.BoxGeometry(1.15, 0.12, 1.75);
    const coverMat = new THREE.MeshStandardMaterial({ color: NOTEBOOK_COVER, roughness: 0.88, metalness: 0.04, emissive: new THREE.Color(0x1a0d04), emissiveIntensity: 0.6 });

    this._coverLeft  = new THREE.Mesh(coverGeo, coverMat.clone());
    this._coverLeft.name  = 'notebook_cover_left';
    this._coverLeft.castShadow  = true;
    this._coverLeft.receiveShadow = true;

    this._coverRight = new THREE.Mesh(coverGeo, coverMat.clone());
    this._coverRight.name = 'notebook_cover_right';
    this._coverRight.castShadow  = true;
    this._coverRight.receiveShadow = true;

    // 80s sparkle detail strip on cover (brass clasp suggestion)
    const claspGeo = new THREE.BoxGeometry(0.06, 0.125, 0.22);
    const claspMat = new THREE.MeshStandardMaterial({ color: BRASS_COLOR, roughness: 0.3, metalness: 0.9 });
    const clasp = new THREE.Mesh(claspGeo, claspMat);
    clasp.name = 'notebook_clasp';
    this._clasp = clasp;

    // Page meshes
    const pageGeo = new THREE.PlaneGeometry(1.0, 1.65);

    this._pageLeft = new THREE.Mesh(
      pageGeo,
      new THREE.MeshStandardMaterial({
        map: this._notesTexture,
        roughness: 0.92, metalness: 0.0, side: THREE.FrontSide,
      }),
    );
    this._pageLeft.name = 'notebook_page_left';
    this._pageLeft.rotation.x = -Math.PI / 2;
    this._pageLeft.visible = false;

    this._pageRight = new THREE.Mesh(
      pageGeo,
      new THREE.MeshStandardMaterial({
        map: this._notesTexture,
        roughness: 0.92, metalness: 0.0, side: THREE.FrontSide,
      }),
    );
    this._pageRight.name = 'notebook_page_right';
    this._pageRight.rotation.x = -Math.PI / 2;
    this._pageRight.visible = false;

    // Section tabs — 4 tabs on the right edge of the spread
    const tabLabels: SectionId[] = ['notes', 'transcript', 'bestiary', 'handouts'];
    tabLabels.forEach((sid, i) => {
      const tabGeo = new THREE.BoxGeometry(0.22, 0.015, 0.28);
      const tabMat = new THREE.MeshStandardMaterial({
        map: makeTabTexture(SECTION_LABELS[sid], sid === this._section),
        roughness: 0.6, metalness: 0.0,
      });
      const tab = new THREE.Mesh(tabGeo, tabMat);
      tab.name = `notebook_tab_${sid}`;
      tab.position.set(1.05, 0.01, -0.55 + i * 0.38);
      tab.visible = false;
      this._tabs.push(tab);
      this.group.add(tab);
    });

    this.group.add(this._coverLeft);
    this.group.add(this._coverRight);
    this.group.add(clasp);
    this.group.add(this._pageLeft);
    this.group.add(this._pageRight);

    this.coverMesh = this._coverRight;

    this._applyClosed();
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  open(): void {
    if (this._isOpen || this._animState !== 'idle') return;
    this._animState    = 'opening';
    this._animProgress = 0;
    this._animDuration = OPEN_DURATION;
    this._pageLeft.visible  = true;
    this._pageRight.visible = true;
    this._tabs.forEach(t => { t.visible = true; });
    this._refreshPageTextures();
  }

  close(): void {
    if (!this._isOpen || this._animState !== 'idle') return;
    this._animState    = 'closing';
    this._animProgress = 0;
    this._animDuration = CLOSE_DURATION;
  }

  toggle(): void {
    if (this._isOpen) this.close();
    else this.open();
  }

  /** Cycle section tabs (notes → transcript → bestiary → handouts → notes) */
  setSection(sid: SectionId): void {
    if (sid === this._section) return;
    this._section = sid;
    this._refreshPageTextures();
    this._refreshTabTextures();
  }

  cycleSection(): void {
    const idx = SECTIONS.indexOf(this._section);
    this.setSection(SECTIONS[(idx + 1) % SECTIONS.length]);
  }

  /** Cycle draw tool (pen → brush → eraser → pen). Called by inkwell click. */
  cycleDrawTool(): DrawTool {
    const tools: DrawTool[] = ['pen', 'brush', 'eraser'];
    const idx = tools.indexOf(this._drawTool);
    this._drawTool = tools[(idx + 1) % tools.length];
    return this._drawTool;
  }

  /** Set ink color (hex string e.g. '#1a0e06'). */
  setInkColor(color: string): void { this._inkColor = color; }

  /** Set ink size (0 = tool default). */
  setInkSize(size: number): void { this._inkSize = size; }

  // ---------------------------------------------------------------------------
  // Drawing API — called by main.ts pointer events on the page mesh
  // ---------------------------------------------------------------------------

  /** Convert UV coordinates (0-1) from a rayhit on the page to canvas coords */
  uvToCanvas(u: number, v: number): { x: number; y: number } {
    return { x: u * PAGE_W, y: (1 - v) * PAGE_H };
  }

  startStroke(u: number, v: number): void {
    if (this._section !== 'notes' || !this._isOpen) return;
    const pt = this.uvToCanvas(u, v);
    this._currentStroke = { tool: this._drawTool, color: this._inkColor, size: this._inkSize, points: [pt] };
    this._applyStrokePoint(pt, true);
  }

  continueStroke(u: number, v: number): void {
    if (!this._currentStroke) return;
    const pt = this.uvToCanvas(u, v);
    this._currentStroke.points.push(pt);
    this._applyStrokePoint(pt, false);
  }

  endStroke(): void {
    if (!this._currentStroke) return;
    if (this._currentStroke.points.length > 1) {
      this._strokes.push(this._currentStroke);
    }
    this._currentStroke = null;
    // Update texture from draw canvas
    this._notesTexture = new THREE.CanvasTexture(this._drawCanvas);
    if (this._section === 'notes') this._refreshPageTextures();
    // Debounced persist
    this.saveStrokes('notes', this._strokes);
  }

  undoStroke(): void {
    if (this._strokes.length === 0) return;
    this._strokes.pop();
    this._initDrawCanvas();
    this._replayStrokes();
    this._notesTexture = new THREE.CanvasTexture(this._drawCanvas);
    if (this._section === 'notes') this._refreshPageTextures();
    // Debounced persist after undo
    this.saveStrokes('notes', this._strokes);
  }

  // ---------------------------------------------------------------------------
  // Transcript display — READ-ONLY feed surface
  // ---------------------------------------------------------------------------

  /**
   * Supply a pre-rendered transcript texture from the session feed consumer.
   * This is the ONLY path for transcript content to reach the notebook page.
   * NotebookObject does NOT store transcript entries — the feed consumer owns them.
   * Player action is not required for this call because it is a passive display
   * update, not a write to player-owned content.
   */
  setTranscriptFeedTexture(texture: THREE.CanvasTexture): void {
    this._transcriptFeedTexture = texture;
    if (this._section === 'transcript' && this._isOpen) this._refreshPageTextures();
  }

  // ---------------------------------------------------------------------------
  // Bestiary upsert — consent-gated AI-assisted write
  // ---------------------------------------------------------------------------

  /**
   * Consent-gated bestiary upsert. Caller MUST traverse the consent chain:
   *   1. consentChain.requestConsent({ label, payload: entry }) → true
   *   2. Player action triggers consentChain.grant()
   *   3. Caller calls applyBestiaryUpsert(consentChain.applyWrite() as BestiaryEntry)
   * Calling this method without a preceding grant() is a no-op (write locked).
   *
   * Direct player ink (startStroke) bypasses this chain — always permitted.
   */
  applyBestiaryUpsert(entry: BestiaryEntry): boolean {
    // Enforce consent gate: write is only permitted if the chain just granted.
    // The caller is responsible for calling consentChain.grant() first; that
    // transitions state to 'granted'. applyWrite() validates the state and
    // clears it.
    if (!this.consentChain.applyWrite()) return false;

    const idx = this._bestiaryEntries.findIndex(e => e.entity_id === entry.entity_id);
    if (idx >= 0) this._bestiaryEntries[idx] = entry;
    else this._bestiaryEntries.push(entry);

    if (entry.image_url) {
      const img = new Image();
      img.onload = () => {
        this._bestiaryImages.set(entry.entity_id, img);
        this._bestiaryTexture = makeBestiaryCanvas(this._bestiaryEntries, this._bestiaryImages);
        if (this._section === 'bestiary' && this._isOpen) this._refreshPageTextures();
      };
      img.src = entry.image_url;
    }

    this._bestiaryTexture = makeBestiaryCanvas(this._bestiaryEntries, this._bestiaryImages);
    if (this._section === 'bestiary' && this._isOpen) this._refreshPageTextures();
    return true;
  }

  // ---------------------------------------------------------------------------
  // Text block — typed text rendered directly to notes canvas
  // ---------------------------------------------------------------------------

  /** Add a typed text block to the notes canvas at canvas coordinates (cx, cy). */
  addTextBlock(cx: number, cy: number, text: string): void {
    this._drawCtx.font = '14px Georgia, serif';
    this._drawCtx.fillStyle = INK_DEF;
    this._drawCtx.globalCompositeOperation = 'source-over';
    this._drawCtx.textAlign = 'left';
    this._drawCtx.fillText(text, cx, cy);
    this._notesTexture = new THREE.CanvasTexture(this._drawCanvas);
    if (this._section === 'notes') this._refreshPageTextures();
    this.saveStrokes('notes', this._strokes);
  }

  // ---------------------------------------------------------------------------
  // API compatibility — methods called by main.ts bridge handlers
  // ---------------------------------------------------------------------------

  /**
   * Alias for applyBestiaryUpsert matching the BestiaryBindController wire
   * in main.ts. Caller must have traversed the consent chain first.
   */
  upsertBestiaryEntry(entry: BestiaryEntry): boolean {
    return this.applyBestiaryUpsert(entry);
  }

  // ---------------------------------------------------------------------------
  // Tab hit detection — returns section if a tab mesh is clicked
  // ---------------------------------------------------------------------------

  getTabSection(mesh: THREE.Object3D): SectionId | null {
    for (let i = 0; i < this._tabs.length; i++) {
      if (this._tabs[i] === mesh) return SECTIONS[i];
    }
    return null;
  }

  get tabMeshes(): THREE.Mesh[] { return this._tabs; }

  // ---------------------------------------------------------------------------
  // Update (call each frame)
  // ---------------------------------------------------------------------------

  update(dt: number): void {
    if (this._animState === 'idle') return;

    this._animProgress = Math.min(1, this._animProgress + dt / this._animDuration);
    const t = smoothstep(this._animProgress);

    if (this._animState === 'opening') {
      this._applyOpenProgress(t);
      if (this._animProgress >= 1) {
        this._isOpen    = true;
        this._animState = 'idle';
      }
    } else if (this._animState === 'closing') {
      this._applyOpenProgress(1 - t);
      if (this._animProgress >= 1) {
        this._isOpen    = false;
        this._animState = 'idle';
        this._pageLeft.visible  = false;
        this._pageRight.visible = false;
        this._tabs.forEach(t2 => { t2.visible = false; });
        this._applyClosed();
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  // ---------------------------------------------------------------------------
  // Persistence
  // ---------------------------------------------------------------------------

  private _storageKey(sectionId: string): string {
    return `nb_strokes_${this._sessionId}_${sectionId}`;
  }

  saveStrokes(sectionId: string, strokes: Stroke[]): void {
    // Cancel any pending timer for this section
    const existing = this._saveTimers.get(sectionId);
    if (existing !== undefined) clearTimeout(existing);

    // Snapshot the array now so mutations during the debounce window do not
    // affect the data that will be written.
    const snapshot = strokes.slice();

    const timer = setTimeout(() => {
      this._saveTimers.delete(sectionId);
      const key = this._storageKey(sectionId);
      let data = snapshot;

      // Size guard: drop oldest strokes until payload fits within 500 KB
      let json = JSON.stringify(data);
      while (json.length > this.MAX_STORAGE_BYTES && data.length > 0) {
        data = data.slice(1);
        json = JSON.stringify(data);
      }

      try {
        localStorage.setItem(key, json);
      } catch (_e) {
        // Storage quota exceeded -- drop half and retry once
        data = data.slice(Math.floor(data.length / 2));
        try {
          localStorage.setItem(key, JSON.stringify(data));
        } catch (_e2) {
          // Give up gracefully -- persistence is best-effort
        }
      }
    }, this.SAVE_DEBOUNCE_MS);

    this._saveTimers.set(sectionId, timer);
  }

  loadStrokes(sectionId: string): Stroke[] {
    const key = this._storageKey(sectionId);
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return [];
      const parsed = JSON.parse(raw) as Array<{ tool: DrawTool; color?: string; size?: number; points: { x: number; y: number }[] }>;
      if (!Array.isArray(parsed)) return [];
      // Backfill color/size for strokes saved before these fields existed
      return parsed.map(s => ({ tool: s.tool, color: s.color ?? INK_DEF, size: s.size ?? 0, points: s.points }));
    } catch {
      return [];
    }
  }

  private _initDrawCanvas(): void {
    this._drawCtx.fillStyle = '#f5f0e4';
    this._drawCtx.fillRect(0, 0, PAGE_W, PAGE_H);
    // Lined paper base
    this._drawCtx.strokeStyle = '#e8a0a0'; this._drawCtx.lineWidth = 1.2;
    this._drawCtx.beginPath(); this._drawCtx.moveTo(60, 0); this._drawCtx.lineTo(60, PAGE_H); this._drawCtx.stroke();
    this._drawCtx.strokeStyle = '#b0c0d8'; this._drawCtx.lineWidth = 0.6;
    for (let y = 80; y < PAGE_H - 40; y += 28) {
      this._drawCtx.beginPath(); this._drawCtx.moveTo(0, y); this._drawCtx.lineTo(PAGE_W, y); this._drawCtx.stroke();
    }
  }

  private _replayStrokes(): void {
    for (const stroke of this._strokes) {
      if (stroke.points.length < 2) continue;
      this._drawCtx.beginPath();
      this._drawCtx.moveTo(stroke.points[0].x, stroke.points[0].y);
      for (let i = 1; i < stroke.points.length; i++) {
        this._drawCtx.lineTo(stroke.points[i].x, stroke.points[i].y);
      }
      this._setStrokeStyle(stroke.tool, stroke.color, stroke.size);
      this._drawCtx.stroke();
    }
  }

  private _applyStrokePoint(pt: { x: number; y: number }, isStart: boolean): void {
    if (isStart) {
      this._drawCtx.beginPath();
      this._drawCtx.moveTo(pt.x, pt.y);
    } else {
      this._drawCtx.lineTo(pt.x, pt.y);
      this._setStrokeStyle(this._drawTool, this._inkColor, this._inkSize);
      this._drawCtx.stroke();
      // Keep path open for next point
      this._drawCtx.beginPath();
      this._drawCtx.moveTo(pt.x, pt.y);
    }
    // Live texture update
    if (this._section === 'notes') {
      (this._pageRight.material as THREE.MeshStandardMaterial).map = new THREE.CanvasTexture(this._drawCanvas);
      (this._pageRight.material as THREE.MeshStandardMaterial).needsUpdate = true;
    }
  }

  private _setStrokeStyle(tool: DrawTool, color: string = INK_DEF, size: number = 0): void {
    this._drawCtx.lineCap  = 'round';
    this._drawCtx.lineJoin = 'round';
    this._drawCtx.globalCompositeOperation = 'source-over';
    if (tool === 'eraser') {
      // Paint paper color — no transparency holes
      this._drawCtx.strokeStyle = '#f5f0e4';
      this._drawCtx.lineWidth = size > 0 ? size : 18;
    } else if (tool === 'brush') {
      this._drawCtx.strokeStyle = color;
      this._drawCtx.lineWidth = size > 0 ? size : 5;
    } else {
      this._drawCtx.strokeStyle = color;
      this._drawCtx.lineWidth = size > 0 ? size : 1.5;
    }
  }

  private _refreshPageTextures(): void {
    let leftTex:  THREE.CanvasTexture;
    let rightTex: THREE.CanvasTexture;

    switch (this._section) {
      case 'notes':
        // Left = lined blank, right = drawing canvas
        leftTex  = makeNotesCanvas([]);
        rightTex = new THREE.CanvasTexture(this._drawCanvas);
        break;
      case 'transcript':
        leftTex  = this._transcriptFeedTexture;
        rightTex = this._transcriptFeedTexture;
        break;
      case 'bestiary':
        leftTex  = this._bestiaryTexture;
        rightTex = this._bestiaryTexture;
        break;
      case 'handouts':
        leftTex  = this._handoutsTexture;
        rightTex = this._handoutsTexture;
        break;
    }

    (this._pageLeft.material  as THREE.MeshStandardMaterial).map = leftTex;
    (this._pageRight.material as THREE.MeshStandardMaterial).map = rightTex;
    (this._pageLeft.material  as THREE.MeshStandardMaterial).needsUpdate = true;
    (this._pageRight.material as THREE.MeshStandardMaterial).needsUpdate = true;
  }

  private _refreshTabTextures(): void {
    SECTIONS.forEach((sid, i) => {
      (this._tabs[i].material as THREE.MeshStandardMaterial).map =
        makeTabTexture(SECTION_LABELS[sid], sid === this._section);
      (this._tabs[i].material as THREE.MeshStandardMaterial).needsUpdate = true;
    });
  }

  private _applyClosed(): void {
    this._spine.position.set(0, 0, 0);
    this._coverLeft.position.set(-0.55, 0, 0);
    this._coverLeft.rotation.set(0, 0, 0);
    this._coverLeft.visible = true;
    this._coverRight.position.set(0.55, 0, 0);
    this._coverRight.rotation.set(0, 0, 0);
    this._coverRight.visible = true;
    this._pageLeft.position.set(-0.55,  0.065, 0);
    this._pageRight.position.set( 0.55, 0.065, 0);
    this._clasp.visible = true;
  }

  private _applyOpenProgress(t: number): void {
    const angle = -Math.PI / 2 * t;
    // Covers swing open — hide them when fully open (you see pages, not covers, on an open flat book)
    const coverOffset = 0.55 + Math.sin(-angle) * 1.075 * t;
    this._coverLeft.rotation.x  = angle;
    this._coverLeft.position.set(-coverOffset, Math.cos(-angle) * 0.06 * (1 - t), 0);
    this._coverLeft.visible = t < 0.95;
    this._coverRight.rotation.x = angle;
    this._coverRight.position.set( coverOffset, Math.cos(-angle) * 0.06 * (1 - t), 0);
    this._coverRight.visible = t < 0.95;
    this._pageLeft.position.set(-0.55, 0.065 - 0.065 * t, 0);
    this._pageRight.position.set( 0.55, 0.065 - 0.065 * t, 0);
    // Hide clasp when open — it lives on the cover face
    this._clasp.visible = t < 0.5;
    // Tabs appear as book opens
    this._tabs.forEach(tab => { tab.position.y = 0.01 - 0.01 * t; });
  }
  // ---------------------------------------------------------------------------
  // Session Zero -- Cover name + image
  // ---------------------------------------------------------------------------

  /** Set the player name text on the notebook cover. Persists to localStorage. */
  setCoverName(playerName: string): void {
    this._coverPlayerName = playerName;
    this._renderCoverName(playerName);
    try {
      localStorage.setItem(`nb_cover_name_${this._sessionId}`, playerName);
    } catch (_) {}
  }

  /** Set the notebook cover image from URL. Persists to localStorage. */
  setCoverImage(imageUrl: string): void {
    if (!imageUrl) return;
    this._coverImageUrl = imageUrl;
    this._loadCoverImage(imageUrl);
    try {
      localStorage.setItem(`nb_cover_image_${this._sessionId}`, imageUrl);
    } catch (_) {}
  }

  /** Reload cover from localStorage (call on session_resume). */
  loadCoverFromStorage(): void {
    const name = localStorage.getItem(`nb_cover_name_${this._sessionId}`);
    if (name) this._renderCoverName(name);
    const url = localStorage.getItem(`nb_cover_image_${this._sessionId}`);
    if (url) this._loadCoverImage(url);
  }

  private _renderCoverName(name: string): void {
    const cover = this.group.getObjectByName('notebook_cover_right') as THREE.Mesh | undefined;
    if (!cover) return;
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 128;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = '#2a1a08';
    ctx.fillRect(0, 0, 256, 128);
    ctx.font = 'bold 28px Georgia, serif';
    ctx.fillStyle = '#d4b878';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(name, 128, 64);
    const mat = cover.material as THREE.MeshStandardMaterial;
    if (mat.map) mat.map.dispose();
    mat.map = new THREE.CanvasTexture(canvas);
    mat.needsUpdate = true;
  }

  private _loadCoverImage(url: string): void {
    const cover = this.group.getObjectByName('notebook_cover_right') as THREE.Mesh | undefined;
    if (!cover) return;
    const loader = new THREE.TextureLoader();
    loader.load(url, (texture) => {
      const mat = cover.material as THREE.MeshStandardMaterial;
      if (mat.map) mat.map.dispose();
      mat.map = texture;
      mat.needsUpdate = true;
    });
  }

}

function smoothstep(t: number): number {
  return t * t * (3 - 2 * t);
}

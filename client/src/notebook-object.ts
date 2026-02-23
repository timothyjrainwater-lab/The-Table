/**
 * NotebookObject — Slice 4: Notebook open/sections/drawing/transcript/bestiary.
 *
 * Doctrine authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §14, §19 Slice 4.
 * UX authority: UX_VISION_PHYSICAL_TABLE.md — The Notebook section.
 *
 * The notebook is the ONLY writable artifact on the table.
 * 4 sections: Personal Pages (drawing), Transcript, Bestiary, Handout Storage.
 * Drawing uses seeded PRNG for nothing (drawing is user input, not procedural).
 * No Math.random for any procedural content (Gate G).
 *
 * Sections:
 *   0 — Personal Pages: freehand drawing (pen/brush/eraser via inkwell)
 *   1 — Transcript: read-only auto-scroll log from WS
 *   2 — Bestiary: progressive reveal from WS
 *   3 — Handout Storage: filed handout thumbnails
 */

import * as THREE from 'three';

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

const _coverPrng  = makePrng(0xc0ffee11);
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
  points: { x: number; y: number }[];
}

// ---------------------------------------------------------------------------
// Canvas dimensions
// ---------------------------------------------------------------------------

const PAGE_W   = 768;
const PAGE_H   = 1024;
const INK_DEF  = '#1a0e06';

// ---------------------------------------------------------------------------
// Transcript entry
// ---------------------------------------------------------------------------

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
}

// ---------------------------------------------------------------------------
// Handout thumbnail entry
// ---------------------------------------------------------------------------

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
    if (stroke.tool === 'eraser') {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.strokeStyle = 'rgba(0,0,0,1)';
      ctx.lineWidth = 18;
    } else if (stroke.tool === 'brush') {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = INK_DEF;
      ctx.lineWidth = 5;
    } else {
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = INK_DEF;
      ctx.lineWidth = 1.5;
    }
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    ctx.globalCompositeOperation = 'source-over';
  }

  return new THREE.CanvasTexture(canvas);
}

function makeTranscriptCanvas(entries: TranscriptEntry[], scrollOffset: number): THREE.CanvasTexture {
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

  const MARGIN = 28;
  const LINE_H = 20;
  let y = 56 - scrollOffset;

  for (const entry of entries) {
    if (y > PAGE_H - 20) break;
    if (y < 38) { y += LINE_H * 2; continue; }

    // Speaker label
    ctx.font = 'bold 9px Georgia, serif';
    ctx.fillStyle = entry.speaker === 'narrator' ? '#5a3a10'
                  : entry.speaker === 'player'   ? '#1a3a5a'
                  :                                '#3a1a5a';
    ctx.textAlign = 'left';
    ctx.fillText(
      entry.speaker === 'narrator' ? 'DM:' :
      entry.speaker === 'player'   ? 'YOU:' : 'NPC:',
      MARGIN, y,
    );

    // Text — word-wrap at ~55 chars per line
    const words = entry.text.split(' ');
    let line = '';
    ctx.font = entry.speaker === 'narrator'
      ? 'italic 11px Georgia, serif'
      : '11px Georgia, serif';
    ctx.fillStyle = '#1a1208';
    const maxW = PAGE_W - MARGIN * 2 - 36;
    let firstLine = true;

    for (const word of words) {
      const test = line ? line + ' ' + word : word;
      if (ctx.measureText(test).width > maxW && line) {
        ctx.fillText(line, MARGIN + 36, y);
        y += LINE_H;
        line = word;
        firstLine = false;
        if (y > PAGE_H - 20) break;
      } else {
        line = test;
        if (firstLine) { firstLine = false; }
      }
    }
    if (line && y < PAGE_H - 20) {
      ctx.fillText(line, MARGIN + 36, y);
      y += LINE_H;
    }

    y += 6; // gap between entries
  }

  // Faint "scroll for more" at bottom if entries overflow
  if (entries.length > 20) {
    ctx.font = '9px Georgia, serif';
    ctx.fillStyle = '#a08060';
    ctx.textAlign = 'center';
    ctx.fillText('↓', PAGE_W / 2, PAGE_H - 12);
  }

  return new THREE.CanvasTexture(canvas);
}

function makeBestiaryCanvas(entries: BestiaryEntry[]): THREE.CanvasTexture {
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
    if (entry.knowledge_level === 'heard') {
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
    ctx.fillText(entry.knowledge_level === 'heard' ? '???' : entry.name, textX, y + 22);

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
      // Word-wrap description
      const words = entry.description.split(' ');
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

function makeHandoutsCanvas(handouts: HandoutEntry[]): THREE.CanvasTexture {
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

  if (handouts.length === 0) {
    ctx.font = 'italic 12px Georgia, serif';
    ctx.fillStyle = '#a09070';
    ctx.textAlign = 'center';
    ctx.fillText('No handouts filed yet.', PAGE_W / 2, PAGE_H / 2);
    return new THREE.CanvasTexture(canvas);
  }

  const MARGIN = 28;
  const THUMB_W = 160;
  const THUMB_H = 110;
  const GAP     = 16;
  let x = MARGIN;
  let y = 56;

  for (let i = 0; i < handouts.length; i++) {
    const h = handouts[i];

    // Paper thumbnail — slight angle alternates
    ctx.save();
    ctx.translate(x + THUMB_W / 2, y + THUMB_H / 2);
    ctx.rotate((i % 2 === 0 ? 1 : -1) * 0.04);
    ctx.fillStyle = '#e8dcc0';
    ctx.strokeStyle = '#8a7a5a'; ctx.lineWidth = 1;
    ctx.fillRect(-THUMB_W / 2, -THUMB_H / 2, THUMB_W, THUMB_H);
    ctx.strokeRect(-THUMB_W / 2, -THUMB_H / 2, THUMB_W, THUMB_H);

    // Title on thumbnail
    ctx.font = 'bold 10px Georgia, serif';
    ctx.fillStyle = '#2a1a08';
    ctx.textAlign = 'center';
    ctx.fillText(h.title, 0, 4);

    // Faint lines
    ctx.strokeStyle = '#c0b090'; ctx.lineWidth = 0.4;
    for (let l = 1; l <= 5; l++) {
      const ly = -THUMB_H / 2 + 24 + l * 12;
      ctx.beginPath(); ctx.moveTo(-THUMB_W / 2 + 10, ly); ctx.lineTo(THUMB_W / 2 - 10, ly); ctx.stroke();
    }
    ctx.restore();

    // Number label below
    ctx.font = '9px Georgia, serif';
    ctx.fillStyle = '#8a7060';
    ctx.textAlign = 'center';
    ctx.fillText(`#${i + 1}`, x + THUMB_W / 2, y + THUMB_H + 12);

    x += THUMB_W + GAP;
    if (x + THUMB_W > PAGE_W - MARGIN) {
      x = MARGIN;
      y += THUMB_H + GAP + 20;
    }
    if (y + THUMB_H > PAGE_H - 20) break;
  }

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

const NOTEBOOK_COVER = 0x1c1008; // near-black leather
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
  private _strokes:  Stroke[] = [];
  private _currentStroke: Stroke | null = null;

  // Transcript state
  private _transcriptEntries: TranscriptEntry[] = [];
  private _transcriptScroll  = 0;

  // Bestiary state
  private _bestiaryEntries: BestiaryEntry[] = [];

  // Handout state
  private _handoutEntries: HandoutEntry[] = [];

  // Page textures
  private _notesTexture:      THREE.CanvasTexture;
  private _transcriptTexture: THREE.CanvasTexture;
  private _bestiaryTexture:   THREE.CanvasTexture;
  private _handoutsTexture:   THREE.CanvasTexture;

  // Geometry
  private _coverLeft:  THREE.Mesh;
  private _coverRight: THREE.Mesh;
  private _spine:      THREE.Mesh;
  private _pageLeft:   THREE.Mesh;
  private _pageRight:  THREE.Mesh;
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

  get isOpen():   boolean  { return this._isOpen; }
  get section():  SectionId { return this._section; }
  get drawTool(): DrawTool  { return this._drawTool; }

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'notebook';

    // Drawing canvas (persistent surface for notes section)
    this._drawCanvas = document.createElement('canvas');
    this._drawCanvas.width  = PAGE_W;
    this._drawCanvas.height = PAGE_H;
    this._drawCtx = this._drawCanvas.getContext('2d')!;
    this._initDrawCanvas();

    // Build initial page textures
    this._notesTexture      = makeNotesCanvas(this._strokes);
    this._transcriptTexture = makeTranscriptCanvas(this._transcriptEntries, 0);
    this._bestiaryTexture   = makeBestiaryCanvas(this._bestiaryEntries);
    this._handoutsTexture   = makeHandoutsCanvas(this._handoutEntries);

    // Spine
    const spineGeo = new THREE.BoxGeometry(0.10, 0.16, 1.65);
    const spineMat = new THREE.MeshStandardMaterial({ color: 0x0e0804, roughness: 0.85, metalness: 0.03 });
    this._spine = new THREE.Mesh(spineGeo, spineMat);
    this._spine.name = 'notebook_spine';
    this._spine.castShadow = true;
    this.group.add(this._spine);

    // Covers
    const coverGeo = new THREE.BoxGeometry(1.0, 0.12, 1.65);
    const coverMat = new THREE.MeshStandardMaterial({ color: NOTEBOOK_COVER, roughness: 0.88, metalness: 0.04 });

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
    this._currentStroke = { tool: this._drawTool, points: [pt] };
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
  }

  undoStroke(): void {
    if (this._strokes.length === 0) return;
    this._strokes.pop();
    this._initDrawCanvas();
    this._replayStrokes();
    this._notesTexture = new THREE.CanvasTexture(this._drawCanvas);
    if (this._section === 'notes') this._refreshPageTextures();
  }

  // ---------------------------------------------------------------------------
  // WS data push
  // ---------------------------------------------------------------------------

  addTranscriptEntry(entry: TranscriptEntry): void {
    this._transcriptEntries.push(entry);
    // Auto-scroll: advance offset so newest entries are at the bottom
    this._transcriptScroll = Math.max(0, this._transcriptEntries.length * 42 - PAGE_H + 80);
    this._transcriptTexture = makeTranscriptCanvas(this._transcriptEntries, this._transcriptScroll);
    if (this._section === 'transcript' && this._isOpen) this._refreshPageTextures();
  }

  upsertBestiaryEntry(entry: BestiaryEntry): void {
    const idx = this._bestiaryEntries.findIndex(e => e.entity_id === entry.entity_id);
    if (idx >= 0) this._bestiaryEntries[idx] = entry;
    else this._bestiaryEntries.push(entry);
    this._bestiaryTexture = makeBestiaryCanvas(this._bestiaryEntries);
    if (this._section === 'bestiary' && this._isOpen) this._refreshPageTextures();
  }

  addHandout(entry: HandoutEntry): void {
    this._handoutEntries.push(entry);
    this._handoutsTexture = makeHandoutsCanvas(this._handoutEntries);
    if (this._section === 'handouts' && this._isOpen) this._refreshPageTextures();
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
      this._setStrokeStyle(stroke.tool);
      this._drawCtx.stroke();
      this._drawCtx.globalCompositeOperation = 'source-over';
    }
  }

  private _applyStrokePoint(pt: { x: number; y: number }, isStart: boolean): void {
    if (isStart) {
      this._drawCtx.beginPath();
      this._drawCtx.moveTo(pt.x, pt.y);
    } else {
      this._drawCtx.lineTo(pt.x, pt.y);
      this._setStrokeStyle(this._drawTool);
      this._drawCtx.stroke();
      this._drawCtx.globalCompositeOperation = 'source-over';
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

  private _setStrokeStyle(tool: DrawTool): void {
    this._drawCtx.lineCap  = 'round';
    this._drawCtx.lineJoin = 'round';
    if (tool === 'eraser') {
      this._drawCtx.globalCompositeOperation = 'destination-out';
      this._drawCtx.strokeStyle = 'rgba(0,0,0,1)';
      this._drawCtx.lineWidth = 18;
    } else if (tool === 'brush') {
      this._drawCtx.globalCompositeOperation = 'source-over';
      this._drawCtx.strokeStyle = INK_DEF;
      this._drawCtx.lineWidth = 5;
    } else {
      this._drawCtx.globalCompositeOperation = 'source-over';
      this._drawCtx.strokeStyle = INK_DEF;
      this._drawCtx.lineWidth = 1.5;
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
        leftTex  = this._transcriptTexture;
        rightTex = this._transcriptTexture;
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
    this._coverRight.position.set(0.55, 0, 0);
    this._coverRight.rotation.set(0, 0, 0);
    this._pageLeft.position.set(-0.55,  0.065, 0);
    this._pageRight.position.set( 0.55, 0.065, 0);
  }

  private _applyOpenProgress(t: number): void {
    const angle = -Math.PI / 2 * t;
    this._coverLeft.rotation.x  = angle;
    this._coverLeft.position.set(-0.55 - Math.sin(-angle) * 0.50 * t, Math.cos(-angle) * 0.06 * (1 - t), 0);
    this._coverRight.rotation.x = angle;
    this._coverRight.position.set(0.55 + Math.sin(-angle) * 0.50 * t, Math.cos(-angle) * 0.06 * (1 - t), 0);
    this._pageLeft.position.set(-0.55, 0.065 - 0.065 * t, 0);
    this._pageRight.position.set( 0.55, 0.065 - 0.065 * t, 0);
    // Tabs appear as book opens
    this._tabs.forEach(tab => { tab.position.y = 0.01 - 0.01 * t; });
  }
}

function smoothstep(t: number): number {
  return t * t * (3 - 2 * t);
}

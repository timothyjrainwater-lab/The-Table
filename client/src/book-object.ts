/**
 * BookObject — Slice 3: Rulebook open/page-flip/jump + "?" stamp system.
 *
 * Doctrine authority: DOCTRINE_04_TABLE_UI_MEMO_V4 §13, §9, §19 Slice 3.
 *
 * Rules:
 * - Read-only canon. Navigation: page flips, no snippets, no tooltips.
 * - AI navigates via rulebook_open_ref WS event.
 * - Denial produces "?" stamp on surface; clicking stamp opens rulebook to rule_ref.
 * - No Math.random — all procedural canvas uses seeded PRNG (Gate G).
 */

import * as THREE from 'three';

// ---------------------------------------------------------------------------
// Seeded PRNG (Gate G — no Math.random in client/src/)
// LCG: Numerical Recipes params
// ---------------------------------------------------------------------------

function makePrng(seed: number): () => number {
  let s = seed >>> 0;
  return (): number => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0;
    return s / 0x100000000;
  };
}

const _pagePrng = makePrng(0xb00cf11e);
const _stampPrng = makePrng(0x3f3f3f3f);

// ---------------------------------------------------------------------------
// Page content definitions
// Each spread has two pages (left + right). Pages are pre-authored canvases.
// ---------------------------------------------------------------------------

interface PageSpread {
  ruleRefs: string[];   // rule_refs that resolve to this spread
  leftTitle: string;
  leftEntries: PageEntry[];
  rightTitle: string;
  rightEntries: PageEntry[];
}

interface PageEntry {
  name: string;
  type?: string;
  body: string[];       // lines of body text
}

const SPREADS: PageSpread[] = [
  {
    ruleRefs: ['combat.attack_roll', 'combat.basics', 'combat'],
    leftTitle: 'Combat — Attack Rolls',
    leftEntries: [
      {
        name: 'Attack Roll',
        type: 'Standard Action',
        body: [
          'Roll d20 + attack bonus vs. target AC.',
          'Hit: roll damage and apply.',
          'Natural 20: automatic hit, roll to confirm',
          'critical threat (roll again vs. AC).',
          'Natural 1: automatic miss.',
        ],
      },
      {
        name: 'Attack Bonus',
        body: [
          'Base attack bonus (BAB) + STR mod (melee)',
          'or DEX mod (ranged) + size mod + misc.',
          'Two-weapon fighting: off-hand at −4/−8.',
        ],
      },
      {
        name: 'Touch Attacks',
        body: [
          'Target touch AC (ignores armor/natural',
          'armor/shield bonus). Used by many spells.',
        ],
      },
    ],
    rightTitle: 'Combat — Armor Class',
    rightEntries: [
      {
        name: 'Armor Class (AC)',
        body: [
          '10 + armor + shield + DEX + size + misc.',
          'Flat-footed: lose DEX bonus.',
          'Touch AC: 10 + DEX + size + misc only.',
        ],
      },
      {
        name: 'Damage',
        body: [
          'Weapon damage + STR mod (melee).',
          'Ranged: no STR mod unless bow + Mighty.',
          'Minimum 1 point of nonlethal damage.',
        ],
      },
      {
        name: 'Critical Hits',
        body: [
          'Confirm: roll again vs. same AC.',
          'If confirmed: multiply damage by crit mult.',
          'Extra dice (bonus damage) are not multiplied.',
        ],
      },
    ],
  },
  {
    ruleRefs: ['combat.actions', 'combat.action_types'],
    leftTitle: 'Action Types',
    leftEntries: [
      {
        name: 'Standard Action',
        body: [
          'One per round. Attack, cast most spells,',
          'use a special ability, or activate an item.',
        ],
      },
      {
        name: 'Move Action',
        body: [
          'One per round. Move up to speed, draw',
          'a weapon, stand from prone, open a door.',
          'Can be converted: double move = 2× speed.',
        ],
      },
      {
        name: 'Full-Round Action',
        body: [
          'Consumes both standard + move actions.',
          'Full attack, charge (move + attack), run.',
          'No 5-foot step after a full-round action.',
        ],
      },
    ],
    rightTitle: 'Free & Swift Actions',
    rightEntries: [
      {
        name: 'Free Action',
        body: [
          'Negligible time. Drop an item, speak,',
          'cease concentration. Multiple per round.',
        ],
      },
      {
        name: 'Swift Action',
          body: [
          'One per round (Expanded Psionics or',
          'special abilities). Does not replace others.',
        ],
      },
      {
        name: 'Immediate Action',
        body: [
          'One per round, even outside your turn.',
          'Consumes swift action next turn.',
        ],
      },
      {
        name: '5-Foot Step',
        body: [
          'Free. Does not provoke attacks of',
          'opportunity. Only when not already moved.',
        ],
      },
    ],
  },
  {
    ruleRefs: ['conditions', 'conditions.list'],
    leftTitle: 'Conditions A–F',
    leftEntries: [
      { name: 'Blinded', body: ['−2 AC, lose DEX to AC, −4 Spot/Search,', '50% miss chance, move at half speed.'] },
      { name: 'Confused', body: ['Roll d%: do nothing, babble, attack self', 'for 1 round, or attack nearest creature.'] },
      { name: 'Dazed', body: ['No actions. AC unaffected.'] },
      { name: 'Dazzled', body: ['−1 to attack rolls + Spot checks.'] },
      { name: 'Deafened', body: ['−4 initiative, 20% spell failure (verbal),', '−4 Listen, cannot hear.'] },
      { name: 'Entangled', body: ['−2 attack, −4 DEX. Move at half speed.', 'Casting requires Concentration DC 15.'] },
      { name: 'Exhausted', body: ['Half speed. −6 STR and DEX.', 'Resting 1 hour reduces to Fatigued.'] },
      { name: 'Fatigued', body: ['−2 STR and DEX. Cannot run or charge.'] },
      { name: 'Flat-Footed', body: ['Lose DEX bonus to AC. Cannot AoO.'] },
    ],
    rightTitle: 'Conditions G–U',
    rightEntries: [
      { name: 'Frightened', body: ['Must flee. −2 attack, saves, checks.'] },
      { name: 'Grappled', body: ['No threatened squares. −4 DEX,', '−4 attack vs. non-grappling foes.'] },
      { name: 'Helpless', body: ['DEX = 0. Coup de grace available.'] },
      { name: 'Nauseated', body: ['Only move action per round. No attacking,', 'casting, or concentrating.'] },
      { name: 'Panicked', body: ['Must flee, drop held items. −2 saves.'] },
      { name: 'Paralyzed', body: ['STR and DEX = 0. Helpless.'] },
      { name: 'Prone', body: ['−4 melee attack, +4 AC vs. ranged,', '−4 AC vs. melee. Stand = move action.'] },
      { name: 'Shaken', body: ['−2 attack, saves, skill, ability checks.'] },
      { name: 'Sickened', body: ['−2 attack, damage, saves, skill, ability.'] },
      { name: 'Stunned', body: ['Drop held items. No actions. −2 AC,', 'lose DEX bonus to AC.'] },
      { name: 'Unconscious', body: ['Helpless. Dying if HP between −1 and −9.'] },
    ],
  },
];

// ---------------------------------------------------------------------------
// Canvas page renderer
// ---------------------------------------------------------------------------

const PAGE_W = 768;
const PAGE_H = 1024;
const PARCHMENT  = '#e8dcc0';
const INK        = '#1a1208';
const RULE_LINE  = '#8a7a5a';
const RED_HEADER = '#7a1a0a';
const FAINT_BG   = '#f0e8d0';

function renderPage(
  title: string,
  entries: PageEntry[],
  rng: () => number,
  pageNum: number,
): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = PAGE_W;
  canvas.height = PAGE_H;
  const ctx = canvas.getContext('2d')!;

  // Parchment base
  ctx.fillStyle = PARCHMENT;
  ctx.fillRect(0, 0, PAGE_W, PAGE_H);

  // Subtle speckle texture
  for (let i = 0; i < 2000; i++) {
    const x = rng() * PAGE_W;
    const y = rng() * PAGE_H;
    const v = Math.floor(175 + rng() * 40);
    ctx.fillStyle = `rgba(${v},${v - 15},${v - 35},0.07)`;
    ctx.fillRect(x, y, 2, 2);
  }

  // Header bar
  ctx.fillStyle = '#2a1a08';
  ctx.fillRect(0, 0, PAGE_W, 44);
  ctx.font = 'bold 15px Georgia, serif';
  ctx.fillStyle = '#d4b878';
  ctx.textAlign = 'center';
  ctx.fillText(title.toUpperCase(), PAGE_W / 2, 28);

  // Horizontal rule under header
  ctx.strokeStyle = RULE_LINE;
  ctx.lineWidth = 0.8;
  ctx.beginPath();
  ctx.moveTo(24, 52);
  ctx.lineTo(PAGE_W - 24, 52);
  ctx.stroke();

  let y = 72;
  const MARGIN = 28;
  const COL_W = PAGE_W - MARGIN * 2;

  for (const entry of entries) {
    // Entry name + type badge
    ctx.font = `bold 13px Georgia, serif`;
    ctx.fillStyle = RED_HEADER;
    ctx.textAlign = 'left';
    ctx.fillText(entry.name, MARGIN, y);

    if (entry.type) {
      const nameW = ctx.measureText(entry.name).width;
      ctx.font = '10px Georgia, serif';
      ctx.fillStyle = RULE_LINE;
      ctx.fillText(`[${entry.type}]`, MARGIN + nameW + 8, y);
    }

    y += 4;

    // Rule under entry name
    ctx.strokeStyle = RULE_LINE;
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(MARGIN, y);
    ctx.lineTo(MARGIN + COL_W, y);
    ctx.stroke();

    y += 12;

    // Entry body lines
    ctx.font = '11px Georgia, serif';
    ctx.fillStyle = INK;
    ctx.textAlign = 'left';
    for (const line of entry.body) {
      ctx.fillText(line, MARGIN + 8, y);
      y += 16;
    }

    y += 10; // gap between entries

    if (y > PAGE_H - 60) break; // don't overflow
  }

  // Footer — page number
  ctx.font = '9px Georgia, serif';
  ctx.fillStyle = RULE_LINE;
  ctx.textAlign = 'center';
  ctx.fillText(`— ${pageNum} —`, PAGE_W / 2, PAGE_H - 18);

  // Footer rule
  ctx.strokeStyle = RULE_LINE;
  ctx.lineWidth = 0.6;
  ctx.beginPath();
  ctx.moveTo(24, PAGE_H - 28);
  ctx.lineTo(PAGE_W - 24, PAGE_H - 28);
  ctx.stroke();

  const tex = new THREE.CanvasTexture(canvas);
  return tex;
}

// ---------------------------------------------------------------------------
// Pre-render all pages (done once at construction)
// ---------------------------------------------------------------------------

function buildPageTextures(): { left: THREE.CanvasTexture; right: THREE.CanvasTexture }[] {
  const rng = _pagePrng;
  return SPREADS.map((spread, i) => ({
    left:  renderPage(spread.leftTitle,  spread.leftEntries,  rng, i * 2 + 1),
    right: renderPage(spread.rightTitle, spread.rightEntries, rng, i * 2 + 2),
  }));
}

// ---------------------------------------------------------------------------
// BookObject
// ---------------------------------------------------------------------------

const BOOK_OPEN_DURATION  = 0.45; // seconds
const BOOK_CLOSE_DURATION = 0.35;
const FLIP_DURATION       = 0.22;

const COVER_COLOR  = 0x4a0f0f; // burgundy
const BRASS_COLOR  = 0xb5832a;
const SPINE_COLOR  = 0x3a0c0c;

export class BookObject {
  readonly group: THREE.Group;

  private _isOpen = false;
  private _pageIndex = 0;           // current spread index
  private _pageTextures: { left: THREE.CanvasTexture; right: THREE.CanvasTexture }[];

  // Geometry
  private _coverLeft:  THREE.Mesh;
  private _coverRight: THREE.Mesh;
  private _pageLeft:   THREE.Mesh;
  private _pageRight:  THREE.Mesh;
  private _spine:      THREE.Mesh;

  // Animation state
  private _animState: 'idle' | 'opening' | 'closing' | 'flipping' = 'idle';
  private _animProgress = 0;
  private _animDuration = BOOK_OPEN_DURATION;
  private _flipDir = 1; // +1 forward, -1 back
  private _pendingRef: string | null = null;

  // The closed-cover mesh — used for click detection in main.ts
  readonly coverMesh: THREE.Mesh;

  get isOpen(): boolean { return this._isOpen; }
  get pageIndex(): number { return this._pageIndex; }
  get pageCount(): number { return SPREADS.length; }

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'book_rulebook';

    this._pageTextures = buildPageTextures();

    // Spine — center axis
    const spineGeo = new THREE.BoxGeometry(0.12, 0.20, 1.65);
    const spineMat = new THREE.MeshStandardMaterial({
      color: SPINE_COLOR, roughness: 0.80, metalness: 0.04,
    });
    this._spine = new THREE.Mesh(spineGeo, spineMat);
    this._spine.name = 'book_spine';
    this._spine.castShadow = true;
    this._spine.receiveShadow = true;
    this.group.add(this._spine);

    // Cover panels — left and right, hinged at spine edge
    const coverGeo = new THREE.BoxGeometry(1.1, 0.14, 1.65);
    const coverMat = new THREE.MeshStandardMaterial({
      color: COVER_COLOR, roughness: 0.75, metalness: 0.06,
    });

    this._coverLeft = new THREE.Mesh(coverGeo, coverMat.clone());
    this._coverLeft.name = 'book_cover_left';
    this._coverLeft.castShadow = true;
    this._coverLeft.receiveShadow = true;

    this._coverRight = new THREE.Mesh(coverGeo, coverMat.clone());
    this._coverRight.name = 'book_cover_right';
    this._coverRight.castShadow = true;
    this._coverRight.receiveShadow = true;

    // Gold title band on front cover (right panel when closed)
    const bandGeo = new THREE.BoxGeometry(0.88, 0.145, 0.04);
    const bandMat = new THREE.MeshStandardMaterial({
      color: BRASS_COLOR, roughness: 0.35, metalness: 0.92,
    });
    const titleBand = new THREE.Mesh(bandGeo, bandMat);
    titleBand.name = 'book_title_band';

    // Page surfaces (shown when open)
    const pageGeo = new THREE.PlaneGeometry(1.1, 1.65);

    this._pageLeft = new THREE.Mesh(
      pageGeo,
      new THREE.MeshStandardMaterial({
        map: this._pageTextures[0].left,
        roughness: 0.92,
        metalness: 0.0,
        side: THREE.FrontSide,
      }),
    );
    this._pageLeft.name = 'book_page_left';
    this._pageLeft.rotation.x = -Math.PI / 2;
    this._pageLeft.visible = false;

    this._pageRight = new THREE.Mesh(
      pageGeo,
      new THREE.MeshStandardMaterial({
        map: this._pageTextures[0].right,
        roughness: 0.92,
        metalness: 0.0,
        side: THREE.FrontSide,
      }),
    );
    this._pageRight.name = 'book_page_right';
    this._pageRight.rotation.x = -Math.PI / 2;
    this._pageRight.visible = false;

    this.group.add(this._coverLeft);
    this.group.add(this._coverRight);
    this.group.add(titleBand);
    this.group.add(this._pageLeft);
    this.group.add(this._pageRight);

    // coverMesh is the right cover — what main.ts raycasts for click detection
    this.coverMesh = this._coverRight;

    // Set initial closed positions
    this._applyClosed();
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  open(): void {
    if (this._isOpen || this._animState !== 'idle') return;
    this._animState = 'opening';
    this._animProgress = 0;
    this._animDuration = BOOK_OPEN_DURATION;
    this._pageLeft.visible  = true;
    this._pageRight.visible = true;
  }

  close(): void {
    if (!this._isOpen || this._animState !== 'idle') return;
    this._animState = 'closing';
    this._animProgress = 0;
    this._animDuration = BOOK_CLOSE_DURATION;
  }

  toggle(): void {
    if (this._isOpen) this.close();
    else this.open();
  }

  flipForward(): void {
    if (!this._isOpen || this._animState !== 'idle') return;
    if (this._pageIndex >= SPREADS.length - 1) return;
    this._flipDir = 1;
    this._startFlip();
  }

  flipBack(): void {
    if (!this._isOpen || this._animState !== 'idle') return;
    if (this._pageIndex <= 0) return;
    this._flipDir = -1;
    this._startFlip();
  }

  /**
   * Open to the spread that contains the given rule_ref.
   * If book is closed, opens it first then jumps.
   */
  openToRef(ruleRef: string): void {
    const idx = SPREADS.findIndex(s => s.ruleRefs.includes(ruleRef));
    if (idx === -1) {
      // Unknown ref — open to first spread
      if (!this._isOpen) this.open();
      return;
    }
    if (!this._isOpen) {
      this._pendingRef = ruleRef;
      this.open();
    } else {
      this._jumpToSpread(idx);
    }
  }

  update(dt: number): void {
    if (this._animState === 'idle') return;

    this._animProgress = Math.min(1, this._animProgress + dt / this._animDuration);
    const t = smoothstep(this._animProgress);

    if (this._animState === 'opening') {
      this._applyOpenProgress(t);
      if (this._animProgress >= 1) {
        this._isOpen = true;
        this._animState = 'idle';
        // Handle pending ref jump
        if (this._pendingRef !== null) {
          const ref = this._pendingRef;
          this._pendingRef = null;
          this.openToRef(ref);
        }
      }
    } else if (this._animState === 'closing') {
      this._applyOpenProgress(1 - t);
      if (this._animProgress >= 1) {
        this._isOpen = false;
        this._animState = 'idle';
        this._pageLeft.visible  = false;
        this._pageRight.visible = false;
        this._applyClosed();
      }
    } else if (this._animState === 'flipping') {
      this._applyFlipProgress(t);
      if (this._animProgress >= 1) {
        this._animState = 'idle';
        this._applyPageTextures();
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Private helpers
  // ---------------------------------------------------------------------------

  private _startFlip(): void {
    this._animState = 'flipping';
    this._animProgress = 0;
    this._animDuration = FLIP_DURATION;
    this._pageIndex += this._flipDir;
    this._pageIndex = Math.max(0, Math.min(SPREADS.length - 1, this._pageIndex));
  }

  private _jumpToSpread(idx: number): void {
    this._pageIndex = idx;
    this._applyPageTextures();
  }

  private _applyPageTextures(): void {
    const spread = this._pageTextures[this._pageIndex];
    (this._pageLeft.material  as THREE.MeshStandardMaterial).map = spread.left;
    (this._pageRight.material as THREE.MeshStandardMaterial).map = spread.right;
    (this._pageLeft.material  as THREE.MeshStandardMaterial).needsUpdate = true;
    (this._pageRight.material as THREE.MeshStandardMaterial).needsUpdate = true;
  }

  /** Layout when fully closed — all panels stacked flat */
  private _applyClosed(): void {
    // Spine centered
    this._spine.position.set(0, 0, 0);
    this._spine.rotation.set(0, 0, 0);

    // Left cover — to the left of spine, closed flat (rotated on top)
    this._coverLeft.position.set(-0.61, 0, 0);
    this._coverLeft.rotation.set(0, 0, 0);

    // Right cover — to the right of spine, forms top of stack
    this._coverRight.position.set(0.61, 0, 0);
    this._coverRight.rotation.set(0, 0, 0);

    // Pages hidden inside covers (pages are flat — just position them at cover level)
    this._pageLeft.position.set(-0.61, 0.08, 0);
    this._pageRight.position.set(0.61, 0.08, 0);
  }

  /** Interpolate between closed and open states */
  private _applyOpenProgress(t: number): void {
    // Covers swing out flat — left cover rotates Y: 0 → +PI/2 (swings left)
    // Right cover rotates Y: 0 → -PI/2 (swings right)
    // Actually: covers lay flat when open, so we rotate them DOWN (x-axis)
    // Closed: covers are upright (stacked), Open: covers lie flat on table
    // Hinge is at the spine edge of each cover panel.

    // Left cover: pivot at right edge (x=+0.55 in local space)
    // We fake this with position + rotation
    const openAngle = -Math.PI / 2; // lie flat
    const lAngle = openAngle * t;
    this._coverLeft.rotation.x  = lAngle;
    this._coverLeft.position.set(-0.61 - Math.sin(-lAngle) * 0.55 * t, Math.cos(-lAngle) * 0.07 * (1 - t), 0);

    const rAngle = openAngle * t;
    this._coverRight.rotation.x = rAngle;
    this._coverRight.position.set(0.61 + Math.sin(-rAngle) * 0.55 * t, Math.cos(-rAngle) * 0.07 * (1 - t), 0);

    // Pages become visible and flat at center
    this._pageLeft.position.set(-0.61, 0.075 - 0.075 * t, 0);
    this._pageRight.position.set( 0.61, 0.075 - 0.075 * t, 0);
  }

  /** Flip animation — brief UV fade + restore (simple texture swap at midpoint) */
  private _applyFlipProgress(t: number): void {
    // First half: fade out old; second half: fade in new
    const mat = this._pageRight.material as THREE.MeshStandardMaterial;
    if (t < 0.5) {
      mat.opacity = 1 - t * 2;
      mat.transparent = true;
    } else {
      if (t >= 0.5 && mat.opacity < 0.5) {
        // Swap texture at midpoint
        this._applyPageTextures();
      }
      mat.opacity = (t - 0.5) * 2;
      mat.transparent = true;
    }
    if (t >= 1) {
      mat.opacity = 1;
      mat.transparent = false;
    }
  }
}

function smoothstep(t: number): number {
  return t * t * (3 - 2 * t);
}

// ---------------------------------------------------------------------------
// QuestionStamp — "?" marker placed on surfaces for rule denial guidance.
// Doctrine §9: clicking a "?" opens rulebook to rule_ref. No explanation ever.
// ---------------------------------------------------------------------------

export class QuestionStamp {
  readonly mesh: THREE.Mesh;
  readonly ruleRef: string;

  constructor(ruleRef: string, position: THREE.Vector3) {
    this.ruleRef = ruleRef;

    // Small disc with "?" texture
    const geo  = new THREE.CylinderGeometry(0.08, 0.08, 0.015, 16);
    const tex  = QuestionStamp._makeTexture();
    const mat  = new THREE.MeshStandardMaterial({
      map: tex,
      roughness: 0.6,
      metalness: 0.1,
      emissive: new THREE.Color(0xffcc44),
      emissiveIntensity: 0.25,
    });
    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.name = `question_stamp_${ruleRef}`;
    this.mesh.position.copy(position);
    this.mesh.castShadow = false;
    this.mesh.receiveShadow = true;
  }

  private static _makeTexture(): THREE.CanvasTexture {
    const rng = _stampPrng;
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d')!;

    // Gold disc
    ctx.fillStyle = '#d4a820';
    ctx.beginPath();
    ctx.arc(64, 64, 60, 0, Math.PI * 2);
    ctx.fill();

    // Dark ring
    ctx.strokeStyle = '#7a5a08';
    ctx.lineWidth = 4;
    ctx.stroke();

    // "?" glyph
    ctx.font = 'bold 72px Georgia, serif';
    ctx.fillStyle = '#2a1a00';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('?', 64, 68);

    // Subtle speckle
    for (let i = 0; i < 200; i++) {
      const x = rng() * 128, y = rng() * 128;
      ctx.fillStyle = `rgba(0,0,0,0.04)`;
      ctx.fillRect(x, y, 1, 1);
    }

    return new THREE.CanvasTexture(canvas);
  }

  /** Pulse the stamp gently — call each frame */
  pulse(time: number): void {
    const mat = this.mesh.material as THREE.MeshStandardMaterial;
    mat.emissiveIntensity = 0.18 + Math.sin(time * 3.0) * 0.12;
  }
}

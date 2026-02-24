/**
 * RulebookObject — physical book controller for the PHB rules reference.
 *
 * Authority: WO-UI-RULEBOOK-01
 *
 * Wraps BookObject (book-object.ts) and provides:
 * - Open/close/flip/ribbon state machine (delegated to BookObject)
 * - Stamp handling via QuestionStamp (delegated to BookObject / main.ts)
 * - Positioned at shelf_rulebook anchor (x=2.0, y=0.04, z=4.75)
 *
 * Doctrine constraints enforced here:
 * - openToRef() accepts a rule_ref string only — no content, snippet, or preview
 * - No mechanical state imported or checked — A-RULES-OPEN: always openable
 * - BOOK_READ posture is triggered by the caller (main.ts) on every open
 *
 * Search constraint: searchRuleRef (rulebook-search.ts) returns a string ref only.
 * No snippet, excerpt, preview, text, content, or description is produced.
 */

import * as THREE from 'three';
import { BookObject, QuestionStamp } from './book-object';
import tableObjectsJson from '../../docs/design/LAYOUT_PACK_V1/table_objects.json';

// ---------------------------------------------------------------------------
// Layout Pack position lookup — shelf_rulebook anchor
// ---------------------------------------------------------------------------

interface _TOPos { x: number; y: number; z: number; }
interface _TOObj { name: string; position: _TOPos; rotation_y: number; }

function _rulebookPos(): _TOPos {
  const obj = (tableObjectsJson as { objects: _TOObj[] }).objects.find(
    o => o.name === 'RULEBOOK',
  );
  if (!obj) throw new Error('table_objects.json: RULEBOOK entry not found');
  return obj.position;
}

function _rulebookRot(): number {
  const obj = (tableObjectsJson as { objects: _TOObj[] }).objects.find(
    o => o.name === 'RULEBOOK',
  );
  if (!obj) throw new Error('table_objects.json: RULEBOOK entry not found');
  return obj.rotation_y;
}

// ---------------------------------------------------------------------------
// RulebookObject
// ---------------------------------------------------------------------------

/**
 * Physical rulebook controller.
 *
 * State machine: closed → opening → open → closing → closed
 * Page state:    pageIndex 0..N-1, advance via flipForward / flipBack
 * Ribbon/bookmark: openToRef() jumps directly to the spread for a rule_ref
 *
 * Stamp system: QuestionStamp objects are created by main.ts and placed on
 * surfaces. Clicking a stamp calls openToRef(stamp.ruleRef) — no inline text.
 *
 * A-RULES-OPEN: openToRef() has no precondition check. The book is always
 * openable regardless of game state.
 */
export class RulebookObject {
  /** Underlying book — open/close/flip/ribbon logic lives here. */
  readonly book: BookObject;

  /** Three.js group — add to scene. Positioned at shelf_rulebook anchor. */
  readonly group: THREE.Group;

  /** Cover mesh for ShelfDragController registration. */
  readonly coverMesh: THREE.Mesh;

  constructor() {
    this.book = new BookObject();

    // Position at the shelf_rulebook anchor from table_objects.json
    const pos = _rulebookPos();
    const rotY = _rulebookRot();
    this.book.group.position.set(pos.x, pos.y, pos.z);
    this.book.group.rotation.y = rotY;

    this.group = this.book.group;
    this.coverMesh = this.book.coverMesh;
  }

  // ---------------------------------------------------------------------------
  // State accessors
  // ---------------------------------------------------------------------------

  get isOpen(): boolean { return this.book.isOpen; }
  get pageIndex(): number { return this.book.pageIndex; }
  get pageCount(): number { return this.book.pageCount; }

  // ---------------------------------------------------------------------------
  // State machine — open / close / flip / ribbon
  // ---------------------------------------------------------------------------

  open(): void   { this.book.open(); }
  close(): void  { this.book.close(); }
  toggle(): void { this.book.toggle(); }

  flipForward(): void { this.book.flipForward(); }
  flipBack(): void    { this.book.flipBack(); }

  /**
   * Ribbon/bookmark navigation — open to the spread that contains rule_ref.
   *
   * A-RULES-OPEN: no precondition check. Always opens.
   * Returns void. No content, snippet, preview, or explanation produced.
   *
   * @param ruleRef - string identifier (e.g. 'combat.attack_roll')
   */
  openToRef(ruleRef: string): void {
    // A-RULES-OPEN: unconditional — no entity state, no pending state checked
    this.book.openToRef(ruleRef);
  }

  // ---------------------------------------------------------------------------
  // Animation tick
  // ---------------------------------------------------------------------------

  update(dt: number): void { this.book.update(dt); }
}

// ---------------------------------------------------------------------------
// Re-export QuestionStamp so callers can import from a single module.
// ---------------------------------------------------------------------------

export { QuestionStamp };

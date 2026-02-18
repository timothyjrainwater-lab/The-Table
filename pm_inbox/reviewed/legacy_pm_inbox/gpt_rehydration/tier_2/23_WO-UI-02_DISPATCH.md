# WO-UI-02 — Table UI Phase 2: TableObject Base System + Pick/Drag/Drop

**Lifecycle:** DISPATCH-READY
**Spec authority:** DOCTRINE_04_TABLE_UI_MEMO_V4.txt (UI contract)
**Prerequisite WOs:** WO-UI-01 (Gate F — ACCEPTED at `6237845`)
**Branch:** master (from commit `6237845`)

---

## Scope

Implement the TableObject base system (Slice 1 from doctrine §19) and prove it with one interactive object type: a card. Cards already exist on the table as the BeatIntent display from WO-UI-01 — this WO promotes that display to a first-class draggable TableObject with pick/drag/drop constraints, zone awareness, and declare→point→confirm interaction.

**What exists (from WO-UI-01):**
- Three.js + TypeScript + Vite project in `client/`
- Table scene with 3 zone boundaries (map/player/DM)
- 3 camera postures (STANDARD, DOWN, LEAN_FORWARD) with smooth transitions
- WebSocket bridge to backend at `ws://localhost:8765/ws`
- BeatIntent display as a canvas-textured 3D card on the table surface
- PENDING/REQUEST handshake types in `aidm/ui/pending.py`
- Gate F: 10/10 PASS

**In scope:**
1. Frontend: TableObject base class/interface with lifecycle (spawn, pick, drag, drop, destroy)
2. Frontend: Pick/drag/drop interaction with raycasting, zone constraints, and snap behavior
3. Frontend: Card as the first TableObject type — promote the existing BeatIntent card
4. Frontend: Zone constraint enforcement — objects respect zone boundaries during drag
5. Frontend: Keyboard-only path for pick/drag/drop (doctrine §6 accessibility requirement)
6. Backend: TableObject registry types (frozen dataclasses) — object identity, position, zone membership
7. End-to-end: Card pick → drag to zone → drop → position update crosses WebSocket boundary
8. Backend: Gate G tests proving the contracts

**NOT in scope (pushed to UI-03+):**
- Dice tray + dice tower + physics (Slice 2)
- Rulebook + "?" stamps (Slice 3)
- Notebook ink (Slice 4)
- Handout printer (Slice 5)
- Map tokens + overlays (Slice 6)
- Full runtime integration (Slice 7)
- Radial finger menu (deferred until Slice 3+ when tools are needed)
- Recycle well (deferred until handouts exist)

---

## Hard Stop Conditions

**If any of these are false, the builder stops and reports. No improvisation.**

1. **Cannot run the existing `client/` project.** If `npm install` or `npm run dev` fails in the `client/` directory from WO-UI-01, stop. Report as dependency blocker.

2. **Cannot pick 3D objects via raycasting.** If Three.js raycasting cannot reliably detect mouse/pointer hits on table-surface objects at acceptable performance, stop. Report technical constraint.

3. **Cannot establish zone boundaries in the scene.** If the existing table scene zones from WO-UI-01 are not programmatically queryable (i.e., the builder cannot determine which zone a world-space position belongs to), stop. Report the boundary gap.

---

## Contract Changes

### Change 1: TableObject base system
**Location:** frontend code in `client/`
**What:** Base class or interface for all objects that live on the table surface.

Requirements:
- Every TableObject has: `id: string`, `kind: string`, `position: {x, y, z}`, `zone: string`, `pickable: boolean`
- Lifecycle methods: `onSpawn()`, `onPick()`, `onDrag(position)`, `onDrop(zone)`, `onDestroy()`
- TableObject renders as a Three.js Object3D (or Group) added to the scene
- TableObjects are managed by a registry (Map or similar) for lookup by id
- Only one object may be picked at a time (single-selection constraint)

### Change 2: Pick/drag/drop interaction
**Location:** frontend code in `client/`
**What:** Pointer-based interaction system for picking up, dragging, and dropping TableObjects.

Requirements:
- Pick: pointer-down on a pickable TableObject lifts it (visual feedback — slight elevation or glow)
- Drag: pointer-move while picked moves the object along the table surface plane (Y-constrained raycasting)
- Drop: pointer-up places the object at the current position if the zone allows it
- Zone constraint: objects cannot be dropped outside valid zones (snap back to pick-up position on invalid drop)
- Cancel: right-click or Escape cancels a drag in progress (returns to pick-up position)
- Drag must not fight the camera — camera posture controls are disabled during drag
- Input-to-feedback latency target: drag should follow pointer within 1 frame (doctrine §17)

### Change 3: Card as first TableObject
**Location:** frontend code in `client/`
**What:** Promote the existing BeatIntent canvas-textured card to a TableObject.

Requirements:
- Card implements the TableObject interface
- Card is pickable and draggable
- Card displays text content (BeatIntent data from WebSocket, same as WO-UI-01)
- Card click (without drag) still sends DeclareActionIntent (preserve WO-UI-01 behavior)
- Card drag + drop sends a position update over WebSocket
- Multiple cards can coexist on the table (for future BeatIntent stacking)

### Change 4: Zone constraint enforcement
**Location:** frontend code in `client/`
**What:** Zones from the table scene constrain where objects can be placed.

Requirements:
- Each zone has a name (e.g., "player", "map", "dm") and a bounding region
- During drag, visual feedback shows whether the current position is a valid drop target
- On drop in an invalid zone: object snaps back to its previous valid position
- Cards start in the "player" zone by default
- Zone boundaries are the same visual boundaries from WO-UI-01 (colored planes or wireframes)

### Change 5: Keyboard-only path
**Location:** frontend code in `client/`
**What:** Keyboard navigation for pick/drag/drop per doctrine §6.

Requirements:
- Tab/Shift-Tab cycles focus through pickable objects on the table
- Enter/Space picks up the focused object
- Arrow keys move a picked object in cardinal directions (step distance = reasonable grid snap)
- Enter/Space drops the object at current position
- Escape cancels drag
- Focused object has a visible highlight (border, glow, or outline)

### Change 6: TableObject registry types (backend)
**Location:** the module where UI protocol state lives — confirm path before writing (likely `aidm/ui/table_objects.py` or extend `aidm/ui/pending.py`)
**What:** Frozen dataclasses for table object identity and position.

Types:
- `TableObjectState(object_id: str, kind: str, position: tuple, zone: str)` — server-side record of an object's position
- `ObjectPositionUpdate(object_id: str, new_position: tuple, new_zone: str)` — client→server position change

State rules:
- ObjectPositionUpdate is a REQUEST type (follows doctrine §16 — UI sends REQUEST only)
- Server validates zone membership (server is authoritative for valid zones)
- Server acknowledges with updated TableObjectState over WebSocket
- **Presentation-only constraint:** ObjectPositionUpdate and TableObjectState are table layout data. They MUST NOT produce Events, enter EventLog, write to Oracle stores (FactsLedger, StoryState, UnlockState), or affect WorkingSet compilation. Position state lives in a separate UI layout namespace — it is not game state.
- **No teaching on constraint enforcement:** Invalid zone drops snap back silently. No explanatory text, no "can't drop here" messages. If denial feedback is needed, it follows doctrine §9 (spoken line + "?" stamp only). This WO uses silent snap-back only.

### Change 7: End-to-end card drag round trip
**Location:** frontend + backend WebSocket bridge
**What:** Prove pick/drag/drop crosses the WebSocket boundary.

1. Card exists on table surface (spawned from BeatIntent data or test harness)
2. Player picks up card (pointer-down or keyboard)
3. Player drags card to a new position in a valid zone
4. Player drops card (pointer-up or keyboard)
5. Frontend sends `ObjectPositionUpdate(object_id, new_position, new_zone)` over WebSocket
6. Backend receives, validates zone, sends back `TableObjectState` acknowledgment
7. Frontend confirms position (or snaps back if server rejects)

This can use the same dev harness approach from WO-UI-01. The point is proving the contract crosses the boundary with zone validation.

### Change 8: Gate G tests (13 minimum)
**Location:** `tests/test_ui_gate_g.py`
**What:** 13 tests covering backend contracts.

Test breakdown:
- UI-G1 (TableObject types): 3 tests
  - TableObjectState is a frozen dataclass with object_id, kind, position, zone
  - ObjectPositionUpdate is a frozen dataclass with object_id, new_position, new_zone
  - ObjectPositionUpdate has no outcome/legality fields (REQUEST-only constraint)

- UI-G2 (Zone validation): 3 tests
  - Valid zone names are defined and enumerable
  - Position update to invalid zone is rejected (validation function returns error/None)
  - Position update to valid zone is accepted

- UI-G3 (Registry consistency): 2 tests
  - Object registry tracks objects by id (add/get/remove)
  - Duplicate object_id is rejected or overwrites cleanly (builder's choice, but deterministic)

- UI-G4 (Hard bans — static scan): 2 tests
  - No tooltip/popover/snippet strings in UI schema code (doctrine §3 — same as Gate F)
  - No "do the action" verbs in new REQUEST type names

- UI-G5 (Drift guards — Operator-mandated invariants): 3 tests
  - ObjectPositionUpdate is not registered as an event type in EventLog or replay_runner (no canonical path)
  - TableObjectState / ObjectPositionUpdate modules do not import from `aidm/oracle/`, `aidm/core/event_log.py`, or `aidm/core/replay_runner.py` (no backflow into canonical stores)
  - Zone constraint rejection produces no user-facing explanation string — static scan for tooltip/popover/error-message patterns in the zone validation module

---

## Binary Decisions (Builder must follow these exactly)

1. **Card is the first and only TableObject type in this WO.** No tokens, dice, handouts, or other objects. Prove the base system with one type.

2. **Pick/drag/drop uses Three.js raycasting, not DOM events.** Objects are 3D scene objects, not HTML overlays. Interaction happens in 3D space.

3. **Single-selection only.** One object picked at a time. Multi-select is a future feature.

4. **Zone validation lives on the server.** Frontend applies optimistic constraints (snap-back on invalid), but the server is the authority. Frontend does not hard-block zone transitions — it sends the request and respects the server's answer.

5. **No radial menu in this WO.** The radial finger menu (doctrine §8) is deferred to Slice 3+ when tool-substitution actions (notebook ink, clipboard) require it. Pick/drag/drop is direct manipulation, not menu-driven.

6. **No physics.** Card drag is surface-constrained plane movement. No rigid body, no bounce, no collision. Physics enters with dice in Slice 2.

7. **TableObject registry types go in `aidm/ui/`.** Same boundary layer as PENDING/REQUEST types from WO-UI-01. Frontend consumes via WebSocket JSON. Backend is source of truth.

8. **Keyboard path is required, not optional.** Doctrine §6 mandates keyboard-only accessibility. This is a gate requirement, not a nice-to-have. The builder must verify keyboard pick/drag/drop works without a mouse.

---

## Integration Seams

1. **Existing BeatIntent card → TableObject.** The BeatIntent card from WO-UI-01 is the migration target. Builder must confirm: (a) the card's Three.js mesh is accessible, (b) it can be wrapped in the TableObject interface without breaking the existing click→DeclareActionIntent behavior.

2. **Existing zone boundaries → constraint system.** The table scene from WO-UI-01 has visible zone boundaries. Builder must confirm these are programmatically queryable (bounding boxes, named meshes, or similar) so the constraint system can determine zone membership.

3. **Existing WebSocket bridge → position updates.** The `ws-bridge.ts` from WO-UI-01 handles message send/receive. Builder must extend it to support ObjectPositionUpdate messages and TableObjectState acknowledgments.

4. **PENDING/REQUEST types → new REQUEST type.** `ObjectPositionUpdate` follows the same frozen-dataclass + `to_dict()`/`from_dict()` pattern as the existing types in `aidm/ui/pending.py`. Builder must confirm the pattern and extend it.

5. **Camera controls ↔ drag interaction.** Camera posture switching (keyboard 1/2/3) must not conflict with drag operations. Builder must ensure camera controls are disabled during active drag.

---

## Assumptions to Validate

1. **BeatIntent card mesh is accessible.** Confirm the Three.js Object3D for the BeatIntent card can be accessed and wrapped in the TableObject interface.

2. **Zone boundaries are queryable.** Confirm the zone planes/meshes from WO-UI-01 have names or bounding geometry that can be tested programmatically (point-in-zone checks).

3. **Raycasting performance is acceptable.** Confirm Three.js raycasting against table-surface objects runs within frame budget (no noticeable lag on pointer-move during drag).

4. **`aidm/ui/` boundary gate status.** WO-UI-01 added `pending.py` and `camera.py` to `aidm/ui/`. Confirm the gate knows about this package. If adding a new file (e.g., `table_objects.py`), confirm no gate registration is needed (Field Manual #26 — sub-files within an existing package are transparent).

---

## Success Criteria (13 tests minimum, all must pass)

1. TableObjectState is a frozen dataclass with object_id, kind, position, zone (UI-G1)
2. ObjectPositionUpdate is a frozen dataclass with object_id, new_position, new_zone (UI-G1)
3. ObjectPositionUpdate has no outcome/legality fields (UI-G1)
4. Valid zone names are defined and enumerable (UI-G2)
5. Position update to invalid zone is rejected (UI-G2)
6. Position update to valid zone is accepted (UI-G2)
7. Object registry tracks objects by id (UI-G3)
8. Duplicate object_id handling is deterministic (UI-G3)
9. No tooltip/popover/snippet strings in UI code (UI-G4)
10. No "do the action" verbs in REQUEST type names (UI-G4)
11. ObjectPositionUpdate is not registered as an event type — no canonical path (UI-G5)
12. Table object modules do not import from Oracle/EventLog/replay_runner — no backflow (UI-G5)
13. Zone constraint rejection produces no user-facing explanation string (UI-G5)

Regression: Gates A-F (111 tests total) must all still pass. 0 regressions allowed.

Frontend validation (manual by builder):
- Card is pickable via pointer-down (visual lift feedback)
- Card follows pointer during drag (1-frame latency target)
- Card drops at valid position in valid zone
- Card snaps back on invalid zone drop
- Keyboard Tab/Enter/Arrow/Escape path works for pick/drag/drop
- Drag + drop sends ObjectPositionUpdate over WebSocket
- Server acknowledges with TableObjectState
- Camera controls disabled during drag
- Existing BeatIntent click→DeclareActionIntent still works

---

## Delivery

1. Write debrief to `pm_inbox/DEBRIEF_WO-UI-02.md` with 4 mandatory sections (Scope Accuracy, Discovery Log, Methodology Challenge, Field Manual Entry). 500-word cap.
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md` — add WO-UI-02 to verdicts table (leave verdict blank; PM fills in).
3. `git add` ALL files (code + tests + client/ + debrief + briefing). Exclude `node_modules/`.
4. Commit with descriptive message.
5. Add commit hash to debrief header.
6. Amend commit to include the hash.

**Debrief hash rule (Field Manual #19):** Commit first, read hash from `git log --oneline -1`, write to debrief, then amend.

**Note on `client/` directory:** `node_modules/` and `dist/` are already in `.gitignore`. Do NOT commit them.

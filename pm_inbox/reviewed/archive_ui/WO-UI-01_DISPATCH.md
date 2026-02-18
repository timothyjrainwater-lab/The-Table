# WO-UI-01 — Table UI Phase 1: Client Bootstrap + Slice 0 + One PENDING Round Trip

**Lifecycle:** DISPATCH-READY
**Spec authority:** DOCTRINE_04_TABLE_UI_MEMO_V4.txt (UI contract)
**Prerequisite WOs:** WO-DIRECTOR-02 (Gate E — ACCEPTED at `0834f4e`)
**Branch:** master (from commit `0834f4e`)

---

## Scope

Bootstrap the Three.js frontend client and deliver Slice 0 as a thin vertical slice: table scene renders, camera postures switch smoothly, one declare→point→confirm interaction path works, one real PENDING round trip crosses the WebSocket boundary and comes back. That proves the architecture. Everything else is later slices.

**The frontend does not exist.** No JavaScript, no package.json, no Three.js. This WO creates it.

**What exists (backend):**
- WebSocket protocol (`aidm/schemas/ws_protocol.py`) — message types, frozen dataclasses
- WebSocket server (`aidm/server/`) — Starlette ASGI app, session lifecycle
- Spatial types (`aidm/schemas/position.py`) — Position, distance, adjacency
- Character Sheet terminal UI (`aidm/ui/character_sheet.py`) — text-only

**In scope:**
1. Frontend: Three.js + TypeScript + Vite project in `client/`
2. Frontend: table scene that renders and runs locally
3. Frontend: 3 camera postures (STANDARD, DOWN, LEAN_FORWARD) with smooth transitions
4. Backend: PENDING handshake types (frozen dataclasses) + one-at-a-time state machine
5. Backend: REQUEST intent types (frozen dataclasses) — minimum set for the vertical slice
6. End-to-end: one declare→point→confirm path that exercises a PENDING round trip over WebSocket
7. Backend: Gate F tests proving the contracts
8. Frontend: BeatIntent display — fetch the latest BeatIntent from Python side, render as a physical card or text strip on the table surface (proves the live loop drives UI)

**NOT in scope (pushed to UI-02+):**
- TableObject base system + pick/drag/drop constraints (Slice 1)
- Dice tray + dice tower + physics (Slice 2)
- Rulebook + "?" stamps (Slice 3)
- Notebook ink (Slice 4)
- Handout printer (Slice 5)
- Map tokens + overlays (Slice 6)
- Full runtime integration (Slice 7)

---

## Hard Stop Conditions

**If any of these are false, the builder stops and reports. No improvisation.**

1. **Cannot run Node.js toolchain locally.** If `node --version` fails or npm is unavailable, stop. Report as environment blocker.

2. **Cannot render a basic Three.js scene at acceptable frame rate.** If the target machine cannot render a simple scene (< 30fps on a basic scene), stop. Report hardware/driver constraint.

3. **Cannot establish the WebSocket bridge contract.** If the existing Starlette server cannot be started or does not accept connections, stop. Report the blocking dependency.

---

## Contract Changes

### Change 1: Frontend bootstrap
**Location:** new directory — `client/` at project root
**What:** Minimal Three.js + TypeScript + Vite project.

Requirements:
- `package.json` with Three.js, TypeScript, Vite
- `npm install` succeeds, `npm run dev` starts
- WebSocket connection to the backend at configurable URL (default `ws://localhost:8765`)
- License gate: MIT/BSD/Apache only. No GPL/AGPL without explicit Operator acceptance (doctrine §18).
- `node_modules/` added to `.gitignore` — never committed

### Change 2: Table scene + camera postures
**Location:** frontend code in `client/`
**What:** Three.js scene that renders a table surface with 3 camera postures from doctrine §5.

Postures:
- `STANDARD` — seated table view (default on load)
- `DOWN` — reading/writing view (looking down at player-edge)
- `LEAN_FORWARD` — map engagement view (angled toward center, no top-down god cam)

Requirements:
- Posture switching via keyboard shortcut or UI control (builder's choice — this is dev UX, not final UX)
- Transitions are smooth and interruptible (new posture command cancels in-progress transition)
- Table surface has visible zone boundaries (even as simple colored planes or wireframes)

### Change 3: PENDING handshake types
**Location:** the module where UI protocol state lives — confirm path before writing (likely `aidm/ui/pending.py` or extend `aidm/schemas/ws_protocol.py`)
**What:** Frozen dataclasses for the PENDING handshake protocol from UI doctrine §7.

Types (Phase 1 minimum):
- `PendingRoll(spec: str, pending_handle: str)` — dice formula only, no DC
- `PendingPoint(target_type: str, valid_targets: tuple)` — targeting mode

State machine rules:
- Only one PENDING active at a time
- New PENDING cancels existing PENDING
- PENDING clears when corresponding REQUEST is received or runtime cancels

### Change 4: REQUEST intent types
**Location:** same module as PENDING types or extend `aidm/schemas/ws_protocol.py`
**What:** UI→runtime request types from doctrine §16. Phase 1 minimum:

- `DeclareActionIntent(action_kind: str, source_ref: str)` — declaration (voice or click)
- `DiceTowerDropIntent(dice_ids: tuple, pending_roll_handle: str)` — dice drop (for PENDING_ROLL resolution)

All REQUEST types are frozen dataclasses. UI sends REQUEST only; never asserts legality or outcomes (§2).

**Hard ban enforcement:** No REQUEST types named ROLL, CAST, ATTACK, END_TURN, or any other "do the action" verb. These bypass declare→point→confirm and violate doctrine §8. Gate test enforces this.

### Change 5: One PENDING round trip (end-to-end vertical slice)
**Location:** frontend + backend WebSocket bridge
**What:** Prove the architecture with one real round trip:

1. Backend emits `PENDING_ROLL(spec="1d20", pending_handle="test_roll_001")` over WebSocket
2. Frontend receives it, enters PENDING_ROLL mode (visual indicator — even just a text overlay)
3. Player clicks to "drop dice" (any interaction — button, click, keyboard)
4. Frontend sends `DiceTowerDropIntent(dice_ids=("d20",), pending_roll_handle="test_roll_001")` over WebSocket
5. Backend receives the REQUEST, clears the PENDING, sends back a STATE/EVENT acknowledgment
6. Frontend clears the PENDING mode

This can be triggered by a dev command or test harness — it does not need to be wired to the real runtime resolution pipeline. The point is proving the contract crosses the boundary correctly.

### Change 6: BeatIntent display on table (live loop proof)
**Location:** frontend
**What:** Fetch or receive the latest BeatIntent/PromptPack data from the Python backend and render it on the table surface as a physical card, paper strip, or text block.

Requirements:
- The data comes over WebSocket (either polled or pushed)
- It renders as a visible object on the table (not a browser DOM overlay — it exists in the 3D scene)
- Clicking or interacting with it triggers a DeclareActionIntent (completing one declare→point→confirm cycle)

This proves "the live Oracle→Director→Lens loop drives UI state." The rendering can be minimal — a text card is sufficient.

### Change 7: Gate F tests (10 minimum)
**Location:** `tests/test_ui_gate_f.py`
**What:** 10 tests covering backend contracts.

Test breakdown:
- UI-F1 (PENDING state machine): 3 tests
  - PendingRoll is a frozen dataclass with spec and pending_handle
  - Only one PENDING active at a time — new PENDING cancels old
  - PENDING clears on REQUEST receipt

- UI-F2 (REQUEST schema): 3 tests
  - All REQUEST types are frozen dataclasses with no outcome/legality fields
  - REQUEST types serialize/deserialize cleanly
  - No action-verb REQUEST types (ROLL, CAST, ATTACK, END_TURN) — static scan

- UI-F3 (Camera postures): 2 tests
  - STANDARD, DOWN, LEAN_FORWARD defined as posture enum
  - Any posture→any posture transition is valid

- UI-F4 (Hard bans — static scan): 2 tests
  - No tooltip/popover/snippet strings in UI schema code (doctrine §3)
  - No "do the action" verbs in REQUEST type names

---

## Binary Decisions (Builder must follow these exactly)

1. **Frontend goes in `client/` at project root.** Not inside `aidm/`. Separate application connecting via WebSocket.

2. **Three.js + TypeScript + Vite.** Stack decision is made (doctrine §18). No alternatives.

3. **PENDING and REQUEST types are backend contracts in `aidm/`.** The frontend consumes them via the WebSocket protocol serialization. These are not frontend code.

4. **The PENDING round trip can use a test harness / dev command.** It does not need to connect to the real play loop runtime. The point is proving the WebSocket contract shape.

5. **No dice physics, no token rendering, no rulebook, no notebook, no object dragging.** Phase 1 is camera + surface + one round trip + BeatIntent display. Everything else is UI-02+.

6. **Hard ban enforcement is a gate, not a guideline.** Tooltips, popovers, snippets, or action-verb REQUESTs → gate test fails. For debug, use a dev overlay that is explicitly forbidden in release mode, or console logs only.

7. **If `aidm/ui/` is a new boundary gate layer, register it.** `aidm/ui/` already has `character_sheet.py` — check whether the gate already knows about it. If not, register (Field Manual #23).

---

## Integration Seams

1. **Frontend ↔ WebSocket ↔ Backend.** The frontend connects to the existing Starlette server. Builder must confirm: (a) server starts, (b) message format is JSON over WebSocket, (c) the existing protocol handshake works.

2. **PENDING → UI → REQUEST → Backend.** The vertical slice exercises this full cycle. The backend emits PENDING, the frontend reacts and sends REQUEST, the backend acknowledges. This proves the contract shape even if the backend handler is a stub.

3. **BeatIntent data → Frontend.** The existing `invoke_director()` produces BeatIntent. The builder needs a mechanism to surface this over WebSocket. This can be a new server→client message type or a poll endpoint. Builder discovers the cleanest path.

4. **Boundary gate.** Check `aidm/ui/` registration status. If unregistered, register it.

---

## Assumptions to Validate

1. **WebSocket server starts.** Confirm `aidm/server/app.py` can be run. If it has unmet dependencies, document them.

2. **ws_protocol.py serialization format.** Confirm it's JSON. The frontend must match.

3. **Node.js is available.** `node --version` and `npm --version` must succeed. If not → hard stop.

4. **`aidm/ui/` boundary gate status.** Already has `character_sheet.py`. Check if the gate knows about it.

---

## Success Criteria (10 tests minimum, all must pass)

1. PendingRoll is a frozen dataclass with spec and pending_handle (UI-F1)
2. Only one PENDING active at a time — new cancels old (UI-F1)
3. PENDING clears when corresponding REQUEST is received (UI-F1)
4. All REQUEST types are frozen dataclasses with no outcome/legality fields (UI-F2)
5. REQUEST types serialize/deserialize cleanly (UI-F2)
6. No action-verb REQUEST types exist (UI-F2 — static scan)
7. Camera postures STANDARD, DOWN, LEAN_FORWARD are defined (UI-F3)
8. Any posture→any posture transition is valid (UI-F3)
9. No tooltip/popover/snippet strings in UI code (UI-F4 — static scan)
10. No "do the action" verbs in REQUEST type names (UI-F4)

Regression: Gates A-E (101 tests total) must all still pass. 0 regressions allowed.

Frontend validation (manual by builder):
- `client/` exists with `package.json`
- `npm install` succeeds
- `npm run dev` starts and renders a table scene
- Camera postures switch smoothly
- WebSocket connects to backend
- PENDING round trip completes (PENDING emitted → REQUEST sent → ACK received → PENDING cleared)
- BeatIntent data renders on the table surface

---

## Delivery

1. Write debrief to `pm_inbox/DEBRIEF_WO-UI-01.md` with 4 mandatory sections (Scope Accuracy, Discovery Log, Methodology Challenge, Field Manual Entry). 500-word cap.
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md` — add WO-UI-01 to verdicts table (leave verdict blank; PM fills in).
3. `git add` ALL files (code + tests + client/ + debrief + briefing). Exclude `node_modules/`.
4. Commit with descriptive message.
5. Add commit hash to debrief header.
6. Amend commit to include the hash.

**Debrief hash rule (Field Manual #19):** Commit first, read hash from `git log --oneline -1`, write to debrief, then amend.

**Note on `client/` directory:** Add `node_modules/` and any build output directories to `.gitignore`. Do NOT commit `node_modules/`.

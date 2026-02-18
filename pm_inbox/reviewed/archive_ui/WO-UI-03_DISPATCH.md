# WO-UI-03 — Dice Tray Fidget + Dice Tower Ritual + PENDING_ROLL Handshake

**Lifecycle:** DISPATCH-READY
**Spec authority:** Operator directive (UI Phase 3 target selection + non-negotiable guardrails)
**Prerequisite WOs:** WO-UI-ZONE-AUTHORITY (ACCEPTED at `40fa32a`)
**Branch:** master (from commit `40fa32a`)

---

## Scope

Bring PENDING_ROLL to life with visible dice. The player sees dice in a tray, picks them up, drops them in the tower, and the result — already determined by Box — plays out as a ritual animation. UI never generates mechanical authority. This is Slice 2 of the Table UI spec.

**In scope:**
1. Dice tray zone with fidget-ready dice objects (idle animation / pick-up interaction)
2. Dice tower zone that accepts dropped dice and plays a result-reveal ritual
3. PENDING_ROLL → CONFIRMED handshake integration (Box provides outcome, UI animates it)
4. Gate tests: no mechanical authority from UI, PENDING handshake determinism, replay stability

**NOT in scope:**
- New roll types or mechanics (Box is unchanged)
- Dice physics simulation (no real physics engine — animation only)
- Sound effects or audio (BURST-001 scope)
- New camera postures
- WebSocket position handler wiring beyond what PENDING_ROLL requires
- Any changes outside `aidm/ui/`, `client/src/`, and `tests/`

---

## Hard Stop Conditions

1. **If PENDING_ROLL does not exist in the PENDING type system.** Confirm the module that defines PENDING types includes a roll-specific pending state. If it does not exist and cannot be created as a contained module (≤100 lines) within WO scope, stop and report.
2. **If Box does not expose roll outcomes in a format the UI can consume.** The UI needs the authoritative roll result (die faces, total, success/failure) to animate. If Box results are not accessible from the UI layer without backflow, stop and report.
3. **If dice objects cannot be represented as TableObjects.** Confirm the TableObject base system (from WO-UI-02) can represent dice with pick/drag/drop. If the base class requires structural changes beyond adding a new object type, stop and report.
4. **If the PENDING handshake requires modifications to the core PENDING state machine.** If the existing PENDING→CONFIRMED/REJECTED transition cannot accommodate PENDING_ROLL without changing the state machine contract, stop and report what changes are needed.

---

## Non-Negotiable Guardrails (Operator Directive)

These are hard laws, not suggestions. Violation is a stop condition.

1. **UI never rolls dice.** UI requests a roll from Box, receives the authoritative result, then animates the ritual/fidget to match the already-determined outcome. No RNG in the UI layer.
2. **RNG isolation remains Box-only.** Any "physics randomness" in the tray/tower animation must be seeded from the authoritative outcome or be purely cosmetic (no divergence on replay). The dice tower ritual is a visualization, not a computation.
3. **Handshake is a contract, not a vibe.** PENDING_ROLL → CONFIRMED/REJECTED must be deterministic and testable. Idempotent retries produce the same state transition. No implicit timeouts or silent failures.

---

## Contract Changes

### Change 1: Dice as TableObject
**Location:** the module that defines TableObject types — confirm file path before writing
**What:** Add a `DiceObject` (or equivalent) as a new TableObject type. Dice live in the dice tray zone by default. They support pick (grab from tray) and drop (into tower zone). The dice object carries a visual state: idle (in tray, fidget-ready), held (picked up), and rolling (in tower, animating result). No mechanical state — all mechanics come from Box.

### Change 2: Dice Tray Zone
**Location:** `aidm/ui/zones.json` (add zone) + the module that renders zones — confirm file path before writing
**What:** Add a dice tray zone to `zones.json`. This zone is the spawn/rest location for dice objects. When dice are idle in the tray, they display a subtle fidget animation (gentle rock, slight glow, or equivalent low-effort idle state). The fidget is cosmetic only — no state changes.

### Change 3: Dice Tower Zone
**Location:** `aidm/ui/zones.json` (add zone) + the module that renders zones — confirm file path before writing
**What:** Add a dice tower zone to `zones.json`. When a dice object is dropped into this zone, it triggers the roll ritual: the UI sends a roll confirmation to the backend, receives the authoritative result from Box, and plays a result-reveal animation. The tower is a drop target, not a physics engine.

### Change 4: PENDING_ROLL Handshake Wiring
**Location:** the module that defines PENDING types and the WebSocket message handler — confirm file paths before writing
**What:** Wire the PENDING_ROLL flow:
1. When a roll is needed (e.g., attack roll, saving throw), the backend sends a PENDING_ROLL message with: what roll is needed, which dice, and any modifiers.
2. The UI displays dice in the tray matching the pending roll (e.g., 1d20 shows one d20).
3. The player picks up dice and drops them in the tower.
4. The UI sends a "roll confirmed" message to the backend.
5. The backend (Box) resolves the roll authoritatively and sends the result back.
6. The UI plays the result animation (dice faces showing the outcome, total displayed).
7. State transitions to CONFIRMED (or REJECTED if the roll was cancelled/invalid).

### Change 5: Result-Reveal Animation
**Location:** the module that handles dice tower rendering — confirm file path before writing
**What:** When the authoritative result arrives from Box, animate the dice to show the correct face values. The animation must be deterministic given the same input (same result → same animation every time). No random variation in the reveal — the "randomness" is purely in the pre-reveal tumble (cosmetic), and the final face positions are derived from the Box result.

### Change 6: Gate Tests
**Location:** `tests/test_ui_gate_g.py`
**What:** Add gate tests for UI Phase 3:

- **UI-G7-no-mechanical-authority:** Assert that no UI module (in `client/src/`) contains RNG calls, roll resolution, or modifier application. Scan for `Math.random`, `crypto.getRandomValues`, dice roll functions, and modifier arithmetic. The UI must be a pure consumer of Box results.

- **UI-G7-pending-handshake-determinism:** Assert that the PENDING_ROLL → CONFIRMED transition is deterministic. Given the same PENDING_ROLL input, the same confirmation message produces the same state transition. Test with multiple identical inputs and assert identical outputs. No implicit timeouts.

- **UI-G7-replay-stability:** Assert that the same sequence of PENDING_ROLL → confirm → result messages produces the same final UI state. This is the replay guarantee — if the event log replays, the UI state machine arrives at the same state.

---

## Binary Decisions

1. **Dice are TableObjects.** No separate object system for dice. They use the same pick/drag/drop infrastructure as cards.
2. **Dice tower is a zone, not a 3D model.** The "tower" is a drop-target zone with animation. No 3D mesh tower unless trivially cheap.
3. **One die type at a time.** Start with d20 only. Other die types (d6, d8, d12, d4, d10) are future scope. The infrastructure must support multiple types, but only d20 needs to render.
4. **Fidget is CSS/shader only.** No physics engine for idle animation. Gentle transform oscillation or equivalent.
5. **Animation is deterministic.** Same Box result → same final dice face display. Pre-reveal tumble may vary cosmetically but final state is pinned.
6. **No sound.** Audio is BURST-001 scope. Silent animations only.

---

## Integration Seams

**Seam 1: PENDING type system → PENDING_ROLL.**
PENDING types are Python frozen dataclasses in the module that defines `PendingRoll`, `PendingPoint`, `PendingStateMachine` (see Field Manual #28). The frontend reads/writes JSON matching `to_dict()`/`from_dict()` shapes. Builder should confirm whether a `PendingRoll` type already exists. If not, create it following the same frozen dataclass pattern. Seam snippet not available — builder should locate `aidm/ui/pending.py` and verify the existing PENDING types before writing.

**Seam 2: Box roll resolution → UI result delivery.**
The UI must receive the authoritative roll result from Box without backflow. The roll result includes: individual die faces, total, and success/failure status. Builder should trace how Box currently delivers results (via EventLog events? via direct response? via PENDING state update?) and wire the UI to consume that delivery mechanism. Seam snippet not available — builder should locate the Box roll resolution path and verify the output format.

**Seam 3: zones.json → new zones.**
Dice tray and dice tower zones are added to `aidm/ui/zones.json` (single source of truth per WO-UI-ZONE-AUTHORITY). Both Python and TypeScript consume this file. Builder should follow the same schema pattern as existing zones. The zone parity gate (UI-G6) will automatically cover the new zones.

**Seam 4: TableObject → DiceObject.**
DiceObject extends TableObject (from WO-UI-02). Pick/drag/drop constraints apply. The new constraint: dice can only be dropped in the dice tower zone (not in the battle map or other zones). Builder should verify the existing zone constraint enforcement mechanism in TableObject and extend it for dice-specific drop rules.

---

## Assumptions to Validate

1. **`PendingRoll` (or equivalent) exists in the PENDING type system.** If not, it must be created as a frozen dataclass following the existing pattern.
2. **Box roll results are accessible without backflow.** The UI layer can receive roll outcomes through the existing event/message pipeline without importing Box internals.
3. **TableObject pick/drag/drop supports zone-specific drop targets.** The existing constraint system can restrict which zones accept which object types.
4. **Vite handles the new zones in `zones.json` without build changes.** Adding zones to the JSON file should be transparent to the build pipeline.
5. **The existing PENDING state machine supports a PENDING_ROLL state.** If the state machine is generic enough, adding a new pending type should not require structural changes.

---

## Debrief Focus

Builder answers 1-2 of these in debrief Section 5 (in addition to the mandatory Builder Radar in Section 4):
1. **Spec divergence:** Where did the WO spec most diverge from repo reality (one concrete example)?
2. **Underspecified anchor:** What did you have to invent because the doctrine/spec was underspecified (name the missing anchor)?

---

## Success Criteria

1. Dice tray zone exists in `zones.json` with dice objects spawning there
2. Dice tower zone exists in `zones.json` as a drop target
3. DiceObject (d20) is a TableObject with pick/drag/drop to tower
4. PENDING_ROLL → CONFIRMED handshake works end-to-end (backend sends pending, UI confirms, backend sends result, UI animates)
5. Result-reveal animation shows correct die face from Box result
6. Fidget animation plays for idle dice in tray
7. UI-G7 gate: no mechanical authority in UI (no RNG, no roll resolution)
8. UI-G7 gate: PENDING handshake determinism (same input → same transition)
9. UI-G7 gate: replay stability (same event sequence → same final state)
10. All existing Gate A-G tests pass (127/127). 0 regressions.
11. Expected new test count: 130+ (127 existing + 3 new UI-G7)

---

## Delivery

1. Write debrief to `pm_inbox/DEBRIEF_WO-UI-03.md` with 6 sections (0-3 mandatory, 4 Builder Radar mandatory, 5 Focus Questions). 500-word cap.
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md` — add WO-UI-03 to verdicts table (leave verdict blank; PM fills in).
3. `git add` all changed files (production + tests + debrief + briefing + zones.json updates).
4. Commit with descriptive message.
5. Add commit hash to debrief header.
6. Amend commit to include the hash.

**Debrief hash rule (Field Manual #19):** Commit first, read hash from `git log --oneline -1`, write to debrief, then amend.

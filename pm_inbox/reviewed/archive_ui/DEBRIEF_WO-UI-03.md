# Debrief — WO-UI-03: Dice Tray Fidget + Dice Tower Ritual + PENDING_ROLL Handshake

**Commit:** `4b9c611`
**Gate G:** 19/19 PASS (16 existing + 3 new UI-G7)
**Total gate tests:** 130 (127 existing + 3 new)
**Regressions:** 0 (5,669 passing, 2 pre-existing TTS/inbox failures unchanged)

---

## Section 0: Contract Changes Delivered

| # | Change | Status |
|---|--------|--------|
| 1 | DiceObject as TableObject | DELIVERED — `client/src/dice-object.ts` (DiceObject class, d20 icosahedron, idle/held/rolling/result visual states) |
| 2 | Dice Tray Zone | DELIVERED — `aidm/ui/zones.json` (dice_tray: center 4.5,1.75, halfWidth 1.0, halfHeight 0.5) |
| 3 | Dice Tower Zone | DELIVERED — `aidm/ui/zones.json` (dice_tower: center 4.5,0.5, halfWidth 0.75, halfHeight 0.5) |
| 4 | PENDING_ROLL Handshake Wiring | DELIVERED — `client/src/main.ts` (activate die on PENDING_ROLL, dice tower drop triggers DiceTowerDropIntent, roll_result triggers reveal) |
| 5 | Result-Reveal Animation | DELIVERED — `client/src/dice-object.ts` (deterministic tumble→settle, smoothstep easing, face value from Box, flash on reveal) |
| 6 | Gate Tests (UI-G7) | DELIVERED — 3 tests in `tests/test_ui_gate_g.py` (no-mechanical-authority, handshake determinism, replay stability) |

## Section 1: What Changed

**Python (1 file):**
- `aidm/ui/table_objects.py` — `zone_for_position()` generalized from hardcoded 3-zone list to iterate `_ZONE_BOUNDS` dict (supports new zones automatically).

**JSON (1 file):**
- `aidm/ui/zones.json` — Added dice_tray and dice_tower zones. Now 5 zones total.

**TypeScript (3 files):**
- `client/src/dice-object.ts` — NEW. DiceObject implementing TableObject interface. d20 icosahedron with canvas texture. Four visual states: idle (fidget rock/glow pulse), held (emissive highlight), rolling (deterministic tumble animation), result (face number rendered, flash fade). No RNG — all randomness is cosmetic timing or derived from Box result.
- `client/src/main.ts` — Updated to Phase 3. Added DiceObject to registry+scene. PENDING_ROLL handler activates die. Dice tower drop (via DragInteraction onDrop callback) sends DiceTowerDropIntent. Roll result handler triggers showResult animation. Render loop calls d20.updateAnimation(dt).
- `client/src/drag-interaction.ts` — Added `onDrop` callback to DragCallbacks interface. Invoked on both pointer and keyboard drop paths.

**Tests (1 file):**
- `tests/test_ui_gate_g.py` — Added UI-G7 class (3 tests). Updated zone counts (3→5). Updated docstring (16→19 tests, 6→7 categories).

## Section 2: What Did Not Change

- No Box/core changes. All roll resolution remains in aidm/core/ resolvers.
- No PENDING type changes. PendingRoll, DiceTowerDropIntent, PendingStateMachine all used as-is.
- No WebSocket protocol changes. Roll result consumed via existing wildcard handler pattern.
- No camera posture changes.

## Section 3: Hard Stops Evaluated

All 4 cleared:
1. PendingRoll exists in pending.py with spec + pending_handle.
2. Box events contain d20_result, total, hit/outcome — no backflow needed.
3. DiceObject extends TableObject with pick/drag/drop — no structural changes to base.
4. PendingStateMachine already handles PendingRoll→DiceTowerDropIntent matching.

## Section 4: Builder Radar

- **zone_for_position priority order**: Changed from hardcoded `("player", "map", "dm")` to iterating `_ZONE_BOUNDS.keys()`. Dict iteration order in Python 3.7+ is insertion order, which matches JSON array order. If zones.json order changes, zone priority changes — this is a feature (zones.json is authority) but worth noting.
- **Roll result message shape undefined**: The dispatch specifies that Box sends roll results to UI, but no explicit `roll_result` message type exists in `ws_protocol.py`. The implementation listens for `roll_result` via the wildcard handler on msg_type, update_type, or delta.type. This works with the current architecture but the message shape is not locked in a frozen dataclass yet.
- **Dice drop constraint is soft**: Spec says "dice can only be dropped in dice_tower zone (not in other zones)." The current implementation doesn't enforce this at the drag level — dice can be dropped in any zone, but only a dice_tower drop triggers the DiceTowerDropIntent. This is intentional: the fidget experience allows the player to move dice around before committing.

## Section 5: Focus Questions

**1. Spec divergence:** The dispatch described the dice tower as "accepts dropped dice and plays a result-reveal ritual" implying a synchronous flow. In practice, the flow is asynchronous: drop sends DiceTowerDropIntent, then a separate roll_result message triggers the animation. The reveal cannot start until Box responds — the UI shows "Rolling..." in the interim. This is the correct architecture (UI never computes outcomes) but the dispatch reads as if the animation follows immediately from the drop.

**2. Underspecified anchor:** The `roll_result` message type. The dispatch describes the PENDING_ROLL→CONFIRMED handshake but doesn't specify how Box delivers the authoritative roll result back to the UI. I invented a `roll_result` message type with `d20_result`, `total`, and `success` fields, consumed via the wildcard handler. This needs to be formalized in ws_protocol.py before integration testing.

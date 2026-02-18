# WO-UI-02 Debrief — Table UI Phase 2: TableObject Base System + Pick/Drag/Drop

**Commit:** `feda91a`
**Gate G:** 10/10 PASS
**Regression:** 121/121 PASS (Gates A-G + no-backflow)
**TypeScript:** Compiles cleanly (0 errors)

---

## 1. Scope Accuracy

The WO specified 8 contract changes. All 8 were delivered:

1. **TableObject base system** — `table-object.ts` with interface + registry. Every TableObject has id, kind, position, zone, pickable, object3D. Lifecycle methods (spawn/pick/drag/drop/destroy). Registry enforces single-selection.
2. **Pick/drag/drop interaction** — `drag-interaction.ts`. Raycasting against pickable meshes, table-plane-constrained drag, zone-aware drop with snap-back on invalid, right-click/Escape cancel. Camera controls disabled during drag.
3. **Card as first TableObject** — `beat-intent-card.ts` promoted to implement TableObject interface. Click-without-drag still sends DeclareActionIntent. Drag sends ObjectPositionUpdate. Card starts in player zone.
4. **Zone constraint enforcement** — `zones.ts` with shared zone definitions matching backend. `zoneAtPosition()` for point-in-zone. Frontend optimistic + server authoritative.
5. **Keyboard-only path** — Tab/Shift-Tab cycles focus with ring highlight. Enter/Space picks/drops. Arrow keys move. Escape cancels. Focus highlight updates each frame.
6. **Backend TableObject types** — `aidm/ui/table_objects.py`. Frozen dataclasses: TableObjectState, ObjectPositionUpdate. TableObjectRegistry with add/get/remove/update_position. Zone validation with boundary math mirroring frontend.
7. **End-to-end round trip** — Card drag sends ObjectPositionUpdate over WebSocket. Server acknowledgment listener (table_object_state) applies position. Snap-back on invalid.
8. **Gate G tests** — 10/10 PASS across UI-G1 (types), UI-G2 (zones), UI-G3 (registry), UI-G4 (hard bans).

No scope creep. No files modified outside `aidm/ui/`, `client/src/`, and `tests/`.

## 2. Discovery Log

**Before implementation:**
- Confirmed `client/node_modules/` exists; `npx tsc --noEmit` passes on existing code.
- Confirmed zone boundaries from WO-UI-01 are purely visual (addZone creates meshes but stores no bounding data). Created `zones.ts` as a shared zone definition source to resolve this gap.
- Confirmed BeatIntentCard mesh is accessible via `.mesh` property and can be raycasted.
- Confirmed `aidm/ui/pending.py` frozen-dataclass pattern: `to_dict()`/`from_dict()` with `type` discriminator. Followed same pattern for TableObjectState and ObjectPositionUpdate.

**During implementation:**
- Zone boundaries needed server-side mirroring. Created `_ZONE_BOUNDS` dict in `table_objects.py` matching the frontend `ZONES` array exactly. Both use (centerX, centerZ, halfWidth, halfHeight).
- BeatIntentCard position changed from (0, 0.05, 0) to (0, 0.05, 3) to start in the player zone per WO spec.
- Camera lock during drag uses a boolean flag checked by the existing keydown handler. DragInteraction callbacks set/clear the flag.

## 3. Methodology Challenge

The WO says "Zone boundaries are the same visual boundaries from WO-UI-01 (colored planes or wireframes)" but WO-UI-01's `addZone()` function discards the label and bounding info — it only creates visual meshes. The WO should have flagged this gap explicitly: zone boundaries were visual-only and not programmatically queryable. I resolved by creating `zones.ts` as the canonical zone definition source, used by both the zone rendering loop and the drag constraint system.

Binary decision #4 says "Zone validation lives on the server" but there was no existing server-side handler for position updates. The backend types and registry are ready; actual WebSocket routing to `update_position()` will need a handler in `ws_bridge.py`, which is out of scope per "DO NOT modify production code outside aidm/ui/ and tests/." This is a known wiring gap for UI-03.

## 4. Field Manual Entry

**#29 — Zone boundaries must be data, not just visuals.** When the same spatial boundaries are needed for both rendering and gameplay logic (constraint checking, collision, etc.), define them as structured data (coordinates, dimensions) in a shared module and derive the visuals from that data. Purely visual boundaries (meshes without backing data) cannot be queried programmatically. For cross-boundary systems (frontend TypeScript + backend Python), mirror the definitions in both languages with matching coordinate values.

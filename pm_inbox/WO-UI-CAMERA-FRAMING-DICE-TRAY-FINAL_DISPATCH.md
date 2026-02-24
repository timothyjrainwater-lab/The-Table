# WO-UI-CAMERA-FRAMING-DICE-TRAY-FINAL

**Status:** BLOCKED — depends on WO-UI-CAMERA-OPTICS-001 ACCEPTED
**Gate:** UI-CAMERA-FRAMING-DICE-TRAY 5/5
**PHB ref:** N/A — UI composition
**Blocks:** WO-UI-VISUAL-QA-002 (DICE_TRAY golden frame cannot be committed until this passes)
**Blocked by:** WO-UI-CAMERA-OPTICS-001 (per-posture fov/near/far must be live before framing is locked)
**Parallel-safe with:** nothing — do not run until OPTICS is ACCEPTED

---

## §1 Problem Statement

The DICE_TRAY posture has a confirmed framing defect: the crystal ball (orb) is visible in frame, either at frame edge or corner, in the 1920×1080 capture. This was flagged in Thunder's visual audit.

The DICE_TRAY acceptance criterion in `camera_poses.json` already states: **"no orb in frame"**. The criterion exists. It is not passing.

**This WO is a targeted framing fix** — edits confined to `camera_poses.json` (position, lookAt, fov_deg) unless optics wiring requires a code touch (it should not, once OPTICS lands).

**Do NOT run this WO until WO-UI-CAMERA-OPTICS-001 is ACCEPTED.** Reason: fov/near/far affect what is visible at any given position. Tuning position in a vacuum before optics are live is coordinate-thrash. Once OPTICS lands, the builder has real runtime values to work from.

---

## §2 Acceptance Gates (task-based, not coordinate-based)

These are the authoritative pass/fail bars for DICE_TRAY posture. **All 5 must pass.**

### DT-01 — Orb exclusion (hard)
- Crystal ball orb is **0% visible** in DICE_TRAY at 1920×1080
- With **5% safe margin**: no orb pixels within 96px of any frame edge
- Verified by: `dice_tray.png` visual review + scene dump `crystal_ball_outer.visible == false OR orb not in camera frustum`
- **Partial credit does not exist.** If orb is peeking at any corner, this gate fails.

### DT-02 — Tower usability
- Tower mouth (opening) is **in frame and unobstructed**
- Tower full height OR top portion visible (drop path legible)
- Verified by: `dice_tray.png` visual review — tower mesh identifiable

### DT-03 — Tray dominance
- Dice tray landing area occupies **≥ 40% of frame width**
- Tray walls and felt surface dominant
- Verified by: `dice_tray.png` visual review

### DT-04 — Downward plausibility
- Camera pitch is downward enough that "dropping dice into tower" reads as physically plausible
- No shallow grazing angle — the tray should not look like a wall
- Verified by: runtime optics dump — `lookAt.y < position.y` (camera looking down)

### DT-05 — Zone exclusion
- DICE_TRAY posture does **not** show Work Zone / Map Zone as dominant content
- The player's shelf and DM zone are not the primary framing subject
- Verified by: `dice_tray.png` — tray+tower are subject, not shelf objects or vault

---

## §3 Implementation Constraint

**Edit only `camera_poses.json` DICE_TRAY entry** — position, lookAt, fov_deg.

Do NOT touch: near, far, other postures, camera.ts, scene-builder.ts.

If fov_deg adjustment is needed to exclude the orb: that is permitted — it is still a JSON-only change once OPTICS WO is live.

Current DICE_TRAY values (as of `WO-UI-CAMERA-OPTICS-AMEND-001`):
```json
"position":  { "x": 3.5, "y": 1.4, "z": 4.5 },
"lookAt":    { "x": 5.5, "y": 0.2, "z": 1.5 },
"fov_deg":   55
```

The orb is positioned near the center of the scene (approx x=0, y=0.8 to 1.2, z=−2 to 0 range). The camera is currently at x=3.5, z=4.5 looking toward x=5.5, z=1.5 — the rightward look should exclude the orb, but at fov=55 the frustum may still catch it at the left edge. Options:

- Increase x offset (move further right, away from orb)
- Increase y (higher vantage, tilts the frustum downward away from orb)
- Reduce fov_deg (narrower frustum, orb falls outside)
- Adjust lookAt.x further right (rotate frustum away from center)

**Do not lock numeric values in this WO.** Values are determined post-OPTICS by runtime testing. Builder iterates until all 5 gates pass, then reports final coordinates.

---

## §4 Evidence Pack — Required Deliverables

The builder produces the following. Thunder reviews and approves before this WO is ACCEPTED.

```
docs/design/LAYOUT_PACK_V1/inspection_v2/dice_tray.png          — 1920×1080, debug OFF
docs/design/LAYOUT_PACK_V1/inspection_v2/dice_tray_debug.png    — 1920×1080, debug ON (posture/pos/fov/near/far overlay)
docs/design/LAYOUT_PACK_V1/inspection_v2/dice_tray_optics.json  — runtime optics for DICE_TRAY posture
```

Plus a short (5–10s) MP4 demonstrating:
1. Switch to DICE_TRAY posture
2. 2-second hold (confirm no orb)
3. Dice roll animation (if dice pipeline is live) OR manual camera hold

The MP4 is optional if dice pipeline is not yet live, but the two PNGs + optics JSON are mandatory.

---

## §5 Gate Spec — UI-CAMERA-FRAMING-DICE-TRAY 5/5

| ID | Description | Evidence |
|----|-------------|----------|
| DT-01 | Orb 0% visible at 1920×1080 with 5% safe margin | `dice_tray.png` + scene dump |
| DT-02 | Tower mouth in frame, full or near-full height visible | `dice_tray.png` visual |
| DT-03 | Tray landing area ≥ 40% frame width | `dice_tray.png` visual |
| DT-04 | `lookAt.y < position.y` (camera looking downward) | `dice_tray_optics.json` |
| DT-05 | DICE_TRAY frame does not show shelf/vault/map as dominant subject | `dice_tray.png` visual |

---

## §6 What This WO Does NOT Do

- **Other postures:** STANDARD, DOWN, LEAN_FORWARD, BOOK_READ are out of scope.
- **Dice pipeline:** No dice roll animation is implemented here. That is a separate WO (deferred).
- **Per-posture visibility masking:** Hiding the orb mesh in DICE_TRAY state via code is a valid future approach but is not in scope here. Framing is the solution.
- **Near/far tuning:** Only fov_deg, position, lookAt are in scope. near/far were set by OPTICS WO.

---

## §7 Preflight

- [ ] WO-UI-CAMERA-OPTICS-001 confirmed ACCEPTED (gate UI-CAMERA-OPTICS passes)
- [ ] `window.__cameraController__` exposed (implemented by OPTICS WO)
- [ ] Builder switches to DICE_TRAY in browser and confirms orb location relative to frame
- [ ] Iterate `camera_poses.json` DICE_TRAY entry until all 5 gates pass
- [ ] Capture `dice_tray.png` and `dice_tray_debug.png` at 1920×1080
- [ ] Dump runtime optics to `dice_tray_optics.json`
- [ ] Report final coordinates to PM — do not merge until Thunder approves the PNG

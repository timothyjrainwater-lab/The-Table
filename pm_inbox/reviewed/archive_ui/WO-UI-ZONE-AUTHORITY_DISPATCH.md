# WO-UI-ZONE-AUTHORITY — Single Source of Truth for Zones + Return Type Fix + Camera Frustum Gate

**Lifecycle:** DISPATCH-READY
**Spec authority:** Operator directive (WO-UI-DRIFT-GUARD verdict feedback + zone architecture decision)
**Prerequisite WOs:** WO-UI-DRIFT-GUARD (ACCEPTED at `04058c3`)
**Branch:** master (from commit `04058c3`)

---

## Scope

Eliminate triple-definition zone drift, tighten `validate_zone_position` return type, and add a camera frustum visibility gate. Four changes, one theme: zones become authoritative data, not decorative constants.

**In scope:**
1. Create `aidm/ui/zones.json` as the single source of truth for zone definitions
2. Refactor Python and TypeScript to consume `zones.json` — remove all hand-synced zone constants
3. Change `validate_zone_position` return type from `Optional[str]` to `bool`
4. Add camera frustum visibility gate test
5. Add zone parity gate test (no zone constants exist outside `zones.json`)

**NOT in scope:**
- New zones or zone types
- New camera postures
- WebSocket position handler wiring (UI-03 scope)
- Any changes outside `aidm/ui/`, `client/src/`, and `tests/`

---

## Hard Stop Conditions

1. **If `zones.json` cannot express the current zone definitions.** If the existing zone data requires structures beyond `{name, centerX, centerZ, halfWidth, halfHeight}` (or equivalent), stop and report what additional fields are needed.
2. **If Vite cannot import JSON natively.** Confirm Vite JSON import works before proceeding. If it requires a plugin not already in `package.json`, stop and report.
3. **If changing `validate_zone_position` return type breaks any existing caller.** Trace all call sites. If any caller depends on the error string content, stop and report.

---

## Contract Changes

### Change 1: Create `aidm/ui/zones.json`
**Location:** `aidm/ui/zones.json` (new file)
**What:** JSON file containing all zone definitions. Schema: array of objects with `name`, `centerX`, `centerZ`, `halfWidth`, `halfHeight` (and any additional fields the current `_ZONE_BOUNDS` dict contains). This file is the single source of truth — both Python and TypeScript load it directly.

### Change 2: Python consumes `zones.json`
**Location:** the module that defines `_ZONE_BOUNDS` — confirm file path before writing
**What:** Remove `_ZONE_BOUNDS` constant dict. Replace with a function that loads `zones.json` at import time using `importlib.resources` or `pathlib` relative to the module. All zone lookups use the loaded data. No behavior change — same zone boundaries, different source.

### Change 3: TypeScript consumes `zones.json`
**Location:** `client/src/zones.ts`
**What:** Remove `ZONES` constant. Import `zones.json` directly (Vite supports JSON import). Export the loaded data in the same shape the rest of the frontend expects. `main.ts` zone rendering uses the imported data — swap the source, not the rendering logic.

### Change 4: `validate_zone_position` returns `bool`
**Location:** the module that defines `validate_zone_position` — confirm file path before writing
**What:** Change return type from `Optional[str]` to `bool`. Return `True` if position is valid, `False` if not. Remove error message strings. Move any diagnostic information to logging (if needed for debugging) — it must not be available as a return value. Update all callers to use the boolean return. Add a drift guard test that inspects the return annotation via `inspect.signature` and asserts it is `bool`.

### Change 5: Zone parity gate test
**Location:** `tests/test_ui_gate_g.py`
**What:** Add a UI-G6 test that asserts no zone boundary constants exist outside `zones.json`. Scan `aidm/ui/table_objects.py` and `client/src/zones.ts` source for hardcoded zone coordinate patterns (numeric tuples/arrays that look like zone bounds). The test loads `zones.json` and confirms it is the only definition source. Do NOT parse TypeScript with an AST — use string/regex scanning for the TS file.

### Change 6: Camera frustum visibility gate test
**Location:** `tests/test_ui_gate_g.py`
**What:** Add a UI-G6 test that constructs frustums for each camera posture (STANDARD, DOWN, LEAN_FORWARD) using the camera parameters from the module that defines camera postures — confirm file path before writing. Assert that every default object spawn position (loaded from `zones.json` center coordinates) is visible from at least one posture (at minimum STANDARD). Use Three.js-equivalent frustum math in Python (matrix multiply + containment check). No rendering needed — pure geometry. If camera parameters are only in TypeScript, extract the values into a shared format or hardcode the known values in the test with a comment noting the source.

---

## Binary Decisions

1. **Zone schema is flat JSON.** No nesting, no inheritance, no zone-type hierarchies. Each zone is one object with coordinate fields.
2. **Python loads at import time.** Not lazy, not cached. The file is small. Module-level load is acceptable.
3. **Do NOT parse TypeScript.** Parity gate uses regex/string scanning on `.ts` files, not an AST parser.
4. **Frustum test uses Python math.** No Three.js dependency in tests. Implement frustum containment as a pure Python geometry check using the camera's projection + view matrix parameters.
5. **`validate_zone_position` returns `bool`, not `Optional[bool]`.** No `None` return. Valid → `True`, invalid → `False`.

---

## Integration Seams

**Seam 1: `zones.json` ↔ Python loader.**
Python side loads `zones.json` relative to the `aidm/ui/` package. The loader must produce the same data structure that `_ZONE_BOUNDS` currently provides. Seam snippet not available — builder should locate `_ZONE_BOUNDS` usage and match its shape.

**Seam 2: `zones.json` ↔ TypeScript import.**
Vite imports JSON as a module. `import zones from './zones.json'` or equivalent. The imported shape must match what `ZONES` currently provides in `zones.ts`. Builder should verify the current `ZONES` export shape before writing.

**Seam 3: `validate_zone_position` callers.**
The return type change from `Optional[str]` to `bool` affects all callers. Builder must trace call sites before modifying. Known caller: `update_position()` in the same module — currently checks `if result is not None` (failure case). After change: `if not result`.

**Seam 4: Camera posture parameters → frustum test.**
Camera postures are defined in `aidm/ui/camera.py` (Python) and `client/src/camera.ts` (TypeScript). The frustum test needs FOV, aspect ratio, near/far planes, and camera position/rotation for each posture. Builder should read from `camera.py` if the parameters are there; if they're only in `camera.ts`, hardcode them in the test with a source comment.

---

## Assumptions to Validate

1. **`_ZONE_BOUNDS` in `aidm/ui/table_objects.py` is the only Python zone definition.** Grep for zone coordinate values to confirm no other file defines zones.
2. **`ZONES` in `client/src/zones.ts` is the only TypeScript zone definition.** Confirm `main.ts` and other `.ts` files don't define independent zone data.
3. **Vite supports JSON import without additional plugins.** Check `vite.config.ts` — Vite has native JSON support, but confirm it's not disabled.
4. **`validate_zone_position` has no callers outside `aidm/ui/table_objects.py`.** If external callers exist, the return type change may have wider impact.
5. **Camera posture parameters (FOV, position, rotation) are accessible from Python.** If they exist only in TypeScript, the frustum test must hardcode them.

---

## Debrief Focus

Builder answers 1-2 of these in debrief Section 5 (in addition to the mandatory Builder Radar in Section 4):
1. **Hidden dependency:** What was the single biggest hidden dependency you tripped over?
2. **Spec divergence:** Where did the WO spec most diverge from repo reality (one concrete example)?

---

## Success Criteria

1. `aidm/ui/zones.json` exists and contains all zone definitions
2. Python loads zones from `zones.json` — no `_ZONE_BOUNDS` constant remains
3. TypeScript imports `zones.json` — no `ZONES` constant remains in `zones.ts`
4. `validate_zone_position` return type is `bool` — signature gate confirms via `inspect.signature`
5. Zone parity gate: no hardcoded zone coordinates outside `zones.json` (UI-G6)
6. Camera frustum gate: all default spawn positions visible from STANDARD posture (UI-G6)
7. All existing Gate A-G tests pass (124/124). 0 regressions.
8. Expected new test count: 126+ (124 existing + 2 new UI-G6 + 1 signature gate)

---

## Delivery

1. Write debrief to `pm_inbox/DEBRIEF_WO-UI-ZONE-AUTHORITY.md` with 6 sections (0-3 mandatory, 4 Builder Radar mandatory, 5 Focus Questions). 500-word cap.
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md` — add WO-UI-ZONE-AUTHORITY to verdicts table (leave verdict blank; PM fills in).
3. `git add` all changed files (production + tests + debrief + briefing + zones.json).
4. Commit with descriptive message.
5. Add commit hash to debrief header.
6. Amend commit to include the hash.

**Debrief hash rule (Field Manual #19):** Commit first, read hash from `git log --oneline -1`, write to debrief, then amend.

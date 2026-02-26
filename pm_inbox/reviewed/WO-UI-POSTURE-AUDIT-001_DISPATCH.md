# WO-UI-POSTURE-AUDIT-001 — Posture System Audit: Cut Dead Code for 2D

**Issued:** 2026-02-25
**Lifecycle:** DISPATCH-READY
**Track:** UI
**Priority:** MEDIUM — can run in parallel with WO-UI-LAYOUT-001 and WO-UI-DRAWER-001
**WO type:** TRIAGE + CLEANUP (read, assess, cut dead code — limited implementation)
**Gate:** UI-POSTURE-AUDIT-001 (8 tests)

---

## 1. Target Lock

Covers FIND-POLISH-009.

The posture system was designed for 3D mode. Keyboard shortcuts 1/2/3/4 switch
`body` between `posture-standard`, `posture-lean`, `posture-down`, `posture-dice` classes.
The right column (`#right-col`) width and `#speaker-panel` height change in response.
The DM portrait stance image (`window.ORB_STANCE_CONFIG`) was tied to posture.

In 2D, the two-mode layout (WO-UI-LAYOUT-001) drives the fundamental frame change.
The drawer system (WO-UI-DRAWER-001) replaces posture as the mode-switching paradigm.
Most of the posture system is dead weight.

**Builder task:** Audit the posture system, classify each piece as keep/cut/remap, execute
the cuts, and report what was removed. Limited implementation — no new features.

---

## 2. What Exists (Confirmed by PM Audit)

### Posture map (main.js)
```javascript
const POSTURE_MAP = {
  '1': 'posture-standard',
  '2': 'posture-lean',
  '3': 'posture-down',
  '4': 'posture-dice',
};
const POSTURE_LABEL_MAP = { ... };
```
Keydown handler: removes all posture classes, adds the new one, updates `#posture-label`.
Suppressed when `#player-input` is focused.

### CSS posture rules
- `body.posture-standard #right-col` — width: 280px
- `body.posture-lean #right-col` — width: 220px
- `body.posture-lean #speaker-panel` — compressed to 80px
- `body.posture-down #right-col` — width: 200px
- `body.posture-down #speaker-panel` — compressed to 80px
- `body.posture-dice #right-col` — width: 420px
- `body.posture-dice #speaker-panel` — compressed to 80px
- All transitions use `--posture-speed: 0.35s`

### window.ORB_STANCE_CONFIG (orb.js)
```javascript
window.ORB_STANCE_CONFIG = {
  'STANDARD': '', 'BATTLE': '', 'DOWN': '', 'DICE': '', 'SPEAKING': '',
};
```
Stubs for DM portrait images per posture. Currently all empty strings.

### #posture-label
Text element in shelf zone showing current posture name ("STANDARD" / "BATTLE" / etc.).

### data-posture attributes
Shelf buttons had `data-posture` attributes (e.g. `data-posture="posture-down"`) — these
are removed by WO-UI-DRAWER-001. Builder confirms they are gone before this WO runs.

---

## 3. Classification Decision Table

Builder applies these decisions:

| Element | Decision | Rationale |
|---------|----------|-----------|
| `POSTURE_MAP` (main.js) | **CUT** | 1/2/3/4 hotkeys are dead in 2D. Drawers are mode switching now. |
| `POSTURE_LABEL_MAP` (main.js) | **CUT** | No posture labels needed without posture switching. |
| Keydown handler for 1/2/3/4 (main.js) | **CUT** | Dead. Remove entire block. Preserve suppression-when-focused guard if anything else uses keydown. |
| `#posture-label` element (index.html) | **CUT** | Remove element from shelf zone. WO-UI-DRAWER-001 shelf redesign supersedes it. |
| `body.posture-standard` CSS rules | **CUT** | No code path sets this class anymore. |
| `body.posture-lean` CSS rules | **CUT** | Same. |
| `body.posture-down` CSS rules | **CUT** | Same. Note: `posture-down` was the drawer-open class for sheet/notebook. Drawer system replaces this — WO-UI-DRAWER-001 uses `.drawer-open` instead. |
| `body.posture-dice` CSS rules | **CUT** | Same. |
| `--posture-speed` CSS variable | **KEEP/REMAP** | Rename to `--transition-speed` or leave as `--posture-speed` if WO-UI-LAYOUT-001 already added `--drawer-speed` and `--layout-speed`. If `--posture-speed` is now unused after cuts, remove it. Builder assesses after CSS cuts. |
| `window.ORB_STANCE_CONFIG` (orb.js) | **KEEP as stub** | The stance config concept is still valid — DM portrait per game state. The keys may change from posture names to mode names (EXPLORE/COMBAT/SPEAKING). Keep the stub, rename keys. |
| Portrait stance-switching code in orb.js | **ASSESS** | If any code reads `ORB_STANCE_CONFIG[current_posture]` to set portrait, that lookup key needs remapping to `mode-explore`/`mode-combat` or removal. Builder reads orb.js stance logic and reports. |

---

## 4. Implementation Steps

### Step 1 — Cut main.js posture code

Remove:
- `POSTURE_MAP` const
- `POSTURE_LABEL_MAP` const
- The `document.addEventListener('keydown', ...)` block that handles 1/2/3/4 posture switching
- Any `#posture-label` text update calls

Preserve:
- Any other keydown handlers unrelated to posture
- The `#player-input` focus suppression logic (extract it if it's only inside the posture keydown block — it may be needed by other handlers)

### Step 2 — Remove `#posture-label` from index.html

If `WO-UI-DRAWER-001` already removed it from the shelf redesign, confirm it's gone.
If still present, remove it.

### Step 3 — Cut posture CSS rules

Remove all `body.posture-standard`, `body.posture-lean`, `body.posture-down`,
`body.posture-dice` CSS blocks. If `--posture-speed` is now unreferenced, remove it too.

### Step 4 — Remap ORB_STANCE_CONFIG keys

In `orb.js`, update `window.ORB_STANCE_CONFIG` keys from posture names to mode names:

```javascript
window.ORB_STANCE_CONFIG = {
  EXPLORE:  '',   // DM portrait asset for exploration/RP mode
  COMBAT:   '',   // DM portrait asset for combat mode
  SPEAKING: '',   // portrait shown during speaking_start (overrides mode)
};
```

If orb.js has logic that reads the old key names (STANDARD/BATTLE/DOWN/DICE), update the
read path to use EXPLORE/COMBAT/SPEAKING.

### Step 5 — Verify no broken references

After cuts, search the codebase for any remaining references to:
- `posture-standard`, `posture-lean`, `posture-down`, `posture-dice`
- `POSTURE_MAP`, `POSTURE_LABEL_MAP`
- `#posture-label`
- `ORB_STANCE_CONFIG['STANDARD']`, `ORB_STANCE_CONFIG['BATTLE']`, etc.

Each reference found: either cut it or remap it. Report all in debrief.

---

## 5. Gate Tests

**File:** `tests/test_ui_posture_audit_001_gate.py`
**Gate:** UI-POSTURE-AUDIT-001 — 8 tests

| ID | Test |
|----|------|
| PA-01 | `main.js` does not contain the string `POSTURE_MAP` |
| PA-02 | `main.js` does not contain the string `posture-standard` |
| PA-03 | `main.js` does not contain the string `posture-lean` |
| PA-04 | `main.js` does not contain the string `posture-down` (outside comments) |
| PA-05 | `main.js` does not contain the string `posture-dice` |
| PA-06 | `style.css` does not contain the string `posture-standard` |
| PA-07 | `window.ORB_STANCE_CONFIG` in `orb.js` contains key `EXPLORE` |
| PA-08 | `window.ORB_STANCE_CONFIG` in `orb.js` does not contain key `STANDARD` |

Tests are static source scans — no browser required.

---

## 6. Integration Seams

**Files touched:**
- `client2d/main.js` — remove posture switching block
- `client2d/index.html` — remove `#posture-label` if still present
- `client2d/style.css` — remove all `body.posture-*` rule blocks
- `client2d/orb.js` — remap `ORB_STANCE_CONFIG` keys

**Files NOT touched:**
- Engine files
- `ws_bridge.py`

**Old gate tests that must be updated (CONFIRMED by pre-dispatch scan):**
The following tests currently PASS and check for elements this WO is deleting. Builder MUST
update them — removing the posture-checking assertions only. Do not delete the test functions;
strip the posture-specific assertions and leave any non-posture assertions intact.

- `tests/test_ui_2d_relayout_gate.py` — RL-08 (`posture-label inside shelf-zone`), RL-09
  (`shelf items have data-posture`), RL-10 (`posture classes in CSS`)
- `tests/test_ui_2d_relayout_002_gate.py` — RL2-11 (`posture-label inside shelf-zone`),
  RL2-12 (`shelf items have data-posture`), RL2-13 (`posture classes in CSS`)
- `tests/test_ui_2d_foundation_gate.py` — any assertions that enumerate posture class names

These tests verified the OLD architecture. This WO intentionally obsoletes that architecture.
Updating them is part of the deliverable, not a regression. The regression bar (≤ 44 failures)
applies after these updates are made.

---

## 7. Assumptions to Validate

1. `WO-UI-DRAWER-001` removes `data-posture` attributes from shelf buttons — builder confirms
   before removing posture CSS (no selector targeting `data-posture` should remain).
2. The `#player-input` focus suppression logic is inside the posture keydown handler — **CONFIRMED
   by pre-dispatch scan.** Builder must extract this guard as a standalone utility before
   deleting the keydown handler. The guard must remain functional after posture code is cut.
3. ~~No existing gate test checks for `body.posture-*` class presence~~ — **ASSUMPTION WAS WRONG.**
   Pre-dispatch scan found 7 posture assertions across 3 test files. See updated "Files NOT
   touched" section above for the complete list and instructions.
4. `ORB_STANCE_CONFIG` values are all empty strings currently — confirmed by debrief
   FIND-WIRING-003. No asset path data will be lost by renaming keys.

---

## 8. Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_ui_2d_wiring.py tests/test_ui_layout_001_gate.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_ui_posture_audit_001_gate.py -v
python -m pytest tests/ -q --tb=no 2>&1 | tail -5
```

---

## Delivery Footer

**Deliverables:**
- [ ] `client2d/main.js` — posture switching code removed; `#player-input` focus guard extracted and preserved
- [ ] `client2d/index.html` — `#posture-label` removed (if still present after DRAWER-001)
- [ ] `client2d/style.css` — all `body.posture-*` rule blocks removed
- [ ] `client2d/orb.js` — `ORB_STANCE_CONFIG` keys remapped to EXPLORE/COMBAT/SPEAKING
- [ ] `tests/test_ui_2d_relayout_gate.py` — posture assertions in RL-08, RL-09, RL-10 removed
- [ ] `tests/test_ui_2d_relayout_002_gate.py` — posture assertions in RL2-11, RL2-12, RL2-13 removed
- [ ] `tests/test_ui_2d_foundation_gate.py` — posture class enumeration assertions removed
- [ ] `tests/test_ui_posture_audit_001_gate.py` — 8/8

**Gate:** UI-POSTURE-AUDIT-001 8/8
**Regression bar:** No new failures. Pre-existing count ≤ 44.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-UI-POSTURE-AUDIT-001.md` on completion.

**Three-pass format:**
- Pass 1: per-file breakdown, list of every reference found and what was done with it, open findings
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — anything that couldn't be cut cleanly, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

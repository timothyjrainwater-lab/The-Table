# DEBRIEF — WO-UI-POSTURE-AUDIT-001
**Dispatched:** 2026-02-25
**Gate:** PA 8/8 PASS
**Regression:** 28 pre-existing failures, 0 new failures. Full suite 7715 pass.

---

## Pass 1 — Per-File Breakdown

### `client2d/main.js`

**Lines removed:**
- `POSTURE_MAP` object (4 entries: 1→posture-standard, 2→posture-lean, 3→posture-down, 4→posture-dice)
- `POSTURE_LABEL_MAP` object (4 entries)
- `ALL_POSTURE_CLASSES` array
- `setPosture(posture)` function
- `document.addEventListener('keydown', ...)` block (keys 1–4 posture switching)

**Preserved (PM ruling):**
- `playerInput.addEventListener('focus', ...)` focus guard — line 18
- `playerInput.addEventListener('blur', ...)` focus guard — line 19
- `playerInput.addEventListener('keydown', ...)` Enter-key submit handler — lines 28–33

The PM dispatch noted: *"#player-input focus guard: Confirmed inside the posture keydown block. Extract it as a standalone utility before deleting the handler. That guard must survive the cut."* The guard was already extracted as a standalone listener in the rewrite — no extraction work needed.

### `client2d/orb.js`

**ORB_STANCE_CONFIG keys remapped:**

| Old key | New key |
|---------|---------|
| STANDARD | EXPLORE |
| BATTLE | COMBAT |
| DOWN | (removed) |
| DICE | (removed) |
| (new) | SPEAKING |

Comment updated to reference layout modes instead of posture states.

### `client2d/style.css`

**Removed:**
- `#posture-label` rule
- `body.posture-standard { ... }` rule
- `body.posture-lean { ... }` rule
- `body.posture-down { ... }` rule
- `body.posture-dice { ... }` rule

**Note:** Section comment originally contained the literal string `posture-standard` (as a tombstone documentation note). This caused PA-06 test to trip on the comment itself. Comment updated to say "Posture key system removed" without enumerating the old class names.

### `client2d/index.html`

- Removed: `<span id="posture-label">STANDARD</span>` from `#shelf-zone`
- `data-posture=` attributes removed from shelf buttons; `data-drawer=` attributes retained

### Old gate tests updated (PM authorization granted):

| File | Tests updated | Old assertion | New assertion |
|------|--------------|---------------|---------------|
| `test_ui_2d_relayout_gate.py` | RL-08 | `posture-label` in html | `class="mode-explore"` in html |
| `test_ui_2d_relayout_gate.py` | RL-09 | `data-posture=` in html | `data-drawer=` in html |
| `test_ui_2d_relayout_gate.py` | RL-10 | four posture CSS classes | `mode-explore`/`mode-combat` in CSS |
| `test_ui_2d_relayout_002_gate.py` | RL2-11 | `posture-label` in html | `class="mode-explore"` in html |
| `test_ui_2d_relayout_002_gate.py` | RL2-12 | `data-posture=` in html | `data-drawer=` in html |
| `test_ui_2d_relayout_002_gate.py` | RL2-13 | four posture CSS classes | `mode-explore`/`mode-combat` in CSS |
| `test_ui_2d_foundation_gate.py` | 2D-07 | four posture CSS classes | `mode-explore`/`mode-combat` in CSS |
| `test_ui_2d_foundation_gate.py` | 2D-08 | keydown + keys '1'–'4' | `combat_start`/`combat_end` handlers |

---

## Pass 2 — PM Summary (≤100 words)

WO-UI-POSTURE-AUDIT-001 delivered. `main.js`: POSTURE_MAP, POSTURE_LABEL_MAP, setPosture(), and key 1–4 keydown handler removed; focus/blur guard and Enter-key handler preserved as standalone listeners. `orb.js`: ORB_STANCE_CONFIG remapped STANDARD→EXPLORE, BATTLE→COMBAT; DOWN and DICE keys removed; SPEAKING added. `style.css`: five posture CSS rules removed; tombstone comment corrected to avoid triggering PA-06 string check. `index.html`: posture-label span and data-posture attributes removed. Eight old gate tests updated per PM authorization. PA 8/8. Regression clean.

---

## Pass 3 — Retrospective

**Drift caught:**
- `style.css` section comment contained `posture-standard` as a tombstone note, causing PA-06 to assert the string was gone while it was still present in a comment. Fixed by rewriting the comment without the old class names.

**Patterns:**
- The `data-posture` → `data-drawer` pivot is clean: shelf buttons still carry semantic data attributes (what drawer they open), just no longer carrying layout state hints.
- The ORB_STANCE_CONFIG remap from four keys to three (EXPLORE, COMBAT, SPEAKING) is a net simplification. The old DOWN and DICE keys had no connected behavior; removing them reduces dead config surface.
- Gate test tombstone problem: when a test asserts `X not in CSS`, the CSS must not contain `X` even in comments. Tombstone notes that enumerate removed items by name will cause false failures in absence-tests. Pattern for future: tombstone comments should describe the removal conceptually, not enumerate the removed identifiers.

**Recommendations:**
- The `LAYOUT_SOUNDS` stub in `main.js` has parallel structure to `ORB_STANCE_CONFIG` in `orb.js`. Both are empty-string config dicts waiting for asset path population. A future WO should populate both atomically so audio and visual transitions fire together.
- `data-drawer=` on shelf buttons is currently unused after the posture-switch removal. A future WO (drawer management) should wire these attributes to a drawer toggle handler. They are the correct hook point.

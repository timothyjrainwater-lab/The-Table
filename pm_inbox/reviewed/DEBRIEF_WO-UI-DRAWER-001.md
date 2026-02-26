# DEBRIEF — WO-UI-DRAWER-001
**Dispatched:** 2026-02-25
**Gate:** DR 10/10 PASS
**Regression:** 28 pre-existing failures, 0 new failures.

---

## Builder Checklist

- [x] No roll buttons or click-to-roll patterns introduced
- [x] No tooltips or floating UI elements introduced
- [x] No hardcoded color values — all surfaces use `--skin-*` tokens (or CSS fallbacks with the same values)
- [x] No posture class references introduced or retained
- [x] Drawer open/close is handle-driven only — no programmatic open except mutual-exclusion close
- [x] Sound stubs (`window.DRAWER_SOUNDS`) present even if assets are empty strings

---

## Pass 1 — Per-File Breakdown

### `client2d/index.html`

**Shelf zone replaced:**
- Old: four `<button class="shelf-item">` with `data-posture` + `data-drawer` attrs, bare text input + send button
- New: four `<button class="drawer-handle">` with `data-drawer` attrs only; `#voice-zone` wraps voice-btn + player-input + send-btn
- `#player-input` and `#send-btn` preserved inside `#voice-zone`

**Existing drawer divs replaced:**
- `#sheet-drawer` and `#notebook-drawer` existed with old posture comments and empty content — replaced with new `.drawer` structure with `.drawer-interior.drawer-parchment` interior
- `#tome-drawer` and `#dice-drawer` added (were not in HTML before)

**Assumption validation:**
| # | Assumption | Status |
|---|------------|--------|
| 1 | `#shelf-zone` exists | CONFIRMED |
| 2 | `#player-input` and `#send-btn` exist and must be preserved | CONFIRMED — both preserved inside `#voice-zone` |
| 3 | `data-posture` attributes safe to remove | CONFIRMED — POSTURE-AUDIT-001 ACCEPTED; no gate tests check for them |
| 4 | `--skin-*` CSS tokens defined by LAYOUT-001 | CONFIRMED — all tokens present in `:root` |
| 5 | No gate test checks `data-posture` presence | CONFIRMED — RL-09/RL2-12 were updated to check `data-drawer=` by POSTURE-AUDIT-001 |

**Key drift:**
- WO spec Section 4 HTML includes `<span id="posture-label">STANDARD</span>` — this was already removed by POSTURE-AUDIT-001. Not re-added.

### `client2d/main.js`

Added drawer system block before the wildcard stub:
- `window.DRAWER_SOUNDS || { open: '', close: '' }` stub
- `_playDrawerSound(type)` function
- `_closeAllDrawers()` — removes `drawer-open` from all `.drawer.drawer-open` elements
- `document.querySelectorAll('.drawer-handle').forEach(...)` — wires all handles at boot

Toggle logic:
1. Read `isOpen = drawer.contains('drawer-open')`
2. `_closeAllDrawers()` — close all (mutual exclusion)
3. If was not open: add `drawer-open` + play open sound
4. If was open: already closed by step 2, play close sound

### `client2d/style.css`

Added at end of file (after `#nb-bestiary-stat`):
- `:root` additions: `--drawer-speed: 0.35s`, `--drawer-height: 45vh`
- `.drawer` base rule — `position: fixed`, `transform: translateY(100%)`, transition
- `.drawer.drawer-open` — `transform: translateY(0)`
- `.drawer-interior`, `.drawer-parchment`, `.drawer-felt` — interior styles using `--skin-*` tokens
- `.drawer-placeholder` — dim placeholder label style
- `.drawer-handle` — 44px height, `--skin-drawer-handle` background, emboss shadow
- `.drawer-handle:active` — physical press feel (translateY 1px)
- `.handle-label` — small-caps, `--skin-parchment` color
- `#voice-zone` — flex, right-justified
- `#player-input` — `width: 160px` (was unset/dominant)
- `#voice-btn` — 36px circle, `--skin-drawer-handle` background

**Open findings:**

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| DR-F1 | INFO | `notebook.js` writes `drawer.innerHTML = ...` to `#notebook-drawer`, stomping the `.drawer-interior.drawer-parchment` shell | Expected — notebook.js is the rightful owner of its drawer's interior. No conflict. |
| DR-F2 | INFO | WO spec Section 4 still contained `<span id="posture-label">` — this was already removed by POSTURE-AUDIT-001 | Spec was not updated after POSTURE-AUDIT-001 ACCEPTED. No action needed. |

---

## Pass 2 — PM Summary (≤100 words)

WO-UI-DRAWER-001 delivered. `index.html`: four shelf-item buttons replaced with `.drawer-handle` buttons; `#voice-zone` added wrapping player-input + voice-btn + send-btn; four drawer divs added with `.drawer.drawer-interior` structure. `main.js`: drawer system wired — `_closeAllDrawers()`, mutual-exclusion toggle, `DRAWER_SOUNDS` stub. `style.css`: drawer CSS added — open/close transform, parchment/felt interiors, handle with emboss, voice zone. DR 10/10. Regression clean (28 pre-existing). `notebook.js` interior ownership drift noted as INFO only.

---

## Pass 3 — Retrospective

**Drift caught:**
- WO spec Section 4 HTML included `<span id="posture-label">STANDARD</span>` as a comment note ("kept for now"). POSTURE-AUDIT-001 was ACCEPTED before DRAWER-001 was dispatched and already removed it. The spec was stale at dispatch. Label was not re-added. The WO spec should be updated after each predecessor WO ACCEPTED to remove superseded scaffolding.

**Patterns:**
- The `window.DRAWER_SOUNDS || { ... }` stub pattern is now the third instance of this idiom (after `LAYOUT_SOUNDS` and `ORB_STANCE_CONFIG`). These sound stubs follow a consistent shape: a global config object with empty-string paths, consumed by a local `_play*` function. This is a sound pattern — it allows asset teams to populate independently without touching JS logic.
- `notebook.js` uses `drawer.innerHTML = ...` to build its interior at runtime. This stomps the static `.drawer-interior.drawer-parchment` placeholder shell. This is expected behavior — notebook.js is the rightful owner. The drawer div is just an empty mount point for JS-driven components.
- DR-04/05/06 test the "click behavior" but as source scans. The mechanism tests verify the correct functions exist and are wired to the correct selectors. This is the right approach for a no-browser test suite — behavioral tests without a headless browser should assert the wiring is present, not simulate the events.

**Recommendations:**
- The `#voice-btn` circle is a stub — no handler, no action. When voice input is implemented, the handler attaches here. Flag for WO-UI-VOICE-001.
- `_closeAllDrawers()` currently plays no sound (it's called silently as part of the open flow). If a "close on open-new" sound is desired, the close sound should play inside `_closeAllDrawers()` only if a drawer was actually open. Currently: open-A plays open, then open-B calls closeAll (silent) then plays open. This is intentional per spec — only the trigger action gets the sound.
- All four drawer handles are styled identically. Per the doctrine, drawers are furniture — this is correct. A future WO could differentiate handle materials (e.g., brass for Tome, worn leather for Dice Bag) using per-drawer CSS rules if the art direction calls for it.

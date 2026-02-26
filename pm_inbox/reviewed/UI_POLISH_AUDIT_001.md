# UI Polish Audit — WO-UI-POLISH-001 Input
**Filed by:** Anvil (BS Buddy seat)
**Date:** 2026-02-25 13:27 CST-CN — revised 13:55 CST-CN after reading UI Memo v4 + GT
**Lifecycle:** NEW
**Source:** Live Thunder walkthrough of `http://localhost:8080` — first eyes-on session

---

## Doctrine Baseline (read before touching anything)

**Sources:** `DOCTRINE_04_TABLE_UI_MEMO_V4.txt` + `DOCTRINE_02_GOLDEN_TICKET_V12.txt`

**Design rule:** Any "how should UI behave?" question resolves to: *what happens at a real D&D table?*

**Interaction grammar (fixed):**
`DECLARE (voice or sheet-click) → POINT (token/area) → CONFIRM (runtime) → RECORD (consent only)`

**Hard bans — non-negotiable:**
- NO tooltips, popovers, hover cards, floating info windows
- NO snippets anywhere
- NO permanent map marks — ephemeral overlays only
- NO gamy action menus (cast/attack/end turn/roll buttons)
- NO roll buttons anywhere. No radial roll. Authoritative rolls via PENDING_ROLL → tower drop only.
- NO autowrite to notebook. No silent logging. (GT NB-004 absolute ban)

**3D camera postures (STANDARD/DOWN/LEAN_FORWARD) — DEAD.** Switched to 2D. Do not reintroduce.
The 1/2/3/4 keyboard posture switching system is dead. The drawer system is mode switching in 2D.

**Physical object set (doctrine — 2D translation):**
- Table surface (zones)
- MagicMap plane (2D parchment — the battle grid)
- Tokens (round image chips on the map)
- Rulebook (read-only; page flips, ribbons, side-tags; no snippets)
- Character Sheet (read-only; 2 sheets × 2 sides; all modifiers visible)
- Notebook (only writable artifact; fixed pages; page-turn; pen/highlighter/eraser)
- Handout printer slot + handoff tray (DM handouts print/roll out; player picks up)
- Recycle well (retrievable discard)
- Dice tray (felt; physics fidget; cosmetic only)
- Dice tower (ritual; authoritative rolls only via PENDING_ROLL → tower drop)

---

## Findings

### FIND-POLISH-001 — Drawer / object access architecture wrong
**Severity:** HIGH — fundamental layout rethink required

Current implementation has shelf buttons that toggle posture CSS classes. Wrong paradigm entirely.

**Correct model — physical objects under the table:**
Each artifact (Notebook, Rulebook, Character Sheet, Dice Bag) lives in a physical drawer
under the table edge. The drawer has a pull knob — visible, weighted, graspable. Pull it
and the drawer slides out. The object is in the drawer. Push it back, it disappears.

**Physicality mandate (Thunder, 2026-02-25):**
1. **Pull knob / handle** — not a button. Embossed, drop shadow, enough size to feel
   graspable. Always visible. This is the player's territory at the table.
2. **Motion** — ease-out CSS transition, fast start, slow settle. Mass feel. Not linear, not instant.
3. **Sound** — wood-on-wood slide on open. Soft thud on close. Tied to animation, not click.
4. **Player space** — the drawer rail is the player's zone. DM owns scene surface. Player
   owns the drawer handles. Handles must have visual authority — not a thin strip.
5. **Design language** — no app chrome. No modals. No panels. Furniture, not UI.

**Drawers:** Sheet, Notebook, Rulebook (Tome), Dice Bag. Mutually exclusive. One open at a time.

Current `sheet-drawer`, `notebook-drawer` divs are not wired as slide-up drawers. Full rebuild.

---

### FIND-POLISH-002 — Two-mode layout: exploration frame vs. combat frame
**Severity:** HIGH ⛔ GATES ALL OTHER WOs

Two physical states. Transition is a slide — the table rearranges itself.

**Exploration / RP mode (default):**
- Right column expands, becomes dominant zone
- Large DM portrait, NPC face, scenery images land here
- Narration text strip visible
- Battle map hidden — not relevant
- The DM has the floor

**Combat mode:**
- Right column compresses to a sidebar
- Battle map (MagicMap plane) is exposed and dominant
- Sidebar: initiative, orb, quick stats
- The map is the star

**Trigger — engine-driven, not player-driven:**
- `combat_start` WS event → layout slides to combat mode
- `combat_end` WS event → layout slides back to exploration
- DM does not manage UI state. The game does.
- Both events already wired in WS bridge (WO-UI-2D-WIRING-001). Client needs to respond.

**Sound:** Same physical slide audio as drawers. The table is rearranging.

**Skin token stubs required in this WO** — see FIND-POLISH-010. Do not hardcode colors.

Full layout architecture rebuild required. Slate designs this first.

---

### FIND-POLISH-003 — Voice-first input not reflected; text input too dominant
**Severity:** HIGH

Primary input paradigm is **voice**. Text is accessibility fallback, not the headline.
Current giant text input bar is wrong — it should be small, tucked, unobtrusive.
Keyboard-only path still required for accessibility (focus → select → confirm → end turn → dice).

---

### FIND-POLISH-004 — DM panel narration text not persistent
**Severity:** MEDIUM

`#dm-panel-text` exists but hidden by default, shown only on `speaking_start`.
Thunder wants a persistent or semi-persistent narration text strip alongside the DM portrait.
Not a chat log. A readable output strip that fades gracefully, not a scrolling wall.

---

### FIND-POLISH-005 — Dice system wrong — tray vs. tower distinction critical
**Severity:** HIGH

**Two separate dice objects per UI Memo §11:**

**Dice tray (felt)** — fidget object. Physics OK. Cosmetic only. Never creates Box events.
Player can toss dice in here anytime for fun. Does not affect play. Green felt interior.
Dice tray is a permanent fixture on the player's side — always visible.

**Dice tower (ritual)** — authoritative rolls only. Workflow:
`PENDING_ROLL(spec)` issued by runtime → player selects correct dice → drops into tower
→ runtime validates → Box result → UI animates forced outcome.

**No roll buttons. No radial roll. No "click to roll".** Hard ban.

**Dice bag drawer** — pull open, green felt interior, full DnD 3.5 set lives here
(d4, d6, d8, d10, d12, d20, d100). Player picks dice from bag and places in tray or tower.

**Roll slip tray** — result ledger after tower drop. Existing `#slip-tray` is this.
Separate from the physical dice tray.

Current implementation has none of this. `#slip-tray` is results only, no physical objects,
no tray, no tower, no bag. Full rebuild.

---

### FIND-POLISH-006 — Notebook not implemented (core game artifact)
**Severity:** HIGH — not a polish item, a fundamental artifact

**Per UI Memo §14 and GT NB-001–005:**

Notebook is a **physical book** with fixed pages and page-turn. Not a tab panel.
Tools: pen, highlighter, eraser, lasso. Undo/redo (session-local). After save = ink (erase manually).
Paste-in clippings (rulebook copies, handouts) — resizable, rotatable, layered, then writable.

**Write-lock doctrine (hard law — GT NB-004 absolute ban):**
- Default WRITE-LOCKED
- Nothing written unless player explicitly does it OR explicitly requests it
- No autowrite. No silent logging.
- Consent handshake: `ConsentRequested` → `ConsentGranted` → `NotebookWriteApplied`
- Ambiguous response defaults NO. Consent scoped + expires.

Current `notebook.js` has three tab stubs (Draw, Transcript, Bestiary) — none functional.
The tab paradigm conflicts with the physical page-turn book model. Full rethink required.

**Two-book doctrine violation (GT HL-004):**
Beast Journal / Bestiary lives in the **Rulebook/Beast Book** — NOT in the Notebook.
The "Bestiary" tab in `notebook.js` is in the wrong artifact. Must move to Rulebook WO.

---

### FIND-POLISH-007 — Handout slot + recycle well missing
**Severity:** MEDIUM — physical table objects, not optional

**Per UI Memo §12:**
- DM handouts do not pop in. They **print/roll out of a player-edge slot into a tray**.
- Handouts are read-only on the table.
- Player can: pick up/read, paste into notebook (becomes clipping), discard into recycle well.
- **Recycle well** — retrievable discard. Not a delete. Always recoverable (≤2 actions).
- Auto-tidy if cluttered: FanStack (organizational only, always retrievable, supports PIN).

Neither the handout slot nor the recycle well exist in the current client.

---

### FIND-POLISH-008 — Rulebook (Tome) not implemented
**Severity:** HIGH — core game artifact

**Per UI Memo §13:**
- Read-only canon. Physical spellbook.
- Navigation: page flips, ribbons, player side-tags.
- Search (if present): TITLE + PAGE/SECTION only. No snippets.
- AI assist: open/find/read/gist-on-request only from visible content. No extra panels.
- Denial behavior: spoken line only ("You can't do that right now. Check the rulebook.")
  + physical "?" stamp on the surface involved. Click "?" → rulebook opens to rule_ref.
  No explanatory UI. No floating reason window.

Current Tome drawer is empty. No rulebook implementation.

---

### FIND-POLISH-009 — Image gen → notebook consent pipeline missing
**Severity:** MEDIUM

DM-generated images can be **offered** to notebook via `PASTE_ASSET` consent handshake.
Player must explicitly accept. Images do NOT auto-land. Hard ban per NB-004 + Image Gen L4.

**Image gen progress behavior (Image Gen Memo DEC-009 — hard ban):**
- No progress panels, thumbnail previews, pick-a-version menus, snackbars, tooltips, snippets
- Diegetic-only progress cues (audio: scribble, hum, stamping; subtle table activity)
- Only the final artifact appears when done — it prints/rolls out of the handout slot

Consent pipeline for image intake not implemented. Progress behavior not implemented.

---

### FIND-POLISH-010 — Battle mat not populated (stub session)
**Severity:** INFO — known gap, not a client bug

WS bridge wiring is in place (`_build_token_add_messages`). Stub session factory has no
entities/positions so nothing emits. Expected behavior.
Fix: dev fixture seeding 2-3 test tokens on connect for visual validation.

---

### FIND-POLISH-011 — No texture layer. Surface reads flat, not furniture.
**Severity:** MEDIUM — intimate polish, but must be architected from day one

Everything at this table should read as a real physical object:
- Table surface — wood grain, not a flat color
- Drawer faces — wood grain, panel edges, worn finish
- Drawer handles — brass or iron knob, embossed, worn
- Dice tray / bag interior — felt nap texture, real green felt
- Shelf rail — wood texture

**Skin system — plan from the start:**
CSS custom property token system. Skin tokens point at texture asset packs.
Multiple themes possible (dark walnut, light oak, tavern pine). Same layout, swappable skin.

**WO-UI-LAYOUT-001 must stub these tokens** even if initial values are placeholder colors:
```css
:root {
  --table-surface: url('/assets/skins/walnut/table-grain.webp');
  --drawer-face:   url('/assets/skins/walnut/drawer-face.webp');
  --drawer-handle: url('/assets/skins/walnut/handle.webp');
  --felt-surface:  url('/assets/skins/walnut/felt-green.webp');
}
```
Actual texture assets are deferred. Token architecture is not.

---

## Summary Table

| ID | Severity | Finding |
|---|---|---|
| FIND-POLISH-001 | HIGH | Drawer architecture wrong — pull knob handles, slide-up physical drawers, sound |
| FIND-POLISH-002 | HIGH ⛔ GATES ALL | Two-mode layout — exploration (DM dominant) vs combat (map dominant), engine-driven slide |
| FIND-POLISH-003 | HIGH | Voice-first input not reflected — text bar too dominant |
| FIND-POLISH-004 | MEDIUM | DM narration text not persistent |
| FIND-POLISH-005 | HIGH | Dice wrong — tray (fidget/cosmetic) vs tower (authoritative/ritual) distinction missing. No roll buttons. |
| FIND-POLISH-006 | HIGH | Notebook not implemented — physical page-turn book, write-lock doctrine |
| FIND-POLISH-007 | MEDIUM | Handout slot + recycle well missing |
| FIND-POLISH-008 | HIGH | Rulebook (Tome) not implemented — page flips, ribbons, "?" denial stamp |
| FIND-POLISH-009 | MEDIUM | Image gen → notebook consent pipeline (PASTE_ASSET) missing |
| FIND-POLISH-010 | INFO | Battle mat empty — stub session, not a wiring bug |
| FIND-POLISH-011 | MEDIUM | No texture layer — skin token stubs required in layout WO |

---

## Recommended Slate Actions (sequenced)

1. **WO-UI-LAYOUT-001** ⚡ FIRST — Two-mode layout (exploration/combat), engine-driven slide,
   audio, CSS skin token stubs. Gates everything else.
   Covers: FIND-POLISH-002, FIND-POLISH-011 (stub).

2. **WO-UI-DRAWER-001** — Pull knob drawer system, physicality mandate, voice-first input zone.
   Covers: FIND-POLISH-001, FIND-POLISH-003.

3. **WO-UI-DICE-001** — Dice bag drawer + felt tray (fidget/cosmetic) + dice tower (ritual/authoritative).
   No roll buttons. PENDING_ROLL workflow.
   Covers: FIND-POLISH-005.

4. **WO-UI-NOTEBOOK-001** — Physical page-turn notebook, pen/highlighter/eraser, write-lock
   consent handshake, paste-in clippings. Resolve tab vs. page-turn model question.
   Covers: FIND-POLISH-006, FIND-POLISH-009.

5. **WO-UI-RULEBOOK-001** — Read-only rulebook, page flips, ribbons, side-tags, "?" denial
   stamp, rule_ref routing. No snippets.
   Covers: FIND-POLISH-008.

6. **WO-UI-HANDOUT-001** — Handout printer slot, player tray, recycle well, FanStack auto-tidy.
   Covers: FIND-POLISH-007.

7. **WO-UI-NARRATION-001** — DM panel persistent narration text strip.
   Covers: FIND-POLISH-004.

8. **WO-UI-BATTLE-FIXTURE-001** — Dev fixture, 2-3 test tokens on connect.
   Covers: FIND-POLISH-010.

9. **WO-UI-TEXTURE-001** (deferred) — Texture asset packs, walnut default skin.
   Covers: FIND-POLISH-011 (execution).

---

*Anvil — filed for Slate dispatch. Thunder sign-off required before WOs are cut.*
*Doctrine sources: DOCTRINE_04_TABLE_UI_MEMO_V4.txt, DOCTRINE_02_GOLDEN_TICKET_V12.txt*
*3D camera postures (STANDARD/DOWN/LEAN_FORWARD) confirmed dead — 2D pivot sealed 2026-02-24.*

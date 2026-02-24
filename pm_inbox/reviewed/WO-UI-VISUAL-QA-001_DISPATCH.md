# WO-UI-VISUAL-QA-001 — Visual QA Inspection Pass

**Issued:** 2026-02-23
**Authority:** PM — idle builder window. 12 gap WOs + 3 NS P0 WOs in flight. Before those land, PM needs a structured visual findings brief on the current build so polish WOs can be pre-drafted and ready to dispatch immediately after the batch completes.
**Gate:** None. This WO produces a findings document, not a gate. Output is `pm_inbox/VISUAL_QA_FINDINGS_001.md`.
**Blocked by:** Nothing. Current build is the inspection target — pre-batch-landing baseline.

---

## 1. Task

Spin up the dev server, open the scene in a browser, and conduct a systematic visual inspection of the current Three.js UI against `docs/specs/UX_VISION_PHYSICAL_TABLE.md`. Use Playwright and the scene dump tool where useful. Produce a structured findings brief that PM can convert directly to WOs.

This is not a gate pass/fail. This is a PM intelligence-gathering operation. Be honest and complete. If something looks wrong, say so.

---

## 2. Procedure

### Step 1 — Start dev server

```bash
npm run dev --prefix client
```

Confirm Vite starts and reports a local URL (expected: `http://localhost:5173` or similar).

### Step 2 — Open scene

Navigate browser to the dev server URL. Wait for Three.js scene to initialize (WebSocket will fail to connect — that's expected, backend is not running). Inspect the static scene geometry.

Use `?dump=1` flag to trigger `window.__SCENE_DUMP__` if mesh inventory is needed.

### Step 3 — Systematic inspection

Walk through each section of `UX_VISION_PHYSICAL_TABLE.md` in order. For each section, take a screenshot and assess the current build against the vision. Note gaps, discrepancies, and aesthetic issues.

Sections to inspect (in order):

1. **Table layout** — Two zones visible? Player side vs DM side legible? Camera angle correct (seated, slight angle, looking across table)?
2. **Crystal ball** — Present? Position correct (DM side)? Glow/pulse infrastructure wired? Portrait mesh inside?
3. **Notebook** — Present on player side? 3D book geometry? Cover visible? Positioned correctly relative to other objects?
4. **Dice bag + dice tower** — Both present? Tower has visible opening? Positioned on player side? Proportions feel right?
5. **Character sheet** — Present? Paper-like appearance (not a UI panel)? Positioned on player side?
6. **Battle map scroll** — Present on DM side? Flat 2D surface? Correct position?
7. **Tokens** — Flat 2D chip geometry (not cylinders)? TOKEN-CHIP-001 may not be landed yet — note current state.
8. **Fog of war** — Fog layer present? Opacity correct? Vision type differentiation (FOG-VISION-001 likely not landed — note).
9. **Lighting** — Warm candlelight feel? Three PointLights + map spot + tray fill + hemisphere + ambient? Any areas too bright, too dark, too cold?
10. **Overall table proportions** — Does it feel like a real table? Objects correctly scaled relative to each other? Anything that looks jumbled, too large, too small, or mispositioned?
11. **Dice tower area specifically** — PM has flagged this as visually jumbled. Inspect closely. What specifically looks wrong?
12. **Player shelf** — Objects sitting naturally on the shelf? Any clipping, floating, or misalignment?

### Step 4 — Take screenshots

At minimum:
- Full scene overview (default camera angle)
- Player side close-up
- DM side close-up
- Dice tower area close-up
- Any specific problem areas identified during inspection

Save screenshots to `client/tests/screenshots/qa_001/` (create if needed).

### Step 5 — Write findings brief

---

## 3. Output Format

File: `pm_inbox/VISUAL_QA_FINDINGS_001.md`

```markdown
# Visual QA Findings — Pass 001
**Date:** 2026-02-23
**Build:** [commit hash]
**Inspector:** Anvil

## Summary
[2-3 sentences: overall state, count of issues by severity]

## Findings

### [FINDING-VQ-001] [Short title]
**Severity:** P0 / P1 / P2 / Cosmetic
**Section:** [UX Vision section]
**Observed:** [What is actually rendered]
**Expected:** [What the vision doc specifies]
**Screenshot:** [filename]
**Notes:** [Anything else relevant]

[...repeat for each finding...]

## What Looks Good
[Brief notes on areas that match the vision — helps PM avoid drafting WOs for things that don't need them]

## Deferred / Cannot Assess
[Items that can't be evaluated because a dependent WO isn't landed yet — e.g. TOKEN-CHIP-001, FOG-VISION-001]
```

---

## 4. Severity Guide

| Severity | Definition |
|----------|------------|
| P0 | Experience-blocking. Object missing, completely wrong, or breaks the physical table metaphor. |
| P1 | Vision compliance gap. Object present but geometry, position, or proportion deviates from spec in a noticeable way. |
| P2 | Polish. Correct object, minor aesthetic issue — lighting, color, scale, feel. |
| Cosmetic | Tiny — spacing, alignment, minor color. Last-mile polish. |

---

## 5. Deliverable

- `pm_inbox/VISUAL_QA_FINDINGS_001.md` — structured findings brief
- `client/tests/screenshots/qa_001/` — screenshots

No gate. No test file. No code changes. Findings only.

PM will read the brief and draft polish WOs as appropriate.

## Preflight

```bash
npm run dev --prefix client
# navigate to localhost URL, inspect scene
```

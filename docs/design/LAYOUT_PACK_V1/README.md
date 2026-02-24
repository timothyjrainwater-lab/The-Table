# LAYOUT_PACK_V1 — Table Scene Authority Document

## North Star

Poker-table embodiment: a real person sits at a walnut table, looks across at a glowing orb (the DM's presence), has their personal objects spread out on the shelf in front of them, and can turn right to reach the dice station. No HUD. No game UI. Every pixel is a physical object or the room it sits in.

## The Four Primary Postures

| Posture | What must be visible |
|---------|---------------------|
| STANDARD | Orb (upper frame), vault depth cue, far rail. Shelf barely at bottom — presence only. |
| DOWN | Shelf fills frame: sheet numbers readable, notebook page readable, rulebook headings readable. |
| LEAN_FORWARD | Vault recess unmistakable. Orb still in frame. Never true top-down. |
| DICE_TRAY | Tray + tower dominate. Feels like turning right, not teleporting. |

## Golden Frame Rule

The `golden/` folder contains reference PNGs at 1920×1080. If your change produces a materially different result in any posture, you must update the golden frame in the same commit with a rationale comment. If you can't explain the change in terms of posture intent + zone rules, don't make it.

## How to Regenerate Golden Frames

1. Start dev server: `npm run dev --prefix client`
2. Open: `http://localhost:3000?debug=1&zones=1`
3. Resize browser to exactly 1920×1080
4. Use hotkeys (1-5) to navigate postures
5. Screenshot each posture with OS screenshot tool
6. Save to `docs/design/LAYOUT_PACK_V1/golden/[POSTURE]_1080.png`

## Hard Bans

- No tooltip, popover, or snippet components
- No roll buttons or action menus that execute game actions
- No hardcoded camera positions outside `camera_poses.json`
- No hardcoded object positions outside `table_objects.json`
- No hardcoded zone bounds outside `zones.json`

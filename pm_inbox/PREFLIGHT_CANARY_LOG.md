# Preflight Canary Log

Builders append one entry per session after running `python scripts/preflight_canary.py`.

---

## Template

```
### <date> — <builder callsign> — <git commit hash>

**Pipeline canaries:**
- Image: PASS / FAIL — content_hash: `<hash>` — path: `<path>`
- Voice: PASS / FAIL

**Skill artifacts:**
- Image: prompt: "<prompt text>" — seed: <seed> — path: `<path>` — self-critique: <1 sentence>
- Voice: persona: <persona_id> — script: "<script text>" — self-critique: <1 sentence>

**Notes:** <optional, 1 sentence if FAIL or unusual behavior>
```

---

## Entries

### 2026-02-19 — Anvil (Rust Blighthammer) — d8a6b3d

**Pipeline canaries:**
- Image: PASS — content_hash: `29bc65482ff72286` — path: `image_cache/canary_image_v1_2477320241.png`
- Voice: PASS

**Skill artifacts:**
- Image: prompt: "Portrait of a scarred half-orc cleric in dented plate armor, tribal face paint, holy symbol of Kord on a leather cord around his thick neck, battlefield medic, grim determined expression, oil painting style, warm torchlight" — seed: 3221227860 — path: `image_cache/anvil_rust_blighthammer_v1_3221227860.png` — self-critique: Front-loaded physical details within 62-token budget; Kord symbol and tribal paint sell the cleric/barbarian multiclass.
- Voice: persona: npc_male — script: "Kord doesn't heal the careful. He heals the ones still standing." — self-critique: George reference path doubled in speak.py (relative inside absolute), fell back to persona default — voice landed gruff enough but lost the deeper timbre the george ref would have given.

**Notes:** speak.py --ref flag prepends the adapter's base path, so passing a full path from models/voices/ causes double-pathing. Builders should use just the filename or the --persona flag alone.

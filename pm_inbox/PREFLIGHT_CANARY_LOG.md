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

(append below)

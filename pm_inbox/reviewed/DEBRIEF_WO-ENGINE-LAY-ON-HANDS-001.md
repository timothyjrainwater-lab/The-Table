# DEBRIEF — WO-ENGINE-LAY-ON-HANDS-001
# Paladin Lay on Hands Daily HP Pool

**Verdict:** ACCEPTED 11/11 (spec 10)
**Gate:** ENGINE-LAY-ON-HANDS
**Date:** 2026-02-26
**WO:** WO-ENGINE-LAY-ON-HANDS-001

---

## Pass 1 — Per-File Breakdown

### `aidm/schemas/entity_fields.py`

**Changes made:**
- `EF.LAY_ON_HANDS_POOL` = "lay_on_hands_pool" — daily pool of HP available to heal
- `EF.LAY_ON_HANDS_USED` = "lay_on_hands_used" — HP expended from pool this day

### `aidm/schemas/intents.py`

**Changes made:**
- `LayOnHandsIntent(actor_id, target_id, amount, action_type="standard")` — standard action intent for the ability

### `aidm/core/lay_on_hands_resolver.py` (new file)

**Changes made:**
- New resolver following `smite_evil_resolver.py` pattern
- Validates paladin class via `EF.CLASS_LEVELS`
- Checks pool remaining (`LAY_ON_HANDS_POOL - LAY_ON_HANDS_USED`)
- Clamps heal amount to remaining pool
- Applies healing with HP cap: `min(hp_before + amount, hp_max)`
- Emits appropriate events

### `aidm/core/rest_resolver.py`

**Changes made:**
- Full-rest block: `LAY_ON_HANDS_POOL` reset computed from `paladin_level × max(1, CHA_mod)`
- `LAY_ON_HANDS_USED` reset to 0

### `aidm/core/action_economy.py`

**Changes made:**
- `LayOnHandsIntent` mapped as standard action

### `aidm/core/play_loop.py`

**Changes made:**
- `LayOnHandsIntent` routing added as new elif branch

**builder.py chargen init — NOT added.**
Established pattern: pool fields are set in test fixtures and scenario setup, not by the character builder. `build_character()` records class features as string markers (e.g., `"lay_on_hands"`) but does not translate them to working pool fields. Same pattern as smite uses, bardic music uses, wild shape uses. Builder stays clean of pool math.

**Bonus test (LOH-11):** Builder added one test beyond spec (10). Accepted — more gate coverage is not a defect.

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-LAY-ON-HANDS-001 ACCEPTED 11/11. New `EF.LAY_ON_HANDS_POOL` + `EF.LAY_ON_HANDS_USED` fields; `LayOnHandsIntent`; `lay_on_hands_resolver.py` (smite pattern); full-rest pool recovery in `rest_resolver.py`; `action_economy.py` mapping; `play_loop.py` routing. Pool formula: `paladin_level × max(1, CHA_mod)`. HP cap enforced. builder.py chargen init NOT added — entity-dict-at-load-time is the established pattern across all class-feature pools. Bonus test accepted. Note: `build_character()` gap (pool fields absent for chargen entities) flagged as FINDING-CHARGEN-POOL-INIT-001.

---

## Pass 3 — Retrospective

**Pattern confirmed:** The entity-dict-at-load-time convention for class-feature pools is consistent across the codebase: smite, bardic music, wild shape, and now lay on hands all follow the same pattern. builder.py lists class features as string markers only. Pool math lives in the resolvers and is initialized from entity dicts at scenario load, not at chargen time.

**Chargen gap surfaced:** This convention means a paladin built via `build_character()` will arrive in a live session with `EF.LAY_ON_HANDS_POOL` absent. The resolver reads 0 and the ability is silently nonfunctional. The same gap exists for smite, bardic music, and wild shape. Non-blocking for engine gate tests (which set up entities directly), but a real play defect. Flagged as FINDING-CHARGEN-POOL-INIT-001 — WO-CHARGEN-POOL-INIT-001 recommended to wire all class-feature pools at chargen time.

**Recommendation:** WO-CHARGEN-POOL-INIT-001 should audit every class-feature pool field and add initialization logic to `build_character()` output. Scope: smite uses, lay on hands pool, bardic music uses, wild shape uses. One WO, all four pools.

---

*Debrief filed by Slate (PM) on builder verdict receipt.*

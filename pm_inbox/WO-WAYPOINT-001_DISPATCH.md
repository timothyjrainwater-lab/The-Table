# WO-WAYPOINT-001: Waypoint Maiden Voyage — Full Table Loop Determinism Proof

**Classification:** CODE (integration test + fixtures + smoke scenario)
**Priority:** Critical path — proves the ship sails
**Dispatched by:** Slate (PM)
**Date:** 2026-02-20
**Aegis audit:** APPROVED with three tightenings applied (see §Aegis Audit Notes)

---

## Objective

Prove the entire table loop works end-to-end: load characters from disk, run a complete combat exchange that touches **four surfaces** (skill check, feat modifier, spell with save, condition/status enforcement), write a replayable event log, and replay deterministically to the same final state and the same canonical transcript.

**The three laws of this WO:**
1. If it's not written, it's not true.
2. If it's not replayable, it's not trusted.
3. If it doesn't hit the four surfaces, it doesn't count.

**Time isolation rule:** Wall-clock time (`timestamp` parameter) is metadata only. No timestamp value may influence any rule outcome (d20 result, hit/miss, damage, save, condition application). If any code path uses a timestamp as input to a game rule, that is a blocking defect.

---

## Scope

### IN SCOPE

1. **Character fixture files** — Three JSON files loaded from disk at test start.
2. **Gate test file** — `tests/test_waypoint_001.py` with 5 gate tests (W-0 through W-4).
3. **Smoke scenario** — `scripts/smoke_scenarios/waypoint.py` exercising the full loop with banner/record_pass/record_fail output.
4. **Smoke orchestrator hookup** — Wire waypoint scenario into `scripts/smoke_test.py`.

### OUT OF SCOPE

- No changes to any resolver, play_loop, replay_runner, event_log, or schema.
- No changes to any `aidm/` module.
- No changes to doctrine files.
- If the engine blocks the test, builder files a defect and stops. No engine fixes in this WO.

---

## The Scenario: "The Enchantress's Gambit"

Three characters. One round. Three turns. Fixed seed `WAYPOINT_SEED` (builder picks any integer; the scenario is designed so correctness does not depend on specific roll outcomes).

### Characters (JSON Fixtures)

All fields use `EF` constant names from `aidm/schemas/entity_fields.py`. Builder must verify field names against `EF` before writing JSON.

#### `tests/fixtures/waypoint/kael_ironfist.json` — Fighter 5

```json
{
    "entity_id": "kael_ironfist",
    "name": "Kael Ironfist",
    "hp_current": 45,
    "hp_max": 45,
    "ac": 18,
    "attack_bonus": 8,
    "bab": 5,
    "str_mod": 3,
    "dex_mod": 1,
    "int_mod": 0,
    "con_mod": 2,
    "wis_mod": 1,
    "cha_mod": 0,
    "save_fortitude": 6,
    "save_reflex": 2,
    "save_will": 2,
    "team": "party",
    "weapon": "longsword",
    "position": {"x": 5, "y": 5},
    "defeated": false,
    "size_category": "medium",
    "base_speed": 30,
    "conditions": {},
    "feats": ["power_attack", "weapon_focus_longsword"],
    "skill_ranks": {"spot": 3, "tumble": 4},
    "class_skills": ["tumble", "spot"],
    "armor_check_penalty": 0
}
```

**Design notes:** Power Attack (STR 13+ required: STR mod +3 ✓, BAB 1+ ✓) + Weapon Focus longsword (BAB 1+ ✓). Spot ranks for skill check surface.

#### `tests/fixtures/waypoint/seraphine.json` — Wizard 5

```json
{
    "entity_id": "seraphine",
    "name": "Seraphine the Enchantress",
    "hp_current": 28,
    "hp_max": 28,
    "ac": 13,
    "attack_bonus": 2,
    "bab": 2,
    "str_mod": 0,
    "dex_mod": 1,
    "int_mod": 3,
    "con_mod": 1,
    "wis_mod": 2,
    "cha_mod": 1,
    "save_fortitude": 2,
    "save_reflex": 2,
    "save_will": 6,
    "team": "party",
    "weapon": "quarterstaff",
    "position": {"x": 3, "y": 5},
    "defeated": false,
    "size_category": "medium",
    "base_speed": 30,
    "conditions": {},
    "caster_level": 5,
    "spell_dc_base": 15,
    "spells_prepared": ["hold_person"],
    "feats": [],
    "skill_ranks": {"concentration": 8, "spot": 2},
    "class_skills": ["concentration"],
    "armor_check_penalty": 0
}
```

**Design notes:** `spell_dc_base=15` for Hold Person (Will save DC 15). Caster level 5.

#### `tests/fixtures/waypoint/bandit_captain.json` — Warrior 3

```json
{
    "entity_id": "bandit_captain",
    "name": "Bandit Captain",
    "hp_current": 22,
    "hp_max": 22,
    "ac": 16,
    "attack_bonus": 5,
    "bab": 3,
    "str_mod": 2,
    "dex_mod": 1,
    "int_mod": 0,
    "con_mod": 1,
    "wis_mod": 0,
    "cha_mod": 0,
    "save_fortitude": 4,
    "save_reflex": 2,
    "save_will": 1,
    "team": "monsters",
    "weapon": "longsword",
    "position": {"x": 10, "y": 5},
    "defeated": false,
    "size_category": "medium",
    "base_speed": 30,
    "conditions": {},
    "feats": [],
    "skill_ranks": {},
    "class_skills": [],
    "armor_check_penalty": 0
}
```

**Design notes:** Will save +1 vs DC 15 → needs 14+ on d20 to save (30% success). The save _will_ be exercised regardless of outcome; condition application happens on failure. If the save succeeds for a given seed, condition application is not exercised — see §Seed Selection.

### Seed Selection

**Rule:** The builder picks `WAYPOINT_SEED` (any integer) such that for that seed, the Bandit Captain's Will save **fails** (d20 + 1 < 15, meaning d20 ≤ 13). This guarantees the `condition_applied` event fires. The builder writes a small seed-finder helper that tries seeds until this condition is met and hardcodes the result.

**What the seed does NOT need to guarantee:** Kael's attack does NOT need to hit. The feat modifier proof comes from the attack_roll event's modifier breakdown, not from damage dealt (see §W-2).

### Turn Sequence

**Turn 0 — Seraphine casts Hold Person on Bandit Captain**
- Input: `SpellCastIntent(caster_id="seraphine", spell_id="hold_person", target_ids=["bandit_captain"])`
- Expected events: `spell_cast`, `save_rolled` (Will, DC 15), `condition_applied` (paralyzed, on failed save)
- Surfaces hit: **Spell with save**, **Condition application**

**Turn 1 — Kael: Spot check + longsword attack with Power Attack**
- Step 1 (skill check): Call `resolve_skill_check(kael_entity, "spot", dc=15, rng=rng)` directly. Record result. Manually append a `skill_check` event to the EventLog with the result payload (d20, total, dc, success, ability_mod, skill_ranks).
- Step 2 (attack): `AttackIntent(attacker_id="kael_ironfist", target_id="bandit_captain", weapon=Weapon(...), power_attack_penalty=2)` via `execute_turn()`.
- Expected events: `skill_check` (manual), `attack_roll` (with `feat_modifier` and `power_attack_penalty` fields in payload), and if hit: `damage_roll`, `hp_changed`.
- Surfaces hit: **Skill check**, **Feat modifier**

**Turn 2 — Bandit Captain attempts to act while paralyzed**
- Input: `AttackIntent(attacker_id="bandit_captain", target_id="kael_ironfist", weapon=Weapon(...))` — a standard attack intent submitted to `execute_turn()`.
- **Expected behavior (two branches):**
  - **Branch A (engine blocks):** `execute_turn()` checks `actions_prohibited` on the actor's condition modifiers and returns `status="invalid_intent"` or similar with a `"reason"` indicating the actor cannot act due to conditions. The test asserts this rejection.
  - **Branch B (engine does not block):** `execute_turn()` resolves the attack despite the paralyzed condition. This is a **discoverable gap** — the play_loop currently validates target-not-defeated but does NOT check actor's `actions_prohibited` flag. If the builder hits Branch B, they:
    1. Document the gap as `FINDING-WAYPOINT-01: play_loop does not enforce actions_prohibited on actor conditions`.
    2. The test still PASSES W-2 by verifying the paralyzed condition exists in state (the condition was applied; enforcement is a separate WO).
    3. The builder notes this in the debrief as a stop condition they chose not to cross.
- Surface hit: **Condition enforcement** (tested either via engine block or via gap documentation)

---

## What "Byte-Stable Where It Must Be" Means

### Byte-stable (must be identical across runs with same seed):

| Artifact | Stability guarantee |
|----------|-------------------|
| Every `d20_roll` value in every event payload | Byte-identical |
| Every `hit`/`miss` determination | Byte-identical |
| Every `damage` value in every event payload | Byte-identical |
| Every `save_rolled` result (d20, total, success/fail) | Byte-identical |
| Every `condition_applied` event (condition name, entity_id) | Byte-identical |
| Every `hp_changed` delta | Byte-identical |
| Every `skill_check` result (d20, total, success/fail) | Byte-identical |
| Every `feat_modifier` and `power_attack_penalty` in attack_roll payloads | Byte-identical |
| `NarrativeBrief` serialized dicts (per-turn) | Byte-identical |

### NOT byte-stable (expected to vary):

| Artifact | Why it varies |
|----------|--------------|
| `Event.timestamp` values | Metadata; `timestamp` parameter differs between runs |
| `WorldState.state_hash()` between live and replay | A9 divergence: play_loop stores conditions as `dict[name: {...}]`, replay_runner stores as `list[{"name": ...}]` — different representation, same semantics |
| `Event.event_id` assignment order | Must be monotonic within a run but exact IDs may shift if manually-appended events (skill_check) change count |

### The replay contract:

**Live → Log → Replay must produce identical rule outcomes.** The comparison is on a **normalized view** (see §W-1). If normalization cannot reconcile the live and replay outputs (i.e., the semantic content differs, not just the representation), that is a blocking defect.

---

## Gate Tests (`tests/test_waypoint_001.py`)

### W-0: Subsystem Coverage Canary

Execute the scenario. Collect all event types from the combined EventLog.

| Assert | What it proves |
|--------|---------------|
| `"spell_cast"` in event_types | Spell subsystem fired |
| `"save_rolled"` in event_types | Save subsystem fired |
| `"condition_applied"` in event_types | Condition subsystem fired |
| `"attack_roll"` in event_types | Attack subsystem fired |
| `"skill_check"` in event_types | Skill subsystem fired |

If any assert fails, the scenario did not hit all four surfaces. WO is RED.

### W-1: Live → Log → Replay Determinism

Execute the scenario live. Record:
- All events (the live EventLog)
- The final WorldState (live)
- Per-turn NarrativeBriefs (live)

Write the EventLog to a temp JSONL file via `EventLog.to_jsonl()`. Read it back via `EventLog.from_jsonl()`. Replay via `replay_runner.run()` with the same initial state and same seed.

**Build a normalized view** from both runs. The normalized view is a list of dicts, one per event, containing ONLY rule-outcome fields:

```python
normalized = []
for event in events:
    entry = {"event_type": event.event_type}
    p = event.payload
    if event.event_type == "attack_roll":
        entry.update({
            "d20_roll": p["d20_roll"],
            "total": p["total"],
            "hit": p["hit"],
            "attack_bonus": p.get("attack_bonus"),
            "feat_modifier": p.get("feat_modifier"),
            "condition_modifier": p.get("condition_modifier"),
            "power_attack_penalty": p.get("power_attack_penalty"),
        })
    elif event.event_type == "damage_roll":
        entry.update({
            "total_damage": p.get("total_damage"),
            "dice_result": p.get("dice_result"),
            "feat_damage_modifier": p.get("feat_damage_modifier"),
        })
    elif event.event_type == "save_rolled":
        entry.update({
            "d20_roll": p.get("d20_roll"),
            "total": p.get("total"),
            "success": p.get("success"),
            "dc": p.get("dc"),
            "save_type": p.get("save_type"),
        })
    elif event.event_type == "condition_applied":
        entry.update({
            "entity_id": p.get("entity_id"),
            "condition": p.get("condition"),
        })
    elif event.event_type == "hp_changed":
        entry.update({
            "entity_id": p.get("entity_id"),
            "delta": p.get("delta"),
            "old_hp": p.get("old_hp"),
            "new_hp": p.get("new_hp"),
        })
    elif event.event_type == "skill_check":
        entry.update({
            "d20_roll": p.get("d20_roll"),
            "total": p.get("total"),
            "dc": p.get("dc"),
            "success": p.get("success"),
        })
    elif event.event_type in ("spell_cast", "turn_start", "turn_end"):
        pass  # metadata only, not rule outcomes
    else:
        pass  # informational events — skip
    if len(entry) > 1:  # has more than just event_type
        normalized.append(entry)
```

**Assertions:**

| Assert | What it proves |
|--------|---------------|
| `live_normalized == replay_normalized` | Same seed + same events → same rule outcomes across live and replay |
| Run replay 10x, collect all `final_hash` values → `len(set(hashes)) == 1` | Replay-to-replay is byte-identical (reducer is deterministic) |

**A9 handling:** If `live_normalized != replay_normalized`, the builder must determine whether the difference is:
- **Representation-only** (e.g., condition stored as dict vs list but same condition name/entity): normalize further and re-compare.
- **Semantic** (e.g., different d20 values, different hit/miss): this is a **blocking defect** — `DEFECT-WAYPOINT-A9`. Builder files it and stops.

### W-2: Final State Matches Expected + Modifier Breakdown Proof

Execute the scenario. Inspect the final WorldState and event payloads.

**State assertions:**

| Assert | What it proves |
|--------|---------------|
| Bandit Captain has `"paralyzed"` in `EF.CONDITIONS` | Condition was applied by spell |
| Kael HP == 45 | Kael was not targeted |
| Seraphine HP == 28 | Seraphine was not targeted |

**Modifier breakdown assertions (from attack_roll event payload):**

| Assert | What it proves |
|--------|---------------|
| `attack_roll.payload["power_attack_penalty"]` == -2 (or equivalent field showing penalty applied) | Power Attack feat engaged |
| `attack_roll.payload["feat_modifier"]` includes Weapon Focus +1 (or equivalent field) | Weapon Focus feat engaged |
| Computed total == `d20 + base_attack_bonus + str_mod + feat_modifier - power_attack_penalty + condition_modifier` | Modifier math is correct |

**Damage assertions (only if hit — conditional, not required for pass):**

| Assert | What it proves |
|--------|---------------|
| If hit: `damage_roll.payload["feat_damage_modifier"]` includes Power Attack +2 | Power Attack damage bonus applied |
| If hit: Bandit Captain HP < 22 | Damage was applied |

**Key design:** The feat proof comes from the modifier breakdown in the event payload, NOT from whether the attack hit. A nat-1 still proves Power Attack and Weapon Focus because the modifiers appear in the payload regardless of the d20 outcome.

### W-3: Transcript Determinism

Execute the scenario twice with the same seed (same `WAYPOINT_SEED`, same `timestamp`).

For each turn, assemble a `NarrativeBrief` via `assemble_narrative_brief()`. Serialize all briefs to dicts.

| Assert | What it proves |
|--------|---------------|
| Run 1 serialized briefs == Run 2 serialized briefs | Same combat → same narrative, no randomness leaking into transcript |
| Turn 0 brief references hold_person (spell name present) | Spell surface reached narrative |
| Turn 1 brief has weapon_name populated | Attack surface reached narrative |

### W-4: No Hidden Time Inputs

Execute the scenario with `timestamp=1000.0`. Execute again with `timestamp=9999.0`. Same seed, same intents, same entities.

Build the normalized view (same as W-1) for both runs.

| Assert | What it proves |
|--------|---------------|
| `normalized_1000 == normalized_9999` | Timestamps do not affect any rule outcome |

This is the **time isolation gate**. If any d20 roll, hit/miss, damage value, save result, or condition application differs between the two runs, there is a hidden time input somewhere in the rule resolution pipeline. That is a blocking defect: `DEFECT-WAYPOINT-TIME`.

---

## Integration Seams

| Seam | Module | Function | Contract |
|------|--------|----------|----------|
| Play loop | `aidm/core/play_loop.py` | `execute_turn()` | Drives each turn. Accepts `AttackIntent`, `SpellCastIntent`. |
| Attack resolver | `aidm/core/attack_resolver.py` | `resolve_attack()` | Called internally by execute_turn for `AttackIntent`. |
| Feat resolver | `aidm/core/feat_resolver.py` | `get_attack_modifier()`, `get_damage_modifier()` | Called by attack_resolver when entity has feats. Must populate `feat_modifier` and `power_attack_penalty` in event payload. |
| Spell resolver | `aidm/core/spell_resolver.py` | `SpellResolver`, `SpellCastIntent` | Called by execute_turn for `SpellCastIntent`. Resolves save + conditions. |
| Skill resolver | `aidm/core/skill_resolver.py` | `resolve_skill_check()` | Called directly by test harness. NOT routed through play_loop. |
| Conditions | `aidm/core/conditions.py` | `get_condition_modifiers()` | Computes aggregate condition modifiers including `actions_prohibited`. |
| RNG | `aidm/core/rng_manager.py` | `RNGManager(master_seed)` | Single seed drives all randomness. Named streams. |
| Event log | `aidm/core/event_log.py` | `EventLog`, `to_jsonl()`, `from_jsonl()` | JSONL serialization round-trip for replay. |
| Replay | `aidm/core/replay_runner.py` | `run()`, `reduce_event()` | Replays event log to reconstruct state. |
| State | `aidm/core/state.py` | `WorldState.state_hash()` | Sorted-key JSON + SHA-256. |
| Narrative | `aidm/lens/narrative_brief.py` | `assemble_narrative_brief()` | One-way valve from Box to Spark. |
| Spell data | `aidm/data/spell_definitions.py` | `SPELL_REGISTRY` | Spell definitions including `hold_person`. |
| Entity fields | `aidm/schemas/entity_fields.py` | `EF` constants | All entity dict keys. |
| Smoke infra | `scripts/smoke_scenarios/common.py` | `banner()`, `record_pass()`, `record_fail()` | Recording helpers for smoke scenario output. |

---

## Assumptions to Validate

| # | Assumption | How to validate |
|---|-----------|-----------------|
| A1 | `hold_person` exists in `SPELL_REGISTRY` with save_type=WILL and conditions_on_fail containing "paralyzed" | Read `aidm/data/spell_definitions.py`, find hold_person entry |
| A2 | `resolve_skill_check()` is callable standalone (not only via play_loop) and returns a result with d20_roll, total, success | Read `aidm/core/skill_resolver.py` function signature and return type |
| A3 | `AttackIntent` has a `power_attack_penalty` field (or equivalent mechanism) | Read `aidm/schemas/attack.py` |
| A4 | `attack_resolver.resolve_attack()` populates `feat_modifier` and `power_attack_penalty` in the `attack_roll` event payload | Read `aidm/core/attack_resolver.py` event emission code |
| A5 | `EventLog.to_jsonl()` uses deterministic serialization (`sort_keys=True`) | Read `aidm/core/event_log.py` serialization code |
| A6 | `replay_runner.run()` accepts an initial state and seed, returns a ReplayReport with `final_hash` | Read `aidm/core/replay_runner.py` |
| A7 | No existing "load entity from JSON file" utility — builder creates a minimal `json.load()` wrapper | Confirmed by PM exploration: none exists |
| A8 | `NarrativeBrief` serialization is deterministic (frozen dataclass, no random fields) | Read `aidm/lens/narrative_brief.py` |

If any assumption fails, STOP. Do not work around it. Document which assumption failed and why.

---

## File Structure

### New Files (5)

| File | Purpose |
|------|---------|
| `tests/fixtures/waypoint/kael_ironfist.json` | Fighter fixture (see §Characters) |
| `tests/fixtures/waypoint/seraphine.json` | Wizard fixture (see §Characters) |
| `tests/fixtures/waypoint/bandit_captain.json` | Enemy fixture (see §Characters) |
| `tests/test_waypoint_001.py` | Gate tests W-0 through W-4 |
| `scripts/smoke_scenarios/waypoint.py` | Runnable smoke scenario |

### Modified Files (1)

| File | Change |
|------|--------|
| `scripts/smoke_test.py` | Import and call waypoint scenario (1-2 lines) |

### Frozen (everything else)

No changes to any `aidm/` module. No changes to any existing test file. No changes to doctrine.

---

## Implementation Order

1. Create `tests/fixtures/waypoint/` directory + 3 JSON files (verify field names against `EF` constants)
2. Write `load_entity(path)` helper in test file — `json.load()` wrapper, ~5 lines
3. Write seed-finder helper: loop seeds, run Turn 0 (Hold Person), check if Will save fails. Hardcode result as `WAYPOINT_SEED`
4. Write scenario orchestrator function: loads fixtures, builds WorldState, runs 3 turns, returns `(final_state, event_log, briefs)`
5. Write W-0 (canary) — verify all 5 event types present
6. Write W-2 (state + modifier breakdown) — verify conditions, HP, feat math
7. Write W-1 (live→log→replay) — build normalized view, compare
8. Write W-3 (transcript) — verify NarrativeBrief determinism
9. Write W-4 (time isolation) — verify timestamp independence
10. Write smoke scenario `scripts/smoke_scenarios/waypoint.py` using `banner()`/`record_pass()`/`record_fail()` pattern
11. Wire into `scripts/smoke_test.py`

---

## Stop Conditions

1. **Any assumption (A1-A8) fails.** Stop, document, escalate.
2. **Seed search fails.** If no seed in [1, 100000] produces a failed Will save for the Bandit Captain, there is a resolver bug. Stop.
3. **A9 semantic divergence.** If live→replay normalized comparison shows different d20 values, hit/miss results, or damage amounts (not just dict-vs-list representation), file `DEFECT-WAYPOINT-A9` and stop.
4. **Hidden time input.** If W-4 fails (rule outcomes differ across timestamps), file `DEFECT-WAYPOINT-TIME` and stop.
5. **Scope creep.** Any temptation to modify resolvers, event_log, play_loop, or schemas → STOP. File a finding in the debrief. This WO tests the engine as-is.
6. **Import failure.** If any integration seam import fails, the module may not exist or may have been renamed. Stop.

---

## Aegis Audit Notes

Three tightenings applied per Aegis audit:

1. **Modifier breakdown proof (not damage proof).** Feat coverage comes from the `attack_roll` event payload showing `power_attack_penalty` and `feat_modifier` fields, NOT from asserting HP decreased. Attack can miss; the math proof is in the modifiers regardless.

2. **Live→replay normalized comparison (not replay-to-replay only).** W-1 compares live execution against replayed execution on a normalized view of rule outcomes. If A9 causes only representation differences (list vs dict), normalize and compare semantics. If semantics diverge, that's a blocking defect.

3. **Engine-enforced condition enforcement (not author-skipped turn).** Turn 2 submits a real `AttackIntent` for the paralyzed Bandit Captain. If the engine blocks it (`actions_prohibited`), the test asserts the block. If the engine resolves it anyway, the builder documents `FINDING-WAYPOINT-01` (play_loop does not enforce `actions_prohibited` on actor conditions) — the condition _exists_ in state (proven by W-2), but enforcement is a gap for a future WO.

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Delivery

### Commit

Single commit. Message format: `feat: WO-WAYPOINT-001 — Waypoint maiden voyage, full table loop determinism proof`

All 5 gate tests (W-0 through W-4) must pass. Existing 256 gate tests (A-K) must still pass. Full test suite (5,997) must show zero regressions.

### Completion Report

File as `pm_inbox/DEBRIEF_WO-WAYPOINT-001.md`. 500 words max. Five mandatory sections:

0. **Scope Accuracy** — Did you deliver what was asked? Note any deviations.
1. **Discovery Log** — Anything you found that the dispatch didn't anticipate. Include FINDING-WAYPOINT-01 if applicable.
2. **Methodology Challenge** — Hardest part and how you solved it.
3. **Field Manual Entry** — One tradecraft tip for the next builder working in this area.
4. **Builder Radar** (mandatory, 3 labeled lines):
   - **Trap.** Hidden dependency or trap for the next WO.
   - **Drift.** Current drift risk.
   - **Near stop.** What got close to triggering a stop condition.

### Debrief Focus Questions

1. **A9 divergence:** Did you encounter the dict-vs-list condition representation mismatch between play_loop and replay_runner? How did you handle it in the normalized view?
2. **Condition enforcement:** Did the engine block the paralyzed Bandit Captain's attack (Branch A) or resolve it (Branch B)? What happened?

# DEBRIEF: ENGINE DISPATCH #8 — Class Feature Resolvers (6 WOs)

**From:** Builder (Sonnet 4.6)
**To:** PM (Aegis), via PO (Thunder)
**Date:** 2026-02-24
**Lifecycle:** NEW
**WOs:** WO-ENGINE-MANEUVER-GATE-001, WO-ENGINE-CLEAVE-WIRE-001, WO-ENGINE-BARBARIAN-RAGE-001, WO-ENGINE-SMITE-EVIL-001, WO-ENGINE-BARDIC-MUSIC-001, WO-ENGINE-WILD-SHAPE-001
**Result:** COMPLETED — 62 gate tests, 6 resolvers, zero regressions

---

## Pass 1 — Full Context Dump

### What Was Done

Six engine WOs delivered in a single session across two context windows. All implement class feature runtime presence for previously-unplayable classes (Barbarian, Paladin, Bard, Druid). Two WOs (Maneuver Gate, Cleave Wire) wire and gate-test previously-built maneuver infrastructure.

---

### WO-ENGINE-MANEUVER-GATE-001 (14 tests)

**Gate: ENGINE-MANEUVER — 14/14**

Retired stale pytest sentinel. Created `tests/test_engine_gate_maneuver.py` covering Bull Rush, Trip, Overrun, and Mounted Combat. Tests verified existing maneuver_resolver.py behavior without modifications to production code.

---

### WO-ENGINE-CLEAVE-WIRE-001 (10 tests)

**Gate: ENGINE-CLEAVE — 10/10**

Files modified:
- **`aidm/core/attack_resolver.py`** — Added cleave trigger: on kill with Cleave feat and available target, appends a follow-up attack roll event. Uses `cleave_used_this_turn` set on `active_combat` to enforce once-per-round limit (Great Cleave bypasses this).
- **`aidm/core/full_attack_resolver.py`** — Same cleave trigger wired identically for full-attack sequences.
- **`aidm/core/play_loop.py`** — Clears `cleave_used_this_turn` at the start of each new actor's turn.

Files created:
- **`tests/test_engine_gate_cleave.py`** — 10 tests.

---

### WO-ENGINE-BARBARIAN-RAGE-001 (10 tests)

**Gate: ENGINE-BARBARIAN-RAGE — 10/10**

Files modified:
- **`aidm/schemas/entity_fields.py`** — Added: `RAGE_ACTIVE`, `RAGE_ROUNDS_REMAINING`, `RAGE_USES_REMAINING`, `FATIGUED`.
- **`aidm/schemas/intents.py`** — Added `RageIntent(actor_id)`. Added to `Intent` union and `parse_intent()`.
- **`aidm/core/play_loop.py`** — Wired `RageIntent` → `activate_rage` or `intent_validation_failed`. Added `tick_rage` call at turn-end when `RAGE_ACTIVE`.

Files created:
- **`aidm/core/rage_resolver.py`** — `validate_rage`, `activate_rage`, `end_rage`, `tick_rage`. Uses `EF.CLASS_LEVELS["barbarian"]` for feature detection (not a non-existent `EF.CLASS_FEATURES`). Stat bonuses injected via `EF.TEMPORARY_MODIFIERS`. Fatigue applied on rage end.
- **`tests/test_engine_gate_barbarian_rage.py`** — 10 tests.

**Key finding:** `EF.CLASS_FEATURES` does not exist as an EF constant. The builder does not write class features onto entity dicts at chargen — only `EF.CLASS_LEVELS`. All class feature detection in this batch uses `CLASS_LEVELS` dict lookup (e.g., `class_levels.get("barbarian", 0) >= 1`). This is the correct pattern going forward.

---

### WO-ENGINE-SMITE-EVIL-001 (8 tests)

**Gate: ENGINE-SMITE-EVIL — 8/8**

Files modified:
- **`aidm/schemas/entity_fields.py`** — `SMITE_USES_REMAINING` already existed. No additions needed.
- **`aidm/schemas/intents.py`** — Added `SmiteEvilIntent(actor_id, target_id, weapon, target_is_evil)`. Added to `Intent` union and `parse_intent()`.
- **`aidm/core/play_loop.py`** — Wired `SmiteEvilIntent` → `resolve_smite_evil`.

Files created:
- **`aidm/core/smite_evil_resolver.py`** — `validate_smite`, `resolve_smite_evil`. CHA mod applied as attack bonus by bumping `AttackIntent.attack_bonus` via `dataclasses.replace`. Paladin level applied as damage bonus by bumping `weapon.damage_bonus` on a weapon copy. No TEMPORARY_MODIFIERS injection — bonuses baked directly into the attack call and do not persist.
- **`tests/test_engine_gate_smite_evil.py`** — 8 tests.

---

### WO-ENGINE-BARDIC-MUSIC-001 (10 tests)

**Gate: ENGINE-BARDIC-MUSIC — 10/10**

Files modified:
- **`aidm/schemas/entity_fields.py`** — Added: `BARDIC_MUSIC_USES_REMAINING`, `INSPIRE_COURAGE_ACTIVE`, `INSPIRE_COURAGE_BONUS`, `INSPIRE_COURAGE_ROUNDS_REMAINING`.
- **`aidm/schemas/intents.py`** — Added `BardicMusicIntent(actor_id, performance, ally_ids)`. Added `ally_ids: List[str]` field (was omitted in an earlier incomplete pass). Added to `Intent` union and `parse_intent()`.
- **`aidm/core/attack_resolver.py`** — Added `_inspire_attack_bonus` and `_inspire_dmg_bonus` from `INSPIRE_COURAGE_ACTIVE` / `INSPIRE_COURAGE_BONUS`. Applied as morale bonus to attack roll and base damage.
- **`aidm/core/save_resolver.py`** — Added `inspire_courage_bonus` to `get_save_bonus()` total when `INSPIRE_COURAGE_ACTIVE`.
- **`aidm/core/play_loop.py`** — Wired `BardicMusicIntent` → `resolve_bardic_music`. Added `tick_inspire_courage` at turn-end when any entity has `INSPIRE_COURAGE_ACTIVE`.

Files created:
- **`aidm/core/bardic_music_resolver.py`** — `validate_bardic_music`, `get_inspire_courage_bonus`, `resolve_bardic_music`, `tick_inspire_courage`. Morale non-stacking enforced via `max(existing, new_bonus)`. Fixed 8-round duration (FINDING-BARDIC-DURATION-001).
- **`tests/test_engine_gate_bardic_music.py`** — 10 tests.

---

### WO-ENGINE-WILD-SHAPE-001 (10 tests)

**Gate: ENGINE-WILD-SHAPE — 10/10**

Files modified:
- **`aidm/schemas/entity_fields.py`** — Added: `WILD_SHAPE_SAVED_STATS`, `WILD_SHAPE_HOURS_REMAINING`, `EQUIPMENT_MELDED`, `NATURAL_ATTACKS`. (`WILD_SHAPE_ACTIVE`, `WILD_SHAPE_FORM`, `WILD_SHAPE_USES_REMAINING` already existed.)
- **`aidm/schemas/intents.py`** — `WildShapeIntent` and `RevertFormIntent` already existed.
- **`aidm/core/attack_resolver.py`** — Added `EQUIPMENT_MELDED` check before weapon resolution: if True, emits `intent_validation_failed` with `reason: equipment_melded` and returns immediately.
- **`aidm/core/play_loop.py`** — Wired `WildShapeIntent` → `resolve_wild_shape` and `RevertFormIntent` → `resolve_revert_form`.

Files created:
- **`aidm/core/wild_shape_resolver.py`** — `validate_wild_shape`, `resolve_wild_shape`, `resolve_revert_form`. v1 form library: wolf, black_bear, riding_dog, eagle, constrictor_snake, crocodile. Saves original stats to `WILD_SHAPE_SAVED_STATS` (deep-copied via WorldState deepcopy). Restores on revert. HP recalculated from new Con modifier (simplified formula, FINDING-WILDSHAPE-HP-001).
- **`tests/test_engine_gate_wild_shape.py`** — 10 tests.

**Drift caught and fixed:** A subagent-written version of `wild_shape_resolver.py` used dict subscript access (`intent["actor_id"]`) instead of attribute access (`intent.actor_id`), and used wrong `Event` constructor kwargs (`id=`, `type=`, `data=` instead of `event_id=`, `event_type=`, `payload=`). Also invented a non-existent `EF.ORIGINAL_STATS` alias. All corrected before gate run.

---

### Open Findings (logged per WO spec)

| ID | Severity | WO | Description |
|----|----------|----|-------------|
| FINDING-WILDSHAPE-HP-001 | LOW | WILD-SHAPE | HP uses simplified Con-based formula; PHB proportional swap deferred |
| FINDING-WILDSHAPE-DURATION-001 | LOW | WILD-SHAPE | Duration not auto-decremented; DM triggers revert manually |
| FINDING-WILDSHAPE-NATURAL-ATTACKS-001 | MEDIUM | WILD-SHAPE | Natural attack resolution path absent in attack_resolver; wolf/bear/etc. attacks go nowhere at runtime |
| FINDING-BARDIC-DURATION-001 | LOW | BARDIC-MUSIC | 8-round flat duration; PHB action-economy maintenance not enforced |

---

### Test Results

| Gate | Tests | Result |
|------|-------|--------|
| ENGINE-MANEUVER | 14/14 | PASS |
| ENGINE-CLEAVE | 10/10 | PASS |
| ENGINE-BARBARIAN-RAGE | 10/10 | PASS |
| ENGINE-SMITE-EVIL | 8/8 | PASS |
| ENGINE-BARDIC-MUSIC | 10/10 | PASS |
| ENGINE-WILD-SHAPE | 10/10 | PASS |
| **Total** | **62/62** | **PASS** |

Full regression: **7,602 passed**, 49 pre-existing failures (UI/audio/camera infrastructure — `test_spark_integration_stress`, `test_speak_signal`, `test_ui_gate_camera_optics`, `test_ui_gate_lighting`, `test_ui_visual_qa_002_gate`, `test_weapon_plumbing` canary). Zero new regressions.

---

## Pass 2 — PM Summary

**ENGINE DISPATCH #8: COMPLETED.** Six WOs delivered. Barbarian, Paladin, Bard, and Druid now have runtime class feature resolvers. Maneuver and Cleave infrastructure gated. 62 gate tests, zero regressions. Four open findings logged (3 LOW, 1 MEDIUM). MEDIUM finding: natural attack resolution path is absent — Druid in Wild Shape cannot actually attack. This should be prioritized before playtesting Druid.

---

## Pass 3 — Retrospective

### EF.CLASS_FEATURES Does Not Exist

This tripped the first context window. The builder chargen system writes `EF.CLASS_LEVELS` (a dict like `{"barbarian": 5}`) but does not write class features onto entity dicts. Any WO that assumes `EF.CLASS_FEATURES` (or a class features list on the entity) will fail silently or KeyError. The correct pattern — confirmed working — is `entity.get(EF.CLASS_LEVELS, {}).get("class_name", 0)`. PM should audit any future WOs that reference class feature detection and ensure they use CLASS_LEVELS.

### Subagent Drift on Event Constructor

The Event dataclass uses `event_id=`, `event_type=`, `payload=` — not `id=`, `type=`, `data=`. A subagent writing a resolver without reading event_log.py will consistently get this wrong. The fix is trivial but the drift is easy to miss without running tests. Consider adding the Event constructor signature to the rehydration kernel or WO template boilerplate.

### TEMPORARY_MODIFIERS vs. Direct Injection

Two different patterns emerged for applying combat bonuses:
- **Rage:** uses `TEMPORARY_MODIFIERS` dict (persistent across turn, cleared on end_rage)
- **Smite:** uses `dataclasses.replace` on the intent/weapon (ephemeral, single-attack scope)
- **Inspire Courage:** uses dedicated EF fields (`INSPIRE_COURAGE_BONUS`) read by resolvers

All three are correct for their scope. This divergence is intentional but PM should be aware if a future WO tries to read Smite bonuses from TEMPORARY_MODIFIERS — they aren't there.

### Natural Attacks — Medium Finding

`FINDING-WILDSHAPE-NATURAL-ATTACKS-001` is the only MEDIUM in this batch. Wild Shape sets `EF.NATURAL_ATTACKS` on the entity (list of attack dicts), but attack_resolver.py has no code path for natural attacks. A Druid in wolf form cannot bite anyone. The WO spec said to log this and not fix it — correct call for scope discipline — but this makes the Druid effectively unplayable in combat even after this WO. Recommend PM prioritize a natural attack resolver before any Druid playtest.

### Context Window Pressure

Six WOs in one dispatch is heavy. The second context window opened mid-WO-6 with a compacted summary. The summary was accurate enough to resume, but three bugs (subscript access, Event kwargs, ORIGINAL_STATS alias) were introduced by a subagent call that didn't have the project's Event contract in context. Future heavy dispatches may benefit from a WO-count cap of 4, or explicit Event/EF contract headers in subagent prompts.

# WO Set — Engine Batch BE

**Lifecycle:** DISPATCH-READY
**Date:** 2026-03-03
**Seat:** Chisel
**Cycle:** BE = 1/5 (new cycle; BD audit ACCEPTED)
**Gate tests at dispatch:** 1,794

---

## Context

BD conditions audit (Anvil, DEBRIEF_AUDIT-WO-016-CONDITIONS.md) returned 7 genuine findings, 7 ghosts. All 7 findings dispatched in this batch.

**PM Design Decisions (made before dispatch):**

- **016-003 (Nauseated):** Option A — add `allows_move_only: bool = False` to `ConditionModifiers`; set nauseated factory `allows_move_only=True`; wire gate in play_loop that permits one move action but blocks standard/swift/full-round/full-attack.
- **016-004 (Confused):** Roll + partial enforcement. Wire `roll_confused_behavior()` (or equivalent d100) at turn start. Emit `confused_behavior_roll` event. Enforce: 11–20 act normally (proceed), 21–50 babble (skip turn), 71–100 attack nearest (position query in world_state). CONSUME_DEFERRED: 01–10 attack caster (no caster tracking in world_state), 51–70 flee (no movement subsystem). All CONSUME_DEFERRED cases → emit event + skip turn + document.
- **016-007 (Factory Names):** Add 8 conditions with factories in `conditions.py` to `_CONDITION_FACTORY_NAMES`: staggered, unconscious, pinned, turned, dazzled, cowering, fascinated, running. Defer 4 from `condition_combat_resolver.py` (blinded, deafened, entangled, confused) — refactoring lookup module import is a separate consolidation WO.

---

## WO1 — WO-ENGINE-CONDITION-IMMUNE-TO-WIRE-001

**Severity:** MEDIUM
**Source findings:** FINDING-AUDIT-CONDITIONS-016-001, FINDING-AUDIT-CONDITIONS-016-002

### Problem

`is_immune_to_poison()` and `apply_disease_exposure()` in `poison_disease_resolver.py` check class-based immunity (undead, monk, druid, paladin) but do NOT scan `EF.CONDITIONS` for a `ConditionInstance.immune_to` list containing "poison" or "disease". A petrified living creature has `immune_to=["poison", "disease"]` in its condition but can still be poisoned or contract disease.

### RAW Fidelity

PHB p.311 — Petrified: "The creature is also treated as an object." Petrified creatures are immune to poison and disease per the PETRIFIED factory (conditions.py, `immune_to=["poison", "disease"]`). The immunity is already encoded in the condition — it just isn't read.

### Parallel Paths

- `is_immune_to_poison()`: single entry point at `poison_disease_resolver.py:59`. No shadow path.
- `apply_disease_exposure()`: single entry point at `poison_disease_resolver.py:293`. No shadow path.
- Both functions have exclusive authority over their immunity check. No parity concern.

### Consumption Chain

- **Write:** `ConditionInstance.immune_to` list set at factory time (e.g., `create_petrified_condition()` sets `immune_to=["poison", "disease"]`)
- **Read:** `is_immune_to_poison()` / `apply_disease_exposure()` scan `entity.get(EF.CONDITIONS, {})`, call `ConditionInstance.from_dict()` on each value, check `.immune_to` for "poison" / "disease"
- **Effect:** Poison or disease application blocked; emit `poison_immune` / `disease_immune` event
- **Test:** Gate test with petrified entity — poison attempt → blocked; non-petrified living entity → proceeds

### Implementation Notes

- In `is_immune_to_poison()`: after existing class-based checks, add loop: `for cond_dict in entity.get(EF.CONDITIONS, {}).values(): ci = ConditionInstance.from_dict(cond_dict); if "poison" in ci.immune_to: return True`
- In `apply_disease_exposure()`: same pattern checking for "disease"
- Use `EF.CONDITIONS` constant, not bare string

### Proof Test

Gate file: `tests/test_engine_condition_immune_to_001_gate.py`
- CIT-001: Petrified entity — poison attempt → immune (True)
- CIT-002: Non-petrified living entity — poison attempt → NOT immune (False)
- CIT-003: Petrified entity — disease attempt → immune (True)
- CIT-004: Non-petrified entity — disease attempt → NOT immune (False)
- CIT-005: Entity with no conditions — poison attempt → NOT immune
- CIT-006: Undead entity — immune via class check (not immune_to scan) → still True
- CIT-007: Monk L11+ — immune via class check → still True
- CIT-008: Round-trip: immune_to survives ConditionInstance.to_dict() + from_dict()

### Coverage Map

Update `docs/ENGINE_COVERAGE_MAP.md`:
- Poison immunity row: add "immune_to ConditionInstance path" to implementation note
- Disease immunity row: same

### PM Acceptance Notes

- Show exact loop code for both `is_immune_to_poison()` and `apply_disease_exposure()` in Pass 1
- Confirm `EF.CONDITIONS` constant used (not bare string "conditions")
- Name both CIT-001 (poison) and CIT-003 (disease) canary tests explicitly in debrief
- Confirm non-petrified living entity is NOT blocked (CIT-002 and CIT-004)

---

## WO2 — WO-ENGINE-NAUSEATED-MOVE-ONLY-001

**Severity:** MEDIUM
**Source finding:** FINDING-AUDIT-CONDITIONS-016-003

### Problem

Nauseated condition sets `actions_prohibited=True` → `play_loop.py:1944` blocks ALL actions including movement. PHB p.311 specifies nauseated allows "a single move action per turn" — current implementation is more restrictive than RAW.

### RAW Fidelity

PHB p.311 — Nauseated: "A nauseated creature is unable to attack, cast spells, concentrate on spells, or do anything else requiring attention. The only action such a character can take is a single move action per turn."

### Design Decision (PM ruling)

Add `allows_move_only: bool = False` to `ConditionModifiers`. Set nauseated factory `allows_move_only=True`. Remove `actions_prohibited=True` from nauseated factory. Wire a new gate in play_loop action budget: if `condition_mods.allows_move_only`, permit `move` intent type only; block all others with `action_denied_nauseated` event.

### Parallel Paths

- `ConditionModifiers` is the single struct for condition effects — no shadow path
- `get_condition_modifiers()` is the single query function — all resolvers use it
- play_loop action budget is the single enforcement site for turn-level restrictions
- No parity concern

### Consumption Chain

- **Write:** `create_nauseated_condition()` in `schemas/conditions.py` sets `allows_move_only=True` (and does NOT set `actions_prohibited=True`)
- **Read:** play_loop action budget gate reads `condition_mods.allows_move_only`; permits move intent; blocks standard/swift/full-round/full-attack
- **Effect:** Nauseated entity can move; cannot attack, cast, or take standard actions
- **Test:** Gate test with nauseated entity — move intent → proceeds; attack intent → denied; cast intent → denied

### Implementation Notes

1. `aidm/schemas/conditions.py` — `ConditionModifiers` dataclass: add `allows_move_only: bool = False`
2. `aidm/schemas/conditions.py` — `create_nauseated_condition()`: remove `actions_prohibited=True`, add `allows_move_only=True`
3. `aidm/core/play_loop.py` — after the `actions_prohibited` gate (~line 1944), add: if `condition_mods.allows_move_only` and intent type is not `"move"`, emit `action_denied` with reason `"nauseated_move_only"`, return TurnResult("action_denied")
4. Intent type for move check: verify the string key used by the intent router for move-only actions (e.g., "move", "walk") — check `aidm/core/intent_classifier.py` or equivalent

### Proof Test

Gate file: `tests/test_engine_nauseated_move_only_001_gate.py`
- NMO-001: Nauseated entity + attack intent → action_denied "nauseated_move_only"
- NMO-002: Nauseated entity + cast intent → action_denied "nauseated_move_only"
- NMO-003: Nauseated entity + move intent → NOT denied (proceeds or reaches routing)
- NMO-004: Non-nauseated entity + attack intent → NOT denied by nauseated gate
- NMO-005: Nauseated entity + full_attack intent → action_denied
- NMO-006: Nauseated condition modifiers — actions_prohibited=False, allows_move_only=True
- NMO-007: ConditionModifiers default — allows_move_only=False (not set for other conditions)
- NMO-008: Nauseated entity with stacking condition (e.g., also stunned) — actions_prohibited wins; confirms gate order correct

### Coverage Map

Update `docs/ENGINE_COVERAGE_MAP.md`:
- Nauseated row: PARTIAL → IMPLEMENTED (allows_move_only enforcement wired)

### PM Acceptance Notes

- Show `ConditionModifiers` dataclass with `allows_move_only: bool = False` field added
- Show nauseated factory: `actions_prohibited=False`, `allows_move_only=True` (confirm both)
- Show play_loop gate for allows_move_only with the exact intent type check used
- Name canary: NMO-001 (attack denied) and NMO-003 (move proceeds) in debrief

---

## WO3 — WO-ENGINE-CONFUSED-BEHAVIOR-001

**Severity:** MEDIUM
**Source finding:** FINDING-AUDIT-CONDITIONS-016-004

### Problem

`roll_confused_behavior()` exists in `condition_combat_resolver.py` but is never called from play_loop turn dispatch. Confused entities act with full player control. PHB p.310 requires a d100 roll at turn start that determines behavior.

### RAW Fidelity

PHB p.310 — Confused: d100 each turn:
- 01–10: Attack the caster (melee or ranged)
- 11–20: Act normally
- 21–50: Do nothing but babble incoherently
- 51–70: Flee from caster at top speed
- 71–100: Attack nearest creature (not necessarily an enemy)

### Design Decision (PM ruling)

Roll d100 at turn start. Emit `confused_behavior_roll` event with bracket + behavior label. Enforce:
- **11–20 (act normally):** proceed, no interference
- **21–50 (babble):** block turn, emit `confused_babble` event, return TurnResult("confused_babble")
- **71–100 (attack nearest):** query world_state for nearest entity by Euclidean position distance; if found, substitute attack intent toward that entity; if position data unavailable, emit `confused_attack_nearest_blocked` and skip turn
- **01–10 (attack caster):** CONSUME_DEFERRED — no caster tracking in world_state; emit `confused_attack_caster_deferred` event; skip turn
- **51–70 (flee):** CONSUME_DEFERRED — no movement subsystem; emit `confused_flee_deferred` event; skip turn

All CONSUME_DEFERRED branches must emit a named event (not silent skip) so the LLM DM layer can narrate behavior in Phase 2.

### Parallel Paths

- `roll_confused_behavior()` in `condition_combat_resolver.py`: use this function (don't re-implement the roll)
- play_loop turn dispatch is the single enforcement site — insert before intent routing
- No shadow path; no parity concern

### Consumption Chain

- **Write:** `create_confused_condition()` sets confused in `EF.CONDITIONS`
- **Read:** play_loop checks for confused condition at turn start; calls `roll_confused_behavior()` (or inline equivalent with seeded RNG); routes based on bracket
- **Effect:** Babble/flee/caster → action blocked or deferred; act normally → player intent proceeds; attack nearest → routed to nearest entity
- **Test:** Gate test with seeded RNG to produce each bracket; verify correct TurnResult and events

### Implementation Notes

1. At turn start in play_loop (after conditions check, before intent routing): detect "confused" in `entity.get(EF.CONDITIONS, {})`
2. Use seeded RNG (`rng.stream("combat")`) to roll d100
3. Emit `confused_behavior_roll` event: `{"bracket": "21-50", "behavior": "babble", "roll": <value>}`
4. Route based on bracket as defined above
5. For attack_nearest (71–100): iterate `world_state.entities`, compute `sqrt((ax-bx)^2 + (ay-by)^2)` using `EF.POSITION`, exclude self, pick minimum distance non-self entity
6. `EF.POSITION` returns `{"x": int, "y": int}` (PTN fix, Batch BA)
7. Emit CONSUME_DEFERRED comment at 01–10 and 51–70 branches — cannot defer silently

### Proof Test

Gate file: `tests/test_engine_confused_behavior_001_gate.py`
- CFB-001: Confused entity + seeded roll 15 (act normally) → intent proceeds
- CFB-002: Confused entity + seeded roll 35 (babble) → TurnResult("confused_babble")
- CFB-003: Confused entity + seeded roll 85 (attack nearest) → attack intent toward nearest entity emitted
- CFB-004: Confused entity + seeded roll 5 (attack caster DEFERRED) → skip turn + event emitted
- CFB-005: Confused entity + seeded roll 60 (flee DEFERRED) → skip turn + event emitted
- CFB-006: Non-confused entity → no confused gate fires; intent proceeds normally
- CFB-007: Attack nearest — 2-entity world_state; confused entity attacks the other entity (not self)
- CFB-008: confused_behavior_roll event carries roll value + bracket + behavior label

### Coverage Map

Update `docs/ENGINE_COVERAGE_MAP.md`:
- Confused row: NOT STARTED → PARTIAL (d100 roll + 3/5 brackets enforced; 2/5 CONSUME_DEFERRED)

### PM Acceptance Notes

- Show the d100 roll call site (line in play_loop) and that it uses `rng.stream("combat")`
- Show the CONSUME_DEFERRED comment lines for 01–10 and 51–70 branches (exact file:line)
- Name: CFB-002 (babble blocks) and CFB-003 (attack nearest routes) as canary pair in debrief
- Confirm `confused_behavior_roll` event is emitted for ALL brackets (including deferred ones)

---

## WO4 — WO-ENGINE-CONDITION-SKILL-COVERAGE-001

**Severity:** LOW
**Source findings:** FINDING-AUDIT-CONDITIONS-016-005, FINDING-AUDIT-CONDITIONS-016-006, FINDING-AUDIT-CONDITIONS-016-007 (partial)

### Problem (three-part)

**Part A (016-005):** `skill_resolver.py` wires dazzled -1 to Spot (lines 273–275) but not to Search. PHB p.309 says dazzled applies to both.

**Part B (016-006):** `check_deafened_spell_failure()` exists in `condition_combat_resolver.py` but is never called from the spell casting path. Coverage map row 387 incorrectly states "deafened condition prevents verbal spells" — PHB p.310 says 20% spell failure (d100 roll), not hard block.

**Part C (016-007, partial):** `_CONDITION_FACTORY_NAMES` in `core/conditions.py` registers 17/29 conditions. 8 conditions have factories in `conditions.py` but are not registered: staggered, unconscious, pinned, turned, dazzled, cowering, fascinated, running. (4 in `condition_combat_resolver.py` deferred — separate consolidation WO.)

### RAW Fidelity

- PHB p.309 — Dazzled: "–1 penalty on attack rolls and Spot checks" → also –1 to Search (PHB p.309 lists both under dazzled description: "The creature is unable to see well because of overstimulation of the eyes. A dazzled creature suffers a –1 penalty on attack rolls, Search checks, and Spot checks.")
- PHB p.310 — Deafened: "A deafened character has a 20% chance of spell failure when casting spells with verbal components."
- PHB general: conditions not in `_CONDITION_FACTORY_NAMES` silently get zero modifiers when stored as `{}` — structural gap, not live bug.

### Parallel Paths

- `skill_resolver.py`: single skill resolution path; no shadow path
- Spell verbal-component block in `play_loop.py`: single entry for verbal check (around line 728–752)
- `_CONDITION_FACTORY_NAMES`: single dict in `core/conditions.py`; no shadow path

### Consumption Chain

**Part A:**
- **Write:** dazzled condition stored in EF.CONDITIONS
- **Read:** `skill_resolver.py` — add `skill_id == "search"` check alongside existing `skill_id == "spot"` dazzled check
- **Effect:** Search checks against dazzled entity incur -1 penalty
- **Test:** dazzled entity + search check → -1 applied

**Part B:**
- **Write:** deafened condition stored in EF.CONDITIONS
- **Read:** `play_loop.py` verbal-component block calls `check_deafened_spell_failure()` (or equivalent); d100 roll; block if fails (≤ 20)
- **Effect:** Deafened caster has 20% chance to lose verbal spell
- **Test:** deafened entity + verbal spell + seeded fail roll → spell blocked; seeded pass roll → proceeds

**Part C:**
- **Write:** `_CONDITION_FACTORY_NAMES` dict gains 8 new entries
- **Read:** `_get_modifiers_for_condition_type()` finds factory for these 8 conditions when stored as `{}`
- **Effect:** Modifiers correctly resolved for legacy empty-dict format
- **Test:** conditions stored as `{}` with these 8 types → correct modifiers (or at minimum no crash)

### Implementation Notes

1. `skill_resolver.py:273-275`: add `elif skill_id == "search" and "dazzled" in conditions: bonus -= 1` (mirror the Spot block)
2. `play_loop.py` verbal-component block (~line 728–752): after silenced/gagged hard-block, add: if deafened condition present → roll d100 (`rng.stream("combat")`); if roll ≤ 20 → emit `deafened_spell_failure` event, block spell
3. `docs/ENGINE_COVERAGE_MAP.md` row 387: update text to "deafened: 20% spell failure for verbal-component spells (PHB p.310)" — no longer "prevents verbal"
4. `core/conditions.py _CONDITION_FACTORY_NAMES`: add 8 entries. Factory lookup is by lowercase condition name: `"staggered": "create_staggered_condition"`, `"unconscious": "create_unconscious_condition"`, `"pinned": "create_pinned_condition"`, `"turned": "create_turned_condition"`, `"dazzled": "create_dazzled_condition"`, `"cowering": "create_cowering_condition"`, `"fascinated": "create_fascinated_condition"`, `"running": "create_running_condition"`. Verify exact factory function name spellings in `schemas/conditions.py` before adding.

### Proof Test

Gate file: `tests/test_engine_condition_skill_coverage_001_gate.py`
- CSC-001: Dazzled entity + search check → -1 penalty applied
- CSC-002: Dazzled entity + spot check → -1 penalty still applied (regression check)
- CSC-003: Non-dazzled entity + search check → no penalty
- CSC-004: Deafened entity + verbal spell + seeded d100 ≤ 20 → spell blocked (deafened_spell_failure event)
- CSC-005: Deafened entity + verbal spell + seeded d100 > 20 → spell proceeds
- CSC-006: Non-deafened entity + verbal spell → no failure roll fires
- CSC-007: Deafened entity + non-verbal spell (somatic only) → no failure roll fires
- CSC-008: Coverage map row 387 update verified (check for "20% spell failure" string OR confirm correct text)

### Coverage Map

Update `docs/ENGINE_COVERAGE_MAP.md`:
- Dazzled row: add Search to skill penalty implementation
- Deafened row: update row 387 wording (20% failure, not hard block); status: PARTIAL → IMPLEMENTED
- Note: `_CONDITION_FACTORY_NAMES` structural completeness: 17/29 → 25/29 (8 added, 4 condition_combat_resolver.py deferred)

### PM Acceptance Notes

- Show before/after of skill_resolver.py dazzled block (both spot and search present)
- Show the exact coverage map row 387 text before and after
- Name canary pair: CSC-001 (dazzled search) + CSC-004 (deafened failure) in debrief
- List all 8 factory name entries added to `_CONDITION_FACTORY_NAMES` explicitly in Pass 1
- Confirm deafened check is NOT a hard block (not returning action_denied before the d100 roll)

---

## ML Preflight Checklist (builder self-check)

- [ ] ML-001: Test isolation — no shared mutable state between gate tests
- [ ] ML-002: Ghost check — verified each gap exists before writing code
- [ ] ML-003: Kernel check — no `KNOWN_TECH_DEBT.md` items touched
- [ ] ML-004: EF constants — no bare string literals for entity fields
- [ ] ML-005: D&D 3.5e only — no 5e mechanics, no advantage/disadvantage
- [ ] ML-006: Resolvers return events only — no WorldState mutation in resolvers
- [ ] ML-007: PM Acceptance Notes reviewed — builder confirmed each item before debrief
- [ ] ML-008: No research artifact required (audit-derived, no OSS source dependency)

## Verdict Review Class

SELF-REVIEW (4 WOs: MEDIUM/MEDIUM/MEDIUM/LOW; no resolver parity shadow path, no data ingestion, no cross-cutting architecture change; ConditionModifiers schema addition is bounded).

---

*Batch BE — 4 WOs — conditions immune_to, nauseated move-only, confused behavior, skill/deafened/factory coverage. Chisel seat.*

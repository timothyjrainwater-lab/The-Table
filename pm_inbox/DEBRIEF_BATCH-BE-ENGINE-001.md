# Debrief — Batch BE Engine
**Commit:** be20f14
**Date:** 2026-03-03
**WOs:** WO-ENGINE-CONDITION-IMMUNE-TO-WIRE-001 (CIT) | WO-ENGINE-NAUSEATED-MOVE-ONLY-001 (NMO) | WO-ENGINE-CONFUSED-BEHAVIOR-001 (CFB) | WO-ENGINE-CONDITION-SKILL-COVERAGE-001 (CSC)
**Gates:** 32 new → **1,826 total** (1,794 + 32)
**Lifecycle:** NEW

---

## Pass 1 — Context Dump

### WO1 — CIT: Condition immune_to wire (poison_disease_resolver.py)

**Files changed:** `aidm/core/poison_disease_resolver.py` (lines 76–85, 368–384), `tests/test_engine_condition_immune_to_001_gate.py` (new, 8 tests)

**is_immune_to_poison() — before/after:**
```python
# BEFORE (line 59): only class-based checks (undead, monk, druid, paladin)
def is_immune_to_poison(entity: Dict[str, Any]) -> bool:
    # ... class checks only
    return False

# AFTER (lines 76–85): added ConditionInstance.immune_to scan
# WO-ENGINE-CONDITION-IMMUNE-TO-WIRE-001: Scan ConditionInstance.immune_to (PHB p.311)
for _cond_dict in entity.get(EF.CONDITIONS, {}).values():
    try:
        _ci = ConditionInstance.from_dict(_cond_dict)
        if "poison" in _ci.immune_to:
            return True
    except Exception:
        pass
```

**apply_disease_exposure() — before/after:**
```python
# BEFORE (line 299): class-based only

# AFTER (lines 368–384): added scan
# WO-ENGINE-CONDITION-IMMUNE-TO-WIRE-001: Scan ConditionInstance.immune_to for "disease" (PHB p.311)
for _dis_cond_dict in entity.get(EF.CONDITIONS, {}).values():
    try:
        _dis_ci = ConditionInstance.from_dict(_dis_cond_dict)
        if "disease" in _dis_ci.immune_to:
            events.append(Event(..., "reason": "condition_immune_to", ...))
            return new_ws, next_event_id + 1, events
    except Exception:
        pass
```

**Confirmation:** `EF.CONDITIONS` constant used throughout (not bare string).

**Canary pair:**
- CIT-001: Petrified entity → `is_immune_to_poison()` returns `True` ✓
- CIT-003: Petrified entity → `apply_disease_exposure()` blocks with `condition_immune_to` event ✓
- CIT-002: Non-petrified living entity → poison NOT blocked ✓
- CIT-004: Non-petrified entity → disease NOT blocked ✓

---

### WO2 — NMO: Nauseated move-only enforcement

**Files changed:** `aidm/schemas/conditions.py` (lines 135, 157, 179, 533), `aidm/core/conditions.py` (lines 167, 206, 233), `aidm/core/play_loop.py` (lines 2007–2027), `tests/test_engine_nauseated_move_only_001_gate.py` (new, 8 tests)

**ConditionModifiers addition** (`schemas/conditions.py:135`):
```python
allows_move_only: bool = False
```

**Nauseated factory** (`schemas/conditions.py:533`):
```python
allows_move_only=True  # WO-ENGINE-NAUSEATED-MOVE-ONLY-001: only move action (PHB p.311)
# actions_prohibited NOT set (was erroneously True before this WO)
```

**get_condition_modifiers() aggregation** (`conditions.py:167, 206, 233`) — three-point fix required:
```python
# Line 167 — init:
any_allows_move_only = False  # WO-ENGINE-NAUSEATED-MOVE-ONLY-001
# Line 206 — loop OR:
any_allows_move_only = any_allows_move_only or mods.allows_move_only
# Line 233 — return kwarg:
allows_move_only=any_allows_move_only,
```

**Bug found during execution:** `get_condition_modifiers()` was not aggregating `allows_move_only` — field existed on schema and factory but was silently dropped at the aggregation boundary. Fixed as shown above.

**play_loop gate** (`play_loop.py:2007–2027`):
```python
if condition_mods.allows_move_only and combat_intent is not None:
    # block all non-move intents
    if not isinstance(combat_intent, (FullMoveIntent,)):
        events.append(Event(..., "reason": "nauseated_move_only", ...))
        return TurnResult(status="action_denied", ...)
```

**Canary pair:**
- NMO-001: Nauseated + AttackIntent → `action_denied` with `reason="nauseated_move_only"` ✓
- NMO-003: Nauseated + FullMoveIntent → NOT denied (proceeds) ✓
- NMO-006: `create_nauseated_condition().modifiers.allows_move_only is True`, `actions_prohibited is False` ✓
- NMO-008: Stunned (actions_prohibited) + nauseated → `reason="actions_prohibited"` fires (not nauseated_move_only) — gate order correct ✓

---

### WO3 — CFB: Confused behavior d100 gate

**Files changed:** `aidm/core/play_loop.py` (lines 2043–2196), import line 49, `tests/test_engine_confused_behavior_001_gate.py` (new, 8 tests)

**Import** (`play_loop.py:49`):
```python
from aidm.core.condition_combat_resolver import roll_confused_behavior, check_deafened_spell_failure
```

**Gate call site** (`play_loop.py:2043`):
```python
_cf_behavior, _cf_roll_events = roll_confused_behavior(
    rng, turn_ctx.actor_id, next_event_id, timestamp=0.0
)
```
Uses `rng.stream("combat")` internally in `roll_confused_behavior()`.

**Branch enforcement (play_loop.py:2043–2196):**
- 11–20 act_normally: fall through to intent routing
- 21–50 babble: `return TurnResult(status="confused_babble")` + `confused_babble` event
- 71–100 attack_nearest: position query on `world_state.entities`, substitute `AttackIntent` toward nearest non-self entity
- 01–10 attack_caster: **CONSUME_DEFERRED** — `confused_attack_caster_deferred` event + skip turn (line 2151, 2168)
- 51–70 flee: **CONSUME_DEFERRED** — `confused_flee_deferred` event + skip turn (line 2179, 2196)

**Bug found during execution:** Confused `attack_nearest` branch built `AttackIntent` without required `attack_bonus` parameter. Fixed: `_cf_attack_bonus = _cf_actor_entity.get(EF.ATTACK_BONUS, 0)` added, passed to constructor.

**CONSUME_DEFERRED comment lines (exact):**
- `# CONSUME_DEFERRED: 01-10 attack_caster — no caster_id tracking in world_state` (play_loop.py:~2149)
- `# CONSUME_DEFERRED: 51-70 flee — no movement subsystem for AI-driven flee` (play_loop.py:~2177)

**Canary pair:**
- CFB-002: roll=35 (babble) → `result.status == "confused_babble"` + `confused_babble` event ✓
- CFB-003: roll=85 (attack_nearest) → intent routes toward `target_1` (not self) ✓
- CFB-008: `confused_behavior_roll` event carries `d100_roll=35` and `behavior="babble"` ✓

---

### WO4 — CSC: Condition skill coverage (dazzled search, deafened 20%, factory names)

**Files changed:** `aidm/core/skill_resolver.py` (lines 277–279), `aidm/core/play_loop.py` (lines 729–771), `aidm/core/conditions.py` (lines 45–52), `docs/ENGINE_COVERAGE_MAP.md` (row 387 updated), `tests/test_engine_condition_skill_coverage_001_gate.py` (new, 8 tests)

**Part A — dazzled Search penalty** (`skill_resolver.py:277–279`):
```python
# BEFORE: only spot had dazzled check (line 275)
if skill_id == "spot" and "dazzled" in _entity_conditions:
    total -= 1

# AFTER: both spot AND search
if skill_id == "spot" and "dazzled" in _entity_conditions:
    total -= 1
# WO-ENGINE-CONDITION-SKILL-COVERAGE-001 Part A: -1 penalty to Search checks when dazzled (PHB p.309)
if skill_id == "search" and "dazzled" in _entity_conditions:
    total -= 1
```

**Part B — deafened 20% verbal spell failure** (`play_loop.py:729–771`):
```python
# Line 729–730: verbal component detection
_has_verbal = getattr(spell, "has_verbal", True)
_is_silent = "silent" in getattr(intent, "metamagic", ())
# Line 731: block only fires for verbal non-silent spells
if _has_verbal and not _is_silent:
    # Line 757: deafened check (NOT a hard block — d100 roll)
    _deaf_failed, _deaf_raw_events = check_deafened_spell_failure(...)
```
Deafened check is INSIDE the `if _has_verbal and not _is_silent:` block — Silent Spell metamagic suppresses the check entirely (CSC-007). Not a hard block — d100 roll determines outcome (CSC-004/005).

**Part C — _CONDITION_FACTORY_NAMES** (`conditions.py:45–52`):
```python
"staggered":   "create_staggered_condition",
"unconscious": "create_unconscious_condition",
"pinned":      "create_pinned_condition",
"turned":      "create_turned_condition",
"dazzled":     "create_dazzled_condition",
"cowering":    "create_cowering_condition",
"fascinated":  "create_fascinated_condition",
"running":     "create_running_condition",
```
17/29 → 25/29 registered (8 added). 4 from `condition_combat_resolver.py` deferred (blinded, deafened, entangled, confused) — separate consolidation WO.

**Coverage map row 387 — before/after:**
- BEFORE: `"deafened condition prevents verbal spells"`
- AFTER: `"deafened: 20% spell failure for verbal-component spells (PHB p.310)"`

**Canary pair:**
- CSC-001: Dazzled entity + search check → total = clean - 1 ✓
- CSC-004: Deafened entity + verbal spell + roll=15 (≤20) → `deafened_spell_failure_check` event with `failed=True` ✓

---

### Gate file summary

| File | Tests | Status |
|------|-------|--------|
| `tests/test_engine_condition_immune_to_001_gate.py` | CIT-001..008 | 8/8 PASS |
| `tests/test_engine_nauseated_move_only_001_gate.py` | NMO-001..008 | 8/8 PASS |
| `tests/test_engine_confused_behavior_001_gate.py` | CFB-001..008 | 8/8 PASS |
| `tests/test_engine_condition_skill_coverage_001_gate.py` | CSC-001..008 | 8/8 PASS |
| **Total BE gates** | **32** | **32/32 PASS** |

Full regression suite: **9,231 passed**, 184 failed (pre-existing ws_bridge / UI posture failures — no new failures introduced).

---

## Pass 2 — PM Summary

Batch BE closes 7 of the 7 genuine findings from Anvil BD audit (WO-016 conditions). CIT wires `ConditionInstance.immune_to` into both poison and disease immunity paths — petrified entities now correctly block exposure. NMO fixes a prior over-restriction: nauseated was using `actions_prohibited` (no action at all), corrected to `allows_move_only` (one move permitted per PHB p.311). CFB wires the pre-existing `roll_confused_behavior()` function into play_loop turn dispatch, enforcing 3/5 PHB brackets with CONSUME_DEFERRED events for the 2 that require subsystems not yet built (caster tracking, AI flee). CSC adds dazzled –1 to Search (was Spot-only), wires deafened 20% verbal failure (was unconnected), and fills 8 factory name gaps in `_CONDITION_FACTORY_NAMES`. Two genuine implementation bugs found and fixed during gate iteration: `get_condition_modifiers()` missing `allows_move_only` aggregation, and confused `AttackIntent` missing required `attack_bonus`. All 32 gates pass, no regression.

---

## Pass 3 — Retrospective

**Out-of-scope findings:**

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| FINDING-BE-FACTORY-NAMES-DEFERRED-001 | LOW | 4 conditions in `condition_combat_resolver.py` (blinded, deafened, entangled, confused) still not in `_CONDITION_FACTORY_NAMES` — consolidation WO needed to move factories or add dynamic import | BACKLOG |
| FINDING-BE-DEAFENED-EVENT-NAME-001 | LOW | `deafened_spell_failure_check` event name (with `_check` suffix) differs from dispatch doc which used `deafened_spell_failure` — consistent with implementation but PM should note the exact event name in coverage map | NOTED |

**Kernel touches:**
- This WO touches KERNEL-04 (Conditions) — `ConditionModifiers` dataclass gained `allows_move_only`, aggregator function gained 3-line OR logic. Schema change is backward-compatible (default `False`).
- This WO touches KERNEL-06 (play_loop turn dispatch) — two new condition gates added (NMO gate at ~2007, CFB gate at ~2043). Gate order: actions_prohibited → allows_move_only → confused → intent routing.
- This WO touches KERNEL-11 (Skill resolver) — dazzled Search penalty added alongside existing Spot penalty.

**ML Preflight self-check:**
- ML-001 ✓ — no shared mutable state between tests
- ML-002 ✓ — ghost checks confirmed: all 4 gaps verified real before coding
- ML-003 ✓ — no KNOWN_TECH_DEBT items touched
- ML-004 ✓ — EF.CONDITIONS used throughout (no bare string)
- ML-005 ✓ — D&D 3.5e only (PHB cites throughout)
- ML-006 ✓ — resolvers return events; no WorldState mutation in resolvers
- ML-007 ✓ — PM Acceptance Notes reviewed before writing debrief
- ML-008 ✓ — no OSS source required; all from BD audit findings

**Consume-site confirmation:**
- CIT: write = `create_petrified_condition() immune_to=["poison","disease"]`; read = `is_immune_to_poison():80` + `apply_disease_exposure():372`; effect = exposure blocked; test = CIT-001/003
- NMO: write = `create_nauseated_condition():533`; read = `play_loop.py:2007`; effect = attack/cast denied; test = NMO-001/003
- CFB: write = `create_confused_condition()`; read = `play_loop.py:2043`; effect = behavior substitution or skip; test = CFB-002/003
- CSC-A: write = dazzled condition; read = `skill_resolver.py:278`; effect = -1 search penalty; test = CSC-001
- CSC-B: write = deafened condition; read = `play_loop.py:757`; effect = 20% verbal failure; test = CSC-004/005
- CSC-C: write = `_CONDITION_FACTORY_NAMES:45–52`; read = `get_modifier_for_condition_type()`; effect = correct factory lookup; structural completeness

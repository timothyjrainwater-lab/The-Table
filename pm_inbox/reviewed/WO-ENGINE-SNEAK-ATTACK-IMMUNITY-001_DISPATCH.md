# WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001 — Auto-Apply CRIT_IMMUNE from Creature Type

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** MEDIUM (FINDING-COVERAGE-MAP-001 rank #19 — undead/constructs/etc. take sneak attack damage unless manually flagged)
**WO type:** BUG (opt-in immunity; should be automatic from creature type)
**Gate:** ENGINE-SNEAK-ATTACK-IMMUNITY (10 tests)

---

## 1. Target Lock

**What works:** `aidm/core/sneak_attack.py` has an `is_target_immune()` function (lines 93–122) that checks `EF.CRIT_IMMUNE`. `EF.CREATURE_TYPE` already exists in `entity_fields.py` (line 234). The sneak attack system is fully implemented — immunity enforcement just requires a creature_type → CRIT_IMMUNE mapping.

**What's missing:** Any entity without `EF.CRIT_IMMUNE = True` explicitly set takes sneak attack damage regardless of its creature type. An undead entity loaded from the bestiary without the manual flag takes rogue sneak attack dice. The fix is: in `is_target_immune()`, if `EF.CRIT_IMMUNE` is not set but `EF.CREATURE_TYPE` matches the immune list, auto-apply immunity at resolution time. Also wire at chargen/bestiary compile time so it's set on entity load, not just at check time.

**PHB references:**
- PHB p.50 (Rogue): "The rogue cannot sneak attack while striking a creature that has concealment or striking the limbs of a creature whose vitals are beyond reach. A rogue also cannot use sneak attack against a creature immune to critical hits."
- PHB creature type rules: Undead, Constructs, Plants, Oozes, Elemental, Incorporeal are immune to critical hits and precision damage.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Fix at check time or entity load time? | Both. Runtime guard in `sneak_attack.py` as belt-and-suspenders. Primary fix at entity load — `builder.py` and bestiary compile set `EF.CRIT_IMMUNE = True` automatically when `EF.CREATURE_TYPE` matches the immune list. |
| 2 | Which creature types are immune? | PHB-compliant set: `{"undead", "construct", "plant", "ooze", "elemental"}`. Incorporeal is a subtype, not a type — handle separately if needed; out of scope here. |
| 3 | Does this affect critical hits too? | Yes — `EF.CRIT_IMMUNE` is already checked by `attack_resolver.py` for crits (WO-ENGINE-COUP-DE-GRACE-001 established the flag). Setting it automatically benefits both sneak attack and crit immunity simultaneously. No separate field needed. |
| 4 | Does this apply to PCs? | Only if a PC has a creature_type set (e.g., a dhampir with `creature_type="undead"`). Default PC creature_type is `"humanoid"` — not in the immune list. No unintended side effects. |
| 5 | What if CREATURE_TYPE is already set but CRIT_IMMUNE is False? | Auto-set CRIT_IMMUNE = True at entity load if creature_type is in immune set. The runtime guard in sneak_attack.py is a fallback for entities loaded before this WO. |

---

## 3. Contract Spec

### Immune types constant in `aidm/core/sneak_attack.py`

Add near the top of the file:

```python
# WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001: PHB creature types immune to precision damage
SNEAK_ATTACK_IMMUNE_CREATURE_TYPES = frozenset({
    "undead", "construct", "plant", "ooze", "elemental",
})
```

### Modification: `is_target_immune()` in `aidm/core/sneak_attack.py`

In the function body, before the final `return False`, add:

```python
# WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001: Auto-check creature type as fallback
creature_type = target.get(EF.CREATURE_TYPE, "").lower()
if creature_type in SNEAK_ATTACK_IMMUNE_CREATURE_TYPES:
    return True
```

This covers any entity that has `CREATURE_TYPE` set but `CRIT_IMMUNE` not yet propagated.

### Modification: `aidm/chargen/builder.py`

After `EF.CREATURE_TYPE` is set on an entity during build, add auto-flag:

```python
# WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001: Auto-apply CRIT_IMMUNE from creature type
from aidm.core.sneak_attack import SNEAK_ATTACK_IMMUNE_CREATURE_TYPES
_creature_type = entity.get(EF.CREATURE_TYPE, "").lower()
if _creature_type in SNEAK_ATTACK_IMMUNE_CREATURE_TYPES:
    entity[EF.CRIT_IMMUNE] = True
```

### Modification: Bestiary compile stage

If a bestiary compile stage (`aidm/core/compile_stages/bestiary.py` or equivalent) sets `EF.CREATURE_TYPE` on entities, apply the same auto-flag there. Builder must locate the exact file and insertion point — follow the same pattern as the chargen addition above.

---

## 4. Implementation Plan

1. `aidm/core/sneak_attack.py` — add `SNEAK_ATTACK_IMMUNE_CREATURE_TYPES` frozenset + runtime guard in `is_target_immune()` (~6 lines total)
2. `aidm/chargen/builder.py` — auto-flag after CREATURE_TYPE assignment (~4 lines)
3. Bestiary compile stage — same auto-flag (~4 lines; builder must locate exact file)
4. Tests

### Tests (`tests/test_engine_sneak_attack_immunity_gate.py`)
Gate: ENGINE-SNEAK-ATTACK-IMMUNITY — 10 tests

| Test | Description |
|------|-------------|
| SAI-01 | Undead target (CREATURE_TYPE="undead", no CRIT_IMMUNE flag): `is_target_immune()` returns True |
| SAI-02 | Construct target: immune |
| SAI-03 | Plant target: immune |
| SAI-04 | Ooze target: immune |
| SAI-05 | Elemental target: immune |
| SAI-06 | Humanoid target (CREATURE_TYPE="humanoid"): NOT immune, sneak attack applies |
| SAI-07 | Target with CREATURE_TYPE="" (unset): NOT immune |
| SAI-08 | Target with CRIT_IMMUNE=True but no CREATURE_TYPE: still immune (existing behavior preserved) |
| SAI-09 | Chargen: entity built with CREATURE_TYPE="undead" has CRIT_IMMUNE=True auto-set |
| SAI-10 | Regression: existing ENGINE-SNEAK-ATTACK gate tests unchanged |

---

## Integration Seams

**Files touched:**
- `aidm/core/sneak_attack.py` — frozenset constant + 3-line guard in `is_target_immune()`
- `aidm/chargen/builder.py` — ~4 lines after CREATURE_TYPE assignment
- Bestiary compile stage — ~4 lines (builder locates exact file)

**Files NOT touched:**
- `aidm/schemas/entity_fields.py` — CREATURE_TYPE and CRIT_IMMUNE already exist
- `aidm/core/attack_resolver.py` — CRIT_IMMUNE already checked there; no change needed

**Event constructor signature (mandatory):**
```python
Event(event_id=<int>, event_type=<str>, payload=<dict>, timestamp=<float>, citations=[])
```

**EF field access pattern:**
```python
target.get(EF.CREATURE_TYPE, "").lower()
target.get(EF.CRIT_IMMUNE, False)
```

---

## Assumptions to Validate

1. `EF.CREATURE_TYPE` is at entity_fields.py line 234 — confirmed from codebase inspection
2. `EF.CRIT_IMMUNE` exists and is checked in both `sneak_attack.py` and `attack_resolver.py` — confirmed
3. `is_target_immune()` is the single check point for sneak attack immunity — confirm no parallel path
4. Builder locates bestiary compile stage file — search for where CREATURE_TYPE is assigned to entities from bestiary data; apply same auto-flag pattern

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/ -k "sneak" -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_sneak_attack_immunity_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/core/sneak_attack.py` — immune type set + runtime guard
- [ ] `aidm/chargen/builder.py` — auto-flag after CREATURE_TYPE
- [ ] Bestiary compile stage — auto-flag (file to be located)
- [ ] `tests/test_engine_sneak_attack_immunity_gate.py` — 10/10

**Gate:** ENGINE-SNEAK-ATTACK-IMMUNITY 10/10
**Regression bar:** Existing sneak attack gate tests unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001.md` on completion.

Three-pass format. Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

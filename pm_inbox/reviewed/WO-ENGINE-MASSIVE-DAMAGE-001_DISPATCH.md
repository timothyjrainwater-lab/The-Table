# WO-ENGINE-MASSIVE-DAMAGE-001 — Massive Damage Rule: DC 15 Fort Save or Die on 50+ HP Hit

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** MEDIUM (FINDING-COVERAGE-MAP-001 rank #15 — silent wrong outcome on any 50+ HP single hit)
**WO type:** BUG (missing enforcement)
**Gate:** ENGINE-MASSIVE-DAMAGE (10 tests)

---

## 1. Target Lock

**What works:** `attack_resolver.py` correctly applies damage, emits `hp_changed` (line 638), then calls `resolve_hp_transition()` for dying/death checks. The damage pipeline is clean and the insertion point is exact.

**What's missing:** PHB p.145 — "Massive Damage: If you ever sustain a single attack that deals an amount of damage equal to half your total hit points or more (minimum 50 points of damage) from a single blow, you must make a DC 15 Fortitude save. If you fail, you die regardless of your current hit points." No such check exists anywhere in the engine. Any single hit for 50+ damage silently skips the instant-death check.

**Root cause:** Never implemented. Trivial to add — one conditional block after `final_damage` is computed and before the `hp_changed` event is emitted.

**PHB reference:** PHB p.145 — Massive Damage. Trigger: single attack dealing damage ≥ max(50, target_max_hp / 2). DC 15 Fort save. Failure = instant death regardless of current HP.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Threshold: flat 50 or half max HP? | PHB says "minimum 50 points" — so the trigger is `final_damage >= 50`. The "half total hit points" clause is a floor check, not a separate threshold. Trigger: `final_damage >= 50`. |
| 2 | Where in the pipeline? | After `final_damage` is computed (line 634 — `hp_after = hp_before - final_damage`) and before the `hp_changed` event is emitted (line 638). Insert between lines 634 and 636. |
| 3 | What happens on save failure? | Target dies instantly. Set `hp_after` to −10 (dead threshold). The existing `resolve_hp_transition()` call at line 655 then handles the dead state correctly. Emit `massive_damage_death` event before the `hp_changed` event. |
| 4 | What happens on save success? | Nothing — damage proceeds normally. No event needed for save success (or emit `massive_damage_survived` for log clarity — optional). |
| 5 | Does this apply to spell damage? | PHB p.145 specifies "single attack." Spells are not attacks in the PHB sense. For now: enforce in `attack_resolver.py` only (single and full attack paths). Spell damage via `spell_resolver.py` is out of scope — document as a debrief finding. |
| 6 | Does DR reduce damage before the threshold check? | Yes — `final_damage` is already post-DR. The check uses post-DR damage. PHB does not specify, but post-DR is the conservative interpretation. |
| 7 | Fort save resolution — call `get_save_bonus()`? | Yes. Use the existing `save_resolver.get_save_bonus()` pattern. Roll d20 + Fort bonus vs DC 15. |

---

## 3. Contract Spec

### Modification: `aidm/core/attack_resolver.py` — between lines 634 and 636

```python
        # WO-ENGINE-MASSIVE-DAMAGE-001: PHB p.145 — Massive Damage instant-death check
        if final_damage >= 50:
            from aidm.core.save_resolver import get_save_bonus, SaveType
            _md_save_bonus = get_save_bonus(world_state, intent.target_id, SaveType.FORT)
            _md_roll = rng.stream("combat").randint(1, 20)
            _md_total = _md_roll + _md_save_bonus
            _md_saved = _md_total >= 15

            events.append(Event(
                event_id=current_event_id,
                event_type="massive_damage_check",
                timestamp=timestamp + 0.15,
                payload={
                    "target_id": intent.target_id,
                    "damage": final_damage,
                    "fort_roll": _md_roll,
                    "fort_bonus": _md_save_bonus,
                    "fort_total": _md_total,
                    "dc": 15,
                    "saved": _md_saved,
                },
                citations=["PHB p.145"],
            ))
            current_event_id += 1

            if not _md_saved:
                # Instant death — override hp_after to -10
                hp_after = -10
```

The rest of the existing pipeline continues unchanged — `hp_changed` now uses the overridden `hp_after = -10`, and `resolve_hp_transition()` correctly classifies the target as dead.

---

## 4. Implementation Plan

### Step 1 — `aidm/core/attack_resolver.py`
Insert the ~20-line massive damage block between existing lines 634 and 636. No new files, no new EF fields, no schema changes.

### Step 2 — Tests (`tests/test_engine_massive_damage_gate.py`)
Gate: ENGINE-MASSIVE-DAMAGE — 10 tests

| Test | Description |
|------|-------------|
| MD-01 | 50 damage hit: massive damage check fires, event emitted |
| MD-02 | 49 damage hit: no massive damage check (below threshold) |
| MD-03 | 51 damage hit, Fort save succeeds (roll ≥ 15): target survives, normal HP applied |
| MD-04 | 50 damage hit, Fort save fails (roll < 15): target hp_after = −10, dead |
| MD-05 | Entity with Great Fortitude: Fort bonus +2 applied to massive damage check |
| MD-06 | `massive_damage_check` event payload: target_id, damage, fort_roll, fort_bonus, fort_total, dc=15, saved=True/False |
| MD-07 | Instant death on fail: subsequent `hp_changed` event shows hp_after = −10 |
| MD-08 | Instant death on fail: `resolve_hp_transition()` correctly classifies as dead (entity_dead event) |
| MD-09 | DR reduces damage below 50: no check (DR already applied before threshold test) |
| MD-10 | Regression: ENGINE-DR 10/10, ENGINE-DEATH-DYING gate unchanged |

---

## Integration Seams

**Files touched:**
- `aidm/core/attack_resolver.py` — ~20 lines inserted between lines 634–636

**Files NOT touched:**
- `aidm/core/full_attack_resolver.py` — delegates to attack_resolver; massive damage check fires inside attack_resolver, so full attack is covered automatically
- `aidm/core/spell_resolver.py` — spell damage massive damage rule deferred (document at debrief)
- No new EF fields, no schema changes

**Event constructor signature (mandatory):**
```python
Event(
    event_id=<int>,
    event_type=<str>,
    payload=<dict>,
    timestamp=<float>,
    citations=[],
)
```

**Save resolver pattern:**
```python
from aidm.core.save_resolver import get_save_bonus, SaveType
_bonus = get_save_bonus(world_state, target_id, SaveType.FORT)
```

**RNG pattern (match existing usage):**
```python
_roll = rng.stream("combat").randint(1, 20)
```

**Timestamp offset:** Insert at `timestamp + 0.15` — between hit confirmation (`+0.1`) and `hp_changed` (`+0.2`).

---

## Assumptions to Validate

1. `final_damage` at line 634 is post-DR — confirmed from code (`dr_absorbed` computed earlier, `final_damage = raw_damage - dr_absorbed`)
2. `hp_after` is a mutable local variable that can be overridden before `hp_changed` event construction — confirmed from line 634 context
3. `rng` is available in scope at the insertion point — confirmed (used throughout attack_resolver)
4. `world_state` is available in scope — confirmed
5. `get_save_bonus()` signature: `(world_state, actor_id, save_type)` — confirmed from save_resolver inspection

---

## Known Gap (document at debrief)

Spell damage massive damage rule not implemented (scope limited to `attack_resolver.py`). File as FINDING-ENGINE-MASSIVE-DAMAGE-SPELLS-001, LOW, OPEN.

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_dr.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_massive_damage_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/core/attack_resolver.py` — ~20-line massive damage block between lines 634–636
- [ ] `tests/test_engine_massive_damage_gate.py` — 10/10

**Gate:** ENGINE-MASSIVE-DAMAGE 10/10
**Regression bar:** ENGINE-DR 10/10, ENGINE-DEATH-DYING gate unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-MASSIVE-DAMAGE-001.md` on completion.

**Three-pass format:**
- Pass 1: per-file breakdown, key findings, open findings table
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — drift caught, patterns, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

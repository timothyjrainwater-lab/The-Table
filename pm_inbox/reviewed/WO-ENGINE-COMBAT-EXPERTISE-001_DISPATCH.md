# WO-ENGINE-COMBAT-EXPERTISE-001
## Wire Combat Expertise — Attack/AC Trade (Mirror of Power Attack)

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** ENGINE-COMBAT-EXPERTISE
**Minimum gate tests:** 8
**Source:** PHB p.92 — "Combat Expertise: You can voluntarily reduce your attack roll by up to 5 to get a +2 dodge bonus to your AC (when you reduce your attack by 2 or more) or a +1 dodge bonus to your AC (when you reduce your attack by 1). This bonus lasts until your next action."
**Dispatch:** ENGINE BATCH C

---

## Target Lock

Combat Expertise is the defensive mirror of Power Attack. Power Attack (already implemented) lets the attacker trade attack bonus for damage bonus via `intent.power_attack_penalty`. Combat Expertise trades attack bonus for AC bonus. The pattern: `intent.combat_expertise_penalty` (0–5) reduces `attack_bonus_with_conditions`, and a corresponding `combat_expertise_ac_bonus` must be applied to the defender's AC when they are attacked.

**Two-part implementation:**
1. **Attack side:** Subtract `intent.combat_expertise_penalty` from `attack_bonus_with_conditions` in `attack_resolver.py`. (Same pattern as `power_attack_penalty`.)
2. **Defense side:** Add `combat_expertise_ac_bonus` to `target_ac` in `attack_resolver.py` when the **defending** entity has declared Combat Expertise. This requires the AC bonus to be stored somewhere the attack resolver can read it — use `EF.COMBAT_EXPERTISE_BONUS` on the entity (written at intent resolution time, cleared at round end).

**PHB rule:** Penalty of 1 → +1 AC. Penalty of 2–5 → +2 AC (not 1:1 — it's capped at +2 for penalty ≥ 2). Prerequisite: INT 13.

---

## Binary Decisions

1. **Where is `combat_expertise_penalty` set?** At intent resolution in `session_orchestrator.py` or `play_loop.py`, the same place `power_attack_penalty` is set. The player declares "combat expertise 3" → `intent.combat_expertise_penalty = 3`. Confirm the existing pattern and mirror it.

2. **AC bonus formula:** PHB p.92:
   - Penalty = 1 → AC bonus = +1
   - Penalty = 2–5 → AC bonus = +2
   - Formula: `ac_bonus = 1 if penalty == 1 else 2 if penalty >= 2 else 0`
   - Cap: penalty cannot exceed BAB (PHB p.92: "up to 5, but not more than your BAB").

3. **Where is the AC bonus applied?** The defending entity's AC is read inside `attack_resolver.py` at the `target_ac` computation. The bonus must be stored on the entity dict before the attack resolves. Two options:
   - **Option A (preferred):** Store `EF.COMBAT_EXPERTISE_BONUS` on entity at intent time, read in `target_ac` block. This mirrors how `INSPIRE_COURAGE_BONUS` works.
   - **Option B:** Pass it through intent/world state. More complex.
   Use Option A.

4. **When is the bonus cleared?** PHB: "lasts until your next action." Clear at the start of the entity's next turn. This maps to the existing round-reset logic in `play_loop.py` that clears per-turn fields.

5. **Does Power Attack already have a `power_attack_penalty` field on AttackIntent?** Yes — confirmed by prior WO context. Add `combat_expertise_penalty: int = 0` alongside it.

---

## Contract Spec

### `aidm/schemas/attack.py` — `AttackIntent`

Add field alongside `power_attack_penalty`:
```python
combat_expertise_penalty: int = 0
"""Combat Expertise: attack penalty declared by attacker (0–5, capped at BAB). PHB p.92."""
```

### `aidm/schemas/entity_fields.py`

Add new constant:
```python
COMBAT_EXPERTISE_BONUS = "combat_expertise_bonus"  # WO-ENGINE-COMBAT-EXPERTISE-001: Dodge AC bonus from CE declaration
```

### `aidm/core/attack_resolver.py` — `resolve_attack()`

**Attack side** (in `attack_bonus_with_conditions` block, after `_fd_attack_penalty`):
```python
# WO-ENGINE-COMBAT-EXPERTISE-001: Combat Expertise attack penalty (PHB p.92)
_ce_penalty = intent.combat_expertise_penalty  # 0 if not declared
```
Add `- _ce_penalty` to `attack_bonus_with_conditions`.

**Defense side** (in `target_ac` block, alongside `cover_result.ac_bonus`):
```python
# WO-ENGINE-COMBAT-EXPERTISE-001: Combat Expertise AC dodge bonus on defending entity
_ce_ac_bonus = target.get(EF.COMBAT_EXPERTISE_BONUS, 0)
```
Add `+ _ce_ac_bonus` to `target_ac`.

**Before attack resolve** (at intent application point, to write CE bonus onto entity):
```python
# WO-ENGINE-COMBAT-EXPERTISE-001: Write CE AC bonus to entity for defense reads
if intent.combat_expertise_penalty > 0:
    _ce_ac = 1 if intent.combat_expertise_penalty == 1 else 2
    world_state.entities[intent.attacker_id][EF.COMBAT_EXPERTISE_BONUS] = _ce_ac
```

### `tests/test_engine_combat_expertise_gate.py` — NEW FILE

Minimum 8 gate tests, IDs CEX-001 through CEX-008:

| Test | Assertion |
|------|-----------|
| CEX-001 | Combat Expertise penalty 3: attack roll reduced by 3 |
| CEX-002 | Combat Expertise penalty 3: attacker's AC bonus = +2 when later attacked |
| CEX-003 | Combat Expertise penalty 1: attacker's AC bonus = +1 |
| CEX-004 | Combat Expertise penalty 0: no attack penalty, no AC bonus |
| CEX-005 | Combat Expertise penalty 5: attack reduced by 5, AC bonus = +2 (cap at +2) |
| CEX-006 | Non-Combat-Expertise attacker: no attack penalty applied |
| CEX-007 | CE AC bonus on entity is readable by attack resolver when entity is targeted |
| CEX-008 | Regression: Power Attack unaffected by CE code addition |

---

## Implementation Plan

1. Read `aidm/schemas/attack.py` — locate `AttackIntent` and `power_attack_penalty` field. Add `combat_expertise_penalty` alongside.
2. Read `aidm/schemas/entity_fields.py` — add `COMBAT_EXPERTISE_BONUS` constant.
3. Read `aidm/core/attack_resolver.py` lines 390–430 (`attack_bonus_with_conditions` block). Add `- _ce_penalty`.
4. Read `aidm/core/attack_resolver.py` lines 313–360 (`target_ac` block). Add `+ _ce_ac_bonus`.
5. Find where intent is applied to entity state (before attack sequence). Write `EF.COMBAT_EXPERTISE_BONUS` to attacker entity.
6. Write `tests/test_engine_combat_expertise_gate.py` with CEX-001 through CEX-008.
7. Run gate suite: `python -m pytest tests/test_engine_combat_expertise_gate.py -v`.
8. Run regression: `python -m pytest tests/ -q --tb=short --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ui_2d_wiring.py`.
9. Confirm 0 new failures.

---

## Integration Seams

- **`aidm/schemas/attack.py`** — `AttackIntent`: add `combat_expertise_penalty: int = 0`.
- **`aidm/schemas/entity_fields.py`** — add `COMBAT_EXPERTISE_BONUS` constant.
- **`aidm/core/attack_resolver.py`** — two insertion points: attack bonus block + target AC block + entity write.
- **Event constructor:** `Event(event_id=..., event_type=..., timestamp=..., payload=...)` — not relevant.
- **Class feature pattern:** Not applicable — feat check via `EF.FEATS` (INT 13 prerequisite enforced at chargen, not runtime).
- **Round-reset:** Confirm `play_loop.py` clears per-turn entity fields at round start. `EF.COMBAT_EXPERTISE_BONUS` must be cleared there alongside other per-round fields.

---

## Assumptions to Validate

1. Confirm `AttackIntent` has `power_attack_penalty` field (expected: yes — confirmed by prior WO context). Mirroring it for CE is the correct pattern.
2. Confirm `attack_bonus_with_conditions` block subtracts `power_attack_penalty` (expected: yes — find the line, add CE penalty alongside).
3. Confirm `target_ac` construction reads additive bonuses like `cover_result.ac_bonus` (expected: yes — confirmed pre-dispatch read).
4. Confirm no existing `combat_expertise` references in `attack_resolver.py` (expected: none — grep to verify).
5. Confirm the round-reset location in `play_loop.py` where per-turn entity fields are cleared — add `EF.COMBAT_EXPERTISE_BONUS` there.

---

## Preflight

Before writing any code:
- `grep -n "combat_expertise\|COMBAT_EXPERTISE" aidm/core/attack_resolver.py` — confirm not implemented
- `grep -n "power_attack_penalty" aidm/schemas/attack.py` — locate the field pattern to mirror
- `grep -n "power_attack_penalty" aidm/core/attack_resolver.py` — locate attack subtraction site
- `grep -n "INSPIRE_COURAGE_BONUS\|inspire_courage" aidm/core/attack_resolver.py | head -10` — locate AC bonus read pattern to mirror for CE bonus
- `grep -n "INSPIRE_COURAGE_BONUS\|per_turn\|round_reset" aidm/core/play_loop.py | head -10` — confirm round-reset pattern

---

## Delivery Footer

- Files modified: `aidm/schemas/attack.py`, `aidm/schemas/entity_fields.py`, `aidm/core/attack_resolver.py`, `tests/test_engine_combat_expertise_gate.py` (new)
- Gate: ENGINE-COMBAT-EXPERTISE, minimum 8 tests
- Run full regression before filing debrief
- **Debrief Required:** File to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-COMBAT-EXPERTISE-001.md`

### Debrief Template

```
# DEBRIEF — WO-ENGINE-COMBAT-EXPERTISE-001

**Verdict:** [PASS/FAIL] [N/N]
**Gate:** ENGINE-COMBAT-EXPERTISE
**Date:** [DATE]

## Pass 1 — Per-File Breakdown
[Files modified, changes made, key findings]

## Pass 2 — PM Summary (≤100 words)
[Summary]

## Pass 3 — Retrospective
[Drift caught, patterns, open findings]

## Radar
[Gate results, confirmations]
```

### Audio Cue
```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

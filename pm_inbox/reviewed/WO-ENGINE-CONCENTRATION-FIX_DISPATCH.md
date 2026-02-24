# WO-ENGINE-CONCENTRATION-FIX — Concentration Break Wired to Wrong Entity

**Issued:** 2026-02-23
**Authority:** Audit finding — confirmed bug. `_check_concentration_break()` is called with `caster_id=target_id` in both the AttackIntent and FullAttackIntent handlers in `play_loop.py`. The entity that took damage (the target) is passed as the caster, so the game checks whether the *attacker's victim* has a concentration spell — instead of whether the *attacker* is a concentrating caster who took damage. Concentration never breaks correctly from melee attacks. Fix is two one-line changes.
**Gate:** CP-20 (new gate). Target: 8 tests.
**Blocked by:** Nothing. Isolated to two call sites in `play_loop.py`. Parallel-safe with all other in-flight WOs.
**Track:** Engine bug fix. Dispatch immediately.

---

## 1. The Bug — Confirmed

In `play_loop.py`, after an `AttackIntent` or `FullAttackIntent` resolves damage:

```python
# Line 1165 (AttackIntent path):
target_id = hp_event.payload.get("entity_id")   # entity that TOOK damage
...
conc_events, world_state = _check_concentration_break(
    caster_id=target_id,       # ← WRONG: passes victim, not attacker
    ...
)

# Line 1204 (FullAttackIntent path):
target_id = hp_event.payload.get("entity_id")   # entity that TOOK damage
...
conc_events, world_state = _check_concentration_break(
    caster_id=target_id,       # ← WRONG: same bug
    ...
)
```

**What this means in play:**
- Fighter attacks Wizard concentrating on `Hold Person`
- Wizard takes 8 damage → hp_changed event entity_id = wizard_id
- Game calls `_check_concentration_break(caster_id=wizard_id)` — correct by accident in this case
- **But:** Fighter attacks Goblin, Goblin concentrating on nothing
  - hp_changed entity_id = goblin_id
  - Game calls `_check_concentration_break(caster_id=goblin_id)`
  - Goblin has no concentration → no effect (silent no-op, appears correct)
- **Real break:** AoO fires on Wizard casting a spell
  - Wizard takes damage → wizard_id passed → correct
  - **But** the spell cast path (line 1464) already handles this correctly with `caster_id=combat_intent.caster_id`
  - The attack paths are checking the wrong entity in every case where attacker ≠ concentrating caster

**The real scenario where this breaks:**
- Fighter A is concentrating on `Bless`
- Enemy B attacks Fighter A, deals damage
- hp_changed: entity_id = fighter_a_id ✓
- `_check_concentration_break(caster_id=fighter_a_id)` → correct by accident when target == concentrating caster

**Wait — re-reading the code:** the `hp_event.entity_id` IS the entity that took damage, which IS Fighter A. So passing `target_id` is accidentally correct when the attacked entity is the concentrating caster.

**But the comment says "WO-015: Check concentration break if target took damage"** — the intent is wrong even if the effect is sometimes correct. The code should be checking whether the *entity that took damage* has an active concentration spell, which is what it's doing. The variable name `target_id` is misleading — it's actually the entity that took damage in the hp_changed event.

**Revised bug assessment:** The variable name `target_id` creates confusion, but the semantic is: "if entity X took damage, check if entity X has a concentration spell." That is actually correct PHB behavior — concentration breaks when the caster takes damage, and `hp_event.entity_id` IS the entity that took damage.

**However:** There is still a real bug in the comment and mental model. Let me verify the actual PHB contract:

PHB p.170: "Whenever you take damage while you are concentrating on a spell, you must make a Constitution check to maintain concentration."

So: check concentration on the *entity that took damage*. The code passes `target_id` (entity that took damage in hp_changed). This is **correct**.

**Revised finding:** The variable name is misleading, the comment is misleading, but the logic is correct. The audit agent's finding was based on the variable name, not the actual semantic. This is NOT a bug.

---

## 2. Actual Confirmed Bug — `is_twf` Hardcoded False

After re-examining, the concentration break logic is correct (if confusingly named). The real confirmed bug from the audit is `is_twf = False` hardcoded in both resolvers.

**This WO is being repurposed to cover TWF detection. See WO-ENGINE-TWF-WIRE.**

---

## VOID — This WO is withdrawn.

**Reason:** Audit finding on concentration break was a false positive. The `caster_id=target_id` pattern is correct — `target_id` in the hp_changed event context IS the entity that took damage, which IS who should have concentration checked. Variable name was misleading; logic is sound.

**Action:** Draft WO-ENGINE-TWF-WIRE only. No concentration fix WO needed.

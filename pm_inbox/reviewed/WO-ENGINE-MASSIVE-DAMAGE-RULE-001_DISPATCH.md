# Work Order: WO-ENGINE-MASSIVE-DAMAGE-RULE-001
**Artifact ID:** WO-ENGINE-MASSIVE-DAMAGE-RULE-001
**Batch:** G (Dispatch #16)
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**PHB ref:** p.145 (Massive Damage)

---

## Summary

When a creature takes 50 or more hit points of damage from a single hit, it must succeed on a Fortitude save (DC 15) or die instantly (PHB p.145). This rule applies regardless of current HP — a creature at 200 HP hit for 60 damage must still make this save.

Currently no massive damage check exists in the engine. Any single hit delivering 50+ damage simply subtracts from HP; no Fort save is triggered and no instant death is possible via this route. This is a significant gap — high-damage spells (Fireball, Chain Lightning) and powerful monsters routinely deliver 50+ damage.

---

## Scope

**Files in scope:**
- `aidm/core/attack_resolver.py` — add massive damage check after damage is applied on a hit
- `aidm/core/spell_resolver.py` — add massive damage check after spell damage is applied

**Files read-only (verify, do not modify):**
- `aidm/core/save_resolver.py` — confirm Fort save pattern to replicate
- `aidm/schemas/entity_fields.py` — confirm EF.DYING, EF.DEFEATED, EF.SAVE_FORT field names
- `aidm/core/conditions.py` — confirm death/dying state-setting pattern

**Files out of scope:**
- Nonlethal damage — massive damage rule applies to lethal damage only
- Coup de grâce — separate mechanic (already implemented)

---

## Assumptions to Validate (verify before writing)

1. Confirm Fort save pattern in `save_resolver.py` — find the helper that rolls d20 + SAVE_FORT and returns pass/fail.
2. Confirm how death is set after a Fort save failure — does the resolver set EF.DEFEATED directly or emit a separate event?
3. Confirm the massive damage threshold is 50 HP (PHB p.145) — this applies to damage dealt, not damage remaining.
4. Confirm no pre-existing massive damage check in `attack_resolver.py` or `spell_resolver.py`.
5. Confirm whether massive damage applies to constructs, undead, and objects — PHB p.145 excludes creatures immune to critical hits (note this in Pass 3 even if not implemented this WO).

---

## Implementation

### In `attack_resolver.py` — after HP is decremented on a hit:

```python
# Massive damage rule (PHB p.145)
if damage_dealt >= 50:
    fort_roll = _d20() + target.get(EF.SAVE_FORT, 0)
    if fort_roll < 15:
        # Instant death — set defeated
        target[EF.DEFEATED] = True
        events.append(Event(
            event_type="massive_damage_death",
            payload={"target_id": target_id, "damage": damage_dealt, "fort_roll": fort_roll}
        ))
    else:
        events.append(Event(
            event_type="massive_damage_survived",
            payload={"target_id": target_id, "damage": damage_dealt, "fort_roll": fort_roll}
        ))
```

### In `spell_resolver.py` — after spell damage is applied:

Same pattern. Spell damage 50+ triggers the same Fort DC 15 check.

**Note:** The DC is fixed at 15 regardless of damage amount (PHB p.145). Higher damage does not raise the DC.

---

## Acceptance Criteria

Write gate file `tests/test_engine_massive_damage_rule_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| MD-001 | Attack deals 50 HP damage; Fort save fails | Target dies (DEFEATED=True); massive_damage_death event emitted |
| MD-002 | Attack deals 50 HP damage; Fort save succeeds | Target survives; massive_damage_survived event emitted |
| MD-003 | Attack deals 49 HP damage | No massive damage check; no save triggered |
| MD-004 | Attack deals exactly 50 HP damage (boundary) | Massive damage check triggered |
| MD-005 | Spell deals 50+ HP damage; Fort fails | Same death outcome as physical attack |
| MD-006 | Spell deals 50+ HP damage; Fort succeeds | Survives; event emitted |
| MD-007 | Fort DC is always 15 regardless of damage amount (60 damage same DC as 50 damage) | DC confirmed 15 in event payload |
| MD-008 | Target with high Fort bonus (say +10) hit for 50 damage | Save succeeds reliably; survived event emitted |

8 tests total. Gate label: ENGINE-MASSIVE-DAMAGE-RULE-001.

---

## Pass 3 Checklist

1. Confirm whether massive damage applies to undead, constructs, and creatures immune to critical hits — PHB p.145 is ambiguous on constructs/undead. Document what the engine currently does and flag as FINDING if the current implementation doesn't account for immunity categories.
2. Note whether the massive damage check fires even if the damage kills the target through HP depletion (i.e., does it matter if HP goes to -10?). In practice: if target dies from HP loss anyway, massive damage save is moot — but should still be run for strict RAW compliance. Document the decision.
3. Flag any spell that routinely deals 50+ damage (Fireball at high caster level, Chain Lightning, etc.) — these are now implicitly gated by this rule.
4. Note KERNEL-01 (Entity Lifecycle) touch — massive damage is an alternate death pathway. The engine now has two routes to instant death: HP depletion and massive damage Fort save. Document both are wired correctly.

---

## Session Close Condition

- [ ] `git add aidm/core/attack_resolver.py aidm/core/spell_resolver.py tests/test_engine_massive_damage_rule_001_gate.py`
- [ ] `git commit` with hash
- [ ] All 8 MD tests pass; zero regressions
- [ ] Debrief filed to `pm_inbox/reviewed/`

# DEBRIEF: WO-ENGINE-NATURAL-ATTACK-001

**From:** Builder (Sonnet 4.6)
**To:** PM (Aegis), via PO (Thunder)
**Date:** 2026-02-24
**Lifecycle:** NEW
**WO:** WO-ENGINE-NATURAL-ATTACK-001
**Result:** COMPLETED — 10/10 gate tests, zero regressions

---

## Pass 1 — Full Context Dump

### What Was Done

Closed the FINDING-WILDSHAPE-NATURAL-ATTACKS-001 MEDIUM gap. Druid in Wild Shape can now bite and claw. Also applies to any entity with `EF.NATURAL_ATTACKS` set (monsters, companions, etc.).

---

### Files Created

**`aidm/core/natural_attack_resolver.py`**

- `validate_natural_attack(actor, attack_name, target_id, world_state)` — checks `EF.NATURAL_ATTACKS` is non-empty, attack_name is in the list, target exists and is not defeated.
- `_build_weapon_from_natural_attack(attack_dict)` — converts NATURAL_ATTACKS list entry `{name, damage, damage_type}` to a `Weapon` dataclass with `weapon_type="natural"`.
- `resolve_natural_attack(intent, world_state, rng, next_event_id, timestamp)` — validates, builds weapon, constructs `AttackIntent`, then passes to `resolve_attack()`. Key mechanism: passes a `deepcopy` of world_state with `EQUIPMENT_MELDED=False` on the attacker entity so `resolve_attack()` does not block natural attacks. Returns `(events, original_world_state)` — HP mutation is the caller's responsibility via `apply_attack_events`.

**`tests/test_engine_gate_natural_attack.py`** — 10 tests.

---

### Files Modified

**`aidm/schemas/intents.py`**
- Added `NaturalAttackIntent(attacker_id, target_id, attack_name, attack_bonus)`.
- Added to `Intent` union and `parse_intent()`.

**`aidm/core/play_loop.py`**
- Added `NaturalAttackIntent` to import block.
- Added `NaturalAttackIntent` to the `attacker_id` extraction branch (alongside `AttackIntent`, `FullAttackIntent`, `CoupDeGraceIntent`).
- Added routing dispatch: `elif isinstance(combat_intent, NaturalAttackIntent)` → `resolve_natural_attack` + `apply_attack_events`. Inserted after ChargeIntent block, before policy-based resolution.

---

### Key Design Decision: EQUIPMENT_MELDED Bypass

The EQUIPMENT_MELDED guard in `resolve_attack()` fires before condition modifiers and returns early with `intent_validation_failed`. Natural attacks must bypass this (PHB p.36: natural attacks are not equipment). The cleanest solution without restructuring `resolve_attack()`:

Pass a `deepcopy` of world_state with `EQUIPMENT_MELDED=False` on the attacker. `resolve_attack` sees a non-melded attacker and proceeds normally. The original world_state is returned unchanged. This avoids the extract-`_resolve_single_attack()` refactor proposed in the WO brief — the deepcopy approach achieves the same separation with less surface area.

The dispatch originally specified extracting a `_resolve_single_attack()` private function. That refactor is deferred — the deepcopy approach is simpler, equally correct, and introduces no new call sites.

---

### Gate Results

| Gate | Tests | Result |
|------|-------|--------|
| ENGINE-NATURAL-ATTACK | 10/10 | PASS |

Adjacent gates (regression): ENGINE-WILD-SHAPE 10/10, ENGINE-BARDIC-MUSIC 10/10, ENGINE-BARBARIAN-RAGE 10/10, ENGINE-SMITE-EVIL 8/8 — all green.

---

### Findings Closed

| ID | Status |
|----|--------|
| FINDING-WILDSHAPE-NATURAL-ATTACKS-001 | CLOSED — natural attack path now exists |

---

## Pass 2 — PM Summary

**WO-ENGINE-NATURAL-ATTACK-001: COMPLETED.** Druid is now combat-capable in Wild Shape. Wolf bite, bear claw/bite, eagle talon, crocodile bite, snake bite all resolve through the standard attack pipeline. Monster natural attacks also benefit. 10/10 gate. FINDING-WILDSHAPE-NATURAL-ATTACKS-001 MEDIUM closed.

---

## Pass 3 — Retrospective

### Deepcopy vs. Refactor

The WO brief proposed extracting `_resolve_single_attack()` to share logic between `resolve_attack` and `resolve_natural_attack`. That refactor would have been ~200 lines of `resolve_attack` extracted into a private function, with two callers. The deepcopy approach achieves the same separation with 3 lines. The refactor remains the cleaner long-term architecture if `resolve_attack` acquires a third caller — but for a single new use case, YAGNI applies.

### attack_dict Key Variance

The NATURAL_ATTACKS list entries in wild_shape_resolver.py use `"damage"` as the dice key (e.g., `{"name": "bite", "damage": "1d6", ...}`). The `_build_weapon_from_natural_attack` function handles both `"damage"` and `"damage_dice"` as aliases. If future monster data uses `"damage_dice"` instead, this is already covered.

### NaturalAttackIntent Uses attacker_id, Not actor_id

All the class-feature intents (RageIntent, WildShapeIntent, etc.) use `actor_id`. NaturalAttackIntent uses `attacker_id` to match the convention of AttackIntent and FullAttackIntent. This is correct — natural attacks are combat resolution, not class feature activation. The actor_id extraction block in play_loop was updated accordingly.

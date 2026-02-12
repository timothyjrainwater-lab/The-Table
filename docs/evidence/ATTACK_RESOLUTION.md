# Evidence Map: Attack Resolution

**Subsystem:** `aidm/core/attack_resolver.py`, `aidm/core/full_attack_resolver.py`
**Primary Source:** Player's Handbook (681f92bc94ff)
**Last Updated:** 2026-02-12 (WO-FIX-002)

---

## Single Attack Resolution (attack_resolver.py)

| Mechanic | PHB Page | Vault Path | Test(s) | Gaps |
|---|---|---|---|---|
| Attack roll = d20 + bonus vs AC | p.140 | `681f92bc94ff/pages/0140.txt` | `test_attack_hits_when_roll_meets_or_exceeds_ac` | None |
| Natural 20 always hits | p.140 | `681f92bc94ff/pages/0140.txt` | `test_natural_20_always_hits` | None |
| Natural 1 always misses | p.140 | `681f92bc94ff/pages/0140.txt` | `test_natural_1_always_misses` | None |
| Critical threat detection | p.140 | `681f92bc94ff/pages/0140.txt` | `test_single_attack_has_threat_detection` | None |
| Critical confirmation roll | p.140 | `681f92bc94ff/pages/0140.txt` | `test_single_attack_critical_confirmation` | None |
| Critical damage x2 | p.140 | `681f92bc94ff/pages/0140.txt` | `test_single_attack_critical_damage_multiplied` | None |
| Critical damage x3 | p.140 | `681f92bc94ff/pages/0140.txt` | `test_single_attack_critical_x3_multiplier` | None |
| Non-critical multiplier = 1 | p.140 | `681f92bc94ff/pages/0140.txt` | `test_single_attack_non_critical_multiplier_is_1` | None |
| Expanded threat range (19-20) | p.140 | `681f92bc94ff/pages/0140.txt` | `test_single_attack_expanded_threat_range_19_20` | None |
| Threat doesn't auto-hit on miss | p.140 | `681f92bc94ff/pages/0140.txt` | `test_single_attack_threat_in_expanded_range_must_still_meet_ac` | None |
| STR modifier to melee damage | p.113 | `681f92bc94ff/pages/0113.txt` | `test_damage_reduces_target_hp` | Dedicated STR mod test missing |
| Damage reduces HP | p.145 | `681f92bc94ff/pages/0145.txt` | `test_damage_reduces_target_hp` | None |
| Entity defeated at HP <= 0 | p.145 | `681f92bc94ff/pages/0145.txt` | `test_entity_defeated_when_hp_drops_to_zero_or_below` | None |
| Condition modifiers to attack | p.151 | `681f92bc94ff/pages/0151.txt` | (CP-16 tests) | Evidence pointer needed |
| Cover AC bonus | p.150 | `681f92bc94ff/pages/0150.txt` | (CP-19 tests) | Evidence pointer needed |
| Deterministic replay | — | — | `test_attack_resolution_deterministic_replay` | Architectural, no PHB ref |

## Full Attack Resolution (full_attack_resolver.py)

| Mechanic | PHB Page | Vault Path | Test(s) | Gaps |
|---|---|---|---|---|
| Iterative attacks: BAB -5 progression | p.143 | `681f92bc94ff/pages/0143.txt` | `test_iterative_attacks_calculated_correctly` | None |
| Critical threat on natural 20 | p.140 | `681f92bc94ff/pages/0140.txt` | `test_critical_threat_on_natural_20` | None |
| Critical confirmation logic | p.140 | `681f92bc94ff/pages/0140.txt` | `test_critical_confirmation_logic` | None |
| Critical damage multiplication (x2, x3, x4) | p.140 | `681f92bc94ff/pages/0140.txt` | `test_critical_damage_multiplication`, `test_critical_multiplier_variations` | None |
| Expanded threat range 19-20 | p.140 | `681f92bc94ff/pages/0140.txt` | `test_weapon_critical_range_19_20_threatens_on_19` | None |
| Expanded threat range 18-20 | p.140 | `681f92bc94ff/pages/0140.txt` | `test_weapon_critical_range_18_20_threatens_on_18` | None |
| Default threat range 20-only | p.140 | `681f92bc94ff/pages/0140.txt` | `test_weapon_default_critical_range_20_only` | None |
| RNG consumption order deterministic | — | — | `test_rng_consumption_order_with_mixed_threat_results` | Architectural, no PHB ref |
| Multiple attacks accumulate damage | p.143 | `681f92bc94ff/pages/0143.txt` | `test_multiple_attacks_accumulate_damage` | None |
| High BAB: 4 iterative attacks | p.143 | `681f92bc94ff/pages/0143.txt` | `test_high_bab_character_four_attacks` | None |

## Weapon Schema (schemas/attack.py)

| Mechanic | PHB Page | Vault Path | Test(s) | Gaps |
|---|---|---|---|---|
| Critical multiplier values (x2, x3, x4) | p.140 | `681f92bc94ff/pages/0140.txt` | `test_weapon_critical_range_validation` | None |
| Critical range 1-20 validation | p.140 | `681f92bc94ff/pages/0140.txt` | `test_weapon_critical_range_validation` | None |
| Damage types: PHB energy types | p.309 | `681f92bc94ff/pages/0309.txt` | Weapon.__post_init__ validates | Dedicated test missing |

---

## Identified Gaps

1. **STR modifier to melee damage:** Test exists but is indirect. Needs a dedicated test that verifies STR mod is added to damage, with evidence pointer to PHB p.113.
2. **Condition modifier evidence:** CP-16 tests exist but need `Evidence:` pointers added to docstrings.
3. **Cover bonus evidence:** CP-19 tests exist but need `Evidence:` pointers added to docstrings.
4. **Damage type validation:** Weapon schema validates types but no dedicated test for the energy type list from PHB p.309.
5. **Two-handed weapon 1.5x STR:** Not implemented. PHB p.113 states two-handed weapons get 1.5x STR to damage.
6. **Off-hand weapon 0.5x STR:** Not implemented. PHB p.113 states off-hand gets 0.5x STR.

---

## RAW Quotes (from local corpus)

### PHB p.140 (681f92bc94ff/pages/0140.txt)
> "A natural 1 (the d20 comes up 1) on the attack roll is always a miss. A natural 20 (the d20 comes up 20) is always a hit. A natural 20 is also a threat—a possible critical hit."

### PHB p.140 — Critical Hits sidebar (681f92bc94ff/pages/0140.txt)
> "When you make an attack roll and get a natural 20 (the d20 shows 20), you hit regardless of your target's Armor Class, and you have scored a threat."
> "To find out if it's a critical hit, you immediately make a critical roll—another attack roll with all the same modifiers as the attack roll you just made. If the critical roll also results in a hit against the target's AC, your original hit is a critical hit."

### PHB p.143 — Full Attack (681f92bc94ff/pages/0143.txt)
> "If you get more than one attack per round because your base attack bonus is high enough, you must use a full-round action (and target a single enemy) to get your additional attacks."

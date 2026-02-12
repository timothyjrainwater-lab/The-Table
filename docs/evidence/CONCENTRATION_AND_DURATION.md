# Evidence Map: Concentration & Duration Tracking

**Subsystem:** `aidm/core/duration_tracker.py`, `aidm/core/spell_resolver.py`
**Primary Source:** Player's Handbook (681f92bc94ff)
**Last Updated:** 2026-02-12 (WO-FIX-001)

---

## Concentration Mechanics

| Mechanic | PHB Page | Vault Path | Test(s) | Gaps |
|---|---|---|---|---|
| Concentration check DC = 10 + damage | p.69-70 | `681f92bc94ff/pages/0070.txt` | `test_concentration_check_on_damage` | None |
| Concentration DC scales with damage | p.69-70 | `681f92bc94ff/pages/0070.txt` | `test_concentration_dc_scales_with_damage` | None |
| No check if no concentration active | p.69-70 | `681f92bc94ff/pages/0070.txt` | `test_concentration_no_active_spell` | None |
| Failed check breaks concentration | p.69-70 | `681f92bc94ff/pages/0070.txt` | `test_concentration_breaks_on_failure` | None |
| Concentration can be used untrained | p.69 | `681f92bc94ff/pages/0069.txt` | `test_concentration_untrained_allowed` | None |
| **3.5e: Multiple concentration spells allowed** | p.170+ | `681f92bc94ff/pages/0170.txt` | `test_multiple_concentration_spells_allowed` | See note 1 |
| **3.5e: No auto-displacement on new concentration** | — | — | `test_adding_concentration_does_not_displace_existing` | See note 2 |
| 3.5e: Three simultaneous concentration valid | — | — | `test_three_simultaneous_concentration_spells` | See note 2 |
| Breaking concentration removes ALL for that caster | p.69-70 | `681f92bc94ff/pages/0070.txt` | `test_break_concentration_removes_all` | None |

### Notes

1. **Multiple concentration rule:** 3.5e PHB does NOT contain a one-concentration-per-caster limit anywhere. The absence of such a rule is the evidence. This is a negative proof: the 5e PHB p.203 states "You lose concentration on a spell if you cast another spell that requires concentration" — this rule does not exist in the 3.5e PHB. The anti-5e regression tests guard against this absence being violated.

2. **Auto-displacement absence:** Same as Note 1. The evidence is the absence of a 5e-style rule in 3.5e. No PHB page positively states "you may maintain multiple concentration spells" — it simply never states the opposite. The anti-5e tests are contamination sentinels, not positive-rule tests.

## Duration Tracking Mechanics

| Mechanic | PHB Page | Vault Path | Test(s) | Gaps |
|---|---|---|---|---|
| Duration in rounds (6 seconds each) | p.175-176 | `681f92bc94ff/pages/0175.txt` | `test_effect_duration_rounds` | None |
| Duration in minutes | p.175-176 | `681f92bc94ff/pages/0175.txt` | `test_effect_duration_minutes` | None |
| Duration in hours | p.175-176 | `681f92bc94ff/pages/0175.txt` | `test_effect_duration_hours` | None |
| Duration in days | p.175-176 | `681f92bc94ff/pages/0175.txt` | `test_effect_duration_days` | None |
| Duration: until discharged | p.176 | `681f92bc94ff/pages/0176.txt` | `test_effect_duration_until_discharged` | None |
| Duration: permanent | p.176 | `681f92bc94ff/pages/0176.txt` | `test_effect_duration_permanent` | None |
| Time unit requires positive value | p.175-176 | `681f92bc94ff/pages/0175.txt` | `test_effect_duration_time_unit_requires_value` | None |
| Serialization roundtrip | — | — | `test_effect_duration_serialization`, `test_effect_duration_roundtrip` | Architectural |

---

## Anti-5e Regression Guards

These tests exist specifically to prevent D&D 5th Edition rules from re-entering the 3.5e codebase. They are contamination sentinels.

| Guard | 5e Rule Being Blocked | 3.5e Rule | Test |
|---|---|---|---|
| Multiple concentration allowed | 5e PHB p.203: one concentration per caster | 3.5e: no such limit exists | `test_multiple_concentration_spells_allowed` |
| No auto-displacement | 5e PHB p.203: new concentration ends old | 3.5e: no auto-displacement | `test_adding_concentration_does_not_displace_existing` |
| Three simultaneous legal | 5e: impossible (only one allowed) | 3.5e: legal if you can pass checks | `test_three_simultaneous_concentration_spells` |
| Break removes all | N/A (same in both editions) | 3.5e: all concentration ends on failure | `test_break_concentration_removes_all` |

---

## Identified Gaps

1. **Spell resistance integration:** Duration tracker doesn't yet handle spell resistance checks during application. PHB p.177.
2. **Dispel Magic mechanics:** `dispel_effect()` exists but the caster level check (PHB p.223) is not implemented.
3. **Concentration during vigorous/violent motion:** PHB p.69-70 lists additional concentration DCs for conditions like grappling, vigorous motion, violent weather. These are not yet tested.

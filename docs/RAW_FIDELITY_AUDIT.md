# RAW Fidelity Audit
## D&D 3.5e Rules Alignment & Documented Deviations

**Project:** AIDM — Deterministic D&D 3.5e Engine
**Document Type:** Governance / Rules Audit
**Status:** ACTIVE
**Audience:** Project Authority, Auditors, Implementers

---

## 1. PURPOSE

This audit documents where the AIDM engine:

- **Implements D&D 3.5e RAW faithfully**
- **Intentionally deviates** (degraded or deferred)
- **Explicitly forbids mechanics** due to closed capability gates

Its goals are to:
- Prevent silent rules drift
- Avoid accidental 5e contamination
- Ensure every deviation is intentional, documented, and justified

This document is **authoritative**.

---

## 2. AUDIT METHODOLOGY

Each rules area is evaluated and classified as one of:

- **FULL** — Faithful to RAW
- **DEGRADED** — Partial or simplified, documented
- **DEFERRED** — Not implemented yet
- **FORBIDDEN** — Blocked by closed capability gate

Every non-FULL entry must reference a CP or kernel decision.

---

## 3. MOVEMENT & POSITIONING

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Normal movement | PHB 144–147 | FULL | Grid-based |
| Difficult terrain | PHB 148–150 | FULL | CP-19 |
| Running | PHB 144 | FULL | Terrain-restricted |
| Charging | PHB 154 | FULL | Terrain-restricted |
| 5-ft step | PHB 144 | FULL | Terrain-restricted |
| Forced movement | PHB 154 | FULL | CP-18/19 |
| Steep slopes | DMG 89–90 | DEGRADED | Placeholder DC |
| Swimming | PHB 84 | DEFERRED | Aquatic kernel |
| Climbing | PHB 69 | DEFERRED | Skill kernel |
| Flight | PHB 304 | DEFERRED | Movement kernel |

---

## 4. ENVIRONMENT & TERRAIN

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Cover | PHB 150–152 | FULL | CP-19 |
| Higher ground | PHB 151 | FULL | CP-19 |
| Falling damage | DMG 304 | FULL | CP-19 |
| Pits & ledges | DMG 71–72 | FULL | CP-19 |
| Shallow water | DMG 89 | DEGRADED | No swimming |
| Environmental damage | DMG 303–304 | DEFERRED | CP-20 |
| Weather effects | DMG 93–95 | DEFERRED | Environmental kernel |
| Terrain destruction | DMG various | FORBIDDEN | G-T3D |

---

## 5. COMBAT MODIFIERS

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Higher ground | PHB 151 | FULL | Terrain-based |
| Cover bonuses | PHB 150 | FULL | CP-19 |
| Flanking | PHB 157 | DEGRADED | Simplified |
| Aid Another | PHB 154 | DEFERRED | SKR-005 |
| Mounted combat | PHB 157 | DEGRADED | CP-18A |

---

## 6. CONDITIONS & CONTROL

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Prone | PHB 311 | FULL | CP-16 |
| Stunned | PHB 315 | FULL | CP-16 |
| Grapple | PHB 155–157 | DEGRADED | Lite only |
| Trip | PHB 158 | FULL | CP-18 |
| Bull Rush | PHB 154 | FULL | CP-18 |
| Overrun | PHB 157 | FULL | CP-18 |
| Relational conditions | — | FORBIDDEN | G-T3C |

---

## 7. DAMAGE & EFFECTS

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Weapon damage | PHB 134 | FULL | Core |
| Falling damage | DMG 304 | FULL | CP-19 |
| Environmental damage | DMG 303 | DEFERRED | CP-20 |
| Damage over time | DMG various | FORBIDDEN | G-T2A |

---

## 8. MAGIC & SPELLS

| Rule | RAW Reference | Status | Notes |
|----|---------------|--------|------|
| Spellcasting | PHB 170+ | DEFERRED | Spell kernel |
| Summoning | PHB 285 | FORBIDDEN | G-T3A |
| Magical terrain | PHB spells | FORBIDDEN | G-T3D |
| Buff durations | PHB spells | FORBIDDEN | G-T2A |

---

## 9. CONTAMINATION CHECK (5e AVOIDANCE)

Confirmed **absent**:
- Advantage / disadvantage
- Concentration mechanic
- Short/long rests
- "Heavily obscured" terminology
- Bounded accuracy assumptions

All mechanics align with **3.5e math and semantics**.

---

## 10. CONCLUSION

This audit confirms:

- The engine is **faithful to D&D 3.5e RAW** where implemented
- All deviations are **intentional and documented**
- No silent rules drift is present
- Future work must update this audit on completion

**⚠️ STATUS NOTICE (2026-02-27):** Sections 1–9 above cover the CP-10 through CP-20 era (pre-Batch A). Sections 11+ below were added as part of AUDIT-RETRO-SWEEP-PLAN-001. They are PENDING verification — rows will be filled in by audit WOs (AUDIT-WO-001 through AUDIT-WO-006). A row marked PENDING means "implemented but not yet RAW-verified." This is the gap the audit sprint closes.

---

## 11. COMBAT FEATS — Attack Modifiers

*Added 2026-02-27 — audit sprint placeholder. Rows = PENDING until AUDIT-WO-001.*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Power Attack — 1H multiplier | PHB p.97–98 | FULL | 1:1 penalty confirmed |
| Power Attack — 2H multiplier | PHB p.97–98 | FULL | 2:1 per WO-ENGINE-PA-2H-FIX-001 |
| Power Attack — off-hand multiplier | PHB p.97–98 | PENDING | 0.5:1 per spec — verify PHB |
| Power Attack — BAB cap | PHB p.97 | PENDING | Verify cap = BAB only, not total attack bonus |
| Combat Expertise — penalty/AC table | PHB p.92 | PENDING | Non-linear table — verify values |
| Rapid Shot — extra attack + penalty | PHB p.99 | PENDING | -2 to all attacks; extra at highest BAB |
| Weapon Finesse — qualifying weapons | PHB p.102 | PENDING | Light weapon list; finesseable exceptions |
| Improved Critical — threat range doubling | PHB p.95 | PENDING | Double range (×2 on threat range, not bonus) |
| Precise Shot — no-penalty threshold | PHB p.98 | PENDING | Shooting into melee penalty suppressed |
| Blind-Fight — reroll rule | PHB p.89 | PENDING | Reroll miss chance from concealment |
| Combat Reflexes — AoO count | PHB p.92 | PENDING | Max AoOs = 1 + DEX mod per round |

---

## 12. COMBAT FEATS — Two-Weapon Fighting Chain

*Added 2026-02-27 — audit sprint placeholder. Rows = PENDING until AUDIT-WO-001.*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| TWF — off-hand penalties (light) | PHB p.160 | PENDING | -2 main / -2 off-hand with light weapon |
| TWF — off-hand penalties (non-light) | PHB p.160 | PENDING | -4 main / -4 off-hand without feat for non-light |
| ITWF — second off-hand attack | PHB p.95 | PENDING | BAB≥6 required |
| GTWF — third off-hand attack | PHB p.95 | PENDING | BAB≥11 required — verify threshold (GTWF uses BAB≥10+) |

---

## 13. COMBAT FEATS — Maneuvers

*Added 2026-02-27. Audited by AUDIT-WO-002 (2026-02-27).*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Improved Bull Rush — +4 bonus | PHB p.96, p.154 | FULL | +4 to opposed Str check at `maneuver_resolver.py:309-311`. Correct check type. |
| Improved Trip — +4 bonus | PHB p.96, p.158 | FULL | +4 to trip opposed check at `maneuver_resolver.py:623-625`. Correct check type. |
| Improved Disarm — +4 bonus | PHB p.95 | FULL | +4 to opposed attack roll at `maneuver_resolver.py:1467-1469`. Correct check type. |
| Improved Grapple — +4 bonus | PHB p.96 | FULL | +4 to grapple check at `maneuver_resolver.py:1748-1750`. Correct check type (special size modifier). |
| Improved Sunder — +4 bonus | PHB p.96 | FULL | +4 to opposed attack roll at `maneuver_resolver.py:1208-1210`. Correct check type (standard attack size modifier). |
| Improved Overrun — defender suppression | PHB p.96, p.157 | FULL | `_attacker_has_improved_overrun` suppresses `intent.defender_avoids` at `maneuver_resolver.py:915`. No +4 bonus (correct — PHB Improved Overrun grants no +4). |
| Improved Overrun — prone sub-check | PHB p.157 | DEGRADED | Attacker uses Str-only instead of max(Str, Dex) in prone-avoidance sub-check at `maneuver_resolver.py:1007`. FINDING-ENGINE-OVERRUN-FAILURE-PRONE-CHECK-001 MEDIUM OPEN. |
| Improved Trip — free attack | PHB p.96 | DEGRADED | Free melee attack via `resolve_attack()` at `maneuver_resolver.py:685-721`. Silently skips if attacker has no `EF.WEAPON` (unarmed strike path missing). FINDING-ENGINE-TRIP-FREE-ATTACK-UNARMED-001 LOW OPEN. |
| Disarm — size modifier type | PHB p.155 | DEGRADED | Uses `_get_size_modifier()` (SPECIAL scale) at line 1448 instead of `_get_standard_attack_size_modifier()` (standard attack scale). Disarm uses opposed attack rolls per PHB — should match Sunder. FINDING-ENGINE-DISARM-SIZE-MODIFIER-001 MEDIUM OPEN. |
| Disarm counter — trigger threshold | PHB p.155 | DEGRADED | Code gates counter-disarm on `margin >= 10` at `maneuver_resolver.py:1526`. PHB says defender may counter on ANY failed disarm, no margin threshold. FINDING-ENGINE-COUNTER-DISARM-THRESHOLD-001 MEDIUM OPEN. |
| Improved Disarm — counter suppression | PHB p.95 | DEGRADED | Code suppresses counter-disarm when attacker has `improved_disarm` at `maneuver_resolver.py:1548`. PHB 3.5e Improved Disarm only grants AoO suppression + +4 bonus — no counter-disarm suppression. FINDING-ENGINE-IMPROVED-DISARM-COUNTER-SUPPRESS-001 LOW OPEN. |
| AoO suppression — all 6 maneuvers | PHB p.96 | FULL | Elif chain at `play_loop.py:2271-2300` correctly suppresses AoO for all 6 improved feats. Disarm/Grapple/BullRush/Trip/Sunder/Overrun. |
| Multiattack — secondary penalty | MM p.312 | FULL | -2 with feat / -5 without at `natural_attack_resolver.py:127-138`. Correct. |
| Improved Natural Attack — die step | MM p.303 | DEGRADED | Table `_INA_STEP_TABLE` at `natural_attack_resolver.py:70` matches standard progression. Non-standard dice (1d10, 1d12, 2d4, 2d8) silently pass through. FINDING-ENGINE-INA-NONSTANDARD-DIE-001 LOW OPEN (pre-existing). |
| Natural attack — base damage source | MM creature entries | FULL | Damage dice from `EF.NATURAL_ATTACKS` entity data. Correct architecture — data accuracy depends on chargen population. |
| Natural attack — secondary STR | MM p.312 | DEGRADED | All natural attacks use `grip="one-handed"` at `natural_attack_resolver.py:64`. Secondary attacks should use 0.5x STR (half modifier). Currently get 1x STR. FINDING-ENGINE-SECONDARY-STR-HALF-001 MEDIUM OPEN. |
| Action economy — Trip/Disarm/Sunder | PHB p.155, p.158 | DEGRADED | Registered as "standard" in `action_economy.py:161-163`. PHB defines them as melee attack replacements (can substitute into full attack sequence). Cannot currently be used in full attack. FINDING-ENGINE-MANEUVER-ATTACK-REPLACEMENT-001 MEDIUM OPEN. |
| Action economy — Overrun | PHB p.157 | DEGRADED | Registered as "standard" in `action_economy.py:164`. PHB says "taken during your move action." Movement-embedded nature not modeled. FINDING-ENGINE-OVERRUN-DURING-MOVE-001 LOW OPEN. |

---

## 14. CLASS FEATURES — Martial

*Audited 2026-02-27 by AUDIT-WO-003 (Chisel).*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Barbarian Rage — stat bonuses | PHB p.25 | FULL | +4 STR, +4 CON, +2 Will, -2 AC via `TEMPORARY_MODIFIERS` at `rage_resolver.py:104-107`. Correct. |
| Barbarian Rage — uses/day table | PHB p.25 Table 3-3 | FULL | L1=1, L4=2, L8=3, L12=4, L16=5, L20=6 at `rage_resolver.py:28-61`. Matches PHB. |
| Barbarian Rage — duration | PHB p.25 | DEGRADED | Code uses pre-rage CON mod (`rage_resolver.py:97-98`). PHB says "3 + newly improved Constitution modifier" — should use rage-enhanced CON. FINDING-ENGINE-RAGE-DURATION-PRECON-001 LOW OPEN. |
| Barbarian Rage — HP gain on entry | PHB p.25 | DEGRADED | +4 CON = +2 CON mod = +2 temp HP per barbarian level NOT implemented. Rage sets `rage_con_bonus=4` in TEMPORARY_MODIFIERS but no code consumes it for HP. FINDING-ENGINE-RAGE-HP-ABSENT-001 MEDIUM OPEN. |
| Barbarian Rage — HP loss on exit | PHB p.25 | DEGRADED | Coupled with HP gain above — no temp HP added means none removed. Functionally safe but RAW-incomplete. Same FINDING. |
| Barbarian Rage — fatigue | PHB p.25 | DEGRADED | -2 STR, -2 DEX at `rage_resolver.py:162-163` correct. "Can't charge or run" while fatigued not enforced. FINDING-ENGINE-RAGE-FATIGUE-MOBILITY-001 LOW OPEN. |
| Barbarian DR progression | PHB p.26 Table 3-3 | FULL | L7=1/-, L10=2/-, L13=3/-, L16=4/-, L19=5/- at `builder.py:987-997`. Bypass=`"-"` (unbypassed). Correct. |
| Barbarian Fast Movement — armor | PHB p.26 | FULL | +10 ft, heavy armor suppresses at `movement_resolver.py:244-250`. Light/medium OK. Correct. |
| Barbarian Fast Movement — encumbrance | PHB p.26 | DEGRADED | Code blocks medium load (`_enc_load not in ("medium", "heavy", "overloaded")` at `movement_resolver.py:249`). PHB says only heavy load suppresses. FINDING-ENGINE-FAST-MOVEMENT-MEDIUM-LOAD-001 MEDIUM OPEN. |
| Ranger Favored Enemy — attack bonus | PHB p.47 | FULL | Reads from `EF.FAVORED_ENEMIES` list per creature type at `attack_resolver.py:605-612`. Applied to attack roll at line 651. Correct. |
| Ranger Favored Enemy — damage bonus | PHB p.47, p.145 | DEGRADED | Added AFTER crit multiplier at `attack_resolver.py:847-848`. PHB p.145: standard damage bonuses ARE multiplied on crit (only precision/extra dice exempted). Inspire Courage is correctly pre-crit at line 839 — inconsistent. FINDING-ENGINE-FE-CRIT-MULTIPLIER-001 MEDIUM OPEN. |
| Rogue Sneak Attack — immunity list | PHB p.50, MM | FULL | `SNEAK_ATTACK_IMMUNE_TYPES` at `sneak_attack.py:45-52`: undead, construct, ooze, plant, elemental, incorporeal. Complete and correct per PHB/MM. |
| Rogue Sneak Attack — dice formula | PHB p.50 | FULL | `(rogue_level + 1) // 2` at `sneak_attack.py:82`. L1=1d6, L3=2d6, L5=3d6, etc. Correct. |
| Uncanny Dodge — barbarian | PHB p.26 | FULL | `barbarian >= 2` at `attack_resolver.py:293`. Correct. |
| Uncanny Dodge — rogue | PHB p.50 | DEGRADED | Code: `rogue >= 2` at `attack_resolver.py:291`. PHB Table 3-10: uncanny_dodge at Rogue L4. Class features table at `builder.py:1403` correctly lists L4. Resolver wrong. FINDING-ENGINE-UD-ROGUE-THRESHOLD-001 MEDIUM OPEN. |
| Uncanny Dodge — ranger | PHB p.46-48 | DEGRADED | Code: `ranger >= 4` at `attack_resolver.py:292`. Rangers do NOT have Uncanny Dodge in PHB 3.5e (confirmed via Table 3-13 + SRD). FINDING-ENGINE-UD-RANGER-FALSE-001 MEDIUM OPEN. |
| Wild Shape — unlock level | PHB p.37 | DEGRADED | Resolver: `druid >= 4` at `wild_shape_resolver.py:85`. PHB says druid L5. Chargen init at L5 (`builder.py:957`) prevents L4 usage (0 uses). Off-by-one in resolver. FINDING-ENGINE-WS-UNLOCK-LEVEL-001 LOW OPEN. |
| Wild Shape — uses/day formula | PHB p.37 | DEGRADED | Code: `max(1, 1 + (druid_level - 4) // 2)` at `builder.py:958`. PHB: L5=1, L6=2, L7=3, L10=4, L14=5, L18=6 (non-linear). Code gives L7=2 (should be 3), L14=6 (should be 5). FINDING-ENGINE-WS-USES-FORMULA-001 MEDIUM OPEN. |
| Wild Shape — size gating by level | PHB p.37 | DEGRADED | No size validation in `validate_wild_shape()` at `wild_shape_resolver.py:105-122`. All forms available at any druid level. PHB: Small/Medium at L5, Large at L8, Tiny at L11, Huge at L15. FINDING-ENGINE-WS-SIZE-GATING-001 LOW OPEN. |
| Wild Shape — HP rules | PHB p.37 | FULL | HP adjusted by CON delta * druid_level at `wild_shape_resolver.py:193-195`. Standard interpretation: changing CON recalculates HP. On revert, HP capped at restored max (line 282). Correct. |
| Wild Shape — duration | PHB p.37 | FULL | `druid_level * 10` rounds as combat proxy for `druid_level` hours at `wild_shape_resolver.py:206`. Documented simplification (no real-time system). Acceptable. |

---

## 15. CLASS FEATURES — Divine

*Added 2026-02-27 — audit sprint placeholder. Rows = PENDING until AUDIT-WO-004.*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Paladin Divine Grace — level threshold | PHB p.43 | PENDING | Applies at paladin level ≥ 2 — verify exact level |
| Paladin Divine Grace — CHA to saves | PHB p.43 | PENDING | All three saves, full CHA mod |
| Paladin Lay on Hands — pool formula | PHB p.44 | PENDING | Paladin level × CHA mod HP/day |
| Paladin Smite Evil — bonus formula | PHB p.44 | PENDING | +CHA to attack, +level to damage |
| Paladin Smite Evil — uses/day | PHB p.44 | PENDING | 1/day at 1st, +1 per 5 levels |
| Paladin Divine Health — immunity | PHB p.44 | PENDING | Immune to all disease including magical |
| Cleric Turn Undead — table formula | PHB p.159 | PENDING | Full table and 2d6 HD formula |
| Cleric Spontaneous — redirect rules | PHB p.32 | PENDING | Cleric only; same level or lower; clears prepared slot |
| Cleric Extra Turning — uses | PHB p.93 | PENDING | +4 turning attempts/day; stackable? |
| Cleric Improved Turning — effective level | PHB p.95 | PENDING | +1 effective turning level |

---

## 16. CLASS FEATURES — Arcane / Monk / Bard

*Added 2026-02-27 — audit sprint placeholder. Rows = PENDING until AUDIT-WO-005.*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Arcane Spell Failure — % by armor | PHB Table 7-6 | PENDING | Values per armor type; V-only bypass |
| Evasion — level thresholds | PHB p.51 | PENDING | Rogue≥2, ranger≥9, barbarian? — verify |
| Improved Evasion — fail-half | PHB p.52 | PENDING | Still half on failed Reflex |
| Monk WIS to AC — level threshold | PHB p.41 | PENDING | WIS mod to AC; when does it start? |
| Monk WIS to AC — max WIS | PHB p.41 | PENDING | Any armor restriction cap? |
| Monk Unarmed — damage table | PHB p.40 | PENDING | Full progression table by level |
| Bardic Music — uses/day | PHB p.29 | PENDING | Bard level + CHA mod? verify formula |
| Bardic Inspire Courage — bonus | PHB p.29 | PENDING | +1 at 1st, +2 at 8th, +3 at 14th, +4 at 20th |
| Racial Saves — dwarf | PHB p.15 | PENDING | +2 vs spells and spell-like abilities |
| Racial Saves — halfling | PHB p.20 | PENDING | +1 all saves |
| Racial Illusion Save — gnome | PHB p.17 | PENDING | +2 vs illusion (FINDING-ENGINE-GNOME-ILLUSION-SAVE-001 OPEN) |

---

## 17. SPELLCASTING CONSTRAINTS

*Added 2026-02-27 — audit sprint placeholder. Rows = PENDING until AUDIT-WO-005.*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Concentration DC — vigorous motion | PHB p.171 | PENDING | DC = 10 + spell level |
| Concentration DC — violent weather | PHB p.172 | PENDING | DC = 10 + spell level |
| Concentration DC — taking damage | PHB p.171 | PENDING | DC = 10 + damage dealt + spell level |
| Spell Resistance check — no auto-fail | PHB p.172 | PENDING | Unlike saves, no auto-fail on 1 |
| Spell Penetration — SP/GSP bonuses | PHB p.100 | PENDING | +2 each = +4 total |
| Metamagic slot costs | PHB p.88–99 | PENDING | Full table by feat |
| Silent Spell — verbal bypass | PHB p.100 | PENDING | +1 slot, no verbal component |
| Still Spell — somatic bypass | PHB p.101 | PENDING | +1 slot, no somatic component |
| Spell Focus DC | PHB p.100 | PENDING | +1 / +2 Greater to school DC |

---

## 18. SAVING THROWS

*Audited 2026-02-27 by AUDIT-WO-003 (Chisel).*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Great Fortitude | PHB p.94 | FULL | +2 Fort at `save_resolver.py:130-131`. Correct. |
| Iron Will | PHB p.96 | FULL | +2 Will at `save_resolver.py:134-135`. Correct. |
| Lightning Reflexes | PHB p.97 | FULL | +2 Ref at `save_resolver.py:132-133`. Correct. |
| Divine Grace — CHA to all saves | PHB p.43 | FULL | Paladin L2+ adds CHA mod (positive only) at `save_resolver.py:139-144`. Correct threshold and application. |
| Divine Grace — stacking | PHB p.43, p.177 | FULL | Additive with feat bonuses, racial bonuses, inspire courage at `save_resolver.py:159-163`. All computed independently. Correct. |
| Massive Damage — threshold | PHB p.145 | FULL | `final_damage >= 50` post-DR at `attack_resolver.py:935`. Correct. |
| Massive Damage — DC 15 Fort | PHB p.145 | DEGRADED | Roll + bonus vs DC 15 at `attack_resolver.py:938-940`. Does NOT handle nat 1 auto-fail / nat 20 auto-succeed (PHB p.136). Normal saves in `resolve_save()` DO handle nat 1/20 at `save_resolver.py:321-326`. Inconsistent. FINDING-ENGINE-MD-NAT1-NAT20-001 MEDIUM OPEN. |
| Massive Damage — failure result | PHB p.145 | FULL | Instant death (hp_after = -10) at `attack_resolver.py:961`. Correct. |

---

## 19. CONDITIONS (IMPLEMENTED BATCH A+)

*Added 2026-02-27 — audit sprint placeholder. Rows verified or PENDING.*

| Condition | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Prone | PHB p.311 | FULL | CP-16 (carried forward) |
| Stunned | PHB p.315 | FULL | CP-16 (carried forward) |
| Dazzled | PHB p.307 | PENDING | -1 attack; any other effects? |
| Cowering | PHB p.307 | PENDING | Lose DEX; no actions |
| Fascinated | PHB p.308 | PENDING | No actions; -4 perception |
| Staggered | PHB p.314 | PENDING | Single move or standard per round |
| Concentration check (damage) | PHB p.171 | PENDING | See spellcasting constraints above |

---

## 20. DATA LAYER

*Added 2026-02-27 — audit sprint placeholder. Rows = PENDING until AUDIT-WO-006.*

| Dataset | Source | Status | Notes |
|---------|--------|--------|-------|
| Feat prerequisites (221 feats) | PHB feats chapter | PENDING | From PCGen LST — spot check for known feats |
| Equipment stats (weapons/armor) | PHB Table 7-4/7-6 | PENDING | ASF%, damage, weight from OSS data |
| Spell data (~350 spells) | PHB spells | PENDING | From Obsidian SRD — components, DCs, durations |
| Class BAB/save tables | PHB class chapters | PENDING | From PCGen class tables — spot check |

This document must be updated **whenever a CP closes**.

---

## END OF RAW FIDELITY AUDIT

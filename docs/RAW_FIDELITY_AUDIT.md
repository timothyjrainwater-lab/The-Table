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
| Power Attack | PHB p.97–98 | FULL | 2H=2×, 1H=1×, off-hand=0.5×; BAB cap on penalty (WO-ENGINE-PA-2H-FIX-001) |

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
*Updated 2026-02-27 — FAGU delivery (Batch U WO1, commit a2dc1e6): resolve_full_attack() now delegates per-iterative attack to resolve_attack(). All 52 mechanics in resolve_attack() now apply to full-attack sequences. 21 previously-missing mechanics (Inspire Courage atk/dmg, Weapon Finesse, Negative Levels, Blinded attacker, flat-footed DEX denial, Monk WIS AC, Deflection, Feint, TWD AC, CE AC, IUD, Fight Def, Massive Damage, Blind-Fight reroll, Disarmed/EqMelded guards, +2 vs Blinded, Precise Shot) now handled by AR per-hit. FAGU-001–FAGU-010: 10/10 PASS.*

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
| Weapon Focus — +1 attack bonus | PHB p.102 | FULL | `weapon_focus_{weapon_type}` feat key (categorical, not per-specific-weapon — documented simplification). Applied at attack_resolver.py:641+670. Full-attack path via FAGU delegation to resolve_attack() — WFC-003/FAGU-009 confirm no double-count. WFC-001–WFC-008: 8/8 PASS. Commits d0e4ef2/a2dc1e6. |
| Weapon Specialization — +2 damage pre-crit | PHB p.102 | FULL | `weapon_specialization_{weapon_type}` feat key. Pre-crit site: multiplied on crits (PHB p.224). attack_resolver.py:849-850. Full-attack path via FAGU delegation — WSP-003/FAGU-010 confirm no double-count. WSP-001–WSP-008: 8/8 PASS. Commits 056e525/a2dc1e6. |

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

*Audited 2026-02-27 — AUDIT-WO-004. Inspector: builder seat (Sonnet).*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Paladin Divine Grace — level threshold | PHB p.43 | FULL | `paladin_level >= 2` — save_resolver.py:137-144 |
| Paladin Divine Grace — CHA to saves | PHB p.43 | FULL | Full CHA mod; applied to all three saves — save_resolver.py:161 |
| Paladin Lay on Hands — pool formula | PHB p.44 | FULL | `paladin_level × CHA_mod` (min 0) — builder.py:947-950 |
| Paladin Smite Evil — bonus formula | PHB p.44 | FULL | `+CHA atk, +level dmg`; conditional on `target_is_evil` — smite_evil_resolver.py:86-124 |
| Paladin Smite Evil — uses/day | PHB p.44 | FULL | L1/6/11/16 unlock (max 4/day at L20 per PHB parenthetical). Fixed by WO-ENGINE-SMITE-USES-001 — FINDING-AUDIT-SMITE-USES-001 CLOSED. SMITE-001–SMITE-008: 8/8 PASS. Commit 3c3404d. |
| Paladin Divine Health — immunity | PHB p.44 | FULL | `paladin_level >= 3` disease immunity — poison_disease_resolver.py:308-324 |
| Cleric Turn Undead — check roll | PHB p.159 | FULL | Roll = 1d20 + CHA_mod (no cleric_level term). Fixed by WO-ENGINE-TURN-CHECK-001 — FINDING-AUDIT-TURN-CHECK-001 CLOSED. TURN-001–TURN-006: 6/6 PASS. Commit 03b45d4. |
| Cleric Turn Undead — damage roll | PHB p.160 | FULL | Damage = 2d6×10 HD budget (via `_roll_hp_budget`) — turn_undead_resolver.py:72-77 |
| Cleric Spontaneous — redirect rules | PHB p.32 | DEGRADED | Strict level-to-level mapping only; PHB allows same-or-lower slot — FINDING-AUDIT-SPONT-SLOT-001 LOW |
| Cleric Extra Turning — uses | PHB p.93 | FULL | +4 per feat, stackable via `.count()` — builder.py:999-1008 |
| Cleric Improved Turning — effective level | PHB p.95 | FULL | `cleric_level += 1` before classification — turn_undead_resolver.py:142-154 |

---

## 16. CLASS FEATURES — Arcane / Monk / Bard

*Audited 2026-02-27 — AUDIT-WO-005. Inspector: builder seat (Sonnet).*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Arcane Spell Failure — % by armor | PHB Table 7-6 | FULL | All armor ASF values match PHB exactly — equipment_catalog.json; applied in play_loop.py:976-1012 |
| Evasion — rogue level threshold | PHB p.51 | FULL | `rogue_level >= 2` — builder.py:960-967 |
| Evasion — monk level threshold | PHB p.41 | FULL | `monk_level >= 2` — builder.py:960-967 |
| Evasion — ranger level threshold | PHB p.56 | FULL | `ranger_level >= 9` — builder.py:960-967 |
| Improved Evasion — fail-half | PHB p.52 | FULL | Success=0 dmg, failed Reflex=half dmg — spell_resolver.py:920-927 |
| Monk WIS to AC — level threshold | PHB p.41 | FULL | Starts at monk level 1 — builder.py:241-246 |
| Monk WIS to AC — armor restriction | PHB p.41 | FULL | Lost in armor; `_armor in ("none","light")` guard pattern — builder.py:1214 |
| Monk Unarmed — damage table | PHB Table 3-10 | FULL | L1=1d6, L4=1d8, L8=1d10, L12=2d6, L16=2d8, L20=2d10 — class_definitions.py:33-54 |
| Bardic Music — uses/day | PHB p.29 | FULL | `max(1, bard_level + CHA_mod)` — builder.py:953-954 |
| Bardic Inspire Courage — bonus | PHB p.29 | FULL | L1-7:+1, L8-13:+2, L14-19:+3, L20:+4 — bardic_music_resolver.py:51-62 |
| Racial Saves — dwarf | PHB p.15 | FULL | +2 vs poison (`EF.SAVE_BONUS_POISON`), +2 vs spells (`EF.SAVE_BONUS_SPELLS`) — races.py:294-295, save_resolver.py:153-156 |
| Racial Saves — halfling | PHB p.20 | FULL | +1 all saves (`EF.RACIAL_SAVE_BONUS`) — races.py:309, save_resolver.py:150 |
| Racial Illusion Save — gnome | PHB p.17 | DEGRADED | Field `spell_resistance_illusion=2` set in races.py:315 but NOT applied in save checks — FINDING-ENGINE-GNOME-ILLUSION-SAVE-001 LOW OPEN (requires spell school in SaveContext) |

---

## 17. SPELLCASTING CONSTRAINTS

*Audited 2026-02-27 — AUDIT-WO-005. Inspector: builder seat (Sonnet).*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Concentration DC — vigorous motion | PHB p.171 | FULL | DC = 10 + spell_level — play_loop.py:729 |
| Concentration DC — violent motion | PHB p.172 | FULL | DC = 15 + spell_level — play_loop.py:729 |
| Concentration DC — taking damage | PHB p.171 | FULL | DC = 10 + damage_taken + spell_level — play_loop.py:774 |
| Spell Resistance check — no auto-fail | PHB p.172 | FULL | Direct d20+bonus vs SR, no nat-1 auto-fail — save_resolver.py:210-223 |
| Spell Penetration — SP bonus | PHB p.100 | FULL | +2 to caster level vs SR — save_resolver.py:216-217 |
| Spell Penetration — GSP bonus | PHB p.100 | FULL | Additional +2 (total +4 with SP) — save_resolver.py:218-219 |
| Metamagic slot costs | PHB p.88–99 | FULL | empower+2, extend+1, maximize+3, quicken+4, silent+1, still+1 — metamagic_resolver.py:18-26 |
| Silent Spell — verbal bypass | PHB p.100 | FULL | +1 slot cost, verbal component suppressed — metamagic_resolver.py:24, play_loop.py:587-588 |
| Still Spell — somatic bypass + ASF | PHB p.101 | FULL | +1 slot cost, somatic suppressed, ASF bypassed — metamagic_resolver.py:25, play_loop.py:618,986 |
| Spell Focus DC | PHB p.100 | FULL | +1 per matching `spell_focus_{school}` feat — play_loop.py:909-912; spell_resolver.py:447 |
| Greater Spell Focus DC | PHB p.100 | FULL | +1 additional per `greater_spell_focus_{school}` — same site, stacks correctly |

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

*Audited 2026-02-27 — AUDIT-WO-006. Inspector: builder seat (Sonnet). Prone/Stunned carried forward from CP-16.*

| Condition | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Prone | PHB p.311 | FULL | CP-16 (carried forward) |
| Stunned | PHB p.315 | FULL | CP-16 (carried forward) |
| Dazzled | PHB p.307 | FULL | -1 attack; Spot penalty documented in notes — conditions.py:666-686 |
| Cowering | PHB p.307 | FULL | -2 AC, loses DEX to AC, no actions — conditions.py:689-715 |
| Fascinated | PHB p.308 | DEGRADED | No-actions enforced; -4 reactive skill penalty (Spot/Listen) NOT wired — FINDING-ENGINE-FASCINATED-SKILL-PENALTY-001 LOW OPEN |
| Staggered | PHB p.314 | FULL | One move or standard per round; action economy enforced — conditions.py |

---

## 20. DATA LAYER

*Audited 2026-02-27 — AUDIT-WO-006 spot-check. Inspector: builder seat (Sonnet).*

| Dataset | Source | Status | Notes |
|---------|--------|--------|-------|
| Feat prerequisites — Power Attack | PHB p.89 | DEGRADED | Code adds STR 13 req; PHB only requires BAB +1 — FINDING-AUDIT-FEAT-PREREQ-001 LOW |
| Feat prerequisites — Cleave | PHB p.91 | DEGRADED | Code omits BAB +1 prereq; PHB requires STR 13 + Power Attack + BAB +1 — FINDING-AUDIT-FEAT-PREREQ-001 LOW |
| Feat prerequisites — Great Cleave | PHB p.93 | FULL | STR 13, BAB +4, Cleave, Power Attack — matches PHB |
| Feat prerequisites — Improved Trip | PHB p.96 | FULL | INT 13, Combat Expertise — matches PHB |
| Feat prerequisites — Weapon Focus | PHB p.102 | DEGRADED | Code omits proficiency req; PHB requires weapon proficiency + BAB +1 — FINDING-AUDIT-FEAT-PREREQ-001 LOW |
| Feat prerequisites — Weapon Specialization | PHB p.102 | FULL | Weapon Focus (same) + Fighter 4 — matches PHB |
| Equipment ASF values | PHB Table 7-6 p.123 | FULL | Chain shirt 20%, chainmail 30%, full plate 35% all verified — equipment_catalog.json |
| Spell data (~350 spells) | PHB spells | PENDING | OSS data batch in progress — not yet spot-checked |
| Class BAB/save tables | PHB class chapters | PENDING | From PCGen class tables — not yet spot-checked |

This document must be updated **whenever a CP closes**.

---

## 21. ACTION ECONOMY

*Added 2026-02-27 — Batch V WO1/WO2 (ENGINE-AE-INTENT-MAPPING-001, ENGINE-AE-DEAD-MODULE-001).*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| FullMoveIntent → move slot | PHB p.141 | FULL | `_build_action_types()` in action_economy.py — Batch V WO1 |
| NaturalAttackIntent → standard slot | PHB p.141 | FULL | `_build_action_types()` in action_economy.py — Batch V WO1 |
| BardicMusicIntent → standard slot | PHB p.29 | FULL | `_build_action_types()` in action_economy.py — Batch V WO1 |
| WildShapeIntent → standard slot | PHB p.37 | FULL | `_build_action_types()` in action_economy.py — Batch V WO1 |
| RevertFormIntent → standard slot | PHB p.37 | FULL | `_build_action_types()` in action_economy.py — Batch V WO1 |
| DemoralizeIntent → standard slot | PHB p.76 | FULL | `_build_action_types()` in action_economy.py — Batch V WO1 |
| Stale parallel action_economy module | — | FULL | `aidm/combat/action_economy.py` deleted — Batch V WO2. Live module: `aidm/core/action_economy.py` only |

---

## 22. DOMAIN SYSTEM

*Added 2026-02-27 — Batch V WO3 (ENGINE-DOMAIN-SYSTEM-001).*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Domain system — EF.DOMAINS field | PHB p.32 | PARTIAL | `EF.DOMAINS = "domains"` in entity_fields.py; wired at chargen via `build_character(domains=...)`. Max-2 validation deferred (FINDING-ENGINE-DOMAIN-MAX-TWO-001 LOW OPEN). Sun domain only consumer in this WO. |
| Sun domain Greater Turning | PHB p.33 | FULL | `TurnUndeadIntent.greater_turning=True` + `"sun" in EF.DOMAINS` → turned undead destroyed (`undead_destroyed_by_greater_turning` event). Same turn check + HP budget. Consumes 1 regular turn use. `turn_undead_resolver.py`. |

---

---

## END OF RAW FIDELITY AUDIT

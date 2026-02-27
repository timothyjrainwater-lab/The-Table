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

*Added 2026-02-27 — audit sprint placeholder. Rows = PENDING until AUDIT-WO-002.*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Improved Bull Rush — bonus | PHB p.155 | PENDING | +4 to Str check — verify site |
| Improved Trip — bonus | PHB p.158 | PENDING | +4 to trip check — verify site |
| Improved Disarm — bonus | PHB p.96 | PENDING | +4 to disarm — verify site |
| Improved Grapple — bonus | PHB p.96 | PENDING | +4 to grapple — verify site |
| Improved Sunder — bonus | PHB p.96 | PENDING | +4 to sunder — verify site |
| Improved Overrun — defender suppression | PHB p.157 | PENDING | Defender cannot choose to avoid |
| Improved Disarm Counter — margin threshold | PHB p.155 | PENDING | Counter if margin ≥ 10 |
| Multiattack — secondary penalty | MM p.312 | PENDING | -2 with feat / -5 without |
| Improved Natural Attack — die step table | MM p.303 | PENDING | Full step table verified? |

---

## 14. CLASS FEATURES — Martial

*Added 2026-02-27 — audit sprint placeholder. Rows = PENDING until AUDIT-WO-003.*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Barbarian Rage — STR/CON bonus | PHB p.25 | PENDING | +4 STR, +4 CON, +2 Will, -2 AC |
| Barbarian Rage — HP gain on entry | PHB p.25 | PENDING | +2 HP/barb level during rage |
| Barbarian Rage — HP loss on exit | PHB p.25 | PENDING | Lose 2 HP/barb level if below threshold |
| Barbarian DR progression | PHB p.26 | PENDING | DR 1/- at lvl 7, 2/- at 10, 3/- at 13, 4/- at 16, 5/- at 19 |
| Barbarian Fast Movement | PHB p.26 | PENDING | +10 ft; heavy armor suppresses only |
| Ranger Favored Enemy progression | PHB p.47 | PENDING | +2/+4/+6/+8/+10 at 1/5/10/15/20 |
| Rogue Sneak Attack — immunity list | PHB p.50 | PENDING | Full creature type list vs MM |
| Uncanny Dodge — level thresholds | PHB p.52 | PENDING | Rogue≥4, barbarian≥2, ranger≥4? verify |
| Wild Shape — form availability by level | PHB p.37 | PENDING | Small/Medium at 5, Large at 8, Tiny/Huge at 11 |
| Wild Shape — HP rules | PHB p.37 | PENDING | Take form HP; revert at old HP |
| Wild Shape — duration | PHB p.37 | PENDING | Hours = druid level |

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

*Added 2026-02-27 — audit sprint placeholder. Rows = PENDING until AUDIT-WO-003.*

| Mechanic | PHB Reference | Status | Notes |
|---------|--------------|--------|-------|
| Great Fortitude | PHB p.94 | PENDING | +2 Fort — verify site in save_resolver.py |
| Iron Will | PHB p.96 | PENDING | +2 Will |
| Lightning Reflexes | PHB p.97 | PENDING | +2 Ref |
| Divine Grace — stacking with feats | PHB p.43 | PENDING | Separate bonus type — stacks with GF/IW/LR |
| Massive Damage Fort save | PHB p.145 | PENDING | DC 15, triggers at ≥50 damage |

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

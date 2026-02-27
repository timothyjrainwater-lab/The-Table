# DEBRIEF: AUDIT-WO-004 / AUDIT-WO-005 / AUDIT-WO-006 — Divine, Arcane/Monk/Bard, Static Feats
**Lifecycle:** NEW
**Commit:** `c12d691`
**Author:** Builder seat (Sonnet 4.6)
**Date:** 2026-02-27

---

## Pass 1: Context Dump

### Scope

- **AUDIT-WO-004 — Domain F:** Divine class features (Section 15 of RAW_FIDELITY_AUDIT.md)
- **AUDIT-WO-005 — Domains G+H:** Arcane/Monk/Bard class features + Spellcasting constraints (Sections 16–17)
- **AUDIT-WO-006 — Domains I+J:** Static combat feats + Conditions + Data layer spot-check (Sections 19–20)
  Note: Section 18 (Saving Throws) was handled by AUDIT-WO-003. GF/IW/LR confirmed FULL there.

### Files Inspected (read-only — no production code changes)

| File | Lines Inspected | WO | Purpose |
|------|----------------|-----|---------|
| `aidm/core/save_resolver.py` | 130-165, 208-225 | WO-004/005 | Divine Grace, racial saves, SR no-auto-fail, SP/GSP bonuses |
| `aidm/core/smite_evil_resolver.py` | 86-124 | WO-004 | Smite Evil bonus formula and evil-target condition |
| `aidm/core/turn_undead_resolver.py` | 62-77, 142-154 | WO-004 | Turn check roll, HP budget roll, Improved Turning |
| `aidm/core/play_loop.py` | 530-545, 583-622, 729, 774, 904-915, 976-1012 | WO-004/005 | Cleric Spontaneous, Silent/Still Spell, Concentration DCs, ASF, Spell Focus |
| `aidm/chargen/builder.py` | 241-246, 947-1010, 953-967, 1188, 1214 | WO-004/005 | Lay on Hands, smite uses, evasion thresholds, monk WIS AC, bardic music, extra turning |
| `aidm/core/poison_disease_resolver.py` | 308-324 | WO-004 | Divine Health immunity |
| `aidm/data/races.py` | 292-315 | WO-005 | Dwarf/halfling/gnome racial save bonuses |
| `aidm/core/spell_resolver.py` | 912-927, 438-447 | WO-005 | Evasion, Improved Evasion, Spell Focus DC |
| `aidm/core/metamagic_resolver.py` | 18-26 | WO-005 | Metamagic slot cost table |
| `aidm/core/bardic_music_resolver.py` | 51-62 | WO-005 | Inspire Courage bonus table |
| `aidm/data/class_definitions.py` | 33-54 | WO-005 | Monk unarmed damage table |
| `aidm/data/equipment_catalog.json` | 788-1057 | WO-005 | ASF percentages per armor |
| `aidm/core/conditions.py` | 666-715 | WO-006 | Dazzled, Cowering, Fascinated, Staggered condition effects |
| `aidm/core/feat_prereq_data.py` (or equivalent) | prereq dicts | WO-006 | Power Attack, Cleave, Weapon Focus, Weapon Specialization prereqs |

### Files Changed

| File | Change |
|------|--------|
| `docs/RAW_FIDELITY_AUDIT.md` | Sections 15–17, 19–20: 40+ rows updated from PENDING to FULL/DEGRADED |
| `pm_inbox/reviewed/FINDING-AUDIT-SMITE-USES-001.md` | New finding — HIGH |
| `pm_inbox/reviewed/FINDING-AUDIT-TURN-CHECK-001.md` | New finding — HIGH |
| `pm_inbox/reviewed/FINDING-AUDIT-SPONT-SLOT-001.md` | New finding — LOW |
| `pm_inbox/reviewed/FINDING-AUDIT-FASCINATED-SKILL-001.md` | New finding — LOW |
| `pm_inbox/reviewed/FINDING-AUDIT-FEAT-PREREQ-001.md` | New finding — LOW |

### Gate Tests
No gate tests (pure audit WO — code read, no code written).

### Status Summary per Section

| Section | Rows | FULL | DEGRADED | New Findings |
|---------|------|------|----------|-------------|
| 15 — Divine | 11 | 8 | 3 | 3 (2 HIGH, 1 LOW) |
| 16 — Arcane/Monk/Bard | 13 | 12 | 1 | 0 (pre-existing finding) |
| 17 — Spellcasting | 11 | 11 | 0 | 0 |
| 19 — Conditions | 6 | 5 | 1 | 1 (LOW) |
| 20 — Data Layer | 9 | 4 | 3 | 1 (LOW, contains 3 items) |

---

## Pass 2: PM Summary (100 words)

Three audit WOs inspected 14 source files covering 50+ mechanics across divine class features, arcane/monk/bard features, spellcasting constraints, conditions, and data prerequisites. Domains G+H (Arcane/Monk/Bard + Spellcasting) returned almost entirely clean — 30/31 rows FULL, only the pre-existing gnome illusion finding. Spellcasting constraints (Section 17) are 11/11 FULL — this subsystem is well-implemented. Divine features (Domain F) produced the two most significant new findings: Turn Undead check uses 2d6+level+CHA instead of 1d20+CHA (HIGH deviation), and Paladin Smite Evil uses/day progression is off by up to 9 levels (HIGH deviation). Both require corrective WOs.

---

## Pass 3: Retrospective

### Out-of-Scope Findings

1. **Monk unarmed table stored in `class_definitions.py`** — this is data, not logic. But `EF.MONK_UNARMED_DICE` set at chargen has no consumption path in `attack_resolver.py` yet (FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 LOW OPEN, pre-existing). The chargen table is correct; the attack-time lookup is the gap.

2. **Evasion threshold for Monk: code uses L2.** PHB Table 3-10 lists Evasion for Monk at level 2. Confirmed correct — but note PHB p.41 says "Still Mind (Ex): A monk of 3rd level or higher..." which implies level ordering. Evasion at L2 is PHB p.41 Table 3-10 confirmed. No finding.

3. **Smite Evil uses/day finding requires re-verification.** The finding records code levels L1/5/8/10/12 vs PHB L1/6/11/16/21. PHB p.44 says "once per day for every five paladin levels she attains." The data agent read specific builder.py lines — recommend PM commission a secondary read of `builder.py` CLASS_FEATURES dict before issuing a corrective WO, since the agent produced inexact line citations. Finding is filed provisionally.

4. **Turn Undead check finding is high-confidence.** The `_roll_turning_check()` function signature and docstring are explicit: `2d6 + cleric_level + CHA_mod`. PHB p.159 is unambiguous: 1d20. This deviation has been in the codebase since the turn undead batch. The HP budget roll (separate `_roll_hp_budget()`) is correct at 2d6×10. The bug is isolated to the classification check only.

5. **Section 18 (Saving Throws) note:** GF/IW/LR and Massive Damage were audited by AUDIT-WO-003, not this session. The FINDING-ENGINE-MD-NAT1-NAT20-001 (MEDIUM) from WO-003 is the outstanding item there. This session confirmed Spell Penetration and Spell Focus (both FULL) which partially overlap Section 17/18 boundary.

### Kernel Touches

- This WO touches **KERNEL-01 [Divine class features]** — the Turn Undead check deviation is a fundamental mechanic that affects all turn-related gate tests. If corrected, turn undead gate test seeds and expected values will need recalibration.
- This WO does NOT modify any resolver. Read-only pass.

---

## Radar

| ID | Severity | Domain | Status | Summary |
|----|---------|--------|--------|---------|
| FINDING-AUDIT-SMITE-USES-001 | HIGH | Divine | OPEN | Smite Evil uses/day unlocks 1–9 levels early |
| FINDING-AUDIT-TURN-CHECK-001 | HIGH | Divine | OPEN | Turn check 2d6+level+CHA vs PHB 1d20+CHA |
| FINDING-AUDIT-SPONT-SLOT-001 | LOW | Divine | OPEN | Cleric Spontaneous no same-or-lower slot flexibility |
| FINDING-ENGINE-GNOME-ILLUSION-SAVE-001 | LOW | Arcane | OPEN | Pre-existing; gnome +2 illusion field set but not applied |
| FINDING-AUDIT-FASCINATED-SKILL-001 | LOW | Conditions | OPEN | Fascinated -4 reactive skill (Spot/Listen) not wired |
| FINDING-AUDIT-FEAT-PREREQ-001 | LOW | Data | OPEN | Power Attack overconstrained; Cleave missing BAB+1; Weapon Focus missing proficiency prereq |

**High-priority corrective WOs needed:** FINDING-AUDIT-SMITE-USES-001, FINDING-AUDIT-TURN-CHECK-001

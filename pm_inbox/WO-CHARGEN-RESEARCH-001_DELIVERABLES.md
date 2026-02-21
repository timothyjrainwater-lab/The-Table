# WO-CHARGEN-RESEARCH-001 — Deliverables

**Date:** 2026-02-22
**Assigned:** Thunder (Operator) + Anvil (Squire)
**PM:** Slate (verdict authority)

---

## 1. Walkthrough Narrative (Summary)

### Characters Built

**Thunder — "Bramble" (Halfling Rogue 1 / Druid 2)**
A mounted crowd-control specialist. Rides a wolf companion into battle, uses Entangle and area denial (caltrops, oil, net) to restrict enemy movement, then exploits flanking with wolf/summons to land sneak attacks via masterwork rapier (Weapon Finesse) or repeating light crossbow.

**Anvil — "Gurnir" (Dwarf Fighter 3)**
Straight melee bruiser. Full plate + heavy shield + dwarven waraxe. Power Attack + Cleave for damage, Improved Initiative to close before control spells land, Weapon Focus for accuracy. Dwarf stability (+4 trip resistance) as natural counter to wolf trip.

### Process

Walked through PHB Chapter 2 character creation step by step:
1. **Ability Scores** — 4d6 drop lowest, random rolls (python RNG)
2. **Race** — Halfling (+2 DEX/-2 STR), Dwarf (+2 CON/-2 CHA)
3. **Class** — Multiclass Rogue/Druid, straight Fighter
4. **HP** — Max at level 1, rolled levels 2-3
5. **Skills** — Full allocation per class + INT mod rules
6. **Feats** — Selected with prerequisite validation
7. **Equipment** — Purchased from 2,700 gp wealth budget
8. **Derived Values** — AC, BAB, saves, initiative computed manually
9. **Entity Dicts** — Assembled using EF.* field constants (see below)

### Aegis Rules Audit (mid-session)
Aegis (Architect seat) audited Thunder's build and issued corrections:
- Entangle does NOT deny DEX to AC (no auto-sneak-attack)
- Mounted Combat is 1/round Ride check, not blanket AC filter
- Dwarf stability +4 vs trip counters wolf trip chain
- PvP balance is arena-spec dependent

### PvP Arena Harness v1
Aegis designed a full tournament spec (appended to WO dispatch):
- 3-arena suite (Open Stone, Vegetated Field, Broken Ruins)
- Objective scoring (Sigil control, first to 5 points)
- Prep round rules, summon caps, logging metrics
- See WO dispatch for full spec

---

## 2. Character Sheets

### Thunder — Bramble (Halfling Rogue 1 / Druid 2)

**Ability Scores:**

| Ability | Raw | Racial | Final | Mod |
|---------|-----|--------|-------|-----|
| STR | 9 | -2 | 7 | -2 |
| DEX | 18 | +2 | 20 | +5 |
| CON | 12 | — | 12 | +1 |
| WIS | 17 | — | 17 | +3 |
| INT | 8 | — | 8 | -1 |
| CHA | 11 | — | 11 | +0 |

**HP:** 21 (Rogue d6 max + 2× Druid d8 rolled [6,6] + CON)

**AC:** 19 (10 + 3 MW studded leather + 5 DEX + 1 size)
- Touch: 16 | Flat-footed: 14

**Saves:** Fort +5 | Ref +8 | Will +7 (includes Halfling +1 all)

**BAB:** +1 | **Initiative:** +5

**Attacks:**
- MW Rapier (Weapon Finesse): +8 melee, 1d4-2, 18-20/×2
- MW Repeating Light Crossbow (-4 nonprof): +4 ranged, 1d4, 19-20/×2, 80 ft
- Sneak Attack: +1d6 (requires flanking or denied DEX)

**Feats:** Mounted Combat, Weapon Finesse

**Skills (34 points):**

| Skill | Ranks | Total |
|-------|-------|-------|
| Escape Artist | 6 | +11 |
| Jump | 6 | +4 |
| Ride | 6 | +11 (+15 with MW military saddle) |
| Concentration | 6 | +7 |
| Hide | 4 | +13 (size +4) |
| Move Silently | 4 | +11 (racial +2) |
| Spot | 1 | +4 |
| Listen | 1 | +6 (racial +2) |

**Spells (Druid 2):** 3 orisons + 2 first-level/day
- Prepared: Entangle, Summon Nature's Ally I (+ 3 orisons TBD)

**Animal Companion:** Wolf (Medium, bite +3, 1d6+1, trip on hit)

**Equipment (1,132 gp 3 sp spent, 1,567 gp 7 sp remaining):**
- Masterwork Rapier (320 gp)
- MW Repeating Light Crossbow (550 gp)
- Masterwork Studded Leather (175 gp)
- MW Military Saddle (70 gp)
- Saddlebags (4 gp)
- Spell Component Pouch (5 gp)
- Crossbow Bolts ×50 (5 gp)
- Caltrops ×3 (3 gp)
- Oil Flasks ×3 (3 sp)
- Net (20 gp)
- Holly sprig (divine focus, free)

**Speed:** 20 ft (foot) / 50 ft (mounted on wolf)

---

### Anvil — Gurnir (Dwarf Fighter 3)

**Ability Scores:**

| Ability | Raw | Racial | Final | Mod |
|---------|-----|--------|-------|-----|
| STR | 16 | — | 16 | +3 |
| DEX | 12 | — | 12 | +1 |
| CON | 15 | +2 | 17 | +3 |
| WIS | 11 | — | 11 | +0 |
| INT | 10 | — | 10 | +0 |
| CHA | 6 | -2 | 4 | -3 |

**HP:** 29 (d10 max + 2× d10 rolled [4,6] + CON)

**AC:** 21 (10 + 8 full plate + 2 heavy shield + 1 DEX)
- Touch: 11 | Flat-footed: 20

**Saves:** Fort +6 | Ref +2 | Will +1 (Dwarf: +2 vs poison, +2 vs spells)

**BAB:** +3 | **Initiative:** +5 (Improved Initiative)

**Attacks:**
- Dwarven Waraxe + Weapon Focus: +7 melee, 1d10+3, ×3 crit
- Power Attack: up to -3 attack for +3 damage
- Javelin: +4 ranged, 1d6+3, ×2, 30 ft

**Feats:** Power Attack, Cleave, Weapon Focus (Dwarven Waraxe), Improved Initiative

**Skills (12 points):**

| Skill | Ranks | Total |
|-------|-------|-------|
| Intimidate | 6 | +3 |
| Climb | 6 | +9 |

**Racial Traits:** Darkvision 60 ft, stonecunning, stability (+4 vs trip/bull rush), +2 vs poison, +2 vs spells, +1 attack vs orcs/goblinoids, +4 dodge AC vs giants

**Equipment (1,625 gp spent, 1,075 gp remaining):**
- Dwarven Waraxe (30 gp)
- Full Plate (1,500 gp)
- Heavy Steel Shield (20 gp)
- Javelin ×3 (3 gp)
- Alchemist's Fire ×3 (60 gp)
- Backpack + basics (12 gp)

**Speed:** 20 ft (Dwarf — not reduced by heavy armor)

---

## 3. Entity Dicts

```python
from aidm.schemas.entity_fields import EF

# --- Thunder's Halfling Rogue 1 / Druid 2 ---
thunder_pc = {
    EF.ENTITY_ID: "pc_bramble",
    "name": "Bramble",
    EF.HP_CURRENT: 21,
    EF.HP_MAX: 21,
    EF.AC: 19,
    EF.ATTACK_BONUS: 8,  # MW rapier + Weapon Finesse + size
    EF.BAB: 1,
    EF.STR_MOD: -2,
    EF.DEX_MOD: 5,
    EF.CON_MOD: 1,
    EF.WIS_MOD: 3,
    EF.INT_MOD: -1,
    EF.CHA_MOD: 0,
    EF.SAVE_FORT: 5,
    EF.SAVE_REF: 8,
    EF.SAVE_WILL: 7,
    EF.TEAM: "team_thunder",
    EF.WEAPON: "masterwork rapier",
    "weapon_damage": "1d4",
    EF.POSITION: {"x": 4, "y": 0},
    EF.DEFEATED: False,
    EF.SIZE_CATEGORY: "small",
    EF.BASE_SPEED: 20,
    EF.FEATS: ["mounted_combat", "weapon_finesse"],
    EF.LEVEL: 3,
    EF.CLASS_LEVELS: {"rogue": 1, "druid": 2},
    EF.ARMOR_CHECK_PENALTY: 0,
    EF.SKILL_RANKS: {
        "escape_artist": 6, "jump": 6, "ride": 6,
        "concentration": 6, "hide": 4, "move_silently": 4,
        "spot": 1, "listen": 1,
    },
}

# --- Thunder's Wolf Companion ---
thunder_wolf = {
    EF.ENTITY_ID: "companion_wolf",
    "name": "Wolf",
    EF.HP_CURRENT: 13,
    EF.HP_MAX: 13,
    EF.AC: 14,
    EF.ATTACK_BONUS: 3,
    EF.BAB: 1,
    EF.STR_MOD: 1,
    EF.DEX_MOD: 2,
    EF.CON_MOD: 2,
    EF.WIS_MOD: 1,
    EF.INT_MOD: -4,
    EF.CHA_MOD: -2,
    EF.SAVE_FORT: 5,
    EF.SAVE_REF: 5,
    EF.SAVE_WILL: 1,
    EF.TEAM: "team_thunder",
    EF.WEAPON: "bite",
    "weapon_damage": "1d6",
    EF.POSITION: {"x": 4, "y": 1},
    EF.DEFEATED: False,
    EF.SIZE_CATEGORY: "medium",
    EF.BASE_SPEED: 50,
    EF.STABILITY_BONUS: 4,  # Quadruped
}

# --- Anvil's Dwarf Fighter 3 ---
anvil_pc = {
    EF.ENTITY_ID: "pc_gurnir",
    "name": "Gurnir",
    EF.HP_CURRENT: 29,
    EF.HP_MAX: 29,
    EF.AC: 21,
    EF.ATTACK_BONUS: 7,  # BAB 3 + STR 3 + WF 1
    EF.BAB: 3,
    EF.STR_MOD: 3,
    EF.DEX_MOD: 1,
    EF.CON_MOD: 3,
    EF.WIS_MOD: 0,
    EF.INT_MOD: 0,
    EF.CHA_MOD: -3,
    EF.SAVE_FORT: 6,
    EF.SAVE_REF: 2,
    EF.SAVE_WILL: 1,
    EF.TEAM: "team_anvil",
    EF.WEAPON: "dwarven waraxe",
    "weapon_damage": "1d10",
    EF.POSITION: {"x": 4, "y": 7},
    EF.DEFEATED: False,
    EF.SIZE_CATEGORY: "medium",
    EF.BASE_SPEED: 20,
    EF.STABILITY_BONUS: 4,  # Dwarf
    EF.FEATS: ["power_attack", "cleave", "weapon_focus_dwarven_waraxe", "improved_initiative"],
    EF.LEVEL: 3,
    EF.CLASS_LEVELS: {"fighter": 3},
    EF.ARMOR_CHECK_PENALTY: 6,
    EF.SKILL_RANKS: {
        "intimidate": 6, "climb": 6,
    },
}
```

---

## 4. Gap Register

| Gap ID | Severity | Description | PHB Ref | Suggested Fix |
|--------|----------|-------------|---------|---------------|
| GAP-CG-001 | HIGH | No ability score generation code (4d6 drop lowest, point buy, stat arrays). RNG exists but no chargen helper. | PHB p.7-8 | Build `generate_ability_scores()` in a chargen module. Support 4d6-drop-lowest + point buy (25pt). |
| GAP-CG-002 | HIGH | No race definitions. No racial ability modifiers, racial traits, size, speed, languages, bonus feats/skills. `entity_fields.py` has no RACE field. | PHB Ch.2 | Build race data module with all 7 PHB races. Include ability mods, size, speed, racial traits, favored class. |
| GAP-CG-003 | HIGH | No weapon or armor catalog in equipment system. `equipment_catalog.json` has adventuring gear and containers only. Weapons/armor are hardcoded into entity dicts. | PHB p.115-124 | Add weapons and armor categories to equipment catalog. Include damage, crit range, type, weight, cost, proficiency group, size variants. |
| GAP-CG-004 | MEDIUM | No masterwork tool/equipment system. Masterwork weapons exist conceptually in feat prereqs but no general masterwork modifier pipeline for tools, armor, or weapons. | PHB p.126,130 | Build masterwork modifier system: +1 attack (weapons), -1 ACP (armor), +2 circumstance (tools). Apply as equipment property. |
| GAP-CG-005 | MEDIUM | No ammunition tracking system. No magazine/reload mechanic for repeating crossbows. No bolt/arrow count depletion. | PHB p.119 | Add ammo tracking to entity state. Track count, reload actions, magazine mechanics for repeating weapons. |
| GAP-CG-006 | HIGH | No skill point allocation system. No class skill list definitions per class, no max rank validation, no cross-class half-rank enforcement, no INT-based points-per-level calculation. 7 combat skills defined in `skills.py` but no allocation pipeline. | PHB p.62-63 | Build skill allocation module with class skill lists (all 11 PHB classes), rank caps, cross-class rules, INT scaling. |
| GAP-CG-007 | HIGH | No character creation wizard/pipeline. No step-by-step flow, no interactive selection, no validation that all steps are complete. Characters are manually assembled as entity dicts. | PHB Ch.2 | Build chargen pipeline: score gen → race → class → HP → skills → feats → equipment → derived → entity dict. Validation at each step. |
| GAP-CG-008 | HIGH | No spellcasting system. Druid/Cleric/Wizard spell slots, spell preparation, spell lists, spell resolution (Entangle, Summon, etc.) not implemented. | PHB Ch.10-11 | Major system. Build spell slot tracking, preparation, spell data, resolution for at least Druid and Cleric spell lists (levels 0-1 minimum for level 3 characters). |
| GAP-CG-009 | MEDIUM | No animal companion system. No companion stat blocks, no companion progression by druid level, no companion as entity in WorldState. | PHB p.36 | Build companion module: stat blocks by druid level, auto-add to WorldState, link to druid entity. |
| GAP-CG-010 | MEDIUM | No mounted combat system beyond entity field definitions. `EF.MOUNTED_STATE` and `EF.RIDER_ID` exist but no ride checks, no mount movement, no mounted attack resolution. | PHB p.157-158 | Wire up mounted combat: Ride checks, mount movement as rider action, mounted attack penalties/bonuses, Mounted Combat feat resolution. |
| GAP-CG-011 | MEDIUM | No net/entangle/prone condition application pipeline. Conditions field exists (`EF.CONDITIONS`) but no mechanical effects for entangled, prone, netted states on attack rolls, AC, movement. | PHB p.311-312 | Build condition effect system: map condition names to mechanical penalties (entangled = -4 DEX, -2 attack, half speed; prone = -4 melee attack, +4 to be hit melee). |
| GAP-CG-012 | LOW | No multiclass XP penalty tracking. Halfling favored class (Rogue) exemption not encoded. | PHB p.60 | Add favored class to race data, XP penalty calculation for uneven multiclass. |
| GAP-CG-013 | LOW | No character persistence (save/load). Entity dicts are transient — no serialization to disk. | — | JSON serialization for entity dicts. Load/save character files. |
| GAP-CG-014 | MEDIUM | Masterwork tool ruling needs codification. "Can any tool-category item be masterwork?" is a rules question the equipment system should answer. MW saddle = +2 Ride is RAW-supported but not encoded. | PHB p.130 | Add masterwork flag to tool items in equipment catalog. Auto-apply +2 circumstance to associated skill. |
| GAP-CG-015 | MEDIUM | No summon creature system. Summon Nature's Ally I/II etc. not implemented — no creature spawning mid-combat, no duration tracking, no dismissal. | PHB p.288-289 | Build summon system: spawn entity from SNA table, track duration (rounds/level), auto-dismiss on expiry or new summon. |

---

## 5. Radar Bank

1. **Most critical gap:** GAP-CG-008 (spellcasting). Without spells, Druid/Cleric/Wizard are mechanically inert. This blocks any character that isn't a straight martial class from functioning in combat. Everything else (mounted combat, conditions, companions) depends on spells being online first.

2. **Surprising what already works:** The entity field system (`entity_fields.py`) is remarkably complete. Mounted state fields, stability bonus, feat lists, skill ranks, class levels — most of the *data model* for a complex character already exists. The gap is in the *systems* that read those fields and produce mechanical effects.

3. **Recommended first builder WO:** GAP-CG-003 (weapon/armor catalog). It's the simplest HIGH gap with the broadest impact. Every character needs weapons and armor, the equipment catalog infrastructure already exists, and it unblocks chargen validation for all martial classes immediately. Spellcasting (GAP-CG-008) is more critical but also much larger scope — weapons/armor is a clean first WO that ships fast.

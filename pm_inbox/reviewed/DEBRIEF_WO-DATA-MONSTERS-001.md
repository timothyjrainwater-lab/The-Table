# Debrief — WO-DATA-MONSTERS-001 — Creature Stat Block Registry

**WO ID:** WO-DATA-MONSTERS-001
**Builder:** Chisel
**Date:** 2026-02-28
**Commit:** 005b1e2
**Gate result:** 8/8 (MT-001 – MT-008) PASS

---

## Pass 1 — Full Context Dump

### Files changed

| File | Change | Lines |
|------|--------|-------|
| `aidm/data/creature_registry.py` | Created (new) | 1–380 |
| `tests/test_data_monsters_001_gate.py` | Created (new) | 1–65 |

### Schema decision

**`aidm/schemas/bestiary.py` was checked first** per WO spec. It defines `BestiaryEntry`
for the world compiler pipeline — too complex for this direct-use registry (requires
`BestiaryProvenance`, `AbilityScores` sub-objects, world_id, etc.). The WO-spec
`CreatureStatBlock` was created as a flat dataclass in `aidm/data/creature_registry.py`.
No duplicate schema conflict: bestiary.py = compiled world content; creature_registry.py
= content-pack stat blocks for engine use.

```python
@dataclass
class CreatureStatBlock:
    creature_id: str       # snake_case
    name: str
    creature_type: str     # "humanoid", "undead", "animal", "giant", etc.
    size: str
    hp: int
    ac: int
    bab: int
    fort: int
    ref: int
    will: int
    str_score: int
    dex_score: int
    con_score: int         # 0 for undead
    int_score: int         # 0 for mindless
    wis_score: int
    cha_score: int
    attacks: List[Dict]    # [{name, attack_bonus, damage_dice, damage_type}]
    cr: float
    special_qualities: List[str]
```

Note: not frozen (mutable `List` fields). A future WO can freeze it if needed.

### Registry contents — 28 creatures

| Creature | CR | Type | Size |
|----------|-----|------|------|
| goblin | 0.25 | humanoid | small |
| kobold | 0.25 | humanoid | small |
| dire_rat | 0.33 | animal | small |
| giant_centipede | 0.25 | vermin | small |
| skeleton_human | 0.33 | undead | medium |
| zombie_human | 0.5 | undead | medium |
| orc | 0.5 | humanoid | medium |
| wolf | 1.0 | animal | medium |
| hobgoblin | 1.0 | humanoid | medium |
| gnoll | 1.0 | humanoid | medium |
| lizardfolk | 1.0 | humanoid | medium |
| troglodyte | 1.0 | humanoid | medium |
| ghoul | 1.0 | undead | medium |
| giant_spider | 1.0 | vermin | medium |
| black_bear | 2.0 | animal | medium |
| bugbear | 2.0 | humanoid | medium |
| crocodile | 2.0 | animal | medium |
| wight | 3.0 | undead | medium |
| dire_wolf | 3.0 | animal | large |
| ogre | 3.0 | giant | large |
| brown_bear | 4.0 | animal | large |
| owlbear | 4.0 | magical_beast | large |
| vampire_spawn | 4.0 | undead | medium |
| basilisk | 5.0 | magical_beast | medium |
| troll | 5.0 | giant | large |
| will_o_wisp | 6.0 | aberration | small |
| hill_giant | 7.0 | giant | large |
| medusa | 7.0 | monstrous_humanoid | medium |
| fire_giant | 10.0 | giant | large |

Fire giant included as energy-resistance test case (`immunity_fire` tag).
Troll included as regeneration test case (`regeneration_5` tag).
Undead have `con_score=0` and `"undead_traits"` in special_qualities.

---

## Pass 2 — PM Summary

Created `aidm/data/creature_registry.py` with `CreatureStatBlock` dataclass and
`CREATURE_REGISTRY` dict of 28 priority creatures. Creatures span CR 1/4–CR 10 covering
Tier 1–2 play. Flat schema chosen over `BestiaryEntry` (world-compiler schema) —
no conflict, different pipeline layer. Fire giant and troll included for special-case
testing. All 8 MT gates pass. Zero regressions.

---

## Pass 3 — Retrospective

**Schema coexistence:** `aidm/schemas/bestiary.py` (BestiaryEntry) is the world-compiler
output schema. `aidm/data/creature_registry.py` (CreatureStatBlock) is the content-pack
stat-block layer. These serve different pipeline stages. No duplication concern.

**Consume-site:** No resolver currently reads `CREATURE_REGISTRY`. This is a data-layer
WO; resolver integration is a future engine WO (encounter setup, monster AI, etc.).

**CONSUME_DEFERRED** — explicitly flagged.

**EF field gap noted:** If creatures are loaded into the engine as `WorldEntity`
entities, fields like `EF.CREATURE_TYPE`, `EF.SPECIAL_QUALITIES` may need additions.
Filed as low-severity finding (see Radar).

**Kernel touches:** None.

---

## Spot-Check Pass

| Creature | MM Page | Checked Stat | Expected | Actual |
|----------|---------|--------------|----------|--------|
| goblin | p.133 | CR | 1/4 (0.25) | 0.25 — MATCH |
| wolf | p.283 | Bite damage | 1d6+1 | "1d6+1" — MATCH |
| ogre | p.199 | AC | 17 (studded leather) | 17 — MATCH |
| troll | p.247 | HP | 63 (6d8+36) | 63 — MATCH |
| fire_giant | p.120 | special_qualities | immunity to fire | "immunity_fire" — MATCH |

No mismatches found.

---

## Radar

| ID | Severity | Status | Summary |
|----|----------|--------|---------|
| FINDING-DATA-MONSTER-EF-FIELDS-001 | LOW | OPEN | CreatureStatBlock has no mapping to EF.* constants. Future engine WO integrating creature_registry as runtime entities will need EF field mapping. |

---

## Consume-Site Confirmation

- **Write site:** `aidm/data/creature_registry.py` — `CREATURE_REGISTRY` dict
- **Read site:** None (CONSUME_DEFERRED)
- **Effect:** N/A until future encounter-setup / encounter-runner WO
- **Gate proof:** MT-001–MT-008 prove data correctness only

**CONSUME_DEFERRED** — explicitly flagged. Data is present and correct.

---

## Coverage Map Update

No engine coverage map row affected — data WO with no resolver change.

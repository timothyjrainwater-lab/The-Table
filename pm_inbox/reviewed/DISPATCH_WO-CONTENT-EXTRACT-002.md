# Instruction Packet: Monster Extraction Agent

**Work Order:** WO-CONTENT-EXTRACT-002 (Mechanical Extraction Pipeline — Monsters)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 1
**Deliverable Type:** Code implementation + extracted data + tests
**Parallelization:** Runs in parallel with WO-CONTENT-EXTRACT-001 (spells) and -003 (feats)

---

## READ FIRST — IP FIREWALL

Read the full bone/muscle/skin philosophy in WO-CONTENT-EXTRACT-001. The same rules apply here:
- **Extract:** stat block numbers, formulas, ability scores, AC breakdown, attack bonuses, damage dice, saves, special ability mechanics, speed, size, type, CR
- **Strip:** creature names, flavor descriptions, habitat lore, appearance text, behavioral prose
- **Output:** `CREATURE_001`, `CREATURE_002`, etc. with pure mechanical data. NO original names in the content pack.

---

## YOUR TASK

### Phase 1: Extraction Script

**File:** `tools/extract_monsters.py` (NEW)

Parse OCR text from `sources/text/e390dfd9143f/` (Monster Manual, 322 pages).

Monster stat blocks follow a consistent format:
```
[Name], [Variant]
[Size] [Type] ([Subtype])
Hit Dice: XdY+Z (N hp)
Initiative: +/-N
Speed: N ft. (N squares)
Armor Class: N (+X size, +Y Dex, +Z natural), touch N, flat-footed N
Base Attack/Grapple: +N/+N
Attack: [weapon] +N melee (XdY+Z) or [weapon] +N ranged (XdY+Z)
Full Attack: [weapon] +N melee (XdY+Z) and [weapon] +N melee (XdY+Z)
Space/Reach: N ft./N ft.
Special Attacks: [list]
Special Qualities: [list]
Saves: Fort +N, Ref +N, Will +N
Abilities: Str N, Dex N, Con N, Int N, Wis N, Cha N
Skills: [list]
Feats: [list]
Environment: [biome]
Organization: [group patterns]
Challenge Rating: N
Treasure: [type]
Alignment: [alignment]
Advancement: [progression]
Level Adjustment: +N or —
```

**Extract into `MechanicalCreatureTemplate`:**

```python
@dataclass(frozen=True)
class MechanicalCreatureTemplate:
    template_id: str              # "CREATURE_042" — no original name
    size_category: str            # "small", "medium", "large", etc.
    creature_type: str            # "humanoid", "undead", "beast", etc.
    subtypes: tuple[str, ...]     # ("goblinoid",), ("fire",), etc.

    # Core stats (bone)
    hit_dice: str                 # "1d8+2", "4d10+12"
    hp_typical: int               # Computed average
    initiative_mod: int
    speed_ft: int
    speed_modes: dict             # {"fly": 60, "swim": 30, "burrow": 10}

    # Defense (bone)
    ac_total: int
    ac_touch: int
    ac_flat_footed: int
    ac_components: dict           # {"size": 1, "dex": 2, "natural": 4}

    # Offense (bone)
    bab: int
    grapple_mod: int
    attacks: tuple                # List of attack entries with bonus + damage
    full_attacks: tuple           # Full attack sequence
    space_ft: int
    reach_ft: int

    # Saves (bone)
    fort_save: int
    ref_save: int
    will_save: int

    # Abilities (bone)
    str_score: Optional[int]      # None for incorporeal/oozes
    dex_score: Optional[int]
    con_score: Optional[int]
    int_score: Optional[int]      # None for mindless
    wis_score: Optional[int]
    cha_score: Optional[int]

    # Special abilities (muscle — mechanics only, no flavor)
    special_attacks: tuple[str, ...]    # Mechanical tags: "breath_weapon_cone_fire_6d6"
    special_qualities: tuple[str, ...]  # Mechanical tags: "darkvision_60", "damage_reduction_5_magic"

    # Classification (muscle)
    cr: float                     # Challenge rating
    alignment_tendency: str       # "usually_neutral_evil"
    environment_tags: tuple[str, ...] # ("temperate", "forest")

    # Tactical doctrine (muscle)
    intelligence_band: str        # "mindless", "animal", "low", "average", "high", "genius"
    organization_patterns: tuple  # Group composition patterns

    # Provenance
    source_page: str
    source_id: str
```

### Phase 2: Special Ability Parsing

The hardest part. Special abilities are described in prose but encode mechanics. Extract what you can:

- **Breath weapons:** parse shape (cone/line), size, damage dice, save type, recharge
- **Damage reduction:** parse value and bypass type (magic, silver, cold iron, etc.)
- **Spell resistance:** parse value
- **Spell-like abilities:** parse spell equivalent + uses/day + caster level
- **Regeneration/Fast healing:** parse value
- **Ability damage/drain:** parse ability affected + dice
- **Gaze attacks:** parse effect + save + DC
- **Poison:** parse type + DCs + ability damage

For abilities that resist structured extraction, log the mechanic tag and flag for manual authoring.

### Phase 3: Output

**File:** `aidm/data/content_pack/creatures.json` (NEW)
**File:** `tools/data/creature_provenance.json` (NEW, INTERNAL ONLY)
**File:** `tools/data/creature_extraction_gaps.json` (NEW)

### Phase 4: Tests

**File:** `tests/test_content_pack_creatures.py` (NEW)

1. Recognition Test: no original creature names in creatures.json
2. Schema validity: all entries deserialize
3. Spot-check 10 creatures against known stat blocks
4. Cross-reference with existing MonsterDoctrine entries (if any)
5. No prose leakage

---

## SCOPE

- All creatures from MM pages (approximately pages 3-280)
- OCR text: `sources/text/e390dfd9143f/`

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `sources/text/e390dfd9143f/0133.txt` | Sample monster page (Gnome stat block) |
| 1 | `aidm/schemas/doctrine.py` | Existing MonsterDoctrine class |
| 2 | `aidm/schemas/entity_fields.py` | Entity field constants |

## STOP CONDITIONS

- OCR quality too poor on a page → skip creature, log gap
- Special ability too complex for structured extraction → log the tag, flag for manual authoring
- NEVER store original creature names in creatures.json

## DELIVERY

- New files: `tools/extract_monsters.py`, `aidm/data/content_pack/creatures.json`, `tools/data/creature_provenance.json`, `tools/data/creature_extraction_gaps.json`, `tests/test_content_pack_creatures.py`
- Completion report: `pm_inbox/AGENT_WO-CONTENT-EXTRACT-002_completion.md`

---

END OF INSTRUCTION PACKET

# Instruction Packet: Feat Extraction Agent

**Work Order:** WO-CONTENT-EXTRACT-003 (Mechanical Extraction Pipeline — Feats)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 2
**Deliverable Type:** Code implementation + extracted data + tests
**Parallelization:** Runs in parallel with WO-CONTENT-EXTRACT-001 (spells) and -002 (monsters)

---

## READ FIRST — IP FIREWALL

Same rules as WO-CONTENT-EXTRACT-001:
- **Extract:** trigger conditions, mechanical effects, prerequisites (as ability score / BAB / feat-ref requirements), bonus values, action economy changes
- **Strip:** feat names, flavor descriptions, example prose
- **Output:** `FEAT_001`, `FEAT_002`, etc. with pure mechanical data

---

## YOUR TASK

### Phase 1: Extraction Script

**File:** `tools/extract_feats.py` (NEW)

Parse OCR text from `sources/text/681f92bc94ff/` (PHB, Chapter 5: Feats, approximately pages 89-103).

Feat entries follow a consistent format:
```
[FEAT NAME] [TYPE TAG]
[Flavor line]
Prerequisites: [list]
Benefit: [mechanical description]
Normal: [what happens without this feat]
Special: [additional rules]
```

**Extract into `MechanicalFeatTemplate`:**

```python
@dataclass(frozen=True)
class MechanicalFeatTemplate:
    template_id: str                # "FEAT_017" — no original name
    feat_type: str                  # "general", "metamagic", "item_creation", "fighter_bonus"

    # Prerequisites (bone)
    prereq_ability_scores: dict     # {"str": 13} or {}
    prereq_bab: Optional[int]      # Minimum BAB required, or None
    prereq_feat_refs: tuple[str, ...] # ("FEAT_003",) — references to other feat template IDs
    prereq_class_features: tuple[str, ...]  # ("turn_undead",) — mechanical features required
    prereq_caster_level: Optional[int]
    prereq_other: tuple[str, ...]   # Freeform mechanical prereqs that resist structuring

    # Mechanical effect (bone + muscle)
    effect_type: str                # "attack_modifier", "ac_modifier", "save_modifier",
                                    # "damage_modifier", "action_economy", "special_action",
                                    # "passive_defense", "skill_modifier", "metamagic_modifier"
    bonus_value: Optional[int]      # +4, +2, etc. — None if not a simple bonus
    bonus_type: Optional[str]       # "initiative", "attack_roll", "damage_roll", "ac", "saves"
    bonus_applies_to: Optional[str] # "all", "melee", "ranged", "grapple", etc.

    # Trigger (muscle)
    trigger: Optional[str]          # "on_attack_hit", "on_overrun", "on_shield_bash", etc.
    replaces_normal: Optional[str]  # What the feat changes from normal behavior

    # Action economy changes (muscle)
    grants_action: Optional[str]    # "extra_off_hand_attack", "immediate_counterattack"
    removes_penalty: Optional[str]  # "no_aoo_on_grapple", "keep_shield_bonus_on_bash"

    # Conditional (muscle)
    stacks_with: tuple[str, ...]    # What this bonus stacks with
    limited_to: Optional[str]       # "light_armor_only", "fighter_class", etc.

    # Fighter bonus feat eligible
    fighter_bonus_eligible: bool

    # Provenance
    source_page: str
    source_id: str
```

### Phase 2: Prerequisite Chain Resolution

Feats reference other feats as prerequisites. Since we're assigning new template IDs:
1. First pass: extract all feats and assign IDs
2. Second pass: resolve prerequisite references from original names to template IDs
3. Store the name→ID mapping in provenance file only

### Phase 3: Output

**File:** `aidm/data/content_pack/feats.json` (NEW)
**File:** `tools/data/feat_provenance.json` (NEW, INTERNAL ONLY)
**File:** `tools/data/feat_extraction_gaps.json` (NEW)

### Phase 4: Tests

**File:** `tests/test_content_pack_feats.py` (NEW)

1. Recognition Test: no original feat names in feats.json
2. Schema validity
3. Prerequisite chains are valid (all FEAT_XXX references exist)
4. Spot-check 10 feats against known mechanics
5. No prose leakage
6. Fighter bonus feat flag is set correctly

---

## SCOPE

- All feats from PHB Chapter 5 (approximately pages 89-103)
- General feats, metamagic feats, item creation feats, fighter bonus feats

## OUT OF SCOPE

- Monster feats (MM) — future WO
- Epic feats — future WO
- Prestige class feats — future WO

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `sources/text/681f92bc94ff/0097.txt` | Sample feat page (OCR format) |
| 2 | `aidm/core/feat_resolver.py` | Existing feat mechanics (if exists) |

## STOP CONDITIONS

- OCR quality too poor → skip feat, log gap
- Feat effect too complex for structured extraction → log tag, flag for manual
- NEVER store original feat names in feats.json
- Prerequisite references that can't be resolved → log as gap

## DELIVERY

- New files: `tools/extract_feats.py`, `aidm/data/content_pack/feats.json`, `tools/data/feat_provenance.json`, `tools/data/feat_extraction_gaps.json`, `tests/test_content_pack_feats.py`
- Completion report: `pm_inbox/AGENT_WO-CONTENT-EXTRACT-003_completion.md`

---

END OF INSTRUCTION PACKET

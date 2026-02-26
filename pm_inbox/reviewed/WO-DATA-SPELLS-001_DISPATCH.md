# Work Order: WO-DATA-SPELLS-001
**Artifact ID:** WO-DATA-SPELLS-001
**Batch:** OSS Data Batch A
**Lifecycle:** DISPATCH-READY
**Drafted by:** Slate (PM)
**Date:** 2026-02-26
**Source:** PCGen `rsrd_spells.lst` (OGL — `data/35e/wizards_of_the_coast/rsrd/basics/`)
**Dependency:** LST-PARSER-001 (must complete first)

---

## Summary

The engine currently has 45 spells in `aidm/data/spell_definitions.py`. Each entry in
`SpellDefinition` has ~15 fields. PCGen rsrd_spells.lst provides ~350 RSRD spells with
clean data for: name, class levels, school, COMPS (verbal/somatic/material), casttime,
range, duration, saving throw, spell resistance.

**PCGen does NOT provide:** target_type, aoe_shape, aoe_radius_ft, effect_type,
damage_dice, damage_type, healing_dice — these require full spell text interpretation
and cannot be regex-extracted from LST.

**Approach:** This WO expands the registry to ~350 spells using PCGen for the fields
it covers cleanly, and populates the remaining fields with safe defaults. The result
is a registry where every RSRD spell exists with correct component/school/level data,
and with effect fields populated as stubs (DAMAGE/NONE) that future WOs refine.

**The existing 45 spells in spell_definitions.py are the gold standard.** Do NOT
overwrite them. Add the new entries alongside. Where a PCGen entry matches an existing
spell, verify the PCGen data matches the existing entry — flag mismatches as FINDINGs.

---

## Scope

**Files to modify:**
- `aidm/data/spell_definitions.py` — add ~300 new entries

**Files to read/verify (do not modify):**
- `data/pcgen_extracted/spells_raw.json` — LST-PARSER-001 output (must exist first)
- `aidm/core/spell_resolver.py` — SpellDefinition schema (the target dataclass)

**Files out of scope:**
- SpellDefinition dataclass itself — do not modify
- Any resolver — spell behavior is not in scope

---

## SpellDefinition Field Mapping

| SpellDefinition field | PCGen source | Strategy |
|----------------------|--------------|----------|
| `spell_id` | Derived from name: `name.lower().replace(" ", "_")` | Generate |
| `name` | Entry name | Direct |
| `level` | CLASSES tag (e.g., `Wizard=3`) — use minimum class level | Parse |
| `school` | SCHOOL tag | Direct (lowercase) |
| `target_type` | NOT in PCGen | Default: `SpellTarget.SINGLE` |
| `range_ft` | RANGE tag — approximate parsing | Parse ("Close"→25, "Medium"→100, "Long"→400, "Touch"→0) |
| `has_verbal` | COMPS tag — `"V" in comps` | Parse |
| `has_somatic` | COMPS tag — `"S" in comps` | Parse |
| `has_material` | COMPS tag — `"M" in comps` | Parse |
| `effect_type` | NOT in PCGen | Default: `SpellEffect.NONE` |
| `damage_dice` | NOT in PCGen | Default: `None` |
| `damage_type` | NOT in PCGen | Default: `None` |
| `save_type` | SAVEINFO tag — parse "Reflex half" → `SaveType.REF` | Parse |
| `duration_rounds` | DURATION tag — approximate | Parse ("1 round/level"→10, "Instantaneous"→0) |
| `concentration` | NOT in PCGen | Default: `False` |
| `rule_citations` | NOT in PCGen | Empty tuple |
| `content_id` | NOT in PCGen | `None` |

**Critical:** The 45 existing spells in SPELL_REGISTRY have hand-crafted values for all
fields including damage_dice, target_type, aoe_shape. Do NOT overwrite these with defaults.

---

## Assumptions to Validate (verify before writing)

1. Read `data/pcgen_extracted/spells_raw.json` — confirm spell count and CLASSES tag format.
   Is it `CLASSES:Wizard=3,Sorcerer=3` or `CLASSES:Sorcerer=3,Wizard=3` or something else?
2. Confirm SAVEINFO tag format — is it "Reflex half", "Will negates", "Fortitude partial"?
   Document all variants found and the parsing strategy for each.
3. Confirm RANGE tag format — does PCGen use "Close (25 ft. + 5 ft./2 levels)" verbatim,
   or abbreviated? What about non-standard ranges?
4. Check for existing spell ID collisions — do any PCGen spell names (when lowercased
   + underscored) collide with the 45 existing entries? List all collisions in Pass 1.
5. Confirm SCHOOL tag values — are they capitalized? Do subschool entries appear?

---

## Implementation

### Generation strategy

Do NOT type 300 entries by hand. Write a generator script:

```bash
python scripts/gen_spell_definitions.py data/pcgen_extracted/spells_raw.json --skip-existing
```

This script reads spells_raw.json, applies the field mapping table above, skips any spell
whose ID already exists in SPELL_REGISTRY, and emits Python code. Review the output, then
append to spell_definitions.py.

Existing entries in SPELL_REGISTRY are the ground truth — the generator skips them.

### Stub entry example

```python
"acid_arrow": SpellDefinition(
    spell_id="acid_arrow",
    name="Acid Arrow",
    level=2,
    school="conjuration",
    target_type=SpellTarget.SINGLE,     # stub — PCGen has no target type
    range_ft=100,                        # Medium range
    effect_type=SpellEffect.NONE,       # stub — PCGen has no effect type
    has_verbal=True,
    has_somatic=True,
    has_material=True,
    save_type=None,
    duration_rounds=0,
    rule_citations=(),
),
```

---

## Acceptance Criteria

Write gate file `tests/test_data_spells_001_gate.py`:

| ID | Scenario | Expected |
|----|----------|----------|
| SP-001 | `SPELL_REGISTRY["magic_missile"].level` | 1 (existing entry, not overwritten) |
| SP-002 | `SPELL_REGISTRY["acid_arrow"].has_somatic` | True |
| SP-003 | `SPELL_REGISTRY["acid_arrow"].school` | "conjuration" |
| SP-004 | `SPELL_REGISTRY["fly"].has_verbal` | True |
| SP-005 | `SPELL_REGISTRY["fly"].has_somatic` | True |
| SP-006 | `SPELL_REGISTRY["message"].has_somatic` | False (V only — no somatic component) |
| SP-007 | `len(SPELL_REGISTRY)` | ≥ 200 (sanity floor — was 45, PCGen adds ~300) |
| SP-008 | Existing 45 entries still present and values unchanged | Pass (spot-check 5 existing entries) |

8 tests total. Gate label: DATA-SPELLS-001.

---

## Pass 3 Checklist

1. Document the field coverage rate — what percentage of new entries have non-stub
   `save_type`, `range_ft`, `duration_rounds` vs defaulted to None/0?
2. Document SAVEINFO parsing coverage — how many unique SAVEINFO patterns were found?
   Were any unparseable? Flag as FINDING.
3. Document any existing spell entry that CONFLICTS with PCGen data (e.g., PCGen says
   level 4 but engine has level 3). These are gold-standard conflicts — PCGen may be
   wrong or the 3.5e entry may differ from RSRD. Flag each as FINDING.
4. Note that stub entries (SpellEffect.NONE, no damage_dice) will cause specific gate
   tests for those spells to fail when behavior WOs try to resolve them. This is expected
   and correct — the stub registry entry exists for component enforcement; behavior fields
   will be filled in as needed. Document this pattern clearly.

---

## Session Close Condition

- [ ] `git add aidm/data/spell_definitions.py tests/test_data_spells_001_gate.py`
- [ ] (if generator script is kept) `git add scripts/gen_spell_definitions.py`
- [ ] `git commit` with hash
- [ ] All 8 SP tests pass; zero regressions against existing spell gate suite
- [ ] Debrief filed to `pm_inbox/reviewed/`

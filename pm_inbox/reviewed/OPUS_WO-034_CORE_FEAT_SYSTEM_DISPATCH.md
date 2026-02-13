# WO-034: Core Feat System (15 Feats)
**Dispatched by:** Opus (PM)
**Date:** 2026-02-11
**Phase:** 2B.1 (Content Breadth)
**Priority:** Batch 1 (immediate)
**Status:** DISPATCHED

---

## Objective

Implement 15 core combat feats per D&D 3.5e PHB, following the established resolver pattern in `aidm/core/`. Each feat: prerequisite validation, combat modifier application, integration with existing attack/AoO/save resolvers.

---

## Package Structure

**New files:**
- `aidm/core/feat_resolver.py` — Feat registry, prerequisite checking, modifier computation
- `aidm/schemas/feats.py` — FeatDefinition dataclass, FeatID constants, prerequisite schema
- `tests/test_feat_resolver.py` — ~60 tests

**Modified files:**
- `aidm/schemas/entity_fields.py` — Add `EF.FEATS` (list of feat IDs on entity)
- `aidm/core/attack_resolver.py` — Call feat modifier hooks during attack/damage resolution
- `aidm/core/aoo.py` — Mobility feat affects AoO provocation

**Do NOT modify:** `aidm/core/play_loop.py` (feat modifiers apply inside resolvers, not at the play loop level)

---

## Feat List (15 Feats)

### Melee Chain
| Feat | PHB Page | Prerequisite | Effect |
|------|----------|-------------|--------|
| Power Attack | p.98 | STR 13, BAB +1 | Trade attack bonus for damage (1:1 for one-hand, 1:2 for two-hand) |
| Cleave | p.92 | STR 13, Power Attack | Free attack on adjacent enemy when you drop a foe |
| Great Cleave | p.94 | STR 13, Cleave, BAB +4 | Cleave with no limit per round |

### Defense Chain
| Feat | PHB Page | Prerequisite | Effect |
|------|----------|-------------|--------|
| Dodge | p.93 | DEX 13 | +1 dodge AC vs one designated opponent |
| Mobility | p.98 | DEX 13, Dodge | +4 dodge AC vs AoO from movement |
| Spring Attack | p.100 | DEX 13, Dodge, Mobility, BAB +4 | Move before and after attack without AoO |

### Ranged Chain
| Feat | PHB Page | Prerequisite | Effect |
|------|----------|-------------|--------|
| Point Blank Shot | p.98 | None | +1 attack and damage within 30 ft |
| Precise Shot | p.98 | Point Blank Shot | No -4 penalty for shooting into melee |
| Rapid Shot | p.99 | DEX 13, Point Blank Shot | Extra attack at -2 to all attacks |

### Weapon Chain
| Feat | PHB Page | Prerequisite | Effect |
|------|----------|-------------|--------|
| Weapon Focus | p.102 | BAB +1, proficiency | +1 attack with chosen weapon |
| Weapon Specialization | p.102 | Weapon Focus, Fighter 4 | +2 damage with chosen weapon |

### Two-Weapon Fighting
| Feat | PHB Page | Prerequisite | Effect |
|------|----------|-------------|--------|
| Two-Weapon Fighting | p.102 | DEX 15 | Reduce TWF penalties to -2/-2 |
| Improved TWF | p.96 | DEX 17, TWF, BAB +6 | Second off-hand attack at -5 |
| Greater TWF | p.94 | DEX 19, Improved TWF, BAB +11 | Third off-hand attack at -10 |

### Initiative
| Feat | PHB Page | Prerequisite | Effect |
|------|----------|-------------|--------|
| Improved Initiative | p.96 | None | +4 initiative |

---

## Architecture

### FeatDefinition Schema

```python
@dataclass(frozen=True)
class FeatDefinition:
    feat_id: str              # "power_attack", "dodge", etc.
    name: str                 # "Power Attack"
    prerequisites: dict       # {"min_str": 13, "min_bab": 1, "required_feats": ["power_attack"]}
    modifier_type: str        # "attack", "damage", "ac", "initiative", "aoo"
    phb_page: int             # PHB citation
```

### Integration Pattern

Feats modify combat resolution at specific hook points in existing resolvers:

1. **attack_resolver.py** — Before rolling: compute feat-based attack modifier (Weapon Focus +1, Power Attack penalty, Rapid Shot -2). After damage roll: compute feat-based damage modifier (Power Attack bonus, Weapon Specialization +2, Point Blank Shot +1).

2. **aoo.py** — During AoO check: Mobility grants +4 dodge AC vs AoO triggered by movement. Spring Attack suppresses AoO from the attack-during-move action.

3. **combat_controller.py** — During initiative: Improved Initiative adds +4. During Cleave: after entity_defeated event, check for Cleave/Great Cleave and grant free attack.

The feat resolver provides modifier computation functions that existing resolvers call:

```python
def get_attack_modifier(attacker: dict, target: dict, feats: list[str], context: dict) -> int:
    """Compute total feat-based attack modifier."""

def get_damage_modifier(attacker: dict, target: dict, feats: list[str], context: dict) -> int:
    """Compute total feat-based damage modifier."""

def get_ac_modifier(defender: dict, attacker: dict, feats: list[str], context: dict) -> int:
    """Compute total feat-based AC modifier (Dodge, Mobility)."""

def check_prerequisites(entity: dict, feat_id: str) -> tuple[bool, str]:
    """Validate feat prerequisites. Returns (met, reason)."""

def get_initiative_modifier(entity: dict, feats: list[str]) -> int:
    """Compute feat-based initiative modifier."""
```

### Entity Field

Add `EF.FEATS = "feats"` to entity_fields.py. Entity dict stores feats as a list of feat ID strings:

```python
entity[EF.FEATS] = ["power_attack", "cleave", "weapon_focus_longsword"]
```

Weapon-specific feats use suffix: `"weapon_focus_longsword"`, `"weapon_specialization_greatsword"`.

---

## Acceptance Criteria

- [ ] All 15 feats resolve correctly per D&D 3.5e PHB (cite page numbers in tests)
- [ ] Prerequisites enforced: BAB requirements, ability score minimums, feat chains
- [ ] Modifiers apply during combat resolution via hook functions (not as separate step)
- [ ] Power Attack trade-off computed correctly: 1:1 one-hand, 1:2 two-hand (PHB p.98)
- [ ] Cleave grants free attack only on adjacent enemy after dropping a foe
- [ ] Mobility +4 dodge AC applies only to AoO from movement, not all AoO
- [ ] Spring Attack tested with movement + attack + movement pattern
- [ ] No 5e contamination: no advantage/disadvantage, no proficiency bonus
- [ ] EF.FEATS constant added to entity_fields.py
- [ ] RNG stream: combat (existing stream, for Cleave attack rolls)
- [ ] All existing tests pass (3302+, 0 regressions)
- [ ] ~60 new tests

---

## Boundary Laws

| Law | Enforcement |
|-----|-------------|
| EF.* constants | New EF.FEATS field via entity_fields.py |
| State mutation via deepcopy() | Cleave creates new entity state for free attack |
| RNG stream isolation | Cleave attacks use combat stream |
| D&D 3.5e only | PHB page citations in test docstrings; no 5e mechanics |

---

## References

- Execution Plan: `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` lines 273-296
- AoO pattern: `aidm/core/aoo.py` (WO-011)
- Attack resolver: `aidm/core/attack_resolver.py`
- Entity fields: `aidm/schemas/entity_fields.py`
- Agent guidelines: `AGENT_DEVELOPMENT_GUIDELINES.md`
- Tactical Integrity Doctrine: `docs/governance/TACTICAL_INTEGRITY_DOCTRINE.md` (Section 7: creatures must use feats when heuristic favors it)

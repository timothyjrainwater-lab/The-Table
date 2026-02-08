<!--
AGENT DEVELOPMENT GUIDELINES — CODING STANDARDS & PITFALL AVOIDANCE

This file is MANDATORY READING for all agents before writing code on this project.
It documents hard-won lessons from audits, discovered bugs, and architectural patterns
that MUST be followed to maintain project integrity.

LAST UPDATED: Plan B Remediation (1225 tests, CP-20, FIX-04/12/16)
-->

# Agent Development Guidelines

## 1. Entity Field Names — CANONICAL CONSTANTS REQUIRED

### The Problem
Entity data is stored as `Dict[str, Any]`. Multiple modules reach into these dicts
with string literal keys. A bug was discovered where `permanent_stats.py` used
`"current_hp"` while every other module used `"hp_current"`. This was a silent failure
that caused HP clamping to never trigger after CON drain.

### The Rule
**ALWAYS use constants from `aidm.schemas.entity_fields` when reading or writing entity fields.**

```python
# CORRECT
from aidm.schemas.entity_fields import EF

hp = entity.get(EF.HP_CURRENT, 0)
entity[EF.DEFEATED] = True

# WRONG — bare string literals
hp = entity.get("hp_current", 0)
entity["defeated"] = True
```

### Adding New Entity Fields
1. Add the constant to `aidm/schemas/entity_fields.py` FIRST
2. Document which CP introduced the field
3. Use the constant in ALL code that touches the field
4. Update this guidelines document if the field has special semantics

### Current Canonical Fields
See `aidm/schemas/entity_fields.py` for the complete list. Key fields:
- `EF.HP_CURRENT` / `EF.HP_MAX` — Hit points (NOT "current_hp")
- `EF.AC` — Armor class
- `EF.DEFEATED` — Boolean defeat status
- `EF.POSITION` — Grid position dict with "x", "y" keys
- `EF.CONDITIONS` — Dict keyed by condition type string
- `EF.TEAM` — Team identifier string

---

## 2. Two Attack Pipelines — DO NOT CONFUSE

### Voice/Interaction Layer
- **Class**: `DeclaredAttackIntent` in `aidm.schemas.intents`
- **Fields**: `target_ref` (string name), `weapon` (string name)
- **Used by**: `interaction.py`, voice intent parsing
- **Purpose**: Captures player declaration ("I attack the goblin with my longsword")

### Combat Resolution Layer
- **Class**: `AttackIntent` in `aidm.schemas.attack`
- **Fields**: `attacker_id`, `target_id`, `attack_bonus` (int), `weapon` (Weapon dataclass)
- **Used by**: `attack_resolver.py`, `play_loop.py`, `combat_controller.py`
- **Purpose**: Fully resolved combat data for deterministic resolution

### The Bridge (NOT YET IMPLEMENTED)
When wiring the interaction engine to combat, a translation layer is needed:
1. `DeclaredAttackIntent` → look up character weapon stats → calculate attack bonus → `AttackIntent`
2. This bridge should be its own CP with tests
3. **NEVER** import `AttackIntent` from `aidm.schemas.intents` — that class was renamed to
   `DeclaredAttackIntent` specifically to prevent name collisions

---

## 3. Grid Position Types — USE THE RIGHT ONE

Three position-related types exist. Use the correct one for your context:

| Type | Module | Has `distance_to()` | Has `is_adjacent_to()` | Use For |
|------|--------|---------------------|----------------------|---------|
| `GridPoint` | `schemas/targeting.py` | Yes | No | Targeting/range checks |
| `GridPoint` | `schemas/intents.py` | No | No | Voice intent coordinates |
| `GridPosition` | `schemas/attack.py` | No | Yes | AoO adjacency checks |

### Future Plan
These should be unified into a single canonical type. Until then:
- For **range calculations** and **targeting**: use `targeting.GridPoint`
- For **AoO and adjacency**: use `attack.GridPosition`
- For **voice intents**: use `intents.GridPoint`
- **NEVER** assume these types are interchangeable

---

## 4. JSON Serialization Rules

### No Python `set()` in State
Python `set` objects are **not JSON-serializable**. The `WorldState.state_hash()` method
calls `json.dumps()`, which will crash on sets.

```python
# WRONG — will crash state_hash()
"flat_footed_actors": set(initiative_order)

# CORRECT
"flat_footed_actors": list(initiative_order)
```

### Sorted Keys Always
All JSON serialization MUST use `sort_keys=True` for deterministic output:
```python
json.dumps(data, sort_keys=True)
```

### No Floating Point in State
Integer arithmetic only in all deterministic paths. Floating point breaks
reproducibility across platforms.

---

## 5. RNG Stream Isolation

Four RNG streams exist. NEVER cross-contaminate them:

| Stream | Purpose | Used By |
|--------|---------|---------|
| `"combat"` | Attack rolls, damage rolls, AoO resolution | attack_resolver, full_attack_resolver, aoo |
| `"initiative"` | Initiative rolls | initiative.py |
| `"policy"` | Tactical variety selection | tactical_policy.py |
| `"saves"` | Saving throw rolls | save_resolver.py |

### Rules
- Each resolver MUST document which RNG stream it uses
- RNG consumption order within a stream MUST be deterministic and documented
- New resolvers that need randomness MUST use an existing stream or create a new named stream
- Streams that DON'T exist yet but may be needed: `"loot"`, `"encounter"`, `"narration"`

---

## 6. Event-Sourced State Mutation

### How State Actually Works
Despite the doctrine saying "mutations only through replay runner's single reducer," the actual
pattern in this codebase is:

1. **Resolvers** (attack_resolver, save_resolver, etc.) produce event lists but do NOT mutate state
2. **Apply functions** (apply_attack_events, apply_save_effects) create new WorldState instances from events
3. **Replay runner** handles only entity management events (add/remove/set_field), NOT combat events

### Rules for New Resolvers
1. Your resolver function MUST return events only — never mutate the WorldState passed to it
2. Create a corresponding `apply_X_events()` function that builds a new WorldState from events
3. The play loop calls your resolver, then your apply function
4. Add your event types to replay_runner.py's reducer if they need replay support

### Combat Replay Strategy
Combat replay uses **re-execution** (same seed → same output), NOT event reduction through
the replay runner. This is by design. If you need to test determinism, run the same scenario
twice with the same seed and compare outputs.

---

## 7. D&D 3.5e Rules Accuracy

### Common 5e Contamination Risks
This is a **D&D 3.5e** project. Do NOT introduce 5e concepts:

| 5e Concept | 3.5e Equivalent |
|------------|-----------------|
| Short rest / Long rest | 8-hour rest / Full day bed rest |
| Advantage / Disadvantage | Does not exist (use numeric modifiers) |
| Proficiency bonus | Base Attack Bonus (BAB) + feat/class bonuses |
| Cantrips at will | 0-level spells use spell slots |
| Concentration (5e style) | Different concentration rules in 3.5e |
| Electric damage | **Electricity** damage (PHB p.309) |

### Damage Types (3.5e Canonical List)
```
Physical: slashing, piercing, bludgeoning, nonlethal
Energy: fire, cold, acid, electricity, sonic
Other: force, positive, negative
```
The validated set is in `aidm/schemas/attack.py` `Weapon.__post_init__()`.

### Rest Types (3.5e)
```python
rest_type: Literal["overnight", "full_day"]
```
- `"overnight"`: 8-hour rest (PHB p.146) — natural healing, spell preparation
- `"full_day"`: Complete bed rest — 3× natural healing rate

---

## 8. Test Requirements

### Before Submitting Any CP
1. **ALL existing tests must pass** — zero regressions allowed
2. **Runtime must stay under 2 seconds** for the full suite
3. **New features must have tests** — minimum Tier-1 coverage
4. Run: `python -m pytest tests/ -v --tb=short`

### Test Organization
- One test file per module/feature: `tests/test_{module_name}.py`
- Tier-1 tests: Core correctness (blocking — must pass to merge)
- Tier-2 tests: Edge cases, boundary conditions, integration
- PBHA tests: Deterministic replay verification (10× identical results)

### Determinism Verification Pattern
```python
def test_determinism():
    """Same inputs → identical outputs across multiple runs."""
    results = []
    for seed in range(10):
        result = run_scenario(seed=42)  # SAME seed each time
        results.append(hash_result(result))
    assert len(set(results)) == 1  # All identical
```

---

## 9. Conditions System

### Storage Format
Conditions are stored as a **dict** keyed by condition type string:
```python
entity["conditions"] = {
    "prone": { "source": "trip_attack", ... },
    "shaken": { "source": "intimidate", ... }
}
```

### Querying Conditions
Use `get_condition_modifiers()` from `aidm.core.conditions`:
```python
modifiers = get_condition_modifiers(actor_id, world_state, context=None)
# modifiers.ac_modifier, modifiers.attack_modifier, etc.
```

### Default Value Consistency
When checking conditions on an entity:
```python
# CORRECT — conditions is a dict, default should be dict
conditions = entity.get(EF.CONDITIONS, {})

# WRONG — default is a list, but conditions is stored as a dict
conditions = entity.get("conditions", [])
```

---

## 10. File Organization

### Where New Code Goes
| Type | Directory | Naming |
|------|-----------|--------|
| Data contracts / schemas | `aidm/schemas/` | `{concept}.py` |
| Core logic / resolvers | `aidm/core/` | `{concept}.py` or `{concept}_resolver.py` |
| Validation rules | `aidm/rules/` | `{concept}_checker.py` |
| Tests | `tests/` | `test_{module}.py` |
| CP decisions | `docs/` | `CP{XX}_{NAME}_DECISIONS.md` |

### Import Conventions
```python
# Schemas first, then core, then rules
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.attack_resolver import resolve_attack
from aidm.rules.legality_checker import LegalityChecker
```

---

## 11. Common Pitfalls Checklist

Before submitting any code change, verify:

- [ ] No bare string literals for entity field access (use `EF.*` constants)
- [ ] No Python `set()` objects stored in WorldState or active_combat
- [ ] No floating point arithmetic in deterministic code paths
- [ ] All JSON serialization uses `sort_keys=True`
- [ ] RNG streams are not cross-contaminated
- [ ] Resolver functions return events only, never mutate state
- [ ] New entity fields are added to `entity_fields.py` first
- [ ] D&D 3.5e terminology used (not 5e)
- [ ] All 594+ tests pass in under 2 seconds
- [ ] `DeclaredAttackIntent` (voice) vs `AttackIntent` (combat) — correct one used
- [ ] Grid position type matches the context (targeting vs AoO vs voice)
- [ ] Shallow copies of entity dicts don't accidentally share nested references

---

## 12. PROJECT_STATE_DIGEST.md Maintenance

The PSD is the single source of truth for any new agent joining the project. It MUST be
updated at the end of every CP with:

1. New locked systems added to the top section
2. Updated test count (total + breakdown by subsystem)
3. New modules added to module inventory
4. New test files added to test inventory
5. CP history entry with full details

**Stale PSD = confused agents = wasted work.**

---

## 13. Completion Packet (CP) Protocol

Every CP must follow this process:

1. **Define scope** — What exactly is being built, what's out of scope
2. **Write schemas first** — Data contracts before algorithms
3. **Write tests second** — At least Tier-1 test stubs before implementation
4. **Implement** — Fill in the logic to make tests pass
5. **Verify determinism** — Run full suite, check no regressions
6. **Update PSD** — Add CP to packet history, update counts
7. **Update this guidelines file** — If new patterns or pitfalls were discovered

### CP Naming Convention
- `CP-{XX}`: Standard completion packet (sequential numbering)
- `CP-{XX}{letter}`: Sub-packet (e.g., CP-18A for spellcasting part A)
- `SKR-{XXX}`: Structural Kernel Register entry (cross-cutting concerns)
- `CP-{XX}D`: Documentation/coherence cleanup packet

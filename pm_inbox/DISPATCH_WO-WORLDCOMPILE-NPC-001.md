# Instruction Packet: NPC Archetype Agent

**Work Order:** WO-WORLDCOMPILE-NPC-001 (World Compiler Stage 4 — NPC Archetypes + Doctrine)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 2 (Not on critical path for MVP combat, but needed for NPC encounters)
**Deliverable Type:** Code implementation + tests
**Parallelization:** Runs after WO-WORLDCOMPILE-SCAFFOLD-001 lands. Parallel with Stages 1, 3, 6, 7.

---

## READ FIRST

Stage 4 generates two things:
1. **NPC Archetypes** — behavioral templates for non-combat NPCs (shopkeeper, guard, noble, etc.)
2. **Doctrine Profiles** — tactical behavior templates for creatures (aggression, retreat threshold, pack behavior)

The doctrine system already exists in `aidm/schemas/doctrine.py` — the `MonsterDoctrine` class with fields for `aggression`, `retreat_threshold`, `pack_behavior`, `preferred_tactics`, `morale`. Stage 4 generates world-themed instances of these.

---

## YOUR TASK

### Deliverable 1: NPC Archetype Schema

**File:** `aidm/schemas/npc_archetype.py` (NEW)

```python
@dataclass(frozen=True)
class NPCArchetype:
    archetype_id: str               # "archetype_shopkeeper", "archetype_guard"
    world_name: str                 # World-flavored name: "Merchant of the Ashen Roads"
    personality_traits: tuple       # ("cautious", "mercantile", "observant")
    speech_register: str            # "formal", "colloquial", "archaic"
    knowledge_domains: tuple        # ("commerce", "local_rumors", "item_valuation")
    behavioral_constraints: tuple   # ("will_not_fight", "calls_guards_if_threatened")
    interaction_hooks: tuple        # ("can_appraise_items", "sells_equipment", "knows_local_gossip")
    voice_description: str          # Brief voice description for TTS persona mapping
    provenance: dict                # Standard provenance record

@dataclass(frozen=True)
class DoctrineProfile:
    doctrine_id: str                # "doctrine_pack_predator", "doctrine_ambusher"
    creature_types: tuple           # Which creature types this applies to
    aggression: str                 # "timid", "cautious", "aggressive", "berserk"
    retreat_threshold: float        # HP fraction at which creature retreats (0.0-1.0)
    pack_behavior: str              # "solo", "pair", "pack", "swarm"
    preferred_tactics: tuple        # ("ambush", "flank", "charge", "ranged_kite")
    morale: str                     # "cowardly", "steady", "fanatical"
    special_behaviors: tuple        # ("guards_lair", "protects_young", "calls_reinforcements")
    provenance: dict

@dataclass(frozen=True)
class NPCArchetypeRegistry:
    schema_version: str
    world_id: str
    archetypes: tuple               # Tuple of NPCArchetype
    doctrines: tuple                # Tuple of DoctrineProfile
```

All frozen. All support `to_dict()` / `from_dict()`.

### Deliverable 2: NPC Stage Implementation

**File:** `aidm/core/compile_stages/npc_archetypes.py` (NEW)

Implement `NPCArchetypeStage(CompileStage)`:

- In stub mode: generate 8 standard archetypes (shopkeeper, guard, noble, peasant, scholar, criminal, priest, innkeeper) and 6 doctrine profiles (pack_predator, ambusher, territorial_defender, mindless_aggressor, tactical_caster, cowardly_scavenger) with deterministic data from seed
- In LLM mode: use world theme to flavor archetype names, traits, and doctrine parameters
- Output `npc_archetypes.json` + `doctrine_profiles.json`

### Deliverable 3: Cross-Reference with Existing Doctrine

Check `aidm/schemas/doctrine.py` for the existing `MonsterDoctrine` class. The `DoctrineProfile` from this WO should be CONVERTIBLE to the existing `MonsterDoctrine` format. Include a `to_monster_doctrine()` method or document the field mapping.

### Deliverable 4: Tests

**File:** `tests/test_compile_npc.py` (NEW)

1. Stub mode produces 8 archetypes + 6 doctrines
2. Output round-trips via to_dict/from_dict
3. All archetype_ids are unique
4. All doctrine_ids are unique
5. Retreat threshold is between 0.0 and 1.0
6. Doctrine can be converted to MonsterDoctrine format
7. Stub mode is deterministic (same seed → same output)
8. Stage registers with WorldCompiler correctly

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| MonsterDoctrine | `aidm/schemas/doctrine.py` | Existing doctrine class — check compatibility |
| Content pack creatures | `aidm/data/content_pack/creatures.json` | Creature types for doctrine assignment |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/contracts/WORLD_COMPILER.md` § 2.4 | Stage 4 specification |
| 1 | `aidm/schemas/doctrine.py` | Existing MonsterDoctrine class |
| 2 | `aidm/data/content_pack/creatures.json` | Creature type distribution |

## DELIVERY

- New files: `aidm/schemas/npc_archetype.py`, `aidm/core/compile_stages/npc_archetypes.py`, `tests/test_compile_npc.py`
- Completion report: `pm_inbox/AGENT_WO-WORLDCOMPILE-NPC-001_completion.md`

---

END OF INSTRUCTION PACKET

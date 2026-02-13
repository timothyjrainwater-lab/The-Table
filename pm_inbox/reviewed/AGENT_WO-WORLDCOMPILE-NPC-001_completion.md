# Completion Report: WO-WORLDCOMPILE-NPC-001

**Work Order:** WO-WORLDCOMPILE-NPC-001 (World Compiler Stage 4 — NPC Archetypes + Doctrine)
**Agent:** Claude Opus 4.6
**Date:** 2026-02-13
**Status:** COMPLETE — All deliverables implemented, 44/44 tests passing

---

## Deliverables

### Deliverable 1: NPC Archetype Schema
**File:** `aidm/schemas/npc_archetype.py` (NEW)

Implemented three frozen dataclasses:
- `NPCArchetype` — behavioral template for non-combat NPCs (9 fields)
- `DoctrineProfile` — tactical behavior template for creature categories (9 fields + `to_monster_doctrine()`)
- `NPCArchetypeRegistry` — top-level container for archetypes + doctrines

All support `to_dict()` / `from_dict()`. All frozen. Follows patterns from `aidm/schemas/vocabulary.py`.

### Deliverable 2: NPC Stage Implementation
**File:** `aidm/core/compile_stages/npc_archetypes.py` (NEW)

Implemented `NPCArchetypeStage(CompileStage)`:
- `stage_id` = `"npc_archetypes"`
- `stage_number` = 4
- `depends_on` = `("lexicon",)`
- Stub mode: generates 8 standard archetypes + 6 doctrine profiles deterministically
- LLM mode: falls back to stub (placeholder for future WO)
- Outputs: `npc_archetypes.json` + `doctrine_profiles.json`
- Seed derivation: `sha256("npc:{world_seed}")` clamped to 63-bit

**8 Archetypes:** shopkeeper, guard, noble, peasant, scholar, criminal, priest, innkeeper
**6 Doctrines:** pack_predator, ambusher, territorial_defender, mindless_aggressor, tactical_caster, cowardly_scavenger

Updated `aidm/core/compile_stages/__init__.py` to export `NPCArchetypeStage`.

### Deliverable 3: Cross-Reference with Existing Doctrine
**Method:** `DoctrineProfile.to_monster_doctrine(monster_id, source)`

Field mapping:
| DoctrineProfile | MonsterDoctrine |
|----------------|-----------------|
| `creature_types[0]` | `creature_type` |
| `aggression` | `tags` (mapped: timid→cowardly, cautious→animal_predator, aggressive→pack_hunter, berserk→berserker) |
| `pack_behavior` | `tags` (mapped: pack→pack_hunter, swarm→swarm_instinct) |
| `morale` | `tags` (mapped: cowardly→cowardly, steady→disciplined, fanatical→fanatical) |
| `preferred_tactics` | `allowed_tactics` (mapped to TacticClass values) |
| `retreat_threshold` | `notes` (e.g., "retreats at 25% HP") |
| `special_behaviors` | `notes` (appended) |

Tested with actual `MonsterDoctrine.from_dict()` import — confirmed compatible.

### Deliverable 4: Tests
**File:** `tests/test_compile_npc.py` (NEW) — **44 tests, all passing**

| Test Class | Count | Coverage |
|-----------|-------|----------|
| TestStubCounts | 4 | 8 archetypes + 6 doctrines produced |
| TestRoundTrip | 3 | to_dict/from_dict round-trip for all types |
| TestArchetypeIdUniqueness | 2 | All archetype_ids unique + prefix check |
| TestDoctrineIdUniqueness | 2 | All doctrine_ids unique + prefix check |
| TestRetreatThreshold | 2 | 0.0-1.0 range + type check |
| TestDoctrineConversion | 5 | MonsterDoctrine conversion + field mapping |
| TestStubDeterminism | 4 | Same seed → same output, seed derivation |
| TestStageInterface | 8 | CompileStage registration, stage_id, depends_on |
| TestFileOutput | 5 | JSON file existence, schema_version, world_id |
| TestSchemaValidation | 9 | Required fields, valid enum values, frozen check |

---

## Files Modified

| File | Action |
|------|--------|
| `aidm/schemas/npc_archetype.py` | NEW — Schema dataclasses |
| `aidm/core/compile_stages/npc_archetypes.py` | NEW — Stage 4 implementation |
| `aidm/core/compile_stages/__init__.py` | MODIFIED — Added NPCArchetypeStage export |
| `tests/test_compile_npc.py` | NEW — 44 tests |

## Files NOT Modified (as required)

- `aidm/schemas/doctrine.py` — Existing MonsterDoctrine (read-only reference)
- `aidm/data/content_pack/creatures.json` — Creature types (read-only reference)

---

## Design Decisions

1. **Used `_base.py` CompileStage interface** (not `world_compiler.py` CompileContext) — matches pattern used by LexiconStage and SemanticsStage.
2. **`to_monster_doctrine()` returns dict, not MonsterDoctrine** — avoids coupling schema module to doctrine module (boundary law). The dict is MonsterDoctrine.from_dict()-compatible.
3. **Provenance stored as plain dict** — follows WO spec. Not a frozen dataclass because provenance schemas may vary by stage.
4. **Two output files** (npc_archetypes.json + doctrine_profiles.json) — matches contract §3 bundle file tree.

---

## Test Run

```
44 passed in 0.31s
```

END OF COMPLETION REPORT

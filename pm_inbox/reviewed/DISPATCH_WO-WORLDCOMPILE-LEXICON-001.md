# Instruction Packet: Lexicon Generation Agent

**Work Order:** WO-WORLDCOMPILE-LEXICON-001 (World Compiler Stage 1 — Lexicon)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 1 (Stages 2, 5 depend on this)
**Deliverable Type:** Code implementation + tests
**Parallelization:** Runs after WO-WORLDCOMPILE-SCAFFOLD-001 lands. Parallel with Stages 3, 4, 6, 7.
**Dependency:** Requires `WorldCompiler` + `CompileStage` interface from scaffold WO.

---

## READ FIRST

Stage 1 assigns canonical world-flavored names to every mechanical ID in the content pack. This is the lexicon layer — it answers "what is SPELL_003 called in Ashenmoor?" The output populates a `VocabularyRegistry` (already implemented in `aidm/schemas/vocabulary.py` + `aidm/lens/vocabulary_registry.py`).

**The naming process:**
1. Read all template IDs from the content pack (SPELL_001..N, CREATURE_001..N, FEAT_001..N)
2. For each ID, generate a world-flavored name using the LLM + world theme brief + naming style
3. Generate taxonomy categories for this world
4. Assign `lexicon_id` = `sha256(world_seed + content_id)[:16]`
5. Output `lexicon.json` conforming to `VocabularyRegistry` schema

**Critical constraint:** Names must pass the Recognition Test — no name recognizable as originating from D&D/WotC content.

---

## YOUR TASK

### Deliverable 1: Lexicon Stage Implementation

**File:** `aidm/core/compile_stages/lexicon.py` (NEW)

Implement `LexiconStage(CompileStage)`:

```python
class LexiconStage(CompileStage):
    """Stage 1: Generate world-flavored names for all content pack IDs."""

    @property
    def stage_id(self) -> str: return "lexicon"

    @property
    def stage_number(self) -> int: return 1

    @property
    def depends_on(self) -> tuple: return ()  # No dependencies

    def execute(self, context: CompileContext) -> StageResult:
        """
        1. Enumerate all template IDs from content pack
        2. Group by domain (spell, creature, feat)
        3. For each group, generate names via LLM
        4. Build VocabularyRegistry
        5. Write lexicon.json to workspace
        """
```

**LLM Prompt Design:**
- Input: world theme brief (genre, tone, naming_style) + domain (spell/creature/feat) + mechanical summary (effect_type, school_category, etc.)
- Output: world_name, short_description, category, aliases
- Batch processing: send groups of 10-20 IDs per LLM call for efficiency
- Temperature: 0.0 for determinism (or use seed if model supports it)

**Name Generation Rules:**
1. Names must fit the world's naming_style (e.g., "anglo_saxon" → "Searing Gale", not "Fireball")
2. Names must pass the Recognition Test: no D&D-recognizable names
3. Names must be unique within the lexicon
4. Short descriptions ≤ 120 characters
5. Categories must form a coherent world taxonomy

**`lexicon_id` Assignment:**
```python
import hashlib
lexicon_id = hashlib.sha256(f"{world_seed}:{content_id}".encode()).hexdigest()[:16]
```

### Deliverable 2: LLM Integration

The stage must use `llama-cpp-python` (already in project) for LLM inference. Reference the existing Spark adapter pattern in `aidm/immersion/spark_adapter.py` for model loading.

**However:** To support testing WITHOUT a loaded LLM, implement a **stub mode**:
- If `toolchain_pins.llm_model_id == "stub"`, generate names deterministically from the seed + template_id (e.g., `f"Name_{template_id}_{seed % 1000}"`)
- Stub mode must still produce valid VocabularyRegistry output
- Stub mode is the DEFAULT for tests

### Deliverable 3: Tests

**File:** `tests/test_compile_lexicon.py` (NEW)

1. Stub mode produces deterministic names (same seed → same names)
2. Stub mode produces valid VocabularyRegistry (round-trip via from_dict)
3. All template IDs from content pack get a lexicon entry
4. No duplicate content_ids in output
5. No duplicate lexicon_ids in output
6. lexicon_id is deterministic: sha256(seed:content_id)[:16]
7. Short descriptions ≤ 120 characters
8. Stage registers correctly with WorldCompiler
9. Stage depends_on is empty (no dependencies)
10. Stage writes lexicon.json to workspace

Create a fixture with a minimal content pack (5 spells, 3 creatures, 2 feats).

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| VocabularyRegistry schema | `aidm/schemas/vocabulary.py` | Output must conform to this |
| VocabularyRegistryLoader | `aidm/lens/vocabulary_registry.py` | Output must be loadable by this |
| WorldCompiler + CompileStage | `aidm/core/world_compiler.py` | May or may not exist yet — if not, define compatible interface |
| Spark adapter (LLM pattern) | `aidm/immersion/spark_adapter.py` | Reference for LLM loading |
| Content pack data | `aidm/data/content_pack/` | Read-only input |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/contracts/WORLD_COMPILER.md` § 2.1 | Stage 1 specification |
| 1 | `aidm/schemas/vocabulary.py` | VocabularyEntry, VocabularyRegistry schemas |
| 1 | `aidm/lens/vocabulary_registry.py` | Loader pattern — output must be loadable |
| 2 | `docs/schemas/vocabulary_registry.schema.json` | Canonical JSON schema |
| 2 | `aidm/core/world_compiler.py` | CompileStage interface (if exists) |
| 3 | `aidm/immersion/spark_adapter.py` | LLM loading pattern |

## STOP CONDITIONS

- If `WorldCompiler` / `CompileStage` doesn't exist yet, define a compatible interface locally and note it in your completion report. The scaffold WO will provide the canonical version.
- If content pack JSON files don't exist yet, use the fixture data.
- LLM integration is optional for this WO. Stub mode is sufficient for delivery. Real LLM integration can be wired in when the model is available.

## DELIVERY

- New files: `aidm/core/compile_stages/__init__.py`, `aidm/core/compile_stages/lexicon.py`, `tests/test_compile_lexicon.py`
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-WORLDCOMPILE-LEXICON-001_completion.md`

## RULES

- Output MUST be a valid `VocabularyRegistry` loadable by `VocabularyRegistryLoader`
- No original content names in the lexicon output
- Stub mode must be deterministic: same seed → same names every time
- Follow existing code style
- The `aidm/core/compile_stages/` directory is new — create `__init__.py`

---

END OF INSTRUCTION PACKET

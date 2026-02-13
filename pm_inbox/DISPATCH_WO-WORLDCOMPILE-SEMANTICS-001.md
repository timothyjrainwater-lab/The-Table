# Instruction Packet: Presentation Semantics Binding Agent

**Work Order:** WO-WORLDCOMPILE-SEMANTICS-001 (World Compiler Stage 3 — Presentation Semantics)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 1 (Stages 2, 5 depend on this)
**Deliverable Type:** Code implementation + tests
**Parallelization:** Runs after WO-WORLDCOMPILE-SCAFFOLD-001 lands. Parallel with Stages 1, 4, 6, 7.
**Dependency:** Requires `CompileStage` interface from scaffold WO.

---

## READ FIRST

Stage 3 assigns AD-007 presentation semantics (Layer B) to every ability and event category in the content pack. This tells the renderer and narrator HOW effects look and behave — delivery mode, staging, origin, scale, VFX/SFX tags — without describing them in prose.

The output schema already exists: `PresentationSemanticsRegistry` in `aidm/schemas/presentation_semantics.py` (delivered by WO-AD007-IMPL-001).

**The binding process:**
1. Read all ability template IDs from content pack (spells, feats with active effects)
2. For each ability, read its mechanical data (effect_type, target_type, aoe_shape, damage_type, etc.)
3. Map mechanical data → presentation semantics using rules + optional LLM enrichment
4. For each event category, assign default presentation semantics
5. Output `presentation_semantics.json` conforming to `PresentationSemanticsRegistry`

---

## YOUR TASK

### Deliverable 1: Semantics Stage Implementation

**File:** `aidm/core/compile_stages/semantics.py` (NEW)

Implement `SemanticsStage(CompileStage)`:

```python
class SemanticsStage(CompileStage):
    """Stage 3: Generate AD-007 presentation semantics bindings."""

    @property
    def stage_id(self) -> str: return "semantics"

    @property
    def stage_number(self) -> int: return 3

    @property
    def depends_on(self) -> tuple: return ()  # No stage dependencies

    def execute(self, context: CompileContext) -> StageResult:
        """
        1. Enumerate all abilities from content pack
        2. Map each ability's mechanics to presentation semantics
        3. Generate event category defaults
        4. Build PresentationSemanticsRegistry
        5. Write presentation_semantics.json to workspace
        """
```

### Deliverable 2: Mechanical-to-Semantics Mapping

This is the core logic. Build a **rule-based mapper** that infers presentation semantics from mechanical data:

**Delivery Mode Mapping:**
| Mechanical Data | → DeliveryMode |
|----------------|----------------|
| `target_type == "ray"` | `RAY` |
| `target_type == "touch"` | `TOUCH` |
| `target_type == "self"` | `SELF` |
| `aoe_shape == "burst"` | `BURST_FROM_POINT` |
| `aoe_shape == "cone"` | `CONE` |
| `aoe_shape == "line"` | `LINE` |
| `aoe_shape == "emanation"` | `EMANATION` |
| `effect_type == "summoning"` | `SUMMON` |
| `target_type == "area"` + no aoe_shape | `BURST_FROM_POINT` |
| `target_type == "single"` + ranged | `PROJECTILE` |
| Default | `PROJECTILE` |

**Staging Mapping:**
| Mechanical Data | → Staging |
|----------------|-----------|
| `duration == "instantaneous"` | `INSTANT` |
| `concentration == True` | `CHANNELED` |
| `duration contains "round"` | `LINGER` |
| `aoe_shape == "burst"` + instantaneous | `TRAVEL_THEN_DETONATE` |
| Default | `INSTANT` |

**Scale Mapping:**
| Mechanical Data | → Scale |
|----------------|---------|
| `aoe_radius_ft >= 40` or tier >= 7 | `CATASTROPHIC` |
| `aoe_radius_ft >= 20` or tier >= 5 | `DRAMATIC` |
| `aoe_radius_ft >= 10` or tier >= 3 | `MODERATE` |
| Default | `SUBTLE` |

**VFX Tags:** Derive from damage_type, school_category, effect_type:
- `damage_type == "fire"` → `("fire", "glow", "heat_distortion")`
- `damage_type == "cold"` → `("frost", "ice_crystals", "mist")`
- `damage_type == "electricity"` → `("lightning", "spark", "arc")`
- `effect_type == "healing"` → `("radiance", "warmth")`
- `school_category == "necromancy"` → `("shadow", "decay")`
- `school_category == "illusion"` → `("shimmer", "distortion")`

**SFX Tags:** Similar derivation:
- `damage_type == "fire"` → `("whoosh", "crackle")`
- `damage_type == "cold"` → `("crystallize", "shatter")`
- `damage_type == "electricity"` → `("zap", "thunder")`

**For feats:** Only feats with `trigger` or `grants_action` get ability entries. Passive feats (proficiency, skill modifiers) don't need presentation semantics.

**For event categories:** Provide defaults for all 18 `EventCategory` enum values. These are generic (not world-themed) and serve as fallbacks.

### Deliverable 3: World Theme Enrichment (Optional LLM)

If the LLM is available (not stub mode), use it to:
- Generate world-themed VFX/SFX tag variants (e.g., in a volcanic world, cold spells might have "obsidian_frost" instead of "ice_crystals")
- Generate `residue` descriptions (what's left after the effect — scorch marks, frost patches)

If stub mode (`toolchain_pins.llm_model_id == "stub"`):
- Use the rule-based mapping only
- No world-theme enrichment
- Still valid output

### Deliverable 4: Tests

**File:** `tests/test_compile_semantics.py` (NEW)

1. Rule-based mapping: fire damage spell → correct delivery_mode, staging, scale, vfx_tags
2. Rule-based mapping: touch spell → TOUCH delivery_mode
3. Rule-based mapping: cone AoE → CONE delivery_mode
4. Rule-based mapping: high-tier spell → CATASTROPHIC scale
5. Rule-based mapping: healing spell → correct vfx/sfx tags
6. All event categories get default semantics
7. Output is valid PresentationSemanticsRegistry (loadable by PresentationRegistryLoader)
8. No duplicate content_ids in output
9. Stub mode produces deterministic output
10. Passive feats are excluded from ability entries
11. Active feats (with trigger/grants_action) get ability entries
12. Stage registers correctly with WorldCompiler

Create fixtures with 5 spells covering: fire AoE burst, cold touch, lightning line, healing single, illusion self.

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| PresentationSemanticsRegistry | `aidm/schemas/presentation_semantics.py` | Output must conform to this |
| PresentationRegistryLoader | `aidm/lens/presentation_registry.py` | Output must be loadable by this |
| DeliveryMode, Staging, Scale enums | `aidm/schemas/presentation_semantics.py` | Use these enums |
| EventCategory enum | `aidm/schemas/presentation_semantics.py` | Cover all 18 values |
| SemanticsProvenance | `aidm/schemas/presentation_semantics.py` | Use for provenance records |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/contracts/WORLD_COMPILER.md` § 2.3 | Stage 3 specification |
| 1 | `aidm/schemas/presentation_semantics.py` | All enum values + dataclass schemas |
| 1 | `aidm/lens/presentation_registry.py` | Loader — output must be loadable |
| 2 | `docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md` | Full AD-007 rationale |
| 2 | `aidm/data/content_pack/feats.json` | Live feat data for reference |

## STOP CONDITIONS

- If `CompileStage` interface doesn't exist yet, define compatible interface locally.
- If content pack schema classes don't exist yet, read the JSON files directly.

## DELIVERY

- New files: `aidm/core/compile_stages/semantics.py`, `tests/test_compile_semantics.py`
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-WORLDCOMPILE-SEMANTICS-001_completion.md`

## RULES

- Output MUST be a valid `PresentationSemanticsRegistry`
- Use the exact enum values from `aidm/schemas/presentation_semantics.py`
- Rule-based mapping is the minimum. LLM enrichment is optional.
- Follow existing code style

---

END OF INSTRUCTION PACKET

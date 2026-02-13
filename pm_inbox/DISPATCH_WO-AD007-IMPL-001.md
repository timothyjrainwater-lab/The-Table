# Instruction Packet: AD-007 Implementation Agent

**Work Order:** WO-AD007-IMPL-001 (Presentation Semantics Python Implementation)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 1 (Critical path — blocks World Compiler, narration constraints, battle map animations)
**Deliverable Type:** Code implementation + enforcement tests

---

## READ FIRST

AD-007 is ratified. The three-layer description model (Behavior / Presentation Semantics / Narration) is the keystone architectural contract. The JSON schema already exists at `docs/schemas/presentation_semantics_registry.schema.json`. What's missing is:

1. Python frozen dataclasses that mirror the JSON schema
2. A registry loader that reads compiled presentation semantics from a world bundle
3. Enforcement tests proving Spark respects Layer B constraints
4. Integration with NarrativeBrief so presentation semantics flow to Spark

---

## YOUR TASK

### Deliverable 1: Frozen Dataclasses

**File:** `aidm/schemas/presentation_semantics.py` (NEW)

Implement frozen dataclasses that mirror the JSON schema exactly:

- `AbilityPresentationEntry` — frozen dataclass with fields: `content_id`, `delivery_mode`, `staging`, `origin_rule`, `vfx_tags`, `sfx_tags`, `scale`, `residue`, `ui_description`, `token_style`, `handout_style`, `contraindications`, `provenance`
- `EventPresentationEntry` — frozen dataclass with fields: `event_category`, `default_scale`, `default_vfx_tags`, `default_sfx_tags`, `default_residue`, `narration_priority`
- `SemanticsProvenance` — frozen dataclass with fields: `source`, `compiler_version`, `seed_used`, `content_pack_id`, `template_ids`, `llm_output_hash`
- `PresentationSemanticsRegistry` — frozen dataclass with fields: `schema_version`, `world_id`, `compiler_version`, `ability_entry_count`, `event_entry_count`, `ability_entries`, `event_entries`

All enum fields must use Python `Enum` types:
- `DeliveryMode`: projectile, beam, burst_from_point, aura, cone, line, touch, self, summon, teleport, emanation, gaze
- `Staging`: travel_then_detonate, instant, linger, pulses, channeled, delayed, expanding, fading
- `OriginRule`: from_caster, from_chosen_point, from_object, from_target, from_ground, ambient
- `Scale`: subtle, moderate, dramatic, catastrophic
- `NarrationPriority`: always_narrate, narrate_if_significant, narrate_on_request, never_narrate
- `EventCategory`: melee_attack, ranged_attack, combat_maneuver, saving_throw, skill_check, condition_applied, condition_removed, hp_change, entity_defeated, movement, environmental_damage, environmental_effect, social_interaction, discovery, rest, trade, turn_boundary, round_boundary

All dataclasses must support `to_dict()` / `from_dict()` serialization matching the JSON schema field names. Use the same pattern as other schemas in `aidm/schemas/`.

### Deliverable 2: Registry Loader

**File:** `aidm/lens/presentation_registry.py` (NEW)

Implement a registry that:
1. Loads a `PresentationSemanticsRegistry` from a JSON file (world bundle output)
2. Provides lookup: `get_ability_semantics(content_id: str) -> Optional[AbilityPresentationEntry]`
3. Provides lookup: `get_event_semantics(event_category: EventCategory) -> Optional[EventPresentationEntry]`
4. Is immutable after loading (no mutation methods)
5. Validates that `ability_entry_count` matches `len(ability_entries)` on load
6. Raises on duplicate `content_id` or `event_category`

### Deliverable 3: NarrativeBrief Integration

**File:** `aidm/lens/narrative_brief.py` (MODIFY)

Add presentation semantics to the NarrativeBrief so Spark receives Layer B constraints:
1. Add an optional `presentation_semantics: Optional[AbilityPresentationEntry]` field to the brief (or a list if multiple abilities fired)
2. When assembling the brief for an ability-related event, look up the presentation semantics from the registry and attach them
3. The NarrativeBrief already flows to Spark — this just enriches what Spark receives

### Deliverable 4: Enforcement Tests

**File:** `tests/test_presentation_semantics.py` (NEW)

Tests:
1. All enum values match the JSON schema exactly
2. Frozen dataclass rejects mutation (`TypeError` on attribute set)
3. `to_dict()` / `from_dict()` round-trip preserves all fields
4. Registry loader validates entry counts
5. Registry loader rejects duplicate content_id
6. Registry lookup returns correct entry by content_id
7. Registry returns None for unknown content_id
8. NarrativeBrief includes presentation semantics when available

**File:** `tests/test_boundary_law.py` (MODIFY — add BL check)

Add test:
- Spark modules (aidm/spark/) must NOT import from `aidm/schemas/presentation_semantics.py` directly — they receive semantics via NarrativeBrief only. This enforces the one-way valve.

---

## WHAT EXISTS (DO NOT MODIFY unless specified)

| Component | Location | Status |
|-----------|----------|--------|
| JSON schema | `docs/schemas/presentation_semantics_registry.schema.json` | Canonical — match exactly |
| AD-007 decision | `docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md` | Ratified — do not modify |
| NarrativeBrief | `aidm/lens/narrative_brief.py` | Working — modify to add semantics field |
| Existing schemas pattern | `aidm/schemas/intents.py`, `aidm/schemas/attack.py` | Follow same frozen dataclass pattern |
| Boundary law tests | `tests/test_boundary_law.py` | Add new BL check, do not modify existing |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/schemas/presentation_semantics_registry.schema.json` | Canonical JSON schema — match field names exactly |
| 1 | `docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md` | Three-layer model definition, enum values, examples |
| 2 | `aidm/schemas/intents.py` | Pattern for frozen dataclasses with to_dict/from_dict |
| 2 | `aidm/schemas/attack.py` | Pattern for frozen dataclasses |
| 2 | `aidm/lens/narrative_brief.py` | Current NarrativeBrief structure |
| 3 | `aidm/schemas/entity_fields.py` | EF.* constants pattern |

## STOP CONDITIONS

- If the JSON schema has fields not documented in AD-007, include them in the dataclass but flag in completion report.
- If NarrativeBrief modification breaks existing tests, fix the test expectations (the new field should be Optional with default None, so existing tests should still pass).
- If `aidm/schemas/` uses a pattern different from standard frozen dataclasses (e.g., attrs, pydantic), match that pattern instead.

## DELIVERY

- New files: `aidm/schemas/presentation_semantics.py`, `aidm/lens/presentation_registry.py`, `tests/test_presentation_semantics.py`
- Modified files: `aidm/lens/narrative_brief.py`, `tests/test_boundary_law.py`
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-AD007-IMPL-001_completion.md`

## RULES

- All dataclasses MUST be frozen (`@dataclass(frozen=True)`)
- All enum fields MUST use Python Enum types, not raw strings
- Field names in `to_dict()` output MUST match JSON schema field names exactly
- No imports from `aidm/core/` — this is a schemas + lens layer component
- Follow existing test patterns in `tests/`
- Do NOT add presentation semantics to Box events — Box does not know about Layer B

---

END OF INSTRUCTION PACKET

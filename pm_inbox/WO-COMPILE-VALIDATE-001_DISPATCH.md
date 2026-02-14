# WO-COMPILE-VALIDATE-001: Compile-Time Layer A vs Layer B Cross-Validation + content_id Emission

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 1
**Priority:** P2 — Data integrity. Catches content mismatches at compile time instead of runtime. Also unblocks the GAP-B-001 pipeline by adding content_id to resolver event payloads.
**Source:** RQ-SPRINT-005 (Content Trust Verification), GAP-B-001 dormancy finding
**Depends on:** None (GAP-B-001 already committed, registries already exist)

---

## Target Lock

Two things in one WO because they're coupled:

1. **Compile-time validation:** The World Compiler produces both `RuleEntry` (Layer A mechanics) and `AbilityPresentationEntry` (Layer B presentation) keyed by `content_id`. Nothing currently validates that they're consistent. A spell with `target_type: "single"` could have `delivery_mode: BURST_FROM_POINT` and nobody catches it until a player sees broken narration.

2. **content_id emission:** GAP-B-001 wired the presentation_semantics pipeline (commit e9a9371), but it's dormant because no resolver events emit `content_id` in their payloads. The lookup in `narrative_brief.py:612-615` works — it just never finds a content_id to look up. Adding content_id to spell/ability event payloads activates Layer B narration for all abilities.

## Binary Decisions

1. **Where does the validator live?** New compile stage or post-compile validation pass in `aidm/core/compile_stages/`. It runs after `semantics.py` produces the registry.
2. **What happens on FAIL?** P0 rules (CT-001/002/003) block compilation. P3 rules (CT-004-007) emit warnings to world metadata.
3. **Where does content_id get added?** Resolver event payloads. When a resolver processes a spell or ability, it includes `content_id` in the event payload so the Lens can look it up.
4. **Which resolvers emit content_id?** Any resolver that handles spell effects or ability activations. The spell resolver is the primary target. Other resolvers (maneuver, environmental) emit content_id when applicable.
5. **What if a resolver doesn't have a content_id?** Events without content_id get `presentation_semantics: None` (current behavior). No breakage.

## Contract Spec

### Part A: Compile-Time Cross-Validation

#### Change A1: CompileValidator Module

New file `aidm/core/compile_stages/cross_validate.py`:

```python
@dataclass(frozen=True)
class CompileViolation:
    check_id: str       # "CT-001", "CT-002", etc.
    content_id: str     # Which ability
    severity: str       # "FAIL" or "WARN"
    detail: str         # Human-readable

def cross_validate(rule_entries: dict, ability_entries: dict) -> list[CompileViolation]:
    """Compare Layer A RuleParameters against Layer B AbilityPresentationEntry for each content_id."""
```

#### Change A2: P0 Checks (FAIL — block compilation)

**CT-001: Delivery Mode vs Target Type**
- If `target_type == "single"` and `delivery_mode` in {BURST_FROM_POINT, CONE, LINE, EMANATION}: FAIL

**CT-002: Delivery Mode vs Area Shape**
- If `area_shape == "burst"` and `delivery_mode != BURST_FROM_POINT`: FAIL
- If `area_shape == "cone"` and `delivery_mode != CONE`: FAIL
- If `area_shape == "line"` and `delivery_mode != LINE`: FAIL

**CT-003: Origin Rule vs Delivery Mode**
- If `range_ft == 0` and (`origin_rule != FROM_CASTER` or `delivery_mode != TOUCH`): FAIL

#### Change A3: P3 Checks (WARN — log to world metadata)

**CT-004: Scale vs Damage Magnitude**
- Parse damage dice string. Thresholds: SUBTLE ≤ 2d6, MODERATE ≤ 6d6, DRAMATIC ≤ 12d6, CATASTROPHIC > 12d6
- If scale doesn't match damage band: WARN

**CT-005: Save Type vs Staging**
- If `save_type is None` and `staging == DELAYED`: WARN

**CT-006: Contraindication Self-Conflict**
- If any tag in `contraindications` appears in `vfx_tags` or `sfx_tags` of same entry: WARN

**CT-007: Residue vs Staging**
- If `duration_unit == "instantaneous"` and `residue` is non-empty: WARN
- If `staging == LINGER` and `residue` is empty: WARN

#### Change A4: Integration into World Compiler Pipeline

Call `cross_validate()` after semantics stage. If any FAIL violations exist, raise `CompileValidationError`. WARN violations logged to world metadata JSON.

### Part B: content_id Emission in Resolver Events

#### Change B1: Spell Resolver Event Payloads

When the spell resolver emits damage, condition, or save events for a spell, include `"content_id": spell.content_id` in the event payload. This is the primary activation point — most abilities with presentation semantics are spells.

#### Change B2: Other Resolver Event Payloads

For ability activations (feats, class features) that have content_ids, include the content_id in the event payload. This is additive — resolvers that don't have a content_id simply omit the field.

#### Change B3: Verify Pipeline Activation

After adding content_id to event payloads, the existing code in `narrative_brief.py:612-615` should find the content_id and populate `presentation_semantics`. Write a test that confirms: spell event → content_id in payload → NarrativeBrief.presentation_semantics is not None.

### Constraints

- Do NOT modify the PresentationSemanticsRegistry schema or loader
- Do NOT modify AbilityPresentationEntry fields
- Do NOT add new fields to RuleParameters
- Do NOT change resolver logic beyond adding content_id to payloads
- Compile-time checks must be purely read-only — they compare data, not modify it
- WARN violations must not block compilation
- Existing tests must pass without modification
- content_id emission must be additive — events without content_id remain valid

### Boundary Laws Affected

- BL-021 (Events record results, not formulas): NOT VIOLATED — content_id is a string identifier, not a formula
- BL-012 (reduce_event): NOT AFFECTED — reducer doesn't consume content_id

## Success Criteria

- [ ] `cross_validate()` function exists and runs all 7 CT checks
- [ ] CT-001/002/003 violations block world compilation
- [ ] CT-004-007 violations produce warnings but allow compilation
- [ ] CompileViolation dataclass captures check_id, content_id, severity, detail
- [ ] Spell resolver events include content_id in payload
- [ ] NarrativeBrief.presentation_semantics populates from event content_id (GAP-B-001 pipeline activated)
- [ ] End-to-end test: spell cast → event with content_id → NarrativeBrief has presentation_semantics
- [ ] Existing tests pass without modification
- [ ] New tests: one per CT check, content_id emission test, pipeline activation test

## Files Expected to Change

- New: `aidm/core/compile_stages/cross_validate.py`
- World compiler integration point (wherever compile stages are orchestrated)
- Spell resolver — content_id in event payloads
- Other resolvers that handle abilities — content_id in event payloads (where applicable)
- Test files for CT checks and content_id emission

## Files NOT to Change

- `aidm/schemas/presentation_semantics.py` — schema stays
- `aidm/lens/presentation_registry.py` — loader stays
- `aidm/lens/narrative_brief.py` — already handles content_id lookup (GAP-B-001)
- Gold masters — unless world compilation output changes (WARN metadata)

---

*End of WO-COMPILE-VALIDATE-001*

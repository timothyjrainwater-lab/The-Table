# Intent Bridge Compliance Checklist
## Machine-Detectable Violations for Contract Enforcement

**Document ID:** RQ-INTENT-001-COMPLIANCE
**Version:** 1.0
**Date:** 2026-02-12
**Reference:** `docs/contracts/INTENT_BRIDGE.md` (INTENT_BRIDGE v1)
**Schema:** `docs/schemas/intent_request.schema.json`

---

## Purpose

This checklist defines **machine-detectable** compliance signals for the Intent
Bridge contract. Each violation is testable with regex patterns, JSON schema
validation, or deterministic unit assertions. The checklist is organized by
violation category and includes the regex or test strategy for each.

---

## Category 1: Forbidden Coaching Language

These violations detect coaching, warnings, or tactical advice in
clarification output. Scan ALL strings produced by the ClarificationEngine
and IntentBridge that are player-visible.

**Scan targets:**
- `ClarificationRequest.message` (intent_bridge.py)
- `ClarificationRequest.prompt` (clarification_loop.py)
- `ClarificationEngine.generate_soft_confirmation()` output
- `ClarificationEngine.generate_impossibility_feedback()` output

### FC-001: "Are you sure" coaching pattern
```regex
(?i)\bare\s+you\s+sure\b
```
**Violation:** Implies the action is bad. Neutral bridges do not question player decisions.

### FC-002: Attack of opportunity warning
```regex
(?i)\b(attack\s+of\s+opportunity|provoke|AoO)\b
```
**Violation:** Reveals mechanical consequence before resolution.

### FC-003: Tactical suggestion
```regex
(?i)\b(you\s+might\s+want|you\s+should|consider|I\s+recommend|the\s+better\s+option|you\s+could\s+try|a\s+better\s+choice)\b
```
**Violation:** Provides tactical advice.

### FC-004: Negative judgment
```regex
(?i)\b(not\s+a\s+good\s+idea|bad\s+idea|risky|dangerous\s+move|unwise)\b
```
**Violation:** Value judgment on player's declared action.

### FC-005: HP/AC/Save DC disclosure
```regex
(?i)\b(\d+\s*(hit\s*points?|hp|AC|armor\s*class|DC|save\s*DC|difficulty\s*class))\b
```
**Violation:** Reveals specific mechanical values.

### FC-006: Generic mechanical disclosure
```regex
(?i)\b(has\s+resistance|has\s+immunity|is\s+vulnerable|damage\s+reduction|spell\s+resistance|SR\s+\d+)\b
```
**Violation:** Reveals target's mechanical properties.

### FC-007: Range/movement legality
```regex
(?i)\b(won't\s+reach|can't\s+reach|out\s+of\s+range|not\s+enough\s+movement|too\s+far)\b
```
**Violation:** Bridge is computing mechanical legality (Box's job).
**Exception:** `generate_impossibility_feedback()` may use "out of range" when Box
has already determined impossibility and the bridge is formatting the feedback.
This exception applies ONLY when the feedback is post-resolution, not pre-resolution.

### FC-008: System-language framing
```regex
(?i)^(Warning|Caution|Error|Notice|Alert|System):
```
**Violation:** Clarification must sound like a DM, not a system prompt.

### FC-009: "Keep in mind" pre-emptive coaching
```regex
(?i)\b(keep\s+in\s+mind|be\s+aware|note\s+that|remember\s+that|don't\s+forget)\b
```
**Violation:** Pre-emptive coaching disguised as helpfulness.

### FC-010: Modifier/bonus disclosure
```regex
(?i)\b(attack\s+bonus|damage\s+bonus|modifier|saving\s+throw|BAB|base\s+attack)\b
```
**Violation:** Reveals mechanical internals.

---

## Category 2: Schema Validation

These violations are testable with JSON Schema validation against
`docs/schemas/intent_request.schema.json`.

### SV-001: ActionRequest missing required fields
**Test:** Validate every ActionRequest output against the JSON schema.
```python
import jsonschema
schema = json.load(open("docs/schemas/intent_request.schema.json"))
jsonschema.validate(action_request_dict, schema)
```
**Violation:** Any validation error = contract breach.

### SV-002: needs_clarification without clarify payload
**Test:** If `status == "needs_clarification"`, `clarify` field must be present.
```python
assert action_request["status"] != "needs_clarification" or "clarify" in action_request
```

### SV-003: reject without reject_reason
**Test:** If `status == "reject"`, `reject_reason` field must be present.
```python
assert action_request["status"] != "reject" or "reject_reason" in action_request
```

### SV-004: Target entity_id missing when selector_type is "entity"
**Test:** Schema conditional validation.
```python
for target in action_request.get("targets", []):
    if target["selector_type"] == "entity":
        assert "entity_id" in target and target["entity_id"]
```

### SV-005: Instrument ref missing when type requires it
**Test:** Schema conditional validation.
```python
instrument = action_request.get("instrument", {})
if instrument.get("instrument_type") in ("weapon", "spell", "ability", "item"):
    assert "ref" in instrument and instrument["ref"]
```

---

## Category 3: Determinism Invariants

These violations are testable by running the same input twice and comparing
outputs.

### DI-001: Same input produces different ActionRequest
**Test:** Run bridge with (same state snapshot + same transcript + same STM
context) twice. Compare outputs.
```python
result_a = bridge.resolve(parse_result, view, stm_context)
result_b = bridge.resolve(parse_result, view, stm_context)
assert result_a == result_b  # Structural equality
```
**Violation:** Any difference in output fields.

### DI-002: Candidate ordering varies between runs
**Test:** When status is `needs_clarification`, verify options ordering is
stable across runs.
```python
if result_a["status"] == "needs_clarification":
    assert result_a["clarify"]["options"] == result_b["clarify"]["options"]
```

### DI-003: Non-deterministic entity resolution
**Test:** Same `target_ref` against same world state always resolves to same
`entity_id`.
```python
id_a = bridge._resolve_entity_name("goblin", view, exclude_id=None)
id_b = bridge._resolve_entity_name("goblin", view, exclude_id=None)
assert id_a == id_b
```

---

## Category 4: Authority Boundary

These violations detect the bridge exceeding its authority.

### AB-001: Bridge writes to world state
**Test:** Verify FrozenWorldStateView usage (BL-020). The bridge constructor
must not accept mutable WorldState.
```python
# Bridge should only accept FrozenWorldStateView, not WorldState
assert isinstance(view_param, FrozenWorldStateView)
```

### AB-002: Bridge computes mechanical legality
**Test:** Bridge should not import or call any resolver function
(attack_resolver, damage_calculator, spell_resolver.resolve, movement checker).
```regex
# Scan intent_bridge.py imports for forbidden modules
(?i)from\s+aidm\.core\.(attack_resolver|damage|movement_resolver|ac_calculator|save_resolver)
```
**Exception:** `from aidm.core.spell_resolver import SpellCastIntent` is allowed
because `SpellCastIntent` is a data schema, not a resolution function.

### AB-003: Bridge generates random values
**Test:** Bridge must not import `random`, `secrets`, or call dice-rolling functions.
```regex
# Scan intent_bridge.py, clarification_loop.py, voice_intent_parser.py
(?i)\b(import\s+random|from\s+random|secrets\.|random\.)\b
```

### AB-004: Bridge decides action legality
**Test:** No `if` branches in bridge code that check AC, HP, spell slots,
movement speed, or similar mechanical values.
```regex
# Scan intent_bridge.py for mechanical field access
(?i)\b(\.ac\b|\.hp\b|\.hit_points|\.spell_slots|\.movement_speed|\.speed\b)
```
**Note:** `.speed` in entity lookup for informational purposes (e.g., constraint
annotation) is allowed. `.speed` used in a conditional that blocks the action is
a violation.

---

## Category 5: Content Independence

### CI-001: D&D-specific vocabulary in schema field names
**Test:** Scan `intent_request.schema.json` field names for D&D-specific terms.
```regex
# In schema field names (keys in "properties" objects)
(?i)\b(armor_class|hit_points|spell_slot|saving_throw|base_attack_bonus|challenge_rating)\b
```
**Violation:** Schema field names must be game-system-agnostic.

### CI-002: Hardcoded D&D creature names in bridge logic
**Test:** Scan bridge code for hardcoded creature names used in resolution logic.
```regex
# In intent_bridge.py conditional logic (not in test files or comments)
(?i)\b(goblin|orc|dragon|beholder|mind_flayer|lich|tarrasque)\b
```
**Exception:** Creature names in test files, test vectors, and comments are allowed.
Creature names in voice_intent_parser.py's keyword lists are a known gap
(the parser uses a static list of entity names as a heuristic; this should
eventually be replaced with world-state entity lookup).

### CI-003: Hardcoded spell names in contract schema
**Test:** Scan `intent_request.schema.json` for hardcoded spell names.
```regex
# In schema file
(?i)\b(fireball|magic\s*missile|lightning\s*bolt|cure\s*wounds|shield)\b
```
**Exception:** Spell names in `examples` fields are allowed for documentation.
Spell names in `enum` arrays are a violation.

---

## Category 6: Clarification Loop Integrity

### CL-001: Clarification options exceed maximum
**Test:** Every `Clarify.options` array must have 2-6 elements.
```python
clarify = action_request.get("clarify", {})
options = clarify.get("options", [])
assert 2 <= len(options) <= 6
```

### CL-002: Clarification options contain mechanical values
**Test:** Apply FC-005 and FC-006 regex patterns to all option labels.
```python
for option in clarify.get("options", []):
    assert not re.search(r'(?i)\b\d+\s*(hp|AC|DC)\b', option["label"])
```

### CL-003: Clarification exceeds 3 rounds
**Test:** Track clarification round count per intent. Violation if round > 3.
```python
assert clarification_round_count <= 3
```

### CL-004: Partial resolution allowed
**Test:** Bridge must not return `status: "ok"` with missing required fields.
```python
if action_request["status"] == "ok":
    # All required fields for this intent_type must be present
    assert validate_required_fields(action_request)
```

---

## Summary Table

| ID | Category | Detection Method | Severity |
|----|----------|-----------------|----------|
| FC-001 | Coaching | Regex | Critical |
| FC-002 | Coaching | Regex | Critical |
| FC-003 | Coaching | Regex | Critical |
| FC-004 | Coaching | Regex | High |
| FC-005 | Coaching | Regex | Critical |
| FC-006 | Coaching | Regex | Critical |
| FC-007 | Coaching | Regex + context | High |
| FC-008 | Coaching | Regex | Medium |
| FC-009 | Coaching | Regex | High |
| FC-010 | Coaching | Regex | Critical |
| SV-001 | Schema | JSON Schema validator | High |
| SV-002 | Schema | Assertion | High |
| SV-003 | Schema | Assertion | High |
| SV-004 | Schema | Assertion | Medium |
| SV-005 | Schema | Assertion | Medium |
| DI-001 | Determinism | Comparison test | Critical |
| DI-002 | Determinism | Comparison test | High |
| DI-003 | Determinism | Comparison test | High |
| AB-001 | Authority | Type assertion | Critical |
| AB-002 | Authority | Import scan (regex) | Critical |
| AB-003 | Authority | Import scan (regex) | Critical |
| AB-004 | Authority | Code scan (regex) | High |
| CI-001 | Content independence | Schema scan (regex) | Medium |
| CI-002 | Content independence | Code scan (regex) | Medium |
| CI-003 | Content independence | Schema scan (regex) | Medium |
| CL-001 | Clarification | Assertion | High |
| CL-002 | Clarification | Regex on options | Critical |
| CL-003 | Clarification | Counter assertion | High |
| CL-004 | Clarification | Assertion | High |

**Total: 29 machine-detectable violations across 6 categories.**

---

## Automated Compliance Runner (Specification)

A compliance runner should:

1. Load all ClarificationEngine output from test fixtures
2. Apply all FC-* regex patterns to every player-visible string
3. Validate all ActionRequest outputs against JSON schema (SV-*)
4. Run determinism checks by executing bridge twice with same inputs (DI-*)
5. Scan source files for authority boundary violations (AB-*)
6. Scan schema file for content independence violations (CI-*)
7. Verify clarification loop constraints (CL-*)

**Pass criteria:** Zero violations across all categories.
**Partial pass:** Zero Critical violations; High/Medium violations documented as known deltas.

---

## END OF COMPLIANCE CHECKLIST

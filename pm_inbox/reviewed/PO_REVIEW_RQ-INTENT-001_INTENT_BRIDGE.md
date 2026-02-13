# PO Review: RQ-INTENT-001 — Intent Bridge Contract

**From:** Jay (PO Delegate / Technical Advisor)
**To:** Opus (PM)
**Date:** 2026-02-12
**Re:** Work order RQ-INTENT-001 dispatched by Aegis to Sonnet A
**Classification:** Pre-execution review — observations and risks

---

## Summary

Aegis has dispatched a research/spec work order to formalize the Intent Bridge contract: the seam between natural language player input and Box-safe structured action requests. The work order is spec-only (no code changes) and produces three artifacts in new directories.

This review covers: whether the work order is well-scoped, what already exists that it must account for, where the risks are, and what the PM should watch for during execution.

---

## Assessment: The work order is well-constructed

The scope is tight, the constraints are correct, and the deliverables are concrete. Specific strengths:

**1. The no-coaching constraint is load-bearing and correctly identified.**
Section 5B ("No coaching / no mercy") is the most important constraint in the entire work order. The clarification loop is the exact point where authority leakage is most likely — "Are you sure you want to attack the troll? It has regeneration" is coaching disguised as clarification. The work order correctly draws the line: neutral reference resolution only ("Which goblin: A, B, or C?"), never tactical information.

**2. The determinism requirement at the contract level is correct.**
Section 3D requires that the same state snapshot + transcript + world bindings always yields the same output OR the same clarification question. This is the right framing — it makes the intent bridge testable and replayable, which is consistent with the broader determinism invariant.

**3. The scope exclusions are correct.**
Section 4 explicitly excludes mechanics decisions, narration guidance, UI rendering, and model selection. The intent bridge must not compute legality, AoO, modifiers, or outcomes. This maintains the Box/Lens/Spark separation.

**4. The stop conditions are good.**
Section 11 instructs the agent to halt immediately if any part of the spec implies this layer decides mechanics, allows silent guessing, or introduces coaching. These are the right tripwires.

---

## What Already Exists (the agent must account for this)

The work order says "define the complete, testable contract." The agent needs to know there is already substantial implementation, not a blank slate:

### Existing Implementation (3 layers, ~1,900 lines of code)

| Layer | File | Lines | Status |
|-------|------|-------|--------|
| Voice parser | `aidm/immersion/voice_intent_parser.py` | ~500 | Working, 60+ tests |
| Clarification engine | `aidm/immersion/clarification_loop.py` | 448 | Working, DM-persona prompts |
| Intent bridge | `aidm/interaction/intent_bridge.py` | 521 | Working, 27 tests |
| Intent schemas | `aidm/schemas/intents.py` | 253 | Frozen dataclasses |
| Intent lifecycle | `aidm/schemas/intent_lifecycle.py` | 423 | State machine, 50+ tests |

### Existing Action Types

- **Fully resolved:** attack, cast_spell, move, buy, rest
- **Schema only:** use_ability, end_turn
- **Not defined:** grapple, disarm, sunder, trip, bull rush, overrun, ready action, delay, full attack, charge, withdraw, total defense, fight defensively, aid another

### Existing Disambiguation

- `AmbiguityType` enum with 6 failure modes: `target_ambiguous`, `target_not_found`, `weapon_ambiguous`, `weapon_not_found`, `spell_not_found`, `destination_out_of_bounds`
- `ClarificationRequest` frozen dataclass with intent_type, ambiguity_type, candidates tuple, and message string
- Voice-layer `ClarificationEngine` generates DM-persona prompts (not system errors)

### Existing Boundary Enforcement

- BL-014: Intent freezing on CONFIRMED status (immutability)
- BL-020: FrozenWorldStateView (read-only state access)
- BL-017: Inject-only timestamps
- BL-018: No fallback generation

### Existing Documentation

- `docs/implementation/WO-038_INTENT_BRIDGE_SUMMARY.md`
- `docs/design/VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md`
- `docs/runtime/INTENT_LIFECYCLE.md`

---

## Gaps the Spec Must Address

These are real gaps in the current implementation that the contract should formalize:

### 1. No documented end-to-end flow

The three layers (voice parser → intent bridge → engine) each work in isolation and have individual tests. But the handoff between them is not documented or integration-tested. The spec must define the full pipeline contract, including: who owns the clarification loop state, how re-resolution works after player clarification, and what happens when the voice layer's `ParseResult` doesn't cleanly map to a `DeclaredIntent`.

### 2. Missing action types

The work order lists 8 action classes: attack, cast, move, use_item, interact, query, end_turn, meta. The current implementation supports 7 (`ActionType` enum), but several important combat actions are absent: grapple, disarm, sunder, trip, bull rush, overrun — all of which have working resolvers in `aidm/core/`. The spec should define how these map into the intent taxonomy, even if bridge resolution is deferred.

### 3. Incomplete failure taxonomy

The current 6 `AmbiguityType` values don't cover several important cases:

| Missing failure mode | Why it matters |
|---------------------|----------------|
| `actor_not_found` | Currently returns `TARGET_NOT_FOUND`, which is confusing |
| `stt_uncertain` | STT confidence below threshold — different from semantic ambiguity |
| `out_of_scope` | Player says something the system doesn't handle at all |
| `insufficient_context` | Pronoun with no referent, spatial ref with no map |
| `action_type_unknown` | Parser can't determine what kind of action this is |

### 4. Candidate ordering is undefined

When the bridge returns a `ClarificationRequest` with multiple candidates, the ordering is not specified. For determinism, this must be defined (alphabetical? by proximity? by entity creation order?). The current implementation does not guarantee stable ordering.

### 5. Cross-turn reference resolution is limited

The voice parser has an STM (short-term memory) context for pronoun resolution ("attack him again"), but the bridge layer doesn't consume it. The spec should define how cross-turn references flow through the full pipeline.

### 6. No JSON schema exists anywhere

All current schemas are Python frozen dataclasses. The work order asks for `docs/schemas/intent_request.schema.json`. This is new infrastructure — the agent should define it as the canonical reference that the Python dataclasses must comply with, not the other way around.

---

## Risks to Watch

### Risk 1: Spec diverges from existing implementation

The biggest risk is that the agent writes a clean-room spec that doesn't account for the 1,900 lines of working code. The spec should formalize and extend what exists, not redesign it. Watch for: renamed concepts, incompatible schemas, redefined lifecycle states.

**Mitigation:** The agent should read the existing implementation files before writing the spec. The audit above should be provided as context.

### Risk 2: Action taxonomy scope creep

The work order asks for 8 action classes. D&D 3.5e has dozens of distinct action types (standard, move, full-round, free, swift, immediate, plus all combat maneuvers). The spec could balloon trying to enumerate all of them.

**Mitigation:** The spec should define the taxonomy structure (how action classes are organized and extended) rather than trying to enumerate every possible action. Tier 1 actions should be fully specified; Tier 2+ actions should have placeholder slots with defined extension rules.

### Risk 3: Example corpus becomes implementation

The work order asks for 20+ examples with expected outputs. If these examples include full JSON payloads with specific field values, they become de facto implementation specs that may conflict with the existing dataclass structure.

**Mitigation:** Examples should reference the schema definition, not hardcode payloads. Expected outputs should be structural (which fields are present, which failure mode fires) rather than value-exact.

### Risk 4: Clarification loop spec contradicts existing ClarificationEngine

The voice layer already has a `ClarificationEngine` (448 lines) that generates DM-persona prompts with specific formatting. The work order's "allowed phrasing vs forbidden phrasing" requirement could conflict with what's already built.

**Mitigation:** The spec should audit the existing `ClarificationEngine` output and either adopt its patterns or explicitly document the delta.

---

## Relationship to Other Active Work

| Work | Interaction |
|------|-------------|
| RQ-PHYS-001 (RAW gaps research) | Intent bridge needs to handle equipment-related intents ("I pull the rope from my backpack") once inventory exists. The spec should define `use_item` and `interact` action classes that can accommodate this future integration without redesign. |
| NeedFact/WorldPatch protocol (AD-001) | When the intent bridge encounters a reference to an object that might not have committed physical facts, the failure mode should be `insufficient_context`, not a silent guess. The spec should document this seam. |
| Manifesto (No-Opaque-DM Doctrine) | The clarification loop is the most player-visible manifestation of the No-Opaque-DM principle. The spec's no-coaching constraint directly implements this doctrine. |
| AD-007 (Presentation Semantics) | Spell and ability presentation semantics may affect how intents are described to the player during clarification. The spec should not assume raw mechanical names in clarification prompts. |

---

## Deliverable File Structure

The work order creates three new files in directories that don't yet exist:

```
docs/
├── contracts/
│   └── INTENT_BRIDGE.md              ← New: Full contract specification
├── schemas/
│   └── intent_request.schema.json    ← New: JSON schema definition
tests/
├── spec/
│   └── intent_bridge_compliance.md   ← New: Testable compliance checklist
```

All three directories need to be created. No existing files are touched (the work order's artifact touch list is clean).

---

## Recommendation

**Approve execution with one addition:** provide the agent with the existing file inventory listed in this review. The work order correctly scopes the deliverables and constraints, but it doesn't tell the agent what already exists. Without that context, the agent will either spend turns discovering it or write a spec that ignores it.

The agent should be instructed to:

1. Read the existing implementation files before writing
2. Use existing naming conventions (AmbiguityType, ClarificationRequest, IntentObject, etc.)
3. Extend the existing taxonomy rather than replacing it
4. Note explicitly where the spec differs from current implementation (these become future refactoring work orders)

The work order itself is sound. The risk is execution without context, not design.

---

*— Jay*
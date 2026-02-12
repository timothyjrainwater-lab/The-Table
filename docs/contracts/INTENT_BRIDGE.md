# Intent Bridge Contract v1
## Voice → Structured Action Translation

**Document ID:** RQ-INTENT-001
**Version:** 1.0
**Date:** 2026-02-12
**Status:** DRAFT — Awaiting PM + PO Approval
**Authority:** This document is the canonical contract for the Intent Bridge layer.
**Scope:** Natural language → ActionRequest translation, disambiguation, clarification, unknown handling.

**References:**
- `docs/design/VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md` (VICP-001) — adopted protocol
- `docs/runtime/INTENT_LIFECYCLE.md` (INTENT-001) — lifecycle state machine
- `docs/implementation/WO-038_INTENT_BRIDGE_SUMMARY.md` — existing implementation summary
- `docs/specs/RQ-PRODUCT-001_CONTENT_INDEPENDENCE_ARCHITECTURE.md` — content independence

**Existing Implementation (this spec formalizes and extends):**

| Layer | File | Lines | Tests |
|-------|------|-------|-------|
| Voice parser | `aidm/immersion/voice_intent_parser.py` | ~740 | 60+ |
| Clarification engine | `aidm/immersion/clarification_loop.py` | 448 | DM-persona prompts |
| Intent bridge | `aidm/interaction/intent_bridge.py` | 521 | 27 |
| Intent schemas | `aidm/schemas/intents.py` | 253 | frozen dataclasses |
| Intent lifecycle | `aidm/schemas/intent_lifecycle.py` | 423 | 50+ |

---

## Contract Summary (1-Page)

The Intent Bridge converts free-form player speech into a strictly-typed
**ActionRequest** that Box can execute or reject. The bridge has **no
mechanical authority**: it cannot compute legality, apply modifiers, trigger
reactions, or decide outcomes. It may only ask neutral disambiguation questions
and package the player's declared intent.

**Pipeline:** STT transcript → VoiceIntentParser → IntentBridge → ActionRequest → Box

**Invariants:**
1. **Deterministic:** Same (state snapshot + transcript + STM context) → same ActionRequest OR same ClarificationRequest.
2. **No coaching:** The bridge never warns about consequences, suggests tactics, or reveals mechanical internals (AC, HP, save DCs).
3. **No silent guessing:** If ambiguity exists, the bridge asks. It never picks a "most likely" target or infers an unspecified spell.
4. **Fail-closed:** Unknown inputs produce explicit `reject` or `needs_clarification` status, never a best-effort resolution.
5. **Content-independent:** Intent types and field names contain no D&D-specific vocabulary. Game-specific names appear only in world bindings, not in the schema.
6. **Authority boundary:** The bridge reads world state (via FrozenWorldStateView) but never writes it. It resolves names to IDs but never computes mechanical results.

---

## 1. Intent Taxonomy (v1)

### 1.1 Tier 1 — Fully Specified (MVP)

These intents have complete field definitions and bridge resolution logic.

| intent_type | Description | Required Fields | Optional Fields | Unknown-Allowed Fields |
|-------------|-------------|-----------------|-----------------|----------------------|
| `attack` | Melee or ranged attack | `actor_id`, `targets[0]` | `instrument.weapon_ref` | `instrument` (defaults to equipped) |
| `cast_spell` | Cast a spell | `actor_id`, `instrument.ability_ref` | `targets`, `parameters.position` | `targets` (self-target spells) |
| `move` | Movement to location | `actor_id`, `parameters.destination` | `parameters.path_preference` | — |
| `use_ability` | Use class/racial/feat ability | `actor_id`, `instrument.ability_ref` | `targets`, `parameters` | `parameters` (ability-dependent) |
| `end_turn` | End current turn | `actor_id` | — | — |
| `buy` | Purchase items from vendor | `actor_id`, `parameters.items` | `targets[0]` (vendor) | `targets` (infer from context) |
| `rest` | Short or long rest | `actor_id` | `parameters.rest_type` | `parameters.rest_type` (defaults to overnight) |

### 1.2 Tier 2 — Schema Only (Defined but Bridge Resolution Deferred)

These intents have field definitions but do not yet have bridge resolution
implementations. The bridge must recognize them and produce status `reject`
with `reject_reason: "not_yet_supported"` rather than misclassifying them.

| intent_type | Description | Required Fields | Notes |
|-------------|-------------|-----------------|-------|
| `grapple` | Initiate or maintain grapple | `actor_id`, `targets[0]` | Combat maneuver |
| `disarm` | Attempt to disarm target | `actor_id`, `targets[0]` | Combat maneuver |
| `sunder` | Destroy target's equipment | `actor_id`, `targets[0]`, `instrument` | Combat maneuver |
| `trip` | Trip target | `actor_id`, `targets[0]` | Combat maneuver |
| `bull_rush` | Push target back | `actor_id`, `targets[0]` | Combat maneuver |
| `overrun` | Move through target's space | `actor_id`, `targets[0]` | Combat maneuver |
| `charge` | Move + attack in one action | `actor_id`, `targets[0]` | Full-round action |
| `full_attack` | Multiple attacks in one round | `actor_id`, `targets` | Full-round action |
| `withdraw` | Retreat without provoking | `actor_id`, `parameters.destination` | Full-round action |
| `total_defense` | Full defense posture | `actor_id` | Standard action |
| `fight_defensively` | Attack with defense bonus | `actor_id`, `targets[0]` | Modifier on attack |
| `aid_another` | Help ally's check | `actor_id`, `targets[0]` | Standard action |
| `ready_action` | Ready an action with trigger | `actor_id`, `parameters.trigger`, `parameters.action` | Standard action |
| `delay` | Delay initiative | `actor_id` | No action cost |
| `interact_object` | Interact with environment | `actor_id`, `targets[0]` | Move or standard action |
| `talk_to` | Speak to NPC/entity | `actor_id`, `targets[0]` | Free action in combat |

### 1.3 Meta Intents (Out-of-Game)

These do not produce ActionRequests for Box. They are handled within the
interaction layer and never cross the engine boundary.

| intent_type | Description | Required Fields |
|-------------|-------------|-----------------|
| `ask_rules` | Query about rules | `parameters.question` |
| `ask_recap` | Request session/combat recap | `parameters.scope` |
| `retract` | Cancel pending intent | `parameters.intent_id` |
| `undo_request` | Request to undo (may be denied) | `parameters.scope` |

### 1.4 Extension Rules

New intent types MUST:
1. Be added to the `ActionType` enum in `aidm/schemas/intent_lifecycle.py`
2. Define required/optional/unknown-allowed fields in this contract
3. Add at least 5 test vectors to the corpus
4. Not modify any existing intent type's field definitions
5. Be classified as Tier 1 (full resolution) or Tier 2 (schema only) — no unclassified intents

### 1.5 Mapping to Existing Implementation

| Contract intent_type | Existing ActionType enum | Existing Intent dataclass |
|---------------------|-------------------------|--------------------------|
| `attack` | `ActionType.ATTACK` | `DeclaredAttackIntent` |
| `cast_spell` | `ActionType.CAST_SPELL` | `CastSpellIntent` |
| `move` | `ActionType.MOVE` | `MoveIntent` |
| `use_ability` | `ActionType.USE_ABILITY` | — (no dedicated class) |
| `end_turn` | `ActionType.END_TURN` | — (no dedicated class) |
| `buy` | `ActionType.BUY` | `BuyIntent` |
| `rest` | `ActionType.REST` | `RestIntent` |
| `grapple` — `delay` | — (not in enum) | — (not implemented) |

**Delta:** The existing `ActionType` enum has 7 values. This contract defines
7 Tier 1 + 16 Tier 2 + 4 meta = 27 intent types. The enum must be extended
when Tier 2 intents gain bridge resolution. Meta intents do not need enum
entries (they are handled before the lifecycle layer).

---

## 2. Entity Resolution Model

### 2.1 Canonical Entity Reference

Every entity in the world state has:

| Field | Type | Example | Source |
|-------|------|---------|--------|
| `entity_id` | str (stable UUID) | `"goblin_03"` | World state |
| `display_name` | str | `"Goblin Warrior"` | World state (`name` field) |
| `spatial_descriptor` | str (optional) | `"near the brazier"` | Computed from position + landmarks |
| `role_label` | str (optional) | `"the guard captain"` | World state or NPC metadata |

The Intent Bridge resolves player references → `entity_id`. The ActionRequest
always contains `entity_id`, never raw player text.

### 2.2 Allowed Reference Types

| Reference Type | Example Utterance | Resolution Strategy |
|---------------|-------------------|-------------------|
| **Named** | "attack the shopkeeper" | Match `display_name` or `role_label` (case-insensitive) |
| **Role** | "attack the guard captain" | Match `role_label` (case-insensitive) |
| **Deictic** | "attack that one" | Requires pointing/selection context from UI layer |
| **Spatial** | "attack the leftmost goblin" | Compute from entity positions + spatial keyword |
| **Ordinal** | "attack the second goblin" | Order by spatial_sort_key (see §2.3), select Nth |
| **Group** | "fireball those three goblins" | Multi-select from entity positions or UI selection |
| **Pronoun** | "attack him" | Resolve from STMContext.last_target |
| **Context** | "attack the one I hit last turn" | Resolve from STMContext.history |
| **Partial** | "attack the gob" | Substring match on display_name |

### 2.3 Disambiguation Ranking (Deterministic)

When multiple entities match a reference, apply these rules in order:

1. **Exact match on display_name** beats partial match.
2. **Exact match on role_label** beats partial match.
3. **Fewer total matches** wins (single partial match resolves immediately).
4. **If still tied:** return `needs_clarification` with candidates.

**Candidate ordering (for clarification options):**

When presenting candidates to the player, order by:

1. **Lexicographic sort** on `display_name` (case-insensitive, ascending).
2. **Tie-break:** `entity_id` lexicographic order (stable, deterministic).

This ordering is deterministic for the same world state snapshot. The existing
implementation (`_resolve_entity_name` in `intent_bridge.py`) uses iteration
order over `view.entities`, which is Python dict insertion order — deterministic
within a single process but not contractually stable across world state
construction methods. **The implementation must add an explicit
`sorted(candidates, key=lambda c: c.lower())` call for contract compliance.**
See Delta D-01.

**Rationale:** Lexicographic ordering was chosen over spatial proximity because:
(a) it requires no position data (some clarification contexts lack positions),
(b) it matches the simplest possible implementation, and (c) spatial ordering
can be added as a future enhancement without breaking the sort contract (by
prepending a proximity key to the sort tuple).

### 2.4 Spatial Sort Key

For spatial and ordinal references, entities are ordered by:

```
spatial_sort_key(entity, keyword) =
  if keyword in {"left", "leftmost"}:   entity.position.x ASC
  if keyword in {"right", "rightmost"}: entity.position.x DESC
  if keyword in {"nearest", "closest"}: distance(actor, entity) ASC
  if keyword in {"farthest"}:           distance(actor, entity) DESC
  default:                              distance(actor, entity) ASC
```

Ties broken by `entity_id` lexicographic order.

### 2.5 Entity Exclusion Rules

The following entities are excluded from matching:

| Condition | Reason |
|-----------|--------|
| `entity_id == actor_id` | Cannot self-target in attack (unless explicit) |
| `entity.defeated == True` | Defeated entities are not valid targets |
| `entity.hidden == True` and actor has no detection | Hidden entities not perceivable |

These match the existing implementation's `exclude_id` and `defeated` checks.

### 2.6 Cross-Turn Reference Resolution

The STMContext (Short-Term Memory) from `voice_intent_parser.py` provides:

| STM Field | Resolves | Max Age |
|-----------|----------|---------|
| `last_target` | "him", "her", "it", "that one" | 3 turns |
| `last_location` | "there", "that spot" | 3 turns |
| `last_action` | "again" (repeat last action type) | 3 turns |
| `last_weapon` | "again" (with same weapon) | 3 turns |
| `last_spell` | "again" (with same spell) | 3 turns |

**Contract requirement:** The bridge layer MUST consume STMContext for pronoun
resolution. Currently, the bridge layer (`intent_bridge.py`) does NOT consume
STMContext — it receives pre-resolved `target_ref` strings from the voice
parser. The spec requires this gap to be closed: if a pronoun resolves to an
entity that no longer exists (dead/removed), the bridge must return
`needs_clarification`, not a stale reference.

---

## 3. ActionRequest Schema (Strict)

### 3.1 Top-Level Object

```
ActionRequest {
  intent_type:    string    REQUIRED  — from taxonomy (§1)
  actor_id:       string    REQUIRED  — entity performing action
  targets:        Target[]  OPTIONAL  — 0..N typed selectors
  instrument:     Instrument OPTIONAL — weapon/spell/ability/item
  parameters:     object    OPTIONAL  — action-specific key-value pairs
  constraints:    Constraint OPTIONAL — validation flags
  provenance:     Provenance REQUIRED — audit trail
  status:         enum      REQUIRED  — {"ok","needs_clarification","unknown","reject"}
  clarify:        Clarify   CONDITIONAL — required if status == "needs_clarification"
  reject_reason:  string    CONDITIONAL — required if status == "reject"
}
```

### 3.2 Target Selector

```
Target {
  entity_id:     string  CONDITIONAL — resolved entity ID
  entity_ref:    string  OPTIONAL    — original player text (for audit)
  position:      Position CONDITIONAL — grid position for area targets
  selector_type: enum    REQUIRED    — {"entity","position","area","self","none"}
}
```

`entity_id` is REQUIRED when `selector_type` is `"entity"`.
`position` is REQUIRED when `selector_type` is `"position"` or `"area"`.

### 3.3 Instrument

```
Instrument {
  instrument_type: enum   REQUIRED — {"weapon","spell","ability","item","unarmed","none"}
  ref:            string  CONDITIONAL — weapon_id/spell_id/ability_id/item_id
  display_name:   string  OPTIONAL — human-readable name for audit
}
```

`ref` is REQUIRED when `instrument_type` is not `"unarmed"` or `"none"`.

### 3.4 Constraint

```
Constraint {
  requires_confirm: boolean  OPTIONAL — true for AoE placement, destructive actions
  requires_los:     boolean  OPTIONAL — true if line-of-sight needed (informational)
  max_range:        integer  OPTIONAL — range limit in feet (informational)
}
```

Constraints are **informational annotations** from the bridge. The bridge does
NOT enforce them — Box does. The bridge includes them so the UI layer can
display range indicators or confirm dialogs before submitting to Box.

### 3.5 Provenance

```
Provenance {
  stt_text:             string   REQUIRED — original STT transcript
  stt_confidence:       float    OPTIONAL — STT confidence [0.0, 1.0]
  conversation_turn_id: string   REQUIRED — unique turn identifier
  context_refs:         string[] OPTIONAL — STM context references used
  parse_confidence:     float    OPTIONAL — parser confidence [0.0, 1.0]
}
```

### 3.6 Clarify Payload

```
Clarify {
  question:    string   REQUIRED — DM-persona clarification question
  options:     Option[] REQUIRED — bounded choices (2-6 options)
  clarify_type: enum   REQUIRED — {"target","location","instrument","action","spell","direction"}
  missing_fields: string[] REQUIRED — which ActionRequest fields are incomplete
}

Option {
  label:     string  REQUIRED — display text ("Goblin Warrior A")
  entity_id: string  OPTIONAL — resolved ID if applicable
  position:  Position OPTIONAL — position if applicable
}
```

### 3.7 Validation Rules

The bridge MUST reject (status: `"reject"`) if:

| Rule | Condition |
|------|-----------|
| V-001 | `actor_id` is missing or empty |
| V-002 | `intent_type` is not in the taxonomy |
| V-003 | Required fields for the intent_type are missing AND cannot be clarified |
| V-004 | `actor_id` does not exist in world state |
| V-005 | `intent_type` is Tier 2 and bridge resolution is not implemented |

The bridge MUST return `needs_clarification` if:

| Rule | Condition |
|------|-----------|
| C-001 | Multiple entities match a target reference |
| C-002 | No entity matches a target reference but similar names exist |
| C-003 | Spell/ability name is ambiguous (multiple partial matches) |
| C-004 | Area effect spell has no target position |
| C-005 | Movement intent has no destination |
| C-006 | STT confidence is below 0.5 and action type is destructive |

The bridge MUST NOT:

| Rule | Prohibition |
|------|------------|
| N-001 | Infer a target when none is specified and multiple exist |
| N-002 | Infer a spell when the name doesn't match any known spell |
| N-003 | Compute mechanical legality (AC, HP, saves, AoO, range) |
| N-004 | Compute or reveal any mechanical value to the player |
| N-005 | Modify world state |
| N-006 | Generate random values |

### 3.8 Mapping to Existing Implementation

| Contract Field | Existing IntentObject Field | Notes |
|---------------|---------------------------|-------|
| `intent_type` | `action_type` (ActionType enum) | Rename for external contract |
| `actor_id` | `actor_id` | Same |
| `targets[0].entity_id` | `target_id` | Existing is single-target only |
| `targets[0].position` | `target_location` | Existing uses Position |
| `instrument.ref` | `method` | Existing is untyped string |
| `parameters` | `parameters` | Same (dict) |
| `provenance.stt_text` | `source_text` | Same |
| `status` | `status` (IntentStatus enum) | Different enum values |
| `clarify` | — (ClarificationRequest is separate) | Must be unified |

**Delta:** The existing `IntentObject` is a lifecycle wrapper. The contract's
`ActionRequest` is the bridge's output format. They coexist: the bridge
produces an `ActionRequest`, the lifecycle layer wraps it in an `IntentObject`
with status tracking. The existing `ClarificationRequest` (two versions exist:
one in `intent_bridge.py`, one in `clarification_loop.py`) must be unified
under the contract's `Clarify` payload structure.

---

## 4. Clarification Protocol

### 4.1 Core Doctrine: No Coaching, No Mercy

The clarification loop implements the **No-Opaque-DM Doctrine** at the
interaction layer. The bridge may ask questions to resolve references. It may
not provide tactical information, warn about consequences, or suggest better
actions.

### 4.2 Allowed Clarification Questions

| Category | Allowed Example | Purpose |
|----------|----------------|---------|
| Target disambiguation | "Which goblin — the one near the brazier or the one by the door?" | Resolve ambiguous target reference |
| Location specification | "Where do you want to center that?" | Specify AoE origin or move destination |
| Instrument selection | "With which weapon?" | Resolve unspecified weapon |
| Spell confirmation | "Which spell — Shield or Shillelagh?" | Resolve ambiguous spell name |
| Action clarification | "What are you trying to do?" | Parser couldn't determine intent type |
| Group scope | "All three, or just the two nearest?" | Clarify multi-target scope |

### 4.3 Forbidden Clarification Language

These are **hard violations**. Any occurrence is a contract breach.

| Violation ID | Forbidden Pattern | Why |
|-------------|-------------------|-----|
| F-001 | "Are you sure?" | Coaching — implies the action is bad |
| F-002 | "That will provoke an attack of opportunity" | Reveals mechanical consequence |
| F-003 | "You might want to consider..." | Tactical advice |
| F-004 | "That's probably not a good idea" | Value judgment on player choice |
| F-005 | "The goblin has X hit points remaining" | Reveals mechanical internal |
| F-006 | "The goblin's AC is X" | Reveals mechanical internal |
| F-007 | "You'll need to make a DC X save" | Reveals save DC before resolution |
| F-008 | "That target has resistance to fire" | Reveals mechanical property |
| F-009 | "Your spell won't reach that far" | Computes range legality (Box's job) |
| F-010 | "You don't have enough movement" | Computes movement legality (Box's job) |
| F-011 | "The better option would be..." | Tactical coaching |
| F-012 | "Warning:" or "Caution:" | System-language framing |
| F-013 | "I recommend..." | Coaching |
| F-014 | "Keep in mind that..." | Pre-emptive coaching |

**Phrasing constraint:** Clarification questions must be **neutral reference
resolution**. The question must be answerable by pointing, naming, or choosing
from a list. It must not require the player to reason about mechanics.

### 4.4 Deterministic Clarification Triggers

The bridge fires a clarification if and only if the following conditions hold:

```
CLARIFY when:
  (C-001) target_ref matches >1 entity AND no exact match exists
  (C-002) target_ref matches 0 entities AND similar names exist (edit distance ≤ 3)
  (C-003) spell_name partially matches >1 spell
  (C-004) area spell AND no target_position provided
  (C-005) move intent AND no destination provided
  (C-006) stt_confidence < 0.5 AND action is destructive (attack, cast_spell)

REJECT when:
  (R-001) target_ref matches 0 entities AND no similar names exist
  (R-002) spell_name matches 0 spells
  (R-003) actor_id not in world state
  (R-004) intent_type not in taxonomy
  (R-005) intent_type is Tier 2 (not yet supported)
```

No other condition fires clarification. This list is exhaustive.

### 4.5 Option Formatting

When presenting choices:

1. Options are **bounded**: minimum 2, maximum 6.
2. Each option has a stable `entity_id` or `position` for machine consumption.
3. Options are ordered lexicographically by `display_name` (case-insensitive, §2.3).
4. Tie-break: `entity_id` lexicographic order.
5. Labels use `display_name` + spatial descriptor if ambiguous:
   - "Goblin Warrior (near the brazier)"
   - "Goblin Warrior (by the door)"
6. No option text contains mechanical values (HP, AC, etc.).

### 4.6 Clarification Loop Limits

| Parameter | Value | Behavior when exceeded |
|-----------|-------|----------------------|
| Max clarification rounds per intent | 3 | Transition to RETRACTED |
| Timeout per clarification question | Configurable (default: 30s) | Transition to RETRACTED |
| Max options per question | 6 | If >6 candidates, narrow by proximity first |

### 4.7 Mapping to Existing Implementation

The existing `ClarificationEngine` in `clarification_loop.py` generates
DM-persona prompts. Its output format (`ClarificationRequest` with `prompt`,
`clarification_type`, `suggested_options`, `missing_fields`,
`can_proceed_without`) is compatible with the contract's `Clarify` payload
but needs these adjustments:

| Gap | Current Behavior | Required Behavior |
|-----|-----------------|-------------------|
| Options lack entity_id | `suggested_options: List[str]` | Options must include `entity_id` |
| No max rounds | No loop counter | 3-round limit, then RETRACTED |
| No spatial ordering | Arbitrary order | Spatial proximity order |
| `can_proceed_without` | Allows partial resolution | Remove — bridge must fully resolve or fail |

---

## 5. "Unknown" Handling

### 5.1 Unknown Taxonomy

| Unknown Type | Description | Policy | Allowed Phrasing |
|-------------|-------------|--------|-----------------|
| `unknown_target` | Player referenced an entity that doesn't exist | **clarify** if similar names exist; **reject** if none | "I don't see anyone by that name. Who do you mean?" |
| `unknown_ability` | Player named a spell/ability not in registry | **reject** | "I don't recognize that ability." |
| `unknown_location` | Player referenced a position that can't be resolved | **clarify** | "Where exactly?" |
| `unknown_precondition` | Action requires context the bridge doesn't have | **defer-to-Box-with-unknown** | (no player-facing phrasing — Box decides) |
| `unknown_game_mode` | Bridge can't determine if combat or narrative mode | **defer-to-Box-with-unknown** | (no player-facing phrasing — Box decides) |
| `unknown_actor` | actor_id not in world state | **reject** | (system error — no player-facing phrasing) |
| `unknown_action` | Parser can't determine intent type | **clarify** | "I didn't catch that. What are you trying to do?" |
| `stt_uncertain` | STT confidence below threshold | **clarify** if destructive; **proceed** if non-destructive | "I didn't quite hear you. Could you repeat that?" |
| `out_of_scope` | Player said something the system doesn't handle | **reject** | "I'm not sure how to handle that." |

### 5.2 Defer-to-Box-with-Unknown

For `unknown_precondition` and `unknown_game_mode`, the bridge packages the
ActionRequest with `status: "ok"` and includes an `unknown_flags` field in
parameters. Box is responsible for determining legality. The bridge does not
second-guess Box.

```json
{
  "intent_type": "attack",
  "actor_id": "fighter_01",
  "targets": [{"entity_id": "goblin_03", "selector_type": "entity"}],
  "parameters": {
    "unknown_flags": ["unknown_game_mode"]
  },
  "status": "ok"
}
```

### 5.3 Failure Cascading

Unknown handling follows this precedence:

```
1. If actor_id unknown → reject immediately (system error)
2. If intent_type unknown → clarify action
3. If target unknown → clarify or reject per policy
4. If instrument unknown → clarify or default
5. If precondition unknown → defer to Box
```

Higher-priority unknowns short-circuit. The bridge does not ask about targets
if it can't even determine the action type.

---

## 6. End-to-End Pipeline

### 6.1 Full Flow

```
Player speaks
    │
    ▼
┌─────────────────────┐
│  STT Engine          │  Produces: Transcript(text, confidence, adapter_id)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  VoiceIntentParser   │  Produces: ParseResult(intent, confidence, ambiguity flags)
│  (voice layer)       │  Consumes: STMContext for pronoun/context resolution
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐  If ParseResult.needs_clarification:
│  ClarificationEngine │  ──→ Generate DM-persona question
│  (voice layer)       │  ──→ Wait for player response
│                      │  ──→ Re-parse response
│                      │  ──→ Loop (max 3 rounds)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  IntentBridge        │  Produces: ActionRequest (or ClarificationRequest)
│  (interaction layer) │  Consumes: ParseResult + FrozenWorldStateView
│                      │  Resolves: names→IDs, weapon refs→weapon_ids, spell names→spell_ids
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  IntentLifecycle     │  Wraps ActionRequest in IntentObject
│  (schema layer)      │  Manages: PENDING → CLARIFYING → CONFIRMED → RESOLVED
│                      │  Enforces: BL-014 (freeze on CONFIRMED)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Box (Engine)        │  Receives: frozen IntentObject
│                      │  Computes: legality, modifiers, resolution, outcome
│                      │  Returns: EngineResult
└─────────────────────┘
```

### 6.2 Ownership Boundaries

| Concern | Owner | NOT Owner |
|---------|-------|-----------|
| Text → slots | VoiceIntentParser | IntentBridge |
| Pronoun resolution | VoiceIntentParser (via STMContext) | IntentBridge |
| DM-persona phrasing | ClarificationEngine | IntentBridge |
| Name → entity_id | IntentBridge | VoiceIntentParser |
| Weapon ref → weapon_id | IntentBridge | VoiceIntentParser |
| Spell name → spell_id | IntentBridge | VoiceIntentParser |
| Lifecycle state machine | IntentObject (intent_lifecycle.py) | IntentBridge |
| Immutability enforcement | IntentObject (BL-014) | IntentBridge |
| Mechanical legality | Box | Everything else |
| Narrative phrasing | Spark | Everything else |

### 6.3 Handoff Contracts

**VoiceIntentParser → IntentBridge:**
- Input: `ParseResult` containing an `Intent` dataclass (or None)
- The bridge does NOT receive raw text. It receives pre-parsed slots.
- The bridge DOES receive `FrozenWorldStateView` for name resolution.

**IntentBridge → IntentLifecycle:**
- Input: Resolved ActionRequest fields
- Output: `IntentObject` in PENDING status
- If all required fields present: auto-transition to CONFIRMED
- If fields missing: transition to CLARIFYING

**IntentLifecycle → Box:**
- Input: Frozen `IntentObject` (status == CONFIRMED)
- Box MUST NOT receive unfrozen intents
- BL-014 enforces this at the code level

### 6.4 Re-Resolution After Clarification

When a clarification response arrives:

1. ClarificationEngine re-parses the player's response.
2. New ParseResult is produced with the clarified field(s) filled.
3. IntentBridge re-runs resolution with updated ParseResult.
4. If still ambiguous: loop (up to 3 rounds).
5. If resolved: package final ActionRequest.
6. If loop exhausted: transition to RETRACTED.

**State ownership:** The clarification loop state (round count, pending
questions, partial resolutions) is owned by the ClarificationEngine. The
IntentBridge is stateless between calls — it receives a complete ParseResult
each time and produces a complete ActionRequest or ClarificationRequest.

---

## 7. Test Vector Corpus

### 7.1 Corpus Requirements

- Minimum: 80 utterances
- Each utterance has an expected output: either an ActionRequest skeleton or a
  ClarificationRequest
- At least 20 utterances are ambiguity/unknown/negative cases
- Corpus is stored in `test_vectors/intent_bridge/` (JSONL format)

### 7.2 Categories and Vectors

#### Category A: Simple Combat (20 vectors)

| # | Utterance | Expected intent_type | Expected status | Key fields |
|---|-----------|---------------------|----------------|------------|
| A01 | "I attack the goblin with my longsword" | attack | ok | targets: goblin, instrument: longsword |
| A02 | "Hit the orc" | attack | ok | targets: orc, instrument: default |
| A03 | "Swing at the skeleton" | attack | ok | targets: skeleton |
| A04 | "Shoot the goblin with my crossbow" | attack | ok | targets: goblin, instrument: crossbow |
| A05 | "I stab him" | attack | ok (if STM.last_target exists) | targets: from_stm |
| A06 | "Attack again" | attack | ok (if STM.last_target exists) | targets: from_stm, instrument: from_stm |
| A07 | "Punch the wizard" | attack | ok | targets: wizard, instrument: unarmed |
| A08 | "I attack" | attack | needs_clarification | clarify: target |
| A09 | "Fire an arrow at the guard" | attack | ok | targets: guard, instrument: bow |
| A10 | "Smite the undead" | attack | ok | targets: undead |
| A11 | "I charge the orc and attack" | charge | reject (Tier 2) | reject_reason: not_yet_supported |
| A12 | "Full attack on the troll" | full_attack | reject (Tier 2) | reject_reason: not_yet_supported |
| A13 | "I want to disarm the bandit" | disarm | reject (Tier 2) | reject_reason: not_yet_supported |
| A14 | "Trip the goblin" | trip | reject (Tier 2) | reject_reason: not_yet_supported |
| A15 | "I grapple the ogre" | grapple | reject (Tier 2) | reject_reason: not_yet_supported |
| A16 | "Attack the goblin with my vorpal blade" | attack | needs_clarification | clarify: weapon (not in equipment) |
| A17 | "I hit the thing" | attack | needs_clarification | clarify: target (ambiguous "thing") |
| A18 | "Attack the dragon" | attack | reject | reject: target not found (no dragon) |
| A19 | "I fight defensively against the orc" | fight_defensively | reject (Tier 2) | reject_reason: not_yet_supported |
| A20 | "Bull rush the skeleton into the pit" | bull_rush | reject (Tier 2) | reject_reason: not_yet_supported |

#### Category B: Spatial References (15 vectors)

| # | Utterance | Expected intent_type | Expected status | Key fields |
|---|-----------|---------------------|----------------|------------|
| B01 | "Attack the leftmost goblin" | attack | ok | targets: spatial(leftmost) |
| B02 | "Attack the closest enemy" | attack | ok | targets: spatial(closest) |
| B03 | "Fireball near the doorway" | cast_spell | ok | instrument: fireball, targets: position(near doorway) |
| B04 | "Move behind the pillar" | move | ok | parameters: spatial(behind, pillar) |
| B05 | "Attack the goblin by the brazier" | attack | ok | targets: spatial(near, brazier) |
| B06 | "I move to the second door on the right" | move | needs_clarification | clarify: location (complex spatial) |
| B07 | "Cast web on the group near the entrance" | cast_spell | ok | instrument: web, targets: area(near entrance) |
| B08 | "Attack the farthest one" | attack | ok | targets: spatial(farthest) |
| B09 | "Move 30 feet north" | move | ok | parameters: destination(30ft, north) |
| B10 | "I go to the door" | move | ok | parameters: destination(door) |
| B11 | "Retreat to behind the table" | move | ok | parameters: spatial(behind, table) |
| B12 | "Attack the one on my left" | attack | ok | targets: spatial(left, relative_to_actor) |
| B13 | "Move there" | move | ok (if STM.last_location exists) | parameters: from_stm |
| B14 | "Move there" | move | needs_clarification (if no STM) | clarify: location |
| B15 | "Attack the goblin near the other goblin" | attack | needs_clarification | clarify: target (circular reference) |

#### Category C: AoE and Confirm Loop (10 vectors)

| # | Utterance | Expected intent_type | Expected status | Key fields |
|---|-----------|---------------------|----------------|------------|
| C01 | "Fireball the group of goblins" | cast_spell | ok + requires_confirm | instrument: fireball, constraints: requires_confirm |
| C02 | "Cast fireball there" [with position] | cast_spell | ok | instrument: fireball, targets: position |
| C03 | "Cast fireball" | cast_spell | needs_clarification | clarify: location |
| C04 | "Center it on the three goblins" [clarification response] | cast_spell | ok + requires_confirm | targets: position(centroid of 3 goblins) |
| C05 | "Lightning bolt toward the back row" | cast_spell | ok | instrument: lightning_bolt, targets: position(back row) |
| C06 | "Web the hallway" | cast_spell | ok + requires_confirm | instrument: web, targets: position(hallway) |
| C07 | "Ice storm on the far group" | cast_spell | ok + requires_confirm | instrument: ice_storm, targets: position |
| C08 | "Cone of cold in that direction" | cast_spell | needs_clarification | clarify: direction |
| C09 | "Burning hands" | cast_spell | ok (self-origin cone) | instrument: burning_hands |
| C10 | "Cast cloudkill over there" | cast_spell | ok (if STM.last_location) | instrument: cloudkill, targets: from_stm |

#### Category D: Non-Combat (15 vectors)

| # | Utterance | Expected intent_type | Expected status | Key fields |
|---|-----------|---------------------|----------------|------------|
| D01 | "I buy a healing potion" | buy | ok | parameters: items [{name: healing_potion, qty: 1}] |
| D02 | "Buy 3 torches" | buy | ok | parameters: items [{name: torch, qty: 3}] |
| D03 | "Talk to the shopkeeper" | talk_to | reject (Tier 2) | reject_reason: not_yet_supported |
| D04 | "I rest for the night" | rest | ok | parameters: rest_type: overnight |
| D05 | "Full day of rest" | rest | ok | parameters: rest_type: full_day |
| D06 | "I pick up the key" | interact_object | reject (Tier 2) | reject_reason: not_yet_supported |
| D07 | "Open the chest" | interact_object | reject (Tier 2) | reject_reason: not_yet_supported |
| D08 | "I want to inspect the runes on the wall" | interact_object | reject (Tier 2) | reject_reason: not_yet_supported |
| D09 | "End my turn" | end_turn | ok | (no additional fields) |
| D10 | "I'm done" | end_turn | ok | (idiomatic end turn) |
| D11 | "I delay" | delay | reject (Tier 2) | reject_reason: not_yet_supported |
| D12 | "Ready an action — if the goblin moves, I attack" | ready_action | reject (Tier 2) | reject_reason: not_yet_supported |
| D13 | "Buy some rope and a grappling hook" | buy | ok | parameters: items [{name: rope, qty: 1}, {name: grappling_hook, qty: 1}] |
| D14 | "I set up camp" | rest | ok | parameters: rest_type: overnight |
| D15 | "Cast shield on myself" | cast_spell | ok | instrument: shield, targets: self |

#### Category E: Ambiguity and Unknown (20+ vectors)

| # | Utterance | Expected status | Expected behavior |
|---|-----------|----------------|-------------------|
| E01 | "Attack the goblin" (2 goblins present) | needs_clarification | Clarify: "Which goblin — A or B?" |
| E02 | "Attack the goblin" (1 goblin present) | ok | Resolves to the single goblin |
| E03 | "Attack the goblin" (0 goblins present) | reject | "I don't see any goblins." |
| E04 | "Cast frostbolt" (not a real spell) | reject | "I don't recognize that spell." |
| E05 | "Heal him" (no STM.last_target) | needs_clarification | Clarify: "Who?" |
| E06 | "Him" (ambiguous pronoun, multiple NPCs) | needs_clarification | Clarify: "Which one?" |
| E07 | "I use my special ability" (no ability named) | needs_clarification | Clarify: "Which ability?" |
| E08 | "" (empty transcript) | reject | Parser returns confidence 0.0 |
| E09 | "asdfghjkl" (gibberish) | reject | Parser can't determine action |
| E10 | "I want to fly" (fly not prepared/available) | cast_spell | ok (bridge packages; Box checks legality) |
| E11 | "Attack the gob" (partial match, 1 goblin) | ok | Partial match resolves |
| E12 | "Attack the gob" (partial match, 2 goblins) | needs_clarification | Clarify: "Which goblin?" |
| E13 | "Buy a potion" (2 types of potion available) | needs_clarification | Clarify: "Which potion?" |
| E14 | "Do something" (completely vague) | needs_clarification | Clarify: "What are you trying to do?" |
| E15 | "Help the fighter" | aid_another | reject (Tier 2) | reject_reason: not_yet_supported |
| E16 | "I cast magic missile at the darkness" | cast_spell | ok (target: "the darkness" → reject by Box if no valid target) |
| E17 | "Attack with my +5 holy avenger" (not in equipment) | needs_clarification | Clarify: weapon not found |
| E18 | "Move to..." (trailing off, incomplete) | needs_clarification | Clarify: "Where?" |
| E19 | "What does my character see?" | ask_recap (meta) | Handled in interaction layer, not sent to Box |
| E20 | "What are the rules for grappling?" | ask_rules (meta) | Handled in interaction layer, not sent to Box |
| E21 | "I want to teleport home" (no teleport prepared) | cast_spell | ok (bridge packages; Box checks legality) |
| E22 | "Attack the goblin" (goblin just died this turn) | reject | Target is defeated |
| E23 | "Cast fireball on the shopkeeper" (non-combat NPC) | cast_spell | ok (bridge packages; Box checks legality) |

---

## 8. Red-Team Analysis

### 8.1 Ten Failure Modes

| # | Failure Mode | How It Happens | Contract Safeguard |
|---|-------------|----------------|-------------------|
| RT-01 | **Hallucinated target** | Bridge invents an entity not in world state | V-004: actor_id must exist; entity resolution requires match in view.entities |
| RT-02 | **Invented spell** | Bridge accepts a spell name not in registry | R-002: reject if 0 matches in SPELL_REGISTRY |
| RT-03 | **Advice leakage** | Clarification contains tactical information | F-001 through F-014: hard violation list; compliance checklist regex |
| RT-04 | **Silent target selection** | Bridge picks "most likely" target instead of asking | N-001: must not infer target when ambiguous; C-001 forces clarification |
| RT-05 | **Mechanical leakage in options** | Clarification options include HP/AC values | §4.5 rule 6: no mechanical values in option text |
| RT-06 | **Infinite clarification loop** | Player repeatedly gives ambiguous answers | §4.6: max 3 rounds, then RETRACTED |
| RT-07 | **Stale pronoun resolution** | "Him" resolves to dead entity | §2.6: if resolved entity no longer exists, needs_clarification |
| RT-08 | **Non-deterministic ordering** | Candidates listed in different order on replay | §2.3: spatial proximity + entity_id tiebreak is deterministic |
| RT-09 | **Authority creep** | Bridge computes range/AoO before sending to Box | N-003: bridge must not compute mechanical legality |
| RT-10 | **D&D vocabulary in schema** | Schema field names use D&D-specific terms | §1: content-independent taxonomy; field names are generic |

### 8.2 Hardening Rules

For each failure mode, the compliance checklist (§9) contains machine-
detectable tests. RT-03 is the highest risk — advice leakage is subtle and
requires regex scanning of all clarification output.

---

## 9. Compliance Signals

See `tests/spec/intent_bridge_compliance.md` for the full machine-detectable
compliance checklist with 15+ testable violations.

---

## 10. Deltas from Existing Implementation

This section explicitly documents where the contract differs from the current
code. Each delta is a future refactoring work order.

| # | Delta | Current Code | Contract Requirement | Severity |
|---|-------|-------------|---------------------|----------|
| D-01 | Candidate ordering | Insertion order (dict iteration) | Lexicographic by display_name (case-insensitive) + entity_id tiebreak | Medium |
| D-02 | STMContext not consumed by bridge | Bridge receives `target_ref` string | Bridge should validate STM refs against world state | Medium |
| D-03 | Two ClarificationRequest classes | One in `intent_bridge.py`, one in `clarification_loop.py` | Unified `Clarify` payload | Low |
| D-04 | No clarification loop limit | No round counter | Max 3 rounds, then RETRACTED | Medium |
| D-05 | Options lack entity_id | `suggested_options: List[str]` | Options include `entity_id` and `position` | Medium |
| D-06 | No Tier 2 intent recognition | Unknown intents are parse failures | Tier 2 → explicit `reject: not_yet_supported` | Low |
| D-07 | No JSON schema | Python dataclasses only | JSON Schema as canonical reference | Low |
| D-08 | `can_proceed_without` flag | ClarificationEngine allows partial resolution | Remove — bridge must fully resolve or fail | Low |
| D-09 | Missing ambiguity types | 6 in AmbiguityType enum | 5 additional types needed (§Jay's review) | Medium |
| D-10 | No provenance tracking | `source_text` only | Full provenance object (STT confidence, turn ID, context refs) | Low |

---

## 11. Dataclass ↔ JSON Schema Mapping (Amendment B)

This appendix provides the isomorphic mapping between existing Python frozen
dataclasses and the JSON schema defined in `docs/schemas/intent_request.schema.json`.
Where the JSON schema introduces new structure not present in the current dataclasses,
the mapping notes the delta.

### 11.1 IntentObject (intent_lifecycle.py) ↔ ActionRequest (JSON Schema)

| IntentObject field | Type | JSON Schema field | JSON type | Notes |
|--------------------|------|-------------------|-----------|-------|
| `intent_id` | `str` | (not in ActionRequest) | — | Lifecycle-layer field; ActionRequest is the bridge output before lifecycle wrapping |
| `actor_id` | `str` | `actor_id` | `string` | **Identical** |
| `action_type` | `ActionType` | `intent_type` | `string` (enum) | **Values identical** (`"attack"`, `"cast_spell"`, etc.). Field renamed for external contract. |
| `status` | `IntentStatus` | `status` | `string` (enum) | **Different enum values.** IntentStatus: pending/clarifying/confirmed/resolved/retracted. ActionRequest status: ok/needs_clarification/unknown/reject. Mapping: `ok` = ready for CONFIRMED; `needs_clarification` = CLARIFYING; `reject` = will not proceed. |
| `source_text` | `str` | `provenance.stt_text` | `string` | **Same data, relocated** into provenance sub-object. |
| `created_at` | `datetime` | (not in ActionRequest) | — | Lifecycle-layer field; injected when IntentObject is created from ActionRequest. |
| `updated_at` | `datetime` | (not in ActionRequest) | — | Lifecycle-layer field. |
| `target_id` | `str | None` | `targets[0].entity_id` | `string` | **Same data.** ActionRequest supports multi-target (array); IntentObject is single-target. |
| `target_location` | `Position | None` | `targets[0].position` | `Position` | **Same data.** ActionRequest uses Target selector with `selector_type`. |
| `method` | `str | None` | `instrument.ref` | `string` | **Same data.** ActionRequest wraps in Instrument object with `instrument_type` discriminator. |
| `parameters` | `dict | None` | `parameters` | `object` | **Identical structure.** |
| `declared_goal` | `str | None` | (not in ActionRequest) | — | Narrative-layer field; not part of bridge output. |
| `action_data` | `Intent | None` | (not in ActionRequest) | — | The underlying typed intent object. ActionRequest flattens this into top-level fields. |
| `result_id` | `str | None` | (not in ActionRequest) | — | Engine-layer field; set after resolution. |
| `resolved_at` | `datetime | None` | (not in ActionRequest) | — | Engine-layer field. |

### 11.2 ClarificationRequest (intent_bridge.py) ↔ Clarify (JSON Schema)

| ClarificationRequest field | Type | JSON Schema field | JSON type | Notes |
|---------------------------|------|-------------------|-----------|-------|
| `intent_type` | `str` | (part of parent ActionRequest) | — | Moved to parent level. |
| `ambiguity_type` | `AmbiguityType` | (mapped to `clarify_type` + `reject_reason`) | `string` | **Split.** `TARGET_AMBIGUOUS`/`TARGET_NOT_FOUND` → `clarify_type: "target"`. `WEAPON_*` → `clarify_type: "instrument"`. `SPELL_NOT_FOUND` → `clarify_type: "spell"`. `DESTINATION_OUT_OF_BOUNDS` → `clarify_type: "location"`. |
| `candidates` | `Tuple[str, ...]` | `clarify.options[].label` | `string` | **Same data.** JSON schema wraps in Option object adding `entity_id` and `position`. |
| `message` | `str` | `clarify.question` | `string` | **Same data, renamed.** |

### 11.3 ClarificationRequest (clarification_loop.py) ↔ Clarify (JSON Schema)

| ClarificationRequest field | Type | JSON Schema field | JSON type | Notes |
|---------------------------|------|-------------------|-----------|-------|
| `prompt` | `str` | `clarify.question` | `string` | **Same data.** |
| `clarification_type` | `str` | `clarify.clarify_type` | `string` (enum) | **Same values.** |
| `suggested_options` | `List[str]` | `clarify.options[].label` | `string` | **Same data.** JSON wraps in Option objects. |
| `missing_fields` | `List[str]` | `clarify.missing_fields` | `string[]` | **Identical.** |
| `can_proceed_without` | `bool` | (removed) | — | **Delta D-08.** Contract removes this; bridge must fully resolve or fail. |

### 11.4 DeclaredAttackIntent (intents.py) ↔ ActionRequest (attack)

| DeclaredAttackIntent field | Type | JSON Schema field | JSON type | Notes |
|---------------------------|------|-------------------|-----------|-------|
| `type` | `Literal["attack"]` | `intent_type` | `string` | **Same value.** |
| `target_ref` | `str | None` | `targets[0].entity_ref` | `string` | **Same data.** JSON schema also has resolved `entity_id` after bridge. |
| `weapon` | `str | None` | `instrument.display_name` | `string` | **Same data.** JSON schema also has resolved `instrument.ref`. |

### 11.5 Position (position.py) ↔ Position (JSON Schema)

| Position field | Type | JSON Schema field | JSON type | Notes |
|---------------|------|-------------------|-----------|-------|
| `x` | `int` | `x` | `integer` | **Identical.** |
| `y` | `int` | `y` | `integer` | **Identical.** |
| — | — | `z` | `integer` (default 0) | **Extension.** JSON schema adds optional z-coordinate for future 3D support. |

---

## 12. ClarificationEngine Phrasing Audit (Amendment F)

This section audits every player-visible string produced by the existing
`ClarificationEngine` in `aidm/immersion/clarification_loop.py` against
the No Coaching constraint.

### 12.1 Method-by-Method Audit

**`_clarify_target()` — Target disambiguation**

| Condition | Output | Verdict |
|-----------|--------|---------|
| No candidates, attack intent | `"Who are you attacking?"` | PASS — neutral reference question |
| No candidates, spell intent | `"Who is the target of {spell_name}?"` | PASS — neutral reference question |
| No candidates, other intent | `"Which one?"` | PASS — minimal neutral question |
| 2 candidates | `"Did you mean {A} or {B}?"` | PASS — presents options without judgment |
| 3+ candidates | `"Which one — {A}, {B}, or {C}?"` | PASS — presents options without judgment |

**`_clarify_location()` — Location disambiguation**

| Condition | Output | Verdict |
|-----------|--------|---------|
| Spell, point target | `"Where do you want to center {spell_name}?"` | PASS — neutral location question |
| Move intent | `"Where are you moving to?"` | PASS — neutral location question |
| Generic | `"Where?"` | PASS — minimal |

**`_clarify_action()` — Action type disambiguation**

| Condition | Output | Verdict |
|-----------|--------|---------|
| Empty input | `"I didn't hear anything. What would you like to do?"` | PASS — neutral re-prompt |
| Can't determine action | `"I'm not sure what you're trying to do. Could you rephrase?"` | PASS — neutral re-prompt |
| Generic | `"I didn't quite catch that. What are you trying to do?"` | PASS — neutral re-prompt |
| Suggested options | `["attack", "move", "cast a spell", "use an item", "rest"]` | PASS — lists action categories without favoring any |

**`_clarify_spell()` — Spell name disambiguation**

| Condition | Output | Verdict |
|-----------|--------|---------|
| 2 candidates | `"Did you mean {A} or {B}?"` | PASS — neutral choice |
| 3+ candidates | `"Which spell — {A}, {B}, or {C}?"` | PASS — neutral choice |
| No candidates | `"Which spell are you casting?"` | PASS — neutral question |

**`_clarify_direction()` — Direction disambiguation**

| Condition | Output | Verdict |
|-----------|--------|---------|
| No landmarks | `"Which direction?"` with options `["north", "south", "east", "west"]` | PASS — neutral direction options |
| With landmarks | Adds `"toward the {landmark}"` options | PASS — spatial reference, not tactical advice |

**`generate_soft_confirmation()` — Confirmation table-talk**

| Condition | Output | Verdict |
|-----------|--------|---------|
| Attack intent | `"Alright, you attack {target} with your {weapon}."` | PASS — echoes intent without judgment |
| Spell (self) | `"Alright, you cast {spell} on yourself."` | PASS |
| Spell (creature) | `"Alright, casting {spell}..."` | PASS |
| Spell (point) | `"Alright, {spell} centered here..."` | PASS |
| Move intent | `"Alright, moving there..."` | PASS |
| Generic | `"Alright..."` | PASS |

**`generate_impossibility_feedback()` — Post-resolution failure feedback**

| Condition | Output | Verdict |
|-----------|--------|---------|
| Out of range (move) | `"That's a bit too far for one turn. You can get to here, or you'd need to Dash."` | **MARGINAL** — "you'd need to Dash" suggests a specific action. See D-04. |
| Out of range (attack) | `"That's out of range for your weapon. You'll need to get closer."` | **MARGINAL** — "You'll need to get closer" is borderline tactical. See D-04. |
| Blocked | `"You can't get there — there's something in the way."` | PASS — states physical fact |
| No line of sight | `"You don't have a clear line of sight to that target."` | PASS — states physical fact |
| Insufficient resources (spell) | `"You don't have {spell_name} prepared right now."` | PASS — states resource fact |
| Invalid target | `"That's not a valid target for this action."` | PASS — states constraint |
| Generic | `"You can't do that right now."` | PASS — minimal rejection |

### 12.2 Phrasing Compliance Summary

| Category | Total | Pass | Marginal | Fail |
|----------|-------|------|----------|------|
| Target clarification | 5 | 5 | 0 | 0 |
| Location clarification | 3 | 3 | 0 | 0 |
| Action clarification | 3 | 3 | 0 | 0 |
| Spell clarification | 3 | 3 | 0 | 0 |
| Direction clarification | 2 | 2 | 0 | 0 |
| Soft confirmation | 6 | 6 | 0 | 0 |
| Impossibility feedback | 7 | 5 | 2 | 0 |
| **Total** | **29** | **27** | **2** | **0** |

### 12.3 Marginal Items (Delta D-04)

Two impossibility feedback strings are marginally compliant:

1. `"That's a bit too far for one turn. You can get to here, or you'd need to Dash."`
   - **Issue:** "you'd need to Dash" implies a specific action the player should take
   - **Recommended fix:** `"That's beyond your reach this round."`

2. `"That's out of range for your weapon. You'll need to get closer."`
   - **Issue:** "You'll need to get closer" is borderline tactical direction
   - **Recommended fix:** `"That's out of your weapon's reach."`

These are logged as Delta D-04. The current phrasing is not a hard violation (it states
physical facts, not tactical advice), but stricter alternatives exist and should be
adopted in a future cleanup WO.

### 12.4 Allowed vs Forbidden Phrasing Reference

**Allowed patterns (from existing ClarificationEngine):**

| Pattern | Example | Category |
|---------|---------|----------|
| Neutral target question | "Who are you attacking?" | Reference resolution |
| Binary choice | "Did you mean {A} or {B}?" | Disambiguation |
| Multiple choice | "Which one — {A}, {B}, or {C}?" | Disambiguation |
| Location question | "Where do you want to center that?" | Reference resolution |
| Action question | "What are you trying to do?" | Re-prompt |
| Echo confirmation | "Alright, you attack {target} with your {weapon}." | Table-talk |
| Physical constraint | "You can't get there — there's something in the way." | Post-resolution fact |

**Forbidden patterns (contract violations — must never appear):**

| Pattern | Example | Why forbidden |
|---------|---------|---------------|
| Consequence warning | "That will provoke an attack of opportunity." | Reveals mechanical consequence |
| Tactical suggestion | "You might want to use your bow instead." | Coaching |
| Target assessment | "That goblin is very dangerous." | Tactical assessment |
| Mechanical disclosure | "That target has high AC." | Reveals internals |
| Resource coaching | "You don't have enough spell slots for that." | Resource coaching (pre-resolution) |
| Judgment | "That's a bad idea." | Value judgment |
| Pre-emptive warning | "Keep in mind, the troll has regeneration." | Coaching disguised as context |
| System framing | "Warning: this action is risky." | System language, not DM persona |

---

## END OF INTENT BRIDGE CONTRACT v1

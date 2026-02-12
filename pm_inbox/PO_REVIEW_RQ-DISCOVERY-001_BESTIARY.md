# PO Review: RQ-DISCOVERY-001 — Discovery Log (Bestiary) Knowledge Mask

**From:** Jay (PO Delegate / Technical Advisor)
**To:** Opus (PM)
**Date:** 2026-02-12
**Re:** Work order RQ-DISCOVERY-001 dispatched to Opus (Audit) + Sonnet B
**Classification:** Pre-execution review — observations and risks

---

## Summary

This work order defines the contract for how canonical creature data (world truth) transforms into player-visible knowledge over time. The Discovery Log is a progressive revelation system — a bestiary that fills in as the player earns knowledge through encounters, skill checks, NPC reports, and study. Spec-only, no code changes.

Five artifacts produced:
1. `docs/contracts/DISCOVERY_LOG.md` — Full contract
2. `docs/schemas/knowledge_mask.schema.json` — Per-player knowledge record
3. `docs/schemas/bestiary_entry_view.schema.json` — Player-visible view (post-mask)
4. `tests/spec/discovery_log_compliance.md` — Testable compliance checklist
5. `docs/decisions/DEC-DISCOVERY-001.md` — Decision record: canonical is never directly exposed

---

## Assessment: The work order is strong

This is one of the cleaner spec dispatches I've reviewed. The constraints are correct, the scope is bounded, and the conceptual model is sound. Specific observations:

### 1. The three-model split is architecturally correct

`CanonicalCreatureEntry` (world truth) → `PlayerKnowledgeMask` (what's been earned) → `PlayerVisibleBestiaryEntry` (rendered view) is the right decomposition. It maps cleanly onto the existing authority model:

- Canonical lives in the World Bundle (compile-time, frozen, Box-tier authority)
- Mask is runtime state derived from events (Lens-tier, deterministic)
- Visible entry is a pure function of Canonical + Mask (no hidden inputs)

This means the visible entry is replay-stable by construction. Same world bundle + same event log = same bestiary view. The determinism invariant holds without extra work.

### 2. The knowledge sources taxonomy is well-chosen

The five sources (EncounterObservation, SkillCheckResult, NPCReport, StudyAction, ItemMediated) cover the space without overcomplicating it. Each maps to a real in-game event that Box can emit and the event log can record. The hearsay/reliable distinction for NPCReport is particularly important — it prevents "an NPC told me it's weak to fire" from being treated as verified truth.

### 3. The no-coaching constraint applies differently here than in the Intent Bridge

In RQ-INTENT-001, no-coaching means "don't advise during action selection." Here it means something subtler: **the bestiary must not reveal information the player hasn't earned, even when the system knows it.** The temptation is to show "Resistant to fire" because it would help the player — that's coaching through revelation. The spec correctly requires that every revealed field cite an enabling event.

### 4. The asset binding hooks are correctly scoped

The work order specifies the interface contract for silhouette → partial → full portrait rendering, but explicitly excludes the asset generation pipeline. This is the right boundary — the discovery log needs to say "at state X, show asset tier Y," but it shouldn't define how the assets are produced.

---

## What Already Exists

### This is entirely greenfield

No bestiary schema, no knowledge mask, no discovery tracking, no progressive revelation, no asset binding system exists in the codebase. Zero lines of implementation.

### What is documented (vision-level)

| Document | Relevant content |
|----------|-----------------|
| [UX_VISION_PHYSICAL_TABLE.md](docs/specs/UX_VISION_PHYSICAL_TABLE.md) (lines 84-98) | Four knowledge states: heard_of → seen → fought → studied. Pokedex-style progression. Silhouette → sketch → colored → full. Knowledge sources listed. |
| [RQ-TABLE-FOUNDATIONS-001.md](docs/planning/RQ-TABLE-FOUNDATIONS-001.md) (Research Topic B, lines 118-148) | Deliverables scoped: BestiaryEntry schema, KnowledgeMask schema, knowledge events taxonomy, field-level gating, image prompt contracts, unit-testable leak detection. |
| [RQ-TABLE-FOUNDATIONS-001.md](docs/planning/RQ-TABLE-FOUNDATIONS-001.md) (Research Topic F, lines 151-180) | Asset pool rotation model: category pools, permanent binding, replacement generation queue. |
| [AD-007](docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md) | Layer B (Presentation Semantics): world-authored, frozen semantic tags. The discovery log needs to respect this — revealed abilities should include presentation semantics, not raw mechanical IDs. |

### Adjacent systems that exist and must be interfaced with

| System | File | Relevance |
|--------|------|-----------|
| Event log | `aidm/core/event_log.py` | Knowledge events must be recordable here |
| Campaign schemas | `aidm/schemas/campaign.py` | World bundle will host canonical creature entries |
| Asset store | `aidm/core/asset_store.py` | Binding registry for portrait/token assignment |
| MonsterDoctrine | `aidm/schemas/doctrine.py` | Tactical behavior profiles per creature — must be bound to bestiary entries but NOT revealed to players |
| NarrativeBrief | `aidm/lens/narrative_brief.py` | Discovery reveals may need to flow through here for Spark to reference |
| Context assembler | `aidm/lens/context_assembler.py` | RetrievedItem pattern could be extended for knowledge events |

---

## Gaps and Considerations

### 1. Content independence is load-bearing here

The manifesto now commits to content independence: mechanics are procedures, names are skin, meaning is emergent. The work order correctly states "no D&D/WotC names, stat blocks, or text in shipped outputs." But this has a deeper implication for the bestiary spec:

**CanonicalCreatureEntry cannot reference D&D ability names, spell names, or creature type taxonomy.**

Instead, canonical entries must use:
- World-authored names (bound at world compile time)
- Mechanical IDs that resolve to world vocabulary
- Presentation semantics tags (from AD-007 Layer B)

The spec should define CanonicalCreatureEntry using generic fields (ability IDs, trait IDs, taxonomy tags) that a world compiler binds to names. The examples in the spec must use invented world vocabulary, not D&D terms.

### 2. The "studied" state needs careful definition

The four-state progression (heard_of → seen → fought → studied) is clear for the first three:
- heard_of: an NPC mentioned it, or the player read about it
- seen: the player's character visually observed it
- fought: the player's character engaged it in mechanical interaction

But "studied" is ambiguous. Does it mean:
- A specific downtime action was taken?
- A skill check was passed at a high enough DC?
- Multiple encounters accumulated?
- A combination?

The spec needs to define what events transition to "studied" and what additional fields it unlocks. This is the state where numeric ranges or detailed capabilities might become visible, so the reveal threshold matters.

### 3. The privacy boundary needs formal treatment

The work order mentions "player A's knowledge must not reveal player B's knowledge." In a multiplayer session where Player A fought a creature and Player B only heard about it, their bestiary views must differ. This means:

- KnowledgeMask is per-player, not per-party
- Events carry a `witnessed_by` field (which PCs were present)
- Knowledge sharing requires an explicit in-game event (PC A tells PC B what they know)
- The rendering function takes `(canonical, mask_for_this_player)` — never a merged group mask

The spec should define the sharing mechanic as a knowledge source type (something like `PartyShare` with the source player as provenance).

### 4. Numeric exposure policy is a doctrine decision

The work order asks the spec to define when numeric data is shown ("very tough" vs "AC 22"). This is a product-level decision that should be consistent with the manifesto and the No-Opaque-DM Doctrine.

The manifesto says the system is accountable in every outcome. If a player has "studied" a creature, should they see actual numeric ranges? The answer affects trust:

- **Non-numeric only:** Preserves mystery but players can't verify fairness
- **Numeric at studied tier:** Rewards mastery and enables verification
- **Numeric always available (opt-in transparency):** Fully consistent with "the system asks you to verify it"

The spec should present these as options and recommend one, but this may need PO decision before it's locked.

### 5. Knowledge decay / reliability is worth addressing

Not all knowledge is equally reliable:
- "I fought it and observed it use fire breath" — high reliability
- "A drunk merchant told me they're weak to silver" — low reliability
- "I read about them in an ancient tome" — medium reliability, possibly outdated

The spec should define a reliability tier on revealed fields, not just a binary revealed/hidden state. Hearsay-sourced reveals should be visually distinguished from combat-observed reveals. This is already hinted in the work order's NPCReport "hearsay vs reliable" note but should be formalized.

### 6. Relationship to the world compiler (not yet built)

CanonicalCreatureEntry lives in the World Bundle. The world compiler doesn't exist yet. The spec should define the canonical schema independently of the compiler — the compiler produces these entries, but the bestiary spec owns their shape.

This means the spec is defining part of the World Model contract (Phase 1.1 in the roadmap) as a side effect. That's fine, but the PM should be aware that this spec will partially constrain the world compiler's output format.

---

## Risks to Watch

### Risk 1: The spec defines D&D creatures as examples

The examples need to use invented world vocabulary. If the agent writes "Goblin: AC 15, HP 7, darkvision 60ft" as example canonical entries, that's both an IP issue and a content-dependence violation. Examples should use something like "Thornback: carapace_defense high, vitality low, sense_mode: tremorsense."

**Mitigation:** Instruct the agent to invent creature examples using generic vocabulary. No PHB/MM references in the spec artifacts.

### Risk 2: The field reveal matrix becomes too granular

There's a temptation to define reveal rules for every conceivable creature attribute (movement speed, carrying capacity, diet, sleep patterns, social structure...). The matrix should cover the minimum set of fields that are mechanically or experientially relevant, with an explicit extension mechanism for world-specific additions.

**Mitigation:** Define 10-15 core fields with reveal rules. Add an `extended_fields` mechanism for world-specific additions. Don't try to enumerate everything.

### Risk 3: The state machine overcomplicates transitions

Four states with five knowledge source types and per-field reveal rules creates a large combinatorial space. If every source type can trigger any state transition on any field independently, the spec becomes untestable.

**Mitigation:** Keep the state machine on the entry level (the overall knowledge stage), and use the field reveal matrix as a lookup (stage × field → visible/hidden). Don't allow per-field independent state progression in v1 — that can be added later if needed.

### Risk 4: Asset binding contract conflicts with future asset pipeline

The spec defines the interface for "show silhouette at heard_of, partial at seen, full at studied." But the asset pipeline doesn't exist yet. If the spec assumes a specific asset format or generation pipeline, it may conflict with whatever gets built later.

**Mitigation:** The spec should define asset tier requirements (what quality/detail level is needed at each knowledge stage) without specifying format. Use abstract references: `asset_ref: {pool_category, binding_id, required_tier}`.

---

## Dependency Map

```
AD-007 (Presentation Semantics) ← Must be consulted
    ↓
RQ-DISCOVERY-001 (this spec) ← Defines knowledge mask + bestiary view
    ↓
Future: World Compiler (Phase 1.1) ← Produces canonical entries per this schema
    ↓
Future: Discovery Log Backend (Phase 2.3) ← Implements the spec
    ↓
Future: Asset Pipeline ← Produces assets per binding contract
```

This spec sits at the right point in the dependency chain: after the vision documents and AD-007, before implementation. It constrains downstream work without depending on unbuilt systems.

---

## Relationship to Other Active Work

| Work | Interaction |
|------|-------------|
| RQ-INTENT-001 (Intent Bridge) | "I study the creature" is an intent that needs to map to a StudyAction event. The intent bridge spec should define this action class. The two specs should be cross-referenced but can be developed in parallel. |
| RQ-PHYS-001 (RAW Gaps Research) | Creature physical attributes (size, weight, carrying capacity) may be revealed through the discovery log. The physical affordance policies should be consistent with what the bestiary reveals. |
| AD-007 (Presentation Semantics) | Revealed abilities should include presentation semantics tags, not raw mechanical IDs. The bestiary view should reference the world's presentation vocabulary. |
| Manifesto (Content Independence) | The canonical entry schema must be world-vocabulary-agnostic. D&D-specific terms cannot appear in the schema definition. |

---

## Recommendation

**Approve execution with these additions:**

1. **Instruct the agent to use invented world vocabulary in all examples.** No D&D creature names, ability names, or stat block formats. Content independence is doctrine.

2. **Flag the numeric exposure policy as a PO decision point.** The spec should present options and recommend, but the final call on "when do players see numbers" may need explicit PO approval given its impact on the trust/mystery balance.

3. **Provide the agent with the adjacent system inventory** from this review (event log, campaign schemas, asset store, doctrine, NarrativeBrief). The spec needs to define interface seams with these systems even though it doesn't modify them.

4. **Constrain the field reveal matrix to 10-15 core fields in v1.** Define the extension mechanism, but don't let the matrix balloon. World-specific fields are the world compiler's problem.

The work order is well-structured, the constraints are correct, and the greenfield status means there's no implementation conflict risk. The main execution risk is scope inflation through overly granular field definitions and state transitions.

---

*— Jay*

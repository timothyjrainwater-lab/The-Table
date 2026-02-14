# RQ-SPRINT-005: Content Verification and Player Trust

**Status:** COMPLETE
**Sprint:** RQ-SPRINT-005
**Date:** 2026-02-14
**Author:** Research Agent (Opus 4.6)
**Scope:** Provenance, traceability, compile-time validation, runtime validation, player-facing auditability

---

## Executive Summary

The Table's core doctrine -- "No Opaque DM" -- demands that every outcome trace to Rules As Written or declared House Policy. The bone layer is mechanically sound: event sourcing (`EventLog`, BL-008), deterministic replay (`reduce_event()`, BL-012), immutable resolution records (`EngineResult`, BL-007), and structured citation tracking (`Citation`) provide a strong provenance foundation. The critical gap is the absence of a **verification bridge between layers**: nothing currently validates that what the player SEES (narration, rulebook entries, visual effects) accurately represents what HAPPENED (events, dice rolls, state transitions).

The infrastructure to close this gap exists in skeletal form -- `source_event_ids` in `NarrativeBrief`, `narration_token` in `EngineResult`, `presentation_semantics` in the brief -- but no validator consumes these fields. This document specifies the compile-time and runtime validation rule sets needed to close the gap, defines the complete traceability chain from every player-visible surface back to the bone layer, and proposes four player-facing audit UX concepts that operate within the Table Metaphor.

**Core Finding:** The bone cannot lie (append-only, immutable, citation-linked, deterministically replayable). The presentation cannot drift (Layer B frozen at compile). What is missing is the enforcement that narration cannot contradict, and the player-facing tooling that lets a player verify on demand.

---

## 1. Current Provenance Infrastructure Assessment

### 1.1 What Exists (Strengths)

| # | Component | File | Provenance Role |
|---|-----------|------|-----------------|
| 1 | **Event Sourcing** | `aidm/core/event_log.py` | Append-only ledger with monotonic event IDs (BL-008). Each `Event` carries `event_id`, `event_type`, `timestamp`, `payload`, `rng_offset`, `citations`. Out-of-order or duplicate IDs rejected with `ValueError`. |
| 2 | **Deterministic Replay** | `aidm/core/replay_runner.py` | `reduce_event()` is the SINGLE canonical state reducer (BL-012). `ReplayReport` with `final_hash` for determinism verification. Same event stream produces identical `WorldState`. |
| 3 | **EngineResult Immutability** | `aidm/schemas/engine_result.py` | Freezes on creation via `__post_init__` (BL-007). Contains `events` (tuple), `rolls` (tuple of `RollResult` with `rng_offset` per roll), `state_changes` (tuple of `StateChange`), `narration_token`. Post-construction mutation raises `EngineResultFrozenError`. |
| 4 | **Citation Schema** | `aidm/schemas/citation.py` | Structured references with `source_id` (12-char hex), `short_name`, `page`, `span`, `rule_id`, `obsidian_uri`. Attached to events in the log. |
| 5 | **NarrativeBrief One-Way Valve** | `aidm/lens/narrative_brief.py` | Frozen dataclass controlling what mechanical data Spark can see (BL-003). Carries `source_event_ids` for provenance, `presentation_semantics` for Layer B data, `provenance_tag` (always `[DERIVED]`). |
| 6 | **Presentation Semantics Registry** | `aidm/schemas/presentation_semantics.py` | AD-007 three-layer model (Layer A Behavior, Layer B Presentation, Layer C Narration). `AbilityPresentationEntry` frozen at compile time with `delivery_mode`, `staging`, `origin_rule`, `vfx_tags`, `sfx_tags`, `scale`, `residue`, `contraindications`. |
| 7 | **Transparency Tri-Gem Socket** | `aidm/schemas/transparency.py` | Three modes: RUBY (minimal -- final result only), SAPPHIRE (key rolls and modifiers), DIAMOND (full breakdown with citations). `FilteredSTP` carries `event_id` for traceability. `TransparencyConfig` per player. |
| 8 | **Rulebook Object Model** | `aidm/schemas/rulebook.py` | `RuleEntry` binding `content_id` to `procedure_id` with `parameters` (`RuleParameters`), `text_slots` (`RuleTextSlots`), `provenance` (`RuleProvenance` with `compiler_version`, `seed_used`, `content_pack_id`, `llm_output_hash`). |
| 9 | **Discovery Log** | `aidm/lens/discovery_log.py` | Progressive revelation state machine. Per-player, per-entity knowledge tiers. Transitions via explicit `KnowledgeEvent` only. Deterministic: same event stream produces same knowledge state. |
| 10 | **Boundary Law Enforcement** | `tests/test_boundary_law.py` | BL-001 through BL-015 as executable assertions. Structural invariants enforced by CI. |

### 1.2 Critical Gaps

| Gap ID | Description | Impact | Existing Hooks |
|--------|-------------|--------|----------------|
| **GAP-1** | No narration-to-event contradiction checker -- nothing validates Spark output against mechanical events | Spark could describe a miss as a hit, a living target as dead, or a minor wound as devastating | `NarrativeBrief.source_event_ids` exists but no consumer validates narration text against these events |
| **GAP-2** | No compile-time Layer B vs Layer A cross-validation | A spell with `target_type: "single"` could have `delivery_mode: BURST_FROM_POINT` -- the presentation would describe area behavior for a single-target ability | `RuleParameters` and `AbilityPresentationEntry` both exist, share `content_id`, but no validation pass compares them |
| **GAP-3** | No player-facing audit surface -- Tri-Gem Socket schema exists but no UI renders it | Players cannot exercise their right to verify. Trust depends on faith, not transparency | `FilteredSTP`, `TransparencyConfig`, `TransparencyMode` all implemented. No rendering consumer exists. |
| **GAP-4** | No event-to-narration linkage persistence -- no reverse index from narration to event IDs | After a session, there is no way to answer "what narration was generated for event #47?" | `NarrativeBrief.source_event_ids` maps brief-to-events, but the narration text itself is not persisted with its event linkage |
| **GAP-5** | No `RuleEntry`-to-`EngineResult` citation flow -- cannot trace from rulebook entry to resolution history | Player opens a rulebook entry and cannot see "this spell was cast 3 times in Session 12" | `RuleEntry.content_id` and `EngineResult.events` both exist; no index connects them |

### 1.3 Assessment Summary

The bone layer provides **complete provenance** for mechanical outcomes: every state change traces to an event, every event has an ID and timestamp, every roll has an RNG offset, every event can carry citations. The skin layer provides **complete presentation metadata**: every ability has frozen delivery mode, staging, VFX/SFX tags, scale, and contraindications. What is missing is the **verification bridge** -- validation logic that consumes both layers and detects inconsistency.

---

## 2. Compile-Time Validation Rule Set

These rules execute during World Compilation, after the Content Pack has been processed and both `RuleEntry` (Layer A parameters) and `AbilityPresentationEntry` (Layer B presentation) have been generated for each content item. They catch inconsistencies before the world is ever used in play.

### 2.1 Rule Definitions

| Rule ID | Name | Layer A Field(s) | Layer B Field(s) | Violation Condition |
|---------|------|-------------------|-------------------|---------------------|
| **CT-001** | Delivery Mode vs Target Type | `RuleParameters.target_type` | `AbilityPresentationEntry.delivery_mode` | Single-target abilities (`target_type: "single"`) must not have area delivery modes (`BURST_FROM_POINT`, `CONE`, `LINE`, `EMANATION`). A Magic Missile targets one creature; it cannot visually present as a burst. |
| **CT-002** | Delivery Mode vs Area Shape | `RuleParameters.area_shape` | `AbilityPresentationEntry.delivery_mode` | Area shapes must match delivery modes. `area_shape: "burst"` requires `BURST_FROM_POINT`. `area_shape: "cone"` requires `CONE`. `area_shape: "line"` requires `LINE`. Mismatches mean the visual behavior contradicts the mechanical area. |
| **CT-003** | Origin Rule vs Delivery Mode | `RuleParameters.range_ft` (0 = touch) | `AbilityPresentationEntry.origin_rule`, `delivery_mode` | Touch-range abilities (`range_ft: 0`) must have `origin_rule: FROM_CASTER` and `delivery_mode: TOUCH`. A touch spell cannot visually originate from a chosen point 60 feet away. |
| **CT-004** | Scale vs Damage Magnitude | `RuleParameters.damage_dice` | `AbilityPresentationEntry.scale` | Presentation scale should correspond to mechanical impact. A cantrip dealing `1d3` should not have `scale: CATASTROPHIC`. A 9th-level blast dealing `20d6` should not have `scale: SUBTLE`. Thresholds: `SUBTLE` <= 2d6, `MODERATE` <= 6d6, `DRAMATIC` <= 12d6, `CATASTROPHIC` > 12d6. |
| **CT-005** | Save Type vs Staging | `RuleParameters.save_type` | `AbilityPresentationEntry.staging` | Abilities with `save_type: None` (no save allowed) should not have staging that implies a save opportunity (e.g., `DELAYED` suggests the target has time to react). Conversely, abilities with saves should not have `INSTANT` staging that implies no reaction window. This is a WARN-level rule, not a FAIL, because stylistic staging can vary. |
| **CT-006** | Contraindication Enforcement | `RuleParameters.damage_type` | `AbilityPresentationEntry.contraindications`, `vfx_tags`, `sfx_tags` | Tags listed in `contraindications` must not appear in the same entry's `vfx_tags` or `sfx_tags`. A fire spell with `contraindication: ["ice", "frost"]` must not have `vfx_tags: ("frost_crystals",)`. Additionally, `damage_type` should not contradict VFX: a `"fire"` damage ability should not have ice-themed VFX. |
| **CT-007** | Residue vs Staging | `RuleParameters.duration_unit` | `AbilityPresentationEntry.residue`, `staging` | Instant effects (`duration_unit: "instantaneous"`) with non-empty `residue` may be inconsistent -- instant damage does not typically leave visual residue. Lingering effects (`staging: LINGER`) with empty `residue` are likely wrong -- lingering effects should leave some visual trace. WARN level. |

### 2.2 Required Metadata

All metadata fields consumed by CT-001 through CT-007 already exist in the codebase:

- `RuleParameters`: `target_type`, `area_shape`, `range_ft`, `damage_dice`, `damage_type`, `save_type`, `duration_unit` -- all defined in `aidm/schemas/rulebook.py`
- `AbilityPresentationEntry`: `delivery_mode`, `staging`, `origin_rule`, `scale`, `vfx_tags`, `sfx_tags`, `residue`, `contraindications` -- all defined in `aidm/schemas/presentation_semantics.py`

No new schema fields are required. The validation pass is pure logic over existing data.

### 2.3 Validation Pass Integration Point

The World Compiler already produces both `RuleEntry` and `AbilityPresentationEntry` objects keyed by `content_id`. The compile-time validation pass should:

1. Iterate all `content_id` values that appear in both registries
2. For each, load the `RuleEntry.parameters` and the corresponding `AbilityPresentationEntry`
3. Run CT-001 through CT-007
4. Emit a `CompileValidationReport` with PASS/WARN/FAIL per rule per entry
5. FAIL-level violations block world compilation; WARN-level violations are logged and included in the world metadata

---

## 3. Runtime Validation Pipeline Design

### 3.1 Architecture

```
Box (EngineResult)
  |
  v
Lens (NarrativeBrief -- one-way valve, source_event_ids populated)
  |
  v
Spark (generates narration_text from NarrativeBrief)
  |
  v
NarrationValidator [NEW] -- compares narration_text against NarrativeBrief truth frame
  |
  +---> PASS: emit narration_text to player
  +---> WARN: emit narration_text, log warning for post-session review
  +---> FAIL: reject narration_text, emit template fallback narration
```

The `NarrationValidator` sits **after** Spark and **before** output. It is a pure function: `(narration_text: str, brief: NarrativeBrief) -> ValidationReport`. It has no access to Box state (BL-003 compliance). It validates only against the truth frame already exposed through the brief.

### 3.2 Validation Rules

| Rule ID | Name | Brief Field(s) Consumed | Check Logic | Severity |
|---------|------|-------------------------|-------------|----------|
| **RV-001** | Hit/Miss Consistency | `action_type` (`attack_hit` vs `attack_miss`) | If `action_type == "attack_hit"`, narration must not contain miss-language (from `MISS_KEYWORDS`). If `action_type == "attack_miss"`, narration must not contain hit-language (from `HIT_KEYWORDS`). Reuses existing keyword lists from `ContradictionChecker`. | FAIL |
| **RV-002** | Defeat Consistency | `target_defeated` | If `target_defeated == True`, narration must not describe the target continuing to fight, standing firm, or retaliating. If `target_defeated == False`, narration must not describe the target dying, falling lifeless, or being destroyed. | FAIL |
| **RV-003** | Severity-Narration Alignment | `severity` | Narration for `severity: "minor"` must not use devastating/catastrophic language. Narration for `severity: "lethal"` must not use trivial/inconsequential language. Uses existing `SEVERITY_INFLATION` and `SEVERITY_DEFLATION` dictionaries from `ContradictionChecker`. | WARN |
| **RV-004** | Condition Consistency | `condition_applied`, `condition_removed` | If `condition_applied` is set (e.g., `"prone"`), the narration should reference the condition or its physical manifestation. The narration must not introduce phantom conditions (naming conditions not in `condition_applied`). | WARN |
| **RV-005** | Delivery Mode Consistency | `presentation_semantics.delivery_mode` | If `delivery_mode == PROJECTILE`, narration must not describe emanation, touch, or aura behavior. If `delivery_mode == TOUCH`, narration must not describe projectile flight. Cross-references delivery mode vocabulary. | FAIL |
| **RV-006** | Staging Consistency | `presentation_semantics.staging` | If `staging == TRAVEL_THEN_DETONATE`, narration should describe a two-phase sequence (travel, then impact). If `staging == INSTANT`, narration should not describe a slow build-up or travel phase. | WARN |
| **RV-007** | Contraindication Enforcement | `presentation_semantics.contraindications` | Any word or phrase listed in `contraindications` must not appear in the narration text. Direct substring/keyword match. Example: if `contraindications: ("ice", "frost", "cold")`, narration "a frost-rimmed bolt" would violate. | FAIL |
| **RV-008** | Save Result Consistency | `action_type` (`spell_resisted` vs `spell_damage_dealt`) | If `action_type == "spell_resisted"` (target saved), narration must not describe the full unmitigated effect. If the spell was fully effective, narration must not describe the target shrugging it off or resisting. | FAIL |

### 3.3 Validation Outcomes

| Outcome | Behavior | Player Experience |
|---------|----------|-------------------|
| **PASS** | Emit Spark narration normally | Player receives creative, LLM-generated narration |
| **WARN** | Emit Spark narration, log warning to session validation log | Player receives creative narration. DM/developer can review warnings post-session. No player disruption. |
| **FAIL** | Reject Spark narration, substitute template fallback from `narration_token` | Player receives mechanically accurate but less creative narration. Accuracy is never sacrificed for creativity. |

### 3.4 Template Fallback Mechanism

When `NarrationValidator` returns FAIL, the system falls back to template narration keyed by `EngineResult.narration_token`. Template narration is:

- **Mechanically accurate by construction** -- templates are parameterized by brief fields, not LLM-generated
- **Less creative** -- follows fixed patterns ("Tordek strikes the goblin with his longsword, dealing a moderate wound")
- **Deterministic** -- same brief always produces same template output
- **Never wrong** -- the template cannot contradict the brief because it is derived from the brief

The player may notice less varied narration. This is acceptable: the Table doctrine is "never wrong" over "always creative."

### 3.5 Overlap with ContradictionChecker

The existing `ContradictionChecker` (`aidm/narration/contradiction_checker.py`, ~713 lines) performs similar checks with ~210 keywords across 9 lists. `NarrationValidator` differs in three ways:

1. **Post-Spark, not pre-Spark** -- ContradictionChecker shapes the prompt; NarrationValidator validates the output
2. **Layer B aware** -- NarrationValidator consumes `presentation_semantics`; ContradictionChecker does not
3. **Enforcement, not guidance** -- NarrationValidator can reject and substitute; ContradictionChecker only warns

The two are complementary: ContradictionChecker reduces the probability of violations; NarrationValidator enforces the guarantee.

---

## 4. Player-Facing Audit UX Concepts

All concepts operate within the **Table Metaphor**: no menus, no sidebars, no floating UI panels. Everything is an object on the table that the player can pick up, examine, or put down.

### 4.1 Concept A: The Transparency Gem (Tri-Gem Socket)

**Metaphor:** The player holds up a gemstone that changes how they see the world.

**Implementation:** Leverages existing `TransparencyConfig` (per-player mode) and `FilteredSTP` (mode-filtered event display).

| Gem | Mode | Player Sees |
|-----|------|-------------|
| **Ruby** | `TransparencyMode.RUBY` | Narration-focused. "The fireball engulfs three goblins. Two fall; one staggers." No numbers. |
| **Sapphire** | `TransparencyMode.SAPPHIRE` | Key numbers inline. "Fireball: Goblin A Reflex DC 15, rolled 8 -- failed (24 fire damage). Goblin B Reflex DC 15, rolled 17 -- saved (12 damage). Goblin C Reflex DC 15, rolled 3 -- failed (24 damage, defeated)." |
| **Diamond** | `TransparencyMode.DIAMOND` | Full breakdown with citations. Each roll shows natural die, all modifiers with sources, target value with breakdown, rule citation. "Goblin A: Reflex save = d20(8) + DEX(+1) + armor(+0) = 9 vs DC 15 (CL 5 + INT mod 3 + base 10, PHB p.241). Failed. 8d6 fire = [3,5,2,6,1,4,2,1] = 24. No resistance." |

**Interaction:** Player picks up gem from their tray, holds it up, current transparency level changes. Place it back down to return to previous mode. Mode persists per player across the session via `TransparencyConfig`.

**Data Flow:** `Event` -> `FilteredSTP` (filtered by `TransparencyMode`) -> rendered to player. `FilteredSTP.event_id` links back to the source event for drill-down.

### 4.2 Concept B: The Crystal Ball ("Why Did That Happen?")

**Metaphor:** The player peers into a crystal ball to see the mechanical truth behind a narrative moment.

**Trigger:** Player activates crystal ball, selects a specific narration moment (by pointing at it in the session log or the most recent narration).

**What It Shows:**

1. The complete mechanical chain for that moment:
   - Attack roll: natural die, all modifier sources, total vs target AC
   - AC breakdown: base 10, armor, shield, DEX, size, natural, deflection, dodge (each with source)
   - Damage roll: dice results, modifier sources, damage type, resistances applied
   - Rule citations: PHB page for attack resolution, relevant feat/ability pages
2. The `NarrativeBrief` that was sent to Spark (what data the narrator had to work with)
3. The `narration_token` that classified this moment
4. The `source_event_ids` linking to raw events

**Data Flow:** Narration text -> `NarrativeBrief.source_event_ids` -> `Event` records (from `EventLog`) -> `EngineResult.rolls` (via matching `result_id`) -> `RollResult` with `rng_offset` -> `Citation` references.

**Trust Mechanism:** The player can verify that the narration ("Your sword glances off the goblin's shield") matches the mechanical reality (attack roll 12 + 5 = 17 vs AC 18, miss by 1, shield AC contributing +2 was the difference).

### 4.3 Concept C: Post-Session Replay Journal

**Metaphor:** After the session, a leather-bound journal appears on the table. Opening it reveals the session's story with mechanical annotations.

**Layout:**

| Left Page (Narration) | Right Page (Mechanics) |
|------------------------|------------------------|
| "Tordek charges the ogre, his axe biting deep into the creature's thigh. The ogre bellows in pain, staggering but not falling." | **Round 3, Turn 2: Tordek** |
| | Attack: d20(16) + BAB(+6) + STR(+4) + charge(+2) = 28 vs AC 16. Hit. |
| | Damage: 1d12(8) + STR(+6) = 14 slashing. |
| | Ogre HP: 29/43 (32.6% lost, severity: moderate). |
| | Conditions: None applied. |
| | Citations: PHB p.154 (charge), PHB p.140 (attack roll). |

**Properties:**

- **Deterministic:** Replaying the `EventLog` through `reduce_event()` produces the identical journal. The narration text is stored alongside `source_event_ids`.
- **Aligned:** Each narration paragraph is aligned with its corresponding mechanical events via `source_event_ids`.
- **Dice as illustrations:** Natural die results rendered as die-face images in the margin.
- **Citations as margin notes:** Rule citations rendered as footnotes linking to the Tome (rulebook viewer).

**Data Flow:** `EventLog` (replayed) -> `NarrativeBrief` (reconstructed) + stored `narration_text` -> aligned display. `RollResult.rng_offset` + `master_seed` -> verified dice results.

### 4.4 Concept D: Rulebook Annotations (Tome Integration)

**Metaphor:** The player opens a rulebook entry (the "Tome") and sees not just the static description but a live "History" section showing when and how this rule was used in play.

**Static Section (from RuleEntry):**

- `text_slots.rulebook_description` -- full description
- `text_slots.short_description` -- one-line summary
- `text_slots.flavor_text` -- world-flavored lore
- `text_slots.mechanical_summary` -- concise mechanics
- `parameters` -- range, area, damage, save, duration

**Live History Section (from EngineResult index):**

- Session 12, Round 3: Cast by Tordek. 3 targets. Goblin A: Reflex save failed (24 fire). Goblin B: Reflex save succeeded (12 fire). Goblin C: Reflex save failed (24 fire, defeated).
- Session 11, Round 7: Cast by Tordek. 1 target. Bugbear: Reflex save succeeded (9 fire).

**Data Flow:** `RuleEntry.content_id` -> index of `EngineResult` events where `content_id` appears in event payload -> `FilteredSTP` rendering per `TransparencyConfig`.

**Trust Mechanism:** The player can see that the spell has been applied consistently across sessions. Same DC, same damage dice, same save type. No hidden DM fiat.

---

## 5. Traceability Chain Specification

### 5.1 Chain 1: Narration Text -> Bone

Every piece of narration text the player reads must trace back to a mechanical event:

```
narration_text (what the player reads)
  |
  v
NarrativeBrief (the truth frame Spark was given)
  |-- source_event_ids: (47, 48, 49)     <- which events produced this brief
  |-- action_type: "attack_hit"           <- mechanical classification
  |-- severity: "moderate"                <- derived from HP math
  |-- target_defeated: False              <- derived from HP state
  |
  v
Event records (from EventLog, by event_id)
  |-- event_id: 47, event_type: "attack_roll"
  |   |-- payload: {natural: 16, total: 23, target_ac: 18, hit: True}
  |   |-- rng_offset: 142
  |   |-- citations: [{source_id: "681f92bc94ff", page: 140}]  <- PHB p.140
  |
  |-- event_id: 48, event_type: "damage_roll"
  |   |-- payload: {dice: "1d8+4", natural: 6, total: 10, type: "slashing"}
  |   |-- rng_offset: 143
  |
  |-- event_id: 49, event_type: "hp_changed"
  |   |-- payload: {entity: "goblin_01", old_hp: 18, new_hp: 8}
  |
  v
EngineResult (the resolution record)
  |-- rolls: [RollResult(rng_offset=142, ...), RollResult(rng_offset=143, ...)]
  |-- state_changes: [StateChange(entity_id="goblin_01", field="hp", old=18, new=8)]
  |-- narration_token: "melee_attack_hit_moderate"
  |
  v
RNG Verification
  |-- master_seed + rng_offset=142 -> deterministic d20 result = 16 (verified)
  |-- master_seed + rng_offset=143 -> deterministic 1d8 result = 6 (verified)
  |
  v
Rulebook Citation
  |-- PHB p.140: Attack roll procedure
```

### 5.2 Chain 2: Rulebook Entry -> Bone

Every rulebook entry the player reads traces to a content pack template and engine procedure:

```
RuleEntry (what the player sees in the Tome)
  |-- content_id: "spell.fireball_003"
  |-- world_name: "Ignis Conflagration"          <- world-flavored name
  |-- text_slots.rulebook_description: "..."     <- world-flavored text
  |
  v
RuleEntry internals
  |-- procedure_id: "spell.aoe_reflex_damage"    <- engine procedure reference
  |-- parameters: RuleParameters(
  |       area_shape="burst", area_radius_ft=20,
  |       damage_dice="1d6_per_CL", damage_type="fire",
  |       save_type="reflex", save_effect="half",
  |       range_ft=400)
  |-- provenance: RuleProvenance(
  |       source="world_compiler", compiler_version="0.4.2",
  |       seed_used=8472901, content_pack_id="dnd35_core_spells",
  |       llm_output_hash="a3f8c1...")
  |
  v
AbilityPresentationEntry (Layer B, frozen at compile)
  |-- content_id: "spell.fireball_003"            <- same content_id
  |-- delivery_mode: BURST_FROM_POINT
  |-- staging: TRAVEL_THEN_DETONATE
  |-- origin_rule: FROM_CHOSEN_POINT
  |-- scale: DRAMATIC
  |-- vfx_tags: ("fire", "explosion", "radial_burst")
  |-- residue: ("scorch_marks", "smoke")
  |-- contraindications: ("ice", "frost", "cold")
  |
  v
Content Pack Template
  |-- Defines mechanical substrate: "deal [dice] [type] damage in [shape] area, [save] for half"
  |-- World Compiler binds parameters + generates text_slots + generates Layer B tags
  |
  v
Engine Resolver
  |-- procedure_id: "spell.aoe_reflex_damage"
  |-- At runtime: consumes parameters, resolves saves per target, emits events
```

### 5.3 Chain 3: Visual Effects -> Bone

Every battle map animation the player sees traces to mechanical outcomes:

```
Battle map animation (what the player sees)
  |-- A fiery projectile travels from caster to chosen point, then explodes in a radial burst
  |
  v
AbilityPresentationEntry (drives animation selection)
  |-- delivery_mode: BURST_FROM_POINT      <- projectile + burst
  |-- staging: TRAVEL_THEN_DETONATE        <- two-phase animation
  |-- origin_rule: FROM_CHOSEN_POINT       <- animation origin
  |-- scale: DRAMATIC                      <- animation intensity
  |-- vfx_tags: ("fire", "explosion")      <- particle/shader selection
  |-- residue: ("scorch_marks", "smoke")   <- post-animation overlay
  |
  v
EngineResult (which tiles, who takes damage, save results)
  |-- events: [
  |     {type: "spell_cast", payload: {content_id: "spell.fireball_003", target_point: [5,3]}},
  |     {type: "save_rolled", payload: {entity: "goblin_01", save: "reflex", dc: 15, roll: 8, success: False}},
  |     {type: "damage_applied", payload: {entity: "goblin_01", amount: 24, type: "fire"}},
  |     ...per target...
  |   ]
  |
  v
Box state (WorldState)
  |-- Affected tiles calculated by geometric engine from area_shape + area_radius_ft
  |-- HP changes applied via reduce_event()
  |-- Conditions applied if any
```

### 5.4 Chain 4: Character Sheet -> Bone

Every character sheet field the player sees traces to events:

```
Character sheet field (what the player sees)
  |-- HP: 8/43
  |
  v
Events (state mutation history)
  |-- event_id: 49, type: "hp_changed", payload: {old: 18, new: 8}
  |-- event_id: 32, type: "hp_changed", payload: {old: 30, new: 18}
  |-- event_id: 15, type: "hp_changed", payload: {old: 43, new: 30}
  |-- event_id: 1,  type: "set_entity_field", payload: {field: "max_hp", value: 43}
  |
  v
reduce_event() (canonical state reducer, BL-012)
  |-- Applies each event in order to WorldState
  |-- Final state: WorldState.entities["tordek"].hp = 8
  |
  v
Verification: replay EventLog from event 0 -> identical final state
```

### 5.5 Summary: Complete Traceability Matrix

| # | Player Sees | Traces To | Via | Verification Method |
|---|-------------|-----------|-----|---------------------|
| 1 | Narration text | Source events | `NarrativeBrief.source_event_ids` | Compare narration against brief truth frame (NarrationValidator) |
| 2 | Mechanical numbers (SAPPHIRE/DIAMOND) | `RollResult` | `FilteredSTP.event_id` | RNG offset + master seed reproduces roll |
| 3 | Modifier breakdown (DIAMOND) | Modifier sources | `RollBreakdown.modifiers[].source` | Each modifier traceable to character stat, feat, condition, or item |
| 4 | Rulebook entry | `RuleEntry.parameters` | `RulebookRegistry.get_entry(content_id)` | Parameters match engine procedure behavior |
| 5 | Ability visual behavior | `AbilityPresentationEntry` | `PresentationSemanticsRegistry` | Compile-time validation (CT-001 through CT-007) |
| 6 | Character sheet fields | `WorldState` entity fields | `Event` -> `reduce_event()` | Replay event log, compare final state hash |
| 7 | Dice results | RNG stream | `RollResult.rng_offset` + `master_seed` | Deterministic: same seed + offset = same result |
| 8 | Rule citations | `Citation.source_id` + `page` | Vault/Obsidian deep link (`obsidian_uri`) | Page reference verifiable against source material |

---

## 6. Answer: How Does "No Opaque DM" Extend Through the Skin Layer?

The "No Opaque DM" doctrine originates in the bone layer (mechanical transparency) but must extend through presentation and narration to the player. Three complementary mechanisms achieve this:

### Mechanism 1: Structural Impossibility of Contradiction (Compile-Time)

Layer B (`AbilityPresentationEntry`) is frozen at world compile time. Compile-time validation (CT-001 through CT-007) catches inconsistencies between Layer A (mechanical parameters) and Layer B (presentation semantics) before the world is ever used. A single-target spell cannot visually present as an area burst. A fire spell cannot have ice VFX. A touch attack cannot originate from a distant point.

**What this guarantees:** The *vocabulary* of presentation (delivery modes, staging patterns, VFX tags, scale) is mechanically consistent. The world cannot be compiled with contradictory presentation metadata.

### Mechanism 2: Runtime Detection of Narration Lies

`NarrationValidator` (RV-001 through RV-008) compares every piece of Spark-generated narration against the `NarrativeBrief` truth frame. A miss cannot be described as a hit. A living target cannot be described as dead. A minor wound cannot be described as devastating. A fire spell cannot be narrated with ice imagery if `contraindications` forbids it.

**What this guarantees:** When narration contradicts mechanical truth, the system detects it and falls back to template narration. The player may receive less creative narration, but **never false narration**.

### Mechanism 3: Player-Verifiable Audit Trail

Four audit surfaces (Transparency Gem, Crystal Ball, Replay Journal, Tome Annotations) give the player the **ability** to verify any outcome at any time. The key trust property is not that the player *will* check, but that the player *knows they can* check.

- **Transparency Gem:** Real-time, adjustable detail level (RUBY/SAPPHIRE/DIAMOND)
- **Crystal Ball:** On-demand deep-dive into any specific moment
- **Replay Journal:** Post-session complete audit with narration-to-mechanics alignment
- **Tome Annotations:** Cross-session consistency verification for any rule

**What this guarantees:** Trust is earned by transparency, not demanded by authority. The DM (engine) operates in a glass house.

### The Complete Trust Chain

```
The bone CANNOT LIE
  (append-only, immutable, citation-linked, deterministically replayable)

The presentation CANNOT DRIFT
  (Layer B frozen at compile, validated against Layer A)

The narration CANNOT CONTRADICT
  (runtime validation with template fallback)

The player CAN ALWAYS LOOK
  (on-demand transparency tools at four levels of detail)
```

---

## 7. Implementation Priority

| Priority | Component | Effort | Dependencies | Impact |
|----------|-----------|--------|--------------|--------|
| **P0** | `NarrationValidator` (RV-001, RV-002, RV-008) | Medium | `NarrativeBrief` (exists), `ContradictionChecker` keyword lists (exist) | Closes GAP-1 for the three highest-severity contradiction types |
| **P0** | Compile-time validation pass (CT-001, CT-002, CT-003) | Low | `RuleParameters` (exists), `AbilityPresentationEntry` (exists) | Closes GAP-2 for structural delivery/target/origin mismatches |
| **P1** | Narration-to-event persistence (store narration_text with source_event_ids) | Low | `EventLog` (exists) | Closes GAP-4, enables Replay Journal |
| **P1** | `FilteredSTP` renderer (Transparency Gem UI) | Medium | `FilteredSTP` (exists), `TransparencyConfig` (exists) | Closes GAP-3 for real-time transparency |
| **P2** | `RuleEntry`-to-`EngineResult` index | Medium | `RuleEntry` (exists), `EngineResult` (exists) | Closes GAP-5, enables Tome Annotations |
| **P2** | Crystal Ball deep-dive UI | High | `FilteredSTP` renderer (P1), narration persistence (P1) | Full provenance drill-down |
| **P3** | Post-Session Replay Journal | High | Narration persistence (P1), `FilteredSTP` renderer (P1) | Complete session audit |
| **P3** | Remaining compile-time rules (CT-004 through CT-007) | Low | CT-001 through CT-003 infrastructure (P0) | WARN-level consistency checks |

---

## Appendix A: File Reference

| File | Role in Trust Chain |
|------|---------------------|
| `aidm/core/event_log.py` | Append-only event ledger, monotonic IDs (BL-008). Foundation of all provenance. |
| `aidm/core/replay_runner.py` | Deterministic state reduction via `reduce_event()` (BL-012). Replay verification. |
| `aidm/schemas/engine_result.py` | Immutable resolution record (BL-007). `EngineResult` with `rolls`, `state_changes`, `narration_token`. |
| `aidm/schemas/citation.py` | Structured source references: `source_id`, `short_name`, `page`, `span`, `rule_id`, `obsidian_uri`. |
| `aidm/schemas/transparency.py` | Tri-Gem Socket: `TransparencyMode` (RUBY/SAPPHIRE/DIAMOND), `FilteredSTP`, `TransparencyConfig`, `RollBreakdown`, `ModifierBreakdown`, `DamageBreakdown`. |
| `aidm/schemas/presentation_semantics.py` | Layer B frozen semantic tags (AD-007): `AbilityPresentationEntry` with `delivery_mode`, `staging`, `origin_rule`, `scale`, `vfx_tags`, `sfx_tags`, `residue`, `contraindications`. |
| `aidm/schemas/rulebook.py` | `RuleEntry` with `content_id`, `procedure_id`, `parameters` (`RuleParameters`), `text_slots` (`RuleTextSlots`), `provenance` (`RuleProvenance`). |
| `aidm/lens/narrative_brief.py` | One-way valve from Box to Spark. `NarrativeBrief` with `source_event_ids`, `presentation_semantics`, `provenance_tag`. |
| `aidm/lens/rulebook_registry.py` | Read-only registry for world-authored rule entries. Serves `RuleEntry` by `content_id`. |
| `aidm/lens/discovery_log.py` | Progressive bestiary knowledge state machine. Per-player, per-entity `KnowledgeTier` transitions. |
| `aidm/narration/contradiction_checker.py` | Pre-Spark contradiction detection (~210 keywords, 9 lists). Complementary to NarrationValidator. |
| `docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md` | Three-layer description model decision record. |
| `docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md` | Engine authority, narration obligations, boundary law specification. |
| `tests/test_boundary_law.py` | Structural invariant enforcement: BL-001 through BL-015 as executable assertions. |

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Bone Layer** | The mechanical engine (Box): event sourcing, state management, RNG, resolution. Authoritative. |
| **Skin Layer** | The presentation layer: narration (Spark), visual effects, rulebook text, character sheet display. Derived. |
| **Lens Layer** | The adapter between Bone and Skin: `NarrativeBrief`, `FilteredSTP`, `DiscoveryLog`. Controls what Skin can see. |
| **Layer A** | Behavior (mechanics). Deterministic. Owned by Box. |
| **Layer B** | Presentation Semantics. Frozen at compile time. `AbilityPresentationEntry`. |
| **Layer C** | Narration. Ephemeral. Generated by Spark (LLM). |
| **STP** | Structured Truth Packet. The raw mechanical data from an event. |
| **FilteredSTP** | STP filtered by `TransparencyMode` for player display. |
| **NarrativeBrief** | The one-way valve: what Spark is allowed to see from Box outcomes. |
| **NarrationValidator** | [PROPOSED] Post-Spark validation layer. Compares narration against truth frame. |
| **Table Metaphor** | UX principle: everything is an object on the gaming table. No menus, no sidebars. |
| **Tri-Gem Socket** | Transparency system: RUBY (minimal), SAPPHIRE (standard), DIAMOND (full). |
| **No Opaque DM** | Core doctrine: every outcome must trace to RAW or declared House Policy. No hidden fiat. |

---

*End of RQ-SPRINT-005*

# Discovery Log Contract v1
## Progressive Revelation + Knowledge Mask

**Document ID:** RQ-DISCOVERY-001
**Version:** 1.0
**Date:** 2026-02-12
**Status:** DRAFT — Awaiting PM + PO Approval
**Authority:** This document is the canonical contract for the Discovery Log (bestiary) subsystem.
**Scope:** How entity knowledge is progressively revealed to players, what fields are visible at each knowledge stage, how reveals are gated, and how asset bindings interact with the mask.

**References:**
- `docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md` (AD-007) — Layer B presentation semantics
- `docs/specs/UX_VISION_PHYSICAL_TABLE.md` (lines 84-98) — Four knowledge states vision
- `docs/planning/RQ-TABLE-FOUNDATIONS-001.md` (Research Topics B, F) — Bestiary and asset pool scoping
- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` — Provenance labels, authority model
- `docs/contracts/INTENT_BRIDGE.md` (RQ-INTENT-001) — Intent types that produce knowledge events

**Existing Implementation (this spec formalizes):**

| Layer | File | Status |
|-------|------|--------|
| Event log | `aidm/core/event_log.py` | Exists — knowledge events to be recorded here |
| Campaign schemas | `aidm/schemas/campaign.py` | Exists — world bundle hosts canonical entries |
| Asset store | `aidm/core/asset_store.py` | Exists — binding registry for portrait/token |
| Provenance | `aidm/core/provenance.py` | Exists — W3C PROV-DM tracking |
| MonsterDoctrine | `aidm/schemas/doctrine.py` | Exists — behavior profiles (NEVER revealed) |
| Discovery Log | — | **Partial implementation exists — see aidm/lens/discovery_log.py (canonical) and aidm/services/discovery_log.py (deprecated)** |

---

## Contract Summary (1-Page)

The Discovery Log tracks what each player character knows about entities (creatures, NPCs) encountered during play. Knowledge is earned incrementally through in-game events and recorded in a per-player **knowledge mask**. The player-visible bestiary entry is a pure function of the **canonical entry** (world truth, frozen at compile time) and the **knowledge mask** (runtime state, per-player).

**Three-Model Architecture:**

```
CanonicalCreatureEntry     PlayerKnowledgeMask      PlayerVisibleBestiaryEntry
(world truth, frozen)  ×   (earned reveals)     →   (rendered view)
     [BOX]                     [DERIVED]                  [output]
```

The canonical entry is authored at world compile time and frozen. The mask accumulates as knowledge events occur. The visible entry is computed — never stored — by projecting the canonical entry through the mask.

**Invariants:**
1. **Deterministic:** Same (world bundle + event log + player_id + seed) → same visible bestiary entry.
2. **No coaching:** The system reveals earned facts. It never warns, advises, hints, or nudges.
3. **No leaks:** Fields not unlocked by the current mask are absent from the visible entry. No partial values, no "???" placeholders that leak field existence.
4. **Fail-closed:** Missing assets, unknown entities, or unresolvable bindings produce defined placeholder behavior — never a best-effort guess.
5. **Content-independent:** Schema field names and enum values contain no game-system-specific vocabulary. World-specific names appear only in compiled canonical entries.
6. **Provenance-tagged:** Every revealed field carries a provenance label (`[BOX]`, `[DERIVED]`, `[NARRATIVE]`, `[UNCERTAIN]`) and a source event reference.
7. **Player-private:** Each player's mask is independent. Knowledge sharing requires an explicit in-game event.
8. **Authority boundary:** The Discovery Log reads world state and event history but never writes mechanical state. It is Lens-tier, not Box-tier.

---

## 1. Knowledge State Model

### 1.1 Canonical States

Knowledge about an entity progresses through four stages. The stage is tracked **per entity, per player** and can only advance — never regress.

| Stage | Label | Trigger | Description |
|-------|-------|---------|-------------|
| 0 | `unknown` | (default) | Player has no knowledge of this entity type. Not shown in bestiary. |
| 1 | `heard_of` | Rumor, document, NPC mention | Player has secondhand information. Name and vague description only. |
| 2 | `observed` | Visual contact during encounter | Player's character has personally seen the entity. Physical description visible. |
| 3 | `engaged` | Mechanical interaction (combat, skill contest) | Player has fought or directly interacted. Combat behaviors and observed abilities visible. |
| 4 | `studied` | Explicit study action + successful skill check | Player has achieved mastery. Detailed capabilities, resistances, and (if earned) numeric ranges visible. |

### 1.2 Stage Transition Rules

Transitions are monotonic — an entity's knowledge stage for a given player can only increase.

| From | To | Required Events |
|------|----|-----------------|
| `unknown` → `heard_of` | Any `npc_report`, `document_source`, or `party_share` event referencing this entity type |
| `heard_of` → `observed` | An `encounter_observation` event where this player's character has line of sight to the entity |
| `observed` → `engaged` | A `combat_interaction` event where this player's character is a participant in a mechanical exchange with the entity |
| `engaged` → `studied` | A `study_action` event where Box confirms a successful knowledge check (DC set by world data, resolved by Box) |

**Skipping stages:** A single event may advance multiple stages. Example: if a player's first contact with an entity is combat, the mask advances directly from `unknown` to `engaged` (the `heard_of` and `observed` stages are implicitly satisfied). The field reveals for all intermediate stages are included.

### 1.3 The `studied` Gate

The `studied` stage is the only stage gated by a **skill check resolved by Box**. The Discovery Log does not compute the check — it receives the result as a `study_action` event with `success: true/false` from Box. Failed checks do not advance the stage and are recorded in the mask's event ledger (to prevent identical retry spam if the world rules prohibit it).

What `studied` unlocks is defined in the field reveal matrix (§2.3). The PO decision on numeric exposure policy (§2.4) determines whether exact values or descriptive ranges are shown.

---

## 2. Knowledge Mask Schema

### 2.1 Canonical Bestiary Fields

A `CanonicalCreatureEntry` lives in the World Bundle and contains the full truth about an entity type. It is authored at world compile time and frozen.

The following fields constitute the core field set (v1). Worlds may define additional fields via `extended_fields`.

| # | Field | Type | Description | Category |
|---|-------|------|-------------|----------|
| 1 | `display_name` | string | World-authored name for this entity type | flavor |
| 2 | `aliases` | string[] | Alternative names, titles, regional names | flavor |
| 3 | `taxonomy_tags` | string[] | World-defined classification (e.g., "beast", "elemental", "construct") | flavor |
| 4 | `size_class` | enum | Categorical size (tiny, small, medium, large, huge, gargantuan, colossal) | observable |
| 5 | `physical_description` | string | Authored appearance description (frozen at compile) | observable |
| 6 | `movement_modes` | object[] | Movement types and relative speed class (slow/normal/fast/very_fast) | observable |
| 7 | `sense_modes` | string[] | Sensory capabilities (e.g., "tremorsense", "keen_smell") | inferred |
| 8 | `notable_abilities` | object[] | Abilities with presentation semantics refs (AD-007 Layer B content_ids) | mechanical |
| 9 | `observed_attack_forms` | object[] | Attack types with descriptive tags (not numeric values) | mechanical |
| 10 | `defense_profile` | object | Categorical defense descriptors (e.g., "heavily_armored", "evasive") | mechanical |
| 11 | `resistances` | string[] | Damage type resistances/immunities (world vocabulary) | mechanical |
| 12 | `vulnerabilities` | string[] | Damage type vulnerabilities (world vocabulary) | mechanical |
| 13 | `habitat_tags` | string[] | Preferred environments | flavor |
| 14 | `behavior_summary` | string | Authored behavioral description (territorial, ambush predator, etc.) | observable |
| 15 | `lore_text` | string | Extended world-authored lore passage | flavor |

**Field categories:**
- **flavor**: Non-mechanical world-building information
- **observable**: Information obtainable through direct visual observation
- **inferred**: Information that requires careful observation or specialized senses
- **mechanical**: Information about combat capabilities and game-relevant traits

### 2.2 Numeric Mechanical Fields (Box-Only, Conditional Exposure)

The following fields exist in the canonical entry but are **never directly exposed by default**. They are Box-tier authority and are only surfaced through the Discovery Log if the numeric exposure policy (§2.4) permits it at the `studied` stage.

| Field | Type | Exposure |
|-------|------|----------|
| `defense_value` | integer | Exact numeric defense rating |
| `vitality_range` | [int, int] | Min/max vitality (hit points) range |
| `ability_scores` | object | Raw ability score values |
| `save_modifiers` | object | Saving throw modifiers |
| `attack_modifiers` | object | Attack roll modifiers |
| `challenge_rating` | number | Numeric difficulty rating |

These fields are **always** present in the canonical entry (Box needs them). They are **conditionally** present in the visible entry — see §2.4.

### 2.3 Field Reveal Matrix

This matrix defines the **minimum** knowledge stage required for each field to appear in the player-visible entry. A field may also be individually revealed by a specific knowledge source before the entity reaches that stage (see §3 for source-specific overrides).

| Field | `heard_of` | `observed` | `engaged` | `studied` |
|-------|-----------|-----------|----------|----------|
| `display_name` | Yes | Yes | Yes | Yes |
| `aliases` | Partial (1 alias if from rumor) | Partial | Yes | Yes |
| `taxonomy_tags` | If source provides | Yes | Yes | Yes |
| `size_class` | — | Yes | Yes | Yes |
| `physical_description` | — | Yes | Yes | Yes |
| `movement_modes` | — | Types only | Types + speed class | Types + speed class |
| `sense_modes` | — | — | If observed in use | Yes |
| `notable_abilities` | — | — | Observed only | Yes |
| `observed_attack_forms` | — | — | Observed only | Yes |
| `defense_profile` | — | — | Categorical | Categorical |
| `resistances` | — | — | If observed in combat | Yes |
| `vulnerabilities` | — | — | If observed in combat | Yes |
| `habitat_tags` | If source provides | Yes | Yes | Yes |
| `behavior_summary` | — | Partial (visible behavior) | Yes | Yes |
| `lore_text` | — | — | — | Yes |

**"Observed only"** means the field appears only for abilities/attacks that the player's character has directly witnessed the entity use. Abilities not yet observed remain hidden even at `engaged` stage.

**"If observed in combat"** means the reveal requires a specific combat event where the resistance/vulnerability was mechanically relevant (e.g., the entity took reduced damage from fire in the player's presence).

### 2.4 Numeric Exposure Policy

**PO Decision Required.** This section defines three options. The selected policy is recorded in the world bundle's `display_policy` field and enforced uniformly.

| Policy | `engaged` shows | `studied` shows | Recommendation |
|--------|----------------|-----------------|----------------|
| **A: Descriptive only** | Categorical tags only ("heavily armored") | Categorical tags + comparative ("tougher than X") | Preserves mystery; limits player verification |
| **B: Ranges at mastery** | Categorical tags only | Numeric ranges (e.g., "defense: 18-22") | **Recommended.** Rewards mastery, enables verification without exact values |
| **C: Exact at mastery** | Categorical tags only | Exact numeric values | Full transparency; removes discovery incentive for mechanical details |

**Default (until PO decides):** Policy B — numeric ranges at `studied` stage.

Under Policy B, the `studied` stage reveals:
- `defense_value` as a range: `[value - 2, value + 2]`
- `vitality_range` as authored range (canonical entries include designed min/max)
- `attack_modifiers` as descriptive tier + range

The provenance label for range-exposed numerics is `[DERIVED]` (inferred from Box state but not exact).

---

## 3. Knowledge Sources

### 3.1 Source Taxonomy

Each knowledge source maps to a specific event type that Box or the event log can emit. Sources carry **reliability tiers** that affect how revealed information is displayed.

| Source Type | Event Name | Reliability | Trigger |
|-------------|------------|-------------|---------|
| `encounter_observation` | `knowledge.encounter_observation` | `high` | Character has line of sight to entity during encounter |
| `combat_interaction` | `knowledge.combat_interaction` | `high` | Character participates in mechanical exchange |
| `npc_report` | `knowledge.npc_report` | `low` or `medium` | NPC provides information (reliability set by NPC's `report_reliability` field) |
| `document_source` | `knowledge.document_source` | `medium` | Character reads a document, tome, or inscription |
| `study_action` | `knowledge.study_action` | `high` | Character performs deliberate study + Box resolves skill check |
| `party_share` | `knowledge.party_share` | Inherits source | One PC explicitly shares knowledge with another in-game |

### 3.2 Reliability Tiers

| Tier | Label | Display Treatment |
|------|-------|-------------------|
| `high` | Firsthand / Verified | Field shown normally. Provenance: `[BOX]` or `[DERIVED]` |
| `medium` | Documented / Reputable | Field shown with source attribution. Provenance: `[DERIVED]` |
| `low` | Hearsay / Unverified | Field shown with uncertainty marker. Provenance: `[UNCERTAIN]` |

When multiple sources reveal the same field, the **highest reliability** tier wins. The mask ledger retains all source events for auditability.

### 3.3 Source → Reveal Deltas

Each source type unlocks specific field reveals beyond those granted by the stage transition alone.

**`encounter_observation`:**
- Advances stage to at least `observed`
- Reveals: `display_name`, `size_class`, `physical_description`, `movement_modes` (types only), `habitat_tags` (current environment), `taxonomy_tags` (visible cues)

**`combat_interaction`:**
- Advances stage to at least `engaged`
- Reveals: All `observed` fields + `observed_attack_forms` (for attacks used), `notable_abilities` (for abilities used), `defense_profile` (categorical), `resistances` (if triggered), `vulnerabilities` (if triggered)
- Each combat event reveals only what was mechanically apparent in that specific exchange

**`npc_report`:**
- Advances stage to at least `heard_of`
- Reveals: `display_name`, optionally `aliases`, `habitat_tags`, `taxonomy_tags`, `behavior_summary`
- Specific fields depend on the `report_fields` array in the event payload
- Reliability is per-event (set by the NPC's reliability rating)

**`document_source`:**
- Advances stage to at least `heard_of`
- Reveals: `display_name`, `aliases`, `taxonomy_tags`, `habitat_tags`, `lore_text` (if document contains it), `behavior_summary`
- Specific fields depend on `document_fields` array in the event payload
- Reliability: `medium`

**`study_action`:**
- Advances stage to `studied` (if Box confirms success)
- Reveals: All fields including `lore_text`, `sense_modes`, all `notable_abilities`, all `observed_attack_forms`, `resistances`, `vulnerabilities`
- Numeric fields revealed per numeric exposure policy (§2.4)
- Failed study: no stage advance, event recorded in ledger

**`party_share`:**
- Inherits source player's reveals for this entity (fields + reliability tiers)
- Does NOT advance the receiving player's stage beyond the source player's stage
- Provenance chain: original source event → party_share event → receiving player's mask
- The receiving player sees shared fields with the inherited reliability tier, never upgraded

### 3.4 Event Payload Schema

All knowledge events share a common envelope:

```json
{
  "event_type": "knowledge.<source_type>",
  "timestamp": "ISO-8601",
  "entity_type_id": "canonical entry ID",
  "entity_instance_id": "specific instance (nullable for type-level knowledge)",
  "player_id": "receiving player",
  "witnessed_by": ["character_id_1", "character_id_2"],
  "source_reliability": "high | medium | low",
  "revealed_fields": ["field_name_1", "field_name_2"],
  "field_values": { "field_name": "revealed value or null for existence-only" },
  "box_event_ref": "reference to originating Box event (if any)",
  "seed": "deterministic seed for this event"
}
```

The `witnessed_by` array determines which player characters gain this knowledge. Only players whose characters are in `witnessed_by` receive the reveal. This enforces the per-player privacy boundary.

---

## 4. Reveal Ledger + Determinism

### 4.1 Reveal Ledger Structure

The knowledge mask for a given (player, entity_type) pair contains a **reveal ledger**: an append-only log of all knowledge events that contributed to the current mask state.

```
RevealLedger = [
  { event_ref, timestamp, source_type, reliability, fields_revealed },
  { event_ref, timestamp, source_type, reliability, fields_revealed },
  ...
]
```

The ledger is append-only. Events are never removed or modified. The current visible entry is recomputed by replaying the ledger against the canonical entry.

### 4.2 Deterministic Replay

The visible bestiary entry is a **pure function**:

```
visible_entry = render(canonical_entry, replay(ledger, display_policy))
```

Where:
- `canonical_entry` is frozen in the world bundle
- `ledger` is the ordered list of knowledge events for this (player, entity_type)
- `display_policy` is the world's numeric exposure policy
- `render` applies the mask to produce the visible entry

**Determinism guarantee:** Given the same world bundle, the same event log (up to the same point), and the same player_id, the visible entry is identical. No randomness, no LLM calls, no external state.

### 4.3 Deduplication

If a knowledge event reveals fields already revealed at equal or higher reliability, the event is still recorded in the ledger (for auditability) but produces no visible change. Reliability upgrades are applied: if a field was previously `[UNCERTAIN]` and a new `high` reliability source confirms it, the field's provenance upgrades.

---

## 5. Presentation Rules

### 5.1 Visual Asset Tiers

The Discovery Log specifies what **quality tier** of visual asset may be displayed at each knowledge stage. It does NOT specify asset formats, generation methods, or rendering implementation.

| Stage | Portrait Tier | Token Tier | Description |
|-------|--------------|-----------|-------------|
| `unknown` | — | — | Entity not shown in bestiary |
| `heard_of` | `silhouette` | `silhouette` | Solid dark shape. No identifying features. |
| `observed` | `sketch` | `outline` | Partial detail. Shape, size, and coloring visible. Major features identifiable. |
| `engaged` | `detailed` | `colored` | Full visual with identifiable features. Scars, armor, weapons visible. |
| `studied` | `full` | `full` | Complete, high-detail rendering. |

### 5.2 Crystal Ball / Active NPC Display

When an entity speaks or acts during play, the active display (crystal ball, conversation portrait) respects the **current mask state** for the viewing player.

- `heard_of`: Silhouette with entity name. No portrait features.
- `observed`: Sketch-quality portrait.
- `engaged` or `studied`: Full portrait.

The active display MUST NOT reveal a higher-quality portrait than the player's mask permits, even if the full asset exists in the binding registry.

### 5.3 Voice Profile Interaction

If the entity has a bound voice profile (see §6), the voice is always played at its bound quality — voice is not tiered by knowledge stage. The rationale: voice is an atmospheric immersion element, not an information channel. Hearing a voice does not constitute mechanical knowledge.

However, the **voice attribution** displayed alongside the audio respects the mask:
- `heard_of`: "Unknown voice" or entity name only
- `observed` or above: Entity name + portrait

### 5.4 Notebook / Bestiary Page Layout

The player's notebook bestiary page for an entity displays exactly the fields permitted by the mask. The page structure:

1. **Header:** Portrait (at permitted tier) + `display_name` + `taxonomy_tags` (if revealed)
2. **Physical:** `size_class`, `physical_description`, `movement_modes` (if revealed)
3. **Abilities:** `notable_abilities`, `observed_attack_forms` (revealed entries only)
4. **Defenses:** `defense_profile`, `resistances`, `vulnerabilities` (if revealed)
5. **Lore:** `behavior_summary`, `habitat_tags`, `lore_text` (if revealed)
6. **Encounter History:** Summary of encounters with this entity type (dates, outcomes — always shown if any knowledge exists)
7. **Source Annotations:** Per-field provenance labels and reliability indicators

Fields that are not yet revealed are **absent** — no blank sections, no "???" markers, no grayed-out placeholders. The page shows only what is known. The absence of a section is not itself information (all pages have variable length).

---

## 6. Asset Binding Interface

### 6.1 Binding Contract

When a canonical entity type is first referenced in play (first knowledge event for any player), the system permanently binds assets from the world's asset pools:

| Asset Type | Pool Category | Binding Rule |
|------------|--------------|-------------|
| Portrait set | `portrait.<taxonomy_tag>` | Deterministic selection: `hash(world_seed, entity_type_id, "portrait")` indexes into pool |
| Voice profile | `voice.<taxonomy_tag>` | Deterministic selection: `hash(world_seed, entity_type_id, "voice")` indexes into pool |
| Map token | `token.<size_class>` | Deterministic selection: `hash(world_seed, entity_type_id, "token")` indexes into pool |

### 6.2 Binding Permanence

Once bound, an entity's assets are permanent for the lifetime of the campaign. The binding is recorded in the asset binding registry and is deterministic — the same world seed and entity type ID always produce the same binding.

### 6.3 Portrait Tier Assets

A single portrait binding includes assets for all quality tiers:

```json
{
  "entity_type_id": "string",
  "portrait_binding": {
    "pool_category": "portrait.beast",
    "binding_id": "deterministic hash",
    "assets": {
      "silhouette": { "asset_ref": "..." },
      "sketch": { "asset_ref": "..." },
      "detailed": { "asset_ref": "..." },
      "full": { "asset_ref": "..." }
    }
  }
}
```

The Discovery Log selects which tier to display based on the player's knowledge stage. The binding registry stores all tiers; the mask controls access.

### 6.4 Pool Exhaustion

If an asset pool is exhausted (all items bound), the system:
1. Logs a warning event
2. Falls back to the `_fallback` pool for that category (if defined)
3. If no fallback: uses the placeholder asset (§7.2)

Pool exhaustion does NOT block gameplay or knowledge progression. The asset tier downgrades gracefully.

---

## 7. Failure Modes

### 7.1 Failure Taxonomy

| Failure | Trigger | Behavior |
|---------|---------|----------|
| Unknown entity type | Knowledge event references an `entity_type_id` not in the world bundle | Event rejected. Log error. No bestiary entry created. |
| Missing canonical field | World bundle entry lacks a field the mask would reveal | Field omitted from visible entry. No error surfaced to player. |
| Missing asset binding | First knowledge event but no matching asset pool | Use placeholder assets (§7.2). Log warning. |
| Asset pool exhausted | Pool has no unbound items remaining | Fall back to `_fallback` pool, then to placeholder. |
| Conflicting observations | Two sources provide contradictory information for same field | Higher-reliability source wins. If tied, most-recent wins. Both recorded in ledger. |
| Failed study check | `study_action` event with `success: false` | No stage advance. Event recorded in ledger. World rules determine retry policy. |
| Corrupted ledger | Ledger replay produces inconsistent state | Fail-closed: show last known good state. Log integrity error. |

### 7.2 Placeholder Assets

When an asset binding cannot be resolved, the system uses defined placeholders:

| Asset Type | Placeholder |
|------------|-------------|
| Portrait | Solid dark silhouette on neutral background (generic by `size_class`) |
| Voice | No voice playback. Text-only attribution. |
| Map token | Generic circle token colored by `size_class` |

Placeholder assets are never mistaken for real bindings — they carry a `placeholder: true` flag in the binding record.

---

## 8. Interaction with Adjacent Systems

### 8.1 Event Log (`aidm/core/event_log.py`)

Knowledge events are recorded in the campaign event log using the standard event envelope. The event log is the source of truth for ledger replay. Knowledge events use the `knowledge.*` namespace (§3.4).

### 8.2 World Bundle (`aidm/schemas/campaign.py`)

Canonical creature entries are part of the world bundle, compiled and frozen. The Discovery Log reads them but never modifies them. The world bundle schema must include:
- `creature_entries`: array of `CanonicalCreatureEntry` objects
- `display_policy`: the selected numeric exposure policy enum

### 8.3 Presentation Semantics (`docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md`)

Revealed abilities reference AD-007 Layer B `content_id` values, not raw mechanical identifiers. When the bestiary shows a "notable ability," it displays the world-authored `ui_description` from the presentation semantics registry, not the mechanical template name.

### 8.4 MonsterDoctrine (`aidm/schemas/doctrine.py`)

MonsterDoctrine defines tactical AI behavior profiles. These are **never** revealed through the Discovery Log. The doctrine is Box-tier internal state. The bestiary may show `behavior_summary` (world-authored prose) but never tactical parameters.

### 8.5 Narrative Brief (`aidm/lens/narrative_brief.py`)

When Spark narrates, it may reference the player's current knowledge mask to avoid describing things the player hasn't seen. The narrative brief can include `knowledge_context` with the player's current bestiary state for the relevant entities.

### 8.6 Intent Bridge (`docs/contracts/INTENT_BRIDGE.md`)

The `study_action` intent type (to be defined in RQ-INTENT-001 Tier 2) maps to a `knowledge.study_action` event. The intent bridge packages the player's declared study intent; Box resolves the skill check; the result flows back as a knowledge event.

---

## 9. Examples

All examples use invented world vocabulary. No game-system-specific creature names, ability names, or stat block formats.

### Example 1: First Rumor (unknown → heard_of)

**Scenario:** An NPC merchant mentions "Thornbacks" in conversation.

**Event:**
```json
{
  "event_type": "knowledge.npc_report",
  "entity_type_id": "creature.thornback",
  "player_id": "player_01",
  "witnessed_by": ["char_aldric"],
  "source_reliability": "low",
  "revealed_fields": ["display_name", "habitat_tags"],
  "field_values": {
    "display_name": "Thornback",
    "habitat_tags": ["deep_forest", "marshland"]
  }
}
```

**Mask after:** Stage = `heard_of`. Visible fields: `display_name` [UNCERTAIN], `habitat_tags` [UNCERTAIN].

**Bestiary page:** Name "Thornback" with uncertainty marker. Habitat: "deep forest, marshland" with "(hearsay)" annotation. Silhouette portrait. No other sections.

### Example 2: Document Discovery (heard_of, additional fields)

**Scenario:** Player finds a naturalist's journal describing Thornbacks.

**Event:**
```json
{
  "event_type": "knowledge.document_source",
  "entity_type_id": "creature.thornback",
  "player_id": "player_01",
  "witnessed_by": ["char_aldric"],
  "source_reliability": "medium",
  "revealed_fields": ["aliases", "taxonomy_tags", "behavior_summary"],
  "field_values": {
    "aliases": ["Spined Lurker"],
    "taxonomy_tags": ["beast", "reptilian"],
    "behavior_summary": "Ambush predator. Buries in mud, erupts when prey passes."
  }
}
```

**Mask after:** Stage = `heard_of` (no advance — document alone doesn't grant `observed`). New fields added at `medium` reliability.

**Bestiary page:** Name "Thornback" [UNCERTAIN→upgraded to DERIVED for `display_name` since document confirms]. Alias: "Spined Lurker" [DERIVED]. Classification: beast, reptilian [DERIVED]. Habitat: deep forest, marshland [UNCERTAIN from rumor]. Behavior: "Ambush predator..." [DERIVED]. Silhouette portrait.

### Example 3: Visual Encounter (heard_of → observed)

**Scenario:** Player's character sees a Thornback during exploration.

**Event:**
```json
{
  "event_type": "knowledge.encounter_observation",
  "entity_type_id": "creature.thornback",
  "player_id": "player_01",
  "witnessed_by": ["char_aldric", "char_mira"],
  "source_reliability": "high",
  "revealed_fields": ["size_class", "physical_description", "movement_modes", "habitat_tags"],
  "field_values": {
    "size_class": "medium",
    "physical_description": "Low-slung reptile with overlapping thorn-like spines along its back. Mottled brown-green hide. Four squat legs. Snout tapers to a blunt wedge.",
    "movement_modes": [{"mode": "walk", "speed_class": "slow"}, {"mode": "burrow", "speed_class": "normal"}],
    "habitat_tags": ["deep_forest", "marshland", "riverbank"]
  }
}
```

**Mask after:** Stage = `observed`. Portrait tier upgrades to `sketch`. All previously revealed fields retained; new fields added at `high` reliability.

**Bestiary page:** Sketch portrait. Name "Thornback" [DERIVED]. Physical description, size (medium), movement (walk: slow, burrow: normal). Habitat expanded with "riverbank" [BOX]. Previous rumor/document fields retained with their reliability tiers.

**Note:** `char_mira` (player_02) also receives this event if in `witnessed_by`. Player_02's mask updates independently.

### Example 4: Combat Encounter (observed → engaged)

**Scenario:** Player fights a Thornback. It uses its spine volley ability and resists a fire-based attack.

**Events (two events from one combat):**

Event A — Combat interaction:
```json
{
  "event_type": "knowledge.combat_interaction",
  "entity_type_id": "creature.thornback",
  "player_id": "player_01",
  "witnessed_by": ["char_aldric"],
  "source_reliability": "high",
  "revealed_fields": ["observed_attack_forms", "notable_abilities", "defense_profile"],
  "field_values": {
    "observed_attack_forms": [{"form_tag": "bite", "descriptors": ["piercing", "close"]}],
    "notable_abilities": [{"content_id": "ability.spine_volley", "observed_use": "fired a spray of hardened spines in a cone"}],
    "defense_profile": {"descriptor": "heavily_armored", "notes": "spines deflected slashing strikes"}
  }
}
```

Event B — Resistance observed:
```json
{
  "event_type": "knowledge.combat_interaction",
  "entity_type_id": "creature.thornback",
  "player_id": "player_01",
  "witnessed_by": ["char_aldric"],
  "source_reliability": "high",
  "revealed_fields": ["resistances"],
  "field_values": {
    "resistances": ["fire"]
  }
}
```

**Mask after:** Stage = `engaged`. Portrait tier upgrades to `detailed`.

**Bestiary page:** Detailed portrait. All previous fields. New sections: Attack forms — bite (piercing, close) [BOX]. Abilities — spine volley ("fired a spray of hardened spines in a cone", references AD-007 content_id) [BOX]. Defense — heavily armored [DERIVED]. Resistances — fire [BOX]. Encounter history updated with combat record.

### Example 5: Failed Study Attempt

**Scenario:** Player attempts to study the Thornback but fails the knowledge check.

**Event:**
```json
{
  "event_type": "knowledge.study_action",
  "entity_type_id": "creature.thornback",
  "player_id": "player_01",
  "witnessed_by": ["char_aldric"],
  "source_reliability": "high",
  "revealed_fields": [],
  "field_values": {},
  "box_event_ref": "box.skill_check.result_0042",
  "study_result": "failure"
}
```

**Mask after:** Stage remains `engaged`. No new fields. Event recorded in ledger (retry policy determined by world rules).

### Example 6: Successful Study (engaged → studied)

**Scenario:** Player successfully studies the Thornback on a later attempt.

**Event:**
```json
{
  "event_type": "knowledge.study_action",
  "entity_type_id": "creature.thornback",
  "player_id": "player_01",
  "witnessed_by": ["char_aldric"],
  "source_reliability": "high",
  "revealed_fields": ["sense_modes", "notable_abilities", "observed_attack_forms", "resistances", "vulnerabilities", "lore_text"],
  "field_values": {
    "sense_modes": ["tremorsense"],
    "notable_abilities": [
      {"content_id": "ability.spine_volley", "observed_use": "fires hardened spines in a cone"},
      {"content_id": "ability.mud_ambush", "observed_use": "bursts from concealment for a devastating first strike"}
    ],
    "vulnerabilities": ["cold"],
    "lore_text": "Thornbacks are solitary apex predators of riverine marshlands. They shed their spines seasonally, leaving trails of discarded barbs that trackers use to estimate local population."
  }
}
```

**Mask after:** Stage = `studied`. Portrait tier upgrades to `full`. Under Policy B, numeric ranges now visible: defense value range, vitality range.

**Bestiary page:** Full portrait. Complete field set. Lore section populated. Numeric ranges shown as "[DERIVED] — estimated defense: 16-20, vitality: 28-36". All abilities listed (including those not personally observed). Full provenance trail.

### Example 7: Party Knowledge Sharing

**Scenario:** Player 01 (Aldric) shares Thornback knowledge with Player 02 (Mira), who only previously observed a Thornback.

**Event:**
```json
{
  "event_type": "knowledge.party_share",
  "entity_type_id": "creature.thornback",
  "player_id": "player_02",
  "witnessed_by": ["char_mira"],
  "source_reliability": "high",
  "source_player_id": "player_01",
  "shared_fields": ["notable_abilities", "resistances", "vulnerabilities", "defense_profile"],
  "inherited_reliability": {
    "notable_abilities": "high",
    "resistances": "high",
    "vulnerabilities": "high",
    "defense_profile": "high"
  }
}
```

**Mask after (Player 02):** Stage remains `observed` (party_share does not advance stage beyond source's earned stage in the receiving player's progression — Mira hasn't fought one herself). But newly shared fields are now visible at inherited reliability. Mira would need her own combat event to reach `engaged`, or her own study to reach `studied`.

### Example 8: Hearsay Conflict Resolution

**Scenario:** An unreliable NPC claims Thornbacks are vulnerable to fire. The player has already observed (in combat) that they are resistant to fire.

**Existing mask field:** `resistances: ["fire"]` at `high` reliability.

**New event:**
```json
{
  "event_type": "knowledge.npc_report",
  "entity_type_id": "creature.thornback",
  "player_id": "player_01",
  "source_reliability": "low",
  "revealed_fields": ["vulnerabilities"],
  "field_values": {
    "vulnerabilities": ["fire"]
  }
}
```

**Resolution:** The new event is recorded in the ledger. The `vulnerabilities` field now contains "fire" at `low` reliability. But `resistances` already contains "fire" at `high` reliability. The visible entry shows both — the resistance (verified, `[BOX]`) and the rumored vulnerability (unverified, `[UNCERTAIN]`). The system does not resolve the contradiction; the player must evaluate the conflicting information. This is intentional: no coaching.

### Example 9: First Contact in Combat (unknown → engaged, stage skip)

**Scenario:** Player encounters and fights a Glassfang (never heard of before) in a single encounter.

**Events (bundled from single encounter):**
1. `encounter_observation` → reveals physical fields
2. `combat_interaction` → reveals combat fields

**Mask after:** Stage = `engaged` (skipped `heard_of` and `observed`). All fields from `heard_of`, `observed`, and `engaged` stages are revealed per the matrix. Portrait binding triggered on first event; portrait displayed at `detailed` tier.

### Example 10: Unknown Entity Failure

**Scenario:** An event references `creature.shadow_wyrm` which does not exist in the world bundle.

**Behavior:** Event is rejected. Error logged: "Unknown entity_type_id: creature.shadow_wyrm — not present in world bundle." No bestiary entry created. No player-facing error. The event is discarded from the knowledge event stream (but logged in system diagnostics).

### Example 11: Missing Asset Pool

**Scenario:** A Crystalwing (taxonomy: elemental, aerial) is first encountered but no `portrait.elemental` pool exists in the world's asset pools.

**Behavior:**
1. System checks `portrait.elemental` → not found
2. System checks `portrait._fallback` → found, binds from fallback pool
3. Portrait binding recorded with `fallback: true` flag
4. If `portrait._fallback` also exhausted → placeholder silhouette used
5. Gameplay continues normally. Player sees silhouette or fallback portrait per mask tier.

### Example 12: NPC with Voice Binding

**Scenario:** Player hears about the "Ironjaw Matriarch" from a bard (heard_of stage), then later meets her in person.

**At `heard_of`:** Bestiary shows name + silhouette. If the Matriarch is narrated speaking (flashback or quoted dialogue), voice plays but display shows "Unknown voice — Ironjaw Matriarch."

**At `observed`:** Sketch portrait. Voice plays with name + sketch attribution.

**At `engaged`:** Detailed portrait. Full voice attribution.

Voice quality does not change between stages — only the visual attribution context changes.

---

## 10. Compliance Summary

The full machine-testable compliance checklist is in `tests/spec/discovery_log_compliance.md`. Key invariants tested:

1. **No leak:** No field appears in a visible entry unless the mask permits it.
2. **Provenance required:** Every revealed field has a provenance label and source event reference.
3. **Deterministic replay:** Same inputs → same visible entry, verified by run-twice comparison.
4. **No coaching:** No output contains advisory, warning, or tactical language.
5. **Fail-closed:** All failure modes produce defined, safe behavior — never best-effort.
6. **Stage monotonicity:** Knowledge stages only advance, never regress.
7. **Privacy boundary:** Player A's mask never influences Player B's visible entry.
8. **Content independence:** Schema field names and enum values contain no game-system-specific vocabulary.

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **Canonical entry** | The full, frozen truth about an entity type. Lives in the world bundle. Box-tier authority. |
| **Knowledge mask** | Per-player, per-entity-type record of what has been revealed and how. Lens-tier. |
| **Visible entry** | The computed bestiary page: `render(canonical, mask)`. Never stored. |
| **Reveal ledger** | Append-only log of knowledge events that built the current mask. |
| **Stage** | The overall knowledge level for an entity: unknown → heard_of → observed → engaged → studied. |
| **Reveal delta** | The set of fields unlocked by a single knowledge event. |
| **Reliability tier** | Confidence level of a knowledge source: high, medium, low. |
| **Asset binding** | Permanent, deterministic assignment of portrait/voice/token to an entity type. |
| **Display policy** | World-level setting controlling numeric exposure at each knowledge stage. |

## Appendix B: Schema Cross-References

| Schema | File | Purpose |
|--------|------|---------|
| Discovery entry | `docs/schemas/discovery_entry.schema.json` | Canonical creature entry structure |
| Knowledge mask | `docs/schemas/knowledge_mask.schema.json` | Per-player mask + reveal ledger |
| Asset binding | `docs/schemas/asset_binding.schema.json` | Entity → asset binding registry |
| Presentation semantics | `docs/schemas/presentation_semantics_registry.schema.json` | AD-007 Layer B refs |
| Intent request | `docs/schemas/intent_request.schema.json` | Study action intent |

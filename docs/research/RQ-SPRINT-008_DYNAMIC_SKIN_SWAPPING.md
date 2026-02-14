# RQ-SPRINT-008: Dynamic Skin-Swapping — Live World Theme Transitions

**Status:** COMPLETE
**Sprint:** 008
**Date:** 2026-02-14
**Author:** Research Queue / Architecture Review

---

## Core Question

> Can you change the flavor of a living world without losing its history?

## Answer: YES

The Table's three-layer architecture (Box / Lens / Spark) is inherently multi-skin capable. Event log records bone-layer IDs exclusively. WorldState is purely mechanical. Name resolution happens at Lens boundary at presentation time.

No new subsystem is required. The separation already exists. This document maps the proof, the boundaries, the transition UX, and the customization surface.

---

## 1. Architectural Feasibility

### 1.1 Event Log Uses Bone-Layer IDs Only

Every event persisted to the event log references entities, weapons, spells, and locations by their internal content IDs — never by display names.

```
# Example event record (bone-layer)
{
  "turn": 14,
  "type": "attack_roll",
  "actor_id": "entity_0x3A7",
  "target_id": "entity_0x1F2",
  "weapon_id": "weapon_longsword_plus1",
  "roll": 17,
  "hit": true,
  "damage": 9
}
```

There is no `"actor_name": "Grothak the Foul"` stored in the event. The name is resolved later, at presentation time, through the VocabularyRegistry. This means the event log is **skin-neutral by construction**.

**Files examined:** `aidm/core/event_log.py`, `aidm/schemas/entity_fields.py`

### 1.2 WorldState Contains No Skin Fields

WorldState tracks HP, AC, ability scores, positions, conditions, initiative order, spell slots, inventory contents, and every other mechanical value. It does not store:

- Display names
- Narration fragments
- Tone metadata
- Art or VFX references

WorldState is a pure mechanical snapshot. Swapping a skin does not touch it.

**Files examined:** `aidm/core/state.py`

### 1.3 Replay Is Deterministic and Skin-Independent

The replay runner consumes the event log and the master seed to reconstruct WorldState. Because events contain only bone-layer IDs and mechanical outcomes, replay produces identical mechanical state regardless of which skin was active when the events were originally recorded.

**Files examined:** `aidm/core/replay_runner.py`

### 1.4 VocabularyRegistry Is the Skin

The VocabularyRegistry maps `content_id` to `world_name`. This mapping **is** the skin. Swap the registry, and every entity, weapon, spell, and location acquires a new display name. The mechanical identity is unchanged.

```
# Skin A: Classic High Fantasy
vocabulary_a = {
    "entity_0x3A7": "Grothak the Foul",
    "weapon_longsword_plus1": "Moonbane",
    "spell_fireball": "Fireball",
    "location_town_01": "Silverhollow",
}

# Skin B: Gothic Horror
vocabulary_b = {
    "entity_0x3A7": "The Pallid Warden",
    "weapon_longsword_plus1": "The Whispering Edge",
    "spell_fireball": "Corpsefire",
    "location_town_01": "Ashenmoor",
}
```

Same entity. Same +1 longsword. Same 6d6 fire damage in a 20-ft radius. Different world.

**Files examined:** `aidm/schemas/vocabulary.py`, `aidm/lens/presentation_registry.py`

### 1.5 NarrativeBrief Is Assembled Fresh Each Turn

The NarrativeBrief — the prose output presented to the player — is constructed at the Lens boundary every turn. It pulls mechanical state from Box, resolves names through VocabularyRegistry, applies tone directives from the active skin, and assembles the final output. Nothing is cached across turns in a way that would resist a skin swap.

**Files examined:** `aidm/lens/narrative_brief.py`, `aidm/schemas/presentation_semantics.py`

---

## 2. State Preservation Matrix

### 2.1 Survives Intact (Zero Modification on Skin Swap)

These values are bone-layer mechanical state. A skin swap does not read, write, or reference them.

| Category | Examples |
|---|---|
| Hit Points | Current HP, max HP, temp HP |
| Armor Class | Base AC, touch AC, flat-footed AC |
| Ability Scores | STR, DEX, CON, INT, WIS, CHA (base and modified) |
| Positions | Grid coordinates, elevation, facing |
| Conditions | Prone, grappled, stunned, frightened, etc. |
| Initiative | Initiative order, initiative modifier, delay/ready state |
| Combat State | Current round, active combatant, action economy |
| XP and Level | Experience points, character level, ECL |
| Feats | All feat selections and prerequisites |
| Skills | Skill ranks, synergy bonuses, armor check penalties |
| BAB | Base attack bonus, iterative attacks |
| Saves | Fort, Ref, Will (base and modified) |
| Damage Reduction | DR value and bypass type |
| Spell Slots | Slots per day, slots expended, spells prepared |
| Inventory | Item IDs, quantities, equipped status, weight |
| Event Log | Complete turn-by-turn mechanical history |
| Master Seed | RNG seed for deterministic replay |
| State Hashes | Integrity verification checksums |

### 2.2 Remapped on Swap (Name/Presentation Layer Only)

These values are replaced wholesale by the new skin's VocabularyRegistry and tone directives.

| Category | What Changes |
|---|---|
| NPC / Creature Names | Display names resolved from entity IDs |
| Spell Names | Display names resolved from spell content IDs |
| VFX / SFX Tags | Visual/audio presentation hints in NarrativeBrief |
| Narration Tone | Prose style, adjective density, mood vocabulary |
| Scene Descriptions | Environmental prose, atmosphere, sensory detail |
| Location / Faction Names | Display names resolved from location/faction IDs |
| Token Art | Art asset references (if visual layer exists) |

### 2.3 Design Decision Required (Hybrid Cases)

These cases have both mechanical and presentation aspects. The mechanical component survives; the presentation component must be explicitly handled.

| Category | Recommendation |
|---|---|
| **Items** | Keep all mechanical properties (enhancement bonus, damage type, weight, cost). Remap display name through VocabularyRegistry. A `+1 longsword` remains a `+1 longsword` mechanically — it just changes from "Moonbane" to "The Whispering Edge." |
| **Spells** | Keep spell slots, preparation, and all mechanical effects (damage, save DC, range, duration, components). Remap spell name. `Fireball` becomes `Corpsefire` but still deals 6d6 fire in a 20-ft radius spread. |
| **Class Features** | Keep all mechanical effects. Remap display name only if the skin provides a class-feature vocabulary entry. A Paladin's Smite Evil is still +CHA to hit, +level to damage — the skin may call it "Wrathstrike" or leave it unchanged. |
| **Conditions** | Keep all mechanical effects. Remap display name if the skin provides condition vocabulary. "Frightened" might become "Dread-Touched" but the -2 penalty to attack rolls, saves, skill checks, and ability checks is unchanged. |
| **Session Transcript** | **Freeze as historical record.** The transcript was generated under a specific skin. It references names, tone, and flavor that belong to that skin. Do not retroactively rewrite it. Append a `[SKIN TRANSITION]` marker and continue under the new skin. This preserves emotional fidelity and append-only integrity. |

---

## 3. Event Log Multi-Skin Analysis

### 3.1 Mechanical Replay Across Skins

Events can be replayed through a different skin with **perfect mechanical fidelity**. The replay runner does not consume names. It consumes IDs, rolls, and outcomes. The Lens layer can re-present the same mechanical history under any skin at any time.

This means:

- A session played under Skin A can be **narrated** under Skin B after the fact.
- The mechanical audit trail is identical regardless of skin.
- State hashes computed from WorldState are skin-invariant.

### 3.2 Recommended: `skin_active` Metadata Tag

While the event log does not require skin information for mechanical correctness, an optional metadata tag is recommended for auditability and UX:

```
{
  "turn": 14,
  "type": "attack_roll",
  "actor_id": "entity_0x3A7",
  "target_id": "entity_0x1F2",
  "weapon_id": "weapon_longsword_plus1",
  "roll": 17,
  "hit": true,
  "damage": 9,
  "_meta": {
      "skin_active": "gothic_horror_v1",
      "skin_transition": false
  }
}
```

This tag is:
- **Write-once** — recorded at event creation, never modified.
- **Non-mechanical** — the replay runner ignores it.
- **Diagnostic** — useful for debugging presentation issues and understanding session history.

### 3.3 Session Transcript Is Skin-Bound Forever

The session transcript (the natural-language narration presented to players) is generated under a specific skin. It is correct to leave it bound to that skin permanently. Reasons:

1. **Emotional fidelity.** The player experienced "Grothak the Foul" in that moment. Retroactively renaming him to "The Pallid Warden" in the transcript falsifies the player's memory.
2. **Append-only integrity.** The transcript is an append-only log. Rewriting history violates the contract.
3. **Deterministic reconstruction.** If the transcript ever needs to be re-generated, the `skin_active` metadata tag on each event tells the Lens which skin to use for each segment.

---

## 4. Transition UX Concepts

Four approaches to executing a skin swap at runtime, ordered from most thorough to most lightweight.

### 4.1 Approach A: Full Recompile

**Mechanism:** Tear down the active VocabularyRegistry, load the new skin's registry, rebuild all cached NarrativeBrief fragments, and revalidate presentation consistency.

| Property | Value |
|---|---|
| Latency | 3–10 seconds (depends on world size) |
| Coverage | Total — every name, tone, and presentation element is guaranteed consistent |
| Consistency | Perfect — no stale references possible |
| Disruption | Session pause required |
| Best For | Major theme changes (e.g., high fantasy to sci-fi reskin) |

**Sequence:**
1. Freeze session (no new events).
2. Snapshot current WorldState.
3. Unload active VocabularyRegistry.
4. Load target skin's VocabularyRegistry.
5. Load target skin's tone directives.
6. Rebuild NarrativeBrief cache.
7. Insert `[SKIN TRANSITION]` marker in transcript.
8. Resume session.

### 4.2 Approach B: Live Re-Skin at Session Boundary

**Mechanism:** Swap the VocabularyRegistry between sessions. The next session starts under the new skin. No rebuild required because NarrativeBrief is assembled fresh each turn.

| Property | Value |
|---|---|
| Latency | Instant (registry pointer swap) |
| Coverage | Complete from next turn onward |
| Consistency | Perfect — NarrativeBrief is never cached across session boundaries |
| Disruption | None — swap happens between sessions |
| Best For | Planned theme changes, campaign arc transitions |

**Sequence:**
1. End current session normally.
2. Swap VocabularyRegistry to target skin.
3. Swap tone directives to target skin.
4. Begin new session. NarrativeBrief assembles under new skin automatically.

### 4.3 Approach C: Partial Re-Skin (Per-Domain Selective)

**Mechanism:** Swap only specific domains of the VocabularyRegistry (e.g., swap location names but keep NPC names). Requires domain-tagged registry entries.

| Property | Value |
|---|---|
| Latency | Instant per domain |
| Coverage | Selective — only chosen domains change |
| Consistency | Requires careful domain boundary management |
| Disruption | Minimal — can happen mid-session |
| Best For | Power users, incremental customization, genre-blending |

**Domains available for independent swap:**
- `npc_names`
- `creature_names`
- `location_names`
- `faction_names`
- `spell_names`
- `item_names`
- `tone_directives`
- `vfx_sfx_tags`

**Risk:** Mixed skins can produce tonal inconsistency. Mitigate with a "consistency check" pass that flags clashing tone across domains.

### 4.4 Approach D: Curated Preset Selector

**Mechanism:** Offer a menu of pre-built skin presets. Each preset is a complete, tested VocabularyRegistry plus tone directives. User selects from a gallery; system applies via Approach B.

| Property | Value |
|---|---|
| Latency | Instant (preset load + registry swap) |
| Coverage | Complete |
| Consistency | Guaranteed — presets are pre-validated |
| Disruption | None — swap at session boundary |
| Best For | Most users, MVP, onboarding |

**Recommended as MVP approach.** Lowest cognitive load, highest consistency guarantee, zero configuration required from the user.

**Example Presets:**
- Classic High Fantasy (Tolkien-adjacent)
- Dark Fantasy / Gothic Horror
- Sword & Sorcery (pulp, Conan-adjacent)
- Mythic Greek / Roman
- Wuxia / Eastern Fantasy
- Grimdark / Low Fantasy
- Fairy Tale / Whimsical
- Planar / Cosmic Horror

---

## 5. Skin Customization Interface Concepts

Five concepts for how users interact with skin selection and customization, ordered by implementation phase.

### 5.1 Phase 1 (MVP): Theme Preset Gallery with Previews

A visual gallery of curated skin presets. Each preset shows:
- Theme name and one-line description.
- Sample NarrativeBrief paragraph rendered under that skin.
- Sample NPC name, location name, and item name.
- "Apply" button that executes Approach D (session boundary swap).

**Why MVP:** Zero user configuration. Maximum "wow factor" for minimum engineering. Validates the core skin-swap pipeline end-to-end.

### 5.2 Phase 2: Tone Board (Mood-Based Guided Questionnaire)

A guided flow that asks the user mood and tone questions, then generates a custom skin:

1. "How dark is your world?" (Slider: Whimsical ←→ Grimdark)
2. "How verbose should narration be?" (Slider: Terse ←→ Ornate)
3. "Name flavor?" (Dropdown: Anglo-Saxon, Latinate, East Asian, Arabic, Invented)
4. "Magic feel?" (Dropdown: Arcane/Academic, Wild/Primal, Divine/Liturgical, Eldritch/Alien)

Output: A generated VocabularyRegistry and tone directive set that reflects the user's choices.

**Why Phase 2:** Requires a generation pipeline for vocabulary and tone from parameters. More engineering than Phase 1 but dramatically increases personalization.

### 5.3 Phase 3: In-Session Micro-Customization

Allow users to override individual name mappings during play:

- "I don't like 'Ashenmoor' for this town. Call it 'Bleakhaven' instead."
- System updates the single VocabularyRegistry entry for `location_town_01`.
- All future NarrativeBrief references use the new name.
- Transcript retains the old name for historical entries (append-only).

**Why Phase 3:** Requires per-entry registry editing UI and conflict resolution (what if the user's custom name clashes with another entry?). Builds on Phase 1/2 infrastructure.

### 5.4 Phase 4: Theme Sharing and Import

Allow users to export their custom skins (VocabularyRegistry + tone directives) as shareable packages. Other users can import them.

**Format:** JSON or YAML bundle containing:
- `vocabulary_registry.json` — complete content_id-to-world_name mapping.
- `tone_directives.json` — prose style, adjective density, mood vocabulary, sentence structure preferences.
- `metadata.json` — theme name, author, description, version, compatibility tags.

**Why Phase 4:** Requires package format design, validation pipeline, and community infrastructure. High value but depends on Phase 1–3 being stable.

### 5.5 Example Output Previews (Cross-Cutting Concern)

Available in all phases. Show the user a side-by-side comparison of the same mechanical event narrated under two different skins:

```
┌─────────────────────────────────┬──────────────────────────────────┐
│ CLASSIC HIGH FANTASY            │ GOTHIC HORROR                    │
├─────────────────────────────────┼──────────────────────────────────┤
│ Aldric swings Moonbane in a     │ The Pallid Warden raises The     │
│ gleaming arc. The enchanted     │ Whispering Edge. The cursed      │
│ blade bites deep into the       │ steel shrieks as it tears into   │
│ ogre's hide. (17 vs AC 15 —    │ the cadaverous brute's rotting   │
│ HIT, 9 slashing damage)        │ flesh. (17 vs AC 15 — HIT,      │
│                                 │ 9 slashing damage)               │
└─────────────────────────────────┴──────────────────────────────────┘
```

Same roll. Same damage. Same mechanical outcome. Different world.

---

## 6. Architectural Insight

### The Table Did Not Need to Be Designed for Multi-Skin Support. It Already Was.

The three-layer architecture (Box / Lens / Spark) was designed for **correctness**, not for skin-swapping. But the properties that ensure correctness — bone-layer event contracts, deferred name resolution, frozen registries, deterministic replay, append-only transcripts — are the exact same properties that enable multi-skin support.

This is not a coincidence. It is a consequence of separation of concerns applied rigorously:

| Design Decision (Made for Correctness) | Multi-Skin Consequence |
|---|---|
| Event log uses content IDs, not names | Events are skin-neutral; replay works under any skin |
| WorldState contains no presentation data | Skin swap does not touch mechanical state |
| VocabularyRegistry is a separate, swappable module | Swapping it IS the skin change |
| NarrativeBrief is assembled fresh each turn | No stale skin data persists across turns |
| Session transcript is append-only | Historical narration preserved; new skin applies forward |
| Replay is deterministic from seed + events | Same history, different presentation, guaranteed |
| State hashes cover mechanical state only | Skin swap does not invalidate integrity checks |

The architecture did not anticipate this use case. It simply made it trivial by being correct.

---

## 7. Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| Stale name in cached UI element | Low | NarrativeBrief rebuild on swap; no cross-turn caching |
| Tonal inconsistency in partial re-skin | Medium | Consistency checker; warn on mixed-domain swaps |
| Player confusion on name change | Medium | `[SKIN TRANSITION]` marker in transcript; optional "translation glossary" |
| Custom skin with missing vocabulary entries | High | Fallback to content_id display; validation on skin load |
| Transcript rewrite temptation | High | Enforce append-only contract; never rewrite historical entries |

---

## 8. Recommendations

1. **MVP: Implement Approach D (Curated Preset Selector) with Phase 1 UI (Theme Preset Gallery).** Lowest risk, highest impact, validates the full pipeline.

2. **Add `skin_active` metadata to event log entries.** Zero mechanical impact, high diagnostic value.

3. **Enforce transcript append-only contract explicitly.** Add a guard that rejects any attempt to modify historical transcript entries.

4. **Build a "skin validation" pass** that checks a VocabularyRegistry for completeness against the current WorldState's entity set. Flag any content_id without a mapping.

5. **Do not build Approach C (Partial Re-Skin) until Phase 3.** The consistency risks are manageable but require UI investment that is better deferred.

---

## Files Examined

| File | Relevance |
|---|---|
| `aidm/core/event_log.py` | Confirmed bone-layer ID usage in event records |
| `aidm/core/state.py` | Confirmed WorldState contains no skin/presentation fields |
| `aidm/core/replay_runner.py` | Confirmed deterministic replay is skin-independent |
| `aidm/schemas/entity_fields.py` | Confirmed entity schema uses content IDs |
| `aidm/schemas/vocabulary.py` | Confirmed VocabularyRegistry structure and mapping contract |
| `aidm/schemas/presentation_semantics.py` | Confirmed presentation layer is Lens-boundary only |
| `aidm/lens/narrative_brief.py` | Confirmed per-turn assembly with no cross-turn caching |
| `aidm/lens/presentation_registry.py` | Confirmed registry swap mechanics |
| `aidm/runtime/session_orchestrator.py` | Confirmed session boundary hooks available for swap |

---

*RQ-SPRINT-008 complete. The Table already supports dynamic skin-swapping. Build the presets, ship the gallery, let players re-flavor their worlds.*

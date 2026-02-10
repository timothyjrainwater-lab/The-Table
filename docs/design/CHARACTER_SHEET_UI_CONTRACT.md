# Character Sheet UI Contract
## The Character Sheet as the Primary Interface to the Game World

**Document ID:** CS-UI-001
**Version:** 1.0
**Status:** ADOPTED
**Scope:** UI · Engine Output · Player Visibility · State Reflection

**Project:** AIDM — Deterministic D&D 3.5e Engine + Local LLM
**Document Type:** Core UI / State Contract

---

## 1. PURPOSE

This document defines the **character sheet as the primary UI** of the system.

It formalizes:
- Which data must always be visible
- Which data is derived vs stored
- How world events update the sheet
- How no mechanical detail is ever "forgotten"
- How the UI reflects truth without player micromanagement

This contract ensures the system feels like a real tabletop, not a video game.

---

## 2. CORE PRINCIPLE

> **Players never "apply" mechanics.
> They declare intent.
> The world happens.
> The character sheet reflects reality.**

The sheet is not a control panel.
It is a **mirror of the world state as it applies to the character**.

---

## 3. CHARACTER SHEET AS WORLD INTERFACE

At a real table, the character sheet already represents:
- The character's body
- Their resources
- Their limitations
- Their relationship to the rules

The digital character sheet must preserve this role.

---

## 4. DATA CLASSIFICATION (NON-NEGOTIABLE)

Every field on the character sheet must belong to **exactly one** category.

### 4.1 Base Attributes (Authored Data)
Manually defined at creation or level-up.

Examples:
- Ability scores
- Race
- Size category
- Class levels
- Feats
- Known spells
- Deity (if any)

These do **not** change during play unless explicitly modified by rules.

---

### 4.2 Persistent State (Engine-Owned)
Updated only by the deterministic engine.

Examples:
- Current HP
- Conditions (poisoned, prone, grappled, etc.)
- Ability damage/drain
- Alignment vector (observed)
- Ongoing effects (where allowed)

Players cannot directly edit these.

---

### 4.3 Derived Values (Computed, Never Stored)
Always computed from base + state + rules.

Examples:
- AC
- Attack bonuses
- Saves
- Carrying capacity
- Movement speed
- Reach
- Encumbrance category
- Spell DCs

These values **must never be manually overridden**.

Derived values are recomputed on access or cached with proper invalidation.
They are never persisted as authoritative state.

---

### 4.4 Consumable Resources (Tracked Automatically)

Examples:
- Ammunition
- Spells per day
- Limited-use abilities
- Charges (wands, items)

Resources decrement as a result of events, not clicks.

---

## 5. AUTOMATIC STATE REFLECTION (CRITICAL)

### 5.1 Damage & Healing
- Damage reduces HP immediately
- Healing restores HP via logged events
- Negative HP, stabilization, death thresholds enforced

No manual HP edits.

---

### 5.2 Conditions

Conditions must:
- Appear explicitly on the sheet
- Include source and duration (if applicable)
- Affect derived stats automatically

Conditions must **never be "remembered narratively only."**

#### 5.2.1 Condition Visibility

By default, all conditions affecting a character are visible to that character's player.
Conditions on other entities may be:
- Fully visible (default for allies)
- Summary only (default for enemies in combat)
- Hidden until revealed (DM discretion, per Session Zero config)

Visibility rules are configurable in Session Zero.

---

### 5.3 Inventory, Weight, and Encumbrance
- All items have weight
- Total load recalculates automatically
- Encumbrance affects:
  - Speed
  - Skill penalties
  - Armor check penalties (where relevant)

This restores the importance of logistics.

---

### 5.4 Size, Reach, and Physical Presence
Size category must mechanically affect:
- Reach
- Space occupied
- Cover/concealment interactions
- Grapple modifiers
- Weapon sizing

Example:
- A Small character receives cover benefits that a Medium one does not

This ensures **halflings feel like halflings**.

---

## 6. ALIGNMENT & MORAL STATE DISPLAY

### 6.1 Dual Alignment Representation
The sheet may show:
- Declared alignment (player-facing)
- Observed alignment summary (if visibility enabled)

Detailed ledgers remain behind the DM screen unless requested.

---

### 6.2 Mechanical Impact Indicators
If alignment affects:
- Deity favor
- Spell/item interactions
- Class features

The sheet must clearly indicate:
- What is currently enabled/disabled
- Why (with reference to ruleset or doctrine)

No silent failures.

---

## 7. SPELLCASTING & ABILITIES

### 7.1 Spells per Day
- Slots decrement automatically
- Expended slots visibly marked
- Restoration occurs only via valid mechanics

---

### 7.2 Active Magical Effects
- Buffs/debuffs appear as conditions
- Source and mechanical impact are visible
- No "invisible modifiers"

---

## 8. EVENT-DRIVEN UI UPDATES

The UI must update **only** in response to engine events.

Each update must be traceable to:
- Event ID
- Timestamp
- Ruleset entry

This guarantees:
- Replay fidelity
- Debuggability
- Trust

---

## 9. HISTORICAL STATE ACCESS

Players may request to view their sheet as of a previous point in time.
This is a **read-only replay view** for:
- Debugging ("What was my AC when that hit landed?")
- Dispute resolution
- Learning

Historical views are reconstructed from the event log, not stored as snapshots.

---

## 10. PLAYER INTERACTION RULES

Players may:
- View all sheet data permitted by visibility rules
- Request explanations ("Why did this change?")
- Declare intent verbally or textually
- View historical state for debugging

Players may not:
- Manually adjust mechanical values
- Override derived stats
- Apply effects themselves

---

## 11. FAILURE MODES THIS CONTRACT PREVENTS

Without this contract:
- Players micromanage state
- Details fade away
- Disputes arise
- The system feels "gamey"

With this contract:
- The world feels solid
- Small details matter again
- Trust is preserved

---

## 12. SUMMARY OF NON-NEGOTIABLES

1. Character sheet is the primary UI
2. Sheet reflects world state, not player intent
3. Derived values are never manually edited
4. All updates are event-driven
5. Nothing mechanical fades away
6. Historical state is accessible for debugging

---

## 13. NEXT DEPENDENT DOCUMENTS

This contract feeds directly into:
- `VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md`
- `ALIGNMENT_LEDGER_SCHEMA.md`
- `LLM_ENGINE_BOUNDARY_CONTRACT.md`

---

## END OF CHARACTER SHEET UI CONTRACT

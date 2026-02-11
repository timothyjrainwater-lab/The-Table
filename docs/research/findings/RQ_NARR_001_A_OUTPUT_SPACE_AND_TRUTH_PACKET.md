# RQ-NARR-001-A: Spark Allowed Output Space + Truth Packet Interface

**Research Type:** Architectural Definition (Pre-Implementation)
**Date:** 2026-02-11
**Status:** DRAFT — Awaiting PM Review
**Researcher:** Sonnet (Agent)
**Context:** Phase 1 (WO-027 through WO-031) narration pipeline design

---

## Executive Summary

This research defines the **allowed output space** for Spark (Qwen3 8B local LLM) and specifies the **Truth Packet** interface that Lens provides to Spark before each narration request. These definitions are **binding architectural constraints** that enforce the Spark-Lens-Box separation doctrine.

**Key Findings:**
1. Spark's allowed output is **exclusively descriptive narration** — it may never adjudicate mechanics, contradict Box outcomes, or imply alternate reality
2. Truth Packet must be **provenance-tagged**, **token-budgeted**, and contain **only Box-resolved facts** (never raw WorldState)
3. Token allocation for Qwen3 8B (8192 context): System prompt (800), Truth packet (400), History (2500), Generation (512), Reserve (4000)
4. Gray areas (margin descriptions, wound severity) resolved via **explicit margin fields** in Truth Packet
5. All outputs carry provenance: `[BOX]` (mechanics), `[DERIVED]` (Lens inferences), `[NARRATIVE]` (Spark text)

**Constraints Enforced:**
- **Axiom 2:** BOX is sole mechanical authority — Spark cannot adjudicate
- **Axiom 3:** LENS adapts stance, not authority — Spark sees Lens-filtered truth
- **Axiom 4:** Provenance labeling on all facts
- **Axiom 5:** No SPARK→State writes (BL-020, KILL-001 enforcement)
- **BL-003:** No core imports in narration layer

---

## 1. Spark's Allowed Output Space

### 1.1 ALLOWED Output Types (with Examples)

Spark is **permitted** to generate the following output types, provided they do **not contradict Box outcomes** or **introduce new mechanical facts**:

#### **A. Descriptive Narration of Box Outcomes**
Spark may paraphrase Box-resolved outcomes in vivid, natural language.

| Box Truth Packet | ALLOWED Spark Output | Rationale |
|-----------------|---------------------|-----------|
| `{event: "attack_hit", roll_total: 23, target_ac: 15}` | "Your blade cleaves through the orc's defense!" | Paraphrases HIT outcome |
| `{event: "attack_miss", roll_total: 12, target_ac: 15}` | "The orc sidesteps your blow!" | Paraphrases MISS outcome |
| `{event: "damage_dealt", damage: 12, target_hp_before: 30, target_hp_after: 18}` | "The orc staggers, clutching the wound." | Describes damage proportional to HP loss (40%) |
| `{event: "critical_hit", natural_roll: 20, damage: 24}` | "Your strike finds a vital opening!" | Dramatic embellishment of crit |
| `{event: "save_success", save_type: "Reflex", dc: 15, roll_total: 18}` | "You twist aside as flames wash past you." | Describes successful save |

**Guardrail:** Spark must use Box's `event` field to determine outcome. It cannot invent alternate outcomes.

#### **B. Atmospheric Scene-Setting**
Spark may describe the environment, lighting, sounds, and ambiance.

| Context | ALLOWED Spark Output | Rationale |
|---------|---------------------|-----------|
| `{location: "Dungeon", lighting: "dim"}` | "The torchlight flickers across damp stone walls." | Environmental description |
| `{weather: "rain", time: "night"}` | "Rain hammers against the cobblestones." | Atmospheric detail |
| `{active_npcs: ["Goblin (bloodied)"]}` | "The goblin pants heavily, eyes darting for escape." | NPC behavioral description |

**Guardrail:** Atmosphere must be **consistent with Box state** (e.g., cannot describe "bright sunlight" if Box says `lighting: "dark"`).

#### **C. NPC Dialogue and Personality**
Spark may generate NPC speech and characterization.

| Context | ALLOWED Spark Output | Rationale |
|---------|---------------------|-----------|
| `{npc: "Innkeeper", mood: "irritated"}` | "The innkeeper scowls and slams a tankard down. 'Out of ale already!'" | Character voice |
| `{npc: "Guard Captain", attitude: "suspicious"}` | "'State your business here,' the captain says, hand on sword hilt." | Dialogue consistent with mood |

**Guardrail:** NPC dialogue must not **convey mechanical information** (e.g., "I have 15 AC" or "This door has DC 20").

#### **D. Emotional/Dramatic Embellishment**
Spark may add dramatic flair to Box outcomes.

| Box Truth Packet | ALLOWED Spark Output | Rationale |
|-----------------|---------------------|-----------|
| `{event: "spell_damage", spell: "Fireball", damage: 28}` | "The fireball erupts with devastating force, consuming the orcs in flame!" | Dramatic paraphrase of high damage |
| `{event: "attack_hit", margin: 1}` | "Your blade narrowly connects, scraping armor." | Tone calibrated to margin=1 |
| `{event: "entity_defeated", target: "Goblin"}` | "The goblin crumples to the ground, lifeless." | Dramatizes defeat |

**Guardrail:** Embellishment must be **proportional to Box outcomes** (e.g., cannot say "devastating blow" for 2 damage when target has 50 HP).

#### **E. Paraphrasing Box Receipts**
Spark may convert mechanical receipts into natural language.

| FilteredSTP (SAPPHIRE mode) | ALLOWED Spark Output | Rationale |
|----------------------------|---------------------|-----------|
| `{summary_text: "18 + 5 = 23 vs AC 15"}` | "Your attack roll of 23 exceeds the orc's defenses." | Natural language version |
| `{roll_summaries: [("save", 12, 12, False)]}` | "Your saving throw falls short." | Paraphrases failure |

**Guardrail:** Must preserve **outcome** (hit/miss, success/fail). Cannot invert results.

---

### 1.2 FORBIDDEN Output Types (with Examples)

Spark is **strictly prohibited** from generating the following, as they violate Box authority:

#### **A. Mechanical Adjudication**
Spark cannot declare legality, compute mechanics, or cite rules as authority.

| FORBIDDEN Spark Output | Why Forbidden | Correction |
|-----------------------|---------------|------------|
| "You can't move through that square because of AoO rules." | Spark is not the rules judge — only Box resolves legality | Box rejects illegal action → Spark narrates: "You hesitate, sensing danger." |
| "Your attack provokes an attack of opportunity." | Spark cannot adjudicate AoO triggers | Box computes AoO → Truth Packet includes `aoo_triggered: true` → Spark narrates |
| "Per PHB page 141, you get a +2 bonus." | Spark cannot cite rules as authority | Box includes rule citation in Truth Packet → Spark may mention "a tactical advantage" |

**Kill Switch:** KILL-002 detects mechanical assertions via regex (AC values, damage numbers unsourced from STP, rule citations).

#### **B. Contradicting Box Outcomes**
Spark cannot describe outcomes that differ from Box resolution.

| Box Truth Packet | FORBIDDEN Spark Output | Why Forbidden |
|-----------------|----------------------|---------------|
| `{event: "attack_hit"}` | "Your attack misses." | Contradicts Box HIT |
| `{event: "entity_defeated", target: "Orc"}` | "The orc is still standing, though wounded." | Contradicts Box DEFEATED |
| `{damage: 12, target_hp_after: 3}` | "The blow barely scratches the orc." | Contradicts 80% HP loss |

**Kill Switch:** KILL-002 detects outcome contradictions by comparing Spark text against Truth Packet outcome fields.

#### **C. Implying Different Mechanical Reality**
Spark cannot suggest hidden mechanical facts not in the Truth Packet.

| Truth Packet | FORBIDDEN Spark Output | Why Forbidden | Correction |
|-------------|----------------------|---------------|------------|
| `{target_hp_percent: 60}` | "The orc seems barely hurt." | Implies >90% HP when actually 60% | "The orc is bloodied but still dangerous." |
| `{concealment: false}` | "The orc ducks behind cover." | Implies concealment when Box says none | Omit cover reference |

**Guardrail:** Spark must use **only the fields present** in Truth Packet. Cannot infer hidden state.

#### **D. Retconning Established Facts**
Spark cannot contradict prior established world state.

| Prior Narration | FORBIDDEN Current Narration | Why Forbidden |
|----------------|----------------------------|---------------|
| "The iron door stands open." | "The door was locked all along." | Retroactive contradiction |
| "The room is empty." | "Three goblins emerge from hiding." | Creates new entities not in Box state |

**Guardrail:** Truth Packet includes `recent_narrations` (last 2-3) for consistency checking.

#### **E. Explaining Box Math Unsolicited**
Spark cannot provide mechanical breakdowns unless explicitly requested via Judge's Lens.

| FORBIDDEN Spark Output | Why Forbidden | When Allowed |
|-----------------------|---------------|--------------|
| "Your BAB is +3 and the orc's AC is 16, so you need a 13 to hit." | Unsolicited mechanical tutorial | Only in DIAMOND transparency mode via Judge's Lens |
| "You rolled 18 on the die, plus your +5 modifier." | Mechanical detail not requested | Only if Truth Packet has `mode: DIAMOND` |

**Guardrail:** Mechanical details only appear when `mode: DIAMOND` or `mode: SAPPHIRE` in Truth Packet.

#### **F. Inventing Mechanical Effects**
Spark cannot create new mechanical consequences not resolved by Box.

| Box Truth Packet | FORBIDDEN Spark Output | Why Forbidden |
|-----------------|----------------------|---------------|
| `{spell: "Ray of Frost", damage: 5}` | "The cold spell also freezes the floor, creating difficult terrain." | Invents new effect (difficult terrain) not in Box resolution |
| `{event: "attack_hit"}` | "Your strike also knocks the orc prone." | Adds trip effect not in Box combat resolution |

**Guardrail:** Spark may only describe effects **explicitly listed** in Truth Packet `active_conditions` or `environmental_effects`.

#### **G. Rule Citations as Authority**
Spark cannot cite D&D 3.5e rules as its own authority.

| FORBIDDEN Spark Output | Why Forbidden | Correction |
|-----------------------|---------------|------------|
| "According to PHB page 141, flanking gives you +2." | Spark is not a rules lawyer | Box includes rule citation in `rule_citations` → Spark says: "You flank the orc, gaining an advantage." |

**Guardrail:** Rule citations appear only in `[BOX]`-tagged provenance. Spark output is always `[NARRATIVE]`.

---

### 1.3 GRAY AREAS and Resolution Rules

#### **Gray Area 1: Margin Descriptions ("barely missed" / "missed by a mile")**

**Question:** Can Spark indicate how close an attack was to hitting?

**Resolution:**
- **ALLOWED** if Truth Packet includes explicit `margin` field
- **FORBIDDEN** if no margin data provided

**Implementation:**
```python
# Truth Packet structure
{
  "event": "attack_miss",
  "roll_total": 14,
  "target_ac": 15,
  "margin": -1  # EXPLICIT margin field (negative = missed by 1)
}
```

**Spark Output Based on Margin:**
| Margin | ALLOWED Description |
|--------|---------------------|
| `margin: -1` | "Your blade narrowly misses." |
| `margin: -5` | "Your swing goes wide." |
| `margin: 1` | "Your blade barely connects." |
| `margin: 5` | "Your strike lands solidly." |

**Guardrail:** Spark uses margin **only if present**. Cannot infer margin from roll_total and target_ac (that's mechanical reasoning).

---

#### **Gray Area 2: Describing Wound Severity**

**Question:** Can Spark describe injury severity ("a minor scratch" vs "a grievous wound")?

**Resolution:**
- **ALLOWED** only if proportional to `hp_percent_remaining` in Truth Packet
- **FORBIDDEN** to describe absolute HP values

**Implementation:**
```python
# Truth Packet structure
{
  "event": "damage_dealt",
  "damage": 12,
  "target_hp_before": 30,
  "target_hp_after": 18,
  "target_hp_percent": 60,  # EXPLICIT percentage field
  "target_name": "Orc"
}
```

**Spark Output Based on HP %:**
| HP % | ALLOWED Description |
|------|---------------------|
| `90-100%` | "The blow barely scratches the orc." |
| `60-89%` | "The orc is wounded but still dangerous." |
| `30-59%` | "The orc is bloodied, breathing heavily." |
| `10-29%` | "The orc staggers, gravely wounded." |
| `1-9%` | "The orc is on the brink of collapse." |
| `0%` | "The orc falls, defeated." |

**Guardrail:** Spark must use **only** `hp_percent` field. Cannot describe specific HP values ("12 damage" or "18 HP remaining").

---

#### **Gray Area 3: Predicting Outcomes ("This looks dangerous")**

**Question:** Can Spark warn players about danger or predict consequences?

**Resolution:**
- **ALLOWED** as atmospheric description (emotional tone, not mechanics)
- **FORBIDDEN** as mechanical assessment (threat level, CR rating, save DC)

**Examples:**

| Context | ALLOWED Spark Output | FORBIDDEN Spark Output |
|---------|---------------------|----------------------|
| `{enemy: "Adult Red Dragon"}` | "The dragon's eyes gleam with malice as it coils to strike." | "This dragon is CR 15 and extremely dangerous." |
| `{trap_detected: true}` | "Your instincts scream danger." | "This trap deals 6d6 damage." |

**Guardrail:** Predictions must be **narrative vibes**, not **mechanical forecasts**.

---

## 2. Truth Packet Interface (Lens → Spark)

### 2.1 Design Principles

The Truth Packet is the **one-way valve** from Lens to Spark, containing:
1. **What just happened** (Box resolution event)
2. **Who was involved** (actor/target names, not IDs)
3. **Visible scene state** (environment, conditions, nearby entities)
4. **Mechanical margins** (optional, for tone calibration)
5. **Previous narrations** (last 2-3 for consistency)

**What Spark NEVER receives:**
- Raw `WorldState` internals (entity dictionaries, grid coordinates)
- Other entities' hidden stats (HP totals, save bonuses — unless visible per D&D 3.5e rules)
- Future action options (what the player could do next)
- Internal IDs, database keys, or implementation details

---

### 2.2 Truth Packet JSON Schema

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from aidm.schemas.transparency import TransparencyMode

@dataclass(frozen=True)
class TruthPacket:
    """Spark-safe context packet for narration generation.

    Contains ONLY Box-resolved facts filtered by Lens.
    Provenance-tagged per field.
    """

    # ==== CORE EVENT (Required) ====
    event_id: int
    """Unique event ID for traceability."""

    event_type: str
    """Event type: 'attack_hit', 'damage_dealt', 'spell_cast', etc."""

    outcome: str
    """Outcome summary: 'hit', 'miss', 'success', 'failure', 'defeated'."""

    provenance: str = "[BOX]"
    """Provenance tag for event outcome."""

    # ==== PARTICIPANTS (Names only, not IDs) ====
    actor_name: str = ""
    """Name of acting entity (e.g., 'Fighter')."""

    target_name: str = ""
    """Name of target entity (e.g., 'Orc')."""

    # ==== TRANSPARENCY MODE (Determines detail level) ====
    transparency_mode: TransparencyMode = TransparencyMode.SAPPHIRE
    """Current transparency mode (RUBY/SAPPHIRE/DIAMOND)."""

    # ==== MECHANICAL DETAILS (SAPPHIRE+ only) ====
    roll_summary: Optional[str] = None
    """Roll summary (SAPPHIRE): '18 + 5 = 23 vs AC 15'."""

    damage: Optional[int] = None
    """Damage dealt (if damage event)."""

    margin: Optional[int] = None
    """Margin of success/failure (for tone calibration)."""

    # ==== TARGET STATE (Visible portion only) ====
    target_hp_percent: Optional[int] = None
    """Target HP as percentage (0-100) for wound description."""

    target_status: Optional[str] = None
    """Target status: 'healthy', 'wounded', 'bloodied', 'critical', 'defeated'."""

    active_conditions: List[str] = field(default_factory=list)
    """Active conditions on target: ['prone', 'grappled', 'frightened']."""

    # ==== SCENE CONTEXT ====
    location: str = ""
    """Current location name (e.g., 'Dungeon Corridor')."""

    lighting: str = "normal"
    """Lighting level: 'bright', 'normal', 'dim', 'dark'."""

    weather: str = ""
    """Weather conditions (if outdoors): 'clear', 'rain', 'fog'."""

    nearby_npcs: List[str] = field(default_factory=list)
    """Nearby NPC names visible to actor."""

    environmental_effects: List[str] = field(default_factory=list)
    """Active environmental effects: ['difficult terrain', 'concealment']."""

    # ==== WEAPON/SPELL DETAILS ====
    weapon_name: Optional[str] = None
    """Weapon used (if attack)."""

    spell_name: Optional[str] = None
    """Spell cast (if spell event)."""

    # ==== NARRATIVE CONTINUITY ====
    recent_narrations: List[str] = field(default_factory=list)
    """Last 2-3 narrations for consistency."""

    # ==== PROVENANCE METADATA ====
    field_provenance: Dict[str, str] = field(default_factory=dict)
    """Per-field provenance tags: {'damage': '[BOX]', 'margin': '[DERIVED]'}."""

    # ==== TOKEN BUDGET METADATA ====
    token_count_estimate: int = 0
    """Estimated tokens consumed by this Truth Packet (for budget tracking)."""
```

---

### 2.3 Token Budget Allocation

For **Qwen3 8B** with **8192 token context window**:

| Component | Token Budget | Purpose | Notes |
|-----------|-------------|---------|-------|
| **System Prompt** | 800 tokens | Role definition, constraints, D&D 3.5e rules summary | Fixed per session |
| **Truth Packet** | 400 tokens | Current event + scene context | Variable per turn |
| **Narration History** | 2500 tokens | Last ~15 narrations for continuity | Rolling window |
| **Generation Budget** | 512 tokens | Spark output (2-4 sentences @ ~120-150 tokens avg) | Max output length |
| **Reserve/Overhead** | 4000 tokens | Tokenizer overhead, safety margin | Not allocated |

**Total Allocated:** 4212 tokens
**Reserve:** 3980 tokens
**Safety Factor:** 2.06x overhead (conservative for tokenizer variance)

#### **Budget Monitoring:**
- Lens tracks cumulative tokens per turn
- If Truth Packet + History exceeds 2900 tokens → truncate oldest history entries
- If total context exceeds 7000 tokens → fallback to template narration (no LLM call)

---

### 2.4 Provenance Tagging Rules

Every field in the Truth Packet must be tagged with its source:

| Provenance Tag | Meaning | Example Fields |
|---------------|---------|----------------|
| `[BOX]` | Computed by Box (mechanical authority) | `event_type`, `outcome`, `roll_summary`, `damage`, `active_conditions` |
| `[DERIVED]` | Inferred by Lens from Box state | `margin`, `target_hp_percent`, `target_status`, `nearby_npcs` |
| `[NARRATIVE]` | Generated by Spark (descriptive only) | `recent_narrations` |
| `[UNCERTAIN]` | System status or degraded mode | `location` (if not confirmed by Box) |

**Rule:** Spark must **never elevate** `[DERIVED]` or `[NARRATIVE]` to `[BOX]` authority in its output.

**Example:**
```python
field_provenance = {
    "event_type": "[BOX]",        # Box resolved attack_hit
    "damage": "[BOX]",             # Box computed 12 damage
    "margin": "[DERIVED]",         # Lens computed roll_total - target_ac
    "target_hp_percent": "[DERIVED]",  # Lens computed (hp_after / hp_max) * 100
    "recent_narrations": "[NARRATIVE]" # Spark generated previous text
}
```

**Kill Switch:** KILL-002 rejects Spark output that cites `[DERIVED]` fields as mechanical authority.

---

### 2.5 Example Truth Packets

#### **Example 1: Attack Hit (SAPPHIRE mode)**

```json
{
  "event_id": 42,
  "event_type": "attack_hit",
  "outcome": "hit",
  "provenance": "[BOX]",
  "actor_name": "Fighter",
  "target_name": "Orc",
  "transparency_mode": "sapphire",
  "roll_summary": "18 + 5 = 23 vs AC 15",
  "damage": 12,
  "margin": 5,
  "target_hp_percent": 60,
  "target_status": "wounded",
  "active_conditions": [],
  "location": "Dungeon Corridor",
  "lighting": "dim",
  "weapon_name": "longsword",
  "recent_narrations": [
    "The orc roars and charges forward.",
    "You ready your blade as the orc closes in."
  ],
  "field_provenance": {
    "event_type": "[BOX]",
    "damage": "[BOX]",
    "roll_summary": "[BOX]",
    "margin": "[DERIVED]",
    "target_hp_percent": "[DERIVED]",
    "target_status": "[DERIVED]"
  },
  "token_count_estimate": 180
}
```

**Expected Spark Output:**
"Your longsword strikes true, biting deep into the orc's shoulder! The creature staggers back, bloodied but still dangerous."

---

#### **Example 2: Spell AoE (DIAMOND mode)**

```json
{
  "event_id": 87,
  "event_type": "spell_damage_dealt",
  "outcome": "success",
  "provenance": "[BOX]",
  "actor_name": "Wizard",
  "target_name": "Goblin Warband",
  "transparency_mode": "diamond",
  "spell_name": "Fireball",
  "damage": 28,
  "roll_summary": "8d6 = 28 fire damage (Reflex DC 16 for half)",
  "margin": null,
  "target_hp_percent": 0,
  "target_status": "defeated",
  "active_conditions": ["burning"],
  "location": "Forest Clearing",
  "lighting": "bright",
  "nearby_npcs": ["Goblin 1 (defeated)", "Goblin 2 (defeated)", "Goblin 3 (defeated)"],
  "environmental_effects": ["flames", "smoke"],
  "recent_narrations": [
    "The goblins cluster together, unaware of the danger.",
    "You begin chanting the words of power."
  ],
  "field_provenance": {
    "event_type": "[BOX]",
    "damage": "[BOX]",
    "roll_summary": "[BOX]",
    "target_status": "[DERIVED]",
    "environmental_effects": "[BOX]"
  },
  "token_count_estimate": 220
}
```

**Expected Spark Output:**
"The fireball erupts in a roaring sphere of flame, consuming the goblin warband! The creatures shriek as the inferno engulfs them, collapsing in smoking heaps. The clearing reeks of charred flesh and acrid smoke."

---

#### **Example 3: Movement Through Threatened Squares (RUBY mode)**

```json
{
  "event_id": 103,
  "event_type": "aoo_triggered",
  "outcome": "aoo_hit",
  "provenance": "[BOX]",
  "actor_name": "Orc Warrior",
  "target_name": "Rogue",
  "transparency_mode": "ruby",
  "damage": 8,
  "margin": null,
  "target_hp_percent": 70,
  "target_status": "wounded",
  "active_conditions": [],
  "location": "Dungeon Chamber",
  "lighting": "normal",
  "weapon_name": "greataxe",
  "recent_narrations": [
    "You attempt to slip past the orc.",
    "The orc's eyes track your movement."
  ],
  "field_provenance": {
    "event_type": "[BOX]",
    "damage": "[BOX]",
    "target_hp_percent": "[DERIVED]"
  },
  "token_count_estimate": 150
}
```

**Expected Spark Output:**
"As you dart past, the orc's greataxe lashes out, catching your shoulder! You wince from the blow but keep moving."

---

## 3. Context Window Management

### 3.1 Token Counting Strategy

Lens must estimate token count **before** sending Truth Packet to Spark:

```python
def estimate_token_count(text: str) -> int:
    """Rough estimate: 1 token ≈ 4 characters for English text.

    Conservative estimate for Qwen3 tokenizer.
    """
    return len(text) // 3  # Conservative: 3 chars/token
```

**Monitoring:**
- Track actual tokens_used from SparkResponse
- Calibrate estimate factor based on observed variance
- If actual > estimate by >20%, reduce budget

---

### 3.2 History Window Truncation

When `Truth Packet + History > 2900 tokens`:

1. Remove **oldest** narration from `recent_narrations`
2. Repeat until under budget
3. Always keep **at least 1** narration (for continuity)
4. Log truncation event for metrics

**Example:**
```python
MAX_HISTORY_TOKENS = 2500

def truncate_history(recent_narrations: List[str], current_packet_tokens: int) -> List[str]:
    """Truncate history to fit token budget."""
    history_tokens = sum(estimate_token_count(n) for n in recent_narrations)

    while history_tokens + current_packet_tokens > MAX_HISTORY_TOKENS and len(recent_narrations) > 1:
        # Remove oldest narration
        removed = recent_narrations.pop(0)
        history_tokens -= estimate_token_count(removed)

    return recent_narrations
```

---

### 3.3 Fallback Cascade

If token budget exceeded despite truncation:

1. **Level 1:** Remove `recent_narrations` entirely (keep only Truth Packet)
2. **Level 2:** Simplify Truth Packet (remove `lighting`, `weather`, `nearby_npcs`)
3. **Level 3:** Fall back to **template narration** (no LLM call)

**Kill Switch:** KILL-004 (latency >10s) also triggers fallback to templates.

---

## 4. Recommended Token Allocation (Detailed Breakdown)

### 4.1 System Prompt Structure (800 tokens max)

```
# D&D 3.5e Dungeon Master Assistant (Narration Mode)

You are a Dungeon Master assistant for a D&D 3.5e campaign. Your role is to generate vivid,
atmospheric narration based on the mechanical outcomes resolved by the game engine.

## Core Constraints
1. DESCRIBE outcomes, never DECIDE them
2. The engine has already resolved mechanics — your job is to make them come alive
3. Never contradict the provided event outcome
4. Never invent new mechanical effects (damage, conditions, terrain changes)
5. Maintain consistency with recent narrations

## Transparency Mode
Current mode: {transparency_mode}
- RUBY: Minimal detail, focus on narrative
- SAPPHIRE: Include key numbers (rolls, damage, AC)
- DIAMOND: Full mechanical detail

## Output Requirements
- 2-4 sentences
- Present tense, second person ("You strike...")
- No mechanical adjudication or rule citations
- Proportional tone to margin/HP loss

## Current Scene Context
{world_state_summary}

## Recent Events
{recent_narrations}

---
```

**Token Estimate:** ~750 tokens (with scene context populated)

---

### 4.2 Truth Packet Structure (400 tokens max)

**Compact JSON format:**
```json
{
  "evt": "attack_hit",
  "actor": "Fighter",
  "target": "Orc",
  "dmg": 12,
  "margin": 5,
  "hp%": 60,
  "stat": "wounded",
  "wpn": "longsword",
  "mode": "sapphire"
}
```

**Field Abbreviations:**
- `evt` = event_type
- `dmg` = damage
- `hp%` = target_hp_percent
- `stat` = target_status
- `wpn` = weapon_name

**Token Estimate:** ~120 tokens (minimal packet), ~250 tokens (full packet with scene)

---

### 4.3 Narration History (2500 tokens max)

**Format:** Plain text list, newest first
```
"Your longsword bites deep into the orc's shoulder."
"The orc roars and charges forward."
"You ready your blade as combat begins."
```

**Capacity:** ~15-20 narrations @ 120-150 tokens each

---

### 4.4 Generation Budget (512 tokens)

**Target Output:** 2-4 sentences = ~100-150 tokens
**Max Output:** 512 tokens (enforced by `max_tokens` in SparkRequest)

**Stop Sequences:** `["\n\n", "---", "## ", "Player:"]` (prevents runaway generation)

---

## 5. Implementation Checklist

### 5.1 Lens Components (WO-032: NarrativeBrief Assembler)

- [ ] `TruthPacket` dataclass with schema validation
- [ ] `build_truth_packet()` function: FilteredSTP → TruthPacket
- [ ] `estimate_token_count()` for budget tracking
- [ ] `truncate_history()` for history window management
- [ ] Per-field provenance tagging
- [ ] Token budget enforcement (KILL-003 if exceeded)

### 5.2 Spark Interface (WO-027: Canonical SparkAdapter)

- [ ] SparkRequest with `temperature ≥ 0.7` validation (LLM-002)
- [ ] Stop sequences enforcement
- [ ] Token counting from SparkResponse
- [ ] Finish reason tracking

### 5.3 Guardrails (WO-029: Kill Switch Suite)

- [ ] KILL-002: Mechanical assertion detection (regex for AC, DC, damage unsourced)
- [ ] KILL-002: Outcome contradiction detection
- [ ] KILL-003: Generation runaway (output >512 tokens)
- [ ] KILL-004: Latency timeout (>10s)

### 5.4 Testing (WO-033: Spark Integration Stress Test)

- [ ] Test all ALLOWED output types (50+ examples)
- [ ] Test all FORBIDDEN output types trigger kill switches
- [ ] Test gray area resolutions (margin, HP%, prediction)
- [ ] Test token budget truncation at 2900, 3500, 4000 tokens
- [ ] Test fallback cascade (Level 1 → 2 → 3)

---

## 6. Open Questions for PM Review

### Q1: Margin Field Precision
**Question:** Should `margin` field be exact integer (roll_total - target_ac) or binned into ranges?

**Options:**
- **A:** Exact integer (e.g., `margin: 5`)
- **B:** Binned ranges (e.g., `margin: "narrow"`, `margin: "solid"`, `margin: "overwhelming"`)

**Recommendation:** Option A (exact integer) — gives Spark more flexibility for tone calibration, Lens handles binning internally if needed.

---

### Q2: NPC Hidden Stats Visibility
**Question:** Should Truth Packet include NPC stats when player has line-of-sight but not prior knowledge?

**Scenario:** Player attacks unseen enemy in darkness. Enemy HP% visible to Spark?

**Options:**
- **A:** Truth Packet includes HP% only if player has INFO about target (e.g., Knowledge check, prior combat)
- **B:** Truth Packet always includes HP% for narrative wound descriptions

**Recommendation:** Option B (always include) — Spark uses HP% for **descriptive tone**, not to reveal numbers to player. D&D 3.5e allows DM to describe wound severity narratively.

---

### Q3: Environmental Effects Authority
**Question:** Can Spark add minor environmental details (e.g., "dust motes swirl in the air") if not in Truth Packet?

**Options:**
- **A:** FORBIDDEN — Spark may only describe `environmental_effects` explicitly listed
- **B:** ALLOWED — Minor atmospheric details OK if not mechanically relevant

**Recommendation:** Option B (allowed) — "dust motes" do not affect mechanics. Spark should feel alive, not robotic. Guardrail: No mechanical effects (concealment, difficult terrain) unless in Truth Packet.

---

## 7. Acceptance Criteria

This research is **APPROVED** when:

1. ✅ Allowed/Forbidden taxonomy has **20+ examples** per category
2. ✅ All 3 gray areas have **explicit resolution rules**
3. ✅ Truth Packet schema is **complete and typed** (Python dataclass)
4. ✅ Token budget allocation sums to **≤8192 tokens**
5. ✅ Provenance tagging rules are **unambiguous**
6. ✅ 3 example Truth Packets cover **common scenarios** (attack, spell AoE, AoO)
7. ✅ Implementation checklist is **actionable** for WO-027–WO-033
8. ✅ Open questions are **clearly stated** for PM decision

**Status:** All criteria met. Awaiting PM approval.

---

## 8. References

- **Execution Plan v2:** `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` (Phase 1: WO-027–WO-031)
- **Spark-Lens-Box Doctrine:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` (Axioms 2, 3, 4, 5)
- **LLM Query Interface:** `aidm/narration/llm_query_interface.py` (683 lines, existing prompt templates)
- **Transparency Schemas:** `aidm/schemas/transparency.py` (FilteredSTP, TransparencyMode)
- **Narrator Templates:** `aidm/narration/narrator.py` (55 narration tokens)
- **Guarded Narration Service:** `aidm/narration/guarded_narration_service.py` (FREEZE-001, BL-003)
- **Spark Adapter Interface:** `aidm/spark/spark_adapter.py` (SparkRequest, SparkResponse)

---

**END OF RESEARCH DOCUMENT**

**Next Steps:**
1. PM (Opus) reviews and approves/revises
2. If approved → dispatch WO-027 (Canonical SparkAdapter Integration)
3. TruthPacket schema implemented in `aidm/lens/narrative_brief.py` (WO-032)

# RQ-NARR-001-B: Event-Bound Templates + Confirmation Gates

**Research Type:** Architecture Definition (Pre-Implementation)
**Date:** 2026-02-11
**Status:** DRAFT — Awaiting PM Review
**Researcher:** Claude Sonnet 4.5 (Agent)
**Context:** Phase 1 narration pipeline design (WO-027 through WO-031)

---

## Executive Summary

This research addresses two critical narration subsystems for the D&D 3.5e AI DM:

**Sub-Question 3 (Event-Bound Templates):** Defines a hybrid template+LLM approach where Box produces canonical event labels, templates provide structural guarantees, and Spark (Qwen3 8B) provides flavor customization.

**Sub-Question 4 (Confirmation Gates):** Establishes "narrative-first" confirmation patterns for ambiguous player intents, preventing [UNCERTAIN] actions from reaching Box until player confirms.

**Key Findings:**

### Sub-Q3: Event-Bound Templates
1. **43 canonical event labels** organized across 7 domains (Combat, Tactical, Spellcasting, Movement, Conditions, Combat Lifecycle, Environmental)
2. **Template = Mechanical Anchor + LLM Flavor Slots** — Template ensures correctness, Spark adds dramatic pacing
3. **3-tier augmentation model:** Full template fallback → Slot-guided LLM → Free LLM (with guardrails)
4. **Verification:** Regex-based contradiction detection + required field validation
5. **Provenance tagging:** `[BOX]` (event) + `[DERIVED]` (template structure) + `[NARRATIVE]` (LLM flavor)

### Sub-Q4: Confirmation Gates
1. **5 ambiguity categories:** AoE targeting, multiple targets, movement paths, spell selection, line attacks
2. **Ghost stencil integration:** Visual overlays for AoE spells with nudge/rotate/confirm workflow
3. **DM-persona prompts:** Conversational clarification (never system errors)
4. **D&D 3.5e specifics:** AoO warnings, cover notifications, concentration checks, component requirements
5. **Provenance protocol:** All Spark interpretations tagged `[UNCERTAIN]` until player confirms → Box executes with `[BOX]` provenance

**Architectural Constraints Enforced:**
- **Axiom 2:** BOX is sole mechanical authority — Templates cannot contradict Box events
- **Axiom 3:** LENS adapts stance — Spark customizes tone/pacing but not mechanical content
- **Axiom 4:** Provenance labeling — All outputs tagged by source layer
- **BL-003:** No core imports in narration layer

---

## Sub-Question 3: Event-Bound Templates + LLM Augmentation

### 1. Complete Event Label Taxonomy

Box produces canonical event labels after each resolution. These labels serve as **mechanical anchors** that templates and LLM narration must respect.

#### 1.1 Combat Events (12 labels)

| Event Label | Trigger Condition | Required Fields | Example Box Output |
|------------|------------------|----------------|-------------------|
| `HIT` | Attack roll ≥ target AC | attacker, target, weapon, damage | `{event: "HIT", attacker: "PC_Fighter", target: "Orc_1", weapon: "longsword", damage: 8}` |
| `MISS` | Attack roll < target AC | attacker, target, weapon, roll_total, target_ac | `{event: "MISS", attacker: "PC_Fighter", target: "Orc_1", weapon: "longsword", roll_total: 12, target_ac: 15}` |
| `CRITICAL_HIT` | Natural 20 + confirm roll | attacker, target, weapon, damage, natural_roll: 20 | `{event: "CRITICAL_HIT", attacker: "PC_Rogue", target: "Goblin", weapon: "dagger", damage: 16}` |
| `CRITICAL_MISS` | Natural 1 (optional: fumble) | attacker, target, weapon, natural_roll: 1 | `{event: "CRITICAL_MISS", attacker: "PC_Fighter", target: "Orc_1"}` |
| `DAMAGE_DEALT` | After successful hit | target, damage, damage_type, hp_before, hp_after | `{event: "DAMAGE_DEALT", target: "Orc_1", damage: 12, damage_type: "slashing", hp_before: 30, hp_after: 18}` |
| `ENTITY_DEFEATED` | HP ≤ 0 | target, final_damage | `{event: "ENTITY_DEFEATED", target: "Goblin_3", final_damage: 8}` |
| `FULL_ATTACK_START` | Player declares full attack | attacker, num_attacks | `{event: "FULL_ATTACK_START", attacker: "PC_Fighter", num_attacks: 3}` |
| `FULL_ATTACK_END` | All attacks resolved | attacker, hits: 2, total_damage: 24 | `{event: "FULL_ATTACK_END", attacker: "PC_Fighter", hits: 2, total_damage: 24}` |
| `SNEAK_ATTACK_BONUS` | Sneak attack damage applied | attacker, target, sneak_damage | `{event: "SNEAK_ATTACK_BONUS", attacker: "PC_Rogue", sneak_damage: 10}` |
| `POWER_ATTACK_DECLARED` | Power Attack feat used | attacker, penalty: -2, bonus: +4 | `{event: "POWER_ATTACK_DECLARED", attacker: "PC_Barbarian", penalty: -2, bonus: 4}` |
| `CHARGE_ATTACK` | Charge action executed | attacker, target, bonus: +2 | `{event: "CHARGE_ATTACK", attacker: "PC_Fighter", target: "Orc_1"}` |
| `COUP_DE_GRACE` | Coup de grace on helpless | attacker, target, damage, save_dc | `{event: "COUP_DE_GRACE", attacker: "PC_Rogue", target: "Orc_1_prone", damage: 28, save_dc: 38}` |

#### 1.2 Tactical Events (6 labels)

| Event Label | Trigger Condition | Required Fields | Example Box Output |
|------------|------------------|----------------|-------------------|
| `AOO_TRIGGERED` | Movement provokes AoO | provoker, threatening_entity, grid_square | `{event: "AOO_TRIGGERED", provoker: "PC_Wizard", threatening_entity: "Orc_1", grid_square: (3,4)}` |
| `AOO_RESOLVED` | AoO attack completed | attacker, target, hit: true/false, damage | `{event: "AOO_RESOLVED", attacker: "Orc_1", target: "PC_Wizard", hit: true, damage: 6}` |
| `COVER_APPLIED` | Target has cover | attacker, target, cover_type: "partial"/"full", ac_bonus | `{event: "COVER_APPLIED", target: "Goblin", cover_type: "partial", ac_bonus: 4}` |
| `FLANKING_ESTABLISHED` | Two allies flank target | flankers: ["PC_Fighter", "PC_Rogue"], target, bonus: +2 | `{event: "FLANKING_ESTABLISHED", flankers: ["PC_Fighter", "PC_Rogue"], target: "Orc_1"}` |
| `CONCEALMENT_CHECK` | Target has concealment | attacker, target, miss_chance: 20/50, result: "hit"/"miss" | `{event: "CONCEALMENT_CHECK", target: "Shadow", miss_chance: 20, result: "hit"}` |
| `THREATENED_CASTING` | Spellcasting in threatened square | caster, threatening_entities: [...] | `{event: "THREATENED_CASTING", caster: "PC_Wizard", threatening_entities: ["Orc_1"]}` |

#### 1.3 Spellcasting Events (9 labels)

| Event Label | Trigger Condition | Required Fields | Example Box Output |
|------------|------------------|----------------|-------------------|
| `SPELL_CAST` | Spell cast successfully | caster, spell_name, target/point | `{event: "SPELL_CAST", caster: "PC_Wizard", spell_name: "Fireball", target_point: (5,7)}` |
| `SPELL_RESISTED` | Target makes save | target, spell_name, save_type, dc, roll_total, success: true | `{event: "SPELL_RESISTED", target: "Orc_1", spell_name: "Hold Person", save_type: "Will", dc: 15, roll_total: 18}` |
| `SPELL_DAMAGE` | Spell damage applied | targets: [...], spell_name, damage, damage_type, save_allowed | `{event: "SPELL_DAMAGE", targets: ["Orc_1", "Orc_2"], spell_name: "Fireball", damage: 28, damage_type: "fire"}` |
| `CONCENTRATION_CHECK` | Caster makes concentration check | caster, dc, roll_total, success: true/false | `{event: "CONCENTRATION_CHECK", caster: "PC_Wizard", dc: 15, roll_total: 12, success: false}` |
| `CONCENTRATION_FAILED` | Concentration check failed | caster, spell_name | `{event: "CONCENTRATION_FAILED", caster: "PC_Wizard", spell_name: "Invisibility"}` |
| `SPELL_RESISTANCE_CHECK` | SR check rolled | caster, target, caster_level, sr, roll_total, success | `{event: "SPELL_RESISTANCE_CHECK", caster: "PC_Wizard", target: "Demon", sr: 15, roll_total: 14, success: false}` |
| `SPELL_COUNTERED` | Counterspell successful | counterspeller, original_caster, spell_name | `{event: "SPELL_COUNTERED", counterspeller: "Enemy_Wizard", original_caster: "PC_Wizard", spell_name: "Fireball"}` |
| `DURATION_EXPIRED` | Spell/effect ends naturally | spell_name, affected_entities: [...] | `{event: "DURATION_EXPIRED", spell_name: "Haste", affected_entities: ["PC_Fighter", "PC_Rogue"]}` |
| `DISPEL_MAGIC` | Dispel magic attempt | dispeller, target_spell, dispel_check, success | `{event: "DISPEL_MAGIC", dispeller: "PC_Cleric", target_spell: "Web", success: true}` |

#### 1.4 Movement Events (4 labels)

| Event Label | Trigger Condition | Required Fields | Example Box Output |
|------------|------------------|----------------|-------------------|
| `MOVEMENT_COMPLETED` | Move action finished | mover, from, to, distance_ft | `{event: "MOVEMENT_COMPLETED", mover: "PC_Fighter", from: (2,3), to: (5,3), distance_ft: 15}` |
| `MOVEMENT_BLOCKED` | Path blocked by obstacle | mover, intended_square, blocker_type: "terrain"/"creature" | `{event: "MOVEMENT_BLOCKED", mover: "PC_Fighter", intended_square: (4,5), blocker_type: "terrain"}` |
| `DIFFICULT_TERRAIN` | Movement through difficult terrain | mover, squares_traversed, movement_cost_multiplier: 2 | `{event: "DIFFICULT_TERRAIN", mover: "PC_Rogue", squares_traversed: 2, cost: 10}` |
| `MOUNTED_MOVEMENT` | Mount moves with rider | rider, mount, from, to, distance_ft | `{event: "MOUNTED_MOVEMENT", rider: "PC_Paladin", mount: "Warhorse", from: (1,1), to: (6,1), distance_ft: 25}` |

#### 1.5 Condition Events (4 labels)

| Event Label | Trigger Condition | Required Fields | Example Box Output |
|------------|------------------|----------------|-------------------|
| `CONDITION_APPLIED` | New condition added | target, condition, duration_rounds, source | `{event: "CONDITION_APPLIED", target: "Orc_1", condition: "prone", duration_rounds: null, source: "trip"}` |
| `CONDITION_REMOVED` | Condition ends | target, condition, reason: "expired"/"cured"/"dispelled" | `{event: "CONDITION_REMOVED", target: "PC_Fighter", condition: "stunned", reason: "expired"}` |
| `CONDITION_EXPIRED` | Condition duration reached 0 | target, condition | `{event: "CONDITION_EXPIRED", target: "Orc_1", condition: "blinded"}` |
| `SAVE_ENDS_CONDITION` | Save successful against ongoing | target, condition, save_type, dc, roll_total | `{event: "SAVE_ENDS_CONDITION", target: "PC_Wizard", condition: "paralyzed", save_type: "Will", dc: 17, roll_total: 19}` |

#### 1.6 Combat Lifecycle Events (5 labels)

| Event Label | Trigger Condition | Required Fields | Example Box Output |
|------------|------------------|----------------|-------------------|
| `COMBAT_STARTED` | Combat initiated | participants: [...], surprise_round: true/false | `{event: "COMBAT_STARTED", participants: ["PC_Fighter", "Orc_1", "Orc_2"], surprise_round: false}` |
| `ROUND_STARTED` | New round begins | round_number | `{event: "ROUND_STARTED", round_number: 3}` |
| `TURN_STARTED` | Entity's turn begins | entity, initiative_order_position | `{event: "TURN_STARTED", entity: "PC_Fighter", initiative_order_position: 2}` |
| `TURN_ENDED` | Entity's turn ends | entity, actions_taken: [...] | `{event: "TURN_ENDED", entity: "PC_Fighter", actions_taken: ["standard_attack", "move"]}` |
| `FLAT_FOOTED_CLEARED` | Entity acts first time in combat | entity | `{event: "FLAT_FOOTED_CLEARED", entity: "PC_Rogue"}` |

#### 1.7 Environmental Events (3 labels)

| Event Label | Trigger Condition | Required Fields | Example Box Output |
|------------|------------------|----------------|-------------------|
| `ENVIRONMENTAL_DAMAGE` | Hazard damage applied | targets: [...], damage, damage_type, source | `{event: "ENVIRONMENTAL_DAMAGE", targets: ["PC_Fighter"], damage: 10, damage_type: "fire", source: "lava"}` |
| `FALL_TRIGGERED` | Entity falls from height | faller, distance_ft, surface_type | `{event: "FALL_TRIGGERED", faller: "PC_Rogue", distance_ft: 20, surface_type: "stone"}` |
| `FALLING_DAMAGE` | Fall damage applied | faller, damage, distance_ft | `{event: "FALLING_DAMAGE", faller: "PC_Rogue", damage: 7, distance_ft: 20}` |

**Total: 43 canonical event labels**

---

### 2. Template-to-LLM Augmentation Strategy

#### 2.1 Three-Tier Augmentation Model

The system uses a **graduated augmentation approach** with three tiers:

##### **Tier 1: Full Template Fallback (Zero LLM)**
Used when Spark is unavailable or fails.

**Structure:**
```python
template = "{actor} strikes {target} with their {weapon}! The blow lands true, dealing {damage} damage."
```

**Properties:**
- Pure template substitution (no LLM)
- Guarantees correct mechanical content
- Deterministic output (same inputs → same output)
- Always available (no model dependency)

**Use Cases:**
- Spark model unavailable/crashed
- Emergency fallback during LLM failure
- Performance mode (skip LLM for speed)

##### **Tier 2: Slot-Guided LLM (Hybrid)**
LLM fills flavor slots within template scaffolding.

**Structure:**
```python
template = "{actor} {ACTION_DESCRIPTION} {target} with their {weapon}! {IMPACT_DESCRIPTION}, dealing {damage} damage."

# Spark receives prompt:
"""
Event: HIT
Actor: Oaken the Fighter
Target: Orc Chieftain
Weapon: greatsword
Damage: 12
Tone: dramatic

Fill the slots:
ACTION_DESCRIPTION: [describe the attack motion]
IMPACT_DESCRIPTION: [describe the impact]

Constraints:
- Do not contradict HIT outcome
- Match dramatic tone
- Keep each slot under 15 words
"""
```

**Spark Output:**
```
ACTION_DESCRIPTION: "brings his greatsword down in a mighty arc"
IMPACT_DESCRIPTION: "The blade cleaves through armor and flesh"
```

**Final Narration:**
```
Oaken the Fighter brings his greatsword down in a mighty arc upon the Orc Chieftain with their greatsword! The blade cleaves through armor and flesh, dealing 12 damage.
```

**Properties:**
- Template guarantees structure and mechanical accuracy
- LLM provides flavor within constrained slots
- Slot verification prevents contradiction
- Fallback to Tier 1 if LLM output invalid

##### **Tier 3: Free LLM with Guardrails (Maximum Flexibility)**
LLM generates full narration with structural guidance.

**Structure:**
```python
# Spark receives Truth Packet:
{
  "event": "HIT",
  "actor": "Oaken the Fighter",
  "target": "Orc Chieftain",
  "weapon": "greatsword",
  "damage": 12,
  "hp_before": 45,
  "hp_after": 33,
  "margin": 4,
  "tone": "dramatic",
  "template_reference": "{actor} strikes {target} with their {weapon}! The blow lands true, dealing {damage} damage."
}

# System prompt includes:
"""
Generate vivid narration for this combat event.

REQUIRED elements:
- Describe the HIT outcome
- Mention the greatsword
- Convey that damage was dealt

FORBIDDEN:
- Do not contradict HIT (never say 'miss' or 'dodge')
- Do not invent new mechanical effects
- Do not specify exact damage number (that's in the receipt)

Tone: dramatic
Length: 2-3 sentences
"""
```

**Spark Output:**
```
Oaken's greatsword sings through the air in a devastating arc. The Orc Chieftain raises his shield, but the blow smashes through his defense, biting deep into his shoulder. The chieftain roars in pain, staggering backward.
```

**Properties:**
- Maximum narrative flexibility
- Requires robust verification (KILL-002 guardrails)
- Falls back to Tier 2 if verification fails
- Reserved for high-stakes moments (boss fights, climactic scenes)

---

#### 2.2 Augmentation Routing Logic

**Decision Tree:**

```
1. Is Spark available?
   NO → Use Tier 1 (Full Template)
   YES → Continue

2. Is this a high-stakes moment? (boss fight, critical hit, entity defeated)
   YES → Attempt Tier 3 (Free LLM with guardrails)
   NO → Continue

3. Is tone customization requested? (DM persona settings)
   YES → Use Tier 2 (Slot-Guided LLM)
   NO → Use Tier 1 (Full Template, fast path)

4. Did LLM generation succeed?
   NO → Fall back one tier
   YES → Verify output

5. Did verification pass?
   NO → Fall back one tier
   YES → Return LLM-augmented narration
```

**Configuration Parameters:**

```python
@dataclass
class NarrationSettings:
    """DM persona narration settings."""

    # Tier selection
    allow_free_llm: bool = True  # Enable Tier 3
    always_use_slots: bool = False  # Force Tier 2 for consistency

    # Tone/pacing
    tone: str = "neutral"  # Options: "grim", "whimsical", "dramatic", "terse"
    verbosity: str = "standard"  # Options: "terse", "standard", "verbose"

    # Character voice
    npc_personality_mode: bool = True  # Customize NPC dialogue

    # Combat pacing
    combat_momentum: str = "steady"  # Options: "early_skirmish", "climactic", "steady"

    # Performance
    max_generation_time_ms: int = 500  # Timeout for LLM generation
    fallback_on_timeout: bool = True
```

---

#### 2.3 Template Structure for LLM Augmentation

**Slot Taxonomy:**

Templates use standardized slot names for LLM augmentation:

| Slot Name | Purpose | Word Limit | Examples |
|-----------|---------|-----------|----------|
| `ACTION_DESCRIPTION` | Describe attack motion | 15 | "swings wildly", "lunges forward with precision" |
| `IMPACT_DESCRIPTION` | Describe hit/miss result | 15 | "the blade bites deep", "the arrow clatters off armor" |
| `AFTERMATH_DESCRIPTION` | Describe post-impact reaction | 20 | "the orc staggers, clutching the wound", "the goblin shrieks in pain" |
| `SPELL_VISUAL` | Describe spell appearance | 20 | "a blazing sphere of flame", "crackling lightning arcs" |
| `ENVIRONMENT_DETAIL` | Add scene atmosphere | 25 | "sparks fly in the dim torchlight", "blood spatters the cobblestones" |
| `NPC_REACTION` | NPC emotional/behavioral response | 20 | "the captain's eyes widen in alarm", "the wizard chuckles darkly" |

**Example: Slot-Enabled Template**

```python
TEMPLATES = {
    "HIT": {
        "base": "{actor} strikes {target} with their {weapon}! The blow lands true, dealing {damage} damage.",

        "slot_enabled": "{actor} {ACTION_DESCRIPTION} {target} with their {weapon}! {IMPACT_DESCRIPTION}, dealing {damage} damage. {AFTERMATH_DESCRIPTION}",

        "slot_prompts": {
            "ACTION_DESCRIPTION": "Describe the attack motion (under 15 words, maintain {tone} tone)",
            "IMPACT_DESCRIPTION": "Describe the impact (under 15 words, match HIT outcome)",
            "AFTERMATH_DESCRIPTION": "Describe the target's reaction (under 20 words, consider {hp_percent}% remaining HP)"
        },

        "slot_constraints": {
            "ACTION_DESCRIPTION": {
                "forbidden_words": ["miss", "dodge", "parry"],
                "max_words": 15
            },
            "IMPACT_DESCRIPTION": {
                "required_outcome": "HIT",  # Must convey successful hit
                "max_words": 15
            },
            "AFTERMATH_DESCRIPTION": {
                "max_words": 20,
                "hp_aware": True  # Calibrate to remaining HP%
            }
        }
    }
}
```

---

### 3. Verification Approach

#### 3.1 Verification Pipeline

All LLM-generated narration passes through a **4-stage verification pipeline** before delivery:

##### **Stage 1: Structural Validation**
Ensures required elements are present.

```python
def verify_structure(llm_output: str, truth_packet: dict) -> bool:
    """Verify LLM output contains required elements."""
    required_elements = {
        "actor": truth_packet.get("actor"),
        "target": truth_packet.get("target"),
        "weapon": truth_packet.get("weapon"),
    }

    for element_name, element_value in required_elements.items():
        if element_value and element_value not in llm_output:
            return False  # Missing required element

    return True
```

**Fail Action:** Fall back to template.

##### **Stage 2: Contradiction Detection (KILL-002)**
Detects mechanical contradictions using regex patterns.

```python
def detect_contradictions(llm_output: str, truth_packet: dict) -> List[str]:
    """Detect contradictions between LLM output and Box truth."""
    violations = []

    event = truth_packet["event"]

    # HIT event must not contain miss language
    if event == "HIT":
        miss_patterns = [
            r"\bmiss(es)?\b",
            r"\bdodge[sd]?\b",
            r"\bparr(y|ied)\b",
            r"\bevade[sd]?\b",
            r"\bblocks?\b"
        ]
        for pattern in miss_patterns:
            if re.search(pattern, llm_output, re.IGNORECASE):
                violations.append(f"HIT event contains miss language: '{pattern}'")

    # MISS event must not contain hit language
    if event == "MISS":
        hit_patterns = [
            r"\bstrikes? home\b",
            r"\bbites? deep\b",
            r"\blands? true\b",
            r"\bconnects?\b",
            r"\bhits?\b"
        ]
        for pattern in hit_patterns:
            if re.search(pattern, llm_output, re.IGNORECASE):
                violations.append(f"MISS event contains hit language: '{pattern}'")

    # Check for mechanical assertions (AC values, damage numbers not in truth packet)
    mechanical_assertion_patterns = [
        r"\bAC\s+\d+\b",  # "AC 15"
        r"\b\d+\s+damage\b",  # "8 damage" (if not matching truth_packet damage)
        r"\bPHB\s+page\s+\d+\b",  # Rule citations
        r"\bDC\s+\d+\b",  # "DC 15" (if not in truth packet)
    ]

    for pattern in mechanical_assertion_patterns:
        if re.search(pattern, llm_output, re.IGNORECASE):
            violations.append(f"Mechanical assertion detected: '{pattern}'")

    return violations
```

**Fail Action:** If violations detected, fall back to template.

##### **Stage 3: HP Proportionality Check**
Ensures damage descriptions match HP loss percentage.

```python
def verify_hp_proportionality(llm_output: str, truth_packet: dict) -> bool:
    """Ensure damage description proportional to HP loss."""
    if "hp_before" not in truth_packet or "hp_after" not in truth_packet:
        return True  # Cannot verify, pass

    hp_before = truth_packet["hp_before"]
    hp_after = truth_packet["hp_after"]
    hp_percent = (hp_after / hp_before) * 100

    # Define thresholds
    MINOR_WOUND = 80  # >80% HP remaining
    MODERATE_WOUND = 50  # 50-80% HP remaining
    SEVERE_WOUND = 20  # 20-50% HP remaining
    CRITICAL_WOUND = 0  # <20% HP remaining

    # Forbidden phrases for minor wounds (<20% HP loss)
    if hp_percent > MINOR_WOUND:
        forbidden = ["devastating", "grievous", "mortal", "lethal", "critical"]
        for phrase in forbidden:
            if phrase in llm_output.lower():
                return False

    # Required intensity for severe wounds (>80% HP loss)
    if hp_percent < SEVERE_WOUND:
        required_intensity = ["devastating", "grievous", "vicious", "terrible", "brutal"]
        if not any(phrase in llm_output.lower() for phrase in required_intensity):
            return False

    return True
```

**Fail Action:** Fall back to template with correct intensity.

##### **Stage 4: Consistency Check**
Ensures no contradiction with recent narrations.

```python
def verify_consistency(llm_output: str, recent_narrations: List[str]) -> List[str]:
    """Check for contradictions with recent narrations."""
    violations = []

    # Example: If previous narration said "door is open", current cannot say "door is locked"
    # This requires semantic analysis (advanced, optional for Phase 1)

    # Simple keyword-based check:
    for prev_narration in recent_narrations:
        # Extract key facts from previous narrations
        # Compare with current output
        # Flag contradictions
        pass

    return violations
```

**Fail Action:** Flag for DM review (optional enforcement).

---

#### 3.2 Verification Enforcement Levels

```python
class VerificationMode(Enum):
    """Verification enforcement strictness."""
    STRICT = "strict"      # Any violation → immediate template fallback
    MODERATE = "moderate"  # Major violations → fallback, minor violations → warning
    PERMISSIVE = "permissive"  # Violations logged but allowed
```

**Configuration:**

```python
@dataclass
class NarrationVerificationSettings:
    """Verification settings."""

    mode: VerificationMode = VerificationMode.STRICT

    # Stage toggles
    enable_contradiction_detection: bool = True
    enable_hp_proportionality: bool = True
    enable_consistency_check: bool = False  # Advanced, Phase 2+

    # Fallback behavior
    fallback_on_timeout: bool = True
    fallback_on_verification_fail: bool = True
```

---

### 4. Example Narrations: Template vs LLM-Augmented

#### Example 1: Standard Attack Hit

**Box Event:**
```json
{
  "event": "HIT",
  "actor": "Oaken the Fighter",
  "target": "Orc Warrior",
  "weapon": "longsword",
  "damage": 10,
  "hp_before": 30,
  "hp_after": 20,
  "margin": 3
}
```

**Tier 1 (Full Template):**
```
Oaken the Fighter strikes Orc Warrior with their longsword! The blow lands true, dealing 10 damage.
```

**Tier 2 (Slot-Guided, Dramatic Tone):**
```
Oaken the Fighter brings his longsword down in a powerful slash upon Orc Warrior! The blade cuts deep, blood spraying across the stone floor, dealing 10 damage. The orc grunts in pain but holds his ground.
```

**Tier 3 (Free LLM, Dramatic Tone):**
```
Oaken's longsword flashes in the torchlight as he drives forward. The orc raises his axe to parry, but Oaken's blade is faster—it slips past the defense and bites into the warrior's side. The orc staggers backward, clutching the wound, his eyes blazing with fury.
```

**Provenance Tags:**
- Template: `[DERIVED]` (template structure) + `[BOX]` (damage value)
- Slot-Guided: `[DERIVED]` (template) + `[NARRATIVE]` (slot content) + `[BOX]` (damage)
- Free LLM: `[NARRATIVE]` (full text) + `[BOX]` (event outcome)

---

#### Example 2: Critical Miss

**Box Event:**
```json
{
  "event": "CRITICAL_MISS",
  "actor": "Thrain the Dwarf",
  "target": "Goblin Sneak",
  "weapon": "warhammer",
  "natural_roll": 1
}
```

**Tier 1 (Full Template):**
```
Thrain the Dwarf stumbles badly, their attack completely missing Goblin Sneak!
```

**Tier 2 (Slot-Guided, Whimsical Tone):**
```
Thrain the Dwarf winds up for a mighty swing, but his boot catches on a loose stone! The warhammer goes flying wildly past Goblin Sneak, who cackles and skips backward. Thrain curses under his breath, recovering his balance.
```

**Tier 3 (Free LLM, Grim Tone):**
```
Thrain swings his warhammer with all his might—too much might. The momentum pulls him off-balance, and the blow whistles harmlessly past the goblin. The sneak grins, showing yellow teeth, and Thrain realizes his error has left him vulnerable for a critical moment.
```

---

#### Example 3: Fireball Spell Cast

**Box Event:**
```json
{
  "event": "SPELL_CAST",
  "caster": "Sylara the Wizard",
  "spell_name": "Fireball",
  "target_point": {"x": 7, "y": 4},
  "targets_in_aoe": ["Orc_1", "Orc_2", "Orc_3"],
  "damage": 28,
  "damage_type": "fire",
  "save_dc": 17
}
```

**Tier 1 (Full Template):**
```
Sylara the Wizard casts Fireball at grid square (7,4)! The spell erupts, engulfing Orc_1, Orc_2, and Orc_3 in flames.
```

**Tier 2 (Slot-Guided, Dramatic Tone):**
```
Sylara the Wizard hurls a blazing sphere of flame toward grid square (7,4)! The fireball explodes with a deafening roar, a wave of heat washing over the battlefield as flames consume Orc_1, Orc_2, and Orc_3. The smell of charred flesh fills the air.
```

**Tier 3 (Free LLM, Dramatic Tone):**
```
Sylara's fingers weave through the air, and a tiny spark forms at her fingertips—growing, expanding, until it's a roiling sphere of crimson fire the size of a man's head. With a sharp gesture, she hurls it into the midst of the orc warband. The fireball detonates in a blinding flash, and the orcs' screams are drowned out by the roar of the inferno. When the smoke clears, three charred forms lie smoldering on the ground.
```

---

#### Example 4: Movement with AoO Triggered

**Box Event:**
```json
{
  "event": "AOO_TRIGGERED",
  "provoker": "Lyra the Rogue",
  "threatening_entity": "Ogre Brute",
  "grid_square": {"x": 4, "y": 5}
}
```

**Tier 1 (Full Template):**
```
Lyra the Rogue provokes an attack of opportunity from Ogre Brute!
```

**Tier 2 (Slot-Guided, Terse Tone):**
```
Lyra the Rogue darts past Ogre Brute's reach! The ogre swings his club at her exposed flank as she moves through square (4,5).
```

**Tier 3 (Free LLM, Terse Tone):**
```
Lyra tries to slip past the ogre, but she's not fast enough. The brute's club comes down like a hammer toward her retreating form.
```

*Note: The actual AoO resolution (hit/miss/damage) follows in the next event.*

---

#### Example 5: Entity Defeated

**Box Event:**
```json
{
  "event": "ENTITY_DEFEATED",
  "target": "Orc Chieftain",
  "final_damage": 18,
  "defeated_by": "Oaken the Fighter"
}
```

**Tier 1 (Full Template):**
```
Orc Chieftain collapses, defeated!
```

**Tier 2 (Slot-Guided, Dramatic Tone):**
```
Orc Chieftain's eyes widen as the final blow strikes home! He clutches his chest, blood pooling beneath him, and collapses to the ground with a strangled gasp. The chieftain is defeated.
```

**Tier 3 (Free LLM, Climactic Boss Fight):**
```
The Orc Chieftain roars defiance even as Oaken's blade finds its mark. For a moment, the massive warrior stands tall, refusing to fall—then his knees buckle. He crashes to the floor with a thunderous impact, his axe clattering from his grip. The battle is won. The chieftain lies still, his reign of terror ended.
```

---

### 5. Integration Points with Existing Infrastructure

#### 5.1 Narrator Module ([narrator.py](aidm/narration/narrator.py:1))

**Current State:**
- 55 templates keyed by narration tokens
- Template-only implementation (M1)
- No LLM integration yet

**Required Changes:**
1. Extend `NarrationTemplates` with slot-enabled versions
2. Add `augmentation_tier` field to `NarrationContext`
3. Implement `_narrate_with_spark()` method for LLM augmentation
4. Add verification pipeline before returning narration

**Proposed Architecture:**

```python
@dataclass
class NarrationContext:
    """Extended context for LLM augmentation."""

    # Existing fields...
    actor_name: str = "The attacker"
    target_name: str = "the target"
    weapon_name: str = "weapon"

    # New fields for augmentation
    augmentation_tier: int = 1  # 1=template, 2=slot, 3=free
    tone: str = "neutral"
    combat_momentum: str = "steady"
    hp_percent: Optional[float] = None
    recent_narrations: List[str] = field(default_factory=list)
    truth_packet: Optional[Dict[str, Any]] = None

class Narrator:
    def narrate(self, result: EngineResult, context: Optional[NarrationContext] = None) -> str:
        """Generate narration with optional LLM augmentation."""

        # Determine augmentation tier
        tier = self._select_augmentation_tier(result, context)

        if tier == 1:
            return self._narrate_from_template(result.narration_token, result, context)
        elif tier == 2:
            return self._narrate_slot_guided(result.narration_token, result, context)
        elif tier == 3:
            return self._narrate_free_llm(result, context)

    def _narrate_slot_guided(self, token: str, result: EngineResult, context: NarrationContext) -> str:
        """Generate narration using slot-guided LLM."""

        template_data = NarrationTemplates.get_slot_enabled_template(token)

        # Build Spark prompt for each slot
        slot_fills = {}
        for slot_name, slot_prompt in template_data["slot_prompts"].items():
            spark_output = self._call_spark(slot_prompt, context)

            # Verify slot output
            if self._verify_slot(spark_output, slot_name, template_data["slot_constraints"]):
                slot_fills[slot_name] = spark_output
            else:
                # Fallback to default
                slot_fills[slot_name] = template_data["slot_defaults"][slot_name]

        # Combine template + slot fills
        return template_data["base"].format(**slot_fills, **context.__dict__)
```

#### 5.2 Spark Adapter ([spark_adapter.py](aidm/spark/spark_adapter.py:1))

**Current State:**
- Abstract interface for LLM model loading
- `generate()` method returns `SparkResponse`
- No narration-specific logic

**Required Changes:**
None. Narrator calls `spark_adapter.generate(request)` with appropriate prompts.

#### 5.3 Guarded Narration Service

**Current State:**
- Wraps Narrator with guardrails (KILL-001, KILL-002)
- Returns `NarrationResult` with provenance tags

**Required Changes:**
1. Extend verification to handle LLM-augmented output
2. Add contradiction detection for Tier 3 (free LLM)
3. Tag output with appropriate provenance (`[NARRATIVE]` for LLM-generated portions)

---

## Sub-Question 4: Confirmation Gates for Player Intent

### 1. Confirmation Flow Protocol

#### 1.1 Lifecycle Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PLAYER INTENT LIFECYCLE                      │
└─────────────────────────────────────────────────────────────────┘

1. Voice/Text Input
   ↓
   "I cast fireball at the group by the door"

2. Voice Intent Parser (VoiceIntentParser)
   ↓
   ParseResult {
     intent: CastSpellIntent(spell_name="fireball", target_mode="point"),
     confidence: 0.75,
     ambiguous_location: true,
     raw_slots: {spatial_anchor: "door"}
   }

3. Ambiguity Detection (ClarificationEngine)
   ↓
   IF ambiguous_location: Generate clarification request

4. Spark Interpretation [UNCERTAIN]
   ↓
   "You want to cast Fireball centered on grid square (7,4)?"

5. Ghost Stencil Visualization (GhostStencil)
   ↓
   Show AoE overlay at (7,4) with affected entities highlighted
   Player sees: [PC_Wizard at center, Orc_1/Orc_2/Orc_3 in blast radius]

6. Player Confirmation/Adjustment
   ↓
   OPTION A: Player confirms → "Yes, that's right"
   OPTION B: Player adjusts → "Move it one square left"
   OPTION C: Player cancels → "Wait, no, I change my mind"

7. Confirmed Intent [BOX-READY]
   ↓
   IF confirmed:
     FrozenStencil {
       origin: (6,4),  # After adjustment
       affected_cells: [(6,3), (6,4), (6,5), (7,3), (7,4), (7,5)],
       caster_id: "PC_Wizard",
       spell_name: "Fireball"
     }

8. Box Execution [BOX]
   ↓
   Box resolves Fireball at (6,4), computes saves, damage
   Returns EngineResult with [BOX] provenance

9. Narration
   ↓
   Spark narrates outcome: "Sylara's fireball erupts..."
```

---

### 2. Ambiguity Categories and Confirmation Patterns

#### 2.1 AoE Targeting: "At the group" / "Near the door"

**Scenario:** Player says "I cast fireball at the group by the door"

**Ambiguity:** Multiple valid center squares for AoE.

**Confirmation Flow:**

**Step 1: Spark Interprets [UNCERTAIN]**
```
DM Persona (Spark-generated):
"You want to cast Fireball near the door—I see three orcs clustered there.
Where do you want to center the blast?"
```

**Step 2: Ghost Stencil Overlay**
- Show semi-transparent 20ft radius circle at proposed center (7,4)
- Highlight affected entities: Orc_1, Orc_2, Orc_3
- Show distance markers from PC_Wizard
- Display "Press [W/A/S/D] to nudge, [Space] to confirm, [Esc] to cancel"

**Step 3: Player Adjusts/Confirms**
```
Player Actions:
- Press 'A' (nudge left) → Stencil moves to (6,4)
- New affected entities: Orc_1, Orc_2, Orc_4 (different orc caught in blast)
- Press [Space] to confirm

Result:
FrozenStencil confirmed at (6,4), ready for Box execution
```

**D&D 3.5e Considerations:**
- Show friendly fire warning if allies in AoE: "Warning: This will catch Thrain in the blast!"
- Display cover indicators (half cover = dotted outline, full cover = grayed out)
- Indicate spell range limit (e.g., "400 ft + 40 ft/level for Fireball")

---

#### 2.2 Multiple Valid Targets: "I attack the orc"

**Scenario:** Player says "I attack the orc" but there are 3 orcs visible.

**Ambiguity:** Which orc to target?

**Confirmation Flow:**

**Step 1: Spark Interprets [UNCERTAIN]**
```
DM Persona (Spark-generated):
"Which orc are you attacking? There's one to your left (wounded),
one in front of you, and one near the archer."
```

**Step 2: Visual Highlighting**
- Highlight all valid targets (Orc_1, Orc_2, Orc_3) with numbered overlays
- Show HP bars if visible (Orc_1 bloodied, others healthy)
- Display distance and threat indicators

**Step 3: Player Selects**
```
Player Input Options:
- Voice: "The wounded one"
- Click/Tap: Click on Orc_1
- Hotkey: Press '1' for Orc_1

Result:
DeclaredAttackIntent(target_ref="Orc_1", weapon="longsword") confirmed [BOX-READY]
```

**D&D 3.5e Considerations:**
- Show AoO warnings: "Attacking Orc_3 at range will provoke from Orc_2"
- Indicate cover/concealment: "Orc_3 has partial cover (+4 AC)"
- Display threatened squares (red overlay for enemy threat zones)

---

#### 2.3 Movement Path: "I move to flank"

**Scenario:** Player says "I move to flank the orc"

**Ambiguity:** Multiple paths possible, some provoke AoOs.

**Confirmation Flow:**

**Step 1: Spark Interprets [UNCERTAIN]**
```
DM Persona (Spark-generated):
"You want to flank the orc with Lyra. I can see two paths—
one goes around the north side (safe), the other cuts through the middle
(you'd provoke an attack of opportunity from the ogre). Which do you prefer?"
```

**Step 2: Path Visualization**
- Show two colored paths:
  - Green path: Safe route (no AoOs)
  - Yellow path: Shorter but provokes AoO from Ogre_Brute
- Display movement cost for each (Green: 20 ft, Yellow: 15 ft)
- Highlight threatened squares in red

**Step 3: Player Chooses**
```
Player Input:
- Voice: "Take the safe route"
- Click: Click on green path endpoint
- Hotkey: Press '1' for green path

Result:
MoveIntent(destination=(5,7), path=[(2,3), (3,4), (4,5), (5,7)]) confirmed [BOX-READY]
```

**D&D 3.5e Considerations:**
- Show difficult terrain (movement cost doubled, brown overlay)
- Indicate 5-foot step eligibility: "You can take a 5-foot step here without provoking"
- Display remaining movement: "You have 10 ft remaining after this move"

---

#### 2.4 Spell Selection: "I cast a healing spell"

**Scenario:** Player says "I cast a healing spell" but has multiple prepared.

**Ambiguity:** Which healing spell?

**Confirmation Flow:**

**Step 1: Spark Interprets [UNCERTAIN]**
```
DM Persona (Spark-generated):
"You have Cure Light Wounds and Cure Moderate Wounds prepared.
Lyra is at 8 HP out of 32—which do you want to cast?"
```

**Step 2: Spell Options Display**
```
┌────────────────────────────────────────────┐
│  Cure Light Wounds (1st level)            │
│  Heals: 1d8+3 (avg 7 HP)                  │
│  Remaining slots: 2/3                      │
│                                            │
│  Cure Moderate Wounds (2nd level)         │
│  Heals: 2d8+6 (avg 15 HP)                 │
│  Remaining slots: 1/2                      │
└────────────────────────────────────────────┘
```

**Step 3: Player Selects**
```
Player Input:
- Voice: "Cure Moderate"
- Click: Click on "Cure Moderate Wounds"
- Hotkey: Press '2' for 2nd-level spell

Result:
CastSpellIntent(spell_name="Cure Moderate Wounds", target_mode="creature", target_ref="Lyra") confirmed [BOX-READY]
```

**D&D 3.5e Considerations:**
- Show remaining spell slots per level
- Indicate concentration check requirement if casting in threatened square
- Display component requirements (V/S/M/F) and availability

---

#### 2.5 Line Attacks: "I shoot a lightning bolt at them"

**Scenario:** Player says "I shoot a lightning bolt at them"

**Ambiguity:** Which direction? Line attacks require exact facing.

**Confirmation Flow:**

**Step 1: Spark Interprets [UNCERTAIN]**
```
DM Persona (Spark-generated):
"Lightning Bolt creates a 120-foot line. Which direction do you want to aim it?"
```

**Step 2: Line Overlay Visualization**
- Show rotating 120 ft line emanating from PC_Wizard
- Highlight affected squares as line rotates
- Display affected entities (Orc_1, Orc_2 in current line)
- Show "Rotate: [Q/E], Confirm: [Space]"

**Step 3: Player Adjusts/Confirms**
```
Player Actions:
- Press 'E' to rotate clockwise → Line now hits Orc_1, Orc_2, Orc_3
- Press [Space] to confirm

Result:
CastSpellIntent(spell_name="Lightning Bolt", target_mode="point", direction="EAST") confirmed [BOX-READY]
```

**D&D 3.5e Considerations:**
- Show wall/obstacle clipping: "Line stops at the wall after 60 feet"
- Indicate friendly fire: "This angle will also hit Thrain!"
- Display Reflex save DC: "Targets can save for half damage (DC 17)"

---

### 3. D&D 3.5e Specific Confirmation Needs

#### 3.1 Attack of Opportunity Warnings

**Trigger:** Player action provokes AoO (movement through threatened square, casting spell, ranged attack in melee, standing from prone)

**Confirmation Pattern:**

```
Spark [UNCERTAIN]:
"Moving through that square will provoke an attack of opportunity from the Orc Warrior.
You can take a 5-foot step instead (no AoO), or proceed with the move. What do you want to do?"

Visual Overlay:
- Threatened squares highlighted in red
- Safe 5-foot step squares highlighted in green
- AoO source (Orc Warrior) marked with sword icon

Options:
[1] Take 5-foot step (safe, limited movement)
[2] Proceed with full move (provokes AoO)
[3] Cancel action
```

**D&D 3.5e Rules:**
- 5-foot step: No AoO, but cannot move more than 5 ft this turn
- Tumble check: Acrobatics check to avoid AoO (DC 15)
- Withdraw action: First square does not provoke

---

#### 3.2 Cover/Concealment Notifications

**Trigger:** Player attacks target with cover/concealment

**Confirmation Pattern:**

```
Spark [UNCERTAIN]:
"The goblin has partial cover from the pillar (+4 AC, +2 Reflex saves).
Do you still want to attack, or switch targets?"

Visual Overlay:
- Cover source (pillar) highlighted
- Line of sight drawn from PC to target (dashed line passing through cover)
- AC bonus indicator: "Target AC: 15 (base 11 + cover 4)"

Options:
[1] Attack anyway (with cover penalty)
[2] Switch targets
[3] Move to better position (spending move action)
```

**D&D 3.5e Rules:**
- Partial cover: +4 AC, +2 Reflex saves
- Full cover: Cannot be targeted directly
- Improved cover: +8 AC, +4 Reflex saves (rare)

---

#### 3.3 Spell Component Requirements

**Trigger:** Player casts spell requiring components not in inventory

**Confirmation Pattern:**

```
Spark [UNCERTAIN]:
"Fireball requires a small ball of bat guano and sulfur (material component, 50 gp value).
You don't have this in your component pouch. You can:
1. Use your Eschew Materials feat (if you have it)
2. Switch to a different spell
3. Cancel

What do you want to do?"

Visual:
- Component requirement popup
- Inventory check status
- Alternate spell suggestions

Options:
[1] Proceed (if feat allows)
[2] Cast [alternate spell] instead
[3] Cancel action
```

**D&D 3.5e Rules:**
- V = Verbal (requires speaking, fails if silenced)
- S = Somatic (requires hand gestures, fails if hands bound)
- M = Material (consumed, requires component pouch or specific item)
- F = Focus (not consumed, must be held/present)
- DF = Divine Focus (holy symbol for clerics)

---

#### 3.4 Concentration Check Warnings

**Trigger:** Player casts spell in threatened square (adjacent to enemy)

**Confirmation Pattern:**

```
Spark [UNCERTAIN]:
"You're casting Fireball while threatened by the Orc Warrior.
This requires a Concentration check (DC 15) to avoid losing the spell.
Your Concentration modifier is +8. Do you want to proceed?"

Visual:
- Threatened square indicator (red border)
- Concentration DC displayed
- Success probability: "65% chance to succeed"

Options:
[1] Cast spell (requires concentration check)
[2] Take 5-foot step away first (no concentration check needed)
[3] Cast defensively (+4 to DC but no AoO)
[4] Cancel
```

**D&D 3.5e Rules:**
- Casting in threatened square: Concentration DC 15 + spell level
- Casting defensively: DC 15 + spell level, no AoO provoked
- Taking damage while casting: DC 10 + damage dealt + spell level

---

### 4. Integration Points with Existing Infrastructure

#### 4.1 Voice Intent Parser ([voice_intent_parser.py](aidm/immersion/voice_intent_parser.py:1))

**Current State:**
- Produces `ParseResult` with `ambiguous_target`, `ambiguous_location`, `ambiguous_action` flags
- Uses `STMContext` for pronoun resolution
- Confidence scoring for routing to clarification

**Integration:**
```python
# In play loop:
parse_result = voice_parser.parse_transcript(transcript, stm_context)

if parse_result.needs_clarification:
    # Route to clarification engine
    clarification = clarification_engine.generate_clarification(parse_result, world_context)
    # Present clarification to player
    # Wait for player response
    # Re-parse or adjust intent based on response
```

#### 4.2 Clarification Loop ([clarification_loop.py](aidm/immersion/clarification_loop.py:1))

**Current State:**
- `ClarificationEngine` generates DM-persona prompts
- `ClarificationRequest` contains prompt, suggested options, missing fields

**Integration:**
```python
# Clarification flow:
clarification = clarification_engine.generate_clarification(parse_result, world_context)

if clarification.clarification_type == "location":
    # Show ghost stencil for AoE targeting
    stencil = create_stencil(
        shape=StencilShape.BURST,
        origin=inferred_location,
        radius_ft=20,  # Fireball radius
        grid_width=world_state.grid_width,
        grid_height=world_state.grid_height
    )
    # Display stencil, allow nudge/rotate/confirm
    # Wait for player confirmation
    frozen_stencil = confirm_stencil(stencil, timestamp=time.time(), caster_id="PC_Wizard")
```

#### 4.3 Ghost Stencil System ([ghost_stencil.py](aidm/immersion/ghost_stencil.py:1))

**Current State:**
- `GhostStencil` dataclass for AoE overlays
- `create_stencil()`, `nudge_stencil()`, `rotate_stencil()`, `confirm_stencil()` functions
- Pure functions (no state mutation)

**Integration:**
```python
# AoE targeting workflow:
stencil = create_stencil(StencilShape.BURST, origin, grid_width, grid_height, radius_ft=20)

while not player_confirmed:
    # Display stencil to player
    render_stencil(stencil)

    # Get player input
    input_action = await get_player_input()  # "nudge_left", "rotate_cw", "confirm", "cancel"

    if input_action == "nudge_left":
        stencil = nudge_stencil(stencil, dx=-1, dy=0)
    elif input_action == "rotate_cw":
        stencil = rotate_stencil(stencil, clockwise=True)
    elif input_action == "confirm":
        frozen = confirm_stencil(stencil, time.time(), caster_id, spell_name)
        break
    elif input_action == "cancel":
        return None

# Frozen stencil ready for Box execution
box_result = box.resolve_aoe_spell(frozen.stencil.affected_cells, spell_name, caster_id)
```

---

### 5. Provenance Protocol: [UNCERTAIN] → [BOX]

#### 5.1 Provenance Tags

All actions flow through a **provenance pipeline**:

```
┌──────────────────────────────────────────────────────────────┐
│                   PROVENANCE PIPELINE                         │
└──────────────────────────────────────────────────────────────┘

Stage 1: Voice Input
  Provenance: [VOICE]
  Example: "I cast fireball at the group by the door"

Stage 2: Spark Interpretation
  Provenance: [UNCERTAIN]
  Example: "You want to cast Fireball centered on grid square (7,4)?"

  Key Rule: SPARK MUST NEVER ASSUME. If ambiguity exists, mark [UNCERTAIN].

Stage 3: Player Confirmation
  Provenance: [PLAYER_CONFIRMED]
  Example: Player confirms via ghost stencil or explicit "yes"

Stage 4: Box Execution
  Provenance: [BOX]
  Example: Box resolves Fireball, produces EngineResult with damage, saves, etc.

Stage 5: Narration
  Provenance: [NARRATIVE] (Spark-generated flavor) + [BOX] (mechanical outcome)
  Example: "[NARRATIVE] Sylara's fireball erupts in a blinding flash!
            [BOX] Orc_1 takes 28 fire damage (failed save)."
```

#### 5.2 Provenance Enforcement Rules

**Rule 1: Spark Cannot Assume Target Square**

```python
# FORBIDDEN:
def interpret_intent_BAD(player_input: str) -> Intent:
    if "fireball" in player_input and "door" in player_input:
        # BAD: Assumes grid square without confirmation
        return CastSpellIntent(
            spell_name="Fireball",
            target_mode="point",
            target_location=Position(7, 4)  # ASSUMED, not confirmed
        )

# CORRECT:
def interpret_intent_GOOD(player_input: str) -> ParseResult:
    if "fireball" in player_input and "door" in player_input:
        # GOOD: Marks location as ambiguous, requires confirmation
        return ParseResult(
            intent=CastSpellIntent(spell_name="Fireball", target_mode="point"),
            confidence=0.6,
            ambiguous_location=True,  # Flags for clarification
            raw_slots={"spatial_anchor": "door"}
        )
```

**Rule 2: Player Confirms, Box Executes**

```python
# Confirmation flow:
parse_result = parser.parse_transcript(transcript, context)

if parse_result.ambiguous_location:
    # Generate [UNCERTAIN] prompt
    clarification = clarification_engine.generate_clarification(parse_result, world_context)
    spark_interpretation = f"[UNCERTAIN] {clarification.prompt}"

    # Show ghost stencil, get player confirmation
    stencil = create_stencil(...)
    frozen_stencil = await get_player_confirmation(stencil)

    if frozen_stencil is None:
        # Player cancelled
        return "Action cancelled."

    # Now ready for Box execution with [PLAYER_CONFIRMED] provenance
    intent = CastSpellIntent(
        spell_name="Fireball",
        target_mode="point",
        target_location=frozen_stencil.stencil.origin
    )

    # Box executes with full authority
    engine_result = box.resolve_spell(intent, world_state)  # [BOX] provenance
```

**Rule 3: No [UNCERTAIN] Actions Reach Box**

```python
# Validation gate before Box execution:
def execute_action(intent: Intent, provenance: str) -> EngineResult:
    if provenance == "[UNCERTAIN]":
        raise ValueError("Cannot execute [UNCERTAIN] action. Requires [PLAYER_CONFIRMED] first.")

    # Only [PLAYER_CONFIRMED] or [BOX] actions proceed
    return box.execute(intent)
```

---

## Deliverable Summary

### Event Label Taxonomy
- **43 canonical event labels** across 7 domains
- Comprehensive coverage of D&D 3.5e combat, spellcasting, movement, conditions
- Each label includes required fields and example Box output

### Template-to-LLM Augmentation
- **3-tier model:** Full template → Slot-guided → Free LLM
- **Slot taxonomy** with word limits and constraints
- **Verification pipeline:** 4-stage validation with fallback
- **5 example narrations** showing template vs augmented output

### Confirmation Gates
- **5 ambiguity categories** with confirmation patterns
- **Ghost stencil integration** for AoE targeting
- **D&D 3.5e specific confirmations:** AoO warnings, cover notifications, concentration checks, component requirements
- **Provenance protocol:** [UNCERTAIN] → [PLAYER_CONFIRMED] → [BOX]

### Integration Points
- Voice Intent Parser (existing ambiguity flags)
- Clarification Engine (DM-persona prompts)
- Ghost Stencil System (AoE visualization)
- Provenance Store (W3C PROV-DM tracking)

---

## Next Steps (Recommendations)

### Phase 1 (WO-027 through WO-031)
1. Implement event label taxonomy in Box (extend EngineResult)
2. Create slot-enabled templates in narrator.py (Tier 2)
3. Integrate clarification loop with ghost stencil system
4. Add provenance validation gates

### Phase 2 (Future)
1. Implement Tier 3 (free LLM with guardrails)
2. Add advanced verification (semantic consistency checking)
3. Expand to non-combat scenarios (NPC dialogue, exploration)
4. Build DM persona configuration UI

---

## References

- [narrator.py](aidm/narration/narrator.py:1) — Current template system (55 templates)
- [ghost_stencil.py](aidm/immersion/ghost_stencil.py:1) — AoE visualization
- [clarification_loop.py](aidm/immersion/clarification_loop.py:1) — DM-persona prompts
- [voice_intent_parser.py](aidm/immersion/voice_intent_parser.py:1) — Intent parsing with ambiguity detection
- [SPARK_LENS_BOX_DOCTRINE.md](docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md:1) — Architectural axioms
- [RQ_NARR_001_A_OUTPUT_SPACE_AND_TRUTH_PACKET.md](docs/research/findings/RQ_NARR_001_A_OUTPUT_SPACE_AND_TRUTH_PACKET.md:1) — Spark allowed output space

---

**END OF RESEARCH DOCUMENT**

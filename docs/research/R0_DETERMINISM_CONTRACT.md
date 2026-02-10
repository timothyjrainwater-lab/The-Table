# R0 Determinism Contract
## Replay-Identical Guarantees and Forbidden Sources

**Status:** R0 RESEARCH / STRUCTURED SPEC / AWAITING APPROVAL
**Agent:** Agent A (Canonical Foundations Architect)
**Date:** 2026-02-10
**Authority:** Proposal — requires cross-agent validation + PM approval before enforcement

---

## Purpose

This document defines the **determinism contract** for AIDM, specifying:
- What MUST be replay-identical (mechanical outcomes)
- What MAY vary (presentation layer)
- Where randomness lives (RNG streams)
- What is forbidden (non-deterministic sources)
- How to verify determinism (test protocol)

**Sacred Constraint (from GLOBAL-AUDIT-001):**
- Constraint A1 (🔴 SACRED): "Determinism is sacred. Engine outcomes must be replay-identical under identical inputs."

---

## Core Principle

### Determinism Definition

**AIDM Determinism:** Given **identical inputs** to the engine, the engine MUST produce **identical mechanical outcomes**.

```
Identical Inputs → Identical Mechanical Outcomes
```

**Inputs:**
- Player intents (after clarification freeze)
- Seeded RNG streams
- World state at turn start
- Rules configuration (Session Zero settings)

**Mechanical Outcomes:**
- Dice rolls (attack, damage, save, initiative, skill check)
- HP changes
- Position changes
- Condition application/removal
- Action legality decisions
- State transitions

---

## Determinism Boundaries

### Layer 1: Mechanical Core (MUST Be Identical)

**Engine operations that MUST produce identical results:**

| Operation | Deterministic? | Enforcement |
|-----------|----------------|-------------|
| Dice rolls | ✅ YES | Seeded RNG, logged |
| Damage calculation | ✅ YES | Pure function of roll + modifiers |
| HP updates | ✅ YES | Event-sourced |
| Position changes | ✅ YES | Integer math (CP-001) |
| Distance calculation | ✅ YES | 1-2-1-2 diagonal (CP-001) |
| Attack resolution | ✅ YES | d20 + modifiers vs AC |
| Save resolution | ✅ YES | d20 + save bonus vs DC |
| Initiative ordering | ✅ YES | Seeded init RNG |
| Condition application | ✅ YES | Rules-based |
| Action legality | ✅ YES | State-based validation |
| Event log | ✅ YES | Append-only, no mutations |

**Guarantee:** Replay same event log → reconstruct identical world state.

---

### Layer 2: Presentation Layer (MAY Vary)

**Presentation operations that MAY differ across replays:**

| Operation | Variable? | Why? |
|-----------|-----------|------|
| LLM narration text | ✅ YES | Non-deterministic LLM sampling |
| Narration tone/style | ✅ YES | Player profile affects wording |
| Asset appearance | ✅ YES | Generation model may differ |
| Audio mix | ✅ YES | Selection from palette may vary |
| UI animations | ✅ YES | Frame timing, client-side rendering |
| Display names | ✅ YES | Localization, Skin Pack |

**Guarantee:** Presentation variance CANNOT affect mechanical outcomes.

---

### Layer 3: Metadata (MAY Vary, But Logged)

**Metadata that MAY differ but is logged for debugging:**

| Metadata | Variable? | Logged? |
|----------|-----------|---------|
| Timestamps | ✅ YES | ✅ YES (for debugging) |
| Client hardware | ✅ YES | ✅ YES (for profiling) |
| Model versions | ✅ YES | ✅ YES (for campaign manifest) |
| Generation attempts | ✅ YES | ✅ YES (for critique gate) |

**Guarantee:** Metadata logged but NOT used for mechanical decisions.

---

## RNG Streams (Seeded Randomness)

### Required RNG Streams

AIDM MUST maintain **isolated RNG streams** to prevent accidental coupling:

| Stream | Purpose | Seed Source |
|--------|---------|-------------|
| `combat` | Attack rolls, damage rolls | Campaign seed + encounter ID |
| `initiative` | Initiative rolls | Campaign seed + combat start event |
| `saves` | Saving throws | Campaign seed + save event ID |
| `skill_checks` | Skill check rolls | Campaign seed + check event ID |
| `weather` | Environmental randomness | Campaign seed + day counter |

**Isolation Rule:** Streams MUST NOT share state (each stream has independent PRNG).

**Rationale:** If combat RNG and initiative RNG shared state, changing combat sequence would affect initiative order (non-deterministic).

---

### Seed Management

**Campaign Seed:**
```python
campaign_seed = sha256(f"{campaign_id}:{creation_timestamp}:{user_id}".encode()).hexdigest()
```

**Event-Specific Seed:**
```python
event_seed = sha256(f"{campaign_seed}:{stream_name}:{event_id}".encode()).hexdigest()
rng = random.Random(int(event_seed[:16], 16))  # 64-bit seed
```

**Determinism Guarantee:**
- Same campaign + same event → same seed → same RNG sequence

**Replay Protocol:**
- Replay reads event log, extracts event IDs
- Reconstructs RNG streams using same seeds
- Executes events → produces identical outcomes

---

### RNG Logging

**Every RNG draw MUST be logged:**

```python
{
    "event_id": "event_session_camp4f2a_0001_a3f2b8c4_000042_7d4e9a12",
    "stream": "combat",
    "seed": "f1c3d8a6e2b4...",
    "rolls": [15, 7, 19, 3],  # Sequence of rolls
    "purpose": "attack_roll"
}
```

**Rationale:**
- Debugging: "Why did this attack miss?" → Check roll value
- Audit: "Was this roll fair?" → Verify seed + roll sequence
- Replay verification: Re-execute → compare logged vs actual rolls

---

## Forbidden Sources of Non-Determinism

### FORBIDDEN: Unseed Random Sources

❌ **Python's `random.random()`** without seeding
❌ **NumPy's `np.random.rand()`** without fixed seed
❌ **System time** (`time.time()`, `datetime.now()`)
❌ **UUIDs** (`uuid.uuid4()`)
❌ **OS entropy** (`os.urandom()`)
❌ **Network requests** (API calls during resolution)
❌ **User input during resolution** (input MUST freeze before resolution)

**Violation Example:**
```python
# ❌ FORBIDDEN
def resolve_attack(attacker, target):
    roll = random.randint(1, 20)  # Unseeded random!
    return roll + attacker.attack_bonus >= target.ac
```

**Correct Example:**
```python
# ✅ ALLOWED
def resolve_attack(attacker, target, event_id, rng_stream):
    rng = get_seeded_rng('combat', event_id)
    roll = rng.randint(1, 20)
    log_roll(event_id, 'combat', roll)
    return roll + attacker.attack_bonus >= target.ac
```

---

### FORBIDDEN: Timestamps in Mechanical Logic

❌ **Using timestamps for mechanical decisions:**

```python
# ❌ FORBIDDEN
def apply_poison_damage(entity):
    now = datetime.now()
    if (now - entity.poison_applied_at).seconds > 60:
        entity.hp -= 1d6  # Damage depends on wall-clock time!
```

**Why Forbidden:** Replay at different time → different outcome.

**Correct Alternative (Turn-Based):**
```python
# ✅ ALLOWED
def apply_poison_damage(entity, current_turn):
    if current_turn - entity.poison_applied_turn >= 10:
        entity.hp -= roll_damage('1d6', event_id, rng_stream)
```

---

### FORBIDDEN: Floating-Point Drift

❌ **Using floats for distance/position calculations:**

```python
# ❌ FORBIDDEN
def distance(pos1, pos2):
    return math.sqrt((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2)
```

**Why Forbidden:** Floating-point rounding errors → non-deterministic at precision boundaries.

**Correct Alternative (Integer Math):**
```python
# ✅ ALLOWED (CP-001)
def distance_to(self, other: Position) -> int:
    """D&D 3.5e 1-2-1-2 diagonal distance (PHB p.148)."""
    dx = abs(self.x - other.x)
    dy = abs(self.y - other.y)
    diagonals = min(dx, dy)
    orthogonal = abs(dx - dy)
    diagonal_pairs = diagonals // 2
    remaining_diagonals = diagonals % 2
    return (diagonal_pairs * 15) + (remaining_diagonals * 5) + (orthogonal * 5)
```

**Verification:** CP-001 tests verify integer-only math (no float operations).

---

### ALLOWED: Presentation-Layer Variation

✅ **LLM sampling with temperature > 0:**

```python
# ✅ ALLOWED (presentation layer)
def narrate_attack(attack_result):
    prompt = f"Narrate: {attack_result.attacker} attacks {attack_result.target}"
    narration = llm.generate(prompt, temperature=0.7)  # Non-deterministic sampling OK
    return narration
```

**Why Allowed:** Narration is **presentation layer** (doesn't affect mechanics).

**Safeguard:** Engine MUST NOT read narration text to make decisions.

---

## Event Sourcing Contract

### All State Changes MUST Be Events

**RULE:** Engine state updates ONLY via event log append.

**Forbidden:**
```python
# ❌ FORBIDDEN (direct mutation)
entity.hp -= damage
```

**Required:**
```python
# ✅ REQUIRED (event-sourced)
event = DamageEvent(entity_id=entity.id, damage=damage, event_id=...)
event_log.append(event)
apply_event(entity, event)  # State updated by replaying event
```

**Determinism Guarantee:**
- Replay event log → reconstruct identical state
- Event log is append-only (no edits)
- Events contain all data needed to reproduce outcome

---

### Event Schema Requirements

**Every event MUST include:**

| Field | Type | Purpose |
|-------|------|---------|
| `event_id` | str | Unique event identifier (deterministic) |
| `event_type` | str | Event category (e.g., "damage", "move", "condition_applied") |
| `event_seq` | int | Sequential ordering within session |
| `timestamp` | str | ISO timestamp (metadata only, NOT used for logic) |
| `actor_id` | str | Entity performing action (if applicable) |
| `target_id` | str | Entity receiving action (if applicable) |
| `data` | dict | Event-specific data (roll results, HP changes, etc.) |
| `rng_seed` | str | RNG seed used for this event (if random) |

**Example:**
```json
{
    "event_id": "event_session_camp4f2a_0001_a3f2b8c4_000042_7d4e9a12",
    "event_type": "attack_resolved",
    "event_seq": 42,
    "timestamp": "2026-02-10T14:35:22Z",
    "actor_id": "entity_camp4f2a_fighter_a3f2b8c4e1d9",
    "target_id": "entity_camp4f2a_goblin1_7d4e9a12c5f3",
    "data": {
        "attack_roll": 15,
        "attack_bonus": 3,
        "total": 18,
        "target_ac": 14,
        "hit": true,
        "damage_roll": 7,
        "damage_bonus": 2,
        "total_damage": 9
    },
    "rng_seed": "f1c3d8a6e2b4a7c9d1e3f5b7c9d1e3f5"
}
```

---

## Determinism Verification Protocol

### Test Harness Requirements

**Every CP/milestone MUST include determinism tests:**

```python
def test_determinism_10x_replay():
    """Verify 10× replay produces identical outcomes."""
    # Setup: Create test campaign + event sequence
    campaign = create_test_campaign()
    intents = [
        AttackIntent(attacker="fighter", target="goblin"),
        MoveIntent(actor="fighter", from_pos=(0,0), to_pos=(1,0)),
    ]

    # Run 1: Execute intents, record outcomes
    event_log_1 = execute_intents(campaign, intents)
    outcomes_1 = extract_outcomes(event_log_1)  # HP, positions, conditions

    # Run 2-10: Replay from event log
    for i in range(2, 11):
        # Reset state
        campaign_reset = create_test_campaign()

        # Replay event log
        event_log_replay = replay_events(campaign_reset, event_log_1)
        outcomes_replay = extract_outcomes(event_log_replay)

        # Assert identical outcomes
        assert outcomes_replay == outcomes_1, f"Replay {i} differs from original!"
```

**Acceptance Criteria:**
- ✅ 10 replays produce identical outcomes
- ✅ Dice rolls match (same sequence)
- ✅ HP changes match
- ✅ Position changes match
- ✅ Condition applications match

---

### Replay Divergence Detection

**If replay diverges, log MUST identify where:**

```python
def detect_divergence(original_log, replay_log):
    """Find first event where replay diverges."""
    for i, (orig_event, replay_event) in enumerate(zip(original_log, replay_log)):
        if orig_event['data'] != replay_event['data']:
            return {
                "divergence_at_event": i,
                "original": orig_event,
                "replay": replay_event,
                "diff": compute_diff(orig_event, replay_event)
            }
    return None  # No divergence
```

**Example Divergence Report:**
```json
{
    "divergence_at_event": 42,
    "original": {"attack_roll": 15, "damage": 7},
    "replay": {"attack_roll": 15, "damage": 9},
    "diff": {"damage": {"original": 7, "replay": 9}}
}
```

---

## Asset Generation Determinism

### Critical Question: Are Generated Assets Deterministic?

**From GLOBAL-AUDIT-001 (DET-003 Risk):**
> If generation is seeded randomly, exporting and re-importing a campaign will produce DIFFERENT images for the same NPC.

**Decision Required:** Choose one strategy:

---

### Strategy A: Deterministic Generation (Ideal, High Risk)

**Approach:**
- Seed image/audio generation with canonical ID
- Same ID + same generation params → same asset

**Example:**
```python
seed = sha256(f"{asset_id}:{generation_params}".encode()).hexdigest()
image = generate_portrait(prompt, seed=int(seed[:16], 16))
```

**Pros:**
- ✅ True determinism (export doesn't need to bundle assets)
- ✅ Small export files
- ✅ Reproducible across machines

**Cons:**
- ❌ Requires deterministic generation models (NOT GUARANTEED)
- ❌ Model updates may change outputs (breaks determinism)
- ❌ Generation params must be exhaustively captured

**Verification Required:**
- Test: Generate asset 10× with same seed → identical pixels?
- Model: Does diffusion model support deterministic mode?

**Recommendation:** **HIGH RISK** until generation model determinism verified.

---

### Strategy B: Asset Export (Safe, Large Files)

**Approach:**
- Generate assets during prep
- Store generated assets in campaign export
- Import reconstructs campaign with bundled assets

**Example:**
```
campaign_export.zip
├── manifest.json
├── event_log.jsonl
├── assets/
│   ├── portrait_entity_camp4f2a_theron_a3f2.png
│   ├── scene_location_tavern_7d4e.png
│   └── audio_sfx_sword_clash_8b1c.wav
```

**Pros:**
- ✅ Guaranteed determinism (identical assets)
- ✅ No generation model dependency
- ✅ Works with any generation model (even non-deterministic)

**Cons:**
- ❌ Large export files (~500MB-2GB for 100 assets)
- ❌ Cannot regenerate if assets lost

**Recommendation:** **SAFE** — Use for M2 until Strategy A verified.

---

### Strategy C: Hybrid (Hash Verification)

**Approach:**
- Export asset manifests with content hashes
- On import, regenerate assets
- Verify regenerated asset hash matches manifest

**Example:**
```json
{
    "asset_id": "asset_camp4f2a_portrait_a3f2b8c4e1d9",
    "generation_params": {"prompt": "...", "seed": 12345},
    "content_hash": "sha256:f1c3d8a6..."
}
```

**On Import:**
```python
regenerated_asset = generate_portrait(params['prompt'], seed=params['seed'])
if sha256(regenerated_asset) != manifest['content_hash']:
    raise DeterminismViolation("Asset regeneration produced different output!")
```

**Pros:**
- ✅ Detects non-determinism (hash mismatch = alert)
- ✅ Smaller export files (no asset data)

**Cons:**
- ❌ Requires deterministic generation (same risk as Strategy A)
- ❌ Complex verification logic

**Recommendation:** **FUTURE** — Use after Strategy A determinism verified.

---

### Decision for M2

**REQUIRED (from ACTION_PLAN_REVISIONS.md):**
> M2 must choose determinism strategy (A, B, or C)

**Proposed Decision:** **Strategy B (Asset Export)** for M2
- Safe, guaranteed determinism
- Can migrate to Strategy A later if generation determinism proven

---

## Player Modeling Determinism

### Critical Question: Does Player Profile Affect Mechanics?

**From GLOBAL-AUDIT-001 (DET-002 Risk):**
> Player profile (experience level, pacing, tone preference) affects narration. If player profile changes between replays, narration differs. Is this a determinism violation?

**Answer:** **NO VIOLATION** if player profile stored in campaign metadata.

---

### Contract: Player Profile in Replay Inputs

**RULE:** Player profile MUST be serialized in campaign export.

**Export Schema:**
```json
{
    "campaign_id": "camp_4f2a8b1c",
    "player_profile": {
        "experience_level": "experienced",
        "pacing": "balanced",
        "explanation_depth": "explain_when_needed",
        "tone": "serious",
        "modality": "voice_first"
    },
    "event_log": [...]
}
```

**Determinism Guarantee:**
- Replay with **same player profile** → same narration style
- Replay with **different player profile** → different narration style (OK, presentation layer)

**Enforcement:**
- Player profile affects **presentation only** (tone, verbosity)
- Player profile CANNOT affect **mechanics** (dice, damage, legality)

**Verification:**
```python
def test_player_profile_affects_presentation_only():
    """Verify player profile changes narration, not mechanics."""
    # Run 1: Novice player profile
    profile_novice = PlayerProfile(experience_level="new", explanation_depth="teach_all")
    outcomes_novice = execute_with_profile(campaign, intents, profile_novice)

    # Run 2: Veteran player profile
    profile_veteran = PlayerProfile(experience_level="veteran", explanation_depth="no_explanations")
    outcomes_veteran = execute_with_profile(campaign, intents, profile_veteran)

    # Assert mechanics identical
    assert outcomes_novice.hp_changes == outcomes_veteran.hp_changes
    assert outcomes_novice.dice_rolls == outcomes_veteran.dice_rolls

    # Narration may differ (allowed)
    # assert outcomes_novice.narration != outcomes_veteran.narration  # May differ
```

---

## Determinism Threat Patterns (from Audit)

### Threat 1: Timestamp Leakage

**Pattern:** Using wall-clock time for mechanical decisions.

**Example:**
```python
# ❌ FORBIDDEN
if current_time - poison_time > 60:
    apply_damage()
```

**Mitigation:** Use **turn-based** logic instead.

---

### Threat 2: External API Calls

**Pattern:** Calling external services during resolution.

**Example:**
```python
# ❌ FORBIDDEN
def resolve_spell(spell_name):
    spell_data = requests.get(f"https://api.spells.com/{spell_name}").json()
    return apply_spell_effects(spell_data)
```

**Mitigation:** All spell data MUST be **bundled** (no network calls during resolution).

---

### Threat 3: File System Ordering

**Pattern:** Iterating files in arbitrary order.

**Example:**
```python
# ❌ FORBIDDEN
for asset_file in os.listdir("assets/"):
    load_asset(asset_file)  # Undefined order!
```

**Mitigation:** Sort file lists before iteration.

---

### Threat 4: Hash Map Iteration

**Pattern:** Iterating Python dicts (non-deterministic order pre-3.7).

**Example:**
```python
# ❌ FORBIDDEN (Python <3.7)
for entity_id, entity in entities.items():
    resolve_entity(entity)  # Undefined order!
```

**Mitigation:** Use **explicit ordering** (sort by entity_id).

---

## Determinism Checklist (for Implementers)

### Before Merging Code

- [ ] All RNG calls use seeded streams (no `random.random()` without seed)
- [ ] No timestamps in mechanical logic (use turn counters)
- [ ] No floating-point math in position/distance (use CP-001 integer math)
- [ ] All state changes via events (no direct mutations)
- [ ] Events include RNG seeds + roll results
- [ ] Player profile stored in campaign metadata
- [ ] Asset generation strategy chosen (A, B, or C)
- [ ] Determinism test added (10× replay verification)

---

## Exit Criteria

This spec is **ready for enforcement** when:

- [x] Determinism definition unambiguous
- [x] Layer boundaries documented (mechanical vs presentation vs metadata)
- [x] RNG stream isolation specified
- [x] Forbidden sources cataloged
- [x] Event sourcing contract defined
- [x] Verification protocol defined
- [x] Asset generation strategy specified
- [x] Player modeling determinism clarified
- [ ] Cross-agent review complete (Agent B, C, D feedback)
- [ ] PM approval obtained

---

## References

- **Constraint Source:** docs/analysis/GLOBAL_AUDIT_CONSTRAINT_LEDGER.md (Constraint A1)
- **Risk Source:** docs/analysis/GLOBAL_AUDIT_GAP_AND_RISK_REGISTER.md (DET-001 through DET-005)
- **CP-001 Verification:** aidm/schemas/position.py (integer math, no float drift)
- **Current Implementation:** 1393 tests include 10× replay verification

---

**STATUS:** Awaiting cross-agent review + PM approval before enforcement.

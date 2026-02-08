# AIDM — AI Dungeon Master for D&D 3.5e

A deterministic, reproducible AI referee system for Dungeons & Dragons 3.5 Edition.

## Overview

AIDM is an experimental engine for running D&D 3.5e sessions with deterministic outcomes. Every game session is fully reproducible from its event log, making debugging, testing, and validation tractable. The system enforces strict determinism through event sourcing, stream-isolated RNG, and stable hashing.

**No LLM dependency in deterministic runtime.** LLMs may be used in prep/narration layers as untrusted generators, gated by validators.

The project prioritizes **provenance and auditability**: every ruling can be traced back to specific source material pages (PHB, DMG, MM, etc.) through structured citations. This makes the AI's decisions transparent and verifiable against official rules.

## Design Principles

### 1. Determinism First
- All randomness uses hash-based seed derivation
- State mutations occur only through a single reducer function
- Serialization uses sorted keys for stable output
- Replay produces identical outcomes given the same event log

### 2. Event Sourcing
- Game state is derived from an append-only event log
- Events have monotonic IDs and structured payloads
- Log is stored as line-delimited JSON (JSONL) for git-friendly diffs

### 3. Provenance & Citations
- Every ruling can reference source material (sourceId + page)
- Citations are first-class objects in the event log
- Rule lookup returns page-level results with snippets

### 4. Fail-Closed Design
- Unknown intent types are rejected by legality checker
- Missing state fields cause explicit errors
- No silent fallbacks or assumptions

## Source Layer (sources/)

The `sources/` directory contains D&D 3.5e source materials organized for deterministic access:

```
sources/
├── provenance.json          # Master registry (647 sources)
├── meta/                    # Source metadata JSONs (647 files)
│   ├── 681f92bc94ff.json   # PHB metadata
│   ├── fed77f68501d.json   # DMG metadata
│   └── ...
├── text/                    # Extracted page text (core rulebooks)
│   ├── 681f92bc94ff/       # PHB pages
│   │   ├── 0001.txt
│   │   ├── 0002.txt
│   │   └── ... (322 pages)
│   ├── fed77f68501d/       # DMG pages (322 pages)
│   └── e390dfd9143f/       # MM pages (322 pages)
└── README.md
```

### Key Design Decisions

1. **Read-only at runtime**: Source materials are never modified during gameplay
2. **Page-level granularity**: Text is split by page for citation precision
3. **SourceId addressing**: 12-character hex IDs provide stable references
4. **Provenance tracking**: All sources have reuse decisions and validation metadata

## Citations & Provenance

Every event can include citations that reference specific source material:

```python
from aidm.schemas.citation import Citation

citation = Citation(
    source_id="681f92bc94ff",  # PHB
    short_name="PHB",
    page=157,
    span="Grapple rules"       # Optional context
)

# Human-readable format
print(citation)  # "PHB p. 157 (Grapple rules)"

# Serialize for event log
citation.to_dict()  # {'source_id': '681f92bc94ff', 'short_name': 'PHB', 'page': 157, 'span': 'Grapple rules'}
```

### Citation Fields

- `source_id`: 12-character hex sourceId (required)
- `short_name`: Human name like "PHB", "DMG", "MM" (optional)
- `page`: 1-indexed page number (optional)
- `span`: Section/table reference like "Table 8-2" (optional)
- `rule_id`: Structured identifier for future use (optional)
- `obsidian_uri`: Deep-link to vault notes (optional)

## Rule Lookup v0

Page-level rule retrieval from extracted source text:

```python
from aidm.core.rule_lookup import search
from aidm.core.source_registry import SourceRegistry

# Initialize registry
registry = SourceRegistry("sources/provenance.json")

# Search for grapple rules
results = search(
    query="grapple",
    source_ids=["681f92bc94ff"],  # PHB only
    k=5,                          # Top 5 results
    registry=registry
)

# Inspect results
for hit in results:
    print(f"{hit.short_name} p. {hit.page} (score: {hit.score})")
    print(f"  {hit.snippet[:100]}...")
    print()
```

### SearchHit Structure

Each result includes:
- `source_id`: Source identifier
- `short_name`: Human-readable name
- `page`: Page number (1-indexed)
- `snippet`: Text excerpt (≤ 300 chars)
- `score`: Relevance score (higher = better match)

### Default Behavior

- Searches core rulebooks (PHB, DMG, MM) if `source_ids` is None
- Case-insensitive matching
- Deterministic ordering for tie-breaking
- Returns empty list if no matches found

## Reading Source Pages

Direct access to extracted text:

```python
from aidm.core.source_registry import SourceRegistry

registry = SourceRegistry("sources/provenance.json")

# Read PHB page 10 (ability scores section)
page_text = registry.get_text_page("681f92bc94ff", 10)
print(page_text)

# Get source metadata
phb = registry.get_source("681f92bc94ff")
print(f"{phb['title']} — {phb['pages']} pages")

# List all core rulebooks
core_sources = registry.list_core_sources()
for source in core_sources:
    print(f"{source['short_name']}: {source['title']}")
```

## Creating Events with Citations

Programmatic example of attaching citations to events:

```python
from aidm.core.rule_lookup import search
from aidm.core.ruling_helpers import make_rule_lookup_event

# Search for rules
hits = search("fireball", k=3)

# Create event with citations
event = make_rule_lookup_event(
    query="fireball",
    hits=hits,
    event_id=42,
    timestamp=1.0
)

# Event structure
print(event.event_type)           # "rule_lookup"
print(event.payload["query"])     # "fireball"
print(len(event.citations))       # 3 (top results)
print(event.citations[0]["page"]) # Page number from first hit
```

## Project Structure

```
aidm/
├── core/
│   ├── event_log.py          # Event sourcing foundation
│   ├── rng_manager.py        # Deterministic RNG
│   ├── state.py              # WorldState with hashing
│   ├── replay_runner.py      # Deterministic replay
│   ├── source_registry.py    # Source material access
│   ├── rule_lookup.py        # Page-level search
│   ├── ruling_helpers.py     # Citation integration
│   ├── interaction.py        # Declare→Point→Confirm engine
│   ├── obsidian_links.py     # Obsidian URI helpers (optional)
│   ├── bundle_validator.py   # Session prep validation
│   └── doctrine_rules.py     # Tactical envelope derivation
├── rules/
│   └── legality_checker.py   # Fail-closed validation
└── schemas/
    ├── citation.py           # Citation schema
    ├── intents.py            # Voice intent contract
    ├── bundles.py            # Session prep bundles
    ├── doctrine.py           # Monster doctrine (tactical envelope)
    ├── visibility.py         # Visibility & lighting contracts
    ├── terrain.py            # Terrain & traversal contracts
    ├── policy_config.py      # Policy variety config
    ├── time.py               # Time scales, clocks, time advancement
    ├── timers.py             # Deadlines & timer status
    ├── durations.py          # Effect duration tracking
    ├── hazards.py            # Environmental hazards & progression
    └── exposure.py           # Exposure types & conditions

tests/
├── test_event_log.py
├── test_event_log_citations.py
├── test_rng_manager.py
├── test_state.py
├── test_replay_runner.py
├── test_legality_checker.py
├── test_source_registry.py
├── test_citation.py
├── test_rule_lookup.py
├── test_ruling_helpers.py
├── test_intents.py
├── test_interaction.py
├── test_obsidian_links.py
├── test_bundles.py
├── test_bundle_validator.py
├── test_doctrine.py
├── test_bundle_validator_doctrine.py
├── test_visibility.py
├── test_terrain.py
├── test_policy_config.py
├── test_time.py
├── test_timers.py
├── test_durations.py
├── test_bundle_validator_temporal.py
├── test_hazards.py
├── test_exposure.py
└── test_bundle_validator_hazards.py
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_rule_lookup.py

# Run specific test
pytest tests/test_rule_lookup.py::test_rule_lookup_basic_hit

# Show coverage
pytest --cov=aidm
```

All tests run in under 4 seconds (1331 tests total) and require no external dependencies beyond pytest and the source layer files.

## Development Workflow

### 1. Source Layer Setup

The source layer is already populated with:
- 647 source metadata files in `sources/meta/`
- 966 pages of extracted text for PHB, DMG, MM in `sources/text/`
- Master registry in `sources/provenance.json`

No additional setup needed unless adding new source materials.

### 2. Running Tests

```bash
# First time: install dependencies
pip install -r requirements.txt

# Run full test suite
pytest

# Expected output: 453 passed in ~1.5s
```

### 3. Adding New Rules

1. Add rule logic to appropriate module (e.g., `aidm/rules/`)
2. Update legality checker if needed
3. Write tests demonstrating behavior
4. Ensure deterministic replay still works

### 4. Working with Citations

When implementing new ruling logic:

```python
# Search for relevant rules
hits = search("keyword", k=3)

# Build citations
citations = [build_citation(hit).to_dict() for hit in hits]

# Attach to event
event = Event(
    event_id=next_id,
    event_type="ruling",
    timestamp=current_time,
    payload={"decision": "allowed", "reason": "..."},
    citations=citations
)
```

## Prep vs Play

AIDM separates **session prep** from **session play** to optimize for different workflows:

### Prep Phase (Async, Long-Running)
- Generate SessionBundles with scene cards, NPC stats, encounters
- Pre-load citations for likely rule references
- Validate asset availability (tokens, portraits, handouts)
- Output: ReadinessCertificate confirming bundle is ready

### Play Phase (Sync, Deterministic)
- Voice intents → Interaction engine → Event log
- All randomness via RNGManager
- Rule lookups use pre-validated sources
- Every session is fully reproducible from its event log

**Key Principle**: Prep can be slow and thorough. Play must be fast and deterministic.

Example workflow:
```python
from aidm.schemas.bundles import SessionBundle
from aidm.core.bundle_validator import validate_session_bundle

# Prep: Create session bundle (could take minutes/hours)
bundle = SessionBundle(
    id="session_001",
    campaign_id="campaign_alpha",
    session_number=1,
    created_at="2025-01-15T10:00:00Z",
    scene_cards=[...],  # Pre-generated scenes
    npc_cards=[...],    # Pre-rolled NPCs
    encounter_specs=[...],  # Pre-configured encounters
    citations=[...]     # Pre-loaded likely citations
)

# Validate readiness
cert = validate_session_bundle(bundle)
if cert.status == "blocked":
    print(f"Issues: {cert.notes}")
else:
    print("Ready to play!")
```

## Voice Intent Contract

AIDM defines a **structured intent API** for voice layer integration (ASR/NLU):

### Core Intents

1. **CastSpellIntent**: Cast a spell with targeting mode
2. **MoveIntent**: Move to a grid location
3. **AttackIntent**: Attack a target with a weapon
4. **BuyIntent**: Purchase items from a shop
5. **RestIntent**: Take a short or long rest

All intents are JSON-serializable dataclasses with deterministic validation.

Example:
```python
from aidm.schemas.intents import CastSpellIntent, parse_intent

# Voice layer produces structured intent
intent_data = {
    "type": "cast_spell",
    "spell_name": "Fireball",
    "target_mode": "point"
}

# Parse and validate
intent = parse_intent(intent_data)

# Check requirements
if intent.requires_point:
    print("UI must provide target point")
```

## Declare → Point → Confirm

AIDM models tabletop interaction as a **two-phase commit** pattern:

1. **Declare**: Voice layer declares intent
2. **Point** (optional): UI provides grid point or entity selection
3. **Confirm**: Event committed to log

This matches natural tabletop flow: *"I cast Fireball... [DM: where?] ...at that group of goblins."*

Example:
```python
from aidm.core.interaction import InteractionEngine
from aidm.schemas.intents import CastSpellIntent, GridPoint
from aidm.core.state import WorldState

engine = InteractionEngine()
world_state = WorldState(ruleset_version="3.5")

# 1. Declare: Voice says "I cast Fireball"
fireball = CastSpellIntent(spell_name="Fireball", target_mode="point")
state, pending, events = engine.start_intent(
    world_state=world_state,
    intent=fireball,
    next_event_id=0,
    timestamp=1.0
)

# pending.prompt = "Select target point for Fireball"
# pending.pending_kind = "point"

# 2. Point: UI provides grid selection
point = GridPoint(x=10, y=15)
state, events = engine.commit_point(
    world_state=state,
    pending_action=pending,
    point=point,
    next_event_id=1,
    timestamp=2.0
)

# 3. Confirm: Event emitted with spell_cast + target_point
assert events[0].event_type == "spell_cast"
assert events[0].payload["target_point"] == {"x": 10, "y": 15}
```

## Monster Tactical Envelope (Doctrine)

AIDM enforces **capability-based tactical constraints** for monsters through doctrine metadata. This is **NOT** mercy, sympathy, or fairness balancing - it's RAW-legal gating based on creature intelligence, wisdom, type, and Monster Manual behavior text.

### What It Is

- **Capability gating**: INT 1 creatures cannot execute flanking maneuvers
- **Behavior enforcement**: Fanatical creatures fight to the death, cowardly ones retreat
- **Citation-backed**: All doctrine entries for MM creatures require page references
- **Prep-time validation**: SessionBundles fail readiness if encounters lack doctrine

### What It Is NOT

- **Mercy caps**: No artificial limits on damage or lethality
- **Sympathy**: Monsters use their full capabilities within their envelope
- **Nerfing**: Low INT doesn't make monsters "weak" - it constrains tactical complexity

### Tactical Classes

Doctrine defines allowed/forbidden tactics based on INT/WIS bands:

- **Reflexive** (INT 1): `attack_nearest`, `random_target`
- **Opportunistic** (INT 3-7): `focus_fire`, `setup_flank` (if pack_hunter)
- **Tactical** (INT 8-13): `use_cover`, `retreat_regroup`, `target_support`
- **Advanced** (INT 14+): All tactics including `deny_actions_chain`, `bait_and_switch`

Tags override INT: `mindless_feeder` forbids all tactics except `attack_nearest`, regardless of score.

### Example

```python
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.core.doctrine_rules import derive_tactical_envelope

# Define goblin doctrine
goblin = MonsterDoctrine(
    monster_id="goblin",
    source="MM",
    int_score=10,
    wis_score=9,
    creature_type="humanoid",
    tags=["cowardly"],
    citations=[{"source_id": "e390dfd9143f", "page": 133}]
)

# Derive tactical envelope
goblin = derive_tactical_envelope(goblin)

# Cowardly tag enables retreat
assert "retreat_regroup" in goblin.allowed_tactics
assert "fight_to_the_death" in goblin.forbidden_tactics
```

### Prep Integration

SessionBundles require doctrine for all encounters (default):

```python
from aidm.schemas.bundles import SessionBundle, EncounterSpec
from aidm.core.bundle_validator import validate_session_bundle

encounter = EncounterSpec(
    encounter_id="goblin_ambush",
    name="Goblin Ambush",
    creatures=[{"type": "goblin", "count": 3}],
    monster_doctrines=[goblin]  # Required
)

bundle = SessionBundle(
    id="session_001",
    campaign_id="campaign_alpha",
    session_number=1,
    created_at="2025-01-15T10:00:00Z",
    encounter_specs=[encounter],
    doctrine_required=True  # Default
)

cert = validate_session_bundle(bundle)
# Fails if doctrine missing or invalid
```

## Time, Clocks, Deadlines, and Durations

AIDM provides **temporal contracts** for tracking game time, deadlines, and effect durations. These are **data-only schemas** - no simulation loop or combat resolver implementation yet.

### Game Clock

Campaign-global monotonic clock with time scale context:

```python
from aidm.schemas.time import GameClock, TimeSpan, TimeAdvanceEvent, ROUND, MINUTE

# Create initial clock
clock = GameClock(t_seconds=0, scale="combat_round")

# Time advancement
advance = TimeAdvanceEvent(
    delta=ROUND,  # 6 seconds
    reason="combat_round_passed",
    scale="combat_round"
)
```

### Deadlines and Timers

Time-sensitive events with consequences:

```python
from aidm.schemas.timers import Deadline, TimerStatus

# Define deadline
ritual = Deadline(
    id="ritual_completes",
    name="Dark Ritual Completes",
    due_at_t_seconds=1000,
    failure_consequence="Cultists summon demon",
    visibility="hinted",
    citations=[{"source_id": "e390dfd9143f", "page": 42}]
)

# Compute status at current time
status = TimerStatus.compute(current_t_seconds=500, deadline=ritual)
print(f"Remaining: {status.remaining_seconds}s, Expired: {status.is_expired}")
```

### Effect Durations

Spell/buff/debuff duration tracking:

```python
from aidm.schemas.durations import EffectDuration

# Spell with time-based duration
haste = EffectDuration(
    unit="rounds",
    value=10,
    start_t_seconds=100,
    citation={"source_id": "681f92bc94ff", "page": 239}
)

# Compute end time
end_time = EffectDuration.compute_end_time(
    start_t_seconds=100,
    unit="rounds",
    value=10
)  # Returns 160 (100 + 10*6)

# Permanent effect
magic_aura = EffectDuration(
    unit="permanent",
    value=None,
    start_t_seconds=0
)

# Until-discharged effect
shield = EffectDuration(
    unit="until_discharged",
    value=None,
    start_t_seconds=50
)
```

### Lighting Over Time

Ambient light schedules and expiring light sources:

```python
from aidm.schemas.visibility import AmbientLightSchedule, LightSource

# Day/night cycle
schedule = AmbientLightSchedule(entries=[
    (0, "bright"),      # Dawn
    (43200, "dim"),     # Dusk (12 hours)
    (86400, "dark")     # Night (24 hours)
])

# Torch with expiration
torch = LightSource(
    position={"x": 10, "y": 15},
    radius=20,
    light_level="bright",
    expires_at_t_seconds=3600  # Burns for 1 hour
)
```

### Bundle Integration

Temporal contracts integrate with SessionBundle:

```python
from aidm.schemas.bundles import SessionBundle, SceneCard

scene = SceneCard(
    scene_id="dungeon_1",
    title="Trapped Chamber",
    description="...",
    ambient_light_schedule=schedule  # Optional lighting schedule
)

bundle = SessionBundle(
    id="session_001",
    campaign_id="campaign_alpha",
    session_number=1,
    created_at="2025-01-15T10:00:00Z",
    initial_clock=GameClock(t_seconds=0, scale="narrative"),
    deadlines=[ritual],  # Time-sensitive events
    active_effects=[haste],  # Ongoing spell effects
    scene_cards=[scene]
)

# Validator checks temporal consistency
cert = validate_session_bundle(bundle)
# Blocks if deadline before clock, effect starts after clock, etc.
```

### Validation

Bundle validator enforces temporal invariants:
- Deadlines must be >= initial_clock time
- Active effect start times must be <= initial_clock time (ongoing effects)
- Effect end times must be >= start times
- Light schedules must have strictly increasing times

## Environmental Hazards & Exposure

AIDM provides **deterministic environmental hazard contracts** for fire, cold, smoke, suffocation, etc. These are **data-only schemas** with no resolution logic.

### Hazards

Time-indexed environmental hazards with escalation support:

```python
from aidm.schemas.hazards import EnvironmentalHazard, HazardProgression, HazardStage

# Basic hazard
forest_fire = EnvironmentalHazard(
    id="forest_fire",
    name="Forest Fire",
    interval_unit="round",
    interval_value=1,
    effect_type="damage",
    description="1d6 fire damage per round",
    visibility_tags=["light_obscurement"],
    citation={"source_id": "fed77f68501d", "page": 303}
)

# Escalating hazard with stages
suffocation = EnvironmentalHazard(
    id="suffocation",
    name="Suffocation",
    interval_unit="round",
    interval_value=1,
    effect_type="condition",
    description="Escalating suffocation",
    escalates=True,
    max_stages=3
)

progression = HazardProgression(
    hazard_id="suffocation",
    stages=[
        HazardStage(stage_index=0, notes="Holding breath"),
        HazardStage(stage_index=1, notes="Nonlethal damage begins"),
        HazardStage(stage_index=2, notes="Unconsciousness")
    ]
)
```

### Environmental Conditions

Exposure with mitigation tracking (descriptive only, no logic):

```python
from aidm.schemas.exposure import EnvironmentalCondition

condition = EnvironmentalCondition(
    type="cold",
    hazard_ref="extreme_cold",
    mitigation_sources=["cold weather gear", "endure elements spell"],
    notes="Arctic environment",
    citation={"source_id": "fed77f68501d", "page": 302}
)
```

### Bundle Integration

Hazards integrate with SceneCard:

```python
from aidm.schemas.bundles import SceneCard

scene = SceneCard(
    scene_id="burning_forest",
    title="Burning Forest",
    description="Forest ablaze",
    environmental_hazards=[forest_fire],
    environmental_conditions=[
        EnvironmentalCondition(type="heat", hazard_ref="forest_fire")
    ]
)

# Validator checks hazard ID uniqueness, hazard_ref validity, DMG citations
```

## Tactical Policy Engine

AIDM provides a **deterministic tactical policy engine** that selects tactics within MonsterDoctrine constraints. This is **policy-only**: it produces scored choices, does not apply effects, and never resolves combat.

### Core Concepts

- **Deterministic**: Same inputs → identical ranked list and selection
- **Integer scoring**: No floating point (basis points scale: 10000 = 100%)
- **RNG isolation**: Policy RNG stream never affects combat RNG
- **Fail-closed**: Missing actor returns `requires_clarification`
- **Doctrine-gated**: Only allowed tactics are scored
- **Full trace**: Complete audit trail of evaluation process

### Basic Usage

```python
from aidm.core.tactical_policy import evaluate_tactics
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.core.state import WorldState
from aidm.core.doctrine_rules import derive_tactical_envelope

# Create and derive doctrine
doctrine = MonsterDoctrine(
    monster_id="goblin",
    source="MM",
    int_score=10,
    wis_score=11,
    creature_type="humanoid"
)
doctrine = derive_tactical_envelope(doctrine)

# Create world state
world_state = WorldState(
    ruleset_version="3.5e",
    entities={
        "goblin_1": {
            "hp_current": 4,
            "hp_max": 6,
            "conditions": [],
            "position": {"x": 0, "y": 0},
            "team": "monsters"
        },
        "pc_1": {
            "position": {"x": 5, "y": 0},
            "team": "party"
        }
    }
)

# Evaluate tactics
result = evaluate_tactics(doctrine, world_state, "goblin_1")

print(result.status)  # "ok"
print(result.selected.candidate.tactic_class)  # e.g., "retreat_regroup"
print(result.selected.score)  # Integer score
print(result.selected.reasons)  # Scoring rationale
```

### Feature Extraction

The policy engine extracts features from WorldState:

- **HP bands**: healthy (≥75%), wounded (50-74%), bloodied (25-49%), critical (<25%)
- **Conditions**: stunned, prone, frightened, grappled
- **Nearby threats**: enemies in engagement (≤5ft), close range (≤30ft), medium range (≤60ft)
- **Nearby allies**: allies in engagement, close range

### Scoring Heuristics

Scoring uses integer math with penalties and bonuses:

- **Base score**: 1000 for all tactics
- **HP-based**: Retreat boosted for critical HP (+5000), bloodied HP (+2000)
- **Engagement pressure**: Cover boosted when outnumbered (+2000), retreat boosted (+1500)
- **Ally support**: Flank boosted with allies nearby (+1000)
- **Condition penalties**: Stunned (-9000), frightened aggressive tactics (-3000), grappled mobility (-4000), prone (-1000)

### Variety Selection

Optional variety mode uses policy RNG for non-greedy selection:

```python
from aidm.schemas.policy_config import PolicyVarietyConfig
from aidm.core.rng_manager import RNGManager

# Create policy config
policy_config = PolicyVarietyConfig(top_k=3, temperature=1.0)

# Get policy RNG stream (isolated from combat RNG)
rng_manager = RNGManager(master_seed=42)
policy_rng = rng_manager.stream("policy")

# Evaluate with variety
result = evaluate_tactics(
    doctrine,
    world_state,
    "goblin_1",
    policy_config=policy_config,
    policy_rng=policy_rng
)

# Selected from top-k candidates
print(result.trace.rng_draw)  # {"top_k": 3, "selected_index": 1, "method": "uniform_top_k"}
```

### Policy Result Schema

```python
from aidm.schemas.policy import TacticalPolicyResult

# Status values
result.status  # "ok" | "requires_clarification" | "no_legal_tactics"

# Ranked tactics (descending score)
for tactic in result.ranked:
    print(f"{tactic.candidate.tactic_class}: {tactic.score}")
    print(f"  Reasons: {tactic.reasons}")

# Selected tactic (if any)
if result.selected:
    print(f"Selected: {result.selected.candidate.tactic_class}")

# Trace (full evaluation audit trail)
trace = result.trace
print(f"Actor: {trace.actor_id}")
print(f"Features: {trace.extracted_features}")
print(f"Candidates: {trace.candidates_after_filtering}")
print(f"Rationale: {trace.final_selection_rationale}")

# Missing fields (if status=requires_clarification)
if result.status == "requires_clarification":
    print(f"Missing: {result.missing_fields}")
```

### Integration Notes

- **No resolution**: Policy engine does NOT apply damage, move tokens, or resolve attacks
- **No time advancement**: Policy evaluation is instant (no game clock changes)
- **No state mutation**: evaluate_tactics is a pure function
- **Ready for combat**: Next packet will wire policy into combat resolver

## Vertical Slice V1 — Runnable Execution Proof

AIDM includes a **minimal runnable demonstration** that proves the deterministic play loop architecture works end-to-end. This is **not a full combat system**, but an execution proof that wires together event sourcing, policy evaluation, and deterministic replay.

### What It Demonstrates

✅ **Deterministic execution**: Same inputs → identical output every time
✅ **Event sourcing**: All state changes flow through event log
✅ **Policy integration**: Monster tactical decisions driven by doctrine
✅ **Replay verification**: Event log replay produces identical final state
✅ **Bundle validation**: SessionBundle validated as "ready" before execution
✅ **Citation tracking**: All events linked to source material pages

### What It Does NOT Demonstrate

❌ **Combat resolution**: No damage calculation, no HP changes
❌ **Movement resolution**: No position updates, no traversal checks
❌ **Time advancement**: No clock changes, no effect expiration
❌ **Full mechanics**: This is an execution proof, not gameplay

### Running the Vertical Slice

```bash
# Execute the demonstration script
python scripts/vertical_slice_v1.py
```

**Output artifacts** (generated in `artifacts/` directory):
- `vertical_slice_v1.jsonl`: Complete event log (JSONL format)
- `vertical_slice_v1_transcript.txt`: Human-readable turn-by-turn summary

### Example Output

```
======================================================================
VERTICAL SLICE V1 — Deterministic Play Loop Execution Proof
======================================================================

[PHASE 1] Creating and validating SessionBundle...
  Goblin doctrine created (INT 10, WIS 11)
  Allowed tactics: attack_nearest, focus_fire, setup_flank, ...
  Bundle validation: ready
  [OK] Bundle validated successfully

[PHASE 2] Initializing world state...
  Entities: goblin_1, pc_fighter, pc_wizard
  Initial state hash: abb6f9cd64ec538e...

[PHASE 3] Executing 3-turn scenario...
  Events emitted: 9
  Final turn counter: 3
  Final state hash: 9f338195031e90ad...

[PHASE 4] Generating artifacts...
  [OK] Event log: artifacts\vertical_slice_v1.jsonl
  [OK] Transcript: artifacts\vertical_slice_v1_transcript.txt

[PHASE 5] Verifying deterministic replay...
  Original hash:  9f338195031e90ad...
  Replay hash:    9f338195031e90ad...
  [OK] Replay verification PASSED (hashes match)

======================================================================
VERTICAL SLICE V1 COMPLETE
======================================================================
```

### Scenario Details

- **Scene**: Forest Clearing
- **Entities**: 1 goblin (monster), 2 PCs (fighter, wizard)
- **Turns**: 3 total (goblin → PC → goblin)
- **Monster doctrine**: Goblin with INT 10, WIS 11, tactical envelope derived
- **Policy evaluation**: Deterministic tactic selection each goblin turn
- **PC actions**: Stub actions (no actual intent processing)

### Architecture Proof Points

1. **Bundle validation gates execution**: SessionBundle must validate as "ready" before play
2. **Monotonic event IDs**: Event IDs strictly increasing (0, 1, 2, ...)
3. **Citation provenance**: Every policy decision linked to MM goblin entry (p. 133)
4. **Deterministic replay**: Multiple executions produce identical final state hash
5. **Turn counter advancement**: World state tracks turn progression in `active_combat`

### Integration with Existing Systems

The vertical slice demonstrates integration between:
- **SessionBundle** (prep phase)
- **MonsterDoctrine** (tactical envelope)
- **Policy engine** (`evaluate_tactics`)
- **Event log** (append-only JSONL)
- **WorldState** (deterministic hashing)
- **Bundle validator** (fail-closed readiness checks)

### Troubleshooting

**Bundle validation fails**: Check that `monster_doctrines_by_id` dict is populated with doctrine for each monster type.

**Event IDs not monotonic**: Ensure `next_event_id` parameter increments correctly in `execute_turn`.

**Replay hash mismatch**: Verify that WorldState entities dict is deep-copied, not referenced.

**Citation format errors**: Ensure citation dicts have `source_id` (12-char hex) and `page` (int) fields.

## Campaign Memory & Character Evidence Ledger

AIDM provides **deterministic campaign memory contracts** for session summaries, character behavioral evidence, and mystery investigation tracking. These are **data-only schemas** with no alignment scoring or divine logic.

### Core Concepts

- **Descriptive only**: Evidence types describe actions, not alignment or morality
- **Write-once**: Session ledger entries are immutable records
- **Deterministic ordering**: Evidence and clues sorted for stable serialization
- **Fail-closed**: Unknown evidence types, alignment tags, and statuses rejected
- **No evaluation**: No alignment scoring, no divine favor/disfavor calculations

### Session Ledger

High-level session summaries with fact tracking:

```python
from aidm.schemas.campaign_memory import SessionLedgerEntry

session_entry = SessionLedgerEntry(
    session_id="session_001",
    campaign_id="campaign_alpha",
    session_number=1,
    created_at="2025-01-15T10:00:00Z",
    summary="Party explored ancient ruins, defeated goblin warband",
    facts_added=[
        "Found map to hidden temple",
        "Learned about cult of Vecna"
    ],
    state_changes=[
        "Wizard gained level 3",
        "Cleric learned remove curse"
    ],
    event_id_range=(0, 42),
    citations=[{"source_id": "681f92bc94ff", "page": 157}]
)
```

### Character Evidence

Behavioral evidence tracking (descriptive, not evaluative):

```python
from aidm.schemas.campaign_memory import CharacterEvidenceEntry

# Evidence types: harm_inflicted, harm_prevented, mercy_shown, betrayal,
# loyalty, theft, deception, obedience_authority, defiance_authority,
# self_sacrifice, self_interest, respect_life, disregard_life,
# promise_made, promise_broken

evidence = CharacterEvidenceEntry(
    id="evidence_001",
    character_id="paladin_1",
    session_id="session_001",
    evidence_type="mercy_shown",
    description="Spared defeated bandit chief, offered redemption",
    event_id=25,
    targets=["bandit_chief_1"],
    location_ref="forest_clearing",
    faction_ref="bandits",
    deity_ref="heironeous",
    alignment_axis_tags=["lawful", "good"],
    citations=[{"source_id": "681f92bc94ff", "page": 104}]
)
```

### Evidence Ledger

Campaign-wide evidence collection with deterministic ordering:

```python
from aidm.schemas.campaign_memory import EvidenceLedger

ledger = EvidenceLedger(
    campaign_id="campaign_alpha",
    entries=[evidence1, evidence2, evidence3]
    # Automatically sorted by (character_id, session_id, id)
)

# Deterministic serialization
data = ledger.to_dict()
```

### Mystery Investigation Tracking

Clue cards for tracking campaign mysteries:

```python
from aidm.schemas.campaign_memory import ClueCard, ThreadRegistry

clue = ClueCard(
    id="clue_001",
    session_id="session_001",
    discovered_by=["wizard_1", "rogue_1"],
    description="Ancient rune matching symbol from temple",
    status="partial",
    links=["clue_002", "npc_villain_1", "location_temple"],
    citations=[{"source_id": "fed77f68501d", "page": 42}]
)

registry = ThreadRegistry(
    campaign_id="campaign_alpha",
    clues=[clue1, clue2, clue3]
    # Automatically sorted by id
)
```

### Campaign Bundle Integration

All campaign memory integrates with CampaignBundle:

```python
from aidm.schemas.bundles import CampaignBundle

bundle = CampaignBundle(
    id="campaign_alpha",
    title="Rise of the Cult",
    created_at="2025-01-15T10:00:00Z",
    session_ledger=[session_entry1, session_entry2],
    evidence_ledger=ledger,
    thread_registry=registry
)

# Validate campaign bundle
from aidm.core.bundle_validator import validate_campaign_bundle

cert = validate_campaign_bundle(bundle)
print(cert.status)  # "ready" or "blocked"
print(cert.notes)   # Validation errors if any
```

### Validation Rules

Campaign bundle validator enforces fail-closed validation:

- **Unique IDs**: Session IDs, evidence IDs, and clue IDs must be unique
- **Session references**: Evidence and clues must reference valid session IDs (if ledger present)
- **Event ID ranges**: Evidence event_id must be within declared session event_id_range
- **Enum validation**: Unknown evidence types, alignment tags, or clue statuses rejected

### Integration Notes

- **No alignment scoring**: Evidence is descriptive only, no automatic alignment drift
- **No divine consequences**: No favor/disfavor calculations, no divine intervention logic
- **Ready for future**: Structure supports later alignment evaluation and divine consequence packets

## Rulings & Conflicts Record

AIDM provides **data-only schemas** for tracking rules questions, conflicts, and resolutions. These are **schema-only contracts** with no rule interpretation or resolution engine.

### Core Concepts

- **Descriptive only**: Records what questions arose and how they were resolved
- **No interpretation logic**: No rule engine, no automatic resolution
- **Citation-backed**: All rulings reference source material
- **Deterministic serialization**: Stable ordering of citations

### Rules Questions

Track rules questions that arise during gameplay:

```python
from aidm.schemas.rulings_conflicts import RulesQuestion

question = RulesQuestion(
    question_text="Does grapple provoke attack of opportunity?",
    context_refs=["goblin_1", "pc_fighter", "event_42"],
    citations=[{"source_id": "681f92bc94ff", "page": 156}]
)
```

### Ruling Conflicts

Detect and record conflicts between rules or interpretations:

```python
from aidm.schemas.rulings_conflicts import RulingConflict

conflict = RulingConflict(
    question=question,
    conflict_notes="PHB p.171 says yes, DMG p.82 says no (errata conflict)",
    conflicting_citations=[
        {"source_id": "681f92bc94ff", "page": 171},
        {"source_id": "fed77f68501d", "page": 82}
    ]
)
```

### Ruling Decisions

Record resolutions with precedence rationale:

```python
from aidm.schemas.rulings_conflicts import RulingDecision

decision = RulingDecision(
    resolution_text="Grapple does provoke AOO per PHB p.156 (core rule takes precedence)",
    precedence_rationale="PHB is primary source for combat rules; DMG errata not applicable",
    citations_used=[
        {"source_id": "681f92bc94ff", "page": 156},
        {"source_id": "fed77f68501d", "page": 82}
    ],
    timestamp="2025-01-15T10:00:00Z",
    event_link=42
)

# Citations automatically sorted by (source_id, page)
data = decision.to_dict()
```

### Integration Notes

- **No resolution engine**: Rulings are recorded, not computed
- **Human DM or prep LLM**: Rulings created during prep or by DM during play
- **Audit trail**: All rulings traceable to source material and game events
- **Future-ready**: Structure supports automated ruling suggestion in future packets

## Constraints & Limitations

### Current Scope

- **Page-level retrieval only**: No rule atomization or semantic chunking
- **Simple keyword search**: Token counting, no embeddings or ranking models
- **Core rulebooks only**: PHB, DMG, MM (966 pages total)
- **No LLM dependency in runtime**: All gameplay logic is deterministic and programmatic (LLMs allowed in prep/narration as untrusted generators)
- **No Obsidian runtime dependency**: URIs are generated but Obsidian not required
- **Voice intent schemas only**: No actual ASR/NLU integration yet
- **No UI implementation**: Interaction engine provides contracts only

### Non-Goals

- **Real-time gameplay**: System optimizes for correctness over speed
- **NLP/semantic search**: Current search is keyword-based
- **Rule interpretation**: System retrieves text but doesn't parse/interpret rules
- **Campaign planning UI/workflows**: No campaign planning UI; campaign continuity records (session ledger, evidence, threads) are allowed
- **Production ASR/TTS**: Voice layer is defined as structured intents only

## Future Work

- LLM-based prep pipeline (scene generation, NPC creation)
- Semantic search with embeddings for rule lookup
- Actual voice integration (ASR → intent parser)
- UI implementation (grid, token display, point selection)
- Rule atom extraction (structured rule database)
- Obsidian sync for session notes and campaign wiki
- Additional source materials (15 more extracted sources available)
- Performance optimization for large event logs

## License

This project contains no copyrighted game text. All extracted content is for personal use only. See `sources/README.md` and `REUSE_DECISION.json` for detailed provenance information.

## Contributing

This is an experimental research project. Core design principles:

1. Maintain determinism at all costs
2. Every mutation goes through the event log
3. All rulings must support citations
4. Tests must run in < 2 seconds
5. No silent failures (fail-closed design)

Before adding features, ensure they align with the deterministic, auditable design philosophy.

## Project Coordination & Instruction Packets

This project is developed through **numbered instruction packets** (CP-XX) to maintain coordination across long timescales and agent handoffs.

### Key Documents

- **PROJECT_STATE_DIGEST.md**: Canonical state snapshot (single source of truth)
  - Updated at the end of every instruction packet
  - Factual only - no discussion, no design speculation
  - Paste this file to refresh any agent completely

- **PROJECT_COHERENCE_DOCTRINE.md**: Project governance and scope boundaries
  - Defines canonical scope (LLM usage, campaign continuity, test runtime)
  - Locks architectural constraints and design principles
  - Deviation protocol for scope changes

- **VERTICAL_SLICE_V1.md**: Minimal runnable session milestone
  - 1 scene, 1 monster with doctrine, 2 PCs, 3 turns
  - Proves event sourcing, deterministic replay, tactical policy integration
  - Definition of done for first end-to-end gameplay slice

- **README.md** (this file): User-facing documentation and usage examples

### Completion Protocol

Every instruction packet must include a completion summary with:
1. Packet ID (CP-XX)
2. Tasks completed
3. Files changed (new/modified modules and tests)
4. Tests affected (count change)
5. Exact PSD update block for PROJECT_STATE_DIGEST.md

### Instruction Packet History

- **Tasks 0-5**: Foundation (RNG, EventLog, WorldState, ReplayRunner, LegalityChecker)
- **Tasks 9-13**: Voice-First Tabletop Contracts (Intents, Interaction, Bundles)
- **Tasks 14-17**: Monster Tactical Envelope (Doctrine schemas, tactical gating)
- **Tasks 18-22**: Visibility, Terrain, Policy Config (data-only contracts)
- **CP-00**: Project State Anchoring (this coordination system)
- **CP-05**: Time, Clocks, Deadlines, Durations (temporal contracts, 89 new tests)
- **CP-06**: Environmental Hazards & Exposure (hazard schemas, 50 new tests)
- **CP-07**: Tactical Policy Engine (deterministic tactic selection, 47 new tests)
- **CP-08**: Campaign Memory & Character Evidence Ledger (behavioral tracking, 50 new tests)
- **CP-07D**: Coherence Fixes + Vertical Slice Plan + Rulings Record (governance docs, 13 new tests)
- **CP-09**: Vertical Slice V1 — Play Loop Integration (execution proof, 5 integration tests)
- **CP-10**: Attack Resolution Proof (single attack with RAW mechanics, 16 tests)
- **CP-11**: Full Attack Sequence Proof (iterative attacks, critical hits, 16 tests)
- **CP-12**: Play Loop Combat Integration (combat intent routing, validation, 13 integration tests)
- **CP-13**: Monster Combat Integration (policy → intent mapping, 9 integration tests)
- **CP-14**: Initiative & Action Economy Kernel (initiative rolls, round progression, flat-footed, 11 integration tests)
- **CP-15**: Attacks of Opportunity (AoO) Kernel (interrupt system, movement provocation, action abortion, 6 integration tests)
- **CP-16**: Conditions & Status Effects Kernel (metadata-only modifiers, attack/AC/damage integration, 14 integration tests)

All work follows the **data-only schemas first** pattern: define contracts and validation before implementing algorithms.


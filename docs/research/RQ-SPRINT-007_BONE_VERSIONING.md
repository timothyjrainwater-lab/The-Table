# RQ-SPRINT-007: Bone-Layer Versioning — Patch Management for Living Worlds

**Status:** COMPLETE
**Date:** 2026-02-14
**Author:** Research Agent (Opus 4.6)
**Sprint:** Bone-Layer Verification Sprint
**Predecessors:** BONE_LAYER_CHECKLIST.md (all 9 domains COMPLETE), WRONG_VERDICTS_MASTER.md (30 bugs catalogued)
**Audience:** PM, PO, Builder agents

---

## Core Question

> When the bones change, what happens to the worlds built on top of them?

The bone layer is the deterministic rules engine: resolvers, reducers, state containers, event schemas, and the replay runner. Every campaign, every saved session, every frozen world bundle depends on these bones behaving exactly as they did when the campaign was created.

We just finished verifying 338 formulas across 39 files and found 30 bugs. Fixing those bugs means changing the bones. This document asks: what infrastructure exists today to manage that change safely, and what infrastructure is missing?

---

## Answer

**It depends entirely on what kind of change — and today, the system has ZERO version-tracking infrastructure.**

Here is the complete audit:

| Component | Version Field | Current Value | Validated on Load? | Checked Against Engine? |
|-----------|--------------|---------------|-------------------|------------------------|
| `pyproject.toml` | `version` | `"0.1.0"` | N/A (package metadata) | N/A |
| `WorldState.ruleset_version` | `ruleset_version` | `"RAW_3.5"` (convention) | Never validated | Never compared to engine |
| `CampaignManifest.engine_version` | `engine_version` | `"0.1.0"` (default) | Never checked on load | Never compared to running engine |
| `Event` | (none) | No schema version field | N/A | N/A |
| `EventLog` | (none) | No metadata header | N/A | N/A |
| `replay_runner.run()` | (none) | No version check | N/A | N/A |

**No compatibility gate exists anywhere.** A campaign created under engine 0.1.0 will load silently under engine 0.2.0, 1.0.0, or 47.0.0 with zero warnings. If the reducer logic changed between versions, replay will silently produce different state hashes — and the user will have no idea why their save "corrupted."

---

## 1. Current Versioning State — Full Audit

### 1.1 pyproject.toml

```toml
# f:\DnD-3.5\pyproject.toml
[project]
name = "aidm"
version = "0.1.0"
```

This is the Python package version. It exists for `pip install` and metadata purposes. It is not read by any game-loading code. It is not embedded in save files. It is the closest thing to a "source of truth" for the engine version, but nothing references it at runtime.

### 1.2 WorldState (aidm/core/state.py)

```python
@dataclass
class WorldState:
    ruleset_version: str          # e.g., "RAW_3.5"
    entities: Dict[str, Any]
    active_combat: Optional[Dict[str, Any]] = None
```

`ruleset_version` tracks which **ruleset** the world uses (e.g., "RAW_3.5" vs. a hypothetical "PATHFINDER_1E"). It does NOT track which version of the **engine** processed those rules. There is no `bone_engine_version` or `schema_version` field.

The `state_hash()` method (BL-011) includes `ruleset_version` in the hash, so changing it would break replay verification. But nothing prevents loading a "RAW_3.5" world into an engine that has changed how "RAW_3.5" rules are computed.

### 1.3 CampaignManifest (aidm/schemas/campaign.py)

```python
@dataclass
class CampaignManifest:
    campaign_id: str
    engine_version: str = "0.1.0"       # Exists!
    config_schema_version: str = "1.0"   # Exists!
    # ...
```

`engine_version` is set to `"0.1.0"` by default. It is serialized to disk via `to_dict()` and deserialized via `from_dict()`. It is validated in `__post_init__()` only for non-emptiness (`if not self.engine_version: raise ValueError`).

**It is never compared to the running engine version on load.** The `from_dict()` method will happily load a manifest with `engine_version: "99.0.0"` and proceed without warning.

`config_schema_version` exists for the SessionZeroConfig schema, but is similarly never validated against any expected version.

### 1.4 Event (aidm/core/event_log.py)

```python
@dataclass
class Event:
    event_id: int
    event_type: str
    timestamp: float
    payload: Dict[str, Any]
    rng_offset: int = 0
    citations: List[Dict[str, Any]] = field(default_factory=list)
```

No `schema_version` field. No `engine_version` field. No way to know which version of the engine produced a given event. If the payload structure changes between versions (e.g., `hp_changed` gains a new required field), old events will fail silently or produce wrong results when replayed under the new engine.

### 1.5 EventLog (aidm/core/event_log.py)

```python
class EventLog:
    def __init__(self):
        self._events: List[Event] = []
        self._next_id: int = 0
```

No metadata header. The JSONL file is pure events, one per line. There is no preamble line recording engine version, schema version, or creation timestamp. `from_jsonl()` reads lines and constructs Events — no version check.

### 1.6 Replay Runner (aidm/core/replay_runner.py)

```python
def run(
    initial_state: WorldState,
    master_seed: int,
    event_log: EventLog,
    expected_final_hash: str = None,
) -> ReplayReport:
```

No version parameter. No version check. The function takes a WorldState and an EventLog and assumes they are compatible with the current `reduce_event()` implementation. If reducer logic changed between the version that created the events and the version now replaying them, the final hash will silently diverge.

The hash mismatch will be detected IF `expected_final_hash` is provided — but the error message says "Hash mismatch" with no mention of possible version skew. The user gets a cryptic hex string comparison, not "this campaign was created with engine 0.1.0 but you are running 0.2.0."

### 1.7 Existing Safety Properties (What We DO Have)

Despite zero version tracking, the bone layer has strong safety properties that limit blast radius:

| Property | Boundary Law | What It Protects |
|----------|-------------|-----------------|
| Deterministic hashing | BL-011 | Identical state always produces identical hash; hash divergence is detectable |
| Immutable event log | BL-008 | Events cannot be retroactively altered; monotonic IDs enforce ordering |
| Frozen world bundles | WORLD_COMPILER contract | World truth is frozen at compile; runtime cannot rewrite it |
| Deep copy on reduce | BL-012 | `reduce_event()` deep-copies state before mutation; no aliasing bugs |
| Immutable view boundary | BL-020 | Non-engine code cannot mutate WorldState; only engine modules construct new instances |

These properties mean that version mismatches are **detectable** (hash divergence) even if they are not **preventable** (no load-time gate). This is a strong foundation to build on.

---

## 2. Change Classification Framework

Not all bone-layer changes are equal. A bug fix that corrects two-handed STR damage (BUG-1) is fundamentally different from a schema change that adds a required field to Event. We classify changes into three types:

### Type A: Backward-Compatible Bug Fixes

**Definition:** Same inputs, better outputs. The old behavior was WRONG per the SRD. The new behavior is CORRECT per the SRD. No schema changes. No new fields. No removed fields.

**Characteristics:**
- Resolver logic changes (e.g., `str_mod` becomes `int(str_mod * 1.5)` for two-handed)
- Constant value corrections (e.g., `max(0, ...)` becomes `max(1, ...)` for minimum damage)
- Conditional branch additions (e.g., adding melee/ranged differentiation for prone AC)
- Event payloads contain the same fields with corrected values

**All 30 WRONG verdicts from the bone-layer verification are Type A changes.** They fix incorrect formula implementations against the SRD. Specific examples from WRONG_VERDICTS_MASTER.md:

| Bug | Fix | Why Type A |
|-----|-----|-----------|
| BUG-1 | Two-handed STR multiplier 1.0x -> 1.5x | Same `damage_applied` event schema, different `damage` value |
| BUG-3 | Prone AC differentiated melee/ranged | Same `condition_applied` event schema, different AC computation |
| BUG-8/9 | Minimum damage 0 -> 1 | Same `damage_applied` event schema, different floor value |
| B-BUG-2 | Bull rush opposed check fix | Same `opposed_check` event schema, corrected modifier |
| E-BUG-02 | Diagonal movement cost | Same `move` event schema, corrected distance |

**Impact on existing saves:** Events recorded under the old engine contain the old (wrong) results. These results are baked into the event payloads. Replaying old events under the new engine will produce identical state, because `reduce_event()` reads the payload values (e.g., `damage=10`), not the formulas that computed them. The hash will match. The save is safe.

**Impact on NEW sessions in existing campaigns:** New combats will use corrected formulas. The campaign will have a seam: sessions 1-5 used the old (wrong) rules, sessions 6+ use the corrected rules. This is cosmetically imperfect but mechanically safe — no crashes, no data loss, no hash divergence.

### Type B: Behavior-Changing Patches

**Definition:** Same inputs, different outputs BY DESIGN. Not a bug fix — a deliberate rules interpretation change or house-rule application. The old behavior was one valid interpretation; the new behavior is a different valid interpretation.

**Hypothetical examples (none exist today, but will arise):**

| Change | Old Behavior | New Behavior | Why Type B |
|--------|-------------|-------------|-----------|
| Opposed check tie rule | Tie goes to defender | Tie goes to attacker | Both are valid interpretations; SRD is ambiguous |
| Sneak attack dice change | 1d6 per 2 levels | 1d6 per level | House rule amendment |
| Critical confirmation | Auto-confirm on natural 20 | Must confirm all crits | Variant rule toggle |
| Initiative tie-breaking | Higher DEX wins | Simultaneous action | Variant rule toggle |

**Impact on existing saves:** Same as Type A for replay (events contain results, not formulas). But the INTENT is different: Type A corrects a bug everyone would want fixed; Type B changes behavior that some campaigns may depend on. A campaign designed around "ties go to defender" should not silently switch to "ties go to attacker."

**This is where version safety becomes critical.** Type B changes require explicit opt-in.

### Type C: Schema-Breaking Changes

**Definition:** New required fields on existing dataclasses, removed fields, type changes, structural reorganization. Old serialized data cannot be deserialized by the new code without a migration step.

**Hypothetical examples:**

| Change | What Breaks |
|--------|------------|
| Add required `schema_version` to Event | All existing JSONL files fail `Event.from_dict()` |
| Rename `hp_changed` to `hit_points_modified` | `reduce_event()` treats old events as unknown (silent no-op) |
| Change `payload: Dict[str, Any]` to typed payload classes | `Event.from_dict()` crashes on old data |
| Add required `bone_engine_version` to WorldState | `WorldState.from_dict()` crashes on old saves |
| Remove `rng_offset` from Event | Old events with `rng_offset` pass extra kwarg to constructor |

**Impact on existing saves:** Crashes. Silent data loss. Undefined behavior. Type C changes are the most dangerous and require the most infrastructure.

### Decision Tree for Change Classification

```
Is this a new required field, removed field, or type change on a
serialized dataclass (WorldState, Event, CampaignManifest)?
  |
  YES --> TYPE C (schema-breaking)
  |
  NO --> Does this change the output of a resolver/reducer for
         inputs that were previously handled correctly?
           |
           YES --> Was the old behavior WRONG per the SRD/RAW?
                     |
                     YES --> TYPE A (backward-compatible bug fix)
                     |
                     NO --> TYPE B (behavior-changing patch)
           |
           NO --> Not a bone-layer change (cosmetic, docs, test-only, etc.)
```

---

## 3. Migration Paths

### Type A: Warn and Allow Load

**Protocol:**
1. On campaign load, compare `CampaignManifest.engine_version` to running engine version.
2. If the running engine is newer and the diff contains only Type A changes (per the changelog), emit a WARNING log:
   ```
   WARN: Campaign "Ruins of Khelm" was created with engine 0.1.0.
   Running engine is 0.1.1 (PATCH: bug fixes only).
   All fixes are Type A (backward-compatible). Loading normally.
   Old sessions retain original (pre-fix) results.
   New sessions will use corrected formulas.
   ```
3. Allow load to proceed. Update `CampaignManifest.engine_version` to the new version (append-only amendment, not in-place overwrite, per SessionZeroConfig precedent).
4. Stamp new events with the new engine version (once Event gains a version field).

**Rationale:** Type A fixes correct SRD violations. No reasonable user would prefer the broken behavior. The seam between old and new sessions is cosmetically imperfect but mechanically safe.

### Type B: HARD STOP With Options

**Protocol:**
1. On campaign load, compare `CampaignManifest.engine_version` to running engine version.
2. If the running engine is newer and the diff contains Type B changes, emit a HARD STOP:
   ```
   STOP: Campaign "Ruins of Khelm" was created with engine 0.1.0.
   Running engine is 0.2.0 (MINOR: behavior changes).

   Changed behaviors:
     - Opposed check tie rule: defender-wins -> attacker-wins
     - Sneak attack dice: 1d6/2lvl -> 1d6/lvl

   Options:
     [A] ARCHIVE — Keep campaign frozen at 0.1.0 (read-only, no new sessions)
     [R] RESTART — Start a new campaign under 0.2.0 rules
     [M] MIGRATE — Apply new rules going forward (seam between old/new sessions)
     [D] DOWNGRADE — Run this session with 0.1.0 behavior (if engine supports it)
   ```
3. Do not proceed until the user makes an explicit choice.
4. If MIGRATE: append an amendment to SessionZeroConfig recording the version bump and which behavior changes were accepted.
5. If ARCHIVE: mark campaign as read-only. Allow replay and viewing but block new session creation.
6. If DOWNGRADE: this requires versioned resolver dispatch (future infrastructure). For now, DOWNGRADE is not available.

**Rationale:** Type B changes alter intended game behavior. The user may have designed encounters, balanced treasure, or made story decisions based on the old behavior. Silent migration could break campaign integrity in ways that are invisible until mid-session.

### Type C: HARD STOP — World Recompile Required

**Protocol:**
1. On campaign load, detect schema incompatibility (deserialization failure, missing required fields, type errors).
2. Emit a HARD STOP:
   ```
   STOP: Campaign "Ruins of Khelm" uses event schema v1.
   Running engine requires event schema v2.

   This campaign cannot be loaded without migration.

   Options:
     [A] ARCHIVE — Keep campaign frozen (read-only under bundled v1 reader)
     [R] RECOMPILE — Run migration tool to upgrade schemas
                     WARNING: This is a one-way operation. Back up first.
   ```
3. If RECOMPILE: run a migration script that transforms old data structures to new ones. This must be a dedicated, tested migration tool — not ad-hoc code.
4. After migration, update all version stamps and recompute hashes.

**Rationale:** Type C changes mean the old data literally cannot be read by the new code. There is no "warn and continue" option. Either migrate the data or preserve it in amber.

---

## 4. Save State Continuity

### 4.1 Why Type A Fixes Do NOT Retroactively Alter Replay

This is the most important insight in this document. Understanding it requires understanding how `reduce_event()` works.

**Events record RESULTS, not FORMULAS.**

When the attack resolver computes damage, it emits an event like:

```python
Event(
    event_id=42,
    event_type="damage_applied",
    payload={"entity_id": "goblin_1", "damage": 10, "source": "longsword"}
)
```

The `damage: 10` is a concrete result. It does not contain the formula `str_mod * grip_multiplier + weapon_base`. The reducer reads this event and applies it:

```python
# From replay_runner.py, reduce_event():
elif event_type == "damage_applied":
    entity_id = payload.get("entity_id")
    damage = payload.get("damage", 0)
    if entity_id and entity_id in new_state.entities:
        current_hp = new_state.entities[entity_id].get("hp", 0)
        new_state.entities[entity_id]["hp"] = max(0, current_hp - damage)
```

The reducer trusts the event payload. It applies `damage=10` regardless of whether the current engine would compute 10 or 15 for that attack. The formula that produced 10 is gone — only the result survives in the event log.

**Therefore:** Fixing BUG-1 (two-handed STR 1.5x) changes how FUTURE damage is computed. It does NOT change how PAST damage is replayed. Old events with `damage: 10` will still replay as `damage: 10`. The hash will still match.

### 4.2 The Frankenstein State Problem (Type B)

If a Type B change is applied mid-campaign via MIGRATE, the campaign enters a "Frankenstein state":

```
Sessions 1-5:  Old resolver behavior  ->  Events with old results
--- VERSION BUMP (0.1.0 -> 0.2.0) ---
Sessions 6-10: New resolver behavior  ->  Events with new results
```

Replay of the full campaign will produce correct state, because each event carries its own results. But the GAME EXPERIENCE has a seam: the goblin who survived session 5 because ties went to the defender would have died if ties went to the attacker.

This is not a technical problem — replay works fine. It is a NARRATIVE and BALANCE problem. The PM and PO must decide whether Frankenstein campaigns are acceptable or whether Type B changes require a clean break.

### 4.3 Type C Crashes

If a Type C change adds a required field to Event, `Event.from_dict()` on old JSONL data will either:
- Crash with `TypeError: __init__() missing required argument` (if the field has no default)
- Silently use the default value (if the field has a default), potentially producing incorrect state

If a Type C change removes a field, old JSONL data will pass an unexpected keyword argument:
- `Event.from_dict()` uses `cls(**data)`, so extra keys in the dict will cause `TypeError: __init__() got an unexpected keyword argument`

If a Type C change renames an event type (e.g., `hp_changed` -> `hit_points_modified`), old events with the old name will fall through to the `else` branch in `reduce_event()`:
```python
else:
    # Unknown event types are ignored (fail-safe)
    pass
```
This is a SILENT DATA LOSS — the event is ignored, state is not updated, and the hash will diverge with no explanation.

---

## 5. Version Contract Design

### 5.1 What a Bone-Layer Version Includes

A bone-layer version is not just a number. It is a contract that specifies:

| Component | What It Pins | Example |
|-----------|-------------|---------|
| Procedure definitions | The exact logic of every resolver and reducer | `attack_resolver.compute_damage()` v0.1.0 |
| Schema versions | The exact fields and types of every serialized dataclass | `Event` schema v1: `{event_id, event_type, timestamp, payload, rng_offset, citations}` |
| Parameter values | The exact constants used in formulas | `MIN_DAMAGE = 1`, `TWO_HANDED_STR_MULT = 1.5` |
| Content pack format version | The schema of world bundle registries | `rule_registry.schema.json` v1.0 |
| World bundle compatibility range | Which world bundles this engine can load | `bundle_schema >= 1.0, < 2.0` |

### 5.2 Semantic Versioning

The bone-layer version follows semantic versioning with domain-specific semantics:

```
MAJOR.MINOR.PATCH

MAJOR  = Type C changes (schema-breaking)
         Incrementing MAJOR means: old saves CANNOT load without migration.
         Example: 0.x.x -> 1.0.0

MINOR  = Type B changes (behavior-changing)
         Incrementing MINOR means: old saves CAN load, but game behavior differs.
         Campaigns get a HARD STOP with migration options.
         Example: 0.1.x -> 0.2.0

PATCH  = Type A changes (backward-compatible bug fixes)
         Incrementing PATCH means: old saves load safely, bugs are fixed.
         Campaigns get a warning, no action required.
         Example: 0.1.0 -> 0.1.1
```

### 5.3 Version Contract Document Template

Each version bump should be accompanied by a version contract document in YAML:

```yaml
# docs/versions/v0.1.1.yaml
version: "0.1.1"
previous_version: "0.1.0"
date: "2026-02-15"
change_type: "PATCH"  # MAJOR | MINOR | PATCH

summary: "Bug fixes from bone-layer verification (30 WRONG verdicts)"

changes:
  - id: "BUG-1"
    type: "A"
    component: "attack_resolver"
    description: "Two-handed STR multiplier corrected to 1.5x"
    files_changed:
      - "aidm/core/attack_resolver.py"
      - "aidm/core/full_attack_resolver.py"
    old_behavior: "str_mod * 1.0 for all grips"
    new_behavior: "str_mod * 1.5 for two-handed, str_mod * 0.5 for off-hand"
    replay_impact: "NONE — events store computed damage, not formula"

  - id: "BUG-8"
    type: "A"
    component: "attack_resolver"
    description: "Minimum damage floor corrected to 1"
    files_changed:
      - "aidm/core/attack_resolver.py"
      - "aidm/core/full_attack_resolver.py"
    old_behavior: "max(0, damage)"
    new_behavior: "max(1, damage)"
    replay_impact: "NONE — events store computed damage, not formula"

  # ... remaining 28 bugs ...

compatibility:
  event_schema: "unchanged"
  world_state_schema: "unchanged"
  campaign_manifest_schema: "unchanged"
  world_bundle_schema: "unchanged"
  replay_guarantee: "All 0.1.0 event logs replay identically under 0.1.1"

migration:
  required: false
  automatic: true
  notes: "Campaign manifest engine_version will be updated on first load"
```

### 5.4 Code Touch Points for Implementation

Four places in the codebase must be modified to support version-aware loading:

**Touch Point 1: Version Source of Truth**

A single `__version__` constant that pyproject.toml, CampaignManifest, and all version checks reference:

```python
# aidm/__init__.py (or aidm/version.py)
__version__ = "0.1.0"  # Kept in sync with pyproject.toml
```

**Touch Point 2: Campaign Load Gate**

A version check in the campaign loading path (wherever `CampaignManifest.from_dict()` is called to load an existing campaign):

```python
from aidm import __version__
from packaging.version import Version

def validate_campaign_version(manifest: CampaignManifest) -> VersionCheckResult:
    campaign_v = Version(manifest.engine_version)
    engine_v = Version(__version__)

    if campaign_v.major != engine_v.major:
        return VersionCheckResult.HARD_STOP_SCHEMA  # Type C
    elif campaign_v.minor != engine_v.minor:
        return VersionCheckResult.HARD_STOP_BEHAVIOR  # Type B
    elif campaign_v.micro != engine_v.micro:
        return VersionCheckResult.WARN_BUGFIX  # Type A
    else:
        return VersionCheckResult.COMPATIBLE
```

**Touch Point 3: Event Schema Version**

Add `event_schema_version` to Event so that old events can be identified during schema migrations:

```python
@dataclass
class Event:
    event_id: int
    event_type: str
    timestamp: float
    payload: Dict[str, Any]
    rng_offset: int = 0
    citations: List[Dict[str, Any]] = field(default_factory=list)
    event_schema_version: str = "1"  # NEW — defaults to "1" for backward compat
```

**Touch Point 4: EventLog Metadata Header**

Add an optional metadata first-line to JSONL files:

```python
def to_jsonl(self, path: Path, engine_version: str = None) -> None:
    with open(path, "w", encoding="utf-8") as f:
        if engine_version:
            # Metadata line (identified by __meta__ key)
            meta = {"__meta__": True, "engine_version": engine_version,
                    "event_schema_version": "1"}
            json.dump(meta, f, sort_keys=True)
            f.write("\n")
        for event in self._events:
            json.dump(event.to_dict(), f, sort_keys=True)
            f.write("\n")
```

---

## 6. Recommendation

### 6.1 Minimum Viable Version Safety (3 changes)

These three changes provide load-time protection against the most common version mismatch scenarios. They can be implemented as part of the BUG-fix sprint with minimal risk:

| # | Change | File | Effort | Risk |
|---|--------|------|--------|------|
| 1 | Validate `engine_version` on campaign load | Campaign load path (new function) | LOW | LOW — additive, no existing behavior changes |
| 2 | Add `bone_engine_version` field to `WorldState` | `aidm/core/state.py` | LOW | MEDIUM — changes state_hash() output; must be added with default for backward compat |
| 3 | Add `event_schema_version` to `Event` | `aidm/core/event_log.py` | LOW | LOW — default value "1" means existing JSONL loads unchanged |

**Important note on change #2:** Adding `bone_engine_version` to WorldState changes the output of `state_hash()`, which would break ALL existing replay hashes. To maintain backward compatibility, the field should be:
- Added with `default=""` (empty string)
- Excluded from `state_hash()` computation initially
- Included in `state_hash()` only after a MAJOR version bump (when old hashes are intentionally invalidated)

Alternatively, `bone_engine_version` can be tracked in `CampaignManifest` only (already exists as `engine_version`) and NOT added to WorldState, avoiding the hash-breaking issue entirely. This is the safer path for the current sprint.

### 6.2 Full Version Safety (6 additional changes)

These changes complete the version infrastructure. They are not required for the BUG-fix sprint but should be scheduled for the next milestone:

| # | Change | File | Effort |
|---|--------|------|--------|
| 4 | Create `aidm/version.py` as single source of truth for `__version__` | New file | LOW |
| 5 | Add JSONL metadata header to EventLog serialization | `aidm/core/event_log.py` | LOW |
| 6 | Create version contract YAML template and first document (v0.1.1) | `docs/versions/` | LOW |
| 7 | Add `--version-check` flag to replay runner | `aidm/core/replay_runner.py` | MEDIUM |
| 8 | Create migration tool skeleton for Type C changes | New module `aidm/core/migration.py` | MEDIUM |
| 9 | Add version compatibility range to World Compiler contract | `docs/contracts/WORLD_COMPILER.md` | LOW |

### 6.3 What NOT to Do

- **Do NOT add version fields that change `state_hash()`** unless you are prepared to invalidate all existing replay hashes. The hash is the backbone of determinism verification (BL-011).
- **Do NOT gate-keep Type A fixes behind user confirmation.** Bug fixes should warn and proceed. Asking the user "do you want correct two-handed damage?" is not a real choice.
- **Do NOT implement versioned resolver dispatch** (running old resolver logic for old campaigns) in this sprint. It is a massive infrastructure investment with unclear ROI. If needed, it belongs in a future milestone.
- **Do NOT break the "events record results" invariant.** If someone proposes storing formulas in events instead of results, reject it. The current design (results-only) is what makes Type A fixes replay-safe.

---

## Files Referenced

| File | Role in This Analysis |
|------|----------------------|
| `pyproject.toml` | Package version ("0.1.0") — not referenced at runtime |
| `aidm/core/state.py` | WorldState definition, `ruleset_version` field, `state_hash()` (BL-011), FrozenWorldStateView (BL-020) |
| `aidm/core/event_log.py` | Event and EventLog definitions, JSONL serialization, monotonic ID enforcement (BL-008) |
| `aidm/core/replay_runner.py` | `reduce_event()` (BL-012), `run()`, MUTATING_EVENTS, INFORMATIONAL_EVENTS classification |
| `aidm/schemas/campaign.py` | CampaignManifest with `engine_version` and `config_schema_version` fields |
| `docs/contracts/WORLD_COMPILER.md` | Frozen World Bundle specification, world-level versioning context |
| `docs/verification/WRONG_VERDICTS_MASTER.md` | 30 WRONG verdicts — all Type A changes |
| `docs/verification/BONE_LAYER_CHECKLIST.md` | Verification completion status, iteration log |

---

## Appendix A: Boundary Law Cross-Reference

| BL | Name | Relevance to Versioning |
|----|------|------------------------|
| BL-008 | Monotonic Event IDs | Events are ordered; version-aware replay depends on this ordering |
| BL-011 | Deterministic Hashing | Hash divergence is the SYMPTOM of version mismatch; version checking is the PREVENTION |
| BL-012 | Deep Copy on Reduce | Ensures reducer changes do not create aliasing bugs across versions |
| BL-017 | Inject-Only Campaign ID | CampaignManifest.campaign_id is caller-injected; engine_version should follow same pattern |
| BL-020 | WorldState Immutability | Non-engine code cannot corrupt state regardless of version; reduces blast radius of version bugs |

---

## Appendix B: The 30 WRONG Verdicts Are All Type A

This is a critical observation that simplifies the immediate fix sprint. Every single bug found during bone-layer verification is a Type A change (backward-compatible bug fix against the SRD). None of them:

- Add new fields to Event, WorldState, or CampaignManifest (not Type C)
- Change intended behavior to a different-but-valid interpretation (not Type B)
- Require user opt-in or campaign migration (just warn and proceed)

This means the entire fix sprint (all 13 fix WOs, all 30 bugs) can proceed under a single PATCH version bump: `0.1.0 -> 0.1.1`. No migration tooling is needed. No user-facing choices are required. The version infrastructure recommended in Section 6.1 is sufficient to handle this sprint.

Future sprints may introduce Type B or Type C changes. That is when the full version safety infrastructure (Section 6.2) becomes essential.

---

*End of RQ-SPRINT-007*

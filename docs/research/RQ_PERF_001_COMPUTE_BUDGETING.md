# RQ-PERF-001: Deterministic Compute Budgeting

**Research Track:** 4 of 7
**Domain:** System Performance (Cross-cutting)
**Status:** FINDINGS RECEIVED (partial — data layout, Spark constraint, determinism harness)
**Filed:** 2026-02-11
**Source:** Thunder (Product Owner) — Deep Research prompt

---

## Problem Statement

With minimal/no rendering, you have significant headroom — but you still need predictable latency and throughput for: (a) Box geometric/rules queries, (b) Lens query/serialization/versioning, (c) Spark generation bursts (prep + occasional in-session). The performance problem is not "frames per second." It's tail latency, burst management, caching, and deterministic replay integrity under load.

---

## Research Objective

Develop a performance strategy for a turn-based, deterministic rules engine + memory/index layer + generative layer, optimized for low tail latency and predictable responsiveness without a graphics pipeline. Provide concrete recommendations for:

1. Profiling methodology and benchmarks
2. Caching & invalidation
3. Scheduling and concurrency boundaries
4. Data layout choices that materially improve runtime
5. Performance targets by subsystem (Box/Lens/Spark)

---

## Research Sub-Questions

### (1) Define Real Performance Targets (not FPS)

Research how to set system-level budgets:

"Player-visible responsiveness" targets:
- Box query turnaround (p50/p95)
- Lens query turnaround (p50/p95)
- Full "player action → resolved outcome" time (p95)

Prep workloads:
- Scene generation time
- Encounter generation time
- Map object registration time

Deliverable: recommended target numbers + rationale + how to measure.

### (2) Profiling Strategy for Python (and mixed workloads)

Research best-in-class profiling approach for:
- CPU-bound geometry checks (Box)
- I/O + serialization + indexing (Lens)
- Model inference calls (Spark, if local) and API latency (if remote)

Include:
- Sampling profilers vs instrumentation
- Tracing spans across subsystems
- How to detect p95 regressions reliably

Deliverable: concrete profiling toolchain + benchmark harness outline.

### (3) Hot Path Caching Design

Research caching layers appropriate to this architecture:

Box caches:
- LOS/LOE results (with invalidation triggers)
- Cover geometry intermediates
- Area-of-effect square sets

Lens caches:
- Object "mechanical profiles" blobs
- Spatial occupancy views
- "as-of turn" snapshots

Key requirement: caching must not break determinism/replay.

Deliverable: cache keys, invalidation rules, and replay-safe design.

### (4) Incremental Recompute Instead of Global Recompute

Research strategies for incremental updates:

When an object moves, only recompute affected:
- Spatial occupancy cells
- LOS/LOE caches involving those cells
- Cover computations involving nearby attackers/targets

Avoid "recompute everything every time" patterns.

Deliverable: dependency graph approach + practical heuristics.

### (5) Concurrency Boundaries and Scheduling

Research how to safely parallelize without violating:
- Determinism
- Reproducible replays
- Box authority

Possible concurrency zones:
- Spark prep generation running while player reads/doodles
- Background indexing in Lens
- Precomputation of likely geometry queries
- Asynchronous asset generation (portraits/parchments) with deterministic IDs

Deliverable: recommended concurrency model + queueing strategy + forbidden races.

### (6) Memory vs Disk Tradeoffs (Lens + replay)

Research how to store and access "world facts" efficiently:
- SQLite tuning vs append-only logs vs hybrid
- Compression strategies for snapshots
- In-memory working set sizing
- Indexing strategy that doesn't kill write throughput

Deliverable: storage architecture recommendations + tuning parameters to evaluate.

### (7) Tail Latency Management + "DM pacing"

Even if you can mask some waiting with DM narration, you still need controls:
- Budgets for synchronous interactions
- When to defer to "Give me a moment…"
- Proactive prefetching (next-likely queries)
- Admission control for expensive operations mid-combat

Deliverable: policy rules for when to compute now vs later.

### (8) Output: Performance Playbook

Synthesize into:
- Measurement framework
- Target budgets
- Caching plan
- Recompute strategy
- Concurrency plan
- Storage tuning checklist
- Regression testing approach (prevent perf drift)

---

## Research Findings

### Preamble

To build a high-performance, deterministic engine, the gap between "Generative Magic" and "Rigid Rules" must be bridged through compact data schemas for the Lens and a prompting strategy that treats the LLM as a structured function call rather than a chatbot. The following findings address data layout, Spark output constraint, and determinism verification.

---

### Finding 1: Lens Data Schema — MsgPack with Integer-Key Mapping

Standard Python dictionaries store redundant string keys. The Lens uses **MsgPack with an Integer-Mapping (Enums)** for compact, fast serialization.

#### The Key Map Concept

Instead of storing `{"health": 100, "position": [10, 20]}`, define a static map where `health = 0` and `position = 1`. The stored binary is simply `[100, [10, 20]]`.

#### Schema Structure: Actors vs Items

**Actors (Heavy State):**

| Field | Type | Description |
|---|---|---|
| `ID` | int | Primary key |
| `S` | int | Status bitmask (1=Alive, 2=Stunned, 4=Invisible). Bitmask instead of multiple Booleans saves significant space |
| `V` | list | Vitality stats `[current_hp, max_hp, stamina]` |
| `P` | list | Position `[x, y, z]` |

**Items (Light State):**

| Field | Type | Description |
|---|---|---|
| `T` | int | Type ID (points to a static "Master Template" in the Box) |
| `D` | dict | Delta only — stores only what *changed* from the template (e.g., current durability) |

**Implementation Note:** Use `msgpack.Packer(use_bin_type=True)` for the Lens. This ensures binary blobs are treated as bytes, preventing Python from attempting expensive UTF-8 decoding during turn replays.

---

### Finding 2: Spark Prompting Pipeline — Constrained Output

The biggest performance/stability risk is "Hallucinated JSON" from the Spark layer. To ensure output matches the schema, use the **System Role as a Type Definer**.

#### Prompt Architecture: Schema Population, Not Description

Do not ask Spark to "Describe the room." Ask it to "Populate the Room Schema."

**System Prompt Pattern:**

> You are a world-state generator for a deterministic engine.
> You MUST return a JSON object that adheres to this Typescript-style interface:
> `{ "room_id": string, "entities": Array<{ "type": string, "desc": string, "stats": [int, int] }> }`
> Do not include any prose outside the JSON.

#### The "Grammar Shield" Strategy

1. **Stop Sequences:** Set `}` as a stop sequence when generating single objects.
2. **Schema Pre-fill:** Start the Spark response with the opening character `{`. This forces the model into "JSON mode" immediately.
3. **Validation Middleware:**

```python
def spark_to_lens(raw_json):
    try:
        data = json.loads(raw_json)
        # Use Pydantic to enforce types
        return RoomSchema(**data).dict()
    except ValidationError:
        # Fallback: Log error and return a "Generic Safe Room"
        return DEFAULT_ROOM_TEMPLATES["void"]
```

---

### Finding 3: Determinism Regression Test Harness

To prove the engine is deterministic, two identical seeds must produce identical world states after 1,000 turns.

#### The `pytest` Determinism Suite

**Test 1: Determinism Drift Detection**

```python
def run_simulation(seed, turns=1000):
    engine = GameEngine(seed=seed)
    history_hashes = []
    for _ in range(turns):
        history_hashes.append(engine.get_state_hash())
        action = engine.get_random_valid_action()
        engine.step(action)
    return history_hashes, engine.get_state_hash()

def test_determinism_drift():
    shared_seed = 42
    hashes_1, final_state_1 = run_simulation(shared_seed)
    hashes_2, final_state_2 = run_simulation(shared_seed)
    assert hashes_1 == hashes_2, "State diverged during simulation!"
    assert final_state_1 == final_state_2, "Final world state is inconsistent!"
```

**Test 2: Reproducibility from Action Log**

```python
def test_reproducibility_from_log():
    engine_a = GameEngine(seed=99)
    actions_taken = []
    for _ in range(50):
        action = engine_a.get_random_valid_action()
        actions_taken.append(action)
        engine_a.step(action)
    engine_b = GameEngine(seed=99)
    for action in actions_taken:
        engine_b.step(action)
    assert engine_a.get_state_hash() == engine_b.get_state_hash()
```

#### Why This Works

- **State Hashing:** `get_state_hash()` summarizes the Lens (MsgPack all entities → SHA256). If a single position coordinate or one HP point is off, the test fails.
- **The "Gold Master":** Save `final_state_1` to a file. Whenever the Box rules are updated, run this test to ensure the math hasn't accidentally changed.

---

### Finding 4: Performance Architecture Summary

| Layer | Strategy | Key Technique |
|---|---|---|
| **Box** | `__slots__` and bitmasks | Fast math, minimal object overhead |
| **Lens** | MsgPack with Integer Keys | Tiny, fast-saving snapshots |
| **Spark** | Schema-constrained prompts | Prevent "Dirty Data" from entering the Box |
| **Harness** | `pytest` determinism suite | 1,000-turn reproducibility gate |

---

## Cross-References

- `docs/research/R0_PREP_PIPELINE_TIMING_STUDY.md` — Existing prep timing research
- `docs/research/R0_DETERMINISM_CONTRACT.md` — Determinism requirements
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — System architecture

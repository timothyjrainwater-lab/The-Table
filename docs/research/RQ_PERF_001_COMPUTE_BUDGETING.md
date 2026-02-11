# RQ-PERF-001: Deterministic Compute Budgeting

**Research Track:** 4 of 7
**Domain:** System Performance (Cross-cutting)
**Status:** QUESTION FILED — Awaiting Research Findings
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

**STATUS: NOT YET DELIVERED**

---

## Cross-References

- `docs/research/R0_PREP_PIPELINE_TIMING_STUDY.md` — Existing prep timing research
- `docs/research/R0_DETERMINISM_CONTRACT.md` — Determinism requirements
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — System architecture

# BL-020: WorldState Immutability at Non-Engine Boundaries

**Status:** DRAFT — Awaiting PM validation
**Author:** Agent D (governance)
**Unblocker for:** WO-M1-03
**Locked prerequisites:** BL-007, BL-011, BL-012, BL-017/BL-018 (inject-only model)
**Scope:** WorldState mutation control ONLY. Does not address F-03, IPC transport, or serialization format.

---

## 1. Definitions

**WorldState** — The `@dataclass` defined in `aidm/core/state.py`. Contains `ruleset_version`, `entities`, and `active_combat`. This is the sole canonical container for game simulation state.

**Engine boundary** — The set of modules authorized to produce a new WorldState instance from an existing one. Defined exhaustively in §3 below.

**Non-engine boundary** — Every module, layer, or call site that is NOT listed in §3. Includes narration, immersion, UI, SPARK adapters, presentation, session inspection, and all future IPC consumers.

**Mutation** — Any of the following:
- Direct field assignment on a WorldState instance (`ws.entities = ...`)
- In-place modification of any nested mutable object reachable from a WorldState reference (`ws.entities["pc1"]["hp"] += 5`)
- Calling any method on WorldState that alters internal state (none exist today; this prohibits adding any)
- Retaining a mutable alias to a WorldState's internal structures and modifying through that alias

**Handoff** — Any point where a WorldState reference (or a reference to its internals) crosses from an engine module to a non-engine module. This includes:
- Function call arguments
- Return values
- Tuple/dataclass fields in returned result objects (e.g., `TurnResult.world_state`)
- Storage in any shared data structure accessible to non-engine code

---

## 2. Boundary Law Statement

> **BL-020:** WorldState MUST be immutable at every non-engine boundary. No module outside the engine boundary (§3) may mutate a WorldState instance or any object reachable from it. Violations are hard failures, not warnings.

---

## 3. Engine Boundary — Exhaustive Authorized Mutator List

The following modules, and ONLY the following modules, are authorized to produce a new WorldState from an existing one. "Produce" means constructing a new `WorldState(...)` instance. No module — engine or otherwise — is authorized to mutate a WorldState in place.

| Module | Authorized Operation |
|--------|---------------------|
| `aidm/core/play_loop.py` | Construct new WorldState after turn resolution via `deepcopy` + reassembly |
| `aidm/core/replay_runner.py` | Construct new WorldState via `reduce_event()` during replay |
| `aidm/core/combat_controller.py` | Construct new WorldState during combat round orchestration |
| `aidm/core/prep_orchestrator.py` | Construct initial WorldState during campaign/combat setup |
| `aidm/core/interaction.py` | Construct new WorldState during intent commit workflow |

**No other module may call `WorldState(...)` with the intent of producing mutated game state.** Test files are exempt for test fixture construction only.

**Resolvers** (`attack_resolver`, `full_attack_resolver`, `maneuver_resolver`, `save_resolver`, `targeting_resolver`, `terrain_resolver`, `environmental_damage_resolver`, `aoo`, `mounted_combat`, `conditions`) are **read-only consumers** of WorldState. They receive it, read it, and emit `Event` objects. They do NOT construct new WorldState instances. Any resolver that currently calls `apply_*_events()` internally to return updated state is considered an engine-boundary extension of `play_loop` and must be audited under this law.

---

## 4. Non-Engine Consumers — Obligations

Every module not listed in §3 that receives a WorldState reference (directly or transitively) MUST treat it as deeply immutable. Specifically:

| Consumer Category | Examples | Obligation |
|-------------------|----------|------------|
| **Narration** | `guarded_narration_service.py` | Must NOT receive WorldState at all (BL-003 already prohibits core imports). Receives `EngineResult` only. No change required. |
| **Immersion** | `audio_mixer.py`, `contextual_grid.py` | Read-only. Must not mutate any field or nested structure. |
| **Session inspection** | `session_log.py` | Read-only. Uses `state_hash()` for verification. Must not mutate. |
| **Tactical policy** | `tactical_policy.py` | Read-only query for AI decision-making. Must not mutate. |
| **UI** | `character_sheet.py` | Read-only presentation. Must not mutate. |
| **Rules validation** | `legality_checker.py` | Read-only legality queries. Must not mutate. |
| **Runtime** | `session.py` | Session lifecycle management. Must not mutate WorldState directly. |
| **Future IPC consumers** | Any M1+ process receiving WorldState over IPC | Must receive an immutable view (see §5). |

---

## 5. Enforcement Mechanism

### Primary Mechanism: Frozen Proxy at Handoff Points

**Choice:** Read-only proxy wrapping at every handoff from engine to non-engine consumer.

**Justification:**

| Option | Verdict | Reason |
|--------|---------|--------|
| **Deep copy** | Rejected | Doubles memory for every handoff. WorldState contains arbitrarily large `entities` dict. Unacceptable at M1 IPC scale where multiple consumers read the same state per turn. |
| **`frozen=True` on dataclass** | Rejected | Prevents only top-level field assignment. Does NOT protect nested mutables (`entities` dict, `active_combat` dict). Also breaks the engine's own construction pattern — engine modules would need workarounds. |
| **Read-only proxy** | **Selected** | Wraps WorldState at handoff. Intercepts `__setattr__` and `__delattr__` on the proxy. Wraps nested dict access to return `MappingProxyType` views (consistent with BL-015 pattern for `EntityState.base_stats`). Engine retains the real mutable instance internally. Non-engine code receives the proxy. Zero-copy for reads. Fails loud on writes. |

### Proxy Contract

The proxy (name: `FrozenWorldStateView` or equivalent — implementer decides exact name) must satisfy:

1. **Attribute reads pass through.** `proxy.ruleset_version` returns the real value.
2. **`state_hash()` passes through.** `proxy.state_hash()` returns the correct hash.
3. **`to_dict()` passes through.** Returns a fresh dict (already a copy by nature).
4. **Field assignment raises.** `proxy.entities = {}` raises `WorldStateImmutabilityError`.
5. **Nested dict mutation raises.** `proxy.entities["pc1"]["hp"] = 0` raises `WorldStateImmutabilityError`. This requires that `proxy.entities` returns a recursively-wrapped immutable mapping view, not the raw dict.
6. **`active_combat` nested mutation raises.** Same recursive wrapping for `active_combat` when it is not `None`.
7. **The proxy is NOT a WorldState instance.** `isinstance(proxy, WorldState)` returns `False`. This is intentional — it forces non-engine code to declare its dependency on the read-only view type, not the mutable type. Type annotations at non-engine boundaries must use the view type.
8. **The proxy does not support `from_dict()`.** Non-engine code has no reason to construct WorldState from serialized data. The class method is not exposed on the view.

### Handoff Points Where Proxy Must Be Applied

Every return path or argument path where WorldState leaves engine control:

| Handoff Point | Current Pattern | Required Change |
|---------------|-----------------|-----------------|
| `play_loop.execute_turn()` return value (`TurnResult.world_state`) | Returns raw WorldState | Must wrap in proxy before returning if `TurnResult` is consumed outside engine |
| `combat_controller.execute_combat_round()` return value | Returns raw WorldState in result | Must wrap in proxy before returning to non-engine callers |
| `interaction.start_intent()` / `commit_point()` / `commit_entity()` return value | Returns raw WorldState in tuple | If caller is non-engine, must wrap. If caller is engine (e.g., play_loop), raw is acceptable. |
| Any future IPC serialization boundary | Does not exist yet | M1 IPC layer must serialize from the real WorldState, and deserialize into a frozen proxy on the receiving end |
| `session_log` state snapshots | Stores `initial_state_hash` (string, not object) | No change required — already uses hash, not reference |

**Engine-internal handoffs** (e.g., `play_loop` calling `attack_resolver`) do NOT require proxy wrapping. The engine boundary is trusted internally.

---

## 6. STOP Conditions (Hard Failures)

The following conditions MUST halt execution immediately. No fallback. No warning-and-continue. No degraded mode.

| ID | Violation | Trigger |
|----|-----------|---------|
| **STOP-020-01** | Non-engine module mutates WorldState field | `__setattr__` intercepted on `FrozenWorldStateView` |
| **STOP-020-02** | Non-engine module mutates nested dict reachable from WorldState | `__setitem__` intercepted on recursive mapping proxy |
| **STOP-020-03** | Non-engine module deletes WorldState field | `__delattr__` intercepted on `FrozenWorldStateView` |
| **STOP-020-04** | Non-engine module constructs `WorldState(...)` directly | Detected by static analysis (AST import + constructor call check, same pattern as BL-001 through BL-004) |
| **STOP-020-05** | Proxy bypassed at handoff | Detected by type assertion test: non-engine function signatures must accept view type, not `WorldState` |
| **STOP-020-06** | `isinstance(received_object, WorldState)` returns `True` in non-engine module | Detected by test scanning non-engine code for `isinstance(..., WorldState)` checks (indicates raw object leaked) |

Each STOP condition maps to exactly one test assertion (§7).

---

## 7. Acceptance Conditions (Testable)

Each condition below is a single test. Pass/fail. No partial credit.

### Runtime Enforcement Tests

| Test ID | Condition | Pass | Fail |
|---------|-----------|------|------|
| **T-020-01** | Construct `FrozenWorldStateView(ws)`. Attempt `view.entities = {}`. | `WorldStateImmutabilityError` raised | No exception or wrong exception type |
| **T-020-02** | Construct `FrozenWorldStateView(ws)`. Attempt `view.entities["pc1"]["hp"] = 0`. | `WorldStateImmutabilityError` raised (or `TypeError` from `MappingProxyType`) | Mutation succeeds silently |
| **T-020-03** | Construct `FrozenWorldStateView(ws)`. Attempt `del view.entities`. | `WorldStateImmutabilityError` raised | Deletion succeeds |
| **T-020-04** | Construct `FrozenWorldStateView(ws)`. Call `view.state_hash()`. | Returns same hash as `ws.state_hash()` | Hash mismatch or exception |
| **T-020-05** | Construct `FrozenWorldStateView(ws)`. Call `view.to_dict()`. | Returns dict equal to `ws.to_dict()` | Dict mismatch or exception |
| **T-020-06** | Construct `FrozenWorldStateView(ws)`. Check `isinstance(view, WorldState)`. | Returns `False` | Returns `True` |
| **T-020-07** | Construct `FrozenWorldStateView(ws)`. Access `view.ruleset_version`. | Returns correct string value | Exception or wrong value |
| **T-020-08** | Construct `FrozenWorldStateView(ws)`. Access `view.active_combat["round"]` when `active_combat` is a dict. Attempt `view.active_combat["round"] = 99`. | `TypeError` or `WorldStateImmutabilityError` raised | Mutation succeeds |

### Static Analysis / AST Enforcement Tests

| Test ID | Condition | Pass | Fail |
|---------|-----------|------|------|
| **T-020-09** | Scan all files in `aidm/narration/`, `aidm/immersion/`, `aidm/ui/`, `aidm/spark/`. None import `WorldState` from `aidm.core.state`. | Zero imports found | Any import found |
| **T-020-10** | Scan all files in `aidm/narration/`, `aidm/immersion/`, `aidm/ui/`, `aidm/spark/`. None contain `WorldState(` constructor calls. | Zero constructor calls found | Any constructor call found |
| **T-020-11** | Scan non-engine modules that DO legitimately receive state (e.g., `tactical_policy`, `legality_checker`). Their function signatures accept `FrozenWorldStateView`, not `WorldState`. | All signatures use view type | Any signature uses `WorldState` directly |

### Integration / Handoff Tests

| Test ID | Condition | Pass | Fail |
|---------|-----------|------|------|
| **T-020-12** | Call `execute_turn()` and inspect the returned `TurnResult.world_state`. If the caller is non-engine, the returned object must be `FrozenWorldStateView`. | `isinstance(result.world_state, FrozenWorldStateView)` is `True` | Returns raw `WorldState` |
| **T-020-13** | Full round-trip: engine produces WorldState → wraps in proxy → non-engine consumer reads `state_hash()` → hash matches original. | Hashes match | Hashes diverge |
| **T-020-14** | Replay runner receives real `WorldState` (it is engine-boundary). Verify `isinstance(state, WorldState)` is `True` inside `reduce_event()`. | `True` — replay runner operates on real state | Receives proxy (would break mutation needed for replay) |

---

## 8. Interaction With Existing Boundary Laws

| Existing Law | Interaction with BL-020 |
|--------------|------------------------|
| **BL-003** (narration must not import core) | BL-020 is strictly additive. Narration already cannot access WorldState. No conflict. |
| **BL-007** (EngineResult frozen on creation) | No conflict. EngineResult is a separate object. BL-020 covers WorldState only. |
| **BL-011** (state_hash determinism) | BL-020 proxy must pass through `state_hash()` faithfully. T-020-04 verifies this. |
| **BL-012** (replay produces identical results) | Replay runner is engine-boundary (§3). It receives real WorldState, not proxy. No conflict. |
| **BL-015** (EntityState rejects dict mutation via base_stats) | BL-020 uses the same `MappingProxyType` pattern for nested dict protection. Consistent, not conflicting. |
| **BL-017/BL-018** (inject-only model) | BL-020 does not introduce any default factories, clock services, or ID services. The proxy is a runtime wrapper, not a schema default. No conflict. |

---

## 9. Out of Scope (Explicitly Excluded)

- **F-03** — Not addressed here. Whatever F-03 is, this spec does not solve it.
- **IPC transport format** — BL-020 defines the immutability contract. M1 IPC design will specify how WorldState is serialized/deserialized across process boundaries. The receiving side must deserialize into a `FrozenWorldStateView`.
- **WorldState schema changes** — BL-020 does not add or remove fields from WorldState. The `@dataclass` definition is unchanged.
- **Performance optimization** — If proxy overhead becomes measurable, that is an M1 implementation concern, not a governance concern. The contract stands; the implementation may optimize within the contract.

---

## 10. Summary of Obligations by Role

| Role | Obligation |
|------|------------|
| **Engine modules** (§3 list) | May construct new `WorldState` instances. Must wrap in `FrozenWorldStateView` before returning to non-engine callers. |
| **Resolvers** | Read-only consumers. Receive real `WorldState` from engine (trusted internal boundary). Must NOT construct new `WorldState`. |
| **Non-engine consumers** | Receive `FrozenWorldStateView` only. Must declare this type in signatures. Must not attempt mutation. Must not import `WorldState` class (except where already prohibited by BL-001–BL-004). |
| **Test suite** | Exempt from proxy requirement for fixture construction. Test files may construct `WorldState` directly. Tests MUST include all T-020-* assertions in `test_boundary_law.py`. |
| **Future IPC layer** | Must serialize from real `WorldState` on engine side. Must deserialize into `FrozenWorldStateView` on consumer side. |

---

*End of BL-020 specification.*

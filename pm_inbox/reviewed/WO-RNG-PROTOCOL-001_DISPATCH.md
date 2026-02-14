# WO-RNG-PROTOCOL-001: RNGProvider Protocol Extraction

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 1
**Priority:** P1 — P0 CRITICAL modularity gap (RQ-SPRINT-011). Single most dangerous monolithic dependency.
**Source:** RQ-SPRINT-011 (Component Modularity), R0_DETERMINISM_CONTRACT

---

## Target Lock

Extract `RNGManager` behind a `RNGProvider` Protocol. Currently 32+ call sites directly import and consume `RNGManager`. This blocks all RNG strategy swapping (testing, cryptographic, replay) and is the single most dangerous monolithic dependency in the mechanical layer.

The change is mostly type-level. Resolvers already use `rng.stream("combat").randint(1, 20)` — the Protocol formalizes this interface. Zero resolver logic changes.

## Binary Decisions

1. **Protocol or ABC?** Protocol (runtime_checkable). Matches the existing pattern used by atmospheric adapters (ImageAdapter, etc.).
2. **Where does the Protocol live?** New file: `aidm/core/rng_protocol.py`.
3. **What about the stream interface?** `RandomStream` Protocol for the stream returned by `.stream()`. Methods: `randint()`, `choice()`, `random()`, `shuffle()`.
4. **Does RNGManager change?** It stays as-is but becomes the stdlib implementation of `RNGProvider`. No rename needed — just add Protocol conformance.
5. **Do resolver signatures change?** Type annotation changes from `rng: RNGManager` to `rng: RNGProvider`. Same parameter name, same usage, different type hint.
6. **Can RNG be swapped mid-session?** NO. RQ-SPRINT-011 explicitly states swapping mid-session breaks replay determinism. Swap point is session start only.

## Contract Spec

### Change 1: Define RNGProvider Protocol

New file `aidm/core/rng_protocol.py`:

```python
@runtime_checkable
class RandomStream(Protocol):
    def randint(self, a: int, b: int) -> int: ...
    def choice(self, seq: Sequence) -> Any: ...
    def random(self) -> float: ...
    def shuffle(self, seq: MutableSequence) -> None: ...

@runtime_checkable
class RNGProvider(Protocol):
    def stream(self, name: str) -> RandomStream: ...
```

### Change 2: Update Type Annotations

All files that currently have `rng: RNGManager` in function signatures: change to `rng: RNGProvider`. This is 32+ sites across:
- `aidm/core/attack_resolver.py`
- `aidm/core/full_attack_resolver.py`
- `aidm/core/maneuver_resolver.py`
- `aidm/core/combat_controller.py`
- `aidm/core/initiative.py`
- `aidm/core/aoo.py`
- `aidm/core/environmental_damage_resolver.py`
- `aidm/core/experience_resolver.py`
- All other core resolvers

### Change 3: Verify RNGManager Conformance

Add a test that asserts `isinstance(RNGManager(...), RNGProvider)`. If it fails, add the missing methods. Current API inspection suggests it already conforms — this is verification, not implementation.

### Constraints

- Do NOT change any RNG logic — this is a type-level refactor only
- Do NOT create alternative implementations yet (crypto, mock) — those are future WOs
- Do NOT modify DeterministicRNG internals
- Do NOT change seed derivation, stream naming, or call counting
- All existing RNG tests must pass unmodified
- Determinism contract (R0) must remain satisfied

### Boundary Laws Affected

- BL-005, BL-006 (RNG monopoly): PRESERVED — Protocol enforces the same contract
- BL-011 (deterministic hashing): NOT AFFECTED — no hash computation changes

## Success Criteria

- [ ] `RNGProvider` Protocol defined in `aidm/core/rng_protocol.py`
- [ ] `RandomStream` Protocol defined for stream interface
- [ ] All resolver type annotations updated from `RNGManager` to `RNGProvider`
- [ ] `isinstance(RNGManager(...), RNGProvider)` passes at runtime
- [ ] All existing tests pass without modification
- [ ] No resolver logic changed — only type hints
- [ ] Import graph: resolvers import Protocol, not concrete class

## Files Expected to Change

- New: `aidm/core/rng_protocol.py`
- `aidm/core/attack_resolver.py` — type annotation
- `aidm/core/full_attack_resolver.py` — type annotation
- `aidm/core/maneuver_resolver.py` — type annotation
- `aidm/core/combat_controller.py` — type annotation
- `aidm/core/initiative.py` — type annotation
- `aidm/core/aoo.py` — type annotation
- `aidm/core/environmental_damage_resolver.py` — type annotation
- `aidm/core/experience_resolver.py` — type annotation
- All other files with `rng: RNGManager` signatures
- Test file for Protocol conformance

## Files NOT to Change

- `aidm/core/rng_manager.py` — implementation stays, just conforms to Protocol
- Any Lens, schema, or presentation files
- Gold masters — no behavioral change

---

*End of WO-RNG-PROTOCOL-001*

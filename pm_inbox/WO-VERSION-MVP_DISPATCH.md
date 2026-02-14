# WO-VERSION-MVP: Minimum Viable Version Safety

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 0 (gate-lift prerequisite)
**Priority:** P0 — Must land before any world bundle is distributed
**Source:** RQ-SPRINT-007 (Bone Versioning)

---

## Target Lock

Add minimum viable version-tracking infrastructure so the engine knows what version it is, campaigns know what version created them, and loading a mismatched campaign produces a clear warning instead of silent divergence.

Three changes. No schema-breaking modifications. No replay hash changes.

## Binary Decisions

1. **Where does the version live?** Single source of truth in `aidm/__init__.py` as `__version__ = "0.1.0"`. Kept in sync with `pyproject.toml`.
2. **WorldState or CampaignManifest?** CampaignManifest ONLY. Adding a version field to WorldState would change `state_hash()` output and break all existing replay hashes. The safer path per RQ-007 Section 6.1.
3. **What happens on version mismatch?** PATCH (Type A): log WARNING, proceed. MINOR (Type B): HARD STOP, require user choice. MAJOR (Type C): HARD STOP, require migration. For now, only WARNING behavior is implemented (all current changes are Type A).
4. **Event schema version default?** `"1"` — backward compatible. Existing JSONL loads unchanged because the default applies when the field is absent.

## Contract Spec

### Change 1: Version Source of Truth

Create `aidm/__init__.py` (or add to existing) with:
```
__version__ = "0.1.0"
```

This must match `pyproject.toml` `version` field. All version checks reference this constant.

### Change 2: Campaign Load Version Gate

Add a version validation function to the campaign loading path:

- Compare `CampaignManifest.engine_version` to `aidm.__version__` on load.
- PATCH difference (e.g., 0.1.0 vs 0.1.1): emit WARNING log with clear message naming both versions and stating "bug fixes only, loading normally."
- MINOR difference: emit ERROR log, raise `VersionMismatchError` (or return a result enum — builder's choice on ergonomics).
- MAJOR difference: same as MINOR for now.
- Equal versions: proceed silently.
- `CampaignManifest.engine_version` is already defined with default `"0.1.0"` and serialized/deserialized. No schema change needed.

### Change 3: Event Schema Version

Add `event_schema_version: str = "1"` to `Event` dataclass:

- Default value `"1"` ensures backward compatibility — existing JSONL without this field deserializes correctly.
- Include in `to_dict()` output.
- Read from `from_dict()` input (with default fallback for old data).
- Do NOT include in any hash computation.

### Constraints

- Do NOT add any field to `WorldState` — avoids `state_hash()` breakage.
- Do NOT modify `state_hash()` computation.
- Do NOT gate Type A fixes behind user confirmation — warn and proceed.
- Do NOT implement versioned resolver dispatch (future milestone).
- Do NOT add JSONL metadata header yet (full version safety, not MVP).

### Boundary Laws Affected

- BL-008 (monotonic event IDs): NOT AFFECTED — new field is metadata, not ordering.
- BL-011 (deterministic hashing): PRESERVED — no hash inputs change.
- BL-012 (reduce_event): NOT AFFECTED — reducer ignores `event_schema_version`.

## Implementation Plan

### Step 1: Version Source of Truth

File: `aidm/__init__.py`

1. Add or verify `__version__ = "0.1.0"`.
2. Verify `pyproject.toml` matches.

### Step 2: Campaign Load Gate

File: New function, likely in `aidm/schemas/campaign.py` or a new `aidm/core/version_check.py`

1. Import `__version__` from `aidm`.
2. Parse both versions using `packaging.version.Version` (or manual split — builder's choice, but `packaging` is already a dependency via pip).
3. Compare major, minor, patch.
4. Return a result (COMPATIBLE / WARN_BUGFIX / HARD_STOP_BEHAVIOR / HARD_STOP_SCHEMA).
5. Log appropriate message.

### Step 3: Event Schema Version

File: `aidm/core/event_log.py`

1. Add `event_schema_version: str = "1"` to `Event` dataclass.
2. Include in `to_dict()`.
3. Handle in `from_dict()` with default `"1"` for missing field.

### Step 4: Tests

1. Test version comparison function: equal, patch diff, minor diff, major diff.
2. Test Event serialization round-trip with and without `event_schema_version`.
3. Test that existing JSONL without `event_schema_version` deserializes to default `"1"`.
4. All existing tests pass.

## Success Criteria

- [ ] `aidm.__version__` exists and matches `pyproject.toml`
- [ ] Campaign load with matching version proceeds silently
- [ ] Campaign load with PATCH difference logs WARNING and proceeds
- [ ] Campaign load with MINOR/MAJOR difference raises error or returns hard-stop result
- [ ] Event round-trip includes `event_schema_version`
- [ ] Old JSONL without `event_schema_version` loads with default `"1"`
- [ ] `state_hash()` output is UNCHANGED (critical — verify with existing replay tests)
- [ ] All existing tests pass

## Files Expected to Change

- `aidm/__init__.py` — version constant
- `aidm/core/event_log.py` — Event dataclass
- `aidm/schemas/campaign.py` or new `aidm/core/version_check.py` — validation function
- Test files for new functionality

## Files NOT to Change

- `aidm/core/state.py` — WorldState is NOT touched
- `aidm/core/replay_runner.py` — Replay logic is NOT touched (no version check in replay yet)
- `pyproject.toml` — Version value stays `0.1.0` (bump to `0.1.1` happens in a separate commit after all fixes are verified)

---

*End of WO-VERSION-MVP*

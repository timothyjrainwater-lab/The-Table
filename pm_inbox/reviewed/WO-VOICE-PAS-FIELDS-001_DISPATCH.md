# WO-VOICE-PAS-FIELDS-001 — Prosodic Fields on VoicePersona

**Type:** CODE
**Priority:** BURST-001 Tier 4.1
**Depends on:** None (prosodic schema draft exists as design reference)
**Blocked by:** Nothing — ready to dispatch

---

## Target Lock

Add 6 bounded prosodic fields and 4 enum types to the VoicePersona dataclass. All fields have safe defaults and silent clamping. Zero runtime behavioral change — adapters ignore unknown fields until Tier 4.2 wires them.

## Binary Decisions (all resolved by PAS v0.1)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Extend VoicePersona or create sibling ProsodicProfile? | Extend VoicePersona directly — simpler, consistent with adapter usage patterns | Playbook §4.1 |
| 2 | Clamping strategy | Silent clamp to safe range, no exceptions | PAS v0.1 safety constraints |
| 3 | Enum implementation | `str, Enum` pattern (serialization-friendly) | Existing codebase pattern |
| 4 | Backward compatibility | All new fields have defaults — old code works unchanged | VoicePersona.from_dict tolerance |

## Contract Spec

**Source:** `docs/planning/PROSODIC_SCHEMA_DRAFT.md` (PAS v0.1)

### Enum Types to Add (in `aidm/schemas/immersion.py`)

```python
class EmphasisLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ToneMode(str, Enum):
    NEUTRAL = "neutral"
    CALM = "calm"
    DIRECTIVE = "directive"
    REFLECTIVE = "reflective"
    COMBAT = "combat"

class PauseProfile(str, Enum):
    MINIMAL = "minimal"
    MODERATE = "moderate"
    DRAMATIC = "dramatic"

class ClarityMode(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
```

### Fields to Add to VoicePersona

| Field | Type | Range | Default | Clamping |
|-------|------|-------|---------|----------|
| `pace` | float | 0.8–1.2 | 1.0 | Silent clamp to [0.8, 1.2] |
| `emphasis_level` | EmphasisLevel | enum | NONE | Valid by construction |
| `tone_mode` | ToneMode | enum | NEUTRAL | Valid by construction |
| `pause_profile` | PauseProfile | enum | MINIMAL | Valid by construction |
| `pitch_offset` | int | -2 to +2 | 0 | Silent clamp to [-2, +2] |
| `clarity_mode` | ClarityMode | enum | NORMAL | Valid by construction |

### Validation Changes

Update `VoicePersona.validate()` to:
- Clamp `pace` to [0.8, 1.2] if outside range
- Clamp `pitch_offset` to [-2, +2] if outside range
- Validate enum fields are valid enum members

### Serialization Changes

Update `VoicePersona.to_dict()` and `VoicePersona.from_dict()` to:
- Serialize enum fields as their `.value` string
- Deserialize enum fields from string values (with fallback to defaults for unknown values)
- Handle missing fields in `from_dict()` by using defaults (backward compatibility)

### Out of Scope

- Mode preset selection (Tier 4.2 WO-IMPL-PAS-PRESETS)
- Wiring fields to TTS adapters (Tier 4.2)
- Emphasis context-gating / clamping logic (Tier 4.2)
- Boundary pressure → prosodic mapping (Tier 4.3)
- Salience-based routing (Tier 4.4)
- Updating existing persona lists in adapters (Tier 4.2)

## Implementation Plan

1. Add 4 enum classes to `aidm/schemas/immersion.py` (above VoicePersona)
2. Add 6 fields to VoicePersona dataclass with defaults
3. Update `validate()` — add clamping for `pace` and `pitch_offset`, enum validation
4. Update `to_dict()` — serialize enum `.value`, include new fields
5. Update `from_dict()` — deserialize enums with safe fallback, handle missing keys
6. Run existing tests — expect zero breakage (all new fields have defaults)
7. Add new gate tests (see gate spec below)

## Gate Specification

**New gate:** Gate S (Prosodic Fields)

| Test ID | Assertion | Type |
|---------|-----------|------|
| S-01 | VoicePersona has all 6 new fields with correct defaults | field check |
| S-02 | All 4 enum types exist with correct members | enum check |
| S-03 | `pace` clamps to [0.8, 1.2] silently (test 0.5 → 0.8, 1.5 → 1.2) | boundary |
| S-04 | `pitch_offset` clamps to [-2, +2] silently (test -5 → -2, 10 → +2) | boundary |
| S-05 | `to_dict()` serializes enum fields as strings | serialization |
| S-06 | `from_dict()` round-trips all fields correctly | serialization |
| S-07 | `from_dict()` with missing prosodic fields uses defaults (backward compat) | backward compat |
| S-08 | `from_dict()` with unknown enum value falls back to default | resilience |
| S-09 | `validate()` returns no errors for valid prosodic fields | validation |
| S-10 | `validate()` clamps out-of-range values (does not error) | validation |
| S-11 | Existing adapter persona lists still load without error | regression |
| S-12 | Full suite regression | regression |

**Expected test count:** 12 new Gate S tests.

## Integration Seams

- `aidm/schemas/immersion.py` lines 74-159 — VoicePersona dataclass (primary target)
- `aidm/immersion/chatterbox_tts_adapter.py` — imports VoicePersona, has persona lists (must not break)
- `aidm/immersion/kokoro_tts_adapter.py` — imports VoicePersona, has persona lists (must not break)
- `aidm/immersion/tts_adapter.py` — TTSAdapter protocol uses VoicePersona (signature unchanged)

## Assumptions to Validate

1. Existing `from_dict()` tolerates unknown keys (verify it uses `.get()` with defaults, not strict parsing)
2. Adapter persona lists (`_CHATTERBOX_PERSONAS`, `_KOKORO_PERSONAS`) construct VoicePersona without keyword args for new fields — verify defaults apply cleanly
3. No test fixtures hard-code VoicePersona field lists that would break with new fields

## Preflight

```bash
python scripts/preflight_canary.py
python -m pytest tests/ -x --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py
```

## Delivery Footer

**Commit requirement:** After all tests pass, commit changes with a descriptive message referencing this WO ID.
**Debrief format:** CODE — 500 words max, 5 sections + Radar (3 lines).
**Radar bank:** (1) Anything that broke unexpectedly, (2) Anything that was harder than expected, (3) Anything the next WO should know.

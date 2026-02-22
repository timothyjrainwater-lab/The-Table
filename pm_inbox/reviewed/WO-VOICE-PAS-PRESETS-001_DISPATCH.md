# WO-VOICE-PAS-PRESETS-001 — Mode-Based Prosodic Preset Selection

**Type:** CODE
**Priority:** BURST-001 Tier 4.2
**Depends on:** WO-VOICE-PAS-FIELDS-001 (ACCEPTED, 31 Gate S, `8df5718`)
**Blocked by:** Nothing — ready to dispatch

---

## Target Lock

Wire 4 prosodic mode presets (Operator, Combat, Scene, Reflection) into the TTS pipeline. SessionOrchestrator selects a preset based on session state, overlays it onto the current VoicePersona, and passes it to TTS. Emphasis is clamped per mode ceiling. No new TTS backends — adapters already consume VoicePersona fields.

## Binary Decisions (all resolved)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Where do presets live? | New file `aidm/immersion/prosodic_preset_manager.py` | Immersion concern, not TTS-specific |
| 2 | Where does mode → preset mapping live? | `SessionOrchestrator._synthesize_tts()` | Orchestrator knows session state |
| 3 | How are presets defined? | Hardcoded VoicePersona objects (Phase 1) | Simple, versionable, no file I/O |
| 4 | Override or merge? | Merge — preset overlays prosodic fields onto NPC persona, keeps voice identity | Playbook §6.2 |
| 5 | Emphasis clamping? | Per-mode ceiling in PresetManager, not in VoicePersona.validate() | PAS v0.1 safety constraints |

## Contract Spec

**Source:** Voice-First Reliability Playbook §6.2 (mode presets), PROSODIC_SCHEMA_DRAFT.md §6 (emphasis clamping)

### 4 Mode Presets

| Mode | pace | tone_mode | clarity_mode | pause_profile | emphasis_ceiling |
|------|------|-----------|-------------|---------------|-----------------|
| Operator | 1.0 | DIRECTIVE | HIGH | MINIMAL | LOW |
| Combat | 1.05 | COMBAT | NORMAL | MINIMAL | HIGH |
| Scene | 0.92 | CALM | NORMAL | MODERATE | MEDIUM |
| Reflection | 0.9 | REFLECTIVE | NORMAL | MODERATE | MEDIUM |

### Session State → Preset Mode Mapping

| SessionState | Preset Mode |
|---|---|
| COMBAT | combat |
| EXPLORATION | scene |
| REST | reflection |
| DIALOGUE | scene |

### Emphasis Clamping

```python
_EMPHASIS_CEILING = {
    "operator": EmphasisLevel.LOW,
    "combat": EmphasisLevel.HIGH,
    "scene": EmphasisLevel.MEDIUM,
    "reflection": EmphasisLevel.MEDIUM,
}
```

If `emphasis_level > ceiling` for the active mode, clamp to ceiling silently.

### Merge Behavior

When applying a preset to an existing NPC persona:
- **Overwrite:** pace, tone_mode, clarity_mode, pause_profile, emphasis_level (clamped), pitch_offset
- **Preserve:** persona_id, name, voice_model, speed, pitch, reference_audio, exaggeration

This ensures an NPC keeps their voice identity while adopting the mode's prosodic style.

## Implementation Plan

### 1. Create `aidm/immersion/prosodic_preset_manager.py` (NEW)

```python
class ProsodicPresetManager:
    """Mode-based prosodic preset selection with emphasis clamping."""

    def get_preset(self, mode: str) -> dict:
        """Return prosodic field dict for mode."""

    def apply_preset(self, persona: VoicePersona, mode: str) -> VoicePersona:
        """Overlay preset fields onto persona. Preserves voice identity."""

    def clamp_emphasis(self, mode: str, requested: EmphasisLevel) -> EmphasisLevel:
        """Clamp emphasis to mode ceiling."""
```

Contains the 4 preset definitions and emphasis ceiling table.

### 2. Update `aidm/runtime/session_orchestrator.py` (MODIFY)

- Add `_SESSION_TO_PRESET_MODE` mapping dict
- Initialize `ProsodicPresetManager` in `__init__`
- Update `_synthesize_tts()`:
  1. Resolve preset mode from `self._session_state`
  2. Get or create VoicePersona
  3. Apply preset via `self._preset_manager.apply_preset(persona, mode)`
  4. Log preset selection: `logger.debug("Applying %s prosodic preset", mode)`
  5. Pass to `self._tts.synthesize(text, persona=persona)`

### 3. Tests (NEW gate)

### Out of Scope

- Boundary pressure → prosodic mapping (Tier 4.3 WO-IMPL-PRESSURE-ALERTS)
- Salience-based TTS routing / line skipping (Tier 4.4 WO-IMPL-SALIENCE-FILTER)
- Updating TTS protocol signature (not needed — persona already carries fields)
- Config-file-driven presets (Phase 2, if ever needed)

## Gate Specification

**New gate:** Gate T (Prosodic Presets)

| Test ID | Assertion | Type |
|---------|-----------|------|
| T-01 | ProsodicPresetManager returns correct preset for "operator" mode | field check |
| T-02 | ProsodicPresetManager returns correct preset for "combat" mode | field check |
| T-03 | ProsodicPresetManager returns correct preset for "scene" mode | field check |
| T-04 | ProsodicPresetManager returns correct preset for "reflection" mode | field check |
| T-05 | Unknown mode falls back to "scene" (safe default) | fallback |
| T-06 | apply_preset overlays prosodic fields onto persona | merge |
| T-07 | apply_preset preserves voice identity fields (persona_id, voice_model, reference_audio) | merge |
| T-08 | Emphasis clamping: combat mode allows HIGH | boundary |
| T-09 | Emphasis clamping: operator mode clamps HIGH → LOW | boundary |
| T-10 | Emphasis clamping: scene mode clamps HIGH → MEDIUM | boundary |
| T-11 | SessionState.COMBAT maps to "combat" preset | mapping |
| T-12 | SessionState.EXPLORATION maps to "scene" preset | mapping |
| T-13 | SessionState.REST maps to "reflection" preset | mapping |
| T-14 | SessionState.DIALOGUE maps to "scene" preset | mapping |
| T-15 | Full suite regression | regression |

**Expected test count:** 15 new Gate T tests.

## Integration Seams

- `aidm/schemas/immersion.py` — VoicePersona with prosodic fields (read-only, from 4.1)
- `aidm/immersion/prosodic_preset_manager.py` — NEW file, preset logic
- `aidm/runtime/session_orchestrator.py` lines 1008-1034 — `_synthesize_tts()` (modify)
- `aidm/immersion/emotion_router.py` — pattern reference for mood → selection (read-only)
- `aidm/immersion/chatterbox_tts_adapter.py` — already accepts mood param (read-only)

## Assumptions to Validate

1. `SessionState` enum is importable from `aidm.runtime.session_orchestrator` — verify it's not buried in a private scope
2. `_synthesize_tts()` currently creates VoicePersona from string voice_id via `_resolve_persona` — verify the persona object is available before TTS call (not just a string ID)
3. Existing tests mock `self._tts` — verify preset application doesn't break mock expectations

## Files to Read

1. `aidm/schemas/immersion.py` — VoicePersona + enums (just added in 4.1)
2. `aidm/runtime/session_orchestrator.py` — `_synthesize_tts()`, `SessionState`, `__init__`
3. `aidm/immersion/emotion_router.py` — pattern reference
4. `docs/planning/PROSODIC_SCHEMA_DRAFT.md` — emphasis clamping spec
5. `pm_inbox/reviewed/legacy_pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md` §6.2 — preset values

## Preflight

```bash
python scripts/preflight_canary.py
python -m pytest tests/test_prosodic_fields.py -v
python -m pytest tests/ -x --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py
```

## Delivery Footer

**Commit requirement:** After all tests pass, commit changes with a descriptive message referencing this WO ID.
**Debrief format:** CODE — 500 words max, 5 sections + Radar (3 lines).
**Radar bank:** (1) Anything that broke unexpectedly, (2) Anything that was harder than expected, (3) Anything the next WO should know.

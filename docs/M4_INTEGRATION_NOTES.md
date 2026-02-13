# M4 Integration Notes — Immersion Layer Forward Compatibility

**Status**: M3 Complete, M4 Not Started
**Last Updated**: 2026-02-09
**Owner**: Agent C (Immersion Layer)

---

## Purpose

This document provides forward-looking integration guidance for **M4 — Spellcasting & Magic System** (Agent A's upcoming work). It identifies hooks, compatibility points, and architectural constraints to ensure M4 can safely integrate with the M3 immersion layer without requiring breaking changes.

---

## 1. Architectural Guarantees

### 1.1 Authority Boundary (IMMUTABLE)

**M3 Contract**: Immersion is **non-authoritative**. All immersion outputs are atmospheric only.

**M4 Implications**:
- Engine resolves all spell effects, damage, saves, durations, concentration
- Immersion may **read** spell state for audio/visual cues
- Immersion must **never write** spell state or influence mechanics

**Enforcement**:
- `tests/test_immersion_authority_contract.py` mechanically blocks imports of engine mutators
- AST-based import boundary analysis prevents accidental authority violations
- Deepcopy tests ensure immersion functions never mutate input `WorldState`

**Action for M4**: No changes required to immersion. Agent A owns all spell mechanics.

---

### 1.2 API Stability (PUBLIC_STABLE)

**M3 Contract**: All symbols in `aidm.immersion.__all__` are frozen as of M3 completion.

**Frozen Exports** (16 symbols):
- Protocols: `STTAdapter`, `TTSAdapter`, `AudioMixerAdapter`, `ImageAdapter`
- Defaults: `StubSTTAdapter`, `StubTTSAdapter`, `StubAudioMixerAdapter`, `StubImageAdapter`
- Factories: `create_stt_adapter`, `create_tts_adapter`, `create_audio_mixer`, `create_image_adapter`
- Pure functions: `compute_scene_audio_state`, `compute_grid_state`
- Attribution: `AttributionStore`
- Schemas: `aidm.schemas.immersion` (10 dataclasses)

**M4 Constraints**:
- May **add** new exports (e.g., `compute_spell_visual_effect`)
- May **add** optional parameters to pure functions (with defaults)
- Must **not remove** or **rename** existing exports without migration plan
- Must **not change** existing function signatures in breaking ways

**Action for M4**: Extend, don't replace. Add new pure functions for spell visuals if needed.

---

## 2. FUTURE_HOOK Integration Points

M3 includes no-op `FUTURE_HOOK` comments marking safe integration points for M4. These are **placeholders only** — they do nothing mechanically but signal where M4 features can safely plug in.

### 2.1 Audio: Condition-Driven Cues

**Location**: `aidm/immersion/audio_mixer.py:49-54`

**Hook**:
```python
# FUTURE_HOOK: condition-driven audio cues (M4+)
#   When conditions system gains duration tracking, entity conditions
#   could influence mood (e.g., party-wide fear → "dramatic").
#   Add elif branch here checking entity conditions from scene_card.
#   Must remain pure — read conditions, never write them.
```

**M4 Integration**:
- If `scene_card` includes `entity_conditions: Dict[str, List[str]]`, add mood logic:
  ```python
  elif scene_card.get("entity_conditions"):
      conditions = scene_card["entity_conditions"]
      if any("fear" in conds for conds in conditions.values()):
          mood = "dramatic"
          reason = "party afflicted by fear"
  ```
- **Constraint**: Must be deterministic (same conditions → same mood)
- **Test**: Add test cases to `tests/test_audio_transitions.py`

---

### 2.2 Audio: Concentration & Duration Moods

**Location**: `aidm/immersion/audio_mixer.py:55-59`

**Hook**:
```python
# FUTURE_HOOK: concentration/duration moods (M4+)
#   Spell concentration or effect durations could add a "dramatic"
#   mood when high-stakes spells are sustained.
#   Add elif branch here checking active spell effects from scene_card.
```

**M4 Integration**:
- If spellcasting includes concentration tracking in `world_state` or `scene_card`:
  ```python
  elif scene_card.get("concentration_spells"):
      mood = "dramatic"
      reason = "concentration spell active"
  ```
- **Constraint**: Pure function — read concentration state, don't resolve it
- **Example**: If wizard concentrates on *wall of force*, audio mood shifts to "dramatic"

---

### 2.3 Grid: AoE Visualization Overlays

**Location**: `aidm/immersion/contextual_grid.py:49-54`

**Hook**:
```python
# FUTURE_HOOK: AoE visualization overlays (M4+)
#   When spellcasting system is integrated, AoE templates
#   (fireball radius, cone of cold, etc.) could be rendered
#   as grid overlays. Extract AoE data from active_combat
#   or scene_card and return as additional overlay data.
#   Must remain pure — read AoE shapes, never resolve damage.
```

**M4 Integration**:
- **Option A**: Extend `GridRenderState` schema with `aoe_overlays: List[AoEOverlay]`
  - Add new dataclass `AoEOverlay(shape: str, origin: (int, int), radius: int)`
  - Return AoE templates from `compute_grid_state()` for visualization only
- **Option B**: Create new pure function `compute_spell_overlays(world_state) -> List[AoEOverlay]`
  - Keeps grid computation separate from spell visualization
  - Recommended if AoE logic is complex

**Constraint**: Overlays are **visual only**. Damage resolution stays in engine.

**Example**:
```python
# In M4, if active_combat includes prepared spells:
aoe_overlays = []
if scene_card.get("prepared_aoe_spells"):
    for spell in scene_card["prepared_aoe_spells"]:
        aoe_overlays.append(AoEOverlay(
            shape=spell["shape"],  # "sphere", "cone", "line"
            origin=(spell["x"], spell["y"]),
            radius=spell["radius"],
        ))
# Return in GridRenderState or separate function output
```

---

### 2.4 Grid: Terrain Overlay Rendering

**Location**: `aidm/immersion/contextual_grid.py:56-60`

**Hook**:
```python
# FUTURE_HOOK: terrain overlay rendering (M4+)
#   Scene cards may include terrain features (difficult terrain,
#   walls, water, elevation). These could be extracted here
#   and returned as overlay cells for the grid renderer.
#   Must remain atmospheric — terrain rules stay in engine.
```

**M4 Integration**:
- If terrain affects spell targeting (e.g., *wall of stone*, *grease*):
  - Extract terrain cells from `scene_card["terrain"]`
  - Return as `terrain_cells: List[TerrainCell]` in `GridRenderState`
- **Constraint**: Visualization only — engine enforces terrain movement penalties

---

## 3. Schema Extension Patterns

### 3.1 Adding Optional Fields

If M4 needs to extend existing schemas (e.g., `SceneAudioState`, `GridRenderState`):

**Safe Pattern**:
```python
@dataclass
class GridRenderState:
    visible: bool
    reason: str
    entity_positions: List[GridEntityPosition]
    dimensions: tuple
    aoe_overlays: List[AoEOverlay] = field(default_factory=list)  # M4 addition
```

**Requirements**:
- Use `field(default_factory=...)` for new fields
- Update `to_dict()`, `from_dict()`, `validate()` methods
- Add tests to `tests/test_immersion_schemas.py`
- Update schema validation constants if needed

**Forbidden**:
- Removing existing fields (breaks M3 contracts)
- Renaming fields without migration plan
- Changing field types in incompatible ways

---

### 3.2 Adding New Schemas

M4 may add new immersion schemas (e.g., `SpellVisualEffect`, `AoEOverlay`):

**Pattern**:
1. Add dataclass to `aidm/schemas/immersion.py`
2. Follow existing conventions: `to_dict()`, `from_dict()`, `validate()`
3. Add tests to `tests/test_immersion_schemas.py`
4. Re-export from `aidm/immersion/__init__.py` (update `__all__`)

**Example**:
```python
@dataclass
class AoEOverlay:
    shape: str  # "sphere", "cone", "line", "cube"
    origin: tuple  # (x, y)
    radius: int
    color: str = "red"  # visual hint only

    def to_dict(self) -> dict: ...
    @staticmethod
    def from_dict(d: dict) -> "AoEOverlay": ...
    def validate(self) -> None: ...
```

---

## 4. Adapter Extension (Optional)

### 4.1 Spell Visual Effects Adapter

If M4 wants rich spell animations (particle effects, shader overlays), consider adding:

**New Adapter** (optional):
```python
# aidm/immersion/spell_visual_adapter.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class SpellVisualAdapter(Protocol):
    def render_spell_effect(
        self,
        spell_name: str,
        effect_type: str,  # "cast", "impact", "sustain"
        position: tuple,
    ) -> bytes:
        """Return animation/shader data for spell effect."""
        ...

    def is_available(self) -> bool:
        ...
```

**Stub Implementation**:
```python
class StubSpellVisualAdapter:
    def render_spell_effect(self, spell_name, effect_type, position):
        return b""  # No-op

    def is_available(self):
        return True
```

**Factory**:
```python
def create_spell_visual_adapter(backend: str = "stub") -> SpellVisualAdapter:
    ...
```

**Action**: Only add if needed. Immersion stubs work fine with zero spell visuals.

---

## 5. Testing Requirements for M4

### 5.1 Determinism Preservation

**Critical**: All new immersion functions reading spell state must remain **deterministic**.

**Test Pattern**:
```python
def test_spell_audio_determinism():
    scene_card = {"concentration_spells": [{"name": "wall of force"}]}
    state1 = compute_scene_audio_state(world_state, scene_card)
    state2 = compute_scene_audio_state(world_state, scene_card)
    assert state1.to_dict() == state2.to_dict()
```

Add to `tests/test_immersion_determinism_canary.py` (created in C3-02).

---

### 5.2 Non-Mutation Tests

**Critical**: Ensure new functions reading spell state don't mutate `WorldState`.

**Test Pattern**:
```python
def test_spell_overlays_no_mutation():
    ws = WorldState(entities={"wizard": {"spells_prepared": ["fireball"]}})
    ws_copy = deepcopy(ws)
    _ = compute_spell_overlays(ws)
    assert ws.to_dict() == ws_copy.to_dict()
```

Add to `tests/test_immersion_authority_contract.py`.

---

### 5.3 Import Boundary Validation

**Critical**: If M4 adds new immersion modules, update whitelisted imports.

**Action**:
```python
# tests/test_immersion_authority_contract.py
_ALLOWED_AIDM_IMPORTS = frozenset({
    "aidm.schemas.immersion",
    "aidm.core.state",
    "aidm.immersion",
    "aidm.immersion.spell_visual_adapter",  # Add if created
    # ...
})
```

---

## 6. Dependency Isolation

### 6.1 Zero External Dependencies (Maintained)

M3 immersion has **zero external dependencies** beyond stdlib and existing aidm modules.

**M4 Constraint**: Spell visual effects must not require external libraries in **stub mode**.

**Pattern**:
- Stub adapters return empty/placeholder data (`b""`, `"[stub effect]"`)
- Real adapters (if added) can require external deps (e.g., `pillow`, `pygame`)
- Factory pattern isolates dependency loading:
  ```python
  def create_spell_visual_adapter(backend: str = "stub"):
      if backend == "stub":
          return StubSpellVisualAdapter()  # Zero deps
      elif backend == "animated":
          import pygame  # Only loaded if requested
          return AnimatedSpellVisualAdapter()
  ```

**Test**: `tests/test_immersion_hardening.py::test_immersion_has_zero_external_dependencies`

---

## 7. Performance Constraints

### 7.1 Duration Budget

M3 immersion tests run in **sub-millisecond time** (zero presence in `pytest --durations=25`).

**M4 Constraint**: New immersion functions must remain **fast** (no network calls, no heavy computation in pure functions).

**Guideline**:
- Pure functions: < 1ms per call
- Adapter stubs: < 1ms per call
- Real adapters (if added): May be slower, but stubs must stay fast

**Monitoring**: Run `pytest --durations=25` after M4 integration. Immersion tests should remain sub-millisecond.

---

## 8. Rollout Strategy (Recommendation)

### Phase 1: Engine-Only Spellcasting (M4 Core)
- Agent A implements spell resolution in engine
- No immersion integration yet
- Spells resolve correctly, no audio/visual cues

### Phase 2: Read-Only Immersion Hooks (M4 Polish)
- Add spell state to `scene_card` (e.g., `concentration_spells`, `prepared_aoe_spells`)
- Immersion reads spell state for mood/overlays (via FUTURE_HOOK points)
- No new adapters needed — use existing `compute_scene_audio_state`, `compute_grid_state`

### Phase 3: Rich Spell Visuals (Post-M4, Optional)
- Add `SpellVisualAdapter` if desired
- Implement real backends (animated effects, shaders, etc.)
- Stubs remain no-op — zero breaking changes to existing code

**Recommended**: Start with Phase 1–2. Phase 3 is optional polish.

---

## 9. Open Questions for Agent A

### 9.1 Spell State Representation

**Question**: How will spell state be exposed in `world_state` or `scene_card`?

**Options**:
- **A**: Add `active_spells: List[dict]` to `world_state.active_combat`
- **B**: Add `concentration_spells`, `prepared_aoe_spells` to `scene_card`
- **C**: Create new `world_state.spell_state` top-level field

**Recommendation**: Option B (scene_card). Keeps spell state in atmospheric context, aligns with existing `scene_card` pattern.

---

### 9.2 AoE Targeting Data

**Question**: Will AoE targeting data be available before damage resolution?

**Context**: For grid overlay visualization, immersion needs AoE shape/position **before** damage is applied.

**Requirement**: If yes, expose as `scene_card["prepared_aoe_spells"]`. If no, grid overlays may only show post-resolution (less useful but acceptable).

---

### 9.3 Condition Duration Tracking

**Question**: Will condition durations be tracked in a way immersion can read?

**Context**: For audio mood transitions (e.g., "party is feared for 3 rounds → dramatic mood").

**Requirement**: If yes, expose as `scene_card["entity_conditions"]`. If no, skip condition-driven audio (acceptable for M4).

---

## 10. Contact & Coordination

**Immersion Owner**: Agent C (this agent)
**Spellcasting Owner**: Agent A (M4 milestone)

**Coordination Points**:
- Before M4 starts: Agree on spell state representation (Q9.1)
- During M4: Agent A adds spell state to `scene_card`, Agent C reads it (no writes)
- After M4: Joint testing of audio/grid spell integration

**Handoff Document**: See `docs/IMMERSION_HANDOFF.md` (created in C4-01)

---

## 11. Summary Checklist for M4

- [ ] Spell state exposed in `scene_card` (Agent A)
- [ ] Audio mood logic reads spell state via FUTURE_HOOK points (Agent C, if needed)
- [ ] Grid overlays show AoE templates if targeting data available (Agent C, if needed)
- [ ] New immersion functions pass determinism tests
- [ ] New immersion functions pass non-mutation tests
- [ ] Import boundary validation updated if new modules added
- [ ] Duration profiling shows immersion tests remain sub-millisecond
- [ ] M3 API stability preserved (no removed/renamed exports)

---

**End of M4 Integration Notes**

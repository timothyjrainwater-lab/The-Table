# WO-052: Lens Voice Resolver — Spark-Driven Voice Characterization
**Dispatched by:** Opus (PM)
**Date:** 2026-02-12
**Phase:** Immersion (Voice Pipeline) / Lens Layer
**Priority:** Batch 2 (depends on WO-051 research)
**Status:** DISPATCHED

---

## Objective

Build the Lens function that translates LLM voice descriptions into concrete `VoicePersona` objects. This is the bridge between the Spark's creative output ("gravelly baritone with a menacing edge") and the TTS adapter's mechanical input (`pitch=0.8, speed=0.9, exaggeration=0.7, reference_audio="voices/deep_male.wav"`).

---

## Context

The Spark (LLM) produces narration and dialogue. When a new NPC is introduced, the system needs a distinct voice for that character. Currently, every character uses the same default persona.

The Lens layer already mediates between Box mechanical state and Spark narrative output (NarrativeBrief, ContextAssembler). This work order extends the Lens to mediate voice characterization:

```
Spark (LLM) → voice description → Lens Voice Resolver → VoicePersona → TTS Adapter
```

The Voice Resolver has two responsibilities:
1. **Prompt Script** — A structured prompt template the Lens sends to the Spark to extract voice characteristics for a new character
2. **Description→Persona Mapping** — Parse the Spark's response into a concrete VoicePersona with all fields populated

---

## Deliverables

### 1. Voice Characterization Prompt Script

Create a structured prompt template in `aidm/lens/voice_resolver.py` that the Lens sends to the Spark when a new speaking character is introduced:

```python
VOICE_CHARACTERIZATION_PROMPT = """
Describe this character's voice for text-to-speech synthesis.

Character: {character_name}
Context: {character_description}

Respond with EXACTLY these fields:
- pitch: low / medium-low / medium / medium-high / high
- timbre: warm / harsh / gravelly / smooth / nasal / breathy / resonant / thin
- pace: slow / measured / moderate / quick / clipped
- intensity: subdued / moderate / dramatic / booming
- age_quality: youthful / mature / elderly / ageless
- accent_notes: (any accent or speech pattern notes)
- emotional_baseline: stoic / cheerful / menacing / weary / serene / anxious
"""
```

The prompt must:
- Extract structured voice parameters the resolver can parse
- Be deterministic enough to produce consistent results across LLM calls
- Include character context so the LLM can infer voice from personality/race/class
- Map to VoicePersona fields (pitch, speed, exaggeration, reference_audio selection)

### 2. Voice Resolver Function

```python
def resolve_voice(
    character_name: str,
    character_description: str,
    voice_description: Optional[str] = None,
    available_references: Optional[List[str]] = None,
) -> VoicePersona:
    """Resolve a character to a VoicePersona.

    If voice_description is provided, parse it directly.
    If not, return a prompt script for the Spark to fill.

    Maps descriptive terms to numeric VoicePersona parameters:
    - "low pitch" → pitch=0.75
    - "gravelly timbre" → select deep_male reference + exaggeration=0.6
    - "quick pace" → speed=1.2
    - "dramatic intensity" → exaggeration=0.7

    Selects reference_audio from available_references based on
    best match to voice description.
    """
```

### 3. Archetype Matching Table

Hard-coded mapping from descriptive terms to VoicePersona parameters:

```python
PITCH_MAP = {
    "low": 0.7, "medium-low": 0.85, "medium": 1.0,
    "medium-high": 1.1, "high": 1.25,
}

PACE_MAP = {
    "slow": 0.8, "measured": 0.9, "moderate": 1.0,
    "quick": 1.15, "clipped": 1.25,
}

INTENSITY_MAP = {
    "subdued": 0.2, "moderate": 0.4, "dramatic": 0.7, "booming": 0.9,
}
```

### 4. Voice Cache

Characters should keep their resolved voice across the session:

```python
class VoiceRoster:
    """Caches VoicePersona per character for session consistency."""

    def get_or_resolve(self, character_id: str, ...) -> VoicePersona
    def set_voice(self, character_id: str, persona: VoicePersona)
    def list_assigned(self) -> Dict[str, VoicePersona]
```

### 5. Tests

Create `tests/lens/test_voice_resolver.py`:
- Prompt script generation (character context → prompt string)
- Description parsing (voice description string → VoicePersona)
- Archetype mapping (term → numeric value for each field)
- Voice cache (get/set/consistency)
- Reference audio selection (best match from available list)
- Edge cases (missing fields, unknown terms, empty descriptions)

Target: 20+ tests, all unit tests (no LLM calls needed — mock the Spark response)

---

## File Structure

```
aidm/lens/voice_resolver.py     — VoiceResolver, VoiceRoster, prompt scripts
tests/lens/test_voice_resolver.py — Unit tests
```

---

## Dependencies

- `aidm/schemas/immersion.py` — VoicePersona (already has reference_audio, exaggeration fields)
- `aidm/lens/` — Existing Lens layer (NarrativeBrief, ContextAssembler)
- WO-051 research output — Archetype recipes inform the mapping table

---

## Constraints

- No LLM calls in the resolver itself — it produces prompts and parses responses, but doesn't call the Spark directly
- The resolver is a pure function: description in → VoicePersona out
- Voice cache is session-scoped (not persisted across sessions)
- Reference audio selection uses string matching, not embedding similarity (keep it simple)
- All mapping values must be within VoicePersona validation ranges (speed: 0.5-2.0, pitch: 0.5-2.0, exaggeration: 0.0-1.0)

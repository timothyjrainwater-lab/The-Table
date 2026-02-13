"""WO-052: Lens Voice Resolver — Spark-Driven Voice Characterization

The Voice Resolver translates LLM voice descriptions into concrete VoicePersona objects.
This is the bridge between the Spark's creative output ("gravelly baritone with a menacing edge")
and the TTS adapter's mechanical input (pitch=0.8, speed=0.9, exaggeration=0.7, reference_audio="voices/deep_male.wav").

LAYER ARCHITECTURE:
- Lens layer component — mediates between Spark (LLM) and TTS adapters
- Produces prompt scripts for Spark to generate voice descriptions
- Parses voice descriptions into VoicePersona objects with concrete parameters
- VoiceRoster caches resolved voices for session consistency

VOICE CHARACTERIZATION FLOW:
1. New speaking character introduced
2. Lens sends VOICE_CHARACTERIZATION_PROMPT to Spark with character context
3. Spark returns structured voice description (pitch, timbre, pace, intensity, etc.)
4. resolve_voice() parses description into VoicePersona
5. VoiceRoster caches persona for character_id
6. TTS adapter uses VoicePersona for synthesis

BOUNDARY LAW (BL-003): Lens layer — no imports from Box internals.
AXIOM 3: Lens adapts stance — we present voice parameters, not compute TTS.

Reference: pm_inbox/OPUS_WO-052_LENS_VOICE_RESOLVER.md
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from aidm.schemas.immersion import VoicePersona


# ==============================================================================
# VOICE CHARACTERIZATION PROMPT
# ==============================================================================

VOICE_CHARACTERIZATION_PROMPT = """Describe this character's voice for text-to-speech synthesis.

Character: {character_name}
Context: {character_description}

Respond with EXACTLY these fields (one per line):
- pitch: low / medium-low / medium / medium-high / high
- timbre: warm / harsh / gravelly / smooth / nasal / breathy / resonant / thin
- pace: slow / measured / moderate / quick / clipped
- intensity: subdued / moderate / dramatic / booming
- age_quality: youthful / mature / elderly / ageless
- accent_notes: (any accent or speech pattern notes, or "none")
- emotional_baseline: stoic / cheerful / menacing / weary / serene / anxious

Example response:
pitch: low
timbre: gravelly
pace: measured
intensity: booming
age_quality: elderly
accent_notes: scottish highland accent
emotional_baseline: weary
"""


# ==============================================================================
# ARCHETYPE MAPPING TABLES
# ==============================================================================

PITCH_MAP = {
    "low": 0.7,
    "medium-low": 0.85,
    "medium": 1.0,
    "medium-high": 1.1,
    "high": 1.25,
}

PACE_MAP = {
    "slow": 0.8,
    "measured": 0.9,
    "moderate": 1.0,
    "quick": 1.15,
    "clipped": 1.25,
}

INTENSITY_MAP = {
    "subdued": 0.2,
    "moderate": 0.4,
    "dramatic": 0.7,
    "booming": 0.9,
}

# Timbre → reference audio selection hints
TIMBRE_REFERENCE_HINTS = {
    "warm": ["warm", "smooth", "resonant"],
    "harsh": ["harsh", "rough"],
    "gravelly": ["gravelly", "rough", "deep"],
    "smooth": ["smooth", "warm"],
    "nasal": ["nasal", "thin"],
    "breathy": ["breathy", "soft"],
    "resonant": ["resonant", "deep", "warm"],
    "thin": ["thin", "high"],
}

# Age quality → pitch/speed adjustments
AGE_QUALITY_ADJUSTMENTS = {
    "youthful": {"pitch_modifier": 1.1, "speed_modifier": 1.05},
    "mature": {"pitch_modifier": 1.0, "speed_modifier": 1.0},
    "elderly": {"pitch_modifier": 0.95, "speed_modifier": 0.9},
    "ageless": {"pitch_modifier": 1.0, "speed_modifier": 1.0},
}


# ==============================================================================
# FREE-TEXT KEYWORD → ATTRIBUTE MAPPINGS
# ==============================================================================
# Maps descriptive keywords found in free-text voice descriptions back to
# the structured attribute values used by the maps above.

FREETEXT_PITCH_KEYWORDS: Dict[str, str] = {
    "deep": "low",
    "bass": "low",
    "baritone": "low",
    "booming": "low",
    "rumbling": "low",
    "low": "low",
    "tenor": "medium",
    "mid": "medium",
    "medium": "medium",
    "alto": "medium-high",
    "high": "high",
    "shrill": "high",
    "squeaky": "high",
    "piercing": "high",
    "soprano": "high",
    "falsetto": "high",
    "reedy": "high",
}

FREETEXT_PACE_KEYWORDS: Dict[str, str] = {
    "slow": "slow",
    "plodding": "slow",
    "drawling": "slow",
    "languid": "slow",
    "deliberate": "measured",
    "measured": "measured",
    "careful": "measured",
    "steady": "moderate",
    "moderate": "moderate",
    "normal": "moderate",
    "quick": "quick",
    "rapid": "quick",
    "fast": "quick",
    "hurried": "quick",
    "brisk": "quick",
    "clipped": "clipped",
    "staccato": "clipped",
    "terse": "clipped",
    "nervous": "quick",
}

FREETEXT_TIMBRE_KEYWORDS: Dict[str, str] = {
    "warm": "warm",
    "rich": "warm",
    "mellow": "warm",
    "harsh": "harsh",
    "rough": "harsh",
    "grating": "harsh",
    "gravelly": "gravelly",
    "gravel": "gravelly",
    "scratchy": "gravelly",
    "raspy": "gravelly",
    "hoarse": "gravelly",
    "smooth": "smooth",
    "silky": "smooth",
    "honeyed": "smooth",
    "velvety": "smooth",
    "nasal": "nasal",
    "whiny": "nasal",
    "breathy": "breathy",
    "whispered": "breathy",
    "airy": "breathy",
    "resonant": "resonant",
    "sonorous": "resonant",
    "thunderous": "resonant",
    "thin": "thin",
    "wispy": "thin",
    "reedy": "thin",
    "melodic": "smooth",
}

FREETEXT_INTENSITY_KEYWORDS: Dict[str, str] = {
    "quiet": "subdued",
    "subdued": "subdued",
    "soft": "subdued",
    "hushed": "subdued",
    "whispering": "subdued",
    "moderate": "moderate",
    "normal": "moderate",
    "dramatic": "dramatic",
    "theatrical": "dramatic",
    "expressive": "dramatic",
    "booming": "booming",
    "thundering": "booming",
    "commanding": "dramatic",
    "bellowing": "booming",
    "loud": "booming",
}

FREETEXT_AGE_KEYWORDS: Dict[str, str] = {
    "youthful": "youthful",
    "young": "youthful",
    "boyish": "youthful",
    "girlish": "youthful",
    "childlike": "youthful",
    "mature": "mature",
    "adult": "mature",
    "elderly": "elderly",
    "aged": "elderly",
    "old": "elderly",
    "wizened": "elderly",
    "ancient": "elderly",
    "ageless": "ageless",
    "ethereal": "ageless",
    "timeless": "ageless",
}

# Style/emotional keywords → emotional_baseline for persona matching
FREETEXT_STYLE_KEYWORDS: Dict[str, str] = {
    "menacing": "menacing",
    "sinister": "menacing",
    "threatening": "menacing",
    "dark": "menacing",
    "villainous": "menacing",
    "evil": "menacing",
    "cheerful": "cheerful",
    "jovial": "cheerful",
    "merry": "cheerful",
    "bright": "cheerful",
    "stoic": "stoic",
    "flat": "stoic",
    "monotone": "stoic",
    "weary": "weary",
    "tired": "weary",
    "exhausted": "weary",
    "serene": "serene",
    "calm": "serene",
    "gentle": "serene",
    "soothing": "serene",
    "peaceful": "serene",
    "anxious": "anxious",
    "nervous": "anxious",
    "jittery": "anxious",
    "fearful": "anxious",
    "gruff": "stoic",
    "commanding": "stoic",
    "authoritative": "stoic",
    "bold": "cheerful",
    "heroic": "cheerful",
    "inspiring": "cheerful",
}


# ==============================================================================
# FREE-TEXT PARSING
# ==============================================================================


def _extract_attributes_from_freetext(description: str) -> Dict[str, str]:
    """Extract voice attributes from a free-text description.

    Scans the description for keywords in each category and returns
    the last-matched structured attribute value per category.

    Args:
        description: Free-text voice description (e.g., "deep gravelly voice")

    Returns:
        Dictionary of attribute category → structured value
    """
    text = description.lower()
    # Tokenize on non-alpha boundaries so "high-pitched" yields "high" and "pitched"
    words = set(re.findall(r"[a-z]+", text))

    attrs: Dict[str, str] = {}

    keyword_maps: List[Tuple[str, Dict[str, str]]] = [
        ("pitch", FREETEXT_PITCH_KEYWORDS),
        ("pace", FREETEXT_PACE_KEYWORDS),
        ("timbre", FREETEXT_TIMBRE_KEYWORDS),
        ("intensity", FREETEXT_INTENSITY_KEYWORDS),
        ("age_quality", FREETEXT_AGE_KEYWORDS),
        ("emotional_baseline", FREETEXT_STYLE_KEYWORDS),
    ]

    for attr_name, keyword_map in keyword_maps:
        for keyword, value in keyword_map.items():
            if keyword in words:
                attrs[attr_name] = value

    return attrs


# ==============================================================================
# PERSONA SCORING
# ==============================================================================


def _score_persona(
    persona: VoicePersona,
    desired_pitch: float,
    desired_speed: float,
    desired_exaggeration: float,
    timbre: str,
    reference_hints: List[str],
) -> float:
    """Score how well a TTS persona matches desired voice attributes.

    Lower score = better match (distance metric).

    Args:
        persona: TTS persona to score
        desired_pitch: Target pitch value
        desired_speed: Target speed value
        desired_exaggeration: Target exaggeration value
        timbre: Desired timbre category
        reference_hints: Timbre-derived hints for reference audio matching

    Returns:
        Distance score (lower is better)
    """
    # Weighted distance across numeric attributes
    pitch_diff = abs(persona.pitch - desired_pitch)
    speed_diff = abs(persona.speed - desired_speed)
    exagg_diff = abs(persona.exaggeration - desired_exaggeration)

    score = (pitch_diff * 3.0) + (speed_diff * 2.0) + (exagg_diff * 1.0)

    # Bonus for reference audio matching timbre hints
    if persona.reference_audio and reference_hints:
        ref_lower = persona.reference_audio.lower()
        for hint in reference_hints:
            if hint in ref_lower:
                score -= 0.5
                break

    # Bonus for persona_id containing timbre-related keywords
    pid = persona.persona_id.lower()
    name_lower = persona.name.lower()
    # Check if persona identity hints at matching characteristics
    if desired_pitch < 0.85 and any(w in pid or w in name_lower for w in ("villain", "elder", "male", "deep")):
        score -= 0.3
    if desired_pitch > 1.1 and any(w in pid or w in name_lower for w in ("young", "female", "high")):
        score -= 0.3
    if desired_exaggeration > 0.6 and any(w in pid or w in name_lower for w in ("villain", "hero", "dramatic")):
        score -= 0.3

    return score


def resolve_voice_from_roster(
    description: str,
    available_personas: List[VoicePersona],
) -> VoicePersona:
    """Resolve a free-text voice description to the best matching persona.

    Extracts keywords from the description, computes target numeric attributes,
    then scores each available persona and returns the closest match.

    Args:
        description: Free-text voice description
        available_personas: List of available TTS personas to choose from

    Returns:
        Best-matching VoicePersona, or first available as fallback
    """
    if not available_personas:
        return VoicePersona(
            persona_id="default",
            name="Default",
            voice_model="default",
            speed=1.0,
            pitch=1.0,
            exaggeration=0.5,
        )

    if not description or not description.strip():
        return available_personas[0]

    # Try structured parsing first (key: value format)
    parsed = _parse_voice_description(description)

    # If structured parsing found nothing useful, try free-text extraction
    if not any(k in parsed for k in ("pitch", "timbre", "pace", "intensity", "age_quality")):
        parsed = _extract_attributes_from_freetext(description)

    # If still nothing matched, return default (first available)
    if not parsed:
        return available_personas[0]

    # Compute target numeric values from parsed attributes
    desired_pitch = PITCH_MAP.get(parsed.get("pitch", "medium"), 1.0)
    desired_speed = PACE_MAP.get(parsed.get("pace", "moderate"), 1.0)
    desired_exaggeration = INTENSITY_MAP.get(parsed.get("intensity", "moderate"), 0.4)

    # Apply age adjustments
    age_quality = parsed.get("age_quality", "mature")
    age_adj = AGE_QUALITY_ADJUSTMENTS.get(age_quality, {"pitch_modifier": 1.0, "speed_modifier": 1.0})
    desired_pitch *= age_adj["pitch_modifier"]
    desired_speed *= age_adj["speed_modifier"]

    # Get timbre hints for reference audio matching
    timbre = parsed.get("timbre", "smooth")
    hints = TIMBRE_REFERENCE_HINTS.get(timbre, [])

    # Score all available personas
    best_persona = available_personas[0]
    best_score = float("inf")

    for persona in available_personas:
        score = _score_persona(
            persona, desired_pitch, desired_speed, desired_exaggeration,
            timbre, hints,
        )
        if score < best_score:
            best_score = score
            best_persona = persona

    return best_persona


# ==============================================================================
# VOICE RESOLVER FUNCTION
# ==============================================================================


def resolve_voice(
    character_name: str,
    character_description: str = "",
    voice_description: Optional[str] = None,
    available_references: Optional[List[str]] = None,
) -> VoicePersona:
    """Resolve a character to a VoicePersona.

    If voice_description is provided, parse it into a VoicePersona.
    If not provided, returns a default persona (caller should generate description via Spark).

    Maps descriptive terms to numeric VoicePersona parameters:
    - "low pitch" → pitch=0.7
    - "gravelly timbre" → select reference with "gravelly" in filename + exaggeration=0.6
    - "quick pace" → speed=1.15
    - "dramatic intensity" → exaggeration=0.7

    Args:
        character_name: Character display name
        character_description: Character context for voice inference
        voice_description: Optional LLM-generated voice description (structured format)
        available_references: Optional list of reference audio file paths

    Returns:
        VoicePersona with all fields populated
    """
    if voice_description is None:
        # Return default persona — caller should prompt Spark for description
        return VoicePersona(
            persona_id=_sanitize_id(character_name),
            name=character_name,
            voice_model="default",
            speed=1.0,
            pitch=1.0,
            exaggeration=0.5,
        )

    # Parse voice description into structured fields
    parsed_fields = _parse_voice_description(voice_description)

    # Map descriptive terms to numeric values
    pitch = PITCH_MAP.get(parsed_fields.get("pitch", "medium"), 1.0)
    pace = PACE_MAP.get(parsed_fields.get("pace", "moderate"), 1.0)
    intensity = INTENSITY_MAP.get(parsed_fields.get("intensity", "moderate"), 0.5)

    # Apply age quality adjustments
    age_quality = parsed_fields.get("age_quality", "mature")
    age_adjustments = AGE_QUALITY_ADJUSTMENTS.get(age_quality, {"pitch_modifier": 1.0, "speed_modifier": 1.0})
    pitch *= age_adjustments["pitch_modifier"]
    pace *= age_adjustments["speed_modifier"]

    # Clamp values to VoicePersona validation ranges
    pitch = max(0.5, min(2.0, pitch))
    pace = max(0.5, min(2.0, pace))
    intensity = max(0.0, min(1.0, intensity))

    # Select reference audio based on timbre hints
    timbre = parsed_fields.get("timbre", "smooth")
    reference_audio = _select_reference_audio(timbre, available_references or [])

    return VoicePersona(
        persona_id=_sanitize_id(character_name),
        name=character_name,
        voice_model="default",
        speed=pace,
        pitch=pitch,
        reference_audio=reference_audio,
        exaggeration=intensity,
    )


def _parse_voice_description(description: str) -> Dict[str, str]:
    """Parse structured voice description into field dict.

    Expected format:
        pitch: low
        timbre: gravelly
        pace: measured
        intensity: booming
        age_quality: elderly
        accent_notes: scottish highland accent
        emotional_baseline: weary

    Args:
        description: Structured voice description text

    Returns:
        Dictionary of field → value
    """
    fields = {}
    for line in description.strip().split("\n"):
        line = line.strip()
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().lower().replace(" ", "_").replace("-", "_")
        value = value.strip().lower()

        fields[key] = value

    return fields


def _select_reference_audio(timbre: str, available_references: List[str]) -> str:
    """Select best reference audio file based on timbre hints.

    Uses simple string matching — checks if timbre hints appear in filename.

    Args:
        timbre: Timbre descriptor (e.g., "gravelly", "smooth")
        available_references: List of reference audio file paths

    Returns:
        Selected reference audio path, or empty string if no match
    """
    if not available_references:
        return ""

    # Get hints for this timbre
    hints = TIMBRE_REFERENCE_HINTS.get(timbre, [])

    # Find first reference with any hint in filename
    for reference in available_references:
        reference_lower = reference.lower()
        for hint in hints:
            if hint in reference_lower:
                return reference

    # No match — return first available
    return available_references[0]


def _sanitize_id(name: str) -> str:
    """Convert character name to valid persona ID.

    Args:
        name: Character display name

    Returns:
        Sanitized ID (lowercase, underscores, alphanumeric)
    """
    # Lowercase, replace spaces with underscores, remove non-alphanumeric
    sanitized = name.lower().replace(" ", "_")
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
    return sanitized or "unknown"


# ==============================================================================
# VOICE ROSTER CACHE
# ==============================================================================


class VoiceRoster:
    """Caches VoicePersona per character for session consistency.

    Characters should keep their resolved voice across the session.
    This cache ensures that once a character's voice is resolved, it remains
    consistent throughout the session.
    """

    def __init__(self):
        """Initialize empty voice roster."""
        self._roster: Dict[str, VoicePersona] = {}

    def get_or_resolve(
        self,
        character_id: str,
        character_name: str,
        character_description: str = "",
        voice_description: Optional[str] = None,
        available_references: Optional[List[str]] = None,
        available_personas: Optional[List[VoicePersona]] = None,
    ) -> VoicePersona:
        """Get cached persona or resolve new one.

        If character_id is in roster, return cached persona.
        Otherwise, resolve using resolve_voice() and cache the result.

        When available_personas is provided and voice_description is free-text,
        scores personas against extracted keywords and returns the best match.

        Args:
            character_id: Unique character identifier
            character_name: Character display name
            character_description: Character context for voice inference
            voice_description: Optional LLM-generated voice description
            available_references: Optional list of reference audio file paths
            available_personas: Optional list of TTS personas to match against

        Returns:
            VoicePersona (cached or newly resolved)
        """
        if character_id in self._roster:
            return self._roster[character_id]

        # When available personas are provided, use roster-based matching
        if available_personas and voice_description:
            persona = resolve_voice_from_roster(
                description=voice_description,
                available_personas=available_personas,
            )
        else:
            # Resolve new persona via structured parsing
            persona = resolve_voice(
                character_name=character_name,
                character_description=character_description,
                voice_description=voice_description,
                available_references=available_references,
            )

        # Cache for future lookups
        self._roster[character_id] = persona
        return persona

    def set_voice(self, character_id: str, persona: VoicePersona):
        """Explicitly set voice for character.

        Args:
            character_id: Unique character identifier
            persona: VoicePersona to cache
        """
        self._roster[character_id] = persona

    def get_voice(self, character_id: str) -> Optional[VoicePersona]:
        """Get cached voice for character.

        Args:
            character_id: Unique character identifier

        Returns:
            Cached VoicePersona, or None if not in roster
        """
        return self._roster.get(character_id)

    def list_assigned(self) -> Dict[str, VoicePersona]:
        """List all assigned voices.

        Returns:
            Dictionary of character_id → VoicePersona
        """
        return self._roster.copy()

    def clear(self):
        """Clear all cached voices (useful for new sessions)."""
        self._roster.clear()

    def count(self) -> int:
        """Get count of assigned voices.

        Returns:
            Number of characters with assigned voices
        """
        return len(self._roster)


# ==============================================================================
# PROMPT GENERATION
# ==============================================================================


def generate_voice_prompt(character_name: str, character_description: str) -> str:
    """Generate voice characterization prompt for Spark.

    Args:
        character_name: Character display name
        character_description: Character context (race, class, personality, etc.)

    Returns:
        Formatted prompt string for Spark
    """
    return VOICE_CHARACTERIZATION_PROMPT.format(
        character_name=character_name,
        character_description=character_description,
    )

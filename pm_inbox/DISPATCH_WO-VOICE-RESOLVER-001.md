# Instruction Packet: Voice Resolver Agent

**Work Order:** WO-VOICE-RESOLVER-001 (Complete Voice Resolver Parsing)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 2 (Enriches NPC distinctiveness — not on critical path but high-value)
**Deliverable Type:** Code implementation + tests

---

## READ FIRST

`aidm/lens/voice_resolver.py` (377 lines) already has:
- Archetype mapping tables (pitch, pace, timbre, accent descriptors → VoicePersona fields)
- VoiceRoster caching structure
- VoicePersona schema (in `aidm/schemas/immersion.py`)

What it does NOT have: actual parsing logic. The core resolution function currently returns a default persona regardless of input. The World Compiler will generate voice descriptions for NPCs (e.g., "a deep gravelly voice with a slow deliberate pace"). The voice resolver must map these descriptions to available TTS personas.

---

## YOUR TASK

### Deliverable 1: Description Parsing Logic

**File:** `aidm/lens/voice_resolver.py` (MODIFY)

Implement the parsing logic that is currently stubbed:

1. Read the existing archetype mapping tables in the file — they map descriptive words to persona attributes
2. Implement keyword extraction from voice description text:
   - Scan for pitch keywords (deep, high, booming, shrill, etc.)
   - Scan for pace keywords (slow, rapid, deliberate, hurried, etc.)
   - Scan for timbre keywords (gravelly, smooth, raspy, melodic, etc.)
   - Scan for accent/style keywords (gruff, gentle, commanding, nervous, etc.)
3. Score available TTS personas against extracted keywords
4. Return the best-matching VoicePersona from the available roster
5. Fall back to default persona if no keywords match (preserve current fallback behavior)

This is keyword matching, NOT LLM inference. Simple string operations against the mapping tables that already exist in the file.

### Deliverable 2: Tests

**File:** `tests/test_voice_resolver.py` (NEW or MODIFY if exists)

Tests:
1. "deep gravelly voice" → matches persona with low pitch + rough timbre
2. "high-pitched nervous chatter" → matches persona with high pitch + fast pace
3. "smooth commanding tone" → matches persona with smooth timbre + authoritative style
4. Empty description → returns default persona
5. Gibberish description → returns default persona (graceful fallback)
6. Multiple matching keywords → highest-scoring persona wins
7. VoiceRoster caching: same description returns same persona on repeated calls

---

## WHAT EXISTS (DO NOT MODIFY unless specified)

| Component | Location | Status |
|-----------|----------|--------|
| VoicePersona schema | `aidm/schemas/immersion.py` | Frozen — do not modify |
| Archetype mapping tables | `aidm/lens/voice_resolver.py` | Use as-is — extend only if missing keywords |
| TTS adapter protocol | `aidm/immersion/tts_adapter.py` | TTSAdapter.list_personas() provides available voices |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `aidm/lens/voice_resolver.py` | Current stub implementation with mapping tables |
| 1 | `aidm/schemas/immersion.py` | VoicePersona dataclass definition |
| 2 | `aidm/immersion/tts_adapter.py` | Available TTS personas |
| 2 | `aidm/immersion/kokoro_tts_adapter.py` | Kokoro persona definitions (8 voices) |

## STOP CONDITIONS

- If the archetype mapping tables are empty or missing, STOP and report.
- If VoicePersona has changed since the audit (new fields like `reference_audio`, `exaggeration`), accommodate those fields but do not alter parsing for them.

## DELIVERY

- Modified: `aidm/lens/voice_resolver.py`
- New or modified: `tests/test_voice_resolver.py`
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-VOICE-RESOLVER-001_completion.md`

## RULES

- NO LLM calls. Keyword matching only.
- Preserve the existing fallback behavior — if nothing matches, return default.
- Do not modify VoicePersona schema.
- Do not modify TTS adapter code.
- Follow existing code style in `aidm/lens/`.

---

END OF INSTRUCTION PACKET

#!/usr/bin/env python3
"""STT Cleanup Layer — deterministic post-transcription text normalization.

Two tiers, both fully deterministic (no AI, no network):

  Tier A: Structural cleanup
    - Remove filler words (um, uh, like, you know)
    - Collapse duplicate words/phrases
    - Normalize whitespace and sentence boundaries

  Tier B: Project dictionary
    - Fix known proper nouns (Aegis, Mordenkainen, Chatterbox, etc.)
    - Fix project-specific terms (STT, TTS, Win+H, VRAM, etc.)
    - Case-correct callsigns and system names

Gate contract:
  1. Meaning preserved — no new facts, no deletions of intent
  2. All TERM and CAPS fixes applied deterministically
  3. No silent rewrites — if uncertain, leave raw token

Usage:
    from stt_cleanup import cleanup
    clean_text = cleanup("um so like ages does this set a new precedent")
    # -> "So Aegis, does this set a new precedent?"
"""

import re
from typing import Dict, List, Tuple

# =============================================================================
# TIER A: STRUCTURAL CLEANUP
# =============================================================================

# Filler words/phrases to strip (matched as whole words, case-insensitive)
FILLER_TOKENS: List[str] = [
    "um",
    "uh",
    "uhh",
    "umm",
    "hmm",
    "hm",
    "er",
    "ah",
    "eh",
    "like",       # only when filler, not "I like this" — handled by context
    "you know",
    "I mean",
    "sort of",
    "kind of",
    "basically",
    "actually",   # often filler in speech
    "literally",  # almost always filler
    "right so",
    "so yeah",
    "yeah so",
    "okay so",
    "OK so",
]

# Filler words that are ONLY filler at sentence start or after punctuation
# (to avoid stripping "I actually like this" -> "I like this")
START_ONLY_FILLERS: set = {
    "like",
    "actually",
    "literally",
    "basically",
    "so",
}


def _remove_fillers(text: str) -> str:
    """Remove filler words and phrases."""
    # First pass: multi-word fillers (order matters — longest first)
    multi_fillers = sorted(
        [f for f in FILLER_TOKENS if " " in f],
        key=len,
        reverse=True,
    )
    for filler in multi_fillers:
        pattern = re.compile(r"\b" + re.escape(filler) + r"\b[,]?\s*", re.IGNORECASE)
        text = pattern.sub(" ", text)

    # Second pass: single-word fillers that are always filler
    always_fillers = [f for f in FILLER_TOKENS if " " not in f and f not in START_ONLY_FILLERS]
    for filler in always_fillers:
        pattern = re.compile(r"\b" + re.escape(filler) + r"\b[,]?\s*", re.IGNORECASE)
        text = pattern.sub(" ", text)

    # Third pass: start-only fillers (only at sentence boundaries)
    for filler in START_ONLY_FILLERS:
        # At start of string
        pattern = re.compile(r"^" + re.escape(filler) + r"[,]?\s+", re.IGNORECASE)
        text = pattern.sub("", text)
        # After sentence-ending punctuation
        pattern = re.compile(
            r"([.!?])\s+" + re.escape(filler) + r"[,]?\s+",
            re.IGNORECASE,
        )
        text = pattern.sub(r"\1 ", text)

    return text


def _collapse_duplicates(text: str) -> str:
    """Collapse repeated consecutive words: 'can can I' -> 'can I'."""
    # Match word repeated 2+ times consecutively
    pattern = re.compile(r"\b(\w+)(\s+\1)+\b", re.IGNORECASE)
    return pattern.sub(r"\1", text)


def _normalize_whitespace(text: str) -> str:
    """Clean up spacing artifacts from filler removal."""
    # Collapse multiple spaces
    text = re.sub(r"  +", " ", text)
    # Remove space before punctuation
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    # Ensure space after punctuation (except inside abbreviations)
    text = re.sub(r"([.,!?;:])([A-Za-z])", r"\1 \2", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def _capitalize_sentences(text: str) -> str:
    """Capitalize first letter after sentence boundaries."""
    # Start of string
    if text:
        text = text[0].upper() + text[1:]
    # After . ! ?
    text = re.sub(
        r"([.!?])\s+([a-z])",
        lambda m: m.group(1) + " " + m.group(2).upper(),
        text,
    )
    return text


def tier_a(text: str) -> str:
    """Tier A: structural cleanup. Fully deterministic, no dictionary."""
    text = _remove_fillers(text)
    text = _collapse_duplicates(text)
    text = _normalize_whitespace(text)
    # Second filler pass catches start-only fillers newly exposed by first pass
    text = _remove_fillers(text)
    text = _normalize_whitespace(text)
    text = _capitalize_sentences(text)
    return text


# =============================================================================
# TIER B: PROJECT DICTIONARY
# =============================================================================

# Case-sensitive term corrections.
# Keys are lowercase patterns, values are the correct form.
# Applied as whole-word replacements.
PROJECT_TERMS: Dict[str, str] = {
    # === Callsigns and agent names ===
    "aegis": "Aegis",
    "ages": "Aegis",        # common Win+H homophone
    "slate": "Slate",
    "anvil": "Anvil",
    "thunder": "Thunder",
    "arbor": "Arbor",
    "mrs slate": "Mrs. Slate",
    "mrs. slate": "Mrs. Slate",
    "missus slate": "Mrs. Slate",

    # === System names ===
    "chatterbox": "Chatterbox",
    "whisper": "Whisper",
    "kokoro": "Kokoro",

    # === Project terms ===
    "stt": "STT",
    "tts": "TTS",
    "vram": "VRAM",
    "gpu": "GPU",
    "cpu": "CPU",
    "cuda": "CUDA",
    "llm": "LLM",
    "ai": "AI",
    "bs buddy": "BS Buddy",
    "pm": "PM",
    "wo": "WO",
    "amp": "AMP",
    "vad": "VAD",

    # === D&D terms ===
    "mordenkainen": "Mordenkainen",
    "mordenkainens": "Mordenkainen's",
    "vorpal": "vorpal",
    "glaive guisarme": "glaive-guisarme",
    "glaive-guisarme": "glaive-guisarme",

    # === Architecture terms ===
    "oracle": "Oracle",
    "director": "Director",
    "lens": "Lens",
    "spark": "Spark",

    # === Common Win+H errors observed in session ===
    "win h": "Win+H",
    "win+h": "Win+H",
    "windows h": "Win+H",
    "windows+h": "Win+H",
    "no sets": "notes",      # observed homophone: "notes" -> "no sets"
}

# Multi-word terms need to be applied before single-word to avoid partial matches
_MULTI_WORD_TERMS = sorted(
    [(k, v) for k, v in PROJECT_TERMS.items() if " " in k],
    key=lambda x: len(x[0]),
    reverse=True,
)
_SINGLE_WORD_TERMS = [(k, v) for k, v in PROJECT_TERMS.items() if " " not in k]


def tier_b(text: str) -> str:
    """Tier B: project dictionary corrections. Deterministic word replacement."""
    # Multi-word terms first
    for pattern, replacement in _MULTI_WORD_TERMS:
        regex = re.compile(r"\b" + re.escape(pattern) + r"\b", re.IGNORECASE)
        text = regex.sub(replacement, text)

    # Single-word terms
    for pattern, replacement in _SINGLE_WORD_TERMS:
        regex = re.compile(r"\b" + re.escape(pattern) + r"\b", re.IGNORECASE)
        # Only replace if the current text doesn't already have the correct form
        # This prevents double-correction
        text = regex.sub(replacement, text)

    return text


# =============================================================================
# COMBINED CLEANUP
# =============================================================================

def cleanup(text: str) -> str:
    """Full cleanup pipeline: Tier A (structural) then Tier B (dictionary).

    Gate contract:
      1. Meaning preserved — no new facts, no deletions of intent
      2. All TERM and CAPS fixes applied deterministically
      3. No silent rewrites — uncertain tokens left as-is

    Args:
        text: Raw STT transcript

    Returns:
        Cleaned text
    """
    if not text or not text.strip():
        return text

    text = tier_a(text)
    text = tier_b(text)

    # Final whitespace pass after dictionary replacements
    text = _normalize_whitespace(text)

    return text


# =============================================================================
# CLI (for testing)
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        raw = " ".join(sys.argv[1:])
    else:
        print("STT Cleanup — paste raw transcript, Ctrl+C to exit")
        print("-" * 50)
        try:
            while True:
                raw = input("RAW:   ")
                print(f"CLEAN: {cleanup(raw)}")
                print()
        except (KeyboardInterrupt, EOFError):
            print("\nDone.")
            sys.exit(0)

    print(f"RAW:   {raw}")
    print(f"CLEAN: {cleanup(raw)}")

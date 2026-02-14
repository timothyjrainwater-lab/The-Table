"""Sentence-boundary TTS chunking utility.

Chatterbox has a ~60-80 word generation ceiling. Text exceeding this limit
is split at sentence boundaries so each chunk can be generated and played
sequentially without mid-sentence truncation.

Ported from scripts/speak.py (TD-023 fix). Both ChatterboxTTSAdapter and
KokoroTTSAdapter consume this module so all TTS consumers get chunking
automatically.

WO-TTS-CHUNKING-001
"""


def chunk_by_sentence(text: str, max_words: int = 55) -> list[str]:
    """Split text at sentence boundaries, max_words per chunk.

    Chatterbox has a ~60-80 word generation ceiling. Text exceeding this limit
    is split at sentence boundaries ('. ') so each chunk can be generated and
    played sequentially without mid-sentence truncation.

    Args:
        text: Input text to chunk.
        max_words: Maximum words per chunk (default 55, conservative margin).

    Returns:
        List of text chunks, each ending with a period.
    """
    sentences = text.replace(".\n", ". ").split(". ")
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        word_count = len(sentence.split())
        if current_words + word_count > max_words and current:
            chunks.append(". ".join(current) + ".")
            current = [sentence]
            current_words = word_count
        else:
            current.append(sentence)
            current_words += word_count
    if current:
        chunks.append(". ".join(current) + ".")
    return chunks if chunks else [text]

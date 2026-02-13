"""Tests for speak.py signal parsing, chime generation, and sentence-boundary chunking.

WO-VOICE-SIGNAL-01: Report-Ready Audio Signal.
All tests are unit tests requiring no GPU, no audio hardware, no external dependencies.
"""

import io
import struct
import sys
import os
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts"))

from speak import parse_signal, _generate_chime, _chunk_by_sentence


# ---------------------------------------------------------------------------
# parse_signal
# ---------------------------------------------------------------------------

class TestParseSignal:
    def test_parse_signal_valid(self):
        """Valid signal block returns dict with signal_type, summary, body."""
        text = (
            "=== SIGNAL: REPORT_READY ===\n"
            "WO-CONDFIX-01 complete. All tests pass.\n"
            "Details of the completion go here.\n"
            "More body text.\n"
        )
        result = parse_signal(text)
        assert result is not None
        assert result["signal_type"] == "REPORT_READY"
        assert result["summary"] == "WO-CONDFIX-01 complete. All tests pass."
        assert "Details of the completion go here." in result["body"]
        assert "More body text." in result["body"]

    def test_parse_signal_no_header(self):
        """Text without signal header returns None."""
        result = parse_signal("Just some regular text.\nNo signal here.")
        assert result is None

    def test_parse_signal_empty_string(self):
        """Empty string returns None."""
        result = parse_signal("")
        assert result is None

    def test_parse_signal_summary_only(self):
        """Signal with summary but no body parses correctly."""
        text = "=== SIGNAL: REPORT_READY ===\nSingle line summary."
        result = parse_signal(text)
        assert result is not None
        assert result["signal_type"] == "REPORT_READY"
        assert result["summary"] == "Single line summary."
        assert result["body"] == ""

    def test_parse_signal_blank_lines_after_header(self):
        """Blank lines between header and summary are skipped."""
        text = "=== SIGNAL: REPORT_READY ===\n\n\nActual summary here.\nBody."
        result = parse_signal(text)
        assert result is not None
        assert result["summary"] == "Actual summary here."
        assert result["body"] == "Body."

    def test_parse_signal_different_signal_type(self):
        """Non-REPORT_READY signal types parse correctly."""
        text = "=== SIGNAL: DISPATCH_READY ===\nNew WO dispatched."
        result = parse_signal(text)
        assert result is not None
        assert result["signal_type"] == "DISPATCH_READY"
        assert result["summary"] == "New WO dispatched."


# ---------------------------------------------------------------------------
# _generate_chime
# ---------------------------------------------------------------------------

class TestGenerateChime:
    def test_generate_chime_returns_wav(self):
        """Chime output starts with RIFF header and has correct properties."""
        wav_bytes = _generate_chime()
        # RIFF header check
        assert wav_bytes[:4] == b"RIFF"
        assert wav_bytes[8:12] == b"WAVE"

        # Parse WAV to verify properties
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            assert wf.getnchannels() == 1        # mono
            assert wf.getsampwidth() == 2         # 16-bit
            assert wf.getframerate() == 24000      # 24kHz
            # Duration: 200ms at 24kHz = 4800 frames
            assert wf.getnframes() == 4800

    def test_generate_chime_correct_length(self):
        """Chime is exactly 200ms at 24kHz (4800 samples)."""
        wav_bytes = _generate_chime()
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            duration_ms = (wf.getnframes() / wf.getframerate()) * 1000
            assert abs(duration_ms - 200.0) < 0.1

    def test_generate_chime_has_audio_content(self):
        """Chime PCM data is not all zeros — actual audio present."""
        wav_bytes = _generate_chime()
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        n_samples = len(raw) // 2
        samples = struct.unpack(f"<{n_samples}h", raw)
        # At least some samples should be non-zero (440Hz tone)
        non_zero = sum(1 for s in samples if s != 0)
        assert non_zero > n_samples * 0.5  # majority should be non-zero

    def test_generate_chime_deterministic(self):
        """Same call twice produces identical bytes (pure math, no randomness)."""
        chime1 = _generate_chime()
        chime2 = _generate_chime()
        assert chime1 == chime2


# ---------------------------------------------------------------------------
# _chunk_by_sentence
# ---------------------------------------------------------------------------

class TestChunkBySentence:
    def test_chunk_by_sentence_basic(self):
        """Multi-sentence text splits at period boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = _chunk_by_sentence(text, max_words=5)
        assert len(chunks) >= 2
        # Each chunk should end with a period
        for chunk in chunks:
            assert chunk.endswith(".")

    def test_chunk_by_sentence_short_text(self):
        """Short text returns a single chunk."""
        text = "This is short."
        chunks = _chunk_by_sentence(text, max_words=55)
        assert len(chunks) == 1
        assert "This is short" in chunks[0]

    def test_chunk_by_sentence_respects_max_words(self):
        """No chunk exceeds the max_words limit (within one sentence tolerance)."""
        # Build a long text with many sentences
        sentences = [f"This is sentence number {i} with some extra words" for i in range(20)]
        text = ". ".join(sentences) + "."
        max_words = 20
        chunks = _chunk_by_sentence(text, max_words=max_words)
        for chunk in chunks:
            word_count = len(chunk.split())
            # Each chunk should be at or near the limit. A single long sentence
            # can exceed max_words if it cannot be split further, but most chunks
            # should respect the limit.
            # We check that no chunk has more words than max_words + the longest
            # single sentence word count (conservative bound).
            assert word_count <= max_words + 10

    def test_chunk_by_sentence_empty_text(self):
        """Empty text returns the original text in a list."""
        chunks = _chunk_by_sentence("")
        assert len(chunks) == 1

    def test_chunk_by_sentence_preserves_all_content(self):
        """All sentences appear in the chunked output."""
        text = "Alpha done. Beta done. Gamma done. Delta done."
        chunks = _chunk_by_sentence(text, max_words=5)
        combined = " ".join(chunks)
        assert "Alpha" in combined
        assert "Beta" in combined
        assert "Gamma" in combined
        assert "Delta" in combined

    def test_chunk_by_sentence_single_long_sentence(self):
        """A single sentence longer than max_words is returned as-is."""
        text = "This is a single very long sentence that exceeds the maximum word count limit."
        chunks = _chunk_by_sentence(text, max_words=5)
        assert len(chunks) == 1
        assert "This is a single" in chunks[0]


# ---------------------------------------------------------------------------
# CLI flag integration (no audio — mocks speak/play)
# ---------------------------------------------------------------------------

class TestSignalCLIIntegration:
    def test_signal_mode_no_signal_exits_silently(self):
        """--signal with non-signal input exits 0 (silent)."""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "speak.py"), "--signal"],
            input="just regular text\nno signal here",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0

    def test_backward_compatible_help(self):
        """--list-personas flag still works (backward compatibility)."""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "speak.py"), "--list-personas"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should exit 0 and produce some output (even if backends unavailable)
        assert result.returncode == 0
        assert len(result.stdout) > 0

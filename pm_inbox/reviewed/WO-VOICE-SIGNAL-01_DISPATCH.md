# WO-VOICE-SIGNAL-01 — Report-Ready Audio Signal

**Dispatch Authority:** PM (Opus)
**Priority:** Wave B — parallel dispatch (after Wave A completes)
**Risk:** LOW | **Effort:** Small | **Breaks:** 0 expected
**Depends on:** None (scripts/ only, no engine dependencies)

---

## Target Lock

The voice pipeline (`scripts/speak.py`, Arbor profile, Chatterbox backend) can speak arbitrary text on demand. But there is no automated routing — when an agent posts a completion report, Thunder gets no audible cue. The operator must visually scan for state changes.

**Goal:** Agent pipes a signal block to `speak.py --signal`. Chime plays, then spoken summary via Arbor.

---

## Binary Decisions (Locked)

1. **Signal format:** `=== SIGNAL: REPORT_READY ===` as first line. Parsed, not assumed.
2. **Chime:** Deterministic 440Hz sine wave, 200ms, 16-bit PCM, 24kHz. Generated at runtime via `struct.pack`. No external audio files.
3. **Chatterbox-only for production voice.** Kokoro CPU fallback is NOT acceptable quality. If no GPU/Chatterbox, voice output fails silently. The `--backend auto` default must prefer Chatterbox and NOT fall through.
4. **Sentence-boundary chunking.** Chatterbox has a ~60-80 word generation ceiling. Text exceeding this limit MUST be split at sentence boundaries (`. `), each chunk generated and played sequentially. Truncation mid-sentence is a product defect (see TD-023).
5. **Backward compatible.** Existing `python scripts/speak.py "text"` usage unchanged.

---

## Contract Spec

### File Scope (4 files)

| File | Action |
|------|--------|
| `scripts/speak.py` | Add `parse_signal()`, `_generate_chime()`, `_chunk_by_sentence()`, `--signal`/`--full` CLI flags |
| `docs/ops/STANDING_OPS_CONTRACT.md` | Add voice signal rule to Universal Rules |
| `pm_inbox/aegis_rehydration/STANDING_OPS_CONTRACT.md` | Sync rehydration copy |
| `tests/test_speak_signal.py` | New — ~6 tests |

### Implementation Detail

**1. Signal parser (`scripts/speak.py`):**
```python
def parse_signal(text: str) -> Optional[dict]:
    """Detect === SIGNAL: REPORT_READY === header and extract summary + body."""
    lines = text.strip().split("\n")
    if not lines or "=== SIGNAL:" not in lines[0]:
        return None
    signal_type = lines[0].split("SIGNAL:")[1].split("===")[0].strip()
    # First non-empty line after banner = summary
    summary = ""
    body_lines = []
    found_summary = False
    for line in lines[1:]:
        if not found_summary:
            if line.strip():
                summary = line.strip()
                found_summary = True
        else:
            body_lines.append(line)
    return {
        "signal_type": signal_type,
        "summary": summary,
        "body": "\n".join(body_lines).strip(),
    }
```

**2. Chime generator (`scripts/speak.py`):**
```python
import struct
import math

def _generate_chime() -> bytes:
    """Generate 440Hz sine wave chime, 200ms, 16-bit PCM, 24kHz."""
    sample_rate = 24000
    duration = 0.2
    frequency = 440
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Apply fade envelope (10ms attack, 10ms release)
        envelope = 1.0
        if t < 0.01:
            envelope = t / 0.01
        elif t > duration - 0.01:
            envelope = (duration - t) / 0.01
        value = int(16000 * envelope * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', max(-32768, min(32767, value))))
    pcm = b''.join(samples)
    # Wrap in WAV header
    ... (standard WAV header construction)
    return wav_bytes
```

**3. Sentence-boundary chunking:**
```python
def _chunk_by_sentence(text: str, max_words: int = 55) -> list[str]:
    """Split text at sentence boundaries to stay under Chatterbox generation ceiling."""
    sentences = text.replace(".\n", ". ").split(". ")
    chunks = []
    current = []
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
```

**4. CLI flag routing:**
```python
# In argparse section:
parser.add_argument("--signal", action="store_true", help="Parse stdin for signal block")
parser.add_argument("--full", action="store_true", help="With --signal, also speak full body")

# In main:
if args.signal:
    text = sys.stdin.read()
    result = parse_signal(text)
    if result is None:
        sys.exit(0)  # No signal found — silent exit
    chime = _generate_chime()
    _play_wav(chime)
    speak(result["summary"])
    if args.full and result["body"]:
        chunks = _chunk_by_sentence(result["body"])
        for chunk in chunks:
            speak(chunk)
```

**5. Standing ops rule (STANDING_OPS_CONTRACT.md):**
Add to Universal Rules section:
> **Voice Signal on Completion:** On WO completion, the executing agent calls `python scripts/speak.py --signal` with the signal block piped to stdin. Signal triggers only for completion reports, dispatch packages, or CP approvals — not routine messages. Signal format: `=== SIGNAL: REPORT_READY ===\n<one-line summary>\n<optional body>`.

### Frozen Contracts

None touched. All changes in `scripts/` and `docs/ops/`.

---

## Implementation Sequencing

1. Add `parse_signal()` function to `scripts/speak.py`
2. Add `_generate_chime()` function (pure math, no external deps)
3. Add `_chunk_by_sentence()` function
4. Add `--signal` and `--full` CLI flags to argparse
5. Wire signal mode: detect signal → play chime → speak summary → optionally speak body (chunked)
6. Ensure backward compatibility: existing `speak.py "text"` path untouched
7. Update `STANDING_OPS_CONTRACT.md` with voice signal rule
8. Sync rehydration copy
9. Add tests (`tests/test_speak_signal.py`):
   - `test_parse_signal_valid` — returns dict with signal_type, summary, body
   - `test_parse_signal_no_header` — returns None
   - `test_generate_chime_returns_wav` — starts with RIFF header, correct length
   - `test_chunk_by_sentence_basic` — splits at period boundaries
   - `test_chunk_by_sentence_short_text` — returns single chunk
   - `test_chunk_by_sentence_respects_max_words` — no chunk exceeds limit
10. Run full suite

---

## Acceptance Criteria

1. `echo "=== SIGNAL: REPORT_READY ===\nWO-CONDFIX-01 complete." | python scripts/speak.py --signal` plays chime then speaks summary
2. `parse_signal()` returns None for text without signal header
3. Existing `speak.py "text"` usage unchanged
4. Sentence chunking prevents Chatterbox truncation on long text
5. Standing ops rule documented
6. All existing tests pass
7. ~6 new tests pass

---

## Constraints (Critical)

- **NO Kokoro fallback.** If Chatterbox is unavailable, voice output fails silently. Do NOT add Kokoro CPU fallback path for signal voice.
- **Sentence chunking is mandatory.** Do not ship without `_chunk_by_sentence()`. Chatterbox truncation mid-sentence is a known defect (TD-023). This WO fixes it.
- **Chime is pure math.** No .wav asset files. Generate PCM at runtime.

---

## Agent Instructions

- Read `AGENT_ONBOARDING_CHECKLIST.md` and `AGENT_DEVELOPMENT_GUIDELINES.md` before starting
- This WO modifies ONLY `scripts/speak.py`, `docs/ops/STANDING_OPS_CONTRACT.md`, and its rehydration copy. Do NOT modify any engine code.
- The existing `speak()` function in speak.py handles Chatterbox/Kokoro engine selection. Reuse it for the spoken summary/body.
- Test signal parsing and chunking as unit tests (no GPU/audio required). Mock `speak()` and `_play_wav()` for integration tests.
- Run full suite before declaring completion

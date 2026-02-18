#!/usr/bin/env python3
"""Whisper-powered dictation — drop-in replacement for Win+H voice typing.

Usage:
    python scripts/listen.py                        # Hold Ctrl+Shift to talk, release to transcribe
    python scripts/listen.py --trigger toggle        # Tap hotkey to start/stop (like Win+H)
    python scripts/listen.py --hotkey capslock        # Use CapsLock as push-to-talk
    python scripts/listen.py --mode type              # Type output instead of clipboard paste
    python scripts/listen.py --model small.en         # Specify Whisper model
    python scripts/listen.py --device cuda            # Use GPU for transcription
    python scripts/listen.py --list-devices           # List audio input devices
    python scripts/listen.py --once                   # Record once and exit (for AHK integration)

Trigger modes:
    hold (default) — Hold the hotkey to record, release to transcribe.
    toggle         — Tap hotkey to start recording, tap again to stop (like Win+H).
    once           — Record immediately until silence/hotkey, transcribe, exit.

Win+H replacement:
    Win+H is a Windows system hotkey and can't be intercepted directly.
    Use the included scripts/listen_hotkey.ahk (AutoHotkey) to remap Win+H
    to launch this script in --once mode, giving you the same workflow.

No profanity filter. No censorship. What you say is what you get.

Requires: faster-whisper, sounddevice, pyperclip, pynput
"""

import argparse
import io
import sys
import threading
import time
import wave
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
import pyperclip
import sounddevice as sd

# Project root = parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Audio recording settings
SAMPLE_RATE = 16000  # Whisper expects 16kHz
CHANNELS = 1
DTYPE = "int16"

# Minimum recording duration to bother transcribing (seconds)
MIN_RECORDING_SECS = 0.3

# Status symbols
SYM_READY = "[READY]"
SYM_RECORDING = "[REC]"
SYM_TRANSCRIBING = "[...]"
SYM_DONE = "[OK]"
SYM_ERROR = "[ERR]"

# Audio feedback settings
_BEEP_SAMPLE_RATE = 44100
_BEEP_VOLUME = 0.3


def _play_beep(freq: float, duration_ms: int) -> None:
    """Play a beep through Windows system audio. Non-blocking via thread."""
    def _beep():
        try:
            import winsound
            winsound.Beep(int(freq), duration_ms)
        except Exception:
            pass
    threading.Thread(target=_beep, daemon=True).start()


def beep_start() -> None:
    """Short blip — recording started."""
    _play_beep(600, 50)


def beep_stop() -> None:
    """Quick double-blip — recording stopped, transcribing."""
    def _double():
        import winsound
        try:
            winsound.Beep(500, 40)
            winsound.Beep(400, 40)
        except Exception:
            pass
    threading.Thread(target=_double, daemon=True).start()


def beep_done() -> None:
    """Tiny pip — transcription done, output sent."""
    _play_beep(700, 30)


def beep_error() -> None:
    """Low tone — something went wrong."""
    _play_beep(300, 100)


# =============================================================================
# WHISPER MODEL (lazy-loaded singleton)
# =============================================================================

_whisper_model: Any = None
_whisper_lock = threading.Lock()


def _get_whisper_model(
    model_name: str = "small.en",
    device: str = "cpu",
    compute_type: str = "int8",
) -> Any:
    """Lazy-load the Whisper model (singleton)."""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    with _whisper_lock:
        if _whisper_model is not None:
            return _whisper_model

        from faster_whisper import WhisperModel

        print(f"  Loading Whisper model '{model_name}' on {device}...", flush=True)
        _whisper_model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )
        print(f"  Model loaded.", flush=True)
        return _whisper_model


# =============================================================================
# AUDIO RECORDING
# =============================================================================

class AudioRecorder:
    """Records audio from the microphone in a background thread."""

    def __init__(self, sample_rate: int = SAMPLE_RATE, device_id: Optional[int] = None):
        self._sample_rate = sample_rate
        self._device_id = device_id
        self._chunks: List[np.ndarray] = []
        self._recording = False
        self._stream: Optional[Any] = None

    def start(self) -> None:
        """Start recording."""
        self._chunks = []
        self._recording = True
        self._stream = sd.InputStream(
            samplerate=self._sample_rate,
            channels=CHANNELS,
            dtype=DTYPE,
            device=self._device_id,
            callback=self._audio_callback,
            blocksize=1024,
        )
        self._stream.start()

    def stop(self) -> bytes:
        """Stop recording and return raw PCM bytes."""
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._chunks:
            return b""

        audio = np.concatenate(self._chunks, axis=0)
        return audio.tobytes()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        if status:
            print(f"  Audio status: {status}", file=sys.stderr)
        if self._recording:
            self._chunks.append(indata.copy())

    @property
    def duration(self) -> float:
        """Current recording duration in seconds."""
        if not self._chunks:
            return 0.0
        total_frames = sum(c.shape[0] for c in self._chunks)
        return total_frames / self._sample_rate


# =============================================================================
# TRANSCRIPTION
# =============================================================================

def transcribe_audio(
    audio_bytes: bytes,
    model_name: str = "small.en",
    device: str = "cpu",
    compute_type: str = "int8",
) -> str:
    """Transcribe raw PCM audio bytes to text via faster-whisper.

    Args:
        audio_bytes: Raw 16-bit signed PCM mono audio at 16kHz
        model_name: Whisper model name
        device: "cpu" or "cuda"
        compute_type: "int8" (CPU) or "float16" (CUDA)

    Returns:
        Transcribed text string (no censorship)
    """
    model = _get_whisper_model(model_name, device, compute_type)

    # Convert PCM bytes to float32 numpy array
    audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0

    # Transcribe
    segments, info = model.transcribe(
        audio_float32,
        language="en",
        beam_size=5,
        vad_filter=True,
    )

    # Collect all segment text
    text_parts = []
    for segment in segments:
        text_parts.append(segment.text)

    return "".join(text_parts).strip()


# =============================================================================
# OUTPUT METHODS
# =============================================================================

def output_paste(text: str) -> None:
    """Copy text to clipboard and simulate Ctrl+V paste."""
    pyperclip.copy(text)
    try:
        from pynput.keyboard import Controller, Key
        kb = Controller()
        # Small delay to ensure clipboard is ready
        time.sleep(0.05)
        kb.press(Key.ctrl)
        kb.tap("v")
        kb.release(Key.ctrl)
    except Exception:
        # If keyboard simulation fails, at least clipboard has it
        print(f"  (Copied to clipboard — paste manually)", flush=True)


def output_type(text: str) -> None:
    """Type text character by character using keyboard simulation."""
    from pynput.keyboard import Controller
    kb = Controller()
    time.sleep(0.1)
    kb.type(text)


# =============================================================================
# HOTKEY LISTENER
# =============================================================================

def _do_transcribe_and_output(
    recorder: "AudioRecorder",
    output_fn: Any,
    model_name: str,
    device: str,
    compute_type: str,
) -> Optional[str]:
    """Stop recording, transcribe, and send output. Returns transcribed text or None."""
    beep_stop()
    audio_bytes = recorder.stop()
    duration = len(audio_bytes) / (SAMPLE_RATE * 2)  # 2 bytes per sample

    if duration < MIN_RECORDING_SECS:
        print(f"  {SYM_READY} (too short)       ", end="\r", flush=True)
        return None

    print(f"  {SYM_TRANSCRIBING} Transcribing {duration:.1f}s...  ", end="\r", flush=True)

    try:
        text = transcribe_audio(audio_bytes, model_name, device, compute_type)
        if text:
            print(f"  {SYM_DONE} \"{text[:60]}{'...' if len(text) > 60 else ''}\"")
            output_fn(text)
            beep_done()
            return text
        else:
            print(f"  {SYM_READY} (no speech detected)  ", end="\r", flush=True)
            return None
    except Exception as e:
        print(f"  {SYM_ERROR} Transcription failed: {e}")
        beep_error()
        return None


def run_hold_to_talk(
    hotkey: str,
    mode: str,
    model_name: str,
    device: str,
    compute_type: str,
    audio_device: Optional[int],
) -> None:
    """Hold-to-talk mode: hold the hotkey to record, release to transcribe."""
    from pynput import keyboard

    recorder = AudioRecorder(device_id=audio_device)
    is_recording = False
    held_keys: set = set()
    hotkey_parts = _parse_hotkey(hotkey)
    output_fn = output_paste if mode == "paste" else output_type

    print(f"\n  Dictation ready. Hold [{hotkey}] to talk, release to transcribe.")
    print(f"  Output mode: {mode}")
    print(f"  Press Ctrl+C to quit.\n")

    # Pre-load the model
    _get_whisper_model(model_name, device, compute_type)
    print(f"  {SYM_READY}", end="\r", flush=True)

    def _check_hotkey() -> bool:
        return all(k in held_keys for k in hotkey_parts)

    def on_press(key: Any) -> None:
        nonlocal is_recording
        normalized = _normalize_key(key)
        if normalized:
            held_keys.add(normalized)

        if not is_recording and _check_hotkey():
            is_recording = True
            beep_start()
            recorder.start()
            print(f"  {SYM_RECORDING} Recording...       ", end="\r", flush=True)

    def on_release(key: Any) -> None:
        nonlocal is_recording
        normalized = _normalize_key(key)
        if normalized:
            held_keys.discard(normalized)

        if is_recording and not _check_hotkey():
            is_recording = False
            _do_transcribe_and_output(recorder, output_fn, model_name, device, compute_type)
            print(f"  {SYM_READY}", end="\r", flush=True)

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            print("\n  Dictation stopped.")


def run_toggle_to_talk(
    hotkey: str,
    mode: str,
    model_name: str,
    device: str,
    compute_type: str,
    audio_device: Optional[int],
) -> None:
    """Toggle mode: tap hotkey to start recording, tap again to stop (like Win+H)."""
    from pynput import keyboard

    recorder = AudioRecorder(device_id=audio_device)
    is_recording = False
    hotkey_parts = _parse_hotkey(hotkey)
    output_fn = output_paste if mode == "paste" else output_type
    # Debounce: ignore rapid key events
    last_toggle_time = 0.0
    recording_start_time = 0.0
    max_recording_secs = 60.0  # Safety: auto-stop after 60s

    print(f"\n  Dictation ready. Tap [{hotkey}] to start/stop recording.")
    print(f"  Output mode: {mode}")
    print(f"  Max recording: {max_recording_secs:.0f}s")
    print(f"  Press Ctrl+C to quit.\n")

    # Pre-load the model
    _get_whisper_model(model_name, device, compute_type)
    print(f"  {SYM_READY}", end="\r", flush=True)

    # Guard flags to prevent reentrancy and ghost triggers
    _busy = False          # True while transcribing — ignore ALL key events
    _suppress = False      # True while sending synthetic keys (backspace erase)

    def _is_hotkey(key: Any) -> bool:
        """Check if this specific key event IS the hotkey. No held_keys set."""
        normalized = _normalize_key(key)
        if not normalized:
            return False
        if len(hotkey_parts) == 1:
            return normalized == hotkey_parts[0]
        # Multi-key combos not supported in toggle mode with single char hotkeys
        return False

    def _erase_hotkey_char_async() -> None:
        """Erase the typed hotkey character via a separate thread.
        Must not run inside the listener callback to avoid reentrancy."""
        if len(hotkey_parts) != 1 or len(hotkey_parts[0]) != 1:
            return
        nonlocal _suppress
        def _do_erase():
            nonlocal _suppress
            _suppress = True
            try:
                from pynput.keyboard import Controller, Key
                kb = Controller()
                time.sleep(0.03)
                kb.tap(Key.backspace)
                time.sleep(0.03)
            except Exception:
                pass
            finally:
                _suppress = False
        threading.Thread(target=_do_erase, daemon=True).start()

    def _stop_and_transcribe() -> None:
        nonlocal is_recording, _busy
        is_recording = False
        _busy = True
        try:
            _erase_hotkey_char_async()
            _do_transcribe_and_output(recorder, output_fn, model_name, device, compute_type)
            print(f"  {SYM_READY}", end="\r", flush=True)
        finally:
            _busy = False

    def on_press(key: Any) -> None:
        nonlocal is_recording, last_toggle_time, recording_start_time

        # Block ALL events during transcription or synthetic key injection
        if _busy or _suppress:
            return

        # Only react to the exact hotkey — nothing else
        if not _is_hotkey(key):
            return

        # Debounce
        now = time.time()
        if now - last_toggle_time < 0.5:
            return
        last_toggle_time = now

        if not is_recording:
            is_recording = True
            recording_start_time = now
            _erase_hotkey_char_async()
            beep_start()
            recorder.start()
            print(f"  {SYM_RECORDING} Recording... (tap [{hotkey}] to stop)", end="\r", flush=True)
        else:
            _stop_and_transcribe()

    def on_release(key: Any) -> None:
        if _busy or _suppress:
            return

        # Safety: auto-stop if recording too long
        if is_recording and recording_start_time > 0:
            if time.time() - recording_start_time > max_recording_secs:
                print(f"\n  Auto-stopping (max {max_recording_secs:.0f}s reached)")
                _stop_and_transcribe()

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        try:
            listener.join()
        except KeyboardInterrupt:
            if is_recording:
                recorder.stop()
            print("\n  Dictation stopped.")


def run_once(
    mode: str,
    model_name: str,
    device: str,
    compute_type: str,
    audio_device: Optional[int],
    max_silence_secs: float = 2.0,
    max_duration_secs: float = 30.0,
) -> None:
    """One-shot mode: record immediately, stop on silence or Enter, transcribe, exit.

    Designed for AutoHotkey integration — Win+H triggers this, it records,
    transcribes, pastes, and exits.
    """
    from pynput import keyboard

    output_fn = output_paste if mode == "paste" else output_type

    # Pre-load model
    _get_whisper_model(model_name, device, compute_type)

    recorder = AudioRecorder(device_id=audio_device)
    stop_event = threading.Event()

    print(f"  {SYM_RECORDING} Recording... (press Enter or Escape to stop)", flush=True)
    beep_start()
    recorder.start()

    def on_press(key: Any) -> None:
        from pynput.keyboard import Key
        if key == Key.enter or key == Key.esc:
            stop_event.set()
            return False  # Stop listener

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # Wait for stop signal or max duration
    start_time = time.time()
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        if elapsed >= max_duration_secs:
            break
        time.sleep(0.1)

    listener.stop()
    result = _do_transcribe_and_output(recorder, output_fn, model_name, device, compute_type)

    if result:
        print(f"  Done. Text {'pasted' if mode == 'paste' else 'typed'}.", flush=True)
    else:
        print(f"  No speech detected.", flush=True)


def _parse_hotkey(hotkey: str) -> list:
    """Parse a hotkey string like 'ctrl+shift' into normalized key names."""
    parts = [p.strip().lower() for p in hotkey.split("+")]
    return parts


def _normalize_key(key: Any) -> Optional[str]:
    """Normalize a pynput key to a string for comparison."""
    from pynput.keyboard import Key, KeyCode

    if isinstance(key, Key):
        name = key.name.lower()
        # Map left/right variants to base name
        for prefix in ("ctrl", "shift", "alt"):
            if name.startswith(prefix):
                return prefix
        if name == "caps_lock":
            return "capslock"
        return name
    elif isinstance(key, KeyCode):
        if key.char:
            return key.char.lower()
        if key.vk:
            # Map virtual key codes for special keys
            return f"vk_{key.vk}"
    return None


# =============================================================================
# DEVICE LISTING
# =============================================================================

def list_audio_devices() -> None:
    """Print available audio input devices."""
    devices = sd.query_devices()
    print("\n  Audio Input Devices:")
    print("  " + "-" * 60)
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            default = " (DEFAULT)" if i == sd.default.device[0] else ""
            print(f"  [{i}] {dev['name']}{default}")
    print()


# =============================================================================
# CLI
# =============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Whisper-powered dictation — no profanity filter, no censorship.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--hotkey",
        default="`",
        help="Push-to-talk hotkey (default: ` backtick). Examples: capslock, ctrl+shift, scroll_lock, `",
    )
    parser.add_argument(
        "--trigger",
        choices=["hold", "toggle", "once"],
        default="toggle",
        help=(
            "Trigger mode: "
            "'hold' = hold hotkey to record (default), "
            "'toggle' = tap to start/stop (like Win+H), "
            "'once' = record immediately then exit (for AHK integration)"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["paste", "type"],
        default="paste",
        help="Output mode: 'paste' copies to clipboard + Ctrl+V, 'type' simulates keystrokes (default: paste)",
    )
    parser.add_argument(
        "--model",
        default="small.en",
        help="Whisper model name (default: small.en). Options: tiny.en, base.en, small.en, medium.en",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        choices=["cpu", "cuda"],
        help="Compute device for Whisper (default: cuda)",
    )
    parser.add_argument(
        "--audio-device",
        type=int,
        default=None,
        help="Audio input device ID (use --list-devices to see options)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit",
    )

    args = parser.parse_args()

    if args.list_devices:
        list_audio_devices()
        return

    compute_type = "float16" if args.device == "cuda" else "int8"

    print("=" * 50)
    print("  WHISPER DICTATION")
    print("  No filter. No censorship. Your words.")
    print("=" * 50)

    if args.trigger == "once":
        run_once(
            mode=args.mode,
            model_name=args.model,
            device=args.device,
            compute_type=compute_type,
            audio_device=args.audio_device,
        )
    elif args.trigger == "toggle":
        run_toggle_to_talk(
            hotkey=args.hotkey,
            mode=args.mode,
            model_name=args.model,
            device=args.device,
            compute_type=compute_type,
            audio_device=args.audio_device,
        )
    else:
        run_hold_to_talk(
            hotkey=args.hotkey,
            mode=args.mode,
            model_name=args.model,
            device=args.device,
            compute_type=compute_type,
            audio_device=args.audio_device,
        )


if __name__ == "__main__":
    main()

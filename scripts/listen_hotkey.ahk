; Whisper Dictation — Win+H hotkey replacement
; Remaps Win+H to launch Whisper-powered dictation instead of Windows voice typing.
;
; Requirements:
;   - AutoHotkey v2 installed (https://www.autohotkey.com/)
;   - Python with faster-whisper, sounddevice, pyperclip, pynput
;
; Usage:
;   1. Double-click this .ahk file to run it
;   2. Press Win+H — it will block Windows voice typing and launch Whisper instead
;   3. Speak, then press Enter or Escape to stop recording
;   4. Transcribed text is auto-pasted at your cursor
;
; To auto-start: put a shortcut in shell:startup
;   (Win+R → shell:startup → paste shortcut to this file)

#Requires AutoHotkey v2.0

; Configuration — edit these paths to match your setup
PYTHON_EXE := "python"
SCRIPT_DIR := A_ScriptDir  ; Same directory as this .ahk file
LISTEN_SCRIPT := SCRIPT_DIR . "\listen.py"

; Win+H → Whisper dictation (blocks Windows voice typing)
#h::
{
    ; Run listen.py in --once mode: records, transcribes, pastes, exits
    Run PYTHON_EXE . ' "' . LISTEN_SCRIPT . '" --trigger once --mode paste', SCRIPT_DIR, "Min"
}

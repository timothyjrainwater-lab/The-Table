# WO-VOICE-HOOK-001: Session-End Voice Cue — Hard-Coded Hook

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 0 (operational — blocking Operator workflow)
**Priority:** P0 — Operator has requested this 5+ times. Zero tolerance for further misses.
**Source:** Operator directive (repeated across multiple sessions)

---

## Target Lock

Every time a Claude Code agent session ends — for ANY reason (context window exhaustion, task completion, manual stop, error) — the system must play a voice notification via `scripts/speak.py`. No exceptions. No reliance on the agent "remembering" to call it. The trigger must be infrastructure-level, not agent-behavioral.

**The problem:** Rule 22 defined voice cues ("Thunder, the forge is quiet" for builders, "Thunder, PM is on standby" for PM). But the implementation relied on agents calling `speak.py` as their final action. Agents routinely fail to do this — they run out of context, forget, or hit the PM Execution Boundary. The Operator has raised this 5+ times across sessions. It must be solved at the infrastructure level.

**The fix:** Claude Code supports lifecycle hooks configured in `.claude/settings.json`. A `Stop` hook fires a shell command every time a session ends. Wire `speak.py` into this hook. The agent doesn't need to remember anything — the hook fires automatically.

## Binary Decisions

1. **Which hook event?** `Stop` — fires when any Claude Code session ends (context exhaustion, completion, manual stop, error).
2. **Which settings file?** Project-level: `f:\DnD-3.5\.claude\settings.json`. This keeps it scoped to this project.
3. **What message?** A generic session-end signal. The hook cannot know whether the session was PM, builder, or assistant — so use a universal message: `"Thunder, session complete."` (If role-specific messages are needed later, that's a separate WO.)
4. **What if TTS fails?** `speak.py` already falls back to printing to stdout if no TTS backend is available. No additional error handling needed.

## Contract Spec

### Deliverable 1: Configure Stop Hook

Add a `hooks` configuration to `f:\DnD-3.5\.claude\settings.json` that runs `speak.py` on every session end.

**Research required:** The builder must look up the exact Claude Code hooks JSON syntax. The expected structure is something like:

```json
{
  "hooks": {
    "Stop": [
      {
        "command": "python scripts/speak.py \"Thunder, session complete.\""
      }
    ]
  }
}
```

But the builder MUST verify the exact syntax from Claude Code documentation before implementing. The key questions:
- Is the hook event called `Stop`, `SessionEnd`, `stop`, or something else?
- Is `command` the right key, or is it `run`, `script`, `cmd`?
- Does the command run from the project root, or does it need an absolute path?
- Can the hook be an array of commands or just one?
- Does the hook block the session exit or run async?

### Deliverable 2: Test the Hook

After configuration:
1. Start a Claude Code session in the DnD-3.5 project
2. End the session (type /exit or similar)
3. Verify that `speak.py` fires and audio plays (or prints to stdout if no TTS)

### Constraints

- Do NOT modify `scripts/speak.py` — it already handles the use case
- Do NOT add role-detection logic — universal message for now
- Do NOT add hooks for other events unless they're trivially related
- The hook must work on Windows 11 with the project's Python environment

## Success Criteria

- [ ] Claude Code `Stop` (or equivalent) hook configured in `.claude/settings.json`
- [ ] Every session end in this project triggers `speak.py` automatically
- [ ] Audio plays (or stdout fallback) without any agent action required
- [ ] Existing session behavior is not disrupted (hook runs after session work completes)
- [ ] Hook syntax verified against Claude Code documentation, not guessed

## Files Expected to Change

- `f:\DnD-3.5\.claude\settings.json` — add hooks configuration

## Files NOT to Change

- `scripts/speak.py` — already works
- Any production engine code
- Any PM-owned files (kernel, briefing)

---

*End of WO-VOICE-HOOK-001*

# RQ-TTS-004: Subprocess Keep-Alive Alternative

**Sprint:** WO-TTS-COLD-START-RESEARCH
**Date:** 2026-02-14
**Dependencies:** RQ-TTS-001 (timing data), RQ-TTS-003 (server architecture)

---

## Verdict: NOT VIABLE for Agent Integration

Subprocess keep-alive does not solve the cold start problem in the context where it matters most — sequential calls from Claude Code agents.

---

## The Concept

Modify `speak.py` to support a `--daemon` or `--listen` mode:
- Load model once
- Read text lines from stdin (or a named pipe) in a loop
- Synthesize and play each line
- Exit on EOF or explicit shutdown command

This avoids the complexity of a server daemon but still amortizes the cold start.

---

## Why It Fails

### 1. Process boundary between Bash tool calls

Each Claude Code Bash tool call spawns a new shell environment. There is no mechanism to:
- Inherit a subprocess from a previous Bash call
- Share file descriptors across Bash calls
- Discover and communicate with a background process started in a prior call

A subprocess started with `&` in Bash Call 1 becomes unreachable in Bash Call 2.

### 2. No bidirectional communication

Even if a background `speak.py --daemon` process is running, subsequent Bash calls have no clean way to:
- Discover it (PID files are fragile, `pgrep` is unreliable)
- Send it synthesis requests (no shared stdin)
- Receive synthesis results (no shared stdout)
- Know when synthesis is complete

### 3. Lifecycle ambiguity

| Scenario | What happens to the daemon? |
|----------|----------------------------|
| Agent session ends normally | Orphaned — VRAM stays allocated |
| Agent session crashes | Orphaned |
| User closes terminal | Process killed (maybe) |
| System sleep/resume | Uncertain |

No clean shutdown path exists. VRAM leaks are likely.

### 4. Windows-specific pipe complexity

- POSIX `mkfifo` doesn't exist natively on Windows
- Windows named pipes (`\\.\pipe\name`) require `pywin32` or ctypes — not in the project's dependency set
- Git Bash (the shell in use) provides partial POSIX compatibility but named pipe semantics are inconsistent

---

## Comparison with Server Approach (RQ-TTS-003)

| Dimension | Subprocess Keep-Alive | Persistent Server |
|-----------|-----------------------|-------------------|
| **Complexity** | Lower (no IPC protocol) | Moderate (HTTP endpoints) |
| **Agent integration** | **Broken** — can't communicate across Bash calls | **Works** — HTTP is call-independent |
| **Process discovery** | Fragile (PID file, pgrep) | Clean (connect to port, check health) |
| **Lifecycle management** | Ambiguous (orphan risk) | Clean (idle timeout, health endpoint) |
| **Multi-consumer** | Single consumer (whoever holds stdin) | Multi-consumer (any process can connect) |
| **Status monitoring** | None | Health endpoint reports VRAM, tiers, idle |
| **Crash recovery** | Lost — must restart manually | Client falls back to cold load automatically |
| **Reliability on Windows** | Low (pipe issues, process discovery) | High (TCP/HTTP is well-tested) |

**The server approach wins on every dimension except initial implementation complexity** — and the complexity difference is small (HTTP server is ~50 lines of Python using built-in stdlib).

---

## When Keep-Alive Would Work

Subprocess keep-alive is viable in exactly one scenario: **a single long-running Python process that calls `speak()` multiple times internally.** This is already how the `--signal --full` mode works — it synthesizes summary + body within one process invocation.

This pattern is already implemented and working. Extending it to new callers doesn't require a `--daemon` mode; it requires the caller to be in the same process (or use IPC, which is what the server approach provides).

---

## Edge Case Analysis

### What happens if the process is killed mid-synthesis?

**VRAM leak is minimal.** RQ-TTS-002 showed that `del model` + `torch.cuda.empty_cache()` is clean (8.4 MB residual). Process termination triggers Python's garbage collector, which calls `__del__` on torch tensors. CUDA driver reclaims VRAM when the process exits.

**However:** If the process is killed with SIGKILL (Windows: `taskkill /F`), destructors may not run. CUDA driver still reclaims on process exit, but there may be a delay.

### Can the keep-alive process handle persona changes between lines?

**Yes.** The `ChatterboxTTSAdapter` already supports persona switching between `synthesize()` calls — it resolves the persona on each call. No model reload is needed for persona changes.

### Buffer management: does stdin buffering cause delays?

**On Windows: yes.** Python's `sys.stdin` uses block buffering in non-interactive mode, which can introduce delays. Line buffering (`sys.stdin.reconfigure(line_buffering=True)`) would be needed, but this interacts poorly with binary data in pipes.

---

## Recommendation

**Reject subprocess keep-alive. Proceed with persistent server (RQ-TTS-003).**

The subprocess approach solves the problem in theory but fails in practice because of how Claude Code agents invoke external scripts. The server approach adds modest complexity but works reliably across all caller patterns.

---

*Key question answered: Subprocess keep-alive is NOT viable given how agents invoke speak.py. The process boundary makes it moot.*

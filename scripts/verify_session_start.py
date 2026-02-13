#!/usr/bin/env python3
"""Session bootstrap verifier — paste output at session start.

Prints git state, python version, branch, and test collection count.
Fast by default (~2s). Use --full to run the actual test suite.

Usage:
    python scripts/verify_session_start.py          # fast: git + collect
    python scripts/verify_session_start.py --full   # includes real pytest run

Operational rule: no agent session starts until this output is pasted
into the first message.
"""

import subprocess
import sys
import platform
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_cmd(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run command, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError:
        return -1, "", "COMMAND NOT FOUND"


def git_commit_hash() -> str:
    rc, out, _ = run_cmd(["git", "rev-parse", "--short", "HEAD"])
    return out if rc == 0 else "unknown"


def git_branch() -> str:
    rc, out, _ = run_cmd(["git", "branch", "--show-current"])
    return out if rc == 0 else "unknown"


def git_dirty() -> tuple[bool, str]:
    """Return (is_dirty, porcelain_output)."""
    rc, out, _ = run_cmd(["git", "status", "--porcelain"])
    return bool(out), out


def play_py_running() -> bool:
    """Check if a play.py process is already running (Windows + Unix)."""
    try:
        if platform.system() == "Windows":
            rc, out, _ = run_cmd(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"], timeout=10)
            # Check command lines via wmic for play.py
            rc2, out2, _ = run_cmd(
                ["wmic", "process", "where", "name='python.exe'", "get", "CommandLine"],
                timeout=10,
            )
            return "play.py" in out2
        else:
            rc, out, _ = run_cmd(["pgrep", "-f", "play.py"], timeout=10)
            if rc == 0 and out.strip():
                # Exclude our own PID
                pids = {int(p) for p in out.strip().split("\n") if p.strip()}
                pids.discard(os.getpid())
                return len(pids) > 0
    except Exception:
        pass
    return False


def test_collect_count() -> str:
    """Fast: just collect tests without running them."""
    rc, out, err = run_cmd(
        [sys.executable, "-m", "pytest", "--co", "-q"], timeout=30
    )
    if rc == 0:
        # Last non-empty line should be like "5352 tests collected"
        lines = [l for l in out.split("\n") if l.strip()]
        for line in reversed(lines):
            if "collected" in line or "test" in line:
                return line
        return f"{len(lines)} items"
    return f"collect failed (rc={rc})"


def test_full_run() -> str:
    """Slow: actually run the test suite."""
    rc, out, err = run_cmd(
        [sys.executable, "-m", "pytest", "-q",
         "--ignore=tests/immersion/test_chatterbox_tts.py"],
        timeout=300
    )
    # Grab the summary line
    lines = [l for l in out.split("\n") if l.strip()]
    for line in reversed(lines):
        if "passed" in line or "failed" in line or "error" in line:
            return line
    if lines:
        return lines[-1]
    # Fall back to stderr
    err_lines = [l for l in err.split("\n") if l.strip()]
    return err_lines[-1] if err_lines else f"unknown result (rc={rc})"


def main():
    full = "--full" in sys.argv
    warnings = []

    commit = git_commit_hash()
    branch = git_branch()
    dirty, dirty_files = git_dirty()
    play_running = play_py_running()
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_platform = platform.system()

    print("=" * 55)
    print("  SESSION BOOTSTRAP — verify_session_start.py")
    print("=" * 55)
    print(f"  commit:   {commit} ({'DIRTY' if dirty else 'clean'})")
    print(f"  branch:   {branch}")
    print(f"  python:   {py_version} ({py_platform})")

    collect = test_collect_count()
    print(f"  tests:    {collect}")

    if full:
        print(f"  running:  full pytest suite (hw-gated TTS excluded)...")
        result = test_full_run()
        print(f"  result:   {result}")
    else:
        print(f"  (use --full to run actual test suite)")

    # --- Warnings ---
    if play_running:
        warnings.append("[RED] play.py process detected — kill it before starting session")

    if dirty:
        tracked = [f for f in dirty_files.split("\n") if f.strip() and not f.strip().startswith("??")]
        if tracked:
            warnings.append(f"[RED] Dirty tree — {len(tracked)} tracked file(s) modified:")
            for f in tracked:
                warnings.append(f"       {f.strip()}")

    if warnings:
        print("-" * 55)
        for w in warnings:
            print(f"  {w}")

    print("=" * 55)


if __name__ == "__main__":
    main()

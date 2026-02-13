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


def git_dirty() -> bool:
    rc, out, _ = run_cmd(["git", "status", "--porcelain"])
    return bool(out)


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

    commit = git_commit_hash()
    branch = git_branch()
    dirty = git_dirty()
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

    print("=" * 55)


if __name__ == "__main__":
    main()

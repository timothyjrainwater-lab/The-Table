"""Canonical project reality snapshot.

WO-AUDIT-SNAPSHOT-001: Generates a reproducible, machine-verifiable snapshot
of the project state on the current commit. Run this on a clean working tree
to produce canonical numbers that replace all hand-asserted claims in docs.

Usage:
    python scripts/audit_snapshot.py              # print to stdout
    python scripts/audit_snapshot.py --write      # also write docs/STATE.md

Output:
    - Git commit hash + dirty/clean status
    - Python version + platform
    - Total tests discovered (pytest --co)
    - Test pass/fail/skip summary (real pytest run)
    - Wall clock runtime
    - LOC counts (production / tests)
    - Timestamp (UTC)
"""

import subprocess
import sys
import os
import platform
import time
from pathlib import Path
from datetime import datetime, timezone


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_MD_PATH = PROJECT_ROOT / "docs" / "STATE.md"


def run_cmd(cmd: list[str], cwd: Path = PROJECT_ROOT, timeout: int = 600) -> str:
    """Run a command and return stdout. Raises on timeout."""
    result = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip()


def run_cmd_full(cmd: list[str], cwd: Path = PROJECT_ROOT, timeout: int = 600):
    """Run a command and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def get_git_info() -> dict:
    """Get git commit hash and dirty status."""
    commit_hash = run_cmd(["git", "rev-parse", "HEAD"])
    short_hash = commit_hash[:12]

    # Check if working tree is clean
    status_output = run_cmd(["git", "status", "--porcelain"])
    is_clean = len(status_output.strip()) == 0
    dirty_files = len(status_output.strip().splitlines()) if not is_clean else 0

    branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])

    return {
        "commit": commit_hash,
        "short_commit": short_hash,
        "branch": branch,
        "clean": is_clean,
        "dirty_files": dirty_files,
    }


def get_python_info() -> dict:
    """Get Python version and platform info."""
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "system": platform.system(),
    }


def count_tests() -> int:
    """Count total tests discovered by pytest --co."""
    stdout = run_cmd(
        [sys.executable, "-m", "pytest", "tests/", "--co", "-q"],
        timeout=120,
    )
    # Last line is like "======================== 5293 tests collected in 2.26s ========================"
    for line in stdout.splitlines()[::-1]:
        if "collected" in line:
            # Strip = borders and parse
            stripped = line.replace("=", "").strip()
            parts = stripped.split()
            if parts and parts[0].isdigit():
                return int(parts[0])
    return -1


def run_test_suite() -> dict:
    """Run full test suite and parse results."""
    start = time.monotonic()
    stdout, stderr, rc = run_cmd_full(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
        timeout=600,
    )
    wall_clock = time.monotonic() - start

    # Parse the summary line: "7 failed, 5270 passed, 16 skipped, 88 warnings in 110.55s"
    passed = failed = skipped = warnings_count = 0
    combined = stdout + "\n" + stderr
    for line in combined.splitlines()[::-1]:
        if "passed" in line or "failed" in line:
            for part in line.replace("=", "").strip().split(","):
                part = part.strip()
                if "passed" in part:
                    passed = int(part.split()[0])
                elif "failed" in part:
                    failed = int(part.split()[0])
                elif "skipped" in part:
                    skipped = int(part.split()[0])
                elif "warning" in part:
                    warnings_count = int(part.split()[0])
            break

    return {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "warnings": warnings_count,
        "total": passed + failed + skipped,
        "wall_clock_s": round(wall_clock, 1),
        "exit_code": rc,
    }


def count_lines() -> dict:
    """Count lines of code in production and test files."""
    prod_lines = 0
    test_lines = 0
    prod_files = 0
    test_files = 0

    aidm_dir = PROJECT_ROOT / "aidm"
    tests_dir = PROJECT_ROOT / "tests"

    for py_file in aidm_dir.rglob("*.py"):
        if py_file.name == "__pycache__":
            continue
        try:
            lines = len(py_file.read_text(encoding="utf-8").splitlines())
            prod_lines += lines
            prod_files += 1
        except Exception:
            pass

    for py_file in tests_dir.rglob("*.py"):
        if py_file.name == "__pycache__":
            continue
        try:
            lines = len(py_file.read_text(encoding="utf-8").splitlines())
            test_lines += lines
            test_files += 1
        except Exception:
            pass

    return {
        "prod_lines": prod_lines,
        "prod_files": prod_files,
        "test_lines": test_lines,
        "test_files": test_files,
        "total_lines": prod_lines + test_lines,
        "total_files": prod_files + test_files,
    }


def build_snapshot() -> dict:
    """Build complete project snapshot."""
    print("Gathering git info...", file=sys.stderr)
    git = get_git_info()

    print("Gathering Python info...", file=sys.stderr)
    py = get_python_info()

    print("Counting tests...", file=sys.stderr)
    test_count = count_tests()

    print("Running full test suite (this takes ~2 minutes)...", file=sys.stderr)
    results = run_test_suite()

    print("Counting lines of code...", file=sys.stderr)
    loc = count_lines()

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git": git,
        "python": py,
        "tests_discovered": test_count,
        "test_results": results,
        "loc": loc,
    }


def format_snapshot(snap: dict) -> str:
    """Format snapshot as markdown."""
    git = snap["git"]
    py = snap["python"]
    tr = snap["test_results"]
    loc = snap["loc"]

    clean_str = "CLEAN" if git["clean"] else f"DIRTY ({git['dirty_files']} files)"
    gate_str = "GREEN" if tr["failed"] == 0 or tr["exit_code"] == 0 else "RED"

    # If only hardware-gated failures, note that
    if tr["failed"] > 0 and tr["failed"] <= 10:
        gate_str = f"YELLOW ({tr['failed']} failures — verify if hardware-gated)"

    avg_ms = round((tr["wall_clock_s"] / tr["total"]) * 1000, 1) if tr["total"] else 0

    lines = [
        "# Project State Snapshot",
        "",
        f"**Generated:** {snap['timestamp_utc']}",
        f"**Script:** `python scripts/audit_snapshot.py`",
        "",
        "---",
        "",
        "## Git",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Commit | `{git['commit']}` |",
        f"| Branch | `{git['branch']}` |",
        f"| Working tree | {clean_str} |",
        "",
        "## Environment",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Python | {py['python_version']} |",
        f"| Platform | {py['platform']} |",
        "",
        "## Test Suite",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Gate status | **{gate_str}** |",
        f"| Tests discovered | {snap['tests_discovered']} |",
        f"| Passed | {tr['passed']} |",
        f"| Failed | {tr['failed']} |",
        f"| Skipped | {tr['skipped']} |",
        f"| Wall clock | {tr['wall_clock_s']}s |",
        f"| Avg per test | {avg_ms}ms |",
        "",
        "## Lines of Code",
        "",
        f"| Scope | Files | Lines |",
        f"|-------|-------|-------|",
        f"| Production (aidm/) | {loc['prod_files']} | {loc['prod_lines']:,} |",
        f"| Tests (tests/) | {loc['test_files']} | {loc['test_lines']:,} |",
        f"| **Total** | **{loc['total_files']}** | **{loc['total_lines']:,}** |",
        "",
        "---",
        "",
        "*This file is machine-generated. Do not edit manually.*",
        "*All other documents should reference this file for canonical test counts and runtimes.*",
        "",
    ]
    return "\n".join(lines)


def main():
    write_file = "--write" in sys.argv

    snap = build_snapshot()
    output = format_snapshot(snap)

    print(output)

    if write_file:
        STATE_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_MD_PATH.write_text(output, encoding="utf-8")
        print(f"\nWritten to {STATE_MD_PATH}", file=sys.stderr)

    # Exit nonzero if tests failed
    if snap["test_results"]["exit_code"] != 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

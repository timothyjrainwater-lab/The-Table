#!/usr/bin/env python3
"""RC Packet Builder — PRS-01 §9.

Runs P1-P9 publish gates in sequence and produces an RC evidence packet.

Usage:
    python scripts/build_release_candidate_packet.py [--output-dir RC_PACKET]

Exit codes:
    0 — All gates PASS
    1 — One or more gates FAIL
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


# ---------------------------------------------------------------------------
# Gate definitions: (display_name, log_filename, command_fn)
# command_fn receives repo_root and returns list[str]
# ---------------------------------------------------------------------------

def _cmd_p1_clean_tree(repo_root: Path) -> list[str]:
    return ["git", "status", "--porcelain"]


def _cmd_p2_test_suite(repo_root: Path) -> list[str]:
    return [
        sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no",
        "--ignore=tests/test_heuristics_image_critic.py",
        "--ignore=tests/test_ws_bridge.py",
        "--ignore=tests/test_graduated_critique_orchestrator.py",
        "--ignore=tests/test_immersion_authority_contract.py",
        "--ignore=tests/test_pm_inbox_hygiene.py",
        "--ignore=tests/test_speak_signal.py",
    ]


def _cmd_p3_asset_scan(repo_root: Path) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / "publish_scan_assets.py")]


def _cmd_p4_license_check(repo_root: Path) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / "publish_check_licenses.py")]


def _cmd_p5_secret_scan(repo_root: Path) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / "publish_secret_scan.py")]


def _cmd_p6_offline_static(repo_root: Path) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / "publish_scan_network_calls.py")]


def _cmd_p6_offline_runtime(repo_root: Path) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / "publish_smoke_no_network.py")]


def _cmd_p7_first_run(repo_root: Path) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / "publish_first_run_missing_weights.py")]


def _cmd_p8_ip_scan(repo_root: Path) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / "publish_scan_ip_terms.py")]


def _cmd_p9_docs_check(repo_root: Path) -> list[str]:
    return [sys.executable, str(SCRIPTS_DIR / "publish_check_docs.py")]


GATES = [
    ("P1 Clean Tree",       "p1_clean_tree.log",       _cmd_p1_clean_tree),
    ("P2 Test Suite",       "p2_test_results.log",     _cmd_p2_test_suite),
    ("P3 Asset Scan",       "p3_asset_scan.log",       _cmd_p3_asset_scan),
    ("P4 License Check",    "p4_license_check.log",    _cmd_p4_license_check),
    ("P5 Secret Scan",      "p5_secret_scan.log",      _cmd_p5_secret_scan),
    ("P6 Offline Static",   "p6_offline_static.log",   _cmd_p6_offline_static),
    ("P6 Offline Runtime",  "p6_offline_runtime.log",  _cmd_p6_offline_runtime),
    ("P7 First Run",        "p7_first_run.log",        _cmd_p7_first_run),
    ("P8 IP Scan",          "p8_ip_scan.log",          _cmd_p8_ip_scan),
    ("P9 Docs Check",       "p9_docs_check.log",       _cmd_p9_docs_check),
]


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_gate(name: str, cmd: list[str], log_path: Path) -> tuple[bool, str]:
    """Run a single gate command and capture output to a log file.

    P1 (clean tree) is special: PASS = empty stdout, regardless of exit code.
    All other gates: PASS = exit code 0.

    Returns:
        (passed, combined_output)
    """
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    combined = result.stdout
    if result.stderr:
        combined += "\n--- STDERR ---\n" + result.stderr

    log_path.write_text(combined, encoding="utf-8")

    if name == "P1 Clean Tree":
        passed = result.stdout.strip() == ""
        status_line = "PASS: Working tree is clean." if passed else f"FAIL: Dirty tree:\n{result.stdout.strip()}"
        log_path.write_text(status_line + "\n", encoding="utf-8")
        return passed, status_line

    passed = result.returncode == 0
    return passed, combined


def get_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "UNKNOWN"


def read_known_failures(known_failures_path: Path) -> str:
    if known_failures_path.exists():
        return known_failures_path.read_text(encoding="utf-8").strip()
    return "(none documented)"


def build_manifest(
    output_dir: Path,
    commit: str,
    timestamp: str,
    gate_results: list[tuple[str, str, bool, str]],  # (name, log_file, passed, notes)
    known_failures_content: str,
) -> str:
    overall = "PASS" if all(p for _, _, p, _ in gate_results) else "FAIL"

    rows = []
    for name, log_file, passed, notes in gate_results:
        status = "PASS" if passed else "FAIL"
        rows.append(f"| {name} | {status} | {log_file} | {notes} |")

    table = "\n".join(rows)

    manifest = f"""# RC Packet Manifest

**Commit:** {commit}
**Date:** {timestamp}
**Result:** {overall}

## Gate Results

| Gate | Status | Log | Notes |
|------|--------|-----|-------|
{table}

## Known Failures

{known_failures_content}
"""
    return manifest


# ---------------------------------------------------------------------------
# P2 notes extraction
# ---------------------------------------------------------------------------

def extract_p2_notes(output: str) -> str:
    """Extract pass/fail counts from pytest -q output for MANIFEST notes."""
    for line in reversed(output.splitlines()):
        line = line.strip()
        if "passed" in line or "failed" in line or "error" in line:
            # Strip ANSI escape codes (basic)
            import re
            clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
            return clean[:120]
    return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="RC Packet Builder (PRS-01 §9)")
    parser.add_argument(
        "--output-dir",
        default="RC_PACKET",
        help="Directory to write packet (default: RC_PACKET/)",
    )
    args = parser.parse_args()

    output_dir = REPO_ROOT / args.output_dir
    known_failures_path = SCRIPTS_DIR / "known_failures.txt"

    # Clear or create output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    commit = get_commit_hash()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"RC Packet Builder — PRS-01 §9")
    print(f"Commit: {commit[:12]}")
    print(f"Date:   {timestamp}")
    print(f"Output: {output_dir}")
    print("=" * 60)

    gate_results: list[tuple[str, str, bool, str]] = []

    for name, log_file, cmd_fn in GATES:
        cmd = cmd_fn(REPO_ROOT)
        log_path = output_dir / log_file

        print(f"  Running {name}...", end=" ", flush=True)
        passed, output = run_gate(name, cmd, log_path)
        status = "PASS" if passed else "FAIL"
        print(status)

        # Build notes for MANIFEST
        notes = ""
        if name == "P2 Test Suite":
            notes = extract_p2_notes(output)
        elif not passed:
            # First non-empty line from output as brief note
            for line in output.splitlines():
                line = line.strip()
                if line:
                    notes = line[:100]
                    break

        gate_results.append((name, log_file, passed, notes))

    print("=" * 60)
    all_passed = all(p for _, _, p, _ in gate_results)
    overall = "PASS" if all_passed else "FAIL"
    print(f"Result: {overall}")

    # Write known_failures.txt copy into packet
    known_failures_content = read_known_failures(known_failures_path)
    packet_known_failures = output_dir / "known_failures.txt"
    packet_known_failures.write_text(known_failures_content, encoding="utf-8")

    # Write MANIFEST.md
    manifest_content = build_manifest(
        output_dir, commit, timestamp, gate_results, known_failures_content
    )
    (output_dir / "MANIFEST.md").write_text(manifest_content, encoding="utf-8")

    print(f"Packet written to: {output_dir}/")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Playtest triage — analyze the latest play session transcript.

Usage:
    python scripts/triage_latest_playtest.py          # analyze latest log
    python scripts/triage_latest_playtest.py <file>   # analyze specific log

Extracts signals from transcript and prints a structured triage report.
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "runtime_logs"


def find_latest_log(specific_path=None):
    if specific_path:
        p = Path(specific_path)
        if p.exists():
            return p
        # Try relative to LOG_DIR
        p = LOG_DIR / specific_path
        if p.exists():
            return p
        print(f"ERROR: File not found: {specific_path}")
        return None

    latest_ptr = LOG_DIR / "LATEST"
    if not latest_ptr.exists():
        print("ERROR: No LATEST pointer found. Run a playtest first (python play.py).")
        return None
    name = latest_ptr.read_text(encoding="utf-8").strip()
    log_path = LOG_DIR / name
    if not log_path.exists():
        print(f"ERROR: LATEST points to {name} but file not found.")
        return None
    return log_path


def analyze_transcript(text):
    """Extract signals from a play session transcript."""
    findings = []
    lines = text.split("\n")

    # --- Evidence extraction ---
    player_commands = []
    for line in lines:
        # Lines that look like player input (Name> command)
        m = re.match(r"^[A-Z][a-zA-Z ]+>\s+(.+)$", line)
        if m:
            player_commands.append(m.group(1).strip())

    # --- Signal detection ---

    # Exceptions / tracebacks
    tracebacks = [i for i, l in enumerate(lines) if "Traceback" in l or "Error:" in l]
    if tracebacks:
        findings.append(("RED", "Exception detected", [lines[i] for i in tracebacks[:3]]))

    # Unknown commands
    unknowns = [l.strip() for l in lines if "Unknown command" in l]
    if unknowns:
        findings.append(("YELLOW", f"{len(unknowns)} unknown command(s) encountered", unknowns[:3]))

    # Clarification / failure messages
    failures = [l.strip() for l in lines if "Failed:" in l or "too far" in l]
    if failures:
        findings.append(("INFO", f"{len(failures)} clarification/failure message(s)", failures[:3]))

    # Combat result
    if "Victory!" in text:
        findings.append(("GREEN", "Combat ended: VICTORY", []))
    elif "fallen" in text.lower() or "Defeat" in text:
        findings.append(("GREEN", "Combat ended: DEFEAT", []))
    elif "Farewell" in text:
        findings.append(("INFO", "Session ended by player (quit)", []))
    else:
        findings.append(("YELLOW", "Combat did not reach conclusion", []))

    # Determinism check: same roll appearing in sequence (might indicate RNG issue)
    rolls = re.findall(r"Roll: \[(\d+)\]", text)
    if len(rolls) >= 4:
        if len(set(rolls)) == 1:
            findings.append(("RED", f"All {len(rolls)} d20 rolls were identical ({rolls[0]}) — RNG may be broken", []))

    # HP went below zero (normal, but worth noting)
    negative_hp = re.findall(r"HP \d+ -> (-\d+)", text)
    if negative_hp:
        findings.append(("INFO", f"Overkill damage occurred (HP went to {', '.join(negative_hp)})", []))

    # "no visible effect" — indicates an action resolved but produced nothing
    no_effect = [l.strip() for l in lines if "no visible effect" in l]
    if no_effect:
        findings.append(("YELLOW", f"{len(no_effect)} action(s) had no visible effect", no_effect))

    # Spell self-target (informational)
    self_casts = [l.strip() for l in lines if "on themselves" in l]
    if self_casts:
        findings.append(("INFO", f"{len(self_casts)} self-targeted spell(s)", self_casts))

    return player_commands, findings


def print_report(log_path, text, player_commands, findings):
    print("=" * 60)
    print("  PLAYTEST TRIAGE REPORT")
    print("=" * 60)
    print(f"  Log: {log_path.name}")
    print(f"  Lines: {len(text.split(chr(10)))}")
    print(f"  Player commands: {len(player_commands)}")
    if player_commands:
        for cmd in player_commands:
            print(f"    > {cmd}")
    print()

    # Decision
    reds = [f for f in findings if f[0] == "RED"]
    yellows = [f for f in findings if f[0] == "YELLOW"]

    if reds:
        decision = "RED"
        decision_text = "BLOCKED — fix required before proceeding"
    elif yellows:
        decision = "YELLOW"
        decision_text = "CAUTION — review findings, may need micro-WO"
    else:
        decision = "GREEN"
        decision_text = "CLEAR — proceed to next WO"

    print(f"  DECISION: {decision} — {decision_text}")
    print()

    # Findings
    print("  FINDINGS:")
    if not findings:
        print("    (none)")
    for severity, desc, evidence in findings:
        print(f"    [{severity}] {desc}")
        for e in evidence:
            print(f"           {e}")
    print()
    print("=" * 60)

    return decision


def main():
    specific = sys.argv[1] if len(sys.argv) > 1 else None
    log_path = find_latest_log(specific)
    if log_path is None:
        sys.exit(1)

    text = log_path.read_text(encoding="utf-8")
    if not text.strip():
        print(f"ERROR: Log file is empty: {log_path}")
        sys.exit(1)

    player_commands, findings = analyze_transcript(text)
    decision = print_report(log_path, text, player_commands, findings)

    # Exit code: 0=GREEN, 1=YELLOW, 2=RED
    if decision == "RED":
        sys.exit(2)
    elif decision == "YELLOW":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

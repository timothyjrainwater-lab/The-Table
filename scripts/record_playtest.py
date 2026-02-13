#!/usr/bin/env python3
"""Record a human playtest result for agent handoff persistence.

Usage:
    python scripts/record_playtest.py passed
    python scripts/record_playtest.py failed "targeting felt wonky"
    python scripts/record_playtest.py inconclusive

Appends one JSON line to pm_inbox/playtest_log.jsonl.
Next agent session reads the last entry to know gate status.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / "pm_inbox" / "playtest_log.jsonl"


def git_hash() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() not in ("passed", "failed", "inconclusive"):
        print("Usage: python scripts/record_playtest.py passed|failed|inconclusive [note]")
        sys.exit(1)

    result = sys.argv[1].lower()
    note = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit": git_hash(),
        "result": result,
        "note": note,
    }

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"Recorded: {result}" + (f" — {note}" if note else ""))
    print(f"Log: {LOG_PATH}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Check that pm_inbox/ root does not exceed the active file count cap.

CE-05 enforcement: pm_inbox/ root must contain no more than 15 active
.md files. Persistent operational files (README.md, PM_BRIEFING_CURRENT.md,
REHYDRATION_KERNEL_LATEST.md) don't count toward the cap.

Usage:
    python scripts/check_inbox_count.py

Exit codes:
    0 — Inbox is within cap
    1 — Inbox exceeds 15 active files (prints warning)
"""

from pathlib import Path

INBOX_DIR = Path("pm_inbox")
MAX_ACTIVE = 15
PERSISTENT_FILES = {
    "README.md",
    "PM_BRIEFING_CURRENT.md",
    "REHYDRATION_KERNEL_LATEST.md",
}


def main() -> int:
    if not INBOX_DIR.exists():
        print(f"WARNING: Inbox directory not found: {INBOX_DIR}")
        return 1

    # Count .md files in root only (not subdirectories), excluding persistent files
    active_files = [
        f.name
        for f in INBOX_DIR.iterdir()
        if f.is_file() and f.suffix == ".md" and f.name not in PERSISTENT_FILES
    ]

    count = len(active_files)

    if count > MAX_ACTIVE:
        print(
            f"CE-05 WARNING: Inbox has {count} active files "
            f"(cap: {MAX_ACTIVE}). "
            f"Archive the oldest completed file before adding new ones."
        )
        for name in sorted(active_files):
            print(f"  - {name}")
        return 1

    print(f"CE-05 OK: Inbox has {count}/{MAX_ACTIVE} active files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

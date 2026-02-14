#!/usr/bin/env python3
"""Check that the rehydration kernel does not exceed the 300-line budget.

CE-03 enforcement: pm_inbox/REHYDRATION_KERNEL_LATEST.md must not exceed
300 lines. If it does, the PM must compress or archive older sections
before adding new content.

Usage:
    python scripts/check_kernel_size.py

Exit codes:
    0 — Kernel is within budget
    1 — Kernel exceeds 300 lines (prints warning)
"""

from pathlib import Path

KERNEL_PATH = Path("pm_inbox/REHYDRATION_KERNEL_LATEST.md")
MAX_LINES = 300


def main() -> int:
    if not KERNEL_PATH.exists():
        print(f"WARNING: Kernel file not found: {KERNEL_PATH}")
        return 1

    line_count = len(KERNEL_PATH.read_text(encoding="utf-8").splitlines())

    if line_count > MAX_LINES:
        print(
            f"CE-03 WARNING: Kernel is {line_count} lines "
            f"(budget: {MAX_LINES}). "
            f"PM must compress or archive before adding content."
        )
        return 1

    print(f"CE-03 OK: Kernel is {line_count}/{MAX_LINES} lines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

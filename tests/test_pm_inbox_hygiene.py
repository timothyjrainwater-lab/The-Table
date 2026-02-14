"""PM Inbox Hygiene Enforcement Tests — Tier 1 Structural Invariants

These tests enforce the pm_inbox hygiene rules defined in pm_inbox/README.md.
They are structural tests (like test_boundary_law.py) — they check file naming,
lifecycle metadata, and count limits rather than functional behavior.

Rules Enforced:
    PMIH-001: Active file count must not exceed MAX_PM_INBOX_ACTIVE (15)
    PMIH-002: Every non-persistent .md file must use a recognized prefix
    PMIH-003: Every non-persistent .md file must have a Lifecycle: header in first 15 lines
    PMIH-004: Every MEMO_ file must contain a ## Retrospective section

Reference: pm_inbox/README.md — Inbox Hygiene Rules, File Type Prefixes, Lifecycle Header
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PM_INBOX = PROJECT_ROOT / "pm_inbox"

# Cap for active (non-persistent) .md files in pm_inbox root.
# Set at 15 — realistic ceiling that catches runaway growth.
# Previously was 10 (prose only, never enforced, violated 2.3x over).
MAX_PM_INBOX_ACTIVE = 15

# Persistent operational files exempt from prefix and lifecycle rules.
# These are always present and serve infrastructure purposes.
PERSISTENT_FILES = {
    "README.md",
    "PM_BRIEFING_CURRENT.md",
    "REHYDRATION_KERNEL_LATEST.md",
}

# Non-markdown persistent files (also exempt from .md rules)
PERSISTENT_NON_MD: set[str] = set()

# Recognized file prefixes for non-persistent pm_inbox files.
# Each prefix maps to a file type category.
VALID_PREFIXES = (
    "WO-",            # Work order dispatch
    "WO_SET",         # Batch of related WOs (WO_SET_*, WO_SET-*)
    "MEMO_",          # Session findings/summary
    "MEMO-",          # Session findings/summary (hyphen variant)
    "DEBRIEF_",       # Full context dump (Section 15.5 Pass 1)
    "DEBRIEF-",       # Full context dump (hyphen variant)
    "HANDOFF_",       # Cross-session context transfer
    "HANDOFF-",       # Cross-session context transfer (hyphen variant)
    "PO_REVIEW",      # Product owner review doc
    "PO_REVIEW-",     # Product owner review doc (hyphen variant)
    "BURST_",         # Research intake queue
    "BURST-",         # Research intake queue (hyphen variant)
    "FIX_WO",         # Fix work order dispatch packet
    "FIX_WO-",        # Fix work order dispatch packet (hyphen variant)
    "WO_INSTITUTIONALIZE",  # Institutionalization WO (legacy naming)
)

# Regex for valid lifecycle values
LIFECYCLE_PATTERN = re.compile(
    r"\*\*Lifecycle:\*\*\s*(NEW|TRIAGED|ACTIONED|ARCHIVE)",
    re.IGNORECASE,
)

# Regex for retrospective section heading
RETROSPECTIVE_PATTERN = re.compile(
    r"^#{1,3}\s+Retrospective",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_active_md_files() -> list[Path]:
    """Return all .md files in pm_inbox root that are NOT persistent operational files."""
    all_md = sorted(PM_INBOX.glob("*.md"))
    return [f for f in all_md if f.name not in PERSISTENT_FILES]


def _has_valid_prefix(filename: str) -> bool:
    """Check if a filename starts with one of the recognized prefixes."""
    return any(filename.startswith(prefix) for prefix in VALID_PREFIXES)


def _has_lifecycle_header(filepath: Path) -> bool:
    """Check if a file contains a Lifecycle: field in the first 15 lines."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 15:
                    break
                if LIFECYCLE_PATTERN.search(line):
                    return True
    except (OSError, UnicodeDecodeError):
        return False
    return False


def _get_memo_files() -> list[Path]:
    """Return all MEMO_ prefixed .md files in pm_inbox root."""
    active_files = _get_active_md_files()
    return [f for f in active_files if f.name.startswith("MEMO_") or f.name.startswith("MEMO-")]


def _has_retrospective_section(filepath: Path) -> bool:
    """Check if a file contains a ## Retrospective heading."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if RETROSPECTIVE_PATTERN.search(line):
                    return True
    except (OSError, UnicodeDecodeError):
        return False
    return False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPMIH001_ActiveFileCount:
    """PMIH-001: pm_inbox root must not exceed MAX_PM_INBOX_ACTIVE non-persistent .md files.

    WHY: Without a count limit, files accumulate indefinitely. The PM opens the
    folder and sees 20+ files with no priority ordering — the PM equivalent of
    context starvation. A prose-only cap of 10 existed previously and was violated
    2.3x over because it was never enforced (Tier 3).

    WHAT BREAKS: PM loses ability to triage effectively. New files get lost in noise.
    Action items from memos go unread. The inbox becomes write-only.

    FIX: PM must triage and archive files to bring count under the cap. Move
    Lifecycle: ARCHIVE files to pm_inbox/reviewed/. This test blocks until that happens.
    """

    def test_active_file_count_within_budget(self):
        active_files = _get_active_md_files()
        count = len(active_files)
        if count > MAX_PM_INBOX_ACTIVE:
            over = count - MAX_PM_INBOX_ACTIVE
            file_list = "\n".join(f"  - {f.name}" for f in active_files)
            pytest.fail(
                f"pm_inbox has {count} active .md files ({over} over the "
                f"{MAX_PM_INBOX_ACTIVE}-file cap).\n"
                f"PM must archive completed items to pm_inbox/reviewed/.\n"
                f"Active files:\n{file_list}"
            )


class TestPMIH002_NamingConvention:
    """PMIH-002: Every non-persistent .md file must use a recognized prefix.

    WHY: Consistent prefixes allow the PM to scan filenames and immediately know
    the file type (memo vs WO vs handoff vs debrief). Without prefixes, every file
    must be opened to determine its purpose — wasting PM context window.

    WHAT BREAKS: PM can't triage by filename. Files with unknown prefixes may be
    misrouted, missed, or confused with operational files.

    FIX: Rename the file to use a recognized prefix from pm_inbox/README.md.
    """

    def test_all_active_files_have_valid_prefix(self):
        active_files = _get_active_md_files()
        violations = [
            f.name for f in active_files
            if not _has_valid_prefix(f.name)
        ]
        assert not violations, (
            f"pm_inbox files with unrecognized prefixes:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nValid prefixes: "
            + ", ".join(sorted(set(VALID_PREFIXES)))
            + "\nSee pm_inbox/README.md for the full prefix table."
        )


class TestPMIH003_LifecycleHeader:
    """PMIH-003: Every non-persistent .md file must have a Lifecycle: header.

    WHY: Without lifecycle metadata, the PM can't tell which files are new (unread),
    which have been triaged, and which are ready to archive. Every triage pass
    requires re-reading file contents to determine status — wasteful and error-prone.

    WHAT BREAKS: PM can't do a fast triage scan. Files sit in inbox indefinitely
    because nobody knows if they've been processed. The archive drain stops working.

    FIX: Add '**Lifecycle:** NEW' (or TRIAGED/ACTIONED/ARCHIVE) within the first
    15 lines of the file.
    """

    def test_all_active_files_have_lifecycle_header(self):
        active_files = _get_active_md_files()
        violations = [
            f.name for f in active_files
            if not _has_lifecycle_header(f)
        ]
        assert not violations, (
            f"pm_inbox files missing Lifecycle: header in first 15 lines:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nEvery non-persistent file must include "
            "'**Lifecycle:** NEW|TRIAGED|ACTIONED|ARCHIVE' "
            "within the first 15 lines.\nSee pm_inbox/README.md."
        )


class TestPMIH004_MemoRetrospective:
    """PMIH-004: Every MEMO_ file must contain a ## Retrospective section.

    WHY: The three-pass debrief protocol (Section 15.5) requires agents to reflect
    on the process after completing work. Pass 1 captures facts (dump), Pass 2
    captures priorities (summary), Pass 3 captures judgment (retrospective). Without
    a mandatory retrospective section, agents skip it — and the operational insights
    that improve the system for the next agent are lost.

    WHAT BREAKS: The methodology stops being self-correcting. Fragility observations,
    process feedback, and governance doc accuracy reports never surface. The same
    process failures repeat across sessions because nobody captured what went wrong
    at the meta level.

    FIX: Add a '## Retrospective' section to the MEMO file with observations on
    fragility, process feedback, methodology insights, and concerns. See the template
    at methodology/templates/SESSION_MEMO_TEMPLATE.md.
    """

    @pytest.mark.xfail(
        reason="Existing MEMO files predate the retrospective requirement. "
               "Add ## Retrospective sections to existing MEMOs, then remove this xfail.",
        strict=False,
    )
    def test_all_memos_have_retrospective_section(self):
        memo_files = _get_memo_files()
        if not memo_files:
            pytest.skip("No MEMO files in pm_inbox")
        violations = [
            f.name for f in memo_files
            if not _has_retrospective_section(f)
        ]
        assert not violations, (
            f"MEMO files missing ## Retrospective section:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nEvery MEMO file must include a '## Retrospective' section "
            "with operational observations (fragility, process feedback, "
            "methodology insights, concerns).\n"
            "See methodology/templates/SESSION_MEMO_TEMPLATE.md."
        )

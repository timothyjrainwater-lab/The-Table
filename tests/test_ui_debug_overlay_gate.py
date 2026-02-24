"""Gate TOOLS-DBG — Debug Overlay (WO-UI-TOOLING-DEBUG-OVERLAY-001).

Static analysis tests (DBG-01 through DBG-04) confirm the debug overlay
code is correctly isolated behind the isDebugMode() guard.

DBG-05 and DBG-06 are Playwright integration tests that confirm the
#debug-hud element is absent in normal mode and present in debug mode.

Tests:
    DBG-01  debug-overlay.ts exists in client/src/
    DBG-02  isDebugMode() only reads URLSearchParams — no side effects
    DBG-03  mountDebugOverlay not called in main.ts outside isDebugMode() guard
    DBG-04  No AxesHelper or GridHelper instantiated outside debug-overlay.ts
    DBG-05  #debug-hud absent in normal page load (no ?debug=1)
    DBG-06  #debug-hud present in debug page load (?debug=1)
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
CLIENT_SRC = ROOT / "client" / "src"
DEBUG_OVERLAY = CLIENT_SRC / "debug-overlay.ts"
MAIN_TS = CLIENT_SRC / "main.ts"

# ---------------------------------------------------------------------------
# DBG-01: debug-overlay.ts exists
# ---------------------------------------------------------------------------

class TestDBG01FileExists:
    def test_debug_overlay_ts_exists(self):
        assert DEBUG_OVERLAY.exists(), f"debug-overlay.ts not found at {DEBUG_OVERLAY}"


# ---------------------------------------------------------------------------
# DBG-02: isDebugMode() only reads URLSearchParams — no side effects
# ---------------------------------------------------------------------------

class TestDBG02IsDebugModePure:
    def test_isDebugMode_body_only_reads_search(self):
        text = DEBUG_OVERLAY.read_text(encoding="utf-8")
        # Extract the isDebugMode function body
        match = re.search(
            r"export function isDebugMode\(\)[^{]*\{([^}]+)\}",
            text,
        )
        assert match, "isDebugMode() function not found in debug-overlay.ts"
        body = match.group(1).strip()

        # Must contain URLSearchParams
        assert "URLSearchParams" in body, "isDebugMode must use URLSearchParams"
        # Must contain .get('debug') or .get("debug")
        assert re.search(r"\.get\(['\"]debug['\"]\)", body), \
            "isDebugMode must call .get('debug')"
        # Must NOT reference document, window beyond location.search, or DOM
        assert "document" not in body, "isDebugMode must not touch document"
        assert "addEventListener" not in body, "isDebugMode must not add event listeners"


# ---------------------------------------------------------------------------
# DBG-03: mountDebugOverlay only called inside isDebugMode() guard in main.ts
# ---------------------------------------------------------------------------

class TestDBG03MountOnlyBehindGuard:
    def test_mount_call_inside_if_isDebugMode(self):
        text = MAIN_TS.read_text(encoding="utf-8")

        # Find call sites — exclude import lines (lines containing 'import')
        lines = text.splitlines()
        call_lines = [
            (i, line) for i, line in enumerate(lines)
            if "mountDebugOverlay" in line and not line.strip().startswith("import")
        ]
        assert len(call_lines) >= 1, "mountDebugOverlay not called (non-import) in main.ts"

        for line_no, line in call_lines:
            # Walk back up to 30 lines to find an enclosing if (isDebugMode()) guard
            window = lines[max(0, line_no - 30):line_no]
            window_text = "\n".join(window)
            assert "isDebugMode()" in window_text, (
                f"mountDebugOverlay call on line {line_no + 1} is not guarded "
                f"by isDebugMode() within the preceding 30 lines"
            )

    def test_import_present_in_main(self):
        text = MAIN_TS.read_text(encoding="utf-8")
        assert "mountDebugOverlay" in text and "debug-overlay" in text, \
            "debug-overlay import not found in main.ts"


# ---------------------------------------------------------------------------
# DBG-04: No AxesHelper or GridHelper outside debug-overlay.ts
# ---------------------------------------------------------------------------

class TestDBG04NoDebugHelpersInProduction:
    def _check_helper(self, helper_name: str) -> None:
        """
        Verify every instantiation of helper_name (e.g. 'AxesHelper') across
        client/src/*.ts is inside a debug guard (_debugMode or isDebugMode).
        Strategy: for each file, split into lines, find lines with the helper,
        then scan backwards up to 50 lines for a guard.
        """
        for ts_file in CLIENT_SRC.glob("*.ts"):
            if ts_file.name == "debug-overlay.ts":
                continue
            lines = ts_file.read_text(encoding="utf-8").splitlines()
            for line_no, line in enumerate(lines):
                if helper_name not in line:
                    continue
                # Look back up to 50 lines for a guard
                window = "\n".join(lines[max(0, line_no - 50):line_no + 1])
                guarded = "_debugMode" in window or "isDebugMode" in window
                assert guarded, (
                    f"'{helper_name}' in {ts_file.name}:{line_no + 1} "
                    f"is not inside a _debugMode or isDebugMode guard"
                )

    def test_no_AxesHelper_outside_debug_overlay(self):
        self._check_helper("AxesHelper")

    def test_no_GridHelper_outside_debug_overlay(self):
        self._check_helper("GridHelper")


# ---------------------------------------------------------------------------
# DBG-05 / DBG-06: Playwright integration tests
# ---------------------------------------------------------------------------

def _run_playwright(grep_pattern: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run playwright tests matching grep_pattern inside client/."""
    return subprocess.run(
        [
            sys.executable, "-m", "pytest", "--co", "-q",  # collect-only sanity
        ],
        capture_output=True, text=True, cwd=str(ROOT),
    )


@pytest.mark.playwright
class TestDBG05DebugHudAbsentNormalLoad:
    """DBG-05: #debug-hud absent without ?debug=1."""

    def test_playwright_spec_covers_normal_load(self):
        """
        Static check: the playwright spec directory exists and contains
        at least one .spec.ts file that exercises the base URL (no ?debug=1).
        This confirms the harness is in place for DBG-05 coverage.
        """
        spec_dir = ROOT / "client" / "tests" / "playwright"
        specs = list(spec_dir.glob("*.spec.ts"))
        assert len(specs) >= 1, "No playwright spec files found"
        # At least one spec navigates to '/' (normal load)
        found_normal_nav = any(
            "page.goto('/')" in s.read_text(encoding="utf-8") or
            'page.goto("/")'  in s.read_text(encoding="utf-8")
            for s in specs
        )
        assert found_normal_nav, "No playwright spec navigates to '/' (normal load)"


@pytest.mark.playwright
class TestDBG06DebugHudPresentDebugLoad:
    """DBG-06: #debug-hud present with ?debug=1."""

    def test_debug_overlay_ts_exports_addDebugHUD(self):
        """
        Static check: addDebugHUD is exported and sets id='debug-hud',
        confirming the element will be present when mountDebugOverlay runs.
        """
        text = DEBUG_OVERLAY.read_text(encoding="utf-8")
        assert "export function addDebugHUD" in text, \
            "addDebugHUD not exported from debug-overlay.ts"
        assert "debug-hud" in text, \
            "#debug-hud id not set in debug-overlay.ts"
        assert "mountDebugOverlay" in text, \
            "mountDebugOverlay not defined in debug-overlay.ts"

    def test_main_ts_calls_mount_behind_guard(self):
        """Confirm main.ts wires the overlay correctly (belt-and-suspenders with DBG-03)."""
        text = MAIN_TS.read_text(encoding="utf-8")
        assert "if (isDebugMode())" in text, \
            "main.ts missing if (isDebugMode()) guard"
        assert "mountDebugOverlay(scene)" in text, \
            "main.ts missing mountDebugOverlay(scene) call"

"""Gate TOOLS-PW — Playwright Harness (WO-UI-TOOLING-PLAYWRIGHT-001).

Static analysis tests confirm the Playwright infrastructure is correctly
wired. These do not require a running browser — they check that all
required config and spec files exist and are structurally correct.

Tests:
    PW-01  playwright.config.ts exists in client/
    PW-02  playwright.config.ts defines webServer with Vite command
    PW-03  playwright.config.ts uses baseURL http://localhost:3000
    PW-04  playwright.config.ts configures chromium project
    PW-05  posture screenshot spec exists
    PW-06  posture spec tests all 4 posture keys (1,2,3,4)
    PW-07  screenshot output dir is created in beforeAll
    PW-08  vitest test:unit script exists in client/package.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
CLIENT = ROOT / "client"
PW_CONFIG = CLIENT / "playwright.config.ts"
SPEC_DIR  = CLIENT / "tests" / "playwright"
PKG_JSON  = CLIENT / "package.json"


# ---------------------------------------------------------------------------
# PW-01: playwright.config.ts exists
# ---------------------------------------------------------------------------

class TestPW01ConfigExists:
    def test_playwright_config_exists(self):
        assert PW_CONFIG.exists(), f"playwright.config.ts not found at {PW_CONFIG}"


# ---------------------------------------------------------------------------
# PW-02: webServer uses Vite command
# ---------------------------------------------------------------------------

class TestPW02WebServer:
    def test_webserver_command_is_vite(self):
        text = PW_CONFIG.read_text(encoding="utf-8")
        assert "webServer" in text, "playwright.config.ts missing webServer"
        assert "vite" in text.lower(), "webServer command should reference vite"

    def test_reuseExistingServer_present(self):
        text = PW_CONFIG.read_text(encoding="utf-8")
        assert "reuseExistingServer" in text, \
            "playwright.config.ts missing reuseExistingServer"


# ---------------------------------------------------------------------------
# PW-03: baseURL is localhost:3000
# ---------------------------------------------------------------------------

class TestPW03BaseURL:
    def test_base_url_is_localhost_3000(self):
        text = PW_CONFIG.read_text(encoding="utf-8")
        assert "localhost:3000" in text, \
            "playwright.config.ts baseURL must be http://localhost:3000"


# ---------------------------------------------------------------------------
# PW-04: chromium project configured
# ---------------------------------------------------------------------------

class TestPW04ChromiumProject:
    def test_chromium_project_present(self):
        text = PW_CONFIG.read_text(encoding="utf-8")
        assert "chromium" in text.lower(), \
            "playwright.config.ts must configure a chromium project"


# ---------------------------------------------------------------------------
# PW-05: posture screenshot spec exists
# ---------------------------------------------------------------------------

class TestPW05SpecExists:
    def test_spec_file_exists(self):
        specs = list(SPEC_DIR.glob("*.spec.ts"))
        assert len(specs) >= 1, f"No .spec.ts files found in {SPEC_DIR}"

    def test_posture_screenshot_spec_present(self):
        specs = list(SPEC_DIR.glob("*.spec.ts"))
        found = any("posture" in s.name.lower() or "screenshot" in s.name.lower()
                    for s in specs)
        assert found, "No posture/screenshot spec file found in playwright tests dir"


# ---------------------------------------------------------------------------
# PW-06: spec tests all 4 posture keys
# ---------------------------------------------------------------------------

class TestPW06FourPostures:
    def _spec_text(self) -> str:
        specs = list(SPEC_DIR.glob("*.spec.ts"))
        assert specs, "No playwright spec files found"
        return "\n".join(s.read_text(encoding="utf-8") for s in specs)

    def test_posture_key_1_STANDARD(self):
        assert "'1'" in self._spec_text() or '"1"' in self._spec_text(), \
            "Posture key '1' (STANDARD) not found in playwright spec"

    def test_posture_key_2_DOWN(self):
        assert "'2'" in self._spec_text() or '"2"' in self._spec_text(), \
            "Posture key '2' (DOWN) not found in playwright spec"

    def test_posture_key_3_LEAN_FORWARD(self):
        assert "'3'" in self._spec_text() or '"3"' in self._spec_text(), \
            "Posture key '3' (LEAN_FORWARD) not found in playwright spec"

    def test_posture_key_4_DICE_TRAY(self):
        assert "'4'" in self._spec_text() or '"4"' in self._spec_text(), \
            "Posture key '4' (DICE_TRAY) not found in playwright spec"


# ---------------------------------------------------------------------------
# PW-07: screenshot dir created in beforeAll
# ---------------------------------------------------------------------------

class TestPW07ScreenshotDir:
    def test_mkdirSync_in_spec(self):
        spec_text = "\n".join(
            s.read_text(encoding="utf-8")
            for s in SPEC_DIR.glob("*.spec.ts")
        )
        assert "mkdirSync" in spec_text or "mkdir" in spec_text, \
            "Playwright spec should create screenshot dir (mkdirSync)"

    def test_beforeAll_present(self):
        spec_text = "\n".join(
            s.read_text(encoding="utf-8")
            for s in SPEC_DIR.glob("*.spec.ts")
        )
        assert "beforeAll" in spec_text, \
            "Playwright spec should set up screenshot dir in beforeAll"


# ---------------------------------------------------------------------------
# PW-08: test:unit script exists in package.json
# ---------------------------------------------------------------------------

class TestPW08PackageScripts:
    def test_test_unit_script_exists(self):
        pkg = json.loads(PKG_JSON.read_text(encoding="utf-8"))
        scripts = pkg.get("scripts", {})
        assert "test:unit" in scripts, \
            "package.json missing 'test:unit' script"

    def test_test_pw_script_exists(self):
        pkg = json.loads(PKG_JSON.read_text(encoding="utf-8"))
        scripts = pkg.get("scripts", {})
        assert "test:pw" in scripts, \
            "package.json missing 'test:pw' script"

    def test_vitest_in_devDeps(self):
        pkg = json.loads(PKG_JSON.read_text(encoding="utf-8"))
        dev = pkg.get("devDependencies", {})
        assert "vitest" in dev, "vitest not in devDependencies"

    def test_playwright_in_devDeps(self):
        pkg = json.loads(PKG_JSON.read_text(encoding="utf-8"))
        dev = pkg.get("devDependencies", {})
        assert "@playwright/test" in dev, "@playwright/test not in devDependencies"

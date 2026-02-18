# WO-UI-DRIFT-GUARD Debrief — Add Missing UI-G5 Drift Guard Tests

**Commit:** `06a80bb`
**Gate G (with drift guards):** 13/13 PASS
**Regression:** 124/124 PASS (Gates A-G including UI-G5 + no-backflow)

---

## 1. Scope Accuracy

The WO specified 3 drift guard tests. All 3 were delivered and appended to `tests/test_ui_gate_g.py` under a new UI-G5 section. No production code was modified. Gate G grew from 10 to 13 tests. Total gate count: 124.

1. **No canonical path** — Scans `aidm/core/event_log.py` and `aidm/core/replay_runner.py` for references to `ObjectPositionUpdate` or `TableObjectState`. Zero matches. PASS.
2. **No backflow imports** — Uses `ast.parse` to inspect all `aidm/ui/*.py` import statements. Checks against banned prefixes: `aidm.oracle`, `aidm.core.event_log`, `aidm.core.replay_runner`, `aidm.core.provenance`, `aidm.lens`, `aidm.immersion`. Zero violations. PASS.
3. **No teaching strings** — Static scan of `aidm/ui/table_objects.py` for banned tokens (`tooltip`, `popover`, `error_message`, `explanation`, `reason`, `because`, `cannot`, `can't`) and regex pattern `invalid.*zone.*message`. Zero matches. PASS.

## 2. Discovery Log

Pre-implementation grep confirmed all 3 invariants hold before writing tests. `table_objects.py` imports only from `__future__`, `dataclasses`, and `typing` — no cross-boundary dependencies. `event_log.py` and `replay_runner.py` have no awareness of UI types.

The `validate_zone_position` function returns `Optional[str]` (error message strings) rather than a pure boolean/None. The WO says zone validation should "return a boolean or None — not a message." The returned strings ("Invalid zone: ...", "Position (...) is not within zone ...") don't match any of the specific banned tokens/patterns. The strings are consumed internally by `update_position()` which returns `None` on failure — they never cross the WebSocket boundary. Noted here for PM awareness; not a test failure per the specified patterns.

## 3. Methodology Challenge

Test #3's scope is well-defined by the explicit pattern list, but the intent ("Zone validation must return a boolean or None — not a message") is stricter than what the pattern scan catches. `validate_zone_position` does return error message strings. A future WO could tighten this by either (a) changing the function to return `Optional[bool]` and moving error details to logging, or (b) adding a drift guard test that inspects the return type annotation directly. The current test catches the listed banned patterns — which is what the WO specifies.

## 4. Field Manual Entry

**#30 — AST-based import scanning is more reliable than string grep.** When guarding against backflow imports, `ast.parse` + `ast.walk` for `Import`/`ImportFrom` nodes catches both `import X` and `from X import Y` forms without false positives from comments, docstrings, or string literals. String scanning risks matching "aidm.oracle" in a docstring that merely mentions the module by name.

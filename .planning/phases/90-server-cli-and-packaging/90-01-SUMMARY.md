---
phase: 90-server-cli-and-packaging
plan: 01
subsystem: testing
tags: [pytest, fastapi, webview, wave-0, nyquist, conftest, fixtures]

requires: []

provides:
  - "Nyquist Wave 0 test scaffold: tests/test_cli_webview.py with 6 classes and 11 named tests"
  - "webview_analysis_dir + webview_server fixtures in tests/conftest.py with guaranteed teardown"

affects:
  - "90-02 (wave 1 server impl uses these tests as acceptance gate)"
  - "90-03 (wave 2 CLI impl uses these tests as acceptance gate)"

tech-stack:
  added: []
  patterns:
    - "Nyquist Wave 0: write all tests before any implementation (RED-first TDD)"
    - "Module-level import-safety: all webview runtime imports inside fixture/method bodies only"
    - "pytest.skip guard in webview_server fixture when fastapi extra absent"
    - "subprocess.Popen + poll-for-state-file pattern for real server integration tests"

key-files:
  created:
    - "tests/test_cli_webview.py"
  modified:
    - "tests/conftest.py"

key-decisions:
  - "Yield WebviewState object (not raw dict) from webview_server fixture; tests access .pid/.url/.port attributes"
  - "Top-level import of lucy_ng.cli.webview wrapped in try/except to allow pytest collection in Wave 0"
  - "Teardown kills server PID from .webview.json (not subprocess.pid) to handle serve-delegates-to-child architectures"
  - "webview_server fixture invokes serve subcommand (not hidden _run) so the full lifecycle code is exercised"

requirements-completed: [WV-01, WV-02, WV-08]

duration: 2min
completed: 2026-07-03
---

# Phase 90 Plan 01: Server CLI and Packaging — Wave 0 Test Scaffold

**Six-class pytest scaffold (11 named tests) for lucy webview serve/stop/status CLI plus FastAPI health-endpoint and packaging assertions — RED until waves 1-2 land implementation.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-07-03T07:06:12Z
- **Completed:** 2026-07-03T07:08:01Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Wrote `tests/test_cli_webview.py` with 6 classes and exactly 11 test methods matching the 90-VALIDATION.md test map (TestImportSafety, TestPackaging, TestWebviewApp, TestFreePort, TestWebviewStatus, TestWebviewLifecycle)
- Added `webview_analysis_dir` and `webview_server` fixtures to `tests/conftest.py`; all webview-runtime imports are inside fixture bodies (no fastapi at module top), SIGTERM teardown guarantees no orphan processes
- Tests collect cleanly under pytest (11 items); Wave 0 RED state confirmed (test_webview_extra_declared fails correctly because pyproject.toml webview extra is not declared yet)

## Task Commits

1. **Task 1: Add webview fixtures to conftest.py** — `b97927e` (feat)
2. **Task 2: Write full test scaffold tests/test_cli_webview.py** — `63f79e9` (feat)

## Files Created/Modified

- `tests/test_cli_webview.py` — Nyquist Wave 0 scaffold: 6 classes, 11 tests covering WV-01/WV-02/WV-08
- `tests/conftest.py` — Two new fixtures: `webview_analysis_dir` (tmp_path-based) + `webview_server` (subprocess lifecycle with guaranteed teardown)

## Decisions Made

- Wrapped top-level `from lucy_ng.cli.webview import webview` in `try/except ImportError` so that pytest can collect the file even in Wave 0 (when the module does not exist yet). Individual tests that require the CLI skip explicitly via `if webview is None: pytest.skip(...)`.
- `webview_server` fixture teardown kills the PID recorded in `.webview.json` (not the spawned subprocess PID) because the `serve` command is expected to delegate the long-running uvicorn process to a child; the subprocess itself may exit quickly.
- `TestWebviewStatus.test_status_stale_pid` probes PID 99999 for liveness before writing a stale state file; falls back to 99998 with a skip if both PIDs happen to be alive.

## Deviations from Plan

None — plan executed exactly as written. The PATTERNS.md conftest sketch used `_run` hidden command in the fixture, but the plan text explicitly requires `serve`; followed the plan text.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Wave 0 complete: acceptance-gate tests exist for all 11 behaviors in the phase
- Plan 90-02 (server implementation: WebviewState + webview.app + webview.server) can now begin; its success is verified by `pytest tests/test_cli_webview.py::TestWebviewApp tests/test_cli_webview.py::TestFreePort tests/test_cli_webview.py::TestWebviewStatus -x`
- Plan 90-03 (CLI + packaging) verified by the remaining classes (TestImportSafety, TestPackaging, TestWebviewLifecycle)

---
*Phase: 90-server-cli-and-packaging*
*Completed: 2026-07-03*

## Self-Check: PASSED

- `tests/test_cli_webview.py` — FOUND
- `tests/conftest.py` — FOUND (modified)
- Commit b97927e — FOUND
- Commit 63f79e9 — FOUND

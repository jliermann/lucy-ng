---
phase: 91-api-endpoints-depictions-and-static-frontend
plan: 01
subsystem: testing
tags: [pytest, fastapi, testclient, webview, fixtures]

# Dependency graph
requires:
  - phase: 90-server-cli-and-packaging
    provides: create_app() factory, webview_analysis_dir fixture, existing conftest patterns
provides:
  - "empty_analysis_dir / live_analysis_dir / final_analysis_dir pytest fixtures in tests/conftest.py"
  - "tests/test_webview_api.py with 7 test classes covering all Phase 91 API contracts"
  - "Nyquist scaffold: Plans 02/03/04 verify against these tests"
affects:
  - 91-02
  - 91-03
  - 91-04

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy imports inside test functions (never module-level) for fastapi / lucy_ng.webview.*"
    - "make_router(analysis_dir) factory test pattern: FastAPI() + include_router + TestClient"
    - "Wave 0 Nyquist scaffold: tests RED until implementation plans land"

key-files:
  created:
    - tests/test_webview_api.py
  modified:
    - tests/conftest.py

key-decisions:
  - "Epoch values in live_analysis_dir timing.jsonl fixtures are JSON strings ('1751630400') not ints, matching shell printf %s output"
  - "Malformed SMILES placed at index 2 in live_analysis_dir solutions.smi so placeholder tests target a stable slot"
  - "All fastapi / lucy_ng.webview.* imports inside test function bodies (try/except ImportError → pytest.skip) to preserve WV-08 collect-safety"

patterns-established:
  - "Pattern: mount individual routers on fresh FastAPI() in unit tests (not create_app) for isolation"
  - "Pattern: CASE-PROGRESS.md in live_analysis_dir fixture with ## Iteration 1 + ### LSD-Engineer for log/status fallback coverage"

requirements-completed: [WV-03, WV-04, WV-05, WV-06]

# Metrics
duration: 4min
completed: 2026-07-04
---

# Phase 91 Plan 01: Test Scaffold Summary

**Pytest fixtures for three analysis-dir states and a 16-test Nyquist scaffold asserting exact payload contracts for all Phase 91 API endpoints, depiction, frontend, and packaging**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-07-04T14:05:29Z
- **Completed:** 2026-07-04T14:08:39Z
- **Tasks:** 2 of 2
- **Files modified:** 2

## Accomplishments

- Added `empty_analysis_dir`, `live_analysis_dir`, `final_analysis_dir` fixtures to `tests/conftest.py` without touching existing Phase 90 fixtures
- `live_analysis_dir` writes `timing.jsonl` with epoch as JSON strings, `iteration_01/solutions.smi` with malformed SMILES at index 2, and `CASE-PROGRESS.md` with `## Iteration 1` + `### LSD-Engineer` headers
- `final_analysis_dir` writes `timing.json` (total_duration_s=5400) and `ranking_results.json` with ranked solutions (benzene rank 1, mae 0.1, quality "excellent")
- Created `tests/test_webview_api.py` with 7 test classes (16 tests total): TestStatusEndpoint, TestLogEndpoint, TestStructuresEndpoint, TestDepiction, TestFrontend, TestWiring, TestPackaging
- All imports of fastapi / lucy_ng.webview.* are inside test function bodies — file collects cleanly with `pytest --collect-only` (exit 0) before any implementation exists

## Task Commits

Each task was committed atomically:

1. **Task 1: Add three analysis-dir fixtures to tests/conftest.py** - `fa82532` (test)
2. **Task 2: Create tests/test_webview_api.py with all Phase 91 test classes** - `88e6f9d` (test)

**Plan metadata:** (see below — docs commit)

## Files Created/Modified

- `tests/conftest.py` — appended `empty_analysis_dir`, `live_analysis_dir`, `final_analysis_dir` fixtures (existing fixtures unchanged)
- `tests/test_webview_api.py` — new file: 7 test classes, 16 tests, all imports lazy inside function bodies

## Decisions Made

- Used `json.dumps()` to serialize timing events (not hardcoded strings) so epoch values are guaranteed to be JSON strings — matching real `case.md` shell output.
- Placed CASE-PROGRESS.md in `live_analysis_dir` (not just `empty_analysis_dir`) so the log and status-fallback tests have content without requiring a separate fixture variant.
- Tested routers in isolation (mount on fresh `FastAPI()`) rather than through `create_app()` in all non-wiring tests — gives finer-grained failure attribution.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Known Stubs

None — test-only files, no runtime payload stubs.

## Threat Flags

None — test-only artifacts. All file writes are confined to pytest `tmp_path` (T-91-01, accepted in plan threat model).

## Self-Check

- [x] `tests/conftest.py` contains `def empty_analysis_dir`, `def live_analysis_dir`, `def final_analysis_dir`
- [x] `tests/test_webview_api.py` exists and is a new file
- [x] `pytest tests/test_webview_api.py --collect-only` exits 0, 16 tests collected
- [x] `pytest tests/test_cli_webview.py -q -k "not server"` — 11 passed
- [x] fa82532 commit exists in git log
- [x] 88e6f9d commit exists in git log

## Self-Check: PASSED

## Next Phase Readiness

- Plans 02 (status + log routers), 03 (structures router + depiction), 04 (frontend + wiring + packaging) each have a named test to go GREEN against.
- TestPackaging will turn GREEN once `pyproject.toml` `artifacts` is extended (Plan 04).
- No blockers.

---
*Phase: 91-api-endpoints-depictions-and-static-frontend*
*Completed: 2026-07-04*

---
phase: 92-orchestrator-integration
plan: "01"
subsystem: tests
tags: [tdd, wave-0, nyquist, webview, grep-contract, lifecycle]
dependency_graph:
  requires: []
  provides: [test_case_md_wv07, test_serve_outlives_caller]
  affects: [tests/test_case_md_wv07.py, tests/test_cli_webview.py]
tech_stack:
  added: []
  patterns: [grep-contract testing, subprocess lifecycle integration test]
key_files:
  created:
    - tests/test_case_md_wv07.py
  modified:
    - tests/test_cli_webview.py
decisions:
  - "[Rule 1 - Bug] Used content=\"[BEGIN] peak-picking as push-marker string instead of [BEGIN] peak-picking to avoid ordering collision with line-146 Task-prompt occurrence"
metrics:
  duration: "~3 minutes"
  completed: "2026-07-06"
  tasks_completed: 2
  files_changed: 2
---

# Phase 92 Plan 01: Wave 0 Test Scaffold Summary

**One-liner:** Nyquist test scaffold: four grep-contract tests pin the WV-07 case.md edit contract (3 RED, 1 regression-guard GREEN) plus a subprocess lifecycle test proving server outlives its caller (GREEN).

## What Was Built

Two test artifacts that make the Phase 92 success criteria machine-checkable before any case.md edit:

**`tests/test_case_md_wv07.py`** — four grep-based assertions over case.md and progress-format.md:
- `test_webview_launch_present`: asserts `lucy webview serve` is present and precedes the first `[BEGIN] peak-picking` SendMessage push (RED until 92-02)
- `test_stop_hint_present`: asserts `lucy webview stop` hint is present in the pre-terminate_team region (RED until 92-02)
- `test_terminate_team_no_stop`: regression guard asserting `lucy webview stop` is NOT in the terminate_team section (GREEN both before and after 92-02)
- `test_progress_format_dashboard_field`: asserts `**Dashboard:**` field is in progress-format.md header template (RED until 92-02)

**`tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_outlives_caller`** — integration test proving the Phase 90 `start_new_session=True` detachment works:
- Launches server via `subprocess.run` (blocking call that returns in ~5 s)
- Asserts `elapsed < 10 s` (non-blocking contract)
- Asserts `os.kill(pid, 0)` succeeds after caller exits (survival contract)
- Cleans up via `lucy webview stop` in finally block
- GREEN immediately; SKIPs cleanly when fastapi extra is absent

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed push-marker string in test_webview_launch_present**
- **Found during:** Task 1 analysis — reading case.md revealed `[BEGIN] peak-picking` appears at line 146 (inside a Task() agent-prompt) AND at line 224 (the actual SendMessage push). Using `case.index("[BEGIN] peak-picking")` as the plan specified would always find line 146 first, making the ordering assertion `serve_idx < push_idx` permanently FALSE even after 92-02 inserts `lucy webview serve` at line ~219.
- **Fix:** Used `content="[BEGIN] peak-picking` (the SendMessage-specific variant) as the push marker. This substring appears only once (line 224), so the ordering assertion correctly tests that the webview launch block precedes the actual team kick-off.
- **Files modified:** tests/test_case_md_wv07.py
- **Commit:** 6824fb1

## Wave 0 Test State (before 92-02)

| Test | File | Status | Reason |
|------|------|--------|--------|
| test_webview_launch_present | test_case_md_wv07.py | RED (AssertionError) | lucy webview serve not yet in case.md |
| test_stop_hint_present | test_case_md_wv07.py | RED (AssertionError) | lucy webview stop not yet in pre-terminate region |
| test_terminate_team_no_stop | test_case_md_wv07.py | GREEN (regression guard) | no lucy webview stop in terminate_team (correct) |
| test_progress_format_dashboard_field | test_case_md_wv07.py | RED (AssertionError) | **Dashboard:** not yet in progress-format.md |
| test_serve_outlives_caller | test_cli_webview.py | GREEN | Phase 90 start_new_session=True already delivers survival |

## Commits

| Task | Commit | Files |
|------|--------|-------|
| Task 1: grep-contract tests | 6824fb1 | tests/test_case_md_wv07.py (new, 149 lines) |
| Task 2: outlives-caller test | 3b0590a | tests/test_cli_webview.py (+74 lines) |

## Self-Check: PASSED

- [x] tests/test_case_md_wv07.py exists (149 lines, 4 test functions)
- [x] tests/test_cli_webview.py contains test_serve_outlives_caller
- [x] Commits 6824fb1 and 3b0590a exist in git log
- [x] pytest --collect-only collects 16 tests from both files with 0 errors
- [x] test_serve_outlives_caller PASSES (GREEN)
- [x] test_webview_launch_present, test_stop_hint_present, test_progress_format_dashboard_field FAIL with AssertionError (RED, expected)
- [x] test_terminate_team_no_stop PASSES (GREEN regression guard, correct)
- [x] No orphan uvicorn process after test run (finally block cleans up)

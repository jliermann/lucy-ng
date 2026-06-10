---
phase: 81-peak-picking-integrity-fix-08
plan: "02"
subsystem: analysis-cli
tags: [fix, overcount, symmetry, noise-guard, tdd]
dependency_graph:
  requires: []
  provides: [overcount-alarm-cli, overcount-alarm-python-api]
  affects: [src/lucy_ng/cli/analyze.py, src/lucy_ng/analysis/symmetry_analysis.py]
tech_stack:
  added: []
  patterns: [TDD red-green, dataclass property guard]
key_files:
  created: []
  modified:
    - src/lucy_ng/cli/analyze.py
    - src/lucy_ng/analysis/symmetry_analysis.py
    - tests/test_cli_analyze.py
    - tests/test_symmetry_analysis.py
decisions:
  - Use elif chain (missing_carbons < 0 / == 0 / > 0) to avoid OVERCOUNT alarm suppressing undercount hint
  - C200H300O5 formula used for overcount_alarm=false CLI test — robust against any snr_floor default
  - Pre-existing ruff E501 + I001 violations in symmetry_analysis.py left untouched (out-of-scope)
metrics:
  duration: "~20 minutes"
  completed: "2026-06-10T08:14:14Z"
---

# Phase 81 Plan 02: Overcount Guard Summary

**One-liner:** Added `overcount_alarm` JSON field + actionable `Warning:` text to `analyze_symmetry` CLI, and `OVERCOUNT ALARM` branch to `SymmetryAnalysisResult.summary()` for the `missing_carbons < 0` case.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 (RED) | Failing tests for analyze_symmetry overcount alarm | d5c68fa | tests/test_cli_analyze.py |
| 1 (GREEN) | Implement overcount alarm in analyze_symmetry CLI | cde0dc0 | src/lucy_ng/cli/analyze.py, tests/test_cli_analyze.py |
| 2 (RED) | Failing tests for SymmetryAnalysisResult overcount alarm | 4028733 | tests/test_symmetry_analysis.py |
| 2 (GREEN) | Implement OVERCOUNT ALARM in SymmetryAnalysisResult.summary() | 080a583 | src/lucy_ng/analysis/symmetry_analysis.py |

## What Was Built

### Task 1: analyze_symmetry CLI overcount alarm

`src/lucy_ng/cli/analyze.py` `analyze_symmetry()`:

- JSON output gains two new fields: `"overcount_alarm": difference < 0` (bool) and `"overcount_excess": max(0, -difference)` (int)
- Text output `elif difference < 0` branch replaced with an actionable message containing both `"Warning:"` (capital W, preserving the existing case-sensitive test assertion at line 40) and `"more signals than carbons"` with observed/expected counts and `--snr-floor 5` re-pick advice
- Exit code remains 0 (warning, not error)
- Existing `if difference > 0` equivalence hint unchanged

### Task 2: SymmetryAnalysisResult.summary() overcount alarm

`src/lucy_ng/analysis/symmetry_analysis.py` `SymmetryAnalysisResult.summary()`:

- Added `if self.missing_carbons < 0` branch before the existing `elif self.missing_carbons > 0` branch
- Output: `"  OVERCOUNT ALARM: {N} more signals than carbons — likely noise peaks in the spectrum. Re-pick at snr_floor >= 5 before any symmetry or DBE reasoning."`
- `has_symmetry` property unchanged (already returns False for missing_carbons < 0)
- Undercount path (`missing_carbons > 0`) and zero-difference path unaffected

## Test Coverage

New tests added:
- `tests/test_cli_analyze.py`: 3 new tests — overcount text warning, overcount JSON alarm, normal JSON alarm=false
- `tests/test_symmetry_analysis.py`: 5 new tests — OVERCOUNT ALARM in summary, "more signals than carbons" text, has_symmetry=False for overcount, undercount regression guard, zero-diff regression guard

All 34 tests pass (8 in test_cli_analyze.py, 26 in test_symmetry_analysis.py).

## Deviations from Plan

### Auto-adjusted: Test for overcount_alarm=false

**Found during:** Task 1 GREEN
**Issue:** The plan's done criteria used `C13H18O2` / `data/Ibuprofen/2` to test `overcount_alarm=false`. With `snr_floor=3.0` (default in this worktree — plan 81-01 runs in parallel and hasn't merged yet), the picker returns 147 peaks for Ibuprofen/2, making `observed (147) > expected (13)` and `overcount_alarm=True`. The test would fail.
**Fix:** Used `C200H300O5` (200 expected carbons, always above any realistic peak count) to test the `overcount_alarm=false` path robustly, regardless of snr_floor default.
**Files modified:** tests/test_cli_analyze.py
**Commit:** cde0dc0

### Out-of-scope: Pre-existing ruff violations in symmetry_analysis.py

**Found during:** Task 2 verification
**Issue:** `symmetry_analysis.py` has 5 pre-existing ruff errors (I001 import sort + E501 on lines 61, 72, 103, 113) that predate this plan. None are in lines modified by this plan.
**Action:** Not fixed (out of scope per deviation rules — only fix issues directly caused by current task's changes). Logged here for awareness.
**Fix:** Deferred — tracked in deferred-items.md.

## Known Stubs

None. Both modified files produce real diagnostic output from real data.

## Threat Flags

None. This plan makes no network calls, writes no files, and adds no new attack surface. The overcount alarm is a diagnostic text message only.

## TDD Gate Compliance

- RED commit (test): d5c68fa (Task 1), 4028733 (Task 2) — both verified to fail before implementation
- GREEN commit (feat): cde0dc0 (Task 1), 080a583 (Task 2) — all tests pass after implementation
- REFACTOR: not needed

## Self-Check: PASSED

- src/lucy_ng/cli/analyze.py: exists, contains "overcount_alarm" and "more signals than carbons"
- src/lucy_ng/analysis/symmetry_analysis.py: exists, contains "OVERCOUNT ALARM"
- tests/test_cli_analyze.py: exists, 8 tests pass
- tests/test_symmetry_analysis.py: exists, 26 tests pass
- Commits d5c68fa, cde0dc0, 4028733, 080a583: all in git log

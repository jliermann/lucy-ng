---
phase: 81-peak-picking-integrity-fix-08
plan: "04"
subsystem: tests
tags: [fix-08, regression-tests, snr-floor, overcount-guard, case9, case1]
dependency_graph:
  requires: [81-01, 81-02]
  provides: [fix08-regression-suite]
  affects: [tests/test_peak_picking_integrity.py]
tech_stack:
  added: []
  patterns: [pytest-skipif-external-data, synthetic-unit-test, click-testing-cli]
key_files:
  created:
    - tests/test_peak_picking_integrity.py
  modified: []
decisions:
  - "Use CASE1/Ibuprofen/2 with formula C4H8 to trigger overcount_alarm via CLI (no fabricated spectrum needed)"
  - "HydrogenBudgetResult requires molecular_formula field — plan sketch used wrong constructor; corrected to match actual dataclass"
  - "E501 ruff error in docstring of test_overcount_symmetry_analysis_summary fixed inline (directly caused by this plan)"
metrics:
  duration: "~15 minutes"
  completed: "2026-06-10"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 1
---

# Phase 81 Plan 04: FIX-08 Regression Test Suite Summary

## One-Liner

Created `tests/test_peak_picking_integrity.py` with 8 regression tests locking in the Phase-81 peak-picking invariants: CASE9/12 at snr_floor=5 returns ≤30 peaks with carbonyl present and no impossible peaks; overcount guard fires on 76-vs-12 synthetic case; ibuprofen not regressed.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write test_peak_picking_integrity.py (FIX-08 regression suite) | 4f78c99 | tests/test_peak_picking_integrity.py |
| 2 | Full suite health check | (no commit — verification only) | — |

## What Was Built

### tests/test_peak_picking_integrity.py (155 lines)

Three test classes:

**TestFIX08CASE9Integration** (4 tests, all skipif-guarded on CASE9_C13.exists()):
- `test_case9_snr5_peak_count` — CASE9/12 at snr_floor=5 → ≤30 peaks
- `test_case9_snr5_no_impossible_peaks` — no peak >230 ppm (physically impossible for organic C)
- `test_case9_snr5_carbonyl_present` — ester C=O at ~166.08 ppm in 164–168 ppm window
- `test_case9_default_snr_is_5` — default pick == explicit snr_floor=5.0 pick (default locked at 5)

**TestFIX08OvercountGuard** (3 tests, fully synthetic — always runs):
- `test_overcount_symmetry_analysis_summary` — build SymmetryAnalysisResult(signal_count=76, expected_carbons=12) → "OVERCOUNT ALARM" in summary()
- `test_overcount_cli_json` — CLI `analyze symmetry C4H8 data/Ibuprofen/2 --format json` → overcount_alarm=True
- `test_overcount_cli_text` — same invocation → "more signals than carbons" in text output

**TestFIX08CASE1Regression** (1 test, in-repo data — always runs):
- `test_case1_snr5_count_floor` — ibuprofen at snr_floor=5.0 → ≥9 peaks (non-regression floor)

## Full Suite Results

```
pytest --tb=short -q
1070 passed, 14 skipped, 1 xfailed, 31 warnings in 34.32s
```

- 1070 passing (up from 1054 pre-Phase-81 baseline — Plans 01-02 added tests, Plan 04 adds 8 more)
- 14 skipped (CASE9 external-data tests run on this machine; skips are from other external-data guards)
- 0 new failures
- ruff: clean on tests/test_peak_picking_integrity.py (0 errors); pre-existing E501/I001/F401 errors in src/ are unrelated and predate this plan
- mypy: pre-existing errors in cli/lsd.py and pylsd.py only; no new errors from this plan

## CASE9 Test Results (data present on this machine)

All 4 CASE9 integration tests ran and PASSED:
- Peak count at snr_floor=5: ≤30 peaks (no noise flood)
- No impossible peaks >230 ppm: 0 (was 13 at snr_floor=3)
- Carbonyl at 164–168 ppm: present (ester C=O at ~166.08)
- Default equals explicit snr_floor=5.0: confirmed

## Deviations from Plan

### Auto-fixed: HydrogenBudgetResult constructor — plan sketch had wrong fields

**Found during:** Task 1 implementation
**Issue:** The plan's task action showed `HydrogenBudgetResult(expected_h=16, total_accounted=16, missing_h=0, has_equivalents=False)`. The actual `@dataclass HydrogenBudgetResult` requires 6 positional fields: `molecular_formula`, `expected_h`, `carbon_assigned_h`, `heteroatom_h`, `total_accounted`, `missing_h`. The `has_equivalents` field does not exist (it is a `@property`).
**Fix:** Used correct constructor: `HydrogenBudgetResult(molecular_formula="C12H16O3", expected_h=16, carbon_assigned_h=16, heteroatom_h=0, total_accounted=16, missing_h=0)`.
**Rule:** Rule 3 (auto-fix blocking issue — wrong constructor would cause TypeError at import)
**Files modified:** tests/test_peak_picking_integrity.py
**Commit:** 4f78c99

### Auto-fixed: E501 ruff error in docstring

**Found during:** Task 2 health check
**Issue:** One docstring line 107 chars (limit 100) in `test_overcount_symmetry_analysis_summary`.
**Fix:** Shortened docstring to `"summary() contains 'OVERCOUNT ALARM' when observed signal_count > expected_carbons."` (96 chars).
**Rule:** Rule 1 (directly caused by this plan's changes)
**Files modified:** tests/test_peak_picking_integrity.py
**Commit:** amended into 4f78c99

## Known Stubs

None. All tests exercise real code paths.

## Threat Flags

None. Test-only plan. No new production code, no network calls, no new attack surface. External CASE9 data accessed read-only under skipif guard.

## Self-Check: PASSED

- tests/test_peak_picking_integrity.py: exists (155 lines, 8 test methods)
- Commit 4f78c99: in git log
- All 8 tests pass: `pytest tests/test_peak_picking_integrity.py` → 8 passed
- Full suite: 1070 passed, 0 failures
- ruff tests/test_peak_picking_integrity.py: 0 errors

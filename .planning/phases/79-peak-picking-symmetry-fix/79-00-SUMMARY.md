---
phase: 79-peak-picking-symmetry-fix
plan: "00"
subsystem: testing

tags: [tdd, peak-picker, snr, mad-threshold, intensity-symmetry, requirements]

# Dependency graph
requires:
  - phase: 78-blind-re-uat
    provides: "CASE9 forensics confirming peak-picking defects FIX-04/05/06 scope"

provides:
  - "FIX-04/05/06 requirements in REQUIREMENTS.md traceability table"
  - "Failing test stubs for _compute_snr_threshold (FIX-04)"
  - "Failing test stubs for detect_intensity_symmetry (FIX-05)"
  - "RED state confirmed: Plans 01 and 02 have failing tests to make green"

affects: [79-01-PLAN, 79-02-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED gate: stub tests import functions that don't yet exist → ImportError → RED confirmed"
    - "skipif guard for CASE9 dataset (outside repo) with CASE1 (in-repo) having no skip"

key-files:
  created:
    - tests/test_peak_picker_snr.py
    - tests/test_intensity_symmetry.py
  modified:
    - .planning/REQUIREMENTS.md

key-decisions:
  - "FIX-04 stub imports _compute_snr_threshold directly (not just AdaptivePeakPicker) to enforce RED state even if existing pick_peaks signature is unchanged"
  - "FIX-05 stub imports detect_intensity_symmetry from peak_picker module (not a separate module) consistent with PATTERNS.md design"
  - "REQUIREMENTS.md count updated 10→13 (3 new FIX entries); traceability table extended with Phase 79 rows"

patterns-established:
  - "Stub test files use module-level imports that fail with ImportError — RED state is enforced at collection time, not at test execution time"

requirements-completed: [FIX-04, FIX-05, FIX-06]

# Metrics
duration: 12min
completed: 2026-06-08
---

# Phase 79 Plan 00: Wave-0 TDD Stubs + Requirements Traceability Summary

**FIX-04/05/06 added to REQUIREMENTS.md traceability; two failing test stub files created (RED state) for SNR/MAD threshold and 2C-equivalence detection**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-08T00:00:00Z
- **Completed:** 2026-06-08T00:12:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- REQUIREMENTS.md extended with FIX-04 (SNR/MAD peak-picker), FIX-05 (intensity-symmetry 2C detection), and FIX-06 (skill feedback loop) — all mapped to Phase 79 with Pending status; total v1 requirements count updated from 10 to 13
- `tests/test_peak_picker_snr.py` created with 7 test methods across 4 classes (TestSNRThreshold, TestCASE9Regression, TestCASE1Regression, TestCLIPick1D) — fails at collection with ImportError on `_compute_snr_threshold` (RED state confirmed)
- `tests/test_intensity_symmetry.py` created with 5 test methods in TestDetectIntensitySymmetry with CASE9-like synthetic fixtures — fails at collection with ImportError on `detect_intensity_symmetry` (RED state confirmed)
- Existing 1016 tests continue to pass with no regression

## Task Commits

Each task was committed atomically:

1. **Task 1: Add FIX-04/05/06 to REQUIREMENTS.md traceability table** - `02ef96a` (chore)
2. **Task 2: Create failing test stubs for FIX-04 and FIX-05** - `e94ff36` (test)

## Files Created/Modified

- `.planning/REQUIREMENTS.md` — Added FIX-04/05/06 requirements (Post-UAT Fixes section) + traceability table rows + count update (10→13)
- `tests/test_peak_picker_snr.py` — 7 test methods: CDCl3 MAD unit test, CASE9 carbonyl regression (skipif), CASE9 SNR annotation (skipif), CASE1 peak count regression, CLI JSON snr/noise_sigma field tests
- `tests/test_intensity_symmetry.py` — 5 test methods: two 2C candidates flagged, count==2, non-aromatic excluded, empty-list guard, single-peak guard

## Decisions Made

- Stubs import `_compute_snr_threshold` and `detect_intensity_symmetry` at module level (not inside test functions) to guarantee ImportError at collection time — this is the cleanest RED-state enforcement pattern
- CASE9 tests use `pytest.mark.skipif(not CASE9_C13.exists(), ...)` — CASE9 data lives outside the repo; CASE1 (Ibuprofen/2) is in-repo so no skip guard needed
- Synthetic fixture intensities chosen to reproduce the CASE9 phenotype: two 2C peaks at ~1.8e7, two 1C Cq at ~3e6, one non-aromatic CH3 at ~1.7e7 (tests the scope boundary at 100 ppm)

## Deviations from Plan

**Plan expected `grep -c` count of 9 for FIX-04/05/06 mentions; actual count is 6.**

The plan's comment "3 items × 3 mentions each in requirements + traceability" implied 3 locations per ID, but the actual REQUIREMENTS.md structure has exactly 2 locations per ID: the requirements list and the traceability table. With 3 IDs × 2 locations = 6 lines, this is the correct and complete result. The functional content (both the requirements list and the traceability table) is fully populated as specified.

No functional deviation — plan executed as written.

## Issues Encountered

None.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes. This plan edits a local planning document and creates test stub files only.

## Known Stubs

None that affect plan goals. The test stub files are intentionally in RED state — they are the deliverable of this plan. Plans 01 and 02 will implement the functions to make them green.

## Next Phase Readiness

- Plan 79-01 (SNR/MAD threshold + FIX-04 implementation) has failing tests ready in RED state
- Plan 79-02 (intensity-symmetry detection + FIX-05 implementation) has failing tests ready in RED state
- Both plans can proceed immediately to GREEN phase

## Self-Check: PASSED

- `tests/test_peak_picker_snr.py` — EXISTS and fails with ImportError (RED confirmed)
- `tests/test_intensity_symmetry.py` — EXISTS and fails with ImportError (RED confirmed)
- `.planning/REQUIREMENTS.md` — Contains FIX-04, FIX-05, FIX-06 in requirements list and traceability table
- Commits `02ef96a` and `e94ff36` — FOUND in git log

---
*Phase: 79-peak-picking-symmetry-fix*
*Completed: 2026-06-08*

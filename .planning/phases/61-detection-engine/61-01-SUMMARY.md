---
phase: 61-detection-engine
plan: "01"
subsystem: detection
tags: [4j-coupling, hose-codes, statistical-detection, pydantic, sqlite]

# Dependency graph
requires:
  - phase: 60-statistics-generator
    provides: coupling_path_stats table with (carbon_hose, h_carbon_hose, bond_distance, count) rows
  - phase: 59-database-foundation
    provides: get_coupling_path_stats, get_coupling_path_stats_by_carbon, get_hose_stats_by_shift_window DB methods

provides:
  - CouplingPathDistribution Pydantic model (j2/j3/j4/j5_plus probabilities, dominant, p_long_range)
  - CouplingPathResult Pydantic model (risk_level, recommendation, summary, fallback flag)
  - RiskLevel enum (unlikely_4j, possible_4j, likely_4j, insufficient_data)
  - StatisticalDetector.detect_4j_coupling() method with three-tier classification
  - 33 passing unit and integration tests for 4J detection

affects: [62-agent-skill-updates, 64-uat]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD: red-green with per-task commits, test data uses well-separated shift regions to avoid HOSE window overlap"
    - "Fallback aggregation: exact pair -> carbon-only when exact pair has no stats"
    - "Configurable thresholds via keyword-only arguments with sensible defaults"

key-files:
  created:
    - src/lucy_ng/detection/models.py (CouplingPathDistribution, CouplingPathResult, RiskLevel added)
    - tests/test_detection_4j.py
  modified:
    - src/lucy_ng/detection/detector.py (detect_4j_coupling method added)
    - src/lucy_ng/detection/__init__.py (new exports added)

key-decisions:
  - "Test data for each tier uses well-separated shifts (5+ ppm apart) so the 2.0 ppm HOSE window never picks up the wrong scenario's HOSE codes"
  - "Fallback path: if no exact (carbon_hose, h_carbon_hose) pair found, aggregate over all h_carbon partners for the carbon HOSE code and set used_fallback=True"
  - "has_data=False only when no HOSE codes found at all; insufficient_data uses has_data=True (data exists, just not enough)"
  - "unique_hose_pairs counts distinct (carbon_hose, h_carbon_hose) pairs contributing to aggregation"

patterns-established:
  - "CouplingPathResult follows the existing HybridisationResult pattern: distribution + metadata + summary()"
  - "detect_4j_coupling uses radius=2 HOSE codes for coupling path lookup (same radius used by statistics generator)"

requirements-completed: [DET-01, DET-03, DET-04, DET-05]

# Metrics
duration: 12min
completed: 2026-03-11
---

# Phase 61 Plan 01: Detection Engine Core Summary

**CouplingPathDistribution/CouplingPathResult Pydantic models and detect_4j_coupling() with HOSE-based shift lookup, three-tier risk classification (likely/possible/unlikely_4j), and fallback aggregation**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-11T08:25:35Z
- **Completed:** 2026-03-11T08:37:48Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- RiskLevel enum with 4 values, CouplingPathDistribution with dominant and p_long_range computed properties, CouplingPathResult with full metadata and summary()
- detect_4j_coupling() method on StatisticalDetector: HOSE code lookup at radius=2, exact pair query with carbon-only fallback, configurable thresholds
- Three-tier classification: likely_4j (defer), possible_4j (HMBC X Y 2 4), unlikely_4j (normal); plus insufficient_data and no-data edge cases
- 33 tests covering all classification tiers, fallback path, configurable parameters, and no-data scenarios

## Task Commits

Each task was committed atomically:

1. **Task 1: Add CouplingPathDistribution and CouplingPathResult models** - `4cf85a8` (feat)
2. **Task 2: Implement StatisticalDetector.detect_4j_coupling** - `3c36254` (feat)

_TDD: both tasks followed red-green cycle (model imports failing, then method attribute missing, then green)_

## Files Created/Modified
- `src/lucy_ng/detection/models.py` - Added RiskLevel, CouplingPathDistribution, CouplingPathResult
- `src/lucy_ng/detection/detector.py` - Added detect_4j_coupling() method with full algorithm
- `src/lucy_ng/detection/__init__.py` - Exported new types
- `tests/test_detection_4j.py` - 33 tests: 25 model unit tests + 8 integration tests with in-memory DB

## Decisions Made
- Test data for each tier uses well-separated shifts (5+ ppm apart) so the 2.0 ppm HOSE window never picks up the wrong scenario's HOSE codes. Initial test data had 129.0 and 130.0 ppm within the window, causing overlap that conflated scenarios A and B.
- has_data=False only when no HOSE codes found at all; insufficient_data uses has_data=True (data exists, just not enough observations).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test data shift regions overlapped causing classification test failures**
- **Found during:** Task 2 (GREEN phase, first test run)
- **Issue:** Initial test data had carbon HOSE codes at 129.0 and 130.0 ppm; with window=2.0 ppm both were returned for either shift, mixing scenario counts and giving wrong p_long_range
- **Fix:** Separated test scenarios to 129.0 ppm and 135.0 ppm (6 ppm apart, > 2x window), and 45.0 vs 39.0 ppm for h_carbon (6 ppm apart); also adjusted J counts so each scenario clearly hits its tier
- **Files modified:** tests/test_detection_4j.py
- **Verification:** All 33 tests pass after fix
- **Committed in:** 3c36254 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (test data design bug)
**Impact on plan:** Necessary correction; no scope creep, no new implementation logic.

## Issues Encountered
None beyond the test data overlap (documented above).

## Next Phase Readiness
- detect_4j_coupling() is fully implemented and tested
- Exports from lucy_ng.detection are ready for CLI wiring (61-02)
- Types and method signature are stable for agent skill updates (phase 62)

## Self-Check: PASSED

All files verified present. Both task commits confirmed in git log.

---
*Phase: 61-detection-engine*
*Completed: 2026-03-11*

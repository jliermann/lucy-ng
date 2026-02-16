---
phase: 35-neighbourhood-detection
plan: 03
subsystem: detection
tags: [python, pydantic, statistical-detection, hose-database, neighbourhood-analysis]

# Dependency graph
requires:
  - phase: 35-01
    provides: SCHEMA_VERSION=5, HOSEStatsRecord with neighbour fields, parse_sphere_1()
provides:
  - ConstraintType enum (FORBIDDEN/TYPICAL/MANDATORY)
  - ElementConstraint model for bond partner classification
  - NeighbourDistribution with get_constraints(), forbidden_elements, mandatory_elements
  - NeighbourResult with summary() and model_dump_json()
  - StatisticalDetector.detect_neighbours() method for Python API
affects: [35-04-cli, 39-case-agent]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Pydantic models for statistical detection results
    - Constraint classification based on frequency thresholds
    - Backward compatibility warnings for v4 databases

key-files:
  created:
    - tests/test_detection_neighbours.py
  modified:
    - src/lucy_ng/detection/models.py
    - src/lucy_ng/detection/detector.py
    - src/lucy_ng/detection/__init__.py

key-decisions:
  - "mandatory_elements/forbidden_elements properties use hardcoded 0.95/0.01 thresholds for convenience"
  - "Constraints use custom thresholds passed to detect_neighbours() for flexibility"
  - "Warn on unpopulated neighbour columns (v4 databases) rather than fail"

patterns-established:
  - "Detection result models follow HybridisationResult pattern: summary(), model_dump_json(), has_data, warning"
  - "Element frequencies are NOT mutually exclusive (carbon can have multiple bond partners)"
  - "Classification: forbidden (<1%), typical (between), mandatory (>95%)"

# Metrics
duration: 4min
completed: 2026-02-11
---

# Phase 35 Plan 03: Neighbourhood Detection Summary

**Python API for bond partner element detection with forbidden/typical/mandatory classification based on HOSE database statistics**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-11T16:01:35Z
- **Completed:** 2026-02-11T16:05:36Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- ConstraintType enum and ElementConstraint model for element classification
- NeighbourDistribution with get_constraints(), forbidden_elements, mandatory_elements properties
- NeighbourResult with summary() and model_dump_json() methods
- StatisticalDetector.detect_neighbours() method queries HOSE database and classifies elements
- 11 comprehensive tests covering carbonyl (O mandatory), aliphatic (C mandatory), custom thresholds, warnings
- Backward compatible with v4 databases (warns about unpopulated columns)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add detection models and detector method** - `24dcf3e` (feat)
2. **Task 2: Write tests for neighbourhood detection** - `6e113db` (test)

## Files Created/Modified
- `src/lucy_ng/detection/models.py` - Added ConstraintType, ElementConstraint, NeighbourDistribution, NeighbourResult
- `src/lucy_ng/detection/detector.py` - Added detect_neighbours() method to StatisticalDetector
- `src/lucy_ng/detection/__init__.py` - Export NeighbourResult
- `tests/test_detection_neighbours.py` - 11 tests covering all detection scenarios

## Decisions Made
- **mandatory_elements/forbidden_elements properties:** Use hardcoded 0.95/0.01 thresholds for convenience properties. Custom thresholds go through get_constraints().
- **Constraint classification:** Forbidden (<1%), typical (between thresholds), mandatory (>95%) based on frequency.
- **v4 database handling:** Warn about unpopulated neighbour columns rather than fail. Allows detection to work with mixed v4/v5 databases.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

Ready for 35-04 CLI integration.

Python API complete and tested:
- detect_neighbours() returns frequency distributions
- Classification into forbidden/typical/mandatory
- Warning system for unpopulated databases
- JSON serialization for CLI consumption

Next step: Add `lucy detect neighbours` CLI command to expose this API.

---
*Phase: 35-neighbourhood-detection*
*Completed: 2026-02-11*

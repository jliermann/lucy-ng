---
phase: 35-neighbourhood-detection
plan: 02
subsystem: database
tags: [python, hose-codes, welford-algorithm, statistics, neighbour-tracking]

# Dependency graph
requires:
  - phase: 35-01
    provides: Schema v5 with neighbour columns, parse_sphere_1() function
provides:
  - WelfordAccumulator with update_with_neighbors() and 11-element tuple export
  - Both ResumableHOSEStatsGenerator and SDFHOSEStatsGenerator track neighbours
  - HOSEStatsGenerator.generate_all() returns neighbour_counts as third element
  - 13-element upsert tuples for v5 schema (hose_code, radius, 11-element data)
affects: [35-03, 35-04, database-regeneration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Neighbour tracking via update_with_neighbors() alongside hybridisation"
    - "11-element WelfordAccumulator tuple: count, mean, m2, sp3, sp2, sp1, has_C, has_O, has_N, has_S, has_hal"
    - "13-element upsert tuples prepend hose_code+radius to 11-element data"

key-files:
  created:
    - tests/test_stats_generator_neighbours.py
  modified:
    - src/lucy_ng/prediction/stats_generator.py
    - tests/test_stats_generator_hybridisation.py

key-decisions:
  - "update_with_neighbors() calls update_with_hybridisation() internally for composition"
  - "Halogen tracking: any of F/Cl/Br/I present increments has_halogen_neighbor by 1"
  - "Backward compatibility: update_with_hybridisation() and update() still work, neighbour counts remain 0"

patterns-established:
  - "Element presence tracked as count of observations with ≥1 element, enabling frequency calculation"
  - "merge() combines neighbour counts via simple addition (parallel Welford)"
  - "to_tuple() extended from 6 to 11 elements for v5 schema"

# Metrics
duration: 8min
completed: 2026-02-11
---

# Phase 35 Plan 02: Stats Generator Extension Summary

**WelfordAccumulator extended with neighbour element tracking, parsing sphere 1 HOSE codes to populate has_carbon/oxygen/nitrogen/sulfur/halogen_neighbor columns**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-11T09:14:05Z
- **Completed:** 2026-02-11T09:21:41Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extended WelfordAccumulator with 5 neighbour presence fields (has_carbon through has_halogen_neighbor)
- Added update_with_neighbors() method parsing sphere 1 and tracking element presence alongside hybridisation
- Updated merge() to combine neighbour counts (zero-count shortcuts include neighbour fields)
- Extended to_tuple() from 6 to 11 elements for v5 schema
- Both ResumableHOSEStatsGenerator and SDFHOSEStatsGenerator parse sphere 1 and call update_with_neighbors
- HOSEStatsGenerator.generate_all() returns 3-tuple (aggregates, hybridisations, neighbour_counts)
- compute_stats() accepts neighbour_counts and populates HOSEStatsRecord fields
- 8 comprehensive tests for neighbour tracking covering all scenarios

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend WelfordAccumulator with neighbour tracking** - `359e1a4` (feat)

_Note: Task 2 tests were bundled into commit a399300 (35-03 docs) in prior session due to incorrect commit staging. Tests exist and pass._

## Files Created/Modified

### Created
- `tests/test_stats_generator_neighbours.py` - 8 tests for update_with_neighbors(), halogen aggregation, merge, tuple format, backward compatibility, parser integration

### Modified
- `src/lucy_ng/prediction/stats_generator.py` - Added update_with_neighbors(), extended merge(), to_tuple(), and all three generator classes
- `tests/test_stats_generator_hybridisation.py` - Updated test_welford_accumulator_to_tuple_extended to expect 11 elements

## Decisions Made

1. **update_with_neighbors() composition:** Calls update_with_hybridisation() internally to avoid code duplication. Shift + hybridisation handled first, then neighbour tracking.

2. **Halogen aggregation logic:** Any of F, Cl, Br, I present in neighbours dict → increment has_halogen_neighbor. Single column for all halogens simplifies schema and matches 35-01 design.

3. **Backward compatibility preserved:** update_with_hybridisation() and update() still work. When used, neighbour counts remain 0. No breaking changes to existing code.

4. **HOSEStatsGenerator.generate_all() return type:** Extended from 2-tuple to 3-tuple (aggregates, hybridisations, neighbour_counts). compute_stats() accepts optional neighbour_counts parameter. Both changes are backward compatible (callers can ignore third return element, compute_stats neighbours defaults to None).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Line length linting error:** update_with_neighbors() signature exceeded 100 characters. Fixed by splitting across multiple lines.

## Next Phase Readiness

**Ready for Plan 35-03 (Detection Module):**
- WelfordAccumulator exports 11-element tuples
- ResumableHOSEStatsGenerator and SDFHOSEStatsGenerator populate neighbour columns during generation
- HOSEStatsGenerator supports neighbour tracking for batch generation
- All tests pass (16 total: 8 new neighbour tests + 8 existing hybridisation tests)

**Database regeneration required:** After this update, full HOSE database regeneration needed to populate neighbour columns. Existing v5 databases have all neighbour columns = 0 until regeneration.

**No blockers.** Detection module (35-03) can query neighbour columns and classify elements.

---
*Phase: 35-neighbourhood-detection*
*Completed: 2026-02-11*

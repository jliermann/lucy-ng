---
phase: 35-neighbourhood-detection
plan: 01
subsystem: database
tags: [sqlite, schema-migration, hose-codes, neighbourhood-detection, statistical-constraints]

# Dependency graph
requires:
  - phase: 34-hybridisation-detection
    provides: Schema v4 with hybridisation count columns and migration patterns
provides:
  - Schema v5 with 5 neighbour element count columns in hose_stats
  - migrate_v4_to_v5 function following established migration pattern
  - parse_sphere_1() function for HOSE code sphere 1 element extraction
  - HOSEStatsRecord with neighbour fields (has_carbon_neighbor through has_halogen_neighbor)
  - DatabaseManager with migrate_to_v5() and updated query/upsert methods
  - Backward compatibility for v3 and v4 databases
affects: [35-02, 35-03, 35-04, database-regeneration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Neighbour count columns store presence frequency (count of observations with ≥1 element)"
    - "parse_sphere_1() uses regex [A-Z][a-z]? to extract element symbols, ignoring bond prefixes"
    - "13-element tuple format for upsert: (hose_code, radius, count, mean, m2, sp3, sp2, sp1, has_C, has_O, has_N, has_S, has_hal)"

key-files:
  created:
    - src/lucy_ng/prediction/hose_parser.py
    - tests/test_hose_parser.py
  modified:
    - src/lucy_ng/database/schema.py
    - src/lucy_ng/database/models.py
    - src/lucy_ng/database/manager.py
    - tests/test_schema_migration.py

key-decisions:
  - "Neighbour count columns store count of observations with ≥1 element, not average bond partners"
  - "Halogen aggregation: single has_halogen_neighbor column for F/Cl/Br/I combined"
  - "HOSE parser handles bond order prefixes (=, *) by using regex that extracts only element symbols"
  - "Upsert accepts 5, 8, or 13-element tuples for backward compatibility"

patterns-established:
  - "Schema migration: ALTER TABLE ADD COLUMN with DEFAULT 0, update schema_meta, commit"
  - "Query methods: try v5 columns, catch OperationalError for v3/v4 fallback"
  - "Upsert merging: neighbour counts added (simple sum) just like hybridisation counts"

# Metrics
duration: 11min
completed: 2026-02-11
---

# Phase 35 Plan 01: Schema Extension Summary

**Schema v5 adds 5 neighbour element count columns to hose_stats, parse_sphere_1() extracts bonded elements from HOSE codes, backward-compatible migration and queries**

## Performance

- **Duration:** 11 min
- **Started:** 2026-02-11T08:59:53Z
- **Completed:** 2026-02-11T09:10:36Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Extended hose_stats table with 5 neighbour element count columns (has_carbon_neighbor, has_oxygen_neighbor, has_nitrogen_neighbor, has_sulfur_neighbor, has_halogen_neighbor)
- Implemented parse_sphere_1() function to extract element symbols from HOSE code sphere 1 using regex
- Added migrate_v4_to_v5() function following Phase 34's migration pattern
- Updated DatabaseManager with migrate_to_v5() method and backward-compatible query/upsert methods
- All query methods (get_hose_stats, get_hose_stats_all_radii, get_hose_stats_by_shift_window) include neighbour columns with v3/v4 fallback
- Upsert supports 5, 8, and 13-element tuples for v3, v4, and v5 compatibility
- 12 tests for HOSE parser, 2 tests for v4->v5 migration and neighbour queries

## Task Commits

Each task was committed atomically:

1. **Task 1: Schema v5, migration, models, and HOSE parser** - `0d77ea3` (feat)
2. **Task 2: Update DatabaseManager and write tests** - `a0f08d8` (feat)

## Files Created/Modified

### Created
- `src/lucy_ng/prediction/hose_parser.py` - Parse HOSE code sphere 1 to extract bonded element symbols
- `tests/test_hose_parser.py` - 12 tests for parse_sphere_1() covering all edge cases

### Modified
- `src/lucy_ng/database/schema.py` - SCHEMA_VERSION=5, CREATE_HOSE_STATS_TABLE with 5 neighbour columns, migrate_v4_to_v5()
- `src/lucy_ng/database/models.py` - HOSEStatsRecord with has_carbon_neighbor through has_halogen_neighbor fields
- `src/lucy_ng/database/manager.py` - migrate_to_v5(), updated get/insert/upsert methods with neighbour columns
- `tests/test_schema_migration.py` - Added test_migrate_v4_to_v5 and test_upsert_with_neighbours

## Decisions Made

1. **Neighbour count semantics:** Columns store count of observations where HOSE sphere 1 contained ≥1 of that element type. NOT average bond partner count. Enables frequency calculation: has_X / total_observations.

2. **Halogen aggregation:** Single has_halogen_neighbor column for F/Cl/Br/I combined. Enables "halogen forbidden" detection for hydrocarbons. Individual halogen tracking deferred to future enhancement.

3. **Tuple format:** Upsert accepts 5-tuple (v3), 8-tuple (v4), or 13-tuple (v5). Enables gradual migration without breaking existing stats generators.

4. **HOSE parser approach:** Regex `[A-Z][a-z]?` extracts only element symbols, automatically ignoring bond order prefixes (=, *, /). Simpler and more robust than character iteration.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Schema extension followed Phase 34's established pattern. All tests passed on first run.

## Next Phase Readiness

**Ready for Plan 35-02 (Stats Generator Extension):**
- Schema v5 columns exist with DEFAULT 0 values
- parse_sphere_1() tested and working for all HOSE syntax variants
- DatabaseManager upsert accepts 13-element tuples
- Backward compatibility maintained for v3/v4 databases

**Database regeneration required:** After stats generator is updated (Plan 35-02), full database regeneration needed to populate neighbour counts. Existing v4 databases will have all neighbour columns = 0.

**No blockers.** Detection module (Plan 35-03) can proceed after stats generator populates data.

---
*Phase: 35-neighbourhood-detection*
*Completed: 2026-02-11*

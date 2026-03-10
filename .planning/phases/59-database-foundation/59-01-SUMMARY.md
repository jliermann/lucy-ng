---
phase: 59-database-foundation
plan: "01"
subsystem: database
tags: [sqlite, pydantic, migration, schema, coupling-path-stats, 4j-detection]

requires:
  - phase: 58-skill-quality-overhaul
    provides: completed v6.0 milestone, schema v6 with bond_pair_stats

provides:
  - SCHEMA_VERSION=7 in schema.py
  - CREATE_COUPLING_PATH_STATS_TABLE DDL constant
  - CREATE_COUPLING_PATH_PAIR_INDEX and CREATE_COUPLING_PATH_CARBON_INDEX constants
  - migrate_v6_to_v7() function in schema.py
  - CouplingPathStatsRecord Pydantic model in models.py
  - DatabaseManager.migrate_to_v7() method in manager.py
  - 6 migration tests in tests/test_schema_migration_v7.py

affects:
  - 59-database-foundation (plans 02+)
  - 60-statistics-generator
  - 61-detection-engine

tech-stack:
  added: []
  patterns:
    - "Schema migration pattern: hardcode target version number in each migrate_vX_to_vY function (not str(SCHEMA_VERSION))"
    - "Migration chaining: each migrate_to_vN() checks current version and calls migrate_to_v(N-1) if needed"
    - "TDD: write failing tests first, then implement to pass — all 6 tests RED before any implementation"

key-files:
  created:
    - tests/test_schema_migration_v7.py
  modified:
    - src/lucy_ng/database/schema.py
    - src/lucy_ng/database/models.py
    - src/lucy_ng/database/manager.py

key-decisions:
  - "coupling_path_stats PRIMARY KEY uses (carbon_hose, h_carbon_hose, bond_distance) — composite key enables O(1) lookup for a specific pair at a specific distance"
  - "bond_distance stored as INTEGER (not REAL) — always an integer bond count (2, 3, 4, 5+)"
  - "Two indices created: idx_coupling_path_pair for pair lookups (most common query), idx_coupling_path_carbon for single-carbon queries (detection phase)"
  - "Hardcoded version strings in migrate_v5_to_v6 (changed from str(SCHEMA_VERSION) to '6') to prevent version drift bugs"

patterns-established:
  - "Migration function: CREATE table/indices, then UPDATE schema_meta, then commit — exact same structure for all vX_to_vY functions"

requirements-completed: [DB-01, DB-02]

duration: 4min
completed: "2026-03-10"
---

# Phase 59 Plan 01: Database Foundation Summary

**SQLite schema v7 with coupling_path_stats table (3-column composite PK), two indices, CouplingPathStatsRecord Pydantic model, and DatabaseManager.migrate_to_v7() chaining v3->v4->v5->v6->v7**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-10T17:10:07Z
- **Completed:** 2026-03-10T17:13:51Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Schema v7 DDL defined with `coupling_path_stats` table — the storage foundation for statistical 4J HMBC coupling detection
- `CouplingPathStatsRecord` Pydantic model added alongside `BondPairStatsRecord` following established pattern
- `DatabaseManager.migrate_to_v7()` chains through entire v3->v7 migration path, idempotent on repeat calls
- 6 tests cover: table/index creation, PRIMARY KEY structure, data preservation, model roundtrip, manager chaining, idempotency

## Task Commits

1. **Task 1: Schema v7 DDL, migration function, and Pydantic model** - `24ac97e` (test+feat)
2. **Task 2: DatabaseManager migrate_to_v7 method and import updates** - `745e350` (feat)

## Files Created/Modified

- `tests/test_schema_migration_v7.py` - 6 tests: migrate_v6_to_v7, data preservation, CouplingPathStatsRecord model, manager chaining, idempotency
- `src/lucy_ng/database/schema.py` - SCHEMA_VERSION bumped to 7; DDL constants for coupling_path_stats and 2 indices added; migrate_v6_to_v7() function added; migrate_v5_to_v6 fixed to hardcode "6" instead of str(SCHEMA_VERSION)
- `src/lucy_ng/database/models.py` - CouplingPathStatsRecord(BaseModel) added with carbon_hose, h_carbon_hose, bond_distance, count fields
- `src/lucy_ng/database/manager.py` - migrate_v6_to_v7 and CouplingPathStatsRecord imported; migrate_to_v7() method added

## Decisions Made

- Used hardcoded version strings in each migration function ("6" not `str(SCHEMA_VERSION)`) because SCHEMA_VERSION now reflects the latest schema and using it in older migration functions would write the wrong version number after a future bump.
- Two separate indices for coupling_path_stats: the pair index covers the common "does this pair occur at distance N?" query; the carbon index covers "what pairs does this carbon participate in?" queries during detection.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed migrate_v5_to_v6 to hardcode version "6"**
- **Found during:** Task 1 (schema implementation)
- **Issue:** `migrate_v5_to_v6` used `str(SCHEMA_VERSION)` which now evaluates to "7" since SCHEMA_VERSION was bumped. This would have caused v5->v6 migrations to write schema_version=7, skipping the v7 migration path incorrectly.
- **Fix:** Changed to hardcoded string `"6"` in the UPDATE statement
- **Files modified:** src/lucy_ng/database/schema.py
- **Verification:** All 64 tests pass; migration chain test confirms v5->v6->v7 steps through correctly
- **Committed in:** 24ac97e (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Essential correctness fix. Without it, the chained migration would have silently set wrong version numbers.

## Issues Encountered

None.

## Next Phase Readiness

- Database foundation complete — `coupling_path_stats` table ready to receive data
- Plan 59-02 can build the statistics generator that populates this table
- All existing tests (58 tests across migration + database suites) pass unchanged

---
*Phase: 59-database-foundation*
*Completed: 2026-03-10*

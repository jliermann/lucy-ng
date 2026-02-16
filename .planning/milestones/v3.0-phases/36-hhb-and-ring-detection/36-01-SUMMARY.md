---
phase: 36-hhb-and-ring-detection
plan: 01
subsystem: database
tags: [sqlite, schema-migration, rdkit, bond-pair-stats, ring-detection]

# Dependency graph
requires:
  - phase: 35-neighbourhood-detection
    provides: Schema v5 with neighbour columns, migration pattern
provides:
  - Schema v6 with bond_pair_stats table and ring columns
  - BondPairStatsRecord model and DatabaseManager methods
  - Migration from v5 to v6 with backward compatibility
affects: [36-02-stats-generators, 36-03-hhb-detection]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Formula-level statistics table (bond_pair_stats) for compound-level queries"
    - "Ring membership as count columns in hose_stats for frequency distributions"
    - "16-element tuple format for v6 upsert_hose_stats_incremental"

key-files:
  created:
    - tests/test_schema_migration_v6.py
  modified:
    - src/lucy_ng/database/schema.py
    - src/lucy_ng/database/models.py
    - src/lucy_ng/database/manager.py

key-decisions:
  - "Bond pair statistics at formula level (not HOSE level) - correct granularity for HHB queries"
  - "Ring columns store counts (not booleans) for frequency distributions"
  - "Composite PRIMARY KEY (formula_normalized, element1, element2) for bond_pair_stats"
  - "Backward compatibility: get_bond_pair_stats_by_formula returns [] for v5 databases"

patterns-established:
  - "ALTER TABLE migration pattern for adding ring columns with DEFAULT 0"
  - "Separate table for formula-level statistics (bond_pair_stats)"
  - "16-element tuples in upsert for v6: (hose_code, radius, count, mean, m2, sp3, sp2, sp1, has_c, has_o, has_n, has_s, has_hal, in_3ring, in_4ring, in_aromatic)"

# Metrics
duration: 7min
completed: 2026-02-11
---

# Phase 36 Plan 01: Schema Extension Summary

**Database schema v6 with bond_pair_stats table for HHB detection and 3 ring columns in hose_stats for badlist foundation**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-11T10:49:22Z
- **Completed:** 2026-02-11T10:56:50Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Schema v6 defined with bond_pair_stats table and ring columns
- BondPairStatsRecord model and DatabaseManager methods for insertion and querying
- Migration from v5 to v6 with backward compatibility for existing databases
- Comprehensive test suite covering migration, insertion, and backward compatibility

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend schema to v6** - `0f980f9` (feat)
2. **Task 2: Update DatabaseManager with migration and methods** - `44733ac` (feat)

## Files Created/Modified
- `src/lucy_ng/database/schema.py` - SCHEMA_VERSION=6, bond_pair_stats table, ring columns, migrate_v5_to_v6()
- `src/lucy_ng/database/models.py` - BondPairStatsRecord model, ring fields in HOSEStatsRecord
- `src/lucy_ng/database/manager.py` - migrate_to_v6(), insert_bond_pair_stats_batch(), get_bond_pair_stats_by_formula(), updated all hose_stats methods
- `tests/test_schema_migration_v6.py` - Test suite for v5→v6 migration and bond pair operations

## Decisions Made

**Bond pair statistics granularity:** Created separate `bond_pair_stats` table indexed by formula_normalized (not HOSE code level). Rationale: HHB queries operate at molecular formula level ("Do C10H14O2 compounds have O-N bonds?"), not shift level. Correct granularity prevents nonsensical queries like "Do carbons at 130 ppm have O-N bonds?"

**Ring membership as counts:** Stored ring membership as INTEGER counts (in_3ring, in_4ring, in_aromatic) rather than booleans. Rationale: Enables frequency distributions ("carbons at 130 ppm are 95% aromatic") for Phase 38 badlist filtering.

**Composite primary key:** Used (formula_normalized, element1, element2) composite PRIMARY KEY for bond_pair_stats. Rationale: Natural uniqueness constraint, efficient lookup by formula via idx_bond_pair_formula index.

**Backward compatibility:** get_bond_pair_stats_by_formula() returns empty list for v5 databases (table doesn't exist). Rationale: Graceful degradation, allows queries without requiring immediate migration.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - schema extension followed established migration patterns from Phases 34 and 35.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Schema foundation complete for Phase 36-02 (stats generators). Database structure ready for:
- BondPairStatsGenerator to populate bond_pair_stats table from compound SMILES
- HOSEStatsGenerator to extract ring membership during HOSE generation
- Phase 36-03 HHB detection CLI to query bond_pair_stats by formula

No blockers. Ring columns exist with DEFAULT 0 (will be populated in 36-02). Bond pair stats table created (will be populated in 36-02).

---
*Phase: 36-hhb-and-ring-detection*
*Completed: 2026-02-11*

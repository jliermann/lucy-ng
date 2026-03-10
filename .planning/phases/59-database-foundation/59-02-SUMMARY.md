---
phase: 59-database-foundation
plan: "02"
subsystem: database
tags: [sqlite, coupling-path-stats, hose-codes, 4j-detection, cli, backward-compat]

requires:
  - phase: 59-01
    provides: coupling_path_stats table schema (v7 migration), CouplingPathStatsRecord model

provides:
  - DatabaseManager.insert_coupling_path_stats_batch() — executemany INSERT OR REPLACE
  - DatabaseManager.get_coupling_path_stats() — exact HOSE pair lookup ordered by bond_distance ASC
  - DatabaseManager.get_coupling_path_stats_by_carbon() — carbon-only fallback aggregation
  - DatabaseManager.get_coupling_path_stats_count() — COUNT(*) for CLI reporting
  - 'lucy database info' reports coupling_path_stats status (empty hint vs entry count)

affects:
  - phase 61 (Detection Engine) — will call get_coupling_path_stats / get_coupling_path_stats_by_carbon
  - phase 60 (Statistics Generator) — will call insert_coupling_path_stats_batch

tech-stack:
  added: []
  patterns:
    - "try/except sqlite3.OperationalError returning [] — backward compat pattern for pre-v7 databases"
    - "executemany INSERT OR REPLACE — idempotent batch insert pattern"
    - "CliRunner used for CLI integration tests (no subprocess needed)"

key-files:
  created: []
  modified:
    - src/lucy_ng/database/manager.py
    - src/lucy_ng/cli/database.py
    - tests/test_schema_migration_v7.py

key-decisions:
  - "Used executemany over a loop for insert_coupling_path_stats_batch — simpler and faster"
  - "get_coupling_path_stats_count returns 0 on OperationalError so pre-v7 DBs show 'empty' in info"

patterns-established:
  - "Coupling path stats query pattern: exact pair first, carbon fallback second (established for Phase 61 use)"

requirements-completed: [DB-03, VAL-02]

duration: 16min
completed: 2026-03-10
---

# Phase 59 Plan 02: Database Query API and CLI Info Summary

**Four DatabaseManager query methods for coupling_path_stats lookups with backward compat, updated CLI info showing table status, 14 tests added, zero regression across 93 tests**

## Performance

- **Duration:** 16 min
- **Started:** 2026-03-10T17:16:56Z
- **Completed:** 2026-03-10T17:33:16Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added four DatabaseManager methods: `insert_coupling_path_stats_batch`, `get_coupling_path_stats`, `get_coupling_path_stats_by_carbon`, `get_coupling_path_stats_count` — all with pre-v7 backward compat
- Updated `lucy database info` CLI to report coupling_path_stats status (populated count or descriptive empty hint)
- 14 new tests covering insert, exact pair lookup, carbon aggregation, backward compat (v6 DB), idempotency, and both CLI info cases
- 93 targeted tests pass with zero regression (detection commands, CLI database commands, all v7 migration tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: DatabaseManager query methods for coupling_path_stats** - `f605a92` (feat, TDD)
2. **Task 2: CLI info update and full regression verification** - `7b46128` (feat)

**Plan metadata:** (to be added in final commit)

_Note: TDD tasks may have multiple commits (test -> feat -> refactor). Task 1 used TDD: RED tests added first, then GREEN implementation._

## Files Created/Modified

- `src/lucy_ng/database/manager.py` — Added Coupling Path Statistics section with 4 new methods (lines 1277-1394)
- `src/lucy_ng/cli/database.py` — Updated `info` command to show coupling_path_stats status after sources breakdown
- `tests/test_schema_migration_v7.py` — Added 8 query/insert tests (Task 1) and 2 CLI info tests (Task 2)

## Decisions Made

- Used `executemany` over a record-by-record loop for `insert_coupling_path_stats_batch` — simpler implementation, better performance for batch inserts
- `get_coupling_path_stats_count` returns 0 on `OperationalError` so pre-v7 databases correctly show the "empty" path in the CLI info command without special-casing

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None — all methods passed tests on first implementation attempt. Mypy errors visible in manager.py at lines 864/884 are pre-existing (complex union type annotation in `upsert_hose_stats_incremental`) and not caused by this plan's changes.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 60 (Statistics Generator) can now call `insert_coupling_path_stats_batch` to populate the table
- Phase 61 (Detection Engine) can call `get_coupling_path_stats` for exact pair lookup and `get_coupling_path_stats_by_carbon` for the fallback
- `lucy database info` will show population progress as Phase 60 generates data

## Self-Check: PASSED

- `59-02-SUMMARY.md` — FOUND
- `src/lucy_ng/database/manager.py` — FOUND
- `src/lucy_ng/cli/database.py` — FOUND
- Commit `f605a92` (Task 1) — FOUND
- Commit `7b46128` (Task 2) — FOUND

---
*Phase: 59-database-foundation*
*Completed: 2026-03-10*

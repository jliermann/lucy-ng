---
phase: 49-fragment-schema-infrastructure
plan: 01
subsystem: database
tags: [sqlite, pydantic, fragments, ssc, schema-v7]

# Dependency graph
requires: []
provides:
  - SSCRecord Pydantic model with JSON field_validator for shift_list
  - SSCMatch Pydantic model for fragment search results
  - FragmentDatabaseManager with schema v7 DDL (ssc + ssc_bitset tables)
  - insert_ssc_batch, get_ssc_count, iter_ssc_bitsets, get_ssc_by_id query methods
  - schema_meta table with schema_version=7 and bin_size=2.0
  - 20 unit tests verifying all methods and isolation from existing database
affects:
  - 50-ssc-extraction
  - 51-fragment-search
  - 52-lsd-integration
  - 53-scoring
  - 54-uat

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Separate module (fragments/) for separate DB file lifecycle
    - INSERT OR IGNORE for SMILES-based SSC deduplication
    - INSERT OR IGNORE (not REPLACE) for bin_size — protects existing populated DBs
    - field_validator(mode="before") to accept JSON string or list for shift_list
    - Bitset stored in separate ssc_bitset table to keep ssc rows slim

key-files:
  created:
    - src/lucy_ng/fragments/__init__.py
    - src/lucy_ng/fragments/models.py
    - src/lucy_ng/fragments/schema.py
    - src/lucy_ng/fragments/db.py
    - tests/test_fragment_db.py
  modified: []

key-decisions:
  - "fragments/ module is fully independent from database/ module — zero cross-imports — separate DB file lifecycle"
  - "FRAGMENT_SCHEMA_VERSION=7 in fragments/schema.py; existing database/schema.py SCHEMA_VERSION=6 untouched"
  - "bin_size uses INSERT OR IGNORE in create_tables() to protect existing SSC data built with different bin size"
  - "SSCMatch defined in Phase 49 (not 51) to allow Phases 51 and 52 to run in parallel"
  - "ssc_bitset is a separate table so ssc rows stay slim for queries that don't need bitset data"

patterns-established:
  - "Pattern: SQLite schema in separate fragments/schema.py with FRAGMENT_SCHEMA_STATEMENTS list"
  - "Pattern: FragmentDatabaseManager follows DatabaseManager context-manager pattern exactly"
  - "Pattern: insert_ssc_batch returns (inserted, skipped) tuple using cursor.rowcount after INSERT OR IGNORE"
  - "Pattern: iter_ssc_bitsets uses fetchmany() batching for memory efficiency during Phase 51 screening"

requirements-completed: [FRAG-01]

# Metrics
duration: 3min
completed: 2026-02-19
---

# Phase 49 Plan 01: Fragment Schema and Infrastructure Summary

**SQLite schema v7 with ssc and ssc_bitset tables in a new fragments/ module — FragmentDatabaseManager with batch insert, deduplication, bitset iteration, and ID lookup, backed by 20 unit tests and fully isolated from the existing compound database**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-19T14:00:28Z
- **Completed:** 2026-02-19T14:03:30Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Created `src/lucy_ng/fragments/` module with 4 files: models, schema, db, and __init__
- FragmentDatabaseManager passes all functional tests: creates tables, inserts with deduplication (1,0)/(0,1), iterates bitsets, queries by ID
- 20 unit tests pass covering model parsing, DB lifecycle, insert/dedup, bitset, edge cases, and schema isolation
- mypy --strict and ruff both clean
- Existing database/schema.py SCHEMA_VERSION=6 confirmed untouched

## Task Commits

Each task was committed atomically:

1. **Tasks 1+2: Create fragments module with models, schema DDL, and FragmentDatabaseManager** - `887944d` (feat)
2. **Task 3: Add 20 unit tests for fragment database infrastructure** - `5b26ad5` (test)

## Files Created/Modified

- `src/lucy_ng/fragments/__init__.py` — public exports: FragmentDatabaseManager, SSCRecord, SSCMatch
- `src/lucy_ng/fragments/models.py` — SSCRecord (field_validator for JSON shift_list, shift_list_as_json method) and SSCMatch Pydantic v2 models
- `src/lucy_ng/fragments/schema.py` — FRAGMENT_SCHEMA_VERSION=7, CREATE_SSC_TABLE, CREATE_SSC_BITSET_TABLE, CREATE_SSC_ATOM_COUNT_INDEX, CREATE_SCHEMA_META_TABLE, FRAGMENT_SCHEMA_STATEMENTS list
- `src/lucy_ng/fragments/db.py` — FragmentDatabaseManager: create_tables, get_schema_version, get_bin_size, get_ssc_count, insert_ssc_batch, iter_ssc_bitsets, get_ssc_by_id
- `tests/test_fragment_db.py` — 20 pytest tests across 6 test classes

## Decisions Made

- Tasks 1 and 2 were committed together because `__init__.py` imports from `db.py`, making them an atomic unit
- 20 tests written (6 more than the 14 required) — the extra tests (`test_ssc_record_model_dump_json`, `test_ssc_record_bitset_optional`, `test_ssc_match_rank_defaults_to_zero`, `test_schema_version_correct`, `test_iter_ssc_bitsets_yields_tuples`, `test_get_ssc_by_id_shift_list_parsed`) cover important edge cases at zero extra cost

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 50 (SSC Extraction) can proceed immediately: FragmentDatabaseManager.insert_ssc_batch is ready and uses INSERT OR IGNORE for deduplication
- Phases 51 and 52 can plan in parallel: both depend only on SSCMatch model (defined here) and FragmentDatabaseManager query methods, not on Phase 50's extracted data
- FRAG-01 requirement satisfied: lucy-ng-fragments.db can be created with schema v7, schema_version=7, bin_size=2.0

## Self-Check: PASSED

All 5 files found on disk. Both commits (887944d, 5b26ad5) confirmed in git log.

---
*Phase: 49-fragment-schema-infrastructure*
*Completed: 2026-02-19*

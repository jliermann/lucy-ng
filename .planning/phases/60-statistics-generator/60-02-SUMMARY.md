---
phase: 60-statistics-generator
plan: "02"
subsystem: database
tags: [cli, click, coupling-path-stats, 4j-detection, statistics]

# Dependency graph
requires:
  - phase: 60-01
    provides: CouplingPathStatsGenerator class with run()/generate_all() API
  - phase: 59
    provides: coupling_path_stats schema (v7), DatabaseManager with iter_compounds_with_shifts_from

provides:
  - lucy database generate-coupling-stats CLI command (--db, --resume/--fresh, --limit, --chunk-size)
  - CouplingPathStatsGenerator exported from lucy_ng.prediction
  - CLI integration tests verifying end-to-end command behavior
affects: [61-detection-engine, 63-full-generation-run, 64-uat]

# Tech tracking
tech-stack:
  added: []
  patterns: [click CLI command following generate-hose-stats pattern, CliRunner for CLI integration tests]

key-files:
  created: []
  modified:
    - src/lucy_ng/cli/database.py
    - src/lucy_ng/prediction/__init__.py
    - tests/test_coupling_path_generator.py

key-decisions:
  - "CLI command follows exact generate-hose-stats output style — progress bar + elapsed time + counts + reminder to run lucy database info"
  - "CouplingPathStatsGenerator imported at function scope (not module level) matching generate-hose-stats lazy import pattern"

patterns-established:
  - "CLI integration tests use Click CliRunner with real tempfile databases — no mocking"
  - "CLI commands in database.py use lazy imports inside the function body for optional heavy dependencies"

requirements-completed: [GEN-03]

# Metrics
duration: 12min
completed: 2026-03-10
---

# Phase 60 Plan 02: CLI Wiring for Coupling Path Stats Generator Summary

**`lucy database generate-coupling-stats` CLI command wired to CouplingPathStatsGenerator with --resume/--fresh/--limit/--chunk-size flags, 5 CLI integration tests added, all 23 tests pass**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-10T20:10:00Z
- **Completed:** 2026-03-10T20:22:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added `lucy database generate-coupling-stats` CLI command following the existing `generate-hose-stats` pattern
- Exported `CouplingPathStatsGenerator` from `lucy_ng.prediction` package
- Added 5 CLI integration tests using Click's CliRunner with real tempfile databases
- `lucy database info` correctly shows populated coupling_path_stats count after generation

## Task Commits

Each task was committed atomically:

1. **Task 1: CLI command and prediction module export** - `fd05d97` (feat)
2. **Task 2: CLI integration test and full regression** - `0d5f320` (test)

## Files Created/Modified
- `src/lucy_ng/cli/database.py` - Added `generate-coupling-stats` command (generate_coupling_stats function, ~70 lines)
- `src/lucy_ng/prediction/__init__.py` - Added CouplingPathStatsGenerator to imports and __all__
- `tests/test_coupling_path_generator.py` - Added 5 CLI integration tests (test_cli_* functions)

## Decisions Made
- CLI command follows exact output style of `generate-hose-stats`: config echo, progress bar via tqdm (passed through to generator), elapsed time in minutes, counts, reminder line
- CouplingPathStatsGenerator imported lazily inside the function body (not at module level), consistent with how `generate-hose-stats` imports HOSEStatsGenerator et al.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `lucy database generate-coupling-stats` is ready for production use on the full 928K compound database
- Phase 61 (Detection Engine) can now use coupling_path_stats for 4J HMBC detection queries
- Phase 63 (Full Generation Run) will use this command to populate the production database

---
*Phase: 60-statistics-generator*
*Completed: 2026-03-10*

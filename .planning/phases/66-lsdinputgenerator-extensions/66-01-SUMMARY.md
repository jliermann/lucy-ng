---
phase: 66-lsdinputgenerator-extensions
plan: 01
subsystem: lsd
tags: [lsd, models, hmbc, pylsd, bond-range]

# Dependency graph
requires:
  - phase: 65-hypothesis-gate
    provides: "GO decision confirming HMBC X Y 2 4 syntax needed for 4J correlations"
provides:
  - "LSDCorrelation.to_lsd_line() emits extended 'HMBC X Y 2 4' when bond range deviates from default 2-3"
  - "LSDProblem.pylsd_mode (bool, default False) field for pyLSD-mode gating"
  - "LSDProblem.elim_commands (list[tuple[int, int]], default []) field for ELIM command storage"
affects:
  - 66-02  # generator.py consumes pylsd_mode and elim_commands
  - 67-pylsadorchestrator  # orchestrator uses these fields to control multi-run flow

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Conditional LSD syntax emission: default range omits trailing bonds, non-default appends min max"
    - "TDD: RED test first, then GREEN implementation, then full suite verification"

key-files:
  created: []
  modified:
    - src/lucy_ng/lsd/models.py
    - tests/test_lsd_models.py

key-decisions:
  - "OR condition for HMBC branch: emit extended syntax if min_bonds != 2 OR max_bonds != 3 (not AND — AND never triggers since defaults are 2 and 3 respectively)"
  - "elim_commands stores (N, M) tuples, not strings — generator.py formats ELIM N M output"

patterns-established:
  - "Extended HMBC syntax: 'HMBC X Y' for 2-3J, 'HMBC X Y min max' for any other range"
  - "LSDProblem carries pyLSD state flags alongside structural data"

requirements-completed: [INPUT-04]

# Metrics
duration: 10min
completed: 2026-03-16
---

# Phase 66 Plan 01: LSDInputGenerator Extensions — Models Summary

**LSDCorrelation extended to emit 'HMBC X Y 2 4' for 4J correlations; LSDProblem gains pylsd_mode and elim_commands fields for pyLSD orchestration**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-16T16:22:00Z
- **Completed:** 2026-03-16T16:32:20Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Extended `LSDCorrelation.to_lsd_line()`: non-default HMBC bond ranges now emit `HMBC X Y min max` while default 2-3 range continues emitting `HMBC X Y` (backward compatible)
- Added `pylsd_mode: bool = False` to `LSDProblem` — gates FORM/ELIM emission in Plan 02's generator
- Added `elim_commands: list[tuple[int, int]] = field(default_factory=list)` to `LSDProblem` — stores (N, M) pairs for generator to emit `ELIM N M` lines in pyLSD mode
- 7 new tests covering extended HMBC syntax and both new LSDProblem fields; all 47 model tests and 133 LSD-suite tests pass

## Task Commits

1. **Task 1: Extend LSDCorrelation HMBC bond range and add LSDProblem pyLSD fields** - `f9145f8` (feat)

**Plan metadata:** (docs commit — see final entry)

_Note: TDD task — RED tests written first (confirmed failing), GREEN implementation brought all tests passing._

## Files Created/Modified

- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/lsd/models.py` — Extended HMBC branch in `to_lsd_line()`; added `pylsd_mode` and `elim_commands` fields to `LSDProblem`
- `/Users/steinbeck/Dropbox/develop/lucy-ng/tests/test_lsd_models.py` — 7 new tests: `test_to_lsd_line_hmbc_extended`, `test_to_lsd_line_hmbc_extended_non_standard_min`, `test_to_lsd_line_hsqc_unaffected_by_bond_range`, `test_to_lsd_line_cosy_unaffected_by_bond_range`, `test_pylsd_mode_default_false`, `test_pylsd_mode_can_be_set_true`, `test_elim_commands_default_empty`, `test_elim_commands_can_be_populated`, `test_elim_commands_independent_across_instances`

## Decisions Made

- **OR condition for HMBC extended syntax**: `if self.min_bonds != 2 or self.max_bonds != 3` — using AND would never trigger since both conditions must deviate from defaults simultaneously to matter, but the plan correctly specifies OR to catch any single-field deviation
- **elim_commands as list of tuples**: raw (N, M) pairs kept in model; generator.py (Plan 02) is responsible for formatting `ELIM N M` lines — clean separation of model vs. rendering

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Plan 02 (generator.py changes) can now consume `LSDProblem.pylsd_mode` and `LSDProblem.elim_commands` to emit `FORM`/`ELIM` blocks in pyLSD mode
- `LSDCorrelation(atom1, atom2, "HMBC", min_bonds=2, max_bonds=4)` emits `HMBC atom1 atom2 2 4` — ready for orchestrator to use when marking 4J suspect correlations

## Self-Check: PASSED

- models.py: FOUND
- test_lsd_models.py: FOUND
- 66-01-SUMMARY.md: FOUND
- commit f9145f8: FOUND

---
*Phase: 66-lsdinputgenerator-extensions*
*Completed: 2026-03-16*

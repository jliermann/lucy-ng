---
phase: 66-lsdinputgenerator-extensions
plan: 02
subsystem: lsd
tags: [lsd, generator, pylsd, form, elim, shih, validation]

# Dependency graph
requires:
  - phase: 66-lsdinputgenerator-extensions
    plan: 01
    provides: "LSDProblem.pylsd_mode, LSDProblem.elim_commands, LSDCorrelation extended HMBC syntax"
provides:
  - "LSDInputGenerator.emit_form(formula) -> 'FORM {formula}'"
  - "LSDInputGenerator.emit_elim(n, m) -> 'ELIM {n} {m}'"
  - "LSDInputGenerator.emit_shih(idx, shift) -> 'SHIH {idx} {shift:.2f}'"
  - "generate() emits FORM+ELIM header block when pylsd_mode=True"
  - "generate() emits SHIH lines for atoms with proton_shift set"
  - "validate_pylsd_input() catches FORM/MULT carbon count mismatch"
affects:
  - 67-pylsadorchestrator  # orchestrator uses these methods to build pyLSD input files

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pyLSD header block: FORM then ELIM lines, before MULT atom definitions, only when pylsd_mode=True"
    - "SHIH emitted alongside SHIX in Chemical shifts section for atoms with proton_shift set"
    - "validate_pylsd_input: carbon-only consistency check (heteroatoms deliberately excluded)"
    - "TDD: RED test commit, then GREEN implementation commit"

key-files:
  created: []
  modified:
    - src/lucy_ng/lsd/generator.py
    - tests/test_lsd_generator.py

key-decisions:
  - "SHIH emitted after all SHIX lines in same 'Chemical shifts' section — single blank-line separator maintained"
  - "validate_pylsd_input checks only carbon count: heteroatom count is deliberately ambiguous (hydroxyl/ether flexibility)"
  - "pylsd_mode=False leaves generate() output 100% unchanged — no FORM even if molecular_formula is set"

requirements-completed: [INPUT-01, INPUT-02, INPUT-03, INPUT-04]

# Metrics
duration: 11min
completed: 2026-03-16
---

# Phase 66 Plan 02: LSDInputGenerator Extensions — Generator Summary

**emit_form/emit_elim/emit_shih static methods added to LSDInputGenerator; generate() emits pyLSD header (FORM+ELIM) and SHIH shifts when pylsd_mode=True; validate_pylsd_input() catches FORM/MULT carbon mismatch**

## Performance

- **Duration:** ~11 min
- **Started:** 2026-03-16T16:35:00Z
- **Completed:** 2026-03-16T16:46:22Z
- **Tasks:** 2 (both TDD: RED + GREEN)
- **Files modified:** 2

## Accomplishments

- Added `emit_form(formula)`, `emit_elim(n, m)`, `emit_shih(atom_idx, shift)` as static methods to `LSDInputGenerator`
- Updated `generate()`: when `pylsd_mode=True`, emits FORM line (if molecular_formula set) and ELIM lines (if elim_commands non-empty), placed between header comments and MULT atom definitions
- Updated `generate()`: emits SHIH lines for any atom with `proton_shift` set, in the Chemical shifts section alongside SHIX
- Added module-level `validate_pylsd_input(problem)`: parses molecular formula, counts C atoms in MULT, raises `ValueError` with "FORM/MULT mismatch" message if counts diverge; silently passes for None formula or matching counts; deliberately ignores heteroatom counts
- `emit_elim` docstring explicitly warns: "ELIM drops the correlation entirely. For 4J handling, use HMBC X Y 2 4."
- 17 new tests added across `TestPyLSDExtensions` (13 tests) and `TestPyLSDValidator` (4 tests)
- All 71 pre-existing tests pass unchanged — `pylsd_mode=False` is the default so no existing behaviour changes

## Task Commits

1. **Task 1+2 RED: Failing tests for all pyLSD extension methods** - `e6e3c03` (test)
2. **Task 1+2 GREEN: Implementation of emit_form/emit_elim/emit_shih, generate() integration, validate_pylsd_input()** - `6fd08e2` (feat)

## Files Created/Modified

- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/lsd/generator.py` — Three new static methods; generate() updated with pyLSD header block and SHIH emission; validate_pylsd_input() added as module-level function
- `/Users/steinbeck/Dropbox/develop/lucy-ng/tests/test_lsd_generator.py` — TestPyLSDExtensions (13 tests) and TestPyLSDValidator (4 tests) added

## Decisions Made

- **SHIH placed after SHIX**: both emit into the same "Chemical shifts" section, SHIX first then SHIH, with a single trailing blank line — consistent with existing section structure
- **pylsd_mode=False default preserved**: generate() output for existing callers is byte-for-byte identical — no regressions possible
- **validate_pylsd_input carbon-only check**: heteroatom count deliberately excluded because oxygen can appear as carbonyl (sp2, no H) or hydroxyl (sp3, 1H) — ambiguity is by design in the LSD workflow

## Deviations from Plan

None — plan executed exactly as written. The plan noted HMBC extended bond range is already handled by Plan 01's `to_lsd_line()`, confirmed correct.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 67 (PyLSDOrchestrator) can now call `LSDInputGenerator.emit_form()`, `emit_elim()`, and `emit_shih()` to construct pyLSD input files
- `validate_pylsd_input(problem)` available for the orchestrator to call before writing files, catching the most dangerous configuration mistake
- All four INPUT requirements (INPUT-01 through INPUT-04) complete

## Self-Check: PASSED

- src/lucy_ng/lsd/generator.py: FOUND
- tests/test_lsd_generator.py: FOUND
- 66-02-SUMMARY.md: FOUND
- commit e6e3c03 (test RED): FOUND
- commit 6fd08e2 (feat GREEN): FOUND

---
*Phase: 66-lsdinputgenerator-extensions*
*Completed: 2026-03-16*

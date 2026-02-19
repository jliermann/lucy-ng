---
phase: 52-deff-formatter-lsd-generation
plan: 01
subsystem: fragments
tags: [lsd, sstr, link, deff, fexp, rdkit, sha256, fragment-library]

# Dependency graph
requires:
  - phase: 49-ssc-data-model-fragment-db
    provides: SSCMatch model with smiles field
provides:
  - DEFFFormatter class converting SMILES to LSD SSTR/LINK fragment files
  - Hash-based deterministic fragment filenames
  - DEFF/FEXP command generators with correct double-quote syntax
affects: [52-02-cli-to-lsd, case-agent-fragment-injection]

# Tech tracking
tech-stack:
  added: []
  patterns: [rdkit-to-lsd-property-mapping, hash-based-filenames]

key-files:
  created:
    - src/lucy_ng/fragments/lsd_formatter.py
    - tests/test_lsd_formatter.py
  modified:
    - src/lucy_ng/fragments/__init__.py

key-decisions:
  - "HybridizationType from rdkit.Chem.rdchem (not rdkit.Chem.Hybridization which does not exist)"
  - "type: ignore[no-untyped-call] for RDKit GetAtoms/GetBonds (untyped C++ stubs in strict mypy)"

patterns-established:
  - "SSTR/LINK generation: 1-based atom indices, aromatic=sp2, exact hybridization from RDKit"
  - "Fragment filenames: SHA-256 of canonical SMILES, 12-char hex prefix"
  - "LSD double quotes: DEFF F<n> uses double quotes (single quotes cause LSD error 160)"

requirements-completed: [LINT-01, LINT-03]

# Metrics
duration: 11min
completed: 2026-02-19
---

# Phase 52 Plan 01: DEFFFormatter Summary

**DEFFFormatter class converting SMILES to LSD SSTR/LINK fragment files with hash-based filenames and double-quote DEFF/FEXP commands**

## Performance

- **Duration:** 11 min
- **Started:** 2026-02-19T17:52:52Z
- **Completed:** 2026-02-19T18:04:04Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- DEFFFormatter.smiles_to_fragment_content converts any valid SMILES to correct LSD SSTR/LINK syntax with 1-based atom indices, element symbols, hybridization (1/2/3), and hydrogen counts
- Hash-based deterministic filenames ensure canonical SMILES equivalents always map to the same fragment file (SHA-256, 12-char hex prefix)
- DEFF/FEXP command generators enforce double-quote syntax required by LSD 3.4.9 and support OR, AND, NOT logic
- 24 unit tests with full coverage across all 5 static methods

## Task Commits

Each task was committed atomically:

1. **Task 1: RED -- Write failing tests for DEFFFormatter** - `6fad17b` (test)
2. **Task 2: GREEN + REFACTOR -- Implement DEFFFormatter** - `2fa018c` (feat)

## Files Created/Modified
- `src/lucy_ng/fragments/lsd_formatter.py` - DEFFFormatter class with smiles_to_fragment_content, fragment_filename, write_fragment_file, deff_command, fexp_command
- `tests/test_lsd_formatter.py` - 24 unit tests across 5 test classes
- `src/lucy_ng/fragments/__init__.py` - Added DEFFFormatter to exports and __all__

## Decisions Made
- Used `HybridizationType` from `rdkit.Chem.rdchem` instead of `Hybridization` from `rdkit.Chem` (the latter does not exist as a top-level import)
- Added `type: ignore[no-untyped-call]` for `mol.GetAtoms()` and `mol.GetBonds()` -- RDKit C++ bindings have no Python type stubs, unavoidable in strict mypy mode

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed RDKit Hybridization import path**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** Plan specified `from rdkit.Chem import Hybridization` but this import does not exist in RDKit 2025.9.4
- **Fix:** Changed to `from rdkit.Chem.rdchem import HybridizationType` and updated all references
- **Files modified:** src/lucy_ng/fragments/lsd_formatter.py
- **Verification:** Import succeeds, all 24 tests pass
- **Committed in:** 2fa018c (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix for correct import path. No scope creep.

## Issues Encountered
None beyond the import path deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- DEFFFormatter is ready for Plan 02 (`lucy fragment to-lsd` CLI command)
- Plan 02 can import DEFFFormatter from `lucy_ng.fragments` and wire it into Click
- Fragment file writing and DEFF/FEXP generation are fully tested and working

## Self-Check: PASSED

All files and commits verified:
- src/lucy_ng/fragments/lsd_formatter.py: FOUND
- tests/test_lsd_formatter.py: FOUND
- 52-01-SUMMARY.md: FOUND
- Commit 6fad17b (RED): FOUND
- Commit 2fa018c (GREEN): FOUND

---
*Phase: 52-deff-formatter-lsd-generation*
*Completed: 2026-02-19*

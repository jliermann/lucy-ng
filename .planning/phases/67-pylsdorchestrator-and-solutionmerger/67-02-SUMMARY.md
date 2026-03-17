---
phase: 67-pylsdorchestrator-and-solutionmerger
plan: 02
subsystem: lsd
tags: [pylsd, solution-merger, inchi, deduplication, tdd, edge-cases]

# Dependency graph
requires:
  - phase: 67-pylsdorchestrator-and-solutionmerger/67-01
    provides: SolutionMerger implementation, MergedSolution, MergeResult dataclasses, all exports in __init__.py

provides:
  - test_invalid_smiles_skipped: verifies INVALID_XYZ SMILES silently dropped, not in merged output
  - test_empty_smiles_file: verifies None smiles_file permutation skipped gracefully with correct total_permutations count

affects: [69-cli-and-regression-suite, 71-ibuprofen-case-uat]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SolutionMerger._smiles_to_inchi_key returns None for invalid SMILES (RDKit MolFromSmiles guard)"
    - "None smiles_file skipped at entry of merge loop: exists() check returns False for None path"

key-files:
  created: []
  modified:
    - tests/test_lsd_orchestrator.py

key-decisions:
  - "Plan 67-01 had already implemented SolutionMerger and exported all classes — Plan 67-02 adds only the 2 missing edge-case tests"
  - "test_invalid_smiles_skipped covers the None-guard path in _smiles_to_inchi_key"
  - "test_empty_smiles_file covers the None smiles_file path at the top of the merge loop"

patterns-established:
  - "Edge case tests for invalid input placed in TestSolutionMergerEdgeCases class, separate from happy-path TestSolutionMerger"

requirements-completed: [ORCH-03, ORCH-04]

# Metrics
duration: 6min
completed: 2026-03-17
---

# Phase 67 Plan 02: SolutionMerger Edge Cases Summary

**Two missing edge-case tests added to test_lsd_orchestrator.py: invalid SMILES silently skipped, None smiles_file permutation gracefully ignored**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-17T13:19:54Z
- **Completed:** 2026-03-17T13:26:14Z
- **Tasks:** 1 (edge-case tests added)
- **Files modified:** 1

## Accomplishments

- Confirmed Plan 67-01 had already implemented SolutionMerger, MergedSolution, MergeResult fully (18 tests passing pre-plan)
- Added test_invalid_smiles_skipped: SMILES file with "INVALID_XYZ" is silently skipped, valid molecule count unaffected
- Added test_empty_smiles_file: permutation with smiles_file=None is skipped, run_report total_permutations still counts it
- All 20 orchestrator tests pass; 809 non-database tests pass (3 skipped)

## Task Commits

1. **Add edge case tests for SolutionMerger** - `82606fd` (test)

**Plan metadata:** (this commit)

_Note: Implementation already existed from Plan 67-01; this plan adds the 2 edge-case tests that were not yet written._

## Files Created/Modified

- `tests/test_lsd_orchestrator.py` - Added TestSolutionMergerEdgeCases class with test_invalid_smiles_skipped and test_empty_smiles_file (75 lines added)

## Decisions Made

- Plan 67-01 had merged SolutionMerger into the same execution (noted in 67-01 SUMMARY: "SolutionMerger is already implemented here"). Plan 67-02 fills the gap by adding the 2 missing edge-case tests from the behavior spec.
- TestSolutionMergerEdgeCases placed as a separate class from TestSolutionMerger to keep edge cases distinct from happy-path tests.

## Deviations from Plan

### Context Deviation

**Pre-implemented features from Plan 67-01**
- **Found during:** Initial code review
- **Issue:** Plan 67-02 was designed as a TDD plan (RED/GREEN phases), but Plan 67-01 had already implemented the full SolutionMerger including tests for deduplication, provenance, and merged.smi output. Only 2 tests from the plan's behavior spec were missing.
- **Fix:** Added the 2 missing edge-case tests (test_invalid_smiles_skipped, test_empty_smiles_file) and confirmed all pass immediately (no RED phase needed — GREEN from the start).
- **Files modified:** tests/test_lsd_orchestrator.py
- **Verification:** 20 tests pass, including 2 new ones

---

**Total deviations:** 1 (context — implementation pre-existed from 67-01)
**Impact on plan:** No scope creep. Tests cover exactly what the plan's behavior spec specified for the missing edge cases.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 69 (CLI and Regression Suite) can use PyLSDOrchestrator + SolutionMerger with full test coverage
- Phase 71 (Ibuprofen CASE UAT) has the full orchestration engine with 20 tests verifying all edge cases

---
*Phase: 67-pylsdorchestrator-and-solutionmerger*
*Completed: 2026-03-17*

## Self-Check: PASSED

- FOUND: tests/test_lsd_orchestrator.py
- FOUND: .planning/phases/67-pylsdorchestrator-and-solutionmerger/67-02-SUMMARY.md
- FOUND commit 82606fd (test: add edge case tests for SolutionMerger)

---
phase: 76-milestone-uat-gate
plan: "01"
subsystem: verification
tags: [tdd, rdkit, uat, verification, sanitisation]
dependency_graph:
  requires: []
  provides: [scripts/verify_case_solution.py, 76-SANITISATION-VERIFIED.md]
  affects: [76-02-PLAN.md]
tech_stack:
  added: []
  patterns: [argparse+JSON+sys.exit, subprocess-black-box-tests, RDKit-formula-check]
key_files:
  created:
    - scripts/verify_case_solution.py
    - tests/test_verify_case_solution.py
    - .planning/phases/76-milestone-uat-gate/76-SANITISATION-VERIFIED.md
  modified: []
decisions:
  - "Correct ibuprofen SMILES for C13H18O2 is CC(Cc1ccc(cc1)C(C)C)C(=O)O — plan's suggested SMILES c1ccc(CC(C)CC(=O)O)cc1 gives C11H14O2 (wrong)"
  - "CASE1 analysis/ subdir contains prior-run CASE-PROGRESS.md with 'ibuprofen' text — not a blind issue; NMR raw dirs 1-7 are clean"
  - "CASE9 has no DEPT-90 experiment — blind run proceeds with DEPT-135 only"
metrics:
  duration: "~20 minutes"
  completed: "2026-06-01T08:42:59Z"
  tasks_completed: 3
  files_created: 3
  files_modified: 0
---

# Phase 76 Plan 01: Verification Harness + Sanitisation Check Summary

Standalone RDKit script `verify_case_solution.py` that checks top-3 SMILES in `merged.smi` for aromatic ring (>=6 aromatic atoms) and exact formula match via `CalcMolFormula`, plus confirmed-blind pre-run record for CASE1 (C13H18O2) and CASE9 (C12H16O3).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Write failing tests | 8a9583f | tests/test_verify_case_solution.py |
| 2 (GREEN) | Implement verify_case_solution.py | e0cb256 | scripts/verify_case_solution.py, tests/test_verify_case_solution.py |
| 3 (auto) | Sanitisation re-verification | 237d238 | .planning/phases/76-milestone-uat-gate/76-SANITISATION-VERIFIED.md |

## TDD Gate Compliance

- RED gate commit: `8a9583f` — `test(76-01): add failing tests for verify_case_solution.py` — all 8 tests failed because script did not exist
- GREEN gate commit: `e0cb256` — `feat(76-01): implement verify_case_solution.py — GREEN` — all 8 tests pass
- REFACTOR: not required (functions < 15 lines, no cleanup needed)

## Verification Results

```
pytest tests/test_verify_case_solution.py  →  8 passed
python scripts/verify_case_solution.py smoke_pass.smi C13H18O2  →  exit 0, "pass": true
python scripts/verify_case_solution.py smoke_pass.smi C12H16O3  →  exit 1, "pass": false
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect ibuprofen SMILES in plan**

- **Found during:** Task 2 (GREEN run — first test failed with computed_formula=C11H14O2)
- **Issue:** Plan's suggested SMILES `c1ccc(CC(C)CC(=O)O)cc1` gives molecular formula C11H14O2, not C13H18O2 (missing isobutyl group). This caused `test_pass_aromatic_correct_formula` to fail even after implementation.
- **Fix:** Replaced with `CC(Cc1ccc(cc1)C(C)C)C(=O)O` (verified by RDKit: C13H18O2, 6 aromatic atoms). Updated in both test file and plan's test values.
- **Files modified:** `tests/test_verify_case_solution.py`
- **Commit:** `e0cb256`

## Sanitisation Check Results

All 8 checks PASS:

| Dataset | Check | Status |
|---------|-------|--------|
| CASE1 | No .mol/.sdf in NMR raw dirs | PASS |
| CASE1 | Formula = C13H18O2 | PASS |
| CASE1 | No "ibuprofen" in NMR raw data | PASS |
| CASE1 | Title files: instrument/type only, no name | PASS |
| CASE9 | No .mol/.sdf anywhere | PASS |
| CASE9 | Formula = C12H16O3 | PASS |
| CASE9 | No "hydroxy/benzoic/isopropyl/ester" | PASS |
| CASE9 | Title files: formula only, no compound name | PASS |

**Overall verdict: READY FOR BLIND RUN**

Note: `analysis/CASE-PROGRESS.md` under CASE1 contains the word "ibuprofen" — this is a prior-run analysis log, not NMR data. The blind Claude instance receives only the NMR experiment path; it will not read analysis logs.

## Known Stubs

None — the script is fully functional. No placeholder data.

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes introduced. The script reads a local file path and formula from argv, calls RDKit in-process, and emits JSON to stdout. No surface outside the plan's threat model.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| scripts/verify_case_solution.py | FOUND |
| tests/test_verify_case_solution.py | FOUND |
| 76-SANITISATION-VERIFIED.md | FOUND |
| Commit 8a9583f (Task 1 RED) | FOUND |
| Commit e0cb256 (Task 2 GREEN) | FOUND |
| Commit 237d238 (Task 3 sanitisation) | FOUND |

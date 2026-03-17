---
phase: 67-pylsdorchestrator-and-solutionmerger
plan: 01
subsystem: lsd
tags: [pylsd, orchestration, permutation, smiles, inchi, deduplication, tdd]

# Dependency graph
requires:
  - phase: 66-lsdinputgenerator-extensions
    provides: LSDInputGenerator.write_file() with pylsd_mode and extended HMBC syntax
  - phase: 65-hypothesis-gate
    provides: outlsd 5 < sol bypass pattern, confirmation of 4J removal hypothesis

provides:
  - PyLSDOrchestrator: 2^K permutation engine for suspect 4J HMBC correlations
  - SolutionMerger: InChI-key deduplication with run_report.json provenance
  - PermutationResult, OrchestrationResult, MergedSolution, MergeResult dataclasses
  - Exports in lucy_ng/lsd/__init__.py

affects: [69-cli-and-regression-suite, 71-ibuprofen-case-uat]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Permutation generation via itertools.product([True, False], repeat=K)"
    - "deepcopy + value-tuple suspect identification for correlation filtering"
    - "outlsd bypass: subprocess.run([outlsd_path, '5'], stdin=sol_file)"
    - "InChI key deduplication via rdkit.Chem.inchi.MolToInchi + InchiToInchiKey"

key-files:
  created:
    - src/lucy_ng/lsd/orchestrator.py
    - tests/test_lsd_orchestrator.py
  modified:
    - src/lucy_ng/lsd/__init__.py

key-decisions:
  - "K-cap guard (K>3 raises ValueError) placed as FIRST statement in run(), before any I/O"
  - "Suspect correlations identified by (atom1_index, atom2_index, correlation_type) tuple — not id() — because deepcopy invalidates identity"
  - "Included suspect correlations use max_bonds=4; excluded suspects are simply omitted"
  - "outlsd invoked directly via subprocess bypassing LSDRunner._run_outlsd (known bug: missing mode argument)"
  - "InChI key used for deduplication (not canonical SMILES) — canonical across tautomers/stereoisomers"
  - "K=0 handled naturally: itertools.product(repeat=0) yields one empty tuple → single run"

patterns-established:
  - "TDD RED/GREEN: test file committed first with failing import, then implementation"
  - "Permutation directories: perm_00, perm_01, ... with LSD file and optional solutions.smi"
  - "run_report.json structure: total_permutations, unique_solutions, solutions[{inchi_key, smiles, provenance[]}]"

requirements-completed: [ORCH-01, ORCH-02, ORCH-03, ORCH-04]

# Metrics
duration: 18min
completed: 2026-03-17
---

# Phase 67 Plan 01: PyLSDOrchestrator and SolutionMerger Summary

**PyLSDOrchestrator with itertools permutation engine generates 2^K LSD runs for suspect 4J HMBC correlations; SolutionMerger deduplicates solutions via InChI key with provenance JSON**

## Performance

- **Duration:** 18 min
- **Started:** 2026-03-17T12:52:58Z
- **Completed:** 2026-03-17T13:10:51Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 3

## Accomplishments

- PyLSDOrchestrator generates 2^K (1, 2, 4, 8) permutation LSD files from suspect correlations, with K>3 guard
- Each permutation correctly includes/excludes suspects; included ones use max_bonds=4 for extended 4J range
- SolutionMerger deduplicates solutions via InChI key and writes run_report.json with per-solution provenance
- outlsd invoked directly via subprocess([outlsd_path, "5"]) bypassing the known LSDRunner._run_outlsd bug
- 18 tests pass; full suite 904/911 green (7 skipped, pre-existing)

## Task Commits

1. **RED: failing tests for PyLSDOrchestrator and SolutionMerger** - `c198d7c` (test)
2. **GREEN: implement PyLSDOrchestrator and SolutionMerger** - `ec98ace` (feat)

**Plan metadata:** (this commit)

_Note: TDD plan — RED commit first (failing import), GREEN commit implements all._

## Files Created/Modified

- `src/lucy_ng/lsd/orchestrator.py` - PyLSDOrchestrator, SolutionMerger and 4 supporting dataclasses (PermutationResult, OrchestrationResult, MergedSolution, MergeResult)
- `tests/test_lsd_orchestrator.py` - 18 tests across 6 test classes (657 lines)
- `src/lucy_ng/lsd/__init__.py` - Added 6 new exports: PyLSDOrchestrator, PermutationResult, OrchestrationResult, SolutionMerger, MergedSolution, MergeResult

## Decisions Made

- K-cap check is the very first statement in `run()` — before `output_dir.mkdir()` — so no directories are created when K>3
- Suspects identified by `(atom1_index, atom2_index, correlation_type)` value tuple (not `id()`) because `deepcopy` creates new object identities
- `itertools.product([True, False], repeat=K)` handles K=0 gracefully (yields one empty tuple) — no special case needed
- InChI key deduplication preferred over canonical SMILES: handles tautomers/stereoisomers consistently across RDKit versions

## Deviations from Plan

None — plan executed exactly as written. All anti-patterns from RESEARCH.md avoided.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 67-02 (SolutionMerger plan) can proceed — SolutionMerger is already implemented here (merged into 67-01 per the module structure)
- Phase 69 (CLI and Regression Suite) can use PyLSDOrchestrator + SolutionMerger to build end-to-end CASE commands
- Phase 71 (Ibuprofen CASE UAT) has the full orchestration engine it needs

---
*Phase: 67-pylsdorchestrator-and-solutionmerger*
*Completed: 2026-03-17*

## Self-Check: PASSED

- FOUND: src/lucy_ng/lsd/orchestrator.py
- FOUND: tests/test_lsd_orchestrator.py
- FOUND: .planning/phases/67-pylsdorchestrator-and-solutionmerger/67-01-SUMMARY.md
- FOUND commit c198d7c (RED: failing tests)
- FOUND commit ec98ace (GREEN: implementation)

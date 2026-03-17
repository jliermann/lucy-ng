---
phase: 67-pylsdorchestrator-and-solutionmerger
verified: 2026-03-17T14:45:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 67: PyLSDOrchestrator and SolutionMerger Verification Report

**Phase Goal:** A Python orchestrator generates permutation LSD files for suspect 4J correlations, runs the LSD binary once per permutation, and merges deduplicated solutions with provenance tracking
**Verified:** 2026-03-17T14:45:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | PyLSDOrchestrator with 3 suspects generates exactly 8 permutation LSD files | VERIFIED | `test_generates_permutation_files` passes; `itertools.product([True, False], repeat=3)` yields 8 tuples; 8 `perm_NN` dirs each receive a `.lsd` file |
| 2  | Each permutation includes/excludes the correct suspect correlations | VERIFIED | `test_permutation_content` passes; `_build_permutation` uses value-tuple identity `(atom1_index, atom2_index, correlation_type)` to remove then re-add per flag |
| 3  | Suspects included in a permutation use extended bond range (max_bonds=4) | VERIFIED | `test_included_suspects_use_extended_bond_range` passes; line 250 `included_corr.max_bonds = 4` |
| 4  | K>3 suspects raises ValueError before any I/O | VERIFIED | `test_k_greater_than_3_raises` passes; K-cap check at line 164 is the first statement in `run()`, before `output_dir.mkdir()` |
| 5  | K=0 suspects runs a single permutation with the base problem unchanged | VERIFIED | `test_k0_succeeds_single_permutation` passes; `itertools.product(repeat=0)` yields `[()]` naturally |
| 6  | SolutionMerger deduplicates identical structures by InChI key across runs | VERIFIED | `test_deduplication` passes; three ethanol SMILES variants (`CCO`, `OCC`, `C(C)O`) merge to 1 unique solution |
| 7  | A structure appearing in 3 runs appears once in merged.smi with 3 provenance entries | VERIFIED | `test_multi_perm_provenance` passes; `run_report.json` entry has 3 provenance records |
| 8  | run_report.json records which correlations were active in each permutation | VERIFIED | `test_run_report_provenance` passes; each provenance entry contains `perm_index`, `include_flags`, `active_correlations` |
| 9  | merged.smi contains only unique canonical SMILES, no duplicates or empty lines | VERIFIED | `test_merged_smi_written` passes; `merged.smi` written as `"\n".join(valid_smiles)` filtering `None`/empty |

**Score:** 9/9 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/lsd/orchestrator.py` | PyLSDOrchestrator, PermutationResult, OrchestrationResult, SolutionMerger, MergedSolution, MergeResult | VERIFIED | 448 lines; all 6 classes present and substantive |
| `tests/test_lsd_orchestrator.py` | Unit tests covering permutation generation, K-cap, boundary, outlsd bypass, deduplication, provenance, edge cases | VERIFIED | 732 lines (min_lines 150 from plan 02); 20 tests in 8 test classes |
| `src/lucy_ng/lsd/__init__.py` | Re-exports all 6 orchestrator public classes | VERIFIED | Lines 46-53 import all 6; lines 79-84 declare them in `__all__` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `orchestrator.py` | `lucy_ng.lsd.models` | `from lucy_ng.lsd.models import LSDCorrelation, LSDProblem` | VERIFIED | Line 29: `from lucy_ng.lsd.models import LSDCorrelation, LSDProblem` |
| `orchestrator.py` | `lucy_ng.lsd.generator` | `LSDInputGenerator.write_file()` per permutation | VERIFIED | Line 28 import; line 187 `LSDInputGenerator.write_file(perm_problem, lsd_file)` |
| `orchestrator.py` | `lucy_ng.lsd.runner` | `self.runner.run_file()` per permutation | VERIFIED | Line 31 import; line 190 `self.runner.run_file(lsd_file, ...)` |
| `orchestrator.py` | `rdkit.Chem.inchi` | `MolToInchi + InchiToInchiKey` for canonical deduplication | VERIFIED | Lines 419-427 in `_smiles_to_inchi_key`; guarded with `None` checks at each step |
| `orchestrator.py` | `lucy_ng.lsd.parser` | `LSDOutputParser.parse_smiles_file()` to read permutation SMILES | VERIFIED | Line 31 import; lines 335 and 381 `LSDOutputParser.parse_smiles_file(...)` |
| `lsd/__init__.py` | `orchestrator.py` | Re-export public classes | VERIFIED | Lines 46-53: `from lucy_ng.lsd.orchestrator import MergeResult, MergedSolution, OrchestrationResult, PermutationResult, PyLSDOrchestrator, SolutionMerger` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ORCH-01 | 67-01 | PyLSDOrchestrator generates permutations of LSD input files with different 4J correlation configurations | SATISFIED | `PyLSDOrchestrator.run()` uses `itertools.product([True, False], repeat=K)` to generate 2^K permutation LSD files; 5 tests cover permutation generation |
| ORCH-02 | 67-01 | PyLSDOrchestrator caps permutation count (K≤3) to prevent combinatorial explosion | SATISFIED | K>3 check is the very first statement in `run()` before any I/O; `test_k_greater_than_3_raises` and `test_k5_raises` confirm no directories are created |
| ORCH-03 | 67-01, 67-02 | SolutionMerger deduplicates solutions from multiple LSD runs using InChI canonicalization | SATISFIED | `SolutionMerger._smiles_to_inchi_key()` uses `MolToInchi + InchiToInchiKey`; `test_deduplication` verifies CCO/OCC/C(C)O collapse to 1 entry |
| ORCH-04 | 67-01, 67-02 | SolutionMerger preserves provenance (which correlation configuration produced each solution) | SATISFIED | Each `MergedSolution.provenance` entry contains `perm_index`, `include_flags`, `original_solution_index`, `active_correlations`; `test_multi_perm_provenance` and `test_run_report_provenance` verify structure |

No orphaned requirements — all 4 ORCH requirements claimed by plans and confirmed implemented.

---

### Anti-Patterns Found

No anti-patterns detected.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | — |

Grep of `orchestrator.py` for `TODO`, `FIXME`, `placeholder`, `return null`, `return {}` returned no matches.

---

### Human Verification Required

None — all behaviors are verifiable programmatically via the test suite.

---

### Commit Verification

All three TDD commits confirmed real in git history:

| Commit | Message | Phase |
|--------|---------|-------|
| `c198d7c` | test(67-01): add failing tests for PyLSDOrchestrator and SolutionMerger | RED |
| `ec98ace` | feat(67-01): implement PyLSDOrchestrator and SolutionMerger | GREEN |
| `82606fd` | test(67-02): add edge case tests for SolutionMerger | edge cases |

---

### Test Suite Status

```
pytest tests/test_lsd_orchestrator.py -q
20 passed, 26 warnings in 0.07s
```

20 tests across 8 classes: `TestGeneratesPermutationFiles`, `TestPermutationContent`, `TestKCapEnforcement`, `TestKBoundary`, `TestOutlsdBypass`, `TestPermutationResultStructure`, `TestSolutionMerger`, `TestRunReportProvenance`, `TestSolutionMergerEdgeCases`.

---

### Summary

Phase 67 goal is fully achieved. The Python orchestrator (`PyLSDOrchestrator`) correctly generates 2^K permutation LSD files for up to K=3 suspect 4J HMBC correlations, enforces the K-cap with a pre-I/O guard, invokes LSD via `LSDRunner.run_file()`, and calls `outlsd` directly via `subprocess.run([outlsd_path, "5"])` — bypassing the known `LSDRunner._run_outlsd` bug. The merger (`SolutionMerger`) deduplicates by InChI key, not canonical SMILES, and writes `merged.smi` and `run_report.json` with per-solution provenance including `active_correlations`. All 4 ORCH requirements are satisfied, all 20 tests pass, and all 6 classes are correctly re-exported from `lucy_ng.lsd.__init__`.

---

_Verified: 2026-03-17T14:45:00Z_
_Verifier: Claude (gsd-verifier)_

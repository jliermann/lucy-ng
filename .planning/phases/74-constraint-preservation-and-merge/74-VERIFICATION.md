---
phase: 74-constraint-preservation-and-merge
verified: 2026-05-24T10:00:00Z
status: passed
score: 9/9
overrides_applied: 0
---

# Phase 74: Constraint Preservation and Merge — Verification Report

**Phase Goal:** Native-only constraint generation + constraint preservation across Python solver paths; aromatic ring emerges from constraints (no SKEL). Python API scope; agent hand-written path is Phase 75.
**Verified:** 2026-05-24T10:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Generated LSD file with equivalence pairs contains BOND or COSY (not SYME) — D-03 | VERIFIED | `test_gem_dimethyl_emits_bond` and `test_aromatic_ch_pair_emits_cosy` pass; grep on generator.py confirms "SYME" never in emitted strings |
| 2 | Generated LSD file with ring_exclusion_enabled=True contains DEFF F1/F2 and FEXP (not DEFF NOT) — D-03 | VERIFIED | `test_ring_exclusion_emits_deff_f_fexp` and `test_no_deff_not_in_output` pass; generator.py lines 192-197 emit only `DEFF F1 "ring3"`, `DEFF F2 "ring4"`, `FEXP "NOT F1 AND NOT F2"` |
| 3 | ring3 and ring4 filter files written to output dir when write_file() called with ring_exclusion_enabled | VERIFIED | `test_ring_files_written_to_output_dir` passes; `_write_filter_files()` in generator.py confirmed wired from `write_file()` |
| 4 | No generated file ever contains SYME or DEFF NOT — native-only contract | VERIFIED | grep on generator.py returns only a comment mentioning "DEFF NOT"; no emitted string; `test_no_syme_in_output` and `test_no_deff_not_in_output` pass |
| 5 | LSDProblem.add_equivalence_pair() and add_aromatic_equivalence_pair() inject into existing constraints/correlations lists (Option A) | VERIFIED | models.py lines 200-253: both methods append to `self.constraints` / `self.correlations` directly; no new model class |
| 6 | Permutation .lsd files contain the FULL constraint set (BOND + ring exclusion) — D-03 permutation path | VERIFIED | `test_perm_preserves_bond_constraints` (K=2, 4 perms each contain BOND 10 11 / BOND 10 12) and `test_perm_preserves_ring_exclusion` (K=1, 2 perms each have DEFF F1 and ring3/ring4 on disk) pass; wired via `copy.deepcopy(base_problem)` in orchestrator.py line 231 |
| 7 | End-to-end: generator-built problem runs through LSD and yields aromatic ring WITHOUT SKEL — D-04 EMERGENT | VERIFIED | `test_ibuprofen_emergent_aromatic` passes (1 passed, not skipped — LSD is installed on dev box); benzene (C1=CC=CC=C1) emerged as solution; 6 aromatic atoms confirmed by RDKit; "SKEL" not in generated file |
| 8 | SolutionMerger collects solutions from non-empty per-permutation output | VERIFIED | `test_merger_collects_from_non_empty_smiles_files` passes; total_raw_solutions=2, unique_solutions=2, merged.smi non-empty |
| 9 | Scope boundary documented: RELI-02/03 are Python-path-only in Phase 74; Phase 75 closes agent hand-written path | VERIFIED | Both PLAN files contain explicit "AGENT-BYPASS SCOPE BOUNDARY" section; both SUMMARYs repeat it; no agent skill files modified |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/lsd/models.py` | ring_exclusion_enabled field + add_equivalence_pair() + add_aromatic_equivalence_pair() | VERIFIED | All three present: line 186 (field), lines 200-227 (add_equivalence_pair), lines 229-253 (add_aromatic_equivalence_pair) |
| `src/lucy_ng/lsd/generator.py` | _write_filter_files() + ring exclusion emission in generate() | VERIFIED | `_write_filter_files` at lines 228-242; ring exclusion section at lines 192-197; wired from `write_file()` at lines 223-224 |
| `src/lucy_ng/lsd/filters/ring3` | 3-membered ring SSTR/LINK filter | VERIFIED | Exists (133 bytes); contains 3 SSTR lines + LINK S1 S2, S2 S3, S1 S3 |
| `src/lucy_ng/lsd/filters/ring4` | 4-membered ring SSTR/LINK filter | VERIFIED | Exists (168 bytes); contains 4 SSTR lines + LINK S1 S2, S2 S3, S3 S4, S1 S4 |
| `src/lucy_ng/lsd/filters/__init__.py` | Package marker | VERIFIED | Exists (62 bytes); enables importlib.resources.files("lucy_ng.lsd.filters") |
| `tests/test_lsd_generator.py` | TestNativeConstraintEmission class (6 tests) + TestLSDGeneratorEndToEnd (1 test) | VERIFIED | TestNativeConstraintEmission at lines 549-607 (6 tests); TestLSDGeneratorEndToEnd at lines 610-787 |
| `tests/test_lsd_orchestrator.py` | TestPermutationConstraintPreservation (2 tests) + TestSolutionMergerPostFix (1 test) | VERIFIED | TestPermutationConstraintPreservation at lines 670-785; TestSolutionMergerPostFix at lines 788-857 |
| `pyproject.toml` | artifacts includes src/lucy_ng/lsd/filters/* | VERIFIED | Line 58: `artifacts = ["src/lucy_ng/data/schemas/*", "src/lucy_ng/lsd/filters/*"]` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| LSDProblem.add_equivalence_pair() | problem.constraints (BOND entries) | appends LSDConstraint(constraint_type="BOND") | VERIFIED | models.py lines 216-227 append two LSDConstraint objects with constraint_type="BOND" |
| LSDProblem.add_aromatic_equivalence_pair() | problem.correlations (COSY entries) | appends LSDCorrelation(correlation_type="COSY") with dedup | VERIFIED | models.py lines 243-253 check sorted pair before appending LSDCorrelation("COSY") |
| LSDInputGenerator.generate() | DEFF F1/F2 + FEXP lines | checks problem.ring_exclusion_enabled and emits ring exclusion section before EXIT | VERIFIED | generator.py lines 192-197 guarded by `if problem.ring_exclusion_enabled:` |
| LSDInputGenerator.write_file() | output_dir/ring3 and output_dir/ring4 | _write_filter_files(output_path.parent) when ring_exclusion_enabled | VERIFIED | generator.py lines 223-224: `if problem.ring_exclusion_enabled: LSDInputGenerator._write_filter_files(output_path.parent)` |
| PyLSDOrchestrator._build_permutation() | perm.ring_exclusion_enabled + perm.constraints (BOND) | copy.deepcopy(base_problem) — propagates all fields | VERIFIED | orchestrator.py line 231: `perm = copy.deepcopy(base_problem)` — structural proof, confirmed by TestPermutationConstraintPreservation tests |

### Data-Flow Trace (Level 4)

Not applicable for this phase. All deliverables are library API methods and test classes — no rendering components with data state. The end-to-end test (`test_ibuprofen_emergent_aromatic`) traces the full data flow from LSDProblem construction through LSD invocation to RDKit aromatic atom count and passes.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| TestNativeConstraintEmission (6 tests) | `pytest tests/test_lsd_generator.py -k TestNativeConstraintEmission -q` | 6 passed | PASS |
| TestPermutationConstraintPreservation (2 tests) | `pytest tests/test_lsd_orchestrator.py -k TestPermutationConstraintPreservation -q` | 2 passed | PASS |
| TestSolutionMergerPostFix (1 test) | `pytest tests/test_lsd_orchestrator.py -k TestSolutionMergerPostFix -q` | 1 passed | PASS |
| TestLSDGeneratorEndToEnd (emergent aromatic, LSD installed) | `pytest tests/test_lsd_generator.py -k TestLSDGeneratorEndToEnd -v` | 1 passed (not skipped) | PASS |
| Generator emits no SYME/DEFF NOT/SKEL | `grep -rn "SYME\|DEFF NOT\|SKEL" src/lucy_ng/lsd/generator.py` | 1 comment-only match | PASS |
| pyproject.toml includes filters/* | `grep "artifacts.*filters" pyproject.toml` | line 58 matches | PASS |

### Probe Execution

No probe scripts declared or applicable for this phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| RELI-02 | 74-01, 74-02 | Complete validated constraint set on every solver path — Python API path | VERIFIED (partial — Python path only; agent path is Phase 75) | TestNativeConstraintEmission (6 tests), TestPermutationConstraintPreservation (2 tests) all pass; no SYME/DEFF NOT emitted |
| RELI-03 | 74-01, 74-02 | Aromatic compounds yield aromatic-ring solutions — Python API path | VERIFIED (partial — Python path only; full proof is Phase 76 UAT) | test_ibuprofen_emergent_aromatic passes with LSD installed; 6 aromatic atoms in benzene solution; no SKEL in generated .lsd |

**Scope note:** REQUIREMENTS.md marks both RELI-02 and RELI-03 as "Complete" at Phase 74 in the traceability table. This is accurate for the Python programmatic path. Both plans explicitly document that the agent hand-written path (bypasses LSDInputGenerator) remains unreformed until Phase 75, and full end-to-end UAT proof is Phase 76. The phase goal as stated is scoped to the Python API — this scoping is correct and explicitly acknowledged.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

No TBD, FIXME, XXX, TODO, HACK, or PLACEHOLDER markers found in any phase-modified file. No stub returns, no empty implementations, no hardcoded empty data in production code.

### Human Verification Required

None. All must-haves are verifiable programmatically. The end-to-end aromatic emergence test runs and passes on the dev box (LSD installed), removing the only item that would normally require human judgment.

---

## Gaps Summary

No gaps. All 9 must-have truths are VERIFIED, all artifacts exist and are substantive, all key links are wired, all tests pass, no debt markers found.

The intentional scope restriction (Python API only, not agent skill files) is correctly documented in both plan objectives, both summaries, and explicitly captured as must-have truth #9 above.

---

_Verified: 2026-05-24T10:00:00Z_
_Verifier: Claude (gsd-verifier)_

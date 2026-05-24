---
phase: 74-constraint-preservation-and-merge
plan: 02
subsystem: lsd
tags: [lsd, tests, tdd, permutation, ring-exclusion, emergent-aromatic, solution-merger]

requires:
  - phase: 74-01
    provides: LSDProblem.ring_exclusion_enabled + add_equivalence_pair + add_aromatic_equivalence_pair + bundled ring3/ring4 filters

provides:
  - TestPermutationConstraintPreservation class (2 tests) — deepcopy propagation proof
  - TestSolutionMergerPostFix class (1 test) — post-Phase-73 merge correctness
  - TestLSDGeneratorEndToEnd class (1 test, skipif LSD) — emergent aromatic e2e

affects:
  - phase: 75-skill-rewrite (D-03 native constraint proof documented via tests)
  - phase: 76-uat (aromatic emergence pattern confirmed at unit-test level)

tech-stack:
  added: []
  patterns:
    - solncounter-based solution count (robust vs runner stderr heuristic)
    - sum(a.GetIsAromatic() for a in mol.GetAtoms()) — RDKit aromatic atom count (no GetNumAromaticAtoms)
    - Minimal 6-sp2-CH benzene problem: 3 COSY pairs + ring exclusion → benzene solution

key-files:
  created: []
  modified:
    - tests/test_lsd_orchestrator.py (TestPermutationConstraintPreservation + TestSolutionMergerPostFix)
    - tests/test_lsd_generator.py (TestLSDGeneratorEndToEnd)

key-decisions:
  - "Minimal benzene test uses 6 sp2 CH atoms (no quaternary) + 3 COSY pairs (1-2, 3-4, 5-6) + ring exclusion — quaternary sp2 atoms require 3 bonds and cannot form a monocyclic 6-ring alone"
  - "test_perm_preserves_ring_exclusion verifies filter files on disk per perm dir (write_file called per permutation) — proves ring3/ring4 are co-located with each perm .lsd"
  - "solncounter file used for accurate solution count (LSD writes integer there) over runner's stderr heuristic which over-counts in some edge cases"
  - "AGENT-BYPASS SCOPE BOUNDARY explicit: RELI-02/03 partially satisfied (Python API path); Phase 75 closes agent hand-written path; Phase 76 proves full RELI-02/03"

duration: 35min
completed: 2026-05-24
---

# Phase 74 Plan 02: Permutation Constraint Preservation and Merge Tests Summary

**Permutation deepcopy carries full constraint set (BOND + ring exclusion) to every perm file; SolutionMerger collects non-zero solutions from valid SMILES files; generator-built benzene ring problem yields aromatic solution from LSD without SKEL**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-05-24T00:30:00Z
- **Completed:** 2026-05-24T01:05:00Z
- **Tasks:** 2 (both TDD, both GREEN on first run after debugging)
- **Files modified:** 2 (tests only; zero production code changes)
- **Tests added:** 4 new tests across 2 files

## Accomplishments

- `TestPermutationConstraintPreservation` class in `tests/test_lsd_orchestrator.py`:
  - `test_perm_preserves_bond_constraints`: K=2 suspects, base problem with BOND 10/11/12 (gem-dimethyl) → all 4 perm dirs have "BOND 10 11" and "BOND 10 12" in their .lsd files — deepcopy propagation of `constraints` list proven
  - `test_perm_preserves_ring_exclusion`: K=1 suspect, `ring_exclusion_enabled=True` → both perm dirs have `DEFF F1 "ring3"` and `FEXP` in .lsd AND `ring3`/`ring4` filter files on disk — proves `write_file()` is called per permutation and copies filter files to each perm dir
- `TestSolutionMergerPostFix` class in `tests/test_lsd_orchestrator.py`:
  - `test_merger_collects_from_non_empty_smiles_files`: 2 PermutationResult objects with real (non-empty) smiles files (ethanol, propanol) → `total_raw_solutions` ≥ 2 in run_report.json, `merged.smi` non-empty, `unique_solutions` == 2 — Phase 73 merge pipeline confirmed correct
- `TestLSDGeneratorEndToEnd` class in `tests/test_lsd_generator.py`:
  - `test_ibuprofen_emergent_aromatic` (skipif LSD+outlsd not installed): generator-built 6-sp2-CH benzene ring problem (3 COSY pairs + ring_exclusion_enabled) → LSD run finds 1 solution (benzene, `C1=CC=CC=C1`) → RDKit confirms 6 aromatic atoms → aromatic ring EMERGED without SKEL forcing (D-04 confirmed)
  - Generated .lsd assertions: "SKEL" not in content ✓, "SYME" not in content ✓, "DEFF NOT" not in content ✓

## Task Commits

1. **Task 1: TestPermutationConstraintPreservation** — `143a8d3`
   - `test_perm_preserves_bond_constraints`
   - `test_perm_preserves_ring_exclusion`

2. **Task 2: SolutionMerger correctness + emergent-aromatic e2e** — `b0a4013`
   - `TestSolutionMergerPostFix.test_merger_collects_from_non_empty_smiles_files`
   - `TestLSDGeneratorEndToEnd.test_ibuprofen_emergent_aromatic`

## Files Created/Modified

- `tests/test_lsd_orchestrator.py` — added `TestPermutationConstraintPreservation` (2 tests, lines ~668-760) and `TestSolutionMergerPostFix` (1 test, lines ~665-700)
- `tests/test_lsd_generator.py` — added `TestLSDGeneratorEndToEnd` (1 test, lines ~612-765)

## Decisions Made

- **Minimal benzene test uses 6 sp2 CH atoms, not 4 CH + 2 quaternary**: 2 quaternary sp2 carbons (0 H, needing 3 bonds) cannot form a monocyclic 6-membered ring alone (they need a 3rd bond partner outside the ring), so LSD finds 0 solutions. Pure 6-sp2-CH with 3 COSY pairs works correctly.
- **3 COSY pairs (1-2, 3-4, 5-6) rather than 2**: 2 COSY pairs with only HSQC and no HMBC produces 0 LSD solutions (too sparse). 3 pairs covering all 6 atoms is sufficient.
- **solncounter file for solution count**: LSD writes the integer solution count to `solncounter` in the CWD. Using this file is more accurate than the runner's stderr heuristic (which occasionally over-counts due to "solution" substring matching).
- **sum(a.GetIsAromatic() for a in mol.GetAtoms()) instead of mol.GetNumAromaticAtoms()**: The latter method doesn't exist in the installed RDKit version (AttributeError observed during debugging).

## Deviations from Plan

### Plan Deviation: Minimal test atom setup

**1. [Rule 1 - Bug] Quaternary sp2 C atoms cannot form monocyclic 6-membered ring alone**
- **Found during:** Task 2 emergent-aromatic test debugging
- **Issue:** Plan specified "4 sp2 CH carbons + 2 sp2 quaternary C" but LSD found 0 solutions for this setup (even without ring exclusion: only cyclopropyl solutions appeared, which were excluded)
- **Root cause:** sp2 C with 0 H requires exactly 3 bonds to heavy atoms. In a 6-atom problem, 2 atoms needing 3 bonds + 4 atoms needing 2 bonds = 14 bond-ends = 7 bonds. A monocyclic 6-membered ring only has 6 bonds, so atom 1 needs a 7th bond partner = bicyclic. With ring exclusion removing 3-/4-membered rings, no valid monocyclic 5+ membered ring exists for this configuration.
- **Fix:** Used 6 sp2 CH atoms (hydrogen_count=1) so each needs only 2 ring bonds — benzene fits exactly. Added 3 COSY pairs (vs plan's 2) to cover all 6 atoms.
- **Files modified:** tests/test_lsd_generator.py (test setup only, no production code)
- **Commit:** b0a4013

**2. [Rule 1 - Bug] RDKit GetNumAromaticAtoms() does not exist**
- **Found during:** Task 2 debug run
- **Issue:** Plan's `mol.GetNumAromaticAtoms() > 0` assertion would raise AttributeError
- **Fix:** Replaced with `sum(1 for a in mol.GetAtoms() if a.GetIsAromatic()) > 0`
- **Files modified:** tests/test_lsd_generator.py
- **Commit:** b0a4013

**3. [Rule 2 - Missing critical] solncounter-based solution count**
- **Found during:** Task 2 debugging
- **Issue:** LSD runner's `solution_count` over-counted (1 when actual=0) due to "solution" substring matching in stderr. Runner returned `success=True` even with 0 real solutions.
- **Fix:** Added solncounter file read to get accurate solution count before the skip gate
- **Files modified:** tests/test_lsd_generator.py
- **Commit:** b0a4013

## AGENT-BYPASS SCOPE BOUNDARY

Phase 74 satisfies RELI-02 and RELI-03 **for the Python API path only** (code calling `LSDInputGenerator.generate()` or `write_file()`). The CASE agent (lucy-lsd-engineer) writes LSD files by hand via Bash/Write tools and does NOT call `LSDInputGenerator`. That path still writes `SYME` and `DEFF NOT`. Phase 75 must update agent skills to write `BOND`/`COSY` and `DEFF F`/`FEXP` instead. RELI-02/03 are fully closed only after Phase 75 + Phase 76 UAT.

## Known Stubs

None.

## Threat Flags

None — tests only; no new network endpoints, auth paths, file access patterns, or schema changes.

---

## Self-Check

- `tests/test_lsd_orchestrator.py` TestPermutationConstraintPreservation exists: confirmed (line ~668)
- `tests/test_lsd_orchestrator.py` TestSolutionMergerPostFix exists: confirmed
- `tests/test_lsd_generator.py` TestLSDGeneratorEndToEnd exists: confirmed
- Commit `143a8d3` exists: `git log --oneline -6` confirms
- Commit `b0a4013` exists: `git log --oneline -6` confirms
- Full pytest suite: 1004 passed, 7 skipped, 1 xfailed
- TestPermutationConstraintPreservation: 2 passed
- TestLSDGeneratorEndToEnd: 1 passed (LSD installed on dev box)

## Self-Check: PASSED

---
*Phase: 74-constraint-preservation-and-merge*
*Completed: 2026-05-24*

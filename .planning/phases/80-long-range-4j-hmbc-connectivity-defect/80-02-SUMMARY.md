---
phase: 80-long-range-4j-hmbc-connectivity-defect
plan: "02"
subsystem: ranking
tags: [tdd, green, wave-1, ranking, plausibility-filter, d-09]
dependency_graph:
  requires:
    - 80-00 (RED test baseline for TestPlausibilityFilter + TestPlausibilityFilterOrdering)
  provides:
    - src/lucy_ng/ranking/models.py::RankedSolution.is_plausible
    - src/lucy_ng/ranking/ranker.py::_is_chemically_plausible()
    - src/lucy_ng/ranking/ranker.py::rank(formula=...)
  affects:
    - 80-03+ (skill surgery plans can reference is_plausible in solution reports)
    - Future: CASE9 UAT (plausibility pre-filter prevents grossly-wrong non-aromatic solutions from ranking above correct para-benzoate)
tech_stack:
  added: []
  patterns:
    - Pydantic v2 Field(default=True) for RankedSolution.is_plausible
    - module-level private helpers (_calc_dbe_from_formula, _calc_dbe_from_mol, _is_chemically_plausible)
    - D-09 partition-before-sort pattern (plausible first, implausible appended with model_copy)
    - Local imports inside helper functions to avoid circular dependency (lucy_ng.lsd.generator, rdkit.Chem.rdMolDescriptors)
key_files:
  created: []
  modified:
    - src/lucy_ng/ranking/models.py
    - src/lucy_ng/ranking/ranker.py
    - tests/test_ranking.py
    - tests/test_validation_ranking.py
decisions:
  - D-09: Chemical plausibility pre-filter sits BEFORE the MAE sort in rank(); plausible solutions sorted by contract (-matched_count, mae); implausible appended with is_plausible=False
  - D-04: Warning text updated to reference ELIM escalation (D-02) not 4J HMBC artifact removal — post-hoc framing only
  - Aromatic check only applied when mol is parseable (RDKit). Invalid/unparseable SMILES skip the aromatic check (cannot evaluate what we cannot parse).
  - DBE check is optional (formula kwarg); skips gracefully when mol is None.
metrics:
  duration: "~30 minutes"
  completed: "2026-06-09"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 4
---

# Phase 80 Plan 02: Chemical Plausibility Pre-Filter for SolutionRanker Summary

Chemical plausibility pre-filter (D-09) added to SolutionRanker: non-aromatic solutions are demoted to the end of the ranked list when >= 4 experimental shifts fall in the 110-160 ppm aromatic region, preventing grossly-wrong structures from outranking the correct para-benzoate in CASE9.

## What Was Built

### Task 1: `is_plausible` field on `RankedSolution`

Added `is_plausible: bool = Field(default=True, ...)` to the Pydantic v2 `RankedSolution` model in `src/lucy_ng/ranking/models.py`. Default `True` ensures backward compatibility — all existing code constructing `RankedSolution` without this field continues to work unchanged.

### Task 2: `_is_chemically_plausible()` helper + pre-filter in `rank()`

Three additions to `src/lucy_ng/ranking/ranker.py`:

**Module-level helpers (before `SolutionRanker` class):**
- `_calc_dbe_from_formula(formula: str) -> float`: Computes DBE = (2C+2+N-H-X)/2 using `parse_molecular_formula()` from `lucy_ng.lsd.generator`.
- `_calc_dbe_from_mol(mol: Chem.Mol) -> float`: Computes DBE via `rdMolDescriptors.CalcMolFormula()` → `_calc_dbe_from_formula()`.
- `_is_chemically_plausible(solution, experimental_shifts, formula=None) -> bool`: Check 1 — aromatic ring required when >= 4 shifts in 110-160 ppm (only when SMILES is parseable by RDKit). Check 2 — DBE deviation > 1 marks implausible (optional, only when formula provided and mol parseable).

**`rank()` signature change:** Added `formula: str | None = None` optional kwarg (backward compatible).

**Pre-filter partition (replacing single sort line):**
```
plausible = [r for r in ranked if _is_chemically_plausible(r, experimental_shifts, formula)]
implausible = [r for r in ranked if not ...]
plausible.sort(key=lambda r: (-r.matched_count, r.mae))
ranked = plausible + [r.model_copy(update={"is_plausible": False}) for r in implausible]
```

**Updated warning text:** Changed "4J HMBC artifact — consider removing HMBC correlations" to "Consider ELIM escalation (D-02)" per D-04 (post-hoc framing only, no removal advice).

## Task Commits

| Task | Description | Commit |
|---|---|---|
| 1 | `is_plausible` field on `RankedSolution` | a30ef71 |
| 2 | `_is_chemically_plausible()` + pre-filter in `rank()` + test fixes | 4786f8d |

## Verification Results

```
TestPlausibilityFilter::test_non_aromatic_rejected_when_aromatic_expected   PASSED
TestPlausibilityFilter::test_aromatic_retained_when_aromatic_expected       PASSED
TestPlausibilityFilter::test_non_aromatic_ok_when_no_aromatic_shifts        PASSED
TestPlausibilityFilterOrdering::test_plausible_ranks_above_implausible      PASSED
TestPlausibilityFilterOrdering::test_survivor_ordering_preserved            PASSED
tests/test_ranking.py (39 total)                                            PASSED
tests/test_validation_ranking.py (17 total)                                 PASSED
Full suite (excl. 80-01 schema files): 924 passed, 14 skipped, 1 xfailed
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wave-0 TestPlausibilityFilterOrdering used invalid placeholder SMILES**
- **Found during:** Task 2 implementation
- **Issue:** The Wave-0 RED tests used `"AROMATIC"` and `"NON_AROMATIC"` as literal SMILES strings. `Chem.MolFromSmiles("AROMATIC")` returns `None`, so `has_aromatic_ring` was `False` for both — both marked implausible, ordering undefined. Tests could not pass with any correct implementation.
- **Fix:** Replaced with real parseable SMILES: `"c1ccccc1C"` (toluene, has aromatic ring) and `"C1CCCCC1C"` (methylcyclohexane, no ring). Updated mock dispatch conditions to match. The test behavior and intent are preserved verbatim.
- **Files modified:** `tests/test_ranking.py`
- **Commit:** 4786f8d

**2. [Rule 1 - Bug] TestTwoTierRanking::test_hallucination_prevention_ibuprofen_style used invalid SMILES**
- **Found during:** Task 2 regression check
- **Issue:** Pre-existing test `test_hallucination_prevention_ibuprofen_style` used `"WRONG"` and `"CORRECT"` as SMILES. Once the plausibility pre-filter activated (4 aromatic shifts in experimental), both were marked implausible. Implausible list preserves input order → "WRONG" first, test expects "CORRECT" first.
- **Fix:** Replaced with real aromatic SMILES (bis-isobutylbenzene and ibuprofen isomer). Both pass the aromatic filter; match-count vs MAE two-tier contract tested as originally intended.
- **Files modified:** `tests/test_ranking.py`
- **Commit:** 4786f8d

**3. [Rule 1 - Bug] TestAromaticSanityCheck::test_warning_when_aromatic_expected_but_no_solutions_aromatic text changed**
- **Found during:** Task 2 regression check
- **Issue:** Test asserted `"4J HMBC" in result.warnings[0]`. Warning text updated per D-04 (no 4J removal advice) — removed "4J HMBC artifact" phrasing.
- **Fix:** Updated test assertion to check `"ELIM" in result.warnings[0]` instead.
- **Files modified:** `tests/test_ranking.py`
- **Commit:** 4786f8d

**4. [Rule 1 - Bug] test_validation_ranking.py::test_ibuprofen_scenario_complete_coverage_wins used invalid SMILES**
- **Found during:** Task 2 regression check (full suite run)
- **Issue:** Same invalid-SMILES problem — `"WRONG_CYCLOHEXADIENE"` and `"CORRECT_IBUPROFEN"` are not valid SMILES. Plausibility filter marked both implausible; order reversed from expectation.
- **Fix:** Replaced with real aromatic SMILES. Test intent (match-count beats MAE in two-tier ranking) fully preserved.
- **Files modified:** `tests/test_validation_ranking.py`
- **Commit:** 4786f8d

## Known Stubs

None. All production code is wired. The `formula` kwarg to `rank()` defaults to `None` (DBE check skipped) — this is intentional design (optional enhancement, not a stub).

## Threat Flags

None. This plan modifies pure Python ranking logic on already-parsed RDKit mol objects. No trust boundaries crossed.

## TDD Gate Compliance

GREEN gate satisfied: all 5 new test methods in `TestPlausibilityFilter` and `TestPlausibilityFilterOrdering` pass. RED gate was established in Wave 0 (plan 80-00, commit af970a4).

## Self-Check: PASSED

Files verified present:
- /Users/steinbeck/Dropbox/develop/lucy-ng/.claude/worktrees/agent-a63f091b1104201ba/src/lucy_ng/ranking/models.py contains `is_plausible`
- /Users/steinbeck/Dropbox/develop/lucy-ng/.claude/worktrees/agent-a63f091b1104201ba/src/lucy_ng/ranking/ranker.py contains `_is_chemically_plausible`

Commits verified:
- a30ef71 present in git log
- 4786f8d present in git log

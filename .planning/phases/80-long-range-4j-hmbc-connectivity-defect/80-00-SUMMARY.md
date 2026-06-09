---
phase: 80-long-range-4j-hmbc-connectivity-defect
plan: "00"
subsystem: tests
tags: [tdd, red-baseline, wave-0, lsd-generator, ranking, schema]
dependency_graph:
  requires: []
  provides:
    - tests/test_lsd_generator.py::TestElimBudget
    - tests/test_ranking.py::TestPlausibilityFilter
    - tests/test_ranking.py::TestPlausibilityFilterOrdering
    - tests/test_inventory_schema.py::TestSchemaV2Phase80
  affects:
    - Wave 1 plans 80-01 and 80-02 (implement against these test contracts)
tech_stack:
  added: []
  patterns:
    - LSDProblem constructor with scalar field (elim_budget)
    - MagicMock(spec=C13Predictor) + rank() call + is_plausible assertion
    - Draft202012Validator + _load_schema() + _minimal_valid_v2() + del field
key_files:
  created: []
  modified:
    - tests/test_lsd_generator.py
    - tests/test_ranking.py
    - tests/test_inventory_schema.py
decisions:
  - TDD RED baseline: all 17 new test methods fail before any production code
  - Exact class and method names from 80-PATTERNS.md used verbatim
  - No new imports added to any test file; all needed symbols already imported
metrics:
  duration: "~8 minutes"
  completed: "2026-06-09"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 3
---

# Phase 80 Plan 00: TDD RED Baseline for 4J-HMBC Fix Summary

Wave 0 foundation complete: three test files extended with four failing test classes that define the contract for Wave 1 implementation plans (80-01 and 80-02).

## What Was Built

Appended four new test classes establishing the RED baseline for FIX-07-A through FIX-07-E:

| Test Class | File | Methods | Failure Mode |
|---|---|---|---|
| TestElimBudget | test_lsd_generator.py | 6 | TypeError: unexpected keyword `elim_budget` |
| TestPlausibilityFilter | test_ranking.py | 3 | AttributeError: `is_plausible` not on RankedSolution |
| TestPlausibilityFilterOrdering | test_ranking.py | 2 | AttributeError: `is_plausible` not on RankedSolution |
| TestSchemaV2Phase80 | test_inventory_schema.py | 6 | AssertionError: retired fields still in schema required |

**Total:** 17 new failing test methods; 145 pre-existing tests unchanged and passing.

## Task Commits

| Task | Description | Commit |
|---|---|---|
| 1 | TestElimBudget (6 methods) appended to test_lsd_generator.py | 7cab164 |
| 2 | TestPlausibilityFilter + TestPlausibilityFilterOrdering appended to test_ranking.py | af970a4 |
| 3 | TestSchemaV2Phase80 (6 methods) appended to test_inventory_schema.py | 91b173f |

## Verification Results

```
TestElimBudget::test_elim_budget_zero_emits_no_elim        FAILED (TypeError)
TestPlausibilityFilter::test_non_aromatic_rejected...      FAILED (AttributeError)
TestPlausibilityFilterOrdering::test_plausible_ranks...    FAILED (AttributeError)
TestSchemaV2Phase80::test_accepts_inventory_without...     FAILED (AssertionError)
145 pre-existing tests                                     PASSED
```

RED baseline confirmed. Wave 1 plans can now implement against this test contract.

## Deviations from Plan

None — plan executed exactly as written. Test classes copied verbatim from 80-PATTERNS.md.

## Known Stubs

None. This plan writes test stubs only; no production code stubs were introduced.

## Threat Flags

None. Test files only — no trust boundaries affected.

## TDD Gate Compliance

This is a RED-only plan (Wave 0). RED gate satisfied: all 17 new test methods fail/error before any implementation. GREEN gate is the responsibility of plans 80-01 and 80-02.

## Self-Check: PASSED

Files verified:
- tests/test_lsd_generator.py contains `class TestElimBudget` at line 1031
- tests/test_ranking.py contains `class TestPlausibilityFilter` and `class TestPlausibilityFilterOrdering`
- tests/test_inventory_schema.py contains `class TestSchemaV2Phase80`

Commits verified in git log: 7cab164, af970a4, 91b173f all present on worktree-agent-afcd852fd208692f3.

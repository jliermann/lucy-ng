---
phase: 83-constraint-hardness-guard
plan: "02"
subsystem: detection
tags: [advisory, fix-10, neighbour-detection, pydantic, computed-field, regression-test]
dependency_graph:
  requires: []
  provides: [advisory-field-on-NeighbourResult, dominant_element-computed-field, CASE9-truth-not-excluded-test]
  affects: [lucy-detect-neighbours-json-output, lucy-detect-neighbours-text-output, lsd-engineer-constraint-hardness-guard]
tech_stack:
  added: []
  patterns: [pydantic-computed-field, advisory-self-labeling, rdkit-structural-assertion]
key_files:
  created: []
  modified:
    - src/lucy_ng/detection/models.py
    - src/lucy_ng/cli/detect.py
    - tests/test_detection_neighbours.py
decisions:
  - "dominant_element implemented as @computed_field on NeighbourResult delegating to NeighbourDistribution.dominant_element property (stays in sync automatically, no change to detector.py)"
  - "type: ignore[prop-decorator] used for @computed_field (mypy v1.x requires this for @property-based computed fields)"
  - "test_agent_file_exists failure confirmed pre-existing (~/.claude/agents/lucy-case-agent.md absent in worktree env)"
metrics:
  duration: "387s"
  completed: "2026-06-10T16:36:20Z"
  tasks_completed: 2
  files_modified: 3
---

# Phase 83 Plan 02: Advisory Fields and CASE9-Truth-Not-Excluded Regression Tests Summary

Advisory self-labeling added to NeighbourResult model: advisory/advisory_note/dominant_element fields expose FIX-10 constraint-hardness status in both JSON and text output; six regression tests including CASE9 structural RDKit assertion.

## What Was Built

### Task 1: Model changes + CLI docstring

**`src/lucy_ng/detection/models.py`**

Added to `NeighbourDistribution`:
- `dominant_element` property — returns the element name with highest frequency among carbon/oxygen/nitrogen/sulfur/halogen, or `None` if all zero.

Changed import to `from pydantic import BaseModel, computed_field`.

Added to `NeighbourResult`:
- `advisory: bool = True` — plain field with default; existing construction sites unaffected.
- `advisory_note: str` — contains the FIX-10 advisory text: "statistical prior — do not encode as a hard LSD constraint without direct connectivity evidence (HMBC/HSQC/exchangeable-H) or convergent multi-source corroboration. See FIX-10."
- `dominant_element` — `@computed_field` / `@property` delegating to `self.distribution.dominant_element`.

Updated `NeighbourResult.summary()`:
- First line is now `[ADVISORY] {advisory_note}`.
- When `dominant_element == "carbon"`, appends "Dominant neighbour: carbon — likely carbon-substituted; heteroatom placement uncertain at this shift."
- When `dominant_element` is non-None and not carbon, appends "Dominant neighbour: {element}".

**`src/lucy_ng/cli/detect.py`**

Added advisory paragraph to `neighbours_command` docstring noting statistical-prior nature, dominant_element check in JSON, and FIX-10 reference.

### Task 2: Regression tests

Six new tests added to `tests/test_detection_neighbours.py`:

| Test | ID | What it verifies |
|------|----|-----------------|
| `test_neighbour_result_advisory_default` | A | advisory=True, "statistical prior" and "FIX-10" in advisory_note |
| `test_neighbour_result_summary_advisory_prefix` | B | summary() starts with "[ADVISORY]" |
| `test_dominant_element_carbon` | C | carbon=0.95, oxygen=0.55 → dominant_element="carbon" |
| `test_dominant_element_oxygen` | D | carbon=0.30, oxygen=0.97 → dominant_element="oxygen" |
| `test_detect_neighbours_json_advisory_and_dominant_element` | E | CLI JSON has advisory=true, dominant_element, advisory_note with "statistical prior" |
| `test_case9_truth_not_excluded_by_fix10_conformant_constraints` | F | RDKit: truth parses, formula=C12H16O3, 0 ring-O, >=1 aromatic C with aliphatic C substituent |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mypy type annotation errors in model changes**
- **Found during:** Task 1 verification
- **Issue:** `type: ignore[misc]` on @computed_field (mypy wants `[prop-decorator]`); `lines = []` needed `list[str]` annotation.
- **Fix:** Changed to `type: ignore[prop-decorator]`; added `lines: list[str] = []` annotation.
- **Files modified:** `src/lucy_ng/detection/models.py`
- **Commit:** 491ea52

**2. [Rule 1 - Bug] Fixed ruff E501 line-too-long in test docstrings**
- **Found during:** Task 2 verification
- **Issue:** Two test docstrings exceeded 100-char line limit.
- **Fix:** Shortened docstring first lines to stay within limit.
- **Files modified:** `tests/test_detection_neighbours.py`
- **Commit:** 9b2f75c

None of the deviations were architectural.

## Pre-existing Issues (out of scope, not fixed)

- `tests/test_validation_ranking.py::TestBadlistPatterns::test_agent_file_exists` — FAILS because `~/.claude/agents/lucy-case-agent.md` is absent in the worktree environment. This file test was failing before our changes; we made no changes to `test_validation_ranking.py`.
- 111 mypy errors across 28 files (all pre-existing in non-touched files).
- `src/lucy_ng/__init__.py` ruff I001 (import sort) — pre-existing.

## Quality Gates

| Gate | Result |
|------|--------|
| `pytest tests/test_detection_neighbours.py` | 22 passed (16 original + 6 new) |
| `pytest` (full suite, excl pre-existing) | 1059 passed, 0 regressions |
| `ruff check src/lucy_ng/detection/models.py src/lucy_ng/cli/detect.py tests/test_detection_neighbours.py` | All checks passed |
| `mypy src/lucy_ng/detection/models.py` | Success: no issues found |

## Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 | 491ea52 | feat(83-02): add advisory, advisory_note, dominant_element to NeighbourResult |
| Task 2 | 9b2f75c | test(83-02): add advisory/dominant_element regression tests + CASE9-truth-not-excluded |

## Self-Check: PASSED

Files exist:
- `src/lucy_ng/detection/models.py` — FOUND (modified)
- `src/lucy_ng/cli/detect.py` — FOUND (modified)
- `tests/test_detection_neighbours.py` — FOUND (modified)

Commits exist:
- 491ea52 — feat(83-02): confirmed
- 9b2f75c — test(83-02): confirmed

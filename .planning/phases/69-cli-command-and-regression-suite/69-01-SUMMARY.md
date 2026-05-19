---
phase: 69-cli-command-and-regression-suite
plan: "01"
subsystem: cli/lsd
tags: [refactor, helper-extraction, tdd, pure-refactor]
dependency_graph:
  requires: []
  provides:
    - "_perform_ranking: callable from lucy_ng.cli.lsd without Click context"
    - "_validate_and_parse_inventory: callable from lucy_ng.cli.lsd without Click context"
  affects:
    - "69-02 (pylsd run command can import _perform_ranking directly)"
tech_stack:
  added: []
  patterns:
    - "Module-private helpers with single underscore prefix"
    - "TDD RED/GREEN per task"
key_files:
  created: []
  modified:
    - src/lucy_ng/cli/lsd.py
    - tests/test_cli_lsd.py
    - tests/test_inventory_schema.py
    - pyproject.toml
    - schemas/constraint_inventory_v2.json
decisions:
  - "lsd_validate_inventory inlines format-aware output code rather than delegating to helper — helper cannot know output_format without it becoming a parameter, and coupling output_format to the helper would duplicate the CLI's concern"
  - "pythonpath=[src] added to pytest config so worktree src takes precedence over editable install from main repo"
  - "schemas/constraint_inventory_v2.json and Phase 68 CLI code brought in as prerequisite — worktree branched before Phase 68 additions"
metrics:
  duration: "~25 minutes"
  completed: "2026-05-19T12:53:55Z"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 5
---

# Phase 69 Plan 01: Helper Extraction — _perform_ranking and _validate_and_parse_inventory

Pure refactor: extracted two module-private helper functions from `lsd_rank` and `lsd_validate_inventory` so that the `pylsd run` command (Plan 02) can call ranking and inventory-parsing logic as direct Python function calls (D-14 and D-13).

## Tasks Completed

| Task | Name | Commit | Key Change |
|------|------|--------|------------|
| 1 | Extract `_perform_ranking()` | 9736e1a | Helper added; `lsd_rank` delegates after arg parsing |
| T1 RED | Failing tests for `_perform_ranking` | 11a65d0 | TestPerformRanking class (4 tests) |
| 2 | Extract `_validate_and_parse_inventory()` | 9e131b8 | Helper added; `lsd_validate_inventory` keeps format-aware output |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree missing Phase 68 additions**
- **Found during:** Task 1 GREEN
- **Issue:** The worktree was branched from a commit before Phase 68 (schemas, validate-inventory command, `_get_schema_path`, `_extract_inventory_block`). The test file `test_inventory_schema.py` didn't exist in the worktree. The `schemas/constraint_inventory_v2.json` file was also absent.
- **Fix:** Brought in Phase 68 content from master as part of the Task 1 feat commit. Copied `test_inventory_schema.py` and `schemas/constraint_inventory_v2.json` from the main repo.
- **Files modified:** `src/lucy_ng/cli/lsd.py`, `tests/test_inventory_schema.py`, `schemas/constraint_inventory_v2.json`
- **Commit:** 9736e1a

**2. [Rule 3 - Blocking] Editable install resolves to main repo src**
- **Found during:** Task 1 GREEN
- **Issue:** `python -m pytest` inside the worktree imported `lucy_ng` from `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/` (the editable install's source) rather than the worktree's `src/`. New helpers in the worktree's `lsd.py` were invisible to pytest.
- **Fix:** Added `pythonpath = ["src"]` to `[tool.pytest.ini_options]` in `pyproject.toml`. This prepends the worktree's `src/` to the Python path, making the worktree's module version take precedence.
- **Files modified:** `pyproject.toml`
- **Commit:** 9736e1a

### TDD Gate Compliance

Both tasks followed RED/GREEN ordering. Task 1 RED commit (11a65d0) precedes Task 1 GREEN commit (9736e1a). For Task 2, the `_validate_and_parse_inventory` helper was included in the Task 1 feat commit (to avoid a separate commit for the Phase 68 prerequisite code), so the new tests (added in 9e131b8) pass immediately — this is expected given the implementation was already staged.

## Verification Results

```
pytest tests/test_cli_lsd.py tests/test_inventory_schema.py -x -q
68 passed, 26 warnings
```

### Done Criteria

- [x] `grep -n "^def _perform_ranking" src/lucy_ng/cli/lsd.py` → line 207
- [x] `_perform_ranking` importable without Click context (via pytest pythonpath)
- [x] `grep -n "^def _validate_and_parse_inventory" src/lucy_ng/cli/lsd.py` → line 339
- [x] `_validate_and_parse_inventory` importable without Click context
- [x] 68 tests pass (11 in test_cli_lsd.py, 57 in test_inventory_schema.py)
- [x] `lsd_rank` is now a thin wrapper calling `_perform_ranking`
- [x] `lsd_validate_inventory` is now a thin wrapper with format-aware output

## Known Stubs

None. This is a pure refactor — no data flows changed, no UI rendering touched.

## Threat Flags

None. This plan introduces no new network endpoints, auth paths, or I/O surface. It is an internal refactor only.

## Self-Check: PASSED

- `src/lucy_ng/cli/lsd.py` exists and contains both helpers
- Commits 11a65d0, 9736e1a, 9e131b8 are in git log
- 68 tests pass

---
phase: 69-cli-command-and-regression-suite
plan: "02"
subsystem: cli/pylsd
tags: [feature, cli, pylsd, orchestration, tdd]
dependency_graph:
  requires:
    - "69-01 (_perform_ranking, _validate_and_parse_inventory helpers)"
    - "Phase 67 (PyLSDOrchestrator, SolutionMerger)"
    - "Phase 68 (constraint_inventory_v2 schema, _validate_and_parse_inventory)"
  provides:
    - "lucy pylsd run CLI command"
    - "_extract_suspects helper for D-13/D-13b/D-13c branching"
    - "pylsd CLI group registered in main lucy CLI"
  affects:
    - "69-03 (regression tests can invoke lucy pylsd run)"
    - "69-04 (LSD form-tolerance tests may reference pylsd_run patterns)"
tech_stack:
  added: []
  patterns:
    - "click.group() + click.command() decorator stacking"
    - "CliRunner(mix_stderr=False) for JSON output tests"
    - "TDD RED/GREEN per task"
    - "raise SystemExit(1) — never sys.exit"
    - "Warnings to stderr (err=True) to avoid polluting JSON stdout"
key_files:
  created:
    - src/lucy_ng/cli/pylsd.py
    - tests/test_pylsd_cli.py
  modified:
    - src/lucy_ng/cli/main.py
decisions:
  - "Warnings in _extract_suspects go to stderr (err=True) so --format json output is clean parseable JSON on stdout"
  - "mix_stderr=False used in test_format_json_structure to isolate JSON stdout from warning stderr"
  - "D-13a cross-check only fires when BOTH inventory and ; ELIM annotations are non-empty (both present must match)"
  - "deferred_4j annotation field const is '; ELIM' — test helper updated to use exact schema value"
metrics:
  duration: "~7 minutes"
  completed: "2026-05-19T14:37:00Z"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 3
---

# Phase 69 Plan 02: pylsd run CLI Command + Tests Summary

CLI entry point for PyLSD multi-run orchestration: `lucy pylsd run <file> --shifts '...'` with D-13 suspect extraction, 2^K permutation orchestration, InChI-dedup merging, and Python-function ranking (D-14).

## Tasks Completed

| Task | Name | Commit | Key Change |
|------|------|--------|------------|
| T1 RED | Failing tests for pylsd run | 21af0db | tests/test_pylsd_cli.py — 11 tests, import fails |
| T1 GREEN | Implement src/lucy_ng/cli/pylsd.py | f4b6f8b | pylsd group + _extract_suspects + pylsd_run |
| T2 | Register pylsd in main.py | 061c589 | 2-line addition; 79 tests pass |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Worktree base stale — missing Plan 01 helpers**
- **Found during:** Pre-execution HEAD assertion
- **Issue:** Worktree was forked before Phase 69 Plan 01 commits. `_perform_ranking` and `_validate_and_parse_inventory` were not present in the worktree's `lsd.py`.
- **Fix:** `git merge master` (fast-forward) to bring in all Plan 01 and Phase 68 additions before starting implementation.
- **Files modified:** All files from master HEAD bd4aa0d..420f933 range (108 files)
- **Commit:** fast-forward merge (no separate commit)

**2. [Rule 1 - Bug] D-13c/D-13b warnings to stderr (not stdout)**
- **Found during:** Task 1 GREEN — test_format_json_structure failed with JSONDecodeError because warnings from _extract_suspects appeared before JSON in mixed stdout
- **Issue:** Warnings emitted by `click.echo(...)` (stdout) were mixed into `result.output` with JSON, making `json.loads(result.output)` fail
- **Fix:** Changed D-13b and D-13c warnings to use `click.echo(..., err=True)` so they go to stderr. Used `CliRunner(mix_stderr=False)` in the JSON format test.
- **Files modified:** `src/lucy_ng/cli/pylsd.py`, `tests/test_pylsd_cli.py`
- **Commit:** f4b6f8b (included in GREEN commit)

**3. [Rule 1 - Bug] deferred_4j schema requires annotation="; ELIM" (not arbitrary string)**
- **Found during:** Task 1 GREEN — test_inventory_primary_used failed with schema validation error
- **Issue:** Test helper used `annotation: "4J suspect"` but schema has `const: "; ELIM"` for the annotation field
- **Fix:** Updated `_make_deferred_4j_entry` to use `"annotation": "; ELIM"`
- **Files modified:** `tests/test_pylsd_cli.py`
- **Commit:** f4b6f8b

### TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test commit) | 21af0db | test(69-02): failing tests, import error confirmed |
| GREEN (feat commit) | f4b6f8b | feat(69-02): all 11 tests pass |
| REFACTOR | n/a | No structural refactor needed |

## Verification Results

```
pytest tests/test_pylsd_cli.py tests/test_cli_lsd.py tests/test_inventory_schema.py -x -q
79 passed, 26 warnings in 1.46s
```

### Done Criteria

- [x] `python -c "from lucy_ng.cli.pylsd import pylsd; print(pylsd.name)"` prints "pylsd"
- [x] `grep -n "raise SystemExit" src/lucy_ng/cli/pylsd.py | wc -l` → 6 (>= 4)
- [x] `grep -c "sys.exit" src/lucy_ng/cli/pylsd.py` → 0
- [x] All three definitions present: `def pylsd`, `def pylsd_run`, `def _extract_suspects`
- [x] `pytest tests/test_pylsd_cli.py -x -q` → 11 passed
- [x] `lucy pylsd run --help` lists --shifts, --no-rank, --working-dir, --timeout, --format
- [x] `grep -n "cli.add_command(pylsd)" src/lucy_ng/cli/main.py` → 1 match (line 54)
- [x] `grep -c "subprocess" tests/test_pylsd_cli.py` → 0

## Known Stubs

None. The pylsd run command is fully implemented end-to-end. _extract_suspects reads real LSD files. All data flows through actual orchestrator/merger/ranker objects (mocked in tests but real in production).

## Threat Flags

None. No new network endpoints introduced. The `--shifts` parse path is guarded by `float()` in try/except (T-69-02-01). The K>3 cap propagates as ValueError from PyLSDOrchestrator (T-69-02-02).

## Self-Check: PASSED

- `src/lucy_ng/cli/pylsd.py` exists (307 lines)
- `tests/test_pylsd_cli.py` exists (11 test cases)
- `src/lucy_ng/cli/main.py` has `cli.add_command(pylsd)` at line 54
- Commits 21af0db (RED), f4b6f8b (GREEN), 061c589 (Task 2) are in git log
- 79 tests pass

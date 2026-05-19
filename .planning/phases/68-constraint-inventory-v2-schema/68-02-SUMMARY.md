---
phase: 68-constraint-inventory-v2-schema
plan: "02"
subsystem: constraint-inventory
tags: [cli, jsonschema, validation, click, testing, tdd]
dependency_graph:
  requires:
    - schemas/constraint_inventory_v2.json (Plan 68-01)
    - jsonschema>=4.18.0 in pyproject.toml (Plan 68-01)
    - tests/test_inventory_schema.py (Plan 68-01)
  provides:
    - src/lucy_ng/cli/lsd.py (validate-inventory subcommand)
    - tests/test_inventory_schema.py (TestValidateInventoryCLI, TestGateLogic classes)
  affects:
    - Plan 68-03/04 (skill docs reference this CLI command via D-12)
tech_stack:
  added:
    - jsonschema.Draft202012Validator (runtime use in CLI)
  patterns:
    - Click subcommand with @lsd.command("validate-inventory")
    - Package-relative path resolution via Path(lucy_ng.__file__).parent.parent.parent
    - CliRunner integration tests (click.testing)
    - TDD RED/GREEN with CliRunner-based test first
key_files:
  created: []
  modified:
    - src/lucy_ng/cli/lsd.py
    - tests/test_inventory_schema.py
decisions:
  - "validate-inventory uses raise SystemExit(1) not sys.exit(1) — consistent with rest of lsd.py"
  - "_get_schema_path() navigates src/lucy_ng -> src -> repo_root to avoid CWD-relative failures (Pitfall 2 avoidance)"
  - "v1 block detection runs before _extract_inventory_block() call — clean separation of legacy and missing block error paths"
  - "TDD: RED commit first (CliRunner tests fail with exit_code=2 = unknown subcommand), GREEN commit adds implementation"
  - "catch_exceptions=False in valid-path tests to surface real exceptions; default (True) in error-path tests to inspect exit codes"
metrics:
  duration: 285s
  completed: "2026-05-19T10:18:54Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 2
  tests_added: 9
  tests_total_after: 934
requirements_met:
  - INPUT-05
---

# Phase 68 Plan 02: validate-inventory CLI Subcommand — Summary

lucy lsd validate-inventory subcommand added to src/lucy_ng/cli/lsd.py with package-relative schema loading; 9 new CLI and gate logic tests extend tests/test_inventory_schema.py.

## What Was Built

### src/lucy_ng/cli/lsd.py — three additions

**_get_schema_path() -> Path**

Private helper that resolves `schemas/constraint_inventory_v2.json` by navigating from `lucy_ng.__file__` (src/lucy_ng) up two levels to the repo root. Raises `FileNotFoundError` with diagnostic message if schema not found. This avoids CWD-relative path failures when the CLI is called from `analysis/iteration_NN/` subdirectories (Pitfall 2 from RESEARCH.md).

**_extract_inventory_block(content: str) -> str | None**

Private helper that extracts JSON text from between `=== CONSTRAINT INVENTORY v2 ===` and `=== END CONSTRAINT INVENTORY ===` delimiters. Strips the `; ` 2-character prefix from each block line. Bare `;` lines become empty strings. Returns None if no v2 block found.

**@lsd.command("validate-inventory")**

Click subcommand registered on the existing `lsd` group. Arguments: `lsd_file` (click.Path(exists=True)), `--format`/`output_format` (text|json, default text). Logic flow:

1. v1 block detection: if `=== CONSTRAINT INVENTORY v1 ===` in content → emit legacy error message → exit 1
2. v2 block extraction: if `_extract_inventory_block()` returns None → emit "no block found" error → exit 1
3. JSON parse: `json.loads()` in try/except JSONDecodeError → exit 1 on failure
4. Schema validation: `jsonschema.Draft202012Validator(schema).iter_errors(instance)` → collect all errors
5. Output: valid → exit 0; invalid → emit errors → exit 1

JSON output contract:
- Valid: `{"valid": true, "file": "<path>", "version": 2}`
- Invalid: `{"valid": false, "file": "<path>", "errors": [{"message": ..., "path": [...], "validator": ...}]}`
- v1 block: `{"valid": false, "file": "<path>", "errors": [{"message": "Legacy v1 inventory detected — upgrade to v2 format", "validator": "version"}]}`

### tests/test_inventory_schema.py — two new classes (9 tests)

**TestValidateInventoryCLI** (6 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| test_valid_v2_file_exits_0 | Valid v2 LSD file | exit 0 |
| test_valid_v2_file_format_json | Valid v2 + --format json | exit 0, valid:true |
| test_v1_block_exits_1 | v1 delimiter | exit 1 |
| test_v1_block_format_json_legacy_message | v1 + --format json | exit 1, "Legacy v1 inventory detected" |
| test_no_inventory_block_exits_1 | No block at all | exit 1 |
| test_invalid_schema_exits_1 | v2 block with version:1 | exit 1 |

**TestGateLogic** (3 tests)

| Test | Pattern | Input | Expected |
|------|---------|-------|----------|
| test_g2_bare_elim_detected | `^ELIM` | `ELIM 4 4` | match |
| test_g2_hmbc_elim_annotation_not_matched | `^ELIM` | `HMBC 4 8 2 4 ; ELIM` | no match |
| test_g2_comment_line_not_matched | `^ELIM` | `; ELIM` | no match |

Helper functions added: `_make_v2_lsd_content()`, `_minimal_v2_inventory_json()`.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 2 (TDD RED) | 95f7370 | test(68-02): add failing CLI and gate logic tests for validate-inventory |
| Task 1 (TDD GREEN) | 3ec334a | feat(68-02): add validate-inventory subcommand to lucy lsd CLI |

## Verification Results

1. `python -c "from lucy_ng.cli.lsd import lsd_validate_inventory; print('ok')"` — PASSED (with PYTHONPATH)
2. `lucy lsd --help | grep validate-inventory` — PASSED (shows command in group)
3. `pytest tests/test_inventory_schema.py -x` — 34 passed (25 from Plan 01 + 9 new)
4. `pytest` (full suite) — 933 passed, 14 skipped, 0 failures (with PYTHONPATH)

**Note on test execution context:** The editable install `.pth` file points to the main repo `src/`. Tests must be run with `PYTHONPATH` set to the worktree's `src/` to pick up the new implementation, or will pass automatically after the worktree is merged into master.

## Deviations from Plan

### Auto-fixed Issues

**[Rule 3 - Blocking] Merged master into worktree branch**

- **Found during:** Task setup
- **Issue:** Worktree branch `worktree-agent-a414cf30bbc03b615` was 10 commits behind master; `schemas/constraint_inventory_v2.json` and `tests/test_inventory_schema.py` from Plan 01 were not present in the worktree.
- **Fix:** `git merge master --no-edit` (fast-forward; no conflicts). The missing artifacts are now present.
- **Files affected:** All Plan 01 artifacts now visible in worktree.

## TDD Gate Compliance

RED gate commit: 95f7370 (test(68-02): add failing CLI and gate logic tests)
GREEN gate commit: 3ec334a (feat(68-02): add validate-inventory subcommand to lucy lsd CLI)

Both gates satisfied. Tests failed correctly in RED (exit_code=2, unknown subcommand) before implementation was added.

## Known Stubs

None. The validate-inventory command is fully wired to the schema file and produces complete JSON output.

## Threat Flags

None. All identified threats are mitigated:
- T-68-03: `click.Path(exists=True)` validates file path at CLI layer; schema uses package-relative absolute path
- T-68-04: `json.loads()` wrapped in try/except JSONDecodeError

## Self-Check: PASSED

- `src/lucy_ng/cli/lsd.py` contains `validate-inventory` — FOUND (line 142)
- `tests/test_inventory_schema.py` contains `TestValidateInventoryCLI` — FOUND (line 386)
- `tests/test_inventory_schema.py` contains `TestGateLogic` — FOUND (line 463)
- Commit 95f7370 (RED) — FOUND
- Commit 3ec334a (GREEN) — FOUND
- 34 tests in test_inventory_schema.py — CONFIRMED

---
phase: 68-constraint-inventory-v2-schema
fixed_at: 2026-05-19T16:00:00Z
review_path: .planning/phases/68-constraint-inventory-v2-schema/68-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 68: Code Review Fix Report

**Fixed at:** 2026-05-19T16:00:00Z
**Source review:** .planning/phases/68-constraint-inventory-v2-schema/68-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 8 (CR-01, CR-02, CR-03, WR-01, WR-02, WR-03, WR-04, WR-05)
- Fixed: 8
- Skipped: 0

## Fixed Issues

### CR-01: `_get_schema_path()` fails silently for non-editable pip installs

**Files modified:** `src/lucy_ng/cli/lsd.py`, `src/lucy_ng/data/__init__.py`, `src/lucy_ng/data/schemas/__init__.py`, `src/lucy_ng/data/schemas/constraint_inventory_v2.json`, `pyproject.toml`, `tests/test_inventory_schema.py`
**Commit:** 4c8ad8e
**Applied fix:** Copied `schemas/constraint_inventory_v2.json` into `src/lucy_ng/data/schemas/` so it ships in the wheel. Updated `_get_schema_path()` to check the bundled package location first (for pip installs), falling back to the repo-root `schemas/` directory for editable/development installs. Added `artifacts = ["src/lucy_ng/data/schemas/*"]` to `[tool.hatch.build.targets.wheel]` in `pyproject.toml`. Added `test_schema_readable_via_get_schema_path()` regression test.

### CR-02: `validate-inventory --format json` omits parsed inventory fields

**Files modified:** `src/lucy_ng/cli/lsd.py`, `tests/test_inventory_schema.py`
**Commit:** 7494aba
**Applied fix:** On valid v2 inventory, the JSON success response now includes `"inventory": instance` (the full parsed inventory object). The response shape is `{"valid": true, "file": "...", "version": 2, "inventory": {...}}`, giving the devils-advocate bash pipeline direct access to `pylsd_mode`, `elim_annotated`, and `deferred_4j`. Added two tests: `test_valid_v2_format_json_includes_inventory_key` and `test_valid_v2_format_json_inventory_values_correct`.

### CR-03: G3 grep `"; ELIM"` is unanchored — false positives from comment lines

**Files modified:** `tests/test_inventory_schema.py`; `/Users/steinbeck/.claude/agents/lucy-devils-advocate.md` (external, applied in-place)
**Commit:** 8c97fc9
**Applied fix:** Changed the G3 grep in `lucy-devils-advocate.md` from the unanchored `grep -c "; ELIM"` to the anchored `grep -cE "^HMBC.*; ELIM"`. Added an explanatory note mirroring G2's anchoring rationale. Added four G3 regex tests to `TestGateLogic` covering the fix and its complementary cases.

### WR-01: Schema cross-field invariants not enforced + WR-02: `hmbc_batches[].batch` missing `minimum: 1`

**Files modified:** `schemas/constraint_inventory_v2.json`, `src/lucy_ng/data/schemas/constraint_inventory_v2.json`, `tests/test_inventory_schema.py`
**Commit:** 358ef36
**Applied fix (WR-01):** Added `allOf` with two `if/then` clauses to the schema:
- G2 invariant: when `pylsd_mode: true`, `elim_value` must be `null` (bare ELIM forbidden in pylsd_mode).
- G3 invariant: when `elim_annotated: true`, `pylsd_mode` must be `true` and `deferred_4j` must have `minItems: 1`.
Added `TestSchemaInvariants` class with 6 tests covering all invariant cases.
**Applied fix (WR-02):** Added `"minimum": 1` to `hmbc_batches[].batch`, making it consistent with `iteration`, `atom1`, and `atom2` fields. Added `test_rejects_hmbc_batch_zero` and `test_wr02_hmbc_batch_number_minimum_1` regression tests.

### WR-03: `lsd-engineer` §5D missing `elim_annotated` in update procedure

**Files modified:** `/Users/steinbeck/.claude/agents/lucy-lsd-engineer.md` (external, applied in-place)
**Commit:** (agent file outside repository — applied in-place, no commit)
**Applied fix:** Added `elim_annotated` to the §5D "Update only these fields" list with the recomputation rule: "set to `true` if `len(deferred_4j) > 0` (after any additions or removals), `false` otherwise. Do not carry forward the previous value blindly." Also fixed the stale §2 "4J Deferral Rule" text that said "as string descriptions" — replaced with reference to the v2 schema object format documented in Section 5C step 5d.

### WR-04: `_extract_inventory_block` silently succeeds when END delimiter is missing

**Files modified:** `src/lucy_ng/cli/lsd.py`, `tests/test_inventory_schema.py`
**Commit:** 1aa6aeb
**Applied fix:** Added a `found_end` boolean; after the loop, if the block was entered but `found_end` is still `False`, return `None` instead of the partial content. This prevents `validate-inventory` from reporting "Valid" on a structurally corrupt LSD file. Added two regression tests: `test_missing_end_delimiter_exits_1` and `test_missing_end_delimiter_format_json_returns_error`.

### WR-05: `read_text()` not wrapped in try/except

**Files modified:** `src/lucy_ng/cli/lsd.py`, `tests/test_inventory_schema.py`
**Commit:** d6b9ea8
**Applied fix:** Wrapped `Path(lsd_file).read_text()` in `try/except (PermissionError, OSError)`. On error, emits clean JSON `{"valid": false, "errors": [{"message": "Cannot read file: ..."}]}` with exit 1. Added explicit `encoding="utf-8"` to avoid locale-dependent failures. Also removed unused `import pytest` (replaced by `from unittest.mock import patch`). Added two regression tests using `unittest.mock.patch` to simulate `PermissionError`.

---

## Test Suite Results

**Before fixes:** 34 passed
**After fixes:** 52 passed (18 new tests added)
**Regressions:** 0
**Full suite (951 tests):** 951 passed, 14 skipped, 0 failed

## New Test Classes Added

- `TestSchemaInvariants` (6 tests) — schema-level G2/G3 cross-field invariants

## Notes

- WR-03 changes are to `~/.claude/agents/lucy-lsd-engineer.md` (outside the git repository), applied in-place with no corresponding commit.
- CR-03 agent file change (`~/.claude/agents/lucy-devils-advocate.md`) is similarly outside the git repository, applied in-place. The corresponding worktree commit (8c97fc9) contains the regex tests that document the fix.
- `hatch build` + `unzip -l dist/*.whl | grep schemas/` will verify CR-01 packaging once hatch is available in the environment.

---

_Fixed: 2026-05-19T16:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_

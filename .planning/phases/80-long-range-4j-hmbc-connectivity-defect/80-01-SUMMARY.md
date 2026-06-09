---
phase: 80-long-range-4j-hmbc-connectivity-defect
plan: "01"
subsystem: lsd-generator, schema, cli
tags: [elim-budget, 4j-hmbc, pylsd-deprecation, schema-migration, tdd-green]

dependency_graph:
  requires: ["80-00"]
  provides: ["LSDProblem.elim_budget field", "ELIM N 0 emission independent of pylsd_mode", "schema v2 without retired pyLSD required fields", "elim_budget optional property in schema", "pylsd deprecation warning"]
  affects: ["src/lucy_ng/lsd/models.py", "src/lucy_ng/lsd/generator.py", "src/lucy_ng/data/schemas/constraint_inventory_v2.json", "schemas/constraint_inventory_v2.json", "src/lucy_ng/cli/pylsd.py", "tests/test_inventory_schema.py"]

tech_stack:
  added: []
  patterns:
    - "scalar field with default on dataclass (elim_budget: int = 0)"
    - "independent conditional block in generate() for ELIM emission"
    - "JSON schema optional property with minimum constraint"
    - "click.echo(..., err=True) deprecation warning as first statement"

key_files:
  created: []
  modified:
    - src/lucy_ng/lsd/models.py
    - src/lucy_ng/lsd/generator.py
    - src/lucy_ng/data/schemas/constraint_inventory_v2.json
    - schemas/constraint_inventory_v2.json
    - src/lucy_ng/cli/pylsd.py
    - tests/test_inventory_schema.py

decisions:
  - "Added elim_budget after elim_commands field in LSDProblem dataclass"
  - "New ELIM emission block placed AFTER existing pylsd_mode block — backward compatible, pylsd_mode path unchanged"
  - "Both schema copies (src/lucy_ng/data/schemas/ and schemas/ root) updated simultaneously"
  - "Updated 3 pre-existing tests that encoded old schema behavior to match Phase 80 reality (Rule 1)"

metrics:
  duration: "5m 33s"
  completed: "2026-06-09"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 6
---

# Phase 80 Plan 01: Python Mechanism Layer 1a — ELIM Budget + Schema Surgery Summary

**One-liner:** Added `LSDProblem.elim_budget` field + independent ELIM N 0 emission in generator; retired `pylsd_mode`/`elim_annotated`/`deferred_4j` from schema required[]; added `elim_budget` optional property; added D-05 deprecation warning to `lucy pylsd run`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add elim_budget field to LSDProblem + decouple ELIM emission | 22287d6 | src/lucy_ng/lsd/models.py, src/lucy_ng/lsd/generator.py |
| 2 | Schema surgery + pyLSD deprecation warning | 205ba7f | src/lucy_ng/data/schemas/constraint_inventory_v2.json, schemas/constraint_inventory_v2.json, src/lucy_ng/cli/pylsd.py, tests/test_inventory_schema.py |

## Test Results

- **TestElimBudget (6/6 GREEN):** All elim_budget field + ELIM emission tests pass
- **TestSchemaV2Phase80 (6/6 GREEN):** All schema migration tests pass
- **Full suite:** 1043 passed, 14 skipped, 1 xfailed, 4 failing in test_ranking.py (pre-existing RED from Wave 0, plan 80-02's responsibility)

## Implementation Details

### Task 1 — elim_budget field + generator decoupling

`LSDProblem.elim_budget: int = 0` added after `elim_commands` field (line 186 of models.py). No `field()` wrapper needed — plain scalar default matching `ring_exclusion_enabled` pattern.

In `generator.py`, a new independent block was added AFTER the existing `pylsd_mode` block and BEFORE the MULT section:
```python
# Global ELIM budget (Phase 80 D-01/D-02: primary 4J mechanism)
if problem.elim_budget > 0:
    lines.append(LSDInputGenerator.emit_elim(problem.elim_budget, 0))
    lines.append("")
```

The existing `pylsd_mode` gate was intentionally NOT modified — backward compatible. The `elim_budget` path is entirely independent.

### Task 2 — Schema surgery

Removed `"pylsd_mode"`, `"elim_annotated"`, `"deferred_4j"` from `"required"` array in both schema copies (`src/lucy_ng/data/schemas/` and root `schemas/`). The three fields remain in `"properties"` as optional (backward compatibility with existing CASE1/CASE9 LSD files that have `deferred_4j: []`).

Added new optional property:
```json
"elim_budget": {
  "type": "integer",
  "minimum": 0,
  "default": 0,
  "description": "Global ELIM N value (Phase 80 D-02). 0 = no ELIM. ..."
}
```

The G2 and G3 `allOf` invariants were left in place — they are vacuously true since `pylsd_mode` is never `true` in new files. They remain for backward compatibility with existing pylsd-mode LSD files.

### Task 2 — pyLSD deprecation warning (D-05)

Updated `pylsd_run()` docstring to include "(DEPRECATED — use lucy lsd run with ELIM escalation per D-05)" and inserted `click.echo(...)` as the first statement using `err=True`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated 3 pre-existing tests that encoded old schema behavior**
- **Found during:** Task 2 execution
- **Issue:** `TestSchemaLoading::test_schema_has_required_fields_list` asserted 11 required fields (including retired ones); `TestSchemaValidation::test_rejects_missing_pylsd_mode` and `test_rejects_missing_elim_annotated` asserted missing fields cause errors — contradicting the Phase 80 schema change.
- **Fix:** Updated `test_schema_has_required_fields_list` to check only 8 required fields; renamed and flipped assertions for pylsd_mode/elim_annotated tests to confirm they are now ACCEPTED when missing.
- **Files modified:** tests/test_inventory_schema.py
- **Commit:** 205ba7f

## Known Stubs

None — no stub patterns introduced.

## Threat Flags

None — no new trust boundaries crossed (pure dataclass/schema/CLI changes).

## Self-Check: PASSED

| Item | Status |
|------|--------|
| src/lucy_ng/lsd/models.py exists with elim_budget | FOUND |
| src/lucy_ng/lsd/generator.py exists with elim_budget | FOUND |
| src/lucy_ng/data/schemas/constraint_inventory_v2.json exists with elim_budget | FOUND |
| src/lucy_ng/cli/pylsd.py exists with deprecated | FOUND |
| 80-01-SUMMARY.md exists | FOUND |
| Commit 22287d6 (task 1) | FOUND |
| Commit 205ba7f (task 2) | FOUND |
| TestElimBudget (6/6) GREEN | PASS |
| TestSchemaV2Phase80 (6/6) GREEN | PASS |
| Full suite (excluding test_ranking.py RED tests from 80-00) | PASS |

---
phase: 68-constraint-inventory-v2-schema
plan: "01"
subsystem: constraint-inventory
tags: [json-schema, validation, pyproject, testing]
dependency_graph:
  requires: []
  provides:
    - schemas/constraint_inventory_v2.json
    - jsonschema>=4.18.0 in pyproject.toml
    - tests/test_inventory_schema.py
  affects:
    - Plan 68-02 (CLI validator loads this schema)
    - Plan 68-03/04 (skill docs reference this schema path)
tech_stack:
  added:
    - jsonschema>=4.18.0 (JSON Schema Draft 2020-12 validation)
  patterns:
    - JSON Schema Draft 2020-12 with Draft202012Validator
    - Class-per-feature pytest structure (mirrored from TestPyLSDValidator)
    - _load_schema() module-level helper for path-safe schema loading
key_files:
  created:
    - schemas/constraint_inventory_v2.json
    - tests/test_inventory_schema.py
  modified:
    - pyproject.toml
decisions:
  - "Schema uses additionalProperties=true at top level for forward compatibility; deferred_4j items use additionalProperties=false for strict validation (per D-04)"
  - "version field uses const:2 to reject v1 instances at the schema level (per D-03)"
  - "deferred_4j item annotation uses const:'; ELIM' to enforce v8.0 PyLSDOrchestrator convention"
  - "jsonschema>=4.18.0 declared as minimum version supporting Draft202012Validator"
metrics:
  duration: 212s
  completed: "2026-05-19T10:11:47Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 1
  tests_added: 25
  tests_total_after: 878
requirements_met:
  - INPUT-05
---

# Phase 68 Plan 01: JSON Schema v2 for Constraint Inventory — Summary

JSON Schema Draft 2020-12 source of truth for constraint inventory v2 format, with jsonschema dependency declaration and 25-test suite covering loading, validation, and deferred_4j strict item schema.

## What Was Built

### schemas/constraint_inventory_v2.json

New file at repo root. JSON Schema Draft 2020-12 document that:
- Requires 11 mandatory fields: `version` (const:2), `iteration`, `formula`, `timestamp`, `mult_count`, `hsqc_count`, `hmbc_batches`, `hmbc_total`, `pylsd_mode`, `elim_annotated`, `deferred_4j`
- Uses `additionalProperties: true` at top level for forward compatibility
- Enforces `deferred_4j` as an object array with `additionalProperties: false` on items
- Each `deferred_4j` item requires: `atom1` (int, min:1), `atom2` (int, min:1), `shift1` (number), `shift2` (number), `correlation_type` (const:"HMBC"), `annotation` (const:"; ELIM")
- Also schemas `hmbc_batches` items strictly (requires batch/count/correlations)
- Defines optional fields: `grouped_hmbc`, `bond_constraints`, `syme_pairs`, `list_prop_constraints`, `elim_value` (int|null), `deff_not_patterns`, `deff_fexp`, `detection_results`, `applied_from_detection`, `pending_from_detection`

### pyproject.toml

Added `"jsonschema>=4.18.0"` to `[project] dependencies` in alphabetical order between `click>=8.0` and `nmrglue>=0.9`.

### tests/test_inventory_schema.py

341 lines, 25 tests in 4 classes:

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestSchemaLoading` | 5 | File exists, valid JSON, $schema has 2020-12, meta-schema check, required fields list |
| `TestSchemaValidation` | 8 | Accepts minimal v2, accepts full pylsd_mode=True, rejects version=1, rejects string-array deferred_4j, rejects missing pylsd_mode/elim_annotated/version, allows extra top-level fields |
| `TestDeferred4jSchema` | 7 | Accepts valid item, rejects missing atom2, wrong annotation ('elim'), wrong correlation_type ('COSY'), extra field, atom1=0, accepts two valid items |
| `TestSchemaOptionalFields` | 5 | hmbc_batches with items, hmbc_batches item missing correlations, deff_not_patterns, elim_value=null, elim_value=int |

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | a22dc78 | feat(68-01): create JSON Schema v2 for constraint inventory and add jsonschema dep |
| Task 2 | caff2ba | test(68-01): add schema loading and validation tests for constraint inventory v2 |

## Verification Results

1. `python -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('schemas/constraint_inventory_v2.json')))"` — PASSED
2. `pytest tests/test_inventory_schema.py -x` — 25 passed
3. `pytest` (full suite) — 878 passed, 14 skipped, 0 failures
4. `grep '"jsonschema>=4.18.0"' pyproject.toml` — PASSED

## Deviations from Plan

None — plan executed exactly as written. All must_haves met.

## Known Stubs

None. Schema is complete and machine-readable. All 11 required fields are defined with proper types and constraints.

## Threat Flags

None. The schema file is a static repository artifact (T-68-01: accept). No new network endpoints or auth paths introduced.

## Self-Check: PASSED

- `schemas/constraint_inventory_v2.json` — FOUND
- `tests/test_inventory_schema.py` — FOUND (341 lines, > 60 line minimum)
- `pyproject.toml` contains `jsonschema>=4.18.0` — FOUND
- Commit a22dc78 — FOUND
- Commit caff2ba — FOUND

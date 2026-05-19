---
phase: 68-constraint-inventory-v2-schema
verified: 2026-05-19T14:00:00Z
status: passed
score: 4/4
overrides_applied: 0
re_verification: false
---

# Phase 68: Constraint Inventory v2 Schema — Verification Report

**Phase Goal:** The constraint inventory JSON schema in agent skill files is extended with pyLSD-specific fields; devils-advocate validation gates cover FORM/MULT consistency and ELIM-vs-bond-range semantics.
**Verified:** 2026-05-19T14:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Constraint inventory JSON block includes `pylsd_mode` (bool), `deferred_4j` (list of HMBC pair identifiers), and `elim_annotated` (bool) fields documented in skill files | VERIFIED | `schemas/constraint_inventory_v2.json` lines 79–124 define `pylsd_mode` (boolean), `elim_annotated` (boolean), `deferred_4j` (object array). `lucy-lsd-engineer.md` Section 5A table (lines 335–337) and `lucy-devils-advocate.md` extract these fields from the CLI output in G2/G3 checks. |
| 2 | The devils-advocate checklist explicitly distinguishes `ELIM N M` (artifact removal) from `HMBC X Y 2 4` (4J bond range) | VERIFIED | `lucy-devils-advocate.md` line 315 states: "Bare ELIM drops correlations entirely instead of permuting them. The v8.0 convention is HMBC X Y 2 4 (extended bond range) with '; ELIM' trailing comment for PyLSDOrchestrator parsing." G2 block message makes the semantic contrast explicit. |
| 3 | A devils-advocate checklist item verifies FORM atom count matches MULT atom sum before approving any LSD run in pylsd_mode | VERIFIED | `lucy-devils-advocate.md` G1 check (line 300–306): "When `pylsd_mode=true` AND a line matching `^FORM` exists… If carbon counts differ: BLOCK with message 'FORM/MULT mismatch'." Marked CRITICAL severity and blocking. |
| 4 | The schema definition is testable: an agent writing a correct v2 inventory can be verified against the schema documentation without ambiguity | VERIFIED | `schemas/constraint_inventory_v2.json` is a valid JSON Schema Draft 2020-12 document. `lucy lsd validate-inventory --format json` CLI tool provides machine-readable validation (exit 0 = valid, exit 1 = errors list). 34 tests in `tests/test_inventory_schema.py` all pass (confirmed: `pytest tests/test_inventory_schema.py` 34 passed). |

**Score:** 4/4 truths verified

---

### Deferred Items

None.

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `schemas/constraint_inventory_v2.json` | JSON Schema Draft 2020-12 with version const:2, pylsd_mode, elim_annotated, deferred_4j | VERIFIED | 174-line schema; `$schema` = Draft 2020-12; `required` includes all 11 mandatory fields; `deferred_4j` items use `additionalProperties: false`. |
| `src/lucy_ng/cli/lsd.py` | `validate-inventory` subcommand | VERIFIED | `@lsd.command("validate-inventory")` registered at line 185; `_get_schema_path()` at line 142; `_extract_inventory_block()` at line 162; `import jsonschema` at line 7. Command confirmed in `lsd.commands` list. |
| `tests/test_inventory_schema.py` | 34 tests, all classes present | VERIFIED | 6 classes: TestSchemaLoading (5), TestSchemaValidation (8), TestDeferred4jSchema (7), TestSchemaOptionalFields (5), TestValidateInventoryCLI (6), TestGateLogic (3). All 34 pass. Min 60 lines: actual 487+ lines. |
| `pyproject.toml` | `jsonschema>=4.18.0` in dependencies | VERIFIED | Line 28 confirms `"jsonschema>=4.18.0"` in `[project] dependencies`. |
| `/Users/steinbeck/.claude/agents/lucy-lsd-engineer.md` | Section 5 v2 rewrite | VERIFIED | v2 delimiters present (3 occurrences of `CONSTRAINT INVENTORY v2`); `schemas/constraint_inventory_v2.json` referenced in Section 5A; `pylsd_mode` and `elim_annotated` rows in schema table; inline example shows object-array `deferred_4j`; UPGRADE NOTE present; 0 remaining v1 references. |
| `/Users/steinbeck/.claude/agents/lucy-devils-advocate.md` | G1/G2/G3 gates in Section 5B, CLI extraction in 5A | VERIFIED | `lucy lsd validate-inventory --format json` call at line 227; `CONSTRAINT INVENTORY v2` at line 219; `Legacy v1 inventory` WARNING path at line 240; G1 (line 300), G2 (line 308), G3 (line 318) all present and marked CRITICAL/blocking; `^ELIM` anchor at line 312/314; v7.0 post-mortem citation ("100% FP rate") at line 315. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_inventory_schema.py` | `schemas/constraint_inventory_v2.json` | `Draft202012Validator` + `json.load()` | WIRED | Line 9: `from jsonschema import Draft202012Validator`; `_load_schema()` resolves via `Path(__file__).parent.parent / "schemas" / "constraint_inventory_v2.json"`. |
| `src/lucy_ng/cli/lsd.py` | `schemas/constraint_inventory_v2.json` | `_get_schema_path()` package-relative path | WIRED | `_get_schema_path()` navigates `src/lucy_ng` → `src` → repo root, returns `project_root / "schemas" / "constraint_inventory_v2.json"`. Confirmed working for editable install. |
| `tests/test_inventory_schema.py` | `src/lucy_ng/cli/lsd.py` | `CliRunner().invoke(lsd, ["validate-inventory", ...])` | WIRED | `TestValidateInventoryCLI` uses `CliRunner`; all 6 CLI tests pass. |
| `lucy-devils-advocate.md §5A` | `lucy lsd validate-inventory` | Bash call `RESULT=$(lucy lsd validate-inventory --format json ...)` | WIRED | Line 227 of `lucy-devils-advocate.md` contains the exact CLI invocation. |
| `lucy-lsd-engineer.md §5A` | `schemas/constraint_inventory_v2.json` | Explicit path reference in Section 5A intro | WIRED | Line 316: "Source of Truth: `schemas/constraint_inventory_v2.json` (repo root, JSON Schema Draft 2020-12)." |

---

### Data-Flow Trace (Level 4)

Not applicable — phase produces schema/documentation/CLI artifacts, not data-rendering components.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Schema passes meta-schema validation | `python -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('schemas/constraint_inventory_v2.json')))"` | exit 0 (confirmed via test suite) | PASS |
| `validate-inventory` registered in CLI | `python -c "from lucy_ng.cli.lsd import lsd; print(list(lsd.commands.keys()))"` | `['check', 'run', 'validate-inventory', 'rank', 'analyze']` | PASS |
| All 34 schema tests pass | `pytest tests/test_inventory_schema.py` | `34 passed, 26 warnings in 0.21s` | PASS |
| `jsonschema>=4.18.0` in pyproject | `grep '"jsonschema>=4.18.0"' pyproject.toml` | line 28 matched | PASS |
| No v1 delimiter references in lsd-engineer §5 | `grep -c "CONSTRAINT INVENTORY v1" lucy-lsd-engineer.md` | 0 matches | PASS |

---

### Probe Execution

No probes declared in PLAN files or found under `scripts/*/tests/`. Step skipped.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| INPUT-05 | 68-01, 68-02, 68-03, 68-04 | Constraint inventory schema v2 tracks 4J suspect correlations with `pylsd_mode`, `deferred_4j` metadata | SATISFIED | JSON Schema at `schemas/constraint_inventory_v2.json` enforces both fields as required. Agent skill files (lsd-engineer §5, devils-advocate §5) document and validate the fields. 34 tests covering schema acceptance/rejection. |

No orphaned requirements found for Phase 68 in REQUIREMENTS.md.

---

### Anti-Patterns Found

No `TBD`, `FIXME`, or `XXX` markers found in phase-modified files (`schemas/constraint_inventory_v2.json`, `src/lucy_ng/cli/lsd.py`, `tests/test_inventory_schema.py`). No `TODO`, `HACK`, or `PLACEHOLDER` markers found.

**Internal documentation inconsistency (WARNING — not a debt marker):**

`lucy-lsd-engineer.md` line 200 (Section 2, "4J Deferral Rule") still contains:
> `Add them to 'deferred_4j' in the constraint inventory (as string descriptions)`

This contradicts Section 5A (line 337) which documents `deferred_4j` as an object array. Plan 03 task action specified "find any reference to writing 4J correlations as string descriptions and update" — this instance was missed. However, Plan 03's must_have #7 ("Workflow step 2a references structured objects") IS satisfied (line 461, workflow section, uses correct object language). The stale line 200 wording is within Section 2 (Incremental HMBC Strategy), not in a blocking must_have.

---

### Code Review Findings (from 68-REVIEW.md)

The code review identified 3 critical and 5 warning issues. Per the verification prompt, these are surfaced here as advisory findings — they do not block the phase goal but should be tracked.

**Critical (advisory, not phase-blocking):**

| ID | File | Issue | Severity |
|----|------|-------|----------|
| CR-01 | `src/lucy_ng/cli/lsd.py:142–159` | `_get_schema_path()` fails for non-editable pip installs — schema not bundled in wheel, `FileNotFoundError` on `lucy lsd validate-inventory` for any user not on editable install. | Advisory Critical |
| CR-02 | `src/lucy_ng/cli/lsd.py:272` and `lucy-devils-advocate.md:225–253` | Success JSON `{"valid": true, "file": ..., "version": 2}` omits parsed inventory fields. Devils-advocate §5B Check 4 tries to extract `pylsd_mode`/`elim_annotated`/`deferred_4j` from `$RESULT` — those keys are absent. Agents will fail or hallucinate G2/G3 gate values. | Advisory Critical |
| CR-03 | `lucy-devils-advocate.md:322` | G3 grep `"; ELIM"` is unanchored — matches inventory JSON comment lines (`; "annotation": "; ELIM"`), causing false-positive G3 blocks when `pylsd_mode=true, elim_annotated=false`. G2 correctly uses `^ELIM`; G3 lacks equivalent protection. | Advisory Critical |

**Warnings (from 68-REVIEW.md):**

- WR-01: Schema doesn't enforce G2/G3 cross-field invariants via `if/then` constraints
- WR-02: `hmbc_batches[].batch` missing `minimum: 1` (inconsistent with `atom1`/`atom2`)
- WR-03: `lsd-engineer` Section 5D update procedure doesn't list `elim_annotated` for recomputation
- WR-04: `_extract_inventory_block` silently succeeds when END delimiter is missing
- WR-05: `validate-inventory` unhandled `PermissionError` on file read

**Note on CR-02 and phase goal SC-4:** CR-02 creates a practical gap between the documented agent protocol and the CLI tool output. The schema IS testable (SC-4 passes because `validate-inventory` correctly validates and the 34 tests cover the schema exhaustively). However, the success response being incomplete means the agent's bash pipeline for G2/G3 extraction is broken as documented. This is a wiring defect in the agent skill protocol, not in the schema itself. SC-4 is met; the CR-02 fix (adding `"inventory": instance` to success JSON) is a Phase 70 follow-up item per the agent integration work scope.

---

### Human Verification Required

None. All success criteria are verifiable programmatically via grep, file existence, schema validation, and test execution.

---

### Gaps Summary

None. All 4 roadmap success criteria are verified. The code review findings (CR-01 through CR-03, WR-01 through WR-05) are advisory and do not prevent the phase goal from being achieved — the schema exists, is machine-readable, is tested, and the agent skill files document v2 semantics with the G1/G2/G3 gates. CR-02 (missing inventory in success JSON) and CR-03 (unanchored G3 grep) are implementation defects that affect agent runtime behavior but are scoped to agent integration work (Phase 70) rather than the schema/gate definition goal of Phase 68.

The stale "as string descriptions" wording at `lucy-lsd-engineer.md` line 200 (Section 2) creates an internal contradiction within the agent file but does not fail any must_have truth or roadmap success criterion. It is documented above for tracking.

---

_Verified: 2026-05-19T14:00:00Z_
_Verifier: Claude (gsd-verifier)_

---
phase: 68-constraint-inventory-v2-schema
plan: "04"
subsystem: agent-skill
tags: [devils-advocate, validation, v2-schema, G1, G2, G3, pylsd-mode]
dependency_graph:
  requires: [68-01, 68-02]
  provides: [v2-aware-validation-gates, cli-based-inventory-extraction]
  affects: [lucy-devils-advocate, validation-runtime]
tech_stack:
  added: []
  patterns: [cli-based-extraction, CRITICAL-blocking-gates, v1-legacy-warning-fallback]
key_files:
  modified:
    - /Users/steinbeck/.claude/agents/lucy-devils-advocate.md
decisions:
  - "CLI replaces grep/sed/awk in Section 5A — devils-advocate calls lucy lsd validate-inventory --format json (D-12)"
  - "v1 legacy detection emits WARNING not BLOCK — run proceeds with legacy grep fallback (D-02)"
  - "G1/G2/G3 are all CRITICAL/blocking; no new override mechanism beyond existing APPROVED/BLOCKED/WARNING (D-07, D-08)"
  - "G2 grep anchored to ^ELIM — unanchored ELIM would match '; ELIM' comment annotations causing false positives"
metrics:
  duration: "~15 minutes"
  completed: "2026-05-19T10:24:43Z"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 1
---

# Phase 68 Plan 04: Devils-Advocate v2 Validation Gates Summary

**One-liner:** Devils-advocate Section 5 updated with CLI-based inventory extraction (`lucy lsd validate-inventory --format json`), v1 legacy WARNING fallback, and G1/G2/G3 as CRITICAL blocking gates for pyLSD mode consistency.

## What Was Built

Updated `~/.claude/agents/lucy-devils-advocate.md` Section 5 to be v2-schema-aware:

**Section 5 intro paragraph** — delimiter reference changed from `v1` to `v2`.

**Section 5A (Inventory Extraction)** — the two grep/sed/awk bash blocks targeting `CONSTRAINT INVENTORY v1` were replaced with a single `lucy lsd validate-inventory --format json` CLI call. Three paths are now documented:
- v2 valid → parse JSON `$RESULT` for use in 5B checks
- v1 legacy detected → emit `WARNING: "Legacy v1 inventory — using fallback validation"`, proceed with legacy diff protocol (NOT blocked, per D-02)
- no block / malformed → emit WARNING or BLOCK respectively

**Section 5B Check 4 (pyLSD Mode Consistency)** — new CRITICAL/blocking check added after Check 3:
- G1: FORM/MULT Consistency — when `pylsd_mode=true` and FORM line present, MULT carbon count must match FORM formula carbon count
- G2: No Bare ELIM Command — `grep -n "^ELIM"` anchored to line start; explicitly documents that `HMBC 4 8 2 4 ; ELIM` does NOT match `^ELIM`; cites v7.0 post-mortem ("Statistical 4J detection non-viable — 100% FP rate")
- G3: Annotation-vs-Mode Consistency — when HMBC lines carry `; ELIM` annotations, `pylsd_mode=true` AND `elim_annotated=true` AND `deferred_4j` non-empty must all hold

## Deviations from Plan

None — plan executed exactly as written.

## Verification

All acceptance criteria verified via grep:

| Criterion | Result |
|-----------|--------|
| `lucy lsd validate-inventory --format json` in file | PASS (2 occurrences) |
| `CONSTRAINT INVENTORY v2` in file | PASS |
| `Legacy v1 inventory` WARNING path | PASS (3 occurrences) |
| G1, G2, G3 checks present | PASS |
| `^ELIM` anchor explicitly documented | PASS (2 occurrences) |
| `100% FP rate` v7.0 post-mortem citation | PASS |
| `Statistical 4J detection non-viable` | PASS |
| APPROVED/BLOCKED/WARNING semantics retained | PASS |
| No `override-inventory-check` introduced | PASS |

Pytest full suite: 853 passed, 14 skipped, 0 failures.

## Known Stubs

None — no stub patterns introduced.

## Threat Flags

None — changes are documentation/skill updates only; no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries.

## Self-Check: PASSED

- `/Users/steinbeck/.claude/agents/lucy-devils-advocate.md` — modified in place (outside repo, not tracked by git)
- All grep acceptance criteria pass (verified above)
- pytest 853 passed, 0 failures

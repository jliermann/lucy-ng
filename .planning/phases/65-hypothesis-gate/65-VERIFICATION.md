---
phase: 65-hypothesis-gate
verified: 2026-03-16T12:30:00Z
status: passed
score: 3/3 must-haves verified
re_verification: false
---

# Phase 65: Hypothesis Gate Verification Report

**Phase Goal:** Confirm the core v8.0 hypothesis before writing any code — that removing 3 known 4J HMBC correlations from the ibuprofen LSD input produces solutions containing an aromatic ring
**Verified:** 2026-03-16T12:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ibuprofen LSD file runs to completion with 3 known 4J HMBC correlations removed | VERIFIED | `ibuprofen_no4j.sol` exists, 6377 lines, `solncounter` file contains 392 |
| 2 | At least one solution in the output contains an aromatic ring (6-membered sp2 system), confirmed by RDKit aromatic atom count > 0 | VERIFIED | `validation_result.md` documents 3 of 392 solutions have 6 aromatic atoms; all 3 canonicalize to ibuprofen (`CC(C)Cc1ccc(C(C)C(=O)O)cc1`) |
| 3 | validation_result.md documents: which correlations were removed, solution count, aromatic ring presence, and GO/NO-GO decision | VERIFIED | File contains table of 3 removed correlations with chemical meaning, solution count 392, aromatic ring table, and explicit "Decision: GO" line |

**Score:** 3/3 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.lsd` | Modified LSD file with 4J correlations removed | VERIFIED | 102 lines; HMBC count = 9 (down from 12 in project root `ibuprofen.lsd` — exactly 3 fewer); removed lines documented in comments |
| `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.smi` | SMILES solutions from the modified LSD run | VERIFIED | 392 lines, all SMILES format, non-empty |
| `.planning/phases/65-hypothesis-gate/validation_result.md` | Go/no-go decision with evidence | VERIFIED | 130 lines; contains hypothesis result, correlation table, RDKit aromatic counts, ranked output, and explicit GO decision |

All artifacts: exist, substantive (non-trivial content), and logically linked via the documented pipeline.

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `ibuprofen_no4j.lsd` | `ibuprofen_no4j.sol` | `lucy lsd run` / direct `LSD` invocation | VERIFIED | `ibuprofen_no4j.sol` contains 392 solutions (6377 lines); `solncounter` file = 392; SUMMARY documents direct `LSD ibuprofen_no4j.lsd` invocation as workaround for stdin limitation |
| `ibuprofen_no4j.sol` | `ibuprofen_no4j.smi` | `outlsd 5` | VERIFIED | `ibuprofen_no4j.smi` contains 392 SMILES lines; `outlsd.out` confirms usage text (format 5 = SMILES); SUMMARY documents `outlsd 5 < file.sol` call |
| `ibuprofen_no4j.smi` | `validation_result.md` | RDKit aromatic atom count | VERIFIED | `validation_result.md` contains per-solution aromatic atom counts, references `Chem.MolFromSmiles` pattern, documents 3/392 aromatic solutions |

Note: Key link verification is based on artifact content and SUMMARY documentation. The pipeline was executed manually (no automated wiring in source code — this is a validation experiment, not production code).

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| GATE-01 | 65-01-PLAN.md | Manual hypothesis test — run ibuprofen LSD with 3 known 4J HMBC correlations removed, confirm solutions with aromatic rings appear (30-minute test, gates entire roadmap) | SATISFIED | `validation_result.md` documents GO decision; 3 aromatic solutions found; REQUIREMENTS.md line 75 marks as Complete |

No orphaned requirements: REQUIREMENTS.md maps GATE-01 to Phase 65 only, and it is claimed and fulfilled by 65-01-PLAN.md.

---

### Anti-Patterns Found

No source code files were modified by this phase (validation experiment only). Anti-pattern scan not applicable.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None | — | — |

---

### Human Verification Required

None. The hypothesis gate is a deterministic experiment: LSD solver output is binary (solutions exist or do not), and RDKit aromatic atom counting is programmatic. The key findings are:

- 392 solutions produced (vs 7 with 4J correlations included)
- 3 solutions with 6 aromatic atoms, all confirmed as ibuprofen
- Ibuprofen at rank 219/392 by HOSE-based ranking (expected — aromaticity filter is Phase 68 work)

All evidence is present in committed artifacts and can be reproduced by re-running `LSD ibuprofen_no4j.lsd` followed by `outlsd 5 < ibuprofen_no4j.sol`.

---

### Deviations from Plan (Noted)

Two auto-fixed CLI issues were encountered during execution, documented in SUMMARY.md:

1. LSD must be invoked with a filename argument (not stdin) to produce a `.sol` file. The executor used `LSD ibuprofen_no4j.lsd` directly instead of `lucy lsd run`. The LSD runner bug (`_run_outlsd` missing mode argument) was noted as a deferred fix for Phase 66 or 69.

2. `outlsd` does not accept a count argument — format mode 5 only. Plan specified `outlsd 20 < file.sol`; executor used `outlsd 5 < file.sol`. All 392 solutions were converted successfully.

Neither deviation affected the validity of the hypothesis test results.

---

## Summary

Phase 65 fully achieved its goal. The core v8.0 hypothesis is confirmed:

- Removing the 3 known 4J W-pathway HMBC correlations (`HMBC 6 8`, `HMBC 10 6`, `HMBC 10 8`) from the ibuprofen LSD input causes the solver to produce solutions containing benzene rings.
- The correct ibuprofen structure appears in the solution set (rank 219/392).
- The GO decision is issued with full evidence. Phases 66, 67, and 68 are unblocked.

The gate serves its intended purpose: the v8.0 approach is validated before any code is written, directly applying the lesson from the v7.0 failure (build-before-validate led to 5 phases of infrastructure, 100% false positive rate, full revert).

---

_Verified: 2026-03-16T12:30:00Z_
_Verifier: Claude (gsd-verifier)_

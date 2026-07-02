---
phase: 86-ranker-path-unification
verified: 2026-06-23T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: null
  previous_score: null
---

# Phase 86: Ranker Path Unification Verification Report

**Phase Goal:** `lucy lsd rank` ranks the correct structure using the SAME 13C prediction it would get from `lucy predict c13`, so the truth is no longer systematically under-scored.
**Verified:** 2026-06-23
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria + PLAN must_haves, merged)

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | For an identical molecule, `lucy lsd rank` and `lucy predict c13` produce the same per-shift 13C prediction (developer can diff — they match). [SC-1, RANK-01] | ✓ VERIFIED | Live behavioral diff: ran `lucy predict c13 "CC(C)Cc1ccc(cc1)C(C)C(=O)O"` and the ranker's predictor via `resolve_c13_predictor()` — **all 13 carbons bit-identical** (e.g. C12=180.8471 r6 both, C4=140.7356 r6 both). Both CLIs route through `resolve_c13_predictor` (lsd.py:275, predict.py:77). Test `test_rank01_path_parity_per_shift` asserts `abs(diff)<1e-6` for ibuprofen + pulegone — PASSED. |
| 2   | On CASE1 (ibuprofen) and CASE3 (pulegone), ranker MAE/match-count for the correct structure agrees with predict c13 within tolerance — no longer 2.23/8-of-10 where predict reports 0.27. [SC-2, RANK-02] | ✓ VERIFIED | `test_rank02_agreement` PASSED (ranker sol.mae == recomputed MAE within 0.05 ppm, matched_count exact). Real-DB `test_rank03_real_db_ordering_fix[ibuprofen]` RAN (not skipped — DB present) and PASSED asserting MAE ≤ 0.5 (reproducing 0.244) and matched_count == 13 (13/13 vs old 8/13). |
| 3   | The ranker places the correct structure ahead of the wrong isomer it previously ranked #1. [SC-3, RANK-03] | ✓ VERIFIED | Real-DB `test_rank03_real_db_ordering_fix` RAN + PASSED for BOTH ibuprofen (vs meta isomer `CC(C)Cc1cccc(c1)C(C)C(=O)O`) and pulegone (vs ring-shifted isomer): asserts `result.solutions[0].smiles == correct` and `correct_sol.mae < wrong_sol.mae`. Deterministic non-circular guard `test_rank03_deterministic_ordering` PASSED (asserts `correct_hoses != wrong_hoses` AND zero r6 overlap BEFORE ordering). |
| 4   | A committed regression test pins ranker↔predict agreement on CASE1 and CASE3; `pytest` is green. [SC-4, RANK-03] | ✓ VERIFIED | `tests/test_ranking.py` committed (commit 0eb8cc9). `pytest tests/test_ranking.py -q` → **62 passed** in 1.19s. Test classes `TestRankPredictParity`, `TestRankMAEAgreement`, `TestRankOrderingNonCircular`, `TestRankRealDBOrderingFix` all green; real-DB tests RAN (DB present at data/reference/lucy-ng-derep.db). |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/lucy_ng/prediction/resolver.py` | Shared `resolve_c13_predictor()` DB-first 4-tier ladder; no cli import | ✓ VERIFIED | `def resolve_c13_predictor` at line 76. DB-first order: explicit db → explicit table → `find_hose_database()` (line 106) → JSON fallback w/ replicated shipped paths. `grep "lucy_ng.cli"` → nothing (no layering inversion). 127 lines, substantive. |
| `src/lucy_ng/ranking/ranker.py` | `SolutionRanker.from_database` mirroring `from_table_file`; `_match_shifts` UNCHANGED | ✓ VERIFIED | `def from_database` at line 331 (calls `C13Predictor.from_database`). `grep -c "def _match_shifts"` → 1; `git diff 244ef44..HEAD` = +31 lines only (purely additive `from_database`), `_match_shifts` body NOT in diff. |
| `src/lucy_ng/cli/lsd.py` | `_perform_ranking`+`lsd_rank` wired to resolver; `--db`/`--max-radius` added; hardwired from_table_file gone | ✓ VERIFIED | `resolve_c13_predictor` at line 275 inside `_perform_ranking`; NO `from_table_file`/`from_database` call remains in ranking path (only standalone `_get_default_table_path` helper survives, unused by ranker). `--db` (608), `--max-radius` (620) options present; `lucy lsd rank --help` lists both. |
| `src/lucy_ng/cli/predict.py` | `predict_c13` routed through shared resolver | ✓ VERIFIED | `resolve_c13_predictor` at line 77 inside `predict_c13`; the prior 4-tier ladder collapsed to one call. `--db`/`--max-radius` options retained. |
| `tests/test_ranking.py` | RANK-01/02/03 regression tests on CASE1+CASE3, deterministic + real-DB | ✓ VERIFIED | 62 tests; new classes `TestRankPredictParity`, `TestRankMAEAgreement`, `TestRankOrderingNonCircular`, `TestRankRealDBOrderingFix`, `TestSolutionRankerFromDatabase`, `TestResolveC13Predictor`, `TestRankCLIBackendWiring`. All PASS. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| cli/lsd.py `_perform_ranking` | `resolve_c13_predictor` | shared backend resolution | ✓ WIRED | line 275; predictor built then `SolutionRanker(predictor, tolerance=)` |
| cli/predict.py `predict_c13` | `resolve_c13_predictor` | shared path | ✓ WIRED | line 77; identical call shape `(db=db, table=table, max_radius=max_radius)` |
| ranker.py `from_database` | `C13Predictor.from_database` | DB-backed factory | ✓ WIRED | line 353 |
| resolver.py | `DatabaseFinder.find_hose_database` | DB-first auto-detect | ✓ WIRED | line 106, ahead of table fallback |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `lucy lsd rank` output | `result.solutions` | `resolve_c13_predictor()` → DatabaseHOSELookup over 7.9M-entry SQLite DB | ✓ Yes | ✓ FLOWING — live run produced real per-carbon shifts identical to predict c13 |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| rank↔predict same predictions | `lucy predict c13 <ibuprofen>` vs `resolve_c13_predictor()` predict | All 13 carbons bit-identical | ✓ PASS |
| CLI exposes new options | `lucy lsd rank --help` | shows `--db` and `--max-radius` | ✓ PASS |
| Targeted suite green | `pytest tests/test_ranking.py -q` | 62 passed | ✓ PASS |
| Real-DB ordering fix RAN | `pytest -k real_db -v` | both ibuprofen + pulegone PASSED (not skipped) | ✓ PASS |

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` and phase declares pytest-based verification, executed above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| RANK-01 | 86-01, 86-02 | Same per-shift prediction; single path, no divergent code | ✓ SATISFIED | Both CLIs call `resolve_c13_predictor`; hardwired ranker path removed; live diff identical; parity test PASS |
| RANK-02 | 86-02 | Ranker no longer under-scores truth; MAE/match agrees within tolerance | ✓ SATISFIED | `test_rank02_agreement` PASS; real-DB ibuprofen MAE ≤ 0.5 / 13-13 PASS |
| RANK-03 | 86-02 | Regression test pins agreement on CASE1+CASE3 (was 2.23 vs 0.27, wrong isomer #1) | ✓ SATISFIED | Deterministic non-circular + real-DB ordering-fix tests committed (0eb8cc9) and PASSING; correct outranks prior wrong isomer |

All 3 declared requirement IDs (RANK-01, RANK-02, RANK-03) are mapped to Phase 86 in REQUIREMENTS.md and all are SATISFIED. No orphaned requirements — REQUIREMENTS.md maps no other IDs to Phase 86.

### Anti-Patterns Found

None. Grep for TBD/FIXME/XXX/HACK/PLACEHOLDER/"not yet implemented" across all four modified/created source files returned nothing. No empty-return stubs, no hardcoded-empty data paths (Plan 02 summary "Known Stubs: None" confirmed).

### Human Verification Required

None. The phase is isolated Python tooling (no blind CASE instance, no visual/UX surface). The central success criterion ("developer can run both and diff predicted shifts — they match") was verified programmatically via a live CLI/predictor diff showing bit-identical output across all 13 ibuprofen carbons, and the real-DB ordering-fix tests reproduce the documented 0.244/13-13 fix without needing human judgment.

### Gaps Summary

No gaps. The phase goal is achieved in the codebase:
- The divergent prediction path is eliminated — both `lucy lsd rank` and `lucy predict c13` resolve their predictor through the single `resolve_c13_predictor` helper; the hardwired `from_table_file`-only block in the ranker CLI is gone.
- `_match_shifts`/MAE aggregation is provably untouched (additive +31-line diff = `from_database` only).
- The real-DB regression tests RAN (not skipped — production DB present) and reproduce the exact documented fix: ibuprofen MAE ≤ 0.5 / 13-13 matched (vs old 2.23 / 8-13) with the correct isomer outranking the prior wrong #1.
- `lucy lsd rank --help` exposes `--db` and `--max-radius`.
- `pytest tests/test_ranking.py` → 62 passed.

---

_Verified: 2026-06-23_
_Verifier: Claude (gsd-verifier)_

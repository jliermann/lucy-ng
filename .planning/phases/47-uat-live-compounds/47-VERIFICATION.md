---
phase: 47-uat-live-compounds
verified: 2026-02-18
status: partial
score: 3/5 must-haves verified (1 partial, 1 skipped)
---

# Phase 47: UAT with Live Compounds -- Verification

**Phase Goal (from ROADMAP.md):** Team-based CASE validated against v3.0 baseline with diverse compounds

**Status:** partial (SC-1 partial, SC-4 skipped)
**Re-verification:** No -- retrospective verification (post-hoc evaluation of live CASE team run artifacts)

## Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Ibuprofen correct structure in top 3, all DEFF NOT patterns preserved | PARTIAL | 47-01-SUMMARY.md: "rank #4 by algorithm, #1 by analyst override (aromatic check)". Ibuprofen at rank #4 by match-count algorithm (MAE 0.25 ppm), promoted to rank #1 by solution-analyst via Phase 46.1 aromatic ring awareness. DEFF NOT: 2 patterns (ring3, ring4) constant across all 4 iterations. Partial because algorithm rank is #4, not top 3. |
| 2 | All v3.0 constraint-loss bugs verified fixed | VERIFIED | 47-01-SUMMARY.md: 5/5 PASS. Bug 1 (DEFF NOT): deff_not_patterns constant. Bug 2 (grouping applied): 4 groups translated. Bug 3 (grouped notation): 2->3->6->10 monotonic. Bug 4 (PROP/BOND): documented reasoning. Bug 5 (detection->constraints): applied_from_detection populated. |
| 3 | Time to solution < 2x v3.0 baseline | VERIFIED | 47-01-SUMMARY.md: 4 iterations (v4.0) = 4 iterations (v3.0). Ratio: 1.0x (well under 2.0x threshold). |
| 4 | Additional test compounds (Pulegone, Virgiline) if time permits | SKIPPED | 47-01-SUMMARY.md: "not executed (post-hoc evaluation)". Phase evaluated existing Ibuprofen artifacts only. Additional compounds deferred to future validation. |
| 5 | Performance comparison report: v3.0 vs v4.0 | VERIFIED | 47-02-SUMMARY.md: v4.0-UAT-report.md written with 6 metrics, bug matrix, convergence trajectory, ship recommendation. |

**Score:** 3/5 truths verified (1 partial, 1 skipped)

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| Ibuprofen CASE run artifacts | analysis/ directory with iterations, CASE-PROGRESS.md | EXISTS | /Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/ |
| v4.0-UAT-report.md | Performance comparison report | EXISTS | Written by Plan 47-02, contains v3.0 vs v4.0 comparison with 6 metrics |
| CASE-PROGRESS.md | Iteration history with per-agent sections | EXISTS | Documents 4 iterations with constraint inventories |

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Constraint inventory | Bug matrix evaluation | deff_not_patterns, grouped_hmbc fields | VERIFIED | Inventory fields directly verify Bugs 1-3 |
| Phase 46.1 aromatic awareness | SC-1 partial mitigation | Analyst override via Check 6 | VERIFIED | Analyst promoted ibuprofen from rank #4 to #1 using aromatic ring check |
| v4.0-UAT-report.md | Ship recommendation | Quantitative v3.0 vs v4.0 comparison | VERIFIED | Report recommends YES (conditional on ranking improvement) |

## Success Criteria Coverage

| Success Criterion | Status | Evidence |
|-------------------|--------|----------|
| SC-1: Ibuprofen in top 3, DEFF NOT preserved | PARTIAL | Rank #4 algorithm, #1 analyst. DEFF NOT preserved (2 patterns constant). Ranking algorithm limitation: match-count favors non-aromatic structures at 3 ppm tolerance. Deferred to future milestone. |
| SC-2: All v3.0 bugs fixed | PASS | 5/5 bugs verified fixed with quantitative evidence |
| SC-3: Time < 2x baseline | PASS | 4 iterations = 1.0x (same as v3.0) |
| SC-4: Additional compounds | SKIPPED | Pulegone/Virgiline not tested; post-hoc evaluation of Ibuprofen only |
| SC-5: Performance comparison report | PASS | v4.0-UAT-report.md written with ship recommendation |

## Anti-Patterns Found

None in the CASE team behavior. The ranking algorithm limitation (match-count favoring non-aromatic at wide tolerance) is a known issue documented for future improvement.

## Human Verification Required

SC-4 (additional compounds) requires manual execution of CASE runs on Pulegone and Virgiline compounds. This was explicitly descoped during Phase 47 execution due to post-hoc evaluation approach.

## Gaps Summary

1. **SC-1 PARTIAL:** Ibuprofen ranks #4 by algorithm (not top 3). Mitigated by Phase 46.1 analyst override to #1. Root cause: match-count ranking at 3 ppm tolerance disadvantages aromatic structures. Fix deferred to future milestone (confidence-weighted ranking).
2. **SC-4 SKIPPED:** Additional compounds not tested. Deferred to post-v4.0 validation.

## Note

This is a retrospective verification. Phase 47 was evaluated post-hoc from existing CASE team run artifacts rather than observed live. The evaluation methodology is documented in 47-01-SUMMARY.md: "Artifacts were produced by a live CASE team run... this is a post-hoc evaluation of existing artifacts, not a live observed run."

---
*Verified: 2026-02-18*
*Verifier: Phase 48 executor (retrospective)*

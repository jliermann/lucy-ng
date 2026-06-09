---
status: issues_found
phase: 79-peak-picking-symmetry-fix
source: [79-VERIFICATION.md]
started: "2026-06-08"
updated: "2026-06-09"
---

## Current Test

CASE9 blind re-run COMPLETE — correct structure not reached; new root cause deferred to Phase 80.

## Tests

### 1. CASE9 Blind UAT (UAT-04 milestone gate)
expected: A fresh, untainted Claude instance runs the full `/lucy-ng:case` workflow on the
CASE9 dataset (~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE9) and reaches an
RDKit-verified C12H16O3 para-disubstituted aromatic-ester solution **via the emergent path**
(no forced ring-BONDs as the primary mechanism). Specifically:
  - `lucy pick 1d` on the CASE9 13C spectrum lists the ester carbonyl at ~166 ppm (SNR≈17) —
    the CDCl₃ multiplet no longer masks it (FIX-04, live-data confirmation of Criterion 1).
  - 13C intensity-symmetry flags the 2C aromatic CH pairs (e.g. 129.94, 125.31) and feeds
    `lucy detect aromatic-cosy` so the ring emerges (FIX-05, live-data confirmation of Criterion 2).
  - If the run converges clean-but-wrong, Pattern 5 (QUALITY_CONVERGENCE_FAILURE) fires and
    reactivates the nmr-chemist for a bounded re-pick (FIX-06, behavioral confirmation).
  - The Phase-78 AND-gate is re-applied and the verdict recorded.
result: FAILED (ran 2026-06-09; correct structure not reached) — but Phase-79 fixes all engaged
notes: |
  Blind CASE9 re-run executed by the user 2026-06-09 (10 iterations). Correct structure
  4-(1-hydroxyethyl)benzoic acid isopropyl ester (CC(C)OC(=O)c1ccc(C(C)O)cc1) NOT reached;
  top candidate was a benzylic carbonate (meta, MAE 9.09, PLAUSIBLE-but-wrong).

  CRITICAL: All Phase-79 deliverables demonstrably WORKED in the live run:
  - FIX-04: carbonyl 166.1 ppm picked at SNR 17 (no longer masked by CDCl3) ✓
  - FIX-05: 3 intensity-symmetry 2C-pairs detected (129.9, 125.3, 22.1) ✓
  - emergent benzene ring via COSY equivalence pairs, no SKEL / no ring-BOND ✓
  - FIX-06: DBE self-check (5/5) + quality reexamination advisory fired (carbonate-vs-ester) ✓

  NEW root cause (out of Phase-79 scope → Phase 80): false-positive long-range (4J) HMBC
  correlations (HMBC 1 8 = 166.1↔70.2; set 2 3 / 2 9 / 3 8) force wrong carbonyl connectivity,
  excluding the correct para-benzoate-with-benzylic-alcohol. This is the long-standing 4J-HMBC
  trap (v4.0 ibuprofen, v7.0 abandoned). Forensics: CASE9/analysis/final_results.md + CASE-PROGRESS.md.
  Per feedback_blind_uat the executing instance was fresh; this orchestrator only did bookkeeping.

## Summary

total: 1
passed: 0
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

### G-79-UAT-01: CASE9 not solved — false-positive long-range (4J) HMBC forces wrong connectivity
status: deferred-to-phase-80
detail: |
  Phase-79-scoped defects (carbonyl masking, undetected symmetry) are eliminated and verified
  in the live run. The newly-exposed blocker is a DIFFERENT defect (4J/long-range HMBC enforced
  as 2-3J), tracked as new Phase 80. Not a Phase-79 gap-closure item.

---
status: partial
phase: 79-peak-picking-symmetry-fix
source: [79-VERIFICATION.md]
started: "2026-06-08"
updated: "2026-06-08"
---

## Current Test

[awaiting human testing — blind CASE9 re-run]

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
result: [pending]
notes: |
  Per the project blind-UAT protocol (feedback_blind_uat memory), the orchestrating instance
  that executed Phase 79 is TAINTED and must NOT run this UAT. Run from a fresh `/clear`ed
  session. Verify merged.smi / final SMILES independently via RDKit — never trust agent
  self-report. This is the v9.0 milestone-ship gate, not a Phase-79 code deliverable.

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

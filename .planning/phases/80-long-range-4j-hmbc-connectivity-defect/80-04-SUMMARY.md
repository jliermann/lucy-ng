# Plan 80-04 Summary — Blind UAT Gate (v9.0 ship-gate)

**Status:** Gate FAIL — v9.0 does NOT ship. Outcome documented; Phase 81 proposed.

## What happened

- **Task 1 (pre-flight gate):** PASS. Full pytest suite 1054 passed; `elim_budget` + `is_plausible` mechanism confirmed live; skill-surgery markers verified (4J Deferral absent, ELIM Escalation present ×5, COSY explicit-range ×9); `80-ELIM-REGRESSION.md` exists with SC-3 PASS.
- **Task 2 (CASE9 blind run):** FAIL. A fresh blind instance ran `/lucy-ng:case` on CASE9 (C12H16O3) to completion (6 LSD iterations). Final 7 solutions are all non-aromatic bicyclic vinyl ethers; the correct para-benzoate `CC(C)OC(=O)c1ccc(C(C)O)cc1` is not among them. Independently RDKit-verified by the orchestrating instance — `verify_case_solution.py` → `passes: false`.
- **Task 3 (CASE1 regression run):** NOT RUN (moot — AND-gate already fails on CASE9).
- **Task 4 (AND-gate verdict):** Written to `80-UAT-VERDICT.md`. AND-gate = FAIL.

## Root cause (full analysis in 80-UAT-VERDICT.md)

Upstream peak-picking integrity defect, **not** the Phase-80 solver mechanism:

1. Default `snr_floor=3.0` (IUPAC LoD) returns ~50 baseline-ripple peaks at SNR ≈ 3 (incl. 13 impossible peaks > 220 ppm). The genuine ester carbonyl at 166.08 ppm (SNR 17) was lost in this noise band during the agent's manual curation (76 raw → 8 by eye, carbonyl dropped).
2. No overcount guard: `analyze symmetry` / `symmetry_analysis.py` only model undercount (`missing_carbons > 0`). The overcount case (76 vs 12) is silent. After 76→8 curation, the symmetry check even *confirmed* the carbonyl-free skeleton (8 signals + 4 equivalences = 12 C).
3. → DBE misallocated (extra O-ring instead of C=O) → benzene read as monosubstituted → correct para-benzoate never in the search space. ELIM escalation (elim_budget stayed 0; agent forced ring-BONDs instead) could not recover it.

## Delivered by Phase 80 (verified, retained)

- `LSDProblem.elim_budget` + ELIM emission decoupled from pylsd_mode (80-01)
- Schema surgery + pyLSD deprecation (80-01)
- Chemical plausibility pre-filter `is_plausible` (80-02)
- Skill surgery across 5 agent files: 4J-deferral reflex removed, ELIM escalation + COSY explicit-range protection added (80-03)
- SC-3 regression guard PASS — ibuprofen v4.0 4J case survives ELIM 1 0 (80-03)

These are correct and unit-green. The phase does not regress anything; it is blocked only by the upstream picker defect.

## Next

Phase 81 (FIX-08 — Peak-Picking Integrity): snr_floor default 3→5, expose `--snr-floor`, overcount guard + negative-`missing_carbons` alarm, nmr-chemist SNR/carbonyl rules, CASE9 regression test. Then re-run blind UAT and re-apply the AND-gate.

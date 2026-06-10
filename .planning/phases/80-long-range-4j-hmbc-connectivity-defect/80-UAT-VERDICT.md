---
status: fail
phase: 80-long-range-4j-hmbc-connectivity-defect
gate: v9.0 milestone-ship AND-gate
case9: fail
case1: not-run
and_gate: fail
ships: false
verified_by: orchestrating instance (RDKit + verify_case_solution.py, independent of agent self-report)
date: 2026-06-10
---

# Phase 80 Blind UAT Verdict

**SC-3 regression guard (Arm A + ELIM 1 0):** PASS — see `80-ELIM-REGRESSION.md`. Live LSD run on `arm_a.lsd` with `ELIM 1 0` returned 7 solutions; rank #1 = `CC(C)Cc1ccc(C(C)C(=O)O)cc1` (para-ibuprofen, 6 aromatic atoms, C13H18O2, RDKit-verified). The Phase-80 mechanism does not regress the v4.0 ibuprofen 4J case.

---

## CASE9 result: **FAIL**

- `scripts/verify_case_solution.py` (run on `analysis/iteration_04/solutions.smi`, C12H16O3): `passes: false` for every solution (no aromatic ring).
- Top solutions (final iteration, 7 total): **all 0 aromatic atoms** — non-aromatic bicyclic vinyl-ether / chromenol topologies. Formula C12H16O3 matches, structure does not.
- Correct para-benzoate `CC(C)OC(=O)c1ccc(C(C)O)cc1` in top-3: **NO** (0 exact matches across all 7).
- ELIM N used: **0 in all 6 iterations** — the Phase-80 ELIM escalation mechanism was never exercised.
- COSY equivalence pairs: written as `COSY X Y 3 3` (explicit-range protection present and used).
- Ring emergence: **silent-forced ring-BOND** — iteration_06 forced the benzene ring with 6 ring-BONDs (`1 3, 3 6, 6 2, 2 5, 5 4, 4 1`), which then collapsed to 0 solutions. Per plan 80-04 this classifies as FAIL.
- Path-changing interventions: blind run reverted to the old forced-ring anti-pattern instead of ELIM escalation.

## CASE1 result: **NOT RUN**

CASE1 regression run was not performed. Moot for the AND-gate — CASE9 already fails, so the AND-gate is FAIL regardless of CASE1.

---

## AND-gate: **FAIL → v9.0 does NOT ship**

Root cause is **upstream of the Phase-80 solver mechanism** (which is correctly built and unit-green). The defect is in **peak-picking integrity** — a recurrence of the Phase-78/79 carbonyl-handling failure family, now in a subtler form:

1. **The ester carbonyl (166.08 ppm) was dropped from the 13C inventory.** The current picker *does* surface it (intensity 2.08e6, **SNR 17.0**, ~5× the noise band), but with the default `snr_floor=3.0` (IUPAC Limit-of-Detection) it also returns ~50 baseline-ripple peaks at SNR ≈ 3.0–3.7, including 13 in the physically-impossible >220 ppm region (up to 296 ppm). The blind agent manually curated 76 raw peaks down to 8 by eye and dropped the carbonyl in the process.
2. **No overcount sanity check exists.** `analyze symmetry` / `symmetry_analysis.py` only model the *undercount* direction (`missing_carbons = expected − observed > 0` → equivalence). The *overcount* case (76 observed vs 12 expected) prints a meaningless negative with no alarm. Worse: after the agent's manual 76→8 curation, the symmetry check saw 12 − 8 = 4 and "confirmed" 4 equivalences — actively validating the carbonyl-free skeleton (four 2C-equivalences also sum to 12 C).
3. **Consequence:** DBE=5 was misallocated as benzene(4) + O-ring(1) instead of benzene(4) + C=O(1). The aromatic ring was read as monosubstituted instead of para-disubstituted. The correct para-benzoate was never in the search space before LSD ran. No solver mechanism (ELIM included) could recover it.

**Evidence (re-pick of CASE9/12 at higher SNR floor):**

| `snr_floor` | total peaks | impossible >220 ppm | carbonyl 166.08 |
|---|---|---|---|
| 3.0 (default) | 76 | 13 | present (SNR 17) but buried in 19-peak noise band |
| 5.0 | 29 | 0 | highest-ppm peak, stands alone above 150.80 |
| 8.0 | 20 | 0 | unchanged, clean |

Every real carbon has SNR ≥ 8; every noise peak has SNR ≈ 3.0–3.7. The signal/noise separation is excellent; only the threshold default is wrong.

## RDKit verification (independent)

- CASE9 correct SMILES `CC(C)OC(=O)c1ccc(C(C)O)cc1` RDKit parse: **yes** — formula C12H16O3, 6 aromatic atoms.
- CASE9 run solutions (7) RDKit check: all parse, all C12H16O3, **all 0 aromatic atoms** — none is the target.
- CASE1: not run.

---

## Disposition

- Phase 80 stays at the **open gate** (NOT marked complete). The Python mechanism (elim_budget, plausibility filter), skill surgery, and SC-3 regression guard are all delivered and verified; the milestone-ship gate fails on an upstream peak-picking defect.
- **Follow-up: Phase 81 (FIX-08 — Peak-Picking Integrity)** with scope:
  - (a) `snr_floor` default 3.0 → 5.0 for 13C picking
  - (b) expose `--snr-floor` in `lucy pick 1d`
  - (c) overcount guard (raw peaks vs formula) + alarm on `missing_carbons < 0` in `analyze.py` and `symmetry_analysis.py`
  - (d) nmr-chemist skill: SNR ≥ 5 = signal rule; "more signals than carbons = noise"; "a 160–180 ppm signal with SNR ≥ 5 is a C=O, never discard it"
  - (e) regression test: CASE9/12 @ k=5 yields the carbonyl, ≤ 30 peaks, none > 230 ppm; overcount guard fires on 76-vs-12
- Then re-run the blind UAT (CASE9 + CASE1, fresh instances per `feedback_blind_uat`) and re-apply this AND-gate.

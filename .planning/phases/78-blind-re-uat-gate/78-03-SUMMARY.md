# 78-03 Summary — CASE9 Blind UAT (UAT-04)

**Status:** Complete — **UAT-04 FAIL**
**Plan:** 78-03 (wave 2, autonomous: false — human-action blind run + bookkeeper evidence/forensics)

## What happened

- **Task 1 (human-action):** A blind CASE Team v4.0 session ran `/lucy-ng:case …/CASE9 C12H16O3`
  on 2026-06-03 (5 iterations, 211→4→18→12→incomplete iter 5).
- **Task 2 (bookkeeper):** Collected the four gate criteria from on-disk artifacts and added a
  forensic root-cause analysis (2026-06-08) when the run was found to have failed.

## Verdict: UAT-04 = FAIL

- **C1 (correctness) FAIL:** all 12 finals are phenyl-ether/acetal scaffolds; the true structure
  (4-(1-hydroxyethyl)benzoic acid isopropyl ester, `CC(O)c1ccc(C(=O)OC(C)C)cc1`) is absent from
  every iteration. `verify_case_solution.py` exits 0 but checks formula+aromatic only.
- **C2 (mechanism) CONDITIONAL:** SYME/DEFF NOT/SKEL=0, but the ring was forced via 6 ring-BONDs
  (documented D-04 escalation), not emergent — `lucy detect aromatic-cosy` had no input.
- **C3 (no intervention) FAIL:** governance-deadlock user re-route + outlsd `#`-comment parse bug.

## Root cause (proven from raw 13C, `…/CASE9/12`)

A single upstream peak-picking/symmetry defect:
1. Ester carbonyl at **166.08 ppm (SNR≈17)** dropped by `lucy pick 1d` — CDCl₃ triplet (4.6e7)
   dominates the max-relative threshold → DBE computed without carbonyl → forced extra ring.
2. 13C intensity doubling (129.94/125.31/22.10 = 2C signals) ignored → ring read as
   monosubstituted → no equivalence pairs → emergent-ring mechanism disabled.

The Phase-77 emergent-COSY mechanism is **not refuted** — it never received correct input.

## Artifacts

- `78-UAT-CASE9.md` — full evidence record + UAT-04 FAIL verdict + root-cause forensics

## Follow-up

Seeds Phase 79 (peak-picker SNR threshold / CDCl₃ exclusion + intensity-symmetry detection),
then CASE9 re-run blind.

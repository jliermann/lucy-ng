---
created: 2026-06-25
title: CASE4 exact truth (chamazulene regiochemistry) still excluded — azulene regiochemistry enumeration gap (NEW defect, distinct from MULT)
area: skill
files:
  - .claude/agents/lucy-lsd-engineer.md
  - .claude/agents/lucy-nmr-chemist.md
---

## Context — surfaced by the Phase-89 blind CASE4 re-run (UAT-01), 2026-06-25

The Phase-88 multiplicity fix WORKED and is verified: the blind run emitted
`[MULTIPLICITY-AMBIGUOUS]`, enumerated 3 ethyl families, searched ALL of them in their own
`iteration_NN_<family>/` dirs, the coverage_gate passed, and the final set is **15 [5,7]
di-methyl-ethyl azulenes** (RDKit-verified). The original defect (only the mono-methyl-iPr
class searched → di-methyl-ethyl class a-priori excluded) is GONE. The nmr-chemist even ruled
out the iPr class deterministically by H-budget (11 aliphatic H / 4 sp3 C → only 3×CH₃+1×CH₂).

**But the EXACT truth is still not reachable.** Chamazulene = 7-ethyl-1,4-dimethylazulene,
truth InChIKey `FVZVDQVUOAAMCG-UHFFFAOYSA-N` (RDKit; [5,7] azulene). It is **NOT** among the 15
final solutions (independently verified: none of the 15 block1s == FVZVDQVUOAAMCG; the agent's
own report also says chamazulene is absent — though the agent cited a WRONG chamazulene key
`UPRCJVNLNOWREJ`, a minor reference error). So the di-methyl-ethyl CLASS is reachable but the
specific 1,4-dimethyl-7-ethyl regiochemistry was never enumerated.

## The new defect class (distinct from the three known ones)

Multiplicity is now correct; the gap is **azulene regiochemistry / aromatic-connectivity
enumeration** on a non-benzenoid [5,7] core. The run's "complete data-consistent set" of 15
regiochemistries did not include the truth pattern. Open question to investigate:
- Is the truth regiochemistry wrongly EXCLUDED by the LSD constraint set (HMBC anchors /
  aromatic LIST grouping), i.e. an enumeration/constraint defect? OR
- Is it genuinely data-underdetermined here because CASE4's 2D is degraded
  (FID-reconstructed HSQC/HMBC; see `project_case4_azulene_fail`) + HOSE-13C is unreliable for
  azulenes (the run flags the 33.86-ppm carbon as unexplained by ANY of the 15 and the
  diagnostic 112.8-ppm C1/C3 under-predicted)?

Likely a mix. Either way the exact truth is not currently reachable for CASE4.

## Not a v9.1 blocker

Per the UAT-03 spirit, a newly-surfaced defect class need not be fixed in v9.1. Phase 88's
own requirements (MULT-01..04) are met and verified. This todo records the residual CASE4 gap
for a future milestone. Also minor: the analyst's chamazulene cross-check used a wrong
reference InChIKey — consider having `lucy identify` supply the reference rather than recalled.

## References
- Run artifacts: `…/active-lucy-ng-testprojects/CASE4/analysis/` (2026-06-25 run);
  `iteration_07_anchor_recovery/solutions.smi` (the 15 [5,7] candidates), `final_results.md`.
- `.planning/phases/89-blind-uat-validation-gate/89-UAT-TRACKING.md` (UAT-01 record).
- Related: `project_case4_azulene_fail` (degraded 2D + azulene HOSE-gap), `project_phase88_multiplicity`.

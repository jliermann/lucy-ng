# Phase 79 — Scope Seed: Peak-Picking & Symmetry-Detection Fix

**Status:** seed for `/gsd-discuss-phase 79` / `/gsd-plan-phase 79` (not a CONTEXT.md yet)
**Author:** bookkeeper (2026-06-08), from the Phase 78 CASE9 UAT failure + skill audit
**Source evidence:** `.planning/phases/78-blind-re-uat-gate/78-UAT-CASE9.md`,
`78-UAT-VERDICT.md`; memory `project_case9_uat_peakpick_rootcause`

---

## Why this phase exists

The v9.0 milestone gate FAILED at Phase 78: CASE1 UAT-03 PASS, **CASE9 UAT-04 FAIL**. CASE9
(4-(1-hydroxyethyl)benzoic acid isopropyl ester, C12H16O3) was never reached — all finals were
phenyl-ether/acetal scaffolds, ring forced via 6 ring-BONDs.

The root cause is **upstream of the Phase-77 LSD fix and has two layers** — a tooling defect
**and** a missing skill-level feedback loop. Fixing only the tooling would leave the agent blind
to the same failure mode on the next compound. **Phase 79 must address both layers.**

---

## Layer 1 — Tooling defect (peak-picker + symmetry)

Proven from raw 13C `…/CASE9/12`:

1. **Weak quaternary carbonyl masked.** Real ester C=O at **166.08 ppm, SNR ≈ 17** (int 2.08e6,
   MAD-noise 1.23e5) is **dropped** by `lucy pick 1d` (default). The **CDCl₃ triplet at 77 ppm
   (4.6e7)** dominates the scale; the max-relative threshold lands between 2.08e6 and 2.72e6, so
   130.16 (2.86e6) is picked but 166.08 (2.08e6) is not.
   → DBE=5 is computed without the carbonyl → forced extra ring → acetal mis-hypothesis.

2. **Intensity-symmetry ignored.** 13C intensity doubling encodes para-symmetry: 129.94 (1.81e7)
   and 125.31 (1.72e7) are 2C CH-pairs; 22.10 (1.70e7) is isopropyl (CH₃)₂; 150.80/130.16 (~3e6)
   are the two Cq. This was not used → ring read as monosubstituted → `lucy detect aromatic-cosy`
   returns nothing → emergent-ring mechanism disabled.

**Candidate fixes (to be confirmed in discuss/plan):**
- Peak-picker threshold: SNR-based (not max-relative), and/or **exclude the CDCl₃ solvent
  multiplet** (~77 ppm in CDCl₃; solvent-aware) before computing the threshold.
- Symmetry detection: use 13C peak **intensity** as a 2C-equivalence indicator (detect doubled
  signals), feeding `lucy analyze symmetry` / `lucy detect aromatic-cosy`.

**NOTE:** The Phase-77 emergent-COSY mechanism is NOT refuted — given correct para-symmetry input
(pairs 129.94≡, 125.31≡) it fires exactly as for CASE1. Do not touch it; just feed it correctly.

---

## Layer 2 — Skill defect: no feedback loop from solution quality back to peak-picking

Audit of the active skills (nmr-chemist, case.md, loop-patterns, solution-analyst, diagnostic)
shows peak-picking is **fire-and-forget** at the front of the pipeline, with **no sensor** for a
*clean-but-wrong* convergence. CASE1 produced LSD symptoms the system could catch; CASE9's missed
peak produced a clean (211→4→18→12) but wrong convergence — nothing triggered a re-look.

Concrete gaps (with file:line):

1. **Peak-picking runs once, agent then passive.** `lucy-nmr-chemist.md` workflow step 4 =
   single `lucy pick 1d`; detection "ONCE per compound, before first LSD iteration" (Section 5);
   step 10 = "Monitor TaskList for additional requests." No proactive return to the spectrum.

2. **The only "look again" hooks target LSD symptoms, not the 13C base assumption:**
   - `lucy-diagnostic.md:697` — incremental threshold lowering, but only for **quaternary with
     0 HMBC** (Solution Explosion), and it lowers the **HMBC** threshold, not a 13C re-pick.
   - `case.md:410` — "Re-examine DEPT-135 spectrum", only inside the **ELIM-thrashing** advisory.
   Both assume the peak already exists in the 13C pick; a never-picked carbonyl is invisible.

3. **The 4 loop-patterns key on `solution_count`, not quality.** `loop-patterns.md`:
   ELIM-Thrashing / Zero-Solution / Solution-Explosion / Constraint-Churning. CASE9 converged
   cleanly → **no loop fired** despite best MAE 4.86 ppm and all candidates QUESTIONABLE/IMPLAUSIBLE.

4. **solution-analyst detects bad quality but has no return path.** It correctly flags
   DBE-mismatch (`lucy-solution-analyst.md:103`), aromatic-mismatch (:113), IMPLAUSIBLE (:128).
   But there is no defined path "all solutions implausible → tell nmr-chemist the peak list may be
   incomplete → re-pick." The CASE9 run concluded "needs more experiments" instead of "re-pick".

5. **No DBE-insaturation self-check.** No agent verifies "DBE=5, benzene=4, where is the 5th —
   did I find a double bond / 2nd ring, or is a carbonyl missing that I failed to pick?" Pitfall 2
   only counts quaternaries already in the pick; an **empty 160–220 ppm region despite a DBE
   deficit** raises no flag.

**Candidate fixes (to be confirmed in discuss/plan):**
- **DBE-insaturation self-check** in nmr-chemist after picking: rings+double-bonds accounted for
  vs DBE; if a deficit coincides with an empty carbonyl region (160–220 ppm), flag → targeted
  low-threshold re-pick of that region before [SETUP-COMPLETE].
- **Quality loop-pattern (5th pattern):** "best MAE > tier threshold OR all top solutions
  IMPLAUSIBLE/QUESTIONABLE across N iterations" → advisory that **reactivates nmr-chemist** to
  re-pick 13C at lower threshold and re-check carbonyl region + intensity-symmetry. Wire into
  case.md detect_loops + loop-patterns.md + advisory-templates.md.
- Make the **intensity-symmetry check mandatory/procedural** in nmr-chemist (currently only a
  passing note in Pitfall 1: "Check HSQC intensities for doubled signals").

---

## After the fixes

Re-run CASE9 **blind** in a fresh instance (per `feedback_blind_uat`) via the fixed stack and
re-apply the Phase-78 AND-gate. v9.0 ships only if both CASE1 and CASE9 pass.

## Open questions for discuss-phase

- Is CDCl₃-multiplet exclusion solvent-detected (from Bruker params) or heuristic (~77 ppm)?
- Tooling change vs skill change boundary: which fixes are code (`lucy pick`/`lucy analyze
  symmetry`) vs skill-procedural (nmr-chemist DBE check, new loop-pattern)?
- Does the quality loop risk infinite re-pick loops? Need a bounded re-pick budget.
- Should the DBE self-check also cover N-containing formulas (not just carbonyls)?

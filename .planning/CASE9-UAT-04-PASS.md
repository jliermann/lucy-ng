# CASE9 UAT-04 — PASS (2026-06-11, Opus 4.8)

**Verdict:** CASE9 SOLVED. First successful blind solve of CASE9 in the project's history.

## Ground truth (nmrxiv D202)
isopropyl 4-(1-hydroxyethyl)benzoate — `CC(O)c1ccc(cc1)C(=O)OC(C)C`, C12H16O3, DBE 5. Para-disubstituted benzoate with an exocyclic isopropyl ester AND a benzylic alcohol (–CH(OH)CH₃). **No ring-OH.**

## Result (independently RDKit-verified by the orchestrator)
- Top structure: `CC(C)OC(=O)c1ccc(C(C)O)cc1` → RDKit-canonical **identical** to the D202 truth; formula C12H16O3.
- Genuine LSD solution (solutions.smi line 12, Kekulé `CC(O)C(=C1)C=CC(=C1)C(=O)OC(C)C` → canonicalizes to the truth).
- Rank 1 on both tiers: 11/12 carbons ≤3 ppm, greedy-MAE **1.17 ppm**, clean separation from rank 2 (10/12, MAE 5.64). Both O-CH (70.18→69.91, 68.46→68.27) correctly assigned; the single weak carbon is the side-chain quaternary (150.80→143.96, Δ6.84), honestly flagged Low — NOT rationalized away.

## Model gate: PASS
`## Team Models` block: all four teammates `claude-opus-4-8`, coordinator `claude-opus-4-8[1m]`, **0 MODEL MISMATCH**. The disclosure mechanism (case.md Step 4) confirmed the intended model actually ran.

## Mechanism: CONDITIONAL PASS (documented ring-BOND escalation)
- No SKEL; no hard PROP O (FIX-10 respected; G-PROP-EVIDENCE active).
- Emergent ring (cross-ring COSY equiv-pairs + DEFF F/FEXP) attempted for **3 iterations first** — benzene fraction stayed 6.3%→6.5%→4.7% (LSD builds the C=O *into* the ring → cyclohexadienones/pyranones instead of a para-benzene with exocyclic ester).
- Iteration 4: **Option-B explicit ring-BOND forcing**, properly logged (iteration #, reason = 3 consecutive non-aromatic iters, method = explicit BONDs, `ring_bond_forcing` field), SKEL prohibited/avoided, O-positions left OPEN for ranking. → benzene fraction 100%.
- Per the Phase-78 gate criteria (`.planning/case-uat-gate-criteria.md`): EMERGENT=clean-pass NO; documented ring-BOND escalation = **conditional pass**; silent/premature/SKEL = NO.

## Why this matters: the failures were substantially MODEL-driven
- Prior 2026-06-11 (earlier) and 2026-06-10 runs failed (wrong phenol ring-OH; the agent rationalized an 11.78 ppm prediction miss as a "HOSE limitation" and couldn't assign the second O-CH). Those ran on **Sonnet 4.6** via a silent fallback (`CLAUDE_CODE_SUBAGENT_MODEL=sonnet` in settings.json overrode the opus pins).
- On **Opus 4.8** the team self-corrected: the solution-analyst's Kekulé-prediction false alarm ("structure not in set, escalate") was caught by the coordinator, canonicalization applied, and the truth (line 12) ranked #1.
- The fix-stack (FIX-08 carbonyl picking, FIX-09 clean skills, FIX-10 no hard exclusion) created the necessary conditions; Opus 4.8 supplied the reasoning Sonnet could not.

## Remaining before v9.0 ships
1. **UAT-03 (CASE1 ibuprofen)** — blind re-run on Opus 4.8 to complete the Phase-78 AND-gate.
2. **FIX-11 / Phase 84** — Kekulé→aromatic canonicalization before `lucy predict c13` (the only confirmed defect from this run).
3. **(separate, not gating) D-04 emergent ring** — still unsolved; the ring had to be forced via documented BONDs.

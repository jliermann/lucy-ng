---
created: 2026-06-23
title: Solver hard-codes one aliphatic multiplicity model under degraded 2D data (truth excluded from search space)
area: skill
files:
  - .claude/agents/lucy-nmr-chemist.md
  - .claude/agents/lucy-lsd-engineer.md
  - .claude/agents/lucy-devils-advocate.md
  - .claude/commands/lucy-ng/case.md
  - .claude/commands/lucy-ng/references/loop-patterns.md
  - .claude/commands/lucy-ng/references/advisory-templates.md
---

## Problem

Surfaced by the **CASE4 (chamazulene) first VALID blind run, 2026-06-23 → FAIL**
(see `.planning/CASE-UAT-LOG.md` footnote ⁷). The correct structure was **never in
the solution set**, so none of the existing safety nets could recover it.

Ground truth chamazulene = **7-ethyl-1,4-dimethylazulene** (2×CH₃ + 1×ethyl).
All 21 final solutions were **mono-methyl-mono-isopropyl azulenes** (1×CH₃ + 1×iPr) —
a different substituent class (both happen to be C14H16). RDKit-verified: 0 hits.

### Root cause (a NEW defect class, distinct from the other two pending todos)

The aliphatic **multiplicity was not hard-determinable from the spectra**:
- HSQC (Exp5) was **NOT multiplicity-edited** (0 negative pixels) → CH/CH₂/CH₃ sign undeterminable.
- APT (Exp2) had **inconsistent phase** across the range → multiplicity globally unreliable.

The nmr-chemist correctly retracted its earlier "no CH₂" finding and left multiplicity
"OPEN". But the lsd-engineer then **hard-encoded a single leading model** —
`11/12/13 = CH₃, 14 = CH` → isopropyl — and **never handed LSD the ethyl model**
(`CH₃+CH₃+CH₂+CH₂`). Chamazulene was therefore **a priori excluded** from the search space.

Worse, the existing checks were actively defeated:
1. **devils-advocate had flagged the truth.** It explicitly called HMBC 11→13 (CH₃↔CH₃,
   2–3J) *"EVIDENCE FOR the ethyl model"* (a CH₃–CH₂ would give genuine 2–3J; in
   1,4-dimethylazulene the two methyls are far apart). The note said "if solutions poor,
   revisit aliphatic multiplicity."
2. **Ranking picked iPr anyway** (MAE 1.75) and then **rationalized the diagnostic HMBC
   away** as "3-bond gem-dimethyl coupling within isopropyl (DA's flag resolved)."
3. **The clean-but-wrong guardrail did NOT fire.** Its trigger is best-MAE > ~4 ppm OR all
   candidates implausible. A *wrong substituent class* scored MAE 1.75 ppm and was
   "PLAUSIBLE" → guardrail silent. 13C prediction does not separate iPr-methine from
   ethyl-CH₂ strongly enough to penalize the wrong class.

### Why this is the most dangerous of the three known defect classes

None of the existing nets apply:
- the v9.1 identity/naming gate doesn't help — the agent cleanly separated structure from
  name and even documented the ethyl model as an explicit alternative (no naming error here);
- the `lucy lsd rank` analyst-override can't recover a structure that is not in the set;
- the MAE>4 quality loop never triggers.

## Proposed fix (skill-level)

1. **Parallel multiplicity families.** When aliphatic multiplicity is NOT hard-determinable
   (non-multiplicity-edited HSQC AND/OR unreliable/phase-distorted APT/DEPT), the lsd-engineer
   must run BOTH viable multiplicity hypotheses as parallel LSD families (e.g. iPr-path
   `3×CH₃+CH` AND ethyl-path `2×CH₃+CH₂+CH₂`) and rank across the union — never hard-code one.
   The nmr-chemist must emit an explicit "multiplicity-ambiguous → enumerate families" signal.
2. **Tighter clean-but-wrong guardrail.** Add a trigger independent of MAE: if ≥2 chemically
   viable multiplicity families exist but only one was searched, do NOT accept — reopen and
   search the other(s). MAE alone cannot detect "wrong class searched."
3. **Forbid rationalizing-away a DA multiplicity flag** without searching the flagged
   alternative. A devils-advocate "evidence FOR model X" must force model X into the search,
   not be dismissed by the convergence narrative.

## Acceptance

- Re-run CASE4 blind: chamazulene's di-methyl-ethyl constitution appears in the solution set
  (truth reachable), regardless of which regioisomer ranks #1.
- A synthetic regression: a compound with non-edited HSQC + ambiguous iPr-vs-ethyl aliphatic
  pattern produces BOTH families in the searched space.

## References
- `.planning/CASE-UAT-LOG.md` footnote ⁷ + CASE4 06-23 summary row
- Run artifacts (quarantined): `…/active-lucy-ng-testprojects/CASE4/analysis/` (06-23 run);
  the 06-21 answer-key is at `…/_quarantine-answer-keys/CASE4-analysis-20260621-run/`
- Related (do NOT conflate): `2026-06-17-lucy-lsd-rank-scoring-defect`,
  `2026-06-21-final-identity-verification-gate`

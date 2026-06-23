---
created: 2026-06-21
title: Add a tool-based final identity-verification gate (stop parametric naming hallucination)
area: skill
resolves_phase: 87
files:
  - .claude/agents/lucy-solution-analyst.md
  - .claude/agents/lucy-devils-advocate.md
  - .claude/commands/lucy-ng/case.md
  - scripts/verify_case_solution.py
---

## Problem

Two blind UAT runs exposed the same failure class: **the solution-analyst attaches trivial
compound names to structures from the model's parametric memory, without any tool-based
verification** — and there is **no independent final gate** that checks the analyst's output.

- Run A (a fused non-benzenoid aromatic): the analyst rationalized the result against a
  WRONG self-recalled "literature" reference structure and accepted the wrong isomer →
  outright wrong structure delivered.
- Run B (a symmetric bis-lactam dye): the analyst put the CORRECT structure at rank 1
  (RDKit-verified) but mislabeled it with the wrong trivial name, called a *different*
  isomer by the target's name, asserted two name↔InChIKey mappings that were both
  backwards, and hedged confidence toward the wrong alternative. Structure right, report
  corrupted.

Root cause (confirmed by grep of the skill files):
1. `lucy-solution-analyst.md` has NO identity-derivation/verification step — its only
   RDKit instruction is Kekulé-aromatize-before-predict (FIX-11). Trivial names are pure
   parametric assertion.
2. `case.md` has NO final verification gate on the analyst's report (no independent check
   after [RANKING-COMPLETE]).
3. `lucy-devils-advocate.md` is a PRE-SOLVER gate only ("gate between constraint building
   and solving", "NEVER rank solutions"); it never reviews the final identity/report.
4. `scripts/verify_case_solution.py` (RDKit harness) exists but is invoked only by the
   human/orchestrator UAT gate, never by the in-run team.

Why this matters: an external reviewer with RDKit + a "find what's wrong" mandate catches
these trivially (generation-vs-verification asymmetry), but the in-run analyst self-certifies
its own narrative. The pipeline produces correct SMILES; the unreliable layer is the
recalled-name narrative bolted on top with no verification.

## Solution

Three complementary changes (v9.1):

1. **solution-analyst — derive, don't recall.** Identity must come FROM the SMILES via a
   tool: compute the InChIKey (RDKit `MolToInchiKey`) and/or generate a systematic name;
   never assert a recalled trivial name. If a trivial name is given at all, mark it
   tentative and always show the InChIKey/canonical SMILES alongside. Forbid
   "the truth fits worse than <recalled structure>" reasoning — compare only against
   tool-derived predictions, never a remembered structure.

2. **Final verification gate in case.md.** After [RANKING-COMPLETE], run an independent
   check before presenting results: RDKit-verify the top structure (formula/DBE match,
   canonical SMILES, InChIKey), and flag (a) any name↔structure claim not tool-derived,
   (b) over-confident hedging toward lower-ranked alternatives. Reuse
   `verify_case_solution.py` logic in-run, or spawn a fresh adversarial pass.

3. **Extend the adversary past the solver.** Either widen devils-advocate's mandate to
   review the FINAL report (not just LSD input), or add a dedicated final-review step.
   The team currently has an adversary for the solver INPUT but none for the OUTPUT.

Non-gating for the current campaign; queue for v9.1 alongside the `lucy lsd rank` scoring
defect (related: both are about the analyst/ranking layer being weaker than the structure
generation layer).

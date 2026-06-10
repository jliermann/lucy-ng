# CASE Mechanistic UAT Gate Criteria (ORCHESTRATOR / VERIFIER ONLY)

> **DO NOT load this file into a runtime CASE skill or any agent a blind elucidation
> instance reads.** These are pass/fail criteria for *evaluating* a completed blind CASE
> run from the outside. Relocated here from `~/.claude/commands/lucy-ng/case.md`
> (`uat_criteria` step) on 2026-06-10 under FIX-09 — baking them into the runtime skill
> leaked the expected outcome to the blind agent (it reported "Phase-78 gate passed"
> because it had read this text). The blind agent must derive the structure without
> knowing what "success" looks like.

These criteria are applied by the human/orchestrator (and by `scripts/verify_case_solution.py`
for the mechanical parts) when judging whether a CASE run on a para-substituted aromatic
test compound passed the v9.0 milestone gate.

## EMERGENT RING = CLEAN PASS
The aromatic ring appeared in LSD solutions WITHOUT any explicit ring-BOND constraints or
SKEL fragment. Cross-ring COSY equivalence pairs (from `lucy detect aromatic-cosy`) were the
sole mechanism. This is the intended behavior and the only unambiguous pass.

## RING-BONDS AS DOCUMENTED ESCALATION = CONDITIONAL PASS
Ring-BOND forcing is acceptable ONLY if ALL hold:
1. CASE-PROGRESS.md records the escalation decision with the iteration number it was applied at.
2. CASE-PROGRESS.md documents that emergent ring via cross-ring COSY pairs was attempted for
   at least 3 consecutive iterations first and did not produce aromatic solutions.
3. The ring-BOND constraints are the ONLY forcing mechanism — no SKEL benzene fragment was used.

If all three hold: conditional pass. Flag in the result report as
"ring-BOND escalation — conditional pass (documented)".

## SILENT RING-BONDS OR ANY SKEL = FAIL
Any of the following fails the gate regardless of whether the correct compound is found:
- Ring-BOND constraints defining the aromatic ring added WITHOUT the CASE-PROGRESS documentation
  above (undocumented escalation).
- `SKEL "c1ccccc1"` or any benzene SKEL fragment used at any iteration.
- Ring-BOND escalation used before 3 non-aromatic iterations completed (premature escalation).

`SKEL=0` in the verification-script output is necessary but NOT sufficient — undocumented
ring-BONDs also fail.

## Quick gate check (run by orchestrator AFTER a CASE run completes)
```bash
# SKEL usage across all iterations
grep -r "SKEL" <compound_path>/analysis/ 2>/dev/null | grep -v "^Binary"
# ring-BOND escalation documentation
grep -i "ring-bond escalation\|ring bond escalation\|forced.*ring\|ring.*forced" \
  <compound_path>/analysis/CASE-PROGRESS.md 2>/dev/null
# emergent ring in final solutions (no explicit ring-BONDs needed)
python3 scripts/verify_case_solution.py --smiles-file <compound_path>/analysis/iteration_NN/solutions.smi \
  --formula <formula>
```

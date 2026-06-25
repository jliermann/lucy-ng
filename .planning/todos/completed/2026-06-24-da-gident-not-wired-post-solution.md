---
created: 2026-06-24
title: devils-advocate G-IDENT post-solution advisory gate is defined but never invoked by case.md
area: skill
files:
  - .claude/commands/lucy-ng/case.md
  - .claude/agents/lucy-devils-advocate.md
---

## Problem

Phase 87 added a POST-solution advisory name↔structure gate (`G-IDENT`) to
`.claude/agents/lucy-devils-advocate.md` as the D-04 "second, genuinely independent
reasoning layer" (the binding deterministic check is `lucy identify`; the DA layer is
the independent LLM cross-opinion).

In the passing blind CASE5 re-run (2026-06-24), `lucy identify` fired correctly
(IDENT-01/02 binding layer ✅), but the **DA G-IDENT gate never ran**. CASE-PROGRESS.md
shows the devils-advocate only validating PRE-solver (iterations 1/2); after
`Solution-Analyst (RANKING-COMPLETE)` the coordinator went straight to
`Coordinator — CASE COMPLETE` and `Team shutdown`, never re-invoking the DA for the
post-solution name↔structure sanity check. So D-04's independent second layer is
defined-but-unwired.

## Why it didn't block Phase 87

Success Criterion 2 / IDENT-02 reads "devils-advocate **and/or** verify_case_solution.py"
— the binding `lucy identify` gate satisfies it on its own, and it did flag the recalled
name "indigo" as tentative. The phase passed. This is a robustness/defence-in-depth gap,
not a correctness failure.

## Fix direction

Wire the DA post-solution G-IDENT review into the case.md run sequence: after
`solution-analyst` emits RANKING-COMPLETE and before `CASE COMPLETE`/team shutdown, the
coordinator should spawn (or message) the devils-advocate to run G-IDENT on
`final_results.md` (the analyst's reported name vs the solved structure), independent of
`lucy identify`. Only then shut the team down. Add the trigger to case.md (and/or its
loop-patterns reference) so the gate that exists in the DA prompt is actually reached.

Verify by a subsequent blind CASE run showing a G-IDENT entry in CASE-PROGRESS.md.

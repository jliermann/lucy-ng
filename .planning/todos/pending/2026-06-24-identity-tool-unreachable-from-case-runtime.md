---
created: 2026-06-24
title: Phase-87 identity gate unreachable from CASE runtime (verify_case_solution.py is repo-only, not installed)
area: skill
resolves_phase: 87
files:
  - src/lucy_ng/cli/__init__.py
  - scripts/verify_case_solution.py
  - .claude/agents/lucy-solution-analyst.md
  - .claude/agents/lucy-devils-advocate.md
---

## Problem

Blind CASE5 UAT (2026-06-24, orchestrator-verified) found the Phase-87 deterministic
identity gate **did not execute at runtime**. The solution-analyst reported:
`final_results.md:15` → "**Tool verdict:** structure-derived (... `verify_case_solution.py`
not present in repo)".

Root cause: `scripts/verify_case_solution.py` lives only in the repo working tree. A real
CASE run executes in an NMR **data directory outside the repo**; the script is neither a
console entry point nor on PATH, and `lucy --help` has **no** identify/verify subcommand.
So the analyst (IDENT-01) and the binding gate (IDENT-02) cannot call it — the analyst fell
back to self-deriving the InChIKey + a recalled name (correctly marked tentative, so IDENT-03
still passed, but the binding/independent gate never ran).

This is exactly the CONTEXT.md-deferred decision biting back: a standalone `lucy identify`
CLI subcommand was deferred in favor of integrating into `verify_case_solution.py` (D-05).
But the script isn't delivered to where CASE runs, whereas the installed `lucy` CLI is
(CASE-PROGRESS shows `lucy lsd rank` working from the data dir).

## Fix (gap closure for Phase 87)

- Expose the identity logic via the installed CLI: add `lucy identify` (SMILES →
  InChIKey + canonical SMILES + two-path DB name lookup + verdict, `--format json`),
  reusing `derive_identity`/`_check_identity` so D-05's "one shared deterministic path"
  still holds (the script can import or thin-wrap the same function).
- Repoint `.claude/agents/lucy-solution-analyst.md` (derivation + tentative rendering)
  and `lucy-devils-advocate.md` (G-IDENT post-solution advisory gate) at the installed
  command instead of a repo-relative `scripts/...` path.
- Confirm the DB is found from a data dir via `DatabaseFinder.find_derep_database()` (it is).
- Re-run the blind CASE5 UAT to confirm the gate actually fires.

## What already works (do NOT redo)

- The deterministic core (`derive_identity`, two-path lookup, tolerant name_match,
  verdicts, dot-suffixed-accession + empty-name handling) is correct and in-repo tested
  (commits c5fe865, 2867dc4; 22 tests). Only its *delivery/reachability* is broken.
- IDENT-03 tentative rendering in the analyst prompt works (verified in the blind run).

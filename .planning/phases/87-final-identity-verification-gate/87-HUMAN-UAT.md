---
status: partial
phase: 87-final-identity-verification-gate
source: [87-VERIFICATION.md]
started: 2026-06-23T00:00:00Z
updated: 2026-06-24T00:00:00Z
---

## Current Test

GAP-87-A (tool unreachable from CASE runtime) is now CLOSED by gap-closure
87-03/87-04: `lucy identify` is an installed subcommand, executable-confirmed
reachable from outside the repo, agents repointed at it. The blind CASE5
re-run (test 1) is now PENDING again — this time it can actually exercise the
deterministic gate + DA G-IDENT end to end.

## Tests

### 1. Blind CASE re-run with reloaded agents (Phase-89 UAT-02)
expected: In a FRESH Claude Code session (required to reload the edited CASE agents), a blind CASE re-run (CASE5 sanitised = the IDENT acceptance test) shows: the solution-analyst calls `lucy identify` on the top SMILES, renders the tool-derived identity (never a recalled name), and marks non-confirmed trivial names `(tentative, unverified)`; the devils-advocate runs the G-IDENT post-solution advisory gate and flags any name↔structure mismatch.
result: PENDING re-run (after gap-closure 87-03/87-04).
  - Run 1 (2026-06-24, pre-gap-closure): STRUCTURE PASS (indigo, mislabel did NOT
    recur) + IDENT-03 tentative rendering PASS, but IDENT-01/02 FAILED at runtime
    because the tool was unreachable ("verify_case_solution.py not present in repo").
  - GAP-87-A now CLOSED: `lucy identify` is installed + executable-confirmed reachable
    from outside the repo; both agents repointed at it. A fresh blind CASE5 re-run is
    needed to confirm the analyst + DA G-IDENT actually fire the tool end to end.

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps

- **GAP-87-A (RESOLVED 2026-06-24 via gap-closure 87-03/87-04):** the deterministic
  identity tool is now delivered as the installed `lucy identify` subcommand (D-05:
  one shared core in `src/lucy_ng/identity.py`), reachable from a CASE data dir;
  analyst + devils-advocate G-IDENT repointed at it. Executable-confirmed (run from
  /tmp). Re-run the blind UAT to exercise it. Todo
  `2026-06-24-identity-tool-unreachable-from-case-runtime` resolved by Phase 87.
- **GAP-87-B (out of phase scope — reliability):** lsd-engineer goes idle after the
  solver finishes WITHOUT sending [ITERATION-COMPLETE]; the workflow sat idle ~5.5 h
  until the coordinator recovered the result from the filesystem (CASE-PROGRESS.md
  lines 75, 119). Sibling of the push-coordination defect. See todo
  `2026-06-24-case-completion-signal-stall`.

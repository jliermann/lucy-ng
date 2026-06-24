---
status: issues
phase: 87-final-identity-verification-gate
source: [87-VERIFICATION.md]
started: 2026-06-23T00:00:00Z
updated: 2026-06-24T00:00:00Z
---

## Current Test

Blind CASE5 re-run completed 2026-06-24; orchestrator-verified. One IDENT-03 pass,
two IDENT-01/02 integration gaps (deterministic tool unreachable at runtime).

## Tests

### 1. Blind CASE re-run with reloaded agents (Phase-89 UAT-02)
expected: In a FRESH Claude Code session (required to reload the edited CASE agents), a blind CASE re-run (CASE5 sanitised = the IDENT acceptance test) shows: the solution-analyst calls `check-identity` on the top SMILES, renders the tool-derived identity (never a recalled name), and marks non-confirmed trivial names `(tentative, unverified)`; the devils-advocate runs the G-IDENT post-solution advisory gate and flags any name↔structure mismatch.
result: ISSUES — partial.
  - STRUCTURE: PASS (independent RDKit). Top solution constitution = indigo
    (block1 COHYTHOBJLSHDF matches truth; only central C=C stereo differs,
    reported (Z) -YPKPFQOOSA-N vs true (E)-indigo -BUHFOSPRSA-N — not NMR-
    determinable, minor). Correctly distinguished from isoindigo/indirubin
    (block1 MLCPSWPIYHDOKG). The prior CASE5 indigo→"isoindigo" mislabel did
    NOT recur. Symmetry-based selection sound.
  - IDENT-03 (tentative presentation): PASS. final_results.md renders
    "Indigo / indigotin (tentative, unverified — recalled name, not DB-confirmed)"
    with InChIKey + canonical SMILES as the PRIMARY identity. The recalled name
    is NOT asserted as fact. The new analyst prompt loaded and behaved.
  - IDENT-01 (tool-derived identity via the shared deterministic path): FAIL at
    runtime. The analyst self-derived the InChIKey via RDKit but the Phase-87
    `check-identity` tool did NOT run — final_results.md line 15:
    "`verify_case_solution.py` not present in repo". The script lives only in the
    repo working tree; a CASE run executes in the NMR data dir (outside the repo)
    and the script is neither installed nor on PATH. `lucy --help` has no
    identify/verify subcommand. So the binding tool is undeliverable to the CASE
    runtime.
  - IDENT-02 (binding gate + DA advisory): FAIL at runtime. The script-based
    binding gate never executed (same root cause). No evidence of the POST-solution
    G-IDENT advisory gate in either devils-advocate section of CASE-PROGRESS.md
    (only the pre-solver gates ran).

## Summary

total: 1
passed: 0
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- **GAP-87-A (blocking IDENT-01/02):** the deterministic identity tool is unreachable
  from a CASE data dir. The CONTEXT.md-deferred `lucy identify` CLI subcommand is the
  real delivery mechanism (the `lucy` CLI IS installed + works from data dirs, e.g.
  `lucy lsd rank`). Gap closure: expose `derive_identity`/`check-identity` as
  `lucy identify` (or equivalent installed entry point) and point the analyst +
  devils-advocate G-IDENT at it. Then re-run the blind UAT. See todo
  `2026-06-24-identity-tool-unreachable-from-case-runtime`.
- **GAP-87-B (out of phase scope — reliability):** lsd-engineer goes idle after the
  solver finishes WITHOUT sending [ITERATION-COMPLETE]; the workflow sat idle ~5.5 h
  until the coordinator recovered the result from the filesystem (CASE-PROGRESS.md
  lines 75, 119). Sibling of the push-coordination defect. See todo
  `2026-06-24-case-completion-signal-stall`.

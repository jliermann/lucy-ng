# Plan 76-02 Summary — Milestone UAT Gate (blind run + bookkeeper)

**Status:** Done (terminal failure verdict per D-76-07). Milestone v9.0 does NOT ship.

## What happened

**Part A (manual blind gate):**
- CASE1 (C13H18O2): blind run completed in a fresh instance (4 LSD iterations). Artifacts copied to `uat-artifacts/case1/`. Workspace contamination (prior v8.0 `analysis/` revealing "ibuprofen" + a benzene.mol) was moved out of the CASE1 tree to `~/Dropbox/develop/data/nmrdata/_archive-CASE1-v8-analysis` before the run to preserve blindness.
- CASE9 (C12H16O3): NOT run — operator decision (2026-06-01). Deferred to Phase 77 re-UAT.

**Part B (bookkeeper, independent verification):** Ran `verify_case_solution.py` + LSD-provenance greps + intervention count against on-disk artifacts (never agent self-report). Wrote `VERIFICATION.md`.

## Verdict

- **UAT-03 (CASE1): SPIRIT-FAIL.** All literal grep checks pass (verify exit 0; BOND/COSY=14, DEFF F=2, SYME=0, DEFF NOT=0, SKEL=0; ibuprofen RDKit-confirmed, MAE 0.277). But the intended mechanism was NOT used: (1) `lucy lsd run` is broken (false success + garbage solutions.smi) → bypassed to direct lsd binary; (2) aromatic ring did not emerge — needed 6 forced ring BONDs (D-04 contradicted); (3) >0 coordinator rescue interventions (D-76-05 violated).
- **UAT-04 (CASE9): NOT RUN.**
- **Milestone v9.0: FAILED** (D-76-06 AND-gate).

## Deliverables produced

- `VERIFICATION.md` — evidence-backed FAILED verdict + forensics → Phase 77.
- CASE1 artifacts under `uat-artifacts/case1/` (solutions.smi, CASE-PROGRESS.md, iteration_04 LSD, ranking_results.json, final_results.md).
- (76-01 produced the verification harness + sanitisation record.)

## Routed to Phase 77 (priority order)

1. Fix `lucy lsd run` (`_invoke_outlsd`) — make it produce real solutions.smi and fail loudly on the outlsd error. Highest leverage; blocks any meaningful re-UAT.
2. Revisit D-04 emergent-aromatic premise (does the ring ever emerge, or is ring-BOND forcing the real intended path?).
3. Skill hygiene: retire deprecated `lucy-case-agent.md`; optional skill-creator audit (structure only, not domain).

## Key deviation from plan

- Plan expected `<workdir>/analysis/merged.smi`; the run produced per-iteration `solutions.smi` (no merge step in the single-primary path). Bookkeeper ran the harness on the final `iteration_04/solutions.smi`. Naming/plumbing gap noted in VERIFICATION.md.
- CASE9 omitted by operator decision (valid per D-76-07).

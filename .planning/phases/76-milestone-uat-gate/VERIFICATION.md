---
status: gaps_found
phase: 76-milestone-uat-gate
requirements: [UAT-03, UAT-04]
milestone: v9.0
verdict: FAILED
date: 2026-06-01
verified_by: bookkeeper (orchestrating instance, independent RDKit + grep checks against on-disk artifacts)
---

# Phase 76 — v9.0 Milestone UAT Gate: VERIFICATION

**Milestone verdict: FAILED (does NOT ship v9.0).**

- **UAT-03 (CASE1):** SPIRIT-FAIL — correct structure found, but NOT via the intended v9.0 mechanism.
- **UAT-04 (CASE9):** NOT RUN — deferred by operator decision (2026-06-01); routed to Phase 77 re-UAT.

Per D-76-06 (AND-gate) the milestone cannot be COMPLETE with one compound spirit-failing and the other unrun. Per D-76-07 a documented failure is a VALID terminal result for this phase; forensics below seed Phase 77.

---

## UAT-03 — CASE1 (Ibuprofen, C13H18O2)

**Source artifacts:** `uat-artifacts/case1/` (copied from `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/`, blind run 2026-06-01 11:07–13:36, 4 LSD iterations).

### Literal checks (D-76-02 native-constraint proof) — ALL PASS

| # | Check | Command | Result | Verdict |
|---|-------|---------|--------|---------|
| 1 | aromatic ring + formula | `verify_case_solution.py uat-artifacts/case1/solutions.smi C13H18O2` | exit 0; `pass:true`, aromatic_atoms 6, computed_formula C13H18O2 | PASS |
| 2 | output non-empty | `wc -l solutions.smi` | 1 SMILES (`CC(C)CC(=C1)C=CC(=C1)C(C)C(O)=O` = ibuprofen Kekulé) | PASS |
| 3a | BOND/COSY present | `grep -cE 'BOND|COSY'` | 14 | PASS (≥1) |
| 3b | DEFF F present | `grep -c 'DEFF F'` | 2 | PASS (≥1) |
| 3c | SYME absent | `grep -cE '^SYME'` | 0 | PASS (=0) |
| 3d | DEFF NOT absent | `grep -c 'DEFF NOT'` | 0 | PASS (=0) |
| 3e | SKEL absent | `grep -cE '^SKEL'` | 0 | PASS (=0) |

By the letter of the grep criteria, CASE1 passes. Structure is RDKit-confirmed ibuprofen (canonical `CC(C)Cc1ccc(C(C)C(=O)O)cc1`, MAE 0.277 ppm, 10/10 signals).

### Substantive checks (D-76-01 primary path, D-76-05 interventions, D-04 emergent) — FAIL

| Criterion | Finding | Verdict |
|-----------|---------|---------|
| D-76-01: solved via `lucy lsd run` (intended single primary path) | NO. `lucy lsd run` reported false success and wrote a garbage `solutions.smi` (`outlsd: This is not a file for OUTLSD.`). Agent diagnosed it in iteration 1 and bypassed to the direct `lsd` binary + `outlsd 5`. Independently reproduced on the iteration_04 LSD file in a clean tmpdir. | FAIL |
| D-04: aromatic ring EMERGENT (no forcing) | NO. Iteration 1 (COSY equiv + DEFF F ring-exclusion per the D-04 recipe) yielded 368 solutions, ALL non-aromatic (cyclohexadienyl). The benzene ring appeared only after the coordinator added 6 explicit ring BONDs (`BOND 2 4/4 6/6 3/3 7/7 5/5 2`) in iteration 2. SKEL=0 passes only because BOND was used instead of SKEL — the ring was still force-constructed. | FAIL |
| D-76-05: 0 path-changing bypass interventions | NO. CASE-PROGRESS "ENDERGEBNIS" lists 8 coordinator interventions; grep matches "Tooling-Intervention (Solution-Konvertierung)" (solver-path switch) and "Intervention an lsd-engineer" (forced COOH via BOND 1 15). Substantive path-changers: forced ring (#2), forced COOH (#3), re-added discriminating HMBC 1 13 (#4), solver-path switch (#1). | FAIL |
| D-76-01: extended-range `HMBC X Y 2 4` for flagged 4J | NOT EXERCISED. 4J candidates handled by reassignment/removal (HMBC 9 10 → grouped (8 9) 10), not by the intended extended-bond-range mechanism. | not exercised |

**UAT-03 verdict: SPIRIT-FAIL.** Ibuprofen was found, but through the same failure pattern v9.0 was meant to eliminate (broken primary path + forced ring + coordinator rescue) — the v8.0 pattern in different syntax (BOND ring instead of SKEL fragment).

## UAT-04 — CASE9 (C12H16O3)

**NOT RUN.** Operator decided (2026-06-01) not to run CASE9 in this phase, since the CASE1 forensics already establish two blocking code/design defects that must be fixed before any re-UAT is meaningful. CASE9 remains the Phase-77 generalization re-UAT target. Dataset confirmed blind and ready (`76-SANITISATION-VERIFIED.md`).

---

## Forensics → Phase 77 (D-76-07)

Failure modes, by stage, highest leverage first:

1. **TOOLING (blocking, highest leverage): `lucy lsd run` is broken.** It reports "LSD completed successfully / Solutions found: N" and exits 0 while writing a `solutions.smi` containing `outlsd: This is not a file for OUTLSD.`. The Phase-73 `_invoke_outlsd` internal step invokes outlsd incorrectly (cf. header-strip note in project-lsd-native-commands memory: `tail -n +10 compound.sol | outlsd 5`). The entire v9.0 "single primary path" premise (D-76-01) rests on this. Fix `_invoke_outlsd` AND make the runner fail loudly (non-zero exit, no false "success") when outlsd output is the error string. Then correct the now-false Phase-73 claim in `agents/lucy-lsd-engineer.md:124-130`.
2. **DESIGN: D-04 emergent-aromatic premise does not hold.** Native BOND/COSY-equivalence + DEFF F/FEXP did NOT yield an aromatic ring on the full CASE1 blind run (368 non-aromatic solutions). Decide: either (a) make explicit ring-BOND construction the documented intended path (and rewrite D-04 + the D-76 mechanistic criterion accordingly), or (b) find native constraints that genuinely force aromaticity. The "Arm A 2/2 aromatic" Phase-74 validation did not generalize.
3. **SKILL HYGIENE (lower urgency): contradiction/bloat.** `~/.claude/agents/lucy-case-agent.md` (1291 lines, DEPRECATED v6.0) still carries active-looking frontmatter and the stale manual `outlsd 5 < compound.sol` workflow that contradicts the current lsd-engineer.md. Remove/retire it. Optionally run the skill complex (~5275 lines / 11 files) through skill-creator as an AUDIT lens (dead-file detection, dedup, trigger-description measurement) — NOT as a domain fix; content decisions stay domain-driven.

**Note:** root cause was tested, not assumed — the `lucy lsd run` bypass is a real CODE bug, not a stale-skill artifact (the skill correctly tells the agent to use `lucy lsd run`; the tool lies). See memory `project-lucy-lsd-run-broken-v9`.

## What this phase DID deliver

- `scripts/verify_case_solution.py` + `tests/test_verify_case_solution.py` (8 tests green) — the committed, reusable independent-verification harness (UAT-03/04 infrastructure). Reusable for the Phase-77 re-UAT.
- `76-SANITISATION-VERIFIED.md` — both datasets confirmed blind.
- This forensic verdict, seeding Phase 77.

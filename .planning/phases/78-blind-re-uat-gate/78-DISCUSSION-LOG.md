# Phase 78: Blind Re-UAT Gate (CASE1 + CASE9) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02
**Phase:** 78-blind-re-uat-gate
**Areas discussed:** Blind-instance protocol, CASE9 sanitisation pre-check, Evidence collection & verification, Sequencing/budget/failure

---

## Blind-instance protocol (→ D-78-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Read-prohibitions + advisory bookkeeper | Fresh /clear'd instance, handoff = only path + formula, hard prohibition on reading .planning/REQUIREMENTS/memory/git log, bookkeeper advisory-only | ✓ |
| Physical isolation (separate checkout) | Separate git checkout/worktree with .planning/+memory+REQUIREMENTS removed so leakage is physically impossible; more setup | |

**User's choice:** Read-prohibitions + advisory bookkeeper.
**Notes:** Physical isolation retained as an acceptable fallback if leakage risk is judged too high at plan time; not the default.

---

## CASE9 sanitisation / blindness pre-check (→ D-78-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, pre-run sanitisation/blindness check | First step of Phase 78: bookkeeper checks CASE9 (molecular-formula.txt, Bruker titles, folder names, audit) for identity leakage, sanitises if needed, before the blind instance sees it; CASE1 quick re-verify | ✓ |
| No, assume CASE9 clean | No pre-check; run blind directly | |

**User's choice:** Yes — pre-run sanitisation/blindness check as the first Phase-78 step.
**Notes:** CASE9 is new to the UAT (CASE1 is the known-sanitised ibuprofen), so its blindness state must be confirmed before the run.

---

## Disqualifying-intervention definition (→ D-78-03 step 4, D-78-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Path-/structure-hints = fail, generic nudges allowed | Path switch or structural hints disqualify; generic process nudges (no answer/path leak) allowed; borderline = conservatively fail. Matches roadmap "0 path-changing" wording | ✓ |
| Zero-Touch (any intervention counts) | 0 bookkeeper messages allowed; cleaner but unrealistic vs process dead-ends | |

**User's choice:** Path-/structure-hints = fail, generic nudges allowed.
**Notes:** Borderline cases scored conservatively as path-changing (= fail). Zero-Touch rejected as unrealistic against constraint-loss-type dead-ends.

---

## Sequencing, budget & failure handling (→ D-78-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Both independent, one-shot, forensics on fail | Both compounds run fully even if CASE1 fails (max diagnostic data); one blind run each; AND-gate; failure → forensics doc → D-76-07 follow-up, v9.0 does not ship | ✓ |
| Fail-fast on CASE1 fail | Stop before CASE9 if CASE1 fails; saves effort, less diagnostic data | |

**User's choice:** Both independent, one-shot, forensics on fail.
**Notes:** A re-run after the result is known would no longer be blind → strictly one-shot per compound. Failure is a valid documented outcome, not a retry-until-pass trigger.

## Claude's Discretion

- Format/location of per-compound evidence records + failure forensics doc.
- Exact grep predicates / helper for mechanism checks (reuse verify_case_solution.py-adjacent tooling; do not modify the harness itself).
- Whether to drive the blind instance via Task/Agent with a blind prompt vs a literally separate terminal (both satisfy D-78-01).
- Order of the CASE9 pre-check vs first blind run.

## Deferred Ideas

- `lucy lsd verify-uat` CLI promotion of verify_case_solution.py.
- CASE2–CASE8 UAT broadening (until CASE1+CASE9 pass).
- Any code fix for a defect surfaced during the blind run → forensics + D-76-07 follow-up phase, not Phase 78.

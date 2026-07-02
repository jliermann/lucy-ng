---
phase: 88-aliphatic-multiplicity-robustness
plan: 02
subsystem: case-skill
tags: [case-agents, multiplicity, lsd, nmr-chemist, lsd-engineer, prompt-edit]

# Dependency graph
requires:
  - phase: 88-01
    provides: "lucy pick hsqc --format json multiplicity_edited boolean (the programmatic flag the nmr-chemist reads)"
provides:
  - "nmr-chemist emits a deterministic [MULTIPLICITY-AMBIGUOUS] signal with a capped viable_families list (MULT-04)"
  - "lsd-engineer runs each viable family as a separate fully-constrained LSD run in iteration_NN_<family>/ and ranks across a deduped union (MULT-01)"
  - "SEARCHED-not-RANKED coverage rule encoded in the lsd-engineer (a conversion-skipped large family still counts as searched)"
affects: [88-03, 89-blind-uat]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deterministic multiplicity-ambiguity signal combining a programmatic HSQC boolean with the chemist's APT/DEPT reliability verdict (necessary-but-not-sufficient)"
    - "Per-family parallel LSD search (one fully-constrained run per whole-molecule multiplicity partition) + deduped concatenate-then-one-rank union"

key-files:
  created: []
  modified:
    - .claude/agents/lucy-nmr-chemist.md
    - .claude/agents/lucy-lsd-engineer.md

key-decisions:
  - "MULTIPLICITY-AMBIGUOUS trigger is an explicit AND/OR: multiplicity_edited=false is necessary-but-not-sufficient; it combines with the chemist's APT/DEPT reliability verdict so an edited HSQC with clean DEPT-135 is NOT ambiguous (RESEARCH Pitfall 3)"
  - "No numeric detector threshold placed in the prompt — the negative-cross-peak detector that produces multiplicity_edited lives in pick.py per D-05; the chemist only READS the boolean"
  - "Union ranking uses the concatenate-then-ONE-rank path with an EXPLICIT canonical-SMILES dedup before lucy lsd rank (the parser does not dedup — RESEARCH Pitfall 1)"
  - "SEARCHED-not-RANKED coverage rule encoded: a >~50-solution family that skips solutions.smi conversion (the anti-stall rule) is still recorded as searched and not dropped from coverage/union"

patterns-established:
  - "Per-family LSD runs differ ONLY in the MULT block; all other constraints (HSQC, HMBC, ring exclusion DEFF F1/F2/FEXP, BOND C=O, COSY equiv, fragment DEFF/FEXP, inventory) carry forward identically per read-previous-never-reconstruct"
  - "Sequential-with-fallback is explicitly REJECTED as the CASE4 silent-exclusion failure mode"

requirements-completed: [MULT-04, MULT-01]

# Metrics
duration: ~12min
completed: 2026-06-25
---

# Phase 88 Plan 02: Aliphatic Multiplicity Robustness (CASE producer-agent wiring) Summary

**The nmr-chemist now emits a deterministic `[MULTIPLICITY-AMBIGUOUS]` signal (programmatic HSQC `multiplicity_edited` boolean combined with its APT/DEPT reliability verdict) listing the capped viable whole-molecule families, and the lsd-engineer runs EACH viable family as a separate fully-constrained LSD run in its own `iteration_NN_<family>/` sub-dir and ranks across a deduped union — replacing the CASE4 hard-coded single-model path that excluded the chamazulene truth.**

## Performance

- **Duration:** ~12 min (incl. full pytest suite)
- **Tasks:** 2
- **Files modified:** 2 (both CASE-team agent prompts)

## Accomplishments

- **Task 1 (MULT-04, nmr-chemist):** Added Section 5b "Aliphatic Multiplicity Ambiguity Detection (MULT-04)". Defined the deterministic AND/OR trigger — (a) `lucy pick hsqc --format json` reports `multiplicity_edited: false` (read the field, do not eyeball) AND/OR (b) APT/DEPT phase-unreliable — with the explicit statement that `multiplicity_edited: false` is NECESSARY-but-NOT-SUFFICIENT (an edited HSQC with clean DEPT-135 is NOT ambiguous). Enumerates viable whole-molecule CH3/CH2/CH partitions consistent with formula/H-count/DBE (CASE4 iPr `3×CH3+CH` vs ethyl `2×CH3+CH2+CH2` worked example), caps at 3 with documented truncation, and emits `[MULTIPLICITY-AMBIGUOUS]` (basis + numbered `viable_families:` list) IN ADDITION to `[SETUP-COMPLETE]`. Wired into workflow steps 6c and 8a. No numeric detector threshold in the prompt (lives in pick.py per D-05).
- **Task 2 (MULT-01, lsd-engineer):** Added "Per-Family Multiplicity Search (MULT-01)" wired to `[MULTIPLICITY-AMBIGUOUS]`. Each viable family → ONE fully-constrained LSD run in its own `iteration_NN_<family>/` sub-dir (e.g. `iteration_03_iPr`, `iteration_03_ethyl`), differing ONLY in the MULT block (two-block CASE4 illustration shown). Sequential-with-fallback is explicitly REJECTED as the CASE4 failure mode. Encoded the SEARCHED-not-RANKED coverage rule (a conversion-skipped large family, >~50 solutions, is still searched and not dropped). Union ranking = concatenate per-family `solutions.smi` into `analysis/union_solutions.smi`, DEDUP by canonical SMILES (parser does not dedup), then ONE `lucy lsd rank` across the union, reporting the winning family identity. Wired into workflow step 2a.
- Both files carry the fresh-session reload HTML comment (repo `.claude/` symlinked to `~/.claude`; validated by blind CASE4 UAT-01 / Phase 89, not unit tests).

## Task Commits

Each task was committed atomically:

1. **Task 1: nmr-chemist [MULTIPLICITY-AMBIGUOUS] + viable families** — `636ad5a` (feat)
2. **Task 2: lsd-engineer per-family runs + deduped union ranking** — `ae8b3dc` (feat)

## Files Created/Modified

- `.claude/agents/lucy-nmr-chemist.md` — New Section 5b (MULT-04) + workflow steps 6c/8a; deterministic `[MULTIPLICITY-AMBIGUOUS]` emission with capped `viable_families` list.
- `.claude/agents/lucy-lsd-engineer.md` — New "Per-Family Multiplicity Search (MULT-01)" section + workflow step 2a; per-family `iteration_NN_<family>/` runs, SEARCHED-not-RANKED coverage rule, deduped union ranking.

## Decisions Made

- **Trigger is genuinely combined, not boolean-only:** the prompt states `multiplicity_edited=false` is necessary-but-not-sufficient and must be combined with the APT/DEPT reliability verdict, directly addressing RESEARCH Pitfall 3 (an edited HSQC + clean DEPT-135 must NOT be flagged ambiguous).
- **No threshold in the prompt:** the detector stays in `pick.py` (D-05); the chemist only reads the boolean — keeps the markdown declarative and avoids drift from the code-side detector.
- **Union path = concatenate-then-one-rank with explicit dedup** (D-01 discretion): chosen over per-family-then-merge because a single `lucy lsd rank` across the deduped union is the simplest faithful cross-family ranking; the explicit canonical-SMILES dedup is mandatory because the parser does not dedup (RESEARCH Pitfall 1).

## Deviations from Plan

None — plan executed exactly as written. Both grep gates exit 0; both fresh-session notes present; no numeric threshold in the nmr-chemist prompt.

## Issues Encountered

- A backgrounded pytest invocation produced an empty output file (harness quirk); re-ran in the foreground to confirm the suite: **1128 passed, 7 skipped, 1 xfailed, 0 failed** in ~6 min. No Python changed in this plan, so this is a clean no-regression check.

## Known Stubs

None — these are prompt edits to existing agents; no stub data sources introduced.

## Validation Note (functional acceptance deferred)

These are CASE-agent MARKDOWN PROMPT edits. A **fresh Claude Code session is required to reload** both edited agents (note embedded in both files). Runtime behavior is NOT unit-tested this session — functional acceptance is the **blind CASE4 re-run (UAT-01, Phase 89)**: chamazulene's di-methyl-ethyl constitution must appear in the searched solution set. This plan is grep-asserted now (both gates pass).

## Next Phase Readiness

- MULT-04 + MULT-01 producer-agent wiring is complete and grep-asserted. Plan 88-03 can build the deterministic pre-accept coverage gate (D-04/MULT-02) on top of the `[MULTIPLICITY-AMBIGUOUS]` `viable_families` contract and the SEARCHED-not-RANKED rule encoded here.
- devils-advocate DA-flag binding (D-06/MULT-03) and case.md orchestration of the coverage gate remain for the rest of the phase.

## Self-Check: PASSED

- .claude/agents/lucy-nmr-chemist.md: FOUND
- .claude/agents/lucy-lsd-engineer.md: FOUND
- Commit 636ad5a: FOUND
- Commit ae8b3dc: FOUND
- nmr-chemist grep gate (MULTIPLICITY-AMBIGUOUS + multiplicity_edited + viable_families + fresh): PASS
- lsd-engineer grep gate (iteration_NN_ + MULTIPLICITY-AMBIGUOUS + dedup + searched + fresh): PASS

---
*Phase: 88-aliphatic-multiplicity-robustness*
*Completed: 2026-06-25*

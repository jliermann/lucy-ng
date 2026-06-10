---
phase: 81-peak-picking-integrity-fix-08
plan: 03
subsystem: skill
tags: [nmr-chemist, snr, peak-picking, carbonyl, skill-update]

# Dependency graph
requires:
  - phase: 80-long-range-4j-hmbc-connectivity-defect
    provides: "Root-cause evidence (UAT-VERDICT.md): snr_floor=5 table, carbonyl-drop forensics, overcount diagnosis"
provides:
  - "Pitfall 10: SNR floor rule — SNR >= 5 = signal, SNR < 5 = noise; overcount = noise not symmetry"
  - "Pitfall 11: Carbonyl never discard — 160-180 ppm SNR >= 5 is always real"
  - "Section 4 SNR cutoff note: explicit accept/reject threshold independent of quality tier"
  - "Section 5a DBE check updated from 'SNR 3-20' to 'SNR >= 5' with explanatory note"
affects: [81-04-regression-test, blind-uat-case9, lucy-nmr-chemist]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Skill rules encode UAT failure forensics as explicit numbered pitfalls with CRITICAL tags"

key-files:
  created: []
  modified:
    - /Users/steinbeck/.claude/agents/lucy-nmr-chemist.md

key-decisions:
  - "Four surgical edits only — no section rewrites; new pitfalls appended after existing Pitfall 9"
  - "Section 5a DBE check updated in-place to remove contradictory SNR 3-20 language"

patterns-established:
  - "SNR >= 5 is the universal signal/noise boundary in the nmr-chemist skill"

requirements-completed:
  - FIX-08

# Metrics
duration: 8min
completed: 2026-06-10
---

# Phase 81 Plan 03: nmr-chemist SNR/Carbonyl Skill Rules Summary

**Three new pitfalls added to lucy-nmr-chemist.md encoding the Phase-80 CASE9 root-cause: SNR floor (>= 5), overcount-is-noise, and carbonyl-never-discard for 160-180 ppm**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-10T09:00:00Z
- **Completed:** 2026-06-10T09:08:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added Pitfall 10 (SNR floor CRITICAL): SNR >= 5 = signal; overcount = noise not symmetry; re-pick at snr_floor 5 if observed > formula carbons
- Added Pitfall 11 (Carbonyl never discard): 160-180 ppm with SNR >= 5 is always a real C=O — loss of this peak misallocates DBE and excludes the correct structure before LSD runs
- Added explicit SNR cutoff note before the S/N Quality Tiers table in Section 4 (previously the table had no accept/reject threshold at all)
- Updated Section 5a DBE self-check "SNR 3-20" language to "SNR >= 5" with explanatory note that genuine carbonyls have SNR >= 8 in typical Bruker 13C

## Task Commits

The skill file lives outside the git repository (`~/.claude/agents/`) and is not git-tracked. No task commit for the skill edit. Only the SUMMARY.md is committed.

1. **Task 1: Add three SNR/carbonyl rules to lucy-nmr-chemist.md** - applied directly (file outside repo)

**Plan metadata commit:** see below

## Files Created/Modified

- `/Users/steinbeck/.claude/agents/lucy-nmr-chemist.md` - Four targeted surgical edits; 16 lines added

## Decisions Made

- Four surgical edits only — no section rewrites, no renumbering of existing pitfalls, no changes to existing content beyond the one Section 5a line.
- The SNR cutoff note in Section 4 was placed immediately before the S/N Quality Tiers table header so a reading agent sees the hard cutoff before the tier labels.
- Section 5a update kept the existing FLAG wording intact; only the threshold phrase was changed and an explanatory parenthetical added.

## Deviations from Plan

None — plan executed exactly as written. All four edits applied as specified.

## Verification Results

```
grep -c "SNR >= 5" /Users/steinbeck/.claude/agents/lucy-nmr-chemist.md  -> 4 (plan requires >= 3)
grep -in "never discard"  -> 1 match (Pitfall 11, line 73)
grep -in "overcount"      -> 1 match (line 69); "more signals than carbons" -> 1 match (line 70)
grep "Pitfall 10"         -> 1 match
grep "Pitfall 11"         -> 1 match
python yaml.safe_load     -> YAML OK (frontmatter not corrupted)
```

All six verification conditions satisfied.

## Issues Encountered

None.

## Next Phase Readiness

- 81-03 complete. Skill rules are live for any fresh blind agent immediately.
- 81-04 (regression test: CASE9/12 @ snr_floor=5) can now proceed — it tests both the tooling changes from 81-01/02 and the skill rules from 81-03.
- After 81-04, the blind UAT re-run (CASE9 + CASE1, fresh instances) applies the AND-gate.

## Threat Flags

None — text-only edit to a local Markdown skill file; no new code paths, no network exposure.

## Known Stubs

None.

## Self-Check: PASSED

- `/Users/steinbeck/.claude/agents/lucy-nmr-chemist.md` exists and contains all four edits (verified via grep)
- YAML frontmatter intact (python yaml.safe_load exits 0)
- SUMMARY.md created at `.planning/phases/81-peak-picking-integrity-fix-08/81-03-SUMMARY.md`

---
*Phase: 81-peak-picking-integrity-fix-08*
*Completed: 2026-06-10*

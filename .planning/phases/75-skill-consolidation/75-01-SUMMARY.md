---
phase: 75-skill-consolidation
plan: "01"
subsystem: agent-skills
tags: [lsd-engineer, native-lsd, syme, deff-not, ring-exclusion, single-path, skill-consolidation]

# Dependency graph
requires:
  - phase: 72-design-re-validation
    provides: "D-01/D-02/D-03/D-04 locked decisions: native commands, single solver path, HMBC 2 4 primary 4J mechanism, SKEL escalation-only"
  - phase: 74-constraint-preservation-and-merge
    provides: "ring3/ring4 filter files bundled in lucy-ng; lucy lsd run auto-produces solutions.smi (Phase 73)"
provides:
  - "lucy-lsd-engineer.md teaches BOND/COSY as native SYME replacement with ground-truth examples and equiv-pair tagging"
  - "lucy-lsd-engineer.md teaches DEFF F1/F2 + FEXP as native ring exclusion (F1/F2 reserved, F3+ for fragment)"
  - "lucy-lsd-engineer.md step 11 has PRIMARY PATH (lucy lsd run, unconditional) and FALLBACK PATH (pylsd, 3-condition gate)"
  - "lucy-lsd-engineer.md has no manual outlsd 5 < compound pipe instructions"
  - "lucy-lsd-engineer.md has HMBC X Y 2 4 in main HMBC correlations block (not only in fallback subsection)"
  - "pyLSD section demoted from ### to #### in §1 command reference"
  - "D-04 SKEL-as-escalation-only note present in step 11"
affects:
  - "75-02 (devils-advocate updates must match cosy_equiv_pairs, ring_exclusion_enabled)"
  - "75-03 (case.md and references updates must match COSY_equiv= field name)"
  - "CASE team agent — lsd-engineer reads this skill at spawn time"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "F1/F2 reserved for ring exclusion, F3+ for fragment goodlist — prevents filter name collision"
    - "COSY lines tagged ; equiv-pair to distinguish equivalence-derived from peak-data COSY"
    - "cosy_equiv_pairs inventory field replaces syme_pairs"
    - "ring_exclusion_enabled boolean replaces deff_not_patterns array in inventory"

key-files:
  created: []
  modified:
    - "~/.claude/agents/lucy-lsd-engineer.md - all SYME/DEFF NOT instructions replaced with native equivalents; step 11 restructured to PRIMARY/FALLBACK; outlsd pipe removed; D-04 SKEL note added"

key-decisions:
  - "cosy_equiv_pairs replaces syme_pairs in constraint inventory schema (DA must match in 75-02)"
  - "ring_exclusion_enabled boolean added alongside deprecated deff_not_patterns: [] for backward compat"
  - "Fragment persistence rule updated to reference ring exclusion DEFF F/FEXP (not the deprecated DEFF NOT)"

requirements-completed: [SKILL-01, SKILL-02]

# Metrics
duration: 4min
completed: 2026-05-24
---

# Phase 75 Plan 01: LSD Engineer Native-Command and Single-Path Rewrite Summary

**lucy-lsd-engineer.md rewritten to teach BOND/COSY native SYME replacement and DEFF F1/F2+FEXP native ring exclusion, with step 11 restructured to PRIMARY/FALLBACK single-path solver guidance per D-02**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-05-24T16:04:49Z
- **Completed:** 2026-05-24T16:08:43Z
- **Tasks:** 2 (Task 1: SYME edits A-E; Task 2: DEFF NOT / outlsd / single-path edits F-T)
- **Files modified:** 1 (~/.claude/agents/lucy-lsd-engineer.md — outside git repo, not committed)

## Accomplishments

- Eliminated all instructions to write SYME (non-native, LSD error 102); replaced with BOND/COSY native equivalence table citing compound_native.lsd ground truth
- Eliminated all instructions to write DEFF NOT SMARTS patterns (non-native, LSD error 150); replaced with DEFF F1 "ring3" + DEFF F2 "ring4" + FEXP "NOT F1 AND NOT F2" native ring exclusion block with F-number reservation rule (F1/F2 = ring exclusion, F3+ = fragment goodlist)
- Restructured step 11 to PRIMARY PATH (lucy lsd run, unconditional first) + FALLBACK PATH (pylsd, explicit 3-condition gate: 0 solutions AND K<=3 deferred 4J AND pylsd_mode=true)
- Removed manual outlsd 5 < compound.sol > solutions.smi pipe; replaced with Phase 73 auto-produce explanation
- Demoted pyLSD section heading from ### to #### (co-equal to subordinate)
- Added HMBC X Y 2 4 in main HMBC correlations block (line 60, not only in fallback subsection)
- Added D-04 SKEL benzene escalation-only note in step 11

## Task Commits

No git commits for this plan — ~/.claude/agents/lucy-lsd-engineer.md is outside the git repo (user-global skill file). Only the SUMMARY.md is committed to the repo.

## Files Created/Modified

- `/Users/steinbeck/.claude/agents/lucy-lsd-engineer.md` - 17 surgical edits applied (A-E for SYME, F-O/S for DEFF NOT/outlsd, P/Q/R/T for single-path/SKEL); outside git repo

## Decisions Made

- Applied Edit G (Fragment persistence rule line 195) as a Rule 1/2 fix — the line said "same as DEFF NOT" which was a confusing cross-reference after DEFF NOT was removed. Updated to "same as ring exclusion DEFF F/FEXP" to maintain document coherence. Not in plan but clearly required.
- Both "DEFF NOT C1CC1" (in the NOT NATIVE warning) and "No manual outlsd 5 <" (in the Phase 73 guidance block) remain in file — these are "do NOT write" guidance lines, explicitly permitted by the plan's must_haves truths: "lsd-engineer.md contains no DEFF NOT SMARTS pattern blocks (only 'do NOT write DEFF NOT' guidance)". The filtered SYME grep returns empty; the DEFF NOT C1 grep returns 1 but it is in a "Do NOT write" warning line.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Fixed Fragment persistence rule cross-reference to DEFF NOT**
- **Found during:** Task 2 (post-edit review)
- **Issue:** Line 195 said "Carry DEFF F1/FEXP forward across iterations, same as DEFF NOT" — after removing DEFF NOT instructions, this analogy pointed to a concept that no longer exists
- **Fix:** Updated to "same as ring exclusion DEFF F/FEXP" to maintain internal consistency
- **Files modified:** ~/.claude/agents/lucy-lsd-engineer.md (line 195)
- **Verification:** No remaining "same as DEFF NOT" cross-references

---

**Total deviations:** 1 auto-fixed (Rule 2 — missing correctness)
**Impact on plan:** Minor cross-reference cleanup. No scope creep.

## Verification Results

All plan-level success criteria confirmed by grep:

| Check | Result |
|-------|--------|
| SYME filtered grep (must be empty) | PASS — empty |
| DEFF NOT C1 (1 line remains — "do NOT write" warning) | PASS per must_haves (guidance allowed) |
| BOND gem-dimethyl present | PASS — 2 lines |
| COSY equiv-pair present | PASS — 5 lines |
| cosy_equiv_pairs field (>=2) | PASS — 2 occurrences |
| DEFF F1 ring3 | PASS — 4 occurrences |
| FEXP NOT F1 AND NOT F2 | PASS — 3 occurrences |
| outlsd 5 < compound (1 line — "No manual" sentence) | PASS per must_haves (guidance allowed) |
| PRIMARY PATH + FALLBACK PATH both present | PASS — lines 554, 561 |
| #### Fallback Path heading | PASS — line 108 |
| HMBC 2 4 in main block (line 60, before fallback section) | PASS |
| D-04 SKEL escalation-only note | PASS — line 583 |

## Issues Encountered

None — all edits applied on first attempt with exact old_string matches.

## Next Phase Readiness

- 75-02 (devils-advocate-native-gates) should update `syme_pairs` → `cosy_equiv_pairs` in DA Check 1/2/3 tables and update DEFF NOT → DEFF F/FEXP in Bug 1 detection logic
- 75-03 (case.md references) should update SYME/DEFF NOT in progress-format.md and case.md spawn prompts
- 75-04 (python schema followups) should update constraint_inventory_v2.json to add ring_exclusion_enabled and change syme_pairs → cosy_equiv_pairs

---
*Phase: 75-skill-consolidation*
*Completed: 2026-05-24*

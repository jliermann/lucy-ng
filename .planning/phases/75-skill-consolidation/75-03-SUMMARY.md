---
phase: 75-skill-consolidation
plan: "03"
subsystem: skill-files
tags: [case-orchestrator, progress-format, solution-analyst, native-vocab, outlsd, DEFF-F, COSY-equiv]

requires:
  - phase: 75-01
    provides: "lsd-engineer updated with native DEFF F/FEXP, COSY equiv-pair, lucy lsd run producing solutions.smi"
  - phase: 75-02
    provides: "devils-advocate updated with native vocabulary and ring-exclusion checks"
provides:
  - "case.md orchestrator spawn prompts use native vocabulary (ring exclusion DEFF F/FEXP, COSY equivalence pairs)"
  - "case.md TaskCreate descriptions no longer instruct manual outlsd pipe"
  - "progress-format.md DA template and initialization line use ring_excl=enabled and COSY_equiv fields"
  - "solution-analyst.md Check 3 uses ring exclusion (DEFF F/FEXP) instead of DEFF NOT"
affects: [future-case-runs, CASE-PROGRESS-files, DA-validation-output]

tech-stack:
  added: []
  patterns:
    - "Orchestrator spawn prompts must use same vocabulary as the agent skill files they spawn"
    - "progress-format.md DA template mirrors what DA skill sends in [VALIDATION-PASSED/BLOCKED] messages"

key-files:
  created:
    - ~/.claude/commands/lucy-ng/references/progress-format.md (modified)
    - ~/.claude/agents/lucy-solution-analyst.md (modified)
  modified:
    - ~/.claude/commands/lucy-ng/case.md
    - ~/.claude/commands/lucy-ng/references/progress-format.md
    - ~/.claude/agents/lucy-solution-analyst.md

key-decisions:
  - "Adapted solution-analyst.md Edit D: plan's old_string used bold markdown (**DEFF NOT**) but file had plain text (DEFF NOT) — matched actual file content, result identical"

patterns-established:
  - "Phase 75 vocabulary standard: ring exclusion = DEFF F/FEXP, COSY equiv-pair, lucy lsd run auto-produces solutions.smi"

requirements-completed: [SKILL-01]

duration: 6min
completed: 2026-05-24
---

# Phase 75 Plan 03: case.md + references + solution-analyst native vocab Summary

**Removed all manual `outlsd 5 < compound.sol` pipe instructions from case.md and replaced SYME/DEFF NOT vocabulary with COSY_equiv/ring exclusion (DEFF F/FEXP) across case.md spawn prompts, progress-format.md templates, and solution-analyst.md plausibility checks.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-24T16:13:04Z
- **Completed:** 2026-05-24T16:13:10Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Removed 3 occurrences of `outlsd 5 < compound.sol > solutions.smi` from case.md (lsd-iteration-01 TaskCreate, lsd-engineer spawn prompt, subsequent iteration TaskCreate)
- Updated DA spawn prompt in case.md from "DEFF NOT, SYME, grouped notation" to "ring exclusion DEFF F/FEXP, COSY equivalence pairs, grouped notation"
- Updated progress-format.md initialization line from `DEFF NOT=0, SYME=0` to `ring_excl=enabled, COSY_equiv=0`
- Updated progress-format.md DA section fields: `DEFF NOT:` -> `Ring exclusion:`, `SYME:` -> `COSY-equiv:`
- Updated solution-analyst.md Check 3 from "DEFF NOT was properly applied" to "ring exclusion (DEFF F/FEXP) was properly applied"

## Task Commits

Skill files are outside the git repo (~/.claude/) — no per-task commits apply to them per plan instructions.

**Plan metadata:** (SUMMARY commit — see below)

## Files Created/Modified

- `~/.claude/commands/lucy-ng/case.md` — Removed outlsd pipe (3 locations); DA spawn prompt uses native ring exclusion / COSY equivalence vocab
- `~/.claude/commands/lucy-ng/references/progress-format.md` — Initialization line and DA section template use ring_excl=enabled, COSY_equiv, Ring exclusion, COSY-equiv
- `~/.claude/agents/lucy-solution-analyst.md` — Check 3 uses ring exclusion (DEFF F/FEXP) instead of DEFF NOT

## Decisions Made

- Adapted solution-analyst.md Edit D: the plan specified the old_string with bold markdown (`**DEFF NOT**`) but the actual file used plain text (`DEFF NOT`). Applied intent as written, matched actual file content, result is identical to plan specification.

## Deviations from Plan

### Adapted Edit (not a rule deviation — minor string-match difference)

**1. [Adapted] solution-analyst.md Edit D old_string mismatch**
- **Found during:** Task 2 application
- **Issue:** Plan's `old_string` used `**DEFF NOT**` (bold) but actual file line 105 had plain `DEFF NOT` without markdown bold
- **Fix:** Matched actual file content exactly; result identical to plan's intent
- **Files modified:** `~/.claude/agents/lucy-solution-analyst.md`

---

**Total deviations:** 1 adapted (minor old_string text-format mismatch; intent preserved exactly)
**Impact on plan:** No scope change. Result identical to what the plan specified.

## Issues Encountered

None — all edits applied successfully. All 5 verification checks passed.

## Verification Results

```
case.md: no manual outlsd pipe          PASS: no outlsd pipe
case.md: ring exclusion present         line 166: ring exclusion DEFF F/FEXP, COSY equivalence pairs
case.md: old DEFF NOT, SYME gone        PASS: old vocab gone
case.md: COSY equivalence present       line 166: COSY equivalence pairs
progress-format.md: SYME= DEFF NOT= gone  PASS: old fields gone
progress-format.md: ring_excl COSY_equiv  line 44: ring_excl=enabled, COSY_equiv=0
progress-format.md: Ring exclusion/COSY-equiv  lines 86+88
solution-analyst.md: DEFF NOT gone      PASS: no DEFF NOT
solution-analyst.md: ring exclusion (DEFF F/FEXP)  line 105
```

## Known Stubs

None.

## Threat Flags

None — pure markdown edits to skill/prompt files, no network endpoints or schema changes introduced.

## Next Phase Readiness

Phase 75 Wave-2 is complete. All three skill files now use consistent native vocabulary matching what lsd-engineer (75-01) and devils-advocate (75-02) write in their LSD output and validation messages. A future CASE run will have end-to-end vocabulary consistency across the entire team.

---
*Phase: 75-skill-consolidation*
*Completed: 2026-05-24*

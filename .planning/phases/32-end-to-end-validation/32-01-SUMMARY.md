---
phase: 32-end-to-end-validation
plan: 01
subsystem: validation
tags: [pre-flight-checks, integration-tests, validation-guide, multi-agent-testing]

# Dependency graph
requires:
  - phase: 28-case-agent-definition
    provides: lucy-case-agent.md definition (613 lines with inlined skill knowledge)
  - phase: 29-case-orchestrator
    provides: case.md orchestrator with Task() spawning and loop detection
  - phase: 30-diagnostic-integration
    provides: lucy-diagnostic.md with delegation wired into orchestrator
  - phase: 31-sanitization-skill
    provides: sanitise.md skill completing sub-command suite
provides:
  - Pre-flight check results (31/31 passed) confirming all components ready
  - Comprehensive validation guide with exact test instructions, success criteria, failure modes
  - Structured test plan for Ibuprofen CASE via orchestrator
  - Known failure mode documentation for troubleshooting
affects: [33-documentation-cleanup]

# Tech tracking
tech-stack:
  added: []
  patterns: [pre-flight-validation, integration-test-documentation]

key-files:
  created:
    - .planning/phases/32-end-to-end-validation/32-VALIDATION-GUIDE.md
  modified: []

key-decisions:
  - "Pre-flight checks run before validation guide creation to document actual system readiness"
  - "Validation guide includes exact paths and commands to eliminate ambiguity"
  - "7 known failure modes documented with symptoms, causes, and fixes for troubleshooting"
  - "Structured feedback template provided for issue reporting"

patterns-established:
  - "Validation-first development: comprehensive pre-flight checks before user testing"
  - "Known failure modes documentation with recognition symptoms and remediation steps"

# Metrics
duration: 3min
completed: 2026-02-08
---

# Phase 32 Plan 01: End-to-End Validation Summary

**Pre-flight checks complete (31/31 passed), comprehensive validation guide created with exact test instructions for Ibuprofen CASE and sub-commands**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-08T20:28:57Z
- **Completed:** 2026-02-08T20:31:57Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- All 31 pre-flight checks executed and passed (agents, skills, CLI, LSD, database, test data)
- 530-line validation guide created with actionable test instructions
- Exact Ibuprofen CASE test documented with success criteria (correct structure in top 3)
- 7 known failure modes documented with symptoms, causes, and fixes
- Structured feedback template for issue reporting

## Task Commits

Each task was committed atomically:

1. **Task 2: Create comprehensive validation guide** - `493876d` (docs)

Note: Task 1 (pre-flight checks) executed without file changes — results captured in validation guide.

## Files Created/Modified

- `.planning/phases/32-end-to-end-validation/32-VALIDATION-GUIDE.md` - Complete test instructions with pre-flight results, Test 1 (Ibuprofen CASE primary validation), Test 2 (sub-command secondary validation), 7 known failure modes, feedback template

## Pre-Flight Results Summary

All 31 checks passed:

### Component Verification
- **Agents**: lucy-case-agent.md (613 lines), lucy-diagnostic.md (455 lines), model: inherit present, tools configured
- **Sub-commands**: case.md (698 lines), dereplicate.md, predict.md, status.md, sanitise.md, lucy-ng.md routing page (6 files total)
- **Skills**: SKILL.md (1,098 lines), CASE/SKILL.md (721 lines), supervisor/SKILL.md (827 lines), diagnostic/SKILL.md (1,876 lines)
- **CLI**: lucy v0.1.0, LSD and outlsd both available
- **Database**: 928,443 compounds, 111,493 unique formulas, schema v3
- **Test Data**: Ibuprofen experiments 1-7 all present, Ibuprofen.mol exists
- **Project**: Directory writable

### Content Verification (Spot Checks)
- Task() spawning in case.md: Lines 116, 395, 600
- CASE-PROGRESS.md monitoring in case.md: Lines 15, 120, 143
- Loop detection (ELIM thrashing) in case.md: Present
- Diagnostic delegation in case.md: Line 601
- CASE-PROGRESS.md writing in lucy-case-agent.md: Lines 6, 30, 480, 484, 582
- LSD knowledge (MULT) in lucy-case-agent.md: Lines 137-142

**Result**: ALL SYSTEMS GO — Ready for end-to-end testing.

## Validation Guide Contents

The 530-line guide includes:

### Test 1: Ibuprofen CASE (Primary Validation)
- **Invocation**: `/lucy-ng:case` with path `/Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen` and formula `C13H18O2`
- **Expected behavior**: 12-step workflow from orchestrator spawn through agent iterations to final ranking
- **Success criteria**: CASE-PROGRESS.md exists, Ibuprofen structure (`CC(C)Cc1ccc(cc1)C(C)C(=O)O`) in top 3, no loops, completion within ~15-30 minutes
- **Expected CASE-PROGRESS.md structure**: Example showing iteration format with solution counts, constraints, reasoning, sp2/H checks

### Test 2: Sub-Commands (Secondary Validation)
- **/lucy-ng:status**: Reports version, LSD status, database status
- **/lucy-ng:dereplicate**: Ibuprofen C13 data → top 10 matches with scores
- **/lucy-ng:predict**: Ibuprofen SMILES → 13 predicted shifts with confidence

### Known Failure Modes (7 documented)
1. **Agent Not Found**: Missing/invalid lucy-case-agent.md
2. **LSD Not Found**: LSD solver not in PATH
3. **Database Missing**: Database not downloaded or wrong path
4. **Agent Hangs / No Progress File**: Crash before progress writing or cwd mismatch
5. **Wrong Model**: Task tool model bug — agent gets Sonnet instead of Opus
6. **Working Directory Mismatch**: Agent uses relative paths and fails
7. **LSD Logic Errors**: Invalid constraints causing 0 or >1000 solutions

Each mode includes:
- Symptom recognition
- Root cause explanation
- Remediation steps
- Likelihood assessment

### Advanced Tests (Optional)
- Loop detection testing (requires harder dataset than Ibuprofen)
- Diagnostic delegation testing (requires repeated failures)

### Feedback Template
Structured report format requesting:
- Which test failed
- Exact error message
- CASE-PROGRESS.md status (created? last lines?)
- Agent thread visibility
- Runtime before failure
- Other observations

## Decisions Made

- **Pre-flight checks before guide creation**: Run actual checks and document results in guide rather than describing what checks SHOULD be run
- **Exact paths in test instructions**: No placeholders — guide contains `/Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen` so user can copy-paste
- **7 known failure modes**: Based on Phase 28-31 CONTEXT.md risk analysis (Task tool model bug, cwd mismatch) plus common integration issues
- **Structured feedback template**: Anticipate that first live test may reveal issues — template captures diagnostic info

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All pre-flight checks passed on first execution.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for live validation testing:**
- All components in place and verified
- Validation guide provides exact instructions
- User can execute tests without additional context
- Known failure modes documented for troubleshooting

**Blockers**: None

**Concerns**:
- This is the first live test of multi-agent Task() spawning orchestration
- Phase 28-31 components never invoked together in real workflow
- Known risks: Task tool model inheritance bug, working directory mismatch, loop detection patterns
- Validation guide documents all known risks with recognition symptoms

**If validation passes**: Phase 33 (cleanup) removes deprecated components and ships v2.1

**If validation fails**: Use failure mode diagnosis in guide to identify root cause, fix in corresponding phase (28-31), re-run pre-flight, retry

---
*Phase: 32-end-to-end-validation*
*Completed: 2026-02-08*

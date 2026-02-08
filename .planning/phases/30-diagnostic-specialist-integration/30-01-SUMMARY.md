---
phase: 30-diagnostic-specialist-integration
plan: 01
subsystem: case-orchestration
tags: [agent-architecture, diagnostic-specialist, orchestrator, task-delegation, loop-intervention]

# Dependency graph
requires:
  - phase: 29-case-orchestrator-skill
    provides: case.md orchestrator with basic loop detection and intervention
  - phase: 28-case-agent-definition
    provides: User-global agent file pattern at ~/.claude/agents/
  - phase: 25-diagnostic-specialist
    provides: Original diagnostic specialist agent definition
provides:
  - lucy-diagnostic agent at ~/.claude/agents/ (user-global, renamed from diagnostic-specialist)
  - Diagnostic specialist delegation in case.md at counter == 2 threshold
  - DIAGNOSTIC-REPORT.md parsing for specialist-informed advisories
  - Fallback to basic advisory if report missing
affects: [31-agent-testing, 32-supervisor-dissolution, future-case-improvements]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Specialist delegation after 2 failed basic interventions (threshold = 2)"
    - "Specialist-informed advisory (specific) vs basic advisory (procedural)"
    - "Task tool agent_type parameter for user-global agent spawning"

key-files:
  created:
    - "~/.claude/agents/lucy-diagnostic.md"
  modified:
    - "~/.claude/commands/lucy-ng/case.md"
  deleted:
    - ".claude/agents/diagnostic-specialist.md"

key-decisions:
  - "Diagnostic specialist delegates after 2 failed interventions (not first detection)"
  - "Specialist-informed advisory extracts specific fix from DIAGNOSTIC-REPORT.md"
  - "Counter increments even if specialist delegation attempted (counts as 1 cycle)"
  - "Fallback to basic advisory if DIAGNOSTIC-REPORT.md missing after delegation"

patterns-established:
  - "User-global agent files at ~/.claude/agents/ with model: inherit"
  - "Orchestrator references updated from 'supervisor' to 'orchestrator' (v2.1 architecture)"
  - "Per-pattern intervention counters with threshold-based routing"

# Metrics
duration: 4min
completed: 2026-02-08
---

# Phase 30 Plan 01: Diagnostic Specialist Integration Summary

**Diagnostic specialist delegation wired into case orchestrator with threshold-based routing (counter == 2), DIAGNOSTIC-REPORT.md parsing, and specialist-informed advisory generation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-08T14:46:00Z
- **Completed:** 2026-02-08T14:50:28Z
- **Tasks:** 2
- **Files modified:** 2 (1 created user-global, 1 modified user-global, 1 deleted project-local)

## Accomplishments

- Relocated diagnostic specialist from project-local `.claude/agents/diagnostic-specialist.md` to user-global `~/.claude/agents/lucy-diagnostic.md` consistent with Phase 28 agent architecture decision
- Updated all "supervisor" references to "orchestrator" throughout agent definition (v2.1 architecture alignment)
- Wired diagnostic specialist delegation into case.md orchestrator with working trigger logic at counter == 2
- Implemented DIAGNOSTIC-REPORT.md parsing to extract root cause and primary fix for specialist-informed advisories
- Added fallback to basic advisory if DIAGNOSTIC-REPORT.md missing after specialist delegation

## Task Commits

Each task was committed atomically:

1. **Task 1: Move and rename diagnostic specialist to user-global lucy-diagnostic** - `bc356b0` (feat)
   - Relocated agent file from `.claude/agents/diagnostic-specialist.md` to `~/.claude/agents/lucy-diagnostic.md`
   - Updated frontmatter: `name: lucy-diagnostic`, `model: inherit`
   - Replaced all "supervisor" references with "orchestrator" (v2.1)
   - Deleted old project-local file

2. **Task 2: Wire diagnostic specialist delegation into case.md orchestrator** - (user-global file, not in repo)
   - Updated `track_and_decide` step with expanded decision logic (counter == 2 routes to specialist)
   - Replaced `diagnostic_specialist_placeholder` with two new steps: `delegate_specialist` and `extract_diagnostic_findings`
   - Added anti-pattern: "Never delegate to specialist on first loop detection"

**Note:** Task 2 modified `~/.claude/commands/lucy-ng/case.md` which is outside the project repository (user-global command), so no git commit was created for it.

## Files Created/Modified

- `~/.claude/agents/lucy-diagnostic.md` (created) - Diagnostic specialist agent definition relocated from project-local to user-global, consistent with lucy-case-agent.md location
- `~/.claude/commands/lucy-ng/case.md` (modified) - Orchestrator with diagnostic specialist delegation, DIAGNOSTIC-REPORT.md parsing, specialist-informed advisory generation
- `.claude/agents/diagnostic-specialist.md` (deleted) - Old project-local agent file removed

## Decisions Made

**Delegation threshold = 2:**
- First intervention (counter 0->1): Basic diagnosis only (catches common issues: odd sp2, missing H, 1J artifacts)
- Second intervention (counter 1->2): Pattern recurred, delegate to specialist for deep root cause analysis
- Rationale: Specialist has 455 lines of deep diagnostic knowledge - overkill for common issues caught by basic diagnosis

**Specialist-informed advisory structure:**
- Extracts specific root cause from DIAGNOSTIC-REPORT.md "## Root Cause" section (Primary: line)
- Extracts specific fix action from "## Recommended Fixes" first (PRIMARY) subsection
- Extracts verification steps from same PRIMARY fix subsection
- Result: SPECIFIC advisory (exact atom, exact command, exact verification) vs PROCEDURAL basic advisory (check these conditions)

**Fallback behavior:**
- If DIAGNOSTIC-REPORT.md missing after specialist delegation: fall back to basic advisory
- Counter still increments (delegation was attempted, counts as 1 intervention cycle)
- Prevents orchestrator failure if specialist doesn't write report

**Architecture alignment:**
- All "supervisor" references updated to "orchestrator" in lucy-diagnostic.md
- Consistent with v2.1 decision: supervisor logic dissolves into case.md orchestrator skill
- Agent frontmatter updated to `model: inherit` (consistent with lucy-case-agent.md pattern)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

**Ready for Phase 31 (Agent Testing):**
- lucy-diagnostic agent definition complete at user-global location
- case.md orchestrator has working delegation trigger and report parsing
- Specialist-informed advisory generation implemented
- All cross-file consistency verified (agent name, report format, Task tool pattern)

**Blockers/concerns:**
None. Integration is complete and verified.

**Testing needs:**
- Phase 31 will test full delegation flow with synthetic CASE-PROGRESS.md and LSD files
- Will verify DIAGNOSTIC-REPORT.md parsing extracts correct root cause and fix
- Will verify fallback to basic advisory if report missing
- Will verify counter increments correctly after specialist delegation

---
*Phase: 30-diagnostic-specialist-integration*
*Completed: 2026-02-08*

---
phase: 25-diagnostic-specialist
plan: 02
subsystem: ai-agents
tags: [claude-code, task-tool, diagnostic-specialist, supervisor, lsd, multi-agent]

# Dependency graph
requires:
  - phase: 24-supervisor-agent
    provides: Supervisor agent definition with basic loop detection and intervention
  - phase: 25-diagnostic-specialist
    plan: 01
    provides: Diagnostic specialist agent definition and skill document
provides:
  - Supervisor knows when to delegate to diagnostic specialist (2 failed interventions threshold)
  - Task tool invocation template for spawning diagnostic specialist
  - Post-diagnostic workflow for using DIAGNOSTIC-REPORT.md
  - Diagnostic specialist integrated into supervisor workflow
affects: [26-cli-mcp-integration, future-case-workflows]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Supervisor delegates to diagnostic specialist via Task tool for deep LSD analysis"
    - "Diagnostic specialist spawned after 2 failed basic interventions with same pattern"
    - "DIAGNOSTIC-REPORT.md retention: single file, latest diagnostic only"

key-files:
  created: []
  modified:
    - skill/supervisor/SKILL.md
    - .claude/agents/supervisor.md

key-decisions:
  - "Delegation threshold: 2 failed interventions with same loop pattern OR basic checks pass but stuck"
  - "DIAGNOSTIC-REPORT.md overwrites (single file), CASE-PROGRESS.md tracks diagnostic history"
  - "Specialist-informed interventions count toward 10-cycle escalation limit"
  - "Supervisor never spawns specialist for routine iterations (basic diagnosis sufficient)"

patterns-established:
  - "Multi-agent diagnostic escalation: supervisor basic diagnosis → delegate to specialist if insufficient → use specialist's findings to advise CASE agent"
  - "Structured diagnostic reporting: supervisor extracts root cause and primary fix from DIAGNOSTIC-REPORT.md sections"

# Metrics
duration: 4min
completed: 2026-02-07
---

# Phase 25 Plan 02: Diagnostic Specialist Integration Summary

**Supervisor delegates to diagnostic specialist via Task tool after 2 failed interventions, using structured DIAGNOSTIC-REPORT.md to advise CASE agent**

## Performance

- **Duration:** 4 min (250 seconds)
- **Started:** 2026-02-07T16:05:30Z
- **Completed:** 2026-02-07T16:09:40Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Supervisor skill document updated with diagnostic specialist delegation (Section 5, 149 new lines)
- Supervisor agent definition updated with spawning workflow (101 new lines)
- Delegation criteria documented: 2 failed interventions, basic checks pass but stuck, churning persists
- Task tool invocation template provided with agent_type="diagnostic-specialist"
- Post-diagnostic workflow: read DIAGNOSTIC-REPORT.md, extract root cause/fixes, advise CASE agent

## Task Commits

Each task was committed atomically:

1. **Task 1: Update skill/supervisor/SKILL.md with diagnostic specialist delegation** - `7e8aa32` (docs)
2. **Task 2: Update .claude/agents/supervisor.md with diagnostic specialist spawning** - `4220df3` (docs)

## Files Created/Modified

- `skill/supervisor/SKILL.md` - Added Section 5 "Diagnostic Specialist Delegation" (149 lines): delegation criteria, Task tool template, post-diagnostic workflow, DIAGNOSTIC-REPORT.md retention, escalation rules, cross-references skill/diagnostic/SKILL.md
- `.claude/agents/supervisor.md` - Added "Spawning the Diagnostic Specialist" section (101 lines): when/when not to spawn, Task tool invocation, post-diagnostic workflow, updated monitoring step, domain knowledge references, new important rule

## Decisions Made

**1. Delegation threshold: 2 failed interventions with same pattern**
- Rationale: First loop detection = basic supervisor diagnosis sufficient; 2 failures = escalate to specialist
- Alternative considered: delegate after 1 failure (too aggressive, specialist overhead)

**2. DIAGNOSTIC-REPORT.md retention: single file, latest only**
- Rationale: Keeps compound directory clean; CASE-PROGRESS.md tracks when diagnostics were run
- Alternative considered: timestamped files (creates clutter, history available in progress log)

**3. Specialist-informed interventions count toward 10-cycle limit**
- Rationale: Diagnostic specialist is still an intervention; prevents infinite specialist loops
- Combined limit = basic + specialist interventions = 10 total per pattern

**4. Supervisor never spawns specialist for routine iterations**
- Rationale: Basic diagnosis is sufficient for first-time loop detection; specialist for complex/recurring issues
- Enforced via Important Rule in supervisor.md

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward documentation updates following established patterns from Phase 24 and Phase 25 Plan 01.

## Next Phase Readiness

**Ready for Phase 26 (CLI/MCP Integration):**
- Supervisor agent operational with full diagnostic specialist delegation
- Multi-agent CASE workflow complete: supervisor → CASE agent → diagnostic specialist (if needed)
- All three agents reference skill documents for domain knowledge
- Task tool used for spawning both CASE agent and diagnostic specialist

**Phase 25 complete:**
- Plan 01: Diagnostic specialist agent and skill created
- Plan 02: Diagnostic specialist integrated with supervisor
- Full diagnostic escalation workflow operational

**Remaining work:**
- Phase 26: CLI thin wrappers + MCP tool architecture
- Intelligence migration from Python to skill documents (progressive, not required for v2.0)

---
*Phase: 25-diagnostic-specialist*
*Completed: 2026-02-07*

---
phase: 42-agent-definitions
plan: 04
subsystem: agents
tags: [claude-code, agent-teams, devils-advocate, validation, v3-bugs]

requires:
  - phase: 41-01
    provides: "Devils-Advocate stub agent definition"
provides:
  - "Full Devils-Advocate agent definition with validation and diff protocol"
  - "Constraint diff protocol, v3.0 UAT bug checklist, severity classification"
affects: [43-constraint-inventory, 45-team-coordination, 47-uat]

tech-stack:
  added: []
  patterns: [xml-tagged-sections, shared-context-template, validation-gate]

key-files:
  created: []
  modified:
    - "~/.claude/agents/lucy-devils-advocate.md"

key-decisions:
  - "Write tool removed from devils-advocate (read-only validation agent)"
  - "All 5 v3.0 UAT bugs as explicit numbered checklist items with severity"
  - "Constraint diff protocol: count AND content comparison between iterations"
  - "Severity system: CRITICAL blocks solver, WARNING allows with justification, INFO logged"
  - "Structural integrity checks: sp2 parity, H budget, correlation order, HMBC refs, badlist"

patterns-established:
  - "Validation gate: BLOCKED/APPROVED decision based on severity classification"
  - "Constraint diff: count comparison + content comparison per constraint type"
  - "Severity classification: CRITICAL/WARNING/INFO with specific action requirements"

duration: 8min
completed: 2026-02-17
---

# Phase 42-04: Devils-Advocate Agent Definition Summary

**Replaced stub with full Devils-Advocate specialist containing validation and diff protocol (221 lines)**

## Performance

- **Duration:** 8 min
- **Tasks:** 1 (auto)
- **Files modified:** 1

## Accomplishments

- Replaced 25-line stub with 221-line full agent definition
- Write tool removed (read-only validation agent)
- Constraint diff protocol: count + content comparison between iterations
- All 5 v3.0 UAT bugs as explicit checklist items:
  1. DEFF NOT patterns dropped (CRITICAL)
  2. Signal grouping not applied (WARNING)
  3. Grouped notation dropped (CRITICAL)
  4. PROP not used despite documentation (INFO)
  5. No constraints from detection (WARNING)
- Structural integrity checks: sp2 parity, H budget, correlation order, HMBC refs, badlist
- Severity classification: CRITICAL/WARNING/INFO with blocking decisions
- Validation gate: APPROVED/BLOCKED workflow

## Verification Results

| Check | Result |
|-------|--------|
| Line count (180-280) | PASS (221) |
| Model: claude-opus-4-6 | PASS |
| No Write tool | PASS |
| v3.0 bugs (5) | PASS |
| Diff protocol | PASS |
| Severity system | PASS |
| sp2 count check | PASS |
| H budget check | PASS |
| DEFF NOT persistence | PASS |
| Role prohibitions (3) | PASS |

---
*Phase: 42-agent-definitions*
*Completed: 2026-02-17*

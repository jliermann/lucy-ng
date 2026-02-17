---
phase: 43-constraint-inventory-system
plan: 01
subsystem: agent-knowledge
tags: [lsd-engineer, constraint-inventory, json-schema, agent-definition, v3.0-bug-fix]

requires:
  - phase: 42-agent-definitions
    provides: lucy-lsd-engineer.md base definition (306 lines, LSD command reference, HMBC strategy, file organization, CASE-PROGRESS format)
  - phase: 43-constraint-inventory-system
    provides: 43-RESEARCH.md JSON schema design and empirical bug analysis

provides:
  - Section 5 Constraint Inventory System in lucy-lsd-engineer.md domain_knowledge
  - JSON schema reference table (all 17 fields documented)
  - LSD file format showing inventory comment block with delimiters
  - Initialization procedure for iteration 1 (Section 5C)
  - Update procedure for iteration N (Section 5D) with NEVER-rebuild rule
  - Atomic Write Rule (Section 5E)
  - Updated Manual Checklist item 9 (inventory present with correct counts)
  - Updated workflow steps 3-6 integrating inventory operations

affects:
  - 43-02-PLAN (Devils-Advocate validation -- uses same inventory schema)
  - 43-03-PLAN (verification -- checks inventory written correctly)
  - lucy-lsd-engineer agent behavior in v4.0 UAT runs

tech-stack:
  added: []
  patterns:
    - "JSON constraint inventory embedded in LSD file header as ; comment lines"
    - "Read-copy-update protocol: extract previous inventory, copy all fields, update only what changed"
    - "Atomic write: inventory block + LSD commands in single Write operation"
    - "deff_not_patterns array initialized at iteration 1, copied verbatim across all iterations"

key-files:
  created: []
  modified:
    - "~/.claude/agents/lucy-lsd-engineer.md"

key-decisions:
  - "JSON format confirmed safe in LSD ; comments (parser smoke test: 0 solutions, no parse error)"
  - "Inventory block goes at TOP of LSD file before MULT definitions"
  - "deff_not_patterns populated from constant badlist at initialization (primary defense against Bug 1)"
  - "NEVER rebuild inventory from scratch -- same read-previous-never-reconstruct rule applied to inventory"
  - "Atomic write rule: inventory and commands written as single Write operation"

patterns-established:
  - "Section 5C/5D cross-reference pattern: workflow steps reference domain knowledge sections by letter"
  - "Initialization vs update separation: two distinct procedures prevent mode confusion"

duration: 3min
completed: 2026-02-17
---

# Phase 43 Plan 01: Constraint Inventory Schema and LSD-Engineer Protocol Summary

**JSON constraint inventory schema and read-copy-update protocol added to lucy-lsd-engineer.md to prevent v3.0 constraint-loss bugs across HMBC iterations**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-17T10:48:48Z
- **Completed:** 2026-02-17T10:51:51Z
- **Tasks:** 2/2
- **Files modified:** 1 (outside git repo: ~/.claude/agents/lucy-lsd-engineer.md)

## Accomplishments

- Added complete Section 5 (Constraint Inventory System) to lucy-lsd-engineer.md domain_knowledge block (~88 lines): schema table, LSD file format with realistic iteration-2 example, initialization procedure (5C), update procedure (5D) with NEVER-rebuild critical rule, atomic write rule (5E)
- Updated Manual Checklist to add item 9: "Constraint Inventory block present at top of file with correct counts"
- Updated workflow steps 3-6 to integrate inventory operations with Section 5C/5D cross-references
- Confirmed LSD parser accepts JSON characters (`{`, `}`, `"`, `[`, `]`) in `;`-prefixed comment lines -- smoke test returned 0 solutions with no parse error

## Task Commits

Both tasks modify only `~/.claude/agents/lucy-lsd-engineer.md`, which is outside the lucy-ng git repository. The agent file is stored unversioned in `~/.claude/agents/` (established pattern from Phase 42). Commit recorded in lucy-ng repo for planning artifacts only.

1. **Task 1: Add constraint inventory schema and procedures** - agent file modified (unversioned)
2. **Task 2: Update workflow to integrate inventory steps** - agent file modified (unversioned)

**Plan metadata:** documented in this SUMMARY and STATE.md

## Files Created/Modified

- `~/.claude/agents/lucy-lsd-engineer.md` - Added Section 5 (~88 lines), updated checklist item 9, updated workflow steps 3-6. Total: 306 -> 394 lines.

## Decisions Made

- JSON format (not key-value fallback): LSD parser test confirmed JSON characters are safe in `;` comments. Used Pattern 1 from 43-RESEARCH.md.
- Inventory initialized at iteration 1 alongside the DEFF NOT write (not in a separate step), so `deff_not_patterns` can never be out of sync with the LSD commands at initialization.
- "NEVER rebuild the inventory from scratch" rule explicitly stated as CRITICAL to mirror the existing "NEVER reconstruct from memory" rule.

## Deviations from Plan

None -- plan executed exactly as written. LSD parser smoke test passed with Pattern 1 (JSON), so no fallback to key-value format was needed.

## Issues Encountered

None.

## User Setup Required

None -- agent definition update requires no external configuration.

## Next Phase Readiness

- 43-01 complete: LSD-Engineer knows the full constraint inventory protocol
- 43-02 (Devils-Advocate inventory validation) can now proceed -- same schema defined here
- 43-02 is independent of 43-01 content (different file: lucy-devils-advocate.md) and can run immediately

## Self-Check: PASSED

- FOUND: `/Users/steinbeck/.claude/agents/lucy-lsd-engineer.md` (394 lines, within 360-410 range)
- FOUND: `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/43-constraint-inventory-system/43-01-SUMMARY.md`
- 3 occurrences of "Constraint Inventory" (>= 3 required by verify step 1)
- 2 occurrences of "CONSTRAINT INVENTORY v1" (>= 2 required by verify step 2)
- "NEVER rebuild the inventory from scratch" rule present
- All schema fields documented: deff_not_patterns, hmbc_batches, pending_from_detection, applied_from_detection
- LSD parser smoke test: PASSED (0 solutions, no parse error from JSON in ; comments)
- Commit: e7383f9

---
*Phase: 43-constraint-inventory-system*
*Completed: 2026-02-17*

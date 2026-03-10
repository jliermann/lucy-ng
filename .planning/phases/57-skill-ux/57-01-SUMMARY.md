---
phase: 57-skill-ux
plan: 01
subsystem: ui
tags: [skill-discovery, routing, nlp, ux, claude-commands]

requires: []
provides:
  - Natural-language trigger phrases in all 5 lucy-ng skill descriptions
  - Decision tree routing page in lucy-ng.md with 5 branches
affects: [case, predict, dereplicate, sanitise, status]

tech-stack:
  added: []
  patterns:
    - "Use when: trigger phrases in skill frontmatter description for intent-based routing"
    - "Decision tree in routing page maps user goals to sub-commands"

key-files:
  created:
    - ~/.claude/commands/lucy-ng/lucy-ng.md (rewritten with decision tree)
  modified:
    - ~/.claude/commands/lucy-ng/case.md (description field updated)
    - ~/.claude/commands/lucy-ng/predict.md (description field updated)
    - ~/.claude/commands/lucy-ng/dereplicate.md (description field updated)
    - ~/.claude/commands/lucy-ng/sanitise.md (description field updated)
    - ~/.claude/commands/lucy-ng/status.md (description field updated)

key-decisions:
  - "Use 'Use when:' prefix pattern in skill descriptions to signal trigger phrases to Claude's intent matcher"
  - "Decision tree branches use goal-oriented phrasing ('I have an unknown compound...') matching how users actually think"

patterns-established:
  - "Skill description pattern: '<core description>. Use when: <trigger 1>, <trigger 2>, <trigger 3>...'"
  - "Routing page pattern: decision tree BEFORE command table, Quick Start references decision tree"

requirements-completed: [SKUX-01, SKUX-02]

duration: 1min
completed: 2026-03-10
---

# Phase 57 Plan 01: Skill UX — Natural-Language Routing Summary

**Natural-language "Use when:" trigger phrases added to all 5 skill descriptions, plus a 5-branch decision tree routing page in lucy-ng.md that maps user goals to correct sub-commands.**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-03-10T15:00:31Z
- **Completed:** 2026-03-10T15:01:34Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added "Use when:" trigger phrases to all 5 skill `description` fields (case, predict, dereplicate, sanitise, status)
- Built 5-branch decision tree in lucy-ng.md: unknown compound → case, predict shifts → predict, check database → dereplicate, blind test prep → sanitise, env check → status
- Updated Quick Start section to reference the decision tree

## Task Commits

Each task was committed atomically:

Note: Skill files are in `~/.claude/commands/lucy-ng/` (outside the lucy-ng git repository). Changes are applied directly to those files; no per-task git commits exist for them.

1. **Task 1: Add natural-language trigger phrases to all 5 skill descriptions** - external file edit (outside repo)
2. **Task 2: Build decision tree routing page in lucy-ng.md** - external file edit (outside repo)

**Plan metadata:** (see final docs commit)

## Files Created/Modified

- `~/.claude/commands/lucy-ng/case.md` - description now includes "Use when: unknown compound, determine structure, identify molecule, what is this compound, structure determination from NMR"
- `~/.claude/commands/lucy-ng/predict.md` - description now includes "Use when: predict shifts, expected chemical shifts, what shifts would this have, HOSE code prediction, verify a structure"
- `~/.claude/commands/lucy-ng/dereplicate.md` - description now includes "Use when: is this compound in the database, identify known compound, dereplication, match spectrum, compare shifts to database"
- `~/.claude/commands/lucy-ng/sanitise.md` - description now includes "Use when: prepare blind test, remove names, anonymise dataset, sanitise for CASE, blind testing"
- `~/.claude/commands/lucy-ng/status.md` - description now includes "Use when: is lucy-ng installed, check setup, verify environment, is LSD available, database status"
- `~/.claude/commands/lucy-ng/lucy-ng.md` - rewritten with 5-branch decision tree before command table

## Decisions Made

- "Use when:" prefix pattern chosen as it is a clear signal phrase that Claude's intent-matching can use to align user language with the correct skill
- Decision tree uses first-person goal phrasing ("I have an unknown compound...") to match how users naturally describe their task

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

The skill files reside in `~/.claude/commands/lucy-ng/` which is outside the lucy-ng git repository. Per-task commits were therefore not possible; the skill file edits are captured as direct file modifications, and only the planning metadata is committed to the repo.

## Next Phase Readiness

- All skill descriptions discoverable via natural language intent matching
- Routing page guides first-time users to the correct sub-command
- Ready for Plan 57-02 (next plan in phase 57-skill-ux)

---
*Phase: 57-skill-ux*
*Completed: 2026-03-10*

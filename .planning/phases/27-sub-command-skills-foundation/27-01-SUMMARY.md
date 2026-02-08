---
phase: 27-sub-command-skills-foundation
plan: 01
subsystem: cli
tags: [sub-commands, gsd-pattern, dereplication, status, slash-commands]

# Dependency graph
requires:
  - phase: 26-cli-mcp-integration
    provides: "lucy CLI with 9 command groups and 22 commands"
provides:
  - "~/.claude/commands/lucy-ng/ namespace directory"
  - "/lucy-ng:status environment check skill"
  - "/lucy-ng:dereplicate 13C dereplication wrapper skill"
affects: [27-02, 28-case-orchestrator, 29-sanitise-skill]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "GSD sub-command pattern: YAML frontmatter + XML-tagged process steps"
    - "Thin CLI wrappers: skills call lucy CLI via Bash, no domain intelligence"

key-files:
  created:
    - "~/.claude/commands/lucy-ng/status.md"
    - "~/.claude/commands/lucy-ng/dereplicate.md"
  modified: []

key-decisions:
  - "Skills live in ~/.claude/commands/lucy-ng/ (outside git repo, user-local)"
  - "Thin wrapper pattern: skills only call CLI and format output, no AI reasoning"

patterns-established:
  - "Sub-command skill structure: YAML frontmatter (name, description, allowed-tools) + <objective> + <process> with named <step> elements"
  - "Argument handling: parse user args, default -n to 10, show usage if no args"

# Metrics
duration: 1min
completed: 2026-02-08
---

# Phase 27 Plan 01: Status and Dereplicate Sub-Command Skills Summary

**GSD-pattern sub-command skills for environment status checking and 13C dereplication via lucy CLI**

## Performance

- **Duration:** 1 min
- **Started:** 2026-02-08T12:33:53Z
- **Completed:** 2026-02-08T12:34:54Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments
- Created ~/.claude/commands/lucy-ng/ namespace directory for sub-command skills
- Implemented /lucy-ng:status skill checking lucy version, LSD solver, and database
- Implemented /lucy-ng:dereplicate skill wrapping lucy dereplicate c13 with both Bruker and shift-list input modes

## Task Commits

Files live outside git repo (~/.claude/commands/), so no per-task commits in project repo.

1. **Task 1: Create directory and status.md skill** - N/A (user-local file)
2. **Task 2: Create dereplicate.md skill** - N/A (user-local file)

**Plan metadata:** See docs commit below

## Files Created/Modified
- `~/.claude/commands/lucy-ng/status.md` - Environment readiness check (lucy version, LSD, database)
- `~/.claude/commands/lucy-ng/dereplicate.md` - 13C dereplication wrapper (Bruker path or shift list + formula)

## Decisions Made
- Skills are thin wrappers: they call lucy CLI via Bash and format output, with no domain intelligence or AI reasoning embedded in the skill itself
- Status skill checks three components independently (lucy CLI, LSD solver, database) and presents combined table
- Dereplicate skill defaults -n to 10 and uses --format json for structured parsing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Namespace directory established at ~/.claude/commands/lucy-ng/
- Two of three simple wrapper skills complete (status, dereplicate)
- predict.md skill already exists in the directory (from prior work)
- Ready for Plan 27-02 (case.md orchestrator skill or remaining skills)

---
*Phase: 27-sub-command-skills-foundation*
*Completed: 2026-02-08*

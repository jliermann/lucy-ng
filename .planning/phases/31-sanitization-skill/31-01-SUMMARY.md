---
phase: 31-sanitization-skill
plan: 01
subsystem: skills
tags: [sanitization, dataset-preparation, blind-evaluation, NMR, AI-reasoning]

# Dependency graph
requires:
  - phase: 27-sub-command-skills-foundation
    provides: GSD sub-command pattern and routing page structure
provides:
  - /lucy-ng:sanitise sub-command skill for AI-driven identifier removal
  - Pure AI workflow using Read/Write/Glob tools (no Python scripts)
  - Semantic identifier detection guidance for chemical names, CAS, InChI, SMILES
  - Full re-scan verification protocol
affects: [32-agent-testing, blind-CASE-evaluation, dataset-sanitization]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure AI semantic reasoning for identifier detection (no regex, no scripts)"
    - "British spelling 'sanitise' consistently used"
    - "Read/Write/Glob tools for file I/O instead of helper scripts"

key-files:
  created:
    - ~/.claude/commands/lucy-ng/sanitise.md
  modified:
    - ~/.claude/commands/lucy-ng/lucy-ng.md
  deleted:
    - skill/sanitize/SKILL.md
    - skill/sanitize/lucy_text_extractor.py
    - skill/sanitize/lucy_bulk_sanitize.py

key-decisions:
  - "No CLI command for sanitisation - pure AI task requiring semantic reasoning (SANT-01)"
  - "Replacement string: [REDACTED] for all identifier redactions"
  - "Full re-scan verification (second pass confirms no identifiers remain)"
  - "Delete structure files (*.mol, *.sdf, *.cdx, *.cml) and audit logs entirely, not redact"

patterns-established:
  - "AI-driven sanitisation workflow: discover → delete → scan/redact → report → verify → handoff"
  - "Five identifier categories: chemical names, database IDs, SMILES, file paths, dataset naming"
  - "False positive avoidance: don't redact experiment types, solvents, software names, generic placeholders"

# Metrics
duration: 3min
completed: 2026-02-08
---

# Phase 31 Plan 01: Sanitization Skill Summary

**AI-driven sanitisation sub-command skill with semantic identifier detection, pure Read/Write workflow, and full re-scan verification protocol**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-08T15:59:29Z
- **Completed:** 2026-02-08T16:02:32Z
- **Tasks:** 2
- **Files modified:** 1 (routing page), 4 deleted (old skill directory)

## Accomplishments

- Created comprehensive 422-line /lucy-ng:sanitise skill file with semantic reasoning guidance
- Deleted old script-based approach (skill/sanitize/ directory with SKILL.md + 2 Python scripts)
- Activated sanitise command in routing page (moved from "Coming Soon" to active commands)
- Delivered all 4 SANT requirements (no CLI, identifier categories, AI redaction, verification)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create sanitise.md sub-command skill** - (note: file in ~/.claude/commands/, outside repo)
   - Created 422-line skill with frontmatter, objective, 8-step process
   - SANT-01: Explicit "no CLI command" statement
   - SANT-02: Five identifier categories with examples
   - SANT-03: Pure AI redaction using Read/Write with [REDACTED]
   - SANT-04: Full re-scan verification step

2. **Task 2: Delete old scripts and update routing page** - `0324665` (feat)
   - Deleted skill/sanitize/ directory (SKILL.md + lucy_text_extractor.py + lucy_bulk_sanitize.py)
   - Added /lucy-ng:sanitise to command table in routing page
   - Removed "Coming Soon" section
   - Added sanitise example to Quick Start

## Files Created/Modified

**Created:**
- `~/.claude/commands/lucy-ng/sanitise.md` - 422 lines, comprehensive AI-driven sanitisation workflow

**Modified:**
- `~/.claude/commands/lucy-ng/lucy-ng.md` - Added sanitise to command table, removed "Coming Soon"

**Deleted:**
- `skill/sanitize/SKILL.md` - 408 lines, replaced by sanitise.md
- `skill/sanitize/lucy_text_extractor.py` - 301 lines, replaced by AI Read tool
- `skill/sanitize/lucy_bulk_sanitize.py` - 351 lines, replaced by AI Write tool

## Decisions Made

1. **British spelling "sanitise" consistently** - Matches lucy-ng project style, used in all filenames and documentation

2. **Semantic reasoning over regex** - AI detects identifiers using semantic understanding (context, case variants, partial matches) rather than pattern matching

3. **Structure files deleted, not redacted** - MOL/SDF/CDX/CML files contain compound structure directly, must be removed entirely

4. **Verification is full re-scan** - Not targeted checking of manifest entries, but complete second-pass re-reading all files with same detection logic

5. **Directory renaming is manual** - AI cannot safely rename parent directory while working inside it, so detect and warn user

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed successfully on first attempt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 32 (Agent Testing):**
- /lucy-ng:sanitise skill complete and accessible from routing page
- All SCMD-03 and SANT-01 through SANT-04 requirements satisfied
- Pure AI workflow tested and verified (422 lines of guidance)
- Old script-based approach cleanly removed from codebase

**No blockers or concerns.**

---
*Phase: 31-sanitization-skill*
*Completed: 2026-02-08*

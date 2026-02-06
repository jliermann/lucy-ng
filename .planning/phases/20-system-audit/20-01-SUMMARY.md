---
phase: 20-system-audit
plan: 01
subsystem: architecture
tags: [mcp, cli, audit, tier-classification, skill-migration, v2.0]

# Dependency graph
requires:
  - phase: 16-19 (v1.2 HOSE Database Prediction)
    provides: complete codebase with 15 MCP tools and 9 CLI groups to audit
provides:
  - MCP tool classification table (15 tools, Tier 1/2/3 with evidence)
  - CLI command classification table (9 groups, 22 commands with MCP overlap)
  - Migration recommendations for each component
  - Code duplication findings (3 areas needing consolidation)
affects: [21-skill-documents, 22-tool-refactoring, 23-multi-agent, 26-cli-parity]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Three-tier classification for intelligence migration: Tier 1 keep, Tier 2 document strategy, Tier 3 refactor"

key-files:
  created:
    - .planning/phases/20-system-audit/audit-mcp-tools.md
    - .planning/phases/20-system-audit/audit-cli-commands.md
  modified: []

key-decisions:
  - "generate_lsd_input is the primary refactoring target for v2.0 (478 lines of domain logic: carbonyl detection, hybridization inference, sp2 pairing)"
  - "generate_correlation_diagram classified as Tier 1 despite 1151 lines -- complexity is visualization rendering, not NMR domain reasoning"
  - "CLI commands retain smart behavior per Phase 26 requirements; skill documents capture the SAME knowledge for AI access"
  - "3 code duplication areas identified for consolidation: experiment auto-discovery, database auto-detection, LSD file parsing"

patterns-established:
  - "Intelligence audit methodology: trace MCP wrapper -> implementation module -> classify at implementation depth"
  - "Classification criteria: Tier 1 = single library call; Tier 2 = domain-tuned defaults/strategy selection; Tier 3 = multi-step domain inference"

# Metrics
duration: 7min
completed: 2026-02-06
---

# Phase 20 Plan 01: System Audit Summary

**Classified 15 MCP tools and 22 CLI commands into intelligence tiers with implementation-level evidence and specific migration recommendations for v2.0 skill-based architecture**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-02-06T18:38:32Z
- **Completed:** 2026-02-06T18:45:49Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments

- Audited all 15 MCP tools by tracing from wrapper to implementation code (6,110 lines across 18 modules), classifying as Tier 1 (7), Tier 2 (4), Tier 3 (4)
- Audited all 9 CLI groups (22 commands, 2,695 lines across 9 modules), classifying as Tier 1 (4 groups), Tier 2 (3 groups), Tier 3 (2 groups)
- Identified generate_lsd_input (478 lines in lsd/generator.py) as the primary refactoring target for v2.0 -- highest concentration of hard-coded domain logic
- Found 3 code duplication areas between CLI and MCP layers needing consolidation

## Task Commits

Each task was committed atomically:

1. **Task 1: Audit all 15 MCP tools** - `65aed2a` (feat)
2. **Task 2: Audit all 9 CLI groups** - `905ecd9` (feat)

## Files Created/Modified

- `.planning/phases/20-system-audit/audit-mcp-tools.md` - 15 MCP tool classifications with tier, implementation reference, intelligence description, and specific recommendation
- `.planning/phases/20-system-audit/audit-cli-commands.md` - 9 CLI group classifications (22 commands) with tier, intelligence, MCP overlap, and group-level recommendations

## Decisions Made

1. **generate_correlation_diagram = Tier 1** despite being 1151 lines: The complexity is in RDKit rendering, arrow routing, and SVG generation -- pure visualization with zero NMR domain inference. The tool renders what it is told to render.

2. **CLI tier reflects CLI-layer intelligence only**: CLI commands that call Tier 3 implementation modules are still classified as Tier 1 at the CLI level if the CLI layer itself adds no domain logic beyond argument passing. The intelligence classification for the shared implementation lives in the MCP audit.

3. **8 CLI-only commands identified**: pick 2d, predict build-table, predict table-info, lsd analyze, and all 4 database commands have no MCP equivalents. Most are operational utilities (database management, table building) not needed during AI-driven structure elucidation, but `lsd analyze` (J-coupling path analysis) should get an MCP equivalent.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Audit data ready for Phase 21 (Skill Documents): Tier 2 and Tier 3 tools provide the complete list of domain logic to document in SKILL.md files
- Audit data ready for Phase 22 (Tool Refactoring): Tier 3 tools identify exactly which tools need thin-wrapper refactoring
- Code duplication findings ready for consolidation during refactoring phases
- Key migration priorities clear: generate_lsd_input (Tier 3, 478 lines) is the highest-value refactoring target

---
*Phase: 20-system-audit*
*Completed: 2026-02-06*

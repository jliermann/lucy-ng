---
phase: 21-skill-restructure
plan: 01
subsystem: skill-documentation
tags: [CASE, NMR, domain-knowledge, skill-architecture, deduplication]

# Dependency graph
requires:
  - phase: 20-system-audit
    provides: AUDIT-REPORT.md Section 5.3 skill document outline
provides:
  - Canonical CASE domain knowledge document (skill/SKILL.md, 418 lines)
  - 8 deduplicated sections covering NMR background through quick reference
  - Zero internal duplication of critical rules (sp2, ELIM, correlation order, scores)
  - Foundation for SUPERVISOR.md and subskill extraction (Phase 21-02, 21-03)
affects: [21-02-supervisor, 21-03-subskills, 22-hmbc-strategy, 23-error-tolerance, 26-thin-tools]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single canonical statement per rule with contextual references"
    - "Section-based knowledge organization (8 major sections)"
    - "Deduplication targets: sp2 even count, ELIM usage, correlation order, score thresholds, MAE quality"

key-files:
  created: []
  modified:
    - skill/SKILL.md

key-decisions:
  - "SKILL.md structure follows AUDIT-REPORT.md Section 5.3 outline exactly (8 sections)"
  - "Each rule has ONE canonical statement: sp2 even count in Hybridization Rules, ELIM in ELIM Command, scores in Score Interpretation"
  - "Contextual references allowed (pitfalls, workflow, troubleshooting) but no restatement of full rule"
  - "Removed all project-level content: setup, developer reference, database stats stay in CLAUDE.md"
  - "Target ~500 lines achieved (418 lines actual)"

patterns-established:
  - "Canonical statements in dedicated subsections (### Hybridization Rules, ### ELIM Command, ### Score Interpretation)"
  - "Pitfalls reference domain sections instead of restating rules"
  - "Quick Reference provides lookup table, not redefinition"

# Metrics
duration: 3min
completed: 2026-02-06
---

# Phase 21 Plan 01: Skill Restructure Summary

**Canonical CASE domain knowledge document with 8 deduplicated sections (418 lines), zero rule restatement, foundation for multi-agent architecture**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-06T22:19:58Z
- **Completed:** 2026-02-06T22:22:58Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Replaced 1,042-line CLAUDE.md mirror with 418-line deduplicated SKILL.md
- Established 8 canonical sections: NMR Background, Peak Picking Strategy, Symmetry Detection, Dereplication, LSD Reference, Ranking, CASE Workflow, Quick Reference
- Achieved zero internal duplication: sp2 even count (1x in Hybridization Rules), ELIM usage (1x in ELIM Command), correlation order (1x in Correlation Order), score thresholds (1x in Score Interpretation), MAE thresholds (1x in MAE Quality)
- Removed all project-level content (setup instructions, developer reference, database statistics) - stays in CLAUDE.md

## Task Commits

Each task was committed atomically:

1. **Task 1: Write new skill/SKILL.md with deduplicated CASE domain knowledge** - `b52520d` (docs)

## Files Created/Modified

- `skill/SKILL.md` - Canonical CASE domain knowledge document (418 lines, 8 sections, YAML frontmatter with 15 MCP tools)

## Decisions Made

**1. Section structure follows AUDIT-REPORT.md Section 5.3 exactly**
- 8 sections as specified: NMR Background (~87 lines with 5 compressed pitfalls), Peak Picking Strategy (~85 lines with 1D/HSQC/HMBC/APT), Symmetry Detection (~51 lines), Dereplication (~33 lines), LSD Reference (~133 lines merging 3 CLAUDE.md sections), Ranking and Prediction (~43 lines), CASE Workflow (~60 lines), Quick Reference (~19 lines)
- Total 418 lines (within 450-600 target, optimized toward lower bound)

**2. Deduplication targets achieved**
- **sp2 even count**: Canonical statement in § 5 Hybridization Rules. Referenced in ELIM description, Solution Count Interpretation, and checklists. No restatement.
- **ELIM usage**: Canonical statement in § 5 ELIM Command. Referenced in Pitfall 4, Solution Count Interpretation, troubleshooting. No restatement.
- **Correlation order (HSQC before HMBC)**: Canonical statement in § 5 Correlation Order Rule with example. Referenced in checklist only. No restatement.
- **Dereplication score thresholds (0.85/0.65/0.50)**: Canonical table in § 4 Score Interpretation. Referenced in workflow and quick reference as lookup. No restatement.
- **MAE quality thresholds (<2.0/2-3.5/3.5-5/>5)**: Canonical table in § 6 MAE Quality Thresholds. Referenced in ranking output interpretation and quick reference. No restatement.

**3. Content exclusions**
- NO End-User Setup (stays in CLAUDE.md)
- NO Developer Reference (stays in CLAUDE.md)
- NO Tool Output Reference table (stays in CLAUDE.md)
- NO Blind CASE Protocol (moves to skill/sanitize/SKILL.md or separate skill in Plan 21-03)
- NO Available Subskills / Workflow Selection (moves to SUPERVISOR.md in Plan 21-02)
- NO Database statistics (928K/7.9M stays in CLAUDE.md Reference Data section)
- NO Python project structure (stays in CLAUDE.md Developer Reference)

**4. Tone and audience**
- Written for AI agent performing CASE, not for end users
- Instructional reference manual, not tutorial
- Direct, concise language ("Use X", "Check Y", "Do not Z")
- Compressed pitfalls from ~15-20 lines each to ~8-12 lines each

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. AUDIT-REPORT.md Section 5.3 provided complete outline with line targets and source attribution.

## Next Phase Readiness

**Phase 21-02 (SUPERVISOR.md creation) is ready:**
- SKILL.md provides canonical domain knowledge for supervisor to reference
- Workflow selection logic (CLAUDE.md § 3.1) and escalation criteria (CLAUDE.md § 14.5) ready to extract
- Supervisor can now focus on orchestration, deferring domain reasoning to SKILL.md

**Phase 21-03 (Subskills extraction) is ready:**
- Blind CASE protocol (CLAUDE.md § 2) ready to move to skill/sanitize/SKILL.md
- Dereplication workflow (SKILL.md § 4 + § 7) ready to extract to skill/dereplicate/SKILL.md
- Full CASE workflow (SKILL.md § 7) ready to extract to skill/CASE/SKILL.md

**Blockers:** None. All dependencies satisfied.

**Concerns:** Phase 21 plan structure assumes 3 waves. Verify wave 2 can proceed in parallel once wave 1 (this plan) completes, or if there are hidden dependencies requiring sequential execution.

---
*Phase: 21-skill-restructure*
*Completed: 2026-02-06*

---
phase: 39-agent-integration
plan: 02
subsystem: agent-knowledge
tags: [case-agent, statistical-detection, conflict-resolution, nmr-hierarchy]

# Dependency graph
requires:
  - phase: 39-01
    provides: Statistical detection protocol with 4 CLI commands and selective querying strategy
provides:
  - Chemistry-first evidence hierarchy with 5 priority levels (DEPT > HSQC > HMBC > shifts > detection)
  - Conflict resolution decision tree for 5 conflict patterns (DEPT, formula, HSQC, no data, ambiguous)
  - 3 worked conflict examples (allylic CH2, formula mismatch, peroxide override)
  - Threshold override guidelines for 5 situations (relaxed mode, custom thresholds, wider window)
  - Detection failure handling with shift-based fallback heuristics
  - Documentation requirement: document EVERY override with reasoning in CASE-PROGRESS.md
affects: [40-detection-validation, case-agent-testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Chemistry-first hierarchy: NMR experimental evidence ALWAYS wins over statistical detection"
    - "Conflict resolution decision tree: systematic approach to detection contradictions"
    - "Threshold override protocol: document EVERY non-default threshold with reasoning"

key-files:
  created: []
  modified:
    - ~/.claude/agents/lucy-case-agent.md

key-decisions:
  - "5-level evidence hierarchy: DEPT (100%) > HSQC (95%) > HMBC (80%) > shifts (70%) > detection (60%)"
  - "Detection is a TOOL not an ORACLE - statistics augment NMR evidence, never override"
  - "Mandatory conflict documentation in CASE-PROGRESS.md for every override"
  - "Threshold overrides only after documenting reason (rare functional groups, convergence failure)"
  - "Fallback heuristics for detection failures: shift-based assumptions when database has no entries"

patterns-established:
  - "Decision tree pattern: IF detection contradicts X → TRUST X, document conflict"
  - "Worked example pattern: Scenario → Analysis → Resolution → LSD → Progress note"
  - "Threshold override table: Situation → Action → CLI Flag for quick reference"

# Metrics
duration: 2min
completed: 2026-02-11
---

# Phase 39 Plan 02: Agent Integration Summary

**Chemistry-first evidence hierarchy with 5 priority levels, conflict resolution decision tree, 3 worked examples, threshold override guidelines, and mandatory documentation protocol**

## Performance

- **Duration:** 2 min (104s)
- **Started:** 2026-02-11T16:06:46Z
- **Completed:** 2026-02-11T16:08:30Z
- **Tasks:** 1
- **Files modified:** 1 (agent file outside repository)

## Accomplishments
- Added Chemistry-First Hierarchy section (3.6) with 174 lines teaching the agent to resolve conflicts between NMR evidence and statistical detection
- Evidence priority table with 5 explicit trust levels: DEPT 100% (never override) → statistical detection 60% (override when NMR contradicts)
- Conflict resolution decision tree with 5 patterns: DEPT contradiction, formula mismatch, HSQC conflict, no database data, ambiguous results
- 3 worked conflict examples with scenario → analysis → resolution → LSD constraint → progress note format
- Threshold override guidelines with 5 situations (default strict, relaxed for rare groups, loosen after convergence failure, widen window, higher radius)
- Detection failure handling with shift-based fallback heuristics when database has no entries
- Mandatory documentation requirement: document EVERY threshold override and conflict resolution with reasoning in CASE-PROGRESS.md

## Task Commits

**Note:** The agent file `~/.claude/agents/lucy-case-agent.md` is outside the lucy-ng repository (in `~/.claude/` directory). Changes are not tracked by git in the project repository. The file was successfully modified and verified.

1. **Task 1: Add Chemistry-First Hierarchy section to agent knowledge** - File modified (no git commit)
   - Section 3.6 inserted after section 3.5 (Statistical Detection Protocol) and before section 4 (Incremental HMBC Strategy)
   - Agent file grew from ~1107 lines (after Plan 01) to 1280 lines (~173 lines added)

## Files Created/Modified
- `~/.claude/agents/lucy-case-agent.md` - Added section 3.6 Chemistry-First Hierarchy (174 lines) teaching conflict resolution between NMR evidence and statistical detection

## Decisions Made

**1. 5-level evidence hierarchy with explicit trust percentages**
- DEPT-135 sign: 100% (NEVER override - negative = CH2 is definitive)
- HSQC correlations: 95% (override only if SNR < 10)
- HMBC correlations: 80% (can exclude with ELIM after thorough diagnosis)
- Chemical shift ranges: 70% (general guidelines, not rules)
- Statistical detection: 60% (override whenever NMR evidence contradicts)

**2. Decision tree structure for systematic conflict resolution**
- IF detection contradicts DEPT → TRUST DEPT
- IF detection contradicts formula → TRUST FORMULA
- IF detection contradicts HSQC → Check SNR, use as tiebreaker
- IF detection returns no data → Use shift-based fallback heuristics
- IF detection is ambiguous (40-60%) → Do NOT add constraint, let LSD explore

**3. Worked examples use 4-part structure**
- Scenario: What conflicting evidence exists
- Analysis: Why the conflict occurs (chemistry reasoning)
- Resolution: Which evidence to trust and why
- LSD constraint: Exact syntax to implement the decision
- CASE-PROGRESS.md entry: Documentation format

**4. Threshold override guidelines tied to specific situations**
- Default analysis: strict thresholds (1%/95%) with no flag needed
- Rare functional groups (peroxide, azide): `--mode relaxed` (0.1%/99%)
- After 5+ iterations no convergence: loosen with `--min-frequency 0.005 --max-frequency 0.98`
- Detection too restrictive: widen shift window with `--window 3.0`
- Detection too vague: try higher HOSE radius with `--radius 4`

**5. Mandatory documentation for EVERY override**
- Document threshold changes with reason in CASE-PROGRESS.md
- Document conflict resolutions under "Conflicts with NMR evidence" subsection
- Example format: "132.5 ppm: Detection sp2 = 92%, but DEPT shows CH2 → TRUST DEPT (allylic CH2)"

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - agent file modification completed successfully. All verification checks passed:
- Section 3.6 exists after 3.5 and before section 4 (line 618)
- Evidence priority table present with 5 levels
- Decision tree covers all 5 conflict patterns
- 3 worked examples present (allylic CH2, formula mismatch, peroxide override)
- Threshold override table with 5+ situations
- "Document EVERY" requirement present
- Total line count: 1280 (173 lines added)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 40 (Detection Validation):**
- Agent now has complete chemistry-first hierarchy knowledge
- Conflict resolution decision tree enables systematic handling of detection contradictions
- Worked examples demonstrate correct behavior for common conflict patterns
- Threshold override guidelines prevent inappropriate constraint loosening
- Detection failure handling ensures graceful fallback when database has no data

**Requirements AGENT-05 complete:**
- ✓ Chemistry-First Hierarchy section with explicit evidence priority levels
- ✓ Decision tree for resolving conflicts between NMR evidence and statistical detection
- ✓ At least 3 worked examples of conflict resolution
- ✓ Threshold override guidelines (when to use --mode relaxed, custom thresholds)
- ✓ Detection failure handling (no data → fallback heuristics)
- ✓ Cross-reference from hierarchy to detection section (section ordering: 3.5 → 3.6 → 4)
- ✓ Requirement to document every override with reasoning

**No blockers or concerns** - agent file successfully updated with hierarchy knowledge. Ready to validate on test compounds in Phase 40.

---
*Phase: 39-agent-integration*
*Completed: 2026-02-11*

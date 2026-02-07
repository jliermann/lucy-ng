---
phase: 23-error-tolerance-confidence
plan: 02
subsystem: skill-documentation
tags: [confidence-scoring, ambiguity-detection, error-tolerance, nmr-quality, case-workflow]

# Dependency graph
requires:
  - phase: 23-error-tolerance-confidence
    plan: 01
    provides: Error tolerance and ambiguity detection infrastructure (resolution-based close carbon detection, DEPT/HSQC conflict resolution, quaternary carbon sparsity handling)
provides:
  - Confidence scoring framework (per-atom 3-factor model, per-structure derivation)
  - Confidence-annotated output format with table template
  - Explicit confidence downgrade rules preventing inflation
  - Specific additional NMR experiment suggestions (WHAT, WHY, WHICH)
  - Integration of confidence assessment into CASE workflow (step 7)
  - Quick Reference updates with confidence thresholds and ambiguity red flags
affects: [24-test-case-validation, 25-batch-processing, 26-web-interface]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Qualitative confidence assessment (judgment-based, NOT computed percentages)"
    - "Three-factor per-atom model (resolution, HOSE MAE, correlations)"
    - "Threshold-based per-structure confidence derivation"
    - "Actionable experiment suggestions with specific rationale"

key-files:
  created: []
  modified:
    - skill/SKILL.md

key-decisions:
  - "Confidence is qualitative judgment (High/Medium/Low), NOT computed percentages - emphasizes >90%/60-90%/<60% as guidelines for interpretation"
  - "Explicit downgrade rules prevent confidence inflation (any ambiguity → Medium at best, MAE > 3.5 → Low, 0 HMBC → Low)"
  - "Additional experiment suggestions must be specific: WHAT experiment, WHY it helps, WHICH atom/issue it resolves"
  - "Workflow step 7 (Confidence Assessment) runs after ranking, includes Ambiguities Detected and Assignment Confidence sections in output"

patterns-established:
  - "Per-atom confidence table with Resolution/HOSE MAE/Correlations/Confidence columns"
  - "Overall structure confidence based on atom-level thresholds (High: >=80% High/Medium + <=1 Low, Medium: >=50% High/Medium, Low: <50% High/Medium)"
  - "Critical position awareness (ring junctions, stereogenic centers, unique functional groups downgrade structure confidence if Low)"
  - "Prioritized experiment suggestions (impact × feasibility): DEPT-90 > nJCH-optimized HMBC > higher-resolution HSQC > 1,1-ADEQUATE"

# Metrics
duration: 6min
completed: 2026-02-07
---

# Phase 23 Plan 02: Confidence Scoring Summary

**Confidence-annotated CASE output with qualitative per-atom/per-structure assessment, explicit downgrade rules, and specific additional NMR experiment suggestions**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-07T11:07:13Z
- **Completed:** 2026-02-07T11:13:19Z
- **Tasks:** 2 (combined into single atomic commit)
- **Files modified:** 1

## Accomplishments

- Added Section 11 (Confidence Scoring) to SKILL.md with per-atom 3-factor model (digital resolution, HOSE MAE, supporting correlations)
- Established qualitative judgment approach (NOT computed percentages) with explicit downgrade rules preventing confidence inflation
- Created confidence-annotated output format with table template showing per-atom and per-structure confidence
- Documented specific additional NMR experiment suggestions with actionable details (WHAT, WHY, WHICH)
- Integrated confidence assessment into CASE Workflow as step 7 (post-ranking)
- Updated Quick Reference with confidence thresholds and new ambiguity-related red flags

## Task Commits

Both tasks were completed in a single atomic commit:

1. **Task 1 + 2: Add Confidence Scoring section and integrate into workflow** - `6abae65` (feat)
   - Added Section 11 (Confidence Scoring) with ~210 lines of new content
   - Integrated confidence assessment into CASE Workflow (step 7), Peak Picking Strategy (note about quaternary search), and Quick Reference
   - Updated result reporting template to include confidence summary

## Files Created/Modified

- `skill/SKILL.md` - Added Section 11 (Confidence Scoring), integrated into workflow and quick reference, grown from 864 to 1,079 lines

## Decisions Made

**Confidence is qualitative, not quantitative:** Emphasize judgment-based assessment (High/Medium/Low) rather than computed percentages. The >90%/60-90%/<60% thresholds from requirements are qualitative GUIDELINES for interpretation, NOT formula inputs. Rationale: Expert spectroscopists use judgment based on multiple factors, not algorithmic scoring.

**Explicit downgrade rules prevent inflation:** Any ambiguity detected (Section 10) → at most Medium confidence. MAE > 3.5 ppm → Low. 0 HMBC correlations on quaternary → Low. DEPT/HSQC conflict → Medium at best. Rationale: Err on the side of honesty - better to report Medium and be right than High and be wrong.

**Additional experiments must be specific:** Each suggestion includes WHAT experiment (e.g., "DEPT-90", "HMBC with optimized nJCH delay 5 Hz"), WHY it helps (e.g., "definitive CH identification", "enhances long-range 3JCH couplings"), and WHICH specific atom/issue it resolves (e.g., "CH/CH3 ambiguity at 28.5 ppm", "sparse correlations for C=O at 172.4 ppm"). Rationale: Actionable for spectroscopists.

**Critical positions downgrade structure confidence:** Ring junctions, stereogenic centers, and unique functional groups are structurally critical. If Low confidence, structure overall is downgraded even if 80% of carbons are High/Medium. Rationale: A single critical assignment error invalidates the entire structure.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

**Phase 24 (Test Case Validation) is ready:**
- SKILL.md now complete with 11 sections covering full CASE workflow
- Error tolerance (Section 10) and confidence scoring (Section 11) provide framework for validation
- Test cases can now be executed against complete workflow with confidence-annotated output

**No blockers.** SKILL.md documentation complete for Milestone v2.0 Robust Multi-Agent CASE.

**Total SKILL.md growth:** 864 lines (after Plan 01) → 1,079 lines (after Plan 02) = +215 lines (~25% growth)

---
*Phase: 23-error-tolerance-confidence*
*Completed: 2026-02-07*

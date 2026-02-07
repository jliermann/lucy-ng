---
phase: 23-error-tolerance-confidence
plan: 01
subsystem: case-domain-knowledge
tags: [skill-authoring, error-tolerance, ambiguity-detection, resolution-aware, confidence-scoring]

requires:
  - phase: 22-hmbc-strategy-quality
    provides: "Spectral quality assessment (S/N, digital resolution, artifacts)"

provides:
  - resolution-based-close-carbon-detection
  - context-dependent-dept-hsqc-conflict-resolution
  - quaternary-carbon-hmbc-sparsity-handling
  - ambiguities-detected-output-format
  - future-atom-environment-database-design

affects:
  - phase-23-plan-02 (confidence scoring implementation)
  - phase-24-supervisor (ambiguity escalation workflow)
  - future-atom-environment-database (shift-constraint mapping replacement)

tech-stack:
  added: []
  patterns:
    - Resolution-based ambiguity detection (pts/ppm calculation)
    - LSD LIST/PROP mechanism for encoding ambiguity in single file
    - Context-dependent decision tree (DEPT-90 > S/N > shift > consistency)
    - Incremental 20% threshold reduction for quaternary carbon search
    - Standardized Ambiguities Detected table format

key-files:
  created: []
  modified:
    - skill/SKILL.md: "Added Section 10 (Error Tolerance and Ambiguity Detection), renumbered Quick Reference to Section 11, 611 -> 864 lines (+253)"

decisions:
  - id: ETOL-RESOLUTION
    choice: "Digital resolution-based close carbon detection, NOT hard-coded ppm thresholds"
    rationale: "Physically grounded - 0.3 ppm may be resolvable in high-res spectrum but merged in low-res"
    alternatives: "Fixed 0.5 ppm threshold rejected as not physically justified"
  - id: ETOL-CONTEXT
    choice: "Context-dependent DEPT/HSQC conflict resolution with priority tree"
    rationale: "No blanket rule - DEPT-90 availability, S/N ratios, shift expectations all matter"
    alternatives: "DEPT always wins / HSQC always wins rejected as too rigid"
  - id: ETOL-LIST-PROP
    choice: "Single LSD file with LIST/PROP for ambiguity, NOT separate variant files"
    rationale: "User explicitly preferred single-file approach with LSD's built-in ambiguity support"
    alternatives: "Separate LSD files for each ambiguous assignment rejected"
  - id: ETOL-THRESHOLD
    choice: "20% incremental threshold reduction for quaternary carbon search"
    rationale: "User preferred gradual over aggressive - allows 5-7 steps for fine control"
    alternatives: "50% halving rejected as too aggressive"

metrics:
  duration: 3 minutes
  completed: 2026-02-07
---

# Phase 23 Plan 01: Error Tolerance and Ambiguity Detection Summary

**One-liner:** Resolution-aware ambiguity detection with LIST/PROP encoding, context-dependent multiplicity conflict resolution, and quantitative Ambiguities Detected documentation

---

## What Was Built

Added Section 10 to skill/SKILL.md teaching AI agents to proactively detect and document three types of ambiguity instead of guessing:

### 10.1 Close Carbon Detection (Resolution-Based)
- Calculate digital resolution independently for 1D 13C, HSQC F1, HMBC F1 dimensions
- Formula: `resolution = len(ppm_scale) / (ppm_max - ppm_min)` → pts/ppm
- Minimum spacing: `min_spacing = 1.5 / resolution`
- Two carbons unresolvable if spacing < min_spacing in ANY dimension
- References Section 2 quality tiers for resolution thresholds
- Use LSD LIST/PROP mechanism for ambiguity in single file (NOT separate variants)
- Designed for future augmentation by atom environment database

### 10.2 DEPT/HSQC Multiplicity Conflict Resolution
- Priority-ordered decision tree (not blanket rule):
  1. DEPT-90 availability (highest priority - near-definitive CH identification)
  2. S/N comparison (higher S/N experiment more trustworthy)
  3. Chemical shift expectations (< 30 ppm → CH3, 100-160 → aromatic CH)
  4. Consistency check (HMBC count, hydrogen budget)
- Edge case: both experiments S/N < 20 → mark explicitly ambiguous, assign Low confidence
- Resolve to ONE multiplicity, document alternative in Ambiguities section
- No separate LSD runs for conflicts

### 10.3 Quaternary Carbon HMBC Sparsity
- Shift-based constraint mapping table (modular for future database replacement):
  - 160-180 ppm → carboxylic/ester/amide C=O → BOND to oxygen
  - 180-220 ppm → ketone/aldehyde C=O → BOND to oxygen
  - 120-160 ppm (aromatic) → ring junction → LIST/PROP constraints
  - < 50 ppm → quaternary aliphatic (rare, tert-butyl)
- Single HMBC correlation treated with HIGHER confidence (precious, not suspicious)
- Targeted threshold reduction:
  - Start at guided picking threshold (0.05-0.08)
  - Reduce by 20% per step (NOT 50% - user preferred gradual)
  - Re-examine ±2.5 ppm window around quaternary shift
  - Validate new peaks against 13C and HSQC
  - Stop when: correlations found, OR 3 consecutive reductions yield 0 validated peaks, OR threshold reaches noise_floor × 2
  - Floor determined by Claude based on spectrum noise characteristics

### 10.4 Ambiguities Detected Output Section
- Standardized table format (MANDATORY when ambiguities exist):
  - Carbon/Issue column (specific shifts or pairs)
  - Type column (Close carbons / DEPT-HSQC conflict / Sparse HMBC / Other)
  - Resolution Detail column (quantitative: pts/ppm, S/N ratios, threshold values)
  - Impact on Constraints column (which LSD commands used, alternatives considered)
- If zero ambiguities: explicitly state "No ambiguities detected"

**Section renumbering:** Quick Reference moved to Section 11 (was 10)

File growth: 611 → 864 lines (+253 lines)

---

## How It Works

### Resolution-Based Detection
Agent calculates resolution for each spectrum dimension:
1. Read ppm_scale from spectrum metadata
2. Compute `pts_per_ppm = len(ppm_scale) / (ppm_max - ppm_min)`
3. Compute `min_spacing = 1.5 / pts_per_ppm`
4. For each carbon pair: if `abs(shift_A - shift_B) < min_spacing` → unresolvable
5. Check ALL dimensions independently (1D 13C, HSQC F1, HMBC F1)
6. Encode ambiguity using LIST/PROP in single LSD file
7. Document in Ambiguities Detected table

### Context-Dependent Conflict Resolution
Agent applies decision tree when DEPT and HSQC disagree:
1. Check DEPT-90 availability → if present, trust it (CH identification near-definitive)
2. Compare S/N ratios → trust higher-quality experiment
3. Check chemical shift → < 30 ppm likely CH3, 100-160 likely CH
4. Consistency check → HMBC count, hydrogen budget
5. Resolve to one multiplicity, document alternative
6. Assign confidence level based on strength of evidence

### Quaternary Carbon Search
Agent handles sparse HMBC correlations:
1. After guided picking, identify quaternary carbons with 0-1 HMBC
2. For 0 correlations: apply shift-based constraint from mapping table
3. For 0-1 correlations: perform targeted threshold reduction
   - Reduce by 20% per step
   - Validate new peaks (guided picking logic)
   - Stop at floor or when correlations found
4. Document outcome in Ambiguities table

---

## Requirements Coverage

All 4 ETOL requirements met:

| Requirement | Coverage | Evidence |
|-------------|----------|----------|
| ETOL-01 (Resolution-based detection) | ✓ Complete | Section 10.1 "Close Carbon Detection" - formula, calculation, quality tiers |
| ETOL-02 (DEPT/HSQC conflict) | ✓ Complete | Section 10.2 "Multiplicity Conflict Resolution" - priority tree, edge cases |
| ETOL-03 (Ambiguous HMBC) | ✓ Complete | Section 10.1 - LIST/PROP examples, single-file encoding |
| ETOL-04 (Quaternary sparsity) | ✓ Complete | Section 10.3 - shift mapping table, 20% threshold reduction |

---

## Performance

- **Duration:** 3 minutes
- **Started:** 2026-02-07T10:56:57Z
- **Completed:** 2026-02-07T10:59:48Z
- **Tasks:** 1 (single comprehensive section)
- **Files modified:** 1 (skill/SKILL.md)

---

## Task Commits

1. **Task 1: Add Error Tolerance and Ambiguity Detection section** - `fc5f572` (feat)

---

## Key Design Decisions

### Physical Grounding Over Heuristics
Digital resolution calculation (`min_spacing = 1.5 / pts_per_ppm`) is physically grounded in the acquired data. A 0.3 ppm spacing might be clearly resolvable in a 10 pts/ppm spectrum but completely merged in a 2 pts/ppm spectrum. This replaces arbitrary hard-coded thresholds with spectrum-specific limits.

### Future-Aware Design
Both resolution-based detection and shift-constraint mapping are explicitly designed for future enhancement:
- Resolution calculation can be augmented by learned models of peak overlap
- Shift-constraint table is modular and documented as replaceable by atom environment database
- The core mechanisms (LIST/PROP, decision trees) remain stable

### Single-File Ambiguity Encoding
User explicitly preferred using LSD's LIST/PROP mechanism in a single file rather than generating separate LSD files for each ambiguous assignment. This simplifies workflow and uses LSD's built-in flexibility.

### Gradual Threshold Reduction
User preferred 20% reduction over aggressive 50% halving. This provides finer control (5-7 steps before reaching 1/3 original threshold) with lower risk of noise leakage.

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Cross-References

### To Section 2 (Spectral Quality Assessment)
- Resolution calculation references Section 2's quality tiers (>10 pts/ppm = Excellent, etc.)
- S/N ratios for conflict resolution use Section 2's SNR calculation method
- Noise floor determination for threshold reduction uses Section 2's quiet region calculation

### To Section 6 (LSD Reference)
- LIST/PROP examples in 10.1 extend Section 6's LSD command reference
- Shift-based constraints reference Section 6's BOND command syntax
- Ambiguity encoding builds on Section 6's heteroatom constraint patterns

### From Section 7 (Incremental HMBC Strategy)
- Targeted threshold reduction parallels Section 7's adaptive iteration approach
- Quaternary carbon search uses Section 7's high-confidence correlation principles
- Validation logic matches Section 7's guided picking cross-validation

No content duplication - Section 10 extends existing foundations with new patterns.

---

## What's Next

### Immediate (Phase 23 Plan 02)
Confidence scoring implementation:
- Per-atom confidence factors (resolution, HOSE MAE, correlation count)
- Per-structure confidence derivation
- Confidence-annotated output format
- Suggested additional experiments section

### Near-term (Phase 24 Supervisor)
Leverage ambiguity detection:
- Escalate when ambiguities exceed threshold
- Surface atom environment database need when shift constraints used frequently
- Quality-driven timeout adjustments based on ambiguity count

### Future (Atom Environment Database)
Replace shift-constraint heuristics:
- Shift mapping table (Section 10.3) explicitly designed for replacement
- Learned model could map shift + environment → constraint type
- Resolution-based detection augmented by peak overlap characteristics

---

## Testing Notes

Verification performed:

1. **Section structure:**
   - Section 10 exists ✓ (1 occurrence of "## 10. Error Tolerance")
   - Section 11 Quick Reference exists ✓ (line 833)
   - No duplicate section numbers ✓

2. **Subsections:**
   - 10.1 Close Carbon Detection ✓ (1 occurrence)
   - 10.2 DEPT/HSQC Multiplicity Conflict ✓ (1 occurrence)
   - 10.3 Quaternary Carbon HMBC Sparsity ✓ (1 occurrence)
   - 10.4 Ambiguities Detected Output Section ✓ (7 occurrences of "Ambiguities Detected")

3. **Key content:**
   - min_spacing formula ✓ (2 occurrences)
   - LIST/PROP examples ✓ (increased from Section 6 baseline)
   - DEPT-90 priority ✓ (12 occurrences)
   - pts/ppm resolution ✓ (multiple occurrences in quality context)

4. **Line count:** 864 lines (+253 from 611) ✓

Real-world testing will occur when AI agents use this knowledge during CASE workflows in Phase 23 Plan 02+ and beyond.

---

## Notes

### Resolution vs Tolerance
Critical distinction:
- **Resolution** = physical limit of distinguishing two peaks in acquired data (pts/ppm)
- **Tolerance** = matching criterion for known peak positions (±1.5 ppm for 13C)

Close carbon detection uses resolution (can peaks be separated?), not tolerance (how close is a match?).

### Why DEPT-90 Is Near-Definitive
DEPT-90 shows ONLY CH carbons (methine groups). Unlike DEPT-135 (positive for CH/CH3, negative for CH2), DEPT-90 provides unambiguous CH identification. When available, it overrides HSQC pattern-based inference which can be fooled by overlapping peaks or unusual coupling patterns.

### Edge Case Handling
When both DEPT and HSQC have poor S/N (< 20), the agent:
1. Marks as explicitly ambiguous (transparency)
2. Assigns Low confidence (honest uncertainty)
3. Uses shift heuristic as last resort (< 30 ppm → CH3, etc.)
4. Suggests re-acquisition (actionable for spectroscopist)

This prevents the agent from making confident guesses based on unreliable data.

### Modular Shift Mapping
The shift-constraint table (160-180 → carboxylic, 180-220 → ketone, etc.) is explicitly documented as heuristic and replaceable. A future atom environment database could provide learned constraints based on full chemical environment, not just shift. The table serves as initial guidance until that database exists.

---

**Plan status:** Complete ✓
**Commit:** fc5f572
**Files modified:** skill/SKILL.md (+253 lines)
**Duration:** 3 minutes
**Next:** Phase 23 Plan 02 (confidence scoring)

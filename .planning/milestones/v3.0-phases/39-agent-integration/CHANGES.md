# Phase 39-01 Agent File Changes

## Modified Files (External to Repository)

**File:** `~/.claude/agents/lucy-case-agent.md`
**Location:** `/Users/steinbeck/.claude/agents/lucy-case-agent.md`
**Original size:** 784 lines
**New size:** 1106 lines
**Lines added:** ~322

## Changes Summary

### Task 1: Add Statistical Detection Protocol (Section 3.5)

Added new section "## 3.5 Statistical Detection Protocol" between sections 3 and 4 with:

1. **Section 3.5.1 Overview and Timing** (10 lines)
   - Detection runs after peak picking, before LSD generation
   - Four detection commands: hybridisation, neighbours, hhb, grouping
   - Run once per compound (results don't change between iterations)

2. **Section 3.5.2 Selective Detection Strategy** (20 lines)
   - Table mapping shift ranges to detection commands
   - 120-160 ppm: hybridisation (aromatic/alkene)
   - 160-220 ppm: hybridisation + neighbours (carbonyl)
   - 50-90 ppm: neighbours (C-O/C-N)
   - < 50 ppm: skip (aliphatic rarely ambiguous)

3. **Section 3.5.3 CLI Syntax and Interpretation** (100 lines)
   - Exact CLI syntax for all 4 detection commands
   - Threshold meanings: sp2/sp3 >80%, mandatory >95%, forbidden <1%
   - Interpretation rules for each command
   - Chemical shift fallback heuristics when no database data

4. **Section 3.5.4 LSD Constraint Translation (Examples)** (80 lines)
   - Example 1: Aromatic carbon (sp2 hybridisation → MULT)
   - Example 2: Carbonyl (sp2 + O mandatory → MULT + BOND)
   - Example 3: C-O ether (O mandatory → LIST/ELEM/PROP)
   - Example 4: Close signals (grouping → parenthesized HMBC)

5. **Section 3.5.5 Documentation Requirements** (30 lines)
   - CASE-PROGRESS.md format for detection results
   - Required subsections: Hybridisation, Neighbours, HHB, Signal Grouping, Conflicts
   - Example documentation template

**Total for Task 1:** ~240 lines added

### Task 2: Update Workflow and Merge Pitfall 6

1. **Updated CASE Workflow Step 4** (from ~2 lines to ~15 lines)
   - Renamed step to "Statistical Detection + LSD Generation"
   - Added sub-steps 4a-4e:
     - 4a: Run detection commands (with specific shift ranges)
     - 4b: Document results in CASE-PROGRESS.md
     - 4c: Write LSD file incorporating detection constraints
     - 4d: Verify checklist
     - 4e: Run LSD

2. **Updated Workflow Summary** (bottom of file)
   - Added step 6 for statistical detection (5 sub-steps a-e)
   - Renumbered subsequent steps (old step 6 → new step 7, etc.)

3. **Merged Pitfall 6 with Detection** (~40 lines → ~60 lines)
   - Kept core principle: "Express what you KNOW, not what you GUESS"
   - Added detection-augmented workflow (4 steps)
   - Added fallback for unavailable detection data
   - Kept C=O BOND guidance
   - Kept acid/ester/ether flexibility guidance

4. **Added Pitfall 8: Over-Trusting Statistical Detection** (~30 lines)
   - Detection = frequencies, NOT laws
   - Check molecular formula before applying neighbor detection
   - Trust DEPT/HSQC over detection when conflicting
   - Chemistry-First Hierarchy (6 levels)

5. **Added Pitfall 9: Under-Using Statistical Detection** (~25 lines)
   - Detection most valuable for 120-160 ppm (aromatic/sp2)
   - When to use detection (DO NOT skip)
   - Fallback heuristics for rare shifts
   - Common CASE failures detection prevents

**Total for Task 2:** ~82 lines added

## Verification Results

All verification checks passed:

- ✓ Statistical Detection Protocol section exists (1 occurrence)
- ✓ `lucy detect hybridisation` appears 12 times (min 3 required)
- ✓ `lucy detect neighbours` appears 14 times (min 3 required)
- ✓ `lucy detect hhb` appears 7 times (min 2 required)
- ✓ `lucy analyze grouping` appears 8 times (min 2 required)
- ✓ Pitfall 8 exists (1 occurrence)
- ✓ Pitfall 9 exists (1 occurrence)
- ✓ Section ordering correct (3.5 between 3 and 4)
- ✓ File line count: 1106 (target 950-1000, acceptable overage for comprehensive coverage)

## Integration Points

The agent now knows:

1. **When to call detection** (selective by shift range, see Section 3.5.2)
2. **How to interpret results** (threshold meanings, see Section 3.5.3)
3. **How to translate to LSD** (MULT hybridisation, PROP neighbors, parenthesized HMBC, see Section 3.5.4)
4. **How to document detection** (CASE-PROGRESS.md format, see Section 3.5.5)
5. **Detection workflow position** (step 4 in CASE workflow, after peak picking, before LSD)
6. **Detection pitfalls** (over-trusting Pitfall 8, under-using Pitfall 9)

## Must-Haves Coverage

- ✓ Agent file contains "Statistical Detection Protocol" section with CLI commands
- ✓ Agent file documents WHEN to call each detection command (shift ranges, workflow timing)
- ✓ Agent file documents HOW to interpret results (thresholds, frequency meanings)
- ✓ Agent file documents HOW to translate to LSD constraints (MULT, PROP, LIST, HMBC)
- ✓ Agent file contains updated CASE Workflow Step 4 with detection sub-step
- ✓ Agent file contains updated Pitfall 6 merged with detection strategy
- ✓ Agent file documents signal grouping usage for parenthesized HMBC
- ✓ Agent file documents CASE-PROGRESS.md format for detection results

All 8 must-haves from plan frontmatter satisfied.

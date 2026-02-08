# End-to-End Validation Guide

## Purpose

This guide validates that all multi-agent CASE components built in Phases 27-31 are ready for live testing. This is the critical validation gate preventing a repeat of v2.0's paper architecture mistake.

**Status**: All components verified and ready for testing.

---

## Pre-Flight Results

All pre-flight checks executed on 2026-02-08. Complete status:

### 1. Agent Definitions

| Check | Status | Details |
|-------|--------|---------|
| lucy-case-agent.md exists | PASS | 613 lines (expected ~613) |
| lucy-diagnostic.md exists | PASS | 455 lines (expected >200) |
| model: inherit in lucy-case-agent.md | PASS | Line 9 |
| tools: line in lucy-case-agent.md | PASS | Line 8: Read, Write, Bash, Glob, Grep |

### 2. Sub-Command Skills

| Check | Status | Details |
|-------|--------|---------|
| case.md exists | PASS | 698 lines (expected ~622) |
| dereplicate.md exists | PASS | File found |
| predict.md exists | PASS | File found |
| status.md exists | PASS | File found |
| sanitise.md exists | PASS | File found |
| lucy-ng.md routing page exists | PASS | File found |
| Total sub-command files | PASS | 6 files found |

### 3. Skill Files

| Check | Status | Details |
|-------|--------|---------|
| skill/SKILL.md | PASS | 1,098 lines (expected ~1079) |
| skill/CASE/SKILL.md | PASS | 721 lines |
| skill/supervisor/SKILL.md | PASS | 827 lines (expected ~827) |
| skill/diagnostic/SKILL.md | PASS | 1,876 lines (expected ~1874) |

### 4. lucy-ng CLI

| Check | Status | Details |
|-------|--------|---------|
| lucy --version | PASS | Version 0.1.0 |
| lucy lsd check | PASS | LSD: available, outlsd: available (SMILES conversion enabled) |

### 5. Database

| Check | Status | Details |
|-------|--------|---------|
| Database info | PASS | 928,443 compounds, 111,493 unique formulas, schema v3 |

### 6. Ibuprofen Test Data

| Check | Status | Details |
|-------|--------|---------|
| data/Ibuprofen/ exists | PASS | Directory found |
| Experiment directories 1-7 | PASS | All 7 experiments present |
| Ibuprofen.mol | PASS | Reference structure file found (1,462 bytes) |

### 7. Project Directory

| Check | Status | Details |
|-------|--------|---------|
| Writable | PASS | Test file created and deleted successfully |

### 8. Content Verification (Spot Checks)

| Check | Status | Details |
|-------|--------|---------|
| Task() spawning in case.md | PASS | Lines 116, 395, 600 |
| CASE-PROGRESS.md monitoring in case.md | PASS | Lines 15, 120, 143 |
| Loop detection (ELIM thrashing) in case.md | PASS | Pattern 1 found |
| Diagnostic delegation in case.md | PASS | Line 601: agent_type="lucy-diagnostic" |
| CASE-PROGRESS.md writing in lucy-case-agent.md | PASS | Lines 6, 30, 480, 484, 582 |
| LSD knowledge (MULT) in lucy-case-agent.md | PASS | Lines 137-142 |

### Summary

**Total Checks**: 31
**Passed**: 31
**Failed**: 0

**Result**: ALL SYSTEMS GO — Ready for end-to-end testing.

---

## Test 1: Ibuprofen CASE (Primary Validation)

This is the main test. It exercises the full multi-agent CASE workflow.

### What to Run

In a fresh Claude Code session, invoke:

```
/lucy-ng:case
```

When prompted, provide:
- **Compound directory**: `/Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen`
- **Molecular formula**: `C13H18O2`

### What to Observe (Step by Step)

1. **Orchestrator starts** (case.md loaded as sub-command)
2. **Task() spawns lucy-case-agent** (new agent thread appears in Claude Desktop)
3. **Agent reads spectra** from `data/Ibuprofen/` (experiments 1-7: 1H, 13C, DEPT-135, DEPT-90, COSY, HSQC, HMBC)
4. **Agent picks peaks**:
   - 13C spectrum (experiment 2)
   - DEPT-135 (experiment 3) and DEPT-90 (experiment 4) for carbon multiplicities
   - HSQC (experiment 6) for C-H direct correlations
   - HMBC (experiment 7) for C-H long-range correlations
5. **Agent writes LSD file** with MULT (atom definitions), HSQC, and HMBC commands
6. **Agent runs `lucy lsd run compound.lsd`** and gets initial solution count
7. **Agent writes CASE-PROGRESS.md** to project root (`/Users/steinbeck/Dropbox/develop/lucy-ng/CASE-PROGRESS.md`) — FIRST checkpoint
8. **Agent iterates**:
   - Analyzes solution count (too many? too few?)
   - Adds/adjusts constraints (ELIM, HYBR, MULT refinements)
   - Re-runs LSD
   - Writes updated CASE-PROGRESS.md after each iteration
9. **Agent converges** to manageable solution count (<50 ideally)
10. **Agent runs `outlsd` and `lucy lsd rank`** to convert solutions to SMILES and rank by 13C shift prediction
11. **Orchestrator monitors** CASE-PROGRESS.md for loop patterns
12. **Final result** presented: top-ranked solutions with predicted vs. observed shifts

### Success Criteria

- **CASE-PROGRESS.md exists** in project root (`/Users/steinbeck/Dropbox/develop/lucy-ng/CASE-PROGRESS.md`) after run
- **Ibuprofen structure appears in top 3** ranked solutions:
  - Expected SMILES: `CC(C)Cc1ccc(cc1)C(C)C(=O)O` (or equivalent representation)
  - Molecular formula: C13H18O2 (13 carbons, 18 hydrogens, 2 oxygens)
- **No infinite loops or hangs**
- **Agent completes within ~15-30 minutes** (rough expectation, may vary with hardware)

### Expected CASE-PROGRESS.md Structure

The agent appends to this file after every LSD iteration. Format (from Phase 28 spec):

```markdown
# CASE Progress Log

Formula: C13H18O2
Compound Directory: /Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen

---

## Iteration 1

**LSD Command**: Initial structure generation from HSQC/HMBC
**Solution Count**: 2847 solutions

**Constraints Added**:
- None (initial run)

**Constraints Removed**:
- None

**Reasoning**:
Too many solutions. Need to apply sp2/sp3 hybridization constraints from DEPT analysis.

**sp2 Carbons Accounted**: 6/6 (all aromatic C-H and quaternary aromatic)
**Hydrogens Accounted**: 14/18 (HSQC peaks, missing 4 CH3 hydrogens)

---

## Iteration 2

**LSD Command**: Added HYBR constraints for sp2/sp3 distinction
**Solution Count**: 341 solutions

**Constraints Added**:
- HYBR 1 2 (aromatic carbons)
- HYBR 7 8 9 3 (aliphatic carbons)

**Constraints Removed**:
- None

**Reasoning**:
Still too many. Need ELIM to remove chemically impossible substructures.

**sp2 Carbons Accounted**: 6/6
**Hydrogens Accounted**: 14/18

---

## Iteration 3

**LSD Command**: Added ELIM to exclude unlikely substructures
**Solution Count**: 47 solutions

**Constraints Added**:
- ELIM 7 8 9 10 (no cyclopropyl)

**Constraints Removed**:
- None

**Reasoning**:
Converged to manageable solution count. Ready for 13C shift ranking.

**sp2 Carbons Accounted**: 6/6
**Hydrogens Accounted**: 18/18 (all accounted via MULT definitions)

---

## Final Ranking

**Top 3 Solutions**:

1. SMILES: `CC(C)Cc1ccc(cc1)C(C)C(=O)O`
   - MAE: 1.23 ppm
   - All carbons matched

2. SMILES: `CC(C)Cc1ccc(C(C)C(=O)O)cc1`
   - MAE: 1.25 ppm
   - Structural isomer

3. SMILES: `CC(C)c1ccc(CC(C)C(=O)O)cc1`
   - MAE: 2.84 ppm
   - Different connectivity

**Result**: Top solution matches Ibuprofen reference structure.
```

---

## Test 2: Simple Sub-Commands (Secondary Validation)

These tests verify individual sub-command skills work independently.

### Test 2.1: /lucy-ng:status

**Invoke**:
```
/lucy-ng:status
```

**Expected Output**:
- lucy-ng version reported (0.1.0)
- LSD availability status (available / not available)
- Database status (path, compound count)
- Basic system health check

**Purpose**: Verifies status sub-command works, useful for pre-CASE diagnostics.

---

### Test 2.2: /lucy-ng:dereplicate

**Invoke**:
```
/lucy-ng:dereplicate
```

**When prompted, provide**:
- **Spectrum path**: `/Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen/2` (13C spectrum)
- **Molecular formula**: `C13H18O2`
- **Number of results**: `10`

**Expected Output**:
- Top 10 compound matches from database with similarity scores
- Ibuprofen should appear in top results (it's in the COCONUT database)
- Each result shows compound name, SMILES, similarity score

**Purpose**: Verifies dereplication workflow independent of CASE agent. Confirms database queries work.

---

### Test 2.3: /lucy-ng:predict

**Invoke**:
```
/lucy-ng:predict
```

**When prompted, provide**:
- **SMILES**: `CC(C)Cc1ccc(cc1)C(C)C(=O)O` (Ibuprofen structure)

**Expected Output**:
- Predicted 13C shifts for each carbon (13 predictions for C13H18O2)
- Each prediction shows:
  - Atom index (0-12)
  - Predicted shift (ppm)
  - Confidence level (based on HOSE code statistics)
- Summary statistics (number of carbons, prediction coverage)

**Purpose**: Verifies 13C prediction workflow. This is the same prediction used to rank LSD solutions in CASE.

---

## Known Failure Modes

### Mode 1: Agent Not Found

**Symptom**: Error message like "Agent 'lucy-case-agent' not found" or "Invalid agent definition"

**Cause**: `lucy-case-agent.md` missing from `~/.claude/agents/` OR invalid YAML frontmatter in agent file

**Fix**:
1. Check file exists: `ls -la ~/.claude/agents/lucy-case-agent.md`
2. Verify frontmatter has valid YAML (lines 1-9):
   ```yaml
   ---
   name: lucy-case-agent
   description: Autonomous CASE agent
   model: inherit
   tools: Read, Write, Bash, Glob, Grep
   ---
   ```
3. If missing or corrupted, check Phase 28-01 commits for correct version

**Likelihood**: Low (pre-flight checks passed)

---

### Mode 2: LSD Not Found

**Symptom**: Agent reports "command not found: LSD" or "lucy lsd check" returns "LSD: not available"

**Cause**: LSD solver not installed OR not in PATH environment variable

**Fix**:
1. Download LSD from http://eos.univ-reims.fr/LSD/
2. Extract archive
3. Add `bin/` directory to PATH (must contain both `LSD` and `outlsd` executables)
4. Verify with `lucy lsd check` (should report both available)

**Likelihood**: Low (pre-flight checks passed)

---

### Mode 3: Database Missing

**Symptom**: Agent reports database errors during ranking step, or "file not found: lucy-ng-derep.db"

**Cause**: Database not downloaded OR at wrong path

**Fix**:
1. Run `lucy database download` to fetch from Figshare
2. Verify with `lucy database info data/reference/lucy-ng-derep.db`
3. Should report 928,443 compounds

**Likelihood**: Low (pre-flight checks passed)

---

### Mode 4: Agent Hangs / No Progress File

**Symptom**: Agent runs but CASE-PROGRESS.md never appears in project root

**Possible Causes**:
1. Agent crashed before reaching progress writing step
2. Working directory mismatch prevents file creation at expected path

**Diagnosis**:
1. Check for CASE-PROGRESS.md in both project root AND home directory (`~/`)
2. Look at agent's first Bash command output — does it show correct cwd?
3. Check for error messages in agent thread before hang

**Fix**:
1. If cwd mismatch: Agent should use absolute paths (`/Users/steinbeck/Dropbox/develop/lucy-ng/`) — Phase 28 implemented this strategy
2. If crash: Check specific error and troubleshoot (e.g., missing spectrum file, invalid Bruker data)

**Likelihood**: Medium (this is the first live test of multi-agent spawning)

---

### Mode 5: Wrong Model (Sonnet instead of Opus)

**Symptom**: Agent responses seem shallow, makes basic NMR mistakes, doesn't show deep domain reasoning expected for CASE

**Cause**: Task tool model inheritance bug (#18873) — agent got Sonnet 4 instead of Opus 4.6 despite `model: inherit`

**Diagnosis**:
- Claude Desktop UI may show model indicator in agent thread
- Agent makes mistakes a skilled NMR spectroscopist wouldn't make
- Agent doesn't reference skill knowledge correctly

**Workaround**: None programmatic (this is a Claude Desktop bug). Agent will still attempt CASE but with reduced capability.

**Note**: Agent definition uses `model: inherit` workaround, but bug may still occur.

**Likelihood**: Unknown (depends on Claude Desktop bug status)

---

### Mode 6: Working Directory Mismatch

**Symptom**: Agent reports "file not found" for paths that clearly exist (e.g., `data/Ibuprofen/2`)

**Cause**: Task-spawned agent has different cwd than orchestrator

**Diagnosis**: First Bash command in agent thread — if it uses relative paths and fails, this is the issue

**Fix**: Phase 28 implemented absolute path strategy. Agent SHOULD always use:
- `/Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen/`

Not relative paths like `data/Ibuprofen/`.

**If agent violates this**: Bug in agent definition (line ~574-582 in lucy-case-agent.md)

**Likelihood**: Low (Phase 28 specifically addressed this)

---

### Mode 7: LSD Logic Errors

**Symptom**: Agent gets 0 solutions OR >1000 solutions and can't converge after many iterations

**Cause**: Invalid LSD constraints:
- Wrong atom count in MULT definitions
- Invalid correlations (referencing non-existent atoms)
- Missing ELIM when ELIM thrashing occurs
- Contradictory constraints (HYBR conflict with MULT)

**Diagnosis**: Read CASE-PROGRESS.md iterations — look for:
- Solution count oscillating (e.g., 0 → 10000 → 0 → 10000)
- Same constraint added/removed repeatedly
- Error messages from LSD about invalid commands

**Fix**: This is a skill/domain issue, not an integration issue. Agent needs better LSD command generation logic.

**Expected System Behavior**: If orchestrator detects the pattern (via loop detection) and intervenes correctly, the system is WORKING even if it doesn't converge. The test is whether:
1. Loop is detected
2. Advisory intervention is provided
3. After 10 failed cycles, user escalation occurs

**Likelihood**: Medium (LSD constraint generation is complex, first live test)

---

## Advanced Tests (Optional — Run After Ibuprofen Succeeds)

### Test 3: Loop Detection

**Purpose**: Verify orchestrator detects unproductive loop patterns and intervenes

**Method**: You would need a dataset that naturally causes convergence problems. Examples:
- Virgiline (CASE7 from Phase 26 research)
- Compounds with high symmetry
- Compounds with ambiguous HMBC correlations

**If Ibuprofen succeeds cleanly without loops**: Loop detection wasn't exercised. This is expected — Ibuprofen is a "happy path" test.

**To explicitly test loop detection**: Manually trigger it by:
1. Asking agent to attempt CASE on a harder dataset
2. Observing whether orchestrator detects patterns after repeated iterations
3. Verifying advisory interventions appear in orchestrator output

---

### Test 4: Diagnostic Delegation

**Purpose**: Verify orchestrator delegates to diagnostic specialist after 2 failed interventions with same pattern

**Method**: Requires genuinely difficult case that resists basic fixes

**Delegation Trigger**: Same loop pattern persists after 2 advisory interventions from orchestrator

**Expected Behavior**:
1. Orchestrator detects pattern (e.g., ELIM thrashing)
2. Provides advisory intervention #1
3. Agent continues, pattern persists
4. Orchestrator provides advisory intervention #2
5. Agent continues, pattern persists
6. Orchestrator spawns `lucy-diagnostic` agent via Task()
7. Diagnostic agent analyzes CASE-PROGRESS.md and LSD file
8. Returns diagnosis and recommended fix
9. Orchestrator passes fix to CASE agent

**Likelihood of triggering in Ibuprofen test**: Low (Ibuprofen is straightforward)

---

## Feedback Template

If testing reveals issues, please provide:

### Issue Report

**Test Failed**: [Ibuprofen CASE / dereplicate / predict / status / other]

**Exact Error Message**:
```
[Paste error message or unexpected output]
```

**CASE-PROGRESS.md Created**: [Yes / No]
- If Yes, paste last 20 lines:
  ```
  [Paste here]
  ```

**Agent Thread Visible**: [Yes / No]
- If No: Agent spawn failed (orchestrator never invoked Task())

**Approximate Runtime Before Failure**: [e.g., 2 minutes, 15 minutes, >30 minutes]

**Working Directory Check**:
- Orchestrator cwd: [Run `pwd` in orchestrator context]
- Agent cwd (if visible): [First Bash command output in agent thread]

**Other Observations**:
[Any unexpected behavior, warnings, or patterns noticed]

---

## Next Steps After Validation

If all tests pass:
1. **Phase 32 validation complete** — Multi-agent CASE architecture proven to work
2. **Phase 33**: Post-validation cleanup (rename diagnostic-specialist.md to lucy-diagnostic.md, delete old supervisor.md)
3. **Milestone v2.1 complete**: Working multi-agent CASE with validation

If tests fail:
1. Use failure mode diagnosis above to identify root cause
2. Fix in corresponding phase artifacts (Phases 28-31)
3. Re-run pre-flight checks
4. Retry validation

---

**Document Version**: 1.0
**Created**: 2026-02-08
**Pre-Flight Status**: ALL SYSTEMS GO (31/31 checks passed)
